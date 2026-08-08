"""Construction for measuring `docs/V1.4-EDITS.md` E-47: a declared constitutive
form whose mechanism set is **complete** for the fitted region, refitted many times
on noisy in-envelope data, so the shape and the *orientation* of the resulting
parameter cloud can be measured rather than argued.

ADR-058 (docs/DECISIONS.md) is the design and states every choice made here: the
declared parameter metric (fractional, `θ̃ᵢ = θᵢ/θᵢ*`), why the invariant-1 default is
*not* used, why noise is relative, and why orientation rather than width is the
reported quantity.

**Known by construction, which is what makes this an oracle** (CLAUDE.md §7):

- The generator is M11.5's Generator C and the fitted form is its contestant 2, so
  the true parameter vector is known exactly: `θ* = (k₁, k₂₀, p)`.
- Every training strain sits at or below `GEN_GAMMA_C`, so the withheld
  recrystallisation term is **identically zero** over the whole fitted region. The
  form is therefore complete there by construction, and M11's failure mode — an
  incomplete mechanism set — is absent by construction rather than by assumption.
- The saturation level implied by any parameter pair is `(k₁/k₂)²` by inspection of
  the rate law, so the quantity E-47 names as the consequence is computable in closed
  form for every refit.

Cites Core §3.8 (identifiability, whose state-direction scope is exactly E-47's
finding), Spec §3.3 (the triage this has no counterpart in), Spec §2.2 with ADR-043
(the declared form and its validity report), Spec §9.3 (the in-envelope/out-of-envelope
split discipline).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from omi.state import FloatArray

from omi_domains.flagship_constitutive.experiment import Query
from omi_domains.flagship_constitutive.forms import KM_DENSITY_CEILING, KOCKS_MECKING
from omi_domains.flagship_constitutive.strain_experiment import (
    GEN_K1,
    GEN_K2_0,
    GEN_K2_EXPONENT,
    GEN_T_REF,
    TRAIN_STRAINS,
    _fit,
    _integrate,
    labels,
    sample_queries,
)

TRUE_THETA: FloatArray = np.array([GEN_K1, GEN_K2_0, GEN_K2_EXPONENT])
"""`θ* = (k₁, k₂₀, p)` — the generator's own values, which contestant 2's declared
form expresses exactly. Known by construction; it is also the declared metric's
scale (ADR-058)."""

PARAMETER_NAMES = ("k1", "k2_0", "exponent")

RELATIVE_NOISE = 0.02
"""Observation noise as a fraction of each label's own magnitude (ADR-058).

Two per cent is small enough that the in-envelope fit residual stays excellent —
which is one of E-47's own bullets and would be uninteresting to refute by adding
enough noise to break the fit — and large enough to be an ordinary laboratory figure
rather than a contrived one."""

N_SEEDS = 300
"""Refits, matching E-15's 300-reseed precedent (`docs/V1.4-EDITS.md` E-15), which is
the repository's standing convention for turning an argued mechanism into a measured
one."""

N_TRAIN_QUERIES = 48

ENVELOPE_STRAIN = max(TRAIN_STRAINS)
"""The upper edge of the fitted region. The in-envelope control is evaluated here."""

PROBE_STRAINS = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0)
"""Accumulated strains at which the alignment curve is evaluated, starting **at** the
envelope edge so the curve's first point is the control and its rotation is visible
against it rather than asserted."""

FAR_STRAIN = 6.0
"""Where the "range nothing reports" is quoted, matching M11.5's furthest held-out
strain so the number is comparable with that record."""


def _predict(theta: FloatArray, queries: Sequence[Query], strains: Sequence[float]) -> FloatArray:
    """Contestant 2's declared form at parameter vector *theta*.

    A local re-expression rather than a call into `strain_experiment`'s private
    predictor factory, so this oracle can evaluate the form at an *arbitrary* θ —
    which the M11.5 API cannot, since it only ever returns a predictor already
    bound to a fitted θ. Uses that module's own shared integrator, so the
    discretisation is identical and no difference measured here can come from a
    different step size.
    """
    k1, k2_0, exponent = float(theta[0]), float(theta[1]), float(theta[2])
    rho_0 = np.array([q.rho_0 for q in queries])
    temperature = np.array([q.temperature for q in queries])
    k2 = k2_0 * (temperature / GEN_T_REF) ** exponent

    def law(rho: FloatArray, gamma: float) -> FloatArray:
        del gamma  # the declared form carries no explicit strain dependence
        return np.asarray(k1 * np.sqrt(np.maximum(rho, 0.0)) - k2 * rho, dtype=np.float64)

    return _integrate(law, rho_0, strains)


def _refit(train: Sequence[Query], noisy: FloatArray) -> FloatArray:
    """Refit `θ = (k₁, k₂₀, p)` on *noisy* in-envelope labels.

    Same optimiser, same bounds and same initial guess as
    `strain_experiment.fit_correct_form`, so the spread measured across seeds is the
    spread of *that* fit and not of a differently-configured one. The bounds are a
    box constraint handled by the optimiser — architecture, never a loss penalty
    (CLAUDE.md invariant 5).
    """
    return _fit(
        lambda p: (_predict(p, train, TRAIN_STRAINS) - noisy).ravel(),
        [2.0, 0.5, 0.3],
        bounds=(0.0, np.inf),
    )


@dataclass(frozen=True)
class RidgeMeasurement:
    """Everything measured, never only the verdict (CLAUDE.md §8).

    The declared metric is carried explicitly (CLAUDE.md invariant 1): every
    parameter-space quantity below is in **fractional** units `θ̃ᵢ = θᵢ/θᵢ*`, and an
    angle in parameter space is meaningless without that statement.
    """

    metric: str
    """The declared parameter metric, quoted in the report (invariant 1)."""
    theta_true: FloatArray
    fitted: FloatArray
    """``(N_SEEDS, 3)`` fitted parameter vectors, in raw units."""
    fractional_sd: FloatArray
    """Per-parameter standard deviation in declared (fractional) units."""
    eigenvalues: FloatArray
    """Eigenvalues of the fractional-unit parameter covariance, descending."""
    ridge_direction: FloatArray
    """Leading eigenvector — the least-constrained direction in declared units."""
    condition_number: float
    """``λ₁/λ_min``: is there a ridge at all, before asking where it points."""
    alignment_curve: tuple[tuple[float, float], ...]
    """``(γ, |cos∠(v₁, e(γ))|)`` — ADR-058's reported quantity. The first entry is the
    in-envelope control."""
    in_envelope_residual: float
    """RMS fit residual against the noiseless labels over the fitted region, relative
    to the response scale — E-47's "excellent in-envelope fit" bullet, measured."""
    response_spread_in_envelope: float
    """Across-seed relative spread of the predicted response at the envelope edge."""
    response_spread_far: float
    """The same at :data:`FAR_STRAIN` — the "range nothing reports"."""
    saturation_spread: float
    """Across-seed relative spread of `(k₁/k₂₀)²`, E-47's own named quantity."""
    density_ceiling_clean_fraction: float
    """Fraction of far-strain queries for which `KOCKS_MECKING`'s declared bounds all
    report an extrapolation factor at or below 1 — E-47's "report clean" bullet,
    checked against the **unwindowed** declaration for the reason ADR-058 gives."""
    binding_bound_at_far: str
    """Which declared bound binds hardest at the far strain, or ``"none"``."""

    @property
    def alignment_in_envelope(self) -> float:
        return self.alignment_curve[0][1]

    @property
    def alignment_far(self) -> float:
        return self.alignment_curve[-1][1]

    @property
    def alignment_growth(self) -> float:
        """How much the ridge rotates into the extrapolation-sensitive direction
        across the probe reach — the divergence-not-difference reading E-41 requires
        of any claim about going further."""
        if self.alignment_in_envelope <= 0.0:
            return float("inf") if self.alignment_far > 0.0 else 1.0
        return self.alignment_far / self.alignment_in_envelope


def _sensitive_direction(theta: FloatArray, queries: Sequence[Query], strain: float) -> FloatArray:
    """The direction in **declared (fractional)** parameter space that the predicted
    response at *strain* is most sensitive to: the leading right-singular vector of
    ``∂ŷ(strain)/∂θ̃`` at *theta*, over the whole query ensemble.

    Central differences in fractional units, so the Jacobian is already expressed in
    the declared metric and no rescaling happens after the SVD (which would change
    the answer).
    """
    columns = []
    for j in range(theta.shape[0]):
        h = 1.0e-4
        up, down = theta.astype(float).copy(), theta.astype(float).copy()
        up[j] *= 1.0 + h
        down[j] *= 1.0 - h
        d = (_predict(up, queries, [strain])[0] - _predict(down, queries, [strain])[0]) / (2.0 * h)
        columns.append(d)
    jacobian = np.stack(columns, axis=1)
    _, _, vt = np.linalg.svd(jacobian, full_matrices=False)
    return np.asarray(vt[0], dtype=np.float64)


def measure(rng: np.random.Generator) -> RidgeMeasurement:
    """Run the E-47 measurement (ADR-058; `docs/V1.4-EDITS.md` E-47).

    Seeded explicitly, per CLAUDE.md §7. The *design of experiment* is drawn once and
    shared by every seed — only the observation noise is redrawn — so the spread
    measured is the spread the noise induces at a fixed campaign, which is the
    quantity E-47's claim is about. Redrawing the queries too would mix in
    design-of-experiment variation and overstate the ridge.
    """
    train = sample_queries(N_TRAIN_QUERIES, rng)
    clean = labels(train, TRAIN_STRAINS)

    fitted = np.empty((N_SEEDS, TRUE_THETA.shape[0]))
    residuals = np.empty(N_SEEDS)
    for i in range(N_SEEDS):
        noisy = clean * (1.0 + RELATIVE_NOISE * rng.standard_normal(clean.shape))
        theta = _refit(train, noisy)
        fitted[i] = theta
        predicted = _predict(theta, train, TRAIN_STRAINS)
        residuals[i] = float(np.sqrt(np.mean(((predicted - clean) / clean) ** 2)))

    fractional = fitted / TRUE_THETA
    covariance = np.cov(fractional, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    ridge = np.asarray(eigenvectors[:, 0], dtype=np.float64)

    alignment = tuple(
        (float(gamma), float(abs(ridge @ _sensitive_direction(TRUE_THETA, train, gamma))))
        for gamma in PROBE_STRAINS
    )

    def relative_spread(strain: float) -> float:
        predictions = np.stack([_predict(theta, train, [strain])[0] for theta in fitted])
        return float(np.mean(predictions.std(axis=0) / np.abs(predictions.mean(axis=0))))

    saturation = (fitted[:, 0] / fitted[:, 1]) ** 2

    far_predictions = _predict(TRUE_THETA, train, [FAR_STRAIN])[0]
    factors = []
    binding: list[str] = []
    for q, rho_far in zip(train, far_predictions):
        report = KOCKS_MECKING.report(
            {
                "strain_rate": q.strain_rate,
                "temperature": q.temperature,
                "stored_density": float(rho_far),
            }
        )
        factors.append(max(report.factors.values()))
        binding.append(report.binding_bound.name if report.binding_bound is not None else "none")
    clean_fraction = float(np.mean(np.asarray(factors) <= 1.0))
    worst = binding[int(np.argmax(factors))] if binding else "none"

    return RidgeMeasurement(
        metric=(
            "fractional parameter units: theta_i / theta_i_true, with theta_true = "
            f"{tuple(float(v) for v in TRUE_THETA)} (ADR-058; CLAUDE.md invariant 1). "
            "Deliberately NOT the invariant-1 aleatoric default, which here would be the "
            "across-seed sd of the very covariance being measured."
        ),
        theta_true=TRUE_THETA,
        fitted=fitted,
        fractional_sd=np.asarray(fractional.std(axis=0), dtype=np.float64),
        eigenvalues=np.asarray(eigenvalues, dtype=np.float64),
        ridge_direction=ridge,
        condition_number=float(eigenvalues[0] / eigenvalues[-1]),
        alignment_curve=alignment,
        in_envelope_residual=float(residuals.mean()),
        response_spread_in_envelope=relative_spread(ENVELOPE_STRAIN),
        response_spread_far=relative_spread(FAR_STRAIN),
        saturation_spread=float(saturation.std() / saturation.mean()),
        density_ceiling_clean_fraction=clean_fraction,
        binding_bound_at_far=worst,
    )


DECLARED_CEILING = KM_DENSITY_CEILING
"""Re-exported so a test can quote the declared bound it is checking against rather
than restating the number (CLAUDE.md §8: never hardcode a narrative number)."""
