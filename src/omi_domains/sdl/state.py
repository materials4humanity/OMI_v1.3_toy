"""The discovery domain's state schema (Core §4 item 1; ADR-060).

A supported heterogeneous catalyst formulated from a multi-metal precursor solution,
calcined, and then evaluated for activity. Chosen as the third domain because its
**control axis is a third kind**: flagship's is apparatus-determined (an operator sets a
route), contrast's is usage-determined (service sets a duty cycle), and this one is
**acquisition-determined** — an agent chooses what to make next. That is the third
decision kind, and it is what makes composition the primary designed variable rather than
a fixed index.

Slot occupancy, and why each:

- `m` — resolved fields: dispersed-phase loading and mean particle size, the two
  quantities a characterisation of the calcined material actually resolves.
- `z` — sub-resolution internal variables: active-site density and a defect-site
  fraction, which govern turnover and are not resolved by any declared modality.
- `ν` — nonlocal: pore-network accessibility. It has **no local value**: whether a site
  is reachable is a property of the whole connected network, not of a point, which is
  Core §3.1's own reason for carrying `ν` separately and E-22's `GLOBAL_POINT` case.
- `Γ` — surface and interface state: support-interface coverage and a surface
  reconstruction index.

**Composition is deliberately not in the schema.** The mean composition indexes the
operator family and is transported by nothing — ADR-051's Parameter role, realised as
ADR-049's `INVARIANT` coupling on item 1's refinement. Putting it in a slot would type a
fixed index as a state, which is precisely the mis-typing `docs/V1.4-EDITS.md` E-46
separates: what the material *is* versus what the operator family is *parameterised by*.
"""

from __future__ import annotations

from omi.state import Slot, StateSchema

SDL_SCHEMA = StateSchema(
    (
        (Slot.M, "dispersed_phase_loading", 1),
        (Slot.M, "mean_particle_size", 1),
        (Slot.Z, "active_site_density", 1),
        (Slot.Z, "defect_site_fraction", 1),
        (Slot.NU, "pore_network_accessibility", 1),
        (Slot.GAMMA, "support_interface_coverage", 1),
        (Slot.GAMMA, "surface_reconstruction_index", 1),
    )
)

SPECIES = ("metal_a", "metal_b", "promoter", "support")
"""The underlying composition space: atomic fractions, constrained to a simplex.

Named generically rather than by element, because the declaration's content is the
**role structure and the attainable region**, not a particular chemistry — and naming
specific elements would imply a calibration this toy does not have (the same discipline
`flagship_constitutive.forms` states for its parameter values)."""

REGIONS = ("bulk", "surface_layer")
"""The two declared regions roles attach to (ADR-051). Two rather than one because the
central claim of per-region roles is only exercised where a species holds different roles
in different regions of the same chain, and one region cannot exhibit it."""

DESCRIPTORS = ("valence_electron_count", "mixing_enthalpy", "support_acidity")
"""The descriptor basis composition is declared in (ADR-052): named functionals of
:data:`SPECIES`, carried alongside the fractions rather than instead of them.

Each makes a falsifiable claim about argument structure — "the rate law depends on
chemistry only through these" — testable by holding out a formulation that varies the
fractions at fixed descriptors."""
