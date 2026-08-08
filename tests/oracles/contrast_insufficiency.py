"""Two-arm construction for the Part 5(1) statistic dry-run: a contrast campaign in
which the declared state is either **sufficient** or **not**, with everything else
held identical.

ADR-057 (docs/DECISIONS.md) is the design and states every choice: why the planted
defect is a hidden *state* variable rather than a wrong rate constant, why the
separation is measured in null-arm sigma units, why the growth ratio rather than the
separation is the reported quantity, and why
`omi.proposed.holdout.check_hold_out_discriminates` is not called.

**Known by construction** (CLAUDE.md §7): a scalar latent per cell — a manufacturing
quality factor, outside `CONTRAST_SCHEMA` — scales two declared rates at once. Arm N
sets its variance to zero, so the two arms are one generator with one switch, exactly
as `strain_experiment.labels(..., k_drx=0.0)` produces M11.5's withheld-free truth.

**Why two rates and not one.** In contrast's declared model no single rate reaches both
the observation suite and the Class-B target: `potential` (the one evaluable modality)
is a function of lithium inventory loss and interface resistance, while `dendrite_risk`
is a function of concentration overpotential and SEI thickness. The two sets are
disjoint, so a latent modulating one rate is either invisible or irrelevant. Scaling
`porosity_rate` (which reaches the target through overpotential) and `resistance_rate`
(which reaches the observable through potential) together is the smallest defect that is
both detectable and consequential. **That the domain forces this is itself a finding**
about how thin "genuinely poor observation suite" (Core §7.2) can be — and it is
reported, not worked around.

Cites Core §2.1 (Axiom S, which the latent breaks), Core §3.1 (the slots the latent is
absent from), Core §7.2 (the contrast instantiation), Spec §1.2 (the deficit and its
matched-pair construction), Spec §9.3 (the baseline comparison), Spec §10 (the
innovation sequence).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np
from scipy.optimize import least_squares

from omi.assimilate import DataObservation, run_filter
from omi.baseline import GradientBoostedTreeRegressor, RidgeRegressor
from omi.chain import Chain, Segment
from omi.operators import Control
from omi.state import Ensemble, FloatArray, Metric, Slot, State
from omi.sufficiency import DeficitResult, sufficiency_deficit

from omi_domains.contrast.build import build_incoming_ensemble
from omi_domains.contrast.operators import CYCLING, CyclingStep
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi_domains.contrast.state import CONTRAST_SCHEMA

CURRENT = 2.0
CYCLE_DURATION = 1.0

LATENT_SD = 0.35
"""Arm I's hidden-variable spread. Arm N is this set to zero.

Sized so the latent's effect on the observable is comparable to — not dominant over —
the observation noise at the *near* depth, and clearly above it at the far depth. A
latent that swamps the noise everywhere would make every candidate statistic pass
trivially, which is M11.4's failure in the opposite direction."""

VOLTAGE_NOISE_SD = 0.02
"""Observation noise on the one evaluable declared modality. Identical in both arms —
this is the "exploration noise" the statistic must not mistake for insufficiency."""

N_CELLS = 240
N_REPLICATES = 40
"""Independent campaigns per arm, which supply the null arm's own scatter — the
denominator of ADR-057's separation."""

NEAR_DEPTH = 6
FAR_DEPTH = 24
"""The axis: campaign depth in intervals. Both are ordinary cycling of the declared
chain; nothing here extrapolates outside a declared bound, because the question is
whether the statistic's reading *grows*."""

DEFICIT_HORIZON = 6
"""Matched-history pairs are matched on the declared state at depth `k` and their
responses compared `DEFICIT_HORIZON` intervals later (Spec §1.2). Fixed rather than
proportional to `k`, so the axis is campaign depth alone."""


def _chain(depth: int) -> Chain:
    control = Control(0.0, CYCLE_DURATION, lambda t: np.array([CURRENT]))
    return Chain(tuple(Segment(CYCLING, control) for _ in range(depth)))


@dataclass(frozen=True)
class Campaign:
    """One realised campaign: the true trajectories, the realised observations, and the
    latent that generated them (available to the *measurement*, never to any model)."""

    depth: int
    latent: FloatArray
    """``(N_CELLS,)`` hidden quality factor. Identically zero in Arm N."""
    states: FloatArray
    """``(depth + 1, N_CELLS, 7)`` true declared-state trajectories."""
    voltage: FloatArray
    """``(depth + 1, N_CELLS)`` noisy terminal-voltage observations."""
    dendrite: FloatArray
    """``(depth + 1, N_CELLS)`` true Class-B target values."""


def _true_step(particles: FloatArray, latent: FloatArray) -> FloatArray:
    """Advance every cell one interval under the **true** dynamics: the declared
    `CyclingStep`, with `porosity_rate` and `resistance_rate` scaled per cell by
    ``1 + latent``.

    Vectorised re-expression of `CyclingStep.step` rather than a per-cell loop over it,
    because the latent makes the operator cell-dependent and `EvolutionOperator.lift`
    applies one operator to a whole ensemble by construction (Core §3.3). The arithmetic
    is the declared operator's, term for term.
    """
    op = CYCLING
    drive = abs(CURRENT) * CYCLE_DURATION
    scale = 1.0 + latent

    idx = {name: CONTRAST_SCHEMA.slice_for(slot, name) for slot, name, _ in CONTRAST_SCHEMA.components}
    out = particles.copy()

    porosity = particles[:, idx["electrode_porosity"]].ravel()
    li_loss = particles[:, idx["lithium_inventory_loss"]].ravel()
    sei = particles[:, idx["sei_thickness"]].ravel()
    cei = particles[:, idx["cei_thickness"]].ravel()
    resistance = particles[:, idx["collector_interface_resistance"]].ravel()

    new_porosity = porosity + op.porosity_rate * scale * drive
    new_li_loss = li_loss + op.li_loss_rate * drive
    new_sei = np.sqrt(sei**2 + op.sei_rate * drive)
    new_cei = np.sqrt(cei**2 + op.cei_rate * drive)
    new_resistance = resistance + op.resistance_rate * scale * drive
    new_potential = op.open_circuit_voltage - op.fade_gain * new_li_loss - CURRENT * new_resistance
    new_overpotential = op.overpotential_gain * abs(CURRENT) / (1.0 + new_porosity)

    for name, value in (
        ("electrode_porosity", new_porosity),
        ("lithium_inventory_loss", new_li_loss),
        ("sei_thickness", new_sei),
        ("cei_thickness", new_cei),
        ("collector_interface_resistance", new_resistance),
        ("potential", new_potential),
        ("concentration_overpotential", new_overpotential),
    ):
        out[:, idx[name]] = value.reshape(-1, 1)
    return out


def _dendrite(states: FloatArray) -> FloatArray:
    """`DendriteRisk` over a whole ``(steps, cells, size)`` block.

    Vectorised for speed only; the coefficients are read off the declared readout
    rather than restated, so the two cannot drift apart, and the clamp is the readout's
    own (a negative hazard is not physical).
    """
    risk = DendriteRisk()
    over = states[:, :, CONTRAST_SCHEMA.slice_for(Slot.NU, "concentration_overpotential")]
    sei = states[:, :, CONTRAST_SCHEMA.slice_for(Slot.GAMMA, "sei_thickness")]
    hazard = risk.overpotential_gain * over - risk.sei_protection_gain * sei
    return np.asarray(np.maximum(hazard, 0.0).reshape(states.shape[0], states.shape[1]), dtype=np.float64)


def run_campaign(depth: int, *, insufficient: bool, rng: np.random.Generator) -> Campaign:
    """Roll one campaign of *depth* intervals. ``insufficient=False`` is Arm N."""
    initial = build_incoming_ensemble(N_CELLS, rng)
    latent = rng.normal(0.0, LATENT_SD, size=N_CELLS) if insufficient else np.zeros(N_CELLS)

    states = np.empty((depth + 1, N_CELLS, CONTRAST_SCHEMA.size))
    states[0] = initial.particles
    for k in range(1, depth + 1):
        states[k] = _true_step(states[k - 1], latent)

    dendrite = _dendrite(states)

    potential_slice = CONTRAST_SCHEMA.slice_for(Slot.NU, "potential")
    clean = states[:, :, potential_slice].reshape(depth + 1, N_CELLS)
    voltage = clean + rng.normal(0.0, VOLTAGE_NOISE_SD, size=clean.shape)

    return Campaign(depth=depth, latent=latent, states=states, voltage=voltage, dendrite=dendrite)


# --- candidate 1: sufficiency deficit ----------------------------------------


def deficit_at(campaign: Campaign, depth: int, metric: Metric) -> DeficitResult:
    """Spec §1.2's three-term deficit, on pairs matched at *depth* and compared
    :data:`DEFICIT_HORIZON` intervals later.

    Matched on the **full declared state**, non-dimensionalised by *metric* (CLAUDE.md
    invariant 1), which is the construction that makes the measurement an oracle: with
    a sufficient state the deficit must collapse, and the only thing separating the two
    arms is whether a component is missing from that state.
    """
    later = depth + DEFICIT_HORIZON
    matched = campaign.states[depth] / metric.scale
    # Nearest distinct neighbour for each cell, then keep each unordered pair once.
    distances = np.linalg.norm(matched[:, None, :] - matched[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    partner = np.argmin(distances, axis=1)
    pairs = sorted({(min(i, int(j)), max(i, int(j))) for i, j in enumerate(partner)})
    a_index = np.array([p[0] for p in pairs])
    b_index = np.array([p[1] for p in pairs])

    response_a = campaign.dendrite[later, a_index]
    response_b = campaign.dendrite[later, b_index]
    component_diffs = campaign.states[depth][a_index] - campaign.states[depth][b_index]

    jacobian = DendriteRisk().jacobian(State(CONTRAST_SCHEMA, campaign.states[depth].mean(axis=0)))
    return sufficiency_deficit(
        response_a=response_a,
        response_b=response_b,
        matched_component_diffs=component_diffs,
        response_jacobian=jacobian.ravel(),
        repeat_variance=0.0,
    )


# --- candidate 2: innovation bias --------------------------------------------


def innovation_bias_at(campaign: Campaign, depth: int, rng: np.random.Generator) -> float:
    """The **signed** mean innovation over the campaign, normalised by its own predicted
    standard error (ADR-057).

    Deliberately not `omi.assimilate.innovation_drift_monitor`'s NIS: that statistic is
    squared and sign-blind, and a sequence biased by exactly the amount the model's own
    covariance predicts passes it. Spec §10's proposition is about the innovation
    sequence; which functional of it to test is `[Pass C]`.

    The filter runs the **declared** model — the latent-free `CyclingStep` — which is
    what makes the innovations informative about the missing component.
    """
    chain = _chain(depth)
    truth_cell = 0
    observations = [
        DataObservation(
            name=f"voltage_{k}",
            readout=TerminalVoltage(),
            noise_covariance=np.array([[VOLTAGE_NOISE_SD**2]]),
            time_index=k,
            value=np.array([campaign.voltage[k, truth_cell]]),
        )
        for k in range(1, depth + 1)
    ]
    initial = Ensemble(CONTRAST_SCHEMA, campaign.states[0].copy())
    result = run_filter(chain, initial, observations, rng)
    analyses = [result.analyses[k] for k in sorted(result.analyses)]
    innovations = np.array([float(a.innovation[0]) for a in analyses])
    predicted = np.array([float(a.innovation_covariance[0, 0]) for a in analyses])
    standard_error = float(np.sqrt(predicted.mean() / innovations.size))
    return float(abs(innovations.mean()) / standard_error)


# --- candidate 3: parameter spread -------------------------------------------

_RATE_TRUTH = np.array([CYCLING.li_loss_rate, CYCLING.resistance_rate])
_RATE_NAMES = ("li_loss_rate", "resistance_rate")


def _voltage_of_rates(rates: FloatArray, initial: FloatArray, depth: int) -> FloatArray:
    """Declared-model terminal voltage at every interval for a candidate rate pair.

    Only the two rates the **observation suite can see** are fitted: `potential` is a
    function of lithium inventory loss and interface resistance and of nothing else, so
    `porosity_rate` — the other rate the latent modulates — is not identifiable from
    voltage at any depth. That asymmetry is the point of candidate 3 and is reported
    rather than removed.
    """
    op = replace(CyclingStep(), li_loss_rate=float(rates[0]), resistance_rate=float(rates[1]))
    drive = abs(CURRENT) * CYCLE_DURATION
    idx = {name: CONTRAST_SCHEMA.slice_for(slot, name) for slot, name, _ in CONTRAST_SCHEMA.components}
    li = initial[:, idx["lithium_inventory_loss"]].ravel().copy()
    res = initial[:, idx["collector_interface_resistance"]].ravel().copy()
    out = np.empty((depth, initial.shape[0]))
    for k in range(depth):
        li = li + op.li_loss_rate * drive
        res = res + op.resistance_rate * drive
        out[k] = op.open_circuit_voltage - op.fade_gain * li - CURRENT * res
    return out


def parameter_spread_at(campaign: Campaign, depth: int, rng: np.random.Generator, n_boot: int = 24) -> float:
    """Across-bootstrap relative spread of the extrapolated observable at ``2 * depth``,
    divided by the same spread in-window — ADR-055's parameter triage in its smallest
    honest form.

    A *spread*, not a danger score: the influence-times-uncertainty product needs the
    parameter information matrix ADR-055 designs and Part 5(1) does not build.
    """
    initial = campaign.states[0]
    fitted = np.empty((n_boot, 2))
    for b in range(n_boot):
        draw = rng.integers(0, N_CELLS, size=N_CELLS)
        target = campaign.voltage[1 : depth + 1][:, draw]
        sub = initial[draw]
        result = least_squares(
            lambda p: (_voltage_of_rates(p, sub, depth) - target).ravel(),
            _RATE_TRUTH * 0.5,
            bounds=(0.0, np.inf),
            xtol=1e-10,
            ftol=1e-10,
        )
        fitted[b] = result.x

    def relative_spread(horizon: int) -> float:
        predictions = np.stack([_voltage_of_rates(theta, initial, horizon)[-1] for theta in fitted])
        return float(np.mean(predictions.std(axis=0) / np.abs(predictions.mean(axis=0))))

    inner = relative_spread(depth)
    if inner <= 0.0:
        return float("inf")
    return relative_spread(2 * depth) / inner


# --- the Spec §9.3 baseline --------------------------------------------------


def baseline_residual_scale(campaign: Campaign, depth: int) -> float:
    """The tabular baseline's held-out predictive residual scale at *depth* — the one
    quantity a tabular surrogate emits that a practitioner would read as "is my model
    insufficient" (Spec §9.3's required comparison; ADR-039's numpy baselines).

    **Grouped, never random** (CLAUDE.md invariant 6): the split is by cell, so no cell
    contributes rows to both sides. A cell is the provenance unit here — it carries the
    latent.

    **Fixed feature dimension at every depth**, deliberately: five summaries of the
    voltage history (first, last, total drop, mean, spread) rather than one column per
    interval. Handing the baseline `depth` raw columns would make its capacity grow with
    the axis, so its residual scale would move between the near and the far probe for a
    reason that has nothing to do with insufficiency — and the growth ratio the whole
    dry-run turns on would be confounded by it.

    The brief asked for a GP baseline; this repository has none and ADR-057 records why
    one is not added. Gradient-boosted trees are the primary Spec §9.3 comparator and
    are what M10.2 and M11.5 used, so the substitution keeps the numbers comparable.
    """
    half = N_CELLS // 2
    history = campaign.voltage[: depth + 1]
    features_all = np.stack(
        [history[0], history[-1], history[0] - history[-1], history.mean(axis=0), history.std(axis=0)],
        axis=1,
    )
    target = campaign.dendrite[depth + DEFICIT_HORIZON]

    scores = []
    for model in (GradientBoostedTreeRegressor(), RidgeRegressor()):
        model.fit(features_all[:half], target[:half])
        predicted = model.predict(features_all[half:])
        scores.append(float(np.sqrt(np.mean((predicted - target[half:]) ** 2))))
    return min(scores)


# --- assembling the dry-run --------------------------------------------------

CANDIDATES = ("deficit", "innovation_bias", "parameter_spread")


def readings(depth: int, *, insufficient: bool, seed: int) -> dict[str, float]:
    """Every candidate statistic plus the baseline, for one campaign."""
    rng = np.random.default_rng(seed)
    campaign = run_campaign(depth + DEFICIT_HORIZON, insufficient=insufficient, rng=rng)
    metric = Metric.from_ensemble(Ensemble(CONTRAST_SCHEMA, campaign.states[0]))
    return {
        "deficit": deficit_at(campaign, depth, metric).deficit_squared,
        "innovation_bias": innovation_bias_at(campaign, depth, rng),
        "parameter_spread": parameter_spread_at(campaign, depth, rng),
        "baseline": baseline_residual_scale(campaign, depth),
    }


def arm_readings(depth: int, *, insufficient: bool, seed0: int = 0) -> dict[str, FloatArray]:
    """`N_REPLICATES` independent campaigns for one arm at one depth."""
    rows = [
        readings(depth, insufficient=insufficient, seed=seed0 + r * 1000 + depth)
        for r in range(N_REPLICATES)
    ]
    return {key: np.array([row[key] for row in rows]) for key in rows[0]}


def axis_signal(depth: int, *, seed: int = 7) -> float:
    """How far the **planted insufficiency itself** moves the observable at *depth*, in
    units of the observation noise (ADR-057's first criterion, E-41's axis signal).

    Arm I's and Arm N's noise-free observable trajectories, differenced, with the same
    initial population and the same latent draw switched off — one generator, one
    switch. Zero would mean an inert axis and nothing for any statistic to read.
    """
    rng_i = np.random.default_rng(seed)
    rng_n = np.random.default_rng(seed)
    arm_i = run_campaign(depth, insufficient=True, rng=rng_i)
    arm_n = run_campaign(depth, insufficient=False, rng=rng_n)
    potential = CONTRAST_SCHEMA.slice_for(Slot.NU, "potential")
    clean_i = arm_i.states[depth, :, potential].ravel()
    clean_n = arm_n.states[depth, :, potential].ravel()
    return float(np.sqrt(np.mean((clean_i - clean_n) ** 2)) / VOLTAGE_NOISE_SD)


@dataclass(frozen=True)
class DryRunVerdict:
    """One candidate's dry-run result. Every field reported whatever the verdict, per
    CLAUDE.md §8 and E-41's own reporting discipline: a rejected candidate's margin
    says whether it was close."""

    candidate: str
    axis_signal_near: float
    axis_signal_far: float
    separation_near: float
    separation_far: float
    baseline_separation_near: float
    baseline_separation_far: float
    arm_i_mean_near: float
    arm_i_mean_far: float
    """The candidate's own mean reading under Arm I at each depth, in its own units.

    Reported unconditionally because the separation can be **unbounded** — a statistic
    identically zero under the null gives a zero-scatter denominator — and when it is,
    these two numbers are the only well-defined statement about whether the candidate
    rises or falls along the axis."""
    verdict: str

    @property
    def growth_ratio(self) -> float:
        """`separation(far) / separation(near)` — ADR-057's reported quantity, and
        E-41's: "an extrapolation test measures what happens as you go further; its
        precondition has to be about divergence, not difference."

        ``nan`` when either separation is unbounded, which is a real case rather than an
        error: see :attr:`arm_i_growth` and the ``SEPARATION_UNBOUNDED`` verdict.
        """
        if not (np.isfinite(self.separation_near) and np.isfinite(self.separation_far)):
            return float("nan")
        if self.separation_near <= 0.0:
            return float("inf") if self.separation_far > 0.0 else 1.0
        return self.separation_far / self.separation_near

    @property
    def arm_i_growth(self) -> float:
        """How the candidate's own Arm I reading moves along the axis, in its own units.

        The fallback divergence reading when the sigma-unit separation is unbounded. It
        is **not** a substitute for the separation — it says nothing about the null arm —
        but a value below 1 settles the divergence question on its own: a statistic whose
        raw magnitude *falls* as the campaign deepens is not a rising trend under any
        normalisation.
        """
        if self.arm_i_mean_near == 0.0:
            return float("inf") if self.arm_i_mean_far != 0.0 else 1.0
        return self.arm_i_mean_far / self.arm_i_mean_near

    @property
    def baseline_growth(self) -> float:
        """The Spec §9.3 baseline's own divergence along the same axis — the comparison
        that matters for a *trend* statistic, as distinct from comparing separations at
        the far point alone."""
        if self.baseline_separation_near <= 0.0:
            return float("inf") if self.baseline_separation_far > 0.0 else 1.0
        return self.baseline_separation_far / self.baseline_separation_near

    def summary(self) -> str:
        return (
            f"{self.candidate}: axis signal {self.axis_signal_near:.2f} -> "
            f"{self.axis_signal_far:.2f} noise-widths; separation "
            f"{self.separation_near:.3f} -> {self.separation_far:.3f} "
            f"(growth {self.growth_ratio:.3f}); arm-I mean "
            f"{self.arm_i_mean_near:.4g} -> {self.arm_i_mean_far:.4g} "
            f"(growth {self.arm_i_growth:.3f}); baseline separation "
            f"{self.baseline_separation_near:.3f} -> {self.baseline_separation_far:.3f} "
            f"-> {self.verdict}"
        )


def _separation(arm_i: FloatArray, arm_n: FloatArray) -> float:
    """`|mean(Arm I) - mean(Arm N)| / sd(Arm N)` — the reading in null-arm sigma units
    (ADR-057), which is the only unit the three candidates share."""
    scatter = float(arm_n.std())
    if scatter <= 0.0:
        return float("inf") if abs(float(arm_i.mean()) - float(arm_n.mean())) > 0.0 else 0.0
    return float(abs(arm_i.mean() - arm_n.mean()) / scatter)


SEPARATION_UNBOUNDED = "SEPARATION_UNBOUNDED"
"""A fifth outcome E-41's three-failure enum does not name.

The sigma-unit separation is `|Δmean| / sd(null)`, and a statistic that is **identically
zero under the null** — which is what a *good* insufficiency detector looks like — gives
a zero denominator, so the criterion E-41 requires cannot be evaluated at all. This is
distinct from all three of `HoldOutVerdict`'s failures: the axis is not inert, the models
are not parallel, and the candidate is not adverse. The criterion is simply undefined.
`HoldOutDiscriminationReport.divergence` handles a zero *numerator* (returning `inf`);
nothing handles a zero *denominator*, because in a model comparison the denominator is a
disagreement between two predictors and never a null arm's scatter.

Reported as its own outcome rather than resolved by substituting a different
denominator, which would answer a question the caller did not ask. Filed as a framework
finding against E-39/E-41's proposed Spec §9.3 wording."""


def dry_run(required_growth: float, minimum_axis_signal: float = 1.0) -> tuple[DryRunVerdict, ...]:
    """Run the dry-run for every candidate at both depths.

    *required_growth* is the declared minimum divergence, supplied by the caller and
    **not** fixed by this module — Part 6's pre-registration owns thresholds (ADR-057).

    Criteria are checked in E-41's order, because an inert axis makes a growth ratio
    meaningless and a flat statistic makes the sign of a baseline comparison
    uninformative — with :data:`SEPARATION_UNBOUNDED` inserted **before** the divergence
    test, since a criterion that cannot be evaluated must not fall through it. A `nan`
    silently failing a `<` comparison is exactly how an unevaluable criterion becomes a
    pass.
    """
    signal_near, signal_far = axis_signal(NEAR_DEPTH), axis_signal(FAR_DEPTH)
    near_i, near_n = arm_readings(NEAR_DEPTH, insufficient=True), arm_readings(NEAR_DEPTH, insufficient=False)
    far_i, far_n = arm_readings(FAR_DEPTH, insufficient=True), arm_readings(FAR_DEPTH, insufficient=False)
    baseline_near = _separation(near_i["baseline"], near_n["baseline"])
    baseline_far = _separation(far_i["baseline"], far_n["baseline"])

    verdicts = []
    for name in CANDIDATES:
        report = DryRunVerdict(
            candidate=name,
            axis_signal_near=signal_near,
            axis_signal_far=signal_far,
            separation_near=_separation(near_i[name], near_n[name]),
            separation_far=_separation(far_i[name], far_n[name]),
            baseline_separation_near=baseline_near,
            baseline_separation_far=baseline_far,
            arm_i_mean_near=float(near_i[name].mean()),
            arm_i_mean_far=float(far_i[name].mean()),
            verdict="DISCRIMINATING",
        )
        if signal_far <= minimum_axis_signal:
            verdict = "INERT_AXIS"
        elif not np.isfinite(report.growth_ratio):
            verdict = SEPARATION_UNBOUNDED
        elif report.growth_ratio < required_growth:
            verdict = "PARALLEL"
        elif report.separation_far <= baseline_far:
            verdict = "ADVERSE"
        else:
            verdict = "DISCRIMINATING"
        verdicts.append(replace(report, verdict=verdict))
    return tuple(verdicts)
