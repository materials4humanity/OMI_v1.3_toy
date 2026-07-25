"""Ensemble assimilation: EnKF forecast/analysis along a chain, an ensemble
smoother, and innovation-based drift monitoring.

Cites Core §3.8 ("the assimilation of measurements into a state estimate is
a filtering algorithm assembled from evolution and readout operators";
"innovations as a drift monitor... → Spec §10") and Spec §10 (S-10: the
innovation sequence is a sufficient statistic for model drift — the
*proposition* is SPEC, the *detection procedure* is PASS-C). ADR-024 fixes
the EnKF numerics (a standard stochastic, perturbed-observation filter, not
a framework invention), ADR-025 the ensemble-smoother construction (cross-
covariance across the same particles' recorded trajectory, reusing Spec
§3.1's "retrospective inference is the correct setting for latent-variable
identifiability"), and ADR-026 the NIS chi-squared drift-monitor convention
that instantiates S-10's proposition (docs/DECISIONS.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats

from omi.chain import Chain
from omi.readouts import FunctionalReadout
from omi.state import Ensemble, FloatArray, State

BoolArray = np.ndarray[tuple[int, ...], np.dtype[np.bool_]]


@dataclass(frozen=True)
class DataObservation:
    """One realised measurement along a chain (Spec §3.1: ``y_j = H_j(s_j) +
    η_j``): a readout standing in for ``H_j``, its noise covariance, the
    chain index it was taken at, and the actual observed value — the
    quantity :class:`~omi.observability.Observation` deliberately does not
    carry, since M3's Gramian is a design-time (pre-data) construction while
    this is a realised assimilation input (ADR-024)."""

    name: str
    readout: FunctionalReadout
    noise_covariance: FloatArray
    time_index: int
    """Which entry of a :class:`~omi.chain.Trajectory`/forecast sequence this
    observation reads (0 = the initial ensemble, i = after segment ``i - 1``),
    matching :class:`~omi.observability.Observation`'s convention."""
    value: FloatArray
    """The realised observation ``y_j`` (Spec §3.1)."""


def _ensemble_mean(ensemble: Ensemble) -> FloatArray:
    result: FloatArray = ensemble.particles.mean(axis=0)
    return result


def _ensemble_covariance(ensemble: Ensemble) -> FloatArray:
    anomalies = ensemble.particles - _ensemble_mean(ensemble)
    n = ensemble.n_particles
    result: FloatArray = (anomalies.T @ anomalies) / (n - 1)
    return result


@dataclass(frozen=True)
class AnalysisResult:
    """One EnKF analysis step (ADR-024, docs/DECISIONS.md): the updated
    ensemble plus the innovation-monitor ingredients (Spec §10 / Core §3.8's
    innovation sequence) computed once, here, rather than recomputed by
    every downstream consumer."""

    time_index: int
    analysis_ensemble: Ensemble
    forecast_mean: FloatArray
    innovation: FloatArray
    """``y_j - H_j(forecast mean)`` (Spec §10's innovation sequence)."""
    innovation_covariance: FloatArray
    """``H'_j P_j^f H'^T_j + R_j``, the linearised innovation covariance."""
    nis: float
    """Normalised innovation squared, ``d^T S^{-1} d`` (ADR-026)."""


def enkf_analysis(
    forecast: Ensemble,
    observation: DataObservation,
    rng: np.random.Generator,
) -> AnalysisResult:
    """One ensemble Kalman filter analysis update (Core §3.8; ADR-024): the
    standard stochastic, perturbed-observation EnKF, linearising the readout
    at the forecast ensemble mean (Spec §3.1's ``H'_j``, via
    :meth:`~omi.readouts.FunctionalReadout.jacobian`).
    """
    forecast_mean = _ensemble_mean(forecast)
    forecast_cov = _ensemble_covariance(forecast)
    h = observation.readout.jacobian(State(forecast.schema, forecast_mean))
    r = observation.noise_covariance
    innovation_cov = h @ forecast_cov @ h.T + r
    gain = forecast_cov @ h.T @ np.linalg.inv(innovation_cov)

    n = forecast.n_particles
    obs_dim = observation.value.shape[0]
    perturbations = rng.multivariate_normal(np.zeros(obs_dim), r, size=n)

    new_particles = np.zeros_like(forecast.particles)
    for i in range(n):
        predicted = observation.readout.evaluate(forecast[i])
        perturbed_y = observation.value + perturbations[i]
        new_particles[i] = forecast.particles[i] + gain @ (perturbed_y - predicted)
    analysis_ensemble = Ensemble(forecast.schema, new_particles)

    innovation = observation.value - observation.readout.evaluate(State(forecast.schema, forecast_mean))
    nis = float(innovation @ np.linalg.solve(innovation_cov, innovation))

    return AnalysisResult(
        observation.time_index, analysis_ensemble, forecast_mean, innovation, innovation_cov, nis
    )


@dataclass(frozen=True)
class FilterResult:
    """The full forward EnKF pass over a chain (Core §3.8; ADR-024;
    docs/ROADMAP.md M5: "EnKF along the chain"): the forecast ensemble
    recorded at every index — needed by the smoother (ADR-025) — and the
    analysis performed at every instrumented index."""

    forecast_ensembles: tuple[Ensemble, ...]
    """``forecast_ensembles[k]`` is the ensemble forecast to index ``k``,
    before any analysis at ``k`` is applied. Length ``len(chain.segments) +
    1``, same indexing as :class:`~omi.chain.Trajectory`."""
    analyses: dict[int, AnalysisResult]
    """``time_index -> AnalysisResult``, one entry per instrumented index."""

    def best_estimate(self, time_index: int) -> Ensemble:
        """The filtered (not smoothed) ensemble at *time_index*: the
        analysis ensemble if an observation was taken there, otherwise the
        forecast (Core §3.8)."""
        if time_index in self.analyses:
            return self.analyses[time_index].analysis_ensemble
        return self.forecast_ensembles[time_index]


def run_filter(
    chain: Chain,
    initial_ensemble: Ensemble,
    observations: Sequence[DataObservation],
    rng: np.random.Generator,
    process_noise: Sequence[FloatArray] | None = None,
) -> FilterResult:
    """Roll an ensemble through *chain*, applying an EnKF analysis (ADR-024)
    at every instrumented index — Core §3.8's "filtering algorithm assembled
    from evolution and readout operators," docs/ROADMAP.md M5's "EnKF along
    the chain."

    *process_noise*, if given, is ``process_noise[i]`` added i.i.d. per
    particle after segment ``i``'s forecast; the default (``None``) adds
    none, since Spec specifies no ``Q`` and ADR-024 declines to invent one.
    """
    by_index: dict[int, list[DataObservation]] = {}
    for obs in observations:
        by_index.setdefault(obs.time_index, []).append(obs)

    forecast_ensembles: list[Ensemble] = []
    analyses: dict[int, AnalysisResult] = {}

    current = initial_ensemble
    for k in range(len(chain.segments) + 1):
        if k > 0:
            segment = chain.segments[k - 1]
            current = segment.operator.lift(current, segment.control)
            if process_noise is not None:
                noise = rng.multivariate_normal(
                    np.zeros(current.schema.size), process_noise[k - 1], size=current.n_particles
                )
                current = Ensemble(current.schema, current.particles + noise)
        forecast_ensembles.append(current)
        for obs in by_index.get(k, []):
            result = enkf_analysis(current, obs, rng)
            analyses[k] = result
            current = result.analysis_ensemble

    return FilterResult(tuple(forecast_ensembles), analyses)


def smooth(
    filter_result: FilterResult,
    observations: Sequence[DataObservation],
) -> dict[int, Ensemble]:
    """The ensemble smoother (Core §3.8: "retrospective inference... is
    therefore the correct setting for latent-variable identifiability";
    ADR-025): for each index ``k``, correct the filtered ensemble using
    every observation at a later index ``j > k``, via the empirical cross-
    covariance between the same particles' recorded ``k``- and ``j``-indexed
    values — no Jacobian chain, no re-linearisation of dynamics.
    """
    by_index: dict[int, list[DataObservation]] = {}
    for obs in observations:
        by_index.setdefault(obs.time_index, []).append(obs)

    n_indices = len(filter_result.forecast_ensembles)
    smoothed: dict[int, Ensemble] = {}

    for k in range(n_indices):
        current = filter_result.best_estimate(k)
        for j in range(k + 1, n_indices):
            for obs in by_index.get(j, []):
                forecast_j = filter_result.forecast_ensembles[j]
                h = obs.readout.jacobian(State(forecast_j.schema, _ensemble_mean(forecast_j)))
                r = obs.noise_covariance
                predicted_j = obs.readout(forecast_j)

                anomalies_k = current.particles - _ensemble_mean(current)
                anomalies_pred = predicted_j - predicted_j.mean(axis=0)
                n = current.n_particles
                cross_cov = (anomalies_k.T @ anomalies_pred) / (n - 1)
                forecast_cov_j = _ensemble_covariance(forecast_j)
                innovation_cov = h @ forecast_cov_j @ h.T + r
                gain = cross_cov @ np.linalg.inv(innovation_cov)

                new_particles = np.zeros_like(current.particles)
                for i in range(n):
                    new_particles[i] = current.particles[i] + gain @ (obs.value - predicted_j[i])
                current = Ensemble(current.schema, new_particles)
        smoothed[k] = current

    return smoothed


@dataclass(frozen=True)
class DriftReport:
    """The NIS chi-squared consistency test (ADR-026) over an innovation
    sequence: Spec §10's proposition (S-10 — "the innovation sequence is a
    sufficient statistic for model drift") made executable, always reported
    alongside the raw sequence and the control limits used, never as a bare
    boolean (CLAUDE.md §8)."""

    nis_sequence: FloatArray
    """One normalised-innovation-squared value per analysis, in time order
    (Spec §10)."""
    dof: int
    """Observation dimension per step (assumed constant across the window)."""
    window: int
    windowed_mean: FloatArray
    """Rolling mean of :attr:`nis_sequence` over :attr:`window` steps."""
    lower_limit: float
    upper_limit: float
    drift_detected: BoolArray
    """Boolean array, same length as :attr:`windowed_mean`: ``True`` where
    the windowed mean exits ``[lower_limit, upper_limit]``."""

    @property
    def any_drift(self) -> bool:
        """Whether the monitor tripped anywhere in the sequence (Spec §10)."""
        return bool(np.any(self.drift_detected))


def innovation_drift_monitor(
    analyses: Sequence[AnalysisResult],
    window: int = 10,
    confidence: float = 0.95,
) -> DriftReport:
    """The declared drift-detection procedure instantiating S-10's
    proposition (Spec §10; Core §3.8; ADR-026, docs/DECISIONS.md): under a
    correctly specified model each analysis's normalised innovation squared
    is chi-squared distributed with ``dof`` degrees of freedom, so a rolling
    window mean that exits the corresponding chi-squared control limits is
    evidence of drift.
    """
    if not analyses:
        raise ValueError("innovation_drift_monitor requires at least one analysis")
    dof = analyses[0].innovation.shape[0]
    nis_sequence: FloatArray = np.array([a.nis for a in analyses])

    alpha = 1 - confidence
    lower_limit = float(stats.chi2.ppf(alpha / 2, df=window * dof) / window)
    upper_limit = float(stats.chi2.ppf(1 - alpha / 2, df=window * dof) / window)

    n = len(nis_sequence)
    if n < window:
        windowed_mean: FloatArray = np.array([])
        drift_detected: BoolArray = np.array([], dtype=bool)
    else:
        windowed_mean = np.array(
            [nis_sequence[i - window + 1 : i + 1].mean() for i in range(window - 1, n)]
        )
        drift_detected = (windowed_mean < lower_limit) | (windowed_mean > upper_limit)

    return DriftReport(nis_sequence, dof, window, windowed_mean, lower_limit, upper_limit, drift_detected)
