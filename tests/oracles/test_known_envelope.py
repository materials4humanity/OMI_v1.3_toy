"""M11.2's gate: the extrapolation report recovers a validated envelope known by
construction, surfaces rather than raises off-manifold, distinguishes the two
spaces by the action they imply, and item 6d still refuses the certificate role
(ADR-043, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-32).
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.interface import classify_invariant
from omi.state import Slot
from omi.proposed import (
    UNBOUNDED,
    CertificateRoleRefused,
    EdgeKind,
    ConstitutiveForm,
    FormKind,
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
from tests.oracles.known_envelope import (
    APPROX_HIGH,
    APPROX_LOW,
    ONE_SIDED_EDGE,
    ONE_SIDED_SCALE,
    known_envelope_form,
    mixed_edge_form,
    one_sided_form,
    one_sided_truth,
    truth,
)

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
    value = form.evaluate({"drive": 1.0e6, "extent": -1.0e6})
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
            name="no_declared_range",
            kind=FormKind.ALGEBRAIC,
            evaluate=lambda values: np.array([0.0]),
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


# --- one-sided windows (amended before M11.3) -------------------------------


def test_one_sided_factor_recovers_the_constructed_rule(observe: ObservationRecorder) -> None:
    """A window declared ``[edge, UNBOUNDED)`` reports ``1 + (edge - value) /
    fitted_scale`` below the edge and exactly ``1.0`` anywhere inside (ADR-043;
    Spec §2.2).

    At least three of the five forms M11.3 declares are one-sided, so this rule
    is load-bearing rather than a corner case: without it, declaring Hall-Petch's
    fine-grain breakdown would require inventing an upper limit its source never
    established.
    """
    form = one_sided_form()
    factors = {}
    for extent in (ONE_SIDED_EDGE + 100.0, ONE_SIDED_EDGE, ONE_SIDED_EDGE - ONE_SIDED_SCALE,
                   ONE_SIDED_EDGE - 3 * ONE_SIDED_SCALE):
        report = form.report({"extent": extent})
        factors[f"{extent:g}"] = report.factors["extent"]
        assert report.factors["extent"] == pytest.approx(one_sided_truth(extent))

    observe("one_sided_factors", factors, "1 + (edge - value)/fitted_scale, flat 1.0 inside")
    # Exactly 1.0 at the edge and inside; the boundary means the same thing as it
    # does for a two-sided window, which is why outside_envelope needs no special case.
    assert form.report({"extent": ONE_SIDED_EDGE}).factors["extent"] == pytest.approx(1.0)
    assert not form.report({"extent": ONE_SIDED_EDGE + 100.0}).outside_envelope
    assert form.report({"extent": ONE_SIDED_EDGE - 0.5}).outside_envelope


def test_a_one_sided_bound_has_no_centre_and_says_so() -> None:
    """`centre` and `half_width` raise rather than returning a plausible number
    for a one-sided window (Spec §2.2): there is no centre, and inventing one is
    the failure the explicit UNBOUNDED declaration exists to avoid."""
    bound = one_sided_form().validity.bounds[0]
    assert bound.is_one_sided
    for attribute in ("centre", "half_width"):
        with pytest.raises(ValueError, match="one-sided"):
            getattr(bound, attribute)


def test_unbounded_is_distinct_from_a_missing_bound() -> None:
    """An explicitly UNBOUNDED edge is a declaration; an omitted *value* at report
    time is still refused (Core §4 item 3's "if none, state how condition (b) is
    satisfied instead"; E-26's "an explicitly empty response is a legal, required
    declaration").
    """
    form = one_sided_form()
    # Declared UNBOUNDED above — legal, and reports fine.
    assert form.report({"extent": 9.0}).factors["extent"] == pytest.approx(1.0)
    # Omitting the value is still an error: an unchecked bound hides violations.
    with pytest.raises(ValueError, match="no value supplied"):
        form.report({})


def test_a_one_sided_bound_requires_a_declared_scale_and_a_two_sided_one_forbids_it() -> None:
    """The scale is required exactly where the half-width cannot serve, and
    refused where it can — so which rule produced a reported factor is never
    ambiguous (ADR-043)."""
    with pytest.raises(ValueError, match="declares no fitted_scale"):
        ValidityBound(name="x", space=ValiditySpace.STATE, low=1.0, high=UNBOUNDED)
    with pytest.raises(ValueError, match="two-sided and also declares a fitted_scale"):
        ValidityBound(name="x", space=ValiditySpace.STATE, low=0.0, high=1.0, fitted_scale=2.0)
    with pytest.raises(ValueError, match="both edges UNBOUNDED"):
        ValidityBound(name="x", space=ValiditySpace.STATE, low=UNBOUNDED, high=UNBOUNDED,
                      fitted_scale=1.0)


def test_form_kind_is_declared_because_the_shared_signature_cannot_express_it() -> None:
    """One signature covers rate laws, explicit solutions and algebraic relations
    (Core §3.3, Core §3.5), so the distinction between "a rate to integrate" and
    "a level to use" must be declared — it is not recoverable from the type."""
    form = known_envelope_form()
    assert form.kind is FormKind.ALGEBRAIC
    # The signature is identical across kinds: a mapping of named quantities in,
    # a response array out. Only `kind` separates them.
    assert form.evaluate({"drive": 1.0, "extent": 1.0}).shape == (1,)
    assert {k.value for k in FormKind} == {"rate_law", "explicit_solution", "algebraic"}


# --- approximate edges (amended before M11.3) -------------------------------


def test_the_report_distinguishes_a_fuzzy_edge_from_a_sharp_one(
    observe: ObservationRecorder,
) -> None:
    """A window can have one edge fixed by physics and one set by a competing
    mechanism, and the report must say which was violated (Spec §2.2; ADR-043).

    Without this, a factor of ``1.05`` against a route-dependent boundary reads
    identically to the same factor against a sharp limit, and a consumer would
    report the edge's own uncertainty as a finding — the failure shape
    `docs/V1.4-EDITS.md` §6 documents nine times over elsewhere.
    """
    form = mixed_edge_form()
    below = form.report({"level": APPROX_LOW - 2.0})
    above = form.report({"level": APPROX_HIGH + 2.0})
    inside = form.report({"level": 0.5 * (APPROX_LOW + APPROX_HIGH)})

    observe(
        "mixed_edge_report",
        {
            "below": {"factor": below.factors["level"], "approx": below.edge_is_approximate},
            "above": {"factor": above.factors["level"], "approx": above.edge_is_approximate},
            "inside": {"factor": inside.factors["level"], "approx": inside.edge_is_approximate},
        },
        "same magnitude either side; only the edge kind differs",
    )

    # Symmetric magnitudes, opposite edge kinds — so the factor alone cannot
    # distinguish them and the declared kind is doing real work.
    assert below.factors["level"] == pytest.approx(above.factors["level"])
    assert below.binding_edge_kind is EdgeKind.APPROXIMATE
    assert below.edge_is_approximate
    assert above.binding_edge_kind is EdgeKind.SHARP
    assert not above.edge_is_approximate

    # Inside the window nothing binds, so there is no edge kind to report.
    assert inside.binding_edge_kind is None
    assert not inside.edge_is_approximate


def test_edges_default_to_sharp_so_a_fuzzy_edge_is_an_explicit_claim() -> None:
    """Declaring an edge approximate is a positive statement about the source, so
    the default is SHARP (Spec §2.2): a domain that has not thought about it gets
    the stronger, checkable claim rather than a silent hedge."""
    bound = known_envelope_form().validity.bounds[0]
    assert bound.low_kind is EdgeKind.SHARP
    assert bound.high_kind is EdgeKind.SHARP


def test_violated_edge_names_the_side_not_only_the_magnitude() -> None:
    """`extrapolation_factor` is a magnitude; `violated_edge` says which side, and
    a window's two edges can differ in kind (Spec §2.2)."""
    bound = mixed_edge_form().validity.bounds[0]
    assert bound.violated_edge(APPROX_LOW - 1.0) == "low"
    assert bound.violated_edge(APPROX_HIGH + 1.0) == "high"
    assert bound.violated_edge(0.5 * (APPROX_LOW + APPROX_HIGH)) is None
