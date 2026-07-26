"""Decision layer primitives (Spec §7.3; ADR-033, docs/DECISIONS.md):
probability of conformance, CVaR, asymmetric cost, and candidate selection.
"""

from __future__ import annotations

import numpy as np

from omi.inverse import Candidate, asymmetric_cost, cvar, probability_of_conformance, select_best_candidate

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
