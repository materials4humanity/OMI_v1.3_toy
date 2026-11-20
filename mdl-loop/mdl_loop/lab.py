"""A virtual furnace bay: runs trajectories on the emulator with M0's noise structure.

One furnace run = one shared trajectory + up to ``slots`` samples. The noise
has three parts, all of which M0 has to separate:

* a furnace-run random effect shared by every sample in the run (box history,
  thermocouple drift, Se charge geometry),
* film-to-film scatter, larger for poor films,
* measurement scatter (spot-to-spot, PL calibration).

Replicates inside one run see only the last two, so they understate the noise a
recipe comparison across runs actually faces. That is the reason M0 has to put
replicates in different runs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .emulator import VirtualKesterite
from .schema import RunRecord, AlkaliDose
from .space import P0_SPACE


@dataclass
class Obs:
    x: dict
    run: int
    qfls: float            # observed, eV; nan if the film failed
    urbach: float          # observed, meV; nan if failed
    failed: bool
    tag: str = ""          # "init", "bo", "confirm", "ovat", ...
    device: float = math.nan   # anchor-device Voc, V, if this film was made into a device
    slot: int = 0              # furnace slot index within the run


@dataclass
class Lab:
    model: VirtualKesterite
    rng: np.random.Generator
    slots: int = 4
    history: list = field(default_factory=list)
    n_runs: int = 0
    n_devices: int = 0

    def furnace_run(self, trajectory: dict, recipes: list[dict], tag: str = "") -> list[Obs]:
        if len(recipes) > self.slots:
            raise ValueError("more samples than furnace slots")
        nm = self.model.noise
        run_eff = self.rng.normal(0.0, self.model.run_sd_ev())
        out = []
        for i, r in enumerate(recipes):
            x = {**trajectory, **r}
            if self.rng.random() < self.model.p_fail(x):
                o = Obs(x, self.n_runs, math.nan, math.nan, True, tag, slot=i)
            else:
                q = (self.model.qfls(x) + run_eff
                     + self.rng.normal(0.0, self.model.film_sd_ev(x))
                     + self.rng.normal(0.0, nm.meas_mev / 1000.0))
                u = self.model.urbach(x) + self.rng.normal(0.0, nm.urbach_mev)
                o = Obs(x, self.n_runs, q, u, False, tag, slot=i)
            out.append(o)
        self.history.extend(out)
        self.n_runs += 1
        return out

    def confirm(self, x: dict, n_runs: int = 2) -> np.ndarray:
        """Replicate one recipe over ``n_runs`` furnace runs; returns the non-failed QFLS values.

        Confirmation runs are kept out of ``history`` and the run counter: they are
        the pre-registered end-of-campaign test, not part of the search budget.
        """
        saved_hist, saved_n = len(self.history), self.n_runs
        vals = []
        traj, rec = P0_SPACE.trajectory(x), P0_SPACE.recipe(x)
        for _ in range(n_runs):
            vals += [o.qfls for o in self.furnace_run(traj, [rec] * self.slots, "final") if not o.failed]
        del self.history[saved_hist:]
        self.n_runs = saved_n
        return np.array(vals)

    def make_device(self, o: Obs) -> float:
        """Finish a measured film into an anchor device (no furnace run consumed).

        The device inherits the film's own quality: its Voc is the film's observed
        QFLS minus the recipe's true device-only loss, plus device-fabrication
        scatter averaged over the film's cells. So the measured gap (QFLS - Voc) is
        the device-only loss plus noise.
        """
        if o.failed:
            raise ValueError("cannot make a device from a failed film")
        nm = self.model.noise
        gap = self.model.qfls(o.x) - self.model.device_voc(o.x)
        sd = nm.device_mev / math.sqrt(max(1, nm.cells_per_device)) / 1000.0
        o.device = o.qfls - gap + self.rng.normal(0.0, sd)
        self.n_devices += 1
        return o.device

    def confirm_device(self, x: dict, n_runs: int = 2) -> np.ndarray:
        """Confirmation runs whose surviving films are all finished into devices."""
        saved_hist, saved_n, saved_d = len(self.history), self.n_runs, self.n_devices
        vals = []
        traj, rec = P0_SPACE.trajectory(x), P0_SPACE.recipe(x)
        for _ in range(n_runs):
            for o in self.furnace_run(traj, [rec] * self.slots, "final"):
                if not o.failed:
                    vals.append(self.make_device(o))
        del self.history[saved_hist:]
        self.n_runs, self.n_devices = saved_n, saved_d
        return np.array(vals)

    def device(self, x: dict) -> float:
        return self.model.device_voc(x) + self.rng.normal(0.0, self.model.noise.device_mev / 1000.0)


def to_record(o: Obs, campaign: str = "C1-sim") -> RunRecord:
    """Map a simulated observation to a schema record (every A4 field filled)."""
    x = o.x
    alk = [AlkaliDose("Na", x["na_mM"], "mM_in_ink", "all")]
    if x["li_mM"] > 0:
        alk.append(AlkaliDose("Li", x["li_mM"], "mM_in_ink", x["li_layer"]))
    return RunRecord(
        run_id=f"{campaign}-{o.run}-{o.slot}", furnace_run_id=f"{campaign}-{o.run}",
        run_order=o.run, operator="loop", furnace_id="F1", box_id="B1", box_position="?",
        precursor_lot="sim", ink_age_h=0.0, substrate_class="Mo-foil", barrier="none",
        back_contact="Mo", ink_system="DMSO/thiourea", cu_ratio=x["cu_ratio"], zn_sn_ratio=1.15,
        s_se_target=0.0, buffer="ZTO",
        ramp_c_per_min=x["ramp_c_per_min"], inter_hold_c=x["inter_hold_c"],
        inter_hold_min=x["inter_hold_min"], anneal_c=x["anneal_c"], anneal_min=x["anneal_min"],
        se_source_mg=x["se_mg"], sn_chalcogenide_pressure_pa=None,
        cool_c_per_min=x["cool_c_per_min"], atmosphere="Ar, graphite box", alkali=alk,
        qfls_ev=None if o.failed else o.qfls, urbach_mev=None if o.failed else o.urbach,
        failed=o.failed, failure_mode="sim-failure" if o.failed else None)
