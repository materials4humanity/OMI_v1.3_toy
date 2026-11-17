"""Compliance operator (design 5.4): homogeneous-material arithmetic.

Limits are weight fraction per homogeneous material. Enforcement doctrine treats
a distinct layer as its own homogeneous material, so each layer is tested alone.
Regulatory scope encoded here is a model of the project's Appendix B reading,
not legal advice; re-verify exemption dockets each cycle.
"""
from __future__ import annotations
import re

ATOMIC_MASS = {
    "H": 1.008, "Li": 6.94, "C": 12.011, "N": 14.007, "O": 15.999, "Na": 22.990,
    "Mg": 24.305, "Al": 26.982, "Si": 28.085, "S": 32.06, "Cl": 35.45, "K": 39.098,
    "Ti": 47.867, "Cr": 51.996, "Fe": 55.845, "Ni": 58.693, "Cu": 63.546,
    "Zn": 65.38, "Ga": 69.723, "Ge": 72.630, "Se": 78.971, "Br": 79.904,
    "Rb": 85.468, "Zr": 91.224, "Mo": 95.95, "Ag": 107.868, "Cd": 112.414,
    "In": 114.818, "Sn": 118.710, "Sb": 121.760, "Te": 127.60, "I": 126.904,
    "Cs": 132.905, "Ba": 137.327, "Hg": 200.592, "Pb": 207.2, "Bi": 208.980,
}

# wt% limits per homogeneous material
LIMITS_WT_PCT = {"Cd": 0.01, "Pb": 0.1, "Hg": 0.1}

# Which substance rules bind per application (project Appendix B reading).
SCOPE = {
    "VIPV": {"regime": "EU ELV (vehicles)", "applies": True},
    "BIPV": {"regime": "RoHS, professional fixed-installation PV exclusion",
             "applies": False},
    "interior": {"regime": "RoHS (consumer product, no shelter)", "applies": True},
}

_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)|(\()|(\))(\d*\.?\d*)")


def parse_formula(formula: str) -> dict:
    """Parse e.g. 'Cu2Zn0.7Cd0.3SnS4' or 'CH3NH3PbI3' or 'Cu2ZnSn(S0.3Se0.7)4'."""
    stack = [{}]
    pos = 0
    for m in _TOKEN.finditer(formula):
        if m.start() != pos:
            raise ValueError(f"cannot parse formula at {formula[pos:]!r}")
        pos = m.end()
        el, num, op, cl, mult = m.groups()
        if el:
            if el not in ATOMIC_MASS:
                raise ValueError(f"unknown element {el}")
            stack[-1][el] = stack[-1].get(el, 0.0) + (float(num) if num else 1.0)
        elif op:
            stack.append({})
        elif cl:
            grp = stack.pop()
            k = float(mult) if mult else 1.0
            for e, c in grp.items():
                stack[-1][e] = stack[-1].get(e, 0.0) + c * k
    if pos != len(formula) or len(stack) != 1:
        raise ValueError(f"cannot parse formula {formula!r}")
    return stack[0]


def weight_fractions(formula: str) -> dict:
    comp = parse_formula(formula)
    total = sum(ATOMIC_MASS[e] * c for e, c in comp.items())
    return {e: 100 * ATOMIC_MASS[e] * c / total for e, c in comp.items()}


def check_layer(name: str, formula: str) -> dict:
    wf = weight_fractions(formula)
    hits = []
    for el, lim in LIMITS_WT_PCT.items():
        if el in wf and wf[el] > 0:
            hits.append({"element": el, "wt_pct": round(wf[el], 2), "limit_wt_pct": lim,
                         "times_over": round(wf[el] / lim, 1), "pass": wf[el] <= lim})
    return {"layer": name, "formula": formula, "restricted": hits,
            "pass": all(h["pass"] for h in hits)}


def check_stack(layers: list[dict]) -> dict:
    """layers: [{'name':..., 'formula':...}]. Returns per-layer and per-application gates."""
    res = [check_layer(l["name"], l["formula"]) for l in layers]
    material_pass = all(r["pass"] for r in res)
    gates = {}
    for app, sc in SCOPE.items():
        if not sc["applies"]:
            gates[app] = {"gate": "moot", "regime": sc["regime"]}
        else:
            gates[app] = {"gate": "pass" if material_pass else "FAIL", "regime": sc["regime"]}
    worst = max((h["times_over"] for r in res for h in r["restricted"]), default=0.0)
    return {"layers": res, "material_pass": material_pass,
            "worst_times_over": worst, "gates": gates}
