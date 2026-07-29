#!/usr/bin/env python3
"""Sweeps Core §3.3's semigroup residual against timescale separation and
prints the table (M10.4 Phase 3; `docs/PHYSICS-ADEQUACY.md` §3.5's proposed
test; result recorded in `docs/V1.4-EDITS.md` E-33).

Prediction under test: "semigroup residual should grow systematically with
timescale separation." Outcome: refuted as stated in both fast-mode regimes —
flat for a decaying stiff transient, and a non-monotone interior peak for a
persistently excited one — with a confound demonstrated against Core §3.3's
own stated attribution of the residual to state insufficiency.

Four arms, all against the same exactly-known two-timescale construction:
  A  exact flow, sufficient state          -> control: residual 0 by construction
  B  fixed resolution, sufficient state, decaying fast mode
  C  fixed resolution, sufficient state, oscillatory (persistent) fast mode
  D  exact propagator, INSUFFICIENT state  -> Core's own stated cause
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from omi.operators import Control, semigroup_residual  # noqa: E402
from tests.oracles.known_stiffness import (  # noqa: E402
    ExactFlowOperator,
    FixedResolutionOperator,
    KnownStiffnessOracle,
    LiftProjectOperator,
)

RATIOS = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0)
INTERVAL = Control(0.0, 1.0, lambda t: np.array([0.0]))
T_MID = 0.5


def main() -> None:
    print("Semigroup residual vs timescale separation ratio")
    print("interval = 1 slow timescale, split at t_mid = 0.5, n_substeps = 256\n")
    header = (
        f"{'ratio':>7} {'A exact':>12} {'B decaying':>12} {'C oscill.':>12} "
        f"{'D insuff.':>12} {'B drift':>10} {'C drift':>10}"
    )
    print(header)
    print("-" * len(header))

    rows = []
    for ratio in RATIOS:
        decay = KnownStiffnessOracle(ratio)
        osc = KnownStiffnessOracle(ratio, oscillatory=True)

        a = semigroup_residual(ExactFlowOperator(decay.generator()), decay.initial_state(), INTERVAL, T_MID)

        b_op = FixedResolutionOperator(decay.generator())
        b_state = decay.initial_state()
        b = semigroup_residual(b_op, b_state, INTERVAL, T_MID)
        b_drift = b_op.norm_drift(b_state, INTERVAL)

        c_op = FixedResolutionOperator(osc.generator())
        c_state = osc.initial_state()
        c = semigroup_residual(c_op, c_state, INTERVAL, T_MID)
        c_drift = c_op.norm_drift(c_state, INTERVAL)

        d = semigroup_residual(
            LiftProjectOperator(decay.generator()), decay.reduced_initial_state(), INTERVAL, T_MID
        )

        rows.append((ratio, a, b, c, d))
        print(
            f"{ratio:>7g} {a:>12.3e} {b:>12.3e} {c:>12.3e} {d:>12.3e} "
            f"{b_drift:>10.1e} {c_drift:>10.1e}"
        )

    b_vals = [r[2] for r in rows]
    c_vals = [r[3] for r in rows]
    d_vals = [r[4] for r in rows]
    peak = int(np.argmax(c_vals))

    print("\nSummary")
    print(f"  A (exact, control):        worst residual {max(r[1] for r in rows):.2e} — zero by construction")
    print(f"  B (decaying fast mode):    max/min spread {max(b_vals) / min(b_vals):.2f}x across 3 decades — FLAT")
    print(f"  C (oscillatory fast mode): interior peak at ratio {RATIOS[peak]:g}; "
          f"rise {c_vals[peak] / c_vals[0]:.0f}x, fall {c_vals[peak] / c_vals[-1]:.0f}x — NON-MONOTONE")
    print(f"  D (insufficiency, exact):  {d_vals[0]:.2e} at ratio 1, falling {d_vals[0] / d_vals[-1]:.0f}x "
          f"by ratio 500 — DECREASING")
    print()
    print(f"  Confound at ratio {RATIOS[peak]:g}: sufficient-state stiffness residual {c_vals[peak]:.3e} "
          f"vs insufficient-state residual {d_vals[peak]:.3e}")
    print(f"    -> within {max(c_vals[peak], d_vals[peak]) / min(c_vals[peak], d_vals[peak]):.2f}x of each other: "
          "the residual's magnitude does not identify the cause.")


if __name__ == "__main__":
    main()
