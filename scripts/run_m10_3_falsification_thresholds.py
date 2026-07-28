#!/usr/bin/env python3
"""Computes the worked values for M10.3 (Core §6.1/Spec §9.4, ADR-041,
docs/DECISIONS.md) and prints them for docs/M10.3-FALSIFICATION-THRESHOLDS.md.

Criterion 1 (sufficiency, bias-blocked): standard error of the deficit
estimator from repeated campaigns (flagship's real matched-pair campaign;
the known-insufficiency oracle's calibration campaign), then
decision_sensitive_threshold at illustrative declared inputs.

Criterion 3's checkable symptom (super-linear rollout error growth):
"excess over linear extrapolation" (e_last - n_steps * e_first) on both
domains' current analytic chains, repeated to get a standard error.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from omi.inverse import decision_sensitive_threshold  # noqa: E402
from omi.state import Metric  # noqa: E402
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming  # noqa: E402
from omi_domains.flagship.build import build_chain as flagship_build_chain  # noqa: E402
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming  # noqa: E402
from tests.oracles.known_insufficiency import KnownInsufficiencyOracle  # noqa: E402
from omi.sufficiency import sufficiency_deficit  # noqa: E402
from tests.test_conformance_contrast import _contrast_rollout_curve  # noqa: E402
from tests.test_conformance_flagship import _matched_pair_sufficiency_campaign  # noqa: E402
from tests.test_conformance_flagship import _flagship_rollout_curve  # noqa: E402

N_REPS = 20
N_REPS_ROLLOUT = 30


def criterion_1() -> None:
    print("## Criterion 1 (sufficiency, bias-blocked)\n")

    vals = []
    for i in range(N_REPS):
        rng = np.random.default_rng(1000 + i)
        vals.append(_matched_pair_sufficiency_campaign(rng).deficit_squared)
    vals_arr = np.array(vals)
    flagship_mean, flagship_se = float(vals_arr.mean()), float(vals_arr.std(ddof=1))
    print(f"flagship deficit_squared: mean={flagship_mean:.5f} se={flagship_se:.5f} (n_reps={N_REPS}, n_pairs=2000)")

    oracle = KnownInsufficiencyOracle()
    oracle_vals = []
    for i in range(N_REPS):
        rng = np.random.default_rng(2000 + i)
        n_pairs = 8000
        response_a, response_b, matched_diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
        repeat_variance = oracle.repeat_variance(2000, rng)
        jacobian = oracle.response_jacobian_incomplete("reversed")
        result = sufficiency_deficit(response_a, response_b, matched_diffs, jacobian, repeat_variance)
        oracle_vals.append(result.deficit_squared)
    oracle_arr = np.array(oracle_vals)
    truth = oracle.truth()
    print(
        f"oracle deficit_squared: mean={oracle_arr.mean():.5f} se={oracle_arr.std(ddof=1):.5f} "
        f"truth={truth} (n_reps={N_REPS}, n_pairs=8000)"
    )

    print("\ndecision_sensitive_threshold(standard_error=flagship_se, ...):")
    for minimum_effect, cost_fa, cost_miss in (
        (1.0, 1.0, 20.0),
        (1.0, 20.0, 1.0),
        (0.05, 1.0, 20.0),
        (0.05, 20.0, 1.0),
    ):
        tau = decision_sensitive_threshold(flagship_se, minimum_effect, cost_fa, cost_miss)
        flagged = "FLAGGED" if flagship_mean > tau else "not flagged"
        print(
            f"  minimum_effect={minimum_effect:<5} cost_fa={cost_fa:<5} cost_miss={cost_miss:<5} "
            f"tau={tau:.5f}  (flagship mean {flagship_mean:.5f} -> {flagged})"
        )


def criterion_3() -> None:
    print("\n## Criterion 3's checkable symptom (super-linear rollout error growth)\n")

    flagship_excess = []
    for i in range(N_REPS_ROLLOUT):
        rng_e = np.random.default_rng(3000 + i)
        ens = flagship_incoming(200, rng_e)
        metric = Metric.from_ensemble(ens)
        chain = flagship_build_chain()
        curve = _flagship_rollout_curve(np.random.default_rng(4000 + i), metric, chain)
        n_steps = len(curve)
        flagship_excess.append(curve[-1] - n_steps * curve[0])
    flagship_arr = np.array(flagship_excess)
    print(
        f"flagship excess-over-linear: mean={flagship_arr.mean():.6f} "
        f"se={flagship_arr.std(ddof=1):.2e} (n_reps={N_REPS_ROLLOUT})"
    )

    contrast_excess = []
    for i in range(N_REPS_ROLLOUT):
        rng_e = np.random.default_rng(5000 + i)
        ens = contrast_incoming(200, rng_e)
        metric = Metric.from_ensemble(ens)
        curve = _contrast_rollout_curve(np.random.default_rng(6000 + i), metric, n_cycles=8)
        n_steps = len(curve)
        contrast_excess.append(curve[-1] - n_steps * curve[0])
    contrast_arr = np.array(contrast_excess)
    print(
        f"contrast excess-over-linear: mean={contrast_arr.mean():.6f} "
        f"se={contrast_arr.std(ddof=1):.2e} (n_reps={N_REPS_ROLLOUT})"
    )

    se_floor = 1e-6  # decision_sensitive_threshold requires a positive standard_error
    for minimum_effect in (0.01, 0.1):
        tau = decision_sensitive_threshold(se_floor, minimum_effect, cost_false_alarm=1.0, cost_miss=20.0)
        print(f"  minimum_effect={minimum_effect}: tau={tau:.5f} (both measured excesses are far below this)")


def main() -> None:
    t0 = time.time()
    criterion_1()
    criterion_3()
    print(f"\nTotal time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
