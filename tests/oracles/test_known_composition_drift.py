"""ADR-050's constancy residual against a drift known by construction (ADR-076; composition
stage C1).

Two arms sharing everything but the boundary flux, so any difference between them is
attributable to the flux alone. The estimator must recover the planted drift exactly and must
separate the four verdicts `ConstancyVerdict` declares.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.proposed.composition import (
    CompositionMetric,
    ConstancyVerdict,
    constancy_residual,
)

from omi_domains.flagship_composition.composition import (
    BULK_MEAN,
    DESCRIPTOR_MAP,
    DESCRIPTORS,
    SURFACE_MEAN,
)
from omi_domains.flagship_composition.interface import domain_mean_trajectory

from tests.conftest import ObservationRecorder
from tests.oracles.known_composition_drift import (
    PLANTED_FLUX,
    closed_arm_deviations,
    open_arm_deviations,
    substructure_change,
    truth,
)


def test_the_closed_arm_conserves_the_domain_mean_exactly(observe: ObservationRecorder) -> None:
    """**ADR-050's conservation claim, and it must be exact rather than small.**

    "A mean over a closed domain is constant by conservation." A drift that were merely small
    would not distinguish conserved from nearly-conserved, and the diagnosis that a violation
    means the domain is *open* rests on that being sharp. The conservative operator does not
    write the deviation at all, so the drift is `0.0` exactly.
    """
    means = domain_mean_trajectory(closed_arm_deviations())
    report = constancy_residual(
        means, tolerance=0.0, region="representative_volume", declared_closed=True
    )
    observe("closed_arm_drift", report.max_absolute_drift, "== 0.0 exactly, not merely small")
    observe("closed_arm_verdict", report.verdict.value, "consistent_closed")

    assert report.max_absolute_drift == truth().closed_drift == 0.0
    assert report.verdict is ConstancyVerdict.CONSISTENT_CLOSED
    assert report.consistent


def test_the_closed_arm_is_not_a_no_op(observe: ObservationRecorder) -> None:
    """The conservation result would be vacuous if the operator changed nothing.

    It coarsens `substructure_density` substantially over the same steps, so what is being
    demonstrated is that **redistribution inside a closed boundary changes the state without
    moving the domain mean** — not that a no-op leaves a mean alone.
    """
    initial, final = substructure_change()
    observe("closed_arm_substructure_ratio", final / initial, "< 0.5 -- a real state change")
    assert final < 0.5 * initial


def test_the_planted_drift_is_recovered_exactly(observe: ObservationRecorder) -> None:
    """The oracle's point: `drift = flux × duration × steps`, known before measuring."""
    means = domain_mean_trajectory(open_arm_deviations())
    report = constancy_residual(
        means, tolerance=1e-12, region="representative_volume", declared_closed=True
    )
    expected = truth().open_drift
    observe("planted_drift_truth", expected, f"flux {PLANTED_FLUX} x duration x steps")
    observe("recovered_drift", report.max_absolute_drift, "== the planted drift")

    assert report.max_absolute_drift == pytest.approx(expected, rel=1e-12, abs=1e-15)


def test_a_drifting_mean_under_a_closed_declaration_diagnoses_an_open_domain(
    observe: ObservationRecorder,
) -> None:
    """**ADR-050's diagnosis, which is the whole reason the verdict is not a pass/fail.**

    The entry is explicit: a violation "does not mean the declaration is arbitrary nonsense; it
    means the declared domain is open, and the coupling should have been `DEPLETED_BY` with a
    declared boundary flux." So the verdict names the repair, and the repair is *not* to adjust
    `c̄` — `c̄` indexes the operator family and is not what moved.
    """
    means = domain_mean_trajectory(open_arm_deviations())
    report = constancy_residual(
        means, tolerance=1e-6, region="representative_volume", declared_closed=True
    )
    observe("undeclared_open_verdict", report.verdict.value, "open_domain_undeclared")
    observe("diagnosis_names_the_repair", "re-declare it open" in report.diagnosis, "True")

    assert report.verdict is ConstancyVerdict.OPEN_DOMAIN_UNDECLARED
    assert not report.consistent
    assert "OPEN" in report.diagnosis
    assert "not to adjust c-bar" in report.diagnosis.replace("NOT", "not")


def test_the_same_drift_under_an_open_declaration_is_consistent(
    observe: ObservationRecorder,
) -> None:
    """The case a pass/fail verdict cannot express, and the reason there are four members.

    Identical measurement, different declaration: a domain declared **open with a named flux**
    that duly drifts is *consistent*. Nothing about the numbers changed — only what was claimed.
    """
    means = domain_mean_trajectory(open_arm_deviations())
    report = constancy_residual(
        means, tolerance=1e-6, region="surface_layer", declared_closed=False
    )
    observe("declared_open_verdict", report.verdict.value, "consistent_open")
    assert report.verdict is ConstancyVerdict.CONSISTENT_OPEN
    assert report.consistent


def test_an_open_declaration_whose_mean_holds_is_reported_not_passed(
    observe: ObservationRecorder,
) -> None:
    """The fourth member. Not an error — a declared flux may be negligible over the interval
    measured — but the declaration claims a transport the measurement does not exhibit, so it
    is surfaced rather than silently passed."""
    means = domain_mean_trajectory(closed_arm_deviations())
    report = constancy_residual(
        means, tolerance=1e-9, region="surface_layer", declared_closed=False
    )
    observe("suspect_open_verdict", report.verdict.value, "suspect_closed_declaration")
    assert report.verdict is ConstancyVerdict.SUSPECT_CLOSED_DECLARATION


def test_a_residual_over_c_bar_alone_would_be_vacuous(observe: ObservationRecorder) -> None:
    """Pins ADR-076's reason for measuring the domain mean of `c̄ + δc` rather than `c̄`.

    `c̄` is a parameter: no operator transports it, so a trajectory of `c̄` is constant by
    construction and a residual over it would return `0.0` for a domain that is losing solute
    through a free surface. That is not a check, it is a tautology — and it is exactly the trap
    a reader might fall into on ADR-050's phrase "constant along the chain by definition".
    """
    steps = len(open_arm_deviations())
    c_bar_only = (float(BULK_MEAN.fractions()[1]),) * steps
    vacuous = constancy_residual(
        c_bar_only, tolerance=0.0, region="representative_volume", declared_closed=True
    )
    real = constancy_residual(
        domain_mean_trajectory(open_arm_deviations()),
        tolerance=0.0,
        region="representative_volume",
        declared_closed=True,
    )
    observe("c_bar_only_drift", vacuous.max_absolute_drift, "== 0.0 -- tautologically")
    observe("domain_mean_drift", real.max_absolute_drift, "> 0 -- the real signal")

    assert vacuous.max_absolute_drift == 0.0
    assert vacuous.verdict is ConstancyVerdict.CONSISTENT_CLOSED
    assert real.max_absolute_drift > 0.0
    assert real.verdict is ConstancyVerdict.OPEN_DOMAIN_UNDECLARED


def test_a_two_step_minimum_is_required() -> None:
    """A drift needs two points. Refused rather than returning zero, which would read as
    "conserved" for a trajectory that was never measured."""
    with pytest.raises(ValueError, match="at least two steps"):
        constancy_residual([0.5], tolerance=0.0, region="r", declared_closed=True)


# --- the simplex as architecture (ADR-076 decision 1) ------------------------


def test_the_simplex_holds_for_arbitrary_off_manifold_coordinates(
    observe: ObservationRecorder,
) -> None:
    """**CLAUDE.md invariant 5, tested where it matters: off-manifold.**

    "Constraint tests run off-manifold with out-of-range controls, because that is where
    inverse design goes." The simplex is architecture on the descriptor map, so fractions are
    non-negative and sum to one for *any* real coordinates — including wildly out-of-range
    ones an optimiser would reach. A validated constraint would have to reject these; a
    structural one absorbs them.
    """
    rng = np.random.default_rng(20240816)
    worst_sum_error = 0.0
    for scale in (1.0, 1e2, 1e4):
        for _ in range(50):
            coordinates = rng.normal(scale=scale, size=len(DESCRIPTOR_MAP.underlying))
            fractions = DESCRIPTOR_MAP.fractions_of(coordinates)
            assert np.all(fractions >= 0.0)
            worst_sum_error = max(worst_sum_error, abs(float(fractions.sum()) - 1.0))
    observe("worst_simplex_sum_error_off_manifold", worst_sum_error, "< 1e-12")
    assert worst_sum_error < 1e-12


def test_descriptors_are_only_reachable_through_the_simplex(observe: ObservationRecorder) -> None:
    """The constraint cannot be bypassed by a caller: the map's only public route to
    `evaluate` runs through `fractions_of` (ADR-076 decision 1)."""
    coordinates = np.array([12.0, -30.0, 4.0, 0.0])
    values = DESCRIPTOR_MAP.named_descriptors_of(coordinates)
    observe("descriptor_names", tuple(values), f"== {DESCRIPTORS}")
    assert tuple(values) == DESCRIPTORS
    assert all(np.isfinite(v) for v in values.values())


def test_the_forward_constraint_does_not_answer_the_inverse_question(
    observe: ObservationRecorder,
) -> None:
    """**Stated as a test so the cheap half is not mistaken for the whole** (ADR-076).

    The simplex removes the *forward* failure mode: no descriptor tuple can be evaluated at an
    off-simplex composition. It says nothing about the *inverse* — given a target descriptor
    tuple, is there any composition mapping to it? Here is a tuple far outside anything the
    declared map produces, and nothing in stage C1 refuses it, because refusing it is ADR-053's
    certificate and stage C3's work.
    """
    reachable = [
        DESCRIPTOR_MAP.named_descriptors_of(
            np.array([a, b, 0.0, 0.0], dtype=float)
        )["hardenability_index"]
        for a in (-5.0, 0.0, 5.0)
        for b in (-5.0, 0.0, 5.0)
    ]
    unreachable_target = 10.0 * max(reachable)
    observe("max_reachable_hardenability", max(reachable), "the map's own range")
    observe("unattainable_target_refused_at_c1", False, "False -- ADR-053's certificate is C3")
    assert unreachable_target > max(reachable)


# --- the descriptor metric (ADR-052's missing half) --------------------------


def test_the_composition_metric_is_zero_only_on_identity(observe: ObservationRecorder) -> None:
    """ADR-052 makes descriptors the metric over `c̄`; until stage C1 only the basis was
    declared and no distance existed."""
    metric = CompositionMetric(
        descriptors=DESCRIPTORS,
        scale=np.array([0.1, 0.1]),
        basis="unit test: equal nominal spreads, so the distance reads in descriptor units",
    )
    here = BULK_MEAN.descriptor_values()
    observe("self_distance", metric.distance(here, here), "== 0.0")
    assert metric.distance(here, here) == 0.0

    shifted = {k: v + 0.05 for k, v in here.items()}
    observe("shifted_distance", metric.distance(here, shifted), "> 0")
    assert metric.distance(here, shifted) > 0.0
    # Symmetric, as any metric must be.
    assert metric.distance(here, shifted) == pytest.approx(metric.distance(shifted, here))


def test_the_metric_refuses_a_missing_descriptor() -> None:
    """A distance over a subset of the declared basis is a distance in a different space, so it
    is refused rather than computed over what happens to be present."""
    metric = CompositionMetric(
        descriptors=DESCRIPTORS, scale=np.array([1.0, 1.0]), basis="unit test"
    )
    with pytest.raises(ValueError, match="no value supplied"):
        metric.distance({DESCRIPTORS[0]: 1.0}, BULK_MEAN.descriptor_values())


def test_the_metric_requires_a_declared_basis() -> None:
    """CLAUDE.md invariant 1: a normalisation with no stated basis makes the distance
    uninterpretable, which is `docs/V1.4-EDITS.md` E-33's finding."""
    with pytest.raises(ValueError, match="normalisation was computed from"):
        CompositionMetric(descriptors=DESCRIPTORS, scale=np.array([1.0, 1.0]), basis="  ")


# --- the open-domain declaration's own discipline ----------------------------


def test_an_open_domain_must_name_its_flux(observe: ObservationRecorder) -> None:
    """ADR-050's repair is to re-declare the domain open **and name the flux**, so an open
    declaration with no closure note is the same under-declaration one step along."""
    from omi.proposed.composition import MeanComposition

    observe("surface_declared_open", not SURFACE_MEAN.domain_declared_closed, "True")
    observe("surface_names_its_flux", "leaves through the free surface" in SURFACE_MEAN.closure_note, "True")
    assert not SURFACE_MEAN.domain_declared_closed
    assert SURFACE_MEAN.closure_note.strip()

    with pytest.raises(ValueError, match="NAME THE FLUX"):
        MeanComposition(
            region="unnamed_open_domain",
            unconstrained=np.zeros(len(DESCRIPTOR_MAP.underlying)),
            descriptor_map=DESCRIPTOR_MAP,
            projection_scale=BULK_MEAN.projection_scale,
            domain_declared_closed=False,
            closure_note="",
        )
