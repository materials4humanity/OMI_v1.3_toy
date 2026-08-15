"""The flagship's instantiation declaration (Core §4, §7.1) — eight items since
ADR-071 split item 1, and **the one domain here that declares item 1b empty**."""

from __future__ import annotations

from omi.interface import InstantiationDeclaration

from omi_domains.flagship.state import FLAGSHIP_SCHEMA
from omi.observability import ObservedInferredConvention

FLAGSHIP_DECLARATION = InstantiationDeclaration(
    state_schema=FLAGSHIP_SCHEMA,
    declared_parameters=(),
    # Item 1b, declared EMPTY, and the emptiness is a finding rather than an omission
    # (docs/V1.4-EDITS.md E-29, E-46; ADR-071).
    #
    # This domain is the one E-29 was written about -- flat-rolled steel, where
    # hardenability, carbon and microalloying are the paradigm operator-family indices --
    # and it is the only domain or sketch in this repository whose item 1b is empty. The
    # reason is not that the physics has no parameters. It is that this build's three
    # de-facto-static components (inclusion_content, prior_grain_size,
    # accumulated_hardening: relaxation rate exactly 0.0 and control-coupling gain
    # exactly 0.0 in both evolution operators, measured in E-29) are declared as SLOT
    # OCCUPANTS in item 1a, where the constitutive operator reads them as state.
    #
    # Moving them to 1b would be a physics change -- E-29 records that repair as out of
    # scope and needing its own decision record -- so the honest declaration is: no
    # operator-family index is declared here, and three quantities that behave like one
    # sit in item 1a instead. The split supplies the destination those three should have;
    # it does NOT detect that they belong there. Detection still takes the measurement
    # E-29 already performed, because nothing here flags a 1a occupant whose rate and
    # gain are both zero.
    control_space=(
        "Apparatus-controlled: heating intensity and transfer speed set by the "
        "processing line. U_adm bounded by furnace and mill capacity. A control "
        "inverse (process inverse) exists (Core §4 item 2)."
    ),
    erasure_inventory=("heating_and_soak",),
    readout_catalogue=(
        "aggregate_hardness: Type-0/Class-A",
        "hardness_constitutive: Type-1",
        "bend_angle: Type-2/Class-B (Tier I½, ADR-035, docs/DECISIONS.md); "
        "process-zone volume = thickness fraction where the local response "
        "exceeds a declared threshold. "
        "Item 4b (Core §4): driver field = outer-fibre-peaked local hardening "
        "response under linear through-thickness bending strain "
        "(curvature × z), evaluated at through-thickness quadrature points; "
        "defect population = inclusion_content, independently measured and "
        "Pareto-tailed at the campaign level (src/omi_domains/flagship/"
        "classb_bend.py); physics map Ψ = linear (driver = "
        "inclusion_weight × inclusion_content + geometry/hardening terms), "
        "so its Spec §4.3 exponent β = 1, read directly off the "
        "constitutive operator's own linear response formula rather than "
        "invented inside omi.classb.",
    ),
    observation_suite=(
        "in-die force/torque sensing (Type-0 readout of z)",
        "coating thickness gauge",
    ),
    invariants=(
        "mass_conservation_across_transformation",
        "coating_thickness_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I (SVE-level analytic operators) from M1, plus Tier I½ from "
        "Phase 2 (ADR-035, docs/DECISIONS.md): a bounded, structurally-"
        "fenced component readout (bend_angle) restricted to one scalar "
        "geometry parameter and one loading mode, no mesh or solver. Tier "
        "II proper (a genuine boundary-value problem, FE2 coupling) remains "
        "an anti-goal per CLAUDE.md §9 and is not implemented."
    ),
)


FLAGSHIP_OBSERVED_INFERRED = ObservedInferredConvention(
    dominance_factor=2.0,
    abstention_band=0.25,
    near_diagonal_window=0,
    justification=(
        "Window 0, the most literal reading of Spec 3.3's 'j ~ k': this chain's stations are "
        "far apart in state-space terms -- HEATING_AND_SOAK is a declared erasure -- so an "
        "observation one segment later is not 'near' anything, and admitting it would be a "
        "modelling claim rather than a notational convenience. rho = 2.0 rather than the "
        "framework's 1.5 because the erasure makes the ratio structurally 0 or infinite here "
        "(measured: tests/oracles/test_share_threshold_degeneracy.py), so a demanding factor "
        "costs nothing and states plainly that a marginal near-diagonal excess would not be "
        "accepted as dominance on a chain whose information structure is this decisive."
    ),
)
"""Flagship's declared observed/inferred convention (ADR-061; Spec §3.3).

The values are cheap here **because** the domain is degenerate in the direction that makes
them cheap, and the justification says so rather than presenting a comfortable choice as a
considered one."""
