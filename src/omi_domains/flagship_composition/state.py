"""The composition variant's state schema (Core §4 item 1a; ADR-050, ADR-076).

Flagship's seven components, **plus one**: a sub-resolution composition quantity in `z`.
Core §3.1's `z` is "path-dependent quantities below imaging resolution... not observable
directly; inferable only through dynamics", which is what unresolved solute redistribution
is.

**What the occupant is, stated precisely, because a looser reading makes the constancy
residual vacuous.** It is the **domain-mean deviation** of the sub-resolution fluctuation
from the declared `c̄` — one scalar functional of `δc(x)`, not the field. For a *closed*
domain it is zero and stays zero, because redistribution inside a closed boundary moves
nothing across it; for an *open* domain it drifts by the boundary flux. That is exactly the
quantity ADR-050's conservation argument constrains, and it is why the residual is computed
over it rather than over `c̄` (which is a parameter, trivially constant, so a residual over
it would measure nothing).

**The full `δc(x)` field is not represented, and that is a scope statement rather than an
omission.** Representing it needs a `FIELD` declared domain, which ADR-049 refuses citing
`C-2.5`, so ADR-050's scope line applies: sub-resolution in `z` now, resolved bands
declarable and unimplemented. ADR-076 decision 4 records why that costs this declaration
nothing it was entitled to claim at SVE scale, and `docs/COMPOSITION-BRIEF.md` records what
it does cost.
"""

from __future__ import annotations

from omi.state import Slot, StateSchema

COMPOSITION_SCHEMA = StateSchema(
    (
        (Slot.M, "prior_deformation", 1),
        (Slot.M, "prior_grain_size", 1),
        (Slot.Z, "substructure_density", 1),
        (Slot.Z, "inclusion_content", 1),
        (Slot.Z, "accumulated_hardening", 1),
        (Slot.Z, "unresolved_solute_mean_deviation", 1),
        (Slot.NU, "levelling_field", 1),
        (Slot.GAMMA, "coating_thickness", 1),
    )
)
"""Eight components: flagship's seven plus `unresolved_solute_mean_deviation`.

`flagship`'s own `FLAGSHIP_SCHEMA` is **untouched** — a separate schema in a separate
package, which is what keeps every pre-existing observation byte-identical (ADR-075
Decision 2)."""

SUBSTRUCTURE_INDEX = 2
DELTA_C_MEAN_INDEX = 5
"""Flat-array indices this package's operators address positionally, stated as constants
for the reason `flagship.operators` states its rate vector positionally: the schema's order
fixes the layout (ADR-011)."""
