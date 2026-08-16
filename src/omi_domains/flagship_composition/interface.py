"""The composition variant's instantiation declaration (Core §4; ADR-071, ADR-075, ADR-076).

`c̄` is declared as item **1b**'s :class:`~omi.interface.ParameterRole`, carrying its
descriptor basis, its underlying space and its projection scale — **not** as an ADR-049
coupled quantity. ADR-050 said the latter and ADR-075 supersedes it on E-46's four-property
test; routing `c̄` back through `CoupledQuantityDeclaration` is prohibited because it
re-creates the second declaration site ADR-071 removed.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ParameterRole

from omi_domains.flagship_composition.composition import (
    BULK_MEAN,
    BULK_PROJECTION_SCALE,
    DESCRIPTORS,
    SPECIES,
)
from omi_domains.flagship_composition.state import COMPOSITION_SCHEMA

MEAN_COMPOSITION_PARAMETER = ParameterRole(
    name="mean_composition",
    indexes=("conservative_redistribution", "boundary_loss_redistribution"),
    justification=(
        "The decomposition c(x) = c-bar + delta-c (ADR-050), with c-bar on this side of the "
        "split. It fails all three of E-46's state properties -- no operator transports the "
        "declared mean, no declared modality assimilates it, and it carries no per-particle "
        "value in an ensemble over one heat-treated volume -- and answers E-46's parameter "
        "question: it decides WHICH member of the redistribution family applies, because both "
        "declared operators' rates are functions of the descriptor values. "
        "delta-c is the separate item-1a occupant `unresolved_solute_mean_deviation`, and the "
        "two are mutually exclusive by name under InstantiationDeclaration's own check, which "
        "is the structural content of the split."
    ),
    constant_over=("representative_volume",),
    descriptor_basis=DESCRIPTORS,
    underlying_space=SPECIES,
    projection_scale=BULK_PROJECTION_SCALE,
)
"""`c̄` as item 1b's declaration.

`projection_scale` is populated, which is what makes the `c̄`/`δc` line **visible to
`omi.interface.diff`** — E-45's finding is that operator reuse silently depends on that line
matching between implementations, and ADR-050 requires it surfaced without claiming it is
checked."""


COMPOSITION_DECLARATION = InstantiationDeclaration(
    state_schema=COMPOSITION_SCHEMA,
    declared_parameters=(MEAN_COMPOSITION_PARAMETER,),
    control_space=(
        "Apparatus-controlled, as flagship's: heating intensity and transfer speed set by the "
        "processing line. U_adm bounded by furnace and mill capacity. Unchanged by the "
        "composition variant -- the composition is a parameter, not a control, at this "
        "declaration's scope (and see docs/V1.4-EDITS.md E-61 for the scope caveat: a campaign "
        "that CHOOSES the composition would declare it as item 2 content instead, which is the "
        "boundary E-61 finds Core §4 does not let a declaration state)."
    ),
    erasure_inventory=(),
    # Deliberately empty, and it is a difference from flagship worth stating: this variant
    # declares only the two redistribution operators, neither of which is an erasure
    # (measured -- both leave the image near-full rank). Flagship's HEATING_AND_SOAK is not
    # re-declared here because this package exists to exercise the composition split, not to
    # restate flagship's chain.
    readout_catalogue=(
        "aggregate_hardness: Type-0/Class-A",
        "hardness_constitutive: Type-1",
    ),
    observation_suite=(
        "quantitative area-scan microanalysis (establishes the projection scale; resolves the "
        "mean, not the sub-resolution fluctuation)",
        "in-die force/torque sensing (Type-0 readout of z)",
    ),
    invariants=(
        "solute_mass_conservation_over_closed_domain",
        "coating_thickness_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I only, SVE-level, as flagship. The projection scale declared on item 1b is what "
        "separates the resolved mean from the sub-resolution fluctuation; resolved segregation "
        "bands would need a FIELD declared domain, which ADR-049 refuses citing C-2.5, so they "
        "are declarable and unimplemented (ADR-050's scope line, ADR-076 decision 4)."
    ),
)
"""The variant's eight-item declaration.

**One thing it declares that no other domain here does**: a parameter whose value depends on
a declared projection scale, so the E-45 mismatch is visible in item 1b rather than invisible
everywhere."""


def domain_mean_trajectory(
    deviations: tuple[float, ...],
    *,
    species: str = "solute_a",
) -> tuple[float, ...]:
    """The domain mean of `c̄ + δc` at each step, for ADR-050's constancy residual.

    *deviations* are the `unresolved_solute_mean_deviation` values read off a rollout. The mean
    is `c̄[species] + δc_mean`, which is what conservation constrains — a residual over `c̄`
    alone would be vacuous, since `c̄` is a parameter and trivially constant (ADR-076).
    """
    fractions = dict(zip(SPECIES, (float(f) for f in BULK_MEAN.fractions())))
    if species not in fractions:
        raise ValueError(f"{species!r} is not a declared species: {SPECIES}")
    return tuple(fractions[species] + d for d in deviations)
