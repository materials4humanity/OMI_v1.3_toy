"""Tabular baselines for Spec §9.3's required comparison (`[Pass C]`):
"comparison against gradient-boosted trees and tabular regression." ADR-039
(docs/DECISIONS.md) fixes the implementation choice: both baselines are
built from scratch in numpy, matching the policy CLAUDE.md §8 and
`src/omi/learning.py` (ADR-029) already establish rather than adding a new
pinned dependency.

Domain-neutral (CLAUDE.md §5 invariant 3): operates on plain feature/target
arrays, with no reference to any domain's state schema or readouts. The
domain-specific comparison itself (which features, which readouts, which
sweep) lives in `tests/test_baseline_characterisation.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

import numpy as np
from scipy.special import erf

from omi.state import FloatArray


class TabularRegressor(Protocol):
    """The shared shape both Spec §9.3 tabular baselines expose, so a sweep
    can iterate over either without a type-specific branch."""

    def fit(self, x: FloatArray, y: FloatArray) -> None:
        """Fit the regressor to *x*, *y* (Spec §9.3's baseline-comparison
        requirement)."""
        ...

    def predict(self, x: FloatArray) -> FloatArray:
        """Predict the target for *x* (Spec §9.3's baseline-comparison
        requirement)."""
        ...


@dataclass
class RidgeRegressor:
    """Closed-form ridge regression with an unregularised intercept (Spec
    §9.3's "tabular regression" baseline): `y ≈ X @ beta + intercept`,
    `beta = (X_c^T X_c + alpha*I)^-1 X_c^T y_c` on centred `X`/`y`.
    """

    alpha: float = 1.0
    _beta: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros(0))
    _x_mean: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros(0))
    _y_mean: float = field(init=False, repr=False, default=0.0)

    def fit(self, x: FloatArray, y: FloatArray) -> None:
        """Solve the ridge normal equations (Spec §9.3's tabular-regression
        baseline)."""
        self._x_mean = x.mean(axis=0)
        self._y_mean = float(y.mean())
        x_c = x - self._x_mean
        y_c = y - self._y_mean
        n_features = x.shape[1]
        gram = x_c.T @ x_c + self.alpha * np.eye(n_features)
        self._beta = np.linalg.solve(gram, x_c.T @ y_c)

    def predict(self, x: FloatArray) -> FloatArray:
        """Predict via the fitted affine map (Spec §9.3)."""
        return (x - self._x_mean) @ self._beta + self._y_mean


@dataclass(frozen=True)
class _TreeNode:
    """A regression-tree node: an internal split or a leaf value."""

    is_leaf: bool
    value: float = 0.0
    feature: int = -1
    threshold: float = 0.0
    left: "_TreeNode | None" = None
    right: "_TreeNode | None" = None


def _best_split(x: FloatArray, residual: FloatArray) -> tuple[int, float, float] | None:
    """Greedy search over every feature and every candidate threshold
    (midpoints between sorted unique values) for the split minimising the
    weighted sum of within-child variance. Returns ``None`` if no split
    reduces variance (e.g. a constant residual)."""
    n, n_features = x.shape
    best: tuple[float, int, float] | None = None  # (score, feature, threshold)
    parent_var = float(np.var(residual)) * n
    for f in range(n_features):
        values = x[:, f]
        order = np.argsort(values)
        sorted_values = values[order]
        sorted_residual = residual[order]
        uniques = np.unique(sorted_values)
        if uniques.shape[0] < 2:
            continue
        thresholds = (uniques[:-1] + uniques[1:]) / 2.0
        for threshold in thresholds:
            left_mask = sorted_values <= threshold
            n_left = int(left_mask.sum())
            n_right = n - n_left
            if n_left == 0 or n_right == 0:
                continue
            left_residual = sorted_residual[left_mask]
            right_residual = sorted_residual[~left_mask]
            score = n_left * float(np.var(left_residual)) + n_right * float(np.var(right_residual))
            if best is None or score < best[0]:
                best = (score, f, float(threshold))
    if best is None or best[0] >= parent_var:
        return None
    _, feature, threshold = best
    return feature, threshold, best[0]


def _build_tree(x: FloatArray, residual: FloatArray, max_depth: int, min_samples_leaf: int) -> _TreeNode:
    if max_depth == 0 or x.shape[0] < 2 * min_samples_leaf:
        return _TreeNode(is_leaf=True, value=float(residual.mean()))
    split = _best_split(x, residual)
    if split is None:
        return _TreeNode(is_leaf=True, value=float(residual.mean()))
    feature, threshold, _score = split
    left_mask = x[:, feature] <= threshold
    if left_mask.sum() < min_samples_leaf or (~left_mask).sum() < min_samples_leaf:
        return _TreeNode(is_leaf=True, value=float(residual.mean()))
    left = _build_tree(x[left_mask], residual[left_mask], max_depth - 1, min_samples_leaf)
    right = _build_tree(x[~left_mask], residual[~left_mask], max_depth - 1, min_samples_leaf)
    return _TreeNode(is_leaf=False, feature=feature, threshold=threshold, left=left, right=right)


def _predict_tree(node: _TreeNode, x: FloatArray) -> FloatArray:
    predictions = np.empty(x.shape[0])
    for i in range(x.shape[0]):
        current = node
        while not current.is_leaf:
            assert current.left is not None and current.right is not None
            current = current.left if x[i, current.feature] <= current.threshold else current.right
        predictions[i] = current.value
    return predictions


@dataclass
class GradientBoostedTreeRegressor:
    """A minimal gradient-boosted regression-tree ensemble (Spec §9.3's
    "gradient-boosted trees" baseline), built from scratch in numpy
    (ADR-039): each successive tree is fit to the current residual
    (squared-error boosting, equivalent to a constant learning rate on the
    negative gradient for an L2 loss), predictions summed with a fixed
    shrinkage.
    """

    n_estimators: int = 50
    max_depth: int = 3
    learning_rate: float = 0.1
    min_samples_leaf: int = 2
    _trees: list[_TreeNode] = field(init=False, repr=False, default_factory=list)
    _base_value: float = field(init=False, repr=False, default=0.0)

    def fit(self, x: FloatArray, y: FloatArray) -> None:
        """Boost successive shallow regression trees against the current
        residual (Spec §9.3's gradient-boosted-trees baseline)."""
        self._base_value = float(y.mean())
        residual = y - self._base_value
        trees: list[_TreeNode] = []
        for _ in range(self.n_estimators):
            tree = _build_tree(x, residual, self.max_depth, self.min_samples_leaf)
            prediction = _predict_tree(tree, x)
            residual = residual - self.learning_rate * prediction
            trees.append(tree)
        self._trees = trees

    def predict(self, x: FloatArray) -> FloatArray:
        """Sum the base value and every tree's shrunk prediction (Spec
        §9.3)."""
        total = np.full(x.shape[0], self._base_value)
        for tree in self._trees:
            total = total + self.learning_rate * _predict_tree(tree, x)
        return total


@dataclass
class GaussianProcessRegressor:
    """A Gaussian-process regressor with an anisotropic squared-exponential kernel and a
    **fitted** white-noise term, for Spec §9.3's baseline-comparison requirement in its
    *acquisition-comparator* role (ADR-065).

    Not one of Spec §9.3's two named tabular baselines, and deliberately not a substitute
    for either: `RidgeRegressor` and `GradientBoostedTreeRegressor` remain the §9.3
    comparators everywhere they are already used, so no existing baseline number is
    re-based (ADR-057 as ADR-065 scopes it). This class exists because a claim *about* a
    Gaussian-process acquisition cannot be evaluated without one.

    Built in numpy for ADR-039's reason — no new pinned dependency (CLAUDE.md §8).

    **The fitted noise level is the point, not an implementation detail.** `noise_ratio`
    is this baseline's own best signal that something is unexplained, and ADR-065's stated
    expectation is that it rises under a missing state variable *and* under inflated
    measurement scatter, converging in both cases. Fixing the noise level instead of
    fitting it would hand a comparative claim to the framework by construction, which is
    the weakened-baseline failure M11 established produces an uninterpretable result.
    """

    length_scale_grid: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0)
    """Candidate ARD length scales, in standardised-input units. A grid rather than a
    gradient optimiser: the marginal likelihood is cheap at campaign sizes, and a declared
    grid is reproducible without a seeded optimiser start."""
    noise_grid: tuple[float, ...] = (0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0)
    """Candidate noise standard deviations, in standardised-target units. Deliberately finer
    than :attr:`length_scale_grid`: the fitted noise level is this baseline's own diagnostic
    (see the class docstring), so a coarse grid would hobble it at exactly the quantity a
    comparative claim rests on."""
    jitter: float = 1.0e-10
    """Numerical floor on the Cholesky factorisation, not a modelling choice."""

    _x: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros((0, 0)))
    _alpha: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros(0))
    _chol: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros((0, 0)))
    _x_mean: FloatArray = field(init=False, repr=False, default_factory=lambda: np.zeros(0))
    _x_scale: FloatArray = field(init=False, repr=False, default_factory=lambda: np.ones(0))
    _y_mean: float = field(init=False, repr=False, default=0.0)
    _y_scale: float = field(init=False, repr=False, default=1.0)
    length_scales: FloatArray = field(init=False, repr=False, default_factory=lambda: np.ones(0))
    noise_sd: float = field(init=False, repr=False, default=0.0)
    """Fitted noise standard deviation in **standardised-target** units; see
    :attr:`noise_ratio` for the reading a practitioner would take."""
    log_marginal_likelihood: float = field(init=False, repr=False, default=float("-nan"))

    def _kernel(self, a: FloatArray, b: FloatArray, length_scales: FloatArray) -> FloatArray:
        scaled_a = a / length_scales
        scaled_b = b / length_scales
        square = (
            (scaled_a**2).sum(axis=1)[:, None]
            + (scaled_b**2).sum(axis=1)[None, :]
            - 2.0 * scaled_a @ scaled_b.T
        )
        return np.asarray(np.exp(-0.5 * np.maximum(square, 0.0)), dtype=np.float64)

    def fit(self, x: FloatArray, y: FloatArray) -> None:
        """Standardise, then select length scales and noise by maximising the exact log
        marginal likelihood over the declared grids (Spec §9.3's fair-baseline
        requirement; ADR-065).

        Inputs are standardised per coordinate, which is what makes one length-scale grid
        serve coordinates with genuinely different ranges — an isotropic kernel on unequal
        ranges would be a weakened opponent for a reason unrelated to the comparison.
        """
        self._x_mean = x.mean(axis=0)
        spread = x.std(axis=0)
        self._x_scale = np.where(spread > 0.0, spread, 1.0)
        self._y_mean = float(y.mean())
        y_spread = float(y.std())
        self._y_scale = y_spread if y_spread > 0.0 else 1.0

        self._x = (x - self._x_mean) / self._x_scale
        target = (y - self._y_mean) / self._y_scale
        n = self._x.shape[0]
        n_features = self._x.shape[1]

        best = (float("-inf"), np.ones(n_features), self.noise_grid[0], np.zeros(0), np.zeros((0, 0)))
        for scale in self.length_scale_grid:
            length_scales = np.full(n_features, scale)
            base = self._kernel(self._x, self._x, length_scales)
            for noise in self.noise_grid:
                gram = base + (noise**2 + self.jitter) * np.eye(n)
                try:
                    chol = np.linalg.cholesky(gram)
                except np.linalg.LinAlgError:  # pragma: no cover - jitter makes this unreachable
                    continue
                alpha = np.linalg.solve(chol.T, np.linalg.solve(chol, target))
                evidence = float(
                    -0.5 * target @ alpha
                    - np.log(np.diag(chol)).sum()
                    - 0.5 * n * np.log(2.0 * np.pi)
                )
                if evidence > best[0]:
                    best = (evidence, length_scales, noise, alpha, chol)

        self.log_marginal_likelihood, self.length_scales, self.noise_sd, self._alpha, self._chol = best

    def predict(self, x: FloatArray) -> FloatArray:
        """Posterior mean at *x* (Spec §9.3)."""
        mean, _ = self.predict_with_sd(x)
        return mean

    def predict_with_sd(self, x: FloatArray) -> tuple[FloatArray, FloatArray]:
        """Posterior mean and standard deviation at *x*, both in the target's own units
        (Spec §9.3's baseline comparison, in ADR-065's acquisition-comparator role).

        Returned together because the acquisition (:func:`expected_improvement`) needs
        both, and because a posterior mean quoted without its uncertainty is the reading
        CLAUDE.md §8 forbids for a measured quantity.
        """
        standardised = (x - self._x_mean) / self._x_scale
        cross = self._kernel(standardised, self._x, self.length_scales)
        mean = cross @ self._alpha
        solved = np.linalg.solve(self._chol, cross.T)
        variance = np.maximum(1.0 - (solved**2).sum(axis=0), 0.0)
        return (
            mean * self._y_scale + self._y_mean,
            np.sqrt(variance) * self._y_scale,
        )

    @property
    def noise_ratio(self) -> float:
        """Fitted noise standard deviation as a fraction of the target's own spread
        (Spec §9.3; ADR-065).

        The comparator's own "is something unexplained" reading, in a unit that does not
        depend on the target's scale, so it is comparable across campaign arms (CLAUDE.md
        invariant 1's reasoning applied to a baseline's diagnostic)."""
        return float(self.noise_sd)

    @property
    def fitted_noise(self) -> float:
        """Fitted noise standard deviation in the **target's** units (Spec §9.3; ADR-065) —
        what a practitioner
        would compare against a known measurement precision."""
        return float(self.noise_sd * self._y_scale)


def expected_improvement(
    mean: FloatArray, standard_deviation: FloatArray, incumbent: float
) -> FloatArray:
    """Closed-form Expected Improvement for a **maximisation** objective (Spec §9.3's
    baseline comparison, in ADR-065's acquisition-comparator role; Core §5's search
    formulation is what an acquisition stands in for).

    `EI(x) = (μ − y*)Φ(z) + σφ(z)`, `z = (μ − y*)/σ`, and zero where `σ = 0`.

    Chosen over upper-confidence-bound because UCB needs an exploration weight for which
    neither Core nor Spec supplies a basis — ADR-026's slack-parameter objection applied to
    the comparator, which is this repository's own standard applied to its opponent. EI
    needs only the incumbent, which a campaign already has.

    Domain-neutral (CLAUDE.md invariant 3): takes arrays, knows nothing of composition.
    """
    sd = np.asarray(standard_deviation, dtype=np.float64)
    gap = np.asarray(mean, dtype=np.float64) - incumbent
    safe = np.where(sd > 0.0, sd, 1.0)
    z = gap / safe
    normal_cdf = _standard_normal_cdf(z)
    normal_pdf = np.exp(-0.5 * z**2) / np.sqrt(2.0 * np.pi)
    value = gap * normal_cdf + sd * normal_pdf
    return np.asarray(np.where(sd > 0.0, value, np.maximum(gap, 0.0)), dtype=np.float64)


def _standard_normal_cdf(z: FloatArray) -> FloatArray:
    """`Φ` via the error function, so :func:`expected_improvement` stays closed-form and
    adds no dependency beyond what ADR-039 already accepts."""
    return np.asarray(0.5 * (1.0 + erf(z / np.sqrt(2.0))), dtype=np.float64)


def root_mean_squared_error(predicted: FloatArray, true: FloatArray) -> float:
    """Plain RMSE, the forward-accuracy metric Spec §9.3's comparison
    reports alongside inverse-design hit rate."""
    return float(np.sqrt(np.mean((predicted - true) ** 2)))


def inverse_design_hit_rate(
    control_grid: FloatArray,
    predicted_response_grid: FloatArray,
    targets: FloatArray,
    true_response_fn: Callable[[float], float],
    tolerance: float,
) -> float:
    """Spec §9.3's inverse-design axis: for each declared *target*, select
    the *control_grid* value whose *predicted_response_grid* entry is
    closest to it (grid-search inversion through the model's own forward
    map), evaluate the true simulator (*true_response_fn*) at that
    selected control, and score a "hit" as `|true - target| < tolerance`
    (ADR-039). Returns the fraction of targets hit — the axis Spec §9.3
    names as the one on which a tabular model is structurally, not merely
    quantitatively, disadvantaged: it has no forward map to invert except
    by re-querying its own fitted surface.
    """
    hits = 0
    for target in targets:
        idx = int(np.argmin(np.abs(predicted_response_grid - target)))
        chosen_control = float(control_grid[idx])
        achieved = true_response_fn(chosen_control)
        if abs(achieved - target) < tolerance:
            hits += 1
    return hits / len(targets)
