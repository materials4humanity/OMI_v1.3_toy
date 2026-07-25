"""The known-erasure oracle (CLAUDE.md §7; Core §3.9, Spec §3.2 Prop 3.2).

A diagonal linear map with an exactly-designed rank: one component survives
at full gain, one survives at a deliberately *small* gain (the OQ-2 probe —
docs/COVERAGE.md Part IV), and one is exactly erased (zero gain). Needs no
learned or even non-linear machinery — the whole point of an oracle
(ADR-004, docs/DECISIONS.md) is that its truth is known by construction, and
a diagonal map's rank and surviving subspace are as constructed as it gets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema


@dataclass(frozen=True)
class ErasureTruth:
    """The constructed ground truth a rank/subspace estimator must recover."""

    rank: int
    surviving_indices: tuple[int, ...]
    erased_indices: tuple[int, ...]

SCHEMA = StateSchema(
    (
        (Slot.M, "surviving_full", 1),  # gain 1.0
        (Slot.M, "surviving_small", 1),  # gain 0.15 — OQ-2 probe
        (Slot.Z, "erased", 1),  # gain 0.0
    )
)

GAINS: FloatArray = np.array([1.0, 0.15, 0.0])


@dataclass(frozen=True)
class DiagonalErasureOperator(EvolutionOperator):
    """A diagonal linear map, ``step(s) = gains * s``: rank and surviving
    subspace are known exactly by construction (Core §3.9)."""

    gains: FloatArray = field(default_factory=lambda: GAINS.copy())

    @property
    def is_erasure(self) -> bool:
        return True

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, state.values * self.gains)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        """Exact analytic Jacobian (ADR-001/ADR-012) — a diagonal linear map
        needs no finite-difference estimate."""
        return np.diag(self.gains)


class KnownErasureOracle:
    """Cites CLAUDE.md §7's "known erasure" oracle: an operator with a
    designed rank-``r`` Jacobian, whose rank and surviving subspace an
    estimator must recover exactly."""

    def __init__(self) -> None:
        self.schema = SCHEMA
        self.operator = DiagonalErasureOperator()
        self.null_control = Control(0.0, 1.0, lambda t: np.array([0.0]))

    def build_ensemble(self, n: int, rng: np.random.Generator) -> Ensemble:
        particles = rng.normal(size=(n, self.schema.size))
        return Ensemble(self.schema, particles)

    def truth(self) -> ErasureTruth:
        """The constructed rank, and which flat-array indices survive versus
        are erased."""
        gains = self.operator.gains
        surviving = tuple(int(i) for i, g in enumerate(gains) if g != 0.0)
        erased = tuple(int(i) for i, g in enumerate(gains) if g == 0.0)
        return ErasureTruth(rank=len(surviving), surviving_indices=surviving, erased_indices=erased)
