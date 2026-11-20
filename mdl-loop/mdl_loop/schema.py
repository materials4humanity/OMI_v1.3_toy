"""Run record schema with the A4 "hidden parameters" as required fields.

Next-stage plan, item A4: cooling rate, chalcogen partial pressure, ramp profile,
alkali species, dose and layer position become *required* fields, and every run
gets a completeness score. The Uppsala survey of 395 kesterite papers is the
benchmark for why: 97% report synthesis temperature, 23% S or Se pressure, 2%
SnS/SnSe pressure, 1.5% a numerical cooling rate.

Field tiers
-----------
* ``A4``      hidden process parameters; weight 3 in the completeness score.
* ``repro``   reproducibility metadata (run order, box, operator, lot); weight 2.
* ``context`` stack and material context; weight 1.
* ``measure`` the figure-of-merit block; weight 1 (absent until measured).

A record that is complete except for A4 fields scores well below one that is
complete except for context fields, on purpose: the loop cannot learn from a
parameter nobody logged.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict, fields
from typing import Any

TIER_WEIGHT = {"A4": 3.0, "repro": 2.0, "context": 1.0, "measure": 1.0}


def _f(tier: str, unit: str = "", doc: str = "", default: Any = None):
    return field(default=default, metadata={"tier": tier, "unit": unit, "doc": doc})


@dataclass
class AlkaliDose:
    species: str                 # "Na", "Li", "K", "Rb", "Cs"
    dose: float                  # in the unit below
    unit: str                    # "mM_in_ink", "nm_NaF", "PDT_mg"
    layer_position: str          # "first", "all", "top", "PDT", "barrier"

    def ok(self) -> bool:
        return bool(self.species) and self.dose is not None and bool(self.unit) and bool(self.layer_position)


@dataclass
class RunRecord:
    # identity
    run_id: str = _f("repro", doc="unique sample id")
    furnace_run_id: str = _f("repro", doc="samples sharing one thermal trajectory share this id")
    run_order: int | None = _f("repro", doc="global sequence number; needed to separate drift from effect")
    operator: str | None = _f("repro")
    furnace_id: str | None = _f("repro")
    box_id: str | None = _f("repro", doc="graphite box identity; box history is a known confounder")
    box_position: str | None = _f("repro")
    precursor_lot: str | None = _f("repro")
    ink_age_h: float | None = _f("repro", "h")

    # context
    substrate_class: str | None = _f("context", doc="glass | Mo-foil | steel-ferritic | steel-austenitic")
    barrier: str | None = _f("context", doc="e.g. SiO2 200 nm; none")
    back_contact: str | None = _f("context")
    ink_system: str | None = _f("context", doc="e.g. DMSO/thiourea/SnCl4")
    cu_ratio: float | None = _f("context", "Cu/(Zn+Sn)")
    zn_sn_ratio: float | None = _f("context", "Zn/Sn")
    s_se_target: float | None = _f("context", "S/(S+Se)")
    buffer: str | None = _f("context", doc="ZTO | Zn(O,S) | CdS (reference only)")

    # A4: hidden parameters (the trajectory)
    ramp_c_per_min: float | None = _f("A4", "°C/min")
    ramp_profile: list | None = _f("A4", doc="[(t_min, T_c), ...] setpoints, if not a single ramp")
    inter_hold_c: float | None = _f("A4", "°C")
    inter_hold_min: float | None = _f("A4", "min")
    anneal_c: float | None = _f("A4", "°C")
    anneal_min: float | None = _f("A4", "min")
    se_source_mg: float | None = _f("A4", "mg", "Se charge in the box; proxy for Se activity")
    se_partial_pressure_pa: float | None = _f("A4", "Pa", "measured or modelled")
    sn_chalcogenide_pressure_pa: float | None = _f("A4", "Pa", "SnSe/SnS; 2% of papers report it")
    cool_c_per_min: float | None = _f("A4", "°C/min", "through the 260-200 °C order-disorder window")
    atmosphere: str | None = _f("A4", doc="e.g. Ar 1 bar static")
    alkali: list | None = _f("A4", doc="list of AlkaliDose")

    # measurement block
    qfls_ev: float | None = _f("measure", "eV")
    qfls_sigma_ev: float | None = _f("measure", "eV")
    urbach_mev: float | None = _f("measure", "meV")
    plqy: float | None = _f("measure")
    eg_ev: float | None = _f("measure", "eV")
    pl_calibration_id: str | None = _f("measure", doc="per-substrate absolute-PL calibration")
    raw_spectrum_uri: str | None = _f("measure")

    # outcome
    failed: bool = field(default=False, metadata={"tier": "outcome"})
    failure_mode: str | None = field(default=None, metadata={"tier": "outcome"})
    notes: str | None = field(default=None, metadata={"tier": "outcome"})

    # ------------------------------------------------------------------
    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, default=str)

    @classmethod
    def schema(cls) -> list[dict]:
        out = []
        for f in fields(cls):
            m = f.metadata
            out.append({"name": f.name, "tier": m.get("tier"), "unit": m.get("unit", ""),
                        "doc": m.get("doc", "")})
        return out


def _present(name: str, v) -> bool:
    if v is None:
        return False
    if name == "alkali":
        if not isinstance(v, list):
            return False
        return len(v) == 0 or all(isinstance(a, AlkaliDose) and a.ok() for a in v)
    if name == "ramp_profile":
        return isinstance(v, list) and len(v) > 0
    if isinstance(v, str):
        return v.strip() != ""
    return True


# Fields where either of two spellings satisfies the requirement.
_EITHER = [("se_source_mg", "se_partial_pressure_pa"), ("ramp_c_per_min", "ramp_profile")]


def completeness(rec: RunRecord, include_measure: bool = False) -> dict:
    """Weighted completeness in [0, 1] plus the missing-field list.

    A single ramp rate or a full ramp profile both satisfy the ramp field; a Se
    charge or a Se pressure both satisfy the chalcogen-activity field. Measurement
    fields count only when ``include_measure`` is set (a run is complete *as a
    process record* before it is measured).
    """
    skip_pairs = {b for _, b in _EITHER}
    total = got = 0.0
    missing = []
    by_tier = {}
    for f in fields(rec):
        tier = f.metadata.get("tier")
        if tier not in TIER_WEIGHT or (tier == "measure" and not include_measure):
            continue
        if f.name in skip_pairs:
            continue
        w = TIER_WEIGHT[tier]
        partner = dict(_EITHER).get(f.name)
        ok = _present(f.name, getattr(rec, f.name)) or (
            partner is not None and _present(partner, getattr(rec, partner)))
        total += w
        got += w if ok else 0.0
        t = by_tier.setdefault(tier, [0, 0])
        t[1] += 1
        t[0] += 1 if ok else 0
        if not ok:
            missing.append(f"{f.name} [{tier}]")
    return {"score": round(got / total, 3), "missing": missing,
            "by_tier": {k: f"{v[0]}/{v[1]}" for k, v in by_tier.items()}}


def typical_literature_record() -> RunRecord:
    """A process record filled at the reporting rates of the Uppsala survey.

    Only the fields that a typical paper reports are set: temperatures and times
    (97%), composition and buffer. Chalcogen pressure (23%), Sn-chalcogenide
    pressure (2%) and cooling rate (1.5%) are left empty, as are the
    reproducibility fields almost no paper carries.
    """
    return RunRecord(
        run_id="lit", furnace_run_id=None, substrate_class="glass", back_contact="Mo",
        ink_system="DMSO/thiourea", cu_ratio=0.78, zn_sn_ratio=1.15, s_se_target=0.2,
        buffer="CdS", barrier="none", ramp_c_per_min=None, anneal_c=540, anneal_min=20,
        atmosphere="Se vapour, graphite box",
        alkali=[AlkaliDose("Na", 0.0, "from glass", "substrate")])
