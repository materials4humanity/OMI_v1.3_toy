"""The known-mixing-erasure oracle (CLAUDE.md §7; Core §3.9, Spec §3.2 Prop
3.2) — OQ-2's deferred half (docs/COVERAGE.md Part IV, docs/DECISIONS.md),
built at Phase 3.4 (docs/ROADMAP.md).

`known_erasure.py`'s oracle is diagonal: each named component aligns with
exactly one singular direction, so operator-level rank and per-component
recoverability could not help but agree (the M2 finding). This oracle is
deliberately **not** diagonal — its Jacobian is a symmetric rank-2 map whose
surviving subspace and kernel are both genuine linear combinations of all
three named components, none axis-aligned. Constructed from a fixed
orthonormal basis (mutually orthogonal by direct calculation, not
approximated), so rank, surviving subspace, and each component's own
overlap with it are all known exactly by construction (ADR-004).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(
    (
        (Slot.M, "component_a", 1),
        (Slot.M, "component_b", 1),
        (Slot.Z, "component_c", 1),
    )
)

# Three mutually orthogonal directions, none axis-aligned (verified by
# direct dot product in MixingErasureOperator.__post_init__, not merely
# asserted): survivors at distinct singular values 1.0 and 0.6 so their
# eigenvectors are uniquely determined up to sign; the third, at singular
# value 0.0 exactly, is the kernel -- the erased direction.
_SURVIVING_1 = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
_SURVIVING_2 = np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0)
_KERNEL = np.array([1.0, 1.0, -2.0]) / np.sqrt(6.0)

SINGULAR_VALUE_1 = 1.0
SINGULAR_VALUE_2 = 0.6


@dataclass(frozen=True)
class MixingErasureTruth:
    """The constructed ground truth: rank, and each named component's own
    squared overlap with the surviving subspace (``sum_j <e_i, u_j>^2`` over
    surviving directions ``u_j``) -- 1.0 would mean "entirely within the
    surviving subspace" (the diagonal oracle's case for every surviving
    component); this oracle's construction gives every component a
    genuinely intermediate value, since the kernel loads on all three."""

    rank: int
    component_surviving_overlap: tuple[float, float, float]
    """Squared overlap of ``component_a``, ``component_b``, ``component_c``
    (in schema order) with the 2-D surviving subspace."""
    kernel_direction: FloatArray
    """The exact (unit) kernel vector, for direct comparison against a
    recovered erased-subspace basis vector up to sign."""


@dataclass(frozen=True)
class MixingErasureOperator(EvolutionOperator):
    """``step(s) = J @ s`` for a fixed, symmetric, rank-2 ``J`` built from
    two distinct nonzero singular values on non-axis-aligned directions
    (Core §3.9): a genuinely mixing erasure, not a diagonal one."""

    jacobian_matrix: FloatArray = field(
        default_factory=lambda: (
            SINGULAR_VALUE_1 * np.outer(_SURVIVING_1, _SURVIVING_1)
            + SINGULAR_VALUE_2 * np.outer(_SURVIVING_2, _SURVIVING_2)
        )
    )

    def __post_init__(self) -> None:
        basis = np.stack([_SURVIVING_1, _SURVIVING_2, _KERNEL], axis=0)
        gram = basis @ basis.T
        if not np.allclose(gram, np.eye(3), atol=1e-12):
            raise ValueError("oracle construction error: basis is not orthonormal")

    @property
    def is_erasure(self) -> bool:
        return True

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, self.jacobian_matrix @ state.values)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        """Exact analytic Jacobian (ADR-001/ADR-012): ``step`` is linear, so
        its own matrix is the Jacobian everywhere, no finite difference
        needed."""
        return self.jacobian_matrix


class KnownMixingErasureOracle:
    """Cites CLAUDE.md §7's oracle philosophy, applied to OQ-2's deferred
    mixing-erasure question: does operator-level rank still predict
    per-component influence when the surviving subspace is not
    axis-aligned, or is a per-component projection needed as a distinct
    diagnostic?"""

    def __init__(self) -> None:
        self.schema = SCHEMA
        self.operator = MixingErasureOperator()
        self.null_control = Control(0.0, 1.0, lambda t: np.array([0.0]))

    def build_ensemble(self, n: int, rng: np.random.Generator) -> Ensemble:
        particles = rng.normal(size=(n, self.schema.size))
        return Ensemble(self.schema, particles)

    def truth(self) -> MixingErasureTruth:
        surviving = np.stack([_SURVIVING_1, _SURVIVING_2], axis=1)  # (3, 2)
        overlaps = []
        for i in range(3):
            e_i = np.zeros(3)
            e_i[i] = 1.0
            projection = surviving @ (surviving.T @ e_i)
            overlaps.append(float(np.dot(projection, projection)))
        return MixingErasureTruth(
            rank=2,
            component_surviving_overlap=(overlaps[0], overlaps[1], overlaps[2]),
            kernel_direction=_KERNEL.copy(),
        )
