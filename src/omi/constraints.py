"""Hard structural constraints: architecture, never loss penalties.

Cites Core §3.9 / Spec §2.2: "Hard constraints beat soft penalties... A
penalty enforces physics where the training data live; an optimiser
searching for an optimal route will find precisely where enforcement is
weak." CLAUDE.md §5 invariant 5 states this as non-negotiable. ADR-030
(docs/DECISIONS.md) fixes which of Spec §2.2's five named categories this
module implements as concrete, differentiable reparameterisations
(positivity, simplex, monotonicity, conservation) and which it declines to
generalise (symmetry, left to domains; thermodynamic admissibility, out of
scope — recorded there, not silently omitted).

Every function here maps an *unconstrained* parameter array to a
*constrained* output for which violating the constraint is not
representable at all — the point of Spec §2.2's requirement. Each also
returns its own exact Jacobian action where `learning.py`'s backprop needs
one, since these functions sit inside a learned operator's forward pass.
"""

from __future__ import annotations

import numpy as np

from omi.state import FloatArray


def positive(x: FloatArray) -> FloatArray:
    """Softplus: `log(1 + e^x)`, positive for every real input (Spec §2.2's
    range constraint — "positivity for densities and damage"). Smooth and
    strictly increasing, so a learned operator's gradient still flows
    through it everywhere, unlike a clip at zero.

    Mathematically positive for any finite `x`; at very large negative `x`
    (below roughly -745 in float64) the true value underflows to exactly
    `0.0` in floating point — a representable-range limit of IEEE double
    precision, not a flaw in the reparameterisation itself.
    """
    return np.logaddexp(0.0, x)


def positive_grad(x: FloatArray) -> FloatArray:
    """`d(positive)/dx = sigmoid(x)` — the exact derivative, for chaining
    through a learned operator's Jacobian (Spec §2.2)."""
    return 1.0 / (1.0 + np.exp(-x))


def simplex(x: FloatArray) -> FloatArray:
    """Softmax: componentwise non-negative and summing to exactly one for
    any real input (Spec §2.2's range constraint — "simplex parameterisation
    for fractions"). Numerically stabilised by subtracting the max.
    """
    shifted = x - np.max(x)
    exp = np.exp(shifted)
    result: FloatArray = exp / np.sum(exp)
    return result


def simplex_jacobian(x: FloatArray) -> FloatArray:
    """`d(simplex)/dx = diag(p) - p p^T` where `p = simplex(x)` — the exact
    softmax Jacobian, for chaining through a learned operator's Jacobian
    (Spec §2.2)."""
    p = simplex(x)
    return np.diag(p) - np.outer(p, p)


def monotone_increasing(deltas: FloatArray, initial: float = 0.0) -> FloatArray:
    """Cumulative sum of `positive(deltas)`, offset by *initial* — non-
    decreasing by construction for any real *deltas* (Spec §2.2:
    "monotonicity... enforce by monotone parameterisation or non-negative
    increments"; CLAUDE.md §3's `z` slot: "accumulated driving measures" are
    exactly this shape)."""
    increments = positive(deltas)
    result: FloatArray = initial + np.cumsum(increments)
    return result


def monotone_increasing_jacobian(deltas: FloatArray) -> FloatArray:
    """`d(monotone_increasing)/d(deltas)` (Spec §2.2): entry `(i, j)` is
    `positive_grad(deltas[j])` if `j <= i`, else 0 — the exact lower-
    triangular Jacobian of a cumulative sum of positive increments."""
    grad = positive_grad(deltas)
    n = deltas.shape[0]
    lower_triangular = np.tril(np.ones((n, n)))
    return lower_triangular * grad[np.newaxis, :]


def conserve_total(x: FloatArray, total: float) -> FloatArray:
    """The Euclidean-nearest point to *x* on the hyperplane
    `{y : sum(y) = total}` (Spec §2.2: "conservation — mass balance across
    transformation and partitioning steps"): `x - (sum(x) - total) / n`,
    exact for any real *x*, never merely close.
    """
    n = x.shape[0]
    excess = float(np.sum(x)) - total
    result: FloatArray = x - excess / n
    return result


def conserve_total_jacobian(n: int) -> FloatArray:
    """`d(conserve_total)/dx = I - (1/n) * ones(n, n)` — constant
    (independent of *x*, since the projection is affine), for chaining
    through a learned operator's Jacobian (Spec §2.2)."""
    return np.eye(n) - np.ones((n, n)) / n
