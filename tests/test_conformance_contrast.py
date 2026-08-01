"""Contrast conformance demonstration: docs/ROADMAP.md M7 exit gate names
"OMI-1 for the flagship" specifically, not the contrast domain. This test
builds every OMI-1 diagnostic *except* a real matched-history sufficiency
campaign for the contrast domain and shows OMI-0 is reached while OMI-1 is
correctly, specifically blocked on exactly that missing item.

This is a scope decision, not a discovered structural impossibility: unlike
the flagship (where `heating_and_soak` is a declared erasure, so a matched-
pair campaign excluding the erased components is a natural, minimal-effort
demonstration — `tests/test_conformance_flagship.py`), the contrast domain
has no erasure at all (`omi_domains/contrast/interface.py`:
``erasure_inventory=()``), so nothing is "free" to exclude from the tracked
state without genuinely testing whether Axiom S survives the exclusion.
Building that campaign properly — including running the augmentation loop
(Spec §1.5) to confirm which components a sufficient schema actually needs —
is real, additional work this milestone does not undertake for this domain.
It remains future work, not a closed question.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.conformance import (
    CalibrationReport,
    ConformanceInputs,
    ConformanceLevel,
    ConformanceNotMet,
    calibration_report,
    generate_report,
    rollout_length_error_curve,
)
from omi.observability import (
    Observation,
    TriageResult,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.operators import Control, semigroup_residual
from omi.state import FloatArray, Metric

from omi_domains.contrast.build import build_chain, build_incoming_ensemble
from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi.interface import SpecificationVersion


def _semigroup_residuals(rng: np.random.Generator) -> FloatArray:
    incoming = build_incoming_ensemble(1, rng)
    state = incoming[0]
    control = Control(0.0, 1.0, lambda t: np.array([2.0]))
    residuals = [semigroup_residual(CYCLING, state, control, t_mid) for t_mid in (0.2, 0.4, 0.6, 0.8)]
    return np.array(residuals)


def _contrast_triage(rng: np.random.Generator, n_cycles: int = 5) -> TriageResult:
    ensemble = build_incoming_ensemble(100, rng)
    chain = build_chain(n_cycles=n_cycles, current=2.0)
    nominal = nominal_trajectory(chain, ensemble[0])
    sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=n_cycles),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    return danger_triage(chain, nominal, 0, gramian, prior, [DendriteRisk()], sensors)


def _contrast_calibration(rng: np.random.Generator, n_cycles: int = 5) -> CalibrationReport:
    n_cases = 300
    n_ensemble = 100
    chain = build_chain(n_cycles=n_cycles, current=2.0)
    readout = TerminalVoltage()
    predictive = np.zeros((n_cases, n_ensemble))
    observations = np.zeros(n_cases)
    for i in range(n_cases):
        ensemble = build_incoming_ensemble(n_ensemble + 1, rng)
        final = chain.rollout(ensemble).final
        values = readout(final)[:, 0]
        predictive[i] = values[:-1]
        observations[i] = values[-1]
    return calibration_report(predictive, observations, nominal_coverage_level=0.9)


def _contrast_rollout_curve(rng: np.random.Generator, metric: Metric, n_cycles: int = 5) -> FloatArray:
    chain = build_chain(n_cycles=n_cycles, current=2.0)
    incoming = build_incoming_ensemble(1, rng)
    baseline = incoming[0]
    slot, name, _dim = baseline.schema.components[0]
    perturbed = baseline.with_component(slot, name, baseline.get(slot, name) + 5 * metric.scale[0])
    return rollout_length_error_curve(chain, baseline, perturbed, metric)


def _contrast_inputs_without_sufficiency() -> ConformanceInputs:
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(incoming)

    return ConformanceInputs(
        specification_version=SpecificationVersion.V1_3,
        declaration=CONTRAST_DECLARATION,
        metric=metric,
        rollout_error_curve=_contrast_rollout_curve(np.random.default_rng(1), metric),
        semigroup_residuals=_semigroup_residuals(np.random.default_rng(2)),
        triage_result=_contrast_triage(np.random.default_rng(3)),
        calibration=_contrast_calibration(np.random.default_rng(4)),
        scale_bridging_occurs=False,
    )


def test_contrast_reaches_omi_0() -> None:
    report = generate_report(_contrast_inputs_without_sufficiency())
    assert report.claim(ConformanceLevel.OMI_0) is ConformanceLevel.OMI_0


def test_contrast_is_honestly_blocked_at_omi_1_on_the_sufficiency_test_only() -> None:
    """The specific, honest finding this milestone reports: every OMI-1 item
    except the sufficiency campaign is already in place for the contrast
    domain (semigroup residuals, dangerous-set triage, calibration) — only
    the matched-history sufficiency test is missing, and for a stated
    reason (module docstring), not a silent gap."""
    report = generate_report(_contrast_inputs_without_sufficiency())
    with pytest.raises(ConformanceNotMet) as excinfo:
        report.claim(ConformanceLevel.OMI_1)

    unmet_names = {r.name for r in excinfo.value.unmet_requirements}
    assert unmet_names == {"sufficiency_test_run_and_reported"}


def test_contrasts_declared_erasure_inventory_is_empty() -> None:
    """Sanity check underpinning this module's docstring: unlike the
    flagship, nothing is free to exclude from contrast's tracked state
    without testing it, because no erasure operator exists here (Core
    §7.2's declared inversion)."""
    assert CONTRAST_DECLARATION.erasure_inventory == ()
