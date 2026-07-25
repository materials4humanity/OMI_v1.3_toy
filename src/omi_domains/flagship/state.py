"""The flagship state schema (Core §7.1's stage table, item 1 of the
instantiation interface, Core §4)."""

from __future__ import annotations

from omi.state import Slot, StateSchema

# Order fixes the flat-array layout (omi.state.StateSchema; ADR-011). Indices
# below are used by omi_domains/flagship/operators.py's relaxation rates.
FLAGSHIP_SCHEMA = StateSchema(
    (
        (Slot.M, "prior_deformation", 1),  # erased by heating and soak
        (Slot.M, "prior_grain_size", 1),  # survives — Core §7.1
        (Slot.Z, "substructure_density", 1),  # erased by heating and soak
        (Slot.Z, "inclusion_content", 1),  # survives — Core §7.1
        (Slot.Z, "accumulated_hardening", 1),  # constitutive-operator memory
        (Slot.NU, "levelling_field", 1),  # nonlocal field "from levelling" — Core §7.1
        (Slot.GAMMA, "coating_thickness", 1),  # survives — Core §7.1
    )
)
