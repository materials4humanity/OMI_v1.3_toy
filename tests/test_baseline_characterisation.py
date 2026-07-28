"""M10.2 (docs/ROADMAP.md): baseline characterisation harness for Spec
§9.3's required comparison against gradient-boosted trees and tabular
regression (ADR-039, docs/DECISIONS.md).

**Scoping note, discovered while building this harness.** Flagship's two
declared Type-0/Type-2 readouts, `AggregateHardness` and
`BendAngleAtReferenceGeometry`, are both, by Core §2.6's own property/
performance distinction, functionals of the constitutive operator alone —
computed against a null (zero-driving) control (`AggregateHardness.evaluate`'s
own docstring: "so no additional hardening accrues"). Confirmed directly:
neither responds at all to the domain's declared process control
(`heating_intensity`, `transfer_speed`) — both are pure functions of the
*incoming* state. A forward/inverse comparison swept over the *control*
axis would therefore be vacuous on these two readouts (every control choice
gives an identical response). This harness instead sweeps the domain's
*composition* axis (incoming `inclusion_content`, `prior_grain_size`), both
of which the constitutive operator's own response formula depends on
directly. Its inverse-design comparison is accordingly a **structure
inverse** (Core §5: target response → incoming composition), not a process
control inverse — a deliberate, stated substitution, not an oversight.

Both tabular baselines and the `DeepONetOperator` "operator graph"
contestant are trained on the *same* record count at each configuration
(ADR-039): comparing against the exact analytic simulator would be vacuous
(zero error by construction), so the simulator is used only as ground
truth for generating labels and scoring held-out test/inversion targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from omi.baseline import (
    GradientBoostedTreeRegressor,
    RidgeRegressor,
    inverse_design_hit_rate,
    root_mean_squared_error,
)
from omi.chain import Chain, Segment
from omi.constraints import monotone_increasing, monotone_increasing_jacobian
from omi.inverse import ApparatusParameterization, gradient_control_search
from omi.learning import DeepONetOperator, TrainingRecord, init_deeponet_params, train_deeponet
from omi.operators import Control
from omi.readouts import FunctionalReadout
from omi.state import FloatArray, Slot, State, StateSchema

from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming_ensemble
from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.readouts import DendriteRisk
from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship.readouts import AggregateHardness, BendAngleAtReferenceGeometry
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

from tests.conftest import ObservationRecorder

HEATING_CONTROL = Control(0.0, 1.0, lambda t: np.array([8.0]))
TRANSFER_CONTROL = Control(0.0, 0.3, lambda t: np.array([1.0]))
TRUE_CHAIN = Chain((Segment(HEATING_AND_SOAK, HEATING_CONTROL), Segment(TRANSFER, TRANSFER_CONTROL)))
"""The ground-truth simulator: fixed control, since neither declared
readout responds to it (see module docstring) -- only the incoming
composition is swept."""

_BASE_VALUES = {
    "prior_deformation": 5.0,
    "prior_grain_size": 20.0,
    "substructure_density": 3.0,
    "inclusion_content": 1.0,
    "accumulated_hardening": 0.0,
    "levelling_field": 0.0,
    "coating_thickness": 10.0,
}
_ORDER = tuple(n for _, n, _ in FLAGSHIP_SCHEMA.components)

CARRIER_SCHEMA = StateSchema(((Slot.M, "inclusion_content", 1), (Slot.M, "grain_size", 1)))
"""A minimal 2-dimensional carrier schema for the learned operator: its
"state" is directly the two swept composition features, not the full
flagship state -- the comparison is about predicting the declared readout,
not reconstructing full-state fidelity."""

DUMMY_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))
GRAIN_SIZE_RANGE = (14.0, 26.0)
FIXED_GRAIN_SIZE_FOR_INVERSION = 20.0


def make_incoming(inclusion_content: float, grain_size: float) -> State:
    values = dict(_BASE_VALUES)
    values["inclusion_content"] = inclusion_content
    values["prior_grain_size"] = grain_size
    return State(FLAGSHIP_SCHEMA, np.array([values[n] for n in _ORDER]))


def true_final_state(incoming: State) -> State:
    state = incoming
    for segment in TRUE_CHAIN.segments:
        state = segment.operator.step(state, segment.control)
    return state


def true_readout_value(inclusion_content: float, grain_size: float, readout: FunctionalReadout) -> float:
    return float(readout.evaluate(true_final_state(make_incoming(inclusion_content, grain_size)))[0])


@dataclass(frozen=True)
class SweepConfig:
    n_records: int
    window_width: float
    noise_std: float
    readout: FunctionalReadout
    readout_name: str


@dataclass(frozen=True)
class ModelScores:
    rmse: float
    hit_rate: float


@dataclass(frozen=True)
class ConfigResult:
    config: SweepConfig
    ridge: ModelScores
    gbt: ModelScores
    deeponet: ModelScores


def _generate_records(config: SweepConfig, rng: np.random.Generator) -> tuple[FloatArray, FloatArray]:
    inclusion = rng.uniform(1.0 - config.window_width / 2, 1.0 + config.window_width / 2, size=config.n_records)
    grain_size = rng.uniform(*GRAIN_SIZE_RANGE, size=config.n_records)
    y_true = np.array([true_readout_value(i, g, config.readout) for i, g in zip(inclusion, grain_size)])
    y_noisy = y_true + rng.normal(0.0, config.noise_std, size=config.n_records)
    x = np.stack([inclusion, grain_size], axis=1)
    return x, y_noisy


def _test_set(config: SweepConfig, n_test: int = 200) -> tuple[FloatArray, FloatArray]:
    rng = np.random.default_rng(12345)  # fixed: independent of the training seed, shared across configs
    inclusion = rng.uniform(1.0 - config.window_width / 2, 1.0 + config.window_width / 2, size=n_test)
    grain_size = rng.uniform(*GRAIN_SIZE_RANGE, size=n_test)
    y_true = np.array([true_readout_value(i, g, config.readout) for i, g in zip(inclusion, grain_size)])
    return np.stack([inclusion, grain_size], axis=1), y_true


def run_config(
    config: SweepConfig,
    seed: int,
    tolerance: float,
    n_epochs: int = 300,
    hidden_dim: int = 16,
    n_inverse_targets: int = 8,
) -> ConfigResult:
    """Fit all three models at *config*'s record count/window/noise, score
    forward RMSE on a fixed held-out test set, and score inverse-design hit
    rate over a grid at a fixed grain size (ADR-039)."""
    rng = np.random.default_rng(seed)
    x_train, y_noisy = _generate_records(config, rng)
    x_test, y_test_true = _test_set(config)

    ridge = RidgeRegressor(alpha=1.0)
    ridge.fit(x_train, y_noisy)
    ridge_rmse = root_mean_squared_error(ridge.predict(x_test), y_test_true)

    gbt = GradientBoostedTreeRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
    gbt.fit(x_train, y_noisy)
    gbt_rmse = root_mean_squared_error(gbt.predict(x_test), y_test_true)

    y_mean = float(y_noisy.mean())
    records = [
        TrainingRecord(
            str(i),
            x_train[i],
            (DUMMY_CONTROL,),
            (x_train[i], np.array([y_noisy[i] - y_mean, y_noisy[i] - y_mean])),
        )
        for i in range(config.n_records)
    ]
    params = init_deeponet_params(
        state_dim=2, control_dim=1, rng=np.random.default_rng(seed + 1), latent_dim=hidden_dim, hidden_dim=hidden_dim
    )
    params, _report = train_deeponet(params, records, np.random.default_rng(seed + 2), n_epochs=n_epochs, learning_rate=0.05)

    def deeponet_predict(x: FloatArray) -> FloatArray:
        operator = DeepONetOperator(params)
        out = np.empty(x.shape[0])
        for i in range(x.shape[0]):
            state = State(CARRIER_SCHEMA, x[i])
            out[i] = float(operator.step(state, DUMMY_CONTROL).values[0]) + y_mean
        return out

    deeponet_rmse = root_mean_squared_error(deeponet_predict(x_test), y_test_true)

    grid = np.linspace(1.0 - config.window_width / 2, 1.0 + config.window_width / 2, 200)
    true_grid = np.array([true_readout_value(float(v), FIXED_GRAIN_SIZE_FOR_INVERSION, config.readout) for v in grid])
    targets = np.linspace(true_grid.min() + tolerance, true_grid.max() - tolerance, n_inverse_targets)

    def true_fn(inclusion_content: float) -> float:
        return true_readout_value(inclusion_content, FIXED_GRAIN_SIZE_FOR_INVERSION, config.readout)

    grid_features = np.stack([grid, np.full_like(grid, FIXED_GRAIN_SIZE_FOR_INVERSION)], axis=1)
    ridge_hit = inverse_design_hit_rate(grid, ridge.predict(grid_features), targets, true_fn, tolerance)
    gbt_hit = inverse_design_hit_rate(grid, gbt.predict(grid_features), targets, true_fn, tolerance)
    deeponet_hit = inverse_design_hit_rate(grid, deeponet_predict(grid_features), targets, true_fn, tolerance)

    return ConfigResult(
        config,
        ModelScores(ridge_rmse, ridge_hit),
        ModelScores(gbt_rmse, gbt_hit),
        ModelScores(deeponet_rmse, deeponet_hit),
    )


def test_flagships_declared_readouts_do_not_respond_to_the_process_control() -> None:
    """Pins the scoping note in this module's own docstring: AggregateHardness
    and BendAngleAtReferenceGeometry are unchanged across a wide range of
    heating_intensity, confirming the sweep axis had to move to composition."""
    incoming = make_incoming(inclusion_content=1.0, grain_size=20.0)
    hardness = AggregateHardness()
    bend = BendAngleAtReferenceGeometry()
    baseline_hardness = None
    baseline_bend = None
    for heating_intensity in (2.0, 8.0, 14.0):
        control = Control(0.0, 1.0, lambda t: np.array([heating_intensity]))
        chain = Chain((Segment(HEATING_AND_SOAK, control), Segment(TRANSFER, TRANSFER_CONTROL)))
        state = incoming
        for segment in chain.segments:
            state = segment.operator.step(state, segment.control)
        h = float(hardness.evaluate(state)[0])
        b = float(bend.evaluate(state)[0])
        if baseline_hardness is None:
            baseline_hardness, baseline_bend = h, b
        else:
            assert h == baseline_hardness
            assert b == baseline_bend


def test_harness_runs_and_produces_finite_scores_on_a_tiny_configuration(observe: ObservationRecorder) -> None:
    """A small, fast configuration (short of the full sweep's settings) that
    exercises every stage of run_config -- confirms the harness itself is
    correct and CI-exercised, without the full sweep's runtime."""
    config = SweepConfig(n_records=30, window_width=5.0, noise_std=0.5, readout=AggregateHardness(), readout_name="AggregateHardness")
    result = run_config(config, seed=0, tolerance=0.5, n_epochs=100, hidden_dim=8, n_inverse_targets=4)

    for name, scores in (("ridge", result.ridge), ("gbt", result.gbt), ("deeponet", result.deeponet)):
        observe(f"{name}_rmse", scores.rmse, "finite, >= 0")
        observe(f"{name}_hit_rate", scores.hit_rate, "finite, in [0, 1]")
        assert np.isfinite(scores.rmse) and scores.rmse >= 0.0
        assert 0.0 <= scores.hit_rate <= 1.0


# ---------------------------------------------------------------------------
# Contrast: the control-inverse sweep (Core §5), attempted after confirming
# sensitivity. CONTRAST_DECLARATION's control_space declares no NUMERIC
# U_adm (only prose: "bounded by manufacturer charge/discharge limits") --
# U_ADM and U_TRUST below are this investigation's own stated assumptions,
# not values drawn from the framework or the domain's own declared
# interface, flagged explicitly rather than presented as given.
# ---------------------------------------------------------------------------

U_ADM = (0.2, 5.0)
"""Declared, stated assumption (this investigation only): the admissible
current range. No numeric bound exists in CONTRAST_DECLARATION to draw
from -- see E-26 (docs/V1.4-EDITS.md) on item 2's own missing sensitivity
requirement, and note separately that neither implemented domain declares
U_adm numerically at all."""

U_TRUST = (1.0, 3.0)
"""Declared, stated assumption: the region training data is drawn from --
Core §5's U_trust, "restrict to where the surrogate is calibrated." Targets
requiring a current outside this range but still within U_ADM test
extrapolation past the trust region -- "the optimiser is an adversary that
seeks the region where the surrogate is most confidently wrong" (Core §5)."""

N_CYCLES = 5
CONTRAST_NOISE_STD = 0.1


def _contrast_incoming_state() -> State:
    rng = np.random.default_rng(0)
    return contrast_incoming_ensemble(1, rng)[0]


_CONTRAST_INCOMING = _contrast_incoming_state()


def contrast_true_final_state(current: float) -> State:
    control = Control(0.0, 1.0, lambda t: np.array([current]))
    state = _CONTRAST_INCOMING
    for _ in range(N_CYCLES):
        state = CYCLING.step(state, control)
    return state


def contrast_true_risk(current: float) -> float:
    return float(DendriteRisk().evaluate(contrast_true_final_state(current))[0])


CONTRAST_CARRIER_SCHEMA = StateSchema(((Slot.M, "current", 1),))


@dataclass(frozen=True)
class ContrastConfig:
    n_records: int


@dataclass(frozen=True)
class ContrastResult:
    config: ContrastConfig
    ridge: "ContrastModelScores"
    gbt: "ContrastModelScores"
    constrained_operator: "ContrastModelScores"


@dataclass(frozen=True)
class ControlSearchDiagnostic:
    """One `gradient_control_search` outcome (ADR-040), kept alongside the
    raw hit/miss score rather than collapsed into it: Core §5 treats the
    trust region as a first-class check ("the optimiser is an adversary
    that seeks the region where the surrogate is most confidently wrong"),
    so whether the returned control lies inside U_TRUST is reported for
    every target, mirroring Spec §7.3/ADR-033's ordered
    diagnose_infeasibility discipline applied to a single-target search."""

    target: float
    chosen_control: float
    achieved: float
    within_trust_region: bool
    hit: bool


@dataclass(frozen=True)
class ContrastModelScores:
    rmse_in_trust: float
    rmse_extrapolation: float
    hit_rate_in_trust: float
    hit_rate_extrapolation: float
    search_diagnostics_in_trust: tuple[ControlSearchDiagnostic, ...] = ()
    search_diagnostics_extrapolation: tuple[ControlSearchDiagnostic, ...] = ()
    """Populated only for the constrained-operator contestant (ADR-040):
    Ridge/GBT are inverted by inverse_design_hit_rate's grid search
    (ADR-039, unchanged), which has no single-target search trajectory to
    report a per-target trust-region diagnostic for."""


@dataclass(frozen=True)
class ConstrainedMonotoneOperator:
    """The re-run operator-graph contestant (ADR-040). DendriteRisk vs.
    current is monotone by construction
    (`test_contrasts_dendrite_risk_responds_to_the_declared_control`), so
    this contestant makes that monotonicity a *hard* structural constraint
    (Core §4.1/Spec §2.2; CLAUDE.md invariant 5), using
    `constraints.monotone_increasing` directly, rather than leaving it to a
    flexible regressor to approximate from noisy data. `raw_params` (K
    values, wholly unconstrained) and `initial` pass through
    `monotone_increasing` (itself `positive` + a cumulative sum) to produce
    a risk *profile* over `grid` that cannot represent a non-monotone
    function for any parameter values whatsoever. Prediction at an
    arbitrary current is linear interpolation between the two nearest grid
    points, which preserves the monotonicity guarantee exactly."""

    grid: FloatArray
    raw_params: FloatArray
    initial: float

    def profile(self) -> FloatArray:
        return monotone_increasing(self.raw_params, self.initial)

    def _bracket(self, current: float) -> tuple[int, float, float]:
        k = self.grid.shape[0]
        j = int(np.clip(np.searchsorted(self.grid, current) - 1, 0, k - 2))
        return j, float(self.grid[j]), float(self.grid[j + 1])

    def predict_one(self, current: float) -> float:
        j, x0, x1 = self._bracket(current)
        profile = self.profile()
        frac = (current - x0) / (x1 - x0)
        return float((1.0 - frac) * profile[j] + frac * profile[j + 1])

    def predict(self, x: FloatArray) -> FloatArray:
        profile = self.profile()
        result: FloatArray = np.interp(x[:, 0], self.grid, profile)
        return result

    def slope_at(self, current: float) -> float:
        """`d(predict_one)/d(current)` on the bracketing grid segment --
        exact except at grid points themselves, where the piecewise-linear
        interpolant has a kink; a subgradient there is standard practice
        for the projected gradient descent this feeds
        (`gradient_control_search`, src/omi/inverse.py)."""
        j, x0, x1 = self._bracket(current)
        profile = self.profile()
        return float((profile[j + 1] - profile[j]) / (x1 - x0))


def train_constrained_monotone_operator(
    grid: FloatArray,
    x_train: FloatArray,
    y_train: FloatArray,
    rng: np.random.Generator,
    n_epochs: int = 300,
    learning_rate: float = 0.05,
) -> ConstrainedMonotoneOperator:
    """Plain gradient descent (no torch, CLAUDE.md §8; matching ADR-029's
    from-scratch precedent) on squared error, using
    `constraints.monotone_increasing_jacobian`'s exact gradient chained
    through the interpolation weights (ADR-040) -- no automatic
    differentiation framework needed since the whole forward map (monotone
    reparameterisation, then linear interpolation) has a closed-form
    Jacobian already supplied by constraints.py.

    `raw_params` is initialised strongly negative (not near zero): `positive`
    is `softplus`, and `softplus(0) ~= 0.693`, not 0, so a near-zero
    initialisation makes every grid cell contribute a nontrivial default
    increment to the monotone cumulative sum whether or not training data
    ever touches it -- discovered by direct diagnosis of an early version of
    this function, which produced a nonsensical extrapolation blow-up from
    this exact cause (grid cells beyond U_TRUST are never bracketed by a
    training point, so their raw parameter never receives a gradient and
    stays at whatever it was initialised to). Initialising strongly negative
    makes `positive(raw_params) ~= 0` by default: an untrained cell
    contributes ~0 to the cumulative sum, so the profile is flat past
    wherever training evidence ends, in either direction -- "no evidence of
    further increase" under a constraint that still forbids decrease,
    rather than an artifact of initialisation.

    That negative initialisation sits in `positive_grad`'s (`sigmoid`)
    near-flat region (`sigmoid(-6) ~= 0.0025`), so plain gradient descent
    barely moves the trained-region parameters at all within a few hundred
    epochs -- diagnosed directly (a fitted profile that stayed almost flat
    across the whole grid, including inside U_TRUST, instead of tracking
    the training data's own near-linear rise). Adam (from-scratch, no
    torch, matching ADR-029/learning.py's existing precedent) is used
    instead of plain SGD for exactly this reason: it rescales each
    parameter's step by that parameter's own past gradient magnitude, so a
    parameter starting in a near-flat region of `sigmoid` still takes a
    learning-rate-sized step rather than a vanishing one."""
    k = grid.shape[0]
    raw_params = rng.normal(-6.0, 0.1, size=k)
    initial = float(y_train.mean())

    x_flat = x_train[:, 0]
    j_idx = np.clip(np.searchsorted(grid, x_flat) - 1, 0, k - 2)
    x0 = grid[j_idx]
    x1 = grid[j_idx + 1]
    frac = (x_flat - x0) / (x1 - x0)
    n = x_flat.shape[0]

    beta1, beta2, eps = 0.9, 0.999, 1e-8
    m_raw, v_raw = np.zeros(k), np.zeros(k)
    m_initial, v_initial = 0.0, 0.0

    for t in range(1, n_epochs + 1):
        profile = monotone_increasing(raw_params, initial)
        jac = monotone_increasing_jacobian(raw_params)
        pred = (1.0 - frac) * profile[j_idx] + frac * profile[j_idx + 1]
        residual = pred - y_train
        d_pred_d_raw = (1.0 - frac)[:, None] * jac[j_idx] + frac[:, None] * jac[j_idx + 1]
        grad_raw = (2.0 / n) * (residual[:, None] * d_pred_d_raw).sum(axis=0)
        grad_initial = (2.0 / n) * residual.sum()

        m_raw = beta1 * m_raw + (1.0 - beta1) * grad_raw
        v_raw = beta2 * v_raw + (1.0 - beta2) * grad_raw**2
        m_raw_hat = m_raw / (1.0 - beta1**t)
        v_raw_hat = v_raw / (1.0 - beta2**t)
        raw_params = raw_params - learning_rate * m_raw_hat / (np.sqrt(v_raw_hat) + eps)

        m_initial = beta1 * m_initial + (1.0 - beta1) * grad_initial
        v_initial = beta2 * v_initial + (1.0 - beta2) * grad_initial**2
        m_initial_hat = m_initial / (1.0 - beta1**t)
        v_initial_hat = v_initial / (1.0 - beta2**t)
        initial = initial - learning_rate * m_initial_hat / (np.sqrt(v_initial_hat) + eps)

    return ConstrainedMonotoneOperator(grid=grid, raw_params=raw_params, initial=initial)


def _contrast_apparatus() -> ApparatusParameterization:
    """U_adm as a box (ADR-032's existing shape) for gradient_control_search
    -- the declared, stated assumption U_ADM above, not a value the domain
    itself supplies numerically (see E-27, docs/V1.4-EDITS.md)."""

    def to_control(params: FloatArray) -> Control:
        return Control(0.0, 1.0, lambda t: np.array([float(params[0])]))

    return ApparatusParameterization(to_control=to_control, parameter_dim=1, bounds=(U_ADM,))


def _gradient_search_hit_rate(
    operator: ConstrainedMonotoneOperator,
    targets: FloatArray,
    true_fn: Callable[[float], float],
    tolerance: float,
    apparatus: ApparatusParameterization,
) -> tuple[float, tuple[ControlSearchDiagnostic, ...]]:
    """Inverts *operator* by `gradient_control_search` (ADR-040) rather than
    grid search, once per target, reporting the trust-region diagnostic for
    each search alongside the raw hit/miss score."""
    diagnostics: list[ControlSearchDiagnostic] = []
    hits = 0
    for target in targets:
        target_value = float(target)

        def forward(u: FloatArray, operator: ConstrainedMonotoneOperator = operator) -> float:
            return operator.predict_one(float(u[0]))

        def forward_grad(u: FloatArray, operator: ConstrainedMonotoneOperator = operator) -> FloatArray:
            return np.array([operator.slope_at(float(u[0]))])

        initial_guess = np.array([(U_ADM[0] + U_ADM[1]) / 2.0])
        u_star = gradient_control_search(forward, forward_grad, target_value, apparatus, initial_guess)
        chosen_control = float(u_star[0])
        achieved = true_fn(chosen_control)
        hit = abs(achieved - target_value) < tolerance
        within_trust = U_TRUST[0] <= chosen_control <= U_TRUST[1]
        diagnostics.append(ControlSearchDiagnostic(target_value, chosen_control, achieved, within_trust, hit))
        hits += int(hit)
    return hits / len(targets), tuple(diagnostics)


CONSTRAINED_OPERATOR_GRID_SIZE = 60
"""K, ADR-040: fixed grid size spanning U_ADM for ConstrainedMonotoneOperator."""


def run_contrast_control_inverse_config(
    config: ContrastConfig, seed: int, tolerance: float, n_epochs: int = 300, hidden_dim: int = 16
) -> ContrastResult:
    """The control-inverse analogue of run_config: train on *config*'s
    record count, drawn from U_TRUST only (a realistic data-collection
    assumption), score forward RMSE separately in-trust and in the
    extrapolation band of U_ADM.

    Ridge and GBT (ADR-039's own baselines) are unchanged: fit exactly as
    before and inverted by inverse_design_hit_rate's grid search over the
    full U_ADM. The operator-graph contestant is rebuilt per ADR-040: a
    ConstrainedMonotoneOperator (hard monotonicity via
    constraints.monotone_increasing, not a soft penalty) inverted by
    gradient_control_search (src/omi/inverse.py, new this ADR) under U_adm,
    with the trust region reported as an active diagnostic on every search
    result rather than folded silently into the hit/miss score. *hidden_dim*
    is accepted for call-site compatibility with the flagship sweep but
    unused here -- the constrained operator's capacity is fixed by
    CONSTRAINED_OPERATOR_GRID_SIZE (ADR-040), not a hidden width.
    """
    del hidden_dim
    rng = np.random.default_rng(seed)
    x_train = rng.uniform(U_TRUST[0], U_TRUST[1], size=(config.n_records, 1))
    y_true_train = np.array([contrast_true_risk(float(c)) for c in x_train[:, 0]])
    y_noisy = y_true_train + rng.normal(0.0, CONTRAST_NOISE_STD, size=config.n_records)

    ridge = RidgeRegressor(alpha=1.0)
    ridge.fit(x_train, y_noisy)
    gbt = GradientBoostedTreeRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
    gbt.fit(x_train, y_noisy)

    constrained_grid = np.linspace(U_ADM[0], U_ADM[1], CONSTRAINED_OPERATOR_GRID_SIZE)
    constrained_operator = train_constrained_monotone_operator(
        constrained_grid, x_train, y_noisy, np.random.default_rng(seed + 1), n_epochs=n_epochs, learning_rate=0.05
    )
    apparatus = _contrast_apparatus()

    test_rng = np.random.default_rng(54321)
    x_in_trust = test_rng.uniform(U_TRUST[0], U_TRUST[1], size=(100, 1))
    y_in_trust = np.array([contrast_true_risk(float(c)) for c in x_in_trust[:, 0]])

    def _extrapolation_draw(n: int, gen: np.random.Generator) -> FloatArray:
        out: list[float] = []
        while len(out) < n:
            c = gen.uniform(U_ADM[0], U_ADM[1])
            if c < U_TRUST[0] or c > U_TRUST[1]:
                out.append(c)
        return np.array(out).reshape(-1, 1)

    x_extrap = _extrapolation_draw(100, test_rng)
    y_extrap = np.array([contrast_true_risk(float(c)) for c in x_extrap[:, 0]])

    def rmse_for(model_predict: Callable[[FloatArray], FloatArray], x: FloatArray, y: FloatArray) -> float:
        return root_mean_squared_error(model_predict(x), y)

    ridge_rmse_in = rmse_for(ridge.predict, x_in_trust, y_in_trust)
    ridge_rmse_ex = rmse_for(ridge.predict, x_extrap, y_extrap)
    gbt_rmse_in = rmse_for(gbt.predict, x_in_trust, y_in_trust)
    gbt_rmse_ex = rmse_for(gbt.predict, x_extrap, y_extrap)
    co_rmse_in = rmse_for(constrained_operator.predict, x_in_trust, y_in_trust)
    co_rmse_ex = rmse_for(constrained_operator.predict, x_extrap, y_extrap)

    grid = np.linspace(U_ADM[0], U_ADM[1], 400)
    risk_trust_lo, risk_trust_hi = contrast_true_risk(U_TRUST[0]), contrast_true_risk(U_TRUST[1])
    in_trust_targets = np.linspace(risk_trust_lo + tolerance, risk_trust_hi - tolerance, 4)
    extrap_targets = np.array(
        [
            (contrast_true_risk(U_ADM[0]) + risk_trust_lo) / 2.0,
            (contrast_true_risk(U_ADM[1]) + risk_trust_hi) / 2.0,
        ]
    )

    def true_fn(current: float) -> float:
        return contrast_true_risk(current)

    ridge_grid = ridge.predict(grid.reshape(-1, 1))
    gbt_grid = gbt.predict(grid.reshape(-1, 1))

    ridge_hit_in = inverse_design_hit_rate(grid, ridge_grid, in_trust_targets, true_fn, tolerance)
    ridge_hit_ex = inverse_design_hit_rate(grid, ridge_grid, extrap_targets, true_fn, tolerance)
    gbt_hit_in = inverse_design_hit_rate(grid, gbt_grid, in_trust_targets, true_fn, tolerance)
    gbt_hit_ex = inverse_design_hit_rate(grid, gbt_grid, extrap_targets, true_fn, tolerance)
    co_hit_in, co_diag_in = _gradient_search_hit_rate(constrained_operator, in_trust_targets, true_fn, tolerance, apparatus)
    co_hit_ex, co_diag_ex = _gradient_search_hit_rate(constrained_operator, extrap_targets, true_fn, tolerance, apparatus)

    return ContrastResult(
        config,
        ContrastModelScores(ridge_rmse_in, ridge_rmse_ex, ridge_hit_in, ridge_hit_ex),
        ContrastModelScores(gbt_rmse_in, gbt_rmse_ex, gbt_hit_in, gbt_hit_ex),
        ContrastModelScores(co_rmse_in, co_rmse_ex, co_hit_in, co_hit_ex, co_diag_in, co_diag_ex),
    )


def test_contrasts_dendrite_risk_responds_to_the_declared_control(observe: ObservationRecorder) -> None:
    """Pins the sensitivity check that had to be verified before attempting
    the control-inverse sweep at all (per instruction): DendriteRisk varies
    substantially and monotonically with current, unlike flagship's two
    declared readouts."""
    values = [contrast_true_risk(c) for c in (0.2, 1.0, 3.0, 5.0)]
    observe("dendrite_risk_at_0.2_1.0_3.0_5.0", values, "strictly increasing, not constant")
    assert values == sorted(values)
    assert values[0] < values[-1]
    assert len(set(round(v, 6) for v in values)) == 4


def test_contrast_control_inverse_harness_runs_and_produces_finite_scores(observe: ObservationRecorder) -> None:
    """A small, fast configuration exercising every stage of
    run_contrast_control_inverse_config."""
    config = ContrastConfig(n_records=20)
    result = run_contrast_control_inverse_config(config, seed=0, tolerance=0.3, n_epochs=100, hidden_dim=8)
    for name, scores in (("ridge", result.ridge), ("gbt", result.gbt), ("constrained_operator", result.constrained_operator)):
        observe(f"contrast_{name}_rmse_in_trust", scores.rmse_in_trust, "finite, >= 0")
        observe(f"contrast_{name}_rmse_extrapolation", scores.rmse_extrapolation, "finite, >= 0")
        assert np.isfinite(scores.rmse_in_trust) and scores.rmse_in_trust >= 0.0
        assert np.isfinite(scores.rmse_extrapolation) and scores.rmse_extrapolation >= 0.0
        assert 0.0 <= scores.hit_rate_in_trust <= 1.0
        assert 0.0 <= scores.hit_rate_extrapolation <= 1.0

    for diag in result.constrained_operator.search_diagnostics_extrapolation:
        assert U_ADM[0] <= diag.chosen_control <= U_ADM[1]
