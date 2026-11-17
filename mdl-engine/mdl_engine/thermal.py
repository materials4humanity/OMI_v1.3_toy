"""Thermal projection (design 5.3). Ships with a borrowed prior and says so."""
from __future__ import annotations

# CIGS-derived relative temperature coefficient of efficiency, %/C.
TC_PRIOR = {"low": -0.40, "mid": -0.35, "high": -0.30,
            "provenance": "CIGS-derived class prior; NO measured TC exists for "
                          "14-15% kesterite (standing red flag, design 5.3)"}

# Representative operating cell temperatures (C). Assumptions, editable.
OPERATING_T = {"VIPV": 70.0, "BIPV": 60.0, "interior": 25.0}


def thermal_multiplier(app: str, tc: dict | None = None) -> dict:
    tc = tc or TC_PRIOR
    t = OPERATING_T[app]
    f = lambda c: round(1 + c / 100.0 * (t - 25.0), 3)
    return {"t_cell_c": t, "multiplier": {"low": f(tc["low"]), "mid": f(tc["mid"]),
                                           "high": f(tc["high"])},
            "provenance": tc.get("provenance", "supplied"),
            "cold_side": "unmodelled: -40..0 C freeze-out behaviour unknown" if app == "VIPV" else None}
