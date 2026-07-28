"""Inverse design in practice: reachability certificates, apparatus
parameterisation, and the decision layer.

Cites Core §5 (inverse design as constrained optimal control; the output
contract "route, or certificate of non-reachability plus nearest reachable
state") and Spec §7 in full: §7.0 the `ℳ_real`/`ℳ_reach` distinction, §7.1
reachability certificates, §7.2 apparatus parameterisation, §7.3 the
decision layer. ADR-031/032/033 (docs/DECISIONS.md) fix what Spec leaves
open: `Φ` restricted to linear functionals with an exact halfspace
projection for the nearest reachable state; apparatus parameterisation as a
structural wrapper no `Control` can bypass; and the decision layer's
probability-of-conformance/CVaR formulas plus OQ-4's ordered three-way
infeasibility diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

import numpy as np
from scipy import stats

from omi.operators import Control
from omi.state import FloatArray, State, StateSchema


@dataclass(frozen=True)
class ReachabilityCertificate:
    """A linear reachability certificate `Φ(s) = w · s` (Core §5; Spec
    §7.1; ADR-031): a functional with a provable per-step bound, built from
    a declared invariant (a conservation balance, a monotone accumulation,
    an equilibrium-limited fraction — Spec §7.1's own candidate list, all
    linear in the flat state vector)."""

    weight: FloatArray
    schema: StateSchema

    def phi(self, state: State) -> float:
        """`Φ(s) = w · s` (Spec §7.1)."""
        return float(self.weight @ state.values)


def achievable_bound(phi_initial: float, max_increments: Sequence[float]) -> float:
    """`Φ(s_0) + Σ_k c_max_k` (Spec §7.1's boxed inequality
    `Φ(s_{k+1}) ≤ Φ(s_k) + c(u_k)`, accumulated over every admissible
    control's worst case): the highest value `Φ` can provably reach after
    the given per-step worst-case increments — a domain-declared input
    (ADR-031), not derived, since Spec gives no formula for `sup_u c(u)`.
    """
    return phi_initial + float(sum(max_increments))


def is_provably_unreachable(
    certificate: ReachabilityCertificate,
    initial_state: State,
    max_increments: Sequence[float],
    target_state: State,
) -> bool:
    """Core §5's output contract, the non-reachability half: `True` when
    *target_state* exceeds the accumulated bound and is therefore provably
    unreachable (Spec §7.1) — never a claim of reachability when `False`,
    only the absence of this particular proof (the certificate gives
    necessary, not sufficient, conditions, per Spec §7.1's own hierarchy).
    """
    bound = achievable_bound(certificate.phi(initial_state), max_increments)
    return certificate.phi(target_state) > bound


def nearest_reachable_state(
    certificate: ReachabilityCertificate,
    initial_state: State,
    max_increments: Sequence[float],
    target_state: State,
) -> State:
    """Core §5's output contract, the nearest-reachable-state half (Spec
    §7.1): the Euclidean-nearest point to *target_state* on the halfspace
    `{s : w·s ≤ bound}` — exact, since ADR-031 restricts `Φ` to a linear
    functional. Returns *target_state* unchanged when it is already
    reachable.
    """
    bound = achievable_bound(certificate.phi(initial_state), max_increments)
    phi_target = certificate.phi(target_state)
    if phi_target <= bound:
        return target_state
    w = certificate.weight
    excess = phi_target - bound
    projected = target_state.values - (excess / float(w @ w)) * w
    return State(target_state.schema, projected)


@dataclass(frozen=True)
class ApparatusParameterization:
    """Spec §7.2's requirement made structural (ADR-032): inverse design is
    parameterised in apparatus settings, never desired driving paths.
    `to_control` is the *only* route from an apparatus-parameter array to a
    `Control` anywhere in this module — nothing here accepts a `Control`
    as a search variable.
    """

    to_control: Callable[[FloatArray], Control]
    parameter_dim: int
    bounds: tuple[tuple[float, float], ...]
    """Per-parameter `(low, high)` admissible range (`𝒰_adm`, Spec §7.2's
    simplest non-trivial case — a box, not the fully coupled constraint
    manifold Spec's own text leaves `[Pass C]`)."""

    def __post_init__(self) -> None:
        if len(self.bounds) != self.parameter_dim:
            raise ValueError("bounds must have one (low, high) pair per apparatus parameter")

    def sample_admissible(self, n: int, rng: np.random.Generator) -> FloatArray:
        """Uniformly sample *n* admissible apparatus-parameter vectors
        (Spec §7.0's `ℳ_reach`: states attainable by forward-sampling the
        evolution graph over `𝒰_adm`)."""
        low = np.array([b[0] for b in self.bounds])
        high = np.array([b[1] for b in self.bounds])
        result: FloatArray = low + (high - low) * rng.uniform(0.0, 1.0, size=(n, self.parameter_dim))
        return result


def gradient_control_search(
    forward: Callable[[FloatArray], float],
    forward_grad: Callable[[FloatArray], FloatArray],
    target: float,
    apparatus: ApparatusParameterization,
    initial_guess: FloatArray,
    n_steps: int = 200,
    learning_rate: float = 0.05,
) -> FloatArray:
    """Projected gradient descent on `(forward(u) - target)**2` over
    `𝒰_adm`'s box (`apparatus.bounds`, Spec §7.2/ADR-032) -- Core §5's
    control inverse ("target response → driving programme") treated as the
    optimal-control problem it names, searched directly rather than by
    forward-sampling (`sample_admissible`, above) or a certificate
    (`ReachabilityCertificate`, above).

    New in this repository (ADR-040): no gradient-based control search
    existed anywhere in this module before this function -- confirmed by
    grep before writing it. This is therefore new machinery connected to
    `constraints.py`'s exact-gradient reparameterisations at the call site
    (via *forward_grad*), not a rewiring of something that was already
    here.

    Clips the iterate back into `𝒰_adm`'s box after every step (making this
    projected, not unconstrained, gradient descent). Does *not* itself
    check the trust region `𝒰_trust` (Core §5) -- callers compare the
    returned point against their own declared trust region and report
    accordingly, mirroring Spec §7.3's own ordered-diagnostic discipline
    (`diagnose_infeasibility`, ADR-033): trust region is a separate,
    first-class check, not something a search function silently folds in.
    """
    low = np.array([b[0] for b in apparatus.bounds])
    high = np.array([b[1] for b in apparatus.bounds])
    u = np.clip(np.asarray(initial_guess, dtype=float), low, high)
    for _ in range(n_steps):
        residual = forward(u) - target
        grad = 2.0 * residual * forward_grad(u)
        u = u - learning_rate * grad
        u = np.clip(u, low, high)
    return u


def probability_of_conformance(predictive_samples: FloatArray, lower: float, upper: float) -> float:
    """Spec §7.3: "optimise probability of conformance against
    specification windows, not expected value" — the empirical fraction of
    a candidate's predictive ensemble landing inside `[lower, upper]`.
    """
    return float(np.mean((predictive_samples >= lower) & (predictive_samples <= upper)))


def cvar(losses: FloatArray, alpha: float) -> float:
    """Conditional Value at Risk (Rockafellar & Uryasev 2000; Spec §7.3:
    "connect CVaR to the conformance and defect-rate language"): the mean
    of the worst `alpha`-fraction tail of *losses* (higher `losses` values
    are worse). A caller whose quantity is "worse when lower" negates it
    first, the standard convention.
    """
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    threshold = np.quantile(losses, 1.0 - alpha)
    tail = losses[losses >= threshold]
    return float(np.mean(tail))


def asymmetric_cost(value: FloatArray, target: float, cost_below: float, cost_above: float) -> FloatArray:
    """A piecewise-linear cost, asymmetric by construction (Spec §7.3:
    "carry asymmetric costs — field failure, downgrade, rework, and re-run
    differ by orders of magnitude"): `cost_below * max(target - value, 0) +
    cost_above * max(value - target, 0)`.
    """
    diff = value - target
    result: FloatArray = np.where(diff < 0.0, cost_below * (-diff), cost_above * diff)
    return result


def decision_sensitive_threshold(
    standard_error: float, minimum_effect: float, cost_false_alarm: float, cost_miss: float
) -> float:
    """Sets a falsification threshold "derived from decision sensitivity"
    (Spec §9.4, filling Core §6.1's `[Pass D]` gap, ADR-041 docs/DECISIONS.md)
    rather than by convention: the Bayes-optimal decision boundary between
    "the criterion's residual is noise" (`N(0, standard_error**2)`) and "the
    residual reflects a real effect of at least *minimum_effect*"
    (`N(minimum_effect, standard_error**2)`), under asymmetric
    misclassification costs (Spec §7.3: "carry asymmetric costs... differ by
    orders of magnitude") -- the same likelihood-ratio-test-with-costs result
    used throughout classical detection theory for two equal-variance
    Gaussians:

    `τ = minimum_effect / 2 + (standard_error**2 / minimum_effect) *
    ln(cost_false_alarm / cost_miss)`

    *standard_error* is the criterion's residual estimator's own sampling
    variability at the declared campaign size (not a tolerance -- an
    empirical fact about the estimator, e.g. from repeated-campaign or
    bootstrap variation). *minimum_effect* is the smallest true deviation
    from "the criterion holds" an application declares worth catching --
    like `𝒰_adm`'s numeric bound (E-27, docs/V1.4-EDITS.md), this is supplied
    by the experimenter, not derived from Core or Spec. *cost_false_alarm*
    and *cost_miss* are the declared costs (Spec §7.3's `asymmetric_cost`
    inputs, in the same units) of wrongly flagging a passing criterion and
    of wrongly clearing a genuinely failing one, respectively. Raising the
    cost ratio `cost_false_alarm / cost_miss` raises τ (more tolerant of the
    residual, since a false alarm is now relatively more expensive);
    shrinking *minimum_effect* toward *standard_error* makes τ increasingly
    sensitive to the cost ratio, since the two classes are no longer easily
    separable by the estimator's own precision -- this sensitivity is the
    reportable output Spec §9.4 asks for, not merely the number itself.
    """
    if minimum_effect <= 0.0:
        raise ValueError("minimum_effect must be positive")
    if cost_false_alarm <= 0.0 or cost_miss <= 0.0:
        raise ValueError("costs must be positive")
    return minimum_effect / 2.0 + (standard_error**2 / minimum_effect) * float(
        np.log(cost_false_alarm / cost_miss)
    )


@dataclass(frozen=True)
class Candidate:
    """One apparatus-parameter candidate and its predictive ensemble over
    the target readout (Spec §7.3's decision layer input)."""

    parameters: FloatArray
    predictive_samples: FloatArray


@dataclass(frozen=True)
class DecisionResult:
    """The decision layer's output (Spec §7.3): the selected candidate,
    alongside every candidate's probability of conformance — never the
    single winner without the comparison that produced it (CLAUDE.md §8)."""

    best: Candidate
    probabilities_of_conformance: tuple[float, ...]


def select_best_candidate(candidates: Sequence[Candidate], lower: float, upper: float) -> DecisionResult:
    """Spec §7.3: select within Core §5's degenerate solution set by
    maximising probability of conformance against the specification
    window `[lower, upper]`, not expected value.
    """
    if not candidates:
        raise ValueError("select_best_candidate requires at least one candidate")
    probabilities = tuple(probability_of_conformance(c.predictive_samples, lower, upper) for c in candidates)
    best_index = int(np.argmax(probabilities))
    return DecisionResult(candidates[best_index], probabilities)


class BindingTerm(str, Enum):
    """OQ-4's answer (Spec §7.3; docs/DECISIONS.md Open Questions;
    ADR-033): which term makes a feasible set empty."""

    TRUST_REGION = "trust_region"
    CONTROL = "control"
    ALEATORIC = "aleatoric"
    NONE = "none"
    """The specification is feasible; no term is binding."""


def diagnose_infeasibility(
    spec_window: tuple[float, float],
    trust_region: tuple[float, float],
    achievable_mean_range: tuple[float, float],
    aleatoric_std: float,
    coverage_fraction: float = 0.997,
) -> BindingTerm:
    """Spec §7.3's decision layer, applied to OQ-4 (docs/COVERAGE.md Part
    IV; ADR-033): given a specification
    window, the surrogate's declared trust region, the range of achievable
    *noise-free* mean responses over `𝒰_adm` within that trust region, and
    the aleatoric standard deviation, identify which single term blocks
    feasibility — checked in a fixed order (ADR-033): trust region, then
    control/`𝒰_adm`, then aleatoric spread at the declared *coverage_fraction*
    (default 99.7%, a "±3σ"-style convention, never 100% since no
    unbounded-support noise distribution can satisfy that).
    """
    lower, upper = spec_window
    trust_lower, trust_upper = trust_region
    overlap_lower = max(lower, trust_lower)
    overlap_upper = min(upper, trust_upper)
    if overlap_lower > overlap_upper:
        return BindingTerm.TRUST_REGION

    mean_lower, mean_upper = achievable_mean_range
    effective_lower = max(mean_lower, trust_lower)
    effective_upper = min(mean_upper, trust_upper)
    if effective_lower > effective_upper:
        return BindingTerm.TRUST_REGION
    if effective_upper < overlap_lower or effective_lower > overlap_upper:
        return BindingTerm.CONTROL

    z = float(stats.norm.ppf(0.5 + coverage_fraction / 2.0))
    half_width = (overlap_upper - overlap_lower) / 2.0
    if aleatoric_std * z > half_width:
        return BindingTerm.ALEATORIC

    return BindingTerm.NONE
