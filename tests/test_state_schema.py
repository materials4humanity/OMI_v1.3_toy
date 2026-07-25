"""Tests for omi.state (ADR-011: flat array + schema; ADR-002: the default
metric). Cites Core §3.1 (four-slot schema), §3.2 (spaces), §3.9/Spec §2.5
(metric dependence).
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.state import Ensemble, Metric, Slot, State, StateSchema

SCHEMA = StateSchema(
    (
        (Slot.M, "field_a", 2),
        (Slot.Z, "internal_a", 1),
        (Slot.NU, "nonlocal_a", 1),
        (Slot.GAMMA, "interface_a", 1),
    )
)


def test_schema_size_and_slices() -> None:
    assert SCHEMA.size == 5
    assert SCHEMA.slice_for(Slot.M, "field_a") == slice(0, 2)
    assert SCHEMA.slice_for(Slot.Z, "internal_a") == slice(2, 3)
    assert SCHEMA.names(Slot.M) == ("field_a",)
    assert not SCHEMA.is_empty(Slot.M)


def test_schema_rejects_duplicate_component() -> None:
    with pytest.raises(ValueError):
        StateSchema(((Slot.M, "x", 1), (Slot.M, "x", 1)))


def test_schema_rejects_nonpositive_dimension() -> None:
    with pytest.raises(ValueError):
        StateSchema(((Slot.M, "x", 0),))


def test_state_shape_must_match_schema() -> None:
    with pytest.raises(ValueError):
        State(SCHEMA, np.zeros(3))


def test_state_get_and_with_component_is_immutable() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    s0 = State(SCHEMA, values)
    np.testing.assert_array_equal(s0.get(Slot.M, "field_a"), [1.0, 2.0])

    s1 = s0.with_component(Slot.Z, "internal_a", np.array([99.0]))
    assert s1.get(Slot.Z, "internal_a")[0] == 99.0
    assert s0.get(Slot.Z, "internal_a")[0] == 3.0  # original untouched


def test_ensemble_shape_validation() -> None:
    with pytest.raises(ValueError):
        Ensemble(SCHEMA, np.zeros((3, 4)))  # wrong width


def test_ensemble_from_states_and_component_view() -> None:
    rng = np.random.default_rng(0)
    states = [State(SCHEMA, rng.normal(size=5)) for _ in range(10)]
    ensemble = Ensemble.from_states(SCHEMA, states)
    assert ensemble.n_particles == 10
    assert ensemble.component(Slot.M, "field_a").shape == (10, 2)
    for i, s in enumerate(ensemble):
        np.testing.assert_array_equal(s.values, states[i].values)


def test_metric_default_uses_aleatoric_sigma() -> None:
    rng = np.random.default_rng(1)
    particles = rng.normal(loc=0.0, scale=3.0, size=(5000, SCHEMA.size))
    ensemble = Ensemble(SCHEMA, particles)
    metric = Metric.from_ensemble(ensemble)
    # Qualitative, not decimal (CLAUDE.md §7): the fitted scale should be
    # within a few percent of the true generating sigma at this sample size.
    assert np.all(np.abs(metric.scale - 3.0) < 0.3)


def test_metric_falls_back_to_one_for_zero_variance_component() -> None:
    particles = np.zeros((10, SCHEMA.size))
    particles[:, 0] = 1.0  # constant component: zero empirical variance
    ensemble = Ensemble(SCHEMA, particles)
    metric = Metric.from_ensemble(ensemble)
    assert metric.scale[0] == 1.0


def test_metric_distance_changes_when_a_component_is_rescaled() -> None:
    """A light-touch check of metric dependence (OQ-5's full investigation,
    with recorded evidence, is scheduled for M2 per docs/ROADMAP.md — this
    only confirms the mechanism the investigation will use is present)."""
    rng = np.random.default_rng(2)
    particles = rng.normal(size=(200, SCHEMA.size))
    ensemble = Ensemble(SCHEMA, particles)
    metric = Metric.from_ensemble(ensemble)

    a, b = ensemble[0], ensemble[1]
    d1 = metric.distance(a, b)

    rescaled_particles = particles.copy()
    rescaled_particles[:, 0] *= 100.0  # blow up one component's units
    rescaled_ensemble = Ensemble(SCHEMA, rescaled_particles)
    rescaled_metric = Metric.from_ensemble(rescaled_ensemble)
    a2 = Ensemble(SCHEMA, rescaled_particles)[0]
    b2 = Ensemble(SCHEMA, rescaled_particles)[1]
    d2 = rescaled_metric.distance(a2, b2)

    # The *rescaled* metric absorbs the unit change (aleatoric-sigma
    # normalisation), so the normalised distance stays comparable rather than
    # exploding by 100x — this is the point of declaring a metric at all.
    assert d2 < 5 * d1
