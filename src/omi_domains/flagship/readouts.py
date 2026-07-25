"""Readouts for the flagship chain (Core §7.1).

``AggregateHardness`` (Type-0, Class A) is deliberately defined *in terms of*
the Type-1 constitutive operator, not as separate duplicated arithmetic —
this is Core §2.6's "properties are functionals of the constitutive operator
alone" made literal in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from omi.operators import Control
from omi.readouts import ConstitutiveOperator, ConstitutiveReadout, FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Slot, State

_NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))


@dataclass(frozen=True)
class HardnessConstitutiveOperator(ConstitutiveOperator):
    """Bound to a state; carries the hardening memory (``accumulated_hardening``
    in ``z``) and maps a subsequent driving programme to a hardness response
    and an updated state (Core §3.5, Type-1)."""

    state: State
    base_hardness: float = 100.0
    inclusion_weight: float = 5.0
    grain_size_weight: float = 20.0
    hardening_weight: float = 2.0
    hardening_rate: float = 0.5

    def respond(self, control: Control) -> tuple[FloatArray, State]:
        s = self.state
        inclusion = s.get(Slot.Z, "inclusion_content")[0]
        grain_size = s.get(Slot.M, "prior_grain_size")[0]
        hardening = s.get(Slot.Z, "accumulated_hardening")[0]
        u = control(control.t0)[0]
        dt = control.duration

        new_hardening = hardening + self.hardening_rate * abs(u) * dt
        response = (
            self.base_hardness
            + self.inclusion_weight * inclusion
            + self.grain_size_weight / (1.0 + abs(grain_size))
            + self.hardening_weight * new_hardening
        )
        updated = s.with_component(Slot.Z, "accumulated_hardening", np.array([new_hardening]))
        return np.array([response]), updated


@dataclass(frozen=True)
class ExtractHardness(ConstitutiveReadout):
    """Core §3.5, Type-1: extracts the hardness constitutive operator implied
    by a state."""

    def __call__(self, state: State) -> HardnessConstitutiveOperator:
        return HardnessConstitutiveOperator(state=state)


@dataclass(frozen=True)
class AggregateHardness(FunctionalReadout):
    """Core §3.5, Type-0; Core §2.6: a property, hence a functional of the
    constitutive operator alone — computed by calling
    :class:`ExtractHardness` with a null (zero-driving) control, so no
    additional hardening accrues and the arithmetic is not duplicated
    between the Type-0 and Type-1 readouts."""

    readout_class: ReadoutClass = field(default=ReadoutClass.A)

    def evaluate(self, state: State) -> FloatArray:
        operator = ExtractHardness()(state)
        response, _ = operator.respond(_NULL_CONTROL)
        return response
