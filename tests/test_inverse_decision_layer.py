"""Decision layer primitives (Spec §7.3; ADR-033, docs/DECISIONS.md):
probability of conformance, CVaR, asymmetric cost, and candidate selection.
"""

from __future__ import annotations

import numpy as np
import pytest

from scipy import stats

from omi.inverse import (
    Candidate,
    asymmetric_cost,
    cvar,
    decision_sensitive_threshold,
    probability_of_conformance,
    select_best_candidate,
)

from tests.conftest import ObservationRecorder


def test_probability_of_conformance_is_the_empirical_fraction_inside_the_window() -> None:
    samples = np.array([1.0, 5.0, 9.0, 11.0, 15.0])
    assert probability_of_conformance(samples, 0.0, 10.0) == 0.6


def test_probability_of_conformance_prefers_a_tighter_distribution_over_a_better_mean(
    observe: ObservationRecorder,
) -> None:
    """Spec §7.3: "optimise probability of conformance... not expected
    value" — a candidate centred exactly on target but wide can lose to one
    off-centre but tight."""
    rng = np.random.default_rng(0)
    tight_offcenter = rng.normal(9.0, 0.3, 2000)
    wide_centered = rng.normal(10.0, 3.0, 2000)

    tight_poc = probability_of_conformance(tight_offcenter, 8.0, 12.0)
    wide_poc = probability_of_conformance(wide_centered, 8.0, 12.0)

    observe("tight_poc", tight_poc, "> wide_poc")
    observe("wide_poc", wide_poc, "< tight_poc")
    assert tight_poc > wide_poc


def test_cvar_is_worse_than_the_mean_for_a_right_skewed_loss(observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(1)
    losses = rng.exponential(scale=1.0, size=5000)
    cvar_value = cvar(losses, alpha=0.1)
    mean_value = float(np.mean(losses))
    observe("cvar", cvar_value, "> mean")
    observe("mean", mean_value, "< cvar")
    assert cvar_value > mean_value


def test_asymmetric_cost_is_asymmetric_by_construction() -> None:
    values = np.array([8.0, 10.0, 12.0])
    cost = asymmetric_cost(values, target=10.0, cost_below=5.0, cost_above=1.0)
    np.testing.assert_allclose(cost, [10.0, 0.0, 2.0])


def test_select_best_candidate_picks_the_higher_conformance_probability(observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(2)
    good = Candidate(np.array([1.0]), rng.normal(10.0, 0.5, 1000))
    bad = Candidate(np.array([2.0]), rng.normal(15.0, 0.5, 1000))

    result = select_best_candidate([bad, good], lower=8.0, upper=12.0)

    observe("probabilities_of_conformance", result.probabilities_of_conformance, "best is the 'good' candidate")
    assert result.best is good
    assert len(result.probabilities_of_conformance) == 2


def _expected_cost(tau: float, se: float, minimum_effect: float, cost_fa: float, cost_miss: float) -> float:
    """Brute-force expected cost at threshold *tau*, for the oracle check
    below: `cost_fa * P(x > tau | H0=N(0,se))  +  cost_miss * P(x <= tau |
    H1=N(minimum_effect, se))` -- the exact quantity
    `decision_sensitive_threshold`'s closed form claims to minimise."""
    p_false_alarm = float(stats.norm.sf(tau, loc=0.0, scale=se))
    p_miss = float(stats.norm.cdf(tau, loc=minimum_effect, scale=se))
    return cost_fa * p_false_alarm + cost_miss * p_miss


def test_decision_sensitive_threshold_minimises_expected_cost_against_a_numerical_sweep(
    observe: ObservationRecorder,
) -> None:
    """Oracle check (CLAUDE.md §7): `decision_sensitive_threshold`'s closed
    form is the standard Bayes-optimal likelihood-ratio-test boundary
    between two equal-variance Gaussians under asymmetric costs -- verified
    here by brute-force sweeping the expected-cost function itself
    (*_expected_cost*, independent of the formula under test) and checking
    the closed-form threshold sits at the numerical minimum, not merely
    plausible."""
    se, minimum_effect, cost_fa, cost_miss = 0.02, 0.05, 1.0, 20.0

    tau = decision_sensitive_threshold(se, minimum_effect, cost_fa, cost_miss)
    sweep = np.linspace(-0.05, 0.15, 4001)
    costs = np.array([_expected_cost(t, se, minimum_effect, cost_fa, cost_miss) for t in sweep])
    numerical_tau = float(sweep[np.argmin(costs)])

    observe("closed_form_tau", tau, "close to numerical_tau")
    observe("numerical_tau", numerical_tau, "close to closed_form_tau")
    assert abs(tau - numerical_tau) < 0.001


def test_decision_sensitive_threshold_rises_with_the_false_alarm_to_miss_cost_ratio() -> None:
    """A costlier miss (relative to a false alarm) should pull the threshold
    down (more willing to flag on weaker evidence); a costlier false alarm
    should push it up -- the qualitative sensitivity Spec §9.4 asks a
    threshold-setting procedure to report, not only a single number."""
    se, minimum_effect = 0.02, 0.05
    tau_favor_catching = decision_sensitive_threshold(se, minimum_effect, cost_false_alarm=1.0, cost_miss=20.0)
    tau_favor_caution = decision_sensitive_threshold(se, minimum_effect, cost_false_alarm=20.0, cost_miss=1.0)
    assert tau_favor_catching < tau_favor_caution


def test_decision_sensitive_threshold_requires_positive_effect_and_costs() -> None:
    with pytest.raises(ValueError):
        decision_sensitive_threshold(0.02, 0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        decision_sensitive_threshold(0.02, 0.05, 0.0, 1.0)
