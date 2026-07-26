"""Known-latent-trajectory oracle test: docs/ROADMAP.md M5 exit gate —
"Oracle with a known latent trajectory: smoother recovers it within stated
intervals" — plus the M5 deliverable "demonstrate a latent variable that no
instrument measures becoming *inferred* — closing the loop with M3's
classification."
"""

from __future__ import annotations

import numpy as np

from omi.assimilate import run_filter, smooth
from omi.observability import (
    Triage,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.state import Metric, Slot, State

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_latent_trajectory import KnownLatentTrajectoryOracle


def test_known_latent_trajectory_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownLatentTrajectoryOracle(), Oracle)


def test_smoother_recovers_the_hidden_trajectory_within_three_sigma(observe: ObservationRecorder) -> None:
    """M5 exit gate: the smoother's posterior mean for the never-observed
    ``hidden`` component must lie within a stated (3-sigma) interval of the
    truth at every chain index, even though the prior ensemble (M3's
    `Ensemble`) is centred far from it."""
    oracle = KnownLatentTrajectoryOracle()
    rng = np.random.default_rng(0)
    obs = oracle.observations(rng)
    initial = oracle.initial_ensemble(300, rng)
    truth = oracle.truth()

    filter_result = run_filter(oracle.chain, initial, obs, rng)
    smoothed = smooth(filter_result, obs)

    per_index_error_in_sigma = []
    for k in range(oracle.n_steps + 1):
        estimate = smoothed[k].component(Slot.Z, "hidden")
        mean, std = estimate.mean(), estimate.std()
        per_index_error_in_sigma.append(float(abs(mean - truth[k]) / std))
        assert abs(mean - truth[k]) < 3 * std, (
            f"index {k}: smoothed mean {mean} is more than 3 sigma ({3*std}) "
            f"from truth {truth[k]}"
        )
    observe("per_index_error_in_sigma", per_index_error_in_sigma, "all < 3.0")


def test_smoother_beats_the_raw_prior_at_the_unobserved_initial_index(observe: ObservationRecorder) -> None:
    """The initial ``hidden`` prior (mean 0, far from the truth of 4.0) is
    uninformed by construction; only retrospective smoothing through later
    ``v`` observations can correct it (Core §3.8: "retrospective inference...
    is the correct setting for latent-variable identifiability"). Assert an
    order-of-magnitude reduction in error, not a specific number
    (CLAUDE.md §7: qualitative claims, not printed figures)."""
    oracle = KnownLatentTrajectoryOracle()
    rng = np.random.default_rng(1)
    obs = oracle.observations(rng)
    initial = oracle.initial_ensemble(300, rng)
    truth = oracle.truth()

    prior_error = abs(initial.component(Slot.Z, "hidden").mean() - truth[0])

    filter_result = run_filter(oracle.chain, initial, obs, rng)
    smoothed = smooth(filter_result, obs)
    smoothed_error = abs(smoothed[0].component(Slot.Z, "hidden").mean() - truth[0])

    observe("prior_error", prior_error, "> smoothed_error * 5")
    observe("smoothed_error", smoothed_error, "< prior_error / 5")
    assert smoothed_error < prior_error / 5


def test_hidden_direction_is_classified_inferred_by_m3_triage(observe: ObservationRecorder) -> None:
    """Closing the loop with M3 (docs/ROADMAP.md M5): using the same
    instrumented-``v``-only design (no sensor ever touches ``hidden``),
    `danger_triage` must label the eigendirection dominated by ``hidden`` as
    `Triage.INFERRED` — identifiable only because the chain model carries
    information forward to a downstream ``v`` observation, never because a
    near-diagonal (same-index) sensor exists."""
    oracle = KnownLatentTrajectoryOracle()
    rng = np.random.default_rng(2)
    initial = oracle.initial_ensemble(300, rng)
    metric = Metric.from_ensemble(initial)
    prior = default_prior_covariance(metric)

    initial_state = State(oracle.schema, initial.particles.mean(axis=0))
    nominal = nominal_trajectory(oracle.chain, initial_state)

    design_observations = oracle.design_observations()
    gramian = compute_gramian(oracle.chain, nominal, time_index=0, observations=design_observations)

    triage = danger_triage(
        oracle.chain, nominal, 0, gramian, prior, [oracle.hidden_readout], design_observations
    )

    hidden_dominated = [d for d in triage.directions if abs(d.eigenvector[1]) > abs(d.eigenvector[0])]
    observe(
        "hidden_dominated_labels",
        [d.label.name for d in hidden_dominated],
        "at least one is INFERRED",
    )
    assert hidden_dominated, "no eigendirection is hidden-dominated"
    assert any(d.label is Triage.INFERRED for d in hidden_dominated)
    for d in hidden_dominated:
        if d.label is Triage.INFERRED:
            assert d.near_diagonal_share is None or d.near_diagonal_share == 0.0
