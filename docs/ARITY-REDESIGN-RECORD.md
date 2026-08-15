# The arity redesign — closeout record

**Live document** (CLAUDE.md §10): describes the repository's current state, corrected in place.
Companion to `docs/ARITY-REDESIGN-BRIEF.md`, which is the *plan*. Where the two disagree, the
brief carries the correction blocks and this record carries what was built.

**What the milestone was.** Core §4's instantiation interface was under pressure from ten places
in `docs/V1.4-EDITS.md`, organised by the brief into five decisions and three stages. All three
stages are executed. This record states what closed, what did not, and — the part that matters
most — **what remains open, by name**.

| stage | ADR | what landed | gate |
|---|---|---|---|
| 1 — additive | ADR-070 | `ScopeDeclaration` (E-44, E-52), `ConstitutiveForm.refines` (E-40), `SymmetryGroupAction` (E-30, half-closed), `error_control_claim` carried on conformance reports (ADR-068's deferral) — **all on wrapper classes**, `diff()` untouched | PASS against `v13-items7` with only E-53's pre-existing exceptions |
| 2 — restructure | ADR-071 | Core §4 item 1 **split** into 1a (`state_schema`) and 1b (`declared_parameters`), carrying `ParameterRole` (E-46, E-29). `INTERFACE_ITEMS` makes the item list data (E-01). Four sketch verdicts re-derived. Item 6 **not** split | FAIL against `v13-items7` on exactly ten rows, by construction → second generation `redesign-items8` frozen (547 rows) → PASS |
| 3 — closeout | ADR-072 | `observe()` bound checked at record time by three narrow rules, with coverage reported (E-59) | PASS against `redesign-items8`, **zero observations moved** |

---

## 1. The count is not stable, and this is the closeout's central statement

**The interface declares eight items. That is a waypoint, not a resting point.** Three ledger
entries propose *additional* items by their own proposed wording, and all three are currently
parked on wrapper classes rather than in the item list:

| pressure | its proposed wording asks for | where it lives here | status |
|---|---|---|---|
| **E-30** — symmetry group | "Add a **new declaration item** — deliberately not a sub-item of item 6" | `DecisionExtendedDeclaration.symmetry_group_actions` (ADR-070) | **half-closed, measured.** A domain can declare a group; `omi.state.Metric` still does not quotient by one. The `1.414`-distance demonstration for a 90°-rotated orientation descriptor stands unrepaired, and no built domain declares a group, so the second half is untested on real content |
| **E-32 / ADR-046** — declared constitutive form | ADR-046 chose "(b) a **new interface item**", noting it "makes the interface eight items" | `ExtendedDeclaration.constitutive_forms` (ADR-042/043) | **closed as content, open as placement.** Five real forms are declared and exercised; item 6 still *refuses* a constitutive form by name, so the framework-side role-scoping (6a/6b/6c) is unbuilt. ADR-046's own count assumed item 1 was whole — with the split, its option (b) lands at **nine**, not eight |
| **E-52** — scope-exit criterion | "Add an **eighth item** to Core §4: 8. Scope-exit criterion" | `ScopeDeclaration.scope_exit_criterion` (ADR-070) | **half-closed, and the domain the evidence came from does not carry it.** SDL declares a criterion; `contrast` — whose terminal voltage goes negative within forty intervals, which is E-52's evidence — has no `DecisionExtendedDeclaration` at all, so the finding stands exactly as measured |

**If all three land as framework items on top of the split, the interface is eleven items.**

**And the inconsistency this exposes is a finding in its own right.** This repository now holds
three declarations on wrappers whose entries propose them as items, and one (the parameter role)
*as* an item on the reasoning that a wrapper would leave it declarable in two places. Those
treatments cannot both be right in general. The distinguishing argument is available and ADR-071
rests on it — *a wrapper is safe where the content has no competing home in the item list, unsafe
where it does* — but it is a **repository** argument the framework does not make. If the next
issued specification adopts E-30, E-32 and E-52 as items while leaving item 1 whole, this
repository will have split the one item the framework kept and wrapped the three it promoted.
Exactly inverted. Flagged, not resolved: resolving it means deciding what the next specification
does.

**A fourth pressure may exist and is not assessed here.** See §5.

## 2. What actually closed

- **E-46** — resolved in code, and the pressure count it explicitly refused to settle is now
  settled *by construction* rather than by adjudicating item 1's charter: with the parameter never
  routed through the state schema, "does item 1's charter stretch" has no purchase. Its own
  prediction held exactly — "only the item number moves".
- **E-29 part 1** — resolved: the missing category exists, and is not a fifth slot, on E-29's own
  argument. **Part 2 is not resolved**, and the demonstration is in this repository: `flagship`'s
  three de-facto-static components still sit in item 1a and its item 1b is **empty**. The split
  supplies a destination; nothing detects that a quantity is in the wrong item. Expressibly
  different, still not detectably different.
- **E-01** — converted from a presentation defect into a standing check, and it paid on first run:
  it reported that the seven published §7.2 rows now cover six of **eight** items, with **1b and 6**
  row-less, without being asked. Its proposed framework wording was also *sharpened* by the
  exercise — the note E-01 proposes appending to §7.2 states a fixed count, which is the same
  pinned-literal defect one level up.
- **E-40, E-44, E-52, E-30** — declaration halves closed at Stage 1 (see the table in §1 for what
  each still leaves open).
- **E-59** — repaired at Stage 3. Value is **prospective**: its own instance was already fixed at
  ADR-067, so there was nothing to catch retroactively.
- **E-60** — repaired at ADR-069, with all 44 previously-unaudited baseline rows verified
  byte-identical before the generation was frozen.

## 3. What the milestone found that was not in the plan

**E-61, new**: items 1b and 2 are separated by the **scope** a declaration is written at — the
discovery domain's mean composition is a fixed index per chain and the control variable per
campaign — and Core §4 states no scope. Found by *filling* the item E-46 proposed, which is the
strongest pedigree available. Same shape as E-31's observer-relative `m`/`z` boundary, one boundary
over: **two of the interface's internal boundaries are now known to be relative to something the
declaration does not carry**, which suggests several items are properties of the *description*
rather than of the system. The code records the scope in free text and nothing more; inventing a
`scope` field would improvise across the gap.

**The brief's cost model was wrong four times, all in the same direction.** Recorded because a
plan that mis-priced its own work is evidence about planning, not just about this milestone:

| the brief predicted | what happened |
|---|---|
| Stage 1's C/D/E would make `diff` "gain keys", forcing a baseline rewrite | They landed on wrappers; `diff` untouched; no rewrite (ADR-070) |
| `test_conformance.py`'s 9 tests move to logic "if [Stage 1] adds a level-table item" | It did not; `error_control_claim` is carried, not gated; they stayed mechanical |
| Twelve rows move at Stage 2 | Ten did — the two `invariants_*` booleans are about item 6 and a new key elsewhere does not touch them |
| `test_flagship_constitutive.py` (12) and `test_known_envelope.py` are *logic* changes, on item 6's split | Item 6 was not split; both mechanical or untouched |

The one price paid in full was §4's: the four sketch verdicts were genuinely re-derived.

## 4. The sketch verdicts, and the honest reading of them

All four sketches fill item 1b; **no pre-existing verdict changed**, and no schema lost a component
to 1b — checked, not assumed. Details in `docs/SKETCHES.md`.

**Four-for-four is weaker evidence than it looks.** An item everything fills may be well-posed or
may be too loose to discriminate. What keeps it from being vacuous is the negative case among the
*implemented* domains: `flagship` — the domain E-29 was written about, flat-rolled steel, where
composition-as-operator-index is the paradigm case — declares item 1b **empty**. So the item does
separate declarations, and it produces an inversion worth stating: **the domain with the strongest
claim to needing item 1b is the one whose declaration leaves it empty, while four domains outside
the framework's implemented pair fill it without strain.**

## 5. Not assessed: a fourth pressure was raised in the Stage 3 authorisation and cannot be evaluated here

The Stage 3 authorisation asked for a disposition of **E-63**, concerning a **kesterite** domain
whose occupant is "neither state nor parameter under the eight-item charter", and asked that a
qualification be recorded against a **white paper's kesterite row**.

**None of the three exists in this repository, verified rather than assumed.** The ledger runs
E-01 → E-61 with E-34 withdrawn — there is no E-62 or E-63. `kesterite` appears nowhere in the
working tree, and nowhere in the full history of either branch (`git grep` over all reachable
commits). No white paper is present; the phrase appears twice, both times naming an *external*
document this repository does not contain.

**So the count-stability statement in §1 is made over three pressures, not four.** If the kesterite
occupant is real and is neither a slot occupant nor an operator-family index, that is a **fourth**
pressure on the item count and §1 is incomplete until it is assessed. Whether it implies a third
role in item 1, a relaxation of the constancy requirement, or a refusal pending Core §2.5 is not
decidable from anything in this repository, and choosing among those readings without the domain in
front of us would be inventing framework — the one move CLAUDE.md §4 rules out, and the one whose
output would be most likely to reach a paper.

**This section is the closeout's admission of incompleteness, and it is deliberate.** A milestone
that ended by claiming closure it does not have would be the failure this build has consistently
refused.

## 6. Verification state at closeout

| check | result |
|---|---|
| full suite | **413 passed, 2 skipped** |
| `mypy --strict src tests` | clean, 152 files |
| lints (vocabulary, citations, gap citations, coverage evidence, observation bounds) | 25 passed |
| audit gate vs `redesign-items8` | **PASS** — 547 of 547 byte-identical, 0 changed, 0 missing, 0 declared exceptions |
| determinism | two independent full runs reproduced all 547 observations byte-identically |
| `observe()` bound coverage | 23.4% of 547 mechanically checkable (100 relational, 18 bare literal, 10 quoted literal); **reported, not targeted** |

**Core and Spec remain unedited**, as they have throughout. Every proposed framework wording lives
in its `docs/V1.4-EDITS.md` entry and nowhere else.
