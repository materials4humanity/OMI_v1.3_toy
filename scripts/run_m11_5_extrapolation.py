#!/usr/bin/env python3
"""M11.5's extrapolation sweep on the fair axis, Generator C (ADR-047,
docs/DECISIONS.md).

**Thresholds were fixed and committed at `97621ac`, before this script existed** —
`docs/M11.5-PREREGISTRATION.md`. They are imported below as constants and are not
recomputed here, so this script cannot adjust them after seeing a result. The
hold-out itself was gated at that commit too, which is the thing M11.4 lacked.

Reports, per ADR-045 and ADR-047:
  - held-out RMSE for every contestant, **pooled over the held-out strains** —
    the registered criterion
  - `gap(3, 1)` and `gap(3, 4)` — **the claim**, per misspecification arm
  - `gap(2, 3a)` / `gap(2, 3b)` — robustness by kind of misspecification
  - `gap(2, 1)` — the ceiling, for context only, with ADR-045's caveat attached
  - per-strain error curves (CLAUDE.md invariant 7), reported but **not** the
    registered criterion
  - the extrapolation factor at every held-out point, so error can be read
    against declared-envelope distance
  - error against a withheld-free truth, the diagnostic that distinguishes "the
    contestant cannot express this physics" from "the contestant does not know
    the withheld term"

Run: python scripts/run_m11_5_extrapolation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from omi.baseline import GradientBoostedTreeRegressor, RidgeRegressor, root_mean_squared_error  # noqa: E402
from omi_domains.flagship_constitutive.forms import KOCKS_MECKING_STRAIN_WINDOWED  # noqa: E402
from omi_domains.flagship_constitutive.strain_experiment import (  # noqa: E402
    HELD_OUT_STRAINS,
    TRAIN_STRAINS,
    fit_correct_form,
    fit_free_form,
    fit_missing_dependence,
    fit_missing_mechanism,
    fit_tabular,
    labels,
    sample_queries,
)

# --- PRE-REGISTERED at 97621ac. Do not recompute, do not adjust. --------------
MINIMUM_EFFECT = 0.629566
THRESHOLDS = {
    "2_correct_form": 0.31484,
    "3a_missing_mechanism": 0.33089,
    "3b_missing_dependence": 0.32181,
    "4_tabular_RidgeRegressor": 0.31621,
    "4_tabular_GradientBoostedTreeRegressor": 0.31738,
}

N_TRAIN = 120
N_EVAL = 400
N_SEEDS = 8
REFERENCE = "1_free_form"


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
    print("M11.5 EXTRAPOLATION SWEEP — Generator C, accumulated-strain hold-out")
    print(f"train strains {TRAIN_STRAINS} (inside the declared window)")
    print(f"held-out strains {HELD_OUT_STRAINS} (outside it)")
    print(f"n_train={N_TRAIN}, n_eval={N_EVAL}, seeds={N_SEEDS}")
    print("hold-out GATED and thresholds pre-registered at 97621ac; both imported\n")

    per_seed: dict[str, list[float]] = {}
    curves: dict[str, dict[float, list[float]]] = {}
    notes: dict[str, str] = {}

    for seed in range(N_SEEDS):
        train = sample_queries(N_TRAIN, np.random.default_rng(1000 + seed))
        y_train = labels(train, TRAIN_STRAINS)
        held = sample_queries(N_EVAL, np.random.default_rng(7000 + seed))
        y_held = labels(held, HELD_OUT_STRAINS)

        for contestant in _fit_all(train, y_train):
            notes[contestant.label] = contestant.note
            predicted = contestant.predict(held, HELD_OUT_STRAINS)
            # The registered criterion: pooled over all (query, strain) pairs.
            per_seed.setdefault(contestant.label, []).append(
                root_mean_squared_error(predicted, y_held)
            )
            # Per-strain curve (CLAUDE.md invariant 7). Reported, not registered.
            for index, strain in enumerate(HELD_OUT_STRAINS):
                curves.setdefault(contestant.label, {}).setdefault(strain, []).append(
                    root_mean_squared_error(predicted[index], y_held[index])
                )

    # --- extrapolation distance ----------------------------------------------
    probe = sample_queries(N_EVAL, np.random.default_rng(7000))
    factors = [
        KOCKS_MECKING_STRAIN_WINDOWED.report(
            {
                "strain_rate": q.strain_rate,
                "temperature": q.temperature,
                "stored_density": q.rho_0,
                "accumulated_strain": strain,
            }
        ).worst_factor
        for strain in HELD_OUT_STRAINS
        for q in probe
    ]
    print(f"held-out extrapolation factor vs the declared strain window: "
          f"min {min(factors):.2f}, median {np.median(factors):.2f}, max {max(factors):.2f}")
    print("  (every held-out point is outside the declared range, by construction)\n")

    # --- held-out error -------------------------------------------------------
    header = f"{'contestant':42s} {'held-out RMSE':>14s} {'sd':>9s}"
    print(header)
    print("-" * len(header))
    means = {}
    for label, values in per_seed.items():
        means[label] = float(np.mean(values))
        print(f"{label:42s} {means[label]:14.5f} {np.std(values, ddof=1):9.5f}")

    # --- the claim ------------------------------------------------------------
    print(f"\nGAPS vs {REFERENCE} (positive = declared physics is BETTER)")
    header2 = f"{'comparison':50s} {'gap':>10s} {'tau':>9s} {'verdict':>14s}"
    print(header2)
    print("-" * len(header2))
    verdicts = {}
    for label in per_seed:
        if label == REFERENCE:
            continue
        gap = means[REFERENCE] - means[label]
        tau = THRESHOLDS[label]
        verdict = "EFFECT" if gap > tau else ("no effect" if gap > -tau else "WORSE")
        verdicts[label] = (gap, tau, verdict)
        print(f"{REFERENCE + ' - ' + label:50s} {gap:10.5f} {tau:9.5f} {verdict:>14s}")

    print("\nROBUSTNESS BY MISSPECIFICATION KIND (gap between 3a and 3b)")
    gap_3a_3b = means["3a_missing_mechanism"] - means["3b_missing_dependence"]
    print(f"    3a (missing mechanism) - 3b (missing dependence) = {gap_3a_3b:+.5f}")
    print(f"    minimum effect worth catching = {MINIMUM_EFFECT:.5f}")
    print(f"    -> {'DIVERGENT: the benefit depends on WHICH kind' if abs(gap_3a_3b) > MINIMUM_EFFECT else 'comparable'}")

    # --- per-strain curves ----------------------------------------------------
    print("\nPER-STRAIN ERROR CURVES (RMSE at each held-out accumulated strain)")
    print("Reported per CLAUDE.md invariant 7. NOT the registered criterion: the")
    print("registered criterion is the pooled figure above, and reading a gap off")
    print("whichever strain flatters it is what the pre-registration forbids.")
    head3 = f"{'contestant':42s}" + "".join(f"{s:>10g}" for s in HELD_OUT_STRAINS)
    print(head3)
    print("-" * len(head3))
    for label in per_seed:
        row = "".join(f"{np.mean(curves[label][s]):10.4f}" for s in HELD_OUT_STRAINS)
        print(f"{label:42s}{row}")

    print("\nFITTED PARAMETERS")
    for label, note in notes.items():
        print(f"    {label:42s} {note}")

    # --- the withheld-free diagnostic ----------------------------------------
    print("\nDIAGNOSTIC: error against a truth with the WITHHELD TERM REMOVED — how")
    print("well each contestant captures everything EXCEPT the recrystallisation it")
    print("was never given. NOT a re-test of the claim; it is what separates 'cannot")
    print("express this physics' from 'does not know the withheld term'.")
    train = sample_queries(N_TRAIN, np.random.default_rng(1000))
    y_train = labels(train, TRAIN_STRAINS)
    held = sample_queries(N_EVAL, np.random.default_rng(7000))
    y_full = labels(held, HELD_OUT_STRAINS)
    y_clean = labels(held, HELD_OUT_STRAINS, k_drx=0.0)

    head4 = f"{'contestant':42s} {'vs full truth':>14s} {'vs withheld-free':>18s}"
    print(head4)
    print("-" * len(head4))
    for contestant in _fit_all(train, y_train):
        pred = contestant.predict(held, HELD_OUT_STRAINS)
        print(f"{contestant.label:42s} {root_mean_squared_error(pred, y_full):14.4f} "
              f"{root_mean_squared_error(pred, y_clean):18.4f}")
    print(f"\n    withheld term magnitude on this draw: {np.mean(np.abs(y_full - y_clean)):.4f}")
    print(f"    spread of held-out RMSE across contestants: "
          f"{max(means.values()) - min(means.values()):.4f}")

    # --- the decision ---------------------------------------------------------
    claim_arms = ["3a_missing_mechanism", "3b_missing_dependence"]
    baselines = ["1_free_form", "4_tabular_RidgeRegressor", "4_tabular_GradientBoostedTreeRegressor"]
    any_benefit = any(verdicts[a][2] == "EFFECT" for a in claim_arms)
    print("\n" + "=" * 72)
    print("VERDICT ON GENERATOR C")
    print("=" * 72)
    for arm in claim_arms:
        gap, tau, verdict = verdicts[arm]
        print(f"  {arm:26s} vs {REFERENCE}: gap {gap:+.4f} against tau {tau:.4f} -> {verdict}")
    print("\n  contestant 2 (correct form) is the CEILING, not the claim (ADR-045):")
    g2, t2, v2 = verdicts["2_correct_form"]
    print(f"      gap {g2:+.4f} vs tau {t2:.4f} -> {v2}")
    print("      A correct form with fitted parameters is a very strong prior. Here it")
    print("      recovers the generator's parameters exactly, so its held-out error is")
    print("      the irreducible cost of not knowing the withheld term and nothing else.")
    print(f"\n  best baseline held-out RMSE: "
          f"{min(means[b] for b in baselines):.4f} ({min(baselines, key=lambda b: means[b])})")
    if not any_benefit:
        print("\n  NO BENEFIT on Generator C — and unlike M11.4 this null is INFORMATIVE:")
        print("  the hold-out was gated before registration and the axis is one where the")
        print("  declared form demonstrably has content. See docs/M11.5-EXTRAPOLATION.md.")
    else:
        print("\n  BENEFIT FOUND on at least one misspecification arm.")


if __name__ == "__main__":
    main()
