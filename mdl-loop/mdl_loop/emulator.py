"""Virtual kesterite v0: a synthetic test surface for the C1 loop.

THIS IS NOT A PREDICTIVE MODEL OF KESTERITE. It is a benchmark surface in the
Olympus sense: smooth, literature-motivated structure with a known optimum, so
an optimizer and a campaign design can be tested before any selenization run is
spent. Every coefficient below is a modelling choice, chosen so that

* the literature recipe sits a few tens of mV of QFLS below the surface optimum
  (``headroom_mev()`` computes the value; it is not quoted here so it cannot go stale),
* the headroom is spread over several mechanisms rather than one knob, and
* some of it is reachable only by moving several parameters together.

Conclusions drawn from it are conditional on that structure. ``interaction=0``
gives a separable variant of the same surface, so any loop-versus-OVAT result
can be checked for how much it depends on the interactions.

Mechanism terms (losses in mV of QFLS)
--------------------------------------
floor     radiative plus intrinsic Cu-Zn antisite floor (v2 map, section 3a). Constant.
grain     grain growth needs temperature x time; Li in the first layer helps.
sn        Sn loss at high temperature and long holds, suppressed by Se activity.
phase     phase-evolution balance (section 3b): an index built from the
          intermediate hold, the ramp rate, Na dose and Se activity must sit on
          a target. Na and Se enter the index only through ``interaction``.
tail      Cu-Zn disorder sets the Urbach energy; time spent in the 260-200 °C
          window (cooling rate) orders the lattice; first-layer Li speeds it.
slowcool  very slow cooling costs a little (re-evaporation, surface change).
alkali    Na benefit saturates; excess Na costs; Li on top segregates.
cu        stoichiometry penalty around Cu/(Zn+Sn) = 0.79.

Device-only terms (seen by anchor devices, invisible to QFLS)
-------------------------------------------------------------
interface  buffer/absorber loss for the ZTO stack (constant).
mose2      excess Se thickens MoSe2 on the back contact.
li_top     surface Li degrades the front interface.

Failure probability rises with fast ramps under high Se charge (blistering),
Cu-rich films (Cu2-xSe), and hot, long anneals.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .space import P0_SPACE, LITERATURE_RECIPE

VOC_SQ_EV = 0.86      # detailed-balance Voc near Eg = 1.10 eV, AM1.5G (approximate)
FLOOR_MV = 200.0
LI_POS = {"first": 1.0, "all": 0.6, "top": 0.2}
_OPT_CACHE: dict = {}


def _sig(z):
    return 1.0 / (1.0 + math.exp(-z))


@dataclass
class NoiseModel:
    """M0's unknowns. ``film_mev`` is the film-to-film spread that M0 measures."""
    film_mev: float = 10.0
    run_frac: float = 0.5          # furnace-run random effect, as a fraction of film_mev
    run_mev: float | None = None   # absolute furnace-run sd; overrides run_frac when set
    meas_mev: float = 3.0          # spot-to-spot plus calibration
    hetero: float = 1.0            # poor films are noisier: sd x (1 + hetero * loss/80 mV)
    urbach_mev: float = 0.6
    device_mev: float = 8.0        # cell-to-cell Voc scatter within one finished film
    cells_per_device: int = 6      # an anchor film is scribed into this many cells and averaged


class VirtualKesterite:
    def __init__(self, interaction: float = 1.0, noise: NoiseModel | None = None):
        self.k = float(interaction)
        self.noise = noise or NoiseModel()
        self._opt = None

    # ---------------------------------------------------------------- terms
    def terms(self, x: dict) -> dict:
        k = self.k
        T, t = x["anneal_c"], x["anneal_min"]
        sp = P0_SPACE["se_mg"]
        s = sp.to_unit(x["se_mg"])                       # Se activity, 0..1
        li = x["li_mM"]
        li_f = (li / (li + 60.0)) * LI_POS[x["li_layer"]]
        na = x["na_mM"]

        grain = 90.0 * math.exp(-(T - 500.0) / 15.0) * math.sqrt(10.0 / (10.0 + t))
        grain *= 1.0 - 0.5 * li_f

        sn = 110.0 * _sig((T - 545.0) / 7.0 + 0.04 * (t - 20.0)) * (1.0 - s) ** 1.5
        starve = 40.0 * math.exp(-6.0 * s) * math.sqrt(10.0 / (5.0 + t))

        w_hold = math.exp(-((x["inter_hold_c"] - 420.0) / 40.0) ** 2 / 2.0)
        lam = (0.3 * math.log1p(x["inter_hold_min"]) * w_hold
               - 0.25 * math.log10(x["ramp_c_per_min"] / 50.0)
               + k * 0.8 * na / (na + 60.0)
               + k * 0.6 * (s - 0.5)
               + (1 - k) * 0.48)                         # keeps the separable optimum in range
        phase = 45.0 * (1.0 - math.exp(-((lam - 0.75) ** 2) / (2 * 0.55 ** 2)))

        tau = (60.0 / x["cool_c_per_min"]) * (1.0 + k * 1.5 * li_f)
        disorder = 1.0 / (1.0 + (tau / 8.0) ** 1.2)
        urbach = 13.0 + 10.0 * disorder
        tail = 2.5 * (urbach - 13.0)
        slowcool = 6.0 * max(0.0, math.log10(2.0 / x["cool_c_per_min"]))

        alkali = 30.0 * (1.0 - na / (na + 25.0)) + 0.15 * max(0.0, na - 120.0)
        if x["li_layer"] == "top":
            alkali += 8.0 * li / (li + 60.0)
        cu = 2500.0 * (x["cu_ratio"] - 0.79) ** 2

        return {"floor": FLOOR_MV, "grain": grain, "sn": sn, "starve": starve, "phase": phase, "tail": tail,
                "slowcool": slowcool, "alkali": alkali, "cu": cu,
                "_urbach_mev": urbach, "_lambda": lam, "_se_activity": s, "_li_f": li_f}

    def qfls(self, x: dict) -> float:
        """Noise-free QFLS in eV."""
        t = self.terms(x)
        loss = sum(v for k_, v in t.items() if not k_.startswith("_"))
        return VOC_SQ_EV - loss / 1000.0

    def urbach(self, x: dict) -> float:
        return self.terms(x)["_urbach_mev"]

    def p_fail(self, x: dict) -> float:
        s = P0_SPACE["se_mg"].to_unit(x["se_mg"])
        z = (-4.0
             + 5.0 * max(0.0, math.log10(x["ramp_c_per_min"] / 150.0)) * s
             + 60.0 * max(0.0, x["cu_ratio"] - 0.84)
             + 2.0 * max(0.0, (x["anneal_c"] - 550.0) / 10.0) * (x["anneal_min"] / 40.0))
        return _sig(z)

    def device_voc(self, x: dict) -> float:
        """Noise-free anchor-device Voc in V (ZTO buffer)."""
        t = self.terms(x)
        interface = 25.0
        mose2 = 20.0 * max(0.0, t["_se_activity"] - 0.7) / 0.3
        li_top = 15.0 * (x["li_mM"] / (x["li_mM"] + 60.0)) if x["li_layer"] == "top" else 0.0
        return self.qfls(x) - (interface + mose2 + li_top) / 1000.0

    # ---------------------------------------------------------------- optimum
    def optimum(self) -> tuple[dict, float]:
        """Global optimum of the noise-free QFLS (cached)."""
        if self._opt is None and self.k in _OPT_CACHE:
            self._opt = _OPT_CACHE[self.k]
        if self._opt is None:
            from scipy.optimize import differential_evolution
            reals = [p for p in P0_SPACE.params if not hasattr(p, "choices")]
            best = (None, -1.0)
            for layer in ("first", "all", "top"):
                def neg(u):
                    x = {p.name: p.from_unit(ui) for p, ui in zip(reals, u)}
                    x["li_layer"] = layer
                    return -self.qfls(x)
                r = differential_evolution(neg, [(0, 1)] * len(reals), seed=0, tol=1e-10,
                                           maxiter=400, polish=True)
                if -r.fun > best[1]:
                    x = {p.name: p.from_unit(ui) for p, ui in zip(reals, r.x)}
                    x["li_layer"] = layer
                    best = (x, -r.fun)
            self._opt = best
            _OPT_CACHE[self.k] = best
        return self._opt

    def headroom_mev(self) -> float:
        return 1000.0 * (self.optimum()[1] - self.qfls(LITERATURE_RECIPE))

    # ---------------------------------------------------------------- noise
    def run_sd_ev(self) -> float:
        nm = self.noise
        return (nm.run_mev if nm.run_mev is not None else nm.run_frac * nm.film_mev) / 1000.0

    def nominal_from_measured(self, film_at_lit_mev: float) -> float:
        """Nominal film_mev that gives ``film_at_lit_mev`` of film scatter at the literature recipe.

        M0 measures noise on the literature recipe; the noise model's ``film_mev`` is
        the scatter of an optimal film. With hetero > 0 the two differ.
        """
        loss = self.headroom_mev()
        return film_at_lit_mev / (1.0 + self.noise.hetero * loss / 80.0)

    def film_sd_ev(self, x: dict) -> float:
        nm = self.noise
        loss = max(0.0, self.optimum()[1] - self.qfls(x)) * 1000.0
        return nm.film_mev * (1.0 + nm.hetero * loss / 80.0) / 1000.0
