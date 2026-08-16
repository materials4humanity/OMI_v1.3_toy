"""`c̄` for the composition variant: the descriptor map, the projection scale, and the
declared mean (Core §4 item 1b; Core §6.2; ADR-050, ADR-052, ADR-076).

**Toy physics with declared provenance.** The descriptor functionals below have the
*form* of real ones and are not calibrated against any dataset — the same discipline
`flagship_constitutive.forms` states for its parameter values (CLAUDE.md §2: the
operators are not the point). What is under test is the declaration machinery and the
constancy residual, not the chemistry.
"""

from __future__ import annotations

import numpy as np

from omi.proposed.composition import DescriptorMap, MeanComposition, ProjectionScale
from omi.state import FloatArray

SPECIES: tuple[str, ...] = ("base", "solute_a", "solute_b", "residual")
"""The underlying fraction space, named generically.

Generic rather than by element for `flagship_constitutive.forms`'s stated reason: naming
specific elements would imply a calibration this toy does not have. Four coordinates, so
the simplex is non-trivial in the direction that matters (`Spec §2.2`)."""

DESCRIPTORS: tuple[str, ...] = ("hardenability_index", "solute_drag_index")
"""The declared descriptor basis (ADR-052).

Each makes a falsifiable claim about argument structure — "the operator depends on
chemistry only through these" — testable by holding the descriptors fixed while varying
the underlying fractions, which is why both spaces are declared and not just one."""

_HARDENABILITY_WEIGHTS: FloatArray = np.array([0.0, 3.0, 1.5, 0.5])
_DRAG_WEIGHTS: FloatArray = np.array([0.0, 1.0, 4.0, 0.25])


def _evaluate(fractions: FloatArray) -> FloatArray:
    """Two weighted sums over the fraction vector (Spec §2.2's proposed sixth category's
    shape, applied to a descriptor rather than a response).

    Linear deliberately: a descriptor map whose own nonlinearity dominated would make the
    held-out test ADR-052 describes harder to interpret than the machinery under test.
    """
    return np.array(
        [
            float(_HARDENABILITY_WEIGHTS @ fractions),
            float(_DRAG_WEIGHTS @ fractions),
        ]
    )


DESCRIPTOR_MAP = DescriptorMap(
    underlying=SPECIES,
    descriptors=DESCRIPTORS,
    evaluate=_evaluate,
    provenance=(
        "Toy functionals with the form of published equivalent-content indices; weights "
        "chosen for separation between the two descriptors, not fitted to data. Declared so "
        "the argument-structure claim is falsifiable (ADR-052), not so the numbers are used."
    ),
)
"""The declared map from fractions to descriptors, with Spec §2.2's simplex applied as
architecture inside it (ADR-076 decision 1): `descriptors_of` cannot be reached with a
fraction vector off the simplex."""


BULK_PROJECTION_SCALE = ProjectionScale(
    length=50.0,
    units="micrometre",
    characterisation_method=(
        "quantitative area-scan microanalysis at the declared step size: features coarser "
        "than this are resolved and enter c-bar's domain mean, finer ones are unresolved and "
        "are carried by the sub-resolution delta-c occupant in z"
    ),
)
"""The `c̄`/`δc` line for the bulk domain (ADR-050; `docs/V1.4-EDITS.md` E-45, E-31).

Declared because operator reuse between two implementations is sound only if their splits
match and **nothing detects a mismatch** — this makes the mismatch visible to
`omi.interface.diff` without making it checkable, which is ADR-050's stated position."""


BULK_MEAN = MeanComposition(
    region="representative_volume",
    unconstrained=np.array([2.2, -0.4, -1.1, -2.0]),
    descriptor_map=DESCRIPTOR_MAP,
    projection_scale=BULK_PROJECTION_SCALE,
    domain_declared_closed=True,
    closure_note=(
        "Closed over the whole declared chain: this is a representative volume in the "
        "interior, no free surface bounds it, and neither declared operator transports "
        "solute across its boundary. That closure is what makes the mean constant by "
        "conservation (ADR-050), and it is the claim the constancy residual tests."
    ),
)
"""`c̄` over the interior representative volume, declared **closed** — the case ADR-050
says must hold by conservation."""


SURFACE_MEAN = MeanComposition(
    region="surface_layer",
    unconstrained=np.array([2.2, -0.4, -1.1, -2.0]),
    descriptor_map=DESCRIPTOR_MAP,
    projection_scale=BULK_PROJECTION_SCALE,
    domain_declared_closed=False,
    closure_note=(
        "OPEN, and the flux is named: solute leaves through the free surface during the "
        "soak. This is ADR-050's own worked instance for a drifting mean — a mean over a "
        "surface layer is not constant because the species leaves through a free boundary — "
        "and the correct declaration is an open domain with the flux named rather than a "
        "closed domain that fails its residual."
    ),
)
"""The same composition over a domain declared **open**. Declared so the constancy
residual's `CONSISTENT_OPEN` verdict has a real subject: a pass/fail check cannot express
a domain that is declared open and duly drifts (ADR-050; ADR-076 decision 2)."""
