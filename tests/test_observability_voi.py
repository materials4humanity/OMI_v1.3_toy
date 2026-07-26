"""Value of information via Woodbury (Spec §3.4), sensor placement, and
worst-case-over-window (Spec §3.6).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import (
    Observation,
    best_placement,
    compute_gramian,
    default_prior_covariance,
    nominal_trajectory,
    posterior_covariance,
    sensitivity_operator,
    value_of_information,
    worst_case_over_window,
    danger_triage,
)
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Metric, Slot, State, StateSchema

from tests.conftest import ObservationRecorder

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


class ReadA(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "a")


class ReadB(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "b")


class ReadAPlusB(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "a") + state.get(Slot.M, "b")


def _chain() -> Chain:
    return Chain((Segment(Identity(), NULL_CONTROL), Segment(Identity(), NULL_CONTROL)))


def test_woodbury_voi_matches_brute_force_reinversion(observe: ObservationRecorder) -> None:
    chain = _chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    existing = [Observation("sensor_a", ReadA(), np.array([[0.01]]), time_index=0)]
    gramian = compute_gramian(chain, nominal, 0, existing)
    candidate = Observation("sensor_b", ReadB(), np.array([[0.02]]), time_index=0)
    targets = [ReadAPlusB()]

    woodbury = value_of_information(chain, nominal, 0, prior, gramian, candidate, targets)

    augmented_gramian = compute_gramian(chain, nominal, 0, existing + [candidate])
    posterior_before = posterior_covariance(prior, gramian.total)
    posterior_after = posterior_covariance(prior, augmented_gramian.total)
    sensitivity = sensitivity_operator(chain, nominal, 0, targets)
    brute_force = float(np.trace(sensitivity @ (posterior_before - posterior_after) @ sensitivity.T))

    observe("woodbury", woodbury, "abs(woodbury - brute_force) < 1e-9")
    observe("brute_force", brute_force, "abs(woodbury - brute_force) < 1e-9")
    assert abs(woodbury - brute_force) < 1e-9


def test_placement_favours_the_unobserved_component_over_a_redundant_sensor(observe: ObservationRecorder) -> None:
    chain = _chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    existing = [Observation("sensor_a", ReadA(), np.array([[0.01]]), time_index=0)]
    gramian = compute_gramian(chain, nominal, 0, existing)
    targets = [ReadAPlusB()]

    new_component = Observation("sensor_b", ReadB(), np.array([[0.02]]), time_index=0)
    redundant = Observation("sensor_a_again", ReadA(), np.array([[0.02]]), time_index=0)

    best, ratios = best_placement(
        chain, nominal, 0, prior, gramian, [new_component, redundant], {"sensor_b": 1.0, "sensor_a_again": 1.0}, targets
    )

    observe("ratios", ratios, "ratios['sensor_b'] > 10 * ratios['sensor_a_again']")
    assert best.name == "sensor_b"
    assert ratios["sensor_b"] > 10 * ratios["sensor_a_again"]


def test_placement_accounts_for_cost() -> None:
    """A much cheaper, slightly-less-valuable sensor can win on ratio."""
    chain = _chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    gramian = compute_gramian(chain, nominal, 0, [])
    targets = [ReadAPlusB()]

    cheap_but_noisy = Observation("cheap", ReadA(), np.array([[1.0]]), time_index=0)
    expensive_precise = Observation("expensive", ReadA(), np.array([[0.001]]), time_index=0)

    best, ratios = best_placement(
        chain, nominal, 0, prior, gramian, [cheap_but_noisy, expensive_precise], {"cheap": 1.0, "expensive": 1000.0}, targets
    )
    assert best.name == "cheap"


def test_worst_case_over_window_returns_the_most_dangerous_trajectory() -> None:
    """Spec §3.6: report the worst case over an ensemble of nominal
    trajectories, not the nominal point."""
    chain = _chain()
    metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    prior = default_prior_covariance(metric)
    observations = [Observation("sensor_a", ReadA(), np.array([[0.01]]), time_index=0)]

    mild_nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0])))
    mild_gramian = compute_gramian(chain, mild_nominal, 0, observations)
    mild_result = danger_triage(chain, mild_nominal, 0, mild_gramian, prior, [ReadAPlusB()], observations)

    # Same linear (state-independent) dynamics, so the "different trajectory"
    # here differs only in which state it is nominally evaluated at; for
    # this identity operator the Gramian doesn't actually depend on the
    # state, so we construct a genuinely different scenario: a version with
    # no observation at all, which is strictly more dangerous.
    unobserved_gramian = compute_gramian(chain, mild_nominal, 0, [])
    unobserved_result = danger_triage(chain, mild_nominal, 0, unobserved_gramian, prior, [ReadAPlusB()], [])

    worst = worst_case_over_window([mild_result, unobserved_result])
    assert worst is unobserved_result
