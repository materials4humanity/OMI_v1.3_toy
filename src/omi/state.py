"""The state schema, the metric, and ensembles on 𝒫(𝒮).

Cites Core §3.1 (the four-slot schema), Core §3.2 (spaces and type
discipline), and Core §3.9 / Spec §2.5 (the metric a Lipschitz constant or
erasure measurement is quoted in). ADR-002 (docs/DECISIONS.md) fixes the
metric's default normalisation; ADR-011 fixes the flat-array-plus-schema
representation used throughout this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Mapping

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


class Slot(Enum):
    """The four state slots (Core §3.1): resolved fields, sub-resolution
    internal variables, the nonlocal/self-consistent field, and interface
    state. Names, not variable names to be renamed for readability
    (CLAUDE.md §3)."""

    M = "m"
    Z = "z"
    NU = "nu"
    GAMMA = "gamma"


@dataclass(frozen=True)
class StateSchema:
    """Declares the named components occupying each slot, and their sizes
    (Core §4 item 1: "State schema — occupants of each slot... with
    resolution limits, and which slots are empty").

    A schema is domain-specific content expressed through a domain-neutral
    shape (ADR-011): it is a flat layout over one array, so every downstream
    numeric routine (Metric, Jacobians, SVDs) is a plain array operation.
    """

    components: tuple[tuple[Slot, str, int], ...]
    """Ordered ``(slot, name, dimension)`` triples. Order fixes the flat
    array layout and must not be changed once state vectors exist."""

    def __post_init__(self) -> None:
        seen: set[tuple[Slot, str]] = set()
        for slot, name, dim in self.components:
            if (slot, name) in seen:
                raise ValueError(f"duplicate component {slot.value}.{name}")
            seen.add((slot, name))
            if dim <= 0:
                raise ValueError(f"component {slot.value}.{name} must have positive dimension")

    @property
    def size(self) -> int:
        """Total flat-vector length underlying the four-slot schema (Core §3.1)."""
        return sum(dim for _, _, dim in self.components)

    def slice_for(self, slot: Slot, name: str) -> slice:
        """Return the flat-array slice occupied by ``slot.name`` (Core §3.1's
        slots, laid out per ADR-011, docs/DECISIONS.md)."""
        offset = 0
        for s, n, dim in self.components:
            if s is slot and n == name:
                return slice(offset, offset + dim)
            offset += dim
        raise KeyError(f"no such component: {slot.value}.{name}")

    def names(self, slot: Slot) -> tuple[str, ...]:
        """Component names declared for *slot* (Core §3.1), in schema order."""
        return tuple(n for s, n, _ in self.components if s is slot)

    def is_empty(self, slot: Slot) -> bool:
        """Whether *slot* has no declared components (Core §4 item 1 requires
        domains to state which slots are empty, e.g. the contrast domain's
        erasure inventory is empty by a different mechanism, but a slot may
        likewise be genuinely unoccupied)."""
        return not self.names(slot)


@dataclass(frozen=True)
class State:
    """A single point ``s = (m, z, ν, Γ) ∈ 𝒮`` (Core §3.1), stored as one flat
    array against a declared :class:`StateSchema` (ADR-011)."""

    schema: StateSchema
    values: FloatArray

    def __post_init__(self) -> None:
        if self.values.shape != (self.schema.size,):
            raise ValueError(
                f"state vector has shape {self.values.shape}, "
                f"schema declares size {self.schema.size}"
            )

    def get(self, slot: Slot, name: str) -> FloatArray:
        """Read the named component's value out of the flat vector (Core §3.1)."""
        return self.values[self.schema.slice_for(slot, name)]

    def with_component(self, slot: Slot, name: str, value: FloatArray) -> "State":
        """Return a new :class:`State` with one component replaced.

        Cites Core §3.3: evolution operators return a new state rather than
        mutating one — states are immutable throughout this framework."""
        sl = self.schema.slice_for(slot, name)
        new_values = self.values.copy()
        new_values[sl] = value
        return State(self.schema, new_values)


@dataclass(frozen=True)
class Ensemble:
    """A statistical representative volume, living on ``𝒫(𝒮)`` rather than
    ``𝒮`` itself (Core §3.2; CLAUDE.md §5 invariant 2). Represented as
    particles: an ``(n_particles, state_dim)`` array against the same
    :class:`StateSchema` every particle shares.
    """

    schema: StateSchema
    particles: FloatArray

    def __post_init__(self) -> None:
        if self.particles.ndim != 2 or self.particles.shape[1] != self.schema.size:
            raise ValueError(
                f"particles has shape {self.particles.shape}, "
                f"expected (n, {self.schema.size})"
            )

    @property
    def n_particles(self) -> int:
        """Particle count representing this element of ``𝒫(𝒮)`` (Core §3.2)."""
        return int(self.particles.shape[0])

    def __getitem__(self, i: int) -> State:
        return State(self.schema, self.particles[i])

    def __iter__(self) -> "_StateIterator":
        return _StateIterator(self)

    def component(self, slot: Slot, name: str) -> FloatArray:
        """The empirical distribution (one value per particle) of a named
        component across the ensemble (Core §3.2: ensembles live on ``𝒫(𝒮)``)."""
        sl = self.schema.slice_for(slot, name)
        return self.particles[:, sl]

    @classmethod
    def from_states(cls, schema: StateSchema, states: list[State]) -> "Ensemble":
        """Build an ensemble (Core §3.2's ``𝒫(𝒮)``) from individually
        constructed particles."""
        if not states:
            raise ValueError("an ensemble needs at least one particle")
        particles = np.stack([s.values for s in states], axis=0)
        return cls(schema, particles)


class _StateIterator(Iterator[State]):
    def __init__(self, ensemble: Ensemble) -> None:
        self._ensemble = ensemble
        self._i = 0

    def __next__(self) -> State:
        if self._i >= self._ensemble.n_particles:
            raise StopIteration
        state = self._ensemble[self._i]
        self._i += 1
        return state


@dataclass(frozen=True)
class Metric:
    """A first-class, declared metric on ``𝒮`` (Core §3.9 / Spec §2.5: every
    Lipschitz constant and erasure measurement is metric-dependent;
    CLAUDE.md §5 invariant 1; ADR-002, docs/DECISIONS.md; OQ-5). Every
    Lipschitz constant, erasure measurement, state distance or trust radius
    reported by this codebase must carry the :class:`Metric` that produced
    it — reports without one are non-conforming.
    """

    schema: StateSchema
    scale: FloatArray
    """Per-component non-dimensionalisation scale, same length as
    ``schema.size``. Default construction (:meth:`from_ensemble`) uses each
    component's aleatoric standard deviation (ADR-002)."""

    def __post_init__(self) -> None:
        if self.scale.shape != (self.schema.size,):
            raise ValueError("metric scale must match the schema's flat size")
        if np.any(self.scale <= 0):
            raise ValueError("metric scale must be strictly positive in every component")

    @classmethod
    def from_ensemble(cls, ensemble: Ensemble) -> "Metric":
        """The default metric (Core §3.9 / Spec §2.5's metric dependence;
        ADR-002): each component scaled by its aleatoric standard deviation
        across a declared incoming population, so a Lipschitz constant reads
        as "how much does a one-sigma incoming variation grow." Components
        with zero empirical variance (constant across the population, or a
        single-particle ensemble) fall back to a scale of 1.0 rather than
        dividing by zero — a defensive numerical choice, not a framework
        claim.
        """
        sigma = ensemble.particles.std(axis=0)
        scale = np.where(sigma > 0, sigma, 1.0)
        return cls(ensemble.schema, scale)

    def normalize(self, delta: FloatArray) -> FloatArray:
        """Non-dimensionalise a state-space displacement by this metric's
        scale (Core §3.9 / Spec §2.5: metric-dependent quantities are
        declared, never bare)."""
        return delta / self.scale

    def distance(self, a: State, b: State) -> float:
        """The declared-metric distance between two states (Core §3.2's
        ``d_𝒮``; CLAUDE.md §5 invariant 1): the Euclidean norm of the
        scale-normalised displacement."""
        return float(np.linalg.norm(self.normalize(a.values - b.values)))


def component_dict(schema: StateSchema, state: State) -> Mapping[str, FloatArray]:
    """A read-only ``"slot.name" -> value`` view of *state*, for diagnostics
    and reporting (CLAUDE.md §8: readable state matters for interrogability,
    Spec §9.3). Not used internally — internal code stays on the flat array
    (ADR-011)."""
    return {
        f"{slot.value}.{name}": state.get(slot, name)
        for slot, name, _ in schema.components
    }
