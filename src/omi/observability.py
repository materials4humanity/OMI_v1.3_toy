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
    irrelevant" entry Spec §3.3's table names explicitly, plus
    :attr:`UNRESOLVED` (ADR-061).
    """

    OBSERVED = "observed"
    INFERRED = "inferred"
    DANGEROUS = "dangerous"
    MARGINALISABLE = "marginalisable"
    OBSERVED_BUT_IRRELEVANT = "observed_but_irrelevant"

    UNRESOLVED = "unresolved"
    """The observed/inferred question was asked and **refused** (ADR-061;
    `docs/V1.4-EDITS.md` E-48, E-53).

    Spec §3.3's two stated conditions do not partition the cases: between "a single
    near-diagonal term dominates" and "information accrues only downstream" lies every
    direction whose near-diagonal terms contribute something without any one of them
    dominating. E-53 records that the threshold an implementation must invent is filling a
    hole in the *definition*, and E-48 measured what that costs — on a chain without
    erasure the invented threshold is approached to `1.4×10⁻¹¹`, so the label is decided by
    rounding.

    This value is the honest answer there. It is returned when the dominance ratio sits
    within a declared band of the declared dominance factor, and when neither the
    near-diagonal nor the downstream terms contribute at all. Reporting "the near-diagonal
    and downstream contributions are equal, so neither label is warranted" is a true
    statement about the chain; forcing a label is not, and Core §3.9 with CLAUDE.md §4 both
    say a framework that knows when to refuse is more credible than one that always
    answers.

    **A triage MUST report the abstained fraction** — see
    :attr:`TriageResult.abstained_fraction`. Without that, a domain abstaining on every
    direction satisfies Spec §9.1's OMI-1 item while establishing nothing, which is the
    satisfiable-without-the-property defect this value would otherwise introduce."""


@dataclass(frozen=True)
class ObservedInferredConvention:
    """The declared conventions the observed/inferred split needs (ADR-061; Spec §3.3;
    Core §3.8), each with a required justification.

    Spec §3.3 distinguishes observed from inferred by "which terms of the Gramian sum
    supply the information" and leaves **two** quantities unspecified: how near an index
    must be to count as near-diagonal, and how much one term must exceed the others to
    "dominate". `docs/V1.4-EDITS.md` E-48 measured that the two compound — on this
    repository's contrast chain the same direction at the same index reads *inferred* at a
    window of 0, *observed* at 2, and splits between the labels at 1, where the criterion is
    approached to `1.4×10⁻¹¹`.

    So both are declared here, per domain, with justifications. Declaring one and leaving
    the other free would repair half of a compounding pair and report it as the whole.
    """

    dominance_factor: float
    """`ρ ≥ 1`: how far the largest near-diagonal contribution must exceed the largest
    downstream one before the direction counts as **observed**.

    A ratio between two comparable quantities rather than a fraction of a total, which is
    why it degrades gracefully where ADR-020's share did not: two equal contributions give
    a ratio of exactly `1`, which fails any `ρ > 1` cleanly and reports the tie instead of
    resolving it by rounding (ADR-061)."""

    abstention_band: float
    """Half-width on the ratio within which the split is **refused** rather than decided.

    The half of the fix that matters most (ADR-061): it converts an arbitrary label into an
    explicit abstention, which is Core §3.9's refusal discipline applied to the framework's
    own diagnostic."""

    near_diagonal_window: int
    """How many indices past `k` still count as "`j ≈ k`" (Spec §3.3's own notation).

    Not eliminated by the ratio form and measured not to be: the window still spans the
    answer on contrast, so it is declared rather than defaulted (ADR-061)."""

    justification: str
    """Why these three values, for this domain — required and non-empty.

    A free-text field **checks nothing by itself**, and E-17 and E-31 both warn about
    good-faith strings that satisfy a requirement without establishing its property. What it
    buys is that the choice becomes visible to a reader and comparable across domains, which
    is weaker than a check and stronger than the silent default that produced E-48."""

    def __post_init__(self) -> None:
        if self.dominance_factor < 1.0:
            raise ValueError(
                f"dominance_factor must be at least 1.0, got {self.dominance_factor}: a value "
                "below 1 would call a direction observed while a downstream term contributes "
                "more than the near-diagonal one, which inverts the distinction"
            )
        if self.abstention_band < 0.0:
            raise ValueError(f"abstention_band must be non-negative, got {self.abstention_band}")
        if self.near_diagonal_window < 0:
            raise ValueError(f"near_diagonal_window must be non-negative, got {self.near_diagonal_window}")
        if not self.justification.strip():
            raise ValueError(
                "an ObservedInferredConvention must justify its values: E-48's finding is that "
                "two silent conventions compounded into a label decided at machine precision, "
                "and an undeclared choice no reader can see is how that happened"
            )


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
    near-diagonal observations at all (ADR-020).

    **Retained and no longer the criterion** (ADR-061). E-48 measured that a threshold on
    this quantity is decided by rounding on a chain without erasure, and E-53 that it
    replaces both of Spec §3.3's stated conditions. It is kept because it is a legible
    summary a reader may want, and because dropping a reported quantity would break the
    audit trail of every result that quoted it; :attr:`dominance_ratio` is what the label
    is computed from."""

    dominance_ratio: float | None
    """`max_{k ≤ j ≤ k+w} q_j / max_{j > k+w} q_j` — the criterion (ADR-061; Spec §3.3's
    own words, "a single near-diagonal term dominates", made exact).

    ``inf`` when nothing downstream contributes, which is unambiguously observed. ``None``
    when the direction is unidentifiable, or when neither side contributes at the declared
    tolerance — the case that returns :attr:`Triage.UNRESOLVED` rather than a label.

    A ratio of comparables rather than a fraction of a total, which is the whole reason it
    is the criterion: on this repository's contrast chain it takes the single value `1.0` at
    every index where the share walked `1/12, 1/10, 1/8, 1/6, 1/4, 1/2` and landed on the
    threshold."""

    label: Triage


@dataclass(frozen=True)
class TriageResult:
    """The complete per-direction triage at one chain index (Spec §3.3),
    with the median thresholds used (ADR-020) and the declared observed/inferred
    convention (ADR-061) kept alongside it."""

    directions: tuple[DirectionDiagnostic, ...]
    """Ordered by :attr:`~DirectionDiagnostic.danger_score`, descending."""
    influence_median: float
    uncertainty_median: float
    convention: ObservedInferredConvention
    """The declared dominance factor, band and window this triage used (ADR-061).

    Carried on the result rather than left at the call site, by the same discipline
    CLAUDE.md invariant 1 imposes on metric-dependent quantities: a classification whose
    value depends on a declared choice travels with that choice."""

    @property
    def abstained_fraction(self) -> float:
        """Fraction of directions returned as :attr:`Triage.UNRESOLVED` (ADR-061; Spec
        §9.1's OMI-1 item as this repository proposes extending it).

        **A required output, not a convenience.** Abstention makes an arbitrary label
        honest; without this number it also makes the conformance item satisfiable by
        declining to answer — a triage abstaining on every direction would report a triage
        and establish nothing, which is the shape §4 of `docs/V1.4-EDITS.md` documents nine
        times. Reporting the fraction turns abstention into a measured property of the chain.
        """
        if not self.directions:
            return 0.0
        return sum(1 for d in self.directions if d.label is Triage.UNRESOLVED) / len(self.directions)

    def dangerous_set(self) -> tuple[DirectionDiagnostic, ...]:
        """The actionable output (Spec §3.3): influential and unidentifiable
        directions, ranked by danger score — the sensing investment case."""
        return tuple(d for d in self.directions if d.label is Triage.DANGEROUS)

    def inferred_set(self) -> tuple[DirectionDiagnostic, ...]:
        """Directions identifiable only through chain dynamics plus
        downstream measurement (Core §3.8) — what no tabular baseline
        recovers, and reported separately per docs/ROADMAP.md M3.

        **Read this alongside :meth:`unresolved_set` and never as a count on its own**
        (ADR-061). Core §3.8 states the framework's differentiator against a tabular
        baseline as the *membership* of this set; E-53's measurement is that the membership
        depends on a declared dominance factor, so the citable quantity is each direction's
        :attr:`~DirectionDiagnostic.dominance_ratio`, not the size of this tuple.
        """
        return tuple(d for d in self.directions if d.label is Triage.INFERRED)

    def unresolved_set(self) -> tuple[DirectionDiagnostic, ...]:
        """Directions on which the observed/inferred question was refused (Spec §3.3's
        distinction, refused rather than forced; Core §3.9's refusal discipline; ADR-061).

        Non-empty is a finding about the chain rather than about the implementation: it says
        the near-diagonal and downstream terms contribute comparably, so *which terms supply
        the information* has no answer at the declared dominance factor.
        """
        return tuple(d for d in self.directions if d.label is Triage.UNRESOLVED)


DEFAULT_CONVENTION = ObservedInferredConvention(
    dominance_factor=1.5,
    abstention_band=0.25,
    near_diagonal_window=0,
    justification=(
        "Framework default, used only where a caller declares nothing (ADR-061). rho=1.5 "
        "reads 'dominates' as a half-again margin rather than as bare inequality, so a "
        "direction whose near-diagonal and downstream maxima are comparable is not called "
        "observed; the band of 0.25 refuses the label across [1.25, 1.75]. The window is 0, "
        "the most literal reading of Spec 3.3's 'j ~ k' -- only an observation AT k counts. "
        "A DOMAIN SHOULD DECLARE ITS OWN: E-48 measured that these two conventions compound, "
        "and a framework default no domain had to defend is how they became invisible."
    ),
)
"""The convention used when a caller declares none (ADR-061).

Kept as a **default rather than a required argument** for one reason and it is not
convenience: making the argument required would change every existing call site at once, and
the audit-preservation gate (ADR-042) exists precisely so that a change to `src/omi/` can be
shown not to have moved any previously-reported number. A default that reproduces the most
literal reading of Spec §3.3 keeps that check meaningful. The justification string says
plainly that a domain should declare its own."""

_RATIO_TOLERANCE = 1.0e-12
"""Below this a Gramian quadratic-form contribution counts as zero (ADR-061).

Stands in for ADR-017's declared erasure rank tolerance — the same question, asked of the
same kind of quantity — rather than introducing a second numerical convention."""


def danger_triage(
    chain: Chain,
    nominal: Trajectory,
    time_index: int,
    gramian: GramianResult,
    prior: FloatArray,
    target_readouts: Sequence[FunctionalReadout],
    observations: Sequence[Observation],
    importance_weights: FloatArray | None = None,
    convention: ObservedInferredConvention = DEFAULT_CONVENTION,
) -> TriageResult:
    """The full danger-score triage at *time_index* (Core §3.8; Spec §3.3):
    eigendecompose the posterior covariance, weight each eigendirection by
    its influence on the declared *target_readouts*, and classify by the
    median-split convention of ADR-020 (docs/DECISIONS.md) for the
    identifiability axis and by *convention* for the observed/inferred axis.

    **The observed/inferred criterion is ADR-061's, not ADR-020's**, and the change is a
    correction rather than a refinement. ADR-020 asked whether the *sum* of near-diagonal
    terms exceeded half the *total*; Spec §3.3 asks whether "a single near-diagonal term
    dominates", and `docs/V1.4-EDITS.md` E-53 records that the two are different questions
    while E-48 measured what the substitution cost — on a chain without erasure the share
    lands exactly on its threshold and the label is decided by rounding. So:

    - **observed** — `max_{k ≤ j ≤ k+w} q_j > ρ · max_{j > k+w} q_j`;
    - **inferred** — the near-diagonal contribution vanishes at the declared tolerance while
      the direction is identifiable from the total, i.e. Spec's *"only through Σ_{j>k}"*;
    - **unresolved** — the ratio sits within the declared band of `ρ`, or neither side
      contributes. Refused rather than assigned, and counted in
      :attr:`TriageResult.abstained_fraction`.

    `w`, `ρ`, the band and the tolerance all travel on the returned
    :class:`TriageResult`, because a classification whose value depends on a declared choice
    must carry it (CLAUDE.md invariant 1).
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

    window = convention.near_diagonal_window
    relevant = [o for o in observations if o.time_index >= time_index]
    near_diagonal_names = [o.name for o in relevant if o.time_index <= time_index + window]
    downstream_names = [o.name for o in relevant if o.time_index > time_index + window]
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

        dominance_ratio: float | None = None
        if identifiable:
            near_max = max(
                (float(v @ gramian.terms[name] @ v) for name in near_diagonal_names), default=0.0
            )
            down_max = max(
                (float(v @ gramian.terms[name] @ v) for name in downstream_names), default=0.0
            )
            if down_max > _RATIO_TOLERANCE:
                dominance_ratio = near_max / down_max
            elif near_max > _RATIO_TOLERANCE:
                dominance_ratio = float("inf")

        if identifiable and influential:
            label = _observed_inferred_label(dominance_ratio, convention)
        elif identifiable and not influential:
            label = Triage.OBSERVED_BUT_IRRELEVANT
        elif not identifiable and influential:
            label = Triage.DANGEROUS
        else:
            label = Triage.MARGINALISABLE

        diagnostics.append(
            DirectionDiagnostic(
                v,
                influence,
                uncertainty,
                influence * uncertainty,
                near_diagonal_share,
                dominance_ratio,
                label,
            )
        )

    diagnostics.sort(key=lambda d: d.danger_score, reverse=True)
    return TriageResult(tuple(diagnostics), influence_median, uncertainty_median, convention)


def _observed_inferred_label(
    dominance_ratio: float | None, convention: ObservedInferredConvention
) -> Triage:
    """ADR-061's criterion, in one place so the three outcomes are visible together.

    ``None`` means neither side contributes at the declared tolerance: the direction was
    classed identifiable by the *uncertainty median* (ADR-020) while carrying no Gramian
    information at all, which is E-48's first-half degeneracy surfacing. Spec §3.3's
    *"inferred"* requires the direction to be identifiable **from the total**, which it is
    not, so the honest answer is a refusal rather than a label — and it is counted, so the
    refusal cannot pass unnoticed.
    """
    if dominance_ratio is None:
        return Triage.UNRESOLVED
    if np.isinf(dominance_ratio):
        return Triage.OBSERVED
    if abs(dominance_ratio - convention.dominance_factor) <= convention.abstention_band:
        return Triage.UNRESOLVED
    if dominance_ratio > convention.dominance_factor:
        return Triage.OBSERVED
    return Triage.INFERRED


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
