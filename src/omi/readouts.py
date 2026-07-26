"""Readout operators: functional (Type-0), constitutive (Type-1), and a
bounded Type-2 component-readout base (Tier I½, ADR-035).

Cites Core §3.5 (the three readout types), Core §2.6 (property vs.
performance by invariance), and Core §3.6 (Class A/B, the weakest-link
formula this module implements literally for Class B). ADR-014
(docs/DECISIONS.md) records why these are three distinct call shapes rather
than one interface, and why Class B here is the literal resampling
construction rather than M6's driver/tail-separated machinery. ADR-035
records why :class:`ComponentReadout` and :class:`Type2Geometry` exist at
all despite CLAUDE.md §9's Tier II anti-goal, and the precise, structurally-
enforced fence around them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import numpy as np

from omi.operators import Control, finite_difference_jacobian
from omi.state import Ensemble, FloatArray, State


class ReadoutType(Enum):
    """Core §3.5's three readout types, graded by codomain."""

    TYPE_0 = 0
    """Functional: ``ρ_0: 𝒮 → ℝ^n`` (or a curve space)."""
    TYPE_1 = 1
    """Operator-valued (constitutive): ``𝒮 → Op(𝒰 → ℛ × 𝒮)``, an operator
    with memory, not a value."""
    TYPE_2 = 2
    """Component: ``Op × 𝔅 → ℛ``, requiring geometry. Tier II boundary-value
    problems remain an anti-goal (CLAUDE.md §9); :class:`ComponentReadout`
    below is the bounded Tier I½ exception ADR-035 (docs/DECISIONS.md)
    carves out of that anti-goal, restricted to a two-scalar geometry."""


class ReadoutClass(Enum):
    """Core §3.6: self-averaging vs. weakest-link/extreme-value."""

    A = "A"
    """Self-averaging: an RVE exists, ``Var ρ(V) ~ V^-1``."""
    B = "B"
    """Weakest-link: no RVE exists; the readout is governed by the worst
    local configuration in the driven volume."""


class FunctionalReadout(ABC):
    """A Type-0 readout (Core §3.5): ``ρ_0: 𝒮 → ℝ^n``.

    A :attr:`readout_class` of :class:`ReadoutClass.B` additionally makes
    :meth:`weakest_link` available — the literal Core §3.6 weakest-link
    construction, not the driver/tail-separated M6 refinement (ADR-014).
    """

    readout_class: ReadoutClass
    readout_type: ReadoutType = ReadoutType.TYPE_0
    """Core §3.5's type tag (ADR-035): every readout base now declares its
    own, so :class:`ReadoutType` is load-bearing rather than declared and
    never read."""

    @abstractmethod
    def evaluate(self, state: State) -> FloatArray:
        """The functional's value at a single state (Core §3.5, Type-0:
        ``ρ_0: 𝒮 → ℝ^n``)."""

    def jacobian(self, state: State) -> FloatArray:
        """``D_s evaluate(state)`` (Core §3.8's Proposition: "the observation
        operator H is a Type-0 readout" — this is Spec §3.1's ``H'_j`` when a
        :class:`FunctionalReadout` is used as an observation operator).
        Defaults to a central finite-difference estimate, same convention as
        :meth:`~omi.operators.EvolutionOperator.jacobian` (ADR-012);
        override with an exact analytic derivative where available.
        """
        return finite_difference_jacobian(lambda v: self.evaluate(State(state.schema, v)), state.values)

    def __call__(self, ensemble: Ensemble) -> FloatArray:
        """Evaluate at every particle, returning the empirical distribution
        of this readout across the ensemble (CLAUDE.md §5 invariant 2: the
        ensemble is a measure, so its readout is a distribution of values,
        not one value)."""
        return np.stack([self.evaluate(ensemble[i]) for i in range(ensemble.n_particles)], axis=0)

    def weakest_link(
        self,
        ensemble: Ensemble,
        n_sub: int,
        n_trials: int,
        rng: np.random.Generator,
    ) -> FloatArray:
        """The Class B distribution at an ``n_sub``-fold larger driven volume
        (Core §3.6): for ``N`` statistically independent sub-volumes,
        ``P(ρ_V > x) = [P(ρ_0 > x)]^N``.

        Computed by direct resampling from this readout's own empirical
        distribution over *ensemble* — the literal formula, with no driven
        volume field, tail extrapolation, or join threshold (ADR-014; those
        arrive at M6). Returns ``n_trials`` Monte Carlo draws of ``ρ_V``, a
        distribution, never a point prediction (CLAUDE.md §5 invariant 4).
        """
        if self.readout_class is not ReadoutClass.B:
            raise ValueError(
                f"weakest_link is only defined for Class B readouts, got {self.readout_class}"
            )
        if self.evaluate(ensemble[0]).shape != (1,):
            raise ValueError("weakest_link requires a scalar (shape (1,)) readout")
        base = self(ensemble)[:, 0]
        drawn = rng.choice(base, size=(n_trials, n_sub), replace=True)
        maxima: FloatArray = drawn.max(axis=1)
        return maxima


class ConstitutiveOperator(ABC):
    """The operator-with-memory a Type-1 readout returns (Core §3.5):
    ``𝒞: 𝒰 → ℛ × 𝒮``. Maps a driving history to a response history *and* an
    updated state — it is not a function, it carries ``z``."""

    @abstractmethod
    def respond(self, control: Control) -> tuple[FloatArray, State]:
        """Apply a driving programme; return ``(response, updated_state)``
        (Core §3.5, Type-1)."""


class ConstitutiveReadout(ABC):
    """A Type-1 readout (Core §3.5): ``ℛ_const: 𝒮 → Op(𝒰 → ℛ × 𝒮)``. Calling
    it on a state returns a bound :class:`ConstitutiveOperator`, not a value —
    this is the formal content of homogenisation (Core §3.5)."""

    readout_type: ReadoutType = ReadoutType.TYPE_1

    @abstractmethod
    def __call__(self, state: State) -> ConstitutiveOperator:
        """Extract the constitutive operator implied by *state*."""


@dataclass(frozen=True)
class Type2Geometry:
    """Core §4 item 4b's geometry input for a Type-2 (component) readout,
    restricted to Tier I½ (ADR-035, docs/DECISIONS.md): a thickness and a
    curvature, nothing richer. This is the structural fence itself — if a
    domain ever needs to pass something other than two bare scalars here
    (a mesh, an element connectivity table, a shape catalogue entry),
    ADR-035 has been breached and must be revisited, not this dataclass
    extended.
    """

    thickness: float
    curvature: float = 0.0
    """Zero curvature is a valid, flat degenerate case; it is not a second
    loading mode."""

    def __post_init__(self) -> None:
        if self.thickness <= 0.0:
            raise ValueError(f"thickness must be positive, got {self.thickness}")


class ComponentReadout(ABC):
    """A Type-2 readout (Core §3.5), restricted to Tier I½ (ADR-035):
    ``ρ_2(𝒞, geometry) -> response``, Core §4's item 4 for a component
    (performance) readout — plus the process-zone *volume* Core §3.6's
    Class B claim couples the two tiers through. Both are returned, never
    just the response, or the coupling claim is not exercised by whatever
    calls this.

    No mechanics vocabulary here (CLAUDE.md §5 invariant 3): the quadrature,
    strain profile, and driver-field construction are entirely the concrete
    domain subclass's responsibility (`omi_domains/flagship/readouts.py`).
    """

    readout_class: ReadoutClass
    readout_type: ReadoutType = ReadoutType.TYPE_2

    @abstractmethod
    def evaluate(
        self, operator: ConstitutiveOperator, geometry: Type2Geometry
    ) -> tuple[FloatArray, float]:
        """Return ``(response, process_zone_volume)`` (Core §3.6) for
        *operator* (a bound Type-1 constitutive operator) under *geometry*
        (Tier I½'s two-scalar fence, ADR-035)."""
