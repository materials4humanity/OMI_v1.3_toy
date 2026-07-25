"""Evolution operators: the elementary map, its lift to ensembles, and the
declared-metric local spectrum.

Cites Core §3.2 (control space), Core §3.3 (evolution operators, the
pushforward/kernel lift to ``𝒫(𝒮)``, and the semigroup identity), and Core
§3.9 (the erasure definition this module lets an operator declare). ADR-012
and ADR-013 (docs/DECISIONS.md) fix the structural choices this module
makes that the Specification itself leaves open.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

import numpy as np

from omi.gaps import NotSpecified
from omi.state import Ensemble, FloatArray, Metric, State


@dataclass(frozen=True)
class Control:
    """A time-dependent driving programme over a declared interval (Core
    §3.2: "elements are functions of time on an interval, not scalars").

    Cites Core §3.2. ADR-013 (docs/DECISIONS.md): wraps a plain callable
    rather than a sampled grid or spline, since no domain here needs either
    yet and a callable admits exact closed-form evaluation at any ``t``.
    """

    t0: float
    t1: float
    fn: Callable[[float], FloatArray]

    def __post_init__(self) -> None:
        if self.t1 <= self.t0:
            raise ValueError(f"control interval must have t1 > t0, got [{self.t0}, {self.t1}]")

    def __call__(self, t: float) -> FloatArray:
        if not (self.t0 <= t <= self.t1):
            raise ValueError(f"t={t} outside declared control interval [{self.t0}, {self.t1}]")
        return self.fn(t)

    @property
    def duration(self) -> float:
        """The interval length ``t1 - t0`` (Core §3.2's control interval)."""
        return self.t1 - self.t0


def _finite_difference_jacobian(
    f: Callable[[FloatArray], FloatArray], x: FloatArray, eps: float = 1e-6
) -> FloatArray:
    """Central finite-difference Jacobian of ``f`` at ``x``.

    Plain numerics, not a framework claim (ADR-012): the default estimator
    when a domain operator does not override :meth:`EvolutionOperator.jacobian`
    with an exact analytic derivative.
    """
    n = x.shape[0]
    f0 = f(x)
    m = f0.shape[0]
    jac = np.zeros((m, n), dtype=np.float64)
    for j in range(n):
        step = np.zeros(n, dtype=np.float64)
        h = eps * max(1.0, abs(x[j]))
        step[j] = h
        jac[:, j] = (f(x + step) - f(x - step)) / (2 * h)
    return jac


class EvolutionOperator(ABC):
    """The elementary evolution operator (Core §3.3):
    ``s_{k+1} = G(s_k, u_k)``.

    ADR-012 (docs/DECISIONS.md) fixes what a concrete domain operator must
    supply versus what this base class computes generically: ``step`` and
    ``is_erasure`` are domain-declared; ``jacobian`` defaults to a
    finite-difference estimate a domain may override; ``lift`` (the
    pushforward to ``𝒫(𝒮)``) and ``lipschitz`` (the metric-scaled local
    spectrum) are generic given those.
    """

    @abstractmethod
    def step(self, state: State, control: Control) -> State:
        """Advance one state under one control programme (Core §3.3)."""

    @property
    @abstractmethod
    def is_erasure(self) -> bool:
        """Whether this operator is declared an erasure (Core §3.9: image of
        substantially lower effective dimension, ``L ≪ 1``). Declared by the
        domain, per ADR-012 — not computed from an invented numeric
        threshold; quantitative erasure completeness is M2's ``erasure.py``.
        """

    def jacobian(self, state: State, control: Control) -> FloatArray:
        """The tangent map ``D_s step(state, control)`` (Core §3.3; Spec
        §3.1's ``F_k``). Defaults to a central finite-difference estimate
        (ADR-012); override with an exact analytic derivative where one is
        available — ADR-001 notes this is what eventually makes M3's
        observability oracles trustworthy.
        """
        return _finite_difference_jacobian(lambda v: self.step(State(state.schema, v), control).values, state.values)

    def lift(self, ensemble: Ensemble, control: Control) -> Ensemble:
        """Pushforward lift to ``𝒫(𝒮)`` (Core §3.3): apply :meth:`step` to
        every particle. ADR-012: generic given ``step``, not overridden per
        domain."""
        new_particles = np.stack(
            [self.step(ensemble[i], control).values for i in range(ensemble.n_particles)],
            axis=0,
        )
        return Ensemble(ensemble.schema, new_particles)

    def lipschitz(self, state: State, control: Control, metric: Metric) -> FloatArray:
        """The local spectrum (singular values) of the Jacobian, expressed in
        the *declared* metric (Core §3.3; Spec §2.5 requires a local
        spectrum, not a single global bound). ADR-012: generic given
        ``jacobian``.
        """
        jac = self.jacobian(state, control)
        scaled = jac * metric.scale[np.newaxis, :] / metric.scale[:, np.newaxis]
        result: FloatArray = np.linalg.svd(scaled, compute_uv=False)
        return result


@dataclass(frozen=True)
class LipschitzReport:
    """A local spectrum together with the metric that produced it (CLAUDE.md
    §5 invariant 1; Core §3.9 / Spec §2.5: every reported Lipschitz constant
    is metric-dependent and must carry its metric). Never pass the bare
    spectrum array around where a report is expected to be quoted."""

    spectrum: FloatArray
    metric: Metric


def lipschitz_report(
    operator: EvolutionOperator, state: State, control: Control, metric: Metric
) -> LipschitzReport:
    """Compute :meth:`EvolutionOperator.lipschitz` and package it with its
    metric (Core §3.9 / Spec §2.5), per docs/ROADMAP.md M2: "Lipschitz
    spectra reported with their metric attached."
    """
    return LipschitzReport(operator.lipschitz(state, control, metric), metric)


def amplification_decomposition(
    operator: EvolutionOperator, state: State, control: Control, metric: Metric
) -> tuple[FloatArray, FloatArray]:
    """Refuses: ``L_total = L_phys x L_num`` (Spec §2.5) has no estimation
    procedure in the Specification — "[Pass B] ... To be written: estimation
    procedure for the local spectrum by finite differences..." This function
    exists so the refusal is executable (CLAUDE.md §4) rather than the
    decomposition being silently omitted; callers needing the *total*
    spectrum should use :func:`lipschitz_report` instead, which is fully
    specified (Core §3.3).
    """
    raise NotSpecified(
        "S-2.5",
        "Spec §2.5",
        "the physical/numerical amplification decomposition L_phys x L_num "
        "has no estimation procedure in the Specification; only the total "
        "local spectrum (lipschitz_report) is specified",
    )


def semigroup_residual(
    op: EvolutionOperator,
    state: State,
    control: Control,
    t_mid: float,
) -> float:
    """Check Core §3.3's semigroup identity for a single operator applied
    across a split interval: evolving straight from ``t0`` to ``t1`` must
    equal evolving ``t0 -> t_mid`` then ``t_mid -> t1``, for the *same*
    underlying control programme restricted to each sub-interval.

    Returns the Euclidean norm of the discrepancy between the two resulting
    state vectors — "≈ 0" for an exact analytic flow (docs/ROADMAP.md M1
    exit gate). This is a diagnostic residual, not a metric-declared
    quantity, so it is reported as a plain float rather than wrapped with a
    :class:`~omi.state.Metric` (Core §3.3; contrast with Spec §2.5, whose
    Lipschitz spectra do require one).
    """
    if not (control.t0 < t_mid < control.t1):
        raise ValueError(f"t_mid={t_mid} must lie strictly inside ({control.t0}, {control.t1})")

    whole = Control(control.t0, control.t1, control.fn)
    first = Control(control.t0, t_mid, control.fn)
    second = Control(t_mid, control.t1, control.fn)

    direct = op.step(state, whole)
    composed = op.step(op.step(state, first), second)
    return float(np.linalg.norm(direct.values - composed.values))
