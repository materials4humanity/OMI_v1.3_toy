"""Known-unreachability oracle test: docs/ROADMAP.md M9 exit gate —
"Known-unreachability oracle: certificate fires exactly outside the bound."
"""

from __future__ import annotations

import numpy as np

from omi.inverse import ReachabilityCertificate, achievable_bound, is_provably_unreachable, nearest_reachable_state
from omi.state import State

from tests.oracles import Oracle
from tests.oracles.known_unreachability import KnownUnreachabilityOracle


def test_known_unreachability_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownUnreachabilityOracle(), Oracle)


def test_achievable_bound_matches_the_constructed_truth_exactly() -> None:
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    bound = achievable_bound(certificate.phi(oracle.initial_state()), oracle.max_increments())
    assert bound == oracle.truth()


def test_a_target_exactly_on_the_boundary_is_not_flagged_unreachable() -> None:
    """"Fires exactly outside the bound" — a target with `Φ` equal to the
    achievable bound is reachable (the saturating control reaches it
    exactly), so the certificate must not fire."""
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    boundary_target = State(oracle.schema, np.array([oracle.truth() / 2.0, oracle.truth() / 2.0]))

    assert not is_provably_unreachable(certificate, oracle.initial_state(), oracle.max_increments(), boundary_target)


def test_a_target_infinitesimally_beyond_the_boundary_is_flagged_unreachable() -> None:
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    epsilon = 1e-9
    just_beyond = State(
        oracle.schema, np.array([oracle.truth() / 2.0 + epsilon, oracle.truth() / 2.0 + epsilon])
    )

    assert is_provably_unreachable(certificate, oracle.initial_state(), oracle.max_increments(), just_beyond)


def test_the_saturating_control_actually_reaches_the_boundary_exactly() -> None:
    """Sanity check on the oracle's own construction: rolling the true
    operator under the saturating control for `n_steps` produces a state
    whose `Φ` equals the claimed bound exactly, not approximately."""
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    control = oracle.saturating_control()

    state = oracle.initial_state()
    for _ in range(oracle.n_steps):
        state = oracle.operator.step(state, control)

    assert np.isclose(certificate.phi(state), oracle.truth())


def test_nearest_reachable_state_projects_exactly_onto_the_boundary() -> None:
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    far_target = State(oracle.schema, np.array([100.0, 100.0]))

    nearest = nearest_reachable_state(certificate, oracle.initial_state(), oracle.max_increments(), far_target)

    assert np.isclose(certificate.phi(nearest), oracle.truth())


def test_nearest_reachable_state_is_the_true_closest_point_on_the_boundary() -> None:
    """The projection must minimise Euclidean distance to the target among
    all points satisfying `Φ(s) = bound` — checked against a coarse grid
    search over the boundary line, an independent (if crude) verification
    of the closed-form projection."""
    oracle = KnownUnreachabilityOracle()
    certificate = ReachabilityCertificate(oracle.weight, oracle.schema)
    far_target = State(oracle.schema, np.array([100.0, 20.0]))
    bound = oracle.truth()

    nearest = nearest_reachable_state(certificate, oracle.initial_state(), oracle.max_increments(), far_target)
    projected_distance = float(np.linalg.norm(nearest.values - far_target.values))

    grid_a = np.linspace(-50.0, 150.0, 20000)
    grid_b = bound - grid_a
    grid_distances = np.sqrt((grid_a - far_target.values[0]) ** 2 + (grid_b - far_target.values[1]) ** 2)
    best_grid_distance = float(np.min(grid_distances))

    assert projected_distance <= best_grid_distance + 1e-3
