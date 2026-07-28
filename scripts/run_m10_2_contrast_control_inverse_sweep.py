#!/usr/bin/env python3
"""Runs the contrast control-inverse sweep (Core §5) and prints a markdown
table. Companion to scripts/run_m10_2_baseline_sweep.py (flagship,
structure inverse) -- see docs/M10.2-BASELINE-CHARACTERISATION.md §6.

Sensitivity was verified first (per instruction): DendriteRisk responds
substantially and monotonically to contrast's declared control (current),
unlike flagship's two declared readouts -- so, unlike flagship, this
sweep tests Spec §9.3's actual claim (the control inverse under U_adm,
with the trust region active), not a structure-inverse substitute.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_baseline_characterisation import (  # noqa: E402
    U_ADM,
    U_TRUST,
    ContrastConfig,
    run_contrast_control_inverse_config,
)

N_RECORDS_LEVELS = (20, 50, 200)
TOLERANCE = 0.3
SEED_BASE = 2000


def main() -> None:
    print(f"U_ADM = {U_ADM}, U_TRUST = {U_TRUST}, tolerance = {TOLERANCE}\n")
    t_start = time.time()
    rows = []
    for n_records in N_RECORDS_LEVELS:
        config = ContrastConfig(n_records=n_records)
        seed = SEED_BASE + n_records
        t0 = time.time()
        result = run_contrast_control_inverse_config(config, seed=seed, tolerance=TOLERANCE, n_epochs=300, hidden_dim=16)
        dt = time.time() - t0
        rows.append((n_records, result, dt))
        print(
            f"N={n_records:4d} "
            f"| ridge rmse_in={result.ridge.rmse_in_trust:.3f} rmse_ex={result.ridge.rmse_extrapolation:.3f} "
            f"hit_in={result.ridge.hit_rate_in_trust:.2f} hit_ex={result.ridge.hit_rate_extrapolation:.2f} "
            f"| gbt rmse_in={result.gbt.rmse_in_trust:.3f} rmse_ex={result.gbt.rmse_extrapolation:.3f} "
            f"hit_in={result.gbt.hit_rate_in_trust:.2f} hit_ex={result.gbt.hit_rate_extrapolation:.2f} "
            f"| deeponet rmse_in={result.deeponet.rmse_in_trust:.3f} rmse_ex={result.deeponet.rmse_extrapolation:.3f} "
            f"hit_in={result.deeponet.hit_rate_in_trust:.2f} hit_ex={result.deeponet.hit_rate_extrapolation:.2f} "
            f"| ({dt:.1f}s)",
            flush=True,
        )

    print(f"\nTotal sweep time: {time.time() - t_start:.1f}s\n")
    print("\n### Markdown table\n")
    print(
        "| N | Ridge RMSE (in/ex) | Ridge hit (in/ex) | GBT RMSE (in/ex) | GBT hit (in/ex) "
        "| DeepONet RMSE (in/ex) | DeepONet hit (in/ex) |"
    )
    print("|---|---|---|---|---|---|---|")
    for n_records, result, _dt in rows:
        print(
            f"| {n_records} "
            f"| {result.ridge.rmse_in_trust:.3f} / {result.ridge.rmse_extrapolation:.3f} "
            f"| {result.ridge.hit_rate_in_trust:.2f} / {result.ridge.hit_rate_extrapolation:.2f} "
            f"| {result.gbt.rmse_in_trust:.3f} / {result.gbt.rmse_extrapolation:.3f} "
            f"| {result.gbt.hit_rate_in_trust:.2f} / {result.gbt.hit_rate_extrapolation:.2f} "
            f"| {result.deeponet.rmse_in_trust:.3f} / {result.deeponet.rmse_extrapolation:.3f} "
            f"| {result.deeponet.hit_rate_in_trust:.2f} / {result.deeponet.hit_rate_extrapolation:.2f} |"
        )


if __name__ == "__main__":
    main()
