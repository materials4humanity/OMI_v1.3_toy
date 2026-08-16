"""The composition variant's declaration (composition stage C1; ADR-050, ADR-052, ADR-075,
ADR-076).

What is checked here is the *declaration*, not the physics: that `c̄` lands in item 1b and
`δc` in item 1a, that the two are mutually exclusive by the check ADR-071 built, that the
projection scale is visible to `omi.interface.diff` as ADR-076 claims, and that `flagship`
itself is untouched — which is the property ADR-075 Decision 2 chose a separate package for.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.interface import InstantiationDeclaration, ParameterRole, ProjectionScale, diff
from omi.state import Slot

from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.state import FLAGSHIP_SCHEMA
from omi_domains.flagship_composition.composition import (
    BULK_MEAN,
    BULK_PROJECTION_SCALE,
    DESCRIPTOR_MAP,
    DESCRIPTORS,
    SPECIES,
)
from omi_domains.flagship_composition.interface import (
    COMPOSITION_DECLARATION,
    MEAN_COMPOSITION_PARAMETER,
)
from omi_domains.flagship_composition.state import COMPOSITION_SCHEMA

from tests.conftest import ObservationRecorder


# --- the split lands on the two items it is supposed to ----------------------


def test_c_bar_is_item_1b_and_delta_c_is_item_1a(observe: ObservationRecorder) -> None:
    """**The decomposition, as a placement claim** (ADR-050, ADR-071, ADR-075).

    `c̄` indexes the operator family and no operator transports it → item 1b. `δc` is
    transported by an operator → item 1a's `z`. That the two sit in different items is the
    structural content of the split; before ADR-071 there was one item for both.
    """
    parameter_names = tuple(p.name for p in COMPOSITION_DECLARATION.declared_parameters)
    z_occupants = COMPOSITION_SCHEMA.names(Slot.Z)
    observe("item_1b_names", parameter_names, "== ('mean_composition',)")
    observe("delta_c_is_a_z_occupant", "unresolved_solute_mean_deviation" in z_occupants, "True")

    assert parameter_names == ("mean_composition",)
    assert "unresolved_solute_mean_deviation" in z_occupants


def test_c_bar_is_not_routed_through_the_coupled_quantity_construction() -> None:
    """**ADR-075's prohibition, pinned.** ADR-050 said `c̄` "is an ADR-049 coupled-quantity
    declaration with `coupling = INVARIANT`"; ADR-075 supersedes that on E-46's four-property
    test, because routing it there re-creates the second declaration site ADR-071 removed.

    This variant carries no decision-extension declaration at all, so the only home `c̄` has
    is item 1b. Checked structurally rather than trusted: the declaration is a plain
    `InstantiationDeclaration`, so there is no `coupled_quantities` field for it to hide in.
    """
    assert isinstance(COMPOSITION_DECLARATION, InstantiationDeclaration)
    assert not hasattr(COMPOSITION_DECLARATION, "coupled_quantities")


def test_the_two_items_are_mutually_exclusive_by_name(observe: ObservationRecorder) -> None:
    """ADR-071's cross-item check, exercised on a real composition declaration.

    A quantity cannot be declared in both items without saying so. Here the names differ
    deliberately (`mean_composition` versus `unresolved_solute_mean_deviation`) because they
    *are* different quantities — the mean and its fluctuation — and the check confirms no
    accidental collision rather than permitting one.
    """
    occupants = {name for _, name, _ in COMPOSITION_SCHEMA.components}
    parameters = {p.name for p in COMPOSITION_DECLARATION.declared_parameters}
    observe("item_1a_1b_collision_count", len(occupants & parameters), "== 0")
    assert not (occupants & parameters)

    with pytest.raises(ValueError, match="also_state_in_regions"):
        InstantiationDeclaration(
            state_schema=COMPOSITION_SCHEMA,
            declared_parameters=(
                ParameterRole(
                    name="unresolved_solute_mean_deviation",  # collides with item 1a
                    indexes=("conservative_redistribution",),
                    justification="deliberately colliding, to exercise ADR-071's check",
                ),
            ),
            control_space=COMPOSITION_DECLARATION.control_space,
            erasure_inventory=(),
            readout_catalogue=COMPOSITION_DECLARATION.readout_catalogue,
            observation_suite=COMPOSITION_DECLARATION.observation_suite,
            invariants=COMPOSITION_DECLARATION.invariants,
            scale_structure=COMPOSITION_DECLARATION.scale_structure,
        )


# --- the projection scale is visible to diff, which is ADR-076's claim -------


def test_the_projection_scale_is_declared_with_its_characterisation_method(
    observe: ObservationRecorder,
) -> None:
    """`docs/V1.4-EDITS.md` E-31's requirement and E-45's reason for it: the `c̄`/`δc` line is
    observer-relative, so a scale with no method behind it is not comparable between
    implementations."""
    scale = MEAN_COMPOSITION_PARAMETER.projection_scale
    assert scale is not None
    observe("projection_scale_length", scale.length, "> 0")
    observe("projection_scale_units", scale.units, "declared, never defaulted")
    observe("projection_method_declared", bool(scale.characterisation_method.strip()), "True")

    assert scale is BULK_PROJECTION_SCALE
    assert scale.length > 0.0
    assert scale.units.strip()
    assert scale.characterisation_method.strip()


def test_a_projection_scale_missing_its_method_or_units_is_refused() -> None:
    """Both are required, for E-33's reason (a bare length is uninterpretable) and E-31's (an
    unattributed boundary is not comparable)."""
    with pytest.raises(ValueError, match="units"):
        ProjectionScale(length=1.0, units="  ", characterisation_method="a method")
    with pytest.raises(ValueError, match="characterisation method"):
        ProjectionScale(length=1.0, units="micrometre", characterisation_method="  ")
    with pytest.raises(ValueError, match="must be positive"):
        ProjectionScale(length=0.0, units="micrometre", characterisation_method="a method")


def test_two_declarations_differing_only_in_projection_scale_differ_under_diff(
    observe: ObservationRecorder,
) -> None:
    """**ADR-076's diff-visibility claim, checked rather than asserted.**

    ADR-050 requires the projection scale "surfaced by `interface.diff`" because E-45's finding
    is that operator reuse silently depends on two implementations' splits matching. This is the
    test that makes the claim true: two declarations identical in every other respect, differing
    only in the declared scale, must differ on item 1b.

    **Visible, not checkable** — nothing verifies that a declared scale is the scale the
    operators were fitted at, so E-45 stays open. What is closed is the invisibility.
    """
    coarser = ProjectionScale(
        length=BULK_PROJECTION_SCALE.length * 4.0,
        units=BULK_PROJECTION_SCALE.units,
        characterisation_method="a coarser scan step, resolving less into the mean",
    )
    variant = InstantiationDeclaration(
        state_schema=COMPOSITION_DECLARATION.state_schema,
        declared_parameters=(
            ParameterRole(
                name=MEAN_COMPOSITION_PARAMETER.name,
                indexes=MEAN_COMPOSITION_PARAMETER.indexes,
                justification=MEAN_COMPOSITION_PARAMETER.justification,
                constant_over=MEAN_COMPOSITION_PARAMETER.constant_over,
                descriptor_basis=MEAN_COMPOSITION_PARAMETER.descriptor_basis,
                underlying_space=MEAN_COMPOSITION_PARAMETER.underlying_space,
                projection_scale=coarser,
            ),
        ),
        control_space=COMPOSITION_DECLARATION.control_space,
        erasure_inventory=COMPOSITION_DECLARATION.erasure_inventory,
        readout_catalogue=COMPOSITION_DECLARATION.readout_catalogue,
        observation_suite=COMPOSITION_DECLARATION.observation_suite,
        invariants=COMPOSITION_DECLARATION.invariants,
        scale_structure=COMPOSITION_DECLARATION.scale_structure,
    )
    result = diff(COMPOSITION_DECLARATION, variant)
    differing = sorted(k for k, v in result.items() if v)
    observe("scale_only_variant_differing_items", differing, "== ['declared_parameters'] only")

    assert differing == ["declared_parameters"], (
        "a projection-scale difference must surface on item 1b and nowhere else — if it "
        "surfaces nowhere, E-45's mismatch is invisible and ADR-076's claim is false"
    )


# --- the descriptor declaration ----------------------------------------------


def test_both_spaces_are_declared_because_the_claim_needs_both(
    observe: ObservationRecorder,
) -> None:
    """ADR-052: "this operator depends on chemistry only through these functionals" is
    falsifiable exactly by varying the underlying space at fixed descriptors, which needs both
    declared. Item 1b carries both, and the map agrees with the declaration."""
    observe("declared_descriptor_basis", MEAN_COMPOSITION_PARAMETER.descriptor_basis, f"== {DESCRIPTORS}")
    observe("declared_underlying_space", MEAN_COMPOSITION_PARAMETER.underlying_space, f"== {SPECIES}")
    assert MEAN_COMPOSITION_PARAMETER.descriptor_basis == DESCRIPTORS == DESCRIPTOR_MAP.descriptors
    assert MEAN_COMPOSITION_PARAMETER.underlying_space == SPECIES == DESCRIPTOR_MAP.underlying


def test_the_declared_mean_is_a_composition_on_the_simplex(observe: ObservationRecorder) -> None:
    """The declared `c̄` is a real composition, not an arbitrary vector — by construction,
    since the only route to it is through the simplex (Spec §2.2; ADR-076 decision 1)."""
    fractions = BULK_MEAN.fractions()
    observe("declared_mean_fraction_sum", float(fractions.sum()), "== 1.0")
    observe("declared_mean_is_non_negative", bool(np.all(fractions >= 0.0)), "True")
    assert float(fractions.sum()) == pytest.approx(1.0, abs=1e-12)
    assert np.all(fractions >= 0.0)


# --- flagship is untouched, which is why a separate package exists -----------


def test_flagship_itself_is_unchanged(observe: ObservationRecorder) -> None:
    """**ADR-075 Decision 2's whole justification, pinned.** The variant exists in its own
    package so that declaring `δc` changes no existing schema — because changing a schema
    changes its `size`, and therefore every metric-normalised quantity computed on it, and
    therefore a large fraction of the audit record.
    """
    observe("flagship_schema_size", FLAGSHIP_SCHEMA.size, "== 7, unchanged")
    observe("composition_schema_size", COMPOSITION_SCHEMA.size, "== 8 -- flagship's seven plus delta-c")
    observe("flagship_declares_no_parameter", len(FLAGSHIP_DECLARATION.declared_parameters), "0")

    assert FLAGSHIP_SCHEMA.size == 7
    assert COMPOSITION_SCHEMA.size == 8
    assert FLAGSHIP_DECLARATION.declared_parameters == ()
    assert COMPOSITION_SCHEMA is not FLAGSHIP_SCHEMA


def test_no_resolved_composition_band_is_declared_anywhere(observe: ObservationRecorder) -> None:
    """**ADR-076 decision 4, and the finding it defers rather than crosses.**

    `δc` is declared sub-resolution in `z` only. A resolved segregation band would be an `m`
    occupant over a `FIELD` declared domain, which ADR-049 refuses citing `C-2.5`
    (body-indexed state, an anti-goal under CLAUDE.md §9). So `m` carries no composition
    occupant, and that absence is the declaration's honest scope rather than an oversight —
    `docs/COMPOSITION-BRIEF.md` records what it costs.
    """
    m_occupants = COMPOSITION_SCHEMA.names(Slot.M)
    observe("m_slot_occupants", m_occupants, "no composition band among them")
    assert not any("solute" in name or "composition" in name for name in m_occupants)
    # And the sub-resolution one is where ADR-050's scope line puts it.
    assert "unresolved_solute_mean_deviation" in COMPOSITION_SCHEMA.names(Slot.Z)
