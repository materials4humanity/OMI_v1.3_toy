"""Subset simulation test: Spec §4.5's rare-event sampling, checked against
the known-tail oracle's exact (closed-form) exceedance probability at a
sample cost far below direct Monte Carlo — the cost claim Spec §4.5 itself
makes ("three orders of magnitude cheaper").
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import stats

from omi.classb import subset_simulation
from omi.state import FloatArray

from tests.oracles.known_tail import KnownTailOracle


def _exact_survival(oracle: KnownTailOracle, d: float) -> float:
    """``P(D > d)`` in closed form for the known-tail oracle's exact
    (non-asymptotic) Pareto-descriptor / power-law-driver construction:
    ``D > d`` iff ``a > (d/k)**(1/beta)``, and `a` is exactly Pareto."""
    a_threshold = (d / oracle.k) ** (1.0 / oracle.beta)
    if a_threshold < oracle.x_m:
        return 1.0
    return float((oracle.x_m / a_threshold) ** oracle.alpha_a)


def _rosenblatt_evaluate(oracle: KnownTailOracle) -> Callable[[FloatArray], FloatArray]:
    """Compose a standard-normal input with the oracle's exact inverse CDF
    (the probability-integral-transform convention `subset_simulation`
    expects, ADR-027): ``z -> Φ(z) -> Pareto quantile -> driver``."""

    def evaluate(z: FloatArray) -> FloatArray:
        u = stats.norm.cdf(z[:, 0])
        u = np.clip(u, 0.0, 1.0 - 1e-15)
        a = oracle.x_m * (1.0 - u) ** (-1.0 / oracle.alpha_a)
        return oracle.driver(a)

    return evaluate


def test_subset_simulation_recovers_a_known_rare_exceedance_probability() -> None:
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5, k=1.0, x_m=1.0)
    target = 50.0
    truth = _exact_survival(oracle, target)
    assert truth < 1e-9, "test is only meaningful if the target is genuinely rare"

    rng = np.random.default_rng(3)
    result = subset_simulation(
        _rosenblatt_evaluate(oracle), target, rng, dimension=1, n_per_level=500, conditional_probability=0.1
    )

    assert result.probability > 0.0
    log_ratio = np.log10(result.probability / truth)
    assert abs(log_ratio) < 1.0, (
        f"subset-simulation estimate {result.probability:.3e} is more than one "
        f"order of magnitude from the exact truth {truth:.3e}"
    )


def test_subset_simulation_uses_far_fewer_evaluations_than_direct_sampling_would() -> None:
    """Spec §4.5's cost claim: subset simulation reaches a rare target at a
    cost of `O(c * n_per_level)`, not `O(1 / P_f)` direct samples."""
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5, k=1.0, x_m=1.0)
    target = 50.0
    truth = _exact_survival(oracle, target)

    rng = np.random.default_rng(3)
    result = subset_simulation(
        _rosenblatt_evaluate(oracle), target, rng, dimension=1, n_per_level=500, conditional_probability=0.1
    )

    direct_sampling_cost = 1.0 / truth
    assert result.n_evaluations < direct_sampling_cost / 1000


def test_subset_simulation_reports_its_level_thresholds() -> None:
    """Never a bare probability (CLAUDE.md §8): the per-level thresholds
    climbing toward the target are always reported alongside the estimate."""
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5, k=1.0, x_m=1.0)
    rng = np.random.default_rng(4)
    result = subset_simulation(_rosenblatt_evaluate(oracle), 50.0, rng, dimension=1)

    assert len(result.level_thresholds) > 0
    thresholds = np.array(result.level_thresholds)
    assert np.all(np.diff(thresholds) > 0), "level thresholds must climb monotonically"
