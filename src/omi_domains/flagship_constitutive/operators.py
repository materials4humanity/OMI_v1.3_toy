"""Evolution operators driven by the declared constitutive forms (M11.3; ADR-044).

Cites Core §3.3 (evolution operators) and Core §3.9 (the erasure this chain still
declares). Unlike `omi_domains.flagship`'s diagonal relaxation, every component
here that changes does so because a **declared form** (`forms.py`) says how.

**What this repairs, and why the original stays broken.** Phase 1 measured that
three flagship components — `prior_grain_size`, `inclusion_content` and
`accumulated_hardening` — carry `rate == 0.0` under *both* flagship operators, so
no declared operator transports them (the measurement behind
`docs/V1.4-EDITS.md` E-29). Two of the three acquire real kinetics here:
`prior_grain_size` grows by the declared parabolic law, and
`accumulated_hardening` accumulates through the transformation forms.
`inclusion_content` stays static **deliberately** — inclusions really are inert
second-phase particles over this chain, so it is a genuine parameter rather than an
un-transported state component, and E-29's proposed parameter category is where it
belongs. Declaring kinetics for it to make the audit look better would be inventing
physics.

`omi_domains.flagship` itself is untouched: it is the audit baseline and E-29's
recorded evidence, and repairing it would delete the only instance in this
repository of a domain satisfying all seven interface items while being physically
inert (ADR-044).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.proposed.constitutive import ChainExtrapolationReport, worst_extrapolation
from omi.state import Slot, State

from omi_domains.flagship_constitutive.forms import (
    GRAIN_GROWTH,
    JMAK,
    KOCKS_MECKING,
    KOISTINEN_MARBURGER,
)


@dataclass(frozen=True)
class ConstitutiveHeatingAndSoak(EvolutionOperator):
    """Heating and soak, with every changing component governed by a declared form
    (Core §3.3; ADR-044).

    Still an **erasure** (Core §3.9): recrystallisation destroys stored
    dislocation substructure, which is the same physical claim
    `omi_domains.flagship.HEATING_AND_SOAK` makes with a bare relaxation rate. The
    difference is that the claim now has a declared form behind it, with a stated
    regime where that form holds.

    **`KOISTINEN_MARBURGER` is deliberately NOT applied here, and the validity
    machinery is why.** A first version applied it at the soak temperature, and the
    extrapolation report flagged the query at `5.71x` outside the form's declared
    window with a `CONTROL_INVERSE` action — correctly, because a soak above `Ms`
    is a temperature at which no athermal transformation occurs and the form does
    not apply at all. The report caught a real modelling error on the machinery's
    first application to real physics, which is the outcome ADR-043 argued the
    category was for. The athermal form now lives on `ConstitutiveTransfer`, where
    the piece cools through the window in which it holds.
    """

    temperature: float = 950.0
    """Soak temperature, inside both `GRAIN_GROWTH`'s and `KOCKS_MECKING`'s declared
    windows at the default (`forms.py`)."""
    substructure_floor: float = 0.05
    """Residual substructure the erasure leaves behind — an erasure with
    `L ≪ 1`, not a projection to exactly zero (Core §3.9)."""
    levelling_relaxation: float = 0.3
    coating_drift: float = 0.05
    coating_target_gain: float = 0.02

    @property
    def is_erasure(self) -> bool:
        return True

    def step(self, state: State, control: Control) -> State:
        hold_time = control.duration
        intensity = control(control.t0)[0]

        grain = state.get(Slot.M, "prior_grain_size")[0]
        substructure = state.get(Slot.Z, "substructure_density")[0]
        levelling = state.get(Slot.NU, "levelling_field")[0]
        coating = state.get(Slot.GAMMA, "coating_thickness")[0]
        deformation = state.get(Slot.M, "prior_deformation")[0]

        # prior_grain_size: was rate == 0.0 in flagship; now the declared
        # parabolic law transports it.
        new_grain = float(
            GRAIN_GROWTH.evaluate(
                {"grain_size": grain, "temperature": self.temperature, "hold_time": hold_time}
            )[0]
        )

        # substructure_density: erased, and the fraction erased is now the
        # declared JMAK recrystallised fraction rather than an unexplained rate.
        recrystallised = float(JMAK.evaluate({"hold_time": hold_time})[0])
        new_substructure = substructure * (1.0 - recrystallised) + self.substructure_floor * recrystallised

        # prior_deformation is erased with the substructure that carried it.
        new_deformation = deformation * (1.0 - recrystallised)

        new_levelling = levelling * np.exp(-self.levelling_relaxation * hold_time)
        coating_target = self.coating_target_gain * intensity
        new_coating = coating_target + (coating - coating_target) * np.exp(
            -self.coating_drift * hold_time
        )

        s = state
        s = s.with_component(Slot.M, "prior_deformation", np.array([new_deformation]))
        s = s.with_component(Slot.M, "prior_grain_size", np.array([new_grain]))
        s = s.with_component(Slot.Z, "substructure_density", np.array([new_substructure]))
        s = s.with_component(Slot.NU, "levelling_field", np.array([new_levelling]))
        s = s.with_component(Slot.GAMMA, "coating_thickness", np.array([new_coating]))
        return s

    def extrapolation_report(self, state: State, control: Control) -> ChainExtrapolationReport:
        """Where this step's declared forms sit relative to their validated ranges
        (Spec §2.2's proposed reporting obligation; ADR-043).

        This is the *buy physics* signal `docs/V1.4-EDITS.md` §11 records as having
        no mechanism in v1.3 — reported alongside the step, never enforcing it.
        """
        return worst_extrapolation(
            {
                "grain_growth": GRAIN_GROWTH.report(
                    {"temperature": self.temperature}
                ),
                "jmak": JMAK.report(
                    {"transformed_fraction": float(JMAK.evaluate({"hold_time": control.duration})[0])}
                ),
                "kocks_mecking": KOCKS_MECKING.report(
                    {
                        "strain_rate": max(abs(control(control.t0)[0]), 1.0e-3),
                        "temperature": self.temperature,
                        "stored_density": state.get(Slot.Z, "substructure_density")[0],
                    }
                ),
            }
        )


@dataclass(frozen=True)
class ConstitutiveTransfer(EvolutionOperator):
    """Short, well-instrumented transfer, during which the piece cools through the
    athermal transformation window (Core §7.1's stage table; Core §3.3).

    This is where `KOISTINEN_MARBURGER` applies: `end_temperature` sits inside its
    declared window, unlike the soak (see `ConstitutiveHeatingAndSoak`, which
    documents why the form was moved here). `accumulated_hardening` — one of the
    three components Phase 1 measured at `rate == 0.0` in flagship — is transported
    by that declared form.
    """

    end_temperature: float = 560.0
    """Temperature reached by the end of transfer, inside `KOISTINEN_MARBURGER`'s
    declared window `[480, 620]` and below `Ms` (`forms.py`)."""
    levelling_relaxation: float = 0.1
    coating_drift: float = 0.02

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        dt = control.duration
        levelling = state.get(Slot.NU, "levelling_field")[0]
        coating = state.get(Slot.GAMMA, "coating_thickness")[0]
        hardening = state.get(Slot.Z, "accumulated_hardening")[0]

        # accumulated_hardening: was rate == 0.0 in flagship; the declared athermal
        # form transports it here, inside the window where that form holds.
        athermal = float(KOISTINEN_MARBURGER.evaluate({"temperature": self.end_temperature})[0])

        s = state
        s = s.with_component(Slot.Z, "accumulated_hardening", np.array([hardening + athermal]))
        s = s.with_component(
            Slot.NU, "levelling_field", np.array([levelling * np.exp(-self.levelling_relaxation * dt)])
        )
        s = s.with_component(
            Slot.GAMMA, "coating_thickness", np.array([coating * np.exp(-self.coating_drift * dt)])
        )
        return s

    def extrapolation_report(self, state: State, control: Control) -> ChainExtrapolationReport:
        """Where this step's declared form sits relative to its validated range
        (Spec §2.2's proposed reporting obligation; ADR-043)."""
        return worst_extrapolation(
            {"koistinen_marburger": KOISTINEN_MARBURGER.report({"temperature": self.end_temperature})}
        )


CONSTITUTIVE_HEATING_AND_SOAK = ConstitutiveHeatingAndSoak()
CONSTITUTIVE_TRANSFER = ConstitutiveTransfer()
