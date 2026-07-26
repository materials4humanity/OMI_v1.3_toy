"""Known-tail oracle test — docs/ROADMAP.md M6 exit gate: "Known-tail oracle
recovers β ξ_a across four (α, β) pairs including a weakly-amplifying case."

Cites Spec §4.3 (Proposition 4.1, tail-index transfer) and Core §3.6 (Class B
tail estimation). At M0 this test exercised a placeholder GPD fit written
directly in the test file, since no framework code existed yet (that
placeholder's own docstring called it "a stand-in for the Class B tail
machinery that arrives at M6"). M6 has now arrived: this test exercises the
real estimator, `omi.classb.estimate_tail_index_hill` composed with
`omi.classb.tail_index_transfer` (ADR-027, docs/DECISIONS.md).
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.classb import estimate_tail_index_hill, tail_index_transfer

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_tail import KnownTailOracle


def test_known_tail_oracle_satisfies_the_oracle_protocol() -> None:
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5)
    assert isinstance(oracle, Oracle)


@pytest.mark.parametrize(
    "alpha_a, beta",
    [
        (3.0, 0.5),  # generic contractive case
        (2.0, 1.0 / 6.0),  # Spec §4.3's own worked sanity check: xi_D = xi_a / 6
        (1.5, 2.0),  # amplifying case, beta > 1, heavier-tailed descriptor too
        (4.0, 1.0),  # weakly-amplifying case, beta == 1 (no rescaling of the tail index)
    ],
)
def test_hill_estimator_and_transfer_recover_xi_d(
    alpha_a: float, beta: float, observe: ObservationRecorder
) -> None:
    """`estimate_tail_index_hill` applied to the *defect descriptor* samples
    (Spec §4.3: the tail index is "measured" from the defect population, not
    from the driver), then rescaled by `tail_index_transfer`, must land near
    the constructed truth `xi_D = beta * xi_a` the oracle carries.

    Tolerance is not a fixed decimal (CLAUDE.md §7): the Hill estimator's
    standard error is `O(1/sqrt(k))` for `k` order statistics (Hill, 1975);
    with `k = 0.1 * 200_000 = 20_000` that error is a few thousandths on
    `xi_a`, comfortably inside the relative band asserted here.
    """
    rng = np.random.default_rng(20260726)
    oracle = KnownTailOracle(alpha_a=alpha_a, beta=beta)
    descriptors = oracle.sample_descriptors(200_000, rng)

    xi_a_hat = estimate_tail_index_hill(descriptors, top_fraction=0.1)
    xi_d_hat = tail_index_transfer(xi_a_hat, beta)
    xi_d_true = oracle.truth()

    observe("xi_a_hat", xi_a_hat, "narrative only, not asserted", units=f"alpha_a={alpha_a}")
    observe("xi_d_hat", xi_d_hat, "abs(xi_d_hat - xi_d_true) < 0.15*xi_d_true + 0.02", units=f"beta={beta}")
    observe("xi_d_true", xi_d_true, "constructed, not measured")

    assert abs(xi_d_hat - xi_d_true) < 0.15 * max(xi_d_true, 1e-6) + 0.02, (
        f"transferred xi_D_hat={xi_d_hat:.4f} vs constructed truth xi_D={xi_d_true:.4f} "
        f"(alpha_a={alpha_a}, beta={beta})"
    )


def test_transfer_scales_linearly_with_beta(observe: ObservationRecorder) -> None:
    """Qualitative ordering, per CLAUDE.md §7's preference for orderings over
    decimals: holding the measured `xi_a` fixed, a larger beta must recover a
    larger `xi_D`, since Spec §4.3 makes `xi_D` directly proportional to
    beta."""
    rng = np.random.default_rng(20260726)
    oracle = KnownTailOracle(alpha_a=3.0, beta=1.0)
    descriptors = oracle.sample_descriptors(200_000, rng)
    xi_a_hat = estimate_tail_index_hill(descriptors, top_fraction=0.1)

    xi_d_small_beta = tail_index_transfer(xi_a_hat, beta=0.5)
    xi_d_large_beta = tail_index_transfer(xi_a_hat, beta=1.0)

    observe("xi_d_small_beta", xi_d_small_beta, "< xi_d_large_beta", units="beta=0.5")
    observe("xi_d_large_beta", xi_d_large_beta, "> xi_d_small_beta", units="beta=1.0")
    assert xi_d_small_beta < xi_d_large_beta


def test_sampling_is_deterministic_given_the_same_generator_state() -> None:
    """Every stochastic helper takes an explicit generator (CLAUDE.md §7);
    two independently-seeded generators with the same seed must reproduce
    identical samples, which is what the determinism harness relies on."""
    oracle = KnownTailOracle(alpha_a=3.0, beta=0.5)
    samples_a = oracle.sample_driver(n=1_000, rng=np.random.default_rng(42))
    samples_b = oracle.sample_driver(n=1_000, rng=np.random.default_rng(42))
    np.testing.assert_array_equal(samples_a, samples_b)
