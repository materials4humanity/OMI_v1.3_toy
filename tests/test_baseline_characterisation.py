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

import numpy as np

from omi.baseline import (
    GradientBoostedTreeRegressor,
    RidgeRegressor,
    inverse_design_hit_rate,
    root_mean_squared_error,
)
from omi.chain import Chain, Segment
from omi.learning import DeepONetOperator, TrainingRecord, init_deeponet_params, train_deeponet
from omi.operators import Control
from omi.readouts import FunctionalReadout
from omi.state import FloatArray, Slot, State, StateSchema

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
