"""M11.1's gate: the v1.3/proposed-v1.4 boundary holds, and the v1.3 audit
survives it (ADR-042, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-35).

The boundary is **not** a directory. It is two structural mechanisms, and this
module tests both:

1. **Versioned claims** — every `ConformanceReport` states the version of Core
   and Spec its level is claimed against (Spec §9.1 requires the level and not
   the version, which is E-35), and comparison across versions is refused.
2. **Composition, not modification** — `ProposedV14Declaration` wraps a v1.3
   declaration rather than replacing or forking it, so Core §4's comparative
   machinery is untouched *by construction*.

The audit-preservation half of the gate is partly a property of the whole suite
rather than of any one test — every pre-existing conformance test must still
pass, with its recorded observations unchanged — and that half is checked by
running the suite and diffing `build/observations.json` against the pre-change
baseline. What is testable here is the structural precondition for it: that the
version is *required* rather than defaulted, so no caller can produce a report
labelled v1.3 by omission.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.conformance import (
    ConformanceInputs,
    ConformanceLevel,
    ConformanceReport,
    ConformanceVersionMismatch,
    compare_reports,
    generate_report,
)
from omi.interface import SpecificationVersion, diff
from omi.proposed import ProposedV14Declaration
from omi.state import Metric

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

from tests.conftest import ObservationRecorder
from tests.oracles.known_envelope import known_envelope_form


def _metric() -> Metric:
    return Metric(FLAGSHIP_SCHEMA, np.ones(FLAGSHIP_SCHEMA.size))


def _inputs(version: SpecificationVersion, curve: bool = False) -> ConformanceInputs:
    return ConformanceInputs(
        specification_version=version,
        declaration=FLAGSHIP_DECLARATION,
        metric=_metric(),
        rollout_error_curve=np.array([0.1, 0.2, 0.4]) if curve else None,
    )


# --- mechanism 1: versioned claims ------------------------------------------


def test_the_specification_version_is_required_not_defaulted() -> None:
    """The no-silent-default guarantee, which is what makes the version a
    *positive* per-result assurance rather than a convention (ADR-042).

    Spec §9.1's own instruction is to "state its level"; E-35's finding is that
    nothing requires the version alongside it. A default here would reintroduce
    exactly that ambiguity through the back door: a proposed-v1.4 caller who
    forgot the argument would silently emit a report labelled v1.3, which is the
    misreading E-35 says becomes possible the moment two versions coexist.
    """
    with pytest.raises(TypeError):
        ConformanceInputs(declaration=FLAGSHIP_DECLARATION, metric=_metric())  # type: ignore[call-arg]


def test_report_carries_the_declared_version_through_unchanged(
    observe: ObservationRecorder,
) -> None:
    """`generate_report` carries the declared version onto the report rather
    than inferring it (Spec §9.1; ADR-042)."""
    for version in SpecificationVersion:
        report = generate_report(_inputs(version))
        observe(
            f"report_version_{version.name}",
            report.specification_version.value,
            f"carried through from inputs, expected {version.value}",
        )
        assert report.specification_version is version


def test_comparison_across_versions_is_refused_not_silently_permitted() -> None:
    """Spec §9.1's level names are defined by its level table, and a framework
    revision changes those rows, so the same name does not denote the same
    requirements across versions (`docs/V1.4-EDITS.md` E-35). `compare_reports`
    therefore refuses, naming both versions — the refusal is the mechanism, and
    ADR-042 records that there is deliberately no flag to suppress it.
    """
    v13 = generate_report(_inputs(SpecificationVersion.V1_3))
    v14 = generate_report(_inputs(SpecificationVersion.PROPOSED_V1_4))

    with pytest.raises(ConformanceVersionMismatch) as excinfo:
        compare_reports(v13, v14)

    assert excinfo.value.left is SpecificationVersion.V1_3
    assert excinfo.value.right is SpecificationVersion.PROPOSED_V1_4
    # Refusal is symmetric: neither direction is the privileged one.
    with pytest.raises(ConformanceVersionMismatch):
        compare_reports(v14, v13)


def test_same_version_comparison_returns_the_requirement_level_diff(
    observe: ObservationRecorder,
) -> None:
    """Within one version the level table is fixed, so a comparison is
    meaningful and returns only the requirements whose satisfaction differs
    (Spec §9.1; ADR-042). Two identical reports agree on everything.
    """
    bare = generate_report(_inputs(SpecificationVersion.V1_3))
    with_curve = generate_report(_inputs(SpecificationVersion.V1_3, curve=True))

    assert compare_reports(bare, bare) == {}

    differences = compare_reports(bare, with_curve)
    observe(
        "same_version_report_diff",
        {name: list(flags) for name, flags in differences.items()},
        "only the rollout-curve requirement should differ",
    )
    assert "rollout_length_error_curve_reported" in differences
    assert differences["rollout_length_error_curve_reported"] == (False, True)


def test_a_v13_claim_and_a_v14_claim_are_different_objects_on_one_domain(
    observe: ObservationRecorder,
) -> None:
    """The case a directory boundary cannot express, and the reason ADR-042
    rejected one: **the same domain evaluated under both interfaces.** This is
    what ADR-045's contestants 1 versus 2/3 require, and it must not need two
    copies of a domain to say.
    """
    v13 = generate_report(_inputs(SpecificationVersion.V1_3, curve=True))
    v14 = generate_report(_inputs(SpecificationVersion.PROPOSED_V1_4, curve=True))

    assert v13.declaration is v14.declaration
    assert v13.specification_version is not v14.specification_version
    assert v13.highest_claimable_level() is ConformanceLevel.OMI_0
    assert v14.highest_claimable_level() is ConformanceLevel.OMI_0
    observe(
        "one_domain_two_version_claims",
        [v13.specification_version.value, v14.specification_version.value],
        "same declaration object, two distinct version-stamped claims",
    )


# --- mechanism 2: composition, not modification -----------------------------


def test_v13_core_projection_diffs_exactly_as_the_v13_declaration_does(
    observe: ObservationRecorder,
) -> None:
    """The composition guarantee, stated as the property that matters: wrapping
    a Core §4 declaration must not change what `omi.interface.diff` says about
    it. Core §4 calls the interface "comparative... which is what converts a
    collection of examples into evidence of generality", so this is the property
    the v1.3 generality evidence rests on (ADR-042).

    At M11.1 the extension is empty, so this is the baseline reading. ADR-044's
    variant domain re-runs the same check after M11.2 adds a category, and any
    disturbance is then attributable to that addition alone.
    """
    wrapped = ProposedV14Declaration(v13_core=FLAGSHIP_DECLARATION)

    direct = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    projected = diff(wrapped.v13_core, CONTRAST_DECLARATION)

    observe(
        "v13_core_projection_diff_matches_direct",
        {"identical": projected == direct, "n_keys": len(direct)},
        "wrapping must not change any item's diff verdict",
    )
    assert projected == direct
    assert wrapped.v13_core is FLAGSHIP_DECLARATION


def test_the_projection_still_holds_with_the_m11_2_extension_populated(
    observe: ObservationRecorder,
) -> None:
    """The re-check M11.2 triggered, and the reason the wrapper was introduced
    empty at M11.1 (ADR-042).

    A declaration carrying declared constitutive forms (Core §4 item 6d, ADR-043)
    must still project to a v1.3 core that diffs identically to the unwrapped
    declaration. If this failed, the extension would be changing what Core §4's
    comparative machinery says about a domain — which is the property ADR-044's
    controlled comparison between flagship and its constitutive variant depends
    on, since that comparison reads the diff as a measurement of the extension
    itself.
    """
    populated = ProposedV14Declaration(
        v13_core=FLAGSHIP_DECLARATION,
        constitutive_forms=(known_envelope_form(),),
    )
    empty = ProposedV14Declaration(v13_core=FLAGSHIP_DECLARATION)

    direct = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    with_forms = diff(populated.v13_core, CONTRAST_DECLARATION)
    without_forms = diff(empty.v13_core, CONTRAST_DECLARATION)

    observe(
        "projection_diff_invariant_to_extension_content",
        {"forms_declared": len(populated.constitutive_forms), "identical_to_direct": with_forms == direct},
        "populating item 6d must not move any v1.3 item's diff verdict",
    )
    assert with_forms == direct == without_forms
    assert populated.v13_core is FLAGSHIP_DECLARATION
    assert empty.constitutive_forms == ()


def test_wrapped_declaration_cannot_claim_to_be_v13() -> None:
    """A declaration carrying the extension is not a v1.3 declaration, and
    `specification_version` is a read-only property rather than a field so that
    saying otherwise is unrepresentable rather than merely checked (Spec §9.1;
    ADR-042)."""
    wrapped = ProposedV14Declaration(v13_core=FLAGSHIP_DECLARATION)
    assert wrapped.specification_version is SpecificationVersion.PROPOSED_V1_4
    with pytest.raises(AttributeError):
        wrapped.specification_version = SpecificationVersion.V1_3  # type: ignore[misc]


def test_the_extension_declares_exactly_the_fields_the_adrs_authorise() -> None:
    """Pins the extension's field list, so every future addition is a deliberate
    edit here and re-triggers the projection check above (ADR-042; Core §4).

    This test did its job once already. M11.1 introduced the wrapper with only
    `v13_core`, deliberately empty, so that the diff-preservation property was
    established *before* the extension had content; M11.2 (ADR-043) then added
    `constitutive_forms` and this assertion failed, which is exactly the prompt
    to re-run the projection check rather than assume it still held. It did still
    hold — see the projection test above, which passes unchanged with the field
    present and a wrapped declaration carrying forms.
    """
    from dataclasses import fields

    assert [f.name for f in fields(ProposedV14Declaration)] == ["v13_core", "constitutive_forms"]


def test_report_is_frozen_so_a_version_cannot_be_restamped_after_the_fact() -> None:
    """A conformance report is a record intended to outlive the run that
    produced it (Spec §9.1; E-35's proposed addition). Restamping one with a
    different version after production would be exactly the forgery the version
    field exists to prevent, so `ConformanceReport` stays frozen.
    """
    report = generate_report(_inputs(SpecificationVersion.V1_3))
    assert isinstance(report, ConformanceReport)
    with pytest.raises(Exception):
        report.specification_version = SpecificationVersion.PROPOSED_V1_4  # type: ignore[misc]
