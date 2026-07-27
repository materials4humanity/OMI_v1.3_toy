# SKETCHES.md

Interface-only sketches (Spec §11.4; Core §7.3 — "[Pass D] — a third and
fourth short sketch, interface-only, to test that the interface is fillable
outside both"; ROADMAP M10.1). Core §1.1 claims eight domain families; two
are implemented (`flagship`, `contrast`) and both are physically adjacent
(materials processing, electrochemistry — both metallurgical/electro-
chemical, both apparatus-adjacent industrial processes). The generality
claim rests on the seven-item interface (Core §4) being fillable outside
that pair, and a filled declaration is evidence even with no code behind it
(CLAUDE.md §5 invariant 11) — a sketch that fills too easily proves less
than one that exposes a missing slot, so this document records strain
honestly where it appears rather than smoothing it into a clean fill.

Four sketches, one page each, Core §4's seven items in the Core's own
order: **Device yield** (this document's first entry — chosen to write
first because Class B volume scaling recovering the classical defect-
density model is independent confirmation of Core §3.6/Spec §4's
mathematics from a field with fifty years of practice and no contact with
OMI), **Layer-wise additive processing**, **Crystallisation and
formulation**, and **one deliberately awkward case**, chosen when this
document is extended, specifically to test Core §6.2's open problem —
"whether the four-slot schema is complete, or whether some domain requires
a fifth." Each sketch's Python-side declaration lives in
`src/omi_domains/sketches/<name>.py` (ADR-038, docs/DECISIONS.md); this
document is the prose the ADR requires alongside it, and the two must not
drift — the declaration below is a direct restatement of the code, not a
paraphrase invented independently of it.

`tests/test_sketches.py` diffs each sketch's declaration against
`FLAGSHIP_DECLARATION` and `CONTRAST_DECLARATION` via `omi.interface.diff`
and records every per-item result (`build/observations.json`, the R1.1
convention, CLAUDE.md §7) — the "machine-diffable" half of M10.1's
deliverable. No expected diff pattern is asserted (unlike
`test_interface_diff.py`'s flagship-vs-contrast pin, ADR-034): a sketch
carries no prior claim about how it should compare, only a requirement that
the comparison actually runs.

---

## Device yield

**Why this sketch.** Semiconductor device fabrication has no historical
contact with OMI, is not adjacent to either implemented domain (no
mechanical processing, no electrochemistry), and its central yield model —
Murphy (1964), Stapper (1983): die yield falls with defect density and
critical area, `Y = exp(-D_0 A_c)` in the simplest (Poisson/Seeds) form,
generalised by a negative-binomial clustering correction — is, term for
term, the same construction as Spec §4.1's Class B weakest-link formula,
`P(rho_V > x) = [P(rho_0 > x)]^N` for `N` independent sub-volumes: a die
fails if any one of its independent critical-area sub-regions contains a
killer defect, exactly as a Class B component fails if any one of its
independent sub-volumes contains the worst local configuration. If this
sketch were ever built out with real data, recovering the classical model
from `omi.classb`'s own machinery would be independent confirmation of
Core §3.6/Spec §4's mathematics from a field that derived its yield theory
entirely on its own. This sketch does not perform that recovery — it is
interface-only, per Spec §11.4 — but records the structural correspondence
that motivates writing it first among the four.

**1. State schema.** All four slots occupied, none forced:
- **m** (resolved fields) — `wafer_defect_map` (inline inspection's
  imaged defect map), `layer_thickness_field` (film-thickness/critical-
  dimension map). Both observable by imaging/metrology tools at a stated
  resolution limit, exactly Core §3.1's own description of `m`.
- **z** (sub-resolution internal variables) — `chamber_seasoning_state`
  (the process chamber's wall-conditioning state, which drives particle
  generation rate but is not directly observable — inferable only from
  defect-rate trends across lots, matching Core §3.1's "inferable only
  through dynamics"), `subresolution_particle_density` (particles below
  the inspection tool's detection limit), `cumulative_thermal_budget`
  (the integrated time-temperature history driving dopant diffusion — a
  standard, tracked fab quantity, and the constitutive-operator memory
  term, playing the same role flagship's `accumulated_hardening` plays).
- **ν** (nonlocal/self-consistent field) — `plasma_sheath_potential`: a
  plasma etch/deposition chamber's sheath potential is set by a
  chamber-wide discharge balance, not by any single point in the chamber —
  the same "determined by a global balance, not localised to a point"
  property Core §3.1 requires of `ν`, playing the role residual stress
  plays for flagship and overpotential plays for contrast.
- **Γ** (surface/interface state) — `interlayer_interface_state`: via and
  contact interface roughness/residue, the controlling state for
  interconnect opens, delamination, and initiation-controlled electrical
  failure — not cosmetic, exactly Core §3.1's requirement for this slot.

No slot is empty here, which is itself worth recording rather than treating
as expected: this sketch is not the one chosen to strain the schema (that
is the fourth, deliberately awkward sketch — see the top of this
document). A repository that never found a domain with an empty or
overloaded slot would be as suspicious as one that always did; this entry
is evidence of an ordinary, comfortable fill, not evidence that no domain
could ever strain it.

**2. Control space.** Apparatus-controlled (like flagship, unlike
contrast): deposition/etch/CMP tool setpoints — pressure, RF power, flow
rates, temperature — as time-dependent recipes, one per process step.
`𝒰_adm` is bounded by each tool's qualified process window. A control
(process) inverse exists in the sense Core §4 item 2 asks about: target
yield → recipe is a live, commercially real question in fab process
integration.

**3. Erasure inventory.** `cmp_planarization` — chemical-mechanical
planarization is a genuinely strong-damping step: it removes several
nanometres to microns of topographic variation inherited from the prior
layer, reducing the state's memory of that layer's local height field to a
much lower-dimensional (near-flat) residual, the same qualitative
description Core §3.9 gives an erasure. **Declared, not measured** — this
sketch is interface-only and builds no operator, so unlike flagship's
`HEATING_AND_SOAK` (whose rank and spectrum Phase 3.1 actually measured,
`tests/test_flagship_real_erasure.py`), `cmp_planarization`'s erasure
status here is exactly the state flagship's own declaration was in before
Phase 3.1 measured it — a claim Core §4 item 3 asks a domain to declare,
not yet a result.

**4. Readout catalogue.**
- `parametric_test_mean: Type-0/Class-A` — self-averaging electrical
  parametric measure (e.g. mean threshold voltage) across a wafer or lot.
- `process_step_constitutive: Type-1` — the operator mapping a local
  recipe history to an updated wafer state and step response, the
  homogenisation-facing readout Core §3.5 describes.
- `die_yield: Type-0/Class-B` — process-zone volume = the die's declared
  critical area under its design rule (a fixed, declared quantity, not a
  Type-2 geometry argument varied per call — see item 7). **Item 4b:**
  driver field = the wafer-level defect-density map
  (`subresolution_particle_density` convolved with the
  `plasma_sheath_potential` field's spatial structure); defect population
  = inline inspection's independently measured defect-size distribution
  (SEM/optical wafer scanners measure a heavy right tail in defect size,
  the empirical basis of Stapper's 1983 negative-binomial model); physics
  map `Ψ` = the design's own critical-area function `A_c(x)`, whose
  exponent is read directly off critical-area analysis of the GDSII
  layout — a standard EDA technique — not invented inside `omi.classb`,
  matching the discipline flagship's own `bend_angle` entry set at Phase
  2.2 (`β` read from the constitutive operator's own formula, not chosen
  freely).

**5. Observation suite.** Inline optical/SEM wafer defect inspection
(sampled, not every wafer — inspection throughput cost is a real fab
constraint, unlike flagship's continuous in-die sensing); end-of-line
electrical parametric test; in-situ chamber sensors (particle counters,
optical emission spectroscopy). Rich and multi-modal like flagship's
suite, but with a genuine latency/coverage limitation Core §4 item 5 asks
to be stated: inspection sampling means not every wafer's defect map is
actually observed, only a scheduled subset.

**6. Invariants.** `mass_conservation_across_deposition_and_removal`
(conservation: wafer mass changes only at declared deposition/removal
steps) and `cumulative_thermal_budget_monotone_nondecreasing`
(monotonicity: thermal budget is a standard tracked fab quantity that only
accumulates across a process flow, the same role flagship's
`coating_thickness_monotone_nondecreasing` plays).

**7. Scale structure.** Tier I only: analytic per-die constitutive
response from feature-scale state to die-level response. Critical-area
analysis is treated as a declared, fixed-per-design scalar rather than a
variable Tier I½ geometry parameter the way flagship's `bend_angle` varies
thickness and curvature — this sketch does not need a Tier I½ extension to
state its Class B claim, unlike flagship's bend-angle campaign. Full 3D
TCAD process simulation, or treating the layout itself as a variable Tier
II geometry, remain anti-goals per CLAUDE.md §9.

**Machine-diff status.** See `tests/test_sketches.py` and
`build/observations.json` for the per-item comparison against
`FLAGSHIP_DECLARATION`/`CONTRAST_DECLARATION`; no pattern is asserted, only
recorded.

---

*(Layer-wise additive processing, Crystallisation and formulation, and the
deliberately awkward fourth sketch are scheduled next per ROADMAP M10.1 and
are not yet written.)*
