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


# --- Andrews' (1965) elemental content, for ADR-078 Decision 2 -----------------
#
# A SEPARATE underlying space and DescriptorMap from SPECIES/DESCRIPTOR_MAP above, on the
# ADR-078 amendment's own reasoning: mixing named-elemental and anonymous coordinates in one
# simplex would misrepresent both. SPECIES is anonymous *by design* (this docstring's own
# reason, restated above); ANDREWS_SPECIES exists for the opposite reason, to make a real
# elemental claim. Nothing in `omi.proposed.composition.DescriptorMap` assumes a domain
# declares only one instance -- it is a plain frozen dataclass with no registry -- so this
# needed no new plumbing, only a second declaration.
#
# **Different in kind from DESCRIPTOR_MAP above, and said so rather than reusing that
# docstring's "toy functional, not fitted to data" framing.** `hardenability_index` and
# `solute_drag_index` are declared explicitly NOT to correspond to any real quantity --
# their whole point is to test the argument-structure claim in the abstract. `carbon` and
# `manganese` below are declared TO correspond to real elemental content, because Andrews'
# (1965) formula is a real regression fitted against real carbon and manganese weight
# percentages, and a composition-dependent Ms edge that is not honestly tied to that content
# is not composition-dependent at all -- the finding this stage's amendment records. The
# *fitted coefficients* Andrews' formula supplies are a real literature source
# (`flagship_constitutive.forms.KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT`'s own provenance
# states this); this map only carries the *chemistry side* of that claim, and states plainly
# where its own honesty runs out (below).

ANDREWS_SPECIES: tuple[str, ...] = ("carbon", "manganese", "balance")
"""The underlying space for Andrews' two most load-bearing terms (ADR-078 amendment).

Three coordinates, not two: `DescriptorMap`'s simplex (ADR-076 decision 1) is architecture
for the claim that the underlying coordinates sum to one *because together they are the
whole composition*. Carbon and manganese alone do not have that property -- no real steel
is entirely carbon and manganese -- so a simplex over just the two would assert `C + Mn = 1`,
which is false for every composition Andrews' regression was fitted to. `balance` is the
explicit third coordinate that makes the closure claim honest, structural via the simplex
exactly as ADR-076 decision 1 already treats `SPECIES`'s own fourth coordinate: declared,
never computed downstream as `1 - carbon - manganese` by a caller, because that is exactly
the validation-instead-of-architecture CLAUDE.md invariant 5 forbids. `balance` plays no
part in Andrews' formula and is not a declared descriptor below -- see `ANDREWS_DESCRIPTORS`."""

ANDREWS_DESCRIPTORS: tuple[str, ...] = ("carbon", "manganese")
"""The two Andrews terms this toy domain's chemistry can honestly carry (ADR-078 amendment).

Nickel, chromium and molybdenum are declared zero-contribution in
`flagship_constitutive.forms.KOISTINEN_MARBURGER_COMPOSITION_DEPENDENT` rather than covered
here, because nothing in this toy domain's declared chemistry tracks them -- stated plainly
as a smaller-than-full-coverage repair, not disguised as complete Andrews coverage (ADR-078
amendment, third paragraph)."""


def _andrews_evaluate(fractions: FloatArray) -> FloatArray:
    """Identity projection onto the carbon/manganese coordinates, dropping `balance`
    (ADR-078 amendment).

    Not a composite index like `_evaluate` above -- Andrews' formula wants carbon and
    manganese content directly, each with its own coefficient, so the honest functional is
    the simplest one: read the two named fractions off and drop the coordinate the formula
    does not use. This is still a real, falsifiable argument-structure claim in ADR-052's
    sense: holding `carbon`/`manganese` fixed while varying `balance` must leave Andrews' Ms
    unchanged, since the formula does not read `balance` at all, and a report over this map
    would show exactly that.
    """
    return fractions[:2]


ANDREWS_DESCRIPTOR_MAP = DescriptorMap(
    underlying=ANDREWS_SPECIES,
    descriptors=ANDREWS_DESCRIPTORS,
    evaluate=_andrews_evaluate,
    provenance=(
        "Andrews, K.W. (1965), 'Empirical formulae for the calculation of some transformation "
        "temperatures', Journal of the Iron and Steel Institute, 203, 721-727 -- the chemistry "
        "side only (which two coordinates the formula reads); the formula itself, its "
        "coefficients and their own provenance statement live with the constitutive form that "
        "consumes this map, not here. Unlike DESCRIPTOR_MAP above, this is not a toy "
        "functional: the correspondence to real carbon and manganese content is the entire "
        "point, not an incidental resemblance."
    ),
)
"""The declared map from (carbon, manganese, balance) fractions to the two descriptor names
Andrews' formula reads (ADR-078 amendment; Spec §2.2's simplex applied as architecture, ADR-076
decision 1, exactly as `DESCRIPTOR_MAP` above)."""


ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION = 100.0
"""The declared unit correspondence between a simplex fraction and Andrews' weight-percent
convention (ADR-078 amendment's fourth paragraph).

**A simplex fraction is not directly usable as Andrews' wt% input, and the conversion is
exact rather than a toy scaling.** `DescriptorMap.fractions_of` returns true fractions of one
(`carbon + manganese + balance == 1`); Andrews' coefficients are calibrated against
weight-*percent* as it is conventionally quoted in the steel literature -- a composition
stated as "0.20" meaning 0.20 wt% carbon, not 20%. Converting a fraction of one to a percent
is multiplication by 100 by the definition of "percent"; this is not a fitted or declared-
uncertain constant the way this file's other toy parameters are, and is stated as such rather
than bundled in among them.

**What this file does not verify.** Andrews' own fitted composition envelope -- the range of
carbon and manganese content the 1965 regression was actually built from -- is not something
this repository has source access to confirm precisely. `ANDREWS_CARBON_RANGE` and
`ANDREWS_MANGANESE_RANGE` below are a toy range in the general neighbourhood of low-to-medium
alloy engineering steels, stated as an informed but unverified estimate rather than a
citation, on the same honesty this module states for its parameter values generally."""

ANDREWS_CARBON_RANGE: tuple[float, float] = (0.001, 0.02)
"""Toy attainable range for the `carbon` simplex fraction -- 0.1 to 2.0 wt% via
`ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION`, in the general neighbourhood of low-to-medium alloy
engineering steels (informed estimate, not a verified citation -- see
`ANDREWS_WT_PERCENT_PER_SIMPLEX_FRACTION`'s docstring)."""

ANDREWS_MANGANESE_RANGE: tuple[float, float] = (0.001, 0.02)
"""Toy attainable range for the `manganese` simplex fraction -- 0.1 to 2.0 wt%, same
provenance and the same honesty limits as `ANDREWS_CARBON_RANGE`."""


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
