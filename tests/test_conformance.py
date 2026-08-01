"""Conformance mechanics: the level table, `ConformanceReport.claim`, and
the nine automated checks (Spec §9.1, §9.2; ADR-028, docs/DECISIONS.md).
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.conformance import (
    ConformanceInputs,
    ConformanceLevel,
    ConformanceNotMet,
    automated_check_suite,
    calibration_report,
    generate_report,
    measure_closure_defect,
    rollout_length_error_curve,
)
from omi.gaps import NotSpecified
from omi.state import Metric

from omi_domains.flagship.build import build_chain, build_incoming_ensemble
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi.interface import SpecificationVersion

from tests.conftest import ObservationRecorder


def _minimal_inputs() -> ConformanceInputs:
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(incoming)
    return ConformanceInputs(
        specification_version=SpecificationVersion.V1_3,
        declaration=FLAGSHIP_DECLARATION,
        metric=metric,
    )


def test_omi_0_is_claimable_with_only_a_rollout_error_curve_supplied() -> None:
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()
    baseline = incoming[0]
    slot, name, _dim = baseline.schema.components[0]
    perturbed = baseline.with_component(slot, name, baseline.get(slot, name) + 5 * metric.scale[0])
    curve = rollout_length_error_curve(chain, baseline, perturbed, metric)

    inputs = ConformanceInputs(
        specification_version=SpecificationVersion.V1_3,
        declaration=FLAGSHIP_DECLARATION,
        metric=metric,
        rollout_error_curve=curve,
    )
    report = generate_report(inputs)

    assert report.claim(ConformanceLevel.OMI_0) is ConformanceLevel.OMI_0


def test_omi_0_is_not_claimable_without_the_rollout_error_curve() -> None:
    report = generate_report(_minimal_inputs())
    with pytest.raises(ConformanceNotMet) as excinfo:
        report.claim(ConformanceLevel.OMI_0)
    assert any(r.name == "rollout_length_error_curve_reported" for r in excinfo.value.unmet_requirements)


def test_claim_refusal_names_the_specific_unmet_requirements_not_just_a_boolean() -> None:
    """docs/ROADMAP.md M7: "the report refuses to claim a level whose
    requirements are unmet" — the refusal must be specific, not a bare
    failure."""
    report = generate_report(_minimal_inputs())
    with pytest.raises(ConformanceNotMet) as excinfo:
        report.claim(ConformanceLevel.OMI_1)

    unmet_names = {r.name for r in excinfo.value.unmet_requirements}
    assert "sufficiency_test_run_and_reported" in unmet_names
    assert "semigroup_residuals_reported" in unmet_names
    assert "observability_triage_with_dangerous_set_declared" in unmet_names
    assert "calibration_diagnostics_reported" in unmet_names
    # closure defect is NOT in this list: no scale bridging is executed.
    assert "closure_defect_wherever_scale_bridging_occurs" not in unmet_names


def test_claiming_a_conformance_not_met_error_is_distinct_from_not_specified() -> None:
    """ADR-028: a missing diagnostic is an evidentiary gap, not a
    Specification derivation gap — the two exceptions must not be
    conflated."""
    report = generate_report(_minimal_inputs())
    with pytest.raises(ConformanceNotMet):
        report.claim(ConformanceLevel.OMI_1)
    # And separately, NotSpecified is reserved for genuine Spec gaps:
    with pytest.raises(NotSpecified):
        measure_closure_defect()


def test_closure_defect_is_vacuously_satisfied_when_no_scale_bridging_occurs() -> None:
    inputs = _minimal_inputs()
    assert inputs.scale_bridging_occurs is False
    report = generate_report(inputs)
    closure_requirement = next(
        r for r in report.requirements if r.name == "closure_defect_wherever_scale_bridging_occurs"
    )
    assert closure_requirement.satisfied


def test_closure_defect_blocks_the_claim_when_scale_bridging_occurs_but_is_unmeasured() -> None:
    minimal = _minimal_inputs()
    inputs = ConformanceInputs(
        specification_version=SpecificationVersion.V1_3,
        declaration=minimal.declaration, metric=minimal.metric, scale_bridging_occurs=True
    )
    report = generate_report(inputs)
    closure_requirement = next(
        r for r in report.requirements if r.name == "closure_defect_wherever_scale_bridging_occurs"
    )
    assert not closure_requirement.satisfied


def test_highest_claimable_level_reflects_exactly_what_was_supplied() -> None:
    minimal = _minimal_inputs()
    rng = np.random.default_rng(0)
    chain = build_chain()
    incoming = build_incoming_ensemble(50, rng)
    baseline = incoming[0]
    slot, name, _dim = baseline.schema.components[0]
    perturbed = baseline.with_component(slot, name, baseline.get(slot, name) + 5 * minimal.metric.scale[0])
    curve = rollout_length_error_curve(chain, baseline, perturbed, minimal.metric)

    only_omi0 = ConformanceInputs(
        specification_version=SpecificationVersion.V1_3,
        declaration=minimal.declaration,
        metric=minimal.metric,
        rollout_error_curve=curve,
    )
    assert generate_report(only_omi0).highest_claimable_level() == ConformanceLevel.OMI_0


def test_automated_check_suite_reports_unavailable_checks_with_a_reason_not_silently() -> None:
    """Spec §9.2's nine checks, several of which have no supporting module
    yet (constraints.py at M8, inverse.py at M9) — each must say *why* it is
    unavailable, never simply be missing from the suite."""
    inputs = _minimal_inputs()
    checks = automated_check_suite(inputs)
    assert len(checks) == 9

    reachability = next(c for c in checks if c.name == "reachability_certificates")
    assert reachability.residual is None
    assert "M9" in reachability.detail

    constraints = next(c for c in checks if c.name == "adversarial_constraint_satisfaction")
    assert constraints.residual is None
    assert "M8" in constraints.detail


def test_calibration_report_distinguishes_well_calibrated_from_overconfident_ensembles(
    observe: ObservationRecorder,
) -> None:
    rng = np.random.default_rng(0)
    n_cases, n_ensemble = 500, 200
    truth = rng.normal(0, 1, n_cases)
    observations = truth + rng.normal(0, 1, n_cases)

    well_calibrated = truth[:, None] + rng.normal(0, 1, (n_cases, n_ensemble))
    overconfident = truth[:, None] + rng.normal(0, 0.2, (n_cases, n_ensemble))

    good = calibration_report(well_calibrated, observations, nominal_coverage_level=0.9)
    bad = calibration_report(overconfident, observations, nominal_coverage_level=0.9)

    observe("good_pit_uniformity_residual", good.pit_uniformity_residual, "< bad_pit_uniformity_residual")
    observe("bad_pit_uniformity_residual", bad.pit_uniformity_residual, "> good_pit_uniformity_residual")
    observe("good_empirical_coverage", good.empirical_coverage, "> bad_empirical_coverage")
    observe("bad_empirical_coverage", bad.empirical_coverage, "< good_empirical_coverage")

    assert good.pit_uniformity_residual < bad.pit_uniformity_residual
    assert good.empirical_coverage > bad.empirical_coverage
