"""Φ is never formed as a chained matrix product (Spec §3.5; ADR-018,
docs/DECISIONS.md): ``propagate_jvp`` / ``propagate_vjp`` apply each
segment's own Jacobian to a vector, one segment at a time. This is checked
two ways: agreement with the "obvious" dense product computed independently
in this test, and the adjoint identity ``w . (Phi v) == (Phi^T w) . v`` that
any correct JVP/VJP pair must satisfy regardless of what Phi actually is.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import nominal_trajectory, propagate_jvp, propagate_vjp
from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "a", 1), (Slot.M, "b", 1), (Slot.Z, "c", 1)))
NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))


@dataclass(frozen=True)
class LinearOperator3(EvolutionOperator):
    """A fixed, arbitrary (non-symmetric, non-diagonal) 3x3 linear map."""

    matrix: FloatArray

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, self.matrix @ state.values)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return self.matrix


M0 = np.array([[1.0, 0.2, 0.0], [0.0, 0.9, 0.1], [0.3, 0.0, 0.8]])
M1 = np.array([[0.7, 0.0, 0.1], [0.2, 1.0, 0.0], [0.0, 0.1, 0.9]])
M2 = np.array([[0.9, 0.1, 0.0], [0.0, 0.6, 0.3], [0.1, 0.0, 1.1]])


def _three_segment_chain() -> Chain:
    return Chain(
        (
            Segment(LinearOperator3(M0), NULL_CONTROL),
            Segment(LinearOperator3(M1), NULL_CONTROL),
            Segment(LinearOperator3(M2), NULL_CONTROL),
        )
    )


def test_jvp_matches_the_dense_product_computed_independently() -> None:
    """propagate_jvp(0, 3, v) must equal (M2 @ M1 @ M0) @ v — the dense
    product this test forms itself, entirely outside omi.observability, to
    check the matrix-free implementation against the obvious answer."""
    chain = _three_segment_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 2.0, 3.0])))
    rng = np.random.default_rng(0)
    v = rng.normal(size=3)

    expected = M2 @ (M1 @ (M0 @ v))
    actual = propagate_jvp(chain, nominal, 0, 3, v)
    np.testing.assert_allclose(actual, expected, atol=1e-10)


def test_vjp_matches_the_dense_transpose_product() -> None:
    chain = _three_segment_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 2.0, 3.0])))
    rng = np.random.default_rng(1)
    w = rng.normal(size=3)

    expected = M0.T @ (M1.T @ (M2.T @ w))
    actual = propagate_vjp(chain, nominal, 0, 3, w)
    np.testing.assert_allclose(actual, expected, atol=1e-10)


def test_jvp_vjp_adjoint_identity_holds_for_a_partial_subinterval() -> None:
    """w . (Phi_{j,k} v) == (Phi_{j,k}^T w) . v for arbitrary v, w — the
    defining property of an adjoint pair, checked on a sub-interval (k=1,
    j=3) rather than the whole chain, since Spec Sec3.1's Phi is defined
    between any two indices, not just the endpoints."""
    chain = _three_segment_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([0.5, -1.0, 2.0])))
    rng = np.random.default_rng(2)
    v = rng.normal(size=3)
    w = rng.normal(size=3)

    lhs = w @ propagate_jvp(chain, nominal, 1, 3, v)
    rhs = propagate_vjp(chain, nominal, 1, 3, w) @ v
    assert abs(lhs - rhs) < 1e-10


def test_propagation_over_zero_segments_is_the_identity() -> None:
    """Phi_{k,k} = I (Spec Sec3.1): propagating across zero segments must
    return the input vector unchanged."""
    chain = _three_segment_chain()
    nominal = nominal_trajectory(chain, State(SCHEMA, np.array([1.0, 1.0, 1.0])))
    v = np.array([3.0, -2.0, 5.0])

    np.testing.assert_array_equal(propagate_jvp(chain, nominal, 1, 1, v), v)
    np.testing.assert_array_equal(propagate_vjp(chain, nominal, 1, 1, v), v)
