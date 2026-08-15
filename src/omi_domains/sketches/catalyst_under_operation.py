"""Catalyst-under-operation sketch (Spec §11.4, Core §7.3 [Pass D],
ROADMAP M10.1): the fourth, deliberately awkward sketch. Interface-only
per ADR-038 (docs/DECISIONS.md): no operators, no readouts, no build
function.

Chosen per the redirected purpose of this sketch (docs/V1.4-EDITS.md
E-22's addendum has already answered Core §6.2's literal fifth-slot
question -- no domain needed a fifth slot; nu is mistyped instead). What
this sketch tests is different: whether the four slots are a PARTITION
(every domain occupies all four, in some proportion) or a CONVENIENCE
(the schema quietly assumes a non-trivial bulk that not every domain has).

A single heterogeneous catalyst pellet under steady operation is chosen
because Core §3.1 justifies Gamma by it being "the controlling state" in
a large class of systems -- here it is not one controlling slot among
four, it is essentially all there is: catalytic activity, selectivity,
and deactivation are governed entirely by the exposed surface/active-site
state, and the bulk support is deliberately engineered to be inert,
stable scaffolding whose only job is to hold the active phase dispersed.

See docs/SKETCHES.md's Catalyst under operation section for the full
argument, including the explicit state/control boundary choice that
makes m and nu empty here (both are real physics at the reactor-bed
scale; this sketch scopes state to one pellet, where they are not).
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ParameterRole
from omi.state import Slot, StateSchema

CATALYST_UNDER_OPERATION_SCHEMA = StateSchema(
    (
        (Slot.Z, "active_phase_dispersion", 1),  # sub-resolution: sintering state, inferred from activity decline
        (Slot.GAMMA, "active_site_fraction", 1),  # exposed/accessible active sites
        (Slot.GAMMA, "surface_poison_coverage", 1),  # fraction of sites blocked by poisons
        (Slot.GAMMA, "surface_reconstruction_state", 1),  # facetting/restructuring under reaction conditions
        (Slot.GAMMA, "coke_layer_thickness", 1),  # carbonaceous deposit at the gas/surface interface
    )
)
"""m and nu are declared EMPTY (docs/SKETCHES.md explains why, including
the state/control boundary choice this depends on) -- the first genuinely
empty slot anywhere in this repository, at any level. Gamma has four of
this schema's five components; z has one; m and nu have none."""

CATALYST_UNDER_OPERATION_DECLARATION = InstantiationDeclaration(
    state_schema=CATALYST_UNDER_OPERATION_SCHEMA,
    declared_parameters=(
        ParameterRole(
            name="catalyst_formulation",
            indexes=("surface_reaction_constitutive", "oxidative_regeneration"),
            justification=(
                "Fills item 1b, and this is the one sketch whose fill is checkable against a "
                "BUILT domain rather than only against prose -- the discovery domain declares the "
                "same structure, where `support` holds SpeciesRole.PARAMETER in both regions and "
                "mean_composition is item 1b's occupant. The support identity, the active-phase "
                "metal and the promoter loading are fixed by manufacture: no operator transports "
                "them, the observation suite (bulk conversion, plus ex-situ surface "
                "characterisation) does not assimilate them, no per-site value exists, and they "
                "decide which surface-kinetics operator applies. "
                "Note what this does NOT rescue: this sketch's declared strain is that m and nu "
                "are empty because the state is scoped to one pellet (the four slots may be a "
                "convenience rather than a partition). Item 1b is orthogonal to that -- a "
                "parameter is not a slot, by E-29's own argument that a fifth slot is the wrong "
                "fix -- so the empty-slot finding stands entirely unchanged."
            ),
        ),
    ),
    control_space=(
        "Apparatus/process-controlled: feed composition, flow rate, "
        "reactor temperature and pressure as a time-dependent recipe. The "
        "bulk gas-phase concentration/temperature field this pellet "
        "experiences is treated as an externally-imposed boundary "
        "condition (control), not as part of this pellet's own state -- "
        "see docs/SKETCHES.md for why this scoping choice is what empties "
        "nu here. U_adm bounded by the reactor's qualified operating "
        "envelope. A control (process) inverse exists: target activity/"
        "selectivity lifetime -> feed/operating-condition recipe."
    ),
    erasure_inventory=("oxidative_regeneration",),
    readout_catalogue=(
        "conversion_mean: Type-0/Class-A",
        "surface_reaction_constitutive: Type-1",
        "catalyst_lifetime_to_deactivation: Type-0/Class-B; process-zone "
        "volume = the pellet's total active surface area, decomposed "
        "into many small sub-areas of heterogeneous local poison/coke "
        "susceptibility. "
        "Item 4b (Core §4): driver field = local poison/coke accumulation "
        "rate across the surface (spatially heterogeneous from local "
        "flow/diffusion variation); defect population = independently "
        "measured site-reactivity/susceptibility distribution "
        "(chemisorption titration, microscopy); physics map Psi = "
        "Langmuir-type site-blocking deactivation kinetics, a standard "
        "framework in catalysis science, not invented inside "
        "omi.classb.",
    ),
    observation_suite=(
        "continuous bulk conversion/selectivity monitoring (in-chain, "
        "but an aggregate, indirect signal several steps removed from "
        "the actual surface state)",
        "ex-situ/destructive surface characterisation between runs "
        "(XPS, chemisorption, TPO for coke quantification -- requires "
        "removing the catalyst from the reactor, not available during "
        "operation)",
    ),
    invariants=(
        "active_phase_mass_conservation_absent_volatilization",
        "cumulative_thermal_exposure_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I only: a single representative pellet's (or small surface "
        "patch's) analytic surface-kinetics operator. State is scoped to "
        "one pellet, not the reactor bed -- a reactor-bed-scale version "
        "of this domain would need to restore a genuine nu (the shared "
        "bulk gas-phase field) and would look structurally different. "
        "Full reactor-bed-scale coupling (spatial gas-phase profile "
        "across the whole bed, pellet-to-pellet heat/mass transfer) "
        "remains an anti-goal per CLAUDE.md §9."
    ),
)
