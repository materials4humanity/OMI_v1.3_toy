# v1.5 planning — the track record

**Snapshot** (CLAUDE.md §10). Generated at the commit closing v1.5 planning. Every measured
figure comes from `scripts/run_v15_part5_1.py`, `scripts/run_v15_part6_gate.py`,
`scripts/run_v15_part6_preregistration.py` and `scripts/run_v15_part6_sweep.py`, all reproducible
unchanged at that commit. The underlying documents are `docs/V1.5-PLANNING-BRIEF.md`,
`docs/V1.5-PART5-1.md`, `docs/V1.5-PART5-2.md`, `docs/V1.5-E53-DECISION.md`,
`docs/V1.5-E53-FIX.md`, `docs/V1.5-PART6.md`, `docs/V1.5-PART6-PREREGISTRATION.md`,
`docs/V1.5-PART6-SWEEP.md`. Corrected by dated addendum below the passage it corrects, never by
rewriting the original text.

**Scope of the track.** Parts 1–4 were design and ADRs with no implementation. Part 5 ran its
inputs, a statistic dry-run and one measurement. An unplanned E-53 milestone interrupted Part 6.
Part 6 designed, pre-registered and ran one experiment. **Implementation of the v1.5 extension is
a separate authorisation and was not begun.**

---

## 0. The headline

v1.5 planning produced **sixteen ledger entries** (E-43 – E-58, contiguous), **nineteen ADRs**
(ADR-048 – ADR-066, plus two amendments to ADR-061 and one to ADR-066), one corrected criterion implemented across
`src/omi/`, a **third domain** with operators, and one pre-registered experiment whose three
criteria were met.

**Two results outrank the experiment.**

1. **E-55.** Flagship's two largest danger scores were being counted as the framework's
   differentiator against a tabular baseline — and **no observation informs them at all.** The
   corrected set is `[0.0]`. The differentiator changes form, and that is a publication
   consequence for both papers.
2. **E-56 with E-57.** The erasure concept is under-specified in two independent ways, and Core
   §3.9's composability argument rests on both. Now §1's seventh headline finding — the only one
   whose target the framework marks SPEC, i.e. believes finished.

**And one negative result the track would be dishonest without.** Of the four diagnostics the
contrast decision loop was to be *driven by*, **three cannot drive it**, for three different
reasons, none of which is a property of the loop.

---

## 1. The purpose extension, and what it demoted

The brief extended the framework's declared purpose from *a chain that models a process* to a
chain that supports a **decision about what to do next** — three decision kinds: which route to
run, how to operate an artefact, what to make.

**What it demoted.** Conformance level plus framework version is **not** a self-describing claim
(E-43): two reports at the same level and the same version can be answering different questions,
because the version does not carry the framework's *purpose*. This demotes E-35's repair — which
added the version — from sufficient to necessary-but-not-sufficient. `SpecificationVersion` gained
`PROPOSED_V1_5` (ADR-059) and the carrier nests: the v1.3 seven items sit whole inside the v1.4
declaration, which sits whole inside the v1.5 one (ADR-042's composition-over-modification, applied
twice), so `omi.interface.diff` compares three domains rather than two plus a special case.

## 2. The declared-domain construction, and which E-22 sub-claims it closed

`ADR-049`'s `DeclaredDomain` / `CouplingDirection` / `TrackedDimensions` gave a domain a way to say
*what kind of thing* a coupled quantity is: a global point value, a set of regions, or a field.

**E-22 had proposed a field over the body and had to withdraw it.** The construction closes two of
its sub-claims and leaves one open:

| E-22 sub-claim | disposition |
|---|---|
| `ν` is mis-typed under Core §2.5's own body-indexing repair | **closed** — `GLOBAL_POINT` is the case the first proposal could not express, and pore-network accessibility is a fourth independent instance of it |
| a domain must be able to declare the *resolution* at which a coupled quantity is tracked | **closed** — `TrackedDimensions` plus a required `tracked_justification`, which is what stops a domain claiming a resolution its observation suite does not supply |
| the body-indexed state itself (Core §2.5) | **open, and out of scope** — Spec §5.2's registration operator is a declared anti-goal (CLAUDE.md §9), so §2 of the ledger was never going to resolve here |

**A closure obligation came with it** (ADR-050): a region-valued conserved quantity must declare
whether its region is *closed*, and the constancy check is expected to **fail** where it is not.
The discovery domain declares exactly that failure in advance — promoter segregates out of the bulk
during calcination — so the failure is the diagnosis rather than a defect.

## 3. Composition, in five parts

The track's largest single piece of design, and the reason a third domain was needed at all.

**The decomposition** (ADR-049, ADR-051). Composition is not one thing. It decomposes into a
*conserved quantity*, an *aggregation functional*, a *region over which it is aggregated*, and a
*flux* that moves it between regions. Declaring "composition" without those four is declaring a
name.

**Roles, per species per region** (ADR-051). A species is a `CONTROL`, a `STATE` or a `PARAMETER`,
and **the same species can hold different roles in different regions of one chain,
simultaneously.** E-29 filed the missing `PARAMETER` category — a quantity that indexes the
operator family and is transported by nothing. The discovery domain exercises the central claim
rather than asserting it: `promoter` is `CONTROL` in the bulk and `STATE` in the surface layer, and
`support` is `PARAMETER` in both, so `parameter_only_species()` makes E-29's second half mechanical
— a readout depending only on it is a readout of the *grade*, not of the process.

**The descriptor metric** (ADR-052). A descriptor basis is a declared set of named functionals of
the underlying coordinates, carried **alongside** the fractions rather than instead of them. Each
makes a falsifiable claim about argument structure — *"the operator family depends on chemistry only
through these"* — testable by holding out a formulation that varies the fractions at fixed
descriptors.

**The third inverse** (ADR-053). Target response → *composition* is a distinct problem from target
response → control programme and target response → state, by Core §5's own separating criterion:
what certifies infeasibility. Not an apparatus constraint and not a reachability bound, but that
the requested coordinates **describe nothing that exists, or nothing this route can make.**
ADR-053 designed the inverse and **declined to design the certificate**, because no domain had
declared an attainable region and inventing one would have been improvisation. Part 5(2) unblocked
it.

**Composition-dependent validity** (ADR-054). A declared form's validity range is itself a function
of composition, so a second-order declaration is needed: the descriptor interval over which the
range is *claimed to hold*. A query inside the form's temperature window but outside that interval
is **refused**, not annotated — a validity range extrapolated across a phase boundary is not a
wider range, it is a different form.

**What this exposed.** E-44: Core §1.1's scope features are never declared and never checked, so a
domain in scope is indistinguishable from one that is not. E-46: Core §4 item 1's charter covers
what the material *is* and cannot host what the operator family is *parameterised by* — two
structurally different declarations item 1 distinguishes nowhere.

## 4. Parameter equifinality: E-47 argued, then measured, then narrowed

E-47's claim was that a declared constitutive form can be in-window, well-fitted, and have
parameters unidentifiable *along the very axis being extrapolated*, with every check passing.

**Measured** (ADR-058; `tests/oracles/known_parameter_ridge.py`), on M11.5's contestant 2 refitted
300 times, in a **declared fractional-parameter metric** chosen deliberately *against* invariant 1's
aleatoric default — which here would force the covariance's diagonal to unity and destroy the
anisotropy the measurement exists to find.

| what E-47 claimed | measured | verdict |
|---|---|---|
| the posterior is a ridge | condition number **`436.7`**, stable across 1–5% noise and across seeds | **confirmed** |
| the ridge points *precisely along* the extrapolated direction | alignment `0.0436 → 0.2402` across the reach, growth **`5.51×`** | **refuted** — it leans, and at 6× the envelope `|cos| = 0.240` is nearer orthogonal than parallel |
| the declared validity report is silent | fires for **41.7%** of far queries — for the wrong reason, `stored_density` against its ceiling | **refuted** |
| the extrapolated uncertainty is unreported | far spread / in-envelope fit residual **`4.75×`**, and nothing in the framework reports the factor | **stands** — the surviving gap |

**The measurement is the point.** E-47 was filed as an argument and is now an entry whose two
strongest claims were removed by the evidence for its third. That is what the ledger is for.

## 5. The decision loop on contrast, and the two diagnostics that drive nothing

ADR-056 designed an **ordered** rule — retire, commission, derate, set control — rather than a
weighted score, because with four terms in one score freezing one changes the argmax rarely and
*"did this diagnostic drive anything"* stops being answerable. The loop is **design only**; what ran
was its inputs, traced over a 24-interval declared campaign.

**This section must not be smoothed over. The negative results are findings, not gaps.**

| diagnostic | drives a decision? | why |
|---|---|---|
| **validity report** (Spec §2.2) | **No — structurally unavailable** | contrast declares no constitutive form, so its operator does not satisfy `ConstitutivelyConstrained` and there is nothing to report against |
| **danger score / triage** (Spec §3.3) | **No — and worse: it fires arbitrarily** | influence median exactly `0.0` at every interval; total danger flat to `6×10⁻⁵` of its own mean; the label split decided at a margin of **`1.4×10⁻¹¹`** |
| **innovation sequence** (Spec §10) | **Yes, as a gate — but not via `any_drift`** | per-window rate nominal (`0.0561` against `0.05`, mean NIS `1.0074`); `any_drift` fires on **38.5%** of *correctly specified* campaigns |
| **blocking trichotomy** (Spec §1.7) | **Yes** | continuous, and the only one of the four that ranks a *purchase* |

Three things follow, each its own entry.

- **The influence boundary collapses the classification** (E-48, first half). Influence is a
  non-negative quadratic form; a target set touching fewer than half the state components makes the
  median exactly zero and `influence ≥ median` a tautology. `MARGINALISABLE` and
  `OBSERVED_BUT_IRRELEVANT` become **unreachable** and Spec §3.3's four-way triage silently becomes
  a two-way identifiability split. Not a contrast property.
- **The near-diagonal boundary decides the rest at machine precision** (E-48, second half). Two
  eigendirections whose shares agree to **eleven decimal places** received different labels. **An
  arbitrarily firing diagnostic is worse than a silent one**, and it is why ADR-056's step 2 is
  keyed on the blocking trichotomy rather than on `dangerous_set()`.
- **Retire is declared nowhere** (E-52). It is Core §3.9's "declare out of scope" reached during
  operation, and Core §4's seven items are exhaustively about the chain's *content*. That the
  absence bites is measurable: contrast's declared operator drives its own terminal voltage
  **negative** within forty intervals of ordinary cycling, and nothing declared bounds it. The
  sixth missing interface category.

**Two more from the dry-run**, which selected `innovation_bias` from three candidates (growth
`6.874`, beating the Spec §9.3 tabular baseline by `2.24×`). E-50: the sufficiency deficit is
**exactly zero** in every null replicate, so E-41's divergence ratio is undefined *precisely because
the statistic detects perfectly*, and a `nan` silently passes a `<` comparison — which this
implementation did, on the first run, until the check was reordered. E-51: Spec §1.2's deficit is
**anti-correlated with campaign length** when the missing variable is a static latent, because
matching on a longer-evolved state implicitly matches the latent — a false negative in the direction
that matters, since a campaign run late in a process is when the question is urgent.

**And the construction's own first version was wrong.** The planted defect was initially a
porosity-dependent rate — a dependence on a *declared* component. Axiom S still held, the deficit
was correctly zero, and candidate 1 would have looked inert for a reason unrelated to candidate 1.
*"The model is insufficient"* names two different failures and Spec §1's machinery addresses one.

## 6. The E-53 interruption, and what it cost

E-53 found that **Spec §3.3's two conditions for `observed` and `inferred` are not complementary**,
so the case every real direction falls into has no label and the threshold an implementation must
invent fills a gap in the *definition*. Part 6 was suspended: a result landing downstream of a
definition with a hole in it inherits the hole.

**The decision** (ADR-061): single-term dominance ratio with a declared factor `ρ`, plus an
**abstention** outcome — and the abstention is the more important half. The blast-radius table
showed nothing numeric consumes the label, so abstention's real cost is that OMI-1 becomes
satisfiable by declining to answer. Hence the **abstained fraction is a required output**, and `ρ`,
the band and the window are declared **per domain with justifications**, not defaulted.

**What it cost, itemised.** `Triage` gained a sixth value; `danger_triage`'s signature changed;
`DirectionDiagnostic` and `TriageResult` gained fields; four repository-owned documents were
reworded in place and `REVIEW_PACK.md` received a dated addendum; the audit gate gained declared
exceptions with two guards (ADR-062), the second of which exists because the first version lacked
it and failed correctly. **Four label-valued observations moved and two were retired; no numeric
observation moved.** The two retirements are numeric and were *retired rather than changed*, which
is the honest answer to "did a number move": their per-direction values are byte-identical and the
*filter* selecting them changed.

**Core §3.8 and Spec §3.3 were not edited, and I declined the instruction to edit them.** They are
the v1.3 specification under audit; all fifty-seven ledger entries cite locations in them, and
editing the text would make those citations unverifiable and make this repository the framework's
author. The replacement wording is in E-53's and E-55's `Proposed wording` fields.

### E-55, and its magnitude

**This is the entry with a publication consequence and it must not be softened.**

Measured on flagship, at its own declared query index:

| | superseded criterion | ADR-061 |
|---|---|---|
| `inferred` danger scores | `[7.9999999798, 4.3085686918, 0.0, 0.0]` | **`[0.0]`** |
| `unresolved` | — | contains **both** nonzero-danger directions |

**Flagship's two largest danger scores were counted as `inferred` — the framework's stated
differentiator, "what no tabular baseline can recover" — and no observation informs them at all.**
The mechanism is ADR-020's `else` branch: a direction can be classed identifiable by a tight
**prior** while carrying no Gramian information, and Spec §3.3 requires inferred directions to be
identifiable *from the total*, which they are not.

**The publication consequence, in one sentence a paper must obey: cite a per-direction dominance
ratio, never a count of inferred directions.** No form of the corrected criterion preserves a count
as the citable quantity — under abstention some directions carry no label at all, so a total
membership does not exist whatever factor is chosen. Two things make this smaller than it sounds and
should be said in the same breath: the substantive *conclusion* survives on both implemented
domains, and a ratio is **falsifiable where a count is not**. `docs/FIGURE-SOURCES.md` carries the
addendum: do not draw a figure that counts inferred directions.

**E-54, settled the same week, is why the corrected criterion is worth having.** Built as a
constructed intermediate chain — full-rank at every decay factor, so sensitivity decays without
being annihilated — the dominance ratio matched its closed form `λ^{−2(w+1)}` to `< 10⁻⁸` across
eight decay factors, labels moving `inferred → unresolved → observed` with turnover at
`ρ^{−1/(2(w+1))} = 0.8165`, **exactly where predicted before the run**. E-54's strong form —
"structurally uninformative across the board" — is **refuted**; its narrow form goes to High: *the
two declared classes of Core §3.9's dichotomy are the degenerate extremes of Core §3.8's
distinction, and the framework says so nowhere.* Both implemented domains sit at those extremes.

## 7. The discovery domain

A third domain, declared in Part 5(2) with no operator and built in Part 6 (ADR-060, ADR-064). Its
claim to being genuinely third is one property — the **control axis**:

| domain | control axis | decision | inverse |
|---|---|---|---|
| flagship | apparatus-determined | which route to run | process |
| contrast | usage-determined | how to operate an artefact | usage |
| **discovery** | **acquisition-determined** | **what to make** | **composition** |

**Every one of Core §4's seven items differs from both existing domains** — measured, not asserted.
It makes four diagnostics live that contrast could not: the validity report (two declared forms, so
the chain-level worst-case aggregation has something to aggregate), per-region species roles, an
**attainable region** with four distinct infeasibility verdicts, and `GLOBAL_POINT` on a fourth
independent instance.

**Two honesty items carried forward rather than discovered later.** The domain declares an erasure,
so §5.2a's measurement **predicts** it sits at flagship's degenerate extreme — recorded and asserted
so Part 6 could not mistake a trivial `observed` for an informative one. And declaring no erasure to
escape that extreme was rejected as dishonest: calcination erases precursor history, and choosing
the physics to suit the diagnostic is not available. The influence-median degeneracy is not escaped
either, and nothing in the declaration should escape it — pre-empting a framework decision inside a
domain declaration would hide the defect behind a domain choice.

**One number was not retuned.** The declared exclusion budget certified a realistic interior
formulation as `EXCLUDED_PAIR`. Rather than adjust it, the budget was **moved into the domain's
declaration**, because "these two cannot both be high" is a claim about a particular chemistry and
does not belong in domain-neutral code.

## 8. Part 6: the campaign experiment

**Pre-registered claim:** *the framework identifies when a campaign is failing due to model
insufficiency rather than exploration noise; a GP-based acquisition cannot.*

**The design result that mattered most is that the claim needs three arms.** "Insufficiency rather
than exploration noise" is a contrast between two *nuisances*, so a null arm and an insufficiency arm
cannot express it — a GP's fitted noise separates those perfectly well. The registered contrast is
insufficiency versus **calibrated noise**.

**ADR-026 disposition.** ADR-026's reasoning still holds, and the statistic it holds against is a
different statistic: its own rejection paragraph pre-authorised a second sign-aware monitor, and its
objection — a slack parameter with no Spec basis — does not apply to a standardised mean scaled by
the same `S_j` it already accepts. ADR-063 declares a **second** monitor; the default is unchanged.
The two have different null hypotheses: NIS asks whether the innovations have the predicted
*magnitude*, `z_n` whether they have the predicted *mean*, and Spec §10 names neither functional.

**Precondition, re-verified on the domain the claim is made on** (Part 5's dry-run was on contrast;
a statistic discriminating on one chain and inert on another is M11.4's failure): axis signal
`1.75 → 4.61` noise-widths, growth ratio `2.909`, and the divergence matched a closed form written
before the run — `z_n ∝ √n` predicts `×2.000`, measured `×2.317`, the excess explained by a
*separately measured* acquisition-selection effect of `×1.264`.

### The result

| criterion | measured | threshold | outcome |
|---|---|---|---|
| 1 — framework separation at 32 samples | `3.1626` | `≥ 2.0` | **MET** |
| 2 — separation growth, 8 → 32 | `3.2076` | `≥ 2.0` | **MET** |
| 3 — comparator separation at 32 samples | `0.2324` | `< 1.0` | **MET** |

Identical at 12, 16 and 24 replicates. Thresholds were committed in an earlier commit than the
sweep, and `git diff` between them touches no threshold file — the mechanical form of "not
revisited".

**Both comparator separations, side by side, as pre-committed:**

| reading | separation |
|---|---|
| insufficiency vs **noise** (registered) | **`0.2324` σ** |
| insufficiency vs **null** (companion) | **`0.9937` σ** |
| ratio | `4.28×` |

Fitted noise / declared instrument sd: `NULL 0.9943` · `NOISY 1.1097` · `INSUFFICIENT 1.1748`. **The
attribution failure in three numbers**: the comparator reads a known noise level correctly with
nothing planted, and reads *both* nuisance arms as carrying extra unexplained variance, within `6%`
of each other. It knows something is unexplained and cannot say which of the two it is.

### Part 6's limits, stated as limits

- **At 8 samples the separation is `0.9860` — below one nuisance sigma.** The discrimination is not
  available at short campaign length. A campaign of eight samples cannot make this call.
- **The comparator's discrimination is weak in absolute terms on *both* contrasts and unstable
  across replicate counts** — on the null contrast it reads `1.57` at 12 replicates, `2.33` at 16,
  and `0.99` at the registered 24, while the registered contrast never approaches `1.0`
  (`0.47 / 0.49 / 0.23`).
  The claim rests on the ratio and the per-arm means, not on criterion 3's margin — a ceiling of
  `1.0` is easy to sit below when your instrument is noisy. The pre-written label printed
  `AMBIGUOUS` at the registered count because its gate reuses criterion 3's ceiling and the
  null-contrast reading landed a hundredth below; the label is recorded verbatim, not rewritten.
- **The variance match drifted on the judged seeds.** Exact to `0.05%` on the calibration seeds,
  `5.37%` on seeds `0..23`, in the direction that makes the noise arm the **weaker** nuisance. Not
  re-tuned: adjusting a registered value after seeing the sweep is what pre-registration forbids.
- **E-58's leg is deferred.** E-41's third criterion is a baseline comparison, and for a
  pre-registered *comparative* claim the baseline comparison **is** the registered quantity — so it
  cannot be evaluated before the thresholds without a peek. Criterion 3 was evaluated on an
  auxiliary contrast at gate time and on the registered contrast only in the sweep. A two-arm
  comparative experiment would have had no auxiliary contrast at all, and the proposed wording says
  so.
- **Scope of the construction.** One planted insufficiency, one domain, one acquisition. The monitor
  is **blind to symmetric insufficiencies** by design, and blind to insufficiencies contributing
  mostly *variance* rather than a mean shift — which is the same fact as the calibrated inflation
  coming out small (`1.160`), seen from the other side.
- **Two confounds were found in the direction that flattered the claim**, both before the thresholds
  existed: the comparator's diagnostic normalised by the campaign's own target spread (which made
  the GP read *lower* under insufficiency than under the null), and ADR-066's original calibration
  rule, which matched the arms on the comparator's own statistic and would have made criterion 3
  **true by construction**. Both replaced, both recorded in the code they changed.

---

## 9. What v1.5 leaves the framework

> v1.5 planning establishes that the framework's declared purpose has to include the *decision* a
> chain supports, not only the process it models, and that this is not a relabelling: a third
> decision kind — what to make — requires a third inverse problem with its own infeasibility
> certificate, a decomposition of composition into a conserved quantity, an aggregation functional,
> a region and a flux, and per-region species roles in which one species is simultaneously a
> control and a state. Six declarable categories the interface cannot express are now enumerated,
> and the seventh item's arity is doing more work than its content supports. Against that, the
> track's two sharpest findings are corrections to what the framework already claims: its stated
> differentiator against a tabular baseline was a categorical count, and on the reference domain
> that count included the two largest danger scores while no observation informed them — so the
> claim must be cited as a per-direction dominance ratio, which is falsifiable where a count is
> not; and the erasure concept, which Core §3.9's composability argument rests on, conjoins a rank
> condition with a gain condition that a real operator separates, while its first branch
> presupposes the sufficiency its second branch does not need. A pre-registered experiment then
> showed, on one construction, that a monitor built from the model's own *predicted* innovation
> covariance separates a state insufficiency from matched exploration noise where a
> Gaussian-process acquisition's fitted noise term absorbs both into one parameter — which is the
> framework's decision-support claim made falsifiable, and met, at a scale that also shows what it
> does not reach.

## 10. What v1.5 could not test

- **The v1.5 extension itself.** Every declaration is a declaration. The composition inverse is
  designed (ADR-053) and its infeasibility certificate is *reportable* against a declared
  attainable region, but **no composition inverse is solved anywhere**, and no decision loop is
  implemented on any domain — ADR-056 is design only, and two of its four diagnostics were measured
  to drive nothing.
- **Whether the acquisition-determined axis is operationally distinct from the apparatus-determined
  one.** ADR-060 names this as the measurement that would collapse the third decision kind into the
  first. Part 6 ran a campaign on the discovery domain but never compared *policies*, so the
  question stays open.
- **Anything about symmetric or variance-dominated insufficiencies**, per §8.
- **Core §2.5**, still — Spec §5.2's registration operator remains a declared anti-goal, so the
  ledger's largest group was never in scope. The same holds for closure-defect measurement, hybrid
  mode/guard structure, closed-loop confounding, the linear-Gaussian dichotomy proof, and every
  Tier II performance claim.
- **E-49's disposition.** Spec §10's monitor conflates a per-window statistic with a per-campaign
  aggregate and records which control limit was crossed nowhere. Both facts were measured; neither
  was fixed, and ADR-063's second monitor deliberately sits *beside* `DriftReport` rather than being
  bolted onto it for that reason.
- **Real neural-operator training at scale**, unchanged from every prior milestone: analytic
  operators are ground truth throughout, and CLAUDE.md §2 is why that is the right order.
