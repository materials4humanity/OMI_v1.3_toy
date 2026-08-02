"""M11.5's fair-axis extrapolation experiment (ADR-047, docs/DECISIONS.md).

Cites Spec §2.2 (the proposed declared-constitutive-form category under test),
Spec §9.3 (prospective validation, grouped splits, and the baseline comparison)
and Core §3.9 (why extrapolation reach is the property that matters for a
composed chain).

**Why this experiment exists.** M11.4 ran the same design on the strain-*rate*
axis and produced a null that was uninformative rather than negative: the declared
form has no strain-rate dependence, so candidate and baseline agreed by
construction along exactly the axis that was withheld
(`docs/M11.4-EXTRAPOLATION.md`; `docs/V1.4-EDITS.md` E-39). Everything here is
ADR-045's design with the axis corrected.

**Generator C — the same shape as Generator A, on an axis the form can see.**

    dρ/dγ = k₁√ρ − k₂(T)·ρ − k_drx·ρ·max(0, γ − γ_c)

- `k₂(T) = k₂₀·(T/T_ref)^p` — the temperature-dependent recovery coefficient,
  carried unchanged from Generator A. Contestant 2 has it; contestant 3b does not.
- `k_drx·ρ·max(0, γ − γ_c)` — **the withheld term**: dynamic recrystallisation
  consuming stored density above a critical accumulated strain. Identically zero
  below `γ_c`, which is set at the upper edge of the training range, so over the
  whole training set contestant 2's form is *exactly* the generator's.

**Why this withheld term and not another.** It is proportional to `ρ`, the same
shape as Kocks–Mecking's own recovery term, so a fitted declared form can *partly
absorb* it by inflating `k₂`. That is what makes the two misspecification arms
interpretable: 3a has no removal term at all and can absorb none of it, 3b has one
but cannot make it temperature-dependent. A withheld term the form could not
represent in any parameterisation would fail both arms identically and collapse the
comparison back toward M11.4's.

**The hold-out is accumulated strain, and it is a control-space region** (Core
§3.2: `𝒰`'s elements are functions of time, so total imposed strain is a property
of the programme). Training draws `γ ∈ [0.25, 1.0]`; evaluation draws
`γ ∈ [2.0, 6.0]`, outside `KOCKS_MECKING_STRAIN_WINDOWED`'s declared window.
Strain rate and temperature are drawn from the **same** ranges in both, so
accumulated strain is the only thing withheld and every gap stays attributable
(CLAUDE.md §5 invariant 6: grouped by region, never randomly).

**Contestant 1 is a free-form rate law, integrated — not a response surface.**
M11.4's contestant 1 extrapolated as `surface(q) × γ`, linear in accumulated
strain by construction, which on a strain hold-out is a straw man rather than a
baseline. Here it is a generic polynomial rate law advanced by the same integrator
at the same step size as every declared-form contestant, which is what OMI's
free-form incumbent actually is (`omi.learning` + `omi.chain`: a learned evolution
operator that is stepped and composed). An integrated rate law that learns
`f(ρ) < 0` at large `ρ` **can** saturate, so the declared form's advantage — if any
— has to be earned rather than handed over by the baseline's extrapolation rule.
ADR-047 records why the axis change obliges this re-specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy.optimize import least_squares

from omi.baseline import root_mean_squared_error
from omi.proposed.holdout import HoldOutDiscriminationReport, check_hold_out_discriminates
from omi.state import FloatArray

from omi_domains.flagship_constitutive.experiment import Query, TEMPERATURE_RANGE
from omi_domains.flagship_constitutive.forms import KM_K1, KM_STRAIN_WINDOW_HIGH

# --- Generator C --------------------------------------------------------------

GEN_K1 = KM_K1
"""Storage coefficient, shared with the declared form — the generator and the
declared form agree on the part of the physics the source establishes."""
GEN_K2_0 = 2.0
GEN_K2_EXPONENT = 1.5
"""`k₂(T) = k₂₀·(T/T_ref)^p`: recovery strengthens with temperature. Contestant 2
carries this dependence; contestant 3b treats `k₂` as constant."""
GEN_T_REF = 900.0
GEN_K_DRX = 0.25
"""Strength of the withheld dynamic-recrystallisation term. Sized so its
contribution over the held-out region is comparable to — not dominant over —
storage and recovery, since a withheld term that swamps the declared physics
reproduces M11.4's failure in the opposite direction: every contestant would again
be wrong by the same overwhelming amount."""
GEN_GAMMA_C = KM_STRAIN_WINDOW_HIGH
"""Critical accumulated strain for recrystallisation onset, **equal to the upper
edge of the declared strain window and of the training range** — so "outside the
declared range" and "the withheld physics is active" name the same region by
construction rather than by coincidence (ADR-045's property, preserved)."""

RHO_CEILING = 1.0e6
"""Numerical ceiling on the integrated state, applied identically to the generator
and to every contestant.

**Not a modelling claim and not a constraint on any contestant's reach.** It is
six orders of magnitude above anything the generator or any fitted contestant
reaches over the held-out region, so no reported prediction touches it. Its only
role is during fitting: the free-form rate law's optimiser explores parameter
regions where the integral diverges, and an infinite residual carries no gradient
for the optimiser to retreat along. Clipping keeps the least-squares residual
finite so a divergent probe is merely *bad* rather than unusable — which is a
fairness measure for the contestant with the most parameters, not a handicap on
the others (ADR-047)."""

STRAIN_STEP = 1.0 / 128.0
"""Fixed integration increment **in accumulated strain**, shared by the generator
and every contestant.

Fixed *step size*, not a fixed step count: M11.4 used 64 steps for any total
strain, which is uniform across contestants but makes the ground truth itself
coarser the further the rollout goes — unacceptable when rollout length is the
held-out axis."""


def _integrate(
    law: Callable[[FloatArray, float], FloatArray],
    rho_0: FloatArray,
    checkpoints: Sequence[float],
) -> FloatArray:
    """Advance a strain-dependent rate law over a query ensemble at once,
    snapshotting at *checkpoints* (Core §3.3's evolution; ADR-047).

    Vectorised over queries rather than looped, so the same fixed step size is
    affordable at every rollout length. Non-negativity of the state is enforced
    **architecturally, in the integrator** — never as a fitting penalty (CLAUDE.md
    §5 invariant 5) — so it holds for every contestant off-manifold as well as on.

    Returns an array of shape ``(len(checkpoints), len(rho_0))``.
    """
    targets = sorted(float(c) for c in checkpoints)
    if targets and targets[0] < 0.0:
        raise ValueError("accumulated strain checkpoints must be non-negative")
    rho = np.asarray(rho_0, dtype=float).copy()
    out = np.empty((len(targets), rho.shape[0]), dtype=float)
    gamma = 0.0
    for index, target in enumerate(targets):
        while gamma < target - 1.0e-12:
            step = min(STRAIN_STEP, target - gamma)
            rho = np.clip(rho + step * law(rho, gamma), 0.0, RHO_CEILING)
            gamma += step
        out[index] = rho
    order = np.argsort(np.argsort(np.asarray(checkpoints, dtype=float), kind="stable"), kind="stable")
    return out[order]


def _generator_law(
    temperature: FloatArray, k_drx: float
) -> Callable[[FloatArray, float], FloatArray]:
    """Generator C's rate law for a query ensemble, with the withheld term's
    strength passed in so the withheld-free truth is produced by the *same* code
    path rather than by a second implementation (ADR-047).

    **Generator C has no strain-rate dependence at all** — Generator A's drag term
    is gone, replaced by the recrystallisation term, because two withheld
    mechanisms would destroy the attribution ADR-045 requires. Strain rate remains
    a sampled control and a contestant feature, so every model must discover for
    itself that it is irrelevant; that is realistic and it handicaps no one
    preferentially.
    """
    k2 = GEN_K2_0 * (temperature / GEN_T_REF) ** GEN_K2_EXPONENT

    def law(rho: FloatArray, gamma: float) -> FloatArray:
        drx = k_drx * max(0.0, gamma - GEN_GAMMA_C)
        return np.asarray(
            GEN_K1 * np.sqrt(np.maximum(rho, 0.0)) - k2 * rho - drx * rho, dtype=np.float64
        )

    return law


# --- the design of experiment -------------------------------------------------

RATE_RANGE = (1.0e-2, 5.0)
"""Strain rates, **identical in training and evaluation** and strictly inside
`KOCKS_MECKING`'s declared window. Held fixed across the split so accumulated
strain is the only quantity withheld."""
RHO_RANGE = (0.5, 6.0)

TRAIN_STRAINS = (0.25, 0.5, 0.75, 1.0)
"""In-envelope accumulated strains, all at or below `GEN_GAMMA_C`, so the withheld
term is identically zero over the whole training set."""
HELD_OUT_STRAINS = (2.0, 3.0, 4.0, 6.0)
"""Held-out accumulated strains, all outside the declared strain window, where the
withheld term is active. Grouped by region, never randomly."""

DRY_RUN_FIT_STRAINS = (0.25, 0.5)
DRY_RUN_PROBE_STRAINS = (0.5, 1.0)
"""The hold-out-discrimination check's split (ADR-045 as amended). **Strictly
in-envelope**: it pushes along the candidate axis as far as the training envelope
permits and never touches `HELD_OUT_STRAINS`, so running it leaks nothing about
the quantity the pre-registered thresholds will judge.

The near probe sits at the **upper edge of the fitted region** and the far probe at
the **upper edge of the envelope**, which is what makes the ratio between them a
reading of divergence-under-extrapolation rather than of two arbitrary points. At
the near point the models are still where their parameters were determined, so
their disagreement there is the offset the training data already exhibits; the
question the check asks is how much that offset grows once they leave it."""


def sample_queries(n: int, rng: np.random.Generator) -> list[Query]:
    """Draw *n* queries with log-uniform strain rate (Spec §9.3's design of
    experiment; seeded per CLAUDE.md §7). The strain axis is not sampled here — it
    is the axis being split, so it is supplied by the caller as checkpoints."""
    log_low, log_high = np.log(RATE_RANGE[0]), np.log(RATE_RANGE[1])
    return [
        Query(
            rho_0=float(rng.uniform(*RHO_RANGE)),
            strain_rate=float(np.exp(rng.uniform(log_low, log_high))),
            temperature=float(rng.uniform(*TEMPERATURE_RANGE)),
        )
        for _ in range(n)
    ]


def _columns(queries: Sequence[Query]) -> tuple[FloatArray, FloatArray, FloatArray]:
    return (
        np.array([q.rho_0 for q in queries]),
        np.array([q.strain_rate for q in queries]),
        np.array([q.temperature for q in queries]),
    )


def labels(
    queries: Sequence[Query], strains: Sequence[float], *, k_drx: float | None = None
) -> FloatArray:
    """Generator-C ground truth, shape ``(len(strains), len(queries))``.

    *k_drx* defaults to :data:`GEN_K_DRX`. Passing ``0.0`` gives the
    **withheld-free** truth the hold-out-discrimination check scores against
    (ADR-045 as amended) — the same generator with one term switched off, not a
    separate model.
    """
    rho_0, _, temperature = _columns(queries)
    law = _generator_law(temperature, GEN_K_DRX if k_drx is None else k_drx)
    return _integrate(law, rho_0, strains)


def withheld_term_magnitude(queries: Sequence[Query], strains: Sequence[float]) -> float:
    """Mean absolute contribution of the withheld term over a region — the scale
    the declared minimum effect is set from (ADR-045's convention, carried over).

    Computed by running the generator twice and differencing. No contestant is
    fitted and no error is measured, so consulting it before registering thresholds
    does not amount to seeing the result those thresholds will judge.
    """
    full = labels(queries, strains)
    clean = labels(queries, strains, k_drx=0.0)
    return float(np.mean(np.abs(full - clean)))


# --- contestants --------------------------------------------------------------


@dataclass(frozen=True)
class Contestant:
    """One fitted predictor and how to read its identity (ADR-045's four
    contestants; Spec §9.3's baseline comparison)."""

    label: str
    predict: Callable[[Sequence[Query], Sequence[float]], FloatArray]
    """``(queries, strains) -> array of shape (len(strains), len(queries))``."""
    declared_form: bool
    """Whether this contestant is constrained to a declared constitutive form
    (Spec §2.2's proposed sixth category) or carries generic structure only."""
    note: str


FIT_TOLERANCE = 1.0e-10
MAX_FIT_EVALUATIONS = 4000
"""Shared optimiser settings. **Every fitted contestant uses the same optimiser
with the same tolerances**, so none is advantaged by fit quality — which matters
more here than at M11.4, because contestant 1 now carries ten parameters against
the declared forms' one to three and a weaker optimiser would disadvantage it for
a reason unrelated to declared physics (ADR-047)."""


def _fit(
    residual: Callable[[FloatArray], FloatArray],
    initial: Sequence[float],
    bounds: tuple[float, float] = (-np.inf, np.inf),
) -> FloatArray:
    """Least-squares fit, shared by every fitted contestant.

    Parameter *bounds* are a box constraint handled by the optimiser — architecture,
    not a loss penalty (CLAUDE.md §5 invariant 5). Declared-form coefficients are
    bounded non-negative because a negative storage or recovery coefficient is not a
    slow fit, it is a different physical claim; free-form rate-law coefficients are
    unbounded because a rate law must be able to go negative, which is exactly how
    it represents recovery.
    """
    result = least_squares(
        residual,
        np.asarray(initial, dtype=float),
        bounds=bounds,
        xtol=FIT_TOLERANCE,
        ftol=FIT_TOLERANCE,
        max_nfev=MAX_FIT_EVALUATIONS,
    )
    return np.asarray(result.x, dtype=float)


def _km_predictor(
    k1: float, k2_of_temperature: Callable[[FloatArray], FloatArray]
) -> Callable[[Sequence[Query], Sequence[float]], FloatArray]:
    """A declared-form predictor: Kocks–Mecking with the given coefficients,
    integrated by the shared integrator. Carries no withheld term."""

    def predict(queries: Sequence[Query], strains: Sequence[float]) -> FloatArray:
        rho_0, _, temperature = _columns(queries)
        k2 = k2_of_temperature(temperature)

        def law(rho: FloatArray, gamma: float) -> FloatArray:
            del gamma  # the declared form has no explicit strain dependence
            return np.asarray(k1 * np.sqrt(np.maximum(rho, 0.0)) - k2 * rho, dtype=np.float64)

        return _integrate(law, rho_0, strains)

    return predict


def fit_correct_form(
    train: Sequence[Query], y: FloatArray, strains: Sequence[float] = TRAIN_STRAINS
) -> Contestant:
    """**Contestant 2** — the canonical form with its temperature dependence,
    fitted (ADR-045). Correct in form, missing only Generator C's withheld
    recrystallisation term.

    Reported with the caveat ADR-045 requires: a correct form with fitted
    parameters is a very strong prior and its win is close to structural, so this
    arm is a **ceiling**, not the number that carries the claim.
    """

    def build(theta: FloatArray) -> Callable[[Sequence[Query], Sequence[float]], FloatArray]:
        k1, k2_0, exponent = float(theta[0]), float(theta[1]), float(theta[2])
        return _km_predictor(k1, lambda t: k2_0 * (t / GEN_T_REF) ** exponent)

    theta = _fit(
        lambda p: (build(p)(train, strains) - y).ravel(),
        [2.0, 0.5, 0.3],
        bounds=(0.0, np.inf),
    )
    k1, k2_0, exponent = float(theta[0]), float(theta[1]), float(theta[2])
    return Contestant(
        label="2_correct_form",
        predict=build(theta),
        declared_form=True,
        note=f"fitted k1={k1:.3f}, k2_0={k2_0:.3f}, exponent={exponent:.3f}; withheld DRX term absent",
    )


def fit_missing_mechanism(
    train: Sequence[Query], y: FloatArray, strains: Sequence[float] = TRAIN_STRAINS
) -> Contestant:
    """**Contestant 3a** — a *missing mechanism*: Kocks–Mecking with the recovery
    term `−k₂ρ` dropped entirely (ADR-045). It has no removal term at all, so it can
    absorb none of the withheld recrystallisation and cannot saturate."""

    def build(theta: FloatArray) -> Callable[[Sequence[Query], Sequence[float]], FloatArray]:
        return _km_predictor(float(theta[0]), lambda t: np.zeros_like(t))

    theta = _fit(lambda p: (build(p)(train, strains) - y).ravel(), [1.0], bounds=(0.0, np.inf))
    return Contestant(
        label="3a_missing_mechanism",
        predict=build(theta),
        declared_form=True,
        note=f"fitted k1={float(theta[0]):.3f}; recovery term dropped",
    )


def fit_missing_dependence(
    train: Sequence[Query], y: FloatArray, strains: Sequence[float] = TRAIN_STRAINS
) -> Contestant:
    """**Contestant 3b** — a *missing dependence*: the recovery coefficient treated
    as constant rather than temperature-dependent (ADR-045). It has a removal term
    and can absorb part of the withheld recrystallisation, but cannot make that
    absorption temperature-dependent."""

    def build(theta: FloatArray) -> Callable[[Sequence[Query], Sequence[float]], FloatArray]:
        constant = float(theta[1])
        return _km_predictor(float(theta[0]), lambda t: np.full_like(t, constant))

    theta = _fit(
        lambda p: (build(p)(train, strains) - y).ravel(), [2.0, 1.0], bounds=(0.0, np.inf)
    )
    return Contestant(
        label="3b_missing_dependence",
        predict=build(theta),
        declared_form=True,
        note=f"fitted k1={float(theta[0]):.3f}, constant k2={float(theta[1]):.3f}",
    )


def _rate_law_basis(rho: FloatArray, log_rate: FloatArray, scaled_t: FloatArray) -> FloatArray:
    """Generic quadratic basis for a rate law in `(ρ, ln γ̇, T/T_ref)` — ten terms,
    the same dimensionality M11.4's free-form contestant carried.

    Deliberately **no** `√ρ` term: that is the declared form's own content and
    handing it over would make contestant 1 a disguised copy of contestant 2. A
    quadratic in `ρ` can nonetheless cross zero, so this basis *is* structurally
    capable of saturating — it simply has to learn where, which is the whole
    question (ADR-047).
    """
    ones = np.ones_like(rho)
    return np.stack(
        [
            ones,
            rho,
            log_rate,
            scaled_t,
            rho * rho,
            log_rate * log_rate,
            scaled_t * scaled_t,
            rho * log_rate,
            rho * scaled_t,
            log_rate * scaled_t,
        ],
        axis=0,
    )


def fit_free_form(
    train: Sequence[Query], y: FloatArray, strains: Sequence[float] = TRAIN_STRAINS
) -> Contestant:
    """**Contestant 1** — the v1.3 incumbent: a **free-form rate law**, integrated
    (ADR-047), with generic structure only and no declared form.

    Not a straw man, and the axis change is what makes that worth restating. On the
    strain axis a response surface extrapolated as `surface × γ` cannot saturate and
    would lose for a reason that has nothing to do with declared physics. This
    contestant is an evolution operator: same integrator, same fixed step size, same
    architectural non-negativity, same optimiser and tolerances as every declared
    form. Its basis can represent a negative rate at large `ρ`, so saturation is
    within its reach.
    """
    rho_0, rate, temperature = _columns(train)
    log_rate, scaled_t = np.log(rate), temperature / GEN_T_REF

    def build(theta: FloatArray) -> Callable[[Sequence[Query], Sequence[float]], FloatArray]:
        def predict(queries: Sequence[Query], strains: Sequence[float]) -> FloatArray:
            q_rho, q_rate, q_temperature = _columns(queries)
            q_log_rate, q_scaled_t = np.log(q_rate), q_temperature / GEN_T_REF

            def law(rho: FloatArray, gamma: float) -> FloatArray:
                del gamma
                basis = _rate_law_basis(rho, q_log_rate, q_scaled_t)
                return np.asarray(theta @ basis, dtype=float)

            return _integrate(law, q_rho, strains)

        return predict

    del rho_0, log_rate, scaled_t  # shapes only; the basis is rebuilt per integration step
    initial = np.zeros(10)
    initial[0] = 1.0
    theta = _fit(lambda p: (build(p)(train, strains) - y).ravel(), list(initial))
    return Contestant(
        label="1_free_form",
        predict=build(theta),
        declared_form=False,
        note=(
            f"free-form rate law, quadratic basis in (rho, ln rate, T/T_ref), {theta.size} terms, "
            "integrated by the shared integrator; non-negativity architectural"
        ),
    )


def _tabular_features(queries: Sequence[Query], strain: float) -> FloatArray:
    rho_0, rate, temperature = _columns(queries)
    return np.stack([rho_0, np.log(rate), temperature, np.full_like(rho_0, strain)], axis=1)


def fit_tabular(
    train: Sequence[Query],
    y: FloatArray,
    regressor: object,
    strains: Sequence[float] = TRAIN_STRAINS,
) -> Contestant:
    """**Contestant 4** — a tabular baseline from `omi.baseline`, unchanged
    (ADR-045; Spec §9.3's required baseline comparison).

    It gains accumulated strain as a feature and is fitted across the in-envelope
    strain range, which is the natural tabular use of this data. It stays a **direct
    regressor** rather than being turned into an integrator: that is what a tabular
    baseline is, M10.2 already characterised how such models extrapolate, and making
    it an operator would delete the external comparator by turning it into a second
    copy of contestant 1 (ADR-047).
    """
    features = np.concatenate([_tabular_features(train, s) for s in strains], axis=0)
    regressor.fit(features, y.ravel())  # type: ignore[attr-defined]

    def predict(queries: Sequence[Query], strains: Sequence[float]) -> FloatArray:
        rows = [
            regressor.predict(_tabular_features(queries, s))  # type: ignore[attr-defined]
            for s in strains
        ]
        return np.stack([np.asarray(row, dtype=np.float64) for row in rows], axis=0)

    return Contestant(
        label=f"4_tabular_{type(regressor).__name__}",
        predict=predict,
        declared_form=False,
        note=f"{type(regressor).__name__} from omi.baseline, unchanged, with accumulated strain as a feature",
    )


# --- the hold-out discrimination check (ADR-045 as amended) -------------------

REQUIRED_DIVERGENCE = 2.0
"""Declared minimum growth factor for the disagreement between the declared-form
candidate and the free-form baseline across the dry-run probe reach.

**Declared, not derived**, for the reason CLAUDE.md invariant 1 gives about
metrics — a ratio means nothing without the bar it is read against. The value says
a hold-out is usable only if the two model classes' disagreement at least
*doubles* as the axis is pushed. It sits between the two axes this repository has
measured with margin in both directions — M11.4's vacuous rate axis reads 1.05,
M11.5's strain axis reads well above 2 — so it is not a bar tuned to admit one
particular experiment. `docs/M11.5-PREREGISTRATION.md` records the measured values
and the fact that the bar was fixed before either was read against it."""


def dry_run_discrimination(
    *,
    rng_train: np.random.Generator,
    rng_probe: np.random.Generator,
    n_train: int = 120,
    n_probe: int = 400,
    required_divergence: float = REQUIRED_DIVERGENCE,
) -> HoldOutDiscriminationReport:
    """Run ADR-045's hold-out-discrimination requirement on the accumulated-strain
    axis, **strictly in-envelope**.

    Fits the declared-form candidate (contestant 2) and the free-form baseline
    (contestant 1) on :data:`DRY_RUN_FIT_STRAINS`, then probes them at the two
    :data:`DRY_RUN_PROBE_STRAINS`. Both probe points are inside the training
    envelope and below `γ_c`, so :data:`HELD_OUT_STRAINS` is never touched and the
    check leaks nothing about the quantity the pre-registered thresholds will
    judge.

    The noise floor is the larger of the two contestants' own in-envelope fit
    residuals: a divergence smaller than the fit's own scatter is not evidence of
    anything.
    """
    train = sample_queries(n_train, rng_train)
    y_train = labels(train, DRY_RUN_FIT_STRAINS)
    candidate = fit_correct_form(train, y_train, DRY_RUN_FIT_STRAINS)
    baseline = fit_free_form(train, y_train, DRY_RUN_FIT_STRAINS)

    noise_floor = max(
        root_mean_squared_error(candidate.predict(train, DRY_RUN_FIT_STRAINS), y_train),
        root_mean_squared_error(baseline.predict(train, DRY_RUN_FIT_STRAINS), y_train),
    )

    probe = sample_queries(n_probe, rng_probe)
    near, far = DRY_RUN_PROBE_STRAINS
    clean = labels(probe, (near, far), k_drx=0.0)
    candidate_predictions = candidate.predict(probe, (near, far))
    baseline_predictions = baseline.predict(probe, (near, far))

    return check_hold_out_discriminates(
        axis="accumulated_strain",
        candidate_near=candidate_predictions[0],
        baseline_near=baseline_predictions[0],
        candidate_far=candidate_predictions[1],
        baseline_far=baseline_predictions[1],
        truth_without_withheld_term_near=clean[0],
        truth_without_withheld_term_far=clean[1],
        noise_floor=noise_floor,
        required_divergence=required_divergence,
    )
