"""Two operators over the sub-resolution occupant: one conserving the domain mean, one
losing solute through a declared boundary (Core §3.3; ADR-050, ADR-076).

**Why two.** ADR-050's constancy residual has two substantive verdicts — a closed domain
whose mean holds, and a domain whose mean drifts — and one operator can exhibit only one of
them. The pair puts both on declared physics rather than only in an oracle, so the domain
*exercises* the diagnosis instead of merely permitting it.

**Why the conservative one changes the state at all.** A no-op would satisfy the residual
trivially and demonstrate nothing. It coarsens `substructure_density` — a real state change
— while leaving the domain-mean deviation **exactly** untouched, which is the substantive
claim: redistribution inside a closed boundary changes the state without moving the domain
mean, and the residual confirms that rather than assuming it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import State

from omi_domains.flagship_composition.state import (
    COMPOSITION_SCHEMA,
    DELTA_C_MEAN_INDEX,
    SUBSTRUCTURE_INDEX,
)


@dataclass(frozen=True)
class ConservativeRedistribution(EvolutionOperator):
    """Redistributes sub-resolution solute without moving the domain mean (Core §3.3;
    Spec §2.2's conservation category).

    **Conservation is structural, not approximate.** The domain-mean deviation is not written
    at all, so the domain mean of `c̄ + δc` is exactly its initial value at every step — for
    any rate, any duration, any number of steps. That is what ADR-050 says a closed domain
    must give, and the residual measures it rather than trusting this docstring.
    """

    coarsening_rate: float

    @property
    def name(self) -> str:
        return "conservative_redistribution"

    @property
    def is_erasure(self) -> bool:
        """Not declared an erasure (Core §3.4). It contracts one component; the declaration is
        about the image's effective dimension, which `omi.erasure` would measure as near-full
        here. Declaring otherwise would be the unmeasured assertion CLAUDE.md §5 forbids."""
        return False

    def __post_init__(self) -> None:
        if self.coarsening_rate < 0.0:
            raise ValueError("coarsening rate must be non-negative")

    def step(self, state: State, control: Control) -> State:
        values = state.values.copy()
        values[SUBSTRUCTURE_INDEX] *= float(np.exp(-self.coarsening_rate * control.duration))
        # DELTA_C_MEAN_INDEX is deliberately not written: nothing crosses the boundary.
        return State(schema=state.schema, values=values)


@dataclass(frozen=True)
class BoundaryLossRedistribution(EvolutionOperator):
    """The same redistribution **plus** a declared boundary flux (Core §3.3; ADR-050's
    decarburisation instance, which is that entry's own worked case for a drifting mean).

    The domain mean therefore moves by `-boundary_flux × duration` per step, exactly and
    predictably, which is what makes the oracle's recovery of a planted drift checkable
    against a known answer (CLAUDE.md §7).
    """

    coarsening_rate: float
    boundary_flux: float
    """Solute lost per unit time through the free boundary, in fraction units. Strictly
    positive: an operator declared as a loss with a non-positive flux is the vacuous
    declaration ADR-050's repair asks to be replaced with a real one. Ingress is not modelled
    and would need its own declaration."""

    @property
    def name(self) -> str:
        return "boundary_loss_redistribution"

    @property
    def is_erasure(self) -> bool:
        """Not declared an erasure, for the same reason as its conservative sibling
        (Core §3.4)."""
        return False

    def __post_init__(self) -> None:
        if self.coarsening_rate < 0.0:
            raise ValueError("coarsening rate must be non-negative")
        if self.boundary_flux <= 0.0:
            raise ValueError(
                "boundary flux must be strictly positive: a loss operator with no loss is the "
                "vacuous declaration ADR-050's repair exists to replace"
            )

    def step(self, state: State, control: Control) -> State:
        dt = control.duration
        values = state.values.copy()
        values[SUBSTRUCTURE_INDEX] *= float(np.exp(-self.coarsening_rate * dt))
        values[DELTA_C_MEAN_INDEX] -= self.boundary_flux * dt
        return State(schema=state.schema, values=values)


COARSENING = ConservativeRedistribution(coarsening_rate=0.4)
"""The closed-domain operator. The rate only has to make the substructure change visible;
nothing downstream depends on its value."""

BOUNDARY_LOSS = BoundaryLossRedistribution(coarsening_rate=0.4, boundary_flux=0.015)
"""The open-domain operator, ADR-050's worked instance. The flux is *declared*, which is the
point: a drifting mean with a named flux is a consistent declaration, while a drifting mean
under a closed declaration is the finding."""

assert COMPOSITION_SCHEMA.size == 8, "operators address components positionally (ADR-011)"
