"""Domain triage comparison (docs/ROADMAP.md M3 exit gate): "Triage
reproduces on both domains, and the contrast domain's poor observation suite
shows a materially different dangerous set."

Flagship gets two sensors (force/torque mid-chain, a coating gauge at the
end) matching its declared "rich, multi-modal" observation suite (Core
§7.1). Contrast gets exactly one (terminal voltage, at the end only) — Core
§7.2's declared inversion, "genuinely poor" — since this toy model has no
state component standing in for the third declared modality (surface
temperature) at all, which is itself an honest reflection of how thin a
"poor observation suite" can be.
"""

from __future__ import annotations

import numpy as np

from omi.observability import Observation, compute_gramian, danger_triage, default_prior_covariance, nominal_trajectory
from omi.state import Metric

from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi_domains.flagship.build import build_chain as flagship_chain
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.readouts import AggregateHardness, CoatingGauge, ForceTorqueSensor

from tests.conftest import ObservationRecorder


def test_flagship_triage_runs_end_to_end() -> None:
    rng = np.random.default_rng(0)
    ensemble = flagship_incoming(100, rng)
    metric = Metric.from_ensemble(ensemble)
    chain = flagship_chain()
    nominal = nominal_trajectory(chain, ensemble[0])

    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(metric)
    result = danger_triage(chain, nominal, 0, gramian, prior, [AggregateHardness()], sensors)

    assert len(result.directions) == ensemble.schema.size
    assert result.dangerous_set() is not None  # runs without error; may be empty


def test_contrast_triage_runs_end_to_end() -> None:
    rng = np.random.default_rng(1)
    ensemble = contrast_incoming(100, rng)
    metric = Metric.from_ensemble(ensemble)
    chain = contrast_chain(n_cycles=5, current=2.0)
    nominal = nominal_trajectory(chain, ensemble[0])

    sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=len(chain.segments)),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(metric)
    result = danger_triage(chain, nominal, 0, gramian, prior, [DendriteRisk()], sensors)

    assert len(result.directions) == ensemble.schema.size


def _unresolved_danger_fraction(chain, nominal, prior, sensors, target_readouts) -> float:  # type: ignore[no-untyped-def]
    """What fraction of the *no-information* target variance (using the bare
    prior, as if nothing were ever observed) is still sitting in directions
    the declared sensor suite leaves dangerous?

    Not a direction-count fraction: with a per-domain median split (ADR-020),
    roughly half of any domain's directions are "influential" and half
    "identifiable" *by construction*, so comparing dangerous-direction
    *counts* across two different domains compares two different medians,
    not sensing quality. Comparing variance against the common, sensor-free
    baseline (the prior) is a like-for-like measure across domains.
    """
    gramian = compute_gramian(chain, nominal, 0, sensors)
    result = danger_triage(chain, nominal, 0, gramian, prior, target_readouts, sensors)
    dangerous_variance = sum(d.danger_score for d in result.dangerous_set())

    no_sensors_gramian = compute_gramian(chain, nominal, 0, [])
    no_sensors_result = danger_triage(chain, nominal, 0, no_sensors_gramian, prior, target_readouts, [])
    total_unobserved_variance = sum(d.danger_score for d in no_sensors_result.directions)

    return dangerous_variance / total_unobserved_variance


def test_contrasts_poor_observation_suite_leaves_more_target_variance_dangerous(
    observe: ObservationRecorder,
) -> None:
    """The actual M3 exit-gate comparison: the contrast domain's poor,
    single-sensor observation suite must leave a materially larger fraction
    of its own no-sensor target variance dangerous (influential and
    unidentifiable, Spec §3.3) than the flagship's two-sensor suite does."""
    flagship_rng = np.random.default_rng(2)
    flagship_ensemble = flagship_incoming(100, flagship_rng)
    flagship_metric = Metric.from_ensemble(flagship_ensemble)
    f_chain = flagship_chain()
    f_nominal = nominal_trajectory(f_chain, flagship_ensemble[0])
    f_sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    f_prior = default_prior_covariance(flagship_metric)
    f_fraction = _unresolved_danger_fraction(f_chain, f_nominal, f_prior, f_sensors, [AggregateHardness()])

    contrast_rng = np.random.default_rng(3)
    contrast_ensemble = contrast_incoming(100, contrast_rng)
    contrast_metric = Metric.from_ensemble(contrast_ensemble)
    c_chain = contrast_chain(n_cycles=5, current=2.0)
    c_nominal = nominal_trajectory(c_chain, contrast_ensemble[0])
    c_sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=len(c_chain.segments)),
    ]
    c_prior = default_prior_covariance(contrast_metric)
    c_fraction = _unresolved_danger_fraction(c_chain, c_nominal, c_prior, c_sensors, [DendriteRisk()])

    observe("flagship_unresolved_danger_fraction", f_fraction, "< contrast_unresolved_danger_fraction")
    observe("contrast_unresolved_danger_fraction", c_fraction, "> flagship_unresolved_danger_fraction")

    print(f"\nflagship unresolved-danger fraction: {f_fraction:.3f}")
    print(f"contrast unresolved-danger fraction: {c_fraction:.3f}")

    assert c_fraction > f_fraction
