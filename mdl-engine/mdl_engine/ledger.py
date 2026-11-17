"""Implication Ledger entry builder (design section 6).

Deterministic fields only. The human-ratified verdict fields are emitted empty
on purpose: autonomy in extraction and physics, never in verdicts.
"""
from __future__ import annotations
import json

from . import sq, diode, decompose, compliance, thermal, transfer

# Representative operating points per application (assumptions, editable).
REP_POINT = {"VIPV": ("outdoor", "400W/m2"), "BIPV": ("outdoor", "200W/m2"),
             "interior": ("indoor", "500lux")}
APPS = ("VIPV", "BIPV", "interior")


def _dev(e):
    d = e.get("device") or {}
    return d if all(k in d for k in ("voc_v", "jsc_ma", "ff_pct")) else None


def build_entry(event: dict, events_by_id: dict | None = None, spectrum=None) -> dict:
    events_by_id = events_by_id or {}
    d = _dev(event)
    entry = {"id": event["id"], "headline": event["headline"],
             "provenance_tier": event.get("tier"), "notes": event.get("notes"),
             "missing": []}

    if d and event.get("eg_ev"):
        entry["normalized"] = sq.normalize(event["eg_ev"], d["voc_v"], d["jsc_ma"],
                                           d["ff_pct"], d.get("eta_pct"), spectrum)
    else:
        entry["missing"].append("device J-V parameters (Voc/Jsc/FF) and/or Eg")

    prev = events_by_id.get(event.get("prev_id"))
    if d and prev and _dev(prev):
        g = decompose.gain_decomposition(_dev(prev), d)
        g["versus"] = prev["id"]
        entry["gain"] = g

    ll = None
    if d:
        ll = diode.project_low_light(d["voc_v"], d["jsc_ma"], d["ff_pct"],
                                     n=d.get("n"), rs=d.get("rs"), rsh=d.get("rsh"))
        entry["low_light"] = ll
        if "class-prior" in ll["provenance"]:
            entry["missing"].append("fitted n, Rs, Rsh (J-V file or intensity-dependent Voc) "
                                    "- low-light result is a prior envelope")

    comp = compliance.check_stack(event["layers"]) if event.get("layers") else None
    if comp:
        entry["compliance"] = comp
    else:
        entry["missing"].append("layer stack for compliance arithmetic")

    m = event.get("mechanism")
    if m:
        entry["transferability"] = transfer.transferability(
            m["class"], m["route"], m["configuration"], m.get("max_process_c"),
            m.get("override"))

    apps = {}
    for app in APPS:
        a = {"gate": comp["gates"][app] if comp else {"gate": "unknown"}}
        kind, key = REP_POINT[app]
        if ll and ll.get("n_feasible", 1):
            if "projection" in ll:
                v = ll["projection"][kind][key]
                a["low_light"] = ({"point": key, "retention": v["retention"]} if kind == "outdoor"
                                  else {"point": key, "eta_pct": v["eta_pct"]})
            else:
                src = ll["outdoor_retention"] if kind == "outdoor" else ll["indoor_eta_pct"]
                a["low_light"] = {"point": key, **src[key],
                                  "unit": "retention" if kind == "outdoor" else "eta_pct"}
        a["thermal"] = thermal.thermal_multiplier(app)
        if a["gate"]["gate"] == "FAIL":
            a["deterministic_sign"] = "BLOCKED by substance gate (value = 0 until addressed)"
        elif a["gate"]["gate"] == "unknown":
            a["deterministic_sign"] = "undetermined"
        else:
            a["deterministic_sign"] = "open (gate %s); multipliers above" % a["gate"]["gate"]
        apps[app] = a
    entry["applications"] = apps

    flags = event.get("data_flags")
    # None = not yet assessed by an extraction pass (unknown is not the same as absent)
    entry["blind_spots"] = None if flags is None else [
        k for k in ("low_light", "temperature", "stability", "mechanical", "reverse_bias")
        if not flags.get(k)]
    entry["human_ratification"] = {"net_sign": None, "threat_opportunity_class": None,
                                   "actions": [], "signed_by": None}
    return entry


def _fmt_env(x):
    return f"{x['median']:.2f} ({x['min']:.2f}-{x['max']:.2f})"


def render_markdown(entry: dict) -> str:
    L = [f"### {entry['id']} - {entry['headline']}",
         f"*Provenance tier: {entry.get('provenance_tier')}*"]
    if entry.get("notes"):
        L.append(f"*Note: {entry['notes']}*")
    n = entry.get("normalized")
    if n:
        L.append(f"- **Normalized:** {n['eta_pct']}% at Eg {n['eg_ev']} eV = {n['pct_sq']}% of SQ "
                 f"({n['spectrum']}); Voc/SQ {n['voc_over_sq']}, Jsc/SQ {n['jsc_over_sq']}, "
                 f"FF/SQ {n['ff_over_sq']}; Voc deficit {n['voc_deficit_sq_mv']} mV vs SQ.")
    g = entry.get("gain")
    if g:
        L.append(f"- **Gain vs {g['versus']}:** +{g['rel_gain_pct']}% relative; shares "
                 f"Voc {g['share_voc']:+.2f} / Jsc {g['share_jsc']:+.2f} / FF {g['share_ff']:+.2f} "
                 f"-> {g['label']}.")
    ll = entry.get("low_light")
    if ll and "projection" in ll:
        o, i = ll["projection"]["outdoor"], ll["projection"]["indoor"]
        L.append(f"- **Low light ({ll['provenance']}):** retention "
                 f"{o['400W/m2']['retention']:.2f} @400, {o['200W/m2']['retention']:.2f} @200, "
                 f"{o['100W/m2']['retention']:.2f} @100 W/m2; indoor "
                 f"{i['1000lux']['eta_pct']}% @1000 lux, {i['200lux']['eta_pct']}% @200 lux.")
    elif ll and ll.get("n_feasible"):
        o, i = ll["outdoor_retention"], ll["indoor_eta_pct"]
        L.append(f"- **Low light ({ll['provenance']}), median (min-max):** retention "
                 f"{_fmt_env(o['400W/m2'])} @400, {_fmt_env(o['200W/m2'])} @200, "
                 f"{_fmt_env(o['100W/m2'])} @100 W/m2; indoor eta "
                 f"{_fmt_env(i['1000lux'])}% @1000 lux.")
    c = entry.get("compliance")
    if c:
        bits = []
        for lay in c["layers"]:
            for h in lay["restricted"]:
                bits.append(f"{lay['layer']} {h['element']} {h['wt_pct']} wt% "
                            f"({h['times_over']:g}x limit)")
        gates = ", ".join(f"{a}: {v['gate']}" for a, v in c["gates"].items())
        L.append(f"- **Compliance:** {'; '.join(bits) if bits else 'no restricted substances'}. "
                 f"Gates -> {gates}.")
    t = entry.get("transferability")
    if t:
        L.append(f"- **Transferability to {t['platform']}:** {t['band']} ({t['score']}): "
                 + "; ".join(t["reasons"]) + ".")
    L.append("- **Application signs (deterministic part):** " + "; ".join(
        f"{a}: {v['deterministic_sign']}" for a, v in entry["applications"].items()))
    if entry["blind_spots"] is None:
        L.append("- **Application-adjacent data flags:** not yet assessed.")
    elif entry["blind_spots"]:
        L.append(f"- **Not reported by source:** {', '.join(entry['blind_spots'])}.")
    if entry["missing"]:
        L.append(f"- **Missing inputs:** {'; '.join(entry['missing'])}.")
    L.append("- **Human ratification:** _pending_")
    return "\n".join(L)


def run(events: list[dict], spectrum=None) -> list[dict]:
    by_id = {e["id"]: e for e in events}
    return [build_entry(e, by_id, spectrum) for e in events]


def blind_spot_map(entries: list[dict]) -> dict:
    keys = ("low_light", "temperature", "stability", "mechanical", "reverse_bias")
    done = [e for e in entries if e["blind_spots"] is not None]
    return {"assessed": len(done), "unassessed": len(entries) - len(done),
            "absent": {k: sum(k in e["blind_spots"] for e in done) for k in keys}}


def dumps(entries) -> str:
    return json.dumps(entries, indent=2, default=float)
