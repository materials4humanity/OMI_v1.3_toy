# PHYSICS-ADEQUACY.md — a domain assessment of OMI v1.3

**Is this framework adequate to the physics it claims to model?**

Assessed from flat-rolled steel processing, with every finding tested for
whether it is steel-specific or general to PSR systems.

**Status: live document under CLAUDE.md §10.** All six §3 findings were
verified against the source at M10.4 (2026-07-29). Each carries a
**Verification** block stating the outcome — confirmed, partly confirmed, or
refuted — with the code or framework citation that settles it. Confirmed
findings are filed in `docs/V1.4-EDITS.md` as E-29 to E-33, marked
`[domain-assessment]` to keep their provenance distinct from the thirty-six
entries found by implementation attempt. Refuted claims are recorded here,
under the finding, and are *not* filed. This document is corrected in place as
findings are settled; it carries no commit stamp and is not a snapshot.

**§3.4 was re-settled at M11.5 and its central claim is now refuted as stated.**
It was this document's own "most important finding", it named the experiment that
would test it, that experiment was built and run across M11.4 and M11.5, and the
answer went against it — see the two correction blocks and the second verification
inside §3.4, and `docs/M11-RECORD.md` for the full account. The section is
corrected in place rather than withdrawn: what it says about the *absence* of the
category stands and was strengthened; what it says about the category *delivering
reach* does not.

---

## 0. What this document is, and how it differs from `V1.4-EDITS.md`

`V1.4-EDITS.md` asks whether the framework is *internally coherent*: does a
section contradict another, is a marker stale, can a declaration be satisfied
without the property it exists to establish. Forty-three entries, and they
hold regardless of what physics instantiates the framework.

This document asks a different question: **is the framework adequate to the
physics?** A framework can be perfectly self-consistent and still lack the
structure a domain needs. Nothing in the ledger would catch that, because
nothing in the ledger reads the framework against a physical system it
claims to describe.

The two documents can disagree without either being wrong. `V1.4-EDITS.md`
E-22 concludes the four-slot schema is complete in count and wrong in the
type of one slot. This document reaches the same conclusion on count by a
different route — and adds that a whole *class* of quantity has no home in
the schema at all, which the internal-coherence audit had no way to see.

**Every finding below carries a generalisation verdict.** Flat-rolled steel
is the worked case because it is the flagship domain and the framework's own
worked example. But a framework claiming eight domain families cannot be
assessed against one, so each finding states whether it is steel-specific,
general, or general-but-manifesting-differently, with the reasoning shown.

---

## 1. The toy cannot answer the question, and the reason matters

Before anything else: **flagship cannot test whether OMI extrapolates.**
Not because it is small, but because of what it is made of.

Every evolution operator in flagship is a closed-form analytic function
chosen by this build (ADR-001). Extrapolating outside a training envelope on
that domain tests whether a surrogate recovers a function someone wrote
down. Real extrapolation asks whether the framework's structure buys you
reach on a system nobody wrote down. These are different questions and only
the second matters industrially.

The failure mode is specific and worth naming, because it explains the
M10.2 result. **An analytic operator is smooth and globally valid by
construction. Real metallurgy is neither.** Hardness after continuous
annealing is not a smooth function of soak temperature — it has a knee where
recrystallisation completes and another where austenite forms, and the
position of those knees is what a mill actually needs. Flagship's readouts
were near-affine over the swept range, which is why ridge regression won 16
of 18 configurations. That result is honest about flagship and says nothing
about steel.

Sharper still: **the toy's physics cannot be wrong in the ways real physics
is wrong.** A model of invented physics can be inaccurate but never
*mechanistically incomplete* — there is no unmodelled mechanism waiting
outside the envelope, because the envelope contains everything by
construction. Mechanistic incompleteness is the dominant extrapolation
failure in real materials modelling, and flagship cannot exhibit it.

*Generalisation:* **general, and it applies to every synthetic domain.** A
semiconductor toy with an analytic diffusion law has the same defect. The
point is not about steel; it is that analytic domains can validate
estimators (which they did, well) and cannot validate extrapolation claims.

---

## 2. What the framework gets right

Credit first, because these are not small and they generalise well.

**Evolution/readout separation is the correct ontology.** Hardness is not a
property of a recipe; it is a readout of a state a recipe produced. Any
metallurgist who has watched two coils on identical setpoints come out
different already believes this. Most materials informatics does not model
it — tabular PSPP maps setpoints to properties and the state disappears.

*Generalisation: universal.* Device threshold voltage is a readout of a
dopant-and-defect state, not of an implant recipe. MOF uptake capacity is a
readout of pore structure and defect density, not of a synthesis protocol.

**The extended state, and the claim that an image is not sufficient.** `z`
carrying back stress and dislocation-population partitioning is what makes
springback, the Bauschinger effect, and bake-hardening predictable at all.
The framework's insistence that **an EBSD map is not a sufficient state** is
a claim most of the field quietly violates.

*Generalisation: universal, and often stronger elsewhere.* In heterogeneous
catalysis the active-site speciation that governs turnover is almost always
sub-resolution. In MOFs, missing-linker and missing-cluster defects control
catalytic and sorption behaviour and are largely invisible to PXRD. The `z`
slot is arguably more load-bearing in those fields than in steel.

**Erasure as a composability argument.** Every metallurgist knows
austenitisation erases cold-work history. Nobody had said: *therefore your
model error does not propagate past it, and that is where to modularise the
chain.* Turning a known metallurgical fact into an error-control argument is
a genuine contribution.

*Generalisation: general but unevenly distributed.* Semiconductor processing
has strong erasures — a high-temperature anneal erases implant damage; epi
growth resets surface state. MOF synthesis is nearly erasure-free: defects
introduced at nucleation persist. Battery service has none, which is exactly
why Core §7.2 chose it as the contrast. The framework's own dichotomy
(erasure *or* observation density) is the right way to carve this and is one
of its better ideas.

**Class A / Class B, and the process-zone volume.** Edge cracking, hydrogen
embrittlement and bendability really are governed by the worst inclusion in
the loaded volume, and treating them as RVE readouts really is a modelling
error people make constantly. The prediction that rankings invert between
gauges is something your customers have complained about.

*Generalisation: universal, and it is the framework's most transferable
idea.* Semiconductor yield is the classical weakest-link problem — the
defect-density yield model is a Poisson weakest-link statement, and it would
be worth confirming that OMI's volume scaling recovers it (Spec §11.4 already
proposes this sketch). Dielectric breakdown, MOF crystal fracture during
pelletisation, and fibre-composite failure are all Class B.

**Open prediction (M10.4): the defect-density recovery has NOT been
computed, anywhere.** A second external assessment states that the Class B
treatment "recovers classical defect-density yield models as a special
case." Checked: it does not, yet. Spec §11.4 *proposes* the recovery
("device yield (where Class B volume scaling recovers the classical
defect-density model, an independent confirmation of §4's mathematics)"),
`docs/ROADMAP.md` M10.1 repeats it as an expectation, and
`docs/SKETCHES.md`'s Device Yield section argues the structural
correspondence term by term — `Y = exp(-D₀A_c)` in the Poisson/Seeds form,
negative-binomial under clustering, against Spec §4.1's
`P(ρ_V > x) = [P(ρ₀ > x)]^N` — while stating in as many words that "this
sketch does not perform that recovery." `src/omi_domains/sketches/
device_yield.py` is interface-only by ADR-038, and
`tests/test_sketches.py` checks only that the declaration is well-formed
and diffs against the two implemented domains. No Poisson or
negative-binomial yield expression is computed in `src/` or `tests/`
(`grep -i "poisson\|negative.binomial"` over both finds nothing but this
sketch's own prose). **So the recovery is an open prediction, not a
result, and MUST NOT be cited as demonstrated.**

It is worth doing and it is cheap. `omi.classb.n_eff` in the bulk regime
already gives `V/ℓ_D³`, and the yield model's critical-area form is the
same construction at `ℓ_D → 0` with `N = A_c/a₀`; a recovery test would
assert that `omi.classb`'s own machinery reproduces `exp(-D₀A_c)` in the
uncorrelated limit and the negative-binomial form under a declared
clustering correlation length, with no yield-specific code added. That
would be independent confirmation of Core §3.6 / Spec §4 from a field that
derived the same mathematics on its own, sixty years ago, with no contact
with this framework — the strongest kind of evidence the generality claim
can get, and stronger than any sketch, because the target answer was fixed
by someone else before this framework existed. It is recorded here rather
than in `docs/V1.4-EDITS.md` because a confirmation-in-waiting is not a
framework defect; if the recovery were attempted and **failed**, that
would be a ledger entry, and a serious one.

---

## 3. Where the framework is inadequate to the physics

Six findings. None appears in `V1.4-EDITS.md`.

### 3.1 Composition has no home in the schema

**Steel.** Chemistry is set at the caster and never evolves in the bulk, but
it parameterises every operator downstream: hardenability sets the CCT
diagram, carbon sets Ms, microalloying sets precipitation kinetics and
recrystallisation-stop temperature. In the four-slot schema, composition sits
in `m` as "composition fields," where it is inert — evolved by nothing,
carried by every operator, and indistinguishable from state that genuinely
changes.

This is why "transfer of evolution operators across composition families" is
listed in Core §6.2 as an open problem. It is open because the schema has no
way to say *this quantity parameterises the operator rather than being
transported by it*. A transformation operator for DP600 and one for DP980 are
not two unrelated operators; they are one operator at two parameter values,
and the framework cannot express that.

Note the wrinkle that makes this more than a labelling issue: **the same
chemical species is a parameter in the bulk and a state at the surface.**
Carbon is fixed in the bulk and evolving in the decarburised layer; aluminium
and silicon are fixed in the substrate and evolving in the coating interlayer.
So "composition is a parameter" is true only relative to a region, and `Γ` is
where it becomes state.

**Generalisation: general, with a domain-dependent boundary.** Semiconductors
are the interesting case — dopant identity is a parameter, but dopant
*profile* genuinely evolves under thermal budget, so the same quantity is
parameter and state at different stages of the same chain. MOF linker and
node chemistry are pure parameters, fixed at synthesis, defining the
topology every subsequent operator acts on. Polymer monomer sequence is a
parameter; molecular-weight distribution is state that evolves under
degradation.

The general statement: **the framework needs to distinguish evolving state
from static parameterisation, and where a quantity falls depends on the
chain's timescale and region.** A fifth slot is the wrong fix — this is not
state. The right fix is a declared parameter set in the instantiation
interface, with operators explicitly parameterised by it.

**Minimal test in the toy.** Add a scalar composition parameter to flagship,
give two "grades" differing only in it, train an operator on one and test
transfer to the other. If the operator is chemistry-*parameterised* it should
transfer with a handful of samples; if chemistry is buried in `m` it will not
transfer at all. That is a direct, cheap test of Core §6.2's open problem.

**Verification (M10.4). CONFIRMED at framework level; one specific claim
corrected; one strengthening.** Filed as `docs/V1.4-EDITS.md` **E-29**, which
also absorbs §3.7 — the two are one finding at two levels, and E-29 states the
framework claim as **detectability**: nothing distinguishes "static by design"
from "should evolve but does not", so a readout depending only on parameters
cannot be flagged structurally. §3.7's flagship defect is the worked example of
what that costs, recorded inside E-29 as a marked repository fault.

- Core §3.1 does place composition in a state slot: `m` is "resolved
  structural fields. Order parameters, indicator fields, orientation fields,
  **composition fields**, geometric descriptors…" — confirmed verbatim.
- Core §4's seven items contain no parameter declaration; the shared
  declaration object has exactly seven fields (`state_schema`, `control_space`,
  `erasure_inventory`, `readout_catalogue`, `observation_suite`, `invariants`,
  `scale_structure`). `StateSchema` declares components as `(Slot, str, int)`
  triples with **no field marking a component static**. Confirmed.
- Core §6.2's open problem does use the missing word — "composition-conditional
  versus composition-**parameterised**". Confirmed.
- **Corrected**: flagship declares *no composition field at all*. "Composition
  sits in `m` as composition fields, where it is inert" describes Core §3.1's
  schema definition, not flagship's instantiation; flagship's nearest
  composition-like quantity, `inclusion_content`, sits in `z`. The
  flagship-specific illustration should not be cited.
- **Strengthened**: flagship already has *three* de-facto-static components —
  `prior_grain_size`, `inclusion_content`, `accumulated_hardening`, each with
  relaxation rate exactly `0.0` **and** control-coupling gain exactly `0.0` in
  both of its evolution operators. Carried by every operator, evolved by none,
  structurally indistinguishable from `prior_deformation` (rate `5.0`). The
  predicted pathology is present; it is simply not in the component predicted.
  These are also exactly the three components flagship's readouts read, which
  is §3.7's defect — see there.

### 3.2 Anisotropy and group structure are absent

**Steel.** Texture is in the state. But `ℓ_D` is a scalar, the state metric
is Euclidean on scaled components (ADR-002), and no directional structure
appears anywhere in the framework. For flat-rolled product this is not a
detail: r-value anisotropy governs deep drawing, banded segregation is
directional by construction, and bendability differs between rolling and
transverse directions routinely enough that specifications call it out
separately.

Spec §4.4 *does* require a directional `ℓ_D` for banded structures. ADR-027
declined it. That is the largest single physics gap in the build, and it is
in the one place the specification was already correct.

The deeper issue is structural, not a missing feature. **Spec §2.2 prescribes
symmetry-equivariant architectures, but the state space and its metric carry
no group action.** If two states differ by a rotation of the texture, the
declared metric reports them as distant. A metric that does not respect the
symmetry group of the state cannot support an equivariant operator on it,
so the framework's own symmetry prescription is disconnected from its own
state definition.

**Generalisation: universal, and more central in several domains than in
steel.** Semiconductors: wafer orientation determines etch rates, carrier
mobility, and strain response — anisotropy is the design variable. MOFs:
pore-channel directionality separates 1D from 3D networks and dominates guest
diffusion; several MOFs have negative thermal expansion along one axis.
Battery electrodes: through-plane versus in-plane tortuosity governs rate
capability. Additive manufacturing: build-direction anisotropy is the field's
central problem.

I cannot construct a PSR system where anisotropy is safely ignorable. The
scalar treatment should be regarded as a simplification the framework has not
declared, not as generality.

**Minimal test in the toy.** Give flagship a two-component texture descriptor
and a directional `ℓ_D`; declare bend angle in RD and TD as separate readouts.
If the Class B machinery cannot express that the two share a state but differ
in process-zone correlation structure, the gap is demonstrated concretely.

**Verification (M10.4). CONFIRMED on both halves; one supporting claim
refuted.** Filed as `docs/V1.4-EDITS.md` **E-30**, scoped to the
group-declaration and metric halves only.

- `ℓ_D` is scalar structurally, not by convention: the correlation-length
  estimator raises `ValueError` on any non-1-D driver field, and the
  weakest-link-count consumer takes `correlation_length: float`. Confirmed.
- Spec §4.4's Requirements block does carry the directional requirement,
  verbatim: "Anisotropic correlation (banded structures) requires a directional
  `ℓ_D` and reduction along each suppressed axis independently." Confirmed.
- The state metric has exactly two fields — a schema and a per-component scale
  vector — and computes a scale-normalised Euclidean norm. Demonstrated
  directly: two states related by a 90° rotation are reported at distance
  `1.414`, not `0`. No group action, no quotient, no non-diagonal form is
  representable. Confirmed.
- Nothing in `src/omi/` carries a symmetry group. Every "direction" in the
  module is an eigendirection of a covariance or Gramian matrix, or the
  forward-versus-reversed *driving* direction (a time-reversal sense).
  Confirmed.
- **Strengthened**: the disconnection is sharper than stated. The
  implementation deliberately defers the equivariant layer to domains as
  "domain content" on the grounds that its form "depends on *which* group acts
  on *which* state components" — correct, and **no interface item accepts that
  content**, so the delegation has no destination. That is the framework
  defect, not merely that the two are disconnected.
- **REFUTED**: "ADR-027 declined it." It did not. ADR-027 states in as many
  words "*Full anisotropic `ℓ_D` now.* **Deferred, not rejected**", carries an
  explicit scope paragraph naming the unimplemented Spec requirement, gives the
  reason (the toy's driver fields are 1-D and no oracle exists to check a
  directional extension against), and names the trigger that would force it. A
  silently-skipped MUST and an openly deferred one are different failures, and
  this is the second. "The largest single physics gap in the build" is a
  comparative judgement this verification cannot settle and does not adopt.
- **Scoping consequence**: because Spec §4.4 is already correct here, the
  directional-`ℓ_D` half is a *build-coverage* gap and belongs in
  `docs/COVERAGE.md`, not the framework ledger. E-30 is scoped to the
  group-declaration and metric halves accordingly.

### 3.3 The `m`/`z` boundary is set by your instrument

**Steel.** What counts as "resolved" depends on whether you have EBSD, APT, or
both. Solute clustering is `z` with EBSD and `m` with atom probe. Core §3.1
acknowledges the resolution limit — `m` is "observable in principle by
imaging, at a stated resolution limit" — but does not follow through on the
consequence: **`𝒮` is observer-relative.**

That undermines a claim the framework leans on. Operator reuse and transfer
across routes assume operators are portable objects. An operator trained under
one characterisation suite is defined on a different state space than the same
physics under a better suite. Two labs can implement the same domain, follow
the interface exactly, and produce non-composable operators.

**Generalisation: universal.** Catalysis is the extreme case — active-site
speciation moves between `m` and `z` depending on whether you have operando
spectroscopy. MOF defect structure moves with access to PDF analysis. This is
not a steel artefact; it is a consequence of `m` being defined by
observability rather than by physics.

**What the framework should say.** The interface should require declaring the
characterisation suite that fixes the `m`/`z` boundary, and operator reuse
should be conditioned on matching boundaries. This is closely related to
`V1.4-EDITS.md` E-26/E-27's pattern — a declaration item that omits a joint
property — but the property here is physical, not interface-internal.

**Verification (M10.4). CONFIRMED.** Filed as `docs/V1.4-EDITS.md` **E-31**.

- Core §4 item 1 asks for "resolution limits" — closer than this section
  allows. But it asks for a *limit*, not the suite that sets it, and
  `StateSchema` has **no resolution-limit field at all**, while its own
  docstring quotes item 1's phrase "with resolution limits" verbatim. The
  framework asks for the quantity and the declaration object cannot carry it.
- Item 5 is not a stand-in: flagship's observation suite is `("in-die
  force/torque sensing (Type-0 readout of z)", "coating thickness gauge")` —
  in-chain process sensors for assimilation, not the characterisation methods
  that fix the `m`/`z` partition.
- **Nothing conditions operator reuse or composition on the boundary
  matching.** The chain-composition module contains no reference to a schema
  whatsoever — no compatibility check of any kind. The interface's diff utility
  compares declared schemas, but that is a report produced after the fact, not
  a precondition, and it compares names and dimensions, which would not detect
  two suites yielding the same names at different resolutions. Confirmed.

### 3.4 No constitutive structure among the hard constraints

**This is the most important finding in this document, and it is the one that
bears directly on extrapolation.**

Spec §2.2's five hard-constraint categories are symmetry, thermodynamic
admissibility, range, monotonicity, and conservation. Every one is a *generic
mathematical* constraint. **Not one is a domain constitutive law.**

Steel has canonical forms with decades of validation: Kocks–Mecking for
dislocation evolution, Koistinen–Marburger for athermal martensite, JMAK for
isothermal transformation, Scheil additivity for non-isothermal paths,
Hall–Petch for grain-size strengthening. Each has a small parameter count, a
known validity range, and — crucially — **correct functional form outside the
data you happen to have.**

That is where extrapolation comes from in this field. An operator constrained
to KM form with three fitted parameters will extrapolate to an unseen cooling
rate because the *shape* is right. A free-form operator with monotonicity
constraints will extrapolate flat, which `V1.4-EDITS.md` E-28 demonstrated
directly: a hard constraint honestly representing "no evidence here" produces
a zero-gradient shelf.

So E-28's finding, read physically, is: **hard constraints as the framework
defines them buy safety outside the envelope, not reach.** Reach requires
constitutive structure, and the framework has no category for it.

> **CORRECTION (M11.5, HEAD `eb809ff`). The claim in the two paragraphs above
> is refuted as stated, and this document is corrected in place because it is
> live (CLAUDE.md §10).** The experiment this section proposed was run
> (`docs/M11-RECORD.md`; `docs/M11.5-EXTRAPOLATION.md`). "An operator
> constrained to KM form with three fitted parameters will extrapolate because
> the shape is right" is **not what was measured**, and the claim must be
> narrowed to what the evidence supports:
>
> **Constitutive structure buys reach only when the declared mechanism set is
> complete for the held-out regime. An incomplete mechanism set is worse than
> no declaration at all.**
>
> The measurement, on an accumulated-strain hold-out gated in advance for its
> ability to discriminate: a declared form missing a *dependence* scored 7.56
> and one missing a *mechanism* scored 69.55 — a gap of **+61.98** against a
> declared minimum effect of 0.63 — while the free-form operator scored 5.06
> and an unchanged tabular baseline 3.27. Every declared-form arm lost. The
> asymmetry, not the presence of a declaration, is what governs the outcome,
> and the framework offers no way to declare, assess, or signal completeness of
> a mechanism set.
>
> **The failure is the criterion's as much as the form's, and that half is not
> a retreat.** The correct declared form was **exact** — RMSE 0.0000, first of
> six — against a ground truth with the withheld term removed, and finished
> *fourth* on the criterion Spec §9.3 prescribes. The contestant that won was
> fourth on withheld-free fidelity and first on the criterion, its −7.49 signed
> bias nearly annihilating the withheld term's −6.56. Forward accuracy against
> the full truth rewards a model whose extrapolation error happens to cancel
> the withheld physics, and cannot distinguish that from a model that knows the
> physics. Filed as `V1.4-EDITS.md` **E-42**.
>
> So this section was right that the framework lacks the category, right that
> declared forms are checkable and catch misapplication (`E-38`), and **wrong
> that adding the category delivers reach** — with the qualification that the
> instrument used to look for reach is itself now in question. What the section
> cannot claim, and no longer does, is that shape-correctness alone extrapolates:
> shape-correctness *within an incomplete mechanism set* extrapolated worse than
> having no declared shape at all.

Interface item 6 asks for "invariants — conservation laws and monotone
functionals." Generic again. There is no place to declare *"transformation
kinetics follow Koistinen–Marburger, validated 300–500 K"*.

**Generalisation: universal, and every domain has its canon.**
Semiconductors: Fick with concentration-dependent diffusivity, Arrhenius,
Shockley–Read–Hall recombination, Fermi–Dirac occupancy. MOFs: Langmuir and
BET isotherms, IAST for mixtures, Henry's-law limits at low pressure.
Catalysis: Langmuir–Hinshelwood kinetics, Sabatier and BEP scaling relations.
Batteries: Butler–Volmer, Nernst, solid-state diffusion. Every one of these
is a hard structural form that a learned operator could be constrained to,
and every one would buy extrapolation the generic categories cannot.

**Proposed addition to the interface.** Item 6 gains a sub-item: *declared
constitutive forms, with parameters, validity range, and the citation
establishing them.* An operator constrained to a declared form should report
which form and where the fit sits relative to its validated range — that
report is the honest extrapolation warning, and it is checkable.

**Minimal test in the toy.** Replace flagship's transformation operator with a
KM-constrained one, hold out a cooling-rate region entirely, and compare
against the unconstrained operator and a tabular baseline. This is the
experiment M10.2 should have run and could not, because flagship had no
constitutive structure to constrain to.

> **CORRECTION (M11.4, HEAD `5ca3f0f`). The test as specified here is the wrong
> one, and running it exactly as written wasted a milestone.** Kocks–Mecking has
> no dependence on the rate at which you drive it, so holding out "a
> cooling-rate region" withholds an axis along which the declared form makes no
> prediction that differs from the baseline's. The comparison is then vacuous by
> construction: M11.4 ran it, every contestant's held-out error came out equal to
> the withheld term's own magnitude to within their spread, and the resulting
> null said nothing (`docs/M11.4-EXTRAPOLATION.md`; `V1.4-EDITS.md` E-39, E-41).
> The corrected specification is: **hold out an axis along which the declared
> form itself makes a differing prediction** — for Kocks–Mecking that is
> *accumulated strain*, where the storage/recovery balance produces saturation —
> and demonstrate before registering the hold-out that the candidate and the
> baseline diverge along it. This document proposed the right *experiment* and
> the wrong *axis*, and the distinction is not a detail.

**Verification (M10.4). CONFIRMED, and more strongly than argued.** Filed as
`docs/V1.4-EDITS.md` **E-32**.

- Spec §2.2's five categories are Symmetry, Thermodynamic admissibility, Range
  constraints, Monotonicity, Conservation. Every one is generic mathematical
  structure; none is a domain constitutive form. Confirmed verbatim.
- The constraints module implements range (positivity, simplex), monotonicity
  and conservation; declines thermodynamic admissibility as out of scope
  (E-10); defers symmetry to domains, where no domain implements it (E-30).
  None of the five, implemented or not, is a constitutive form — so finishing
  the list would not supply the missing category. Confirmed.
- **Strengthened**: "there is no place to declare *'transformation kinetics
  follow Koistinen–Marburger, validated 300–500 K'*" understates it. There is a
  place, and it **throws**. The item-6 implementation classifies each declared
  invariant as conservation or monotonicity and refuses any name matching
  neither. Run against four canonical forms — `koistinen_marburger_martensite_kinetics`,
  `kocks_mecking_dislocation_evolution`, `jmak_isothermal_transformation`,
  `hall_petch_grain_size_strengthening` — **all four raise**, while
  `charge_conservation_coulomb_counting` and
  `sei_thickness_monotone_nondecreasing` classify. The refusal cites "Spec
  §2.2's two hard-constraint categories that apply here", a faithful reading of
  item 6, so it is evidence *for* this finding rather than an artefact of the
  implementation.
- The extrapolation argument is corroborated independently: this ledger's E-28
  measured, by building, that a hard monotonicity constraint honestly
  representing "no evidence past the training data" produces a flat,
  zero-gradient shelf. Safety without reach, from the other direction.
- **Not established**: that adding the category would *deliver* the reach it is
  argued to deliver. That needs the held-out constitutive-form experiment this
  document proposes, which was not run.

**Second verification (M11.5, HEAD `eb809ff`). The last bullet is now settled,
and it is settled against this section.** The experiment was built and run
(`docs/M11-RECORD.md`). Adding the category does **not** deliver the reach
argued for: every declared-form arm lost to a free-form operator, and an
unchanged tabular baseline beat all of them. What survives, and what does not:

- **Survives.** Spec §2.2 has no constitutive category; item 6 refuses canonical
  form names; the category is declarable, checkable and composable once added;
  and a declared validity range caught a genuine modelling error on its first
  application to real physics with no oracle involved (`V1.4-EDITS.md` E-38).
  The *diagnostic* value of declaring a form is confirmed.
- **Refuted as stated.** That shape-correctness buys extrapolation accuracy. It
  does so only under a condition this section never states — a **complete
  mechanism set for the held-out regime** — and violating that condition is
  worse than declaring nothing (+61.98 between the two misspecification arms).
- **Newly in question.** Whether the measurement could have shown reach even had
  it been there. The correct declared form was exact against a withheld-free
  truth and fourth on Spec §9.3's criterion, beaten by a model whose error
  happened to cancel the withheld physics (`V1.4-EDITS.md` E-42).

### 3.5 Timescale separation and stiffness are unaddressed

**Steel.** Recovery, recrystallisation, grain growth and precipitation span
seconds to hours in the same anneal. Their coupling is stiff. The framework
defines evolution operators over intervals `[t_k, t_{k+1}]` and says nothing
about stiffness, timescale separation, or how the interval is chosen.

The semigroup identity of Core §3.3 assumes intervals can be split
arbitrarily and the composition is unchanged. For a stiff system this is
exactly where a learned operator degrades — an operator learned at one Δt
composes badly at another, because the fast mode is unresolved at the coarse
step and dominant at the fine one.

There is a testable prediction here, and the machinery to test it already
exists: **semigroup residual should grow systematically with timescale
separation.** The build measures semigroup residuals routinely (Spec §9.2).
Nobody has swept them against a stiffness parameter.

**Generalisation: universal.** Batteries span double-layer charging
(microseconds) to SEI growth (months) — the framework's own contrast domain
is stiffer than steel. MOF guest diffusion is fast, framework breathing
slower, degradation slower still. Semiconductor processing separates
implant damage annealing from dopant diffusion by orders of magnitude.

This connects to Core §3.7's closure-defect discussion, but that treats
*spatial* coarse-graining. Temporal coarse-graining raises the same
Mori–Zwanzig issue and is not discussed at all.

**Minimal test in the toy.** Give flagship a two-timescale operator with a
tunable separation ratio, and plot semigroup residual against that ratio. If
the residual grows as predicted, the framework needs a declared temporal
resolution alongside its spatial one.

**Verification (M10.4). CONFIRMED on the absence; the falsifiable prediction
was TESTED and REFUTED as stated, and the refutation is a sharper finding.**
Filed as `docs/V1.4-EDITS.md` **E-33**, the only entry in that ledger whose
finding was put to a measured test.

*The absence, confirmed.* Searched both documents for `stiff`, `timescale`,
`time scale`, `step size`, `temporal resolution`, `temporal coarse`, `fast
mode`, `slow mode`, `multirate`: **zero occurrences of any of them**. Core
defines the operator over `[t_k, t_{k+1}]` and gives no guidance anywhere on
choosing or bounding it. Mori–Zwanzig appears three times, every one spatial —
Core §3.7 projects "to **scale** λ" via homogenisation and Γ-convergence and
grounds its RG rejection in "characteristic **lengths**"; Core §6.2 asks for
kernels for "**structural** coarse-graining", Core's own adjective. So this
section's claim that §3.7 is spatial-only is confirmed by Core's own
vocabulary, not by inference.

*The prediction, refuted.* Built a two-timescale system with an exactly
controllable separation ratio and swept Core §3.3's residual across three
decades, with an A-stable integrator (Crank–Nicolson, exactly norm-preserving
for a rotation) so the residual is pure consistency error, and norm drift
reported at every point (never above `6.6e-4`). Results, and the sweep is
reproducible via `scripts/run_m10_4_stiffness_sweep.py`:

- *Control*: an exact matrix-exponential flow has residual below `1.2e-16` at
  every ratio, so stiffness alone generates no residual.
- *Decaying fast mode*: residual **flat** — total spread `3.08×` across three
  decades, with the highest ratio *lower* than the lowest. The unresolved
  mode's amplitude decays as fast as its rate grows, and the effects cancel.
  The prediction fails outright here.
- *Persistently excited (oscillatory) fast mode*: residual moves by four orders
  of magnitude but **non-monotonically** — an interior peak at ratio `50`,
  rising `10,853×` to it and falling `3,528×` past it. Largest where the fast
  mode is *marginally* resolved; small at both extremes, because when grossly
  under-resolved the whole-interval and split-interval answers are wrong the
  same way. Not the systematic growth predicted.

An earlier attempt with explicit Euler reported a residual of order `1e85` at
high separation. That was the integrator diverging, not a semigroup
inconsistency — recorded because it is exactly the artefact a careless version
of this test would have published as a confirmation.

*What the sweep established instead, which is stronger.* Core §3.3 attributes
residual violation to one cause — "a cheap, automatable proxy for insufficiency
of `𝒮`". Supplying that cause cleanly (a genuinely insufficient state advanced
by an *exact* propagator, so zero numerical error anywhere) gives `1.193e-01`
at ratio 1, falling `98×` across the sweep as adiabatic elimination makes the
closure accurate. So the two causes depend on stiffness differently and partly
oppositely. **And at ratio `50` they are indistinguishable**: a fully
sufficient state with fixed temporal resolution gives `9.894e-03`; a genuinely
insufficient state with an exact propagator gives `1.238e-02` — within
`1.25×`. The remedies differ entirely (resolve time better versus augment the
state) and Core §3.3, naming only the second, cannot tell them apart. A small
residual certifies neither.

**Re-run at the sharpened design (M10.4, second pass) — the confound above does
NOT survive, and the refutation is now the primary result.** The first pass used
a *coupled* generator and, for the arm that moved, a *persistently excited*
(oscillatory) fast mode. The sharpened design specifies the canonical stiff-decay
case instead: state `(x_fast, x_slow)`, **decoupled** pure decay, stiffness ratio
`r = λ_fast/λ_slow` swept, both modes explicit so sufficiency is exact rather
than assumed. That is also the more representative case for the metallurgical
motivation quoted at the top of this section — recovery, recrystallisation and
grain growth are decay processes, not oscillations. Reproducible via
`scripts/run_m10_4_stiffness_sweep.py`. Results across three decades of `r`:

| arm | `r=1` → `r=1000` | verdict |
|---|---|---|
| (a) exact analytic — the null | worst `6.94e-18` | passes; stiffness alone generates no residual |
| (b1) fixed step **count**, explicit Euler, stable throughout (`max λ·h = 0.977 < 2`) | `1.271e-04` → `8.987e-05` | **flat**: spread `1.58×`, last/first `0.71×` |
| (b2) fixed step **size**, commensurable split | `0.00e+00` at every `r` | vacuous pass |
| (c) learned at one `Δt` | `0.14`–`0.30`, no trend | dominated by unseen duration, not stiffness |

**The per-component decomposition gives the mechanism, and it is physical rather
than numerical.** The slow component's contribution is `8.987e-05` at *every*
ratio — stiffness-independent to every digit, as it must be, since the slow
mode's own dynamics do not depend on `r`. The fast component's rises briefly
(peaking at `r=3`) and then collapses super-exponentially: `1.08e-06` at `r=10`,
`1.52e-14` at `r=30`, `4.94e-324` at `r=1000`. Once the fast mode is stiff it is
annihilated *identically* in the coarse and the fine evaluation, so their
difference vanishes and it leaves the residual altogether. **So a stiff mode
cannot confound this diagnostic by being under-resolved — being under-resolved is
exactly what removes it from the measurement.**

**The metric caveat was the decisive arm, and it resolves in the framework's
favour.** As anticipated, the fast mode's variance collapses as `r` grows.
Normalising the residual by the **outgoing** population's per-component σ
therefore divides by a vanishing number and manufactures a spurious excursion of
`5.7e+16×` — `1.72e-03` at `r=1`, rising to `9.79e+13` at `r=300`, then
collapsing back to `1.23e-03` at `r=1000` only because σ underflows to exactly
zero and the zero-variance guard fires. Anyone who had normalised that way would
have reported "residual grows with stiffness by fourteen orders of magnitude",
and it would have been pure artifact. ADR-002's convention takes σ from the
**incoming** population, which does not depend on `r` at all, so it is
stiffness-independent by construction and reproduces the flat result
(`6.34e-04` → `4.51e-04`, spread `1.56×`). **The refutation therefore survives
every stiffness-independent metric, and the growth a careless normalisation
would have shown is the artifact this section's own caveat warned about.**

**Consequences for the first pass, stated rather than quietly dropped.** The
oscillatory measurement was correct for the system it was run on, but that system
is not the one this section describes, and the confound it exhibited is specific
to a fast mode that stays excited. For the canonical stiff-decay case the
attribution is **not** confounded by stiffness. `docs/V1.4-EDITS.md` E-33 has
been corrected in place accordingly: its absence finding (no treatment of
stiffness or temporal resolution anywhere in Core or Spec) stands unchanged and
is textual; its confound claim is narrowed to the persistently-excited case and
no longer carries the entry; and the entry's centre of gravity moves to the
metric under-specification, which is the robust framework finding this sweep
produced.

**One candidate finding refuted, recorded because a refutation earns its place
here.** The (b2) vacuous pass looked like a framework defect — a conformance
check that can score exactly zero however wrong the operator is. It is not:
Spec §9.2 specifies the check "on **random** sub-interval splits", and a random
split is almost surely incommensurable with any fixed internal step. The
Specification already guards against it. It remains a live hazard for
implementations that pick *fixed* split points, which this repository does
(`t_mid` values of 0.2/0.5/0.8 and 0.2/0.4/0.6/0.8, none randomised) — a
repository defect, not a framework one, and recorded as such. How live: on a
commensurable split the pass survives even at ratios where the fixed step has
left explicit Euler's stability region entirely (`λ·h = 3` and `10`), because
both the direct and the composed path diverge to the *same* wrong answer. An
implementation with a fixed split point can therefore score `0.00e+00` on an
operator that has blown up by twenty-seven orders of magnitude.

### 3.6 Metastability strains Axiom S in a characteristic way

**Steel.** Retained austenite, bainite/martensite selection, tempering
sequences — much of what matters commercially is metastable, and its evolution
depends on barrier heights rather than on the current state's distance from
equilibrium.

Axiom S requires the state to be sufficient for its own future. For a
metastable system, sufficiency needs the *basin structure*, not just the
current occupancy — two samples with identical phase fractions can have
different subsequent transformation behaviour if their interfaces or carbon
distributions differ. That is exactly the sufficiency test failing, but with
a particular signature: divergence appears only under driving that crosses a
barrier, and not otherwise.

I offer this as a **prediction rather than a confirmed gap**: metastable
systems should fail sufficiency tests in a way that ordinary path-dependence
does not, and Spec §1.6's fingerprint table has no row for it. Confirming it
needs a metastable oracle, which does not exist.

**Generalisation: general, and central in several domains.** Pharmaceutical
polymorph selection is the textbook case and is already one of this build's
sketches. MOF framework flexibility — the same composition occupying open and
closed pore states — is metastability with commercial consequences.
Amorphous versus crystalline selection in semiconductors and in phase-change
memory is the same structure.

**Verification (M10.4). Recorded as a prediction, not filed as a finding.**
This section explicitly offers itself as "a **prediction** rather than a
confirmed gap", and states that confirming it "needs a metastable oracle, which
does not exist." That remains true: no metastable oracle was built, and none of
the five entries filed from this document covers §3.6. It is therefore neither
confirmed nor refuted here, and is **not** in `docs/V1.4-EDITS.md` — filing an
untested prediction as a framework finding is exactly what this repository's own
gap discipline forbids. (The five entries filed from this document are E-29–E-33;
none covers §3.6.) Noted for whoever builds the oracle: the prediction is
specific and falsifiable — divergence appearing only under driving that crosses
a barrier, and not otherwise — which is the shape a probe-set fingerprint row
(Spec §1.6) would need to encode, and E-03's paired-probe finding is the
nearest existing machinery.

### 3.7 A physics error in flagship that the interface audit read as an interface gap

Worth separating out, because it changes how `V1.4-EDITS.md` E-26 should be
read.

E-26 found flagship's readouts are invariant to its declared controls, and
filed it as a Core §4 item 2 gap — the interface does not require declaring
readout sensitivity. That finding stands.

But metallurgically, **the invariance is itself a modelling error.** Soak
temperature and time change grain size and phase fractions; grain size and
phase fractions change hardness. In real steel, hardness after annealing
absolutely responds to heating intensity. Flagship's constitutive operator
apparently does not read the parts of state the thermal controls modify —
so either the operators do not change those state components, or the
constitutive readout ignores them.

The distinction matters for what to fix. E-26's proposed edit — require a
sensitivity declaration — would have caused flagship to declare "no readout
responds to any control," which is a truthful declaration of a broken domain.
The interface fix catches the symptom. The domain also needs the physics
repaired, or every subsequent control-inverse experiment on flagship remains
vacuous no matter what the interface requires.

*Generalisation: this specific error is flagship's, but the lesson is
general.* A synthetic domain can satisfy every structural requirement while
being physically inert, and the framework has no check for that. The
sensitivity declaration E-26 proposes is the closest thing available, and it
detects rather than prevents.

**Verification (M10.4). CONFIRMED, and the disjunction resolves; the
framework-level half is filed, the domain repair is not performed.** Filed
**inside `docs/V1.4-EDITS.md` E-29**, not as a separate entry: this section and
§3.1 turned out to be one finding at two levels, and the flagship defect itself
is a *repository* construction fault, which CLAUDE.md §10 keeps out of a ledger
reserved for the framework. It is recorded inside E-29, clearly marked, on the
precedent of E-17's own marked repo-fix note — because it is the evidence for
what §3.1's missing category costs and is unintelligible separated from it. (An
entry E-34 was briefly assigned to this section alone and withdrawn; the number
is retired, not reused.)

The disjunction offered here — "either the operators do not change those state
components, or the constitutive readout ignores them" — resolves to **the
first; the second is refuted.** Flagship's constitutive operator reads three
real state components (`inclusion_content`, `prior_grain_size`,
`accumulated_hardening`) and ignores nothing. But in **both** of flagship's
evolution operators all three carry relaxation rate exactly `0.0` **and**
control-coupling gain exactly `0.0` — not small, exactly zero — so they are
invariants of the whole chain. Measured: aggregate hardness is
`106.12805030058055` on the incoming state and `106.1280503006` after the full
chain at heating intensities `2`, `8` and `14` — identical to ten decimal
places across a sevenfold control sweep — with `prior_grain_size` unchanged at
`19.603685`. The Class-B bend readout is likewise pinned at `107.1280503006`.
There are **two independent breaks**: separately, the only component in the
schema with a nonzero control-coupling gain is `coating_thickness`, which no
hardness-path readout reads. The metallurgical diagnosis is exactly right on
mechanism — soak should change grain size, and flagship's grain size has rate
`0.0` under soak.

**And it is §3.1's missing category, one level down.** The three components the
readout reads *are* flagship's three de-facto-static components. This is not an
unrelated coding slip: it is a readout depending only on static parameters,
which nothing in the framework can flag because the framework has no notion of
a static parameter. E-29 files the framework-level half, and states it as a
**detectability** claim rather than as a missing check: because nothing
distinguishes "static by design" from "should evolve but does not", a readout
depending only on parameters cannot be flagged structurally. Core §2.6 supplies
the legitimate case that makes the confusion genuine — a *property* is "a
functional of the constitutive operator alone" and is *supposed* to be invariant
under the test configuration, which is a different claim from being invariant
under the processing controls that produced the state. Flagship implements the
first correctly and fails the second, and the framework has no vocabulary
separating them. With a parameter category the two become distinguishable and
the check is mechanically computable from the declaration and the operators,
needing no honesty from the declarer — unlike E-26's declaration requirement.

**The repair is not performed.** Per this task's scope, flagship's physics is
recorded as broken and left broken. Repairing it would make the control inverse
non-vacuous, enable the constitutive-form extrapolation test E-32 leaves
untested, and make this build's baseline comparison meaningful on the control
axis for the first time — one task with several payoffs, needing its own
decision record.

---

## 4. Extrapolation, taxonomised

The question that prompted this document deserves a direct answer, and the
answer is that "extrapolation" names four different problems with different
mechanisms.

| Regime | What it asks | What buys it | Framework support |
|---|---|---|---|
| **Interpolation in envelope** | predict inside the swept range | any decent surrogate | Full — and Spec §9.3 honestly says tabular often wins |
| **Extrapolation in control space, same mechanism** | a cooling rate faster than any seen | correct functional form | **Absent** — §3.4; generic constraints give flat shelves |
| **Extrapolation to a new mechanism** | a phase that never formed in training | the mechanism must be represented at all | **Absent, and arguably out of scope** — no constraint helps if the physics is not in the graph |
| **Extrapolation across composition family** | a new grade | chemistry-parameterised operators | **Absent** — §3.1; Core §6.2 lists it open |

Three of four are unsupported, and the framework's own claimed mechanisms —
hard constraints, physics-informed losses, manifold projection, trust region
— only the trust region was demonstrated, and it *restricts* extrapolation
rather than enabling it.

This is not a refutation. It is a scoping statement, and it is one the
framework is unusually well set up to make honestly: Spec §9.3 already says
to state when not to use OMI. The accurate version is that OMI's current
value is **interrogable intermediate states, retrospective diagnosis, and
correct treatment of geometry-dependent and weakest-link responses** — all
real, all things tabular models cannot do — and that extrapolation outside
the training envelope needs constitutive structure the framework does not
yet have a category for.

*Generalisation: the taxonomy is domain-independent.* The middle two rows are
where every materials-informatics extrapolation claim lives, in every field.

---

## 5. Generalisation audit

| Finding | Steel instance | Verdict | Notes on other classes |
|---|---|---|---|
| Toy cannot test extrapolation (§1) | analytic operators, near-affine readouts | **General** | any synthetic domain has this |
| Composition has no home (§3.1) | hardenability, Ms, precipitation | **General, boundary is domain-dependent** | dopant profile is parameter *and* state in semiconductors; linker chemistry is pure parameter in MOFs |
| Anisotropy absent (§3.2) | texture, r-value, banding | **General; more central elsewhere** | wafer orientation; MOF pore directionality; electrode tortuosity; AM build direction |
| `m`/`z` is instrument-relative (§3.3) | EBSD vs APT | **General** | operando spectroscopy in catalysis; PDF in MOFs |
| No constitutive structure (§3.4) | KM, JMAK, Scheil, Hall–Petch | **General; every domain has a canon** | Fick/SRH; Langmuir/IAST; Butler–Volmer; Langmuir–Hinshelwood |
| Stiffness unaddressed (§3.5) | recovery→recrystallisation→growth | **General; batteries are stiffer** | µs to months in the contrast domain itself |
| Metastability strains Axiom S (§3.6) | retained austenite, bainite selection | **General; predicted, not confirmed** | polymorphs; MOF breathing; phase-change memory |
| Flagship physics inert (§3.7) | readouts ignore thermal controls | **Domain-specific defect, general lesson** | any synthetic domain can be structurally valid and physically inert |

Every row except the last is general. That is worth stating plainly: **these
are not steel complaints.** The framework's domain-neutrality is real, and
so are these gaps, in the same domain-neutral way.

---

## 6. What would settle it

One experiment, and it is smaller than it sounds.

Take a real continuous-annealing line. Readouts: hardness and r-value —
Class A, well-instrumented, commercially meaningful. Constrain the
transformation operator to a declared constitutive form (KM plus a
hardenability parameterisation). Hold out **a grade transition**, not random
coils — grouped splits by composition family, per Spec §9.3.

Compare against a well-tuned gradient-boosted baseline on the held-out
grade.

- If the constrained operator graph wins, the extrapolation claim is real and
  §3.4's proposed interface addition is the mechanism.
- If it does not, Spec §9.3's honest caveat applies and the framework's value
  is the interrogable states and retrospective smoothing — which are worth
  having, and are not what the abstract leads with.

Either outcome is publishable and the second is more interesting than it
sounds, because almost nobody reports it.

**In the meantime, four things are buildable in the existing toy** and each
tests one finding above without field data: the chemistry-transfer test
(§3.1), the directional-`ℓ_D` bendability test (§3.2), the KM-constrained
extrapolation test (§3.4), and the semigroup-residual-versus-stiffness sweep
(§3.5). None needs a new domain. All four would strengthen the paper's
physics claims, which are currently its weakest.

---

## 7. Standing caveat

Written from metallurgy, against a specification and this build's reports,
without reading the current source. Findings §3.1–§3.6 are about the
framework's text and hold independently. §3.7 is about flagship's
construction and should be verified against the code before it is cited.

**Updated at M10.4.** §3.7 has now been verified against the code and its
open disjunction resolved (see its Verification block); it is safe to cite,
with the correction that the second branch is refuted. §3.1's flagship-specific
illustration is wrong and should not be cited — the framework-level finding
stands. §3.2's claim that ADR-027 "declined" the directional `ℓ_D` is refuted:
it was explicitly deferred, with a stated reason. §3.5's prediction has been
tested and refuted as stated. Everything else in §3 is confirmed.

Two of the filed entries were also **strengthened beyond what this document
argued**, and the strengthening is noted here because it changes what should be
cited. §3.2's metric point is not contingent on a domain needing texture: Core
§3.1 names "orientation fields" among `m`'s occupants, so the framework names an
occupant its own metric requirement mishandles, and the 90°/`1.414`
demonstration is the proof rather than an illustration — cite it that way.
And §3.4's proposed interface addition cannot be a sub-item of item 6 as this
document suggests: item 6 serves *two* roles (hard constraints per Spec §2.2 and
reachability certificates per Spec §7.1), a constitutive form can serve only the
first, and adding one to item 6 would silently widen the pool Spec §7.1 draws
certificates from. E-32 proposes a role-scoped split instead, which also repairs
item 6's existing omission of Spec §7.1's third candidate kind
("equilibrium-limited fractions at attainable driving levels", which item 6 never
names and this build's faithful classifier therefore refuses).

**An external verification table exists and is superseded by in-repository
measurement. Do not reconcile the two — the measurements win.** A later
external assessment arrived carrying its own status table for §3.1–§3.7. It was
written without access to the Phase 1 and Phase 3 results below and is stale in
four specific places, each of which would *overwrite better data* if imported:

| It reports | Actually established here |
|---|---|
| §3.5 "partially addressed, prediction can now be tested" | The prediction **was** tested, twice, and **refuted**: residual is flat in the stiffness ratio at exact sufficiency (`1.271e-04` → `8.987e-05` over three decades, spread `1.58×`), with a passing null arm and a per-component mechanism. See §3.5's second-pass block. |
| §3.7 "still needs verification" | Verified **by measurement** at Phase 1, and its open disjunction resolved — first branch confirmed, second branch refuted. See §3.7's Verification block. |
| ADR-027 "declined" the directional `ℓ_D` | **Deferred, not rejected**, with a stated reason and a named trigger. Corrected at Phase 1 and recorded in `docs/V1.4-EDITS.md` E-30, which also finds the directional half is a build-coverage gap against a *correct* Specification and belongs in `docs/COVERAGE.md` (row S-4.4, where it is), not in the ledger. |
| §3.1's row omits the three de-facto-static components | Phase 1 measured them: `prior_grain_size`, `inclusion_content` and `accumulated_hardening` carry `rate == 0.0` under **both** flagship operators, so no declared operator transports them. That measurement is what links §3.1's missing category to §3.7's physics error, and is why the two are filed as one ledger entry (E-29) plus a recorded repository defect. Omitting it loses the link. |

The reason for the asymmetry is not that the external reader was careless: a
status table written from the documents cannot see a measurement that was not
in them yet. **The Phase 1 and Phase 3 reports, and the Verification blocks in
§3 below, are this document's record of what is established.** An external
table is evidence about the *documents*, never about the build.

Generalisation verdicts for semiconductors, MOFs, catalysis and batteries are
argued from domain knowledge, not from instantiations — they are the same
kind of claim as Core §1.1's own scope statement, and carry the same
weight, which is to say they are plausible and untested. The four interface
sketches are the right vehicle for testing them, and §3.1–§3.5 give each
sketch something specific to look for.
