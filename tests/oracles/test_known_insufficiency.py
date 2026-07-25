"""Known-insufficiency oracle test: docs/ROADMAP.md M4 exit gate — "deficit
recovers the constructed gap; deficit ≈ 0 when matching on the full state;
the raw statistic demonstrably over-states." Also answers OQ-1
(docs/COVERAGE.md Part IV) with evidence.
"""

from __future__ import annotations

import numpy as np

from omi.sufficiency import ProbeSet, discriminating, sufficiency_deficit
from omi.state import Slot, StateSchema

from tests.oracles import Oracle
from tests.oracles.known_insufficiency import KnownInsufficiencyOracle


def test_known_insufficiency_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownInsufficiencyOracle(), Oracle)


def test_deficit_recovers_the_constructed_gap_for_the_incomplete_description() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(0)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_incomplete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)
    truth = oracle.truth()

    # Qualitative tolerance (CLAUDE.md §7): within 15% of the constructed
    # value at this sample size, not a fixed decimal.
    assert abs(result.deficit_squared - truth) / truth < 0.15


def test_deficit_is_near_zero_when_matching_on_the_full_state() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(1)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_complete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_complete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)
    truth = oracle.truth()

    assert result.deficit_squared < 0.05 * truth


def test_raw_statistic_demonstrably_overstates_the_deficit() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(2)
    n_pairs = 8000

    response_a, response_b, matched_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
    repeat_variance = oracle.repeat_variance(2000, rng)
    jacobian = oracle.response_jacobian_incomplete("reversed")

    result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)

    assert result.raw_gap_squared > result.deficit_squared
    assert result.repeat_variance_term > 0.0
    assert result.mismatch_correction_term > 0.0


def test_oq1_single_probe_direction_gives_the_same_deficit_either_way() -> None:
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
    assert 0.7 < ratio < 1.3, "expected comparable deficits under either single probe alone"


def test_oq1_discriminating_signature_separates_kinematic_from_magnitude_type() -> None:
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

    assert not discriminating(naive_signatures, tolerance=0.01)
    assert discriminating(full_signatures, tolerance=0.01)


def test_augmentation_candidates_are_schema_components() -> None:
    """ADR-023: a candidate is a (Slot, str, dim) naming a schema addition."""
    schema = StateSchema(((Slot.M, "v", 1),))
    candidate = (Slot.Z, "hidden", 1)
    augmented = StateSchema(schema.components + (candidate,))
    assert augmented.size == 2
    assert augmented.names(Slot.Z) == ("hidden",)
