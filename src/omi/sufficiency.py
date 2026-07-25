"""Sufficiency: the three-term deficit decomposition, probe sets, the
augmentation loop, and the blocking-term trichotomy.

Cites Core §2.1 (Axiom S; the sufficiency test), Core §2.2 (state selection
as a measurable bias-variance trade-off — PASS-B in Core, but its
estimators are SPEC in Spec §1, per COVERAGE.md row C-2.2), and Spec §1 in
full. ADR-021, ADR-022 and ADR-023 (docs/DECISIONS.md) fix the structural
choices Spec §1 leaves open: how matched-pair campaign data is represented,
the probe-set decomposition resolving OQ-1, and the augmentation loop's
candidate representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

import numpy as np
from scipy import stats

from omi.observability import TriageResult
from omi.state import FloatArray, Slot, StateSchema


@dataclass(frozen=True)
class DeficitResult:
    """The three-term decomposition of a sufficiency deficit (Spec §1.2).

    Cites Spec §1.2's requirement: "An implementation reporting a
    sufficiency deficit MUST report all three terms separately. A raw
    response gap is not a sufficiency deficit." ``raw_gap_squared`` is kept
    here for exactly that transparency requirement — it is never returned by
    any function on its own (ADR-021, docs/DECISIONS.md).
    """

    deficit_squared: float
    """``δ²(𝒮)``, clamped at zero (Spec §1.2's boxed formula)."""
    raw_gap_squared: float
    """``E[(ρ_A-ρ_B)²]`` — the naive statistic, reported only alongside its
    corrections, never standalone (ADR-021)."""
    repeat_variance_term: float
    """``2σ²_rep`` — measurement/aleatoric noise, doubled because the
    difference of two independent draws has twice the variance of one."""
    mismatch_correction_term: float
    """``Σ_j (∂ρ/∂s_j)² E[(s_{A,j}-s_{B,j})²]`` — the imperfect-matching
    correction: matching is performed on measurable proxies, never on the
    state itself."""


def sufficiency_deficit(
    response_a: FloatArray,
    response_b: FloatArray,
    matched_component_diffs: FloatArray,
    response_jacobian: FloatArray,
    repeat_variance: float,
) -> DeficitResult:
    """Spec §1.2's boxed deficit estimator, computed from already-collected
    matched-pair campaign data (ADR-021): *response_a*/*response_b* are
    per-pair terminal responses; *matched_component_diffs* is
    ``(n_pairs, n_matched)``, the per-pair difference in each matched
    component; *response_jacobian* is ``∂ρ/∂s_j`` for each matched component
    (obtain via :func:`omi.observability.sensitivity_operator` — Spec §1
    "depends on §3"); *repeat_variance* is ``σ²_rep``, estimated separately
    from repeated identical-condition trials.
    """
    raw_gap_squared = float(np.mean((response_a - response_b) ** 2))
    repeat_term = 2.0 * repeat_variance
    mean_squared_diffs = np.mean(matched_component_diffs**2, axis=0)
    mismatch_term = float(np.sum(response_jacobian**2 * mean_squared_diffs))
    deficit_squared = max(0.0, raw_gap_squared - repeat_term - mismatch_term)
    return DeficitResult(deficit_squared, raw_gap_squared, repeat_term, mismatch_term)


def variance_term(triage: TriageResult) -> float:
    """``Var_est(𝒮) = tr(W S_k P_k S_k^*) = Σ_i 𝒟_i`` (Spec §1.3): exactly
    the sum of danger scores from Spec §3.3 — this is why Spec §1 depends on
    §3. No separate computation; this is a one-line reuse of the M3 triage.
    """
    return sum(d.danger_score for d in triage.directions)


def learning_error() -> float:
    """``Err_learn(𝒮)`` (Spec §1.4): measured from a learned model's
    rollout-length curve at matched data budget.

    Every module through M7 (ADR-001, docs/DECISIONS.md) uses exact
    analytic operators, which are not fit to any data budget and therefore
    have no learning error by construction — this is the *correct* value
    for this instantiation, ``0.0``, not a placeholder standing in for a
    future estimate. Replaced by a genuine measurement once M8 introduces
    learned operators behind the same protocol.
    """
    return 0.0


class BlockingTerm(str, Enum):
    """Spec §1.7's diagnostic trichotomy: which term blocks the augmentation
    loop when it terminates with a residual deficit. Only :attr:`BIAS` (with
    no candidate available) is a refutation (Core §6.1, criterion 1) —
    conflating the three "is how a framework acquires an undeserved
    reputation for failure" (Spec §1.7)."""

    VARIANCE = "variance"
    """The needed component exists but cannot be identified — buy sensing
    (Spec §3.4)."""
    LEARNING = "learning"
    """The state is right, the operator is undertrained — buy data or
    simulation."""
    BIAS = "bias"
    """No bounded augmentation removes the deficit — a falsification event
    (Core §6.1, criterion 1)."""


def diagnose_blocking_term(
    delta_bias_squared: float,
    delta_variance_est: float,
    delta_learning_error: float,
    has_candidate_in_pool: bool,
) -> BlockingTerm:
    """Spec §1.7: identify which term blocks when no candidate is accepted.

    Mirrors the augmentation loop's own acceptance rule (Spec §1.5 step 6:
    accept iff ``Δ(Bias²) > ΔVar_est + ΔErr_learn``) run in reverse — an
    implementation MUST report which term blocks before declaring any of
    them (Spec §1.7).
    """
    if not has_candidate_in_pool:
        return BlockingTerm.BIAS
    # A candidate exists but failed step 6's test, i.e.
    # Delta(Bias^2) <= DeltaVar_est + DeltaErr_learn: attribute the block to
    # whichever cost term dominates the rejection.
    if delta_variance_est >= delta_learning_error:
        return BlockingTerm.VARIANCE
    return BlockingTerm.LEARNING


@dataclass(frozen=True)
class ProbeSet:
    """A forward/reversed probe pair's responses for one matched-history
    pair (Spec §1.6), decomposed into symmetric and antisymmetric parts —
    ADR-022's resolution of OQ-1 (docs/COVERAGE.md Part IV): a directional
    (kinematic) hidden variable can diverge under *both* probes equally in
    magnitude, so "which single probe diverges" does not reliably identify
    it. The decomposition does: a purely directional effect lives entirely
    in :attr:`antisymmetric_gap`, with :attr:`symmetric_gap` near zero.
    """

    forward_a: float
    forward_b: float
    reversed_a: float
    reversed_b: float

    @property
    def symmetric_gap(self) -> float:
        """Spec §1.6 / ADR-022: the matched-pair gap in the probes'
        *average* response — insensitive to a purely directional hidden
        variable."""
        symmetric_a = (self.forward_a + self.reversed_a) / 2.0
        symmetric_b = (self.forward_b + self.reversed_b) / 2.0
        return symmetric_a - symmetric_b

    @property
    def antisymmetric_gap(self) -> float:
        """Spec §1.6 / ADR-022: the matched-pair gap in the probes'
        *half-difference* response — exactly where a purely directional
        hidden variable's effect lives."""
        antisymmetric_a = (self.forward_a - self.reversed_a) / 2.0
        antisymmetric_b = (self.forward_b - self.reversed_b) / 2.0
        return antisymmetric_a - antisymmetric_b

    @property
    def signature(self) -> tuple[float, float]:
        """The ``(symmetric_gap, antisymmetric_gap)`` pair used to fingerprint
        which candidate component is missing (Spec §1.6)."""
        return (self.symmetric_gap, self.antisymmetric_gap)


@dataclass(frozen=True)
class AugmentationStep:
    """One step of the augmentation loop, kept for auditability — Spec §1.8:
    "The three terms MUST be reported separately at each accepted
    augmentation, so the trajectory of the loop is auditable."
    """

    schema: StateSchema
    deficit: DeficitResult
    variance_est: float
    accepted_candidate: tuple[Slot, str] | None
    """The ``(slot, name)`` accepted this step, or ``None`` for the loop's
    final (stopping) step."""


@dataclass(frozen=True)
class AugmentationResult:
    """The outcome of :func:`augmentation_loop` (Spec §1.5)."""

    final_schema: StateSchema
    steps: tuple[AugmentationStep, ...]
    stopped_reason: str
    """``"sufficient_at_tolerance"`` or ``"candidates_exhausted"``."""
    blocking_term: BlockingTerm | None
    """Set only when ``stopped_reason == "candidates_exhausted"`` (Spec
    §1.7) — ``None`` when the loop stopped because it reached sufficiency."""


def augmentation_loop(
    initial_schema: StateSchema,
    candidate_pool: Sequence[tuple[Slot, str, int]],
    sufficiency_test: Callable[[StateSchema], DeficitResult],
    variance_delta: Callable[[StateSchema], float],
    tolerance_bias_squared: float,
) -> AugmentationResult:
    """Spec §1.5's augmentation loop, implemented literally.

    *candidate_pool* is tried in the given order — the caller supplies it
    already ordered by divergence-fingerprint priority (Spec §1.6); this
    function does not read fingerprints itself, only accepts or rejects the
    nominated candidate per Spec §1.5 step 6. ``Err_learn`` is
    :func:`learning_error`, exactly zero for analytic operators (ADR-023).
    """
    schema = initial_schema
    remaining = list(candidate_pool)
    steps: list[AugmentationStep] = []
    current_variance = variance_delta(schema)
    current_deficit = sufficiency_test(schema)

    while True:
        if current_deficit.deficit_squared <= tolerance_bias_squared:
            steps.append(AugmentationStep(schema, current_deficit, current_variance, None))
            return AugmentationResult(schema, tuple(steps), "sufficient_at_tolerance", None)

        accepted: tuple[Slot, str, int] | None = None
        best_shortfall = np.inf
        best_deltas = (0.0, 0.0)
        for candidate in remaining:
            slot, name, dim = candidate
            candidate_schema = StateSchema(schema.components + ((slot, name, dim),))
            candidate_deficit = sufficiency_test(candidate_schema)
            candidate_variance = variance_delta(candidate_schema)

            delta_bias_squared = current_deficit.deficit_squared - candidate_deficit.deficit_squared
            delta_variance = candidate_variance - current_variance
            delta_learning = learning_error() - learning_error()

            if delta_bias_squared > delta_variance + delta_learning:
                accepted = candidate
                steps.append(
                    AugmentationStep(candidate_schema, candidate_deficit, candidate_variance, (slot, name))
                )
                schema = candidate_schema
                current_variance = candidate_variance
                current_deficit = candidate_deficit
                remaining.remove(candidate)
                break

            shortfall = (delta_variance + delta_learning) - delta_bias_squared
            if shortfall < best_shortfall:
                best_shortfall = shortfall
                best_deltas = (delta_variance, delta_learning)

        if accepted is None:
            has_candidate = len(remaining) > 0
            blocking = diagnose_blocking_term(
                current_deficit.deficit_squared, best_deltas[0], best_deltas[1], has_candidate
            )
            steps.append(AugmentationStep(schema, current_deficit, current_variance, None))
            return AugmentationResult(schema, tuple(steps), "candidates_exhausted", blocking)


def required_sample_size(alpha: float, beta: float, sigma: float, delta: float) -> float:
    """Spec §8's power-analysis formula: ``n ≈ 2(z_{1-α/2}+z_{1-β})²(σ/δ)²``
    per arm.

    Formula only, no worked values (docs/ROADMAP.md M4: "Refuse: campaign
    power analysis worked values (S-8, PASS-C) — formula only, no numbers").
    Every parameter is required with no default — a default for *alpha* or
    *beta* (e.g. the common 0.05/0.2 convention) would itself be a "worked
    value" this module does not supply.
    """
    z_alpha = float(stats.norm.ppf(1.0 - alpha / 2.0))
    z_beta = float(stats.norm.ppf(1.0 - beta))
    return 2.0 * (z_alpha + z_beta) ** 2 * (sigma / delta) ** 2


def discriminating(candidate_signatures: dict[str, tuple[float, float]], tolerance: float) -> bool:
    """Spec §1.6's design requirement: a probe set "MUST be chosen to
    discriminate between candidate components, not merely to detect
    divergence." Returns ``False`` if any two named candidates'
    ``(symmetric_gap, antisymmetric_gap)`` signatures are indistinguishable
    at *tolerance* — i.e. the probe set can tell *that* something diverges
    but not *which* candidate is responsible.
    """
    names = list(candidate_signatures.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = np.array(candidate_signatures[names[i]])
            b = np.array(candidate_signatures[names[j]])
            if np.linalg.norm(a - b) < tolerance:
                return False
    return True
