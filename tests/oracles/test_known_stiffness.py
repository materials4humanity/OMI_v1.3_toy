"""The stiffness sweep: Core §3.3's semigroup residual against timescale
separation (M10.4 Phase 3; `docs/PHYSICS-ADEQUACY.md` §3.5's proposed test).

The prediction under test, quoted from that assessment: "semigroup residual
should grow systematically with timescale separation" — because "an operator
learned at one `Δt` composes badly at another, because the fast mode is
unresolved at the coarse step and dominant at the fine one."

**Outcome: refuted as stated, in both fast-mode regimes, and the way it fails
is the finding.** With a decaying stiff transient the residual does not depend
on the separation ratio at all. With a persistently excited (oscillatory) stiff
mode it varies by four orders of magnitude, but *non-monotonically* — it peaks
where the fast mode is marginally resolved and collapses at both extremes. So
the residual's magnitude is not a monotone function of stiffness in either
regime, and a small residual certifies neither adequate temporal resolution nor
state sufficiency. Recorded in `docs/V1.4-EDITS.md` E-33.
"""

from __future__ import annotations

import numpy as np

from omi.operators import Control, semigroup_residual

from tests.conftest import ObservationRecorder
from tests.oracles import Oracle
from tests.oracles.known_stiffness import (
    ExactFlowOperator,
    FixedResolutionOperator,
    KnownStiffnessOracle,
    LiftProjectOperator,
)

SEPARATION_RATIOS = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0)
"""Swept over almost three decades of timescale separation."""

INTERVAL = Control(0.0, 1.0, lambda t: np.array([0.0]))
"""One slow timescale — the step an implementer sizes to the process being
modelled. The control value is unused: these generators are autonomous, so the
sweep isolates timescale structure from any control-coupling effect."""

T_MID = 0.5


def test_known_stiffness_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownStiffnessOracle(), Oracle)


def test_exact_flow_has_zero_semigroup_residual_at_every_separation_ratio(
    observe: ObservationRecorder,
) -> None:
    """The control arm, and the oracle's constructed truth: stiffness *alone*
    produces no semigroup residual. Without this, a residual measured in the
    arms below could not be attributed to the approximation rather than to the
    physics being stiff."""
    residuals = {}
    for oscillatory in (False, True):
        for ratio in SEPARATION_RATIOS:
            oracle = KnownStiffnessOracle(ratio, oscillatory=oscillatory)
            operator = ExactFlowOperator(oracle.generator())
            residuals[f"{'osc' if oscillatory else 'decay'}_{ratio:g}"] = semigroup_residual(
                operator, oracle.initial_state(), INTERVAL, T_MID
            )

    worst = max(residuals.values())
    observe("exact_flow_semigroup_residuals", residuals, "all < 1e-12 (constructed truth: exactly 0)")
    observe("exact_flow_worst_residual", worst, "< 1e-12")
    assert worst < 1e-12, "an exact matrix-exponential flow must satisfy the semigroup identity"


def test_stiffness_does_not_systematically_grow_the_residual_for_a_decaying_fast_mode(
    observe: ObservationRecorder,
) -> None:
    """Arm A of the sweep, and the first half of the refutation: with the fast
    mode a *decaying transient*, the residual is flat in the separation ratio.

    The mechanism, which is why this is a physical result and not a numerical
    accident: the unresolved mode's amplitude decays as fast as its rate grows,
    so it contributes to the error only over a vanishing initial window. The
    two effects cancel.
    """
    residuals = []
    drifts = []
    for ratio in SEPARATION_RATIOS:
        oracle = KnownStiffnessOracle(ratio)
        operator = FixedResolutionOperator(oracle.generator())
        state = oracle.initial_state()
        residuals.append(semigroup_residual(operator, state, INTERVAL, T_MID))
        drifts.append(operator.norm_drift(state, INTERVAL))

    spread = max(residuals) / min(residuals)
    observe("decaying_residuals_by_ratio", dict(zip([f"{r:g}" for r in SEPARATION_RATIOS], residuals)),
            "max/min spread < 10 (flat, not systematically growing)")
    observe("decaying_residual_spread", spread, "< 10")
    observe("decaying_norm_drift_worst", max(drifts), "< 1e-3 (integrator not diverging)")

    assert max(drifts) < 1e-3, "residual must be consistency error, not integrator divergence"
    # Flat across three decades of separation: less than one order of magnitude
    # of spread, against a prediction of systematic growth.
    assert spread < 10.0
    # And specifically not growing: the highest ratio is no worse than the lowest.
    assert residuals[-1] <= residuals[0]


def test_residual_is_non_monotone_in_separation_for_a_persistently_excited_fast_mode(
    observe: ObservationRecorder,
) -> None:
    """Arm B, and the second half: with the fast mode *persistently excited*,
    the residual does move with the separation ratio — by four orders of
    magnitude — but it **peaks** at intermediate separation and collapses at
    both extremes, so it is not the systematic growth predicted.

    Physically: the residual is largest where the fast mode is *marginally*
    resolved. Where it is well resolved, both the whole-interval and split-
    interval answers are accurate; where it is grossly under-resolved, both are
    wrong in the same way and their difference shrinks again.
    """
    residuals = []
    drifts = []
    for ratio in SEPARATION_RATIOS:
        oracle = KnownStiffnessOracle(ratio, oscillatory=True)
        operator = FixedResolutionOperator(oracle.generator())
        state = oracle.initial_state()
        residuals.append(semigroup_residual(operator, state, INTERVAL, T_MID))
        drifts.append(operator.norm_drift(state, INTERVAL))

    peak_index = int(np.argmax(residuals))
    observe("oscillatory_residuals_by_ratio", dict(zip([f"{r:g}" for r in SEPARATION_RATIOS], residuals)),
            "interior peak: rises then falls; peak/first > 100 and peak/last > 100")
    observe("oscillatory_peak_separation_ratio", SEPARATION_RATIOS[peak_index], "strictly interior to the sweep")
    observe("oscillatory_rise_to_peak", residuals[peak_index] / residuals[0], "> 100")
    observe("oscillatory_fall_from_peak", residuals[peak_index] / residuals[-1], "> 100")
    observe("oscillatory_norm_drift_worst", max(drifts), "< 1e-2 (integrator not diverging)")

    assert max(drifts) < 1e-2, "residual must be consistency error, not integrator divergence"
    # The peak is strictly interior: the residual both rises and falls across
    # the swept range, so it is not monotone in the separation ratio.
    assert 0 < peak_index < len(residuals) - 1
    assert residuals[peak_index] / residuals[0] > 100.0
    assert residuals[peak_index] / residuals[-1] > 100.0


def test_insufficiency_produces_residual_that_falls_with_separation_confounding_the_diagnostic(
    observe: ObservationRecorder,
) -> None:
    """Arm C, the confound. Core §3.3 attributes semigroup-residual violation
    to one cause: "a cheap, automatable proxy for insufficiency of `𝒮`". This
    arm supplies that cause cleanly — a genuinely insufficient state advanced
    by an *exact* propagator, so there is no discretisation error anywhere —
    and confirms the diagnostic does fire for it.

    But it fires *decreasing* in the separation ratio, because a fast mode that
    equilibrates instantly makes a fixed closure accurate (adiabatic
    elimination). Set against Arm B's interior peak, this is the confound: the
    same diagnostic responds to two different causes with two different, and
    partly opposite, dependences on stiffness — so neither the magnitude nor
    the trend identifies which cause is acting.
    """
    residuals = []
    for ratio in SEPARATION_RATIOS:
        oracle = KnownStiffnessOracle(ratio)
        operator = LiftProjectOperator(oracle.generator())
        residuals.append(semigroup_residual(operator, oracle.reduced_initial_state(), INTERVAL, T_MID))

    observe("insufficiency_residuals_by_ratio", dict(zip([f"{r:g}" for r in SEPARATION_RATIOS], residuals)),
            "large at low separation; falls by > 10x by the highest ratio")
    observe("insufficiency_residual_at_lowest_separation", residuals[0], "> 1e-2")
    observe("insufficiency_decay_factor", residuals[0] / residuals[-1], "> 10")

    # The diagnostic does detect insufficiency, with an exact propagator.
    assert residuals[0] > 1e-2
    # And it weakens as separation grows — the opposite direction to Arm B's
    # rise, which is what makes the trend uninformative about the cause.
    assert residuals[0] / residuals[-1] > 10.0


def test_the_two_causes_are_indistinguishable_by_residual_magnitude_at_one_separation_ratio(
    observe: ObservationRecorder,
) -> None:
    """The confound made decision-relevant, and the sharpest form of this
    sweep's finding.

    At one separation ratio, compare (a) a **fully sufficient** state whose
    operator merely has fixed temporal resolution against (b) a **genuinely
    insufficient** state whose propagator is exact. Both report a semigroup
    residual of the same order of magnitude. The remedies are entirely
    different — buy temporal resolution versus augment the state — and Core
    §3.3's diagnostic, which names only the second cause, cannot tell a
    practitioner which they are looking at.
    """
    ratio = 50.0

    stiff_oracle = KnownStiffnessOracle(ratio, oscillatory=True)
    stiff_operator = FixedResolutionOperator(stiff_oracle.generator())
    stiff_state = stiff_oracle.initial_state()
    stiffness_residual = semigroup_residual(stiff_operator, stiff_state, INTERVAL, T_MID)

    insufficient_oracle = KnownStiffnessOracle(ratio)
    insufficiency_residual = semigroup_residual(
        LiftProjectOperator(insufficient_oracle.generator()),
        insufficient_oracle.reduced_initial_state(),
        INTERVAL,
        T_MID,
    )

    ratio_of_residuals = max(stiffness_residual, insufficiency_residual) / min(
        stiffness_residual, insufficiency_residual
    )
    observe("separation_ratio", ratio, "fixed at the stiffness arm's peak")
    observe("stiffness_residual_sufficient_state", stiffness_residual, "same order as insufficiency_residual")
    observe("insufficiency_residual_exact_propagator", insufficiency_residual,
            "same order as stiffness_residual")
    observe("residual_ratio_between_the_two_causes", ratio_of_residuals, "< 10 (same order of magnitude)")
    observe("stiff_arm_norm_drift", stiff_operator.norm_drift(stiff_state, INTERVAL),
            "< 1e-2 (integrator not diverging)")

    assert stiff_operator.norm_drift(stiff_state, INTERVAL) < 1e-2
    # Both causes are live at this ratio, and within one order of magnitude of
    # each other: the residual's magnitude does not identify the cause.
    assert stiffness_residual > 1e-3
    assert insufficiency_residual > 1e-3
    assert ratio_of_residuals < 10.0
