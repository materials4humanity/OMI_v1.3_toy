"""M8 exit gate (docs/ROADMAP.md): "A learned operator passes the same
oracle tests as its analytic counterpart, at stated tolerance... Rollout
curve reported."

A `DeepONetOperator` (`omi.learning`) is trained to approximate the
contrast domain's `CyclingStep` (`omi_domains.contrast.operators.CYCLING`)
— an exact, semigroup-consistent analytic operator that remains the test
oracle throughout (ADR-001, docs/DECISIONS.md). Training uses grouped,
held-out data (`grouped_train_test_split`) so accuracy is checked on groups
the network never saw, never on training data.
"""

from __future__ import annotations

from typing import Iterator

import numpy as np
import pytest

from omi.learning import (
    DeepONetOperator,
    TrainingRecord,
    grouped_train_test_split,
    init_deeponet_params,
    train_deeponet,
)
from omi.operators import Control, semigroup_residual
from omi.state import Metric, State

from omi_domains.contrast.build import build_incoming_ensemble
from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.state import CONTRAST_SCHEMA

N_STEPS = 4
CONTROL = Control(0.0, 1.0, lambda t: np.array([2.0]))
FIRST_HALF = Control(0.0, 0.5, lambda t: np.array([2.0]))
SECOND_HALF = Control(0.5, 1.0, lambda t: np.array([2.0]))

PREDICTION_TOLERANCE = 0.15
"""Stated tolerance (docs/ROADMAP.md M8: "at stated tolerance") for a
held-out one-step prediction against the analytic ground truth, on state
components whose typical scale is ~0.01-4 (`omi_domains/contrast/build.py`)."""


class _Fixture:
    def __init__(
        self,
        learned_operator: DeepONetOperator,
        untrained_operator: DeepONetOperator,
        test_records: list[TrainingRecord],
        probe_state: State,
    ) -> None:
        self.learned_operator = learned_operator
        self.untrained_operator = untrained_operator
        self.test_records = test_records
        self.probe_state = probe_state


@pytest.fixture(scope="module")
def trained() -> Iterator[_Fixture]:
    rng = np.random.default_rng(0)
    n_records = 40
    incoming = build_incoming_ensemble(n_records, rng)

    records = []
    for i in range(n_records):
        state = incoming[i]
        trajectory = [state.values.copy()]
        s = state
        for _ in range(N_STEPS):
            s = CYCLING.step(s, CONTROL)
            trajectory.append(s.values.copy())
        records.append(
            TrainingRecord(
                group_id=f"batch{i}",
                initial_state=state.values.copy(),
                controls=tuple([CONTROL] * N_STEPS),
                true_trajectory=tuple(trajectory),
            )
        )

    train_records, test_records = grouped_train_test_split(records, test_fraction=0.2, rng=np.random.default_rng(1))

    state_dim = CONTRAST_SCHEMA.size
    untrained_params = init_deeponet_params(state_dim, control_dim=1, rng=np.random.default_rng(2), latent_dim=16, hidden_dim=24)

    probe_values = incoming[0].values.copy()
    trained_params, _report = train_deeponet(
        untrained_params,
        train_records,
        rng=np.random.default_rng(3),
        n_epochs=300,
        learning_rate=0.005,
        noise_std=0.01,
        spectral_cap=4.0,
        semigroup_weight=0.05,
        semigroup_probe=(probe_values, CONTROL, FIRST_HALF, SECOND_HALF),
    )

    yield _Fixture(
        learned_operator=DeepONetOperator(trained_params, erasure=False),
        untrained_operator=DeepONetOperator(untrained_params, erasure=False),
        test_records=test_records,
        probe_state=State(CONTRAST_SCHEMA, probe_values),
    )


def test_learned_operator_matches_the_analytic_oracle_on_held_out_groups(trained: _Fixture) -> None:
    """The primary oracle test (ADR-001: analytic operators remain the test
    oracle): one-step predictions on groups never used in training must be
    close to `CyclingStep`'s exact output, at the stated tolerance."""
    assert trained.test_records, "grouped split produced no held-out groups"
    max_error = 0.0
    for record in trained.test_records:
        state = State(CONTRAST_SCHEMA, record.initial_state)
        for k, control in enumerate(record.controls):
            state = trained.learned_operator.step(state, control)
            error = float(np.max(np.abs(state.values - record.true_trajectory[k + 1])))
            max_error = max(max_error, error)

    assert max_error < PREDICTION_TOLERANCE, (
        f"held-out prediction error {max_error:.4f} exceeds the stated tolerance {PREDICTION_TOLERANCE}"
    )


def test_learned_operator_beats_a_naive_identity_baseline_on_held_out_groups(trained: _Fixture) -> None:
    """Sanity check on the demonstration itself: the trained network must
    have learned *something* about `CyclingStep`'s dynamics, not merely
    memorised near-identity behaviour."""
    identity_error = 0.0
    learned_error = 0.0
    n = 0
    for record in trained.test_records:
        state = State(CONTRAST_SCHEMA, record.initial_state)
        for k, control in enumerate(record.controls):
            state = trained.learned_operator.step(state, control)
            learned_error += float(np.sum((state.values - record.true_trajectory[k + 1]) ** 2))
            identity_error += float(np.sum((record.true_trajectory[0] - record.true_trajectory[k + 1]) ** 2))
            n += 1
    assert learned_error < identity_error / 10


def test_semigroup_consistency_training_reduces_the_learned_operators_own_residual(trained: _Fixture) -> None:
    """The semigroup-consistency training term (Spec §2.3) must measurably
    reduce the learned operator's own semigroup residual relative to an
    untrained network of the same architecture — the oracle test M1 already
    established for analytic operators (`tests/test_semigroup.py`), passed
    here at a loosened, stated tolerance rather than floating-point
    precision."""
    untrained_residual = semigroup_residual(trained.untrained_operator, trained.probe_state, CONTROL, t_mid=0.5)
    trained_residual = semigroup_residual(trained.learned_operator, trained.probe_state, CONTROL, t_mid=0.5)

    assert trained_residual < untrained_residual / 3


def _learned_vs_analytic_rollout_curve(
    learned_operator: DeepONetOperator, baseline_state: State, metric: Metric
) -> list[float]:
    """The learned operator's rollout compared against the analytic
    oracle's (ADR-001), at every prefix length — the M8 analogue of
    `omi.conformance.rollout_length_error_curve` (M7), which compares two
    *states* through one chain; here the comparison is between two
    *operators* (learned vs. analytic) applied to the same state, so it is
    computed directly rather than forcing that function's signature.
    """
    analytic_state = baseline_state
    learned_state = baseline_state
    distances = []
    for _ in range(N_STEPS):
        analytic_state = CYCLING.step(analytic_state, CONTROL)
        learned_state = learned_operator.step(learned_state, CONTROL)
        distances.append(metric.distance(analytic_state, learned_state))
    return distances


def test_rollout_length_error_curve_reported_for_the_learned_operator(trained: _Fixture) -> None:
    """docs/ROADMAP.md M8 exit gate: "Rollout curve reported" — the learned
    operator's discrepancy from the analytic oracle at every rollout length,
    never a single terminal number (CLAUDE.md §5 invariant 7), and bounded
    rather than blowing up, checked as an ordering/bound rather than an
    exact figure (CLAUDE.md §7).
    """
    incoming = build_incoming_ensemble(30, np.random.default_rng(5))
    baseline_state = incoming[0]
    # An explicitly declared identity metric (CLAUDE.md §5 invariant 1
    # requires a *declared* metric, not necessarily the ensemble-derived
    # default): the incoming population's own per-component std is a poor
    # normalisation here, since several components (e.g. lithium inventory
    # loss) start clipped at exactly zero across the whole population and
    # only diverge after cycling — a population-derived scale would be
    # tiny relative to the post-rollout range and wildly amplify small
    # absolute errors. Raw Euclidean distance is declared explicitly
    # instead, and is what the stated bound below is set against.
    identity_metric = Metric(CONTRAST_SCHEMA, np.ones(CONTRAST_SCHEMA.size))

    curve = _learned_vs_analytic_rollout_curve(trained.learned_operator, baseline_state, identity_metric)

    assert len(curve) == N_STEPS
    assert all(np.isfinite(d) for d in curve)
    assert max(curve) < 1.0  # loose, stated bound: no blow-up over N_STEPS
