"""Known-stiffness oracle: two-timescale linear systems with an exactly
controllable separation ratio, for sweeping Core §3.3's semigroup residual
against stiffness (M10.4 Phase 3; the cheapest of the four tests
`docs/PHYSICS-ADEQUACY.md` §3.5 proposes, and the first *physics-derived*
prediction this build has tested).

**What is known by construction.** Each generator is block-triangular, so its
eigenvalues are exactly its diagonal blocks and the separation ratio is an
exact input rather than a fitted property. The fast mode drives the slow one
through a nonzero off-diagonal, so the two are a genuinely coupled system and
not two independent scalars. The exact flow is the matrix exponential, which
satisfies Core §3.3's semigroup identity identically — so **the constructed
truth is that an exact operator's semigroup residual is zero at every
separation ratio**, and any residual an approximating operator shows is
attributable to the approximation rather than to the physics.

**Two fast-mode regimes, because the prediction turns out to depend on which.**
`decaying_generator` gives the fast mode a real negative eigenvalue: a stiff
*transient* that dies almost immediately, its amplitude decaying as fast as
its rate grows. `oscillatory_generator` gives it a lightly-damped complex pair:
a stiff mode that stays excited for the whole interval, which is what
"unresolved at the coarse step" most naturally denotes. The two behave
completely differently under the sweep, and reporting only one would be a
strawman either way.

**Three arms, because the point is a confound.** Core §3.3 offers the semigroup
residual as "a cheap, automatable proxy for insufficiency of `𝒮`" — one stated
cause. This oracle supplies: :class:`ExactFlowOperator` on a sufficient state
(residual zero by construction — the control); :class:`FixedResolutionOperator`
on a sufficient state (the stiffness arm, where any residual is pure
temporal-resolution error with the state fully sufficient); and
:class:`LiftProjectOperator` on a genuinely insufficient state with an exact
propagator (Core's own stated cause, with zero numerical error anywhere in it).

**Why Crank–Nicolson and not explicit Euler** for the fixed-resolution arm.
Explicit Euler amplifies a rotation by `sqrt(1 + (ω·dt)²) > 1` per substep
regardless of step size, so on the oscillatory generator it diverges over many
substeps and the "residual" it reports is that divergence, not a consistency
error — measured directly while building this oracle: iterated Euler gave a
residual of order `1e85` at separation ratio 500, which is a blown-up
integrator and nothing else. Crank–Nicolson is A-stable and, for a pure
rotation, exactly the Cayley transform and therefore norm-preserving, so the
residual it reports is pure consistency error. The norm drift against the exact
flow is reported alongside every measurement so this is checkable rather than
asserted.

Slot placement is deliberate: the fast mode occupies `z` (Core §3.1:
"sub-resolution internal variables... inferable only through dynamics"),
because an unresolved fast mode is exactly what that slot is for.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm, solve

from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, Slot, State, StateSchema

DECAYING_SCHEMA = StateSchema(
    (
        (Slot.M, "resolved_mode", 1),
        (Slot.Z, "unresolved_mode", 1),
    )
)
"""Slow mode (resolved, `m`) plus one fast decaying mode (sub-resolution, `z`)."""

OSCILLATORY_SCHEMA = StateSchema(
    (
        (Slot.M, "resolved_mode", 1),
        (Slot.Z, "unresolved_mode_a", 1),
        (Slot.Z, "unresolved_mode_b", 1),
    )
)
"""Slow mode plus a fast oscillator pair — a fast mode that stays excited."""

REDUCED_SCHEMA = StateSchema(((Slot.M, "resolved_mode", 1),))
"""The insufficient description: the slow mode alone, fast mode dropped."""

SLOW_RATE = 1.0
"""`λ_slow`. The swept interval is one slow timescale — the natural choice an
implementer makes, sizing the step to the process being modelled — which is
what leaves the fast mode progressively unresolved as the ratio grows."""

COUPLING = 1.0
"""The fast mode's contribution to the slow mode's rate of change. Nonzero, so
the fast mode is not ignorable in principle."""

OSCILLATOR_DAMPING = 0.05
"""Light damping on the oscillatory pair, so it persists across the interval
rather than decaying like the transient case."""


def decaying_generator(separation_ratio: float) -> FloatArray:
    """`A` in `ds/dt = -A s`, upper triangular: `eig(A) = {SLOW_RATE,
    SLOW_RATE · separation_ratio}` exactly. The fast mode is a real decaying
    transient."""
    if separation_ratio < 1.0:
        raise ValueError("separation_ratio must be >= 1 (the fast mode is the faster one)")
    return np.array([[SLOW_RATE, -COUPLING], [0.0, SLOW_RATE * separation_ratio]])


def oscillatory_generator(separation_ratio: float) -> FloatArray:
    """`A` in `ds/dt = -A s`, block upper triangular: the fast block is a
    lightly-damped rotation at angular frequency `SLOW_RATE ·
    separation_ratio`, so the fast mode stays excited for the whole
    interval."""
    if separation_ratio < 1.0:
        raise ValueError("separation_ratio must be >= 1 (the fast mode is the faster one)")
    omega = SLOW_RATE * separation_ratio
    return np.array(
        [
            [SLOW_RATE, -COUPLING, 0.0],
            [0.0, OSCILLATOR_DAMPING * omega, -omega],
            [0.0, omega, OSCILLATOR_DAMPING * omega],
        ]
    )


@dataclass(frozen=True)
class ExactFlowOperator(EvolutionOperator):
    """`s(t+dt) = exp(-A dt) s(t)` — a semigroup by construction at every
    separation ratio. The control arm."""

    generator: FloatArray

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, expm(-self.generator * control.duration) @ state.values)


@dataclass(frozen=True)
class FixedResolutionOperator(EvolutionOperator):
    """The same dynamics advanced by a **fixed number of internal substeps
    regardless of the interval's length** (Crank–Nicolson, `n_substeps` per
    call).

    The stand-in for "an operator learned at one `Δt`": a learned operator has
    a fixed internal resolution and is asked to span whatever interval it is
    handed, so a longer interval asks it to represent more per unit of its own
    capacity. Splitting the interval halves each substep, changing the answer —
    which is exactly the semigroup residual. Nothing about the *physics*
    differs from :class:`ExactFlowOperator`; only the resolution at which it is
    realised, and the state is fully sufficient throughout.
    """

    generator: FloatArray
    n_substeps: int = 256

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        sub_dt = control.duration / self.n_substeps
        identity = np.eye(self.generator.shape[0])
        lhs = identity + self.generator * sub_dt / 2.0
        rhs = identity - self.generator * sub_dt / 2.0
        values = state.values
        for _ in range(self.n_substeps):
            values = solve(lhs, rhs @ values)
        return State(state.schema, values)

    def norm_drift(self, state: State, control: Control) -> float:
        """Relative discrepancy in state norm against the exact flow over the
        same interval — reported alongside every residual so a reader can
        confirm the integrator is not diverging and the residual is therefore
        consistency error rather than blow-up."""
        approx = self.step(state, control)
        exact = ExactFlowOperator(self.generator).step(state, control)
        return float(abs(np.linalg.norm(approx.values) / np.linalg.norm(exact.values) - 1.0))


@dataclass(frozen=True)
class LiftProjectOperator(EvolutionOperator):
    """The exact flow reached through a **closure**: lift the slow-mode-only
    state by assigning the fast mode a fixed declared value, advance exactly,
    project back.

    Genuinely insufficient in Axiom S's sense — the true future depends on the
    actual fast-mode value, which this description does not carry — and
    **exact everywhere else**, since the propagator is the matrix exponential.
    Any semigroup residual is therefore attributable to the insufficiency
    alone, making this the clean instance of the one cause Core §3.3 names
    ("a cheap, automatable proxy for insufficiency of `𝒮`"). Re-lifting at the
    split point is what discards the true fast-mode value and breaks the
    semigroup property; this is Core §3.7's "absorb" treatment.
    """

    generator: FloatArray
    closure_value: float = 1.0

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        lifted = np.concatenate(
            [state.values, np.full(self.generator.shape[0] - state.values.shape[0], self.closure_value)]
        )
        evolved = expm(-self.generator * control.duration) @ lifted
        return State(state.schema, evolved[: state.values.shape[0]])


@dataclass(frozen=True)
class KnownStiffnessTruth:
    separation_ratio: float
    slow_rate: float
    fast_rate: float
    exact_semigroup_residual: float
    """Zero by construction: `exp(-A(t1-t0)) = exp(-A(t1-tm))·exp(-A(tm-t0))`
    identically, for every generator and every separation ratio."""


@dataclass(frozen=True)
class KnownStiffnessOracle:
    """The oracle protocol (`tests/oracles/__init__.py`)."""

    separation_ratio: float = 1.0
    oscillatory: bool = False

    def truth(self) -> KnownStiffnessTruth:
        return KnownStiffnessTruth(
            separation_ratio=self.separation_ratio,
            slow_rate=SLOW_RATE,
            fast_rate=SLOW_RATE * self.separation_ratio,
            exact_semigroup_residual=0.0,
        )

    def generator(self) -> FloatArray:
        if self.oscillatory:
            return oscillatory_generator(self.separation_ratio)
        return decaying_generator(self.separation_ratio)

    def schema(self) -> StateSchema:
        return OSCILLATORY_SCHEMA if self.oscillatory else DECAYING_SCHEMA

    def initial_state(self) -> State:
        """A state exciting both modes, so neither is trivially absent."""
        values = np.array([1.0, 1.0, 0.0]) if self.oscillatory else np.array([1.0, 1.0])
        return State(self.schema(), values)

    def reduced_initial_state(self) -> State:
        return State(REDUCED_SCHEMA, np.array([1.0]))
