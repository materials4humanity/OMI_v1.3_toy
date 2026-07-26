"""Hard structural constraints (Spec §2.2; ADR-030, docs/DECISIONS.md):
each layer's constraint holds by construction, checked off-manifold with
adversarial out-of-range inputs — docs/ROADMAP.md M8 exit gate: "constraint
satisfaction holds off-manifold."
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pytest

from omi.constraints import (
    conserve_total,
    conserve_total_jacobian,
    monotone_increasing,
    monotone_increasing_jacobian,
    positive,
    positive_grad,
    simplex,
    simplex_jacobian,
)
from omi.state import FloatArray

TRAINING_SCALE = 5.0
"""Typical magnitude of inputs a network would see in training — the
adversarial checks below probe far outside this, per CLAUDE.md §5 invariant
5: "Constraint tests run off-manifold with out-of-range controls, because
that is where inverse design goes.\""""

OFF_MANIFOLD_SCALE = 100.0
"""20x TRAINING_SCALE — adversarial, but comfortably within float64's
representable range for `positive` (softplus underflows to exactly 0.0
only below roughly -745, i.e. beyond 7 sigma at this scale for the sample
sizes used here; per `positive`'s own docstring caveat)."""


def _numeric_jacobian(
    f: Callable[[FloatArray], FloatArray], x: FloatArray, eps: float = 1e-6
) -> FloatArray:
    n_in = x.shape[0]
    n_out = f(x).shape[0]
    jac = np.zeros((n_out, n_in))
    for j in range(n_in):
        dx = np.zeros(n_in)
        dx[j] = eps
        jac[:, j] = (f(x + dx) - f(x - dx)) / (2 * eps)
    return jac


@pytest.mark.parametrize("scale", [TRAINING_SCALE, OFF_MANIFOLD_SCALE])
def test_positive_holds_on_and_off_manifold(scale: float) -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, scale, 100)
    assert np.all(positive(x) > 0.0)


@pytest.mark.parametrize("scale", [TRAINING_SCALE, OFF_MANIFOLD_SCALE])
def test_simplex_holds_on_and_off_manifold(scale: float) -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(0.0, scale, 6)
    p = simplex(x)
    assert np.all(p >= 0.0)
    assert np.isclose(p.sum(), 1.0)


@pytest.mark.parametrize("scale", [TRAINING_SCALE, OFF_MANIFOLD_SCALE])
def test_monotone_increasing_holds_on_and_off_manifold(scale: float) -> None:
    rng = np.random.default_rng(2)
    deltas = rng.normal(0.0, scale, 8)
    m = monotone_increasing(deltas, initial=1.0)
    assert np.all(np.diff(m) >= 0.0)


@pytest.mark.parametrize("scale", [TRAINING_SCALE, OFF_MANIFOLD_SCALE])
def test_conserve_total_holds_on_and_off_manifold(scale: float) -> None:
    rng = np.random.default_rng(3)
    x = rng.normal(0.0, scale, 5)
    y = conserve_total(x, total=10.0)
    assert np.isclose(float(np.sum(y)), 10.0)


def test_positive_grad_matches_finite_difference() -> None:
    rng = np.random.default_rng(4)
    x = rng.normal(0.0, TRAINING_SCALE, 20)
    numeric = (positive(x + 1e-6) - positive(x - 1e-6)) / 2e-6
    assert np.max(np.abs(positive_grad(x) - numeric)) < 1e-6


def test_simplex_jacobian_matches_finite_difference() -> None:
    rng = np.random.default_rng(5)
    x = rng.normal(0.0, TRAINING_SCALE, 5)
    assert np.max(np.abs(simplex_jacobian(x) - _numeric_jacobian(simplex, x))) < 1e-6


def test_monotone_increasing_jacobian_matches_finite_difference() -> None:
    rng = np.random.default_rng(6)
    deltas = rng.normal(0.0, TRAINING_SCALE, 5)
    f = lambda d: monotone_increasing(d, initial=1.0)  # noqa: E731
    assert np.max(np.abs(monotone_increasing_jacobian(deltas) - _numeric_jacobian(f, deltas))) < 1e-6


def test_conserve_total_jacobian_matches_finite_difference() -> None:
    rng = np.random.default_rng(7)
    x = rng.normal(0.0, TRAINING_SCALE, 5)
    f = lambda v: conserve_total(v, total=10.0)  # noqa: E731
    assert np.max(np.abs(conserve_total_jacobian(5) - _numeric_jacobian(f, x))) < 1e-6
