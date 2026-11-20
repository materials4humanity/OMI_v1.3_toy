"""Campaign driver and the C1 power analysis.

C1's kill condition in the next-stage plan reads: "No separation from the
control after a pre-registered number of runs." This module supplies that
number. For each assumed M0 noise floor it runs both arms many times on the
emulator and asks: after N furnace runs per arm, how often does a
pre-registered confirmation test (two replicate furnace runs of each arm's
recommended recipe, one-sided Welch t-test at alpha = 0.05) declare the loop
better than OVAT?
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

from .emulator import VirtualKesterite, NoiseModel
from .lab import Lab
from .space import LITERATURE_RECIPE
from .strategies import OVAT, GPBO, DeviceAwareGPBO

CHECKPOINTS = (10, 15, 20, 25, 30, 40)


@dataclass
class Job:
    arm: str              # "loop" | "loop-dev" | "ovat" | "ovat-greedy" | "bo-naive" | "loop-tr"
    noise_mev: float
    seed: int
    interaction: float = 1.0
    budget: int = 40
    confirm_runs: int = 2


def run_job(job: Job) -> dict:
    model = VirtualKesterite(job.interaction, NoiseModel(film_mev=job.noise_mev))
    model.optimum()
    rng = np.random.default_rng([job.seed, int(job.noise_mev * 10), int(job.interaction * 10),
                                 {"loop": 1, "ovat": 5, "bo-naive": 3, "loop-tr": 4, "ovat-greedy": 2,
                                  "loop-dev": 6}[job.arm]])
    lab = Lab(model, rng)
    if job.arm == "ovat":
        strat = OVAT(LITERATURE_RECIPE, careful=True)
    elif job.arm == "ovat-greedy":
        strat = OVAT(LITERATURE_RECIPE, careful=False)
    elif job.arm == "loop-dev":
        strat = DeviceAwareGPBO(LITERATURE_RECIPE, rng)
    elif job.arm == "loop-tr":
        strat = GPBO(LITERATURE_RECIPE, rng, noise_aware=True, trust_region=True, n_init=4)
    else:
        strat = GPBO(LITERATURE_RECIPE, rng, noise_aware=(job.arm == "loop"))
    lit_q = model.qfls(LITERATURE_RECIPE)
    lit_dev = model.device_voc(LITERATURE_RECIPE)
    trace, cps = [], {}
    for r in range(1, job.budget + 1):
        strat.step(lab)
        rec, claimed = strat.recommend(lab)
        true_q = model.qfls(rec)
        ref = lit_dev if job.arm == "loop-dev" else lit_q      # what the arm's claim is about
        trace.append({"run": r, "true_gain_mev": 1000 * (true_q - lit_q),
                      "true_device_gain_mev": 1000 * (model.device_voc(rec) - lit_dev),
                      "claimed_gain_mev": (1000 * (claimed - ref)) if claimed == claimed and
                      claimed != -math.inf else None})
        if r in CHECKPOINTS:
            conf = lab.confirm(rec, job.confirm_runs)
            cps[r] = {"rec": rec, "true_gain_mev": 1000 * (true_q - lit_q),
                      "device_gain_mev": 1000 * (model.device_voc(rec) - lit_dev),
                      "urbach_mev": model.urbach(rec),
                      "confirm_mev": (1000 * (conf - lit_q)).tolist(),
                      "n_failed": sum(o.failed for o in lab.history),
                      "n_devices": lab.n_devices}
    return {"arm": job.arm, "noise_mev": job.noise_mev, "seed": job.seed,
            "interaction": job.interaction, "headroom_mev": model.headroom_mev(),
            "trace": trace, "checkpoints": cps}


def welch_one_sided(a, b) -> float:
    """p-value for mean(a) > mean(b)."""
    a, b = np.asarray(a), np.asarray(b)
    if len(a) < 2 or len(b) < 2:
        return 1.0
    t, p = stats.ttest_ind(a, b, equal_var=False, alternative="greater")
    return float(p) if p == p else 1.0


def power_table(results: list[dict], interaction: float = 1.0, arm_a="loop", arm_b="ovat",
                alpha: float = 0.05, margin_mev: float = 5.0) -> dict:
    """Per noise level and checkpoint: separation power and true-gap statistics."""
    by = {}
    for r in results:
        if r["interaction"] != interaction:
            continue
        by.setdefault((r["noise_mev"], r["seed"]), {})[r["arm"]] = r
    out = {}
    for (noise, seed), arms in by.items():
        if arm_a not in arms or arm_b not in arms:
            continue
        for n in CHECKPOINTS:
            A, B = arms[arm_a]["checkpoints"].get(str(n)) or arms[arm_a]["checkpoints"].get(n), \
                   arms[arm_b]["checkpoints"].get(str(n)) or arms[arm_b]["checkpoints"].get(n)
            if A is None or B is None:
                continue
            d = out.setdefault(noise, {}).setdefault(n, {"sig": [], "gap": [], "a": [], "b": [],
                                                         "a_dev": [], "b_dev": [], "rev": []})
            p = welch_one_sided(A["confirm_mev"], B["confirm_mev"])
            prev = welch_one_sided(B["confirm_mev"], A["confirm_mev"])
            d["sig"].append(p < alpha)
            d["rev"].append(prev < alpha)
            d["gap"].append(A["true_gain_mev"] - B["true_gain_mev"])
            d["a"].append(A["true_gain_mev"])
            d["b"].append(B["true_gain_mev"])
            d["a_dev"].append(A["device_gain_mev"])
            d["b_dev"].append(B["device_gain_mev"])
    table = {}
    for noise, rows in sorted(out.items()):
        table[noise] = {}
        for n, d in sorted(rows.items()):
            g = np.array(d["gap"])
            table[noise][n] = {
                "n_seeds": len(g),
                "power": round(float(np.mean(d["sig"])), 3),
                "wrong_way": round(float(np.mean(d["rev"])), 3),
                "p_true_gap_gt_margin": round(float(np.mean(g > margin_mev)), 3),
                "gap_median_mev": round(float(np.median(g)), 1),
                f"{arm_a}_gain_median_mev": round(float(np.median(d["a"])), 1),
                f"{arm_b}_gain_median_mev": round(float(np.median(d["b"])), 1),
                f"{arm_a}_device_gain_median_mev": round(float(np.median(d["a_dev"])), 1),
                f"{arm_b}_device_gain_median_mev": round(float(np.median(d["b_dev"])), 1),
            }
    return table


def runs_needed(table: dict, target: float = 0.8) -> dict:
    out = {}
    for noise, rows in table.items():
        hit = [n for n, v in sorted(rows.items()) if v["power"] >= target]
        out[noise] = hit[0] if hit else None
    return out


def winners_curse(results: list[dict], arm: str, n: int, interaction: float = 1.0) -> dict:
    """Claimed versus true gain of the recommended recipe at run n."""
    by = {}
    for r in results:
        if r["arm"] != arm or r["interaction"] != interaction:
            continue
        t = r["trace"][n - 1]
        if t["claimed_gain_mev"] is None:
            continue
        truth = t["true_device_gain_mev"] if arm == "loop-dev" else t["true_gain_mev"]
        by.setdefault(r["noise_mev"], []).append(t["claimed_gain_mev"] - truth)
    return {k: {"median_overclaim_mev": round(float(np.median(v)), 1),
                "p90_overclaim_mev": round(float(np.percentile(v, 90)), 1), "n": len(v)}
            for k, v in sorted(by.items())}


def confirmation_power(results: list[dict], n: int, confirm_runs=(2, 4, 6, 8), alpha: float = 0.05,
                       repeats: int = 50, interaction: float = 1.0, arm_a="loop", arm_b="ovat",
                       seed: int = 12345, device: bool = False) -> dict:
    """Power of the end-of-campaign test as a function of confirmation runs per arm.

    Takes the recipes each arm recommended at run ``n`` and re-simulates the
    confirmation test ``repeats`` times for each confirmation size, so the
    estimate integrates over confirmation noise rather than one draw.
    """
    rng = np.random.default_rng(seed)
    pairs = {}
    for r in results:
        if r["interaction"] == interaction and r["arm"] in (arm_a, arm_b):
            cp = r["checkpoints"].get(str(n)) or r["checkpoints"].get(n)
            pairs.setdefault((r["noise_mev"], r["seed"]), {})[r["arm"]] = cp["rec"]
    out = {}
    for (noise, sd), arms in sorted(pairs.items()):
        if arm_a not in arms or arm_b not in arms:
            continue
        model = VirtualKesterite(interaction, NoiseModel(film_mev=noise))
        lab = Lab(model, rng)
        for k in confirm_runs:
            d = out.setdefault(noise, {}).setdefault(k, {"sig": [], "rev": []})
            conf = lab.confirm_device if device else lab.confirm
            for _ in range(repeats):
                a, b = conf(arms[arm_a], k), conf(arms[arm_b], k)
                d["sig"].append(welch_one_sided(a, b) < alpha)
                d["rev"].append(welch_one_sided(b, a) < alpha)
    return {noise: {k: {"power": round(float(np.mean(v["sig"])), 3),
                        "wrong_way": round(float(np.mean(v["rev"])), 3)} for k, v in rows.items()}
            for noise, rows in out.items()}


def absolute_power(results: list[dict], n: int, arm: str = "loop", confirm_runs=(2, 4),
                   margin_mev: float = 5.0, lit_runs: int = 4, alpha: float = 0.05,
                   repeats: int = 30, interaction: float = 1.0, seed: int = 7,
                   device: bool = False) -> dict:
    """Power of an absolute criterion: the arm's confirmed recipe beats the
    literature recipe (replicated over ``lit_runs`` M0 furnace runs) by more than
    ``margin_mev``, one-sided Welch at ``alpha``."""
    rng = np.random.default_rng(seed)
    out = {}
    for r in results:
        if r["arm"] != arm or r["interaction"] != interaction:
            continue
        cp = r["checkpoints"].get(str(n)) or r["checkpoints"].get(n)
        lab = Lab(VirtualKesterite(interaction, NoiseModel(film_mev=r["noise_mev"])), rng)
        conf = lab.confirm_device if device else lab.confirm
        for k in confirm_runs:
            d = out.setdefault(r["noise_mev"], {}).setdefault(k, [])
            for _ in range(repeats):
                lit = conf(LITERATURE_RECIPE, lit_runs)
                a = conf(cp["rec"], k)
                d.append(welch_one_sided(a - margin_mev / 1000.0, lit) < alpha)
    return {noise: {k: round(float(np.mean(v)), 3) for k, v in sorted(rows.items())}
            for noise, rows in sorted(out.items())}


def device_gap(results: list[dict], n: int = 40, arm_a="loop", arm_b="ovat",
               interaction: float = 1.0) -> dict:
    by = {}
    for r in results:
        if r["interaction"] == interaction and r["arm"] in (arm_a, arm_b):
            by.setdefault((r["noise_mev"], r["seed"]), {})[r["arm"]] = r
    out = {}
    for (noise, _), arms in by.items():
        if arm_a in arms and arm_b in arms:
            ca = arms[arm_a]["checkpoints"].get(str(n)) or arms[arm_a]["checkpoints"].get(n)
            cb = arms[arm_b]["checkpoints"].get(str(n)) or arms[arm_b]["checkpoints"].get(n)
            out.setdefault(noise, {"q": [], "d": [], "se": []})
            out[noise]["q"].append(ca["true_gain_mev"] - cb["true_gain_mev"])
            out[noise]["d"].append(ca["device_gain_mev"] - cb["device_gain_mev"])
            out[noise]["se"].append(ca["rec"]["se_mg"])
    return {noise: {"qfls_gap_median_mev": round(float(np.median(v["q"])), 1),
                    "device_gap_median_mev": round(float(np.median(v["d"])), 1),
                    "p_device_gap_gt_0": round(float(np.mean(np.array(v["d"]) > 0)), 2),
                    f"{arm_a}_se_mg_median": round(float(np.median(v["se"])))}
            for noise, v in sorted(out.items())}
