"""M0 design support: map what M0 measures to C1's power, and size M0 itself.

Two questions the B1 design note needs answered:

1. M0 measures noise on the *literature recipe*. The C1 simulations set noise
   at an *optimal* film and scaled it up for poorer films (``hetero``). Whether
   poorer films really are noisier is unknown, so the lookup is run under both
   assumptions: given M0's measured film-to-film and run-to-run spread at the
   literature recipe, what is C1's primary-criterion power?
2. How many furnace runs, films per run and PL spots per film does M0 need to
   estimate those spreads well enough to make the proceed / fix / stop call?
"""
from __future__ import annotations

from . import _blas  # noqa: F401  (pins BLAS threads; must precede numpy)

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

from .campaign import (CHECKPOINTS, welch_one_sided, finalize_copy, _final_anchor_diag,
                       SENSITIVITY_ROUNDS)
from .emulator import VirtualKesterite, NoiseModel
from .lab import Lab
from .space import LITERATURE_RECIPE
from .strategies import OVAT, DeviceAwareGPBO

MEASURED_FILM = (5.0, 8.0, 11.0, 15.0)     # film-to-film sd at the literature recipe, meV
RUN_RATIO = 0.5                            # run-to-run sd as a fraction of measured film sd
SPOT_MEV = 3.0                             # PL spot-to-spot plus calibration, meV
HETEROS_M0 = (1.0, 0.0)                    # noise shape: poorer films noisier / constant


def noise_for(measured_film: float, hetero: float) -> NoiseModel:
    probe = VirtualKesterite(1.0, NoiseModel(film_mev=1.0, hetero=hetero))
    nominal = probe.nominal_from_measured(measured_film)
    return NoiseModel(film_mev=nominal, hetero=hetero, run_mev=RUN_RATIO * measured_film,
                      meas_mev=SPOT_MEV)


@dataclass
class LookupJob:
    arm: str
    measured_film: float
    hetero: float
    seed: int
    budget: int = 40
    final_anchor: bool = True     # loop-dev only: anchor the final recommendation (0.4)
    start: int = 0                # 0: literature recipe; k > 0: alternative start k (0.5)


START_SCALE = 0.1   # unit-space sd of an alternative start around the literature recipe


def start_recipe(seed: int, k: int) -> dict:
    """Start point of campaign ``k`` for ``seed``: the literature recipe for k = 0,
    otherwise a perturbation of its continuous parameters (sd ``START_SCALE`` in
    unit coordinates, categorical settings kept), drawn from its own generator.
    Both arms of a campaign pair share it. No emulator truth is used to pick it,
    so a start can be better or worse than the literature recipe.
    """
    if k == 0:
        return dict(LITERATURE_RECIPE)
    from .space import P0_SPACE
    return P0_SPACE.perturb(LITERATURE_RECIPE, np.random.default_rng([seed, k, 2027]),
                            START_SCALE, p_flip=0.0)


def run_lookup(job: LookupJob) -> dict:
    nm = noise_for(job.measured_film, job.hetero)
    model = VirtualKesterite(1.0, nm)
    model.optimum()
    key = [job.seed, int(job.measured_film * 10), int(job.hetero * 10),
           {"loop-dev": 61, "ovat": 51}[job.arm], 2026]
    rng = np.random.default_rng(key + [job.start] if job.start else key)
    lab = Lab(model, rng)
    start = start_recipe(job.seed, job.start)
    strat = (DeviceAwareGPBO(start, rng) if job.arm == "loop-dev"
             else OVAT(start, careful=True))
    lit_q, lit_d = model.qfls(LITERATURE_RECIPE), model.device_voc(LITERATURE_RECIPE)
    cps = {}
    ref = lit_d if job.arm == "loop-dev" else lit_q        # what the arm's claim is about

    def entry(rec, claimed):
        return {"rec": rec, "true_gain_mev": 1000 * (model.qfls(rec) - lit_q),
                "device_gain_mev": 1000 * (model.device_voc(rec) - lit_d),
                "claimed_gain_mev": 1000 * (claimed - ref) if math.isfinite(claimed) else None}

    for r in range(1, job.budget + 1):
        strat.step(lab)
        if r in CHECKPOINTS:
            fin = (finalize_copy(strat, lab) if job.arm == "loop-dev" and job.final_anchor
                   else None)
            rec, claimed = strat.recommend(lab)
            cps[str(r)] = entry(rec, claimed)
            if fin is not None:
                f, lab2 = fin
                cps[str(r)] = {**entry(f["rec"], f["claimed"]), "n_devices": lab2.n_devices,
                               "final_anchor": _final_anchor_diag(f), "v03": cps[str(r)]}
                g, _ = finalize_copy(strat, lab, SENSITIVITY_ROUNDS)
                cps[str(r)]["until_anchored"] = {**entry(g["rec"], g["claimed"]),
                                                 "final_anchor": _final_anchor_diag(g)}
    return {"arm": job.arm, "measured_film": job.measured_film, "hetero": job.hetero,
            "seed": job.seed, "start": job.start, "budget": job.budget,
            "start_true_gain_mev": 1000 * (model.qfls(start) - lit_q),
            "nominal_film": nm.film_mev, "run_mev": nm.run_mev,
            "checkpoints": cps}


def lookup_table(results: list[dict], n: int = 40, conf_runs: int = 4, lit_runs: int = 4,
                 margin_mev: float = 5.0, alpha: float = 0.05, repeats: int = 30,
                 seed: int = 99) -> dict:
    """C1 primary power and median gains per (measured film sd, hetero)."""
    rng = np.random.default_rng(seed)
    cells = {}
    for r in results:
        cells.setdefault((r["measured_film"], r["hetero"]), []).append(r)
    out = {}
    for (mf, h), rs in sorted(cells.items()):
        lab = Lab(VirtualKesterite(1.0, noise_for(mf, h)), rng)
        row = {}
        for arm in ("loop-dev", "ovat"):
            ra = [r for r in rs if r["arm"] == arm]
            if not ra:
                continue
            sig = []
            for r in ra:
                rec = r["checkpoints"][str(n)]["rec"]
                for _ in range(repeats):
                    lit = lab.confirm(LITERATURE_RECIPE, lit_runs)
                    a = lab.confirm(rec, conf_runs)
                    sig.append(welch_one_sided(a - margin_mev / 1000.0, lit) < alpha)
            row[arm] = {
                "primary_power": round(float(np.mean(sig)), 3),
                "qfls_gain_median_mev": round(float(np.median(
                    [r["checkpoints"][str(n)]["true_gain_mev"] for r in ra])), 1),
                "device_gain_median_mev": round(float(np.median(
                    [r["checkpoints"][str(n)]["device_gain_mev"] for r in ra])), 1),
                "n_seeds": len(ra)}
        row["nominal_film_mev"] = round(rs[0]["nominal_film"], 2)
        out[f"film{mf:g}_hetero{h:g}"] = row
    return out


# --------------------------------------------------------------------------- M0 sizing
def nested_estimates(y: np.ndarray) -> dict:
    """Method-of-moments variance components for a balanced runs x films x spots array (meV)."""
    R, F, S = y.shape
    film_means = y.mean(axis=2)
    run_means = film_means.mean(axis=1)
    grand = run_means.mean()
    ms_spot = ((y - film_means[:, :, None]) ** 2).sum() / (R * F * (S - 1))
    ms_film = S * ((film_means - run_means[:, None]) ** 2).sum() / (R * (F - 1))
    ms_run = F * S * ((run_means - grand) ** 2).sum() / (R - 1)
    v_spot = ms_spot
    v_film = max(0.0, (ms_film - ms_spot) / S)
    v_run = max(0.0, (ms_run - ms_film) / (F * S))
    return {"spot": math.sqrt(v_spot), "film": math.sqrt(v_film), "run": math.sqrt(v_run),
            "ms": (ms_run, ms_film, ms_spot), "df": (R - 1, R * (F - 1), R * F * (S - 1))}


def film_upper_bound(est: dict, S: int, level: float = 0.8) -> float:
    """Approximate one-sided upper bound on the film sd (Satterthwaite on MS_film/S)."""
    ms_run, ms_film, ms_spot = est["ms"]
    _, df_f, df_s = est["df"]
    v = max(1e-9, (ms_film - ms_spot) / S)
    num = v ** 2
    den = (ms_film / S) ** 2 / df_f + (ms_spot / S) ** 2 / df_s
    nu = max(1.0, num / den)
    return math.sqrt(nu * v / stats.chi2.ppf(1 - level, nu))


def run_ci(est: dict, F: int, S: int, level: float = 0.8) -> tuple:
    """Approximate two-sided CI on the run sd (Satterthwaite)."""
    ms_run, ms_film, _ = est["ms"]
    df_r, df_f, _ = est["df"]
    v = max(1e-9, (ms_run - ms_film) / (F * S))
    den = (ms_run / (F * S)) ** 2 / df_r + (ms_film / (F * S)) ** 2 / df_f
    nu = max(1.0, v ** 2 / den)
    lo = math.sqrt(nu * v / stats.chi2.ppf(1 - (1 - level) / 2, nu))
    hi = math.sqrt(nu * v / stats.chi2.ppf((1 - level) / 2, nu))
    return lo, hi


def size_m0(true_film: float, true_run: float, R: int, F: int = 4, S: int = 3,
            spot: float = SPOT_MEV, n_sim: int = 4000, seed: int = 0,
            film_threshold: float | None = None) -> dict:
    """Precision of M0's estimates for one design, by simulation."""
    rng = np.random.default_rng(seed)
    films, runs, ubs, run_w = [], [], [], []
    passes = 0
    for _ in range(n_sim):
        y = (rng.normal(0, true_run, (R, 1, 1)) + rng.normal(0, true_film, (R, F, 1))
             + rng.normal(0, spot, (R, F, S)))
        e = nested_estimates(y)
        films.append(e["film"])
        runs.append(e["run"])
        ub = film_upper_bound(e, S)
        ubs.append(ub)
        lo, hi = run_ci(e, F, S)
        run_w.append(hi / max(lo, 1e-6))
        if film_threshold is not None and ub <= film_threshold:
            passes += 1
    films, runs = np.array(films), np.array(runs)
    out = {"R": R, "F": F, "S": S, "furnace_runs": R, "films": R * F, "pl_spots": R * F * S,
           "film_rel_sd": round(float(films.std() / true_film), 3),
           "film_p10_p90": [round(float(np.percentile(films, 10)), 1),
                            round(float(np.percentile(films, 90)), 1)],
           "run_p10_p90": [round(float(np.percentile(runs, 10)), 1),
                           round(float(np.percentile(runs, 90)), 1)],
           "run_zero_estimates": round(float(np.mean(runs == 0.0)), 3),
           "run_ci80_ratio_median": round(float(np.median(run_w)), 1)}
    if film_threshold is not None:
        out["p_pass"] = round(passes / n_sim, 3)
    return out


def main():
    """python -m mdl_loop.m0 --out out   (lookup sweep with resume, then summaries)"""
    import argparse
    import json
    import os
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "m0_lookup.jsonl")
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                done.add((r["arm"], r["measured_film"], r["hetero"], r["seed"]))
    jobs = [LookupJob(arm, m, h, s) for s in range(a.seeds) for h in HETEROS_M0
            for m in MEASURED_FILM for arm in ("loop-dev", "ovat")]
    jobs = [j for j in jobs if (j.arm, j.measured_film, j.hetero, j.seed) not in done]
    with Pool(a.workers) as pool, open(path, "a") as f:
        for r in pool.imap_unordered(run_lookup, jobs):
            f.write(json.dumps(r) + "\n")
            f.flush()
    with open(path) as f:
        results = [json.loads(line) for line in f if line.strip()]
    summary = {"lookup_n40": lookup_table(results, 40), "lookup_n20": lookup_table(results, 20, repeats=15),
               "sizing_at_11": {R: size_m0(11.0, 5.5, R, n_sim=3000, seed=7) for R in (4, 8, 12)},
               "go_rule_ub80_le_13": {R: {tf: size_m0(float(tf), 0.5 * tf, R, n_sim=2000,
                                                       film_threshold=13.0, seed=tf * 7 + R)["p_pass"]
                                           for tf in (8, 10, 11, 12, 13, 15, 17)} for R in (8, 12)}}
    summary["environment"] = _blas.environment()
    with open(os.path.join(a.out, "m0_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary["go_rule_ub80_le_13"]))


if __name__ == "__main__":
    main()
