"""The discovery domain's declaration: Core §4's seven items, plus the decision extension's refinements
(ADR-059, ADR-060).

Machine-diffable against flagship and contrast through `omi.interface.diff`, because the
v1.3 seven items are held whole inside the constitutive-extension carrier, which is held whole inside the
decision-extension carrier (ADR-042 applied twice). Nothing here implements an operator or runs a
campaign.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ScopeDeclaration
from omi.proposed.declaration import ExtendedDeclaration
from omi.proposed.decision import (
    AttainableRegion,
    CouplingDirection,
    CoupledQuantityDeclaration,
    DeclaredDomainKind,
    DecisionExtendedDeclaration,
    SpeciesRole,
    SpeciesRoleDeclaration,
    TrackedDimensions,
)

from omi_domains.sdl.forms import SDL_FORMS
from omi_domains.sdl.state import DESCRIPTORS, SDL_SCHEMA
from omi.observability import ObservedInferredConvention

SDL_V13_CORE = InstantiationDeclaration(
    state_schema=SDL_SCHEMA,
    control_space=(
        "Acquisition-determined: the preparation recipe (precursor fractions, calcination "
        "temperature and hold) plus the evaluation condition (temperature, partial pressure) "
        "are chosen by an acquisition policy deciding what to make next, not by an apparatus "
        "operator following a route and not by a service duty cycle. U_adm is bounded by the "
        "synthesis rig's temperature and hold limits and by the attainable region declared "
        "below. The inverse here is a COMPOSITION inverse (Core §5 as ADR-053 extends it), "
        "distinct from flagship's process inverse and contrast's usage inverse."
    ),
    erasure_inventory=("CALCINATION",),
    readout_catalogue=(
        "turnover_frequency: Type-0/Class-A",
        "selectivity: Type-0/Class-A",
        "deactivation_onset: Type-0/Class-B",
    ),
    observation_suite=(
        "dispersed phase loading (elemental analysis)",
        "mean particle size (diffraction line broadening)",
        "turnover frequency (reactor test)",
        "selectivity (product analysis)",
    ),
    invariants=(
        "metal_mass_conservation_across_calcination",
        "mean_particle_size_monotone_nondecreasing",
        "site_density_monotone_nonincreasing",
    ),
    scale_structure=(
        "Two-tier: site-scale kinetics homogenised to pellet-scale effective rate, then pellet "
        "to reactor bed. Only the site-to-pellet homogenisation is declared here; the closure "
        "defect across it is NOT measured (Spec §6's procedure is an anti-goal, CLAUDE.md §9), "
        "so it is declared as unmeasured rather than assumed small."
    ),
)
"""Core §4's seven items. Deliberately the same shape as the other two domains, so
`omi.interface.diff` compares three declarations rather than two plus a special case."""


SDL_EXTENDED = ExtendedDeclaration(v13_core=SDL_V13_CORE, constitutive_forms=SDL_FORMS)
"""The constitutive-extension layer: two declared constitutive forms (Spec §2.2's proposed category).

**This is what makes the validity report live**, and it is the one diagnostic Part 5(1)
found structurally unavailable on contrast."""


MEAN_COMPOSITION = CouplingDirection.INVARIANT
"""Named so the role/coupling identification ADR-051 left for Part 3 to settle is visible
at the point of declaration rather than only in prose."""


SDL_DECLARATION = DecisionExtendedDeclaration(
    extended_core=SDL_EXTENDED,
    decision_kind=(
        "campaign / discovery: deciding WHAT TO MAKE. The third of Core §5's decisions once "
        "ADR-053's composition inverse is admitted — flagship decides a route for a given "
        "material, contrast decides a duty cycle for a given artefact, and this decides the "
        "material itself."
    ),
    coupled_quantities=(
        CoupledQuantityDeclaration(
            name="mean_composition",
            domain_kind=DeclaredDomainKind.REGIONS,
            coupling=CouplingDirection.INVARIANT,
            tracked=TrackedDimensions.NONE,
            tracked_justification=(
                "Bulk composition is uniform by preparation: the precursor is a mixed solution, so "
                "there is no gradient to track in the bulk region. The surface layer is declared "
                "separately as its own region rather than as a through-thickness profile, because "
                "the campaign resolves it as a single averaged enrichment (one surface-sensitive "
                "measurement) and declaring a profile would claim a resolution the observation "
                "suite does not supply."
            ),
            regions=("bulk", "surface_layer"),
            descriptor_basis=DESCRIPTORS,
            underlying_space=("metal_a", "metal_b", "promoter", "support"),
            closure_note=(
                "The BULK region is closed over a preparation-and-evaluation chain: no metal "
                "leaves. The SURFACE_LAYER region is NOT closed — promoter segregates into it "
                "from the bulk during calcination — so mean composition over the surface layer "
                "must be declared DEPLETED_BY and not INVARIANT. Declared here as INVARIANT over "
                "the bulk only; ADR-050's constancy check is expected to FAIL over the surface "
                "layer, and that failure is the diagnosis rather than a defect."
            ),
        ),
        CoupledQuantityDeclaration(
            name="pore_network_accessibility",
            domain_kind=DeclaredDomainKind.GLOBAL_POINT,
            coupling=CouplingDirection.DETERMINED_BY,
            tracked=TrackedDimensions.NONE,
            tracked_justification=(
                "Accessibility has NO local value even in principle: whether a site is reachable "
                "is a property of the whole connected pore network, not of a point. This is Core "
                "§3.1's own reason for carrying nu separately and E-22's revised GLOBAL_POINT "
                "case — the one that forced E-22's first proposal (a field over the body) to be "
                "withdrawn. Tracking it at any spatial resolution would over-localise a quantity "
                "with no localisation."
            ),
            closure_note="",
        ),
        CoupledQuantityDeclaration(
            name="surface_promoter_enrichment",
            domain_kind=DeclaredDomainKind.REGIONS,
            coupling=CouplingDirection.DEPLETED_BY,
            tracked=TrackedDimensions.NONE,
            tracked_justification=(
                "Declared per-region rather than as a profile for the same reason as "
                "mean_composition: one surface-sensitive modality resolves an average, not a "
                "gradient. Declared DEPLETED_BY because the promoter arriving at the surface "
                "LEAVES the bulk — the conserved quantity is total promoter, the aggregation "
                "functional is the region mean, and the flux is the segregation current during "
                "calcination."
            ),
            regions=("surface_layer",),
            closure_note="",
        ),
    ),
    species_roles=(
        SpeciesRoleDeclaration("metal_a", "bulk", SpeciesRole.CONTROL, "set per sample by the recipe"),
        SpeciesRoleDeclaration("metal_b", "bulk", SpeciesRole.CONTROL, "set per sample by the recipe"),
        SpeciesRoleDeclaration(
            "promoter",
            "bulk",
            SpeciesRole.CONTROL,
            "set per sample by the recipe; its bulk value is chosen, not observed",
        ),
        SpeciesRoleDeclaration(
            "promoter",
            "surface_layer",
            SpeciesRole.STATE,
            "the same species, a STATE in this region: it segregates during calcination and "
            "evolves under that operator. ADR-051's central claim exercised — one species, two "
            "roles, one chain, simultaneously.",
        ),
        SpeciesRoleDeclaration(
            "support",
            "bulk",
            SpeciesRole.PARAMETER,
            "fixed by the support batch for the whole campaign; indexes the operator family and "
            "is transported by nothing. ADR-051's Parameter role, i.e. E-29's missing category.",
        ),
        SpeciesRoleDeclaration(
            "support",
            "surface_layer",
            SpeciesRole.PARAMETER,
            "parameter in both regions, so it is reported by parameter_only_species()",
        ),
    ),
    attainable_region=AttainableRegion(
        descriptor_bounds={
            "valence_electron_count": (6.0, 11.0),
            "mixing_enthalpy": (-45.0, 5.0),
            "support_acidity": (0.05, 0.95),
        },
        underlying_bounds={
            "metal_a": (0.0, 0.30),
            "metal_b": (0.0, 0.30),
            "promoter": (0.0, 0.08),
            "support": (0.40, 1.0),
        },
        sums_to_one=("metal_a", "metal_b", "promoter", "support"),
        excluded_pairs=(
            (
                "promoter",
                "metal_b",
                0.010,
                "a promoter-rich, metal_b-rich precursor precipitates a mixed oxide during "
                "drying, so the intended dispersed phase never forms; the pair is excluded by "
                "the preparation chemistry, not by the target property. The product budget "
                "0.010 is where 'both high' begins for these two ranges (promoter is bounded "
                "at 0.08 and metal_b at 0.30, so the reachable product tops out near 0.024): it "
                "admits a promoter-rich formulation at low metal_b and a metal_b-rich one at low "
                "promoter, and excludes only the corner where both are high. Declared by the "
                "domain rather than by the framework, because where the interaction bites is a "
                "fact about this chemistry.",
            ),
        ),
        route_note=(
            "The declared route is incipient-wetness impregnation followed by calcination. It "
            "reaches the interior of the region above but NOT the high-loading corner: total metal "
            "above ~0.45 exceeds the support's pore volume in one impregnation and would require a "
            "multi-step route this declaration does not include. Stated in prose because it is the "
            "one constraint here that is not machine-checkable from the declared coordinates alone "
            "— a route bound is a statement about the apparatus, and item 2's admissible set is "
            "where it belongs; recorded here so a reader does not mistake the checkable "
            "constraints for the whole certificate."
        ),
    ),
    scope=ScopeDeclaration(
        control_axis_evidence=(
            "Item 2 plus decision_kind jointly, and stronger than E-44's generic 'strong but "
            "implicit' finding for the other two domains: control_space states directly that "
            "'an acquisition policy decides what to make next,' and decision_kind names the same "
            "axis as the object of the campaign decision itself, not merely its admissible set."
        ),
        hidden_state_evidence=(
            "Item 1's z slot: active_site_density and defect_site_fraction, which state.py's own "
            "docstring records as 'not resolved by any declared modality' — governing turnover "
            "but absent from observation_suite (item 5). The clearest of the three domains on "
            "this feature, because the unresolved variables are named rather than merely implied "
            "by an incomplete observation_suite."
        ),
        structure_mediated_response_evidence=(
            "The pore_network_accessibility coupled quantity (DETERMINED_BY, GLOBAL_POINT): "
            "turnover_frequency and selectivity (item 4) depend on whether a site is reachable "
            "through the connected pore network, a structural property with 'no local value even "
            "in principle' per that declaration's own tracked_justification. Response is mediated "
            "by network structure, not read directly off composition."
        ),
        recurring_decision_under_uncertainty_evidence=(
            "decision_kind names this directly: 'campaign / discovery: deciding WHAT TO MAKE,' "
            "repeated over an acquisition policy's cycles under the epistemic uncertainty the "
            "attainable_region and species_roles declarations exist to bound. E-44 found this "
            "feature has 'no interface item at all' under the seven items alone; the decision "
            "extension is what supplies it, and this domain is where ADR-048 built it to be "
            "exercised."
        ),
        scope_exit_criterion=(
            "Outside attainable_region's declared bounds (descriptor_bounds, underlying_bounds, "
            "the sums_to_one simplex, or inside an excluded_pairs corner) this instantiation MUST "
            "be reported out of scope: the constitutive forms' validity range and the campaign's "
            "own reachability certificate (ADR-053) are stated relative to that region, not "
            "beyond it. route_note further narrows reachability inside the region without "
            "widening it, so the attainable_region bound is the binding one."
        ),
    ),
    symmetry_group_actions=(),
    # Empty, not undeclared-by-omission: no built form here is a function of an oriented
    # field (no crystallographic texture, no directional loading) for any declared group to
    # act on. Composition is a simplex-valued fraction vector, permutation-symmetric in the
    # species labels only in the trivial sense that the labels are already generic
    # ("metal_a"/"metal_b") rather than a physical claim worth declaring a group over
    # (docs/V1.4-EDITS.md E-30).
)
"""The full decision-extension declaration.

Four things this domain declares that neither existing domain does: **constitutive forms
with composition-dependent validity** (making the validity report live), **species roles
per region** (making ADR-051's one-species-two-roles claim exercised rather than asserted),
an **attainable region** (the object ADR-053 said no domain supplied, without which its
composition-inverse infeasibility certificate could not be designed), and — as of
:class:`~omi.interface.ScopeDeclaration` (`docs/V1.4-EDITS.md` E-44, E-52; ADR-069, Stage 1
Decision C) — the first declaration to evidence all four scope features with something
stronger than an implicit reading, because ``decision_kind`` and ``z``'s named-but-unresolved
variables give this domain the most direct textual evidence of the three built so far.
``symmetry_group_actions`` is declared empty: nothing here is a function of an oriented field.
"""


SDL_OBSERVED_INFERRED = ObservedInferredConvention(
    dominance_factor=2.0,
    abstention_band=0.5,
    near_diagonal_window=0,
    justification=(
        "Window 0: the evaluation reading and the preparation steps are separated by a declared "
        "erasure (CALCINATION), so nothing one segment away is near-diagonal in any sense the "
        "physics supports. rho = 2.0 for the same reason as flagship's -- an erasure makes the "
        "ratio structurally decisive, so a demanding factor is free. The band is WIDER than "
        "either existing domain's, at 0.5, and that is the one value here chosen against "
        "convenience: this domain's chain is not implemented (ADR-060), so no measurement "
        "supports a narrow band, and a wide band abstains more often. Abstaining while "
        "undeclared-by-measurement is the honest default, and ADR-061's required abstained "
        "fraction makes the cost of it visible rather than hidden."
    ),
)
"""The discovery domain's declared observed/inferred convention (ADR-061; Spec §3.3).

Declared **before** any operator exists, which is the point: the convention is part of the
domain's declaration rather than a tuning knob discovered while looking at results."""
