"""Class B machinery: driver/tail separation, tail-index transfer, the
correlation-length-driven dimensional reduction of the weakest-link count,
rare-event sampling, and the four-rung validation ladder.

Cites Core §3.6 (Class A/B; tail-index transfer; dimensional reduction) and
Spec §4 in full: §4.1 the failure-driver object, §4.2 driver/tail separation,
§4.3 tail transfer (Proposition 4.1: ``ξ_D = β·ξ_a``), §4.4 volume scaling
and dimensional reduction (Proposition 4.2), §4.5 rare-event sampling, §4.6
the validation ladder. Every formula in Spec §4 is fully derived (SPEC); what
this module declares are the numerical conventions Spec leaves as a stated
range or an unnamed estimator — the join threshold, the tail-index
estimator, the correlation-length crossing convention and its error bar, and
the subset-simulation proposal — all fixed by ADR-027 (docs/DECISIONS.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy import stats

from omi.state import FloatArray


def tail_index_transfer(xi_a: float, beta: float) -> float:
    """``ξ_D = β·ξ_a`` (Spec §4.3, boxed result of Proposition 4.1): the
    driver's tail shape is the measured defect-population tail shape,
    rescaled by the physics map's exponent — the generative model is never
    asked to extrapolate."""
    return beta * xi_a


def estimate_tail_index_hill(samples: FloatArray, top_fraction: float = 0.1) -> float:
    """The Hill (1975) estimator of a regularly-varying tail's Pareto shape
    ``ξ_a`` from i.i.d. samples (Spec §4.3 requires a "measured" tail index;
    ADR-027 declares Hill, over the top ``top_fraction`` order statistics,
    as the default estimator for exactly the regularly-varying tail class
    Proposition 4.1 assumes).
    """
    if not (0.0 < top_fraction < 1.0):
        raise ValueError("top_fraction must be in (0, 1)")
    sorted_desc = np.sort(samples)[::-1]
    n = sorted_desc.shape[0]
    k = max(2, int(np.ceil(top_fraction * n)))
    top = sorted_desc[:k]
    threshold = sorted_desc[k]
    alpha_hat = k / np.sum(np.log(top / threshold))
    return float(1.0 / alpha_hat)


@dataclass(frozen=True)
class JoinDiagnostics:
    """The threshold-stability diagnostics Spec §4.2 requires: the join
    threshold, the quantile it sits at, how many samples lie above it, and
    the sensitivity of the resulting exceedance estimate to that choice —
    never a single cached threshold with no reported alternative (ADR-027)."""

    threshold: float
    threshold_quantile: float
    n_above_threshold: int
    sensitivity_quantiles: FloatArray
    """The alternative quantiles probed for the sensitivity check."""
    sensitivity_exceedance_probabilities: FloatArray
    """The design-point exceedance probability recomputed at each of
    :attr:`sensitivity_quantiles` — Spec §4.2 requires this span "at least a
    factor of two in exceedance probability."""


@dataclass(frozen=True)
class JoinedTailModel:
    """The driver/tail-separated distribution of Spec §4.2: below the join
    threshold, the empirical (bulk) distribution; above it, a generalised-
    Pareto tail transferred from an independently measured defect population
    via :func:`tail_index_transfer` (Spec §4.3)."""

    bulk_samples: FloatArray
    threshold: float
    tail_shape: float
    """``ξ_D`` (Spec §4.3)."""
    tail_scale: float
    """The generalised-Pareto scale of the joined tail, at :attr:`threshold`."""

    def exceedance_probability(self, d: float) -> float:
        """``P(D > d)`` (Spec §4.1's object): the empirical bulk survival
        function below :attr:`threshold`, and the transferred generalised-
        Pareto tail (peaks-over-threshold form) above it — the join Spec
        §4.2 requires, never a single model extrapolated across both
        regimes."""
        p_above_threshold = float(np.mean(self.bulk_samples > self.threshold))
        if d <= self.threshold:
            return float(np.mean(self.bulk_samples > d))
        exceedance = d - self.threshold
        if abs(self.tail_shape) < 1e-12:
            tail_survival = float(np.exp(-exceedance / self.tail_scale))
        else:
            base = 1.0 + self.tail_shape * exceedance / self.tail_scale
            if base <= 0.0:
                return 0.0
            tail_survival = float(base ** (-1.0 / self.tail_shape))
        return p_above_threshold * tail_survival


def join_driver_tail(
    bulk_samples: FloatArray,
    xi_a: float,
    beta: float,
    threshold_quantile: float = 0.95,
) -> JoinedTailModel:
    """Build the driver/tail-separated model (Spec §4.2): fit the join
    threshold at *threshold_quantile* of *bulk_samples* (ADR-027's default,
    0.95); the tail *shape* is transferred from the measured defect-
    population index (Spec §4.3, :func:`tail_index_transfer`) rather than
    fit from the same bulk samples — the generative model supplies the bulk
    only, never the tail shape. The tail *scale* has no transfer formula in
    Spec (only the shape is a rescaled invariant, Proposition 4.1), so it is
    fit by constrained maximum likelihood on the peaks-over-threshold
    exceedances with the shape held fixed at the transferred value — the
    scale is a units-carrying nuisance parameter the join must still match
    to the data at the threshold, not a free choice (ADR-027).
    """
    threshold = float(np.quantile(bulk_samples, threshold_quantile))
    tail_shape = tail_index_transfer(xi_a, beta)
    exceedances = bulk_samples[bulk_samples > threshold] - threshold
    _shape, _loc, tail_scale = stats.genpareto.fit(exceedances, f0=tail_shape, floc=0)
    return JoinedTailModel(bulk_samples, threshold, tail_shape, float(tail_scale))


def join_diagnostics(
    bulk_samples: FloatArray,
    xi_a: float,
    beta: float,
    design_point: float,
    threshold_quantile: float = 0.95,
    sensitivity_span: tuple[float, float] = (0.90, 0.975),
    n_sensitivity_points: int = 5,
) -> JoinDiagnostics:
    """The Spec §4.2 threshold-stability report: the chosen join together
    with the design-point exceedance probability recomputed at a spread of
    alternative quantiles spanning *sensitivity_span* — by default 0.90 to
    0.975, which brackets ADR-027's own default of 0.95 and Spec's stated
    90th-95th-percentile range on both sides.
    """
    quantiles = np.linspace(sensitivity_span[0], sensitivity_span[1], n_sensitivity_points)
    probabilities = np.zeros(n_sensitivity_points)
    for i, q in enumerate(quantiles):
        model = join_driver_tail(bulk_samples, xi_a, beta, float(q))
        probabilities[i] = model.exceedance_probability(design_point)

    threshold = float(np.quantile(bulk_samples, threshold_quantile))
    n_above = int(np.sum(bulk_samples > threshold))
    return JoinDiagnostics(threshold, threshold_quantile, n_above, quantiles, probabilities)


@dataclass(frozen=True)
class CorrelationLengthResult:
    """``ℓ_D`` together with its error bar and the short-domain reliability
    diagnostic Spec §4.4 requires ("biased low on short domains") — never a
    bare point estimate (ADR-027)."""

    correlation_length: float
    standard_error: float
    domain_length: float
    domain_to_correlation_ratio: float
    reliable: bool
    """``False`` when :attr:`domain_to_correlation_ratio` falls below the
    declared reliability ratio (default 10, ADR-027) — the estimate is then
    flagged as likely biased low rather than silently trusted."""


def _autocorrelation(field: FloatArray) -> FloatArray:
    centered = field - field.mean()
    n = centered.shape[0]
    full = np.correlate(centered, centered, mode="full")
    acf = full[n - 1 :]
    result: FloatArray = acf / acf[0]
    return result


def _crossing_lag(field: FloatArray) -> int:
    acf = _autocorrelation(field)
    below = np.where(acf < np.exp(-1.0))[0]
    return int(below[0]) if below.size > 0 else int(acf.shape[0] - 1)


def estimate_correlation_length(
    driver_field: FloatArray,
    spacing: float,
    n_segments: int = 8,
    reliability_ratio: float = 10.0,
) -> CorrelationLengthResult:
    """Estimate ``ℓ_D`` from the driver field's own two-point autocorrelation
    (Spec §4.4, not the structure's autocorrelation generally): the lag at
    which the empirical ACF first drops below ``1/e``, scaled by *spacing*
    (ADR-027). The error bar is a block bootstrap over *n_segments*
    non-overlapping sub-segments of the field; the domain-to-``ℓ_D`` ratio is
    always reported, since Spec's own text warns the estimate is "biased low
    on short domains" and that warning is only honest computed, not assumed.
    """
    if driver_field.ndim != 1:
        raise ValueError("estimate_correlation_length expects a 1-D driver field")
    n = driver_field.shape[0]
    domain_length = n * spacing

    lag = _crossing_lag(driver_field)
    correlation_length = lag * spacing

    segment_len = n // n_segments
    if segment_len < 4:
        raise ValueError(f"driver_field too short for {n_segments} bootstrap segments")
    segment_lengths = []
    for i in range(n_segments):
        segment = driver_field[i * segment_len : (i + 1) * segment_len]
        segment_lengths.append(_crossing_lag(segment) * spacing)
    standard_error = float(np.std(segment_lengths, ddof=1) / np.sqrt(n_segments))

    ratio = domain_length / correlation_length if correlation_length > 0 else np.inf
    return CorrelationLengthResult(
        correlation_length, standard_error, domain_length, float(ratio), ratio >= reliability_ratio
    )


def n_eff(volume: float, correlation_length: float, process_zone_thickness: float) -> float:
    """The weakest-link count, dimensionally reduced when the driver
    correlation length exceeds the process-zone thickness (Proposition 4.2,
    Spec §4.4): ``V / ℓ_D³`` in the uncorrelated/bulk regime
    (``ℓ_D ≤ t``, "no change in the size-effect exponent, only its
    intercept"), or ``(V / t) / ℓ_D²`` in the reduced, in-plane regime
    (``ℓ_D > t``) — "the size effect with respect to thickness is
    suppressed."
    """
    if correlation_length <= process_zone_thickness:
        return volume / correlation_length**3
    area = volume / process_zone_thickness
    return area / correlation_length**2


@dataclass(frozen=True)
class SubsetSimulationResult:
    """A rare-event probability estimate by subset simulation (Spec §4.5),
    with the per-level thresholds and sample cost always reported alongside
    the final estimate (CLAUDE.md §8) — never a bare number."""

    probability: float
    level_thresholds: tuple[float, ...]
    n_evaluations: int


def subset_simulation(
    evaluate: Callable[[FloatArray], FloatArray],
    target_value: float,
    rng: np.random.Generator,
    dimension: int = 1,
    n_per_level: int = 500,
    conditional_probability: float = 0.1,
    proposal_std: float = 1.0,
    max_levels: int = 20,
) -> SubsetSimulationResult:
    """Subset simulation (Au & Beck 2001; Spec §4.5) for ``P(evaluate(Z) >
    target_value)`` where ``Z`` is standard-normal in *dimension* dimensions
    (ADR-027: the standard-normal input-space convention, so *evaluate* is
    typically a Rosenblatt/probability-integral-transform composition of the
    physical generative model). Intermediate levels hold a fixed conditional
    exceedance probability (default 0.1, Spec's own worked cost example);
    each level advances its surviving seeds by one Metropolis step per
    dimension with a symmetric Gaussian proposal, accepting exactly when the
    proposal remains in the current level's exceedance region (a symmetric
    proposal about a standard-normal target needs no further correction —
    Spec's "modified Metropolis").
    """
    samples = rng.standard_normal((n_per_level, dimension))
    values = evaluate(samples)
    n_evaluations = n_per_level
    probability = 1.0
    thresholds: list[float] = []

    for _ in range(max_levels):
        level_threshold = float(np.quantile(values, 1.0 - conditional_probability))
        if level_threshold >= target_value or np.mean(values > target_value) >= conditional_probability:
            final_fraction = float(np.mean(values > target_value))
            return SubsetSimulationResult(probability * final_fraction, tuple(thresholds), n_evaluations)

        thresholds.append(level_threshold)
        seeds = samples[values > level_threshold]
        n_seeds = seeds.shape[0]
        if n_seeds == 0:
            return SubsetSimulationResult(0.0, tuple(thresholds), n_evaluations)
        probability *= conditional_probability

        chain_length = n_per_level // n_seeds
        new_samples = np.zeros((chain_length * n_seeds, dimension))
        new_values = np.zeros(chain_length * n_seeds)
        for i in range(n_seeds):
            current = seeds[i]
            current_value = float(evaluate(current[np.newaxis, :])[0])
            for step in range(chain_length):
                proposal = current + rng.normal(0.0, proposal_std, size=dimension)
                proposal_value = float(evaluate(proposal[np.newaxis, :])[0])
                acceptance_ratio = np.exp(
                    0.5 * (np.sum(current**2) - np.sum(proposal**2))
                )
                if proposal_value > level_threshold and rng.uniform() < min(1.0, acceptance_ratio):
                    current, current_value = proposal, proposal_value
                idx = i * chain_length + step
                new_samples[idx] = current
                new_values[idx] = current_value

        samples, values = new_samples, new_values
        n_evaluations += new_samples.shape[0]

    final_fraction = float(np.mean(values > target_value))
    return SubsetSimulationResult(probability * final_fraction, tuple(thresholds), n_evaluations)


def competing_risk_survival(exceedance_probabilities: Sequence[float], counts: Sequence[float]) -> float:
    """The overall no-failure (survival) probability under several
    independent defect populations (OQ-3, docs/DECISIONS.md's Open
    Questions): ``∏_p (1 - F_p)^{N_p}``, the direct extension of Spec §4.1's
    single-population weakest-link survival to competing risks.
    """
    if len(exceedance_probabilities) != len(counts):
        raise ValueError("exceedance_probabilities and counts must have the same length")
    survival = 1.0
    for p, n in zip(exceedance_probabilities, counts):
        survival *= (1.0 - p) ** n
    return survival


@dataclass(frozen=True)
class ValidationLadderResult:
    """The four-rung validation ladder (Spec §4.6), each rung a residual —
    never a pass/fail (CLAUDE.md §8, mirroring S-9.2's own reporting
    discipline) — except rung 3, which additionally carries the hard
    "void the construction" flag Spec's text requires when fractography
    fails."""

    bulk_residual: float
    """Rung 1: bulk driver distribution vs. SVE-ensemble prediction."""
    fractography_residual: float
    """Rung 3: predicted vs. observed initiating-defect descriptor."""
    voids_construction: bool
    """Rung 3's hard requirement: "where rung 3 fails... the entire
    construction is void and MUST NOT be reported as calibrated by rungs 1,
    2 and 4 passing" — set when :attr:`fractography_residual` exceeds the
    declared tolerance."""
    volume_scaling_residual: float
    """Rung 4: observed vs. predicted size-effect exponent."""


def validate_bulk_distribution(sve_samples: FloatArray, direct_measurement_samples: FloatArray) -> float:
    """Rung 1 (Spec §4.6): the two-sample Kolmogorov-Smirnov statistic
    between the generative model's SVE-ensemble bulk distribution and an
    available direct measurement — "validatable at modest n," the cheapest
    bulk check.
    """
    statistic, _p_value = stats.ks_2samp(sve_samples, direct_measurement_samples)
    return float(statistic)


def validate_psi_by_fractography(
    predicted_initiator_sizes: FloatArray,
    observed_initiator_sizes: FloatArray,
    tolerance: float,
) -> tuple[float, bool]:
    """Rung 3 (Spec §4.6): "the cheapest and most diagnostic rung," run at
    ``n ≈ 20`` — the two-sample KS statistic between the extreme-value
    model's predicted distribution over initiating-defect descriptors and
    the descriptors actually observed by post-mortem fractography. Returns
    ``(residual, voids_construction)``: when the residual exceeds
    *tolerance*, the entire construction is void per Spec's explicit
    requirement, regardless of how rungs 1, 2 and 4 read.
    """
    statistic, _p_value = stats.ks_2samp(predicted_initiator_sizes, observed_initiator_sizes)
    return float(statistic), bool(statistic > tolerance)


def validate_volume_scaling_exponent(
    volumes: FloatArray, failure_probabilities: FloatArray, predicted_exponent: float
) -> float:
    """Rung 4 (Spec §4.6): at three or more driven volumes straddling
    ``ℓ_D``, fit the observed Weibull-type size-effect exponent
    (``log(-log(1-P_f))`` linear in ``log(V)``) and return its residual
    against the exponent :func:`n_eff`'s regime predicts (1 in the bulk
    regime, or the reduced exponent of Proposition 4.2 in the thin-zone
    regime).
    """
    if volumes.shape[0] < 3:
        raise ValueError("rung 4 requires at least three driven volumes")
    log_v = np.log(volumes)
    log_neg_log_survival = np.log(-np.log(1.0 - failure_probabilities))
    observed_exponent, _intercept = np.polyfit(log_v, log_neg_log_survival, 1)
    return float(observed_exponent - predicted_exponent)
