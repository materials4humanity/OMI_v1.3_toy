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

## Layer-wise additive processing

**Why this sketch.** Metal powder-bed-fusion additive manufacturing (laser
or electron-beam powder bed fusion) is chosen because it exercises "hybrid
structure and body-indexed state at their most extreme" (docs/ROADMAP.md
M10.1): the process is a textbook hybrid system (Core §3.4 — continuous
melt-pool evolution within a layer, punctuated by discrete recoat/new-layer
events), and its state is a field over a body that is itself under
construction, one layer at a time — more extreme than Core §2.5's own
framing usually envisions (a fixed body indexed by material coordinate),
since here the body's spatial extent is growing during the very process
being modelled. **This sketch does not fill cleanly**, and the strain is
recorded here rather than smoothed over, per this document's own opening
paragraph.

**1. State schema — the item that strains.** `omi.state.StateSchema`
(ADR-011, docs/DECISIONS.md) is a flat, finite-dimensional vector. It can
declare one representative build location's state — the same Tier I move
flagship, contrast, and the device-yield sketch all make — but it cannot
express that this domain's actual state is a field over a growing body.
`src/omi_domains/sketches/layerwise_additive.py`'s `LAYERWISE_ADDITIVE_SCHEMA`
is exactly that forced approximation, not a genuine fill:
- **m** — `local_melt_pool_geometry` (in-situ camera's melt-pool
  descriptor), `layer_surface_roughness_field` (recoated-layer surface
  topography). Point-valued fine, at one location.
- **z** — `subsurface_porosity_density` (sub-resolution until post-build
  CT — "inferable only through dynamics," exactly Core §3.1's own
  description), `local_thermal_history_moments` (constitutive-operator
  memory: cumulative reheating from subsequent layers' passes at this
  location).
- **ν** — `part_scale_residual_stress_field`: whole-part residual stress
  and thermal state, set by a global heat-conduction balance across the
  whole build and the build plate — not localisable to a point, exactly
  Core §3.1's requirement for this slot. **This is the slot where the
  approximation costs the most**: whole-part distortion and warpage is
  often this domain's dominant commercial failure mode, and it is
  *definitionally* a whole-body quantity, more centrally so than either
  implemented domain's own nonlocal field (flagship's `levelling_field`,
  contrast's `potential`/`concentration_overpotential`) — those matter,
  but neither domain's *dominant* slot (Core §7.1/§7.2 both name `m`/`z`
  or `Γ` as dominant, not `ν`) is the one Tier I's point-valued treatment
  most damages. Here it is.
- **Γ** — `interlayer_bond_state`: bond quality between the current and
  previous layer, controlling delamination and interlaminar fracture —
  not cosmetic, exactly Core §3.1's requirement.

Declaring this schema as *the* state, full stop, silently reverts the
domain to Tier I and discards exactly the physics that makes this domain
commercially hard. See `docs/V1.4-EDITS.md` E-21 for the resulting
framework finding: Core §4 item 1 does not currently ask a domain to
declare whether its state is point-valued or requires body-indexing, so an
instantiation attempt can under-declare a genuinely field-valued domain
without anything in item 1 flagging it — this sketch is the second,
independent piece of evidence (after E-14's Class-B-validation finding)
that Core §2.5's `[Pass C]` status blocks more than one thing.

**2. Control space.** Apparatus-controlled: laser/beam power, scan speed,
hatch spacing, layer thickness as a time-dependent recipe across the whole
build, with discrete layer-boundary events (recoat, new-layer start) as
points of discontinuity within that one programme. Core §3.2's control
space already admits an arbitrary function of time, so — unlike item 1 —
this item fills without needing the hybrid/jump-map machinery of Core §3.4
(anti-goal, CLAUDE.md §9) to be built: one long, highly discontinuous
control function over the whole build suffices to *declare* the item,
even though *simulating* it faithfully would need mode-labelling. `𝒰_adm`
is bounded by the machine's qualified process window. A control (process)
inverse exists: target part quality/density → recipe.

**3. Erasure inventory.** `hot_isostatic_pressing` (HIP) — a genuine,
strongly damping post-build step that closes internal porosity under
combined heat and pressure. Unlike flagship's `heating_and_soak`
(mid-chain) or the device-yield sketch's `cmp_planarization` (mid-chain),
HIP is **terminal**: during the build itself, defects tend to *compound*
rather than erase (layer-to-layer stress concentration, propagating
lack-of-fusion), so condition (a) of Core §3.9's error-control dichotomy is
not satisfied mid-build. Condition (b) is weak too during the build — the
richest observation (post-build CT, item 5) is not available until the
build is already finished. This domain's error control comes almost
entirely from the terminal HIP + CT combination, not from anything
continuous during the process — worth stating explicitly, since it is a
genuinely different profile from every domain and sketch so far.

**4. Readout catalogue.**
- `final_density_mean: Type-0/Class-A` — self-averaging bulk density
  (e.g. Archimedes measurement).
- `melt_pool_constitutive: Type-1` — local thermal-mechanical constitutive
  operator, local scan parameters → local response + updated local state.
- `porosity_induced_fatigue_life: Type-0/Class-B` — process-zone volume =
  the *completed* part's volume. Unlike item 1's build-time state, this
  readout is only ever evaluated post-build, so its volume is fixed at
  evaluation time — the growing-body concern above is specific to the
  build-time state, not to this readout. **Item 4b:** driver field = the
  built part's internal pore size/location field; defect population =
  independently measured pore-size distribution from post-build X-ray CT
  (standard AM qualification practice; lack-of-fusion pore sizes are
  heavy-tailed); physics map `Ψ` = a fracture-mechanics defect-size-to-
  fatigue-limit relation (Murakami's `√area` model), exponent read
  directly from that published model, not invented inside `omi.classb`.

**5. Observation suite.** In-situ melt-pool monitoring (photodiode/camera,
per layer); layer-wise optical imaging of the recoated surface; post-build
X-ray CT. The CT scan is rich but available only once, after the build is
already complete — too late to correct anything during the build, unlike
every other domain and sketch declared so far (flagship's/contrast's/
device-yield's observations all arrive during their respective processes).
This is a genuinely different temporal-availability profile Core §4 item 5
("latency and coverage") is well suited to state, and this sketch is the
first case in this repository where it matters this much.

**6. Invariants.** `mass_conservation_across_melting_and_solidification`
(conservation: powder mass becomes part mass, minus spatter/evaporative
losses) and `cumulative_build_height_monotone_nondecreasing`
(monotonicity: build height only grows as layers are added — physically
obvious, not manufactured to fit the taxonomy).

**7. Scale structure — the second item that strains, same root cause as
item 1.** Tier I only, as declared: one representative location's analytic
melt-pool response. But the domain's dominant mechanism — whole-part
residual-stress accumulation and distortion, carried in `ν` — is
fundamentally Tier II/body-indexed (Core §2.5, `[Pass C]`), and the scale
separation a homogenisation step would need to bridge (melt-pool scale,
microseconds and microns, to whole-part scale, hours and the full build)
is far wider than flagship's SVE-to-component bridge. Full Tier II remains
an anti-goal per CLAUDE.md §9.

**Machine-diff status.** See `tests/test_sketches.py` and
`build/observations.json`; no pattern is asserted, only recorded — this
sketch's Tier I schema still diffs mechanically against
`FLAGSHIP_DECLARATION`/`CONTRAST_DECLARATION` even though it is a forced
approximation on item 1, since `omi.interface.diff` compares whatever
`StateSchema` object it is given, not whether that object is a faithful
representation of the domain.

---

## Crystallisation and formulation

**Why this sketch.** Batch cooling/antisolvent crystallisation, chosen per
ROADMAP M10.1 for "polymorph selection as a bifurcating evolution operator,
dissolution as a Class B readout" — and written third, deliberately,
because Core §3.1 names *supersaturation* as its own worked example of
`ν`, and this domain's headline phenomenon (polymorph selection) is itself
supersaturation-driven (classical nucleation theory; Ostwald's rule of
stages). E-21/E-22 (docs/V1.4-EDITS.md) predicted `ν` would plausibly be
dominant here too, on physics with nothing in common with either metal
processing (flagship, device yield, layer-wise additive) or
electrochemistry (contrast). **The prediction holds** — see item 1 below
and E-22's addendum.

**1. State schema.** All four slots occupied, none forced:
- **m** — `particle_size_distribution_moments` (bulk PSD summary, laser
  diffraction), `crystal_habit_descriptor` (aspect ratio/morphology,
  imaging). Point-valued fine, matching every other domain's `m`.
- **z** — `subcritical_nuclei_density` (below detection limit; "inferable
  only through dynamics," Core §3.1's own phrase, exactly the induction-
  time-dependent nucleation-rate inference this domain actually uses),
  `crystal_defect_density` (dislocation/inclusion accumulation, the
  constitutive-operator memory term).
- **ν** — `supersaturation`: Core §3.1's own named example. In the
  well-mixed idealisation common to batch crystallisers, supersaturation
  is not merely a field satisfying a global PDE (as flagship's residual
  stress and layer-wise additive's part-scale stress are) — it collapses
  further, to a **single shared scalar** for the whole vessel, since every
  growing crystal draws from the same mother-liquor solute reservoir and
  no crystal's local growth model can account for how much solute remains
  without reference to what every other crystal has already consumed.
  This is, if anything, a *purer* instance of "pointwise evolution
  operators cannot own them" (Core §3.1) than either previous domain's
  `ν`: residual stress at least has *a* value at each point (just one
  that depends on the whole body); the well-mixed limit of supersaturation
  does not even have a meaningful local value to approximate. In an
  imperfectly-mixed real vessel, supersaturation reverts to a genuine
  spatial field with the same globally-coupled structure as the other two
  domains' `ν` — both regimes are worth naming, since real industrial
  crystallisers sit at different points between them.
  **`ν` is plausibly this domain's dominant slot**, confirming E-21's
  prediction on a third, structurally unrelated domain: polymorph
  selection — the phenomenon this sketch exists to test — is itself
  governed by supersaturation level via the relative nucleation barriers
  of competing polymorphs, more centrally than layer-wise additive's `ν`
  governed distortion (a real but secondary commercial concern there).
- **Γ** — `crystal_surface_state`: surface defect/roughness state,
  controlling both dissolution rate (this domain's own declared Class-B
  readout, item 4) and further growth/agglomeration — not cosmetic,
  matching Core §3.1's requirement and echoing flagship's own
  Γ→adhesion coupling.

**Bifurcation does not strain the interface.** Polymorph selection near
the metastable-zone boundary is a genuine bifurcation: a small
perturbation in supersaturation or seeding selects a qualitatively
different polymorphic outcome, with very different downstream properties
(solubility, stability, bioavailability). This does not require anything
beyond `S × 𝒰 → S` (or its ensemble lift) to represent — a bifurcating map
is still just a map, highly sensitive in a narrow region — and Core §3.9
already names this exact case directly: "Where dynamics are genuinely
expansive... a better surrogate is not the answer... predict the
invariant or **the bifurcation label** rather than the trajectory." This
sketch is the clearest real-world instance of that clause found in this
repository so far, not a gap in it — recorded here as a confirming
observation, not escalated to `docs/V1.4-EDITS.md`, since Core's text
already anticipates it in full.

**2. Control space.** Apparatus-controlled: cooling-rate profile,
antisolvent addition rate, seeding schedule as a time-dependent recipe.
`𝒰_adm` bounded by the crystalliser's equipment limits. A control
(process) inverse exists: target polymorph/particle-size distribution →
recipe, a live crystallisation-process-design problem.

**3. Erasure inventory.** `full_dissolution_recrystallization` — fully
dissolving the crystalline material and recrystallising under controlled
conditions genuinely erases prior crystal history (habit, defect
structure, even polymorph), a strong contractive erasure comparable in
role to flagship's `heating_and_soak`. Unlike device yield's
`cmp_planarization` or layer-wise additive's `hot_isostatic_pressing`
(both terminal, post-process), this erasure is naturally **mid-chain** —
usable as an intermediate reprocessing step, or as the very first step
(dissolving raw starting material before crystallising). Combined with
item 5's genuinely rich, real-time observation suite (below), this domain
plausibly satisfies **both** conditions of Core §3.9's error-control
dichotomy robustly, the same profile as flagship — on completely
unrelated physics. Useful confirming evidence that flagship's profile
(real erasure + rich sensing) is not a metallurgy-specific artefact.
Contrast with layer-wise additive (E-23): that domain's only erasure and
richest observation are *both* terminal, so neither condition holds
mid-chain in practice — this sketch shows the opposite is equally
possible on unrelated physics, i.e. the dichotomy's profile is not
domain-family-clustered.

**4. Readout catalogue.**
- `bulk_yield_mean: Type-0/Class-A` — self-averaging total
  crystallised yield/purity across a batch.
- `crystal_growth_constitutive: Type-1` — supersaturation and
  temperature → growth rate + updated local crystal state, the classical
  crystal-growth-kinetics operator.
- `dissolution_time_to_90pct: Type-0/Class-B` — process-zone volume =
  the *finished* batch's particle population, fixed at evaluation time
  (dissolution testing runs on an isolated, dried sample, not the growing
  in-process population — the same "fixed at evaluation, not at
  build/process time" pattern device yield's critical area and
  layer-wise additive's fatigue life both already established). **Item
  4b:** driver field = local particle-surface dissolution flux, correlated
  with the particle-size-distribution field; defect population =
  independently measured particle-size distribution (laser diffraction;
  heavy-tailed coarse fraction); physics map `Ψ` = Noyes-Whitney/
  Hixson-Crowell dissolution kinetics (dissolution time ∝ particle
  radius²for diffusion-limited dissolution), exponent read directly from
  that textbook model, not invented inside `omi.classb` — the same
  discipline as every prior domain's item 4b.

**5. Observation suite.** In-line FBRM (focused beam reflectance,
real-time particle count/chord-length), in-line Raman/NIR spectroscopy
(real-time polymorph identification *and* supersaturation monitoring —
directly observing the dominant slot, unlike either prior sketch), at-line
laser diffraction (particle size distribution). This is the richest,
most continuous, most genuinely *real-time* observation suite of any
domain or sketch so far — crystallisation is one of the pharmaceutical
industry's most PAT (process analytical technology)-instrumented unit
operations, precisely because real-time supersaturation control is the
lever that determines polymorphic outcome. A sharp contrast to layer-wise
additive's strictly terminal richest observation (E-23).

**6. Invariants.** `solute_mass_conservation_across_crystallisation`
(conservation) and `cumulative_crystallised_mass_monotone_nondecreasing`
(monotonicity). **One honest scoping note**: this domain's own declared
erasure (`full_dissolution_recrystallization`) is precisely a controlled
violation of the monotonicity invariant when invoked — crystallised mass
genuinely drops back toward zero on dissolution. This is not a
contradiction: the invariant holds *between* erasures, not across the
whole chain unconditionally, the same way any domain's monotonicity
invariant should be read as scoped to the segment it actually governs.
Worth stating explicitly here since this is the first domain or sketch in
this repository whose own declared erasure directly targets the same
physical quantity one of its own invariants governs.

**7. Scale structure.** Tier I only: a single representative-batch,
well-mixed-limit population-balance-style state (classical
supersaturation-driven growth/nucleation kinetics) — a natural, commonly-
used industrial idealisation, unlike layer-wise additive's Tier I
stand-in (which discards a dominant physical mechanism rather than
merely coarsening it). Tier II (spatially-resolved CFD-coupled population
balance, capturing genuine within-vessel supersaturation gradients)
remains an anti-goal per CLAUDE.md §9.

**Machine-diff status.** See `tests/test_sketches.py` and
`build/observations.json`; no pattern is asserted, only recorded.

---

*(The deliberately awkward fourth sketch, chosen specifically to attack
Core §6.2's open "does some domain need a fifth slot" question, is
scheduled next per ROADMAP M10.1 and is not yet written.)*
