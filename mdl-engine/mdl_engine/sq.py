"""Detailed-balance (Shockley-Queisser) limit and %SQ normalization (design 5.1).

Two spectra are supported:
  * "blackbody": a 5772 K blackbody diluted to 1000 W/m^2. Needs no data file.
    It under-reads the AM1.5G limit by roughly 1.5-2.5 absolute points near
    1.1-1.4 eV, so %SQ computed with it is biased HIGH by ~5-8% relative.
    Voc_SQ is almost unaffected (a few mV).
  * a tabulated spectrum (e.g. ASTM G173 AM1.5G) loaded with load_spectrum().
    Use this for anything public. The file is not bundled.

Every result carries `spectrum` so the provenance is on the face of the number.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from functools import lru_cache

import numpy as np
from scipy import integrate, optimize

from .constants import Q, KB, H, C, T_CELL, T_SUN, P_STC, vt

_PREF = 2.0 * math.pi / (H**3 * C**2)  # photons / (m^2 s J^3) into a hemisphere


@dataclass(frozen=True)
class Spectrum:
    name: str
    energy_ev: tuple          # ascending photon energies, eV
    flux: tuple               # photons / (cm^2 s eV)

    def photons_above(self, eg: float) -> float:
        e = np.asarray(self.energy_ev)
        f = np.asarray(self.flux)
        m = e >= eg
        if m.sum() < 2:
            return 0.0
        e0 = np.concatenate([[eg], e[m]])
        f0 = np.concatenate([[np.interp(eg, e, f)], f[m]])
        return float(np.trapezoid(f0, e0))


def load_spectrum(path: str, name: str = "AM1.5G (ASTM G173)", wl_col: int = 0,
                  irr_col: int = 2, skiprows: int = 2, delimiter: str = ",") -> Spectrum:
    """Load a wavelength(nm) / spectral irradiance (W m^-2 nm^-1) table.

    Defaults match NREL's astmg173.csv (col 2 = global tilt).
    """
    d = np.genfromtxt(path, delimiter=delimiter, skip_header=skiprows)
    wl = d[:, wl_col] * 1e-9
    irr = d[:, irr_col] * 1e9            # W m^-2 m^-1
    e_j = H * C / wl
    # photon flux per unit energy: phi(E) = irr(lambda) * lambda^2/(h c) / E
    flux_j = irr * wl**2 / (H * C) / e_j   # photons m^-2 s^-1 J^-1
    e_ev = e_j / Q
    order = np.argsort(e_ev)
    flux_ev = flux_j[order] * Q * 1e-4     # photons cm^-2 s^-1 eV^-1
    return Spectrum(name, tuple(e_ev[order]), tuple(flux_ev))


def _bb_photons_above(eg_ev: float, temp: float) -> float:
    """Blackbody hemispherical photon flux above eg, photons m^-2 s^-1."""
    kt = KB * temp
    x0 = eg_ev * Q / kt
    val, _ = integrate.quad(lambda x: x * x / math.expm1(x), x0, max(x0 + 60, 80))
    return _PREF * kt**3 * val


def _bb_power(temp: float) -> float:
    kt = KB * temp
    val, _ = integrate.quad(lambda x: x**3 / math.expm1(x), 1e-9, 80)
    return _PREF * kt**4 * val            # W m^-2


@lru_cache(maxsize=None)
def _bb_dilution() -> float:
    return (P_STC * 1e4) / _bb_power(T_SUN)


@dataclass(frozen=True)
class SQResult:
    eg_ev: float
    jsc_ma: float
    voc_v: float
    ff: float
    eta_pct: float
    spectrum: str

    def as_dict(self):
        return asdict(self)


def j0_rad(eg_ev: float, temp: float = T_CELL) -> float:
    """Radiative saturation current, A/cm^2 (front-hemisphere emission only)."""
    return Q * _bb_photons_above(eg_ev, temp) * 1e-4


def _ideal_mpp(jsc: float, j0: float, temp: float):
    v_t = vt(temp)
    voc = v_t * math.log(jsc / j0 + 1.0)
    p = lambda v: -v * (jsc - j0 * math.expm1(v / v_t))
    r = optimize.minimize_scalar(p, bounds=(0.0, voc), method="bounded",
                                 options={"xatol": 1e-7})
    return voc, -r.fun


@lru_cache(maxsize=4096)
def _sq_bb(eg_ev: float, temp: float) -> SQResult:
    jsc = Q * _bb_dilution() * _bb_photons_above(eg_ev, T_SUN) * 1e-4
    voc, pmax = _ideal_mpp(jsc, j0_rad(eg_ev, temp), temp)
    return SQResult(float(eg_ev), float(jsc * 1e3), float(voc), float(pmax / (voc * jsc)), float(100 * pmax / P_STC),
                    "blackbody-5772K (approx; %SQ reads high)")


def sq_limit(eg_ev: float, spectrum: Spectrum | None = None,
             temp: float = T_CELL) -> SQResult:
    if spectrum is None:
        return _sq_bb(round(float(eg_ev), 6), temp)
    jsc = Q * spectrum.photons_above(eg_ev)
    voc, pmax = _ideal_mpp(jsc, j0_rad(eg_ev, temp), temp)
    return SQResult(float(eg_ev), float(jsc * 1e3), float(voc), float(pmax / (voc * jsc)), float(100 * pmax / P_STC),
                    spectrum.name)


def normalize(eg_ev: float, voc_v: float, jsc_ma: float, ff_pct: float,
              eta_pct: float | None = None, spectrum: Spectrum | None = None) -> dict:
    """%SQ coordinates of a device (design 5.1). FF in percent."""
    s = sq_limit(eg_ev, spectrum)
    eta = eta_pct if eta_pct is not None else voc_v * jsc_ma * ff_pct / 100.0
    frac = eta / s.eta_pct
    return {
        "eg_ev": eg_ev,
        "eta_pct": round(eta, 3),
        "sq_eta_pct": round(s.eta_pct, 2),
        "pct_sq": round(float(100 * frac), 1),
        "logit_sq": round(math.log(frac / (1 - frac)), 3),
        "voc_over_sq": round(voc_v / s.voc_v, 3),
        "jsc_over_sq": round(jsc_ma / s.jsc_ma, 3),
        "ff_over_sq": round(ff_pct / 100.0 / s.ff, 3),
        "voc_deficit_sq_mv": round(1e3 * (s.voc_v - voc_v), 1),
        "voc_deficit_eg_mv": round(1e3 * (eg_ev - voc_v), 1),
        "spectrum": s.spectrum,
    }
