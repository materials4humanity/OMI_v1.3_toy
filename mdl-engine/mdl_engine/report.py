"""Run both layers on the bundled seed data and write a report + charts.

    python -m mdl_engine [--out DIR] [--spectrum astmg173.csv]
"""
from __future__ import annotations
import argparse, json, os
from importlib import resources

import numpy as np

from . import ledger, temporal as T, diode, sq

BLUE, ORANGE, INK, MUTED, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def _load(name):
    return json.loads(resources.files("mdl_engine.data").joinpath(name).read_text())


def _series(R, key):
    return [(r["t"], r["eta"]) for r in R[key]]


def _style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def temporal_analysis(R) -> dict:
    out = {}
    for key in ("publication_dated", "certification_dated_mixed_area"):
        ev = _series(R, key)
        y, c = T.annual_counts(ev, 2014, 2026)
        out[key] = {
            "increments": T.increments(ev),
            "drift_2023_on": T.drift_rate(ev, 2023.2, 2027),
            "drift_since_plateau_end": T.drift_rate(ev, 2013.9, 2027),
            "n_records_2023_on": sum(1 for t, _ in T.frontier(ev) if t >= 2022.5),
            "changepoint_2014_2026": T.poisson_changepoint(y, c),
            "gate_fired_W2": T.gate_backtest(ev, 2, 2026.9),
            "gate_fired_W3": T.gate_backtest(ev, 3, 2026.9),
        }
    y, c = T.annual_counts(_series(R, "publication_dated"), 2010, 2026)
    out["changepoint_2010_2026_publication"] = T.poisson_changepoint(y, c)
    out["record_count_test"] = {
        f"k={k}": {f"ratio={r}": round(T.record_count_test(k, r)["p_value"], 4)
                   for r in (1.3, 2, 3, 10)} | {"ratio_needed_p05": round(T.ratio_needed(k), 1)}
        for k in (3, 4, 5, 6)}
    out["static_null_reach_15p04"] = {
        f"tail={b}": {f"ratio={r}": T.simulate_static_null(12.6, 15.04, 200, int(200 * (r - 1)), b,
                                                          n_sim=4000)["p_reach_target"]
                      for r in (1.3, 2, 3, 10)} for b in (0.3, 0.5, 0.8)}
    out["window_calibration"] = {
        "outlier_incumbent": T.calibrate_window(incumbent_lead=1.0, n_sim=2000),
        "incumbent_at_capability": T.calibrate_window(incumbent_lead=0.0, n_sim=2000)}
    return out


def charts(R, events, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF,
                         "savefig.facecolor": SURF})
    paths = []

    # 1. Frontier on two clocks
    fig, ax = plt.subplots(figsize=(7.2, 4.2)); _style(ax)
    for key, col, lab in (("publication_dated", BLUE, "Publication-dated"),
                          ("certification_dated_mixed_area", ORANGE,
                           "Certification/table-dated (mixed area rules)")):
        f = T.frontier(_series(R, key))
        t = [x[0] for x in f] + [2026.9]; e = [x[1] for x in f] + [f[-1][1]]
        ax.step(t, e, where="post", color=col, lw=2, label=lab)
        ax.plot(t[:-1], e[:-1], "o", color=col, ms=5, mec=SURF, mew=1.5)
    ax.axvspan(2015.9, 2023.28, color=MUTED, alpha=0.08, lw=0)
    ax.text(2019.6, 15.05, "draft 2-year gate fired\n2015.9 to 2023.3", ha="center", va="top",
            fontsize=9, color=MUTED)
    ax.set_xlim(2009.5, 2027); ax.set_ylim(9, 16)
    ax.set_ylabel("Best certified efficiency (%)", color=MUTED, fontsize=9)
    ax.set_title("Kesterite record frontier: the same history on two clocks", loc="left",
                 fontsize=11, color=INK, pad=12)
    ax.legend(frameon=False, fontsize=9, loc="lower right", labelcolor=MUTED)
    p = os.path.join(outdir, "frontier_two_clocks.png"); fig.tight_layout(); fig.savefig(p, dpi=170)
    plt.close(fig); paths.append(p)

    # 2. Low-light retention: fitted device vs prior envelope
    by = {e["id"]: e for e in events}
    g = np.logspace(np.log10(0.02), 0, 40)
    fig, ax = plt.subplots(figsize=(7.2, 4.2)); _style(ax)
    d = by["cui_2026"]["device"]
    curves = []
    for n in diode.N_PRIOR:
        for rs in diode.RS_PRIOR:
            p = diode.fit_from_metrics(d["voc_v"], d["jsc_ma"], d["ff_pct"], n, rs)
            if p:
                base = diode.simulate(p)["eta_pct"]
                curves.append([diode.simulate(p, s)["eta_pct"] / base for s in g])
    curves = np.array(curves)
    ax.fill_between(g * 1000, curves.min(0), curves.max(0), color=BLUE, alpha=0.18, lw=0)
    ax.plot(g * 1000, np.median(curves, 0), color=BLUE, lw=2,
            label="15.45% device, Voc 602 mV: only Voc/Jsc/FF known (band = every diode fit consistent with them)")
    f = by["fitted_15p4_ref30"]["device"]
    p = diode._build(f["voc_v"], f["jsc_ma"], f["n"], f["rs"], f["rsh"], 298.15)
    base = diode.simulate(p)["eta_pct"]
    ax.plot(g * 1000, [diode.simulate(p, s)["eta_pct"] / base for s in g], color=ORANGE, lw=2,
            label="15.4% device with published diode fit (n 1.42, Rsh ~970 ohm cm2)")
    ax.set_xscale("log"); ax.set_xlim(20, 1000)
    from matplotlib.ticker import NullFormatter, NullLocator
    ax.xaxis.set_minor_locator(NullLocator()); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([20, 50, 100, 200, 400, 1000]); ax.set_xticklabels(["20", "50", "100", "200", "400", "1000"])
    ax.set_xlabel("Irradiance (W/m2)", color=MUTED, fontsize=9)
    ax.set_ylabel("Efficiency relative to STC", color=MUTED, fontsize=9)
    ax.set_title("Two ~15.4% kesterite cells: what STC numbers do not tell you about low light",
                 loc="left", fontsize=11, color=INK, pad=12)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", labelcolor=MUTED)
    ax.set_ylim(0, 1.25); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    p_ = os.path.join(outdir, "low_light_retention.png"); fig.tight_layout(); fig.savefig(p_, dpi=170)
    plt.close(fig); paths.append(p_)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="out")
    ap.add_argument("--spectrum", default=None, help="ASTM G173 csv (NREL layout)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    spec = sq.load_spectrum(a.spectrum) if a.spectrum else None
    events, R = _load("events.json"), _load("records.json")
    entries = ledger.run(events, spec)
    temporal = temporal_analysis(R)
    with open(os.path.join(a.out, "implication_ledger.json"), "w") as f:
        f.write(ledger.dumps(entries))
    with open(os.path.join(a.out, "temporal_analysis.json"), "w") as f:
        json.dump(temporal, f, indent=2, default=float)
    with open(os.path.join(a.out, "implication_ledger.md"), "w") as f:
        f.write("# Implication ledger - deterministic layer output\n\n")
        f.write("\n\n".join(ledger.render_markdown(e) for e in entries) + "\n")
    paths = charts(R, events, a.out)
    print("wrote", a.out, [os.path.basename(p) for p in paths])
    return entries, temporal


if __name__ == "__main__":
    main()
