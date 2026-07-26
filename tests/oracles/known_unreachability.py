"""The known-unreachability oracle (CLAUDE.md §7; docs/ROADMAP.md M9): a
system with a linear invariant `Φ(s) = a + b` whose per-step increment is
exactly bounded by a declared admissible control range, so the achievable
bound after any number of steps is known exactly by construction — the
oracle `omi.inverse.is_provably_unreachable` (Spec §7.1) must recover
exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "a", 1), (Slot.M, "b", 1)))

C_MAX = 1.5
"""The declared admissible control bound: every control this oracle's true
trajectories ever use satisfies `0 <= u <= C_MAX`."""


@dataclass(frozen=True)
class AccumulatorOperator(EvolutionOperator):
    """`(a, b) -> (a + u, b + u)` for a scalar control `u` — `Φ = a + b`
    increases by exactly `2u` per step, so its per-step increment is
    bounded by `2 * C_MAX` whenever `u` stays admissible (Core §5; Spec
    §7.1's boxed inequality, made exact by construction)."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        u = control(control.t0)[0]
        a, b = state.values
        return State(state.schema, np.array([a + u, b + u]))

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.eye(2)


class KnownUnreachabilityOracle:
    """Cites CLAUDE.md §7's oracle philosophy and docs/ROADMAP.md M9's
    "certificate fires exactly outside the bound" exit gate."""

    def __init__(self, n_steps: int = 4) -> None:
        self.schema = SCHEMA
        self.n_steps = n_steps
        self.operator = AccumulatorOperator()
        self.weight: FloatArray = np.array([1.0, 1.0])

    def initial_state(self) -> State:
        return State(self.schema, np.array([0.0, 0.0]))

    def max_increments(self) -> list[float]:
        """The exact per-step worst-case increment of `Φ = a + b`, known by
        construction (`2 * C_MAX`, since both components move by the same
        admissible `u`)."""
        return [2.0 * C_MAX] * self.n_steps

    def truth(self) -> float:
        """The exact achievable bound on `Φ` after `n_steps` (Spec §7.1):
        `Φ(s_0) + Σ c_max_k = 0 + n_steps * 2 * C_MAX`."""
        return float(self.n_steps * 2.0 * C_MAX)

    def saturating_control(self) -> Control:
        """A control programme that saturates the admissible bound exactly
        (`u = C_MAX` throughout) — rolling the oracle's own operator under
        this control for `n_steps` reaches `Φ` exactly at :meth:`truth`."""
        return Control(0.0, 1.0, lambda t: np.array([C_MAX]))
