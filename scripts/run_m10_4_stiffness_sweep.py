#!/usr/bin/env python3
"""Sweeps Core §3.3's semigroup residual against timescale separation and prints
the tables (M10.4 Phase 3; `docs/PHYSICS-ADEQUACY.md` §3.5's proposed test;
result recorded in `docs/V1.4-EDITS.md` E-33).

**The sharpened target.** Not "does residual grow with stiffness" but: does Core
§3.3's stated *attribution* hold? Core §3.3 names one cause — "Violation of
semigroup consistency under sub-interval resampling is a cheap, automatable
proxy for insufficiency of `𝒮`" — and Spec §9.2 makes that residual one of nine
automated conformance checks. If a **provably sufficient** state produces
residual that grows with timescale separation, the attribution is confounded and
the conformance check is reporting an ambiguous quantity.

**Outcome: REFUTED.** At exact sufficiency the residual is flat in the stiffness
ratio across three decades. The sweep did establish two other things: the answer
is metric-dependent in a way that matters, and a fixed-step-size operator can
pass the check vacuously.

Arms, in the order the design requires:
  (a) EXACT analytic operator      — the NULL; must be ~machine epsilon at every
                                     ratio, else the harness has a bug
  (b1) fixed step COUNT            — the treatment: coarse whole-interval call vs
                                     fine half-interval calls
  (b2) fixed step SIZE             — the literal reading; degenerate on a
                                     commensurable split
  (c) LEARNED operator at one Δt   — the realistic case, confounded with training
                                     quality, reported separately and never pooled
  + metric arms (E-07/OQ-5): raw, identity, incoming-σ (ADR-002), outgoing-σ
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from omi.learning import DeepONetOperator, TrainingRecord, init_deeponet_params, train_deeponet  # noqa: E402
from omi.operators import Control, semigroup_residual  # noqa: E402
from omi.state import Ensemble, Metric, State  # noqa: E402
from tests.oracles.known_stiffness import (  # noqa: E402
    DECOUPLED_SCHEMA,
    ExactFlowOperator,
    FixedStepOperator,
    decoupled_generator,
    metric_semigroup_residual,
)

RATIOS = (1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
INTERVAL = Control(0.0, 1.0, lambda t: np.array([0.0]))
T_MID = 0.5
N_SUBSTEPS = 1024
INITIAL = State(DECOUPLED_SCHEMA, np.array([1.0, 1.0]))


def _fixed(ratio: float) -> FixedStepOperator:
    return FixedStepOperator(decoupled_generator(ratio), n_substeps=N_SUBSTEPS, scheme="euler")


def _learned(ratio: float, seed: int, n_records: int = 48, n_epochs: int = 300) -> DeepONetOperator:
    exact = ExactFlowOperator(decoupled_generator(ratio))
    rng = np.random.default_rng(seed)
    records = []
    for i in range(n_records):
        values = rng.uniform(0.5, 1.5, size=2)
        nxt = exact.step(State(DECOUPLED_SCHEMA, values), INTERVAL)
        records.append(
            TrainingRecord(f"group{i}", values.copy(), (INTERVAL,), (values.copy(), nxt.values.copy()))
        )
    params = init_deeponet_params(
        state_dim=2, control_dim=1, rng=np.random.default_rng(seed + 1), latent_dim=16, hidden_dim=16
    )
    params, _report = train_deeponet(
        params, records, np.random.default_rng(seed + 2), n_epochs=n_epochs, learning_rate=0.05
    )
    return DeepONetOperator(params)


def main() -> None:
    print("Core §3.3 semigroup residual vs timescale separation, at EXACT sufficiency")
    print("state = (x_fast, x_slow), both modes explicit -> Markovian by construction")
    print(f"interval = 1 slow timescale, split at t_mid = {T_MID}, N_substeps = {N_SUBSTEPS}\n")

    # --- (a) the null -------------------------------------------------------
    null = [semigroup_residual(ExactFlowOperator(decoupled_generator(r)), INITIAL, INTERVAL, T_MID)
            for r in RATIOS]
    print(f"(a) NULL, exact analytic operator: worst residual {max(null):.2e}")
    if max(null) >= 1e-12:
        print("    NULL FAILED — the harness is measuring a bug, not stiffness. Stop.")
        raise SystemExit(1)
    print("    NULL PASSES -> any residual below is the operator, not the physics\n")

    # --- (b1) fixed count, with the per-component decomposition -------------
    hdr = f"{'ratio':>7} {'residual':>12} {'fast comp':>12} {'slow comp':>12} {'max λ·h':>8} {'stable':>7}"
    print("(b1) fixed step COUNT, explicit Euler — the treatment arm")
    print(hdr)
    print("-" * len(hdr))
    b1 = []
    for r in RATIOS:
        op = _fixed(r)
        res = semigroup_residual(op, INITIAL, INTERVAL, T_MID)
        direct = op.step(INITIAL, INTERVAL)
        composed = op.step(op.step(INITIAL, Control(0.0, T_MID, INTERVAL.fn)),
                           Control(T_MID, 1.0, INTERVAL.fn))
        per = np.abs(direct.values - composed.values)
        prod = op.max_step_product(1.0)
        b1.append(res)
        print(f"{r:>7g} {res:>12.3e} {per[0]:>12.3e} {per[1]:>12.3e} {prod:>8.3f} "
              f"{'yes' if prod < 2 else 'NO':>7}")
    print(f"    spread max/min = {max(b1) / min(b1):.2f}x   last/first = {b1[-1] / b1[0]:.2f}x"
          f"   -> {'FLAT: prediction REFUTED' if max(b1) / min(b1) < 3 else 'GROWS'}\n")

    # --- (b2) fixed size ----------------------------------------------------
    # Holding h fixed means λ·h grows with the ratio, so unlike (b1) this arm
    # leaves explicit Euler's stability region partway along the sweep. Rows are
    # marked: an entry past the limit is integrator divergence, not a residual,
    # and is exactly the artefact a careless version of this test would publish
    # as a confirmation.
    print("(b2) fixed step SIZE h=0.01, explicit Euler   (* = λ·h >= 2, DIVERGED, not a residual)")
    for tm, tag in ((0.5, "commensurable  (0.5/h integer)"), (0.3333, "incommensurable")):
        cells = []
        for r in RATIOS:
            op = FixedStepOperator(decoupled_generator(r), internal_step=0.01, scheme="euler")
            res = semigroup_residual(op, INITIAL, INTERVAL, tm)
            unstable = op.max_step_product(1.0) >= 2.0
            cells.append(f"{res:.2e}{'*' if unstable else ' '}")
        print(f"    t_mid={tm:<7} {tag:32s} " + " ".join(cells))
    print("    commensurable split -> identically zero at every ratio: a VACUOUS pass.")
    print("    (Spec §9.2 specifies 'random sub-interval splits', which guards against this;")
    print("     this repository's own fixed t_mid values do not.)")
    print("    The starred incommensurable entries carry no information about stiffness:")
    print("     h is fixed, so the scheme is simply unstable there. Note the commensurable")
    print("     row passes at the starred ratios too — both paths diverge to the same")
    print("     wrong answer, so the check passes on an operator that has blown up.\n")

    # --- metric arms --------------------------------------------------------
    rng = np.random.default_rng(0)
    population = Ensemble(DECOUPLED_SCHEMA, 1.0 + 0.2 * rng.standard_normal((4000, 2)))
    incoming = Metric.from_ensemble(population)
    identity = Metric(DECOUPLED_SCHEMA, np.ones(2))
    print("METRIC ARMS (E-07/OQ-5). incoming-σ scale = "
          f"{np.array2string(incoming.scale, precision=4)}  (ADR-002; ratio-independent)")
    hdr2 = f"{'ratio':>7} {'raw':>12} {'identity':>12} {'incoming-σ':>12} {'outgoing-σ':>12} {'σ_out(fast)':>13}"
    print(hdr2)
    print("-" * len(hdr2))
    inc_vals, out_vals = [], []
    for r in RATIOS:
        op = _fixed(r)
        realised = np.column_stack(
            [op.step(State(DECOUPLED_SCHEMA, b), INTERVAL).values for b in np.eye(2)])
        sigma = (population.particles @ realised.T).std(axis=0)
        outgoing = Metric(DECOUPLED_SCHEMA, np.where(sigma > 0, sigma, 1.0))
        raw = semigroup_residual(op, INITIAL, INTERVAL, T_MID)
        i_v = metric_semigroup_residual(op, INITIAL, INTERVAL, T_MID, incoming)
        o_v = metric_semigroup_residual(op, INITIAL, INTERVAL, T_MID, outgoing)
        inc_vals.append(i_v)
        out_vals.append(o_v)
        print(f"{r:>7g} {raw:>12.3e} "
              f"{metric_semigroup_residual(op, INITIAL, INTERVAL, T_MID, identity):>12.3e} "
              f"{i_v:>12.3e} {o_v:>12.3e} {sigma[0]:>13.3e}")
    print(f"    incoming-σ spread {max(inc_vals) / min(inc_vals):.2f}x (flat) vs "
          f"outgoing-σ excursion {max(out_vals) / out_vals[0]:.1e}x (ARTIFACT)\n")

    # --- (c) learned, reported separately -----------------------------------
    print("(c) LEARNED operator trained at one Δt — reported separately, NOT pooled with (b)")
    hdr3 = f"{'ratio':>7} {'residual':>12} {'fwd err @ trained Δt':>22} {'residual/fwd':>13}"
    print(hdr3)
    print("-" * len(hdr3))
    for r in RATIOS:
        learned = _learned(r, seed=int(r) + 7)
        res = semigroup_residual(learned, INITIAL, INTERVAL, T_MID)
        exact = ExactFlowOperator(decoupled_generator(r))
        fwd = float(np.linalg.norm(
            learned.step(INITIAL, INTERVAL).values - exact.step(INITIAL, INTERVAL).values))
        print(f"{r:>7g} {res:>12.3e} {fwd:>22.3e} {res / fwd:>13.1f}")
    print("    residual sits far above the network's own forward error and shows no clean")
    print("    stiffness trend: it is dominated by being asked for an unseen duration.")


if __name__ == "__main__":
    main()
