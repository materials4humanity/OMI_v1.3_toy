"""Known-ranking-inversion oracle test: docs/ROADMAP.md M6 exit gate —
"Ranking inversion reproduces" (Core §3.6; Spec §4.4, Proposition 4.2).
"""

from __future__ import annotations

from omi.classb import n_eff

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_ranking_inversion import KnownRankingInversionOracle


def test_known_ranking_inversion_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownRankingInversionOracle(), Oracle)


def test_material_a_is_weaker_at_the_thick_process_zone(observe: ObservationRecorder) -> None:
    oracle = KnownRankingInversionOracle()
    thick, _thin = oracle.truth()
    p_a, p_b = oracle.failure_probability("A", thick), oracle.failure_probability("B", thick)
    observe("p_fail_a_thick", p_a, "> p_fail_b_thick")
    observe("p_fail_b_thick", p_b, "< p_fail_a_thick")
    assert p_a > p_b


def test_material_b_is_weaker_at_the_thin_process_zone(observe: ObservationRecorder) -> None:
    oracle = KnownRankingInversionOracle()
    _thick, thin = oracle.truth()
    p_b, p_a = oracle.failure_probability("B", thin), oracle.failure_probability("A", thin)
    observe("p_fail_b_thin", p_b, "> p_fail_a_thin")
    observe("p_fail_a_thin", p_a, "< p_fail_b_thin")
    assert p_b > p_a


def test_the_ranking_genuinely_inverts_between_the_two_thicknesses(observe: ObservationRecorder) -> None:
    """The qualitative claim under test (CLAUDE.md §7: assert orderings, not
    printed figures): the sign of ``P_fail(A) - P_fail(B)`` flips between the
    thick and thin process-zone thickness."""
    oracle = KnownRankingInversionOracle()
    thick, thin = oracle.truth()

    difference_thick = oracle.failure_probability("A", thick) - oracle.failure_probability("B", thick)
    difference_thin = oracle.failure_probability("A", thin) - oracle.failure_probability("B", thin)

    observe("difference_thick", difference_thick, "> 0")
    observe("difference_thin", difference_thin, "< 0")

    assert difference_thick > 0
    assert difference_thin < 0


def test_the_inversion_is_driven_by_dimensional_reduction_not_by_severity_alone(
    observe: ObservationRecorder,
) -> None:
    """Sanity check on the oracle itself: material B's effective count grows
    between the thick and thin zone (Proposition 4.2's reduction engaging as
    the zone thins below its correlation length), while material A's stays
    fixed (its correlation length is smaller than both thicknesses, so it
    never leaves the bulk regime) — the inversion is the reduction's doing,
    not an arbitrary parameter change."""
    oracle = KnownRankingInversionOracle()
    thick, thin = oracle.truth()

    n_eff_a_thick = n_eff(oracle.volume, oracle.correlation_length_a, thick)
    n_eff_a_thin = n_eff(oracle.volume, oracle.correlation_length_a, thin)
    observe("n_eff_a_thick", n_eff_a_thick, "== n_eff_a_thin")
    observe("n_eff_a_thin", n_eff_a_thin, "== n_eff_a_thick")
    assert n_eff_a_thick == n_eff_a_thin

    n_eff_b_thick = n_eff(oracle.volume, oracle.correlation_length_b, thick)
    n_eff_b_thin = n_eff(oracle.volume, oracle.correlation_length_b, thin)
    observe("n_eff_b_thick", n_eff_b_thick, "< n_eff_b_thin")
    observe("n_eff_b_thin", n_eff_b_thin, "> n_eff_b_thick")
    assert n_eff_b_thin > n_eff_b_thick
