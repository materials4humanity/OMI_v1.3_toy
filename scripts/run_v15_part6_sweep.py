#!/usr/bin/env python
"""Part 6's registered sweep, at the declared replicate count.

Thresholds are imported from `tests/oracles/part6_thresholds.py`, committed in an earlier commit
(`git log` is the record). Nothing here may change them, and this script does not compute any.

Usage: `python scripts/run_v15_part6_sweep.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tests.oracles.discovery_campaign as campaign  # noqa: E402
import tests.oracles.part6_sweep as sweep  # noqa: E402
import tests.oracles.part6_thresholds as thresholds  # noqa: E402


def main() -> None:
    print("=== v1.5 Part 6 registered sweep ===")
    print(f"  contrast          {thresholds.REGISTERED_CONTRAST[0]} vs {thresholds.REGISTERED_CONTRAST[1]}")
    print(f"  noise inflation   {thresholds.NOISE_INFLATION}  (registered, not recomputed here)")
    print(f"  campaign lengths  {campaign.NEAR_SAMPLES} -> {campaign.FAR_SAMPLES} samples")
    print(f"  seeds             {sweep.SWEEP_SEEDS[0]}..{sweep.SWEEP_SEEDS[-1]}")

    result = sweep.run_sweep()

    print()
    print("=== the three registered criteria, each stated separately ===")
    for outcome in result.criteria:
        print(f"  {outcome.line()}")

    print()
    print("=== the framework statistic on the registered contrast ===")
    print(f"  separation           {result.framework_separation_near:.4f} -> "
          f"{result.framework_separation_far:.4f}  (growth {result.framework_growth:.4f})")
    print(f"  z, INSUFFICIENT      {result.framework_mean_insufficient_near:.4f} -> "
          f"{result.framework_mean_insufficient_far:.4f}")
    print(f"  z, NOISY             {result.framework_mean_noisy_near:.4f} -> "
          f"{result.framework_mean_noisy_far:.4f}")
    print(f"  z, NULL at far       {result.framework_mean_null_far:.4f}   (reference E|Z| = 0.798)")

    print()
    print("=== the comparator's TWO separations, side by side (pre-committed null handling) ===")
    print(f"  vs NOISY  (registered contrast)   {result.comparator_separation_registered:.4f} sigma")
    print(f"  vs NULL   (companion reading)     {result.comparator_separation_null_contrast:.4f} sigma")
    print(f"  fitted noise / instrument sd: INSUFFICIENT {result.comparator_mean_insufficient_far:.4f}  "
          f"NOISY {result.comparator_mean_noisy_far:.4f}  NULL {result.comparator_mean_null_far:.4f}")
    print(f"  ratio (null-contrast / registered)  {result.comparator_separation_ratio:.4f}x   "
          "[computed after the run; not a registered criterion]")
    print(f"  reading: {result.comparator_reading}")

    print()
    print("=== the calibration, checked on the sweep's own seeds ===")
    print(f"  var(d), INSUFFICIENT  {result.calibration_variance_insufficient:.7f}")
    print(f"  var(d), NOISY         {result.calibration_variance_noisy:.7f}")
    mismatch = abs(
        result.calibration_variance_noisy - result.calibration_variance_insufficient
    ) / result.calibration_variance_insufficient
    print(f"  relative mismatch     {mismatch:.2%}   (calibrated to 0.05% on seeds 2000..2023)")

    print()
    print("=== search quality, reported so the comparator is not quietly diminished ===")
    print(f"  best found: INSUFFICIENT {result.best_found_insufficient:.4f}  "
          f"NOISY {result.best_found_noisy:.4f}  NULL {result.best_found_null:.4f}")

    unmet = [outcome.name for outcome in result.criteria if not outcome.met]
    print()
    if unmet:
        print(f"OUTCOME: NULL on {len(unmet)} of 3 criteria — {', '.join(unmet)}")
        print("  Pre-committed as publishable (docs/V1.5-PART6-PREREGISTRATION.md §5).")
        print("  No second construction, no re-selected statistic, no extended axis.")
    else:
        print("OUTCOME: all three registered criteria met.")


if __name__ == "__main__":
    main()
