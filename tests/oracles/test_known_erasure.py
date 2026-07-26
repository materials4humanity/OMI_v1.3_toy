"""Known-erasure oracle test: docs/ROADMAP.md M2 exit gate — "measurement
recovers r and the surviving subspace" — and OQ-2's investigation
(docs/COVERAGE.md Part IV, docs/DECISIONS.md), with evidence rather than
prose.
"""

from __future__ import annotations

import numpy as np

from omi.erasure import component_recoverability, measure_erasure
from omi.state import Metric, Slot

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_erasure import KnownErasureOracle


def test_known_erasure_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownErasureOracle(), Oracle)


def test_measured_rank_matches_the_designed_rank(observe: ObservationRecorder) -> None:
    oracle = KnownErasureOracle()
    rng = np.random.default_rng(0)
    ensemble = oracle.build_ensemble(2000, rng)
    metric = Metric.from_ensemble(ensemble)

    measurement = measure_erasure(oracle.operator, ensemble[0], oracle.null_control, metric)
    truth = oracle.truth()

    observe("measured_rank", measurement.rank, "== truth.rank")
    observe("truth_rank", truth.rank, "constructed, not measured")

    assert measurement.rank == truth.rank
    assert measurement.surviving_basis.shape[1] == truth.rank
    assert measurement.erased_basis.shape[1] == oracle.schema.size - truth.rank


def test_surviving_and_erased_subspaces_match_the_designed_directions() -> None:
    """Project each designed-surviving standard basis vector onto the
    *measured* surviving subspace (and each designed-erased one onto the
    measured erased subspace); the projection residual must vanish — i.e.
    the measured subspace really does span the constructed directions, not
    merely have the right dimension."""
    oracle = KnownErasureOracle()
    rng = np.random.default_rng(1)
    ensemble = oracle.build_ensemble(2000, rng)
    metric = Metric.from_ensemble(ensemble)
    measurement = measure_erasure(oracle.operator, ensemble[0], oracle.null_control, metric)
    truth = oracle.truth()

    for i in truth.surviving_indices:
        e_i = np.zeros(oracle.schema.size)
        e_i[i] = 1.0
        basis = measurement.surviving_basis
        projection = basis @ (basis.T @ e_i)
        assert np.linalg.norm(e_i - projection) < 1e-8

    for i in truth.erased_indices:
        e_i = np.zeros(oracle.schema.size)
        e_i[i] = 1.0
        basis = measurement.erased_basis
        projection = basis @ (basis.T @ e_i)
        assert np.linalg.norm(e_i - projection) < 1e-8


def test_oq2_naive_magnitude_heuristic_disagrees_with_recoverability(observe: ObservationRecorder) -> None:
    """OQ-2 (docs/COVERAGE.md Part IV): "a component can lose 85% of its
    magnitude while the residual remains a deterministic function of the
    input, hence still assimilable." Here the small-gain (0.15) component
    loses 97.75% of its *variance* by a naive fraction-retained reading, yet
    is exactly as recoverable (R^2 approx 1) as the untouched component — and
    it is the recoverability measure, not the naive one, that agrees with
    the correct operator-level rank (both call it "surviving").
    """
    oracle = KnownErasureOracle()
    rng = np.random.default_rng(2)
    ensemble = oracle.build_ensemble(2000, rng)
    lifted = oracle.operator.lift(ensemble, oracle.null_control)

    def naive_fraction_of_variance_retained(slot: Slot, name: str) -> float:
        pre_std = ensemble.component(slot, name)[:, 0].std()
        post_std = lifted.component(slot, name)[:, 0].std()
        return float((post_std / pre_std) ** 2)

    naive_full = naive_fraction_of_variance_retained(Slot.M, "surviving_full")
    naive_small = naive_fraction_of_variance_retained(Slot.M, "surviving_small")
    naive_erased = naive_fraction_of_variance_retained(Slot.Z, "erased")

    r2_full = component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.M, "surviving_full")
    r2_small = component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.M, "surviving_small")
    r2_erased = component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.Z, "erased")

    observe("naive_full", naive_full, "> 0.99")
    observe("naive_small", naive_small, "< 0.05")
    observe("naive_erased", naive_erased, "< 0.01")
    observe("r2_full", r2_full, "> 0.999")
    observe("r2_small", r2_small, "> 0.999")
    observe("r2_erased", r2_erased, "< 0.01")
    observe("naive_small_variance_loss_pct", (1.0 - naive_small) * 100.0, "narrative only, not asserted")
    observe("r2_small_minus_naive_small", r2_small - naive_small, "> 0.9")

    # The naive heuristic and the correct measurement agree on the two
    # unambiguous cases...
    assert naive_full > 0.99 and r2_full > 0.999
    assert naive_erased < 0.01 and r2_erased < 0.01

    # ...but sharply disagree on the small-gain component: naive reasoning
    # says "mostly erased" (>95% of variance lost); recoverability agrees
    # with the operator-level rank (measure_erasure counts it in the
    # surviving subspace) and says "fully recoverable."
    assert naive_small < 0.05
    assert r2_small > 0.999
    assert r2_small - naive_small > 0.9
