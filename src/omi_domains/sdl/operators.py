"""The discovery domain's three evolution operators (Core §3.2; ADR-064).

`Preparation` → `Calcination` → `Evaluation`. ADR-060 declared this domain with **no**
operator and said the operator was Part 6's work; ADR-064 discharges that, because Part 6's
gate requires the vacuity precondition to be re-verified on the domain the claim is made on
and a declaration cannot be run.

**Composition is a field of the operator, never a component of the state.** The operator
*family* is indexed by composition and a campaign chooses which member to instantiate —
ADR-051's Parameter role and E-46's separation realised in code. Putting composition in
`SDL_SCHEMA` would type a fixed index as a state, and it would collapse ADR-053's
composition inverse into the structure inverse.

**Calcination is the declared erasure** (`SDL_V13_CORE.erasure_inventory`), and its
completeness is *measured* by `tests/test_sdl_operators.py` rather than asserted here: every
post-calcination component is set by composition and the calcination programme, plus a small
declared feed-through of the incoming precursor state, except `dispersed_phase_loading`,
which is conserved exactly because the domain declares
`metal_mass_conservation_across_calcination`. So the Jacobian carries one singular value near
unity and the rest near the feed-through coefficient.

What is still deliberately **not** implemented, per ADR-060 and ADR-064: ADR-054's refusal
outside `COMPOSITION_VALIDITY_INTERVAL`, and every Tier II anti-goal (CLAUDE.md §9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, Slot, State

from omi_domains.sdl.forms import (
    SINTERING_EXPONENT,
    SINTERING_RATE,
    particle_coarsening,
)
from omi_domains.sdl.state import SPECIES

PRECURSOR_FEEDTHROUGH = 0.02
"""How much of the incoming precursor state survives calcination, as a fraction.

**A declared number with no Spec basis, and the one design choice in this module that is not
physics** (ADR-064). It sets how *complete* the erasure is and therefore what
`omi.erasure.measure_erasure` reports, so it is declared here with its consequence stated
rather than buried in an expression. The oracle asserts the qualitative claim — effective
rank one out of seven, `L << 1` — and not this value, per CLAUDE.md §7.
"""


def descriptors(composition: Mapping[str, float]) -> dict[str, float]:
    """The declared descriptor basis (ADR-052; `omi_domains.sdl.state.DESCRIPTORS`) as
    named functionals of the species fractions.

    Each makes the falsifiable claim ADR-052 states — "the operator family depends on
    chemistry only through these" — which is testable by holding out a formulation that
    varies the fractions at fixed descriptors. The coefficients are order-of-magnitude
    placeholders for a toy declaration, on the same footing as
    `omi_domains.sdl.forms`' parameter values.
    """
    metal_a = composition["metal_a"]
    metal_b = composition["metal_b"]
    promoter = composition["promoter"]
    support = composition["support"]
    metal_total = max(metal_a + metal_b + promoter, 1.0e-9)
    return {
        "valence_electron_count": (9.0 * metal_a + 10.0 * metal_b + 7.0 * promoter) / metal_total,
        "mixing_enthalpy": -300.0 * metal_a * metal_b + 5.0 * promoter - 2.0,
        "support_acidity": 0.15 + 0.7 * support,
    }


def _normalised(composition: Mapping[str, float]) -> dict[str, float]:
    """The species fractions with the declared simplex constraint applied as
    *architecture* rather than as a penalty (CLAUDE.md invariant 5): a set of fractions
    summing to 1.03 is not a slightly wrong composition, it is not a composition."""
    total = sum(composition[name] for name in SPECIES)
    if total <= 0.0:
        raise ValueError("a composition with non-positive total is not a composition")
    return {name: composition[name] / total for name in SPECIES}


@dataclass(frozen=True)
class Preparation(EvolutionOperator):
    """Incipient-wetness impregnation followed by drying (Core §3.2): the recipe becomes a
    dried-precursor state.

    The control programme carries the drying temperature; the recipe itself is this
    operator's :attr:`composition` field, for ADR-064's reason.
    """

    composition: Mapping[str, float]
    uptake: float = 0.92
    """Fraction of the dissolved metal that ends up on the support after drying."""
    seed_size: float = 2.0
    """Precursor crystallite size before any thermal treatment, in the toy's own length
    index — the units `forms.PARTICLE_COARSENING`'s `mean_particle_size` bound uses."""
    pore_filling_gain: float = 1.1
    defect_gain: float = 0.9
    site_gain: float = 40.0
    """The same geometric site-density constant `Calcination` and `Evaluation` use, so the
    three operators agree on what a site density means."""
    predried_fraction: float = 0.05
    """Fraction of the precursor already decomposed by drying. Small, and non-zero for a
    stated reason: a state component with no incoming variation contributes a structurally
    zero singular value to an erasure measurement, which would inflate the reported
    completeness with a direction the population never occupies."""

    @property
    def is_erasure(self) -> bool:
        """`False`: drying compresses nothing — a different recipe gives a different
        precursor, which is what makes the composition inverse well-posed at this step."""
        return False

    def step(self, state: State, control: Control) -> State:
        fractions = _normalised(self.composition)
        drying_temperature = float(control(control.t0)[0])
        metal = fractions["metal_a"] + fractions["metal_b"] + fractions["promoter"]

        loading = self.uptake * metal
        # Hotter drying nucleates fewer, larger crystallites, and a more heavily loaded pore
        # crowds them together: the two standard drying trade-offs, and the second is why the
        # precursor size carries recipe information for calcination to erase.
        size = self.seed_size * (1.0 + 0.0015 * (drying_temperature - 350.0)) * (1.0 + 1.5 * loading)
        accessibility = max(
            state.get(Slot.NU, "pore_network_accessibility")[0] - self.pore_filling_gain * loading,
            0.05,
        )
        defects = self.defect_gain * fractions["promoter"]
        # Drying already decomposes a small fraction of the precursor, so a dried sample has a
        # few active sites. Declared non-zero deliberately: a component the incoming population
        # never varies is a component no erasure measurement can say anything about.
        sites = self.predried_fraction * self.site_gain * loading / size

        s = state
        s = s.with_component(Slot.M, "dispersed_phase_loading", np.array([loading]))
        s = s.with_component(Slot.M, "mean_particle_size", np.array([size]))
        s = s.with_component(Slot.Z, "active_site_density", np.array([sites]))
        s = s.with_component(Slot.Z, "defect_site_fraction", np.array([defects]))
        s = s.with_component(Slot.NU, "pore_network_accessibility", np.array([accessibility]))
        s = s.with_component(Slot.GAMMA, "support_interface_coverage", np.array([min(loading * 2.0, 1.0)]))
        s = s.with_component(Slot.GAMMA, "surface_reconstruction_index", np.array([0.0]))
        return s


@dataclass(frozen=True)
class Calcination(EvolutionOperator):
    """Thermal treatment (Core §3.2), and **this domain's declared erasure** (Core §3.4).

    The calcined dispersion is set by composition and the calcination programme: the
    precursor's own state survives only through :data:`PRECURSOR_FEEDTHROUGH`. The one
    exception is `dispersed_phase_loading`, conserved exactly — the domain's declared
    invariant `metal_mass_conservation_across_calcination`. An erasure that violated a
    declared conservation law would not be a more complete erasure, it would be a wrong
    operator (ADR-064).
    """

    composition: Mapping[str, float]
    equilibrium_size_gain: float = 0.018
    site_gain: float = 40.0
    promoter_segregation: float = 0.55
    reconstruction_gain: float = 0.0012

    @property
    def is_erasure(self) -> bool:
        """`True` — declared, and *measured* by `tests/test_sdl_operators.py` rather than
        taken on this property's word (Core §3.4's `L << 1`; Spec §3.2's rank bound)."""
        return True

    def equilibrium_size(self, temperature: float, hold: float) -> float:
        """The dispersion the composition and programme determine, independent of the
        precursor state — the mechanism that makes this operator an erasure."""
        descriptor = descriptors(_normalised(self.composition))
        # Acidic supports anchor the dispersed phase; a strongly negative mixing enthalpy
        # resists coarsening. Both act on the equilibrium size, not on the rate.
        anchoring = 1.0 + 0.8 * descriptor["support_acidity"]
        alloying = 1.0 - 0.010 * descriptor["mixing_enthalpy"]
        driving = self.equilibrium_size_gain * (temperature - 600.0) * (1.0 + 0.5 * hold)
        return max(3.0 + driving / (anchoring * alloying), 1.0)

    def step(self, state: State, control: Control) -> State:
        fractions = _normalised(self.composition)
        temperature = float(control(control.t0)[0])
        hold = control.duration

        loading = state.get(Slot.M, "dispersed_phase_loading")[0]
        size_before = state.get(Slot.M, "mean_particle_size")[0]
        defects_before = state.get(Slot.Z, "defect_site_fraction")[0]
        accessibility_before = state.get(Slot.NU, "pore_network_accessibility")[0]
        coverage_before = state.get(Slot.GAMMA, "support_interface_coverage")[0]
        reconstruction_before = state.get(Slot.GAMMA, "surface_reconstruction_index")[0]

        size = self.equilibrium_size(temperature, hold) + PRECURSOR_FEEDTHROUGH * size_before
        # Dispersed area per unit mass goes as 1/d: the geometric relation, not a fit.
        sites = self.site_gain * loading / size
        defects = self.promoter_segregation * fractions["promoter"] + PRECURSOR_FEEDTHROUGH * defects_before
        accessibility = max(
            0.85 - 0.9 * loading + PRECURSOR_FEEDTHROUGH * accessibility_before, 0.05
        )
        coverage = min(1.2 * loading / size + PRECURSOR_FEEDTHROUGH * coverage_before, 1.0)
        reconstruction = self.reconstruction_gain * max(temperature - 600.0, 0.0) + (
            PRECURSOR_FEEDTHROUGH * reconstruction_before
        )

        s = state
        s = s.with_component(Slot.M, "dispersed_phase_loading", np.array([loading]))
        s = s.with_component(Slot.M, "mean_particle_size", np.array([size]))
        s = s.with_component(Slot.Z, "active_site_density", np.array([sites]))
        s = s.with_component(Slot.Z, "defect_site_fraction", np.array([defects]))
        s = s.with_component(Slot.NU, "pore_network_accessibility", np.array([accessibility]))
        s = s.with_component(Slot.GAMMA, "support_interface_coverage", np.array([coverage]))
        s = s.with_component(Slot.GAMMA, "surface_reconstruction_index", np.array([reconstruction]))
        return s


@dataclass(frozen=True)
class Evaluation(EvolutionOperator):
    """One interval of reaction at a declared evaluation condition (Core §3.2), with
    time-on-stream deactivation.

    **Consumes the declared constitutive forms** rather than restating them:
    `forms.particle_coarsening` supplies the coarsening rate in its own linearising
    variable `d^n`, and the site density is recomputed from the coarsened size through the
    same geometric relation `Calcination` uses. That is what makes the validity report live
    on a real trajectory instead of on a hypothetical query (ADR-064).

    :attr:`coarsening_scale` is the hook the Part 6 construction drives: `1.0` is the
    declared model, and a per-sample value other than `1.0` is a quantity the declared
    schema does not carry (ADR-066).
    """

    site_gain: float = 40.0
    coarsening_scale: float = 1.0
    reconstruction_rate: float = 0.004
    defect_annealing: float = 0.02

    @property
    def is_erasure(self) -> bool:
        """`False`: deactivation is a slow drift, not a compression — nothing about the
        calcined material becomes unrecoverable over an evaluation."""
        return False

    def step(self, state: State, control: Control) -> State:
        dt = control.duration
        temperature = float(control(control.t0)[0])

        loading = state.get(Slot.M, "dispersed_phase_loading")[0]
        size = state.get(Slot.M, "mean_particle_size")[0]
        defects = state.get(Slot.Z, "defect_site_fraction")[0]
        accessibility = state.get(Slot.NU, "pore_network_accessibility")[0]
        coverage = state.get(Slot.GAMMA, "support_interface_coverage")[0]
        reconstruction = state.get(Slot.GAMMA, "surface_reconstruction_index")[0]

        rate = float(particle_coarsening({}) [0]) * self.coarsening_scale
        # The declared form is a law for d^n, so it is integrated in d^n (forms.py).
        thermal = np.exp(0.004 * (temperature - 550.0))
        new_size = float((size**SINTERING_EXPONENT + rate * thermal * dt) ** (1.0 / SINTERING_EXPONENT))
        new_sites = self.site_gain * loading / new_size
        new_defects = defects * float(np.exp(-self.defect_annealing * dt))
        new_reconstruction = reconstruction + self.reconstruction_rate * dt
        new_coverage = min(1.2 * loading / new_size, 1.0)

        s = state
        s = s.with_component(Slot.M, "mean_particle_size", np.array([new_size]))
        s = s.with_component(Slot.Z, "active_site_density", np.array([new_sites]))
        s = s.with_component(Slot.Z, "defect_site_fraction", np.array([new_defects]))
        s = s.with_component(Slot.NU, "pore_network_accessibility", np.array([accessibility]))
        s = s.with_component(Slot.GAMMA, "support_interface_coverage", np.array([new_coverage]))
        s = s.with_component(Slot.GAMMA, "surface_reconstruction_index", np.array([new_reconstruction]))
        return s


DECLARED_COARSENING_RATE = SINTERING_RATE
"""Re-exported so a consumer reads the coarsening rate off the declared form rather than
off a second copy of the number (CLAUDE.md §8: never hardcode a narrative number)."""


def sites_from_size(loading: float, size: float, site_gain: float = 40.0) -> FloatArray:
    """The geometric site-density relation both `Calcination` and `Evaluation` use.

    Exposed so the Part 6 construction can express the vectorised true dynamics in terms of
    the *declared* relation rather than a re-typed copy of it — the discipline
    `tests/oracles/contrast_insufficiency.py` states for the same reason."""
    return np.array([site_gain * loading / max(size, 1.0e-9)])
