"""The known-blind-spot oracle (CLAUDE.md §7): a sensor suite orthogonal to
a designed direction, which must appear in ``ker G`` (Core §3.8; Spec §3.1).

A differencing sensor suite (measuring ``x1 - x2`` and ``x2 - x3``) is
orthogonal by construction to the common-mode direction ``(1, 1, 1)`` — a
uniform shift of every component leaves every difference unchanged, so no
information about that direction can ever reach the sensors, regardless of
dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import Observation
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "x1", 1), (Slot.M, "x2", 1), (Slot.M, "x3", 1)))
NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))

BLIND_DIRECTION: FloatArray = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)


@dataclass(frozen=True)
class IdentityOperator3(EvolutionOperator):
    """Trivial dynamics — the blind spot is a property of the sensor suite,
    not of any particular dynamics erasing information."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return state

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.eye(3)


class DifferenceReadout(FunctionalReadout):
    """``(x1 - x2, x2 - x3)`` — orthogonal to the common-mode direction
    ``(1, 1, 1)`` by construction: adding a constant to every component
    leaves both differences unchanged."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        x1, x2, x3 = state.values
        return np.array([x1 - x2, x2 - x3])

    def jacobian(self, state: State) -> FloatArray:
        """Exact analytic Jacobian (ADR-001: exact tangent maps are what
        make an observability oracle trustworthy) — a finite-difference
        estimate would leave the designed blind direction only
        approximately, not exactly, in the kernel."""
        return np.array([[1.0, -1.0, 0.0], [0.0, 1.0, -1.0]])


class KnownBlindSpotOracle:
    """Cites CLAUDE.md §7's "known blind spot" oracle."""

    def __init__(self) -> None:
        self.schema = SCHEMA
        self.chain = Chain((Segment(IdentityOperator3(), NULL_CONTROL),))
        self.sensor = Observation(
            "difference_sensor", DifferenceReadout(), np.eye(2) * 0.01, time_index=1
        )

    def truth(self) -> FloatArray:
        """The designed-unobservable direction, unit-normalised."""
        return BLIND_DIRECTION
