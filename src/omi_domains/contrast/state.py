"""The contrast state schema (Core §7.2, item 1 of the instantiation
interface, Core §4). Γ is the dominant slot (three components, versus one
each for m and z) — the load-bearing inversion Core §7.2 names: "that Γ is
structural, not cosmetic." ν holds potential and concentration
overpotential, per Core §7.2's table, in place of the flagship's residual
stress.
"""

from __future__ import annotations

from omi.state import Slot, StateSchema

CONTRAST_SCHEMA = StateSchema(
    (
        (Slot.M, "electrode_porosity", 1),
        (Slot.Z, "lithium_inventory_loss", 1),
        (Slot.NU, "potential", 1),
        (Slot.NU, "concentration_overpotential", 1),
        (Slot.GAMMA, "sei_thickness", 1),
        (Slot.GAMMA, "cei_thickness", 1),
        (Slot.GAMMA, "collector_interface_resistance", 1),
    )
)
