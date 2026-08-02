#!/usr/bin/env python3
"""M11.5's pre-registration: **gate the hold-out first**, then set the
falsification thresholds — before any sweep code exists (ADR-045 as amended and
ADR-047 require the ordering; ADR-041 supplies the threshold procedure).

Two steps, in this order, because the second is pointless without the first.

**Step 1 — the hold-out-discrimination gate** (`omi.proposed.holdout`). M11.4
satisfied every requirement Spec §9.3 states and produced a comparison that could
not have detected any effect, because the declared form had no dependence on the
axis that was withheld (`docs/V1.4-EDITS.md` E-39). ADR-045's amendment makes the
check a precondition rather than a post-mortem. It runs **strictly in-envelope**:
fit both contestants below the training range's upper edge, probe at that edge and
again at the envelope's, and require the withheld-free truth to vary along the axis
and the two model classes to diverge along it. `HELD_OUT_STRAINS` is never touched.

**Step 2 — thresholds**, by the same procedure and the same declared costs M11.4
used, so the two milestones' verdicts are read on the same scale.

Run: python scripts/run_m11_5_preregistration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from omi.baseline import GradientBoostedTreeRegressor, RidgeRegressor, root_mean_squared_error  # noqa: E402
from omi.inverse import decision_sensitive_threshold  # noqa: E402
from omi_domains.flagship_constitutive.strain_experiment import (  # noqa: E402
    DRY_RUN_FIT_STRAINS,
    DRY_RUN_PROBE_STRAINS,
    HELD_OUT_STRAINS,
    REQUIRED_DIVERGENCE,
    TRAIN_STRAINS,
    dry_run_discrimination,
    fit_correct_form,
    fit_free_form,
    fit_missing_dependence,
    fit_missing_mechanism,
    fit_tabular,
    labels,
    sample_queries,
    withheld_term_magnitude,
)

N_TRAIN = 120
N_EVAL = 120
N_PILOT_SEEDS = 8

MINIMUM_EFFECT_FRACTION = 0.10
"""The declared minimum effect worth catching, as a fraction of the magnitude of
**the withheld physics itself**. Unchanged from M11.4, deliberately: the yardstick
should not move between two milestones whose results will be compared, and M11.4's
pre-registration already records why an in-envelope RMSE is the wrong scale for an
extrapolation effect."""

COST_FALSE_ALARM = 3.0
COST_MISS = 1.0
"""Declared asymmetric costs (Spec §7.3), unchanged from M11.4. A false alarm —
claiming declared physics buys reach when it does not — is three times as costly as
a miss, because it is the direction that would put an unsupported claim into a
paper. The ratio raises the threshold and makes a positive finding harder, which is
the correct asymmetry for the party that wants one."""


def _fit_all(train, y_train):  # type: ignore[no-untyped-def]
    return [
        fit_free_form(train, y_train),
        fit_correct_form(train, y_train),
        fit_missing_mechanism(train, y_train),
        fit_missing_dependence(train, y_train),
        fit_tabular(train, y_train, RidgeRegressor()),
        fit_tabular(train, y_train, GradientBoostedTreeRegressor()),
    ]


def main() -> None:
    print("M11.5 PRE-REGISTRATION — in-envelope only, no held-out evaluation")
    print(f"campaign size: n_train={N_TRAIN}, n_eval={N_EVAL}, seeds={N_PILOT_SEEDS}")
    print(f"in-envelope strains {TRAIN_STRAINS}; held-out region {HELD_OUT_STRAINS} NOT touched\n")

    # --- Step 1: the gate -----------------------------------------------------
    print("=" * 78)
    print("STEP 1 — HOLD-OUT DISCRIMINATION GATE (ADR-045 as amended; E-39, E-41)")
    print("=" * 78)
    print(f"dry run fits on strains {DRY_RUN_FIT_STRAINS} and probes at {DRY_RUN_PROBE_STRAINS}")
    print("both probe points are in-envelope and below the recrystallisation onset,")
    print("so the check leaks nothing about the quantity the thresholds will judge.\n")

    gate = dry_run_discrimination(
        rng_train=np.random.default_rng(1000), rng_probe=np.random.default_rng(3000)
    )
    print(f"  axis                          {gate.axis}")
    print(f"  withheld-free truth's own signal along the axis   {gate.axis_signal:.5f}")
    print(f"  disagreement at the fitted edge                   {gate.disagreement_near:.5f}")
    print(f"  disagreement at the envelope edge                 {gate.disagreement_far:.5f}")
    print(f"  divergence                                        {gate.divergence:.3f}"
          f"   (required {gate.required_divergence:.3f})")
    print(f"  candidate error on withheld-free truth            {gate.candidate_error:.5f}")
    print(f"  baseline  error on withheld-free truth            {gate.baseline_error:.5f}")
    print(f"  noise floor (worst in-envelope fit residual)      {gate.noise_floor:.5f}")
    print(f"\n  VERDICT: {gate.verdict.value.upper()}")

    if not gate.usable:
        print("\n  The axis is REFUSED. Per ADR-045 as amended it must be rechosen, and no")
        print("  thresholds are registered: a threshold for a comparison that cannot")
        print("  discriminate is a number with nothing behind it.")
        return

    print("\n  The axis is admitted. Thresholds follow.")
    print("  Retro-validation that this gate discriminates rather than decorates lives in")
    print("  tests/test_holdout_discrimination.py: run against M11.4's strain-rate axis")
    print("  it returns INERT_AXIS, and fails all three criteria independently.\n")

    # --- Step 2: thresholds ---------------------------------------------------
    print("=" * 78)
    print("STEP 2 — THRESHOLDS (ADR-041)")
    print("=" * 78)

    per_seed: dict[str, list[float]] = {}
    for seed in range(N_PILOT_SEEDS):
        train = sample_queries(N_TRAIN, np.random.default_rng(1000 + seed))
        y_train = labels(train, TRAIN_STRAINS)
        # An independent in-envelope draw: the estimator's variability includes
        # evaluation-set sampling, not only training-set sampling.
        evaluate = sample_queries(N_EVAL, np.random.default_rng(5000 + seed))
        y_eval = labels(evaluate, TRAIN_STRAINS)

        for contestant in _fit_all(train, y_train):
            predicted = contestant.predict(evaluate, TRAIN_STRAINS)
            per_seed.setdefault(contestant.label, []).append(
                root_mean_squared_error(predicted, y_eval)
            )

    print(f"\n{'contestant':42s} {'mean RMSE':>11s} {'sd':>10s}   (in-envelope)")
    print("-" * 68)
    for label, values in per_seed.items():
        print(f"{label:42s} {np.mean(values):11.5f} {np.std(values, ddof=1):10.5f}")

    probe = sample_queries(400, np.random.default_rng(99))
    withheld = withheld_term_magnitude(probe, HELD_OUT_STRAINS)
    minimum_effect = float(MINIMUM_EFFECT_FRACTION * withheld)

    print(f"\nwithheld recrystallisation term, mean |contribution| over the held-out")
    print(f"region: {withheld:.6f}")
    print("  (a generator-only quantity: the generator is run twice and differenced;")
    print("   no contestant is fitted, no prediction made, no error measured)")
    print(f"minimum_effect = {MINIMUM_EFFECT_FRACTION:.0%} of that = {minimum_effect:.6f}")

    reference = "1_free_form"
    print(f"\nPER-COMPARISON thresholds vs {reference} (ADR-041):")
    header = f"{'comparison':50s} {'gap sd':>10s} {'tau':>10s}"
    print(header)
    print("-" * len(header))
    thresholds = {}
    for label, values in per_seed.items():
        if label == reference:
            continue
        sd = float(np.std(np.array(per_seed[reference]) - np.array(values), ddof=1))
        tau = decision_sensitive_threshold(
            standard_error=sd,
            minimum_effect=minimum_effect,
            cost_false_alarm=COST_FALSE_ALARM,
            cost_miss=COST_MISS,
        )
        thresholds[label] = (sd, tau)
        print(f"{reference + ' - ' + label:50s} {sd:10.5f} {tau:10.5f}")

    print("\n--- PRE-REGISTERED VALUES (committed before any sweep code exists) ---")
    print(f"required_divergence = {REQUIRED_DIVERGENCE}   (the gate, fixed before it was read)")
    print(f"minimum_effect      = {minimum_effect:.6f}")
    print(f"cost_false_alarm    = {COST_FALSE_ALARM}")
    print(f"cost_miss           = {COST_MISS}")
    print("thresholds (per comparison):")
    for label, (sd, tau) in thresholds.items():
        print(f"    vs {label:44s} sd={sd:.5f}  tau={tau:.5f}")
    print("\nDecision rule, fixed now. The criterion is held-out RMSE POOLED over all")
    print(f"(query, strain) pairs at strains {HELD_OUT_STRAINS}, and a gap in it counts as")
    print("a real effect only if it exceeds that comparison's tau. Per-strain curves are")
    print("reported alongside (CLAUDE.md invariant 7) but are NOT the registered criterion:")
    print("picking the strain at which a gap looks best is exactly what this rule forbids.")


if __name__ == "__main__":
    main()
