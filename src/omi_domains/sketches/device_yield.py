"""Device yield sketch (Spec §11.4, Core §7.3 [Pass D], ROADMAP M10.1):
semiconductor device fabrication, chosen because Class B volume scaling
(Core §3.6, Spec §4.1's ``P(rho_V > x) = [P(rho_0 > x)]^N``) is structurally
the same construction as the classical Poisson/negative-binomial
defect-density yield model (Murphy 1964; Stapper 1983) — a field that has
used it for fifty years without any contact with OMI. Interface-only per
ADR-038 (docs/DECISIONS.md): no operators, no readouts, no build function.
The prose "one page" is ``docs/SKETCHES.md``'s Device Yield section; this
module supplies only the two objects that section's claims must be checked
against.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ParameterRole
from omi.state import Slot, StateSchema

DEVICE_YIELD_SCHEMA = StateSchema(
    (
        (Slot.M, "wafer_defect_map", 1),  # resolved: inline inspection's defect map
        (Slot.M, "layer_thickness_field", 1),  # resolved: film-thickness/CD map
        (Slot.Z, "chamber_seasoning_state", 1),  # sub-resolution: not directly observable
        (Slot.Z, "subresolution_particle_density", 1),  # below inspection tool resolution
        (Slot.Z, "cumulative_thermal_budget", 1),  # constitutive-operator memory
        (Slot.NU, "plasma_sheath_potential", 1),  # nonlocal: set by a chamber-wide discharge balance
        (Slot.GAMMA, "interlayer_interface_state", 1),  # controls via/contact opens, not cosmetic
    )
)

DEVICE_YIELD_DECLARATION = InstantiationDeclaration(
    state_schema=DEVICE_YIELD_SCHEMA,
    declared_parameters=(
        ParameterRole(
            name="design_rule_and_layout",
            indexes=("process_step_constitutive", "die_yield"),
            justification=(
                "Fills item 1b, and the evidence that this item was missing is in this same "
                "declaration: item 4 already says the Class B process-zone volume is 'the die's "
                "declared critical area under its design rule', and item 7 already says "
                "critical-area analysis is 'a declared, fixed-per-design scalar'. So the layout "
                "was ALREADY a declared operator-family index -- written into the prose of two "
                "other items because item 1 had nowhere to host it. Against E-46's four "
                "properties: no operator transports the layout, no inline inspection assimilates "
                "it, it carries no per-die value in an ensemble over one design, and it decides "
                "which critical-area function A_c(x) the yield map uses."
            ),
        ),
        ParameterRole(
            name="tool_chamber_identity",
            indexes=("process_step_constitutive",),
            justification=(
                "Declared as a SECOND parameter specifically because this domain separates an "
                "index from a state on one physical object, which is the sharpest available "
                "illustration of what the item-1 split buys. The chamber's IDENTITY -- which "
                "tool, which hardware set -- is fixed and indexes the operator family; the same "
                "chamber's SEASONING STATE evolves run to run and is declared in item 1a's z "
                "slot. Before ADR-071 both would have been item 1 content with nothing "
                "distinguishing them, which is E-29's detectability finding exactly: 'static by "
                "design' and 'should evolve but does not' had identical structural signatures."
            ),
        ),
    ),
    # `indexes` names operators this sketch declares but does not build (ADR-038:
    # interface-only). So the falsifiable half of a ParameterRole -- a named operator
    # either does or does not vary with the quantity -- is not checkable here, only
    # stated. That is ADR-038's known scope limit, not a defect in the declaration.
    control_space=(
        "Apparatus-controlled: deposition/etch/CMP tool setpoints (pressure, "
        "RF power, flow rates, temperature) as time-dependent recipes. "
        "U_adm bounded by each tool's qualified process window. A control "
        "(process) inverse exists: target yield -> recipe (Core §4 item 2)."
    ),
    erasure_inventory=("cmp_planarization",),
    readout_catalogue=(
        "parametric_test_mean: Type-0/Class-A",
        "process_step_constitutive: Type-1",
        "die_yield: Type-0/Class-B; process-zone volume = the die's declared "
        "critical area under its design rule. "
        "Item 4b (Core §4): driver field = wafer-level defect-density map "
        "(subresolution_particle_density convolved with the chamber's "
        "plasma_sheath_potential field); defect population = inline "
        "inspection's measured defect-size distribution (SEM/optical wafer "
        "scanners; independently measured, heavy-tailed per Stapper 1983); "
        "physics map Psi = the design's critical-area function A_c(x) "
        "relating defect size to killer-defect probability, whose exponent "
        "is read directly off critical-area analysis of the GDSII layout "
        "(a standard EDA technique), not invented inside omi.classb.",
    ),
    observation_suite=(
        "inline optical/SEM wafer defect inspection (sampled, not every "
        "wafer, per fab throughput cost)",
        "end-of-line electrical parametric test",
        "in-situ chamber sensors (particle counters, OES)",
    ),
    invariants=(
        "mass_conservation_across_deposition_and_removal",
        "cumulative_thermal_budget_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I only (analytic per-die constitutive response from feature-"
        "scale state to die-level response). Critical-area analysis is "
        "treated as a declared, fixed-per-design scalar rather than a "
        "variable Tier I½ geometry parameter (unlike flagship's "
        "bend_angle). Full 3D TCAD process simulation or layout-as-"
        "variable-geometry Tier II remain anti-goals per CLAUDE.md §9."
    ),
)
