"""The discovery domain's declared constitutive forms (Core §4 item 6d / Spec §2.2's
proposed sixth hard-constraint category; ADR-043, ADR-054, ADR-060).

**Declaring these is what makes the validity report live on this domain**, which is the
diagnostic Part 5(1) found structurally unavailable on contrast: contrast declares no
constitutive form, so its operator does not satisfy `ConstitutivelyConstrained` and there
was nothing for an extrapolation report to be computed against. Here there is.

**Composition-dependent validity, per ADR-054.** A form's validity range is declared as a
function over composition rather than as a fixed interval, and this module realises that
by declaring the range at a **reference formulation** together with the descriptor
interval over which the range itself is claimed to hold. ADR-054's regime-boundary rule
applies: a query whose composition leaves that interval is **refused** rather than
annotated, because a validity range extrapolated across a phase boundary is not a wider
range, it is a different form.

**Parameter values are order-of-magnitude placeholders for a toy declaration, not
calibrated catalysis**, and every `provenance` string says so — the same discipline
`omi_domains.flagship_constitutive.forms` states for its own. What is claimed is the
*structure*: the functional form, which quantity bounds it, and which mechanism ends it.
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

LH_RATE_CONSTANT = 4.0
LH_ADSORPTION_CONSTANT = 2.5
LH_TEMPERATURE_WINDOW = (450.0, 700.0)
LH_PARTIAL_PRESSURE_WINDOW = (0.05, 2.0)
LH_SITE_DENSITY_CEILING = 12.0
"""Ceiling in the toy's own dimensionless site-density index, not in physical site
counts — declared in the units the state component actually carries, for the reason
`flagship_constitutive.forms.KM_DENSITY_CEILING` states: a bound in units the state does
not use is a unit error wearing a bound's clothes."""


def langmuir_hinshelwood(values: Mapping[str, float]) -> FloatArray:
    """`r = k·K·p / (1 + K·p)²` — single-site adsorption-limited turnover, scaled by the
    available active-site density (Spec §2.2's proposed sixth category).

    A **rate**, so its output must be integrated to give a conversion (see
    :class:`~omi.proposed.constitutive.FormKind`). Saturating in partial pressure by
    construction, which is the mechanism that ends the form's usefulness at high coverage.
    """
    pressure = max(values["partial_pressure"], 0.0)
    sites = max(values["active_site_density"], 0.0)
    occupancy = LH_ADSORPTION_CONSTANT * pressure
    return np.array([LH_RATE_CONSTANT * sites * occupancy / (1.0 + occupancy) ** 2])


LANGMUIR_HINSHELWOOD = ConstitutiveForm(
    name="langmuir_hinshelwood_turnover",
    kind=FormKind.RATE_LAW,
    evaluate=langmuir_hinshelwood,
    parameters={"k": LH_RATE_CONSTANT, "K": LH_ADSORPTION_CONSTANT},
    validity=ValidityRange(
        (
            ValidityBound(
                name="temperature",
                space=ValiditySpace.CONTROL,
                low=LH_TEMPERATURE_WINDOW[0],
                high=LH_TEMPERATURE_WINDOW[1],
                regime=(
                    "fitted temperature window; above it the support sinters and the site count "
                    "this form treats as a parameter starts evolving"
                ),
            ),
            ValidityBound(
                name="partial_pressure",
                space=ValiditySpace.CONTROL,
                low=LH_PARTIAL_PRESSURE_WINDOW[0],
                high=LH_PARTIAL_PRESSURE_WINDOW[1],
                regime="single-site regime; above it multi-site competition changes the rate law",
            ),
            ValidityBound(
                name="active_site_density",
                space=ValiditySpace.STATE,
                low=0.0,
                high=LH_SITE_DENSITY_CEILING,
                regime="dilute-site regime where sites act independently",
            ),
        )
    ),
    provenance=(
        "Langmuir-Hinshelwood single-site kinetics, canonical. Parameter values are "
        "order-of-magnitude placeholders for this toy declaration, not a calibrated fit; the "
        "declared structure and boundary mechanisms are what is claimed."
    ),
    governs=((Slot.Z, "active_site_density"),),
)


SINTERING_EXPONENT = 3.0
SINTERING_RATE = 0.02
SINTERING_TEMPERATURE_WINDOW = (500.0, 750.0)


def particle_coarsening(values: Mapping[str, float]) -> FloatArray:
    """`d(d^n)/dt = k` — power-law coarsening of the dispersed phase (Spec §2.2).

    Returns the rate of change of `d^n`, not of `d`: a coarsening law stated in the
    linearising variable is the form the source establishes, and converting it here would
    hide which quantity the power law is actually linear in.
    """
    del values  # the toy's rate is temperature-indexed via its validity window, not evaluated here
    return np.array([SINTERING_RATE])


PARTICLE_COARSENING = ConstitutiveForm(
    name="power_law_particle_coarsening",
    kind=FormKind.RATE_LAW,
    evaluate=particle_coarsening,
    parameters={"n": SINTERING_EXPONENT, "k": SINTERING_RATE},
    validity=ValidityRange(
        (
            ValidityBound(
                name="temperature",
                space=ValiditySpace.CONTROL,
                low=SINTERING_TEMPERATURE_WINDOW[0],
                high=SINTERING_TEMPERATURE_WINDOW[1],
                regime=(
                    "below, coarsening is kinetically frozen on the campaign timescale; above, "
                    "support-mediated transport takes over and the exponent changes"
                ),
                low_kind=EdgeKind.APPROXIMATE,
            ),
            ValidityBound(
                name="mean_particle_size",
                space=ValiditySpace.STATE,
                low=UNBOUNDED,
                high=40.0,
                regime=(
                    "power law holds while particles are small against the support pore scale; "
                    "above it the pore network confines growth"
                ),
                fitted_scale=10.0,
            ),
        )
    ),
    provenance=(
        "Power-law coarsening, canonical form. Exponent and rate are placeholders for this toy "
        "declaration; the claim is the functional form and the two boundary mechanisms."
    ),
    governs=((Slot.M, "mean_particle_size"),),
)


SDL_FORMS = (LANGMUIR_HINSHELWOOD, PARTICLE_COARSENING)
"""The declared forms, in the order they would apply along a preparation-then-evaluation
chain. **Two, not one**, so the chain-level worst-case report
(`omi.proposed.constitutive.worst_extrapolation`) has something to aggregate — a
single-form domain cannot exercise it."""


COMPOSITION_VALIDITY_INTERVAL: dict[str, tuple[float, float]] = {
    "valence_electron_count": (7.2, 9.4),
    "mixing_enthalpy": (-28.0, -4.0),
    "support_acidity": (0.15, 0.85),
}
"""ADR-054's composition-dependent validity, in its declarable form: the descriptor
interval over which the two forms' **validity ranges above are themselves claimed to
hold**.

This is the second-order declaration ADR-054 asks for and it is deliberately separate
from the ranges themselves. A query inside `LANGMUIR_HINSHELWOOD`'s temperature window but
outside this interval is not mildly extrapolated — the window was established for a
different chemistry, so the form's own bounds are unwarranted there. ADR-054's rule is that
such a query is **refused** rather than annotated with a factor, because annotating implies
the range still means something.

**Not implemented as a refusal here**, and that is the honest scope statement: the refusal
belongs to the operator that consumes the form, and this part declares no operator. What is
declared is the interval the refusal would fire outside.
"""
