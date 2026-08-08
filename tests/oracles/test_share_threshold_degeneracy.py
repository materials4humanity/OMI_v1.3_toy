"""E-48 triage (Part 5(2) §5.2a): the near-diagonal share's value set on both implemented
domains, and the label's dependence on ADR-020's declared window.

The question this answers: is the `1.4×10⁻¹¹` margin Part 5(1) measured a property of
**contrast's construction** or of the **statistic**? The answer is neither of the two the
question offered — it is a property of the statistic's *value set*, which is discrete for
structural reasons on both domains, at opposite extremes. Nothing here fixes it.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import ObservationRecorder
from tests.oracles.share_threshold_degeneracy import (
    CONTRAST_DEPTH,
    OBSERVED_SHARE_THRESHOLD,
    SPEC_CRITERION,
    contrast_label_by_window,
    contrast_share_ladder,
    contrast_term_contributions,
    flagship_constitutive_shares,
    flagship_declared_shares,
    flagship_lengthened_shares,
    predicted_contrast_share,
)


def test_contrasts_share_is_an_exact_rational_predicted_before_it_is_computed(
    observe: ObservationRecorder,
) -> None:
    """**The oracle claim**: contrast's share is `1/(depth − k)` exactly, derivable from the
    chain's structure without forming a Gramian.

    `CyclingStep` advances the two components `TerminalVoltage` reads by state-independent
    constant increments, so every downstream observation's sensitivity to a perturbation at
    `k` is identical, every relevant Gramian term contributes the same quadratic form, and
    the share collapses to a **ratio of term counts**. That is why it lands *exactly* on
    `0.5` rather than near it — and it is generic for the erasure-free additive class, not
    an accident of contrast's numbers.
    """
    ladder = contrast_share_ladder()
    predicted = {r.index: predicted_contrast_share(r.index) for r in ladder}
    errors = {r.index: abs(r.share - predicted[r.index]) for r in ladder}
    observe("spec_criterion_quoted", SPEC_CRITERION, "narrative; the text being operationalised")
    observe("contrast_share_ladder", {r.index: r.share for r in ladder}, "== 1/(24-k) to 1e-9")
    observe("contrast_share_as_fractions", {r.index: r.as_fraction for r in ladder}, "small rationals")
    observe("contrast_predicted_vs_measured_max_error", max(errors.values()), "< 1e-9")

    assert max(errors.values()) < 1.0e-9, (
        "the share is not the closed-form count ratio, so the mechanism behind the exact "
        "threshold landing is not the one recorded"
    )
    assert any(r.index == CONTRAST_DEPTH - 2 for r in ladder)
    on_threshold = [r for r in ladder if r.index == CONTRAST_DEPTH - 2]
    observe("contrast_margins_at_depth_minus_two", [r.margin for r in on_threshold], "< 1e-9")
    assert all(r.margin < 1.0e-9 for r in on_threshold), (
        "the share no longer lands on the threshold at depth-2, which would narrow E-48"
    )


def test_the_two_contributing_gramian_terms_are_exactly_equal(
    observe: ObservationRecorder,
) -> None:
    """The mechanism, measured directly rather than inferred from the share.

    At the index where the label flips, three observations are relevant. The one **at** the
    index contributes exactly zero — `TerminalVoltage` reads a recomputed nonlocal
    component with no sensitivity to the direction in question there — and the two
    downstream contribute **identical** amounts. So the near-diagonal window catches exactly
    one of two equal halves, the share is exactly `1/2`, and which side of ADR-020's strict
    `> 0.5` a direction falls on is decided by the last bits of two mathematically equal
    floats.

    This is stronger than "the margin is small": there is no margin. The quantity *is* the
    threshold.
    """
    contributions, shares = contrast_term_contributions()
    observe("gramian_term_contributions_at_flip_index", contributions.tolist(), "first == 0; last two equal")
    observe("gramian_term_shares_at_flip_index", shares.tolist(), "0, ~0.5, ~0.5")

    assert contributions[0] == 0.0, (
        "the observation at the index now contributes, so the near-diagonal sum is no "
        "longer supplied by a single downstream term"
    )
    nonzero = contributions[1:]
    assert nonzero.size == 2
    relative_difference = abs(nonzero[0] - nonzero[1]) / nonzero.mean()
    observe("relative_difference_between_the_two_terms", relative_difference, "< 1e-9")
    assert relative_difference < 1.0e-9, (
        "the two contributing terms are no longer equal, so the share is not exactly the "
        "threshold and E-48's machine-precision claim narrows to a small-margin claim"
    )


def test_the_label_moves_across_its_whole_range_with_the_declared_window(
    observe: ObservationRecorder,
) -> None:
    """**A second undeclared convention, not just an undeclared threshold.**

    ADR-020's `near_diagonal_window` operationalises Spec §3.3's "`j ≈ k`", and Spec gives
    no basis for choosing it. Same chain, same index, same directions: at window 0 the share
    is `0.0` and both directions are `inferred`; at window 1 it is `0.5` and they split; at
    window 2 it is `1.0` and both are `observed`.

    So the classification is decided by two undeclared quantities, not one, and the window
    spans the entire range of possible answers on its own.
    """
    by_window = contrast_label_by_window()
    summary = {
        window: [(round(r.share, 12), r.label) for r in readings]
        for window, readings in by_window.items()
    }
    observe("label_by_near_diagonal_window", summary, "window 0 -> inferred; 2 -> observed; 1 -> split")

    labels_at = {w: {r.label for r in rs} for w, rs in by_window.items()}
    assert labels_at[0] == {"inferred"}, "window 0 no longer gives a unanimous inferred verdict"
    assert labels_at[2] == {"observed"}, "window 2 no longer gives a unanimous observed verdict"
    assert len(labels_at[1]) == 2, (
        "window 1 no longer splits two equivalent directions, which is the flip E-48 records"
    )


def test_flagship_is_degenerate_at_the_opposite_extreme(observe: ObservationRecorder) -> None:
    """The comparison the triage turned on: flagship's shares are exactly `0.0` or `1.0`.

    `HEATING_AND_SOAK` is a declared erasure operator, so a perturbation's sensitivity to
    downstream observations is either preserved or annihilated — never smoothly divided. The
    margin to the threshold is exactly `0.5` at every index, on the declared chain and on a
    lengthened composition of the same operators alike.

    **So there is no natural discontinuity at `0.5`.** The threshold is arbitrary (ADR-020),
    and the statistic is effectively a boolean on flagship and a rational ladder on contrast.
    Neither domain has any structural feature at `0.5`; contrast lands on it because its
    ladder passes through it, and flagship never approaches it.
    """
    declared = flagship_declared_shares()
    lengthened = flagship_lengthened_shares()
    declared_margins = [r.margin for r in declared]
    lengthened_shares = [r.share for r in lengthened]
    observe("flagship_declared_shares", [r.share for r in declared], "each 0.0 or 1.0")
    observe("flagship_declared_min_margin", min(declared_margins), "== 0.5")
    observe("flagship_lengthened_shares", lengthened_shares, "all far above the threshold")
    observe(
        "flagship_lengthened_min_margin",
        min(r.margin for r in lengthened),
        "> 0.4 -- eleven orders of magnitude above contrast's",
    )
    observe("observed_share_threshold", OBSERVED_SHARE_THRESHOLD, "narrative; ADR-020's declared value")

    assert all(share in (0.0, 1.0) for share in [r.share for r in declared]), (
        "flagship's declared shares are no longer exactly boolean, so the opposite-extreme "
        "half of the triage no longer holds"
    )
    assert min(declared_margins) == 0.5
    assert min(r.margin for r in lengthened) > 0.4, (
        "the lengthened flagship chain now approaches the threshold, which would make the "
        "degeneracy chain-length-dependent rather than erasure-dependent"
    )


def test_the_constitutive_chain_lands_at_flagships_extreme_because_it_declares_an_erasure(
    observe: ObservationRecorder,
) -> None:
    """The third chain, checked because it is the one that declares constitutive forms —
    so it is where an SDL-style validity report would run.

    It lands at flagship's extreme, exactly `0.0`/`1.0`, and the reason is one declared
    property: `CONSTITUTIVE_HEATING_AND_SOAK.is_erasure` is `True`. So the degeneracy
    tracks the **erasure declaration**, not the domain — which is what makes the finding
    predictive rather than descriptive, and what makes it a constraint on the SDL domain's
    design: a discovery domain with an empty erasure inventory sits at contrast's extreme.
    """
    from omi_domains.flagship_constitutive.operators import (
        CONSTITUTIVE_HEATING_AND_SOAK,
        CONSTITUTIVE_TRANSFER,
    )

    readings = flagship_constitutive_shares()
    observe("constitutive_shares", [r.share for r in readings], "each 0.0 or 1.0")
    observe("constitutive_min_margin", min(r.margin for r in readings), "== 0.5")
    observe(
        "constitutive_erasure_flags",
        [CONSTITUTIVE_HEATING_AND_SOAK.is_erasure, CONSTITUTIVE_TRANSFER.is_erasure],
        "first True -- the property the degeneracy tracks",
    )

    assert all(r.share in (0.0, 1.0) for r in readings)
    assert min(r.margin for r in readings) == 0.5
    assert CONSTITUTIVE_HEATING_AND_SOAK.is_erasure, (
        "the constitutive chain no longer declares an erasure, so its landing at flagship's "
        "extreme is not explained by the property recorded here"
    )


def test_the_two_domains_sit_at_opposite_degeneracies_by_eleven_orders_of_magnitude(
    observe: ObservationRecorder,
) -> None:
    """The headline number of the triage, as a single comparison.

    Both domains' shares are discrete for structural reasons. Contrast's ladder passes
    exactly through the threshold; flagship's boolean never comes near it. The answer to
    "construction or statistic" is **the statistic's value set**, and which extreme a domain
    lands at is decided by whether it declares an erasure operator — which is precisely the
    axis Core §7.2 chose the two domains to invert.
    """
    contrast_min = min(r.margin for r in contrast_share_ladder())
    flagship_min = min(r.margin for r in flagship_declared_shares())
    observe("contrast_min_margin", contrast_min, "< 1e-9")
    observe("flagship_min_margin", flagship_min, "== 0.5")
    observe("margin_ratio_flagship_over_contrast", flagship_min / max(contrast_min, 1e-300), "> 1e8")

    assert contrast_min < 1.0e-9
    assert flagship_min > 0.4
    assert flagship_min / contrast_min > 1.0e8, (
        "the two domains' margins are no longer separated by many orders of magnitude, so "
        "the opposite-degeneracies framing overstates what is measured"
    )
