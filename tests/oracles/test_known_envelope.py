"""M11.2's gate: the extrapolation report recovers a validated envelope known by
construction, surfaces rather than raises off-manifold, distinguishes the two
spaces by the action they imply, and item 6d still refuses the certificate role
(ADR-043, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-32).
"""

from __future__ import annotations

import pytest

from omi.interface import classify_invariant
from omi.state import Slot
from omi.proposed import (
    CertificateRoleRefused,
    ConstitutiveForm,
    InvariantRole,
    InvariantSubItem,
    ValidityAction,
    ValidityBound,
    ValidityRange,
    ValiditySpace,
    assert_certificate_eligible,
    certificate_eligible,
    roles_for,
    worst_extrapolation,
)

from tests.conftest import ObservationRecorder
from tests.oracles.known_envelope import known_envelope_form, truth

# (drive, extent) queries: inside, control-only outside, state-only outside, both.
QUERIES = ((5.0, 1.0), (26.5, 1.4), (6.0, 3.6), (30.0, 5.0))


def test_reported_factor_recovers_the_constructed_envelope(observe: ObservationRecorder) -> None:
    """The estimator must recover the factor the oracle fixed (CLAUDE.md §7).

    Both bounds are checked at every query, not only the binding one, because a
    report that got the binding bound right by luck while mis-scaling the other
    would pass a binding-only check — and the two half-widths differ by 5× here
    precisely so that a factor computed against the wrong bound cannot agree.
    """
    form = known_envelope_form()
    worst_ratios = []
    for drive, extent in QUERIES:
        expected = truth(drive, extent)
        report = form.report({"drive": drive, "extent": extent})

        assert report.factors["drive"] == pytest.approx(expected.control_factor)
        assert report.factors["extent"] == pytest.approx(expected.state_factor)
        assert report.worst_factor == pytest.approx(
            max(expected.control_factor, expected.state_factor)
        )
        assert report.outside_envelope is expected.outside_envelope
        worst_ratios.append(report.worst_factor)

    observe(
        "known_envelope_worst_factors",
        {f"drive={d:g},extent={e:g}": r for (d, e), r in zip(QUERIES, worst_ratios)},
        "each recovered exactly from the constructed half-widths",
    )


def test_the_binding_space_determines_the_practitioner_action(
    observe: ObservationRecorder,
) -> None:
    """The control/state split must be legible in the *output*, not only in the
    declaration (ADR-043): a control-space violation is reachable by Core §5's
    control inverse, a state-space violation is not, and the two call for
    different purchases (`docs/V1.4-EDITS.md` §10).
    """
    form = known_envelope_form()
    actions = {}
    for drive, extent in QUERIES:
        expected = truth(drive, extent)
        report = form.report({"drive": drive, "extent": extent})
        actions[f"drive={drive:g},extent={extent:g}"] = report.action.value

        if not expected.outside_envelope:
            assert report.action is ValidityAction.WITHIN_ENVELOPE
            assert report.binding_space is None
            assert report.actionable_by_control_inverse is False
        elif expected.binding_space is ValiditySpace.CONTROL:
            assert report.action is ValidityAction.CONTROL_INVERSE
            assert report.actionable_by_control_inverse is True
        else:
            assert report.action is ValidityAction.BUY_PHYSICS
            assert report.actionable_by_control_inverse is False

    observe("known_envelope_actions", actions, "one action per query, from the binding space")
    # All three actions must actually occur, or the query set is not exercising
    # the distinction the test claims to check.
    assert set(actions.values()) == {a.value for a in ValidityAction}


def test_a_state_space_violation_is_not_recoverable_by_any_control(
    observe: ObservationRecorder,
) -> None:
    """The asymmetry that makes both spaces necessary (ADR-043): sweeping the
    control across its entire declared window cannot clear a state-space
    violation, because the state bound does not depend on the control.

    This is the property that settles the control-versus-state question by
    elimination rather than preference — a control-only design would report this
    case as recoverable, and it is not.
    """
    form = known_envelope_form()
    off_state = 3.6  # outside [0, 2] by construction
    actions = set()
    for drive in (0.0, 2.5, 5.0, 7.5, 10.0):  # the entire declared control window
        report = form.report({"drive": drive, "extent": off_state})
        actions.add(report.action)

    observe(
        "state_violation_actions_across_full_control_window",
        sorted(a.value for a in actions),
        "must be BUY_PHYSICS at every admissible control",
    )
    assert actions == {ValidityAction.BUY_PHYSICS}


def test_off_manifold_queries_surface_rather_than_raise() -> None:
    """Reported, never enforced (ADR-043 point 2). Refusing would make the
    operator unusable exactly where inverse design must probe, and E-28 is the
    standing evidence that a constraint blocking the optimiser rather than
    informing it composes into a new failure.
    """
    form = known_envelope_form()
    report = form.report({"drive": 1.0e6, "extent": -1.0e6})
    assert report.outside_envelope
    assert report.worst_factor > 1000.0
    # And the form is still evaluable out there — surfaced, not refused.
    value = form.evaluate(1.0e6, -1.0e6)
    assert value.shape == (1,)


def test_a_missing_bound_value_raises_rather_than_being_skipped() -> None:
    """A declared bound silently omitted from a report is a bound whose violation
    cannot be seen — the "diagnostic blind to its own dominant input" shape
    `docs/V1.4-EDITS.md` §6 documents eight times over. So it raises.
    """
    form = known_envelope_form()
    with pytest.raises(ValueError, match="no value supplied"):
        form.report({"drive": 5.0})


def test_a_form_without_a_declared_validity_range_is_rejected() -> None:
    """The load-bearing field is load-bearing (ADR-043): an unbounded form makes
    an unbounded claim, which is the failure the category exists to prevent."""
    with pytest.raises(ValueError, match="declares no validity bounds"):
        ConstitutiveForm(
            name="unbounded",
            evaluate=lambda: None,  # type: ignore[arg-type,return-value]
            parameters={},
            validity=ValidityRange(()),
            provenance="none",
            governs=((Slot.M, "x"),),
        )


def test_chain_level_report_names_the_binding_segment(observe: ObservationRecorder) -> None:
    """Chain composition reports the worst factor **and which segment is
    responsible** (ADR-043 point 3), mirroring Spec §7.3's ordered diagnosis:
    "3.1× outside" without saying where is not actionable (E-06).
    """
    form = known_envelope_form()
    per_segment = {
        "first": form.report({"drive": 5.0, "extent": 1.0}),
        "second": form.report({"drive": 6.0, "extent": 3.6}),
        "third": form.report({"drive": 7.0, "extent": 1.2}),
    }
    chain = worst_extrapolation(per_segment)

    observe(
        "chain_binding_segment",
        {"segment": chain.binding_segment, "worst_factor": chain.worst_factor},
        "the segment carrying the out-of-envelope state bound",
    )
    assert chain.binding_segment == "second"
    assert chain.action is ValidityAction.BUY_PHYSICS
    assert chain.worst_factor == pytest.approx(truth(6.0, 3.6).state_factor)


def test_a_fully_in_envelope_chain_names_no_binding_segment() -> None:
    """`None` rather than an arbitrary winner: with nothing outside its range,
    naming a "binding" segment would invent a finding (ADR-043)."""
    form = known_envelope_form()
    chain = worst_extrapolation({"a": form.report({"drive": 5.0, "extent": 1.0})})
    assert chain.binding_segment is None
    assert chain.action is ValidityAction.WITHIN_ENVELOPE
    assert not chain.outside_envelope


def test_empty_chain_report_is_within_envelope() -> None:
    """A chain declaring no forms is not out of envelope (Core §4 item 6d: an
    empty declaration is legal and means generic structure only)."""
    chain = worst_extrapolation({})
    assert chain.binding_segment is None
    assert chain.action is ValidityAction.WITHIN_ENVELOPE


# --- item 6's role-scoped split (E-32) --------------------------------------


def test_item_6d_refuses_the_reachability_certificate_role() -> None:
    """A declared constitutive form cannot serve as a `Φ` (Core §5's output
    contract; Spec §7.1; E-32): it is a functional form for an operator, not a
    scalar functional of state with a provable per-step accumulation bound.
    """
    assert not certificate_eligible(InvariantSubItem.CONSTITUTIVE_FORM)
    assert roles_for(InvariantSubItem.CONSTITUTIVE_FORM) == frozenset(
        {InvariantRole.HARD_CONSTRAINT}
    )
    with pytest.raises(CertificateRoleRefused):
        assert_certificate_eligible(InvariantSubItem.CONSTITUTIVE_FORM)


def test_the_other_three_sub_items_remain_certificate_eligible() -> None:
    """6a–6c are what Spec §7.1's sourcing sentence should draw from (E-32's
    proposed wording), including 6c — the kind §7.1 names and item 6 never
    did."""
    for sub_item in (
        InvariantSubItem.CONSERVATION,
        InvariantSubItem.MONOTONICITY,
        InvariantSubItem.EQUILIBRIUM_LIMITED_FRACTION,
    ):
        assert certificate_eligible(sub_item)
        assert_certificate_eligible(sub_item)


def test_v13_classifier_is_unchanged_and_still_refuses_both_new_kinds() -> None:
    """ADR-043: v1.3's `classify_invariant` refusal is **preserved, not
    relaxed**. It refuses a constitutive form and an equilibrium-limited
    fraction alike, which is correct under v1.3's two categories and is the
    evidence E-32 rests on — the proposed-v1.4 split is a replacement, not a
    loosening.
    """
    for name in ("some_transformation_kinetics_form", "equilibrium_limited_phase_fraction"):
        with pytest.raises(ValueError, match="refuses to guess"):
            classify_invariant(name)
