"""The flagship's seven-item instantiation declaration (Core §4, §7.1)."""

from __future__ import annotations

from omi.interface import InstantiationDeclaration

from omi_domains.flagship.state import FLAGSHIP_SCHEMA

FLAGSHIP_DECLARATION = InstantiationDeclaration(
    state_schema=FLAGSHIP_SCHEMA,
    control_space=(
        "Apparatus-controlled: heating intensity and transfer speed set by the "
        "processing line. U_adm bounded by furnace and mill capacity. A control "
        "inverse (process inverse) exists (Core §4 item 2)."
    ),
    erasure_inventory=("heating_and_soak",),
    readout_catalogue=(
        "aggregate_hardness: Type-0/Class-A",
        "hardness_constitutive: Type-1",
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
        "Tier I only at M1 (SVE-level analytic operators); Tier II (component "
        "BVP) is an anti-goal per CLAUDE.md §9 and is not implemented."
    ),
)
