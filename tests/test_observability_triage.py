"""Danger score, the four-way triage, and the observed/inferred split (Core
§3.8; Spec §3.3). Cites ADR-020 (docs/DECISIONS.md) for the median-split and
near-diagonal-window conventions used here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import (
    Observation,
    Triage,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Metric, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "a", 1), (Slot.M, "b", 1)))
NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))


@dataclass(frozen=True)
class Identity(EvolutionOperator):
    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return state

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.eye(2)


@dataclass(frozen=True)
class Coupling(EvolutionOperator):
    """``a_new = a + b``, ``b_new = b``: b leaks into a's evolution, so a
    downstream sensor on a alone can inform on the (a, b) mix without any
    sensor ever watching b directly."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        a, b = state.values
        return State(state.schema, np.array([a + b, b]))

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.array([[1.0, 1.0], [0.0, 1.0]])


class ReadA(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "a")


class ReadAPlusB(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "a") + state.get(Slot.M, "b")


def _identity_chain() -> Chain:
    return Chain((Segment(Identity(), NULL_CONTROL), Segment(Identity(), NULL_CONTROL)))


def test_unobserved_direction_is_dangerous_when_the_target_depends_on_it() -> None:
    chain = _identity_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    observations = [Observation("sensor_a", ReadA(), np.array([[0.01]]), time_index=2)]
    gramian = compute_gramian(chain, nominal, 0, observations)

    result = danger_triage(chain, nominal, 0, gramian, prior, [ReadAPlusB()], observations)

    by_direction = {tuple(np.round(d.eigenvector, 3)): d for d in result.directions}
    b_direction = by_direction[(0.0, 1.0)]
    a_direction = by_direction[(1.0, 0.0)]
    assert b_direction.label is Triage.DANGEROUS
    # The sensor is two steps downstream of k=0 (not near-diagonal at the
    # default window), so even the well-identified 'a' direction is
    # correctly "inferred," not "observed" (ADR-020).
    assert a_direction.label is Triage.INFERRED


def test_unobserved_direction_is_marginalisable_when_the_target_ignores_it() -> None:
    chain = _identity_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    observations = [Observation("sensor_a", ReadA(), np.array([[0.01]]), time_index=2)]
    gramian = compute_gramian(chain, nominal, 0, observations)

    result = danger_triage(chain, nominal, 0, gramian, prior, [ReadA()], observations)

    by_direction = {tuple(np.round(d.eigenvector, 3)): d for d in result.directions}
    assert by_direction[(0.0, 1.0)].label is Triage.MARGINALISABLE
    # Same reasoning as above: identifiable via a downstream-only sensor.
    assert by_direction[(1.0, 0.0)].label is Triage.INFERRED


def test_downstream_only_sensor_yields_inferred_not_observed() -> None:
    """A direction identifiable *only* through a sensor strictly downstream
    of k, with no near-diagonal observation at all, must be classified
    "inferred" — Core §3.8: "the chain model, not the instrument, is doing
    the work."""
    chain = Chain((Segment(Coupling(), NULL_CONTROL), Segment(Coupling(), NULL_CONTROL)))
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    observations = [Observation("sensor_a_late", ReadA(), np.array([[0.01]]), time_index=2)]
    gramian = compute_gramian(chain, nominal, 0, observations)

    result = danger_triage(chain, nominal, 0, gramian, prior, [ReadA()], observations)

    identifiable_directions = [d for d in result.directions if d.uncertainty < 0.1]
    assert identifiable_directions, "expected at least one identifiable direction"
    for d in identifiable_directions:
        assert d.label is Triage.INFERRED
        assert d.near_diagonal_share is None


def test_a_near_diagonal_sensor_makes_the_same_direction_observed() -> None:
    """Add a sensor exactly at k=0 (in addition to the downstream one); a
    direction that becomes dominated by that near-diagonal term flips to
    "observed"."""
    chain = _identity_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    observations = [
        Observation("sensor_a_now", ReadA(), np.array([[0.01]]), time_index=0),
    ]
    gramian = compute_gramian(chain, nominal, 0, observations)
    result = danger_triage(chain, nominal, 0, gramian, prior, [ReadA()], observations)

    by_direction = {tuple(np.round(d.eigenvector, 3)): d for d in result.directions}
    observed = by_direction[(1.0, 0.0)]
    assert observed.label is Triage.OBSERVED
    assert observed.near_diagonal_share == 1.0
