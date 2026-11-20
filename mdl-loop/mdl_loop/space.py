"""The P0 formation-trajectory search space for campaign C1.

Two levels, because a furnace imposes them:

* ``run`` parameters are the thermal/chalcogen trajectory. Every sample in one
  furnace run shares them.
* ``sample`` parameters are set in the ink or precursor stack, so the samples
  in one run can differ in them (alkali dose and layer position, Cu ratio).

Bounds follow P0 (implication-engine design, section 2): selenization-class
anneals capped at 560 °C, deliberate alkali dosing (no glass supply), Mo foil as
the bring-up substrate. The literature recipe is the Nature Energy 2026 flexible
Mo-foil route summarised in the next-stage plan (Li in the first precursor layer,
Na in the rest, 535 °C reached in about one minute, 20-minute hold); the values
the plan does not give (Se charge, cooling rate, Cu ratio) are marked assumed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Real:
    name: str
    lo: float
    hi: float
    log: bool = False
    level: str = "run"
    unit: str = ""

    def to_unit(self, v: float) -> float:
        if self.log:
            return (math.log(v) - math.log(self.lo)) / (math.log(self.hi) - math.log(self.lo))
        return (v - self.lo) / (self.hi - self.lo)

    def from_unit(self, u: float) -> float:
        u = min(max(u, 0.0), 1.0)
        if self.log:
            return math.exp(math.log(self.lo) + u * (math.log(self.hi) - math.log(self.lo)))
        return self.lo + u * (self.hi - self.lo)


@dataclass(frozen=True)
class Cat:
    name: str
    choices: tuple
    level: str = "sample"


class Space:
    def __init__(self, params):
        self.params = list(params)
        self.names = [p.name for p in self.params]
        self.run_names = [p.name for p in self.params if p.level == "run"]
        self.sample_names = [p.name for p in self.params if p.level == "sample"]
        self.dim = sum(len(p.choices) if isinstance(p, Cat) else 1 for p in self.params)

    def __getitem__(self, name):
        return self.params[self.names.index(name)]

    # encoding ---------------------------------------------------------
    def encode(self, x: dict) -> np.ndarray:
        out = []
        for p in self.params:
            if isinstance(p, Cat):
                out.extend(1.0 if x[p.name] == c else 0.0 for c in p.choices)
            else:
                out.append(p.to_unit(x[p.name]))
        return np.array(out)

    def encode_many(self, xs) -> np.ndarray:
        return np.array([self.encode(x) for x in xs])

    # sampling ---------------------------------------------------------
    def _draw(self, p, rng):
        if isinstance(p, Cat):
            return p.choices[rng.integers(len(p.choices))]
        return p.from_unit(rng.random())

    def sample(self, rng, n: int = 1, level: str | None = None, base: dict | None = None):
        """Random points. With ``level`` set, only that level is drawn and the
        rest is copied from ``base``."""
        out = []
        for _ in range(n):
            x = dict(base) if base else {}
            for p in self.params:
                if level is None or p.level == level:
                    x[p.name] = self._draw(p, rng)
            out.append(x)
        return out

    def lhs_runs(self, rng, n: int):
        """Latin-hypercube trajectories (run-level parameters only)."""
        reals = [p for p in self.params if p.level == "run"]
        cols = []
        for _ in reals:
            perm = rng.permutation(n)
            cols.append((perm + rng.random(n)) / n)
        return [{p.name: p.from_unit(cols[j][i]) for j, p in enumerate(reals)} for i in range(n)]

    def perturb(self, x: dict, rng, scale: float, level: str | None = None, p_flip: float = 0.15):
        y = dict(x)
        for p in self.params:
            if level is not None and p.level != level:
                continue
            if isinstance(p, Cat):
                if rng.random() < p_flip:
                    y[p.name] = p.choices[rng.integers(len(p.choices))]
            else:
                y[p.name] = p.from_unit(p.to_unit(x[p.name]) + scale * rng.standard_normal())
        return y

    def trajectory(self, x: dict) -> dict:
        return {k: x[k] for k in self.run_names}

    def recipe(self, x: dict) -> dict:
        return {k: x[k] for k in self.sample_names}


P0_SPACE = Space([
    Real("ramp_c_per_min", 10, 600, log=True, level="run", unit="°C/min"),
    Real("inter_hold_c", 300, 480, level="run", unit="°C"),
    Real("inter_hold_min", 0, 30, level="run", unit="min"),
    Real("anneal_c", 500, 560, level="run", unit="°C"),
    Real("anneal_min", 5, 40, level="run", unit="min"),
    Real("se_mg", 40, 640, log=True, level="run", unit="mg"),
    Real("cool_c_per_min", 0.5, 50, log=True, level="run", unit="°C/min"),
    Real("na_mM", 0, 160, level="sample", unit="mM"),
    Real("li_mM", 0, 200, level="sample", unit="mM"),
    Cat("li_layer", ("first", "all", "top"), level="sample"),
    Real("cu_ratio", 0.70, 0.88, level="sample", unit="Cu/(Zn+Sn)"),
])

# Literature reproduction target (stage B3). Values marked * are assumed.
LITERATURE_RECIPE = {
    "ramp_c_per_min": 500.0,      # 535 °C in about one minute
    "inter_hold_c": 400.0,        # * irrelevant while the hold time is zero
    "inter_hold_min": 0.0,
    "anneal_c": 535.0,
    "anneal_min": 20.0,
    "se_mg": 200.0,               # *
    "cool_c_per_min": 20.0,       # * uncontrolled natural cooling
    "na_mM": 80.0,
    "li_mM": 120.0,
    "li_layer": "first",
    "cu_ratio": 0.78,             # *
}
