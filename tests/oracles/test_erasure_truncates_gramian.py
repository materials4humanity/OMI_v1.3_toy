"""Erasure-truncation oracle (docs/ROADMAP.md M3 exit gate): "rank(G_post) <= r"
— Spec §3.2 Proposition 3.2: "If an erasure with Jacobian rank r lies between
k and j, then rank(H'_j Phi_{j,k}) <= r." Reuses the M2 known-erasure oracle's
designed-rank operator (tests/oracles/known_erasure.py), placed as a chain
segment with sensors only downstream of it.
"""

from __future__ import annotations

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import Observation, compute_gramian, nominal_trajectory
from omi.operators import Control
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, State

from tests.oracles.known_erasure import GAINS, SCHEMA, DiagonalErasureOperator


class FullStateReadout(FunctionalReadout):
    """Observes every component directly — as rich a sensor suite as
    possible, so any rank deficiency found downstream is attributable to the
    erasure, not to a weak sensor."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.values

    def jacobian(self, state: State) -> FloatArray:
        return np.eye(state.values.shape[0])


def test_gramian_rank_before_the_erasure_is_bounded_by_its_designed_rank() -> None:
    """A rich (full-state, low-noise) sensor placed strictly *after* the
    erasure still cannot make the pre-erasure Gramian's rank exceed the
    erasure's own designed rank (2 of 3) — Spec §3.2 Prop 3.2."""
    control = Control(0.0, 1.0, lambda t: np.array([0.0]))
    chain = Chain((Segment(DiagonalErasureOperator(), control),))

    initial = State(SCHEMA, np.array([1.0, 1.0, 1.0]))
    nominal = nominal_trajectory(chain, initial)

    sensor = Observation("full_state_sensor", FullStateReadout(), np.eye(3) * 0.0001, time_index=1)
    gramian = compute_gramian(chain, nominal, time_index=0, observations=[sensor])

    designed_rank = int(np.sum(GAINS != 0.0))
    assert designed_rank == 2

    measured_rank = np.linalg.matrix_rank(gramian.total)
    assert measured_rank <= designed_rank
    assert measured_rank == designed_rank  # this rich a sensor should achieve the bound exactly


def test_erased_direction_is_unidentifiable_even_with_a_perfect_downstream_sensor() -> None:
    """Corollary 3.3 (Spec §3.2): directions in ker(F_erasure) are
    unidentifiable from post-erasure data, however good the sensor is."""
    control = Control(0.0, 1.0, lambda t: np.array([0.0]))
    chain = Chain((Segment(DiagonalErasureOperator(), control),))
    initial = State(SCHEMA, np.array([1.0, 1.0, 1.0]))
    nominal = nominal_trajectory(chain, initial)

    sensor = Observation("near_perfect_sensor", FullStateReadout(), np.eye(3) * 1e-8, time_index=1)
    gramian = compute_gramian(chain, nominal, time_index=0, observations=[sensor])

    erased_direction = np.array([0.0, 0.0, 1.0])  # the exactly-zero-gain component
    action = gramian.total @ erased_direction
    assert np.linalg.norm(action) < 1e-6
