"""Erasure measurement: rank, surviving subspace, and component-level
recoverability.

Cites Core §3.9 (the erasure definition and its three consequences) and
Spec §3.2 (Proposition 3.2, Corollary 3.3: an erasure of Jacobian rank ``r``
truncates the observability Gramian to rank ``r``, and kernel directions are
both unidentifiable and uninfluential downstream). ADR-017 (docs/DECISIONS.md)
fixes the numerical rank tolerance; OQ-2 (docs/COVERAGE.md Part IV,
docs/DECISIONS.md) is investigated by :func:`component_recoverability`
alongside the operator-level rank measurement in
``tests/oracles/test_known_erasure.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble, FloatArray, Metric, Slot, State


@dataclass(frozen=True)
class ErasureMeasurement:
    """The metric-scaled Jacobian's singular-value spectrum, split into a
    surviving subspace (the row space — ``rank`` directions) and an erased
    subspace (the numerical kernel), per Spec §3.2's Proposition 3.2 /
    Corollary 3.3.

    The full spectrum is always carried alongside the integer ``rank``
    (ADR-017): whether a given rank deficiency is "substantially lower" — the
    qualitative content of Core §3.9's ``L ≪ 1`` — is a judgement for the
    reader of the spectrum, not a hidden constant.
    """

    spectrum: FloatArray
    """Singular values in descending order, length = ``min(state_dim, state_dim)``."""
    rank: int
    """Numerical rank at the declared tolerance (ADR-017)."""
    surviving_basis: FloatArray
    """``(state_dim, rank)``: right singular vectors spanning the surviving
    subspace — directions that remain identifiable and influential
    downstream (Spec §3.2 Corollary 3.3)."""
    erased_basis: FloatArray
    """``(state_dim, state_dim - rank)``: right singular vectors spanning the
    numerical kernel — unidentifiable from post-erasure data and without
    downstream influence (Spec §3.2 Corollary 3.3)."""
    metric: Metric
    """The declared metric the Jacobian was scaled by before the SVD (Core
    §3.9 / Spec §2.5: erasure measurement is metric-dependent)."""
    tol: float
    """The absolute singular-value threshold used for the rank cutoff
    (ADR-017) — reported, not hidden."""


def measure_erasure(
    operator: EvolutionOperator,
    state: State,
    control: Control,
    metric: Metric,
    rtol: float | None = None,
) -> ErasureMeasurement:
    """Measure an operator's erasure rank and surviving subspace at
    ``(state, control)``, in the declared *metric* (Core §3.9; Spec §3.2's
    Proposition 3.2).

    *rtol*, if given, overrides the default numerical-rank tolerance
    (ADR-017): the absolute cutoff becomes ``spectrum[0] * rtol``. The
    default matches :func:`numpy.linalg.matrix_rank`'s own convention.
    """
    jacobian = operator.jacobian(state, control)
    scaled = jacobian * metric.scale[np.newaxis, :] / metric.scale[:, np.newaxis]
    _, spectrum, vt = np.linalg.svd(scaled)

    if rtol is None:
        rtol = max(scaled.shape) * np.finfo(scaled.dtype).eps
    tol = float(spectrum[0] * rtol) if spectrum.size else 0.0
    rank = int(np.sum(spectrum > tol))

    v = vt.T
    surviving = v[:, :rank]
    erased = v[:, rank:]
    return ErasureMeasurement(spectrum, rank, surviving, erased, metric, tol)


def component_recoverability(
    operator: EvolutionOperator,
    ensemble: Ensemble,
    control: Control,
    slot: Slot,
    name: str,
) -> float:
    """An empirical estimate of Core §3.9 consequence 3's "residual variance
    explained by upstream variables" for one named component, across
    *ensemble* — R-squared of the post-step value regressed on the pre-step
    value.

    This operationalises only one of Core's two named candidate measures
    (the other, mutual information, is not implemented — see OQ-2,
    docs/COVERAGE.md Part IV). R-squared equals the squared Pearson
    correlation for a least-squares linear fit with intercept, so it is
    computed directly from the correlation coefficient rather than via a
    separate regression routine.

    Returns 0.0 if either the pre- or post-step value is constant across the
    ensemble (correlation undefined; there is nothing for either variable to
    explain).
    """
    lifted = operator.lift(ensemble, control)
    pre = ensemble.component(slot, name)[:, 0]
    post = lifted.component(slot, name)[:, 0]
    if np.std(pre) == 0.0 or np.std(post) == 0.0:
        return 0.0
    correlation = np.corrcoef(pre, post)[0, 1]
    return float(correlation**2)
