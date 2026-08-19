"""M11.3's gate: the constitutive variant is a sibling that leaves flagship
untouched, its v1.3 core is indistinguishable from flagship's, two of the three
`rate == 0.0` components acquire real kinetics, and the extrapolation report is
live on a real chain (ADR-044, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-32, E-29).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pytest

from omi.chain import Chain
from omi.interface import InstantiationDeclaration, classify_invariant, diff
from omi.proposed import CertificateRoleRefused, FormKind, InvariantSubItem, ValidityAction
from omi.proposed import assert_certificate_eligible
from omi.proposed.constitutive import ConstitutivelyConstrained, ValiditySpace
from omi.state import FloatArray, Slot, State

from omi_domains.flagship.build import build_chain, build_incoming_ensemble
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship_constitutive.build import build_constitutive_chain
from omi_domains.flagship_constitutive.forms import DECLARED_FORMS, HALL_PETCH
from omi_domains.flagship_constitutive.interface import (
    CONSTITUTIVE_DECLARATION,
    CONSTITUTIVE_V13_CORE,
)

from tests.conftest import ObservationRecorder

STATIC_IN_FLAGSHIP = ("prior_grain_size", "inclusion_content", "accumulated_hardening")
"""The three components Phase 1 measured at `rate == 0.0` under both flagship
operators (`docs/V1.4-EDITS.md` E-29)."""


def _rollout_means(chain: Chain, n: int = 60) -> dict[str, float]:
    ensemble = build_incoming_ensemble(n, np.random.default_rng(0))
    final = chain.rollout(ensemble).final
    names = [name for _, name, _ in ensemble.schema.components]
    return dict(zip(names, final.particles.mean(axis=0)))


# --- the sibling relationship ------------------------------------------------


def test_flagship_itself_is_untouched(observe: ObservationRecorder) -> None:
    """ADR-044's load-bearing constraint: the analytic flagship is unchanged, so
    every M0-M9 oracle result that used it still stands.

    Checked at the level that matters — flagship's own operators still carry
    `rate == 0.0` for the three components E-29 identified, which is the *defect*
    E-29 records. Repairing it would delete this repository's only instance of a
    domain satisfying all seven interface items while being physically inert.
    """
    schema = FLAGSHIP_DECLARATION.state_schema
    still_static = {}
    for name in STATIC_IN_FLAGSHIP:
        index = schema.slice_for(
            Slot.M if name == "prior_grain_size" else Slot.Z, name
        ).start
        still_static[name] = [
            float(HEATING_AND_SOAK.rates[index]),
            float(TRANSFER.rates[index]),
        ]

    observe(
        "flagship_static_components_unchanged",
        still_static,
        "all rates still 0.0 — E-29's defect is preserved, not repaired",
    )
    assert all(r == 0.0 for rates in still_static.values() for r in rates)


def test_the_two_v13_cores_are_indistinguishable(observe: ObservationRecorder) -> None:
    """**ADR-044 predicted the diff would isolate item 6. It is empty**, and that is
    the stronger result (`docs/V1.4-EDITS.md` E-32).

    v1.3's seven items cannot express "this domain declares five constitutive
    forms", so the honest v1.3 core of the variant is identical to flagship's while
    the domains differ substantially in physics. Core §4 calls the interface
    "comparative... which is what converts a collection of examples into evidence
    of generality"; here the comparison is blind to the difference the extension is
    about.
    """
    result = diff(CONSTITUTIVE_V13_CORE, FLAGSHIP_DECLARATION)
    observe(
        "constitutive_vs_flagship_v13_diff",
        {k: v for k, v in result.items()},
        "every item False — v1.3 cannot see the difference",
    )
    assert not any(result.values()), "v1.3 cores must be indistinguishable"
    assert len(CONSTITUTIVE_DECLARATION.constitutive_forms) == 5


def test_the_other_road_is_closed_too_diff_refuses_an_honest_item_6() -> None:
    """The complementary half of the finding: a domain that instead names its
    declared forms *inside* item 6 cannot be diffed against anything at all.

    `classify_invariant` refuses a name that is neither a conservation law nor a
    monotone functional — correct under v1.3's two categories — and `diff` calls it
    on every invariant of both declarations. So declaring the forms breaks the
    comparison and not declaring them makes it blind: both roads are closed, which
    is what makes E-32's missing category consequential rather than cosmetic.
    """
    honest = InstantiationDeclaration(
        state_schema=FLAGSHIP_DECLARATION.state_schema,
        declared_parameters=FLAGSHIP_DECLARATION.declared_parameters,
        control_space=FLAGSHIP_DECLARATION.control_space,
        erasure_inventory=FLAGSHIP_DECLARATION.erasure_inventory,
        readout_catalogue=FLAGSHIP_DECLARATION.readout_catalogue,
        observation_suite=FLAGSHIP_DECLARATION.observation_suite,
        invariants=FLAGSHIP_DECLARATION.invariants + ("declared_constitutive_forms_five",),
        scale_structure=FLAGSHIP_DECLARATION.scale_structure,
    )
    with pytest.raises(ValueError, match="refuses to guess"):
        diff(honest, FLAGSHIP_DECLARATION)
    with pytest.raises(ValueError, match="refuses to guess"):
        classify_invariant("declared_constitutive_forms_five")


# --- what the kinetics repair, and what stays static on purpose --------------


def test_two_of_the_three_static_components_acquire_real_kinetics(
    observe: ObservationRecorder,
) -> None:
    """E-26 becomes exercisable rather than only detectable (ADR-044).

    `prior_grain_size` and `accumulated_hardening` are transported by declared
    forms in the variant and by nothing in flagship. `inclusion_content` stays
    static in **both**, deliberately: inclusions really are inert over this chain,
    so it is a genuine parameter in E-29's proposed sense rather than an
    un-transported state component, and declaring kinetics for it to improve the
    audit would be inventing physics.
    """
    flagship = _rollout_means(build_chain())
    variant = _rollout_means(build_constitutive_chain())
    incoming = _rollout_means_incoming()

    moved = {
        name: {
            "in": incoming[name],
            "flagship": flagship[name],
            "variant": variant[name],
        }
        for name in STATIC_IN_FLAGSHIP
    }
    observe("static_components_under_both_chains", moved, "two move in the variant, one by design does not")

    for name in ("prior_grain_size", "accumulated_hardening"):
        assert flagship[name] == pytest.approx(incoming[name]), f"{name} must be static in flagship"
        assert variant[name] != pytest.approx(incoming[name]), f"{name} must move in the variant"

    # The deliberate exception, asserted so it cannot silently change.
    assert variant["inclusion_content"] == pytest.approx(incoming["inclusion_content"])
    assert flagship["inclusion_content"] == pytest.approx(incoming["inclusion_content"])


def _rollout_means_incoming(n: int = 60) -> dict[str, float]:
    ensemble = build_incoming_ensemble(n, np.random.default_rng(0))
    names = [name for _, name, _ in ensemble.schema.components]
    return dict(zip(names, ensemble.particles.mean(axis=0)))


def test_the_erasure_survives_the_substitution(observe: ObservationRecorder) -> None:
    """The variant still declares an erasure and still performs one (Core §3.9):
    substituting a declared form for a bare rate must not quietly remove the
    physical claim that recrystallisation destroys stored substructure.
    """
    incoming = _rollout_means_incoming()
    variant = _rollout_means(build_constitutive_chain())
    ratio = variant["substructure_density"] / incoming["substructure_density"]
    observe("variant_substructure_retained_fraction", ratio, "erasure still contracts (< 1)")
    assert build_constitutive_chain().segments[0].operator.is_erasure
    assert ratio < 1.0


# --- the declared forms and their reports ------------------------------------


def test_all_five_forms_declare_a_range_provenance_and_kind(
    observe: ObservationRecorder,
) -> None:
    """Core §4 item 6d's required content, per form (Spec §2.2; ADR-043)."""
    summary = {}
    for form in DECLARED_FORMS:
        spaces = sorted(s.value for s in form.validity.spaces())
        summary[form.name] = {
            "kind": form.kind.value,
            "spaces": spaces,
            "n_bounds": len(form.validity.bounds),
            "one_sided": [b.name for b in form.validity.bounds if b.is_one_sided],
        }
        assert form.provenance
        assert form.validity.bounds
        assert form.governs
    observe("declared_forms_summary", summary, "five forms, each with a declared range")
    assert len(DECLARED_FORMS) == 5
    # All three FormKinds occur, so the tag is doing real work on real physics.
    assert {f.kind for f in DECLARED_FORMS} == set(FormKind)


def test_both_window_rules_are_exercised_by_real_physics(
    observe: ObservationRecorder,
) -> None:
    """Three two-sided windows and one genuinely one-sided, so neither rule rests
    on the oracle alone (ADR-043; ADR-044's form table)."""
    one_sided = {
        f.name: [b.name for b in f.validity.bounds if b.is_one_sided] for f in DECLARED_FORMS
    }
    one_sided = {k: v for k, v in one_sided.items() if v}
    observe("one_sided_windows_among_declared_forms", one_sided, "Hall-Petch's fine-grain edge")

    assert list(one_sided) == [HALL_PETCH.name]
    # Hall-Petch is unbounded above: coarse grains simply strengthen less.
    grain_bound = next(b for b in HALL_PETCH.validity.bounds if b.name == "grain_size")
    assert grain_bound.is_one_sided
    assert grain_bound.fitted_scale is not None
    with pytest.raises(ValueError, match="one-sided"):
        grain_bound.centre


def test_koistinen_marburger_declares_one_sharp_and_one_approximate_edge(
    observe: ObservationRecorder,
) -> None:
    """A transformation window with a sharp upper edge (`Ms`, above which no
    athermal transformation occurs) and an approximate lower edge (where a
    competing isothermal product intervenes during the quench, so the boundary is
    route-dependent) — the case `EdgeKind` exists for (ADR-043).
    """
    form = next(f for f in DECLARED_FORMS if "koistinen" in f.name)
    bound = form.validity.bounds[0]
    below = form.report({"temperature": float(bound.low) - 40.0})  # type: ignore[arg-type]
    above = form.report({"temperature": float(bound.high) + 40.0})  # type: ignore[arg-type]

    observe(
        "koistinen_marburger_edges",
        {
            "below_is_approximate": below.edge_is_approximate,
            "above_is_approximate": above.edge_is_approximate,
            "factors_equal": below.worst_factor == pytest.approx(above.worst_factor),
        },
        "equal magnitudes, different edge kinds",
    )
    assert below.edge_is_approximate, "the competing-mechanism edge must be APPROXIMATE"
    assert not above.edge_is_approximate, "Ms is sharp physics"
    assert bound.space is ValiditySpace.CONTROL


def test_the_chain_reports_where_every_stage_sits_in_its_envelope(
    observe: ObservationRecorder,
) -> None:
    """The *buy physics* mechanism, live on a real chain (`docs/V1.4-EDITS.md` §11;
    Spec §2.2's proposed reporting obligation).

    Both stages must be inside their declared windows at the nominal recipe — if
    they are not, the recipe is evaluating declared physics outside where it was
    established, which is a finding about the recipe rather than about the report.
    """
    chain = build_constitutive_chain()
    ensemble = build_incoming_ensemble(8, np.random.default_rng(0))
    state = State(ensemble.schema, ensemble.particles[0])

    stages = {}
    for index, segment in enumerate(chain.segments):
        operator = segment.operator
        assert isinstance(operator, ConstitutivelyConstrained)
        report = operator.extrapolation_report(state, segment.control)
        stages[f"stage_{index}"] = {
            "worst_factor": report.worst_factor,
            "action": report.action.value,
            "binding": report.binding_segment,
        }
        assert report.action is ValidityAction.WITHIN_ENVELOPE
        state = segment.operator.step(state, segment.control)

    observe("constitutive_chain_envelope_report", stages, "every stage inside its declared windows")


def test_an_off_recipe_soak_surfaces_a_buy_physics_signal(
    observe: ObservationRecorder,
) -> None:
    """Driving the soak outside the declared grain-growth window produces the
    signal the category exists for, and it is *reported*, not enforced (ADR-043).

    The soak temperature is a control, so a control-space violation reports
    `CONTROL_INVERSE` — actionable by Core §5's existing machinery. That is the
    honest classification: the recipe can be moved back inside the window.
    """
    from omi_domains.flagship_constitutive.operators import ConstitutiveHeatingAndSoak

    hot = ConstitutiveHeatingAndSoak(temperature=1400.0)
    ensemble = build_incoming_ensemble(4, np.random.default_rng(0))
    state = State(ensemble.schema, ensemble.particles[0])
    control = build_constitutive_chain().segments[0].control

    report = hot.extrapolation_report(state, control)
    observe(
        "off_recipe_soak_report",
        {
            "worst_factor": report.worst_factor,
            "binding": report.binding_segment,
            "action": report.action.value,
        },
        "outside the declared window, and still evaluable",
    )
    assert report.outside_envelope
    assert report.action is ValidityAction.CONTROL_INVERSE
    # Surfaced, never enforced: the operator still steps.
    assert hot.step(state, control).values.shape == state.values.shape


def test_declared_forms_are_never_certificate_eligible() -> None:
    """Item 6d is hard-constraint only (Core §5; Spec §7.1; E-32): this domain's
    five forms cannot be drawn on for a reachability certificate."""
    with pytest.raises(CertificateRoleRefused):
        assert_certificate_eligible(InvariantSubItem.CONSTITUTIVE_FORM)


# --- the catch: the validity report finding a real modelling error ------------


def test_the_report_catches_koistinen_marburger_applied_at_the_soak_temperature(
    observe: ObservationRecorder,
) -> None:
    """**A first-class result, reproduced rather than recounted** (ADR-043, ADR-044).

    This test reconstructs the modelling error M11.3 actually made and shows the
    validity report catching it. The first version of
    `ConstitutiveHeatingAndSoak` applied `KOISTINEN_MARBURGER` at the soak
    temperature. That is wrong physics: the soak is above `Ms`, where no athermal
    transformation occurs and the form does not apply at all — and because the form
    clamps to zero above `Ms`, the *output* was a perfectly plausible `0.0` that no
    output check would have questioned. Nothing in the state, the response, or any
    oracle would have flagged it.

    The extrapolation report flagged it, on the machinery's first application to
    real physics, with the correct action attached: a control-space violation, so
    `CONTROL_INVERSE` — the recipe can be moved back inside the window, which is
    exactly what the repair did (the form moved to the transfer stage, where the
    piece cools through the window in which it holds).

    Why this is the strongest evidence for the proposed category rather than a
    process anecdote: **no oracle is involved.** The other tests in this repository
    check an estimator against an answer chosen in advance. Here the declared range
    caught a mistake nobody had identified, in code its own author had just written,
    and the recorded factor is the distance between where the query sat and where
    the source establishes the form — a number with physical meaning, not a
    constructed one.
    """
    from omi_domains.flagship_constitutive.forms import KOISTINEN_MARBURGER, MS_TEMPERATURE
    from omi_domains.flagship_constitutive.operators import ConstitutiveHeatingAndSoak

    soak = ConstitutiveHeatingAndSoak()
    assert soak.temperature > MS_TEMPERATURE, "the soak must be above Ms for this to be the error"

    report = KOISTINEN_MARBURGER.report({"temperature": soak.temperature})
    silent_output = float(KOISTINEN_MARBURGER.evaluate({"temperature": soak.temperature})[0])

    observe(
        "km_at_soak_temperature_caught_by_validity_report",
        {
            "soak_temperature": soak.temperature,
            "ms_temperature": MS_TEMPERATURE,
            "extrapolation_factor": report.worst_factor,
            "action": report.action.value,
            "binding_space": report.binding_space.value if report.binding_space else None,
            "output_that_would_have_passed_unnoticed": silent_output,
        },
        "outside the declared window, with a plausible output and the correct action",
    )

    # The error is caught.
    assert report.outside_envelope
    assert report.worst_factor > 5.0
    # With the right action: a control-space violation is addressable by Core §5.
    assert report.action is ValidityAction.CONTROL_INVERSE
    assert report.binding_space is ValiditySpace.CONTROL
    # And the reason it needed catching: the output alone looks fine.
    assert silent_output == pytest.approx(0.0)
    # The sharp edge is the one violated — Ms is physics, not a fitted guess.
    assert not report.edge_is_approximate

    # The repair holds: the form now lives where it is valid.
    from omi_domains.flagship_constitutive.operators import ConstitutiveTransfer

    transfer_report = KOISTINEN_MARBURGER.report(
        {"temperature": ConstitutiveTransfer().end_temperature}
    )
    assert not transfer_report.outside_envelope
    assert transfer_report.action is ValidityAction.WITHIN_ENVELOPE


# --- composition-dependent Ms: the crossing oracle (ADR-078 Decision 2, Gate item 4) --


def _andrews_wt_percent(unconstrained: FloatArray) -> Mapping[str, float]:
    """Simplex fractions -> Andrews' weight-percent convention, via the declared
    conversion (`flagship_composition.composition
    .ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION`). `unconstrained` is the pre-simplex
    coordinate vector for `ANDREWS_DESCRIPTOR_MAP` -- not the fraction itself -- so a
    caller wanting an exact target fraction `p` passes `np.log(p)`: softmax is
    shift-invariant and `softmax(log(p)) == p` for any `p` summing to one.
    """
    from omi_domains.flagship_composition.composition import (
        ANDREWS_DESCRIPTOR_MAP,
        ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION,
    )

    fractions = ANDREWS_DESCRIPTOR_MAP.named_descriptors_of(unconstrained)
    return {
        name: value * ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION for name, value in fractions.items()
    }


def test_andrews_ms_crosses_a_held_constant_query_temperature_by_composition_alone(
    observe: ObservationRecorder,
) -> None:
    """**The crossing oracle** (ADR-078 Gate item 4): a constructed crossing point where
    composition alone moves `Ms` across a held-constant query temperature.

    Two compositions, both inside the declared toy attainable range
    (`flagship_composition.composition.ANDREWS_CARBON_RANGE`/`ANDREWS_MANGANESE_RANGE`,
    0.1-2.0 wt% each), differing only in manganese -- carbon is held fixed, so the
    crossing is attributable to composition alone, not to a second thing moving with it:

    - **A**: 0.1 wt% carbon, 0.1 wt% manganese -- `Ms = 539 - 423*0.1 - 30.4*0.1 = 493.66`
    - **B**: 0.1 wt% carbon, 0.4 wt% manganese -- `Ms = 539 - 423*0.1 - 30.4*0.4 = 484.54`

    Known by construction from Andrews' own formula, recomputed independently below
    rather than trusted from `_andrews_ms`'s own implementation, so this is a genuine
    recovery check and not a test of the function against itself. A held-constant query
    of `487` sits inside A's window (`[480, 493.66]`) and outside B's (`[480, 484.54]`).
    """
    from omi_domains.flagship_constitutive.forms import (
        KM_COMPETING_PRODUCT_ONSET,
        KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT,
    )

    query_temperature = 487.0
    composition_a = _andrews_wt_percent(np.log(np.array([0.001, 0.001, 0.998])))
    composition_b = _andrews_wt_percent(np.log(np.array([0.001, 0.004, 0.995])))
    expected_ms_a = 539.0 - 423.0 * composition_a["carbon"] - 30.4 * composition_a["manganese"]
    expected_ms_b = 539.0 - 423.0 * composition_b["carbon"] - 30.4 * composition_b["manganese"]
    assert expected_ms_a == pytest.approx(493.66, abs=1e-6)
    assert expected_ms_b == pytest.approx(484.54, abs=1e-6)
    assert expected_ms_a > query_temperature > expected_ms_b, (
        "the constructed crossing itself: query_temperature must sit strictly between "
        "the two Ms values for this to be a crossing rather than two same-side points"
    )

    report_a = KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT.report(
        {"temperature": query_temperature}, evaluated_at=composition_a
    )
    report_b = KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT.report(
        {"temperature": query_temperature}, evaluated_at=composition_b
    )

    observe(
        "andrews_ms_crossing",
        {
            "composition_a_wt_pct": composition_a,
            "composition_b_wt_pct": composition_b,
            "query_temperature": query_temperature,
            "resolved_ms_a": report_a.binding_bound.high if report_a.binding_bound else None,
            "resolved_ms_b": report_b.binding_bound.high if report_b.binding_bound else None,
            "factor_a": report_a.worst_factor,
            "factor_b": report_b.worst_factor,
            "action_a": report_a.action.value,
            "action_b": report_b.action.value,
        },
        "factor crosses 1.0 between A and B, purely from manganese content",
    )

    # The resolved bound's high edge IS the composition-dependent Ms, recovered exactly
    # -- confirming ValidityRange.report()'s resolution (ADR-078 Decision 1) against the
    # same independently-recomputed values, not against the implementation under test.
    assert report_a.binding_bound is not None
    assert report_b.binding_bound is not None
    assert report_a.binding_bound.high == pytest.approx(expected_ms_a, abs=1e-6)
    assert report_b.binding_bound.high == pytest.approx(expected_ms_b, abs=1e-6)
    # The low edge is unchanged from KOISTINEN_MARBURGER -- only the high edge moved.
    assert report_a.binding_bound.low == KM_COMPETING_PRODUCT_ONSET
    assert report_b.binding_bound.low == KM_COMPETING_PRODUCT_ONSET

    # A: comfortably inside the window.
    assert not report_a.outside_envelope
    assert report_a.action is ValidityAction.WITHIN_ENVELOPE
    # B: clearly outside, driven by the composition-dependent edge -- a control-space
    # violation, since "temperature" is declared ValiditySpace.CONTROL here exactly as
    # in KOISTINEN_MARBURGER, so CONTROL_INVERSE is the action the existing logic gives.
    assert report_b.outside_envelope
    assert report_b.action is ValidityAction.CONTROL_INVERSE
    assert report_b.binding_space is ValiditySpace.CONTROL
    # The crossing itself, in the vocabulary the report exists to produce.
    assert report_a.worst_factor <= 1.0 < report_b.worst_factor


def test_composition_dependent_ms_evaluate_and_report_agree(
    observe: ObservationRecorder,
) -> None:
    """`ConstitutiveForm.evaluate` and `.report` are independent call paths
    (`ConstitutiveForm.report` does not invoke `.evaluate`), so nothing structural
    stops them disagreeing about what `Ms` is for a composition-dependent form. This
    is what keeps `koistinen_marburger_composition_dependent` honest: both read `Ms`
    from the same `_andrews_ms` helper rather than one holding a stale fixed value.
    """
    from omi_domains.flagship_constitutive.forms import (
        KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT,
    )

    composition = _andrews_wt_percent(np.log(np.array([0.001, 0.004, 0.995])))  # composition B
    expected_ms = 539.0 - 423.0 * composition["carbon"] - 30.4 * composition["manganese"]

    # Just above the composition's own Ms: evaluate() must clamp to zero (no athermal
    # transformation), the same clamping rule KOISTINEN_MARBURGER's own evaluate() uses.
    values = {**composition, "temperature": expected_ms + 1.0}
    fraction_above_ms = float(
        KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT.evaluate(values)[0]
    )
    report_above_ms = KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT.report(
        {"temperature": values["temperature"]}, evaluated_at=composition
    )

    observe(
        "evaluate_report_agreement_above_ms",
        {"fraction": fraction_above_ms, "outside_envelope": report_above_ms.outside_envelope},
        "fraction == 0.0 and outside_envelope is True -- both read the same Ms",
    )
    assert fraction_above_ms == pytest.approx(0.0)
    assert report_above_ms.outside_envelope
