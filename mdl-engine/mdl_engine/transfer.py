"""Transferability operator (design 5.5): mechanism class x platform deltas.

Scores are expected gain retention on platform P0, as coarse bands. Every
default is overridable; the point is to force the reasons into writing.
"""
from __future__ import annotations

P0 = {
    "version": "P0",
    "route": {"solution-molecular-ink": 1.0, "hydrothermal": 0.8, "nanoparticle": 0.7,
              "vacuum": 0.3},
    "configuration": {"substrate": 1.0, "superstrate": 0.4},
    "max_process_c": 560,
}

MECHANISM_BASE = {
    "bulk growth-kinetics": (0.8, "transfers high; thermal profile needs re-optimization on steel"),
    "doping/ordering": (0.8, "transfers high; dose/anneal re-optimization expected"),
    "alkali": (0.85, "conditionally better: P0 doses alkali deliberately (no glass supply)"),
    "interface/buffer": (0.6, "stack-dependent; re-check against the Cd-free buffer"),
    "contact/optics": (0.3, "transfers low; front stack differs"),
    "architecture-specific": (0.2, "transfers low; tied to the source architecture"),
    "substrate-specific": (0.0, "does not transfer"),
}

BANDS = ((0.7, "HIGH"), (0.4, "MEDIUM"), (0.15, "LOW"), (-1, "NONE"))


def transferability(mechanism_class: str, route: str, configuration: str,
                    max_process_c: float | None = None, override: dict | None = None) -> dict:
    base, why = MECHANISM_BASE[mechanism_class]
    reasons = [f"mechanism '{mechanism_class}': {why} (base {base})"]
    score = base
    r = P0["route"].get(route, 0.5)
    c = P0["configuration"].get(configuration, 0.5)
    # Bulk mechanisms survive an architecture change better than interface/optical ones.
    arch_sensitive = mechanism_class in ("interface/buffer", "contact/optics",
                                         "architecture-specific")
    if r < 1:
        score *= r
        reasons.append(f"route '{route}' is off-primary (x{r})")
    if c < 1:
        pen = c if arch_sensitive else (1 + c) / 2
        score *= pen
        reasons.append(f"'{configuration}' configuration translation penalty (x{pen:.2f})")
    if max_process_c and max_process_c > P0["max_process_c"]:
        score *= 0.6
        reasons.append(f"process {max_process_c} C exceeds P0 budget {P0['max_process_c']} C (x0.6)")
    if override:
        score = override["score"]
        reasons.append(f"OVERRIDE: {override['reason']}")
    band = next(b for t, b in BANDS if score >= t)
    return {"score": round(score, 2), "band": band, "reasons": reasons, "platform": P0["version"]}
