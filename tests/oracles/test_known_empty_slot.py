"""Known-empty-slot oracle test (docs/ROADMAP.md M10.1): sketch 4
(catalyst under operation, ``docs/SKETCHES.md``) confirmed that
``omi.state.StateSchema``/``omi.interface.diff`` handle a genuinely empty
slot correctly, but explicitly left open whether the *numerical* machinery
downstream of a schema — ``measure_erasure``, ``compute_gramian``,
``danger_triage`` — tolerates a schema where three of four slots are
vacuous, since an interface-only sketch builds no operator to check that
with. This oracle answers it directly: a minimal chain, one full-rank
linear operator, one sensor, one target readout, all on a schema where
``m``, ``z``, and ``ν`` are declared empty and only ``Γ`` (two components)
is occupied.
"""

from __future__ import annotations

import numpy as np

from omi.erasure import component_recoverability, measure_erasure
from omi.observability import compute_gramian, danger_triage, default_prior_covariance, nominal_trajectory
from omi.state import Metric, Slot, State

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_empty_slot import KnownEmptySlotOracle


def test_known_empty_slot_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownEmptySlotOracle(), Oracle)


def test_schema_itself_reports_m_and_nu_and_z_empty() -> None:
    """Sanity check on the oracle's own construction, not the machinery
    under test: confirms this is a genuinely Gamma-only schema before
    asking whether anything downstream copes with it."""
    oracle = KnownEmptySlotOracle()
    assert oracle.schema.is_empty(Slot.M)
    assert oracle.schema.is_empty(Slot.Z)
    assert oracle.schema.is_empty(Slot.NU)
    assert not oracle.schema.is_empty(Slot.GAMMA)
    assert oracle.schema.size == 2


def test_measure_erasure_recovers_the_designed_spectrum_on_a_gamma_only_schema(
    observe: ObservationRecorder,
) -> None:
    """measure_erasure does not assume a populated m/z/nu: it operates on
    the flat state vector generically and recovers the operator's exact,
    known-by-construction singular values."""
    oracle = KnownEmptySlotOracle()
    rng = np.random.default_rng(0)
    ensemble = oracle.build_ensemble(200, rng)
    metric = Metric.from_ensemble(ensemble)
    initial = State(oracle.schema, np.array([1.0, 1.0]))
    segment = oracle.chain.segments[0]

    measurement = measure_erasure(segment.operator, initial, segment.control, metric)

    observe("rank", measurement.rank, "== 2 (full rank, truth().size)")
    observe("spectrum", measurement.spectrum, "== truth() == [1.0, 0.3]")
    assert measurement.rank == 2
    assert np.allclose(measurement.spectrum, oracle.truth())


def test_component_recoverability_runs_on_a_gamma_only_component(observe: ObservationRecorder) -> None:
    """component_recoverability likewise does not assume any component
    lives in a particular slot -- Slot.GAMMA works exactly like Slot.M
    would."""
    oracle = KnownEmptySlotOracle()
    rng = np.random.default_rng(1)
    ensemble = oracle.build_ensemble(200, rng)
    segment = oracle.chain.segments[0]

    r_squared = component_recoverability(segment.operator, ensemble, segment.control, Slot.GAMMA, "surface_state_a")
    observe("component_recoverability", r_squared, "> 0.999 (noiseless deterministic linear map)")
    assert r_squared > 0.999


def test_compute_gramian_runs_on_a_gamma_only_chain(observe: ObservationRecorder) -> None:
    """compute_gramian does not assume a populated m/z/nu either: the
    Gramian's shape and content follow the schema's actual size (2), and
    the sensor's own designed sensitivity (observes surface_state_a only)
    is recovered exactly."""
    oracle = KnownEmptySlotOracle()
    initial = State(oracle.schema, np.array([1.0, 1.0]))
    nominal = nominal_trajectory(oracle.chain, initial)

    gramian = compute_gramian(oracle.chain, nominal, 0, [oracle.sensor])

    observe("gramian_shape", list(gramian.total.shape), "== (2, 2)")
    assert gramian.total.shape == (2, 2)

    # The sensor observes surface_state_a alone, and the operator does not
    # mix components (diagonal), so the Gramian must be exactly rank 1,
    # entirely in the surface_state_a direction -- known by construction.
    expected_direction = np.array([1.0, 0.0])
    action = gramian.total @ expected_direction
    observe("gramian_action_on_designed_direction", action.tolist(), "nonzero, aligned with [1, 0]")
    assert action[0] > 0.0
    assert np.linalg.matrix_rank(gramian.total) == 1


def test_danger_triage_runs_on_a_gamma_only_chain_and_classifies_both_directions(
    observe: ObservationRecorder,
) -> None:
    """danger_triage is the machinery with the most surface area to break
    on an unusual schema (eigendecomposition, sensitivity operator,
    median-split classification) -- it runs to completion and produces a
    valid label for both of this schema's two directions, with no NaN and
    no crash, on a state where three of four slots contributed nothing at
    all to its input.
    """
    oracle = KnownEmptySlotOracle()
    rng = np.random.default_rng(2)
    ensemble = oracle.build_ensemble(200, rng)
    metric = Metric.from_ensemble(ensemble)
    initial = State(oracle.schema, np.array([1.0, 1.0]))
    nominal = nominal_trajectory(oracle.chain, initial)
    gramian = compute_gramian(oracle.chain, nominal, 0, [oracle.sensor])
    prior = default_prior_covariance(metric)

    result = danger_triage(oracle.chain, nominal, 0, gramian, prior, [oracle.target], [oracle.sensor])

    observe("n_directions", len(result.directions), "== 2 (schema.size)")
    assert len(result.directions) == 2

    labels = [d.label.value for d in result.directions]
    observe("labels", labels, "each a valid Triage label, no crash/NaN")
    for d in result.directions:
        assert not np.isnan(d.danger_score)
        assert not np.isnan(d.influence)
        assert not np.isnan(d.uncertainty)

    observe("influence_median", result.influence_median, "finite, nonzero")
    assert np.isfinite(result.influence_median)
