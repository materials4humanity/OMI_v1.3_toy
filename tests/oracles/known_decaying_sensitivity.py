"""A constructed chain whose downstream Gramian terms contribute **unequal but
non-annihilating** quadratic forms — the one measurement that separates E-54's two readings.

E-54 records that Core §3.8's observed/inferred distinction is degenerate on both classes of
Core §3.9's error-control dichotomy: *vacuous* where every downstream observation contributes
the same amount (no erasure, contrast), *trivial* where an erasure annihilates all but one
(flagship). It states two readings and marks the second **Medium**:

- **narrow** — the two *declared* classes are the degenerate extremes, and the distinction is
  informative in between;
- **strong** — the distinction is structurally uninformative across the board.

Two domains chosen to invert each other on this axis cannot distinguish those. This oracle
can, because the decay rate is a **dial**.

**Known by construction, which is what makes it an oracle** (CLAUDE.md §7). The operator is a
diagonal linear map with per-component factor `λ`, and the readout reads one component. So the
Gramian term at observation `j` for the eigendirection along that component is exactly
``λ^{2(j−k)}`` times the term at `k`, and the dominance ratio at window `w` is
``λ^{−2(w+1)}`` in closed form — computable before any Gramian is formed, for every `λ`. A
chain with `λ → 1` reproduces contrast's degeneracy and `λ → 0` reproduces flagship's, with
everything in between reachable.

Cites Core §3.8 (the distinction), Core §3.9 (the dichotomy whose two conditions this
interpolates between), Spec §3.3 (the criterion), Spec §2.5 (the declared metric, which is the
identity here by construction — see :func:`build`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import (
    DEFAULT_CONVENTION,
    Observation,
    ObservedInferredConvention,
    Triage,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import Ensemble, FloatArray, Metric, Slot, State, StateSchema

DECAY_SCHEMA = StateSchema(((Slot.M, "decaying", 1), (Slot.M, "companion", 1)))
"""Two components so the posterior has a non-trivial eigenbasis and the median split has
something to split. Only the first is read.

Domain-neutral names on purpose: this is a constructed system, not a domain, so it must not
acquire domain vocabulary it would then have to justify (CLAUDE.md invariant 3 draws the line
at `src/omi/`, and this is a test oracle, but a constructed system with a physical-sounding
name invites being read as evidence about physics)."""

CHAIN_LENGTH = 8
OBSERVATION_NOISE_VARIANCE = 1.0
"""Unity, so every Gramian term is exactly the squared propagated sensitivity and the closed
form in :func:`predicted_dominance_ratio` needs no scale factor."""

COMPANION_DECAY = 0.5
"""The second component's factor, held fixed while the first is swept. Different from the
swept value at every point of the sweep, so the two components never share an eigenvalue and
the eigenbasis stays well-conditioned."""


@dataclass(frozen=True)
class GeometricDecay(EvolutionOperator):
    """`s ↦ (λ·s₀, μ·s₁)` — a diagonal linear map (Core §3.3's evolution operator).

    **Not an erasure at any `λ > 0`**, and that is the whole point: the Jacobian is
    `diag(λ, μ)`, which is full-rank for every positive factor, so sensitivity *decays*
    without being annihilated. At `λ = 1` it is the identity on the read component, which is
    contrast's structure; as `λ → 0` it approaches flagship's, without ever being rank
    deficient.
    """

    decay: float = 0.7
    companion_decay: float = COMPANION_DECAY

    @property
    def is_erasure(self) -> bool:
        """`False` for every positive factor (Core §3.9's condition (a) requires an image of
        substantially lower effective dimension; a full-rank contraction has none)."""
        return False

    def step(self, state: State, control: Control) -> State:
        del control  # the decay is a property of the operator, not of a driving programme
        s = state.with_component(
            Slot.M, "decaying", np.array([self.decay * state.get(Slot.M, "decaying")[0]])
        )
        return s.with_component(
            Slot.M, "companion", np.array([self.companion_decay * s.get(Slot.M, "companion")[0]])
        )


@dataclass(frozen=True)
class FirstComponent(FunctionalReadout):
    """Reads the decaying component (Core §3.5, Type-0; Core §2.6, Class A)."""

    readout_class: ReadoutClass = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "decaying")

    def jacobian(self, state: State) -> FloatArray:
        """Exact and constant (ADR-001): a direct component read."""
        jac = np.zeros((1, state.schema.size))
        jac[0, state.schema.slice_for(Slot.M, "decaying")] = 1.0
        return jac


def build(decay: float) -> tuple[Chain, Ensemble, list[Observation]]:
    """A chain of :data:`CHAIN_LENGTH` identical decaying steps, an incoming ensemble with
    unit spread in both components, and one observation at **every** index.

    The ensemble's unit spread makes `Metric.from_ensemble` the identity, so the declared
    metric contributes no scaling to any quantity reported here (CLAUDE.md invariant 1: the
    metric is declared even when it is trivial, precisely so the triviality is on record
    rather than assumed).
    """
    operator = GeometricDecay(decay=decay)
    control = Control(0.0, 1.0, lambda t: np.array([0.0]))
    chain = Chain(tuple(Segment(operator, control) for _ in range(CHAIN_LENGTH)))
    particles = np.array([[1.0, 1.0], [-1.0, -1.0]], dtype=float)
    ensemble = Ensemble(DECAY_SCHEMA, particles)
    sensors = [
        Observation(
            f"probe_{j}",
            FirstComponent(),
            np.array([[OBSERVATION_NOISE_VARIANCE]]),
            time_index=j,
        )
        for j in range(0, CHAIN_LENGTH + 1)
    ]
    return chain, ensemble, sensors


def predicted_dominance_ratio(decay: float, window: int = 0) -> float:
    """`λ^{−2(w+1)}` — the dominance ratio in closed form, before any Gramian is formed.

    The propagated sensitivity of the read component to a perturbation at `k` is `λ^{j−k}`,
    so observation `j`'s Gramian contribution along that direction is `λ^{2(j−k)}` (the noise
    variance is unity). The largest near-diagonal term is therefore the one at `k` itself and
    the largest downstream term is the one at `k + w + 1`, giving
    ``1 / λ^{2(w+1)}``.

    This is what makes the module an oracle rather than a sweep: the estimator's answer is
    known for every `λ`, so a disagreement is a defect in the estimator and not a surprise
    about the construction.
    """
    return float(decay ** (-2.0 * (window + 1)))


@dataclass(frozen=True)
class DecayReading:
    """One decay rate's measured and predicted readings."""

    decay: float
    window: int
    measured_ratio: float
    predicted_ratio: float
    share: float
    label: str

    @property
    def relative_error(self) -> float:
        if not np.isfinite(self.predicted_ratio) or self.predicted_ratio == 0.0:
            return float("nan")
        return abs(self.measured_ratio - self.predicted_ratio) / self.predicted_ratio


def read(decay: float, *, index: int = 2, window: int = 0, dominance_factor: float = 1.5) -> DecayReading:
    """Measure the dominance ratio and the superseded share for one decay rate.

    *index* is interior — away from both ends — so the direction has near-diagonal *and*
    downstream observations, which is the configuration the distinction is supposed to be
    about and the one neither implemented domain provides at its own query index.
    """
    chain, ensemble, sensors = build(decay)
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    nominal = nominal_trajectory(chain, ensemble[0])
    gramian = compute_gramian(chain, nominal, index, sensors)
    convention = ObservedInferredConvention(
        dominance_factor=dominance_factor,
        abstention_band=DEFAULT_CONVENTION.abstention_band,
        near_diagonal_window=window,
        justification=(
            "Constructed oracle, not a domain: the dominance factor and window are swept "
            "inputs to a measurement of whether the criterion discriminates, so declaring "
            "them here is declaring the experiment rather than a domain's physics."
        ),
    )
    result = danger_triage(
        chain, nominal, index, gramian, prior, [FirstComponent()], sensors, convention=convention
    )
    read_slice = DECAY_SCHEMA.slice_for(Slot.M, "decaying")
    direction = max(
        (d for d in result.directions if d.dominance_ratio is not None),
        key=lambda d: abs(float(d.eigenvector[read_slice][0])),
        default=None,
    )
    if direction is None:  # pragma: no cover - would mean the construction carries no information
        raise AssertionError(f"no direction with a defined dominance ratio at decay={decay}")
    return DecayReading(
        decay=decay,
        window=window,
        measured_ratio=float(direction.dominance_ratio),  # type: ignore[arg-type]
        predicted_ratio=predicted_dominance_ratio(decay, window),
        share=float(direction.near_diagonal_share) if direction.near_diagonal_share is not None else float("nan"),
        label=direction.label.value,
    )


DECAY_SWEEP = (0.995, 0.95, 0.9, 0.8, 0.7, 0.5, 0.3, 0.1)
"""Decay rates from *almost no decay* (contrast's structure) to *almost annihilation*
(flagship's), chosen to straddle the dominance factor rather than to bracket it comfortably:
at `ρ = 1.5` the criterion turns over near `λ = 0.816`, and the sweep has three points above
and five below."""


def sweep(*, window: int = 0, dominance_factor: float = 1.5) -> tuple[DecayReading, ...]:
    """The whole sweep, in one call, so the discrimination question is answered by a curve
    rather than by two endpoints."""
    return tuple(read(d, window=window, dominance_factor=dominance_factor) for d in DECAY_SWEEP)


def turnover_decay(dominance_factor: float = 1.5, window: int = 0) -> float:
    """The decay rate at which the criterion flips, in closed form: `ρ^{−1/(2(w+1))}`.

    Reported because a criterion that discriminates must have a *locatable* turnover, and
    quoting it makes the discrimination claim falsifiable rather than impressionistic.
    """
    return float(dominance_factor ** (-1.0 / (2.0 * (window + 1))))


ALL_LABELS = tuple(t.value for t in Triage)
"""Re-exported so a test can quote the label set it checks against rather than restating it."""
