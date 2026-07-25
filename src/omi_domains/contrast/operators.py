"""The contrast domain's single analytic evolution operator: a charge/
discharge cycling step (Core §7.2). Declares **no erasure** — the load-bearing
inversion of the error-control dichotomy (Core §3.9): this domain must
eventually satisfy condition (b) (observation density sufficient for
assimilation to correct drift) instead of condition (a), via continuous
telemetry assimilation — out of scope until M5, declared in
``omi_domains/contrast/interface.py`` for now.

Every degrading quantity accumulates by an exact closed form (linear or
parabolic in elapsed charge throughput ``|I| * dt``), and the nonlocal slot
``ν`` (potential, overpotential) is recomputed algebraically from the
post-update state each step rather than integrated — a state-space-native
reading of Core §3.1's "determined by a global balance," and semigroup-exact
by construction, same as the flagship's relaxation operators.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Slot, State


@dataclass(frozen=True)
class CyclingStep(EvolutionOperator):
    """One usage interval under a held-constant current ``I`` (Core §7.2's
    usage-determined control axis)."""

    porosity_rate: float = 0.01
    li_loss_rate: float = 0.02
    sei_rate: float = 0.05
    cei_rate: float = 0.03
    resistance_rate: float = 0.01
    open_circuit_voltage: float = 4.0
    fade_gain: float = 1.5
    overpotential_gain: float = 0.2

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        dt = control.duration
        current = control(control.t0)[0]
        drive = abs(current) * dt

        porosity = state.get(Slot.M, "electrode_porosity")[0]
        li_loss = state.get(Slot.Z, "lithium_inventory_loss")[0]
        sei = state.get(Slot.GAMMA, "sei_thickness")[0]
        cei = state.get(Slot.GAMMA, "cei_thickness")[0]
        resistance = state.get(Slot.GAMMA, "collector_interface_resistance")[0]

        new_porosity = porosity + self.porosity_rate * drive
        new_li_loss = li_loss + self.li_loss_rate * drive
        new_sei = np.sqrt(sei**2 + self.sei_rate * drive)
        new_cei = np.sqrt(cei**2 + self.cei_rate * drive)
        new_resistance = resistance + self.resistance_rate * drive
        new_potential = self.open_circuit_voltage - self.fade_gain * new_li_loss - current * new_resistance
        new_overpotential = self.overpotential_gain * abs(current) / (1.0 + new_porosity)

        s = state
        s = s.with_component(Slot.M, "electrode_porosity", np.array([new_porosity]))
        s = s.with_component(Slot.Z, "lithium_inventory_loss", np.array([new_li_loss]))
        s = s.with_component(Slot.GAMMA, "sei_thickness", np.array([new_sei]))
        s = s.with_component(Slot.GAMMA, "cei_thickness", np.array([new_cei]))
        s = s.with_component(Slot.GAMMA, "collector_interface_resistance", np.array([new_resistance]))
        s = s.with_component(Slot.NU, "potential", np.array([new_potential]))
        s = s.with_component(Slot.NU, "concentration_overpotential", np.array([new_overpotential]))
        return s


CYCLING = CyclingStep()
