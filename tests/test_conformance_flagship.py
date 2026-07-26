"""Flagship OMI-1 conformance demonstration: docs/ROADMAP.md M7 exit gate
— "OMI-1 for the flagship."

Every diagnostic here is produced by the real flagship chain
(`omi_domains.flagship`), not a synthetic toy schema: the semigroup residual
on the real relaxation operators, a matched-history sufficiency campaign on
the real incoming ensemble and `AggregateHardness` readout, the M3 domain
triage (`tests/test_domain_triage.py`'s own flagship setup), and calibration
diagnostics from the chain's own aleatoric-uncertainty population.
"""

from __future__ import annotations

import numpy as np

from omi.chain import Chain
from omi.conformance import (
    CalibrationReport,
    ConformanceInputs,
    ConformanceLevel,
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
    sensitivity_operator,
)
from omi.operators import Control, semigroup_residual
from omi.state import Ensemble, FloatArray, Metric, Slot
from omi.sufficiency import DeficitResult, sufficiency_deficit

from omi_domains.flagship.build import build_chain, build_incoming_ensemble
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship.readouts import AggregateHardness, CoatingGauge, ForceTorqueSensor
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

from tests.conftest import ObservationRecorder

MEASUREMENT_NOISE_STD = 0.5
"""A hardness tester's repeat noise (Spec §1.2's ``σ²_rep``) — small
relative to the ~100-unit hardness scale, standing in for real repeat-trial
variability since this is an analytic-operator toy chain, not an
instrumented line."""


def _semigroup_residuals(rng: np.random.Generator) -> FloatArray:
    incoming = build_incoming_ensemble(1, rng)
    state = incoming[0]
    residuals: list[float] = []
    heating_control = Control(0.0, 1.0, lambda t: np.array([8.0]))
    transfer_control = Control(0.0, 0.3, lambda t: np.array([1.0]))
    for t_mid in (0.2, 0.5, 0.8):
        residuals.append(semigroup_residual(HEATING_AND_SOAK, state, heating_control, t_mid))
    for t_mid in (0.1, 0.15, 0.25):
        residuals.append(semigroup_residual(TRANSFER, state, transfer_control, t_mid))
    return np.array(residuals)


def _matched_pair_sufficiency_campaign(rng: np.random.Generator) -> DeficitResult:
    """A real matched-history sufficiency campaign (Spec §1.2) on the
    flagship chain: pairs share every *surviving* component
    (prior_grain_size, inclusion_content, accumulated_hardening,
    levelling_field, coating_thickness) but differ in the two components
    ``heating_and_soak`` erases (prior_deformation, substructure_density).

    Cites Core §3.9's error-control dichotomy directly: `AggregateHardness`
    depends only on surviving components (`omi_domains/flagship/readouts.py`),
    and the flagship's relaxation operators have no cross-component coupling
    (`omi_domains/flagship/operators.py`), so the erased components have
    exactly zero downstream influence on this readout — the deficit this
    campaign measures is expected, honestly, to be at noise level, not
    assumed to be so.
    """
    n_pairs = 2000
    chain = build_chain()
    hardness = AggregateHardness()

    matched = build_incoming_ensemble(n_pairs, rng)
    unmatched_a = build_incoming_ensemble(n_pairs, rng)
    unmatched_b = build_incoming_ensemble(n_pairs, rng)

    pd_slice = FLAGSHIP_SCHEMA.slice_for(Slot.M, "prior_deformation")
    sd_slice = FLAGSHIP_SCHEMA.slice_for(Slot.Z, "substructure_density")

    particles_a = matched.particles.copy()
    particles_b = matched.particles.copy()
    particles_a[:, pd_slice] = unmatched_a.particles[:, pd_slice]
    particles_a[:, sd_slice] = unmatched_a.particles[:, sd_slice]
    particles_b[:, pd_slice] = unmatched_b.particles[:, pd_slice]
    particles_b[:, sd_slice] = unmatched_b.particles[:, sd_slice]

    ensemble_a = chain.rollout(Ensemble(FLAGSHIP_SCHEMA, particles_a)).final
    ensemble_b = chain.rollout(Ensemble(FLAGSHIP_SCHEMA, particles_b)).final

    response_a = hardness(ensemble_a)[:, 0] + rng.normal(0.0, MEASUREMENT_NOISE_STD, n_pairs)
    response_b = hardness(ensemble_b)[:, 0] + rng.normal(0.0, MEASUREMENT_NOISE_STD, n_pairs)

    matched_names = [
        (Slot.M, "prior_grain_size"),
        (Slot.Z, "inclusion_content"),
        (Slot.Z, "accumulated_hardening"),
        (Slot.NU, "levelling_field"),
        (Slot.GAMMA, "coating_thickness"),
    ]
    matched_indices = [FLAGSHIP_SCHEMA.slice_for(slot, name).start for slot, name in matched_names]
    matched_component_diffs = particles_a[:, matched_indices] - particles_b[:, matched_indices]

    nominal = nominal_trajectory(chain, Ensemble(FLAGSHIP_SCHEMA, particles_a[:1])[0])
    full_sensitivity = sensitivity_operator(chain, nominal, 0, [hardness])
    response_jacobian = full_sensitivity[0, matched_indices]

    repeated_condition = Ensemble(FLAGSHIP_SCHEMA, np.repeat(particles_a[:1], 1000, axis=0))
    repeated_final = chain.rollout(repeated_condition).final
    repeated_measurements = hardness(repeated_final)[:, 0] + rng.normal(0.0, MEASUREMENT_NOISE_STD, 1000)
    repeat_variance = float(np.var(repeated_measurements))

    return sufficiency_deficit(response_a, response_b, matched_component_diffs, response_jacobian, repeat_variance)


def _flagship_triage(rng: np.random.Generator) -> TriageResult:
    ensemble = build_incoming_ensemble(100, rng)
    chain = build_chain()
    nominal = nominal_trajectory(chain, ensemble[0])
    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    return danger_triage(chain, nominal, 0, gramian, prior, [AggregateHardness()], sensors)


def _flagship_calibration(rng: np.random.Generator) -> CalibrationReport:
    """Predictive ensembles from the chain's own aleatoric spread, each
    checked against one freshly drawn 'true' realisation from the same
    distribution — a positive control on real chain physics, not synthetic
    mock data."""
    n_cases = 300
    n_ensemble = 100
    chain = build_chain()
    hardness = AggregateHardness()
    predictive = np.zeros((n_cases, n_ensemble))
    observations = np.zeros(n_cases)
    for i in range(n_cases):
        ensemble = build_incoming_ensemble(n_ensemble + 1, rng)
        final = chain.rollout(ensemble).final
        values = hardness(final)[:, 0]
        predictive[i] = values[:-1]
        observations[i] = values[-1]
    return calibration_report(predictive, observations, nominal_coverage_level=0.9)


def _flagship_rollout_curve(rng: np.random.Generator, metric: Metric, chain: Chain) -> FloatArray:
    incoming = build_incoming_ensemble(1, rng)
    baseline = incoming[0]
    slot, name, _dim = FLAGSHIP_SCHEMA.components[0]
    perturbed = baseline.with_component(slot, name, baseline.get(slot, name) + 5 * metric.scale[0])
    return rollout_length_error_curve(chain, baseline, perturbed, metric)


def test_flagship_matched_pair_deficit_is_at_noise_level(observe: ObservationRecorder) -> None:
    """Sanity check on the campaign itself before it feeds a conformance
    claim: the deficit must clamp to (near) zero, and for the honestly
    stated reason (no cross-component coupling reaches AggregateHardness
    from the erased components), not because the campaign is degenerate."""
    rng = np.random.default_rng(20260726)
    result = _matched_pair_sufficiency_campaign(rng)
    observe("deficit_squared", result.deficit_squared, "< repeat_variance_term")
    observe("repeat_variance_term", result.repeat_variance_term, "> deficit_squared")
    assert result.deficit_squared < result.repeat_variance_term


def test_flagship_reaches_omi_1() -> None:
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()

    inputs = ConformanceInputs(
        declaration=FLAGSHIP_DECLARATION,
        metric=metric,
        rollout_error_curve=_flagship_rollout_curve(np.random.default_rng(1), metric, chain),
        semigroup_residuals=_semigroup_residuals(np.random.default_rng(2)),
        sufficiency_result=_matched_pair_sufficiency_campaign(np.random.default_rng(3)),
        triage_result=_flagship_triage(np.random.default_rng(4)),
        calibration=_flagship_calibration(np.random.default_rng(5)),
        scale_bridging_occurs=False,
    )
    report = generate_report(inputs)

    assert report.claim(ConformanceLevel.OMI_1) is ConformanceLevel.OMI_1
    assert report.unmet(ConformanceLevel.OMI_1) == ()


def test_flagship_does_not_reach_omi_2() -> None:
    """OMI-2 needs reachability certificates (inverse.py, M9) and a
    prospective inverse-design trial (M9) — neither exists yet."""
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()

    inputs = ConformanceInputs(
        declaration=FLAGSHIP_DECLARATION,
        metric=metric,
        rollout_error_curve=_flagship_rollout_curve(np.random.default_rng(1), metric, chain),
        semigroup_residuals=_semigroup_residuals(np.random.default_rng(2)),
        sufficiency_result=_matched_pair_sufficiency_campaign(np.random.default_rng(3)),
        triage_result=_flagship_triage(np.random.default_rng(4)),
        calibration=_flagship_calibration(np.random.default_rng(5)),
    )
    report = generate_report(inputs)
    unmet = {r.name for r in report.unmet(ConformanceLevel.OMI_2)}
    assert "reachability_certificates_reported" in unmet
    assert "prospective_inverse_design_trial_reported" in unmet
