"""Known-mixing-erasure oracle test: Phase 3.4 (docs/ROADMAP.md), OQ-2's
deferred half (docs/COVERAGE.md Part IV) — "does operator-level rank still
predict per-component influence when the surviving subspace is not
axis-aligned, or is a per-component projection needed as a distinct
diagnostic?"
"""

from __future__ import annotations

import numpy as np

from omi.erasure import component_recoverability, component_surviving_overlap, measure_erasure
from omi.state import Metric, Slot

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_mixing_erasure import KnownMixingErasureOracle


def test_known_mixing_erasure_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownMixingErasureOracle(), Oracle)


def test_measured_rank_and_surviving_subspace_match_the_designed_mix(observe: ObservationRecorder) -> None:
    """Operator-level rank and the surviving-subspace *span* are recovered
    exactly, the same guarantee the diagonal oracle gives — this alone is
    unaffected by mixing, since SVD does not care whether singular vectors
    are axis-aligned."""
    oracle = KnownMixingErasureOracle()
    rng = np.random.default_rng(0)
    ensemble = oracle.build_ensemble(2000, rng)
    metric = Metric.from_ensemble(ensemble)

    measurement = measure_erasure(oracle.operator, ensemble[0], oracle.null_control, metric)
    truth = oracle.truth()

    observe("measured_rank", measurement.rank, "== truth().rank")
    assert measurement.rank == truth.rank

    # Recovered erased direction should match the designed kernel up to sign.
    erased_direction = measurement.erased_basis[:, 0]
    alignment = float(np.abs(np.dot(erased_direction, truth.kernel_direction)))
    observe("erased_direction_alignment_with_designed_kernel", alignment, "> 0.999 (parallel up to sign)")
    assert alignment > 0.999


def test_component_recoverability_gives_no_clean_per_component_answer_for_a_mixing_erasure(
    observe: ObservationRecorder,
) -> None:
    """The M2 finding on the diagonal oracle was clean: R² > 0.999 for every
    surviving component, near 0 for the erased one. Here, none of the three
    named components aligns with a singular direction, so univariate
    recoverability should show *intermediate* values for all three, tracking
    (not identical to, since it's a different quantity — correlation of a
    noiseless linear map, not a geometric overlap) each component's own
    overlap with the surviving subspace rather than a clean survive/erase
    split.
    """
    oracle = KnownMixingErasureOracle()
    rng = np.random.default_rng(1)
    ensemble = oracle.build_ensemble(2000, rng)
    truth = oracle.truth()

    r_squared = {
        "component_a": component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.M, "component_a"),
        "component_b": component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.M, "component_b"),
        "component_c": component_recoverability(oracle.operator, ensemble, oracle.null_control, Slot.Z, "component_c"),
    }
    observe("component_recoverability", r_squared, "all intermediate, none near exactly 0 or 1")

    # None is a clean 0 or 1 -- the diagonal oracle's signature result.
    for name, value in r_squared.items():
        assert 0.05 < value < 0.999, f"{name}: expected an intermediate R^2, got {value} (looks diagonal-clean)"

    # component_c has the largest kernel loading (truth().kernel_direction[2]
    # ~ -0.816 vs ~0.408 for a/b) so it should show the lowest recoverability
    # of the three -- this is the qualitative ordering the framework's own
    # geometry predicts, checked as an ordering (CLAUDE.md §7), not a figure.
    observe(
        "ordering_check",
        (r_squared["component_c"], r_squared["component_a"], r_squared["component_b"]),
        "component_c < component_a and component_c < component_b",
    )
    assert r_squared["component_c"] < r_squared["component_a"]
    assert r_squared["component_c"] < r_squared["component_b"]


def test_component_surviving_overlap_recovers_the_designed_geometry_exactly(observe: ObservationRecorder) -> None:
    """`component_surviving_overlap` (added at Phase 3.4, `src/omi/erasure.py`)
    is a pure geometric projection, needing no ensemble — it recovers the
    designed per-component overlap essentially exactly, unlike
    `component_recoverability`'s noisier, differently-defined correlation
    estimate. This is the distinct diagnostic OQ-2 asked whether mixing
    erasure would need."""
    oracle = KnownMixingErasureOracle()
    rng = np.random.default_rng(2)
    ensemble = oracle.build_ensemble(2000, rng)
    metric = Metric.from_ensemble(ensemble)
    measurement = measure_erasure(oracle.operator, ensemble[0], oracle.null_control, metric)
    truth = oracle.truth()

    overlaps = {
        "component_a": component_surviving_overlap(measurement, oracle.schema, Slot.M, "component_a"),
        "component_b": component_surviving_overlap(measurement, oracle.schema, Slot.M, "component_b"),
        "component_c": component_surviving_overlap(measurement, oracle.schema, Slot.Z, "component_c"),
    }
    observe("component_surviving_overlap", overlaps, "matches truth().component_surviving_overlap closely")

    truth_overlaps = dict(zip(("component_a", "component_b", "component_c"), truth.component_surviving_overlap))
    for name in overlaps:
        assert abs(overlaps[name] - truth_overlaps[name]) < 0.01, (
            f"{name}: measured {overlaps[name]:.4f}, designed {truth_overlaps[name]:.4f}"
        )


def test_operator_level_rank_alone_does_not_predict_per_component_influence_for_mixing_erasure(
    observe: ObservationRecorder,
) -> None:
    """The answer to OQ-2's deferred question, stated directly: operator-
    level rank (a single integer, 2 here) is silent on *which* components
    survive when the erasure mixes — `component_a`/`component_b` retain
    ~83% overlap with the surviving subspace while `component_c` retains
    only ~33%, information rank cannot supply and only a per-component
    projection (`component_surviving_overlap`) recovers. `component_
    recoverability`'s univariate correlation gives a *qualitatively*
    consistent but not quantitatively identical picture (checked in the
    ordering test above) — the two diagnostics are related, not
    interchangeable, and neither is "operator-level rank" alone.
    """
    oracle = KnownMixingErasureOracle()
    truth = oracle.truth()
    observe(
        "component_surviving_overlap_spread",
        truth.component_surviving_overlap,
        "not uniform, not derivable from rank=2 alone",
    )
    # The three overlaps are not all equal -- rank alone (a single number)
    # cannot distinguish which of three components is most affected.
    assert len(set(round(v, 6) for v in truth.component_surviving_overlap)) > 1
