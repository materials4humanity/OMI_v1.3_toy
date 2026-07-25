"""Readouts for the contrast domain (Core §7.2).

``DendriteRisk`` is Type-0/Class-B — Core §7.2's "initiation-controlled
plating and dendrite events," modelled as a scalar hazard function of state
rather than a geometry-dependent field, so it needs no Tier II (unlike the
flagship's Type-2 Class B readouts, which are out of scope, CLAUDE.md §9).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Slot, State


@dataclass(frozen=True)
class TerminalVoltage(FunctionalReadout):
    """Core §3.5, Type-0; Core §2.6, Class A (self-averaging): the cell's
    terminal potential, read directly off ``ν`` — one of the only three
    modalities this domain's poor observation suite actually offers."""

    readout_class: ReadoutClass = field(default=ReadoutClass.A)

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.NU, "potential")

    def jacobian(self, state: State) -> FloatArray:
        """Exact analytic Jacobian (ADR-001): a direct component read has a
        trivial, exact derivative — no finite-difference estimate needed."""
        jac = np.zeros((1, state.schema.size))
        jac[0, state.schema.slice_for(Slot.NU, "potential")] = 1.0
        return jac


@dataclass(frozen=True)
class DendriteRisk(FunctionalReadout):
    """Core §3.6, Class B: a weakest-link hazard — driven up by
    concentration overpotential, damped by a thicker (more protective) SEI
    layer. Clamped at zero: a "negative hazard" is not physical."""

    readout_class: ReadoutClass = field(default=ReadoutClass.B)
    overpotential_gain: float = 5.0
    sei_protection_gain: float = 0.05

    def evaluate(self, state: State) -> FloatArray:
        overpotential = state.get(Slot.NU, "concentration_overpotential")[0]
        sei = state.get(Slot.GAMMA, "sei_thickness")[0]
        hazard = max(self.overpotential_gain * overpotential - self.sei_protection_gain * sei, 0.0)
        return np.array([hazard])
