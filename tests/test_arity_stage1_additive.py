"""Stage 1 of the arity redesign: the additive decisions C, D, E, plus the
`conformance.py` carrying `docs/ARITY-REDESIGN-BRIEF.md` deferred at M11 (ADR-068, ADR-069).

Everything here lands on a **wrapper class** (`DecisionExtendedDeclaration`,
`ConstitutiveForm`) rather than on `omi.interface.InstantiationDeclaration` itself — a
considered correction to the brief's own prediction that these fields would "gain keys" on
`diff`. `omi.interface.diff` and every comparability result it has ever produced are
untouched by anything in this module; :mod:`tests.test_interface_diff` is the test that
would catch a violation of that, and nothing here duplicates it.

Four pieces, one file, because all four are Stage 1's one authorised unit of work:

- **Decision C** — `omi.interface.ScopeDeclaration` (E-44, E-52).
- **Decision D** — `omi.proposed.constitutive.ConstitutiveForm.refines` / `refinement_note`
  (E-40), exercised on the real worked case.
- **Decision E** — `omi.proposed.decision.SymmetryGroupAction` (E-30, half-closed by design).
- **The conformance wiring** — `ConformanceInputs.error_control_claim` /
  `ConformanceReport.error_control_claim`, carried but not gated (ADR-068's deferral,
  now Decision C's per the brief).
"""

from __future__ import annotations

import pytest

from omi.conformance import ConformanceInputs, generate_report
from omi.erasure import (
    ErasureCompleteness,
    ErrorControlVerdict,
    StateSufficiencyEvidence,
    condition_a_claim,
)
from omi.interface import ScopeDeclaration, SpecificationVersion
from omi.proposed.constitutive import (
    ConstitutiveForm,
    FormKind,
    ValidityBound,
    ValidityRange,
    ValiditySpace,
)
from omi.proposed.decision import SymmetryGroupAction
from omi.state import Metric, Slot

from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.state import FLAGSHIP_SCHEMA
from omi_domains.flagship_constitutive.forms import KOCKS_MECKING, KOCKS_MECKING_STRAIN_WINDOWED
from omi_domains.sdl.interface import SDL_DECLARATION

from tests.conftest import ObservationRecorder

# --- Decision C: ScopeDeclaration -------------------------------------------


def test_scope_declaration_reports_evidenced_and_undeclared_features_generically(
    observe: ObservationRecorder,
) -> None:
    """A declaration with two of four features evidenced splits cleanly, on a scope
    declaration built for this test rather than a real domain's — the generic behaviour
    should not depend on which domain exercises it (E-44's proposed "MUST be able to
    point... to the item that evidences it")."""
    scope = ScopeDeclaration(
        control_axis_evidence="item 2 names it",
        hidden_state_evidence="",
        structure_mediated_response_evidence="item 4 implies it",
        recurring_decision_under_uncertainty_evidence="",
        scope_exit_criterion="",
    )
    observe("scope_evidenced_features", scope.evidenced_features(), "control_axis, structure_mediated_response")
    observe(
        "scope_undeclared_features", scope.undeclared_features(), "hidden_state, recurring_decision_under_uncertainty"
    )
    assert scope.evidenced_features() == ("control_axis", "structure_mediated_response")
    assert scope.undeclared_features() == ("hidden_state", "recurring_decision_under_uncertainty")
    assert not scope.declares_scope_exit


def test_scope_declaration_default_is_all_undeclared_and_no_scope_exit(
    observe: ObservationRecorder,
) -> None:
    """The all-empty case: E-44's finding is that silence is itself informative, so an
    unpopulated `ScopeDeclaration` must say "nothing evidenced" rather than raise or
    default to something evidenced by omission."""
    scope = ScopeDeclaration()
    observe("empty_scope_evidenced", scope.evidenced_features(), "()")
    observe("empty_scope_undeclared_count", len(scope.undeclared_features()), "4")
    assert scope.evidenced_features() == ()
    assert len(scope.undeclared_features()) == 4
    assert not scope.declares_scope_exit


def test_scope_exit_criterion_reported_distinctly_from_the_four_features(
    observe: ObservationRecorder,
) -> None:
    """E-52's item is orthogonal to E-44's four: a domain can evidence every scope
    feature and still decline to state where it stops applying, or vice versa."""
    scope = ScopeDeclaration(scope_exit_criterion="beyond the declared attainable region")
    observe("scope_exit_declared_with_no_features", scope.declares_scope_exit, "True")
    observe("scope_exit_features_still_all_undeclared", len(scope.evidenced_features()), "0")
    assert scope.declares_scope_exit
    assert scope.evidenced_features() == ()


# --- Decision E: SymmetryGroupAction -----------------------------------------


def test_symmetry_group_action_requires_group_components_and_justification() -> None:
    """ADR-043's discipline for an unexplained bound, applied to a group action
    (`docs/V1.4-EDITS.md` E-30): each of the three fields is checked at construction,
    not merely documented as required."""
    with pytest.raises(ValueError, match="name a group"):
        SymmetryGroupAction(group="", components=("orientation_x",), justification="justified")
    with pytest.raises(ValueError, match="no component"):
        SymmetryGroupAction(group="SO(3)", components=(), justification="justified")
    with pytest.raises(ValueError, match="no justification"):
        SymmetryGroupAction(group="SO(3)", components=("orientation_x",), justification="  ")


def test_symmetry_group_action_constructs_when_fully_declared(observe: ObservationRecorder) -> None:
    """The positive case: a well-formed declaration is unremarkable, which is the point
    — the validation exists to reject the incomplete case, not to make the complete one
    hard."""
    action = SymmetryGroupAction(
        group="SO(3)",
        components=("orientation_x", "orientation_y", "orientation_z"),
        justification="a full 3D rotation acts jointly on the three-component orientation field",
    )
    observe("symmetry_group_action_group", action.group, "SO(3)")
    observe("symmetry_group_action_n_components", len(action.components), "3")
    assert action.group == "SO(3)"
    assert len(action.components) == 3


def test_no_built_domain_declares_a_symmetry_group_action(observe: ObservationRecorder) -> None:
    """What E-30's docstring claims about this repository's domains, checked rather
    than asserted: `symmetry_group_actions` is empty on the one decision-extension
    declaration built so far, because none of the three domains declares an
    orientation-like field for a group to act on."""
    observe("sdl_symmetry_group_actions", SDL_DECLARATION.symmetry_group_actions, "()")
    assert SDL_DECLARATION.symmetry_group_actions == ()


# --- Decision D: ConstitutiveForm.refines / refinement_note -----------------


def _bare_form(name: str, **overrides: object) -> ConstitutiveForm:
    """A minimal well-formed form, for testing `refines` validation in isolation from
    any domain's real physics (the same role `tests/oracles/known_envelope.py` plays
    for `ValidityRange`, kept local here since only `refines` is under test)."""
    defaults: dict[str, object] = dict(
        name=name,
        kind=FormKind.ALGEBRAIC,
        evaluate=lambda values: __import__("numpy").array([values["x"]]),
        parameters={},
        validity=ValidityRange((ValidityBound(name="x", space=ValiditySpace.STATE, low=0.0, high=1.0, regime="test"),)),
        provenance="test fixture",
        governs=((Slot.M, "x"),),
    )
    defaults.update(overrides)
    return ConstitutiveForm(**defaults)  # type: ignore[arg-type]


def test_refines_requires_a_non_empty_refinement_note() -> None:
    """E-40's own proposed wording: "stating which items changed" — a `refines`
    declaration with nothing to say is indistinguishable from an unexplained edit, so
    it is refused rather than silently accepted."""
    base = _bare_form("base_form")
    with pytest.raises(ValueError, match="refinement_note"):
        _bare_form("derived_form", refines=base.name, refinement_note="")
    with pytest.raises(ValueError, match="refinement_note"):
        _bare_form("derived_form", refines=base.name, refinement_note="   ")


def test_refines_none_does_not_require_a_note(observe: ObservationRecorder) -> None:
    """The independent case (E-40's own distinction): a form declaring no lineage owes
    no explanation of a change, since none is claimed."""
    form = _bare_form("independent_form")
    observe("independent_form_refines", form.refines, "None")
    assert form.refines is None
    assert form.refinement_note == ""


def test_a_form_cannot_declare_itself_as_its_own_refinement() -> None:
    """A self-loop in the lineage graph is not a refinement of anything; refused at
    construction rather than left for a consumer of the lineage to detect."""
    with pytest.raises(ValueError, match="cannot refine itself"):
        _bare_form("self_form", refines="self_form", refinement_note="not a real change")


def test_kocks_mecking_strain_windowed_declares_the_real_worked_case(
    observe: ObservationRecorder,
) -> None:
    """**The worked case E-40 documents, exercised structurally rather than only in
    prose.** `KOCKS_MECKING_STRAIN_WINDOWED` was published alongside `KOCKS_MECKING`
    because `ValidityRange.report` needs a value for every declared bound, so the
    windowed form could not extend the original's range without breaking every caller
    of the original — but the physics is identical, and before this field
    `omi.interface.diff`-level tooling had no way to see that these are one lineage
    rather than two independent disagreeing forms.
    """
    observe("windowed_form_refines", KOCKS_MECKING_STRAIN_WINDOWED.refines, f"== {KOCKS_MECKING.name!r}")
    observe(
        "windowed_form_refinement_note_nonempty",
        bool(KOCKS_MECKING_STRAIN_WINDOWED.refinement_note.strip()),
        "True",
    )
    assert KOCKS_MECKING_STRAIN_WINDOWED.refines == KOCKS_MECKING.name
    assert KOCKS_MECKING_STRAIN_WINDOWED.refinement_note.strip()
    assert KOCKS_MECKING.refines is None, "the original form must not retroactively claim to refine anything"


# --- The conformance wiring: carried, not gated ------------------------------


def _metric() -> Metric:
    import numpy as np

    return Metric(FLAGSHIP_SCHEMA, np.ones(FLAGSHIP_SCHEMA.size))


def _completeness(surviving_gain: float) -> ErasureCompleteness:
    return ErasureCompleteness(
        effective_rank=1,
        state_dimension=FLAGSHIP_SCHEMA.size,
        tolerance=1.0e-6,
        surviving_gain=surviving_gain,
        erased_gain=1.0e-3,
        metric=_metric(),
    )


def test_conformance_report_carries_the_error_control_claim_unchanged(
    observe: ObservationRecorder,
) -> None:
    """ADR-068's deferred wiring, Decision C's per the brief: the claim travels from
    inputs to report unmodified. No interpretation, no gating — carrying it is the
    entire scope of this repair."""
    claim = condition_a_claim(
        _completeness(surviving_gain=0.5),
        StateSufficiencyEvidence(deficit_squared=0.01, threshold=0.05, provenance="test fixture"),
    )
    assert claim.verdict is ErrorControlVerdict.CLAIMABLE

    inputs = ConformanceInputs(
        declaration=FLAGSHIP_DECLARATION,
        metric=_metric(),
        specification_version=SpecificationVersion.V1_3,
        error_control_claim=claim,
    )
    report = generate_report(inputs)
    observe("carried_error_control_verdict", report.error_control_claim.verdict.name, "CLAIMABLE")  # type: ignore[union-attr]
    assert report.error_control_claim is claim


def test_error_control_claim_does_not_gate_any_omi_0_1_2_requirement(
    observe: ObservationRecorder,
) -> None:
    """**Deliberately not implemented, and this test pins that it stays that way for
    Stage 1.** A refused claim (the common case — no sufficiency deficit was supplied)
    must not lower `highest_claimable_level()` or flip any `RequirementStatus`,
    because whether condition (a) should gate a level is a restructuring decision (A or
    B), not this stage's additive one. Only the field's *presence on the report*
    changes; the level table is untouched.
    """
    import numpy as np

    refused = condition_a_claim(_completeness(surviving_gain=2.0))
    assert refused.verdict is ErrorControlVerdict.REFUSED_GAIN_NOT_CONTRACTED
    curve = np.array([0.1, 0.2, 0.4])

    with_claim = generate_report(
        ConformanceInputs(
            declaration=FLAGSHIP_DECLARATION,
            metric=_metric(),
            specification_version=SpecificationVersion.V1_3,
            rollout_error_curve=curve,
            error_control_claim=refused,
        )
    )
    without_claim = generate_report(
        ConformanceInputs(
            declaration=FLAGSHIP_DECLARATION,
            metric=_metric(),
            specification_version=SpecificationVersion.V1_3,
            rollout_error_curve=curve,
            error_control_claim=None,
        )
    )
    observe(
        "requirements_identical_regardless_of_error_control_claim",
        with_claim.requirements == without_claim.requirements,
        "True",
    )
    observe("highest_level_identical", with_claim.highest_claimable_level() == without_claim.highest_claimable_level(), "True")
    assert with_claim.requirements == without_claim.requirements
    assert with_claim.highest_claimable_level() == without_claim.highest_claimable_level()
    assert with_claim.error_control_claim is refused
    assert without_claim.error_control_claim is None


def test_error_control_claim_defaults_to_none_on_every_existing_call_site(
    observe: ObservationRecorder,
) -> None:
    """Every report this repository generated before Stage 1 constructed
    `ConformanceInputs` without this field; the default must make those call sites'
    behaviour unchanged rather than requiring a retrofit."""
    report = generate_report(
        ConformanceInputs(
            declaration=FLAGSHIP_DECLARATION,
            metric=_metric(),
            specification_version=SpecificationVersion.V1_3,
        )
    )
    observe("default_error_control_claim", report.error_control_claim, "None")
    assert report.error_control_claim is None


# --- SDL's declaration, updated with the new fields (this stage's fourth site) ----


def test_sdl_declaration_evidences_all_four_scope_features(observe: ObservationRecorder) -> None:
    """SDL is the first declaration to populate `scope`, and E-44's finding predicts
    it should be the strongest case of the three built domains: `decision_kind` names
    the campaign decision directly, and `z`'s two components are documented in
    `state.py` itself as unresolved by any declared modality."""
    assert SDL_DECLARATION.scope is not None
    observe("sdl_scope_evidenced_features", SDL_DECLARATION.scope.evidenced_features(), "all four")
    observe("sdl_scope_undeclared_features", SDL_DECLARATION.scope.undeclared_features(), "()")
    observe("sdl_declares_scope_exit", SDL_DECLARATION.scope.declares_scope_exit, "True")
    assert SDL_DECLARATION.scope.evidenced_features() == (
        "control_axis",
        "hidden_state",
        "recurring_decision_under_uncertainty",
        "structure_mediated_response",
    )
    assert SDL_DECLARATION.scope.undeclared_features() == ()
    assert SDL_DECLARATION.scope.declares_scope_exit
