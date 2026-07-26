"""OQ-3 investigation (docs/DECISIONS.md Open Questions; docs/COVERAGE.md
Part IV): "With several populations of differing α and β, survival is
∏ₚ[1−Fₚ]^{Nₚ} and no single ξ describes the range of interest... check
whether a single-ξ fit misestimates the design-point exceedance
probability."

Two defect populations drive the same component: a common, light-tailed
population (many members, mild individual severity) and a rare, heavy-tailed
population (few members, severe individual tails). A practitioner unaware of
the two populations pools all descriptors and fits one tail index; this test
checks what that costs at a design point deep enough that the rare
population's heavier tail — not the common population's — actually
determines the risk.
"""

from __future__ import annotations

import numpy as np

from omi.classb import competing_risk_survival, estimate_tail_index_hill

from tests.oracles.known_tail import KnownTailOracle

COMMON_POPULATION = KnownTailOracle(alpha_a=5.0, beta=1.0, k=1.0, x_m=1.0)
N_COMMON = 10_000

RARE_POPULATION = KnownTailOracle(alpha_a=1.5, beta=1.0, k=1.0, x_m=1.0)
N_RARE = 10

DESIGN_POINT = 50.0


def _exact_exceedance(oracle: KnownTailOracle, d: float) -> float:
    """``P(D > d)`` in closed form (exact for this oracle's construction,
    not just asymptotic): ``D > d`` iff the descriptor exceeds ``(d/k)**(1/beta)``."""
    a_threshold = (d / oracle.k) ** (1.0 / oracle.beta)
    if a_threshold < oracle.x_m:
        return 1.0
    return float((oracle.x_m / a_threshold) ** oracle.alpha_a)


def _true_design_point_failure_probability() -> float:
    """The competing-risk-aware answer (OQ-3's own formula, `∏ₚ[1−Fₚ]^{Nₚ}`,
    via `omi.classb.competing_risk_survival`), using each population's own
    exact tail rather than a single pooled fit."""
    f_common = _exact_exceedance(COMMON_POPULATION, DESIGN_POINT)
    f_rare = _exact_exceedance(RARE_POPULATION, DESIGN_POINT)
    survival = competing_risk_survival([f_common, f_rare], [N_COMMON, N_RARE])
    return 1.0 - survival


def _naive_single_xi_failure_probability(rng: np.random.Generator) -> float:
    """The naive answer: pool every descriptor from both populations (as a
    practitioner unaware there are two populations would), fit one Hill tail
    index to the pooled sample, and predict the design-point failure
    probability from that single fitted model applied to the *total* count."""
    common_samples = COMMON_POPULATION.sample_descriptors(N_COMMON, rng)
    rare_samples = RARE_POPULATION.sample_descriptors(N_RARE, rng)
    pooled = np.concatenate([common_samples, rare_samples])

    xi_pooled = estimate_tail_index_hill(pooled, top_fraction=0.1)
    alpha_pooled = 1.0 / xi_pooled
    x_m_pooled = float(pooled.min())

    if DESIGN_POINT < x_m_pooled:
        f_pooled = 1.0
    else:
        f_pooled = (x_m_pooled / DESIGN_POINT) ** alpha_pooled

    survival = (1.0 - f_pooled) ** (N_COMMON + N_RARE)
    return 1.0 - survival


def test_oq3_a_single_pooled_tail_fit_badly_underestimates_the_design_point_risk() -> None:
    """OQ-3, answered: pooling both populations and fitting a single tail
    index underestimates the true, competing-risk-aware design-point failure
    probability by orders of magnitude — the pooled fit is dominated by the
    numerous common population and misses that the rare population's
    heavier tail is what actually governs the extreme design point.
    """
    rng = np.random.default_rng(7)
    true_probability = _true_design_point_failure_probability()
    naive_probability = _naive_single_xi_failure_probability(rng)

    assert naive_probability > 0.0
    assert true_probability / naive_probability > 100, (
        f"expected the naive single-xi estimate ({naive_probability:.3e}) to badly "
        f"underestimate the true competing-risk probability ({true_probability:.3e})"
    )


def test_the_rare_heavy_tailed_population_dominates_the_true_design_point_risk() -> None:
    """Sanity check on the construction itself: despite having 1000x fewer
    members, the rare population contributes more design-point exceedance
    than the common one — that asymmetry is exactly what a pooled fit
    cannot see."""
    f_common = _exact_exceedance(COMMON_POPULATION, DESIGN_POINT)
    f_rare = _exact_exceedance(RARE_POPULATION, DESIGN_POINT)

    common_contribution = N_COMMON * f_common
    rare_contribution = N_RARE * f_rare
    assert rare_contribution > common_contribution
