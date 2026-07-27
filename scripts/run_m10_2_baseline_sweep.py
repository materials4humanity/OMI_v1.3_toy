#!/usr/bin/env python3
"""Runs the full M10.2 baseline-characterisation sweep (ADR-039,
docs/DECISIONS.md) and prints a markdown table of the results.

Not part of the pytest suite (tests/test_baseline_characterisation.py holds
the reusable harness and a small, fast confirming test) -- this script runs
the full grid the milestone's go/no-go table needs, which is too slow to be
part of every `pytest -q` run. Output is transcribed, not paraphrased, into
docs/M10.2-BASELINE-CHARACTERISATION.md; re-running this script with the
same seed reproduces it exactly.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_baseline_characterisation import SweepConfig, run_config  # noqa: E402
from omi_domains.flagship.readouts import AggregateHardness, BendAngleAtReferenceGeometry  # noqa: E402

N_RECORDS_LEVELS = (20, 50, 200)
WINDOW_NOISE_RATIOS = (2.0, 10.0, 50.0)
NOISE_STD = 0.5
READOUTS = (
    ("AggregateHardness (Type-0)", AggregateHardness()),
    ("BendAngleAtReferenceGeometry (Type-2)", BendAngleAtReferenceGeometry()),
)
TOLERANCE = 0.5
SEED_BASE = 1000


def main() -> None:
    t_start = time.time()
    rows = []
    for readout_name, readout in READOUTS:
        for n_records in N_RECORDS_LEVELS:
            for ratio in WINDOW_NOISE_RATIOS:
                window_width = ratio * NOISE_STD
                config = SweepConfig(
                    n_records=n_records,
                    window_width=window_width,
                    noise_std=NOISE_STD,
                    readout=readout,
                    readout_name=readout_name,
                )
                seed = SEED_BASE + hash((readout_name, n_records, ratio)) % 10000
                t0 = time.time()
                result = run_config(config, seed=seed, tolerance=TOLERANCE, n_epochs=300, hidden_dim=16)
                dt = time.time() - t0
                rows.append((readout_name, n_records, ratio, result, dt))
                print(
                    f"{readout_name:38s} N={n_records:4d} ratio={ratio:5.1f} "
                    f"| ridge rmse={result.ridge.rmse:7.3f} hit={result.ridge.hit_rate:.2f} "
                    f"| gbt rmse={result.gbt.rmse:7.3f} hit={result.gbt.hit_rate:.2f} "
                    f"| deeponet rmse={result.deeponet.rmse:7.3f} hit={result.deeponet.hit_rate:.2f} "
                    f"| ({dt:.1f}s)",
                    flush=True,
                )

    print(f"\nTotal sweep time: {time.time() - t_start:.1f}s\n")

    print("\n### Markdown table\n")
    print("| Readout | N | window/noise | Ridge RMSE | Ridge hit | GBT RMSE | GBT hit | DeepONet RMSE | DeepONet hit | Winner (RMSE) | Winner (hit rate) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for readout_name, n_records, ratio, result, _dt in rows:
        rmse_scores = {"Ridge": result.ridge.rmse, "GBT": result.gbt.rmse, "DeepONet": result.deeponet.rmse}
        hit_scores = {"Ridge": result.ridge.hit_rate, "GBT": result.gbt.hit_rate, "DeepONet": result.deeponet.hit_rate}
        rmse_winner = min(rmse_scores, key=lambda k: rmse_scores[k])
        hit_winner = max(hit_scores, key=lambda k: hit_scores[k])
        print(
            f"| {readout_name} | {n_records} | {ratio:.0f} | {result.ridge.rmse:.3f} | {result.ridge.hit_rate:.2f} "
            f"| {result.gbt.rmse:.3f} | {result.gbt.hit_rate:.2f} | {result.deeponet.rmse:.3f} | {result.deeponet.hit_rate:.2f} "
            f"| {rmse_winner} | {hit_winner} |"
        )


if __name__ == "__main__":
    main()
