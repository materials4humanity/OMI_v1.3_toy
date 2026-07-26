"""Tests for omi.readouts (ADR-014): FunctionalReadout, weakest_link, and
ConstitutiveReadout. Cites Core §3.5 (readout types) and §3.6 (Class B).
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.operators import Control
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema

from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.readouts import DendriteRisk
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.readouts import AggregateHardness, ExtractHardness

from tests.conftest import ObservationRecorder

SCHEMA = StateSchema(((Slot.M, "x", 1),))


class ClassAReadout(FunctionalReadout):
    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "x")


def test_functional_readout_call_batches_over_ensemble() -> None:
    particles = np.arange(10.0).reshape(10, 1)
    ensemble = Ensemble(SCHEMA, particles)
    readout = ClassAReadout()
    values = readout(ensemble)
    assert values.shape == (10, 1)
    np.testing.assert_array_equal(values[:, 0], np.arange(10.0))


def test_weakest_link_rejects_class_a_readout() -> None:
    readout = ClassAReadout()
    ensemble = Ensemble(SCHEMA, np.ones((10, 1)))
    with pytest.raises(ValueError):
        readout.weakest_link(ensemble, n_sub=5, n_trials=100, rng=np.random.default_rng(0))


def test_weakest_link_distribution_grows_with_n_sub(observe: ObservationRecorder) -> None:
    """Core §3.6: P(rho_V > x) = [P(rho_0 > x)]^N — the max over more
    sub-elements should be stochastically larger (CLAUDE.md §7: qualitative
    orderings, not decimals)."""

    class ClassBReadout(FunctionalReadout):
        readout_class = ReadoutClass.B

        def evaluate(self, state: State) -> FloatArray:
            return state.get(Slot.M, "x")

    rng = np.random.default_rng(1)
    particles = rng.exponential(scale=1.0, size=(5000, 1))
    ensemble = Ensemble(SCHEMA, particles)
    readout = ClassBReadout()

    small_n = readout.weakest_link(ensemble, n_sub=2, n_trials=4000, rng=rng)
    large_n = readout.weakest_link(ensemble, n_sub=50, n_trials=4000, rng=rng)
    observe("small_n_sub_mean", float(small_n.mean()), "< large_n_sub_mean", units="n_sub=2")
    observe("large_n_sub_mean", float(large_n.mean()), "> small_n_sub_mean", units="n_sub=50")
    assert large_n.mean() > small_n.mean()


def test_flagship_type0_and_type1_readouts_agree_by_construction() -> None:
    """AggregateHardness (Type-0) is defined as ExtractHardness (Type-1)
    called with a null control (ADR-014's design note in
    omi_domains/flagship/readouts.py) — this pins that identity."""
    rng = np.random.default_rng(2)
    ensemble = flagship_incoming(5, rng)
    state = ensemble[0]

    functional_value = AggregateHardness().evaluate(state)
    operator = ExtractHardness()(state)
    null_control = Control(0.0, 1.0, lambda t: np.array([0.0]))
    constitutive_value, updated_state = operator.respond(null_control)

    np.testing.assert_array_equal(functional_value, constitutive_value)
    # Zero driving must not accrue hardening (Core §3.5's operator carries z,
    # but a null control is a no-op on that memory).
    np.testing.assert_array_equal(
        updated_state.get(Slot.Z, "accumulated_hardening"),
        state.get(Slot.Z, "accumulated_hardening"),
    )


def test_flagship_constitutive_operator_accrues_hardening_under_real_driving(
    observe: ObservationRecorder,
) -> None:
    rng = np.random.default_rng(3)
    ensemble = flagship_incoming(1, rng)
    state = ensemble[0]
    operator = ExtractHardness()(state)
    driving_control = Control(0.0, 2.0, lambda t: np.array([3.0]))

    _, updated_state = operator.respond(driving_control)
    before = float(state.get(Slot.Z, "accumulated_hardening")[0])
    after = float(updated_state.get(Slot.Z, "accumulated_hardening")[0])
    observe("hardening_before", before, "< hardening_after")
    observe("hardening_after", after, "> hardening_before")
    assert after > before


def test_contrast_dendrite_risk_is_class_b_and_weakest_link_works(observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(4)
    initial = contrast_incoming(100, rng)
    trajectory = contrast_chain(n_cycles=15, current=2.0).rollout(initial)

    readout = DendriteRisk()
    assert readout.readout_class is ReadoutClass.B
    base = readout(trajectory.final)
    assert base.shape == (100, 1)

    worst = readout.weakest_link(trajectory.final, n_sub=10, n_trials=2000, rng=rng)
    observe("base_mean", float(base.mean()), "<= worst_mean")
    observe("worst_mean", float(worst.mean()), ">= base_mean")
    assert worst.mean() >= base.mean()
