"""OQ-5 investigation (docs/COVERAGE.md Part IV; ADR-002, docs/DECISIONS.md):
metric dependence of every reported Lipschitz constant. Cites Core §3.9 /
Spec §2.5: every Lipschitz constant is metric-dependent, and the state has
heterogeneous units admitting no natural metric.

This is the pinned test ADR-002 names (`tests/oracles/test_metric_dependence.py`),
run at M2 per docs/ROADMAP.md's "Investigate OQ-5 (metric dependence)."
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble, FloatArray, Metric, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "a", 1), (Slot.M, "b", 1)))

# A fixed coupling: b weakly appears to influence a (raw coefficient 0.01);
# a does not influence b. Component b's *natural* scale (aleatoric sigma) is
# 100x component a's, as if a and b were expressed in mismatched units for
# the same underlying physical scale of variation. Whether that coupling
# term is "negligible" or "as important as the diagonal" depends entirely on
# which metric interprets it — that dependence is what OQ-5 asks about.
COUPLING: FloatArray = np.array([[1.0, 0.01], [0.0, 1.0]])

NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))


@dataclass(frozen=True)
class CoupledOperator(EvolutionOperator):
    """A fixed linear coupling with an exact analytic Jacobian (ADR-001/012)."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, COUPLING @ state.values)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return COUPLING.copy()


def _build_ensemble(n: int, rng: np.random.Generator) -> Ensemble:
    a = rng.normal(scale=1.0, size=n)
    b = rng.normal(scale=100.0, size=n)
    return Ensemble(SCHEMA, np.stack([a, b], axis=1))


def test_bare_undeclared_metric_hides_the_true_coupling_strength() -> None:
    """Without a metric reflecting each component's real scale (here, both
    treated as unit-scale), the coupling term (raw coefficient 0.01) reads as
    negligible next to the diagonal (1.0) — a naive, metric-blind reading."""
    rng = np.random.default_rng(0)
    ensemble = _build_ensemble(2000, rng)
    op = CoupledOperator()
    bare_metric = Metric(SCHEMA, np.array([1.0, 1.0]))

    jac = op.jacobian(ensemble[0], NULL_CONTROL)
    scaled = jac * bare_metric.scale[np.newaxis, :] / bare_metric.scale[:, np.newaxis]
    assert abs(scaled[0, 1]) < 0.02


def test_aleatoric_sigma_metric_reveals_the_coupling_is_as_strong_as_the_diagonal() -> None:
    """Declaring the metric from the ensemble's own aleatoric spread
    (ADR-002's default) rescales the coupling entry by b's much larger
    natural scale, revealing that a one-sigma change in b moves a by about as
    much as a one-sigma change in a does."""
    rng = np.random.default_rng(1)
    ensemble = _build_ensemble(2000, rng)
    op = CoupledOperator()
    metric = Metric.from_ensemble(ensemble)

    jac = op.jacobian(ensemble[0], NULL_CONTROL)
    scaled = jac * metric.scale[np.newaxis, :] / metric.scale[:, np.newaxis]
    assert abs(scaled[0, 1]) > 0.5


def test_lipschitz_spectrum_changes_with_the_declared_metric() -> None:
    """Same operator, same state: two different declared metrics give two
    different local spectra — "confirm every reported L changes" (OQ-5)."""
    rng = np.random.default_rng(2)
    ensemble = _build_ensemble(2000, rng)
    op = CoupledOperator()
    bare_metric = Metric(SCHEMA, np.array([1.0, 1.0]))
    true_metric = Metric.from_ensemble(ensemble)

    spectrum_bare = op.lipschitz(ensemble[0], NULL_CONTROL, bare_metric)
    spectrum_true = op.lipschitz(ensemble[0], NULL_CONTROL, true_metric)

    assert not np.allclose(spectrum_bare, spectrum_true, rtol=0.1)


def test_aleatoric_normalisation_makes_a_one_sigma_perturbation_comparable_across_slots() -> None:
    """Perturbing each component by its own empirical one-sigma and pushing
    it through the operator should move the readout ('a') by a comparable
    amount for both components — "confirm the aleatoric-sigma normalisation
    makes them comparable across slots" (OQ-5), not the ~100x discrepancy a
    raw, undeclared-unit comparison would show.
    """
    rng = np.random.default_rng(3)
    ensemble = _build_ensemble(5000, rng)
    op = CoupledOperator()
    metric = Metric.from_ensemble(ensemble)

    baseline = ensemble[0]
    baseline_a = op.step(baseline, NULL_CONTROL).get(Slot.M, "a")[0]

    perturbed_a = baseline.with_component(Slot.M, "a", baseline.get(Slot.M, "a") + metric.scale[0])
    perturbed_b = baseline.with_component(Slot.M, "b", baseline.get(Slot.M, "b") + metric.scale[1])

    effect_from_a = op.step(perturbed_a, NULL_CONTROL).get(Slot.M, "a")[0] - baseline_a
    effect_from_b = op.step(perturbed_b, NULL_CONTROL).get(Slot.M, "a")[0] - baseline_a

    ratio = effect_from_b / effect_from_a
    assert 0.5 < ratio < 2.0
