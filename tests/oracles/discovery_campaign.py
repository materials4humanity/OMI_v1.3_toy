"""Part 6's construction: a Bayesian-optimisation campaign on the discovery domain, in
three arms, with a planted **state** insufficiency introduced at a known step.

Design: ADR-064 (the operators), ADR-065 (the GP acquisition comparator and what it is
expected to do well), ADR-066 (the planted insufficiency and the campaign axis), ADR-063
(the statistic and why ADR-026 is extended rather than superseded). Read those before
reading this; every choice below is stated there.

**The three arms, one generator and two switches.**

| arm | hidden variable | observation noise |
|---|---|---|
| `NULL` | none | declared |
| `INSUFFICIENT` | `precursor_texture` per sample, outside `SDL_SCHEMA` | declared |
| `NOISY` | none | **inflated** by a calibrated factor |

`NOISY` is the arm that makes the pre-registered claim evaluable at all: the claim is
*insufficiency rather than exploration noise*, so the registered comparison is
`INSUFFICIENT` against `NOISY`, and a two-arm design cannot express it (ADR-065).

**Known by construction** (CLAUDE.md §7): `precursor_texture` is a scalar drawn at
preparation, absent from the declared schema, which scales the coarsening rate `Evaluation`
applies as `exp(tau)`. Two samples with identical declared post-calcination state and
identical evaluation control therefore have different futures, which is Axiom S failing with
respect to the declared state (Core §2.1) — and **not** a mis-specified operator, which is
the error Part 5(1)'s first construction made (ADR-066).

**The GP drives; the framework watches.** Both arms' campaigns are run by the same
GP-Expected-Improvement policy, so the framework's diagnostic never chooses its own samples.
That removes any reading in which the diagnostic looks good because it steered the campaign.

Cites Core §2.1 (Axiom S), Core §3.2 (the chain), Core §3.5 (the readout), Core §5 as
ADR-053 extends it (the attainable region a campaign may propose within), Spec §9.3 (the
baseline comparison), Spec §10 (the innovation sequence).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable

import numpy as np

from omi.assimilate import DataObservation, run_filter
from omi.baseline import GaussianProcessRegressor, expected_improvement
from omi.state import Ensemble, FloatArray, State

from omi_domains.sdl.build import (
    EVALUATION_TEMPERATURE,
    build_chain,
    build_incoming_ensemble,
    sample_attainable_compositions,
)
from omi_domains.sdl.readouts import TurnoverFrequency
from omi_domains.sdl.state import SDL_SCHEMA

N_EVALUATION_INTERVALS = 4
"""Time-on-stream intervals per sample — the *within*-sample axis, held fixed so the campaign
length is the only thing that moves (ADR-066)."""

OBSERVE_AT_END_ONLY = True
"""One activity measurement per sample, at the end of the declared time on stream.

**This is a correction to the construction's first version, and the reason is worth keeping.**
Observing at every interval gave the filter three chances to assimilate *within* the sample,
and it did: the EnKF corrected the state after the first observation, so innovations two
through four were near zero and the campaign-level mean was diluted by them. That is not a
defect of the filter — it is Core §3.9's condition (b) working — but it means a within-sample
innovation sequence is the wrong place to read a *cross-sample* insufficiency. What a campaign
cannot predict is the next sample, and the forecast innovation of a fresh sample is the
quantity that says so. It is also how a real campaign measures: one endpoint activity per
sample after a standard time on stream."""

TURNOVER_NOISE_SD = 0.06
"""Declared observation noise on the reactor test, in the readout's own units. The filter is
given exactly this value, so the innovation covariance it predicts is correct in the `NULL`
and `INSUFFICIENT` arms and wrong only in `NOISY` — where the extra scatter is undeclared,
which is what makes `NOISY` a nuisance the model does not know about."""

TEXTURE_SD = 0.35
"""`precursor_texture`'s spread, drawn **half-normal**: `|N(0, TEXTURE_SD)|`.

**One-sided, and that is a physical claim rather than a convenience.** The latent is a
precursor *disorder* density, which has a floor at zero — a perfect precursor — and can only
accelerate coarsening. So the arm-N value `0` is the physical floor rather than an arbitrary
midpoint, and the population's mean effect is **first order** in the latent.

The construction's first version drew it zero-mean and relied on `E[exp(tau)] > 1` for the
bias, which is second order in `TEXTURE_SD` and left the experiment underpowered — the
measured `z` was below the null arm's own scatter. ADR-066 records the change. The scope limit
it was recording still stands and is unchanged: **a signed monitor detects insufficiencies
with a non-zero mean effect and is blind to symmetric ones.**"""

CANDIDATE_POOL = 160
"""Attainable compositions the acquisition chooses from. A discrete pool rather than a
continuous optimiser: the acquisition maximum is then exact rather than a local optimum, so a
difference between arms cannot be an optimiser artefact."""

INITIAL_DESIGN = 4
"""Samples drawn at random before the acquisition takes over — identical across arms for a
given seed, which is what makes the arms one generator with two switches."""

FILTER_ENSEMBLE = 40
NEAR_SAMPLES = 8
FAR_SAMPLES = 32
"""The axis: campaign length in samples. Near and far are **prefixes of one campaign**
(ADR-066), so reading both costs one run and no seed-to-seed difference sits between them."""

N_REPLICATES = 24
"""Independent campaigns per arm. Supplies the null arm's own scatter, which is the
denominator of the separation (ADR-057's convention, reused so Part 5's and Part 6's
readings are on one scale)."""

GP_FEATURES = ("metal_a", "metal_b", "promoter")
"""The comparator's feature set: the three free composition coordinates. `support` is omitted
because the declared simplex makes it their complement, and handing a GP a linearly dependent
column is neither fairer nor more informative."""


class Arm(str, Enum):
    """The three arms (ADR-065, ADR-066)."""

    NULL = "null"
    INSUFFICIENT = "insufficient"
    NOISY = "noisy"


@dataclass(frozen=True)
class Sample:
    """One made-and-measured sample."""

    composition: dict[str, float]
    texture: float
    """The hidden `precursor_texture`. Available to the *measurement*, never to any model."""
    clean_turnover: FloatArray
    """``(N_EVALUATION_INTERVALS,)`` noise-free observable, for the axis-signal measurement."""
    observed_turnover: FloatArray
    """``(N_EVALUATION_INTERVALS,)`` what the campaign actually saw."""
    innovations: FloatArray
    """Signed innovations from the declared-model filter (Spec §10)."""
    predicted_variance: FloatArray
    """The filter's own predicted innovation variance at each observation — the quantity that
    makes the statistic standardised rather than merely signed (ADR-063)."""


@dataclass(frozen=True)
class Campaign:
    """One realised campaign of :attr:`samples`, in acquisition order."""

    arm: Arm
    noise_inflation: float
    samples: tuple[Sample, ...]

    def prefix(self, n: int) -> "Campaign":
        """The first *n* samples — the same campaign read at a shorter length (ADR-066)."""
        return replace(self, samples=self.samples[:n])


def _feature_row(composition: dict[str, float]) -> FloatArray:
    return np.array([composition[name] for name in GP_FEATURES], dtype=np.float64)


def _true_sample(
    composition: dict[str, float],
    texture: float,
    incoming: FloatArray,
    noise_sd: float,
    rng: np.random.Generator,
) -> tuple[FloatArray, FloatArray]:
    """Roll one sample under the **true** dynamics and observe it.

    The true evaluation operator carries `coarsening_scale = exp(texture)`. That is a
    per-sample multiplier on a rate, with the multiplier outside the declared schema — the
    shape ADR-066 requires and `tests/oracles/contrast_insufficiency.py` uses for the same
    reason. It is *not* a dependence on a declared state component, which is the operator
    error Part 5(1) planted first and had to withdraw.
    """
    chain = build_chain(composition, N_EVALUATION_INTERVALS, coarsening_scale=float(np.exp(texture)))
    trajectory = chain.rollout(Ensemble(SDL_SCHEMA, incoming[None, :]))
    readout = TurnoverFrequency()
    # Trajectory index 0 is the blank support, 1 the dried precursor, 2 the calcined material;
    # the evaluation intervals are therefore 3 .. 2 + N_EVALUATION_INTERVALS, and the observation
    # in `_filter_innovations` is placed at the last of them. Indexing this from 2 instead of 3
    # is what the construction did first, and it read the truth one interval before the forecast
    # — a spurious null-arm bias of a third of the observation noise, larger than the planted
    # effect and of the same sign, which showed up as the *null* arm having the higher statistic.
    clean = np.array(
        [
            float(readout.evaluate(State(SDL_SCHEMA, trajectory.ensembles[k].particles[0]))[0])
            for k in range(3, 3 + N_EVALUATION_INTERVALS)
        ]
    )
    observed = clean + rng.normal(0.0, noise_sd, size=clean.shape)
    return clean, observed


def _filter_innovations(
    composition: dict[str, float],
    observed: FloatArray,
    incoming: Ensemble,
    rng: np.random.Generator,
) -> tuple[FloatArray, FloatArray]:
    """Run the **declared** model's filter over one sample's observations (Spec §10).

    The declared model has `coarsening_scale = 1.0` and knows nothing of the texture, which
    is what makes the innovations informative about the missing component. The declared
    observation noise is :data:`TURNOVER_NOISE_SD` in every arm, including `NOISY` — a model
    told about the extra scatter would not be a model that has to detect it.
    """
    chain = build_chain(composition, N_EVALUATION_INTERVALS)
    observations = [
        DataObservation(
            name="turnover_end",
            readout=TurnoverFrequency(),
            noise_covariance=np.array([[TURNOVER_NOISE_SD**2]]),
            time_index=2 + N_EVALUATION_INTERVALS,
            value=np.array([observed[-1]]),
        )
    ]
    result = run_filter(chain, incoming, observations, rng)
    analyses = [result.analyses[k] for k in sorted(result.analyses)]
    return (
        np.array([float(a.innovation[0]) for a in analyses]),
        np.array([float(a.innovation_covariance[0, 0]) for a in analyses]),
    )


def run_campaign(
    n_samples: int,
    arm: Arm,
    seed: int,
    *,
    noise_inflation: float = 1.0,
) -> Campaign:
    """One GP-Expected-Improvement campaign of *n_samples* samples in *arm*.

    The acquisition is the comparator's (ADR-065): a GP with an ARD squared-exponential
    kernel and a fitted noise term, refitted at every step, maximising Expected Improvement
    over the remaining attainable candidates. The objective is the turnover frequency
    observed at the final evaluation interval, which is what an SDL campaign would optimise.

    Every candidate is inside the domain's **declared attainable region** (Core §5 as
    ADR-053 extends it), because a campaign can only make what exists — the region is
    *reported* rather than enforced by the framework, and this caller is the one asking.
    """
    rng = np.random.default_rng(seed)
    pool = sample_attainable_compositions(CANDIDATE_POOL, rng)
    support = build_incoming_ensemble(FILTER_ENSEMBLE, rng)
    noise_sd = TURNOVER_NOISE_SD * noise_inflation

    order = list(rng.permutation(len(pool))[:INITIAL_DESIGN])
    remaining = [i for i in range(len(pool)) if i not in order]

    samples: list[Sample] = []
    features: list[FloatArray] = []
    objective: list[float] = []

    while len(samples) < n_samples:
        if len(samples) >= INITIAL_DESIGN:
            gp = GaussianProcessRegressor()
            gp.fit(np.stack(features), np.array(objective))
            candidates = np.stack([_feature_row(pool[i]) for i in remaining])
            mean, sd = gp.predict_with_sd(candidates)
            acquisition = expected_improvement(mean, sd, float(max(objective)))
            chosen = remaining.pop(int(np.argmax(acquisition)))
        else:
            chosen = order[len(samples)]
            remaining = [i for i in remaining if i != chosen]

        composition = pool[chosen]
        texture = abs(float(rng.normal(0.0, TEXTURE_SD))) if arm is Arm.INSUFFICIENT else 0.0
        incoming = support.particles[len(samples) % support.n_particles]
        clean, observed = _true_sample(composition, texture, incoming, noise_sd, rng)
        innovations, variance = _filter_innovations(composition, observed, support, rng)

        samples.append(
            Sample(
                composition=composition,
                texture=texture,
                clean_turnover=clean,
                observed_turnover=observed,
                innovations=innovations,
                predicted_variance=variance,
            )
        )
        features.append(_feature_row(composition))
        objective.append(float(observed[-1]))

    return Campaign(arm=arm, noise_inflation=noise_inflation, samples=tuple(samples))


# --- the framework's statistic (ADR-063) -------------------------------------


@dataclass(frozen=True)
class InnovationMeanReport:
    """The standardised signed innovation mean, with everything ADR-063 requires reported
    alongside it — never the statistic alone, and never without its **sign**, which is
    E-49's finding applied to this monitor's own report."""

    signed_mean: float
    pooled_variance: float
    n_innovations: int
    z: float

    @property
    def direction(self) -> str:
        """Which way the innovations are biased. E-49's whole content is that a monitor
        recording no direction cannot say which response is indicated, so this monitor
        records one."""
        if self.signed_mean > 0.0:
            return "model_under_predicts"
        if self.signed_mean < 0.0:
            return "model_over_predicts"
        return "unbiased"


def innovation_mean_report(campaign: Campaign) -> InnovationMeanReport:
    """`z_n = |mean(d)| / sqrt(mean(S)/n)` over the campaign's pooled innovations
    (Spec §10's sufficient statistic; ADR-063).

    Pooled over the campaign rather than over a sliding window, because this monitor answers
    a campaign question and a window would discard the accumulation that makes `n` the axis
    (ADR-063). ADR-026's windowed chi-squared monitor is unchanged and still the default.
    """
    innovations = np.concatenate([s.innovations for s in campaign.samples])
    variances = np.concatenate([s.predicted_variance for s in campaign.samples])
    n = int(innovations.size)
    signed_mean = float(innovations.mean())
    pooled = float(variances.mean())
    standard_error = float(np.sqrt(pooled / n))
    return InnovationMeanReport(
        signed_mean=signed_mean,
        pooled_variance=pooled,
        n_innovations=n,
        z=abs(signed_mean) / standard_error if standard_error > 0.0 else float("inf"),
    )


def predicted_growth_ratio(near: int = NEAR_SAMPLES, far: int = FAR_SAMPLES) -> float:
    """`sqrt(n_far / n_near)` — the growth ratio ADR-066 predicts **in closed form** before
    anything is run, because a persistent bias makes `z_n` scale as `sqrt(n)`.

    The same discipline `tests/oracles/known_decaying_sensitivity.py` uses for the dominance
    ratio: a measured divergence is worth much more when the value it should take was
    written down first.
    """
    return float(np.sqrt(far / near))


# --- the comparator's own diagnostic (ADR-065) -------------------------------


@dataclass(frozen=True)
class GpNoiseReport:
    """The GP comparator's own "something is unexplained" reading (ADR-065)."""

    fitted_noise: float
    """Fitted noise standard deviation in the readout's own units."""
    standardised_noise: float
    """The same quantity as a fraction of the campaign's own target spread."""

    @property
    def excess_ratio(self) -> float:
        """`fitted_noise / TURNOVER_NOISE_SD` — **the comparator's diagnostic**, and the
        reading a practitioner actually takes: "the GP thinks the noise is this many times
        my instrument's known precision, so something is unexplained."

        The construction's first version used :attr:`standardised_noise` instead, and it was
        confounded in the direction that *flattered* the framework: the insufficiency arm has
        a wider target spread, so dividing by that spread made the GP's reading come out
        *lower* under insufficiency than under the null. Normalising by the declared
        instrument precision instead is the fair comparison, and it is the one ADR-065
        promises. Recorded because a confound that favours the claim is the one that has to
        be found before the thresholds are set, not after.
        """
        return self.fitted_noise / TURNOVER_NOISE_SD


def gp_noise_report(campaign: Campaign) -> GpNoiseReport:
    """The GP comparator's fitted noise level (ADR-065).

    This is the comparator at its strongest, and deliberately so. Fitting the noise by
    marginal likelihood is what a practitioner using a GP actually does, and it is the
    mechanism by which a GP *absorbs* unexplained variance rather than flagging its source.
    Spec §9.3 requires a fair baseline and M11 established that a weakened one produces an
    uninterpretable result.
    """
    gp = GaussianProcessRegressor()
    gp.fit(
        np.stack([_feature_row(s.composition) for s in campaign.samples]),
        np.array([float(s.observed_turnover[-1]) for s in campaign.samples]),
    )
    return GpNoiseReport(fitted_noise=gp.fitted_noise, standardised_noise=gp.noise_ratio)


def best_found(campaign: Campaign) -> float:
    """The campaign's incumbent objective — reported so the comparator's *search* quality is
    visible and not quietly omitted. ADR-065 states plainly that the GP is expected to search
    well; a report that hid it would be arguing rather than measuring."""
    return float(max(float(s.observed_turnover[-1]) for s in campaign.samples))


# --- E-41's vacuity gate, on the domain the claim is made on ------------------


def axis_signal(campaign_i: Campaign, campaign_n: Campaign, n_samples: int) -> float:
    """E-41's first criterion: how far the **planted insufficiency itself** moves the
    observable over a campaign of *n_samples*, in units of the observation noise.

    **The axis differs in kind from Part 5(1)'s and the difference is stated rather than
    smoothed over.** On contrast the axis was campaign depth and the per-interval effect
    itself grew. Here the per-sample effect is constant by construction — samples are
    independent — and what grows is the *accumulated evidence*. So the axis signal is the
    mean effect times `sqrt(n)` over the noise, which is the detectable effect a campaign of
    that length carries. An axis whose content is accumulation rather than growth is still an
    axis; it is a different one, and E-41's wording covers only the first.
    """
    effect = float(
        np.mean([s.clean_turnover[-1] for s in campaign_i.samples[:n_samples]])
        - np.mean([s.clean_turnover[-1] for s in campaign_n.samples[:n_samples]])
    )
    return float(abs(effect) * np.sqrt(n_samples) / TURNOVER_NOISE_SD)


def separation(arm_values: FloatArray, null_values: FloatArray) -> float:
    """`|mean(arm) - mean(null)| / sd(null)` — null-arm sigma units, ADR-057's convention
    reused unchanged so Part 5's and Part 6's readings sit on one scale."""
    scatter = float(null_values.std())
    if scatter <= 0.0:
        return float("inf") if abs(float(arm_values.mean()) - float(null_values.mean())) > 0.0 else 0.0
    return float(abs(arm_values.mean() - null_values.mean()) / scatter)


@dataclass(frozen=True)
class VacuityReading:
    """One statistic's reading on the vacuity gate, at both campaign lengths.

    **Criterion 3 is evaluable here on one contrast and not on the other, and the distinction
    is the whole of it.** E-41's third criterion compares the candidate's separation against a
    baseline's. On the `INSUFFICIENT`-versus-`NULL` contrast — this gate's subject — both
    instruments have a separation, so criterion 3 can be and is evaluated. On the
    `INSUFFICIENT`-versus-`NOISY` contrast, the baseline comparison **is** the registered claim,
    so evaluating it at gate time would be a look at the pre-registered quantity; it is deferred
    to the sweep. The collision between E-41's precondition and a pre-registered comparative
    claim is filed as a framework finding rather than resolved by relaxing the criterion
    (ADR-065).
    """

    statistic: str
    axis_signal_near: float
    axis_signal_far: float
    separation_near: float
    separation_far: float
    mean_near: float
    mean_far: float
    null_mean_near: float
    null_mean_far: float
    """The statistic's reading on the **null** arm at each length, in its own units.

    Reported unconditionally, because for the comparator it is the substantive fairness check:
    a GP whose fitted noise equals the declared instrument precision when nothing is planted is
    correctly calibrated, which is a much stronger statement about the opponent than any
    separation threshold. A separation is a ratio and can be small because a denominator is
    large; these two numbers say what the instrument actually read."""

    @property
    def growth_ratio(self) -> float:
        """`separation(far) / separation(near)` — E-41's reported quantity."""
        if self.separation_near <= 0.0:
            return float("inf") if self.separation_far > 0.0 else 1.0
        if not (np.isfinite(self.separation_near) and np.isfinite(self.separation_far)):
            return float("nan")
        return self.separation_far / self.separation_near

    @property
    def own_growth(self) -> float:
        """How the statistic's own arm-I mean moves along the axis, in its own units."""
        if self.mean_near == 0.0:
            return float("inf") if self.mean_far != 0.0 else 1.0
        return self.mean_far / self.mean_near

    def verdict(
        self,
        required_growth: float,
        minimum_axis_signal: float = 1.0,
        baseline_separation_far: float | None = None,
    ) -> str:
        """E-41's three criteria, in E-41's order.

        *baseline_separation_far* is the comparator's separation on **this same contrast**. When
        it is omitted the verdict ends at `DIVERGING_BASELINE_DEFERRED`, which is not a pass: it
        names the criterion that was not evaluated, so a reader is never handed two criteria
        dressed as three.
        """
        if self.axis_signal_far <= minimum_axis_signal:
            return "INERT_AXIS"
        if not np.isfinite(self.growth_ratio):
            return "SEPARATION_UNBOUNDED"
        if self.growth_ratio < required_growth:
            return "PARALLEL"
        if baseline_separation_far is None:
            return "DIVERGING_BASELINE_DEFERRED"
        if self.separation_far <= baseline_separation_far:
            return "ADVERSE"
        return "DISCRIMINATING"

    def summary(self) -> str:
        return (
            f"{self.statistic}: axis signal {self.axis_signal_near:.2f} -> "
            f"{self.axis_signal_far:.2f} noise-widths; separation "
            f"{self.separation_near:.3f} -> {self.separation_far:.3f} "
            f"(growth {self.growth_ratio:.3f}); own mean {self.mean_near:.4g} -> "
            f"{self.mean_far:.4g} (growth {self.own_growth:.3f}); null mean "
            f"{self.null_mean_near:.4g} -> {self.null_mean_far:.4g}"
        )


def vacuity_gate(n_replicates: int = N_REPLICATES, seed0: int = 0) -> tuple[VacuityReading, ...]:
    """Re-verify E-41's precondition **on the discovery domain**, for the framework statistic
    and for the comparator's own diagnostic.

    Part 5(1)'s dry-run was on contrast. A statistic that discriminates on one chain and is
    inert on another is M11.4's failure exactly, so the precondition is re-run on the domain
    the claim will be made on. The `NOISY` arm is not touched here: it is the registered
    comparison and looking at it would be a peek.
    """
    insufficient = [run_campaign(FAR_SAMPLES, Arm.INSUFFICIENT, seed0 + r) for r in range(n_replicates)]
    null = [run_campaign(FAR_SAMPLES, Arm.NULL, seed0 + r) for r in range(n_replicates)]

    readings = []
    extractors: tuple[tuple[str, Callable[[Campaign], float]], ...] = (
        ("innovation_mean_z", lambda c: innovation_mean_report(c).z),
        ("gp_noise_excess_ratio", lambda c: gp_noise_report(c).excess_ratio),
    )
    for name, extract in extractors:
        near_i = np.array([extract(c.prefix(NEAR_SAMPLES)) for c in insufficient])
        near_n = np.array([extract(c.prefix(NEAR_SAMPLES)) for c in null])
        far_i = np.array([extract(c) for c in insufficient])
        far_n = np.array([extract(c) for c in null])
        readings.append(
            VacuityReading(
                statistic=name,
                axis_signal_near=float(
                    np.mean([axis_signal(i, n, NEAR_SAMPLES) for i, n in zip(insufficient, null)])
                ),
                axis_signal_far=float(
                    np.mean([axis_signal(i, n, FAR_SAMPLES) for i, n in zip(insufficient, null)])
                ),
                separation_near=separation(near_i, near_n),
                separation_far=separation(far_i, far_n),
                mean_near=float(near_i.mean()),
                mean_far=float(far_i.mean()),
                null_mean_near=float(near_n.mean()),
                null_mean_far=float(far_n.mean()),
            )
        )
    return tuple(readings)


def gate_verdict(readings: tuple[VacuityReading, ...], required_growth: float) -> str:
    """The framework statistic's verdict with all three of E-41's criteria evaluated on the
    `INSUFFICIENT`-versus-`NULL` contrast, using the GP comparator's separation on that same
    contrast as criterion 3's baseline.

    The registered claim's contrast is `INSUFFICIENT`-versus-`NOISY`, and criterion 3 there is
    deferred to the sweep — see :class:`VacuityReading`. Two contrasts, two verdicts, and
    conflating them is precisely what would let a favourable precondition be read as the claim.
    """
    candidate = next(r for r in readings if r.statistic == "innovation_mean_z")
    baseline = next(r for r in readings if r.statistic == "gp_noise_excess_ratio")
    return candidate.verdict(required_growth, baseline_separation_far=baseline.separation_far)
