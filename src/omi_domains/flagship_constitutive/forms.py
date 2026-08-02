"""The five declared constitutive forms for the flagship chain (M11.3; ADR-044,
docs/DECISIONS.md), filling Core §4 item 6d / Spec §2.2's proposed sixth
hard-constraint category.

Cites Core §4 item 6 (role-scoped by `omi.proposed.item6`) and Spec §2.2. Every
form is declared as `omi.proposed.constitutive.ConstitutiveForm`: an evaluable
callable, its fitted parameters, **its validity range**, its provenance, and the
state components it governs.

**The validity boundaries matter more than the forms.** A canonical form is easy
to write down; what the extension is arguing for is that declaring *where it stops
being true* buys extrapolation reach, so the boundary is the load-bearing content
(ADR-043). Each form below states its own, with the mechanism that ends it.

**Two edge kinds, both exercised by real physics rather than by the oracle alone.**
Three windows are two-sided and one is genuinely one-sided:

| Form | Window | Why |
|---|---|---|
| Kocks–Mecking | two-sided in control (strain rate, temperature) + state (stored density) | fitted regime has both ends; saturation is a state ceiling |
| Grain growth | two-sided in temperature | below, kinetics are frozen; above, abnormal growth intervenes |
| JMAK | two-sided in transformed fraction | early nucleation transient below, impingement above |
| Koistinen–Marburger | two-sided in temperature | `Ms` above (no athermal transformation), competing isothermal product below |
| Hall–Petch | **one-sided** in grain size | breaks at fine grain size; no upper limit — coarse grains simply strengthen less |

Koistinen–Marburger's **lower** edge is declared `APPROXIMATE`: it is where a
competing isothermal transformation product intervenes during the quench, so it
depends on the cooling path taken to reach it and is genuinely fuzzy rather than
imprecisely known. Declaring it as a clean number would fabricate precision the
physics does not have — a fuzzy bound honestly declared is worth more than a
precise one invented (ADR-043).

**Parameter values here are order-of-magnitude placeholders for a toy chain, not
calibrated metallurgy**, and every `provenance` string says so. What is claimed is
the *structure* — the functional form, which quantity bounds it, and which
mechanism ends it — because that is what the extrapolation experiment tests.

**A sixth object, but still five forms.** `KOCKS_MECKING_STRAIN_WINDOWED` (added
at M11.5, ADR-047) is the same physics and the same parameters as `KOCKS_MECKING`
with one further bound declared. It exists as a sibling because a declared
validity range cannot be extended in place without breaking every existing caller
— see that constant's own docstring, and `docs/V1.4-EDITS.md` E-40.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np

from omi.proposed.constitutive import (
    UNBOUNDED,
    ConstitutiveForm,
    EdgeKind,
    FormKind,
    ValidityBound,
    ValidityRange,
    ValiditySpace,
)
from omi.state import FloatArray, Slot

GAS_CONSTANT = 8.314
"""J/(mol·K), for the Arrhenius factor in grain growth."""


# --- Kocks–Mecking dislocation evolution -------------------------------------

KM_K1 = 8.0
KM_K2 = 2.0
KM_RATE_WINDOW = (1.0e-3, 10.0)
KM_TEMPERATURE_WINDOW = (500.0, 1100.0)
KM_DENSITY_CEILING = 20.0
"""Saturation ceiling in the *toy's own* dimensionless density index, not in
physical m^-2. Declared in the units the state component actually carries: a bound
stated in units the state does not use is not a bound, it is a unit error wearing
one, and the extrapolation report would read every in-range query as sitting at the
far edge of an enormous window."""


def kocks_mecking(values: Mapping[str, float]) -> FloatArray:
    """`dρ/dγ = k₁√ρ − k₂ρ` — storage minus dynamic recovery (Spec §2.2's
    proposed sixth category; a **rate law**, so its output must be integrated).

    Returns the derivative with respect to accumulated shear strain, not a
    dislocation density: see `FormKind.RATE_LAW`.
    """
    rho = max(values["stored_density"], 0.0)
    return np.array([KM_K1 * np.sqrt(rho) - KM_K2 * rho])


KOCKS_MECKING = ConstitutiveForm(
    name="kocks_mecking_dislocation_evolution",
    kind=FormKind.RATE_LAW,
    evaluate=kocks_mecking,
    parameters={"k1": KM_K1, "k2": KM_K2},
    validity=ValidityRange(
        (
            ValidityBound(
                name="strain_rate",
                space=ValiditySpace.CONTROL,
                low=KM_RATE_WINDOW[0],
                high=KM_RATE_WINDOW[1],
                regime="fitted strain-rate window; above it dislocation drag changes the storage term",
            ),
            ValidityBound(
                name="temperature",
                space=ValiditySpace.CONTROL,
                low=KM_TEMPERATURE_WINDOW[0],
                high=KM_TEMPERATURE_WINDOW[1],
                regime="fitted temperature window; above it dynamic recrystallisation intervenes",
            ),
            ValidityBound(
                name="stored_density",
                space=ValiditySpace.STATE,
                low=0.0,
                high=KM_DENSITY_CEILING,
                regime="below the saturation ceiling where k1*sqrt(rho) ~ k2*rho",
            ),
        )
    ),
    provenance=(
        "Kocks & Mecking, canonical single-internal-variable dislocation kinetics. "
        "Parameter values are order-of-magnitude placeholders for this toy chain, not a "
        "calibrated fit; the declared structure and boundary mechanisms are what is claimed."
    ),
    governs=((Slot.Z, "substructure_density"),),
)


KM_STRAIN_WINDOW_HIGH = 1.0
"""Accumulated strain above which dynamic recrystallisation nucleates and begins
consuming stored dislocation density — a mechanism the Kocks–Mecking pair
`(k₁, k₂)` does not express, so the form's validity ends there.

The value is the toy's own, chosen to coincide with the upper edge of M11.5's
training range (ADR-047, docs/DECISIONS.md) so that "outside the declared window"
and "the withheld physics is active" name the same region by construction rather
than by coincidence — the property ADR-045 required of Generator A's rate window
and which is preserved here verbatim."""

KOCKS_MECKING_STRAIN_WINDOWED = ConstitutiveForm(
    name="kocks_mecking_dislocation_evolution_strain_windowed",
    kind=FormKind.RATE_LAW,
    evaluate=kocks_mecking,
    parameters={"k1": KM_K1, "k2": KM_K2},
    validity=ValidityRange(
        KOCKS_MECKING.validity.bounds
        + (
            ValidityBound(
                name="accumulated_strain",
                space=ValiditySpace.CONTROL,
                low=UNBOUNDED,
                high=KM_STRAIN_WINDOW_HIGH,
                regime=(
                    "fitted strain window; above it dynamic recrystallisation nucleates and "
                    "consumes stored density, which the (k1, k2) pair cannot represent"
                ),
                high_kind=EdgeKind.APPROXIMATE,
                fitted_scale=1.0,
            ),
        )
    ),
    provenance=(
        "Kocks & Mecking as above, with the strain window the source's own fitting range "
        "implies made explicit. Identical physics and identical parameters to "
        "KOCKS_MECKING; the only difference is one further declared bound."
    ),
    governs=((Slot.Z, "substructure_density"),),
)
"""`KOCKS_MECKING` with one further declared bound, published **alongside** the
original rather than amending it (ADR-047, docs/DECISIONS.md).

**Why a second object and not an edit.** `ValidityRange.report` requires a value
for every declared bound and raises otherwise — deliberately, since silently
skipping an undeclared bound is how a validity range stops meaning anything
(ADR-043). The consequence is that a form's validity range **cannot be extended
without breaking every existing caller**: M11.3's chain and M11.4's sweep both
call `KOCKS_MECKING.report` with three keys and would raise against a
four-bound form. Declaring a sibling leaves those artefacts byte-stable.

The cost is that Core §4's item-6 comparison now sees two forms where the physics
is one. That refinement path is missing from the extension's design and is filed
as `docs/V1.4-EDITS.md` E-40; this constant is the worked instance behind it.

The lower edge is `UNBOUNDED` rather than `0.0`: accumulated strain is
non-negative as a matter of the quantity's definition, not as a matter of where
the form was fitted, and declaring a validity edge at a definitional floor would
report every small-strain query as sitting far from a window centre that does not
exist (ADR-043's one-sided rule). The upper edge is `APPROXIMATE` because a
recrystallisation onset strain is route- and microstructure-dependent — the same
honesty M11.3 applied to Koistinen–Marburger's lower edge.
"""


# --- Grain growth -------------------------------------------------------------

GG_N = 2.5
GG_K0 = 1.0e17
GG_ACTIVATION_ENERGY = 2.5e5
GG_TEMPERATURE_WINDOW = (700.0, 1200.0)


def grain_growth(values: Mapping[str, float]) -> FloatArray:
    """`dⁿ − d₀ⁿ = k₀ exp(−Q/RT)·t` solved for `d` — an **explicit solution**,
    already integrated over the hold (Spec §2.2; `FormKind.EXPLICIT_SOLUTION`)."""
    d0 = max(values["grain_size"], 1.0e-9)
    rate = GG_K0 * np.exp(-GG_ACTIVATION_ENERGY / (GAS_CONSTANT * values["temperature"]))
    return np.array([(d0**GG_N + rate * values["hold_time"]) ** (1.0 / GG_N)])


GRAIN_GROWTH = ConstitutiveForm(
    name="parabolic_grain_growth",
    kind=FormKind.EXPLICIT_SOLUTION,
    evaluate=grain_growth,
    parameters={"n": GG_N, "k0": GG_K0, "activation_energy": GG_ACTIVATION_ENERGY},
    validity=ValidityRange(
        (
            ValidityBound(
                name="temperature",
                space=ValiditySpace.CONTROL,
                low=GG_TEMPERATURE_WINDOW[0],
                high=GG_TEMPERATURE_WINDOW[1],
                regime=(
                    "below: kinetics frozen and the Arrhenius fit is unconstrained; "
                    "above: abnormal growth and solute-drag breakdown"
                ),
            ),
        )
    ),
    provenance=(
        "Classical parabolic/Arrhenius grain-growth law with n in the usual 2-3 range. "
        "Placeholder parameters for a toy chain, with k0 chosen so the Arrhenius factor is "
        "not numerically inert at the declared soak temperature — a first attempt used a "
        "physically-shaped k0 that produced no measurable growth at all, which is a "
        "calibration failure rather than a physics one. The exponent range and the "
        "abnormal-growth boundary are the substantive declarations."
    ),
    governs=((Slot.M, "prior_grain_size"),),
)


# --- JMAK recrystallisation ---------------------------------------------------

JMAK_K = 0.35
JMAK_N = 1.8
JMAK_FRACTION_WINDOW = (0.05, 0.95)


def jmak(values: Mapping[str, float]) -> FloatArray:
    """`X = 1 − exp(−k tⁿ)` — an **explicit solution** in elapsed time
    (Spec §2.2; `FormKind.EXPLICIT_SOLUTION`)."""
    t = max(values["hold_time"], 0.0)
    return np.array([1.0 - np.exp(-JMAK_K * t**JMAK_N)])


JMAK = ConstitutiveForm(
    name="jmak_recrystallised_fraction",
    kind=FormKind.EXPLICIT_SOLUTION,
    evaluate=jmak,
    parameters={"k": JMAK_K, "n": JMAK_N},
    validity=ValidityRange(
        (
            ValidityBound(
                name="transformed_fraction",
                space=ValiditySpace.STATE,
                low=JMAK_FRACTION_WINDOW[0],
                high=JMAK_FRACTION_WINDOW[1],
                regime=(
                    "below: early nucleation transient, the fixed-nucleation assumption not yet "
                    "established; above: impingement, where the constant-n Avrami exponent fails"
                ),
            ),
        )
    ),
    provenance=(
        "Johnson-Mehl-Avrami-Kolmogorov, assuming a fixed nucleation and growth mode. "
        "Placeholder k and n for a toy chain; the fixed-mode assumption and the "
        "impingement boundary are what the declaration asserts."
    ),
    governs=((Slot.Z, "substructure_density"),),
)


# --- Koistinen–Marburger ------------------------------------------------------

KM_ALPHA = 0.011
MS_TEMPERATURE = 620.0
KM_COMPETING_PRODUCT_ONSET = 480.0


def koistinen_marburger(values: Mapping[str, float]) -> FloatArray:
    """`f_m = 1 − exp(−α(Ms − T))` — athermal transformed fraction, an
    **explicit solution** with no time in it (Spec §2.2). Clamped at zero above
    `Ms`, where the form gives a negative argument and no transformation occurs.
    """
    undercooling = MS_TEMPERATURE - values["temperature"]
    if undercooling <= 0.0:
        return np.array([0.0])
    return np.array([1.0 - np.exp(-KM_ALPHA * undercooling)])


KOISTINEN_MARBURGER = ConstitutiveForm(
    name="koistinen_marburger_athermal_fraction",
    kind=FormKind.EXPLICIT_SOLUTION,
    evaluate=koistinen_marburger,
    parameters={"alpha": KM_ALPHA, "ms_temperature": MS_TEMPERATURE},
    validity=ValidityRange(
        (
            ValidityBound(
                name="temperature",
                space=ValiditySpace.CONTROL,
                low=KM_COMPETING_PRODUCT_ONSET,
                high=MS_TEMPERATURE,
                regime=(
                    "above Ms: no athermal transformation and the form does not apply; "
                    "below the lower edge: a competing isothermal product intervenes during "
                    "the quench, so the boundary is route-dependent"
                ),
                low_kind=EdgeKind.APPROXIMATE,
                high_kind=EdgeKind.SHARP,
            ),
        )
    ),
    provenance=(
        "Koistinen & Marburger (1959), athermal transformation kinetics; alpha ~ 0.011 /K is "
        "the conventional value. Ms is a sharp upper edge. The lower edge is declared "
        "APPROXIMATE because it is a competing-mechanism boundary that depends on the "
        "cooling path, not a fixed temperature (ADR-043)."
    ),
    governs=((Slot.Z, "accumulated_hardening"),),
)


# --- Hall–Petch + forest hardening -------------------------------------------

HP_SIGMA_0 = 100.0
HP_K = 20.0
HP_FOREST_COEFFICIENT = 2.0
HP_FINE_GRAIN_EDGE = 1.0
HP_GRAIN_SIZE_SCALE = 10.0


def hall_petch_forest(values: Mapping[str, float]) -> FloatArray:
    """`σ = σ₀ + k/√d + β·ρ_forest` — **algebraic** in state components, no time
    (Spec §2.2; `FormKind.ALGEBRAIC`).

    This is the real Hall-Petch exponent. The v1.3 flagship readout uses
    `20/(1 + |d|)`, a hyperbolic surrogate with the right sign and the wrong
    exponent (ADR-044) — replacing it is one of the things the extension buys, and
    the difference is recorded rather than quietly corrected.
    """
    d = max(values["grain_size"], 1.0e-9)
    forest = max(values["accumulated_hardening"], 0.0)
    return np.array([HP_SIGMA_0 + HP_K / np.sqrt(d) + HP_FOREST_COEFFICIENT * forest])


HALL_PETCH = ConstitutiveForm(
    name="hall_petch_with_forest_hardening",
    kind=FormKind.ALGEBRAIC,
    evaluate=hall_petch_forest,
    parameters={"sigma_0": HP_SIGMA_0, "k": HP_K, "forest_coefficient": HP_FOREST_COEFFICIENT},
    validity=ValidityRange(
        (
            ValidityBound(
                name="grain_size",
                space=ValiditySpace.STATE,
                low=HP_FINE_GRAIN_EDGE,
                high=UNBOUNDED,
                regime=(
                    "validated above the fine-grain edge only; below it the Hall-Petch slope "
                    "breaks down. No upper limit: coarse grains simply strengthen less, and the "
                    "form remains descriptive"
                ),
                fitted_scale=HP_GRAIN_SIZE_SCALE,
            ),
        )
    ),
    provenance=(
        "Hall (1951), Petch (1953), with an additive forest-hardening term. The one-sided "
        "window is the substantive declaration: the fine-grain breakdown is real and there is "
        "genuinely no upper bound, so declaring one would invent a limit (ADR-043)."
    ),
    governs=((Slot.M, "prior_grain_size"), (Slot.Z, "accumulated_hardening")),
)


DECLARED_FORMS: tuple[ConstitutiveForm, ...] = (
    KOCKS_MECKING,
    GRAIN_GROWTH,
    JMAK,
    KOISTINEN_MARBURGER,
    HALL_PETCH,
)
"""Core §4 item 6d for this domain, in the order ADR-044 tabulates them."""
