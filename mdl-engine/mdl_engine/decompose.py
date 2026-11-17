"""Gain decomposition (design 5.2): which J-V parameter carried a record's gain.

Since eta = Voc*Jsc*FF, ln(eta2/eta1) splits exactly into three log terms.
"""
from __future__ import annotations
import math


def gain_decomposition(prev: dict, new: dict) -> dict:
    """prev/new: dicts with voc_v, jsc_ma, ff_pct. Returns shares summing to 1."""
    d = {k: math.log(new[k] / prev[k]) for k in ("voc_v", "jsc_ma", "ff_pct")}
    total = sum(d.values())
    eta1 = prev["voc_v"] * prev["jsc_ma"] * prev["ff_pct"] / 100
    eta2 = new["voc_v"] * new["jsc_ma"] * new["ff_pct"] / 100
    if abs(total) < 1e-9:
        shares = {k: 0.0 for k in d}
    else:
        shares = {k: v / total for k, v in d.items()}
    diode = shares["voc_v"] + shares["ff_pct"]
    if total <= 0:
        label = "no-gain"
    elif diode >= 0.67:
        label = "diode-quality-led (Voc/FF)"
    elif shares["jsc_ma"] >= 0.67:
        label = "current-led (Jsc/optics)"
    else:
        label = "mixed"
    return {
        "eta_prev_pct": round(eta1, 2), "eta_new_pct": round(eta2, 2),
        "rel_gain_pct": round(100 * (math.exp(total) - 1), 1),
        "share_voc": round(shares["voc_v"], 2),
        "share_jsc": round(shares["jsc_ma"], 2),
        "share_ff": round(shares["ff_pct"], 2),
        "label": label,
    }
