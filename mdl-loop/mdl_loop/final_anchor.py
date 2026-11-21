"""0.4: anchor the final recommendation before the loop stops, measured against 0.3.

The 0.2 memo (section 2.4) found the device-aware loop over-claims its device
gain because the recommended film is usually not anchored. In 0.4 the loop
finishes that film into a device before stopping, refits the gap model and
re-recommends (``DeviceAwareGPBO.finalize``). Every campaign record carries
both answers: the 0.4 checkpoint at top level and the 0.3 one under ``v03``,
from the same campaign (see ``campaign.finalize_copy``), so the comparison is
paired campaign by campaign.

Cells measured, device-aware loop only:

* the M0 lookup cells (``m0.MEASURED_FILM`` x both noise-shape assumptions),
* the 10 meV cell of the main sweep (``campaign.run_job``).

Per cell and view: over-claim (claimed minus true device gain, median and
90th percentile), true device and QFLS gain, and the C1 primary power (4
confirmation runs vs 4 literature runs, > 5 meV QFLS margin, one-sided Welch,
alpha 0.05). Primary power uses common random numbers: one generator per
campaign for the literature runs and one for the recipe's runs, identical for
both views, so a campaign whose recommendation did not change contributes the
same draws to both.

All of it runs on the synthetic virtual-kesterite surface.

    python -m mdl_loop.final_anchor --out out --seeds 24
"""
from __future__ import annotations

import os

# Single-threaded BLAS: about 3x faster with two worker processes on this code,
# and it removes thread-count dependence of the floating-point results.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json  # noqa: E402
from dataclasses import dataclass  # noqa: E402

import numpy as np  # noqa: E402

from .campaign import Job, run_job, welch_one_sided  # noqa: E402
from .emulator import NoiseModel, VirtualKesterite  # noqa: E402
from .lab import Lab  # noqa: E402
from .m0 import MEASURED_FILM, LookupJob, noise_for, run_lookup  # noqa: E402
from .space import LITERATURE_RECIPE  # noqa: E402

MAIN_NOISE = 10.0
HETEROS = (1.0, 0.0)


@dataclass(frozen=True)
class Cell:
    kind: str          # "m0" | "main"
    film: float        # measured film sd at the literature recipe (m0) or nominal sd (main), meV
    hetero: float = 1.0

    @property
    def key(self) -> str:
        if self.kind == "main":
            return f"main_film{self.film:g}"
        return f"m0_film{self.film:g}_hetero{self.hetero:g}"

    def noise(self) -> NoiseModel:
        return NoiseModel(film_mev=self.film) if self.kind == "main" else noise_for(self.film, self.hetero)


def cells() -> list[Cell]:
    return [Cell("m0", m, h) for h in HETEROS for m in MEASURED_FILM] + [Cell("main", MAIN_NOISE)]


def run_cell(arg: tuple) -> dict:
    """One device-aware campaign in one cell; returns a record with a ``cell`` key."""
    cell, seed = arg
    if cell.kind == "main":
        r = run_job(Job("loop-dev", cell.film, seed))
        cps = {str(k): v for k, v in r["checkpoints"].items()}
    else:
        r = run_lookup(LookupJob("loop-dev", cell.film, cell.hetero, seed))
        cps = r["checkpoints"]
    return {"cell": cell.key, "kind": cell.kind, "film": cell.film, "hetero": cell.hetero,
            "seed": seed, "checkpoints": cps}


VIEWS = ("v03", "v04", "until_anchored")


def view(cp: dict, which: str) -> dict:
    """0.3 record, 0.4 record (top level), or the until-anchored sensitivity variant."""
    return cp if which == "v04" else cp[which]


def _diag(cps: list[dict], which: str) -> dict:
    g = [view(cp, which)["final_anchor"] for cp in cps]
    return {"p_pre_rec_already_anchored": round(float(np.mean([x["pre_anchored"] for x in g])), 3),
            "p_device_made": round(float(np.mean([x["device_made"] for x in g])), 3),
            "devices_made_mean": round(float(np.mean([x["devices_made"] for x in g])), 2),
            "p_rec_changed": round(float(np.mean([x["rec_changed"] for x in g])), 3),
            "p_final_rec_anchored": round(float(np.mean([x["final_anchored"] for x in g])), 3)}


def primary_power(recs: list[tuple[int, dict]], cell: Cell, conf_runs: int = 4, lit_runs: int = 4,
                  margin_mev: float = 5.0, alpha: float = 0.05, repeats: int = 30,
                  seed: int = 404) -> tuple[float, list[float]]:
    """C1 primary power over campaigns, common random numbers per campaign.

    ``recs`` is a list of (campaign seed, recommended recipe). Returns the
    pooled power and the per-campaign pass fractions.
    """
    model = VirtualKesterite(1.0, cell.noise())
    lit_q = model.qfls(LITERATURE_RECIPE)
    per = []
    tag = [int(cell.film * 10), int(cell.hetero * 10), {"m0": 0, "main": 1}[cell.kind]]
    for s, rec in recs:
        lab_lit = Lab(model, np.random.default_rng([seed, s, *tag, 0]))
        lab_rec = Lab(model, np.random.default_rng([seed, s, *tag, 1]))
        hits = 0
        for _ in range(repeats):
            lit = lab_lit.confirm(LITERATURE_RECIPE, lit_runs) - lit_q
            a = lab_rec.confirm(rec, conf_runs) - lit_q
            hits += welch_one_sided(a - margin_mev / 1000.0, lit) < alpha
        per.append(hits / repeats)
    return float(np.mean(per)), per


def _q(v, p):
    return round(float(np.percentile(v, p)), 1)


def summarize(results: list[dict], ns=(40, 20), repeats: int = 30) -> dict:
    by: dict[str, list[dict]] = {}
    for r in results:
        by.setdefault(r["cell"], []).append(r)
    cell_of = {c.key: c for c in cells()}
    out = {"surface": "synthetic virtual-kesterite test surface (emulator v0); not kesterite data"}
    for key in [c.key for c in cells() if c.key in by]:
        rs = sorted(by[key], key=lambda r: r["seed"])
        cell = cell_of[key]
        row = {"n_seeds": len(rs)}
        for n in ns:
            cps = [r["checkpoints"][str(n)] for r in rs]
            d = {}
            per_view = {}
            for which in VIEWS:
                vs = [view(cp, which) for cp in cps]
                over = [v["claimed_gain_mev"] - v["device_gain_mev"] for v in vs]
                dev = [v["device_gain_mev"] for v in vs]
                pw, per = primary_power([(r["seed"], v["rec"]) for r, v in zip(rs, vs)], cell,
                                        repeats=repeats)
                per_view[which] = (np.array(over), np.array(dev), np.array(per))
                d[which] = {"overclaim_median_mv": _q(over, 50), "overclaim_p90_mv": _q(over, 90),
                            "device_gain_median_mv": _q(dev, 50),
                            "qfls_gain_median_mev": _q([v["true_gain_mev"] for v in vs], 50),
                            "primary_power": round(pw, 3)}
                if which != "v03":
                    d[which]["final_anchor"] = _diag(cps, which)
                    dd = per_view[which][1] - per_view["v03"][1]
                    d[which]["paired_minus_v03"] = {
                        "device_gain_median_mv": _q(dd, 50),
                        "device_gain_mean_mv": round(float(dd.mean()), 1),
                        "p_device_gain_lower": round(float(np.mean(dd < -1e-9)), 3),
                        "p_device_gain_higher": round(float(np.mean(dd > 1e-9)), 3),
                        "abs_overclaim_change_median_mv": _q(np.abs(per_view[which][0])
                                                             - np.abs(per_view["v03"][0]), 50)}
                    dp = per_view[which][2] - per_view["v03"][2]
                    d[which]["paired_minus_v03"]["primary_power"] = round(float(dp.mean()), 3)
                    d[which]["paired_minus_v03"]["primary_power_se"] = round(
                        float(dp.std(ddof=1) / np.sqrt(len(dp))), 3)
            row[str(n)] = d
        out[key] = row
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
    path = os.path.join(a.out, "final_anchor.jsonl")
    if not a.report_only:
        done = set()
        if os.path.exists(path):
            with open(path) as f:
                done = {(r["cell"], r["seed"]) for r in map(json.loads, f) if r}
        jobs = [(c, s) for s in range(a.seeds) for c in cells() if (c.key, s) not in done]
        with Pool(a.workers) as pool, open(path, "a") as f:
            for i, r in enumerate(pool.imap_unordered(run_cell, jobs), 1):
                f.write(json.dumps(r) + "\n")
                f.flush()
                if i % 10 == 0:
                    print(f"{i}/{len(jobs)} campaigns", flush=True)
    with open(path) as f:
        results = [json.loads(line) for line in f if line.strip()]
    results = [r for r in results if r["seed"] < a.seeds]
    summ = summarize(results)
    with open(os.path.join(a.out, "final_anchor_summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps({k: v.get("40") for k, v in summ.items() if isinstance(v, dict)}, indent=1))


if __name__ == "__main__":
    main()
