"""Layer-wise additive processing sketch (Spec §11.4, Core §7.3 [Pass D],
ROADMAP M10.1): metal powder-bed-fusion additive manufacturing, chosen
because it exercises "hybrid structure and body-indexed state at their most
extreme" (docs/ROADMAP.md M10.1) — Core §3.4 (hybrid continuous-discrete
systems) and Core §2.5 (body-indexed state), both `[Pass C]`/anti-goal
(CLAUDE.md §9). Interface-only per ADR-038 (docs/DECISIONS.md): no
operators, no readouts, no build function.

**This sketch does not fill cleanly.** `omi.state.StateSchema` (ADR-011) is
a flat, finite-dimensional vector — it can declare a single representative
build location's state (a Tier I stand-in, the same move flagship and the
device-yield sketch make), but it cannot express that this domain's actual
state is a field over a body that is itself under construction, growing one
layer at a time. The schema below is exactly that forced Tier I
approximation, not a genuine fill of Core §4 item 1 — see
``docs/SKETCHES.md``'s Layer-wise additive processing section for the full
argument, and ``docs/V1.4-EDITS.md`` E-21 for the resulting framework
finding.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration
from omi.state import Slot, StateSchema

LAYERWISE_ADDITIVE_SCHEMA = StateSchema(
    (
        (Slot.M, "local_melt_pool_geometry", 1),  # resolved: in-situ camera's melt-pool descriptor
        (Slot.M, "layer_surface_roughness_field", 1),  # resolved: recoated-layer surface topography
        (Slot.Z, "subsurface_porosity_density", 1),  # sub-resolution until post-build CT
        (Slot.Z, "local_thermal_history_moments", 1),  # constitutive-operator memory (reheating cycles)
        (Slot.NU, "part_scale_residual_stress_field", 1),  # nonlocal: whole-part, global heat-conduction balance
        (Slot.GAMMA, "interlayer_bond_state", 1),  # controls delamination/interlaminar fracture
    )
)
"""One representative build location's state — a Tier I stand-in for a
domain whose actual state is body-indexed (Core §2.5). Declaring this as
*the* state schema, full stop, silently reverts the domain to Tier I and
discards the whole-part residual-stress accumulation and distortion
physics that is often this domain's dominant commercial failure mode —
recorded honestly as a forced approximation, not claimed as a clean fill.
"""

LAYERWISE_ADDITIVE_DECLARATION = InstantiationDeclaration(
    state_schema=LAYERWISE_ADDITIVE_SCHEMA,
    control_space=(
        "Apparatus-controlled: laser/beam power, scan speed, hatch spacing, "
        "and layer thickness as a time-dependent recipe across the whole "
        "build, with discrete layer-boundary events (recoat, new-layer "
        "start) as points of discontinuity within that one programme — Core "
        "§3.2's control space already admits an arbitrary function of time, "
        "so this item fills without needing hybrid/jump-map machinery "
        "(Core §3.4, anti-goal) to be built. U_adm bounded by the machine's "
        "qualified process window. A control (process) inverse exists: "
        "target part quality/density -> recipe."
    ),
    erasure_inventory=("hot_isostatic_pressing",),
    readout_catalogue=(
        "final_density_mean: Type-0/Class-A",
        "melt_pool_constitutive: Type-1",
        "porosity_induced_fatigue_life: Type-0/Class-B; process-zone volume "
        "= the completed part's volume (fixed at evaluation time, unlike "
        "the growing build-time state above — this readout is only "
        "evaluated post-build). "
        "Item 4b (Core §4): driver field = the built part's internal pore "
        "size/location field; defect population = independently measured "
        "pore-size distribution from post-build X-ray CT (standard in AM "
        "qualification; lack-of-fusion pore sizes are heavy-tailed); "
        "physics map Psi = a fracture-mechanics defect-size-to-fatigue-"
        "limit relation (Murakami's sqrt(area) model), whose exponent is "
        "read directly from that published model, not invented inside "
        "omi.classb.",
    ),
    observation_suite=(
        "in-situ melt-pool monitoring (photodiode/camera, per layer)",
        "layer-wise optical imaging of the recoated surface",
        "post-build X-ray CT (rich, but available only once, after the "
        "build is complete -- too late to inform assimilation during the "
        "build itself, unlike every other declared observation in this "
        "repository's domains and sketches so far)",
    ),
    invariants=(
        "mass_conservation_across_melting_and_solidification",
        "cumulative_build_height_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I only, as declared above: a single representative build "
        "location's analytic melt-pool constitutive response. The "
        "domain's dominant physical mechanism -- whole-part residual-"
        "stress accumulation and distortion, carried in nu -- is "
        "fundamentally a body-indexed, Tier II phenomenon (Core §2.5, "
        "[Pass C]), and more centrally so here than for either "
        "implemented domain: flagship's and contrast's dominant slots "
        "(Core §7.1/§7.2) do not themselves require whole-body spatial "
        "coupling to be evaluated, while this domain's do. Homogenisation "
        "would need to bridge melt-pool scale (microseconds, microns) to "
        "whole-part scale (hours, the full build) -- a far wider scale "
        "separation than flagship's SVE-to-component bridge. Full Tier II "
        "(body-indexed state, registration operator) remains an anti-goal "
        "per CLAUDE.md §9."
    ),
)
