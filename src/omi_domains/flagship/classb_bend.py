"""The flagship's Class B campaign for `BendAngle` (Core §7.1, Tier I½;
ADR-035, docs/DECISIONS.md): wires `omi.classb`'s driver/tail separation,
correlation-length estimation, dimensional reduction, and validation ladder
to a real driver field, rather than the hand-supplied numbers every prior
milestone used (`docs/COVERAGE.md`, C-3.6 / S-4.1 / S-4.2 / S-4.4 / S-4.6;
`build/REVIEW-EXTRACT.md` §2).

Item 4b (Core §4), declared: the **defect population** is
``inclusion_content`` — independently measured, Pareto-tailed
(:data:`XI_A_INCLUSION`, :data:`X_M_INCLUSION`), spatially correlated along
one axis (many potential initiation sites); the **driver field** is
`BendAngle`'s outer-fibre response as inclusion content varies site to site
under one fixed reference geometry; the **physics map** Ψ is linear (the
constitutive operator's own response formula is affine in
``inclusion_content``), so its Spec §4.3 exponent is ``BETA = 1.0`` — read
directly off :class:`~omi_domains.flagship.readouts.HardnessConstitutiveOperator`,
not invented here or in `omi.classb`.

**Rung 4 (Spec §4.6), bulk regime, is empirical, not closed-form** (a Phase
2 review found the original closed-form version circular, V1.4-EDITS.md
E-12): :func:`_empirical_bulk_failure_probabilities` draws ``round(N_eff)``
i.i.d. sub-volume defect samples per trial, runs each through the real
`BendAngle`, takes the per-trial maximum driver value, thresholds, and
repeats over many trials — the observed exponent this produces is
independent of the exponent :func:`~omi.classb.n_eff` predicts, so a
residual now reflects genuine sampling agreement rather than
floating-point identity. The per-site exceedance probability ``p0``
(:attr:`BendCampaignResult.p0`) is separately *model-based*: fit once, at
one reference geometry, from :func:`~omi.classb.join_driver_tail`'s GPD
tail. It is **not** calibrated against the empirical bulk sampling above,
and the two are not reconciled — :attr:`BendCampaignResult.bulk_p0_implied`
reports what the empirical trials themselves imply per thickness (by
inverting `1 - (1-p0)**N_eff`), for comparison only.

The thin regime remains closed-form (`_failure_probabilities`, `p0` held
fixed while :func:`~omi.classb.n_eff`'s own formula is evaluated at each
swept thickness): the algebraic identity behind its thickness-independence
is exactly what
`tests/test_flagship_classb_bend.py`'s thin-regime test now marks as
blocked rather than validated (V1.4-EDITS.md E-14) — see that test for why
no amount of resampling here would make the reduction emergent without
Core §2.5's body-indexed state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from omi.classb import (
    CorrelationLengthResult,
    JoinDiagnostics,
    JoinedTailModel,
    ValidationLadderResult,
    estimate_correlation_length,
    estimate_tail_index_hill,
    join_diagnostics,
    join_driver_tail,
    n_eff,
    tail_index_transfer,
    validate_bulk_distribution,
    validate_psi_by_fractography,
    validate_volume_scaling_exponent,
)
from omi.readouts import Type2Geometry
from omi.state import FloatArray, Slot, State

from omi_domains.flagship.readouts import BendAngle, ExtractHardness
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

XI_A_INCLUSION = 0.4
"""The defect population's own Pareto shape (Spec §4.3's ``ξ_a``) — a
moderately heavy tail, declared once here (Core §4 item 4b), not inside
`omi.classb`."""
X_M_INCLUSION = 0.5
"""Pareto scale (minimum inclusion content) — matches the same order of
magnitude as `omi_domains.flagship.build.build_incoming_ensemble`'s
``inclusion_content`` prior, so this campaign's defect population is a
heavier-tailed refinement of that prior, not an unrelated invention."""
BETA = 1.0
"""Spec §4.3's physics-map exponent Ψ: read directly off
:class:`~omi_domains.flagship.readouts.HardnessConstitutiveOperator`'s
response formula, which is affine (hence exactly linear, β=1) in
``inclusion_content`` for fixed geometry and hardening history."""

REFERENCE_THICKNESS = 1.0
REFERENCE_CURVATURE = 2.0
"""The one geometry `p0` (the per-site exceedance probability) is measured
at (see module docstring) — held fixed while thickness alone varies in the
`n_eff` sweep."""

N_SITES = 500
SITE_SPACING = 0.1
CORRELATION_KERNEL_SIGMA_INDEX = 10.0
"""Gaussian-smoothing bandwidth (in site-index units) for the generative
spatial field (see :func:`_correlated_pareto_field`): for a Gaussian kernel
of index-space standard deviation σ, the smoothed field's own autocorrelation
is itself approximately Gaussian, crossing ``1/e`` at lag ≈ 2σ — so this
targets a generative correlation length near ``2 * 10 * SITE_SPACING = 2.0``,
in the same length units as thickness. `estimate_correlation_length` is run
on the resulting field to get the value this campaign actually uses; the
generative target above is context for why the field looks the way it does,
not a value handed to `n_eff` directly.
"""

DRIVER_THRESHOLD = 111.0
"""``D_c`` (Spec §4.1), declared for this campaign specifically (overriding
:attr:`~omi_domains.flagship.readouts.BendAngle.driver_threshold`'s
single-state default): calibrated so that, under
:data:`PEAK_STRAIN_REFERENCE`, only the upper tail of the Pareto-tailed
defect population (roughly its top 2%, not its bulk) drives a site past
threshold — the rare, weakest-link regime Class B concerns, rather than a
threshold most specimens fail outright or none ever reach."""

FIXED_FOOTPRINT_AREA = 25.0
"""Held fixed while thickness varies, so ``volume = FIXED_FOOTPRINT_AREA *
thickness`` isolates the effect of thickness (relative to the estimated
correlation length) on the weakest-link count — the experiment
:func:`n_eff`'s two-regime formula is stated for."""

N_EMPIRICAL_TRIALS_BULK = 1500
"""Monte Carlo trial count for :func:`_empirical_bulk_failure_probabilities`
(V1.4-EDITS.md E-12). Chosen for a standard error on each empirical
``P_fail`` of roughly 1-1.5 percentage points (``sqrt(p(1-p)/n)`` at the
observed ``p`` ~ 0.5-0.9) at a runtime the test suite can absorb — not
tuned to produce any particular residual."""


def _nominal_state(inclusion_content: float) -> State:
    """A synthetic flagship state varying only ``inclusion_content``; every
    other component is fixed at a nominal value irrelevant to
    :class:`~omi_domains.flagship.readouts.HardnessConstitutiveOperator`
    (which reads only ``inclusion_content``, ``prior_grain_size`` and
    ``accumulated_hardening``)."""
    values = np.zeros(FLAGSHIP_SCHEMA.size)
    values[FLAGSHIP_SCHEMA.slice_for(Slot.M, "prior_grain_size")] = 20.0
    values[FLAGSHIP_SCHEMA.slice_for(Slot.Z, "inclusion_content")] = inclusion_content
    values[FLAGSHIP_SCHEMA.slice_for(Slot.Z, "accumulated_hardening")] = 0.0
    return State(FLAGSHIP_SCHEMA, values)


def _correlated_pareto_field(n_sites: int, sigma_index: float, rng: np.random.Generator) -> FloatArray:
    """A spatially-correlated, Pareto-marginal ``inclusion_content`` field
    (item 4b's defect population): white noise convolved with a Gaussian
    kernel (giving the field genuine, non-i.i.d. spatial correlation), then
    rank-transformed to the Pareto marginal via the probability-integral
    transform (the same construction `tests/test_classb_subset_simulation.py`
    uses, reused here for a real domain rather than a synthetic oracle).
    """
    pad = int(np.ceil(6 * sigma_index))
    white = rng.normal(size=n_sites + 2 * pad)
    kernel_radius = int(np.ceil(3 * sigma_index))
    x = np.arange(-kernel_radius, kernel_radius + 1)
    kernel = np.exp(-0.5 * (x / sigma_index) ** 2)
    kernel = kernel / np.sqrt(np.sum(kernel**2))
    smoothed = np.convolve(white, kernel, mode="same")
    trimmed = smoothed[pad : pad + n_sites]
    standardised = (trimmed - trimmed.mean()) / trimmed.std()
    u = stats.norm.cdf(standardised)
    u = np.clip(u, 1e-12, 1.0 - 1e-12)
    # Inverse Pareto CDF in terms of the GPD shape xi_a (alpha_a = 1/xi_a,
    # Spec §4.3's own relation, docstring of tests/oracles/known_tail.py):
    # x = x_m * (1-u)**(-1/alpha_a) = x_m * (1-u)**(-xi_a).
    inclusion: FloatArray = X_M_INCLUSION * (1.0 - u) ** (-XI_A_INCLUSION)
    return inclusion


def driver_field_for_sites(
    inclusion_samples: FloatArray, thickness: float, curvature: float
) -> FloatArray:
    """Run :class:`~omi_domains.flagship.readouts.BendAngle` — the real,
    production Type-2/Class-B readout, not a shortcut re-implementation of
    its arithmetic — once per site, varying only ``inclusion_content``.
    Returns the outer-fibre response at each site: Spec §4.1's failure
    driver field, genuinely spatially varying because the underlying defect
    population is.
    """
    readout = BendAngle(driver_threshold=DRIVER_THRESHOLD)
    geometry = Type2Geometry(thickness=thickness, curvature=curvature)
    driver_field = np.empty(inclusion_samples.shape[0])
    for i, inclusion in enumerate(inclusion_samples):
        state = _nominal_state(float(inclusion))
        operator = ExtractHardness()(state)
        response, _process_zone_volume = readout.evaluate(operator, geometry)
        driver_field[i] = response[0]
    return driver_field


@dataclass(frozen=True)
class BendCampaignResult:
    """Everything :func:`run_bend_classb_campaign` measured, so a caller (or
    a test) can inspect the intermediate quantities rather than only a
    verdict (CLAUDE.md §8)."""

    inclusion_samples: FloatArray
    driver_field: FloatArray
    correlation_length: CorrelationLengthResult
    xi_a_hat: float
    xi_d_hat: float
    joined_tail_model: JoinedTailModel
    join_diagnostics: JoinDiagnostics
    p0: float
    """Model-based (fitted GPD tail), not calibrated against the empirical
    bulk sampling below — see :attr:`bulk_p0_implied` for the comparison,
    reported rather than reconciled."""
    bulk_volumes: FloatArray
    bulk_failure_probabilities: FloatArray
    """Empirical (Monte Carlo), not closed-form — see module docstring,
    V1.4-EDITS.md E-12."""
    bulk_n_eff: FloatArray
    bulk_p0_implied: FloatArray
    """Per-thickness per-sub-volume exceedance probability implied by
    :attr:`bulk_failure_probabilities` and :attr:`bulk_n_eff` — compare
    against :attr:`p0`, do not use to adjust it."""
    bulk_volume_scaling_residual: float
    thin_volumes: FloatArray
    thin_failure_probabilities: FloatArray
    thin_volume_scaling_residual: float
    validation_ladder: ValidationLadderResult


def bulk_regime_thicknesses(ell_d: float) -> FloatArray:
    """Three thicknesses at or above the estimated correlation length —
    :func:`~omi.classb.n_eff`'s bulk/volumetric regime."""
    return ell_d * np.array([1.25, 2.0, 4.0])


def thin_regime_thicknesses(ell_d: float) -> FloatArray:
    """Three thicknesses below the estimated correlation length —
    :func:`~omi.classb.n_eff`'s reduced, in-plane regime."""
    return ell_d * np.array([0.15, 0.3, 0.5])


def _failure_probabilities(thicknesses: FloatArray, ell_d: float, p0: float) -> tuple[FloatArray, FloatArray]:
    """Closed-form: ``1 - (1-p0)**n_eff(...)``. Used only for the thin
    regime (see module docstring on why the bulk regime no longer uses
    this — V1.4-EDITS.md E-12)."""
    volumes = FIXED_FOOTPRINT_AREA * thicknesses
    counts = np.array([n_eff(float(v), ell_d, float(t)) for v, t in zip(volumes, thicknesses)])
    failure_probabilities = 1.0 - (1.0 - p0) ** counts
    return volumes, failure_probabilities


def _empirical_bulk_failure_probabilities(
    thicknesses: FloatArray, ell_d: float, rng: np.random.Generator, n_trials: int = N_EMPIRICAL_TRIALS_BULK
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Rung 4 (Spec §4.6), bulk regime, by direct Monte Carlo simulation of
    the weakest-link construction (V1.4-EDITS.md E-12) — never the closed
    form fed back into itself. At each thickness: ``n_sub = round(n_eff(...))``
    i.i.d. Pareto-marginal ``inclusion_content`` draws stand in for that many
    statistically independent sub-volumes; the real `BendAngle` is run on
    each (via :func:`driver_field_for_sites`); the trial "fails" if the
    maximum of the ``n_sub`` responses exceeds :data:`DRIVER_THRESHOLD`.
    Repeated *n_trials* times per thickness; the failure fraction is the
    empirical ``P_fail``.

    Returns ``(volumes, empirical_failure_probabilities, n_eff_counts,
    p0_implied)`` — the last is each thickness's per-sub-volume exceedance
    probability *implied* by the empirical result
    (``1 - (1 - Pf)**(1/n_eff)``), reported for comparison against the
    separately fitted, model-based ``p0`` (:attr:`BendCampaignResult.p0`)
    and never used to adjust it.
    """
    volumes = FIXED_FOOTPRINT_AREA * thicknesses
    counts = np.array([n_eff(float(v), ell_d, float(t)) for v, t in zip(volumes, thicknesses)])
    failure_probabilities = np.empty(thicknesses.shape[0])
    for i, count in enumerate(counts):
        n_sub = max(1, int(round(float(count))))
        failures = 0
        for _ in range(n_trials):
            u = rng.uniform(size=n_sub)
            inclusion = X_M_INCLUSION * (1.0 - u) ** (-XI_A_INCLUSION)
            driver = driver_field_for_sites(inclusion, REFERENCE_THICKNESS, REFERENCE_CURVATURE)
            if driver.max() > DRIVER_THRESHOLD:
                failures += 1
        failure_probabilities[i] = failures / n_trials
    p0_implied = 1.0 - (1.0 - failure_probabilities) ** (1.0 / counts)
    return volumes, failure_probabilities, counts, p0_implied


def run_bend_classb_campaign(rng: np.random.Generator) -> BendCampaignResult:
    """The full wiring (Phase 2.3): a real driver field through
    `join_driver_tail`/`join_diagnostics`, `estimate_correlation_length`,
    `n_eff`'s dimensional reduction validated across six thicknesses
    straddling the estimated correlation length (three per regime, per
    :func:`bulk_regime_thicknesses` / :func:`thin_regime_thicknesses`), and
    validation-ladder rungs 1, 3 and 4.
    """
    inclusion_samples = _correlated_pareto_field(N_SITES, CORRELATION_KERNEL_SIGMA_INDEX, rng)
    driver_field = driver_field_for_sites(inclusion_samples, REFERENCE_THICKNESS, REFERENCE_CURVATURE)

    correlation_length = estimate_correlation_length(driver_field, SITE_SPACING)
    ell_d = correlation_length.correlation_length

    xi_a_hat = estimate_tail_index_hill(inclusion_samples, top_fraction=0.1)
    xi_d_hat = tail_index_transfer(xi_a_hat, BETA)

    joined_model = join_driver_tail(driver_field, xi_a_hat, BETA, threshold_quantile=0.9)
    diagnostics = join_diagnostics(
        driver_field, xi_a_hat, BETA, design_point=DRIVER_THRESHOLD, threshold_quantile=0.9
    )
    p0 = joined_model.exceedance_probability(DRIVER_THRESHOLD)

    bulk_thicknesses = bulk_regime_thicknesses(ell_d)
    thin_thicknesses = thin_regime_thicknesses(ell_d)
    bulk_volumes, bulk_pf, bulk_n_eff_counts, bulk_p0_implied = _empirical_bulk_failure_probabilities(
        bulk_thicknesses, ell_d, rng
    )
    thin_volumes, thin_pf = _failure_probabilities(thin_thicknesses, ell_d, p0)
    bulk_residual = validate_volume_scaling_exponent(bulk_volumes, bulk_pf, predicted_exponent=1.0)
    thin_residual = validate_volume_scaling_exponent(thin_volumes, thin_pf, predicted_exponent=0.0)

    # Rung 1: an independent "direct measurement" draw of the same
    # generative model, standing in for a second, independently obtained
    # bulk sample (Spec §4.6 rung 1).
    direct_measurement = _correlated_pareto_field(N_SITES, CORRELATION_KERNEL_SIGMA_INDEX, rng)
    direct_driver = driver_field_for_sites(direct_measurement, REFERENCE_THICKNESS, REFERENCE_CURVATURE)
    bulk_residual_rung1 = validate_bulk_distribution(driver_field, direct_driver)

    # Rung 3 (fractography, "simulable here since you know which defect
    # initiated failure"): the fitted tail model's predicted exceedances
    # over threshold vs. independently simulated specimens' own maxima.
    predicted_initiator_sizes = DRIVER_THRESHOLD + stats.genpareto.rvs(
        c=joined_model.tail_shape,
        scale=joined_model.tail_scale,
        size=500,
        random_state=rng,
    )
    n_trials, n_sites_per_trial = 30, 100
    observed_initiator_sizes = np.empty(n_trials)
    for trial in range(n_trials):
        trial_samples = _correlated_pareto_field(n_sites_per_trial, CORRELATION_KERNEL_SIGMA_INDEX / 5.0, rng)
        trial_driver = driver_field_for_sites(trial_samples, REFERENCE_THICKNESS, REFERENCE_CURVATURE)
        observed_initiator_sizes[trial] = trial_driver.max()
    fractography_residual, voids_construction = validate_psi_by_fractography(
        predicted_initiator_sizes, observed_initiator_sizes, tolerance=0.35
    )

    # volume_scaling_residual mixes two different epistemic kinds: bulk_residual
    # is a genuine empirical-vs-predicted comparison (E-12); thin_residual is
    # an arithmetic identity of n_eff's own formula against itself (E-14,
    # `tests/test_flagship_classb_bend.py`'s thin-regime test is blocked, not
    # asserted, for exactly this reason). Reporting the worse of the two is a
    # documented, not a hidden, choice — Spec §4.6 does not say how to combine
    # a multi-regime rung 4 into one number.
    ladder = ValidationLadderResult(
        bulk_residual=bulk_residual_rung1,
        fractography_residual=fractography_residual,
        voids_construction=voids_construction,
        volume_scaling_residual=max(abs(bulk_residual), abs(thin_residual)),
    )

    return BendCampaignResult(
        inclusion_samples=inclusion_samples,
        driver_field=driver_field,
        correlation_length=correlation_length,
        xi_a_hat=xi_a_hat,
        xi_d_hat=xi_d_hat,
        joined_tail_model=joined_model,
        join_diagnostics=diagnostics,
        p0=p0,
        bulk_volumes=bulk_volumes,
        bulk_failure_probabilities=bulk_pf,
        bulk_n_eff=bulk_n_eff_counts,
        bulk_p0_implied=bulk_p0_implied,
        bulk_volume_scaling_residual=bulk_residual,
        thin_volumes=thin_volumes,
        thin_failure_probabilities=thin_pf,
        thin_volume_scaling_residual=thin_residual,
        validation_ladder=ladder,
    )
