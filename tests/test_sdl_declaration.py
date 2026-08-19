"""The discovery domain's declaration (ADR-059, ADR-060, docs/DECISIONS.md): does it
differ from both existing domains on every item, and does it make live the things it was
declared to make live?

**Declaration only.** No operator is implemented and no campaign is run, so nothing here
advances a state. What is checked is that the declaration is comparable (Core §4: "it is
comparative... which is what converts a collection of examples into evidence of
generality"), that the decision-extension refinements are exercised rather than asserted, and that the
one diagnostic Part 5(1) found dark on contrast is now available.
"""

from __future__ import annotations

import pytest

from omi.interface import ParameterRole, SpecificationVersion, diff
from omi.proposed.constitutive import (
    ConstitutivelyConstrained,
    RegimeVerdict,
    check_composition_regime,
)
from omi.proposed.decision import (
    AttainabilityVerdict,
    CoupledQuantityDeclaration,
    CouplingDirection,
    DeclaredDomainKind,
    SpeciesRole,
    TrackedDimensions,
)
from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.contrast.operators import CYCLING
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.sdl.forms import COMPOSITION_VALIDITY_INTERVAL, SDL_FORMS
from omi_domains.sdl.interface import SDL_DECLARATION, SDL_V13_CORE
from omi_domains.sdl.state import DESCRIPTORS, REGIONS, SPECIES

from tests.conftest import ObservationRecorder


def test_the_declaration_differs_from_both_existing_domains_on_every_item(
    observe: ObservationRecorder,
) -> None:
    """Core §4's comparability requirement, on the third domain.

    A third domain that agreed with either existing one on several items would add little
    to the generality claim — the pair was chosen to *invert* each other, and a third
    should be a third case rather than a variant. Every one of the declared items differs
    from both — eight since ADR-071 split item 1, and the new item 1b differs too: this
    domain declares mean composition as an operator-family index where flagship declares no
    parameter at all.
    """
    against_flagship = diff(SDL_V13_CORE, FLAGSHIP_DECLARATION)
    against_contrast = diff(SDL_V13_CORE, CONTRAST_DECLARATION)
    observe("sdl_vs_flagship_items_differing", sorted(k for k, v in against_flagship.items() if v), "all")
    observe("sdl_vs_contrast_items_differing", sorted(k for k, v in against_contrast.items() if v), "all")

    assert all(against_flagship.values()), (
        f"the discovery domain agrees with flagship on {sorted(k for k, v in against_flagship.items() if not v)}"
    )
    assert all(against_contrast.values()), (
        f"the discovery domain agrees with contrast on {sorted(k for k, v in against_contrast.items() if not v)}"
    )


def test_the_declaration_carries_its_own_specification_version(
    observe: ObservationRecorder,
) -> None:
    """E-35's finding does not stop applying at the second extension.

    A level name is not self-describing without the **claim target** it is stated against, so
    a declaration carrying the decision-extension refinements must not be representable as a
    constitutive-extension claim. The target is a read-only property, so it cannot be
    constructed wrong. Named by purpose rather than by a version number per ADR-067.
    """
    observe("sdl_specification_version", SDL_DECLARATION.specification_version.value, "proposed-decision-extension")
    observe("sdl_decision_kind_declared", bool(SDL_DECLARATION.decision_kind.strip()), "True")
    assert SDL_DECLARATION.specification_version is SpecificationVersion.PROPOSED_DECISION_EXTENSION
    assert SDL_DECLARATION.decision_kind.strip(), (
        "E-43's finding is that a level plus a version is still not self-describing without "
        "the purpose the claim is made for; the field exists to carry it"
    )


def test_one_species_holds_two_different_roles_in_two_regions_of_one_chain(
    observe: ObservationRecorder,
) -> None:
    """**ADR-051's central claim, exercised rather than asserted.**

    The promoter is a `CONTROL` in the bulk — chosen per sample by the recipe — and a
    `STATE` in the surface layer, where it segregates during calcination and evolves under
    that operator. Simultaneously, in one chain. A declaration that could not express this
    would force one reading to be the default, which is the failure ADR-051 exists to
    prevent.
    """
    roles = SDL_DECLARATION.roles_for("promoter")
    observe("promoter_roles_by_region", {r: v.value for r, v in roles.items()}, "control in bulk, state in surface")
    observe("declared_regions", REGIONS, "narrative only")

    assert roles["bulk"] is SpeciesRole.CONTROL
    assert roles["surface_layer"] is SpeciesRole.STATE
    assert len(set(roles.values())) == 2, (
        "no species now holds two roles across regions, so ADR-051's per-region claim is "
        "declared but not exercised"
    )


def test_a_parameter_only_species_is_mechanically_identifiable(
    observe: ObservationRecorder,
) -> None:
    """E-29's part 2, made mechanical.

    E-29 found that "a readout depending only on parameters cannot be flagged". With roles
    declared per region, a species that is `PARAMETER` everywhere it appears is identifiable
    without reading prose — which is what lets a readout of the *grade* be separated from a
    readout of the *process*, Core §2.6's property/performance distinction.
    """
    parameter_only = SDL_DECLARATION.parameter_only_species()
    observe("parameter_only_species", parameter_only, "== ('support',)")
    observe("declared_species", SPECIES, "narrative only")

    assert parameter_only == ("support",)


def test_the_composition_declaration_states_where_constancy_will_fail_and_why(
    observe: ObservationRecorder,
) -> None:
    """ADR-050's diagnosis, declared in advance rather than discovered in Part 6 —
    **re-expressed at ADR-071, because the quantity it is about moved items.**

    Mean composition used to be declared here as an `INVARIANT`-coupled quantity on the
    decision extension, which `SpeciesRole.PARAMETER`'s own docstring describes as the
    parameter role realised through a coupling direction — i.e. the workaround
    `docs/V1.4-EDITS.md` E-46 predicted would be needed while item 1 had nowhere to host an
    operator-family index. Stage 2 gave it one, so it is now item 1b's `ParameterRole` on
    `SDL_V13_CORE`, with `constant_over=("bulk",)` and `also_state_in_regions=("surface_layer",)`.

    **ADR-050's diagnosis is unchanged by the move, and that is the point of this test.** The
    bulk is closed; the surface layer is not, because promoter segregates into it during
    calcination; so a constancy check over the surface layer is still *expected to fail*, and
    the failure is still the diagnosis rather than a defect. The two halves are now declared
    in two items — the constant-over-bulk half in 1b, the `DEPLETED_BY`
    surface_promoter_enrichment half here — which is E-46's own distinction rather than a
    dilution of ADR-050's.
    """
    parameters = {p.name: p for p in SDL_V13_CORE.declared_parameters}
    invariant = SDL_DECLARATION.quantities_with_coupling(CouplingDirection.INVARIANT)
    depleted = SDL_DECLARATION.quantities_with_coupling(CouplingDirection.DEPLETED_BY)
    determined = SDL_DECLARATION.quantities_with_coupling(CouplingDirection.DETERMINED_BY)

    observe("item_1b_parameter_names", tuple(sorted(parameters)), "== ('mean_composition',) since ADR-071")
    observe("mean_composition_constant_over", parameters["mean_composition"].constant_over, "== ('bulk',)")
    observe(
        "mean_composition_also_state_in_regions",
        parameters["mean_composition"].also_state_in_regions,
        "== ('surface_layer',) -- E-46's dual-role clause, on a real domain",
    )
    observe("invariant_quantities", invariant, "== () -- relocated to item 1b by ADR-071")
    observe("depleted_by_quantities", depleted, "non-empty -- ADR-050's corrective case declared")
    observe("determined_by_quantities", determined, "non-empty")

    assert tuple(sorted(parameters)) == ("mean_composition",)
    assert parameters["mean_composition"].constant_over == ("bulk",)
    assert parameters["mean_composition"].also_state_in_regions == ("surface_layer",), (
        "the surface layer is where constancy is expected to fail; E-46 requires the dual "
        "role to be declared rather than left to the closure note's prose"
    )
    assert invariant == (), (
        "mean_composition is item 1b's occupant since ADR-071; an INVARIANT-coupled entry "
        "would be the second declaration site the split exists to remove"
    )
    assert depleted, "no DEPLETED_BY quantity is declared, so E-25's refusal case is unexercised"
    assert determined, "no DETERMINED_BY quantity is declared, so the closure residual has no subject"


def test_the_nonlocal_quantity_is_declared_global_point_not_a_field(
    observe: ObservationRecorder,
) -> None:
    """E-22's revised proposal, exercised on a third independent domain.

    Pore-network accessibility has **no local value even in principle** — reachability is a
    property of the connected network, not of a point — so typing it as a field over the
    body would over-localise it in exactly the way E-22 found Core §2.5's repair does to
    `ν`. `GLOBAL_POINT` is the case that forced E-22's first proposal to be withdrawn, and
    this is a fourth domain exhibiting it.
    """
    accessibility = next(
        q for q in SDL_DECLARATION.coupled_quantities if q.name == "pore_network_accessibility"
    )
    observe("accessibility_domain_kind", accessibility.domain_kind.value, "global_point")
    observe("accessibility_tracked", accessibility.tracked.value, "none")
    assert accessibility.domain_kind is DeclaredDomainKind.GLOBAL_POINT
    assert accessibility.tracked is TrackedDimensions.NONE


def test_every_tracked_dimension_declaration_carries_a_justification(
    observe: ObservationRecorder,
) -> None:
    """ADR-049's required justification, enforced at construction and non-empty in fact.

    Required at every kind including the degenerate one, because a `GLOBAL_POINT`
    declaration tracked at `NONE` is an assertion of spatial uniformity — the assumption
    v1.3 never made anyone defend (E-44). The field is free text and therefore checks
    nothing by itself; what it buys is visibility to `interface.diff`.
    """
    lengths = {q.name: len(q.tracked_justification.strip()) for q in SDL_DECLARATION.coupled_quantities}
    observe("tracked_justification_lengths", lengths, "each > 0")
    assert all(length > 0 for length in lengths.values())

    with pytest.raises(ValueError, match="justification"):
        CoupledQuantityDeclaration(
            name="unjustified",
            domain_kind=DeclaredDomainKind.GLOBAL_POINT,
            coupling=CouplingDirection.DETERMINED_BY,
            tracked=TrackedDimensions.NONE,
            tracked_justification="   ",
        )


def test_the_descriptor_basis_is_declared_with_its_underlying_space(
    observe: ObservationRecorder,
) -> None:
    """ADR-052: both are carried, because a descriptor without its ground truth cannot be
    held out against.

    The claim "this operator depends on chemistry only through these functionals" is
    falsifiable exactly by varying the underlying space at fixed descriptors — which
    requires both to be declared. A declaration carrying only descriptors is refused at
    construction.

    **Read from item 1b since ADR-071**, where mean composition now lives. ADR-052's rule
    travelled with the quantity rather than staying behind with the carrier: `ParameterRole`
    enforces the same descriptor-needs-its-underlying-space refusal that
    `CoupledQuantityDeclaration` does, and both refusals are exercised below so the rule is
    checked on the item that actually hosts the declaration *and* on the one that no longer
    does.
    """
    composition = next(p for p in SDL_V13_CORE.declared_parameters if p.name == "mean_composition")
    observe("descriptor_basis", composition.descriptor_basis, f"== {DESCRIPTORS}")
    observe("underlying_space", composition.underlying_space, "the raw fractions")
    assert composition.descriptor_basis == DESCRIPTORS
    assert composition.underlying_space == SPECIES

    # Item 1b's own refusal, on the carrier that now hosts the declaration.
    with pytest.raises(ValueError, match="underlying space"):
        ParameterRole(
            name="descriptors_without_truth",
            indexes=("SomeOperator",),
            justification="justified",
            descriptor_basis=("some_descriptor",),
        )

    # And the decision extension's, unchanged -- ADR-052 applies wherever a descriptor
    # basis is declarable, not only where mean composition happens to be declared.
    with pytest.raises(ValueError, match="underlying space"):
        CoupledQuantityDeclaration(
            name="descriptors_without_truth",
            domain_kind=DeclaredDomainKind.GLOBAL_POINT,
            coupling=CouplingDirection.DETERMINED_BY,
            tracked=TrackedDimensions.NONE,
            tracked_justification="justified",
            descriptor_basis=("some_descriptor",),
        )


def test_the_attainable_region_certifies_each_kind_of_infeasibility_distinctly(
    observe: ObservationRecorder,
) -> None:
    """**The object ADR-053 said no domain supplied.**

    ADR-053 declined to design the composition inverse's infeasibility certificate because
    it needs a declared attainable region and none existed. This is that region, and the
    certificate it produces names *which* constraint bound — which is what makes the
    composition inverse a third inverse problem rather than a relabelled structure inverse
    (Core §5 separates its existing pair by exactly that criterion).
    """
    region = SDL_DECLARATION.attainable_region
    assert region is not None

    inside_underlying = {"metal_a": 0.15, "metal_b": 0.10, "promoter": 0.02, "support": 0.73}
    inside_descriptors = {"valence_electron_count": 8.3, "mixing_enthalpy": -18.0, "support_acidity": 0.5}
    inside = region.report(inside_descriptors, inside_underlying)
    observe("attainable_inside_verdict", inside.verdict.value, "attainable")
    observe("attainable_inside_worst_factor", inside.worst_factor, "<= 1.0")
    assert inside.verdict is AttainabilityVerdict.ATTAINABLE
    assert inside.attainable

    far_descriptors = dict(inside_descriptors, valence_electron_count=14.0)
    outside = region.report(far_descriptors, inside_underlying)
    observe("attainable_outside_descriptor_verdict", outside.verdict.value, "outside_descriptor_bounds")
    observe("attainable_outside_binding", outside.binding_constraint, "the descriptor that bound")
    assert outside.verdict is AttainabilityVerdict.OUTSIDE_DESCRIPTOR_BOUNDS
    assert outside.binding_constraint == "descriptor:valence_electron_count"

    unnormalised = dict(inside_underlying, support=0.90)
    broken = region.report(inside_descriptors, unnormalised)
    observe("attainable_unnormalised_verdict", broken.verdict.value, "underlying_infeasible")
    assert broken.verdict is AttainabilityVerdict.UNDERLYING_INFEASIBLE

    excluded_underlying = {"metal_a": 0.05, "metal_b": 0.25, "promoter": 0.07, "support": 0.63}
    excluded = region.report(inside_descriptors, excluded_underlying)
    observe("attainable_excluded_pair_verdict", excluded.verdict.value, "excluded_pair")
    assert excluded.verdict is AttainabilityVerdict.EXCLUDED_PAIR


def test_a_missing_constraint_value_raises_rather_than_being_skipped() -> None:
    """A constraint silently omitted from a certificate is a constraint whose violation
    cannot be seen — the shape `docs/V1.4-EDITS.md` §6 documents repeatedly, and the same
    rule ADR-043's `ValidityRange.report` already applies to validity bounds."""
    region = SDL_DECLARATION.attainable_region
    assert region is not None
    with pytest.raises(ValueError, match="no value supplied"):
        region.report({"valence_electron_count": 8.3}, {"metal_a": 0.15})


def test_the_validity_report_is_live_on_this_domain_and_dark_on_contrast(
    observe: ObservationRecorder,
) -> None:
    """**Part 5(1)'s negative result carried forward, and what changes.**

    On contrast the validity report was structurally unavailable: no declared constitutive
    form, so nothing to report against. This domain declares two, so the report exists, has
    two forms to aggregate a chain-level worst case over, and can say for a given evaluation
    which declared bound binds and in which space.

    What it still cannot do is say whether the declared mechanism set is *complete* for the
    regime — M11.5's measured finding, and the reason the buy-physics row is "signalled on
    the wrong axis". Declaring forms makes the diagnostic live; it does not make it
    sufficient, and the declaration says so rather than leaving Part 6 to discover it.
    """
    observe("sdl_declared_form_count", len(SDL_FORMS), ">= 2, so a chain-level worst case aggregates")
    observe(
        "contrast_operator_is_constitutively_constrained",
        isinstance(CYCLING, ConstitutivelyConstrained),
        "False -- the diagnostic stays dark there",
    )
    observe(
        "composition_validity_interval_declared",
        sorted(COMPOSITION_VALIDITY_INTERVAL),
        "ADR-054's second-order range, over the descriptor basis",
    )

    assert len(SDL_FORMS) >= 2
    assert not isinstance(CYCLING, ConstitutivelyConstrained)
    assert set(COMPOSITION_VALIDITY_INTERVAL) == set(DESCRIPTORS), (
        "ADR-054's composition-dependent validity is declared over a different coordinate set "
        "than the descriptor basis, so the two cannot be evaluated together"
    )

    for form in SDL_FORMS:
        assert form.validity.bounds, f"form {form.name} declares no validity range"
        assert form.parameters, f"form {form.name} declares no fitted parameters"


def test_the_erasure_inventory_is_non_empty_which_predicts_the_e48_extreme(
    observe: ObservationRecorder,
) -> None:
    """The E-48 triage's prediction, applied to this domain before Part 6 runs it.

    §5.2a measured that which degeneracy a chain's near-diagonal share exhibits tracks one
    declared property: whether the chain declares an erasure operator. This domain declares
    one (calcination genuinely destroys precursor-history information), so it is predicted
    to sit at **flagship's** extreme — shares pinned near 0 or 1, margin far from the
    threshold — rather than on contrast's rational ladder.

    That is not a rescue. Both extremes are degenerate; declaring an erasure moves the
    degeneracy rather than removing it, and the observed/inferred label will be near-trivial
    here for the opposite reason. Recorded in the declaration so Part 6 inherits the
    expectation instead of rediscovering it.
    """
    observe("sdl_erasure_inventory", SDL_V13_CORE.erasure_inventory, "non-empty")
    observe("contrast_erasure_inventory", CONTRAST_DECLARATION.erasure_inventory, "empty -- the inversion")
    assert SDL_V13_CORE.erasure_inventory, (
        "the discovery domain no longer declares an erasure, so the E-48 extreme it is "
        "predicted to sit at changes"
    )
    assert not CONTRAST_DECLARATION.erasure_inventory


# --- ADR-078 Decision 3: the regime-boundary check, boundary case included ---------


def test_check_composition_regime_reads_the_boundary_as_inside_not_outside(
    observe: ObservationRecorder,
) -> None:
    """**The ADR-078 Gate item 5 oracle**: three constructed descriptor tuples against
    this domain's own `COMPOSITION_VALIDITY_INTERVAL` -- comfortably inside, comfortably
    outside on exactly one descriptor, and exactly at a declared edge.

    Not wired into SDL's forms or any operator, per ADR-078's scope note: SDL has no
    evolution operator calling `report()` yet (ADR-064 built the discovery domain's
    three operators, not this check), so there is nothing here for the regime check to
    guard. This test exercises `check_composition_regime` as domain-neutral machinery,
    reading `COMPOSITION_VALIDITY_INTERVAL` as data rather than adding a new declared
    capability to the domain.

    **The boundary case is the one worth getting right rather than assumed.**
    `ExtrapolationReport.outside_envelope` is `worst_factor > 1.0` — strictly greater,
    so a value exactly at an edge reads as inside. `check_composition_regime` uses the
    same two-sided arithmetic `ValidityBound.extrapolation_factor` does
    (`|value - centre| / half_width`), so the same convention should hold here, and
    this test confirms it does rather than assuming the two implementations agree.
    """
    centre = {
        name: 0.5 * (low + high) for name, (low, high) in COMPOSITION_VALIDITY_INTERVAL.items()
    }

    # Case 1: every descriptor at its interval's own centre -- comfortably inside.
    within = dict(centre)
    report_within = check_composition_regime(within, COMPOSITION_VALIDITY_INTERVAL)

    # Case 2: mixing_enthalpy pushed far past its high edge (-4.0); the other two stay
    # at their centres, so exactly one descriptor is responsible.
    outside = dict(centre)
    outside["mixing_enthalpy"] = 10.0
    report_outside = check_composition_regime(outside, COMPOSITION_VALIDITY_INTERVAL)

    # Case 3: support_acidity placed EXACTLY at its declared high edge (0.85); the
    # other two stay at their centres.
    low, high = COMPOSITION_VALIDITY_INTERVAL["support_acidity"]
    on_edge = dict(centre)
    on_edge["support_acidity"] = high
    report_on_edge = check_composition_regime(on_edge, COMPOSITION_VALIDITY_INTERVAL)

    observe(
        "regime_within_verdict",
        report_within.verdict.value,
        f"== {RegimeVerdict.WITHIN_INTERVAL.value!r}",
    )
    observe(
        "regime_outside_verdict_and_binding",
        (report_outside.verdict.value, report_outside.binding_descriptor),
        "== ('outside_interval', 'mixing_enthalpy')",
    )
    observe(
        "regime_on_edge_verdict_and_factor",
        (report_on_edge.verdict.value, report_on_edge.factor),
        "verdict WITHIN_INTERVAL, factor None -- an edge value reads as inside, not outside",
    )

    # Case 1: comfortably inside.
    assert report_within.verdict is RegimeVerdict.WITHIN_INTERVAL
    assert report_within.binding_descriptor is None
    assert report_within.factor is None

    # Case 2: comfortably outside, on exactly the descriptor that was pushed.
    assert report_outside.verdict is RegimeVerdict.OUTSIDE_INTERVAL
    assert report_outside.binding_descriptor == "mixing_enthalpy"
    assert report_outside.factor is not None
    assert report_outside.factor > 1.0

    # Case 3: exactly at the edge -- inside, per this file's own boundary convention,
    # confirmed against the arithmetic directly: |high - centre| / half_width == 1.0.
    assert high - centre["support_acidity"] == pytest.approx(0.5 * (high - low))
    assert report_on_edge.verdict is RegimeVerdict.WITHIN_INTERVAL
    assert report_on_edge.binding_descriptor is None
    assert report_on_edge.factor is None


def test_check_composition_regime_raises_on_a_missing_descriptor() -> None:
    """A descriptor named in the declared interval but absent from the supplied
    composition is a malformed call, not a regime finding -- distinct from
    `RegimeVerdict.OUTSIDE_INTERVAL`, which is a diagnosis with an answer."""
    incomplete = {
        name: 0.5 * (low + high)
        for name, (low, high) in COMPOSITION_VALIDITY_INTERVAL.items()
        if name != "mixing_enthalpy"
    }
    with pytest.raises(ValueError, match="mixing_enthalpy"):
        check_composition_regime(incomplete, COMPOSITION_VALIDITY_INTERVAL)
