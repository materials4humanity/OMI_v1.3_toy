"""The contrast's instantiation declaration (Core §4, §7.2) — eight items since ADR-071
split item 1."""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ParameterRole

from omi_domains.contrast.state import CONTRAST_SCHEMA
from omi.observability import ObservedInferredConvention

CONTRAST_DECLARATION = InstantiationDeclaration(
    state_schema=CONTRAST_SCHEMA,
    declared_parameters=(
        ParameterRole(
            name="cell_design",
            indexes=("CyclingStep", "DendriteRisk"),
            justification=(
                "Fails all three of E-46's state properties and answers its parameter question. "
                "The cell's chemistry and build -- electrode couple, electrolyte formulation, "
                "separator, format -- is fixed when the artefact is manufactured: no operator "
                "transports it, no observation in item 5 (terminal current, voltage, surface "
                "temperature) assimilates it, and it carries no per-particle value in an ensemble "
                "over cells of one design. What it does is decide WHICH cycling and dendrite "
                "operator applies: the same duty cycle imposed on a different couple is a "
                "different map, not the same map at a different state. Before ADR-071 this domain "
                "had nowhere to declare it, so a graphite cell and a lithium-metal cell under one "
                "usage programme were structurally indistinguishable declarations."
            ),
        ),
    ),
    # constant_over is left empty: a cell's design is constant over the whole service
    # chain, which is item 1b's ordinary case rather than a region-scoped one. No
    # descriptor basis is declared, because this domain has no descriptor functionals --
    # unlike the discovery domain, whose composition parameter carries one (ADR-052).
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


CONTRAST_OBSERVED_INFERRED = ObservedInferredConvention(
    dominance_factor=1.5,
    abstention_band=0.25,
    near_diagonal_window=0,
    justification=(
        "Window 0, and the choice is load-bearing rather than conventional. This chain's "
        "telemetry is per-interval, so at window 1 or 2 the near-diagonal set admits "
        "observations whose sensitivity to a perturbation at k is IDENTICAL to the downstream "
        "ones -- CyclingStep advances the observed components by state-independent constant "
        "increments -- and the label then moves with the window rather than with the physics "
        "(measured: E-48, tests/oracles/test_share_threshold_degeneracy.py). Window 0 asks the "
        "only question this chain can answer: does the observation AT k inform this direction. "
        "rho = 1.5 with a band of 0.25 is the framework default, retained deliberately: at rho "
        "= 1 the ratio of exactly 1.0 this chain produces would abstain everywhere, which is "
        "honest but uninformative, and inventing a domain-specific factor to avoid that would "
        "be choosing a number to get an answer."
    ),
)
"""Contrast's declared observed/inferred convention (ADR-061; Spec §3.3; E-48).

The domain where the two conventions were measured to compound, so the justification records
what each value is avoiding rather than only what it is."""
