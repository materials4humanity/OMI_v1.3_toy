"""The contrast's seven-item instantiation declaration (Core §4, §7.2)."""

from __future__ import annotations

from omi.interface import InstantiationDeclaration

from omi_domains.contrast.state import CONTRAST_SCHEMA

CONTRAST_DECLARATION = InstantiationDeclaration(
    state_schema=CONTRAST_SCHEMA,
    control_space=(
        "Usage-determined: the charge/discharge duty cycle is set by the "
        "service application, not an apparatus operator. U_adm is bounded by "
        "manufacturer charge/discharge limits. The control inverse here is a "
        "usage inverse (Core §5), not a process inverse."
    ),
    erasure_inventory=(),
    readout_catalogue=(
        "terminal_voltage: Type-0/Class-A",
        "dendrite_risk: Type-0/Class-B",
    ),
    observation_suite=(
        "terminal current",
        "voltage",
        "surface temperature",
    ),
    invariants=(
        "charge_conservation_coulomb_counting",
        "sei_thickness_monotone_nondecreasing",
    ),
    scale_structure=(
        "Three-tier recursion (electrode -> cell -> pack, Core §7.2); only the "
        "electrode/cell tier is analytically modelled at M1, pack-level "
        "aggregation is not implemented."
    ),
)
