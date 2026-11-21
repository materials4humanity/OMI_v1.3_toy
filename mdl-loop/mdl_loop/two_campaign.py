"""0.5: two 20-run campaign pairs against one 40-run pair, loop vs OVAT.

The 0.1 memo (section 1.1) found a single 40-run head-to-head against OVAT
cannot reach 80% power, because campaigns differ from one another more than
confirmation noise. The ratified pre-registration (0.2 memo, section 0) says a
decisive head-to-head, if funders need one, comes from a second pair of
campaigns. This module asks whether two independent 20-run pairs, combined,
beat one 40-run pair at the same total furnace runs.

Arms: the 0.4 device-aware loop (final anchor on) and the careful OVAT
control, both from ``m0.run_lookup`` at the M0 lookup noise levels.

Per M0 cell and seed, four campaigns:

* pair A, 40 runs, from the literature recipe (its 20-run checkpoint is pair A
  at 20 runs: a checkpoint is what the campaign would hand over if it stopped
  there, final anchor included);
* pair B, 20 runs, from an alternative start (``m0.start_recipe``) with its
  own random streams.

Designs, each with the same search and confirmation furnace runs per arm:

* ``single40``  one 40-run pair; 4 confirmation runs per arm;
* ``two20``     pairs A and B at 20 runs; 2 confirmation runs per recipe.
  The combined estimate is the mean of the two within-pair differences, with a
  Welch-Satterthwaite standard error (stratified test).

Reference and sensitivity rows (not the same total runs, or not the
pre-registered test): ``single20`` (pair A at 20 runs, 4 confirmation runs per
arm, half the search runs), ``two20_pooled`` (all four recipes' films pooled
by arm, plain Welch), ``two20_conf4`` (stratified, 4 confirmation runs per
recipe, 4 more runs per arm).

The test is the 0.2 secondary: loop minus OVAT QFLS on confirmation runs,
one-sided at alpha 0.05. Power = the test favours the loop; wrong-way = the
reversed one-sided test favours OVAT. Confirmation draws use common random
numbers: each (campaign, arm) has its own generator and simulates 4
confirmation runs per repeat; a design using k runs takes the first k. The
device-level difference is the true device-Voc gap loop minus OVAT of the
recipes handed over (the mean over pairs for two20).

All of it runs on the synthetic virtual-kesterite surface.

    python -m mdl_loop.two_campaign --out out --seeds 24
"""
from __future__ import annotations

from . import _blas  # noqa: F401  (pins BLAS threads; must precede numpy)

import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

from .campaign import welch_one_sided  # noqa: E402
from .emulator import VirtualKesterite  # noqa: E402
from .lab import Lab  # noqa: E402
from .m0 import HETEROS_M0, MEASURED_FILM, LookupJob, noise_for, run_lookup  # noqa: E402
from .space import LITERATURE_RECIPE  # noqa: E402

ARMS = ("loop-dev", "ovat")
ALPHA = 0.05
MAX_CONF = 4


def plan(seeds: int) -> list[LookupJob]:
    jobs = []
    for s in range(seeds):
        for h in HETEROS_M0:
            for m in MEASURED_FILM:
                for arm in ARMS:
                    jobs += [LookupJob(arm, m, h, s, budget=40, start=0),
                             LookupJob(arm, m, h, s, budget=20, start=1)]
    return jobs


def _key(r: dict) -> tuple:
    return (r["arm"], r["measured_film"], r["hetero"], r["seed"], r["start"])


# --------------------------------------------------------------------------- tests
def stratified_p(pairs: list[tuple[np.ndarray, np.ndarray]]) -> tuple[float, float]:
    """One-sided p-values (loop > OVAT, OVAT > loop) for the mean of within-pair
    differences, Welch-Satterthwaite degrees of freedom. ``pairs`` holds
    (loop films, OVAT films) per campaign pair."""
    k = len(pairs)
    d, var_terms = 0.0, []
    for a, b in pairs:
        if len(a) < 2 or len(b) < 2:
            return 1.0, 1.0
        d += (a.mean() - b.mean()) / k
        var_terms += [a.var(ddof=1) / len(a) / k ** 2, b.var(ddof=1) / len(b) / k ** 2]
    ns = [len(x) for ab in pairs for x in ab]
    se2 = sum(var_terms)
    if se2 <= 0:
        return 1.0, 1.0
    df = se2 ** 2 / sum(v ** 2 / (n - 1) for v, n in zip(var_terms, ns))
    t = d / math.sqrt(se2)
    return float(stats.t.sf(t, df)), float(stats.t.sf(-t, df))


def _films(runs: list[np.ndarray], k: int) -> np.ndarray:
    return np.concatenate(runs[:k]) if k else np.array([])


def confirm_draws(rec: dict, model: VirtualKesterite, seed_key: list[int], repeats: int):
    """``repeats`` x ``MAX_CONF`` single confirmation runs of ``rec`` (QFLS, eV)."""
    lab = Lab(model, np.random.default_rng(seed_key))
    return [[lab.confirm(rec, 1) for _ in range(MAX_CONF)] for _ in range(repeats)]


DESIGNS = ("single40", "two20", "single20", "two20_pooled", "two20_conf4")


def campaign_set(cps: dict, model, seed: int, tag: list[int], repeats: int, crn_seed: int) -> dict:
    """Per-seed test outcomes for every design. ``cps[(arm, pair, n)]`` is a checkpoint."""
    roles = {("loop-dev", "A", 40): 0, ("ovat", "A", 40): 1, ("loop-dev", "A", 20): 2,
             ("ovat", "A", 20): 3, ("loop-dev", "B", 20): 4, ("ovat", "B", 20): 5}
    draws = {k: confirm_draws(cps[k]["rec"], model, [crn_seed, seed, *tag, i], repeats)
             for k, i in roles.items()}
    out = {d: {"win": [], "rev": []} for d in DESIGNS}
    for j in range(repeats):
        def f(arm, pair, n, k):
            return _films(draws[(arm, pair, n)][j], k)
        res = {
            "single40": (welch_one_sided(f("loop-dev", "A", 40, 4), f("ovat", "A", 40, 4)),
                         welch_one_sided(f("ovat", "A", 40, 4), f("loop-dev", "A", 40, 4))),
            "single20": (welch_one_sided(f("loop-dev", "A", 20, 4), f("ovat", "A", 20, 4)),
                         welch_one_sided(f("ovat", "A", 20, 4), f("loop-dev", "A", 20, 4))),
            "two20": stratified_p([(f("loop-dev", p, 20, 2), f("ovat", p, 20, 2)) for p in "AB"]),
            "two20_conf4": stratified_p([(f("loop-dev", p, 20, 4), f("ovat", p, 20, 4)) for p in "AB"]),
        }
        la = np.concatenate([f("loop-dev", p, 20, 2) for p in "AB"])
        oa = np.concatenate([f("ovat", p, 20, 2) for p in "AB"])
        res["two20_pooled"] = (welch_one_sided(la, oa), welch_one_sided(oa, la))
        for d, (p, prev) in res.items():
            out[d]["win"].append(p < ALPHA)
            out[d]["rev"].append(prev < ALPHA)

    def gap(n, pairs, field):
        return float(np.mean([cps[("loop-dev", p, n)][field] - cps[("ovat", p, n)][field] for p in pairs]))
    truth = {"single40": (40, "A"), "single20": (20, "A"), "two20": (20, "AB"),
             "two20_pooled": (20, "AB"), "two20_conf4": (20, "AB")}
    for d, (n, pairs) in truth.items():
        out[d]["device_gap_mv"] = gap(n, pairs, "device_gain_mev")
        out[d]["qfls_gap_mev"] = gap(n, pairs, "true_gain_mev")
        out[d]["power"] = float(np.mean(out[d].pop("win")))
        out[d]["wrong_way"] = float(np.mean(out[d].pop("rev")))
    return out


def summarize(results: list[dict], repeats: int = 50, crn_seed: int = 505) -> dict:
    idx = {_key(r): r for r in results}
    seeds = sorted({r["seed"] for r in results})
    out = {"surface": "synthetic virtual-kesterite test surface (emulator v0); not kesterite data",
           "alpha": ALPHA, "repeats": repeats}
    for h in HETEROS_M0:
        for m in MEASURED_FILM:
            model = VirtualKesterite(1.0, noise_for(m, h))
            tag = [int(m * 10), int(h * 10)]
            per = []
            starts = []
            for s in seeds:
                need = {(a, "A", n): idx.get((a, m, h, s, 0)) for a in ARMS for n in (40, 20)}
                need.update({(a, "B", 20): idx.get((a, m, h, s, 1)) for a in ARMS})
                if any(v is None for v in need.values()):
                    continue
                cps = {k: v["checkpoints"][str(k[2])] for k, v in need.items()}
                per.append(campaign_set(cps, model, s, tag, repeats, crn_seed))
                starts.append(need[("ovat", "B", 20)]["start_true_gain_mev"])
            if not per:
                continue
            row = {"n_seeds": len(per),
                   "start_B_true_gain_mev_p10_p50_p90": [round(float(np.percentile(starts, q)), 1)
                                                         for q in (10, 50, 90)]}
            for d in DESIGNS:
                pw = np.array([p[d]["power"] for p in per])
                ww = np.array([p[d]["wrong_way"] for p in per])
                dg = np.array([p[d]["device_gap_mv"] for p in per])
                qg = np.array([p[d]["qfls_gap_mev"] for p in per])
                row[d] = {"power": round(float(pw.mean()), 3), "wrong_way": round(float(ww.mean()), 3),
                          "device_gap_median_mv": round(float(np.median(dg)), 1),
                          "p_device_gap_gt_0": round(float(np.mean(dg > 0)), 3),
                          "qfls_gap_median_mev": round(float(np.median(qg)), 1),
                          "p_qfls_gap_lt_0": round(float(np.mean(qg < 0)), 3)}
                if d != "single40":
                    base = np.array([p["single40"]["power"] for p in per])
                    bw = np.array([p["single40"]["wrong_way"] for p in per])
                    se = lambda x: round(float(x.std(ddof=1) / math.sqrt(len(x))), 3)  # noqa: E731
                    row[d]["minus_single40"] = {"power": round(float((pw - base).mean()), 3),
                                                "power_se": se(pw - base),
                                                "wrong_way": round(float((ww - bw).mean()), 3),
                                                "wrong_way_se": se(ww - bw)}
            out[f"film{m:g}_hetero{h:g}"] = row
    return out


def main():
    import argparse
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "two_campaign.jsonl")
    if not a.report_only:
        done = set()
        if os.path.exists(path):
            with open(path) as f:
                done = {_key(json.loads(line)) for line in f if line.strip()}
        jobs = [j for j in plan(a.seeds)
                if (j.arm, j.measured_film, j.hetero, j.seed, j.start) not in done]
        # longest jobs first keeps both workers busy to the end
        jobs.sort(key=lambda j: -(j.budget * (5 if j.arm == "loop-dev" else 1)))
        with Pool(a.workers) as pool, open(path, "a") as f:
            for i, r in enumerate(pool.imap_unordered(run_lookup, jobs), 1):
                f.write(json.dumps(r) + "\n")
                f.flush()
                if i % 20 == 0:
                    print(f"{i}/{len(jobs)} campaigns", flush=True)
    with open(path) as f:
        results = [json.loads(line) for line in f if line.strip()]
    results = [r for r in results if r["seed"] < a.seeds]
    summ = summarize(results)
    summ["environment"] = _blas.environment()
    with open(os.path.join(a.out, "two_campaign_summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps({k: {d: v[d] for d in ("single40", "two20")} for k, v in summ.items()
                      if isinstance(v, dict) and "single40" in v}, indent=1))


if __name__ == "__main__":
    main()
