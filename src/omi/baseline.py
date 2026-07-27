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
