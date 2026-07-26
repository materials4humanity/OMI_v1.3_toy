"""Known-insufficiency oracle test: docs/ROADMAP.md M4 exit gate — "deficit
recovers the constructed gap; deficit ≈ 0 when matching on the full state;
the raw statistic demonstrably over-states." Also answers OQ-1
(docs/COVERAGE.md Part IV) with evidence.
"""

from __future__ import annotations

import numpy as np

from omi.sufficiency import ProbeSet, discriminating, sufficiency_deficit
from omi.state import Slot, StateSchema

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_insufficiency import KnownInsufficiencyOracle


def test_known_insufficiency_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownInsufficiencyOracle(), Oracle)


def test_deficit_recovers_the_constructed_gap_for_the_incomplete_description(
    observe: ObservationRecorder,
) -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(0)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_incomplete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)
    truth = oracle.truth()

    observe("deficit_squared", result.deficit_squared, "abs(deficit_squared - truth) / truth < 0.15")
    observe("truth", truth, "constructed, not measured")
    observe("relative_error", abs(result.deficit_squared - truth) / truth, "< 0.15")

    # Qualitative tolerance (CLAUDE.md §7): within 15% of the constructed
    # value at this sample size, not a fixed decimal.
    assert abs(result.deficit_squared - truth) / truth < 0.15


def test_deficit_is_near_zero_when_matching_on_the_full_state(observe: ObservationRecorder) -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(1)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_complete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_complete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)
    truth = oracle.truth()

    observe("deficit_squared", result.deficit_squared, "< 0.05 * truth")
    observe("truth", truth, "constructed, not measured")

    assert result.deficit_squared < 0.05 * truth


def test_raw_statistic_demonstrably_overstates_the_deficit(observe: ObservationRecorder) -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(2)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_incomplete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)

    observe("raw_gap_squared", result.raw_gap_squared, "> deficit_squared")
    observe("deficit_squared", result.deficit_squared, "< raw_gap_squared")
    observe("repeat_variance_term", result.repeat_variance_term, "> 0.0")
    observe("mismatch_correction_term", result.mismatch_correction_term, "> 0.0")

    assert result.raw_gap_squared > result.deficit_squared
    assert result.repeat_variance_term > 0.0
    assert result.mismatch_correction_term > 0.0


def test_oq1_single_probe_direction_gives_the_same_deficit_either_way(observe: ObservationRecorder) -> None:
    """OQ-1's core empirical claim: a genuinely directional hidden variable
    diverges under *both* probes at equal magnitude — running the incomplete
    campaign under "forward" alone recovers essentially the same deficit as
    under "reversed" alone, so "reversed driving only" is not actually true
    of this variable even though it is exactly the kinematic/directional
    type Spec §1.6's table describes."""
    oracle = KnownInsufficiencyOracle()
    rng_fwd = np.random.default_rng(10)
    rng_rev = np.random.default_rng(11)
    n_pairs = 8000

    fwd_a, fwd_b, fwd_diffs = oracle.sample_incomplete_campaign(n_pairs, "forward", rng_fwd)
    fwd_result = sufficiency_deficit(
        fwd_a, fwd_b, fwd_diffs, oracle.response_jacobian_incomplete("forward"),
        oracle.repeat_variance(2000, rng_fwd),
    )

    rev_a, rev_b, rev_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng_rev)
    rev_result = sufficiency_deficit(
        rev_a, rev_b, rev_diffs, oracle.response_jacobian_incomplete("reversed"),
        oracle.repeat_variance(2000, rng_rev),
    )

    ratio = fwd_result.deficit_squared / rev_result.deficit_squared
    observe("forward_deficit_squared", fwd_result.deficit_squared, "ratio vs reversed_deficit_squared in (0.7, 1.3)")
    observe("reversed_deficit_squared", rev_result.deficit_squared, "ratio vs forward_deficit_squared in (0.7, 1.3)")
    observe("ratio", ratio, "0.7 < ratio < 1.3")
    assert 0.7 < ratio < 1.3, "expected comparable deficits under either single probe alone"


def test_oq1_discriminating_signature_separates_kinematic_from_magnitude_type(
    observe: ObservationRecorder,
) -> None:
    """OQ-1's resolution (ADR-022): the symmetric/antisymmetric decomposition
    distinguishes a directional (kinematic) hidden variable from a
    non-directional (magnitude) one, even when a naive single-probe reading
    reports the *same* divergence magnitude for both and so cannot tell them
    apart."""
    oracle = KnownInsufficiencyOracle()
    h_a, h_b = 1.0, 1.6

    kinematic_probes = oracle.probe_set(h_a, h_b)  # antisymmetric by construction

    # A non-directional "magnitude" candidate: same effect regardless of
    # direction, tuned so its single-probe (reversed) divergence matches the
    # kinematic candidate's — a naive reading cannot tell them apart.
    naive_shared_gap = kinematic_probes.reversed_a - kinematic_probes.reversed_b
    magnitude_probes = ProbeSet(
        forward_a=naive_shared_gap, forward_b=0.0, reversed_a=naive_shared_gap, reversed_b=0.0
    )

    naive_signatures = {
        "kinematic": (0.0, kinematic_probes.reversed_a - kinematic_probes.reversed_b),
        "magnitude": (0.0, magnitude_probes.reversed_a - magnitude_probes.reversed_b),
    }
    full_signatures = {
        "kinematic": kinematic_probes.signature,
        "magnitude": magnitude_probes.signature,
    }

    naive_result = discriminating(naive_signatures, tolerance=0.01)
    full_result = discriminating(full_signatures, tolerance=0.01)
    observe("naive_signatures", naive_signatures, "discriminating(...) is False")
    observe("full_signatures", full_signatures, "discriminating(...) is True")
    observe("naive_discriminating", naive_result, "False")
    observe("full_discriminating", full_result, "True")

    assert not naive_result
    assert full_result


def test_augmentation_candidates_are_schema_components() -> None:
    """ADR-023: a candidate is a (Slot, str, dim) naming a schema addition."""
    schema = StateSchema(((Slot.M, "v", 1),))
    candidate = (Slot.Z, "hidden", 1)
    augmented = StateSchema(schema.components + (candidate,))
    assert augmented.size == 2
    assert augmented.names(Slot.Z) == ("hidden",)
