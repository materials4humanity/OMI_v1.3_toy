"""E-53's fork, measured: what each of the three candidate criteria would report on both
implemented domains, and how each depends on the two undeclared conventions.

**The decision input, not the decision, and not a fix.** `danger_triage` is unchanged;
these readings evaluate the alternative criteria against the same Gramian terms the triage
already computes. ADR-061 (docs/DECISIONS.md) is where the choice is made and why.

The three options and what E-53 records about them:

| # | form | Spec's words it makes exact |
|---|---|---|
| 1 | support test — any near-diagonal contribution earns `observed` | *"only"* |
| 2 | single-term dominance ratio `max_near / max_down` vs declared `ρ` | *"a single term dominates"* |
| 3 | abstention band — refuse to label within a declared band | neither; Core §3.9's refusal discipline |
"""

from __future__ import annotations

import numpy as np

from tests.conftest import ObservationRecorder
from tests.oracles.share_threshold_degeneracy import (
    contrast_option_comparison,
    flagship_option_comparison,
)

LITERAL_DOMINANCE = 1.0
"""`ρ = 1` — the most literal reading of "dominates": strictly greater than everything
downstream. Declared here as one of two readings compared, not as a recommendation."""

MARGINED_DOMINANCE = 1.5
"""`ρ = 1.5` — dominance with headroom. The second reading compared."""

ABSTENTION_BAND = 0.25
"""Half-width on the ratio within which option 3 refuses to label. Declared here for the
comparison; ADR-061 makes it a per-domain declaration rather than a constant."""


def test_option_one_makes_dominates_vacuous_on_a_condition_b_chain(
    observe: ObservationRecorder,
) -> None:
    """**Option 1's cost, measured rather than argued.**

    The support test earns `observed` for any nonzero near-diagonal contribution. On
    contrast that is `True` at every index — including where the near-diagonal share is
    `1/12`, i.e. where 92% of the direction's information accrues downstream. Calling that
    "observed" makes Spec §3.3's word *dominates* carry no content, which is exactly the
    objection E-53 records against option 1 as a sole answer.
    """
    readings = contrast_option_comparison()
    supports = [c.support_observed for c in readings]
    shares = sorted({round(c.share, 6) for c in readings})
    observe("option_one_support_verdicts_on_contrast", supports, "all True")
    observe("shares_at_which_option_one_says_observed", shares, "includes 1/12 -- 8% near-diagonal")

    assert all(supports), "option 1 no longer labels every contrast direction observed"
    assert min(shares) < 0.1, (
        "the smallest share option 1 calls observed is no longer far below the threshold, so "
        "the vacuity objection to option 1 is weaker than recorded"
    )


def test_option_two_removes_the_ladder_and_replaces_a_zero_margin_with_a_real_one(
    observe: ObservationRecorder,
) -> None:
    """**The measured case for option 2, and its honest limit.**

    The share walks `1/12, 1/10, 1/8, 1/6, 1/4, 1/2` across contrast's interior and lands on
    the threshold. The **dominance ratio is `1.0` at every one of those indices**, to within
    floating-point noise — index-independent, because it compares two contributions that are
    equal rather than a sum against a total. So the ladder is an artefact of the share's
    construction and option 2 removes it. (Asserted as a *spread* below `10⁻⁶` rather than as
    exact equality: the ratio of two equal quantities computed through different eigenvector
    projections agrees to about nine figures, not to the last bit, and claiming otherwise
    would overstate the measurement.)

    What option 2 does **not** do is remove a declared number: `ρ` is still declared, and it
    still decides the answer. The honest claim is about the **margin**: the old threshold was
    approached to `1.4×10⁻¹¹`, and the new comparison sits `0.5` away from `ρ = 1.5`.
    """
    readings = contrast_option_comparison()
    ratios = [c.dominance_ratio for c in readings]
    shares = {round(c.share, 6) for c in readings}
    margins = [abs(c.dominance_ratio - MARGINED_DOMINANCE) for c in readings]
    spread = max(ratios) - min(ratios)
    observe("option_two_ratios_on_contrast", sorted({round(r, 9) for r in ratios}), "all 1 to ~1e-9")
    observe("option_two_ratio_spread_across_indices", spread, "< 1e-6 -- index-independent")
    observe("share_values_on_contrast", sorted(shares), "six distinct values -- the ladder")
    observe("option_two_margin_to_rho", min(margins), "~0.5 -- against the share's 1.4e-11")

    assert spread < 1.0e-6, (
        "the dominance ratio varies with the index on contrast, so option 2 does not remove "
        "the ladder after all"
    )
    assert all(abs(r - 1.0) < 1.0e-6 for r in ratios), (
        "the ratio is index-independent but no longer sits at 1, so the equal-contributions "
        "mechanism behind it is not the one recorded"
    )
    assert len(shares) > 1, "the share is no longer a ladder, which would remove the contrast"
    assert min(margins) > 0.4, (
        "option 2's comparison now sits close to the declared dominance factor, so its margin "
        "advantage over the share threshold no longer holds"
    )


def test_the_abstention_fires_exactly_where_the_two_contributions_are_equal(
    observe: ObservationRecorder,
) -> None:
    """**Option 3's content, and why it is the more important half.**

    At the most literal reading of "dominates" — `ρ = 1`, strictly greater than everything
    downstream — contrast's ratio of exactly `1.0` sits *on* the criterion, and option 3
    reports `unresolved` rather than picking a side. That is a true and useful statement:
    the near-diagonal and downstream maxima are equal, so neither label is warranted.

    At `ρ = 1.5` the same reading is decisively `inferred`. So the choice of `ρ` changes the
    answer, and abstention is what makes the `ρ = 1` case honest instead of arbitrary.
    """
    readings = contrast_option_comparison()
    literal = {c.option_two_verdict(LITERAL_DOMINANCE, ABSTENTION_BAND) for c in readings}
    margined = {c.option_two_verdict(MARGINED_DOMINANCE, ABSTENTION_BAND) for c in readings}
    observe("verdicts_at_literal_dominance", sorted(literal), "== ['unresolved']")
    observe("verdicts_at_margined_dominance", sorted(margined), "== ['inferred']")

    assert literal == {"unresolved"}, (
        "the abstention no longer fires at the literal dominance reading, so the equal-maxima "
        "case is being assigned a label again"
    )
    assert margined == {"inferred"}, (
        "the margined reading no longer gives a decisive answer, so rho's effect on the "
        "verdict is not the one recorded"
    )


def test_the_window_still_moves_the_verdict_under_option_two(
    observe: ObservationRecorder,
) -> None:
    """**The partial-repair check, and it fails: option 2 does not eliminate the window.**

    Same chain, same indices, same criterion, three window values: `inferred` at 0 and 1,
    and `observed` for some directions at 2. So `near_diagonal_window` remains a free
    parameter that spans the answer, and any fix that declared the threshold while leaving
    the window undeclared would be a partial repair reported as a whole one.

    What *does* improve is the character of the dependence: at each window the ratio is
    decisive (`~0`, `1`, or `inf`) rather than knife-edge, so the window is a visible
    modelling choice rather than a hidden tie-breaker.
    """
    by_window = {
        window: {c.option_two_verdict(MARGINED_DOMINANCE, ABSTENTION_BAND) for c in contrast_option_comparison(window=window)}
        for window in (0, 1, 2)
    }
    ratios_by_window = {
        window: sorted({float(f"{c.dominance_ratio:.4g}") for c in contrast_option_comparison(window=window)})
        for window in (0, 1, 2)
    }
    observe("option_two_verdicts_by_window", {w: sorted(v) for w, v in by_window.items()}, "0,1 inferred; 2 includes observed")
    observe("option_two_ratios_by_window", ratios_by_window, "~0 / 1 / inf -- decisive at each")

    assert by_window[0] == {"inferred"}
    assert by_window[1] == {"inferred"}
    assert "observed" in by_window[2], (
        "the window no longer moves option 2's verdict, which would mean the window could be "
        "left undeclared after all -- a stronger result than measured"
    )


def test_flagship_is_insensitive_to_both_conventions_because_its_answer_is_structural(
    observe: ObservationRecorder,
) -> None:
    """The other half of the dichotomy, and the reason E-54 is a separate finding.

    On a chain with a declared erasure the ratio is `0` or `inf` at every window and every
    `ρ`: the erasure annihilates downstream sensitivity, so *which* terms supply the
    information has a structural answer that no declared convention affects. The
    observed/inferred distinction is therefore **trivial** here and **vacuous** on contrast,
    and informative on neither — which is a property of the two error-control classes rather
    than of any threshold.
    """
    verdicts = {
        (window, rho): sorted({c.option_two_verdict(rho, ABSTENTION_BAND) for c in flagship_option_comparison(window=window)})
        for window in (0, 1, 2)
        for rho in (LITERAL_DOMINANCE, MARGINED_DOMINANCE)
    }
    ratios = sorted({float(f"{c.dominance_ratio:.4g}") for c in flagship_option_comparison()})
    observe("flagship_option_two_ratios", ratios, "only 0 and inf -- structural")
    observe("flagship_verdicts_by_window_and_rho", {f"w{w}_rho{r}": v for (w, r), v in verdicts.items()}, "stable")

    assert all(ratio in (0.0, float("inf")) for ratio in ratios), (
        "flagship's dominance ratios are no longer purely structural, so the "
        "trivial-versus-vacuous framing of E-54 overstates what is measured"
    )
    for (window, rho), value in verdicts.items():
        assert set(value) <= {"observed", "inferred"}, (
            f"flagship abstains at window={window}, rho={rho}, which would mean its answer is "
            "not structural after all"
        )


def test_nothing_numeric_in_the_repository_consumes_the_label(
    observe: ObservationRecorder,
) -> None:
    """**The blast-radius result that decides the abstention's price.**

    The concern about abstention is that downstream machinery might require a total
    labelling. It does not: in this repository the observed/inferred label feeds **no
    computation**. `value_of_information`, `best_placement`, `worst_case_over_window` and
    `variance_term` are all functions of the Gramian, the prior and the danger scores;
    `dangerous_set()` filters on `DANGEROUS`, which is decided by the influence/uncertainty
    median split and not by the near-diagonal share; and Spec §9.1's OMI-1 line item checks
    that a triage was *reported*, not what it says.

    Checked structurally rather than by reading the source: the same chain's numeric outputs
    are computed at three window values, which change every label, and they do not move.
    """
    from omi.observability import (
        Observation,
        compute_gramian,
        danger_triage,
        default_prior_covariance,
        nominal_trajectory,
        value_of_information,
        worst_case_over_window,
    )
    from omi.state import Metric
    from omi.sufficiency import variance_term
    from omi_domains.contrast.build import build_chain, build_incoming_ensemble
    from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage

    depth = 24
    ensemble = build_incoming_ensemble(200, np.random.default_rng(0))
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    chain = build_chain(n_cycles=depth, current=2.0)
    nominal = nominal_trajectory(chain, ensemble[0])
    sensors = [
        Observation(f"voltage_{j}", TerminalVoltage(), np.array([[0.01]]), time_index=j)
        for j in range(1, depth + 1)
    ]
    index = depth - 2
    """The index where Part 5(1) measured the label flip, so the window genuinely moves the
    labelling here — at an interior index it does not, and the test would prove nothing."""
    gramian = compute_gramian(chain, nominal, index, sensors)
    targets = [DendriteRisk()]

    numeric: dict[int, tuple[float, float, float]] = {}
    labels: dict[int, list[str]] = {}
    for window in (0, 1, 2):
        result = danger_triage(
            chain, nominal, index, gramian, prior, targets, sensors, near_diagonal_window=window
        )
        voi = value_of_information(
            chain, nominal, index, prior, gramian, sensors[-1], targets
        )
        numeric[window] = (
            variance_term(result),
            voi,
            variance_term(worst_case_over_window([result])),
        )
        labels[window] = sorted(d.label.value for d in result.directions)

    observe("labels_by_window", labels, "differ across windows")
    observe("numeric_outputs_by_window", {w: list(v) for w, v in numeric.items()}, "identical across windows")

    assert len(set(tuple(v) for v in labels.values())) > 1, (
        "the labels no longer change with the window, so this test is not exercising the "
        "independence it claims to check"
    )
    assert len(set(numeric.values())) == 1, (
        "a numeric output moved when only the labelling convention changed, so something "
        "downstream does consume the label and abstention has a price this test denies"
    )
