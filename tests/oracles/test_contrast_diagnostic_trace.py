"""Which diagnostics can drive ADR-056's decision loop on contrast, and which cannot —
the Part 5(1) §5.1 measurement, taken without implementing the loop.

The loop is design-only (ADR-056, docs/DECISIONS.md). What is asserted here is the
property that decides its shape: a diagnostic whose reading does not move over a
campaign cannot change a decision, whatever rule is written on top of it. Three of the
four named diagnostics are settled by these traces before any loop exists.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import ObservationRecorder
from tests.oracles.contrast_diagnostic_trace import (
    CAMPAIGN_DEPTH,
    DRIFT_WINDOW,
    drift_null_rate,
    evaluable_observation_modalities,
    terminal_voltage_trajectory,
    triage_trace,
    validity_report_is_available,
)


def test_the_triage_median_split_is_degenerate_on_contrast(observe: ObservationRecorder) -> None:
    """ADR-020's median split cannot classify on this domain, and the reason is
    arithmetic rather than domain-specific.

    Influence is a quadratic form and therefore non-negative. `dendrite_risk` depends on
    two of seven state components, so more than half the eigendirections have influence
    exactly zero, the median *is* zero, and `influence >= influence_median` is a
    tautology — every direction is "influential", and two of the five `Triage` labels
    become unreachable.
    """
    trace = triage_trace()
    observe("influence_medians", trace.influence_medians, "every entry == 0.0")
    observe("distinct_label_sets", sorted({s for s in trace.label_sets}), "narrative; see interior test")

    assert trace.influence_median_is_identically_zero, (
        "the influence median is nonzero somewhere, which would make the median split "
        "non-degenerate and change ADR-056's step 2"
    )
    for labels in trace.label_sets:
        assert "marginalisable" not in labels
        assert "observed_but_irrelevant" not in labels


def test_the_continuous_triage_reading_is_flat_across_the_campaign(
    observe: ObservationRecorder,
) -> None:
    """The total danger score does not move where a decision could act on it.

    The terminal interval is excluded deliberately and the exclusion is the honest part:
    at the last index there is no downstream observation left, the posterior collapses to
    the prior, and the danger score jumps five orders of magnitude for a structural
    reason. A campaign that has ended is not a campaign a decision changes.
    """
    trace = triage_trace()
    observe("total_danger_by_interval", dict(zip(trace.intervals, trace.total_danger)), "interior flat")
    observe("danger_relative_range_interior", trace.danger_relative_range, "< 1e-3")
    observe("dangerous_set_sizes", trace.dangerous_counts, "constant across the campaign")

    assert trace.danger_relative_range < 1.0e-3, (
        "the total danger score varies materially across the interior, so the continuous "
        "reading is decision-relevant after all"
    )
    assert len(set(trace.dangerous_counts)) == 1, "the dangerous set's size changes over the campaign"


def test_the_observed_inferred_split_is_decided_at_machine_precision(
    observe: ObservationRecorder,
) -> None:
    """**The finding this trace was worth running for**, and it is not the one expected.

    The triage's categorical output *does* change over the campaign — at two of thirteen
    sampled intervals. But it does not change because the information changed. ADR-020
    operationalises Spec §3.3's "one near-diagonal Gramian term dominates" as a strict
    `share > 0.5`, with no margin, and on contrast the share passes through 0.5 exactly.
    At that interval two eigendirections whose shares agree to eleven decimal places
    receive **different labels** — one `observed`, one `inferred` — which is a distinction
    Core §3.8 describes as "the chain model, not any instrument, is doing the work".

    So a loop keyed on the labels would not merely fail to fire: it would fire at
    arbitrary intervals, on the sign of a rounding error. That is a worse failure than
    silence, and it is the reason ADR-056's step 2 is keyed on continuous quantities.

    This is Spec §3.3's own diagnostic exhibiting the shape `docs/V1.4-EDITS.md` §6
    documents: a plausible, bounded, categorical answer whose actual determinant is
    invisible in the output.
    """
    trace = triage_trace()
    disagreement = trace.label_disagreement_at_equal_shares
    observe("modal_label_set", trace.modal_label_set, "narrative only")
    observe("intervals_where_label_set_differs", trace.intervals_where_labels_differ, "isolated, not a trend")
    observe("smallest_margin_to_observed_threshold", trace.smallest_threshold_margin, "< 1e-6")
    observe("shares_receiving_different_labels", disagreement, "non-empty; two shares agreeing to ~1e-10")

    assert trace.smallest_threshold_margin < 1.0e-6, (
        "the near-diagonal share never approaches ADR-020's threshold, so the split is "
        "carrying information here and this finding does not apply"
    )
    assert len(disagreement) >= 2, (
        "no interval contains two directions with numerically equal shares and different "
        "labels; the machine-precision finding would then be an over-reading of the margin"
    )
    assert abs(disagreement[0] - disagreement[1]) < 1.0e-6


def test_the_validity_report_diagnostic_is_unavailable_on_this_domain(
    observe: ObservationRecorder,
) -> None:
    """One of ADR-056's four diagnostics cannot fire at all, and not because of the loop.

    Contrast declares no constitutive form, so its operator does not satisfy Spec §2.2's
    proposed `ConstitutivelyConstrained` obligation and there is nothing for an
    extrapolation report to be computed against. A domain can be fully OMI-0 conformant
    and still leave an operational loop with no validity signal — which is a finding about
    what conformance certifies, not about contrast.
    """
    observe("contrast_operator_is_constitutively_constrained", validity_report_is_available(), "False")
    assert not validity_report_is_available(), (
        "contrast's operator now declares constitutive forms, so the validity-report "
        "diagnostic is available and ADR-056's availability table is stale"
    )


def test_the_declared_observation_suite_is_wider_than_the_state_schema_supports(
    observe: ObservationRecorder,
) -> None:
    """The candidate-measurement pool is smaller than the declared suite.

    Contrast declares three observation modalities; the state schema carries a component
    for one of them, and terminal current is a control and therefore known exactly. Surface
    temperature is declarable and not evaluable, so a "commission the temperature sensor"
    action can be named and cannot be costed. Same shape as E-44 one level down: a
    declaration with no backing behind it.
    """
    evaluable, missing = evaluable_observation_modalities()
    observe("evaluable_modalities", evaluable, "len 2 of 3 declared")
    observe("declared_but_unevaluable_modalities", missing, "== ('surface temperature',)")

    assert missing == ("surface temperature",), (
        "the set of declared-but-unevaluable modalities changed, so ADR-056's item-5 "
        "caveat no longer describes the domain"
    )


def test_nothing_declared_stops_the_chain_leaving_physical_validity(
    observe: ObservationRecorder,
) -> None:
    """The evidence behind ADR-056's fourth action having no declared home.

    The declared operator drives its own declared readout negative within a few dozen
    intervals of ordinary cycling, and no item of Core §4's seven bounds it: contrast
    declares no constitutive form and hence no validity range, item 4's catalogue carries
    no specification limits, item 2's admissible set is declared in words rather than
    numbers, and neither declared invariant is violated. A retirement criterion therefore
    has to be declared in the *analysis*, outside anything `omi.interface.diff` can compare
    across domains.
    """
    trajectory = terminal_voltage_trajectory()
    first_negative = int(np.argmax(trajectory < 0.0)) if np.any(trajectory < 0.0) else -1
    observe("terminal_voltage_at_interval_0", float(trajectory[0]), "narrative only")
    observe("terminal_voltage_final", float(trajectory[-1]), "< 0 -- past physical validity")
    observe("first_interval_with_negative_voltage", first_negative, "> 0 and < len(trajectory)")

    assert first_negative > 0, (
        "the declared chain no longer drives its readout negative, so the scope-exit "
        "finding's evidence is stale"
    )
    assert not validity_report_is_available(), "a validity range now exists; the finding narrows"


def test_the_drift_monitor_is_calibrated_per_window_but_its_campaign_aggregate_is_not(
    observe: ObservationRecorder,
) -> None:
    """The one diagnostic that *can* gate ADR-056's loop, with the qualification that
    decides how.

    ADR-026's NIS convention is correctly calibrated here: the mean NIS sits at 1 under a
    correct model and the per-window flag rate is at its nominal level. But
    `DriftReport.any_drift` is a maximum over many windowed tests with no multiplicity
    correction, so it fires on a large fraction of **correctly specified** campaigns. A
    loop keyed on it would derate or commission on a false alarm two campaigns in five.

    Also measured: the two control limits are crossed in comparable numbers, and
    `DriftReport` records **which** nowhere. ADR-056's gate needs that distinction because
    an upward trip (the model is wrong) and a downward trip (the forecast covariance is
    overstated) call for opposite responses.
    """
    rate = drift_null_rate()
    nominal = 1.0 - rate.confidence
    observe("null_arm_mean_nis", rate.mean_nis, "within 10% of 1.0")
    observe("null_arm_per_window_flag_rate", rate.per_window_flag_rate, f"within 3x of nominal {nominal}")
    observe("null_arm_any_drift_rate", rate.any_drift_rate, "> 0.2 -- not a decision-grade trigger")
    observe("null_lower_tail_windows", rate.lower_tail_windows, "both tails materially populated")
    observe("null_upper_tail_windows", rate.upper_tail_windows, "both tails materially populated")

    assert abs(rate.mean_nis - 1.0) < 0.1, (
        "the NIS statistic is not calibrated on this domain, so neither rate below means "
        "what it is being read as"
    )
    assert rate.per_window_flag_rate < 3.0 * nominal, (
        "the per-window false-alarm rate is far above nominal, which would be a defect in "
        "ADR-026's convention rather than in its aggregate"
    )
    assert rate.any_drift_rate > 0.2, (
        "the campaign-level aggregate no longer over-fires on the null arm; if this is a "
        "real improvement, ADR-056's drift gate can be simplified"
    )
    assert min(rate.lower_tail_windows, rate.upper_tail_windows) > 0.2 * max(
        rate.lower_tail_windows, rate.upper_tail_windows
    ), (
        "one control limit accounts for nearly all null-arm trips, so the two-tail "
        "conflation ADR-056 works around would be a smaller problem than recorded"
    )
    observe("drift_window", DRIFT_WINDOW, "narrative only")
    observe("campaign_depth", CAMPAIGN_DEPTH, "narrative only")
