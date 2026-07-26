"""Known-blind-spot oracle test: docs/ROADMAP.md M3 exit gate — "a designed
unobservable direction appears in ker G."
"""

from __future__ import annotations

import numpy as np

from omi.observability import compute_gramian, nominal_trajectory
from omi.state import State

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_blind_spot import KnownBlindSpotOracle


def test_known_blind_spot_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownBlindSpotOracle(), Oracle)


def test_designed_direction_lies_in_the_kernel_of_the_gramian(observe: ObservationRecorder) -> None:
    oracle = KnownBlindSpotOracle()
    initial = State(oracle.schema, np.array([1.0, 2.0, 3.0]))
    nominal = nominal_trajectory(oracle.chain, initial)

    gramian = compute_gramian(oracle.chain, nominal, time_index=0, observations=[oracle.sensor])

    blind_direction = oracle.truth()
    action = gramian.total @ blind_direction
    norm = float(np.linalg.norm(action))
    observe("kernel_action_norm", norm, "< 1e-10")
    assert norm < 1e-10


def test_gramian_rank_is_exactly_two_not_three() -> None:
    """The differencing sensor suite resolves a 2-dimensional subspace
    (differences) and is blind to exactly one direction (common-mode) — the
    Gramian's numerical rank must be 2, not 3."""
    oracle = KnownBlindSpotOracle()
    initial = State(oracle.schema, np.array([1.0, 2.0, 3.0]))
    nominal = nominal_trajectory(oracle.chain, initial)
    gramian = compute_gramian(oracle.chain, nominal, time_index=0, observations=[oracle.sensor])

    assert np.linalg.matrix_rank(gramian.total) == 2


def test_a_direction_orthogonal_to_the_blind_spot_is_not_in_the_kernel(observe: ObservationRecorder) -> None:
    """Sanity check on the oracle itself: (1, -1, 0) is resolved by the
    difference sensor and must NOT be annihilated by the Gramian."""
    oracle = KnownBlindSpotOracle()
    initial = State(oracle.schema, np.array([1.0, 2.0, 3.0]))
    nominal = nominal_trajectory(oracle.chain, initial)
    gramian = compute_gramian(oracle.chain, nominal, time_index=0, observations=[oracle.sensor])

    resolvable_direction = np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0)
    action = gramian.total @ resolvable_direction
    norm = float(np.linalg.norm(action))
    observe("resolved_action_norm", norm, "> 0.1")
    assert norm > 0.1
