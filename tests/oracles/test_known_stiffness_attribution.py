"""Does Core §3.3's stated ATTRIBUTION hold? (M10.4 Phase 3, sharpened.)

Core §3.3 names exactly one cause: "Violation of semigroup consistency under
sub-interval resampling is a cheap, automatable proxy for insufficiency of
`𝒮`." Spec §9.2 then makes that residual one of nine automated conformance
checks. The sharpened question is therefore not "does residual grow with
stiffness" but: **if a provably sufficient state produces residual that grows
with timescale separation, the attribution is confounded and a conformance
check is reporting an ambiguous quantity.**

The oracle makes sufficiency exact rather than assumed — both decay modes are
explicit components of the state, so the description is Markovian by
construction and there is no hidden variable for a residual to be blamed on.

**Outcome: REFUTED.** At exact sufficiency, with the explicit integrator inside
its stability limit throughout, the residual is *flat* in the stiffness ratio
across three orders of magnitude (spread 1.58×, and slightly decreasing). The
mechanism is physical and is visible in the per-component decomposition: the
fast mode is annihilated identically in the coarse and the fine evaluation once
it is stiff, so it drops out of the residual entirely, leaving the slow mode's
error, which is stiffness-independent by construction.

Two things the sweep did establish, neither of them the predicted confound:
the answer is **metric-dependent** — normalising by the *outgoing* population's
per-component σ manufactures a spurious fourteen-order-of-magnitude apparent
growth, while ADR-002's *incoming*-population convention cannot, being
stiffness-independent by construction; and a fixed-step-size operator scores
*exactly* zero at every stiffness ratio when the split point is commensurable
with its internal step, which Spec §9.2's own "random sub-interval splits"
wording already guards against but this repository's fixed split points do not.
Recorded in `docs/PHYSICS-ADEQUACY.md` §3.5 and in `docs/V1.4-EDITS.md` E-33.
"""

from __future__ import annotations

import numpy as np

from omi.learning import DeepONetOperator, TrainingRecord, init_deeponet_params, train_deeponet
from omi.operators import Control, semigroup_residual
from omi.state import Ensemble, Metric, State

from tests.conftest import ObservationRecorder
from tests.oracles.known_stiffness import (
    DECOUPLED_SCHEMA,
    ExactFlowOperator,
    FixedStepOperator,
    decoupled_generator,
    metric_semigroup_residual,
)

STIFFNESS_RATIOS = (1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
"""Three orders of magnitude, exceeding the two the design calls for."""

INTERVAL = Control(0.0, 1.0, lambda t: np.array([0.0]))
"""One slow timescale — the step an implementer sizes to the process being
modelled. The control value is unused: the generator is autonomous, so the
sweep isolates timescale separation from any control-coupling effect."""

T_MID = 0.5
N_SUBSTEPS = 1024
"""Chosen so the explicit integrator stays inside its stability limit at every
ratio swept (`max λ·h = 1000/1024 = 0.977 < 2`), because the single largest
trap in this measurement is mistaking integrator divergence for a consistency
error."""

INITIAL = State(DECOUPLED_SCHEMA, np.array([1.0, 1.0]))
"""Both modes excited, so neither is trivially absent from the residual."""

LEARNED_ARM_RATIOS = (1.0, 10.0, 100.0, 1000.0)
"""A four-point subset for variant (c), spanning three decades. The learned arm
needs one training run per ratio, and
its two findings are a *flatness* in the ratio and a *magnitude* comparison
against the analytic arm — neither needs a dense grid or a converged fit, and
the confound it carries (training quality) is reported alongside rather than
tuned away. The analytic arms, which actually adjudicate the attribution
question, keep the full grid. `scripts/run_m10_4_stiffness_sweep.py` reruns this
arm at a larger budget for the documented figures."""


def _population(seed: int = 0, n: int = 4000) -> Ensemble:
    rng = np.random.default_rng(seed)
    return Ensemble(DECOUPLED_SCHEMA, 1.0 + 0.2 * rng.standard_normal((n, 2)))


def test_null_exact_operator_has_zero_residual_at_every_stiffness_ratio(
    observe: ObservationRecorder,
) -> None:
    """**The null control, and it is not optional.** The exact analytic operator
    satisfies the semigroup identity identically at every stiffness ratio, so
    its residual must be at machine precision. If it were not, everything below
    would be measuring a harness bug rather than stiffness."""
    residuals = {
        f"{r:g}": semigroup_residual(ExactFlowOperator(decoupled_generator(r)), INITIAL, INTERVAL, T_MID)
        for r in STIFFNESS_RATIOS
    }
    worst = max(residuals.values())
    observe("null_exact_residuals", residuals, "all < 1e-12 (constructed truth: identically 0)")
    observe("null_exact_worst", worst, "< 1e-12")
    assert worst < 1e-12, "NULL FAILED — the harness is measuring a bug, not stiffness"


def test_residual_is_flat_in_stiffness_at_exact_sufficiency(observe: ObservationRecorder) -> None:
    """**The treatment, and the refutation.** A fixed-step-count explicit Euler
    operator over a provably sufficient state: the coarse (whole-interval) call
    takes larger substeps than the two fine (half-interval) calls, which is the
    "unresolved at the coarse step, resolved at the fine one" mechanism. The
    residual does *not* grow with the stiffness ratio.

    The per-component decomposition gives the reason, and it is physical: the
    slow component's contribution is stiffness-independent to every digit, while
    the fast component's rises briefly and then collapses super-exponentially —
    once the fast mode is stiff it is annihilated in the coarse and the fine
    evaluation alike, so their difference vanishes and it leaves the residual.
    """
    residuals, fast, slow, products = [], [], [], []
    for r in STIFFNESS_RATIOS:
        operator = FixedStepOperator(decoupled_generator(r), n_substeps=N_SUBSTEPS, scheme="euler")
        residuals.append(semigroup_residual(operator, INITIAL, INTERVAL, T_MID))
        direct = operator.step(INITIAL, INTERVAL)
        composed = operator.step(
            operator.step(INITIAL, Control(0.0, T_MID, INTERVAL.fn)), Control(T_MID, 1.0, INTERVAL.fn)
        )
        per_component = np.abs(direct.values - composed.values)
        fast.append(float(per_component[0]))
        slow.append(float(per_component[1]))
        products.append(operator.max_step_product(1.0))

    labels = [f"{r:g}" for r in STIFFNESS_RATIOS]
    spread = max(residuals) / min(residuals)
    observe("stiffness_ratios", labels, "three orders of magnitude")
    observe("residual_by_ratio", dict(zip(labels, residuals)), "spread < 3x (flat, not growing)")
    observe("residual_spread", spread, "< 3.0")
    observe("residual_last_over_first", residuals[-1] / residuals[0], "<= 1.0 (not growing)")
    observe("fast_component_by_ratio", dict(zip(labels, fast)), "collapses super-exponentially")
    observe("slow_component_by_ratio", dict(zip(labels, slow)), "stiffness-independent")
    observe("max_lambda_h_by_ratio", dict(zip(labels, products)), "all < 2 (Euler stable throughout)")

    assert max(products) < 2.0, "residual must be consistency error, not integrator divergence"
    # Flat across three decades, against a prediction of systematic growth.
    assert spread < 3.0
    assert residuals[-1] <= residuals[0]
    # The slow component carries the residual and does not vary with stiffness.
    assert max(slow) / min(slow) < 1.001
    # The fast component's contribution is annihilated at high stiffness.
    assert fast[-1] < 1e-30 * fast[0]


def test_answer_is_metric_dependent_and_an_outgoing_sigma_metric_manufactures_growth(
    observe: ObservationRecorder,
) -> None:
    """**The metric caveat (E-07/OQ-5), and it is the pivotal arm.**
    `omi.operators.semigroup_residual` returns a bare Euclidean norm and
    documents the choice as deliberate ("a diagnostic residual, not a
    metric-declared quantity"), while CLAUDE.md §5 invariant 1 holds that every
    *state distance* is metric-dependent — and a semigroup residual is a state
    distance.

    The two-mode system is exactly where that matters: the fast mode's variance
    collapses as stiffness grows. Normalising by the **outgoing** population's
    per-component σ therefore divides by a vanishing number and manufactures a
    spurious apparent growth of some fourteen orders of magnitude — which then
    collapses back only because σ underflows and the zero-variance guard fires.
    Normalising by the **incoming** population's σ, which is ADR-002's actual
    convention, is stiffness-independent by construction and reproduces the flat
    result. So the refutation above survives a change of metric, and the growth
    a careless normalisation would have reported is an artifact.
    """
    population = _population()
    incoming = Metric.from_ensemble(population)
    identity = Metric(DECOUPLED_SCHEMA, np.ones(2))

    raw, by_identity, by_incoming, by_outgoing = [], [], [], []
    for r in STIFFNESS_RATIOS:
        operator = FixedStepOperator(decoupled_generator(r), n_substeps=N_SUBSTEPS, scheme="euler")
        # The operator is linear in the state, so its action on the whole
        # population is one matmul against the matrix it realises — obtained by
        # stepping the two basis states. Exact in exact arithmetic, and equal to
        # per-particle stepping to floating-point rounding (largest component
        # difference measured at 2e-15, far below any figure reported here).
        # Stepping 4000 particles individually through 1024 substeps gives the
        # same answer at ~2000x the cost, and was this file's bottleneck: 76s
        # before this change, 2s after.
        realised = np.column_stack(
            [operator.step(State(DECOUPLED_SCHEMA, basis), INTERVAL).values for basis in np.eye(2)]
        )
        evolved = population.particles @ realised.T
        sigma = evolved.std(axis=0)
        outgoing = Metric(DECOUPLED_SCHEMA, np.where(sigma > 0, sigma, 1.0))

        raw.append(semigroup_residual(operator, INITIAL, INTERVAL, T_MID))
        by_identity.append(metric_semigroup_residual(operator, INITIAL, INTERVAL, T_MID, identity))
        by_incoming.append(metric_semigroup_residual(operator, INITIAL, INTERVAL, T_MID, incoming))
        by_outgoing.append(metric_semigroup_residual(operator, INITIAL, INTERVAL, T_MID, outgoing))

    labels = [f"{r:g}" for r in STIFFNESS_RATIOS]
    observe("incoming_sigma_metric_scale", incoming.scale.tolist(),
            "stiffness-independent by construction (ADR-002 uses the INCOMING population)")
    observe("residual_raw_no_metric", dict(zip(labels, raw)), "flat")
    observe("residual_identity_metric", dict(zip(labels, by_identity)), "flat")
    observe("residual_incoming_sigma_metric", dict(zip(labels, by_incoming)), "flat")
    observe("residual_outgoing_sigma_metric", dict(zip(labels, by_outgoing)),
            "spurious excursion > 1e10x — the artifact")
    observe("outgoing_metric_worst_over_first", max(by_outgoing) / by_outgoing[0], "> 1e10")
    observe("incoming_metric_spread", max(by_incoming) / min(by_incoming), "< 3.0")

    # The refutation survives every stiffness-independent metric.
    assert max(by_identity) / min(by_identity) < 3.0
    assert max(by_incoming) / min(by_incoming) < 3.0
    # And an outgoing-population normalisation manufactures growth that is not
    # in the dynamics at all.
    assert max(by_outgoing) / by_outgoing[0] > 1e10


def test_fixed_step_size_operator_passes_vacuously_on_a_commensurable_split(
    observe: ObservationRecorder,
) -> None:
    """A second, separate hazard found while running the sweep. An operator with
    a fixed *internal step size* traverses the same grid whether it is called
    once across the interval or twice across its halves, whenever the split
    point is commensurable with that step — so its residual is **identically
    zero at every stiffness ratio**, however wrong the operator is.

    Spec §9.2's own wording already guards against this: the check is specified
    "on **random** sub-interval splits", and a random split is almost surely
    incommensurable. So this is not a Specification defect — it is a hazard for
    any implementation that picks fixed split points, as this repository's own
    conformance usage does (`t_mid` values of 0.2/0.5/0.8 and 0.2/0.4/0.6/0.8,
    none randomised).

    How vacuous is measured, not asserted rhetorically: because `h` is held
    fixed here, `λ·h` grows with the ratio, so the high-ratio end of this sweep
    leaves explicit Euler's stability region and the operator's own output
    diverges. The commensurable residual is still exactly zero there — both the
    direct and the composed path diverge to the *same* wrong answer — so the
    check passes on an operator that has blown up by many orders of magnitude.
    """
    commensurable, incommensurable, diverged_magnitude = [], [], []
    for r in STIFFNESS_RATIOS:
        operator = FixedStepOperator(decoupled_generator(r), internal_step=0.01, scheme="euler")
        commensurable.append(semigroup_residual(operator, INITIAL, INTERVAL, 0.5))
        incommensurable.append(semigroup_residual(operator, INITIAL, INTERVAL, 0.3333))
        if operator.max_step_product(1.0) >= 2.0:
            diverged_magnitude.append(
                float(np.max(np.abs(operator.step(INITIAL, INTERVAL).values)))
            )

    labels = [f"{r:g}" for r in STIFFNESS_RATIOS]
    observe("fixed_step_size_commensurable_split", dict(zip(labels, commensurable)),
            "identically 0 at every ratio — a vacuous pass")
    observe("fixed_step_size_incommensurable_split", dict(zip(labels, incommensurable)),
            "nonzero; high-ratio entries are Euler divergence, not consistency error")
    observe("vacuous_pass_worst_diverged_output_magnitude", max(diverged_magnitude),
            "the check still reads 0 on an output this large (> 1e20)")

    assert all(x == 0.0 for x in commensurable)
    assert incommensurable[0] > 0.0
    # The pass survives even total divergence of the operator being checked.
    assert max(diverged_magnitude) > 1e20


def _learned_at_fixed_dt(stiffness_ratio: float, seed: int) -> DeepONetOperator:
    """Train a `DeepONetOperator` against the exact flow **at one `Δt` only**
    (the whole interval), so evaluating it at a split point asks it for a
    duration it never saw. `dt` is one of its branch inputs, so this is a
    genuine interpolation-in-`Δt` question rather than an architectural
    impossibility."""
    exact = ExactFlowOperator(decoupled_generator(stiffness_ratio))
    rng = np.random.default_rng(seed)
    records = []
    for i in range(24):
        values = rng.uniform(0.5, 1.5, size=2)
        nxt = exact.step(State(DECOUPLED_SCHEMA, values), INTERVAL)
        records.append(
            TrainingRecord(f"group{i}", values.copy(), (INTERVAL,), (values.copy(), nxt.values.copy()))
        )
    params = init_deeponet_params(
        state_dim=2, control_dim=1, rng=np.random.default_rng(seed + 1), latent_dim=16, hidden_dim=16
    )
    params, _report = train_deeponet(
        params, records, np.random.default_rng(seed + 2), n_epochs=100, learning_rate=0.05
    )
    return DeepONetOperator(params)


def test_learned_operator_trained_at_one_dt_reported_separately(observe: ObservationRecorder) -> None:
    """Variant (c), the realistic case — **reported separately from the
    fixed-step arm and never pooled with it**, because it is confounded with
    training quality in a way the analytic arms are not.

    A learned operator trained only at the whole-interval `Δt` and then asked
    for half-intervals shows a residual orders of magnitude above either
    analytic arm, and it is not a clean function of stiffness: what it mostly
    measures is that the network never saw the duration it is being asked for.
    That is the honest reading, and it is why this arm cannot adjudicate the
    attribution question the analytic arms settle.
    """
    ratios = LEARNED_ARM_RATIOS
    residuals, forward_errors = [], []
    for r in ratios:
        learned = _learned_at_fixed_dt(r, seed=int(r) + 7)
        residuals.append(semigroup_residual(learned, INITIAL, INTERVAL, T_MID))
        exact = ExactFlowOperator(decoupled_generator(r))
        forward_errors.append(
            float(
                np.linalg.norm(
                    learned.step(INITIAL, INTERVAL).values - exact.step(INITIAL, INTERVAL).values
                )
            )
        )

    labels = [f"{r:g}" for r in ratios]
    observe("learned_residual_by_ratio", dict(zip(labels, residuals)),
            "finite; confounded with training quality — not pooled with the analytic arms")
    observe("learned_forward_error_at_trained_dt", dict(zip(labels, forward_errors)),
            "the training-quality confound, reported alongside")
    observe("learned_residual_over_fixed_step_arm", max(residuals) / 8.987e-05,
            "orders of magnitude above the analytic arm")

    assert all(np.isfinite(x) for x in residuals)
    assert all(np.isfinite(x) for x in forward_errors)
