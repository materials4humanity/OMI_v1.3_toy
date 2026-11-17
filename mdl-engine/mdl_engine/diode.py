"""One-diode model, parameter recovery, and low-irradiance projection (design 5.2).

    J = Jph - J0*(exp((V + J*Rs)/(n*Vt)) - 1) - (V + J*Rs)/Rsh

Solved parametrically in the junction voltage Vj = V + J*Rs, so no implicit
root-finding is needed for a full curve.

Units at the API boundary: V, mA/cm^2, ohm*cm^2, FF in percent, G in suns.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
from scipy import optimize

from .constants import T_CELL, P_STC, vt

LOW_G_SUNS = (1.0, 0.4, 0.2, 0.1, 0.05)       # 1000/400/200/100/50 W/m^2
LUX_LEVELS = (1000, 500, 200)

# Indoor conversion assumptions (white LED). Stated, not hidden.
LED_LER_LM_PER_W = 320.0      # luminous efficacy of radiation
LED_MEAN_PHOTON_EV = 2.25     # power-weighted mean photon energy
EQE_VISIBLE_DEFAULT = 0.85


@dataclass(frozen=True)
class DiodeParams:
    jph_ma: float      # photocurrent at 1 sun
    j0_ma: float
    n: float
    rs: float          # ohm cm^2
    rsh: float         # ohm cm^2
    temp_k: float = T_CELL
    dn_per_decade: float = 0.0   # ideality rise per decade of falling intensity

    def as_dict(self):
        return asdict(self)


def _effective(p: DiodeParams, suns: float):
    """(n, J0) at a given intensity.

    With dn_per_decade = 0 these are just (n, J0). Otherwise the LOCAL ideality
    n(G) = n + dn*log10(1/G) is what sets dVoc/dlnG (deep defects make Voc fall
    faster as light falls: the Park et al. mechanism), so J0 is re-referenced to
    keep the junction's Voc(G) on that integrated path.
    """
    if p.dn_per_decade == 0.0 or suns >= 1.0:
        return p.n, p.j0_ma * 1e-3
    v_t = vt(p.temp_k)
    dec = math.log10(1.0 / suns)
    voc1 = p.n * v_t * math.log(p.jph_ma / p.j0_ma + 1.0)
    voc = voc1 - v_t * math.log(10) * (p.n * dec + 0.5 * p.dn_per_decade * dec * dec)
    n_eff = p.n + p.dn_per_decade * dec
    j0 = p.jph_ma * 1e-3 * suns / math.expm1(max(voc, 1e-6) / (n_eff * v_t))
    return n_eff, j0


def _curve(p: DiodeParams, suns: float = 1.0):
    """Return dict(voc, jsc, ff, pmax[mW/cm^2]) at a given intensity (suns)."""
    jph = p.jph_ma * suns * 1e-3
    n, j0 = _effective(p, suns)
    nvt = n * vt(p.temp_k)
    f = lambda vj: jph - j0 * math.expm1(vj / nvt) - vj / p.rsh
    hi = nvt * math.log(jph / j0 + 1.0) + 1e-6
    voc = optimize.brentq(f, 0.0, hi, xtol=1e-10)
    vj = np.linspace(0.0, voc, 4000)
    j = jph - j0 * np.expm1(vj / nvt) - vj / p.rsh
    v = vj - j * p.rs
    # Jsc: current where terminal V = 0 (vj = J*Rs)
    g = lambda x: x - p.rs * (jph - j0 * math.expm1(x / nvt) - x / p.rsh)
    vj0 = optimize.brentq(g, 0.0, voc, xtol=1e-12) if p.rs > 0 else 0.0
    jsc = jph - j0 * math.expm1(vj0 / nvt) - vj0 / p.rsh
    pw = v * j
    i = int(np.argmax(pw))
    lo, hi_ = max(i - 1, 0), min(i + 1, len(vj) - 1)
    r = optimize.minimize_scalar(
        lambda x: -(x - (jph - j0 * math.expm1(x / nvt) - x / p.rsh) * p.rs)
        * (jph - j0 * math.expm1(x / nvt) - x / p.rsh),
        bounds=(vj[lo], vj[hi_]), method="bounded", options={"xatol": 1e-9})
    pmax = -r.fun
    return {"voc_v": voc, "jsc_ma": jsc * 1e3, "ff_pct": 100 * pmax / (voc * jsc),
            "pmax_mw": pmax * 1e3}


def simulate(p: DiodeParams, suns: float = 1.0) -> dict:
    c = _curve(p, suns)
    c["eta_pct"] = 100 * c["pmax_mw"] * 1e-3 / (P_STC * suns)
    return c


def _build(voc, jsc_ma, n, rs, rsh, temp):
    """Params reproducing Voc and Jsc exactly for given (n, Rs, Rsh)."""
    nvt = n * vt(temp)
    jsc = jsc_ma * 1e-3
    jph = jsc * (1 + rs / rsh)
    for _ in range(30):
        j0 = (jph - voc / rsh) / math.expm1(voc / nvt)
        if j0 <= 0:
            return None
        vj0 = jsc * rs
        new = jsc + j0 * math.expm1(vj0 / nvt) + vj0 / rsh
        if abs(new - jph) < 1e-14:
            break
        jph = new
    return DiodeParams(jph * 1e3, j0 * 1e3, n, rs, rsh, temp)


def fit_from_metrics(voc_v: float, jsc_ma: float, ff_pct: float, n: float,
                     rs: float, temp_k: float = T_CELL) -> DiodeParams | None:
    """Find the Rsh that reproduces FF for assumed (n, Rs). None if infeasible.

    Three numbers (Voc, Jsc, FF) cannot fix four parameters; n and Rs must come
    from a J-V fit or from a prior. See project_low_light for the envelope.
    """
    def ff_at(log_rsh):
        p = _build(voc_v, jsc_ma, n, rs, 10 ** log_rsh, temp_k)
        return -1.0 if p is None else _curve(p)["ff_pct"]

    lo, hi = math.log10(voc_v / (jsc_ma * 1e-3)) + 0.05, 7.0
    f_lo, f_hi = ff_at(lo) - ff_pct, ff_at(hi) - ff_pct
    if f_hi < 0 or f_lo > 0:
        return None
    lr = optimize.brentq(lambda x: ff_at(x) - ff_pct, lo, hi, xtol=1e-6)
    return _build(voc_v, jsc_ma, n, rs, 10 ** lr, temp_k)


def lux_to_jph_ma(lux: float, eqe_visible: float = EQE_VISIBLE_DEFAULT):
    """(photocurrent mA/cm^2, incident power mW/cm^2) under a white LED."""
    p_w_cm2 = lux / LED_LER_LM_PER_W * 1e-4
    return eqe_visible * p_w_cm2 / LED_MEAN_PHOTON_EV * 1e3, p_w_cm2 * 1e3


def project(p: DiodeParams, suns=LOW_G_SUNS, lux=LUX_LEVELS,
            eqe_visible: float = EQE_VISIBLE_DEFAULT) -> dict:
    """eta(G) outdoors (same spectrum, scaled) and indoor LED efficiency."""
    base = simulate(p, 1.0)
    out = {"stc": {k: round(v, 4) for k, v in base.items()}, "outdoor": {}, "indoor": {}}
    for s in suns:
        r = simulate(p, s)
        out["outdoor"][f"{int(round(1000 * s))}W/m2"] = {
            "eta_pct": round(r["eta_pct"], 2),
            "retention": round(r["eta_pct"] / base["eta_pct"], 3),
            "voc_v": round(r["voc_v"], 3), "ff_pct": round(r["ff_pct"], 1)}
    for lx in lux:
        jph, pin = lux_to_jph_ma(lx, eqe_visible)
        suns_eq = jph / p.jph_ma
        r = _curve(p, suns_eq)
        out["indoor"][f"{lx}lux"] = {
            "eta_pct": round(100 * r["pmax_mw"] / pin, 2),
            "power_uw_cm2": round(1e3 * r["pmax_mw"], 2),
            "voc_v": round(r["voc_v"], 3), "ff_pct": round(r["ff_pct"], 1)}
    return out


N_PRIOR = tuple(np.round(np.linspace(1.2, 2.2, 11), 2))
RS_PRIOR = (0.2, 0.4, 0.6, 0.8, 1.0)


def project_low_light(voc_v: float, jsc_ma: float, ff_pct: float,
                      n: float | None = None, rs: float | None = None,
                      rsh: float | None = None, dn_per_decade: float = 0.0,
                      eqe_visible: float = EQE_VISIBLE_DEFAULT) -> dict:
    """Low-light projection with honest provenance.

    * n, rs, rsh all given  -> single projection, provenance 'fitted'.
    * otherwise             -> envelope over the class prior grid of (n, Rs)
      combinations that can reproduce the reported FF; provenance 'class-prior'.
    """
    if n is not None and rs is not None and rsh is not None:
        p = _build(voc_v, jsc_ma, n, rs, rsh, T_CELL)
        p = DiodeParams(p.jph_ma, p.j0_ma, n, rs, rsh, T_CELL, dn_per_decade)
        proj = project(p, eqe_visible=eqe_visible)
        return {"provenance": "fitted (n, Rs, Rsh supplied)", "params": p.as_dict(),
                "ff_model_pct": proj["stc"]["ff_pct"], "ff_reported_pct": ff_pct,
                "projection": proj}

    ns = (n,) if n is not None else N_PRIOR
    rss = (rs,) if rs is not None else RS_PRIOR
    rows = []
    for ni in ns:
        for ri in rss:
            p = fit_from_metrics(voc_v, jsc_ma, ff_pct, ni, ri)
            if p is None:
                continue
            p = DiodeParams(p.jph_ma, p.j0_ma, p.n, p.rs, p.rsh, p.temp_k, dn_per_decade)
            rows.append((p, project(p, eqe_visible=eqe_visible)))
    if not rows:
        return {"provenance": "infeasible: no (n, Rs) in the prior grid reproduces FF",
                "n_feasible": 0}

    def env(getter):
        v = np.array([getter(pr) for _, pr in rows])
        return {"min": round(float(v.min()), 3), "median": round(float(np.median(v)), 3),
                "max": round(float(v.max()), 3)}

    out = {"provenance": "class-prior envelope (n, Rs borrowed; Rsh solved from FF)",
           "n_feasible": len(rows),
           "n_range": [min(p.n for p, _ in rows), max(p.n for p, _ in rows)],
           "rsh_range_ohm_cm2": [round(min(p.rsh for p, _ in rows)),
                                 round(max(p.rsh for p, _ in rows))],
           "outdoor_retention": {}, "indoor_eta_pct": {}}
    for k in rows[0][1]["outdoor"]:
        out["outdoor_retention"][k] = env(lambda pr, k=k: pr["outdoor"][k]["retention"])
    for k in rows[0][1]["indoor"]:
        out["indoor_eta_pct"][k] = env(lambda pr, k=k: pr["indoor"][k]["eta_pct"])
    return out
