#!/usr/bin/env python
"""Recompute Part 6's pre-registered inputs: the monitor's null distribution and the third arm's
calibrated noise inflation.

Run at the commit that introduces `tests/oracles/part6_thresholds.py`, and **before any sweep
code exists** — ADR-045's requirement, M11.4/M11.5's precedent.

**What this script deliberately does not do.** It never evaluates the framework statistic on the
`NOISY` arm, and it never computes a separation between the `INSUFFICIENT` and `NOISY` arms for
either instrument. That comparison is the registered quantity. The calibration reads the
*variance* of the declared model's innovations — a property of the generator, computed by running
it and differencing, which is the class of design information M11.5's pre-registration §5
established as admissible.

Usage: `python scripts/run_v15_part6_preregistration.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tests.oracles.discovery_campaign as campaign  # noqa: E402
import tests.oracles.part6_thresholds as thresholds  # noqa: E402

NULL_REPLICATES = 40


def innovation_variance(arm: campaign.Arm, inflation: float) -> float:
    """Variance of the declared model's forecast innovations, pooled over the calibration seeds.

    The quantity the arms are matched on (ADR-066 as amended): the unexplained scatter a
    practitioner actually sees. Taken about each pooled sequence's own mean, so a *bias* does not
    enter — which is the whole point, since the two arms are meant to differ in their mean and
    agree in their scatter.
    """
    pooled = [
        np.concatenate(
            [
                sample.innovations
                for sample in campaign.run_campaign(
                    campaign.FAR_SAMPLES, arm, seed, noise_inflation=inflation
                ).samples
            ]
        )
        for seed in thresholds.CALIBRATION_SEEDS
    ]
    return float(np.concatenate(pooled).var())


def report_null_distribution() -> None:
    print("=== the monitor's null distribution (ADR-063) ===")
    z_values = [
        campaign.innovation_mean_report(
            campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.NULL, 1000 + seed)
        ).z
        for seed in range(NULL_REPLICATES)
    ]
    print(f"  replicates                {NULL_REPLICATES}")
    print(f"  null z mean               {np.mean(z_values):.4f}   (registered {thresholds.NULL_Z_MEAN})")
    print(f"  null z 95th percentile    {np.quantile(z_values, 0.95):.4f}   "
          f"(registered {thresholds.NULL_Z_Q95})")
    print(f"  control limit             {thresholds.CONTROL_LIMIT}   "
          "(measured quantile, not the normal 1.960)")


def report_calibration() -> None:
    print()
    print("=== the third arm's calibration (ADR-066 as amended) ===")
    target = innovation_variance(campaign.Arm.INSUFFICIENT, 1.0)
    low = innovation_variance(campaign.Arm.NOISY, 1.0)
    high = innovation_variance(campaign.Arm.NOISY, 1.4)

    # Innovation variance is affine in the squared inflation, so two grid points solve it exactly.
    per_unit = (high - low) / (1.4**2 - 1.0**2)
    signal = low - per_unit
    solved = float(np.sqrt(max((target - signal) / per_unit, 0.0)))
    achieved = innovation_variance(campaign.Arm.NOISY, thresholds.NOISE_INFLATION)

    print(f"  seeds                     {thresholds.CALIBRATION_SEEDS[0]}..{thresholds.CALIBRATION_SEEDS[-1]}"
          "   (disjoint from the sweep's)")
    print(f"  var(d), INSUFFICIENT      {target:.7f}   (registered "
          f"{thresholds.CALIBRATION_INNOVATION_VARIANCE_INSUFFICIENT})")
    print(f"  var(d), NOISY at 1.0      {low:.7f}")
    print(f"  var(d), NOISY at 1.4      {high:.7f}")
    print(f"  solved inflation          {solved:.4f}   (registered {thresholds.NOISE_INFLATION})")
    print(f"  var(d) at the registered  {achieved:.7f}   (registered "
          f"{thresholds.CALIBRATION_INNOVATION_VARIANCE_NOISY})")
    print(f"  relative match            {abs(achieved - target) / target:.2%}")


def report_registered_rule() -> None:
    print()
    print("=== the registered decision rule (no quantity below is measured here) ===")
    print(f"  contrast                  {thresholds.REGISTERED_CONTRAST[0]} vs "
          f"{thresholds.REGISTERED_CONTRAST[1]}")
    print(f"  criterion 1  separation(framework) at {campaign.FAR_SAMPLES} samples "
          f">= {thresholds.REQUIRED_SEPARATION}")
    print(f"  criterion 2  growth({campaign.NEAR_SAMPLES} -> {campaign.FAR_SAMPLES}) "
          f">= {thresholds.REQUIRED_GROWTH}")
    print(f"  criterion 3  separation(comparator) at {campaign.FAR_SAMPLES} samples "
          f"<  {thresholds.COMPARATOR_CEILING}")
    print("  all three must hold for the claim to be supported; any failure is a declared,")
    print("  pre-committed null (docs/V1.5-PART6-PREREGISTRATION.md §5)")


def main() -> None:
    report_null_distribution()
    report_calibration()
    report_registered_rule()


if __name__ == "__main__":
    main()
