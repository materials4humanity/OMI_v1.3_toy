"""M11.4's extrapolation experiment: does declared physics buy reach?
(ADR-045, docs/DECISIONS.md.)

Cites Spec §2.2 (the proposed declared-constitutive-form category under test),
Spec §9.3 (prospective validation and grouped splits) and Core §3.9 (why
extrapolation reach is the property that matters for a composed chain).

**Generator A — the primary experiment.** Kocks–Mecking as the backbone, with two
features the contestants must recover from data and **one named term withheld from
every contestant**:

    dρ/dγ = k₁√ρ − k₂(T)·ρ − k_drag·ρ·max(0, ln(γ̇/γ̇_ref))

- `k₂(T) = k₂₀·(T/T_ref)^p` — a temperature-dependent recovery coefficient. Present
  in the generator; contestant 2 carries it, contestant 3b does not.
- `k_drag·ρ·max(0, ln(γ̇/γ̇_ref))` — **the withheld term**, a strain-rate-dependent
  drag contribution that is identically zero below `γ̇_ref` and grows above it. No
  contestant carries it.

**Why this design is the whole point of Generator A.** Below `γ̇_ref` the drag term
vanishes, so contestant 2's form is *exactly* the generator's form and its only error
in-envelope is parameter estimation. Above `γ̇_ref` the drag bites, and contestant 2's
error is attributable to **one identified missing contribution** and nothing else.
That is what makes every gap in this experiment interpretable, and it is why ADR-045
was amended to make this generator primary rather than the composite (whose diffuse
misspecification cannot support attribution).

It is also why the generator is *not* bare Kocks–Mecking: a generator differing from
contestant 2 by nothing would recover it to machine precision by construction, which
is `docs/V1.4-EDITS.md` E-12's circularity at larger scale.

**The hold-out is a control-space region, grouped, never random** (CLAUDE.md §5
invariant 6): training draws strain rates inside `KOCKS_MECKING`'s declared window,
evaluation draws them far above it, so the held-out region lies outside the declared
validity range and the extrapolation report is exercised rather than merely present.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from omi.constraints import positive
from omi.state import FloatArray

from omi_domains.flagship_constitutive.forms import KM_K1, KM_RATE_WINDOW

# --- Generator A --------------------------------------------------------------

GEN_K1 = KM_K1
"""Storage coefficient, shared with the declared form (`forms.py`) — the
generator and the declared form agree on the part of the physics the source
establishes."""
GEN_K2_0 = 2.0
GEN_K2_EXPONENT = 1.5
"""`k₂(T) = k₂₀·(T/T_ref)^p`: recovery strengthens with temperature. Contestant 2
carries this dependence; contestant 3b treats `k₂` as constant."""
GEN_T_REF = 900.0
GEN_K_DRAG = 1.2
GEN_RATE_REF = KM_RATE_WINDOW[1]
"""The withheld drag term switches on at the **upper edge of the declared
validity window**, so "outside the declared range" and "the withheld physics is
active" are the same region by construction rather than by coincidence."""

N_INTEGRATION_STEPS = 64
"""Fixed strain increments per unit strain, for every contestant and the
generator alike — so no contestant is advantaged by integration resolution."""


def _integrate(rate_law: Callable[[float], float], rho_0: float, total_strain: float) -> float:
    """Explicit integration of a rate law in accumulated strain, at a fixed step
    count shared by every contestant (Core §3.3's evolution; ADR-045)."""
    rho = rho_0
    step = total_strain / N_INTEGRATION_STEPS
    for _ in range(N_INTEGRATION_STEPS):
        rho = max(rho + step * rate_law(rho), 0.0)
    return float(rho)


def generator_a(rho_0: float, strain_rate: float, temperature: float, total_strain: float = 1.0) -> float:
    """Ground truth for Generator A (ADR-045): Kocks–Mecking with a
    temperature-dependent recovery coefficient **and** a withheld strain-rate drag
    term no contestant carries."""
    k2 = GEN_K2_0 * (temperature / GEN_T_REF) ** GEN_K2_EXPONENT
    excess = max(0.0, float(np.log(strain_rate / GEN_RATE_REF))) if strain_rate > 0 else 0.0

    def law(rho: float) -> float:
        return float(GEN_K1 * np.sqrt(max(rho, 0.0)) - k2 * rho - GEN_K_DRAG * rho * excess)

    return float(_integrate(law, rho_0, total_strain))


# --- the design of experiment -------------------------------------------------


@dataclass(frozen=True)
class Query:
    """One evaluation point: an initial state and a control pair (Core §3.2)."""

    rho_0: float
    strain_rate: float
    temperature: float

    @property
    def features(self) -> FloatArray:
        """Tabular feature vector for `omi.baseline`'s regressors — log rate,
        because the withheld term is logarithmic in rate and a linear feature would
        handicap the baselines for a reason unrelated to the claim (Spec §9.3)."""
        return np.array([self.rho_0, float(np.log(self.strain_rate)), self.temperature])


IN_ENVELOPE_RATE = (1.0e-2, 5.0)
"""Training rates, strictly inside `KOCKS_MECKING`'s declared window `[1e-3, 10]`
and strictly below `GEN_RATE_REF`, so the withheld term is identically zero over
the whole training set (ADR-045)."""
HELD_OUT_RATE = (20.0, 200.0)
"""Evaluation rates, **outside** the declared window, where the withheld term is
active. Grouped by region, never randomly (CLAUDE.md §5 invariant 6)."""
TEMPERATURE_RANGE = (700.0, 1000.0)
RHO_RANGE = (0.5, 6.0)


def sample_queries(
    n: int, rate_range: tuple[float, float], rng: np.random.Generator
) -> list[Query]:
    """Draw *n* queries with log-uniform strain rate (Spec §9.3's design of
    experiment; seeded per CLAUDE.md §7)."""
    log_low, log_high = np.log(rate_range[0]), np.log(rate_range[1])
    return [
        Query(
            rho_0=float(rng.uniform(*RHO_RANGE)),
            strain_rate=float(np.exp(rng.uniform(log_low, log_high))),
            temperature=float(rng.uniform(*TEMPERATURE_RANGE)),
        )
        for _ in range(n)
    ]


def labels(queries: Sequence[Query], total_strain: float = 1.0) -> FloatArray:
    """Generator-A ground truth for a query set (ADR-045)."""
    return np.array([generator_a(q.rho_0, q.strain_rate, q.temperature, total_strain) for q in queries])


# --- contestants --------------------------------------------------------------


@dataclass(frozen=True)
class Contestant:
    """One fitted predictor and how to read its identity (ADR-045's four
    contestants; Spec §9.3's baseline comparison)."""

    label: str
    predict: Callable[[Query, float], float]
    declared_form: bool
    """Whether this contestant is constrained to a declared constitutive form
    (Spec §2.2's proposed category) or carries generic structure only."""
    note: str


def _fit_scalar(
    residual: Callable[[FloatArray], FloatArray],
    initial: FloatArray,
    n_steps: int = 400,
    learning_rate: float = 0.02,
) -> FloatArray:
    """Least-squares fit by projected gradient descent on unconstrained
    parameters mapped through `omi.constraints.positive` (Spec §2.2: positivity is
    architecture, not a penalty) — the same discipline every fitted contestant
    uses, so none is advantaged by its optimiser."""
    raw = np.asarray(initial, dtype=float).copy()
    for _ in range(n_steps):
        base = float(np.mean(residual(positive(raw)) ** 2))
        grad = np.zeros_like(raw)
        for j in range(raw.shape[0]):
            probe = raw.copy()
            h = 1.0e-5
            probe[j] += h
            grad[j] = (float(np.mean(residual(positive(probe)) ** 2)) - base) / h
        raw -= learning_rate * grad
    return positive(raw)


def _km_predictor(k1: float, k2_fn: Callable[[float], float], drag: float = 0.0) -> Callable[[Query, float], float]:
    def predict(q: Query, total_strain: float) -> float:
        k2 = k2_fn(q.temperature)
        excess = max(0.0, float(np.log(q.strain_rate / GEN_RATE_REF))) if q.strain_rate > 0 else 0.0

        def law(rho: float) -> float:
            return float(k1 * np.sqrt(max(rho, 0.0)) - k2 * rho - drag * rho * excess)

        return _integrate(law, q.rho_0, total_strain)

    return predict


def fit_correct_form(train: Sequence[Query], y: FloatArray) -> Contestant:
    """**Contestant 2** — the canonical form with its temperature dependence, fitted
    (ADR-045). Correct in form, missing only Generator A's withheld drag term.

    Reported with the caveat ADR-045 requires: a correct form with fitted parameters
    is a very strong prior and its win is close to structural, so this arm is a
    calibration reference and **not** the number that carries the claim.
    """

    def residual(theta: FloatArray) -> FloatArray:
        k1, k2_0, exponent = float(theta[0]), float(theta[1]), float(theta[2])
        predict = _km_predictor(k1, lambda T: k2_0 * (T / GEN_T_REF) ** exponent)
        return np.array([predict(q, 1.0) for q in train]) - y

    theta = _fit_scalar(residual, np.array([2.0, 0.5, 0.3]))
    k1, k2_0, exponent = float(theta[0]), float(theta[1]), float(theta[2])
    return Contestant(
        label="2_correct_form",
        predict=_km_predictor(k1, lambda T: k2_0 * (T / GEN_T_REF) ** exponent),
        declared_form=True,
        note=f"fitted k1={k1:.3f}, k2_0={k2_0:.3f}, exponent={exponent:.3f}; withheld drag term absent",
    )


def fit_missing_mechanism(train: Sequence[Query], y: FloatArray) -> Contestant:
    """**Contestant 3a** — a *missing mechanism*: Kocks–Mecking with the recovery
    term `−k₂ρ` dropped entirely (ADR-045). Degrades monotonically with accumulated
    strain, since nothing balances storage."""

    def residual(theta: FloatArray) -> FloatArray:
        predict = _km_predictor(float(theta[0]), lambda T: 0.0)
        return np.array([predict(q, 1.0) for q in train]) - y

    theta = _fit_scalar(residual, np.array([1.0]))
    return Contestant(
        label="3a_missing_mechanism",
        predict=_km_predictor(float(theta[0]), lambda T: 0.0),
        declared_form=True,
        note=f"fitted k1={float(theta[0]):.3f}; recovery term dropped",
    )


def fit_missing_dependence(train: Sequence[Query], y: FloatArray) -> Contestant:
    """**Contestant 3b** — a *missing dependence*: the recovery coefficient treated
    as a constant rather than temperature-dependent (ADR-045). Degrades with thermal
    excursion away from wherever the constant was effectively fitted."""

    def residual(theta: FloatArray) -> FloatArray:
        predict = _km_predictor(float(theta[0]), lambda T: float(theta[1]))
        return np.array([predict(q, 1.0) for q in train]) - y

    theta = _fit_scalar(residual, np.array([2.0, 1.0]))
    return Contestant(
        label="3b_missing_dependence",
        predict=_km_predictor(float(theta[0]), lambda T: float(theta[1])),
        declared_form=True,
        note=f"fitted k1={float(theta[0]):.3f}, constant k2={float(theta[1]):.3f}",
    )


def fit_free_form(train: Sequence[Query], y: FloatArray) -> Contestant:
    """**Contestant 1** — the v1.3 incumbent: free-form, generic structure only
    (ADR-045). A quadratic response surface in `(ρ₀, ln γ̇, T)` with positivity
    enforced architecturally through `omi.constraints.positive` (Spec §2.2), fitted
    by least squares.

    Deliberately *not* a straw man: the feature set includes `ln γ̇`, which is the
    functional form the withheld term actually takes, so the free-form contestant is
    given the chance to learn the missing physics from in-envelope data. It cannot,
    because the term is identically zero there — which is the point of the
    experiment rather than a handicap imposed on it.
    """
    design = _quadratic_design(train)
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)

    def predict(q: Query, total_strain: float) -> float:
        row = _quadratic_design([q])[0]
        return float(max(row @ coefficients, 0.0)) * total_strain

    return Contestant(
        label="1_free_form",
        predict=predict,
        declared_form=False,
        note=f"quadratic surface in (rho0, ln rate, T), {design.shape[1]} terms, positivity enforced",
    )


def _quadratic_design(queries: Sequence[Query]) -> FloatArray:
    rows = []
    for q in queries:
        r, lr, t = q.rho_0, float(np.log(q.strain_rate)), q.temperature / GEN_T_REF
        rows.append([1.0, r, lr, t, r * r, lr * lr, t * t, r * lr, r * t, lr * t])
    return np.array(rows)


def fit_tabular(train: Sequence[Query], y: FloatArray, regressor: object) -> Contestant:
    """**Contestant 4** — a tabular baseline from `omi.baseline`, unchanged
    (ADR-045; Spec §9.3's required baseline comparison). Fitted on the same
    in-envelope data as everyone else."""
    features = np.array([q.features for q in train])
    regressor.fit(features, y)  # type: ignore[attr-defined]

    def predict(q: Query, total_strain: float) -> float:
        return float(regressor.predict(q.features[np.newaxis, :])[0]) * total_strain  # type: ignore[attr-defined]

    return Contestant(
        label=f"4_tabular_{type(regressor).__name__}",
        predict=predict,
        declared_form=False,
        note=f"{type(regressor).__name__} from omi.baseline, unchanged",
    )
