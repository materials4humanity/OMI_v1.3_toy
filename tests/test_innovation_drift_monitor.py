"""Innovation drift monitor test: docs/ROADMAP.md M5 exit gate — "Innovation
monitor detects a planted drift," instantiating Spec §10's proposition (S-10)
via the NIS chi-squared convention of ADR-026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import numpy as np

from omi.assimilate import DriftReport, innovation_drift_monitor, run_filter

from tests.conftest import ObservationRecorder
from tests.oracles.known_drift import CHANGE_POINT, KnownDriftOracle


def _drift_report(with_drift: bool, seed: int) -> DriftReport:
    oracle = KnownDriftOracle(with_drift=with_drift)
    rng = np.random.default_rng(seed)
    obs = oracle.observations(rng)
    initial = oracle.initial_ensemble(300, rng)
    result = run_filter(oracle.chain, initial, obs, rng)
    analyses = [result.analyses[k] for k in sorted(result.analyses)]
    return innovation_drift_monitor(analyses, window=8, confidence=0.95)


def test_a_nominal_run_with_no_planted_drift_rarely_trips_the_monitor(observe: ObservationRecorder) -> None:
    report = _drift_report(with_drift=False, seed=0)
    flagged_fraction = report.drift_detected.mean()
    observe("flagged_fraction", flagged_fraction, "< 0.2")
    assert flagged_fraction < 0.2


def test_a_planted_drift_is_detected_after_the_change_point(observe: ObservationRecorder) -> None:
    """After the ramp has run long enough to dominate the observation noise,
    the windowed NIS must be unambiguously and persistently above the
    control limit — not a borderline crossing (CLAUDE.md §7: assert
    qualitative claims, not printed figures)."""
    report = _drift_report(with_drift=True, seed=0)

    window = report.window
    late_start_index = CHANGE_POINT + 15 - (window - 1)
    late_flags = report.drift_detected[late_start_index:]
    late_means = report.windowed_mean[late_start_index:]

    observe("late_flags_all_true", bool(late_flags.all()), "True")
    observe("late_means_min", float(late_means.min()), "> 5 * upper_limit")
    observe("upper_limit", report.upper_limit, "narrative only, not asserted")

    assert late_flags.all(), "drift monitor failed to stay tripped well after the planted change point"
    assert np.all(late_means > 5 * report.upper_limit), (
        "windowed NIS after the change point is not decisively above the control limit"
    )


def test_the_planted_drift_run_flags_far_more_windows_than_the_nominal_run(observe: ObservationRecorder) -> None:
    nominal = _drift_report(with_drift=False, seed=0)
    drifted = _drift_report(with_drift=True, seed=0)
    observe("nominal_flagged_windows", int(nominal.drift_detected.sum()), "narrative only, not asserted")
    observe("drifted_flagged_windows", int(drifted.drift_detected.sum()), "> 3 * max(1, nominal_flagged_windows)")
    assert drifted.drift_detected.sum() > 3 * max(1, nominal.drift_detected.sum())
