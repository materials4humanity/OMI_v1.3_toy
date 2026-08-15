# audit/baselines/ — one frozen file per criterion generation

**Live document** (CLAUDE.md §10). ADR-069's versioned-baseline scheme, replacing an
accumulating exception list once ADR-062's own stated trigger fired.

A generation is a frozen `build/observations.json` snapshot from a full-suite run at the
commit whose results are being preserved, keyed by `(test, name)` (ADR-069). A new
generation is written whenever the interface criterion the comparison is made against
changes in a way that would otherwise force another declared-exception file. Nothing here
is ever rewritten in place; a new generation is *added*.

| file | criterion | frozen at | rows | audited pairs |
|---|---|---|---|---|
| `v13-items7.json` | Core §4's seven-item interface, exactly as issued in v1.3 | `57f7db8` ("M10.4 Part B: plan the proposed-v1.4 constitutive track") — the last commit before `src/omi/` was touched by the proposed constitutive extension | 267 | **267** — every `(test, name)` pair, verified (see below) |
| `redesign-items8.json` | The **eight-item** interface: Core §4 item 1 split into 1a (state schema) and 1b (declared parameters), items 2–7 unchanged — ADR-071, implementing `docs/V1.4-EDITS.md` E-46. Item 6 is **not** split | the arity redesign's Stage 2 commit | 547 | **547** — every `(test, name)` pair, unique by construction |

### Why the second generation was opened (ADR-071)

`omi.interface.diff` iterates the declaration's fields, so splitting item 1 gave it a ninth key
(`declared_parameters`) and every `diff`-dict observation moved by construction. Measured against
`v13-items7` immediately before the freeze, **exactly ten rows moved and nothing else**:

| what moved | rows | why |
|---|---|---|
| eight sketch-versus-domain `diff` dicts | 8 | each gained one key, value `True`; no pre-existing key's value changed |
| `diff_result`, recorded by two different tests | 2 | **retired with no replacement** — see below |

Nothing else in the 267-row baseline moved except E-53's four already-declared label changes and its
two already-declared retirements. **No numeric observation moved at all.** So the item-1 split
changed what the interface *declares* and nothing about what any estimator *measures*, which is the
property a re-charter is supposed to have and is checkable here rather than asserted.

`docs/ARITY-REDESIGN-BRIEF.md` §2 predicted "eleven names, twelve rows". The realised count is ten
rows: `invariants_literal_differs` and `invariants_structural_differs` did **not** move, because
both are booleans about item 6 and a new key elsewhere in the dict does not touch them.

**`diff_result` is retired with no replacement**, the one retirement ADR-062's guard would have
blocked and the case the brief flagged in advance as un-retirable. It recorded the raw `diff()`
dict, and one of its two recordings pinned ADR-034's mapping of Core §7.2's seven published rows
onto six of Core §4's items — a hand-written claim that `tests/test_interface_diff.py` now
*derives* from `omi.interface.INTERFACE_ITEMS` instead of asserting. The comparison ceased to exist
rather than moved, so no `replaced_by` would be honest. The versioned scheme is what makes that
disposition legitimate: `diff_result` remains valid and audited **forever** in `v13-items7`, under
the seven-item criterion it was true of, and simply does not exist here.

**How a reader verifies a pre-redesign claim against this generation, forever, after
later generations exist.** Check out `57f7db8` (or any later commit up to the one that
freezes the *next* generation) and run `scripts/check_audit_gate.sh
audit/baselines/v13-items7.json`. The file is never edited in place, so the comparison
means the same thing at any later commit that still carries it. A claim stated against
this generation — "flagship and contrast differ on all seven items" — is a claim about
**v1.3's seven-item criterion specifically**, and remains checkable under exactly that
criterion no matter what a later generation adds or restructures. What a reader must
**not** do is compare an observation frozen here against a later generation's run: the
generation label is what makes that mistake visible rather than silent, the same
discipline ADR-061's `superseded_label()` uses for the observed/inferred criterion.

## Why this file exists (ADR-062's trigger, fired)

ADR-062 declared exceptions for the E-53 criterion change and stated its own limit: *"A
second declared-exception file arriving for an unrelated change would be the signal that
label semantics are churning rather than being corrected once — at which point the right
move is a versioned baseline per criterion rather than an accumulating exception list."*
The arity redesign is that second file. Rather than extend `audit/e53-label-changes.json`
or add a sibling exception file for a change with nothing to do with E-53, this repository
moves to versioned baselines here.

## The re-keying, and what it found (E-60; ADR-069)

The gate previously keyed observations by `name` alone. **17 of the v1.3 baseline's 223
distinct names are each recorded by more than one test**, so a `{name: row}` dict
comprehension silently kept only the last-written row per name and **dropped 44 of the
267 rows from comparison — 16.5% of the baseline, never audited.** Filed as
`docs/V1.4-EDITS.md` E-60.

**Verified before this generation was frozen, per the finding's own recommendation: zero
drift.** All 44 previously-unaudited rows were checked against a fresh full-suite run at
the commit that repairs the keying, matched by `(test, name)`:

| check | result |
|---|---|
| previously-shadowed rows, re-audited | **44 / 44** |
| byte-identical to their recorded baseline value | **44 / 44** |
| drifted | **0** |
| `(test, name)` pairs unique within the baseline | **yes — 267 rows, 267 pairs** |
| `(test, name)` pairs unique within a fresh full-suite run | **yes — 514 rows, 514 pairs** |
| full 267-row baseline, re-keyed, against the fresh run | 261 byte-identical, 4 changed / 2 retired (both **E-53's own declared exceptions**, unaffected by the re-keying), 0 undeclared |

So the repair changed **what was checked**, not **what the checks found**: nothing in
this repository's audit trail was ever silently wrong, and every number this repository
has reported under the old keying remains correct. The guarantee it rested on was 16%
narrower than stated until this generation was frozen.

## What happens to the observation-count invariant

It is per-generation, not global. A run today produces roughly twice `v13-items7`'s row
count; comparing that whole number against 267 and calling the difference "newly added"
carries no information, because the generation the comparison is made against determines
what counts as new. Each generation's own row count is its own reference point, stated
in the table above, and is not summed across generations.

## Adding a generation

1. Land the interface change (the whole change, not a partial one — a generation frozen
   mid-change is not a criterion, it is an accident).
2. Run the **full** suite fresh.
3. Copy `build/observations.json` to `audit/baselines/<name>.json`.
4. Add a row to the table above: the criterion in one sentence, the commit, the row
   count, and confirm every row is `(test, name)`-unique (the gate itself refuses to run
   against a baseline that is not).
5. Never edit an existing row's file. A correction to a frozen generation is a **new**
   generation, named for what changed, exactly as CLAUDE.md §10 requires for any other
   snapshot.
