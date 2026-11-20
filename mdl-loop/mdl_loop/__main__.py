"""python -m mdl_loop --out out [--seeds 24] [--workers 2]

Runs the A7 sweep (both arms at four M0 noise floors, plus the separable-surface
control and the two ablations), then writes results.jsonl, summary.json and the
learning-curve chart.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from multiprocessing import Pool

from .campaign import (Job, run_job, power_table, runs_needed, winners_curse, CHECKPOINTS,
                       confirmation_power, absolute_power, device_gap)

NOISES = (5.0, 10.0, 20.0, 30.0)


def plan(seeds: int) -> list[Job]:
    jobs = []
    for s in range(seeds):
        for n in NOISES:
            jobs += [Job("ovat", n, s), Job("ovat-greedy", n, s), Job("loop", n, s),
                     Job("loop-dev", n, s)]
        for n in (10.0, 20.0):
            jobs.append(Job("bo-naive", n, s))
        jobs += [Job("ovat", 10.0, s, interaction=0.0), Job("ovat-greedy", 10.0, s, interaction=0.0),
                 Job("loop", 10.0, s, interaction=0.0)]
        jobs.append(Job("loop-tr", 10.0, s))
    return jobs


def _run(job):
    return run_job(job)


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def summarize(results: list[dict]) -> dict:
    full = power_table(results, 1.0)
    sep = power_table(results, 0.0)
    naive = power_table(results, 1.0, arm_a="bo-naive", arm_b="ovat")
    tr = power_table(results, 1.0, arm_a="loop-tr", arm_b="ovat")
    greedy = power_table(results, 1.0, arm_a="loop", arm_b="ovat-greedy")
    return {
        "headroom_mev": {str(r["interaction"]): round(r["headroom_mev"], 1) for r in results},
        "power_loop_vs_ovat": full,
        "runs_for_80pct_power": runs_needed(full, 0.8),
        "runs_for_50pct_power": runs_needed(full, 0.5),
        "separable_surface_loop_vs_ovat": sep,
        "naive_bo_vs_ovat": naive,
        "trust_region_vs_ovat": tr,
        "loop_vs_greedy_ovat": greedy,
        "winners_curse_at_40": {a: winners_curse(results, a, 40)
                                for a in ("loop", "bo-naive", "ovat", "ovat-greedy")},
        "confirmation_power_at_20": confirmation_power(results, 20),
        "confirmation_power_at_40": confirmation_power(results, 40),
        "confirmation_power_at_40_alpha10": confirmation_power(results, 40, alpha=0.10),
        "confirmation_power_separable_at_40": confirmation_power(results, 40, interaction=0.0),
        "absolute_power_loop": {"20": absolute_power(results, 20), "40": absolute_power(results, 40)},
        "absolute_power_ovat": {"20": absolute_power(results, 20, arm="ovat"),
                                "40": absolute_power(results, 40, arm="ovat")},
        "device_gap_at_40": device_gap(results, 40),
        # A8: device-aware loop
        "a8_power_loopdev_vs_ovat": power_table(results, 1.0, arm_a="loop-dev", arm_b="ovat"),
        "a8_device_gap_loopdev_vs_ovat_at_40": device_gap(results, 40, arm_a="loop-dev"),
        "a8_device_gap_loopdev_vs_loop_at_40": device_gap(results, 40, arm_a="loop-dev", arm_b="loop"),
        "a8_qfls_absolute_power_loopdev": {"20": absolute_power(results, 20, arm="loop-dev"),
                                           "40": absolute_power(results, 40, arm="loop-dev")},
        "a8_device_absolute_power": {a: {"20": absolute_power(results, 20, arm=a, device=True),
                                         "40": absolute_power(results, 40, arm=a, device=True)}
                                     for a in ("loop-dev", "loop", "ovat")},
        "a8_device_h2h_power_at_40": confirmation_power(results, 40, arm_a="loop-dev", device=True,
                                                        confirm_runs=(2, 4)),
        "a8_winners_curse_device_at_40": winners_curse(results, "loop-dev", 40),
        "checkpoints": list(CHECKPOINTS),
    }


def chart(results: list[dict], path: str):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surf, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    col = {"loop": "#2a78d6", "ovat": "#eb6834"}
    lab = {"loop": "Loop (noise-aware BO)", "ovat": "OVAT control"}
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True, facecolor=surf)
    for ax, n in zip(axes, NOISES):
        ax.set_facecolor(surf)
        for arm in ("ovat", "loop"):
            G = np.array([[t["true_gain_mev"] for t in r["trace"]] for r in results
                          if r["arm"] == arm and r["noise_mev"] == n and r["interaction"] == 1.0])
            if not len(G):
                continue
            x = np.arange(1, G.shape[1] + 1)
            med = np.median(G, 0)
            ax.fill_between(x, np.percentile(G, 25, 0), np.percentile(G, 75, 0),
                            color=col[arm], alpha=0.14, lw=0)
            ax.plot(x, med, color=col[arm], lw=2)
            if n == NOISES[0]:
                ax.text(x[-1] + 0.5, med[-1], lab[arm].split(" (")[0], color=ink2, fontsize=8.5,
                        va="center")
        ax.set_title(f"M0 film-to-film σ = {n:g} meV", fontsize=10, color=ink, loc="left")
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(grid)
        ax.tick_params(colors=ink2, labelsize=8.5)
        ax.set_xlabel("furnace runs", color=ink2, fontsize=9)
        ax.set_xlim(0, 46)
    axes[0].set_ylabel("true QFLS gain over literature recipe (meV)", color=ink2, fontsize=9)
    handles = [plt.Line2D([], [], color=col[a], lw=2) for a in ("loop", "ovat")]
    fig.legend(handles, [lab["loop"], lab["ovat"]], loc="upper right", frameon=False,
               fontsize=9, ncol=2, labelcolor=ink2)
    fig.suptitle("C1 on the virtual kesterite: median and interquartile range over seeds",
                 x=0.01, ha="left", fontsize=11, color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=160, facecolor=surf)


def chart_device(results: list[dict], path: str):
    """Device-level view at the checkpoints: QFLS loop, device-aware loop, OVAT."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surf, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    col = {"loop": "#2a78d6", "ovat": "#eb6834", "loop-dev": "#1baf7a"}
    lab = {"loop": "Loop, QFLS only", "ovat": "OVAT control", "loop-dev": "Loop, device-aware (A8)"}
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True, facecolor=surf)
    for ax, n in zip(axes, NOISES):
        ax.set_facecolor(surf)
        for arm in ("ovat", "loop", "loop-dev"):
            rs = [r for r in results if r["arm"] == arm and r["noise_mev"] == n and r["interaction"] == 1.0]
            if not rs:
                continue
            x = np.array(CHECKPOINTS)
            G = np.array([[r["checkpoints"][str(c)]["device_gain_mev"] for c in CHECKPOINTS] for r in rs])
            ax.fill_between(x, np.percentile(G, 25, 0), np.percentile(G, 75, 0), color=col[arm],
                            alpha=0.12, lw=0)
            ax.plot(x, np.median(G, 0), color=col[arm], lw=2, marker="o", ms=4)
        ax.set_title(f"M0 film-to-film σ = {n:g} meV", fontsize=10, color=ink, loc="left")
        ax.axhline(0, color=grid, lw=1)
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.set_axisbelow(True)
        for sp_ in ("top", "right"):
            ax.spines[sp_].set_visible(False)
        for sp_ in ("left", "bottom"):
            ax.spines[sp_].set_color(grid)
        ax.tick_params(colors=ink2, labelsize=8.5)
        ax.set_xlabel("furnace runs", color=ink2, fontsize=9)
    axes[0].set_ylabel("true device Voc gain over literature recipe (mV)", color=ink2, fontsize=9)
    handles = [plt.Line2D([], [], color=col[a], lw=2, marker="o", ms=4) for a in ("loop-dev", "loop", "ovat")]
    fig.legend(handles, [lab[a] for a in ("loop-dev", "loop", "ovat")], loc="upper right",
               frameon=False, fontsize=9, ncol=3, labelcolor=ink2)
    fig.suptitle("Device-level outcome: median and interquartile range over 24 seeds",
                 x=0.01, ha="left", fontsize=11, color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=160, facecolor=surf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "results.jsonl")
    if not a.report_only:
        done = set()
        if os.path.exists(path):
            done = {(r["arm"], r["noise_mev"], r["seed"], r["interaction"]) for r in load(path)}
        jobs = [j for j in plan(a.seeds) if (j.arm, j.noise_mev, j.seed, j.interaction) not in done]
        t0 = time.time()
        with Pool(a.workers) as pool, open(path, "a") as f:
            for i, r in enumerate(pool.imap_unordered(_run, jobs), 1):
                f.write(json.dumps(r) + "\n")
                f.flush()
                if i % 10 == 0:
                    print(f"{i}/{len(jobs)} jobs, {time.time() - t0:.0f} s", flush=True)
    results = load(path)
    summ = summarize(results)
    with open(os.path.join(a.out, "summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    chart(results, os.path.join(a.out, "learning_curves.png"))
    chart_device(results, os.path.join(a.out, "device_outcome.png"))
    print(json.dumps({"runs_for_80pct_power": summ["runs_for_80pct_power"],
                      "runs_for_50pct_power": summ["runs_for_50pct_power"]}))


if __name__ == "__main__":
    main()
