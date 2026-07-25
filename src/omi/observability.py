"""Observability: the Gramian, posterior covariance, danger score, the
four-way triage, value of information, and worst-case-over-window.

Cites Core §3.8 (assimilation, the observability Gramian, danger score, the
observed/inferred/dangerous/marginalisable triage) and Spec §3 in full
(construction §3.1, erasure truncation §3.2, the decision-weighted spectrum
§3.3, value of information §3.4, matrix-free computation §3.5, trajectory
dependence §3.6). ADR-018, ADR-019 and ADR-020 (docs/DECISIONS.md) fix the
structural choices Spec §3's formulas leave open: how Φ is propagated
without ever being formed as a chained matrix product, the default prior
covariance, and the triage's threshold conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import numpy as np

from omi.chain import Chain, Trajectory
from omi.readouts import FunctionalReadout
from omi.state import Ensemble, FloatArray, Metric, State


@dataclass(frozen=True)
class Observation:
    """One instrumented index in a chain: a readout standing in for an
    observation operator (Core §3.8's Proposition: "the observation operator
    H is a Type-0 readout"), a noise covariance, and where in the chain it is
    taken.
    """

    name: str
    readout: FunctionalReadout
    noise_covariance: FloatArray
    time_index: int
    """Which entry of a :class:`~omi.chain.Trajectory` this observation reads
    (0 = the initial ensemble, i = after segment ``i - 1``)."""


def nominal_trajectory(chain: Chain, initial_state: State) -> Trajectory:
    """Roll a single reference state through *chain* (Spec §3.1's ``{s̄_k}``),
    by lifting it to a one-particle ensemble and reusing
    :meth:`~omi.chain.Chain.rollout` — no separate nominal-trajectory
    machinery is needed."""
    singleton = Ensemble(initial_state.schema, initial_state.values[np.newaxis, :])
    return chain.rollout(singleton)


def propagate_jvp(chain: Chain, nominal: Trajectory, k: int, j: int, v: FloatArray) -> FloatArray:
    """``Φ_{j,k} v`` as a forward Jacobian-vector product (Spec §3.5):
    apply each segment's own Jacobian to a vector, one segment at a time,
    from index ``k`` to index ``j``. ``Φ_{j,k}`` is never formed as a
    matrix — segment Jacobians are never multiplied together (ADR-018)."""
    result = v
    for m in range(k, j):
        state_m = nominal.ensembles[m][0]
        segment = chain.segments[m]
        jacobian = segment.operator.jacobian(state_m, segment.control)
        result = jacobian @ result
    return result


def propagate_vjp(chain: Chain, nominal: Trajectory, k: int, j: int, w: FloatArray) -> FloatArray:
    """``Φ_{j,k}^T w`` as a reverse vector-Jacobian product (Spec §3.5):
    the transpose of a product reverses order, so segments are traversed
    from ``j`` down to ``k``, each contributing its Jacobian's transpose
    (ADR-018)."""
    result = w
    for m in reversed(range(k, j)):
        state_m = nominal.ensembles[m][0]
        segment = chain.segments[m]
        jacobian = segment.operator.jacobian(state_m, segment.control)
        result = jacobian.T @ result
    return result


def _observation_term_action(
    chain: Chain, nominal: Trajectory, k: int, observation: Observation, v: FloatArray
) -> FloatArray:
    """One term's action on a vector: ``Φ_{j,k}^T H_j'^T R_j^{-1} H_j' Φ_{j,k} v``
    (Spec §3.1), computed entirely through JVP/VJP primitives — no matrix
    named ``Φ`` ever appears (ADR-018)."""
    j = observation.time_index
    nominal_state_j = State(nominal.ensembles[j].schema, nominal.ensembles[j][0].values)
    propagated = propagate_jvp(chain, nominal, k, j, v)
    observed = observation.readout.jacobian(nominal_state_j) @ propagated
    weighted = np.linalg.solve(observation.noise_covariance, observed)
    back_through_readout = observation.readout.jacobian(nominal_state_j).T @ weighted
    return propagate_vjp(chain, nominal, k, j, back_through_readout)


@dataclass(frozen=True)
class GramianResult:
    """The observability Gramian at index ``k`` (Spec §3.1), decomposed into
    its per-observation terms — needed for the observed/inferred split
    (Spec §3.3) and for erasure truncation (Spec §3.2)."""

    time_index: int
    total: FloatArray
    terms: dict[str, FloatArray] = field(default_factory=dict)
    """Observation name -> that observation's own ``(n, n)`` contribution to
    :attr:`total`, restricted to observations with ``time_index >= k``
    (Spec §3.1: "the sum runs over ``j ≥ k`` only")."""


def compute_gramian(
    chain: Chain,
    nominal: Trajectory,
    time_index: int,
    observations: Sequence[Observation],
) -> GramianResult:
    """Materialise the observability Gramian (Spec §3.1) at *time_index* and
    every contributing observation's own term (ADR-018: dense at these toy
    state dimensions, built from state-dimension-many JVP/VJP evaluations
    rather than ever forming ``Φ`` as a chained matrix product).
    """
    state_dim = nominal.initial.schema.size
    names = [obs.name for obs in observations]
    if len(names) != len(set(names)):
        raise ValueError("observation names must be unique")

    terms: dict[str, FloatArray] = {}
    for observation in observations:
        if observation.time_index < time_index:
            continue
        term_matrix = np.zeros((state_dim, state_dim))
        for i in range(state_dim):
            basis_vector = np.zeros(state_dim)
            basis_vector[i] = 1.0
            term_matrix[:, i] = _observation_term_action(chain, nominal, time_index, observation, basis_vector)
        terms[observation.name] = term_matrix

    total = np.zeros((state_dim, state_dim))
    for term in terms.values():
        total = total + term
    return GramianResult(time_index, total, terms)


def default_prior_covariance(metric: Metric) -> FloatArray:
    """The default observability prior (Spec §3.1's ``P_k^0``): ``diag(metric.scale ** 2)``
    (ADR-019) — the aleatoric variance already declared by the metric,
    reused rather than inventing a new prior."""
    return np.diag(metric.scale**2)


def posterior_covariance(prior: FloatArray, gramian: FloatArray) -> FloatArray:
    """``P_k = ((P_k^0)^{-1} + G_k)^{-1}`` (Spec §3.1).

    **Proposition 3.1 (Spec §3.1):** under process noise this deterministic
    Gramian is an *upper bound* on achievable information — the true
    posterior covariance is at least this large. Callers MUST NOT quote the
    result as achieved posterior precision (CLAUDE.md §8).
    """
    return np.linalg.inv(np.linalg.inv(prior) + gramian)


def sensitivity_operator(
    chain: Chain, nominal: Trajectory, time_index: int, target_readouts: Sequence[FunctionalReadout]
) -> FloatArray:
    """``S_k = [Dρ^(1)Φ_{N,k}; ...; Dρ^(M)Φ_{N,k}]`` (Spec §3.3): each target
    readout's Jacobian at the terminal state, propagated backward to
    *time_index* by VJP (ADR-018) — the chain rule applied one segment at a
    time, never through a formed ``Φ_{N,k}``.
    """
    terminal_index = len(chain.segments)
    terminal_state = nominal.ensembles[terminal_index][0]
    rows = []
    for readout in target_readouts:
        readout_jacobian = readout.jacobian(terminal_state)
        for row in readout_jacobian:
            rows.append(propagate_vjp(chain, nominal, time_index, terminal_index, row))
    return np.stack(rows, axis=0)


class Triage(str, Enum):
    """The four-way triage of Core §3.8 / Spec §3.3, plus the "observed but
    irrelevant" entry Spec §3.3's table names explicitly."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    DANGEROUS = "dangerous"
    MARGINALISABLE = "marginalisable"
    OBSERVED_BUT_IRRELEVANT = "observed_but_irrelevant"


@dataclass(frozen=True)
class DirectionDiagnostic:
    """Per-eigendirection diagnostics behind one entry of the triage (Spec
    §3.3) — the continuous ``influence`` and ``uncertainty`` scores are kept
    alongside the categorical :attr:`label` (ADR-020), never discarded."""

    eigenvector: FloatArray
    influence: float
    """``v_i^* S_k^* W S_k v_i``: target-variance contribution (Spec §3.3)."""
    uncertainty: float
    """``v_i^* P_k v_i``: residual uncertainty — exactly the eigenvalue of
    ``P_k`` for its own eigenvector."""
    danger_score: float
    """``influence * uncertainty`` (Spec §3.3's boxed ``𝒟_i``)."""
    near_diagonal_share: float | None
    """Fraction of this direction's Gramian quadratic form supplied by
    near-diagonal observations (``time_index`` within the declared window of
    `k`); ``None`` when the direction is unidentifiable or there are no
    near-diagonal observations at all (ADR-020)."""
    label: Triage


@dataclass(frozen=True)
class TriageResult:
    """The complete per-direction triage at one chain index (Spec §3.3),
    with the median thresholds used (ADR-020) kept alongside it."""

    directions: tuple[DirectionDiagnostic, ...]
    """Ordered by :attr:`~DirectionDiagnostic.danger_score`, descending."""
    influence_median: float
    uncertainty_median: float

    def dangerous_set(self) -> tuple[DirectionDiagnostic, ...]:
        """The actionable output (Spec §3.3): influential and unidentifiable
        directions, ranked by danger score — the sensing investment case."""
        return tuple(d for d in self.directions if d.label is Triage.DANGEROUS)

    def inferred_set(self) -> tuple[DirectionDiagnostic, ...]:
        """Directions identifiable only through chain dynamics plus
        downstream measurement (Core §3.8) — what no tabular baseline
        recovers, and reported separately per docs/ROADMAP.md M3."""
        return tuple(d for d in self.directions if d.label is Triage.INFERRED)


def danger_triage(
    chain: Chain,
    nominal: Trajectory,
    time_index: int,
    gramian: GramianResult,
    prior: FloatArray,
    target_readouts: Sequence[FunctionalReadout],
    observations: Sequence[Observation],
    importance_weights: FloatArray | None = None,
    observed_share_threshold: float = 0.5,
    near_diagonal_window: int = 0,
) -> TriageResult:
    """The full danger-score triage at *time_index* (Core §3.8; Spec §3.3):
    eigendecompose the posterior covariance, weight each eigendirection by
    its influence on the declared *target_readouts*, and classify by the
    median-split convention of ADR-020 (docs/DECISIONS.md).

    *near_diagonal_window* operationalises "a near-diagonal term `j ≈ k`"
    (Spec §3.3): observations with ``time_index`` within this many steps of
    *time_index* are "near-diagonal"; the default, 0, is the most literal
    reading (only an observation *at* `k` itself counts). A direction is
    *observed* if the near-diagonal observations together supply more than
    *observed_share_threshold* of its Gramian quadratic form; *inferred* if
    it is identifiable at all but that information accrues only through
    farther, downstream observations — "the chain model, not the
    instrument, is doing the work" (Core §3.8).
    """
    posterior = posterior_covariance(prior, gramian.total)
    sensitivity = sensitivity_operator(chain, nominal, time_index, target_readouts)
    n_outputs = sensitivity.shape[0]
    weights = importance_weights if importance_weights is not None else np.eye(n_outputs)

    eigenvalues, eigenvectors = np.linalg.eigh(posterior)
    n = eigenvectors.shape[1]
    influences = [
        float(eigenvectors[:, i] @ sensitivity.T @ weights @ sensitivity @ eigenvectors[:, i]) for i in range(n)
    ]
    uncertainties = [float(ev) for ev in eigenvalues]

    influence_median = float(np.median(influences))
    uncertainty_median = float(np.median(uncertainties))

    relevant = [o for o in observations if o.time_index >= time_index]
    near_diagonal_names = [o.name for o in relevant if o.time_index <= time_index + near_diagonal_window]
    near_diagonal_term = None
    if near_diagonal_names:
        near_diagonal_term = sum(
            (gramian.terms[name] for name in near_diagonal_names),
            start=np.zeros_like(gramian.total),
        )

    diagnostics = []
    for i in range(n):
        v = eigenvectors[:, i]
        influence = influences[i]
        uncertainty = uncertainties[i]
        identifiable = uncertainty <= uncertainty_median
        influential = influence >= influence_median

        near_diagonal_share = None
        if identifiable and near_diagonal_term is not None:
            total_quad = float(v @ gramian.total @ v)
            if total_quad > 0:
                near_diagonal_share = float(v @ near_diagonal_term @ v) / total_quad

        if identifiable and influential:
            label = (
                Triage.OBSERVED
                if (near_diagonal_share is not None and near_diagonal_share > observed_share_threshold)
                else Triage.INFERRED
            )
        elif identifiable and not influential:
            label = Triage.OBSERVED_BUT_IRRELEVANT
        elif not identifiable and influential:
            label = Triage.DANGEROUS
        else:
            label = Triage.MARGINALISABLE

        diagnostics.append(
            DirectionDiagnostic(v, influence, uncertainty, influence * uncertainty, near_diagonal_share, label)
        )

    diagnostics.sort(key=lambda d: d.danger_score, reverse=True)
    return TriageResult(tuple(diagnostics), influence_median, uncertainty_median)


def value_of_information(
    chain: Chain,
    nominal: Trajectory,
    time_index: int,
    prior: FloatArray,
    gramian: GramianResult,
    candidate: Observation,
    target_readouts: Sequence[FunctionalReadout],
    importance_weights: FloatArray | None = None,
) -> float:
    """``ΔV_c = tr(W S_k (P_k - P_k') S_k^T)`` (Spec §3.4): the expected
    reduction in target variance from adding *candidate* at index ``k``,
    computed by the Woodbury identity so the augmented posterior ``P_k'`` is
    never inverted from scratch — only a ``(candidate observation
    dimension)``-sized system is solved, reusing the already-computed
    ``P_k``.
    """
    posterior = posterior_covariance(prior, gramian.total)
    j = candidate.time_index
    state_dim = posterior.shape[0]
    nominal_state_j = nominal.ensembles[j][0]
    readout_jacobian = candidate.readout.jacobian(nominal_state_j)
    obs_dim = readout_jacobian.shape[0]

    # U = Phi_{j,k}^T H_c'^T, built column by column via VJP (ADR-018): Phi
    # is never formed, only its transpose action on each readout-space basis
    # vector.
    u = np.zeros((state_dim, obs_dim))
    for column in range(obs_dim):
        basis_vector = np.zeros(obs_dim)
        basis_vector[column] = 1.0
        back_through_readout = readout_jacobian.T @ basis_vector
        u[:, column] = propagate_vjp(chain, nominal, time_index, j, back_through_readout)

    sensitivity = sensitivity_operator(chain, nominal, time_index, target_readouts)
    n_outputs = sensitivity.shape[0]
    weights = importance_weights if importance_weights is not None else np.eye(n_outputs)

    posterior_u = posterior @ u
    inner = candidate.noise_covariance + u.T @ posterior_u
    delta_posterior = posterior_u @ np.linalg.solve(inner, posterior_u.T)

    delta_v = np.trace(weights @ sensitivity @ delta_posterior @ sensitivity.T)
    return float(delta_v)


def best_placement(
    chain: Chain,
    nominal: Trajectory,
    time_index: int,
    prior: FloatArray,
    gramian: GramianResult,
    candidates: Sequence[Observation],
    costs: dict[str, float],
    target_readouts: Sequence[FunctionalReadout],
    importance_weights: FloatArray | None = None,
) -> tuple[Observation, dict[str, float]]:
    """Placement maximises ``ΔV_c / cost_c`` over candidate (modality, index)
    pairs (Spec §3.4) — A-optimal *on the readout*, not on the state, since
    :func:`value_of_information` is weighted by ``target_readouts`` and
    :func:`sensitivity_operator` throughout, never by raw state precision.
    """
    ratios: dict[str, float] = {}
    best: Observation | None = None
    best_ratio = -np.inf
    for candidate in candidates:
        delta_v = value_of_information(
            chain, nominal, time_index, prior, gramian, candidate, target_readouts, importance_weights
        )
        ratio = delta_v / costs[candidate.name]
        ratios[candidate.name] = ratio
        if ratio > best_ratio:
            best_ratio = ratio
            best = candidate
    assert best is not None
    return best, ratios


def worst_case_over_window(results: Sequence[TriageResult]) -> TriageResult:
    """Report the worst case over an ensemble of nominal trajectories
    spanning the operating window, not the nominal point (Spec §3.6).

    "Worst" is the trajectory with the largest total danger score
    (``Σ_i 𝒟_i``); ADR-020 explains why that trajectory's whole
    :class:`TriageResult` is returned rather than an elementwise max across
    trajectories' per-direction diagnostics (their eigenbases come from
    different linearisation points and are not directly comparable).
    """
    if not results:
        raise ValueError("worst_case_over_window requires at least one result")

    def _total_danger(result: TriageResult) -> float:
        return sum(d.danger_score for d in result.directions)

    return max(results, key=_total_danger)
