"""The discovery domain's readouts (Core §3.5; ADR-064), matching the three entries the
domain's `readout_catalogue` declares.

`TurnoverFrequency` is the one the observation suite resolves and the one a campaign
optimises. It evaluates the declared `LANGMUIR_HINSHELWOOD` form rather than restating its
arithmetic, so the readout and the declared form cannot drift apart — and so a validity
report computed against that form is a statement about this readout and not about a
lookalike.

**The evaluation condition is a field of the readout, not a state component.** Core §2.6's
property/performance distinction is what licenses that: a property is a functional of the
constitutive operator alone within a *declared test class*, so the test class belongs to the
readout's declaration. A turnover frequency quoted without its partial pressure is not a
property, it is a number.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import FloatArray, Slot, State

from omi_domains.sdl.forms import langmuir_hinshelwood


@dataclass(frozen=True)
class TurnoverFrequency(FunctionalReadout):
    """Core §3.5 Type-0; Core §2.6 Class A (self-averaging — a reactor test averages over
    an enormous number of sites, so a representative volume exists by construction).

    The declared `LANGMUIR_HINSHELWOOD` form, evaluated at this readout's declared partial
    pressure and modulated by pore-network accessibility: a site that cannot be reached does
    not turn over, which is Core §3.1's reason for carrying `ν` at all.
    """

    readout_class: ReadoutClass = field(default=ReadoutClass.A)
    partial_pressure: float = 1.0
    """The declared test condition. Inside `LH_PARTIAL_PRESSURE_WINDOW` by default; a caller
    may move it outside, and the declared form's validity report is what says so."""

    def evaluate(self, state: State) -> FloatArray:
        sites = state.get(Slot.Z, "active_site_density")[0]
        accessibility = state.get(Slot.NU, "pore_network_accessibility")[0]
        rate = langmuir_hinshelwood(
            {"partial_pressure": self.partial_pressure, "active_site_density": sites}
        )
        return np.asarray(rate * max(accessibility, 0.0), dtype=np.float64)

    def jacobian(self, state: State) -> FloatArray:
        """Exact analytic Jacobian (ADR-001): the form is linear in `active_site_density`
        and this readout is linear in accessibility, so both partials are closed-form and
        no finite-difference estimate is needed."""
        sites = state.get(Slot.Z, "active_site_density")[0]
        accessibility = max(state.get(Slot.NU, "pore_network_accessibility")[0], 0.0)
        per_site = float(
            langmuir_hinshelwood({"partial_pressure": self.partial_pressure, "active_site_density": 1.0})[0]
        )
        jac = np.zeros((1, state.schema.size))
        jac[0, state.schema.slice_for(Slot.Z, "active_site_density")] = per_site * accessibility
        if accessibility > 0.0:
            jac[0, state.schema.slice_for(Slot.NU, "pore_network_accessibility")] = per_site * sites
        return jac


@dataclass(frozen=True)
class Selectivity(FunctionalReadout):
    """Core §3.5 Type-0; Class A. Defect sites and a reconstructed surface both open the
    side pathway, so selectivity falls with either."""

    readout_class: ReadoutClass = field(default=ReadoutClass.A)
    defect_penalty: float = 3.0
    reconstruction_penalty: float = 1.5

    def evaluate(self, state: State) -> FloatArray:
        defects = state.get(Slot.Z, "defect_site_fraction")[0]
        reconstruction = state.get(Slot.GAMMA, "surface_reconstruction_index")[0]
        side = self.defect_penalty * defects + self.reconstruction_penalty * reconstruction
        return np.array([1.0 / (1.0 + max(side, 0.0))])

    def jacobian(self, state: State) -> FloatArray:
        """Exact analytic Jacobian (ADR-001) of the rational form above."""
        defects = state.get(Slot.Z, "defect_site_fraction")[0]
        reconstruction = state.get(Slot.GAMMA, "surface_reconstruction_index")[0]
        side = self.defect_penalty * defects + self.reconstruction_penalty * reconstruction
        jac = np.zeros((1, state.schema.size))
        if side > 0.0:
            scale = -1.0 / (1.0 + side) ** 2
            jac[0, state.schema.slice_for(Slot.Z, "defect_site_fraction")] = scale * self.defect_penalty
            jac[0, state.schema.slice_for(Slot.GAMMA, "surface_reconstruction_index")] = (
                scale * self.reconstruction_penalty
            )
        return jac


@dataclass(frozen=True)
class DeactivationOnset(FunctionalReadout):
    """Core §3.6 Class B: a weakest-link hazard, because a supported catalyst deactivates
    where its *worst* region does — one runaway sintering hot spot ends the batch, and no
    representative volume exists for that (Core §2.6's Class B criterion).

    Returned as a hazard so the Class-B machinery's driver/tail separation has a scalar
    driver, and clamped at zero because a negative hazard is not physical — the same
    convention `omi_domains.contrast.readouts.DendriteRisk` states.
    """

    readout_class: ReadoutClass = field(default=ReadoutClass.B)
    size_gain: float = 0.08
    accessibility_protection: float = 0.6

    def evaluate(self, state: State) -> FloatArray:
        size = state.get(Slot.M, "mean_particle_size")[0]
        accessibility = state.get(Slot.NU, "pore_network_accessibility")[0]
        hazard = self.size_gain * size - self.accessibility_protection * accessibility
        return np.array([max(hazard, 0.0)])

    def jacobian(self, state: State) -> FloatArray:
        """Exact analytic Jacobian (ADR-001): piecewise-linear, so the derivative is the
        affine part where the pre-clamp value is positive and zero where the clamp bites."""
        size = state.get(Slot.M, "mean_particle_size")[0]
        accessibility = state.get(Slot.NU, "pore_network_accessibility")[0]
        pre_clamp = self.size_gain * size - self.accessibility_protection * accessibility
        jac = np.zeros((1, state.schema.size))
        if pre_clamp > 0.0:
            jac[0, state.schema.slice_for(Slot.M, "mean_particle_size")] = self.size_gain
            jac[0, state.schema.slice_for(Slot.NU, "pore_network_accessibility")] = (
                -self.accessibility_protection
            )
        return jac
