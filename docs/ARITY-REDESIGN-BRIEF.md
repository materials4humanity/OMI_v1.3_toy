# The arity redesign — milestone brief

**Live document** (CLAUDE.md §10). **A brief, not an execution.** Nothing here is implemented;
executing it is a separate authorisation. Written after ADR-067 (the version rename) and ADR-068
(E-56/E-57's repairs), both of which are already in the tree and have closed part of the
sequencing.

**What it is.** Core §4's seven-item instantiation interface is under pressure from ten places in
the ledger. This brief organises them into **five decisions**, states which restructure and which
are additive, and prices the work — including the two things that turned out to cost most, neither
of which is code: the audit baseline and the four fillability sketches.

**Standing constraint.** Core and Spec stay unedited. Every proposed wording is already in its
ledger entry.

---

## 0. The five decisions

Ten pressures, five decisions. Four of the ten are one decision.

| | decision | pressures | restructures? |
|---|---|---|---|
| **A** | **What item 1 is.** Split it: what the material *is* versus what the operator family is *parameterised by*. Declare the `m`/`z` boundary against item 5, since resolution limits are a property of the instruments | E-46, E-29, E-31, composition's role/descriptor half (ADR-051, ADR-052) | **yes** |
| **B** | **What item 6 is.** Split by role — invariants-as-hard-constraints versus invariants-as-reachability-certificates have different mathematical requirements — and admit a declared-form category | E-32 / ADR-046 | **yes** |
| **C** | **What the declaration is for.** State the decision the chain supports and the scope features it claims | ADR-048, E-44 (and E-52's homeless scope-exit criterion) | no — additive |
| **D** | **Declarations change.** A declaration needs lineage of its own, distinct from the framework's claim target | E-40 | no — additive |
| **E** | **The symmetry group.** Declare a group action on state components | E-30 | no — additive, and independent of A–D |

**E-01 is not a pressure on the arity.** Core §7.2's table having seven rows that cover six of
Core §4's items is a *presentation* defect. It is evidence that the count is loose, and it becomes
a **test obligation** (§3 below), but it argues for no particular number.

### Why A and B restructure and C, D, E do not

`omi.interface.diff` iterates `fields(InstantiationDeclaration)`. C, D and E do not touch that
carrier at all — as built (ADR-070), each lands on a wrapper class instead, so `diff`'s output is
untouched rather than merely stable. Either way the point below holds: additive work cannot
surface a mis-typing *inside* an existing item, whether the addition appends a key or, as it
turned out, doesn't touch the seven-item carrier at all.

E-46's finding is a **mis-typing inside** item 1. Appending an item 8 "operator-family
parameterisation" leaves item 1's charter still covering both things, so a domain could declare
its parameterisation in either place and `diff` would report two identical domains as different.
**Appending cannot surface a mis-typing inside an existing item; only re-chartering can.** Item 6's
two roles are the same shape.

**One mitigating fact, checked:** neither `FLAGSHIP_SCHEMA` nor `CONTRAST_SCHEMA` carries a
parameterisation, `SDL_SCHEMA` deliberately excludes composition, and none of the four sketch
schemas carries one either — every component in all seven schemas is genuinely evolving state. So
re-chartering item 1 changes what the charter *means* without forcing content to move. That makes
A cheaper than feared in code and no cheaper in judgement.

## 1. The re-baselining plan

**ADR-062's own trigger has fired.** Its *what would change this decision* reads: "A second
declared-exception file arriving for an unrelated change would be the signal that label semantics
are churning rather than being corrected once — at which point the right move is a versioned
baseline per criterion rather than an accumulating exception list." The redesign is that second
file. So: **versioned baseline per criterion, not a longer exception list.**

### What a versioned baseline means concretely

One baseline file per **criterion generation**, each frozen at the commit that closed it, each
naming the criterion it was produced under:

```
audit/baselines/v13-items7.json          # 267 rows, frozen at M11's 57f7db8 — today's file, renamed
audit/baselines/redesign-itemsN.json     # written at the redesign's close
audit/BASELINES.md                       # which criterion each was produced under, and its commit
```

The gate takes a baseline path (it already does) and compares only within one generation. Nothing
is ever rewritten; a new generation is *added*.

**How a reader verifies a pre-redesign claim after the redesign.** They check out the commit the
baseline names, or they read the frozen file directly. A v1.3-items-7 claim — "flagship and
contrast differ on all seven items" — stays verifiable **forever, as a v1.3-criterion claim**,
because the file recording it is never edited and the criterion it was produced under is named
beside it. What they must *not* do is compare a v1.3-items-7 observation against a
redesign-items-N run; the generation label is what makes that mistake visible rather than silent.
That is the same discipline ADR-061 applied to the observed/inferred criterion, which is why
`superseded_label()` still exists in the oracle modules: **a repository cannot show why it changed
a criterion using only the criterion it changed to.**

### What happens to the 514-observation invariant

It does not survive, and it should not. Today's run produces 514 observations and the gate compares
them against a 267-row baseline, reporting 248 as "newly added" — a number that has been growing
since M11 and carries no information. Under versioned baselines:

- the **v1.3-items-7** generation freezes at its 267 rows and is never re-run for comparison;
- the **redesign** generation starts from a full run at the closing commit, so "newly added" is 0
  by construction and any later growth is meaningful again;
- the invariant becomes *per generation*: **no undeclared movement within a generation**, which is
  what ADR-042's audit-preservation gate was always trying to say.

### And the keying defect this scoping found — E-60

**The gate keys observations by `name` alone.** 267 baseline rows carry only **223 distinct
names**, so **44 rows (16.5%) collapse in the dict comprehension and have never been compared.**
Worst groups: `residual` (10), `max_abs_error` (8), `xi_a_hat` / `xi_d_hat` (5 each). Filed as
**E-60** in the ledger's §13.

Every PASS this repository has reported — including this session's — is a true statement about
**223 of 267** observations, not 267. Nothing was hidden by an action taken here; the dropped rows
were already unaudited when the baseline was committed at M11. But the guarantee is 16% narrower
than every report implied.

**The repair belongs in this re-baselining and not before it.** Key on `(test, name)`. Doing that
to the *existing* baseline would surface 44 previously-invisible observations at once, every one
reading as "newly added" — noise indistinguishable from a real movement. Doing it as part of
writing a new generation is free: the new baseline is written keyed by the pair from the start.

## 2. The nine diff retirements

Following the E-53 fix's precedent exactly: an observation whose *meaning* changed is **retired and
reissued under a new name**, never mutated under the old one, because reusing the name is the one
way a change can move a value while appearing not to.

Nine dict-valued `diff` observations, each keyed by the seven item field names, so all nine move
when the field set moves:

| retired | replaced by |
|---|---|
| `diff_result` | `diff_result_adr069` |
| `catalyst_under_operation_vs_flagship_diff` | `catalyst_under_operation_vs_flagship_diff_adr069` |
| `catalyst_under_operation_vs_contrast_diff` | `catalyst_under_operation_vs_contrast_diff_adr069` |
| `crystallisation_formulation_vs_flagship_diff` | `crystallisation_formulation_vs_flagship_diff_adr069` |
| `crystallisation_formulation_vs_contrast_diff` | `crystallisation_formulation_vs_contrast_diff_adr069` |
| `device_yield_vs_flagship_diff` | `device_yield_vs_flagship_diff_adr069` |
| `device_yield_vs_contrast_diff` | `device_yield_vs_contrast_diff_adr069` |
| `layerwise_additive_vs_flagship_diff` | `layerwise_additive_vs_flagship_diff_adr069` |
| `layerwise_additive_vs_contrast_diff` | `layerwise_additive_vs_contrast_diff_adr069` |

**Two corrections to my own earlier count, because the earlier number was loose.** First, there are
**ten rows** behind these nine names: `diff_result` is one of E-60's duplicated names, recorded by
two different tests with coincidentally identical values, and **one of the two is unaudited today**.
Second, two further observations are diff-*derived* and also move —
`invariants_literal_differs` and `invariants_structural_differs`, both booleans from the
flagship/contrast comparison — so the honest total is **eleven names, twelve rows**, not nine.
Under versioned baselines none of them needs a declared exception at all: they stay valid in the
v1.3-items-7 generation and simply do not exist in the new one.

### The one claim that cannot be honestly retired — and it is a finding

**`diff_result` as recorded by `test_specific_inversions_named_in_core_section_7_2` has no
replacement, because the comparison itself ceases to be meaningful.**

That observation pins ADR-034's mapping of **Core §7.2's seven published rows** onto six of Core
§4's items. §7.2's table is text in the issued v1.3 specification. After a re-charter of item 1
there is no §7.2 row corresponding to the new item 1a/1b split — the table was written against an
item list that no longer exists, and mapping it onto the new one would require deciding, row by
row, which new item each row now means. **That decision is exactly the judgement E-46 says
appending cannot surface**, so making it silently inside a retirement's `replaced_by` field would
smuggle the redesign's central question into an audit annotation.

So the honest disposition is to retire it **without** a replacement, recording that the comparison
ceased to exist. **ADR-062's guard forbids that**: a retirement must name a replacement present in
the run, precisely so that "retired" cannot be used to delete an inconvenient observation. The
guard, which is right, blocks the one legitimate deletion.

**Versioned baselines dissolve this rather than needing an exception.** In the v1.3-items-7
generation the mapping observation stays valid and audited forever — it *is* a v1.3 result, and
§7.2 *does* name v1.3's items. In the redesign generation there is simply no such observation,
because there is no published table for the new item list to be mapped against. Nothing is
retired, nothing is deleted, and no `replaced_by` has to lie. **This is the strongest single
argument for the versioned baseline over an extended exception list**, and it was found by looking
for a claim that could not be honestly retired rather than by planning the migration.

## 3. `test_interface_diff.py` rebuilt — E-01 as a test obligation

Today the file hard-codes `CORE_7_2_ROW_TO_INTERFACE_ITEM` and asserts
`len(...) == 7` alongside a comment that the seven rows cover only six items. That is E-01's
finding **pinned by hand**: a human wrote the mapping down, and a change to the item list makes the
literal stale without any test noticing.

Rebuild so the comparison table is **regenerable from the item list**:

- the declaration exposes its items as data — name, charter, and which §7.2 row (if any) names it;
- the test *derives* the row→item mapping and asserts the properties E-01 actually found: that the
  published table has seven rows, that they cover strictly fewer distinct items than the interface
  declares, and **which** item has no row;
- adding or re-chartering an item then changes the derived mapping automatically, and a new item
  with no §7.2 row is reported rather than silently absent.

**This converts E-01 from a presentation defect into a standing check**, and it is the one place
the redesign makes an existing finding *harder* to lose rather than easier.

## 4. The four sketches — re-derived, not reformatted

`src/omi_domains/sketches/` holds four M10 fillability sketches: `catalyst_under_operation`,
`crystallisation_formulation`, `device_yield`, `layerwise_additive`. Under CLAUDE.md invariant 11
each is **evidence for the generality claim** — a sketch that fills, or fails to fill, the items
for a domain outside flagship and contrast. A re-charter means each verdict is re-*established*,
not reformatted.

**What it costs.** 20 tests in `tests/test_sketches.py`, and per sketch: re-read the physics against
the new charter for A and B, then answer the **new** items C, D and E ask, which no sketch has ever
been asked. The mechanical part is small; the judgement part is the whole cost.

**Is any verdict at risk of changing? Measured, not guessed.** No — **none of the four schemas
carries a parameterisation-like component**; every component in all four is genuinely evolving
state (checked: dispersion, site fractions, coverages, PSD moments, defect densities, thermal
budget, sheath potential, residual stress, bond state). So no sketch's item-1 *content* has to
move, and no existing verdict flips.

**The risk is the opposite one: new verdicts appear, and some may be "cannot fill".** That is not a
problem to be managed — invariant 11 says a sketch that cannot fill an item **is a finding**. Two
sketches are the likely sources, and naming them in advance is the point of saying this before
executing:

- **`crystallisation_formulation`** — a *formulation* domain. Decision A will ask it to declare an
  operator-family parameterisation for the first time, and a formulation's composition is exactly
  the quantity E-46 separates. Expect a substantive new declaration, or a stated inability.
- **`catalyst_under_operation`** — a supported catalyst under service. Same question, and it also
  overlaps the discovery domain, so its answer is checkable against a built domain rather than only
  against prose.

`device_yield` and `layerwise_additive` are process domains whose parameterisation is a tool or
recipe index; Decision A's item 1b should be straightforwardly fillable there, which makes them the
control cases.

## 5. The `observe()` staleness lint — E-59, scheduled here

**Fail when a bound string quotes a literal that no longer matches the recorded value.** Parse the
`bound` for quoted literals and bare numerics; where one is present, require it to be consistent
with the recorded `value`.

Scheduled here rather than earlier because it is **new capability**, and here specifically because
this milestone already touches every declaration, rewrites the baseline, and re-derives the sketch
verdicts — so it is where a verification-discipline change is cheapest to land and hardest to
forget. E-59's instance cost nothing (a post-baseline observation), and that it cost nothing was
luck.

**Expect it to fail on existing observations when first switched on.** That is the point, and the
first run's failures should be triaged and reported rather than suppressed — the same handling
`superseded_label()` got. Budget for it.

## 6. Cost across the 68 affected tests

Six files hold 68 tests that touch a declaration or `diff` directly:

| file | tests | logic change or mechanical? |
|---|---|---|
| `tests/test_sketches.py` | 20 | **logic** — §4: verdicts re-derived, new items answered |
| `tests/test_sdl_declaration.py` | 12 | **logic** for the items A and C touch; mechanical elsewhere |
| `tests/test_flagship_constitutive.py` | 12 | **logic** — item 6's split is Decision B, and this file is where the declared-form category is exercised |
| `tests/test_extended_boundary.py` | 10 | **mechanical** — it asserts field *names* of the carriers (`["v13_core", "constitutive_forms"]`), so it moves with the field list but its claims are unchanged |
| `tests/test_conformance.py` | 9 | **mechanical**, unless a new item enters the OMI level table — which is a Decision C question, not settled here |
| `tests/test_interface_diff.py` | 5 | **rewritten** — §3 |

**Split: roughly 44 logic, 24 mechanical**, with the caveat that `test_conformance.py`'s 9 move
into the logic column if Decision C adds an item to the level table.

**Three conformance-domain files, all affected, all mechanically:** `test_conformance_flagship.py`,
`test_conformance_contrast.py`, `test_conformance_omi2_refusal.py`. They construct
`ConformanceInputs` from declarations, so they follow the field list; none asserts on the item
*count*. The OMI-2 refusal file is the one to watch — its value is that it names the specific unmet
items, and a new item changes that list, so its assertion text needs re-reading even though its
structure does not.

**Three oracle files, affected unevenly:**

- `tests/oracles/test_known_empty_slot.py` — **mechanical**. It builds a Γ-only schema to prove the
  machinery does not assume a populated `m`/`z`; a re-chartered item 1 does not change that.
- `tests/oracles/test_known_envelope.py` — **logic**. It carries E-32's evidence that item 6's split
  is a *replacement* rather than a relaxation, which is Decision B's own subject matter.
- `tests/oracles/test_contrast_diagnostic_trace.py` — **logic, and it is where E-52 lands**. It
  records that no item of Core §4's seven bounds contrast's terminal voltage. Decision C is what
  gives the scope-exit criterion a home, so this test's finding either resolves or is restated as
  narrower.

## 7. Can it be one commit? No — three stages, and the audit gate is why

**It must be staged, and A and B both moving the field set is the reason.** The gate must pass at
each step, and a single commit that re-charters item 1, splits item 6, adds three items and rewrites
the baseline would produce one enormous diff in which a real movement and a deliberate one are
indistinguishable — which is precisely the failure ADR-042's gate exists to prevent.

| stage | contents | gate posture |
|---|---|---|
| **1 — additive** | Decisions **C, D, E**: new items, no charter changes | passed against a versioned baseline (`audit/baselines/v13-items7.json`, ADR-069) — the baseline moved for the unrelated E-60 keying repair that preceded this stage, **not** because Stage 1 disturbed `diff`; see the correction below |
| **2 — restructure** | Decisions **A and B**: item 1 re-chartered, item 6 split. `test_interface_diff.py` rebuilt (§3) | passes against the **stage-1 baseline**, which is the new generation's first freeze |
| **3 — evidence** | The four sketches re-derived (§4), the `observe()` lint switched on (§5) | passes against the stage-2 baseline; the lint's first-run failures are triaged in this stage, not suppressed |

Staging this way also means **the versioned baseline is created before the restructuring**, so the
restructuring is audited against a generation that already has the new keying — E-60's repair lands
in stage 1 and pays off in stage 2.

> **Correction, filed after Stage 1 executed (ADR-070; CLAUDE.md §10 — live document, corrected in
> place).** This section's stage-1 row originally predicted *"`diff` gains keys; no existing key's
> value moves"* and that the appended keys would be *"where the versioned baseline is written"*.
> That is not what was built: all three of C, D and E's fields land on wrapper classes
> (`DecisionExtendedDeclaration`, `ConstitutiveForm`) rather than on `InstantiationDeclaration`
> itself, so `omi.interface.diff()` is **completely untouched** — not "gains keys that are all
> `False`", literally the same nine keys as before. See ADR-070 for the reasoning (principally:
> ADR-042's composition-over-modification precedent already answers this, and none of C/D/E is
> among Core §4's seven items). §6's caveat that `test_conformance.py`'s 9 tests move to the logic
> column "unless [Stage 1] adds an item to the OMI level table" also did not fire: the
> `error_control_claim` wiring is carried, not gated, so those 9 tests stayed mechanical. Both
> corrections reduce Stage 1's realised cost below what this section priced.

## 8. Sequencing, updated for what commits 1, 2 and Stage 1 closed

**Already closed, so no longer blocked by anything:**

- the version tangle (**ADR-067**) — the carriers are named for what they propose, so the redesign
  does not have to rename them again;
- **E-56 and E-57's repairs** (**ADR-068**) — done in `erasure.py` alone, and the sequencing
  analysis held: nothing pulled in a declaration change;
- **Decision C** (**ADR-070**) — `ScopeDeclaration` is built and populated on `SDL_DECLARATION`,
  and E-52's scope-exit criterion now has a home (`scope_exit_criterion`);
- **Decision D** (**ADR-070**) — `ConstitutiveForm.refines` / `.refinement_note`, with
  `KOCKS_MECKING_STRAIN_WINDOWED` exercising the real E-40 worked case;
- **Decision E** (**ADR-070**) — `SymmetryGroupAction`, declaring a group without making
  `omi.state.Metric` respect it (deliberately half-closed, stated in that class's own docstring);
- **ADR-068's deferred `conformance.py` wiring** — `error_control_claim` is carried on
  `ConformanceInputs` / `ConformanceReport`, deliberately **not** gating any OMI-0/1/2 requirement;
  whether it should is left to Decisions A/B.

**Still blocked by the redesign:**

- the **composition inverse** — needs Decision A to read the parameterisation as decision variables;
- the **validity-report → buy-physics path** — needs Decision B's declared-form category;
- **whether `error_control_claim` should gate an OMI-0/1/2 level** — Stage 1 carries it; gating it
  is a restructuring question for Decision A or B, deliberately left open by ADR-070;
- **further fillability sketches** — adding one before the item list settles means rewriting it.

**Not blocked, and available now if the redesign is deferred:**

- **E-49's disposition** — `DriftReport`'s two tails and the missing multiplicity correction, wholly
  inside `assimilate.py`;
- **E-58's precondition clause** — `proposed/holdout.py`;
- **E-51's warning** that the deficit is anti-correlated with campaign length — `sufficiency.py`;
- **E-47's surviving gap**, the unreported extrapolation factor — `proposed/constitutive.py`;
- **ADR-060's policy comparison** — whether the acquisition-determined axis is operationally
  distinct from the apparatus-determined one. Needs operators, not declarations, and it is the
  measurement that would collapse the third decision kind into the first if it came out the wrong
  way.

**Recommended order if the redesign is authorised:** stage 1 → stage 2 → stage 3 as above, with
E-49 and E-58 available in parallel because they touch no shared file. If the redesign is deferred
instead, do the four unblocked repairs first; they are small, independent, and each closes a
ledger entry that currently has no code behind it.
