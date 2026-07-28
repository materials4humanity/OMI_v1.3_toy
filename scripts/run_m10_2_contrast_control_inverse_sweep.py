#!/usr/bin/env python3
"""Runs the contrast control-inverse sweep (Core §5) and prints a markdown
table. Companion to scripts/run_m10_2_baseline_sweep.py (flagship,
structure inverse) -- see docs/M10.2-BASELINE-CHARACTERISATION.md §6.

Sensitivity was verified first (per instruction): DendriteRisk responds
substantially and monotonically to contrast's declared control (current),
unlike flagship's two declared readouts -- so, unlike flagship, this
sweep tests Spec §9.3's actual claim (the control inverse under U_adm,
with the trust region active), not a structure-inverse substitute.

Re-run (ADR-040, docs/DECISIONS.md): the operator-graph contestant is now
a ConstrainedMonotoneOperator inverted by gradient_control_search
(src/omi/inverse.py, new this ADR) under U_adm, rather than an
unconstrained DeepONetOperator inverted by naive grid search. Ridge and
GBT are unchanged. Each row also prints, per model, the count of
extrapolation-band search results landing outside U_TRUST (constrained
operator only -- Ridge/GBT use grid search and have no single-target
search trajectory to report this for).
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
        result = run_contrast_control_inverse_config(config, seed=seed, tolerance=TOLERANCE, n_epochs=300)
        dt = time.time() - t0
        rows.append((n_records, result, dt))
        n_outside_trust = sum(
            1 for d in result.constrained_operator.search_diagnostics_extrapolation if not d.within_trust_region
        )
        n_extrap_targets = len(result.constrained_operator.search_diagnostics_extrapolation)
        print(
            f"N={n_records:4d} "
            f"| ridge rmse_in={result.ridge.rmse_in_trust:.3f} rmse_ex={result.ridge.rmse_extrapolation:.3f} "
            f"hit_in={result.ridge.hit_rate_in_trust:.2f} hit_ex={result.ridge.hit_rate_extrapolation:.2f} "
            f"| gbt rmse_in={result.gbt.rmse_in_trust:.3f} rmse_ex={result.gbt.rmse_extrapolation:.3f} "
            f"hit_in={result.gbt.hit_rate_in_trust:.2f} hit_ex={result.gbt.hit_rate_extrapolation:.2f} "
            f"| constrained_operator rmse_in={result.constrained_operator.rmse_in_trust:.3f} "
            f"rmse_ex={result.constrained_operator.rmse_extrapolation:.3f} "
            f"hit_in={result.constrained_operator.hit_rate_in_trust:.2f} "
            f"hit_ex={result.constrained_operator.hit_rate_extrapolation:.2f} "
            f"outside_trust={n_outside_trust}/{n_extrap_targets} "
            f"| ({dt:.1f}s)",
            flush=True,
        )
        for diag in result.constrained_operator.search_diagnostics_extrapolation:
            print(
                f"    extrap target={diag.target:.4f} chosen_control={diag.chosen_control:.4f} "
                f"achieved={diag.achieved:.4f} within_trust={diag.within_trust_region} hit={diag.hit}",
                flush=True,
            )

    print(f"\nTotal sweep time: {time.time() - t_start:.1f}s\n")
    print("\n### Markdown table\n")
    print(
        "| N | Ridge RMSE (in/ex) | Ridge hit (in/ex) | GBT RMSE (in/ex) | GBT hit (in/ex) "
        "| Constrained op. RMSE (in/ex) | Constrained op. hit (in/ex) | Outside U_trust (ex) |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for n_records, result, _dt in rows:
        n_outside_trust = sum(
            1 for d in result.constrained_operator.search_diagnostics_extrapolation if not d.within_trust_region
        )
        n_extrap_targets = len(result.constrained_operator.search_diagnostics_extrapolation)
        print(
            f"| {n_records} "
            f"| {result.ridge.rmse_in_trust:.3f} / {result.ridge.rmse_extrapolation:.3f} "
            f"| {result.ridge.hit_rate_in_trust:.2f} / {result.ridge.hit_rate_extrapolation:.2f} "
            f"| {result.gbt.rmse_in_trust:.3f} / {result.gbt.rmse_extrapolation:.3f} "
            f"| {result.gbt.hit_rate_in_trust:.2f} / {result.gbt.hit_rate_extrapolation:.2f} "
            f"| {result.constrained_operator.rmse_in_trust:.3f} / {result.constrained_operator.rmse_extrapolation:.3f} "
            f"| {result.constrained_operator.hit_rate_in_trust:.2f} / {result.constrained_operator.hit_rate_extrapolation:.2f} "
            f"| {n_outside_trust}/{n_extrap_targets} |"
        )


if __name__ == "__main__":
    main()
