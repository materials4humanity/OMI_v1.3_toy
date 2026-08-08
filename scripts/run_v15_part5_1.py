#!/usr/bin/env python3
"""v1.5 planning Part 5(1): the contrast diagnostic trace, the statistic dry-run, and the
E-47 parameter-ridge measurement.

Design-only for the decision loop itself (ADR-056, docs/DECISIONS.md) — nothing here
implements it. What runs is:

  §5.1  the loop's **inputs**, traced over a declared contrast campaign, so ADR-056's
        decision predicates can be evaluated against recorded readings rather than
        guessed at: which diagnostics move, which cannot move, and which move for
        reasons that are not information (`tests/oracles/contrast_diagnostic_trace.py`)
  §5.2  the statistic dry-run: three candidates against two arms, scored on E-41's
        divergence criterion in null-arm sigma units, with the Spec §9.3 tabular
        baseline as the comparator (ADR-057; `tests/oracles/contrast_insufficiency.py`)
  §5.3  E-47 measured: is the parameter posterior of a complete, in-window, well-fitted
        declared form a ridge, and does it point along the extrapolated axis (ADR-058;
        `tests/oracles/known_parameter_ridge.py`)

**No thresholds are fixed here.** Part 6's pre-registration owns them, in its own earlier
commit. `REQUIRED_GROWTH` below is this script's declared bar for "diverges at all".

Run: python scripts/run_v15_part5_1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tests.oracles.contrast_insufficiency as dryrun  # noqa: E402
from tests.oracles.contrast_diagnostic_trace import (  # noqa: E402
    OBSERVED_SHARE_THRESHOLD,
    drift_null_rate,
    evaluable_observation_modalities,
    triage_trace,
    validity_report_is_available,
)
from tests.oracles.known_parameter_ridge import (  # noqa: E402
    DECLARED_CEILING,
    N_SEEDS,
    PARAMETER_NAMES,
    RELATIVE_NOISE,
    measure,
)

REQUIRED_GROWTH = 2.0


def rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def section_5_1() -> None:
    rule("5.1  Which diagnostics can drive the loop (ADR-056) -- trace, not loop")

    trace = triage_trace()
    print("Danger-score triage, per interval of a 24-interval declared campaign:")
    print(f"{'k':>3} {'influence median':>17} {'total danger':>14} {'|dangerous|':>12}  labels")
    for k, median, danger, count, labels in zip(
        trace.intervals, trace.influence_medians, trace.total_danger, trace.dangerous_counts, trace.label_sets
    ):
        print(f"{k:>3} {median:>17.6e} {danger:>14.6e} {count:>12}  {','.join(labels)}")

    print()
    print(f"  influence median identically zero : {trace.influence_median_is_identically_zero}")
    print("    -> influence is a non-negative quadratic form, so `influence >= median` is a")
    print("       tautology: MARGINALISABLE and OBSERVED_BUT_IRRELEVANT are unreachable and")
    print("       the four-way triage collapses to the two-way identifiability split.")
    print(f"  total danger relative range (interior) : {trace.danger_relative_range:.3e}")
    print(f"  modal label set                       : {','.join(trace.modal_label_set)}")
    print(f"  intervals whose label set differs     : {trace.intervals_where_labels_differ}")
    print(f"  smallest margin to the {OBSERVED_SHARE_THRESHOLD} share threshold : "
          f"{trace.smallest_threshold_margin:.3e}")
    equal = trace.label_disagreement_at_equal_shares
    if equal:
        print(f"  two directions labelled differently at shares : {equal[0]!r} vs {equal[1]!r}")
        print("    -> the OBSERVED/INFERRED split -- Core 3.8's 'is the chain model or an")
        print("       instrument doing the work' -- is decided by the sign of a rounding error.")
        print("       A loop keyed on the labels fires ARBITRARILY, which is worse than silence.")

    print()
    print(f"Validity report available on contrast : {validity_report_is_available()}")
    print("  -> contrast declares no constitutive form, so one of the four named diagnostics")
    print("     is structurally unavailable. A domain can be fully OMI-0 conformant and leave")
    print("     an operational loop with no validity signal at all.")

    evaluable, missing = evaluable_observation_modalities()
    print()
    print(f"Observation modalities evaluable      : {evaluable}")
    print(f"Declared but not evaluable            : {missing}")
    print("  -> the candidate-measurement pool is smaller than the declared suite: a")
    print("     'commission the temperature sensor' action can be named and cannot be costed.")

    drift = drift_null_rate()
    print()
    print(f"Innovation monitor on {drift.n_campaigns} CORRECTLY SPECIFIED campaigns:")
    print(f"  mean NIS (expect ~1.0)              : {drift.mean_nis:.4f}")
    print(f"  per-window flag rate (nominal {1 - drift.confidence:.2f})  : {drift.per_window_flag_rate:.4f}")
    print(f"  campaigns with any_drift == True    : {drift.any_drift_rate:.3f}")
    print(f"  windows tripping lower / upper limit: {drift.lower_tail_windows} / {drift.upper_tail_windows}")
    print("  -> the statistic is calibrated; the campaign-level aggregate is not. `any_drift`")
    print("     is a maximum over many windowed tests with no multiplicity correction, so a")
    print("     loop keyed on it acts on a false alarm in a large fraction of clean campaigns.")
    print("  -> and both control limits are crossed in comparable numbers while DriftReport")
    print("     records WHICH nowhere -- yet an upward trip (model wrong) and a downward trip")
    print("     (forecast covariance overstated) require OPPOSITE responses.")


def section_5_2() -> None:
    rule(f"5.2  Statistic dry-run (ADR-057) -- {dryrun.N_REPLICATES} replicates per arm per depth")

    print(f"Arms: N = declared state sufficient; I = hidden latent (sd {dryrun.LATENT_SD}) outside")
    print(f"the schema scaling porosity_rate and resistance_rate. Observation noise "
          f"{dryrun.VOLTAGE_NOISE_SD} in both.")
    print(f"Axis: campaign depth, {dryrun.NEAR_DEPTH} -> {dryrun.FAR_DEPTH} intervals. "
          f"Declared required growth: {REQUIRED_GROWTH}")
    print()

    verdicts = dryrun.dry_run(required_growth=REQUIRED_GROWTH)
    for verdict in verdicts:
        print(f"  {verdict.summary()}")

    print()
    print("Reported quantity is the GROWTH RATIO, not the separation (E-41): a candidate that")
    print("is flat is inert regardless of its magnitude.")
    print()
    for verdict in verdicts:
        if verdict.verdict == dryrun.SEPARATION_UNBOUNDED:
            print(f"  {verdict.candidate}: E-41's criterion CANNOT BE EVALUATED. The statistic is")
            print("    identically zero under the null, so the sigma-unit denominator is zero.")
            print("    This is a fourth outcome E-41's three-verdict enum does not name, and it")
            print(f"    arises BECAUSE the statistic detects perfectly. Its own magnitude falls")
            print(f"    {verdict.arm_i_mean_near:.4g} -> {verdict.arm_i_mean_far:.4g} "
                  f"(x{verdict.arm_i_growth:.3f}) as the campaign deepens.")
        elif verdict.verdict == "DISCRIMINATING":
            print(f"  {verdict.candidate}: SELECTED. Growth {verdict.growth_ratio:.3f} >= "
                  f"{REQUIRED_GROWTH}, and separation {verdict.separation_far:.3f} beats the")
            print(f"    Spec 9.3 baseline's {verdict.baseline_separation_far:.3f} "
                  f"(x{verdict.separation_far / verdict.baseline_separation_far:.2f}).")
        elif verdict.verdict == "ADVERSE":
            print(f"  {verdict.candidate}: REJECTED. It diverges "
                  f"({verdict.growth_ratio:.3f}) but the tabular baseline separates the arms")
            print(f"    better at the far depth ({verdict.baseline_separation_far:.3f} vs "
                  f"{verdict.separation_far:.3f}), so it buys nothing over a GBT.")
        else:
            print(f"  {verdict.candidate}: REJECTED ({verdict.verdict}).")


def section_5_3() -> None:
    rule(f"5.3  E-47 measured (ADR-058) -- {N_SEEDS} refits, {RELATIVE_NOISE:.0%} relative noise")

    m = measure(np.random.default_rng(0))
    print(f"Declared metric: {m.metric}")
    print()
    print("Fit quality (E-47's own preconditions):")
    for name, value, true in zip(PARAMETER_NAMES, m.fitted.mean(axis=0), m.theta_true):
        print(f"  {name:<12} fitted {value:>9.4f}   true {true:>7.3f}   "
              f"bias {abs(value / true - 1.0):.2e}")
    print(f"  in-envelope relative residual        : {m.in_envelope_residual:.5f} "
          f"(injected noise {RELATIVE_NOISE})")
    print()
    print("Is it a ridge? (E-47's premise -- CONFIRMED)")
    print(f"  covariance eigenvalues               : {m.eigenvalues}")
    print(f"  condition number                     : {m.condition_number:.1f}")
    print(f"  fractional sd per parameter          : "
          f"{dict(zip(PARAMETER_NAMES, np.round(m.fractional_sd, 5)))}")
    print()
    print("Where does it point? (E-47's consequence -- PARTLY REFUTED)")
    print(f"  {'gamma':>6}  |cos(ridge, sensitive direction)|")
    for gamma, alignment in m.alignment_curve:
        print(f"  {gamma:>6.1f}  {alignment:.4f}")
    print(f"  alignment growth across the reach    : {m.alignment_growth:.3f}x")
    print("  -> the ridge ROTATES toward the extrapolation-sensitive direction, which is")
    print("     E-41's divergence reading on a second axis. But it never ALIGNS with it:")
    print(f"     |cos| = {m.alignment_far:.4f} at six times the envelope edge is still nearer")
    print("     orthogonal than parallel. E-47's mechanism is real; 'the extrapolated")
    print("     prediction is arbitrary' is not supported.")
    print()
    print("What does it cost?")
    print(f"  response relative spread, in-envelope: {m.response_spread_in_envelope:.5f}")
    print(f"  response relative spread, far        : {m.response_spread_far:.5f} "
          f"(x{m.response_spread_far / m.response_spread_in_envelope:.2f})")
    print(f"  far spread / in-envelope fit residual: "
          f"{m.response_spread_far / m.in_envelope_residual:.2f}x")
    print(f"  saturation (k1/k2_0)^2 relative sd   : {m.saturation_spread:.5f}")
    print("  -> a practitioner reading the fit residual as the extrapolated prediction's")
    print("     uncertainty is wrong by ~5x. The absolute spread is ~1% of the response.")
    print()
    print("Is the declared validity report clean? (E-47's bullet -- REFUTED)")
    print(f"  queries in-window at the far strain  : {m.density_ceiling_clean_fraction:.3f}")
    print(f"  hardest-binding declared bound       : {m.binding_bound_at_far} "
          f"(declared ceiling {DECLARED_CEILING})")
    print("  -> checked against the UNWINDOWED KOCKS_MECKING, which declares no bound on")
    print("     accumulated strain at all. The report still fires, via the stored-density")
    print("     saturation ceiling, for a substantial minority of queries -- and it fires for")
    print("     the wrong reason, since that ceiling is a statement about a physical regime")
    print("     and not about whether the data pinned the parameters.")


if __name__ == "__main__":
    section_5_1()
    section_5_2()
    section_5_3()
    print()
