"""Known-tail oracle test — the M0 pattern-establishing oracle (CLAUDE.md §7).

Cites Spec §4.3 (Proposition 4.1, tail-index transfer) and Core §3.6 (Class B
tail estimation). Deliberately exercises no src/omi/ framework code (there is
none yet: docs/ROADMAP.md M0 is scaffolding only). The "estimator under test"
here is a plain peaks-over-threshold generalised-Pareto fit written directly
in this file — a stand-in for the Class B tail machinery that arrives at M6 —
which is exactly why this oracle needs no framework code (ADR-004, ADR-009 in
docs/DECISIONS.md).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from tests.oracles import Oracle
from tests.oracles.known_tail import FloatArray, KnownTailOracle


def _fit_gpd_shape(samples: FloatArray, quantile: float = 0.95) -> float:
    """Peaks-over-threshold generalised-Pareto shape estimate.

    Not framework code (see module docstring) — a plain scipy fit standing in
    for the driver/tail separation Spec §4.2 will eventually formalise.
    """
    threshold = np.quantile(samples, quantile)
    exceedances = samples[samples > threshold] - threshold
    shape, _loc, _scale = stats.genpareto.fit(exceedances, floc=0)
    return float(shape)


def test_known_tail_oracle_satisfies_the_oracle_protocol() -> None:
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5)
    assert isinstance(oracle, Oracle)


@pytest.mark.parametrize(
    "alpha_a, beta",
    [
        (3.0, 0.5),  # generic contractive-ish case
        (2.0, 1.0 / 6.0),  # Spec §4.3's own worked sanity check: xi_D = xi_a / 6
        (4.0, 2.0),  # amplifying case, beta > 1
    ],
)
def test_gpd_shape_recovers_tail_index_transfer(alpha_a: float, beta: float) -> None:
    """The fitted shape must land near the constructed truth xi_D = beta * xi_a.

    Tolerance is not a fixed decimal (CLAUDE.md §7): it is set from the known
    finite-sample behaviour of a peaks-over-threshold GPD shape MLE, whose
    standard error is on the order of (1+xi)/sqrt(m) for m exceedances
    (Hosking & Wallis 1987) — a few tenths for the sample sizes used here.
    The 0.4 absolute band absorbs that sampling error plus ordinary fitting
    variability; the claim under test is tail-index *transfer*, not decimal
    agreement with an estimator's output.
    """
    rng = np.random.default_rng(20260725)
    oracle = KnownTailOracle(alpha_a=alpha_a, beta=beta)
    samples = oracle.sample_driver(n=200_000, rng=rng)

    xi_hat = _fit_gpd_shape(samples)
    xi_true = oracle.truth()

    assert abs(xi_hat - xi_true) < 0.4, (
        f"fitted xi={xi_hat:.3f} vs constructed truth xi={xi_true:.3f} "
        f"(alpha_a={alpha_a}, beta={beta})"
    )


def test_gpd_shape_scales_with_beta() -> None:
    """Qualitative ordering, per CLAUDE.md §7's preference for orderings over
    decimals: holding alpha_a fixed, a larger beta must recover a larger
    xi_D, since Spec §4.3 makes xi_D directly proportional to beta.
    """
    rng = np.random.default_rng(20260725)
    small = KnownTailOracle(alpha_a=3.0, beta=0.5)
    large = KnownTailOracle(alpha_a=3.0, beta=1.0)

    xi_small = _fit_gpd_shape(small.sample_driver(n=200_000, rng=rng))
    xi_large = _fit_gpd_shape(large.sample_driver(n=200_000, rng=rng))

    assert xi_small < xi_large


def test_sampling_is_deterministic_given_the_same_generator_state() -> None:
    """Every stochastic helper takes an explicit generator (CLAUDE.md §7);
    two independently-seeded generators with the same seed must reproduce
    identical samples, which is what the determinism harness relies on."""
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5)
    samples_a = oracle.sample_driver(n=1_000, rng=np.random.default_rng(42))
    samples_b = oracle.sample_driver(n=1_000, rng=np.random.default_rng(42))
    np.testing.assert_array_equal(samples_a, samples_b)
