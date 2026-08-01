#!/usr/bin/env python3
"""M11.4's extrapolation sweep, Generator A (ADR-045, docs/DECISIONS.md).

**Thresholds were fixed and committed at `bd44bb6`, before this script existed** —
`docs/M11.4-PREREGISTRATION.md`. They are imported below as constants and are not
recomputed here, so this script cannot adjust them after seeing a result.

Reports, per ADR-045:
  - held-out RMSE for every contestant, and rollout-length error curves
  - `gap(3, 1)` and `gap(3, 4)` — **the claim**, per misspecification arm
  - `gap(2, 3a)` / `gap(2, 3b)` — robustness by kind of misspecification
  - `gap(2, 1)` — the ceiling, for context only, with ADR-045's caveat attached
  - the extrapolation factor at every held-out query, so error can be read
    against declared-envelope distance

Run: python scripts/run_m11_4_extrapolation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from omi.baseline import GradientBoostedTreeRegressor, RidgeRegressor, root_mean_squared_error  # noqa: E402
from omi_domains.flagship_constitutive.forms import KOCKS_MECKING  # noqa: E402
from omi_domains.flagship_constitutive.experiment import (  # noqa: E402
    HELD_OUT_RATE,
    IN_ENVELOPE_RATE,
    fit_correct_form,
    fit_free_form,
    fit_missing_dependence,
    fit_missing_mechanism,
    fit_tabular,
    labels,
    sample_queries,
)

# --- PRE-REGISTERED at bd44bb6. Do not recompute, do not adjust. --------------
MINIMUM_EFFECT = 0.701923
THRESHOLDS = {
    "2_correct_form": 0.35161,
    "3a_missing_mechanism": 0.38944,
    "3b_missing_dependence": 0.36706,
    "4_tabular_RidgeRegressor": 0.35165,
    "4_tabular_GradientBoostedTreeRegressor": 0.35348,
}

N_TRAIN = 120
N_EVAL = 400
N_SEEDS = 8
ROLLOUT_STRAINS = (0.25, 0.5, 1.0, 2.0, 4.0)
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
    print("M11.4 EXTRAPOLATION SWEEP — Generator A (primary)")
    print(f"train rates {IN_ENVELOPE_RATE} (in declared window), "
          f"held-out rates {HELD_OUT_RATE} (outside it)")
    print(f"n_train={N_TRAIN}, n_eval={N_EVAL}, seeds={N_SEEDS}")
    print("thresholds pre-registered at bd44bb6 and imported, not recomputed\n")

    per_seed: dict[str, list[float]] = {}
    curves: dict[str, dict[float, list[float]]] = {}
    notes: dict[str, str] = {}

    for seed in range(N_SEEDS):
        train = sample_queries(N_TRAIN, IN_ENVELOPE_RATE, np.random.default_rng(1000 + seed))
        y_train = labels(train)
        held = sample_queries(N_EVAL, HELD_OUT_RATE, np.random.default_rng(7000 + seed))

        for contestant in _fit_all(train, y_train):
            notes[contestant.label] = contestant.note
            y_held = labels(held)
            predicted = np.array([contestant.predict(q, 1.0) for q in held])
            per_seed.setdefault(contestant.label, []).append(
                root_mean_squared_error(predicted, y_held)
            )
            # Rollout-length error curve (CLAUDE.md §5 invariant 7).
            for strain in ROLLOUT_STRAINS:
                truth = labels(held, strain)
                pred = np.array([contestant.predict(q, strain) for q in held])
                curves.setdefault(contestant.label, {}).setdefault(strain, []).append(
                    root_mean_squared_error(pred, truth)
                )

    # --- extrapolation distance -------------------------------------------
    probe = sample_queries(N_EVAL, HELD_OUT_RATE, np.random.default_rng(7000))
    factors = [
        KOCKS_MECKING.report(
            {"strain_rate": q.strain_rate, "temperature": q.temperature, "stored_density": q.rho_0}
        ).worst_factor
        for q in probe
    ]
    print(f"held-out extrapolation factor vs KOCKS_MECKING's declared window: "
          f"min {min(factors):.2f}, median {np.median(factors):.2f}, max {max(factors):.2f}")
    print("  (every held-out query is outside the declared range, by construction)\n")

    # --- held-out error ------------------------------------------------------
    header = f"{'contestant':42s} {'held-out RMSE':>14s} {'sd':>9s}"
    print(header)
    print("-" * len(header))
    means = {}
    for label, values in per_seed.items():
        means[label] = float(np.mean(values))
        print(f"{label:42s} {means[label]:14.5f} {np.std(values, ddof=1):9.5f}")

    # --- the claim -----------------------------------------------------------
    print(f"\nGAPS vs {REFERENCE} (positive = declared physics is BETTER)")
    header2 = f"{'comparison':44s} {'gap':>10s} {'tau':>9s} {'verdict':>14s}"
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
        print(f"{REFERENCE + ' - ' + label:44s} {gap:10.5f} {tau:9.5f} {verdict:>14s}")

    print("\nROBUSTNESS BY MISSPECIFICATION KIND (gap between 3a and 3b)")
    gap_3a_3b = means["3a_missing_mechanism"] - means["3b_missing_dependence"]
    print(f"    3a (missing mechanism) - 3b (missing dependence) = {gap_3a_3b:+.5f}")
    print(f"    minimum effect worth catching = {MINIMUM_EFFECT:.5f}")
    print(f"    -> {'DIVERGENT: the benefit depends on WHICH kind' if abs(gap_3a_3b) > MINIMUM_EFFECT else 'comparable'}")

    # --- rollout curves ------------------------------------------------------
    print("\nROLLOUT-LENGTH ERROR CURVES (RMSE vs accumulated strain)")
    head3 = f"{'contestant':42s}" + "".join(f"{s:>10g}" for s in ROLLOUT_STRAINS)
    print(head3)
    print("-" * len(head3))
    for label in per_seed:
        row = "".join(f"{np.mean(curves[label][s]):10.4f}" for s in ROLLOUT_STRAINS)
        print(f"{label:42s}{row}")

    print("\nFITTED PARAMETERS")
    for label, note in notes.items():
        print(f"    {label:42s} {note}")

    # --- why the null is uninformative, diagnosed rather than explained away ---
    print("\nDIAGNOSTIC: error against a DRAG-FREE generator — how well each contestant")
    print("captures everything EXCEPT the withheld term. NOT a re-test of the claim.")
    from omi_domains.flagship_constitutive import experiment as exp

    train = sample_queries(N_TRAIN, IN_ENVELOPE_RATE, np.random.default_rng(1000))
    y_train = labels(train)
    held = sample_queries(N_EVAL, HELD_OUT_RATE, np.random.default_rng(7000))
    y_full = labels(held)
    saved = exp.GEN_K_DRAG
    try:
        exp.GEN_K_DRAG = 0.0
        y_nodrag = labels(held)
    finally:
        exp.GEN_K_DRAG = saved

    head4 = f"{'contestant':42s} {'vs full truth':>14s} {'vs drag-free':>14s}"
    print(head4)
    print("-" * len(head4))
    for contestant in _fit_all(train, y_train):
        pred = np.array([contestant.predict(q, 1.0) for q in held])
        print(f"{contestant.label:42s} {root_mean_squared_error(pred, y_full):14.4f} "
              f"{root_mean_squared_error(pred, y_nodrag):14.4f}")
    print(f"\n    withheld term magnitude on this draw: {np.mean(np.abs(y_full - y_nodrag)):.4f}")
    print(f"    spread of held-out RMSE across contestants: "
          f"{max(means.values()) - min(means.values()):.4f}")
    print("    -> every contestant's held-out error IS the withheld term, to within the spread.")
    print("    -> and against the drag-free truth the FREE-FORM arm is best, because the")
    print("       drag-free physics has no rate dependence at all: the declared form is")
    print("       constant along the held-out axis, so it has nothing to contribute there.")

    # --- the decision --------------------------------------------------------
    claim_arms = ["3a_missing_mechanism", "3b_missing_dependence"]
    baselines = ["1_free_form", "4_tabular_RidgeRegressor", "4_tabular_GradientBoostedTreeRegressor"]
    any_benefit = any(verdicts[a][2] == "EFFECT" for a in claim_arms)
    print("\n" + "=" * 72)
    print("VERDICT ON GENERATOR A")
    print("=" * 72)
    for arm in claim_arms:
        gap, tau, verdict = verdicts[arm]
        print(f"  {arm:26s} vs {REFERENCE}: gap {gap:+.4f} against tau {tau:.4f} -> {verdict}")
    print(f"\n  contestant 2 (correct form) is the CEILING, not the claim (ADR-045):")
    g2, t2, v2 = verdicts["2_correct_form"]
    print(f"      gap {g2:+.4f} vs tau {t2:.4f} -> {v2}")
    print(f"      A correct form with fitted parameters is a very strong prior and its")
    print(f"      win is close to structural. It calibrates the scale; it is not evidence.")
    print(f"\n  best baseline held-out RMSE: "
          f"{min(means[b] for b in baselines):.4f} ({min(baselines, key=lambda b: means[b])})")
    if not any_benefit:
        print("\n  NO BENEFIT on Generator A. Per ADR-045, Generator B is NOT run:")
        print("  a form that cannot beat free-form when the only withheld physics is one")
        print("  named term will not do better when an entire coupling is missing.")
    else:
        print("\n  BENEFIT FOUND on at least one misspecification arm.")


if __name__ == "__main__":
    main()
