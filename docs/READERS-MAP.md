# READERS-MAP.md — where to look for what

One page, for someone arriving to write from this repository. It points; it does
not restate. Start at `CLAUDE.md` for the prime directive, then use this.

## The framework and its two documents

| Document | Holds | Rule |
|---|---|---|
| `docs/OMI-v1_3-Core.md` | Claims — everything falsifiable | the framework |
| `docs/OMI-v1_3-Implementation-Spec.md` | Procedures — everything executable | the framework |
| `CLAUDE.md` | Prime directive, vocabulary, gap discipline, invariants | governance |

The job of the code is to make the framework's claims **measurable and
falsifiable**, not to predict well (`CLAUDE.md` §2). Read that before reading any
result as a performance number.

## The ledger: `docs/V1.4-EDITS.md` (57 entries, grouped by root cause)

Entry IDs are permanent (E-34 was withdrawn into E-29 and its number retired, never
reused). §1 holds the authoritative counts and the entry locator. The groups:

- **§2 — Core §2.5, the body-indexed state.** The single most consequential gap; four
  entries trace to it (E-14, E-21, E-22, E-25). A fifth, E-24, is grouped here because
  it *bounds* the gap: a promotion confirming Core §4 item 2 is **not** blocked by it.
- **§3 — Core §6.1's falsifiability claim** blocked by other unresolved rows (E-11, E-16).
- **§4 — declarations satisfiable without their property** (E-12, E-13, E-17, E-20,
  E-23, E-26, E-27, E-35, E-43). Nine entries, one shape.
- **§5 — the interface has no declarable category for something the physics needs**
  (E-29–E-32, E-40, E-44, E-46, E-52). Four of the five domain-assessment entries live here.
  Six missing categories, and the count is now the argument.
- **§6 — diagnostics blind to their own dominant error source** (E-03, E-04, E-18,
  E-05, E-06, E-15, E-19, E-33, E-45, E-47, E-48, E-49, E-51, E-53, E-54, E-56). Sixteen entries — the
  largest group. E-56 is the newest: an erasure that collapses six of seven state directions while
  *amplifying* the seventh, which Core §3.4's definition has no term for. E-45 alone carries an argument rather than a measurement and says so;
  E-47 was argued, then measured, then **narrowed by the measurement**.
- **§7 — status markers over/understating completeness** (E-01, E-02, E-08, E-09, E-10).
- **§8 — defects between individually sound prescriptions** (E-28, E-36, E-57).
  **E-57 is the one that reaches Core §3.9's own first branch**: a state-space erasure cannot
  bound error from a variable outside the state space, so condition (a) presupposes exactly the
  sufficiency Core §1 exists to measure.
- **§9 — a principle the framework never states** (E-37, E-39, E-41, E-42, E-50, E-55, E-58) —
  enlarged by the M11 extrapolation track and again by v1.5 planning. **E-55 is the one with a
  publication consequence**: the framework's differentiator against a tabular baseline must be
  cited as a per-direction dominance ratio, never as a count of inferred directions.
- **§10 — confirmations** (E-07 found nothing wrong; E-38 a proposal that worked).
- **§13 — not framework findings at all** (E-59, E-60): an `observe()` bound string is free text
  no lint checks, so a recorded value and its stated bound can diverge silently; and the audit
  gate keyed observations by *name alone*, so 44 of the 267 baseline rows shared a name and had
  never been compared — every reported PASS covered 223 of 267. **E-60 is repaired** (ADR-069): the
  gate now keys on `(test, name)`, the 44 previously-uncompared rows were checked and found
  byte-identical, and the baseline itself moved to `audit/baselines/v13-items7.json` under a new
  versioned-baseline scheme (`audit/BASELINES.md`) that ADR-062's own stated trigger called for.
  E-59's lint is still scheduled into `docs/ARITY-REDESIGN-BRIEF.md`. Both stay out of every
  framework total on purpose, so the count a paper cites is not inflated by defects in this
  repository's own tooling.
- **§11** re-reads every entry by *which practitioner intervention it blocks* (buy
  sensing / characterisation / data / physics / run experiments / declare out of
  scope), and finds the framework prices only one of six.
- **§12** states what the build never attempted.

**Provenance matters and is not flattened:** 52 entries were found by *attempting to
build* the framework; 5 (E-29–E-33, marked `[domain-assessment]`) by *reading it
against physics* (`docs/PHYSICS-ADEQUACY.md`).

## Which milestone produced which findings

| Milestone | What it built | Where |
|---|---|---|
| M0–M1 | scaffolding, state/operators/chain/readouts/interface | `src/omi/`, ADRs in `docs/DECISIONS.md` |
| M2 | erasure measurement, Lipschitz reports | E-04, E-18, E-19; F5 |
| M3 | observability: Gramian, danger triage, VOI | E-20; F8 |
| M4 | sufficiency deficit, probe sets, blocking trichotomy | E-03 |
| M5 | assimilation (EnKF, smoother, drift monitor) | — |
| M6 | Class B: tail transfer, N_eff, validation ladder | E-05, E-13, E-14; F6, F7 |
| M7 | conformance OMI-0/1/2 reporting | E-01 |
| M8 | learned operators + hard constraints | E-28 |
| M9 | inverse design, reachability certificates, decision layer | E-06, E-17 |
| M10 | remediation; baseline characterisation; falsification thresholds | E-16, E-26, E-27; `docs/M10.2-*` |
| M11 | the constitutive-form extrapolation track — **refuted** | E-35, E-38, E-39, E-40, E-41, E-42; F1–F4 |
| v1.5 planning, Parts 1–4 | **design and ADRs only, no code** — a declared composition axis, the interface-arity pressure it exposes, parameter equifinality | E-43, E-44, E-45, E-46, E-47; ADR-048–ADR-055, `docs/V1.5-PLANNING-BRIEF.md` |
| v1.5 planning, Part 5(1) | the contrast decision loop (**design only**), the statistic dry-run, and E-47 **measured** | E-48–E-52; ADR-056–ADR-058, `docs/V1.5-PART5-1.md` |
| v1.5 planning, Part 5(2) | the E-48 triage, and the SDL domain's **declaration** (no operators) | E-53; ADR-059–ADR-060, `docs/V1.5-PART5-2.md` |
| v1.5 planning, E-53 milestone | the observed/inferred blast radius, and the criterion **chosen but not implemented** | E-54; ADR-061, `docs/V1.5-E53-DECISION.md` |
| v1.5 planning, E-53 **fix** | the criterion **implemented**; `Triage.UNRESOLVED`; E-54 settled by a constructed intermediate chain | E-55; ADR-061 amended, ADR-062, `docs/V1.5-E53-FIX.md` |
| v1.5 planning, Part 6 | the campaign experiment **designed and pre-registered**: the discovery domain's operators, a GP acquisition comparator, a three-arm planted-insufficiency construction, the vacuity precondition re-verified on that domain | E-56, E-57, E-58; ADR-063–ADR-066, `docs/V1.5-PART6.md`, `docs/V1.5-PART6-PREREGISTRATION.md` |
| v1.5 planning, Part 6 **sweep** | the registered contrast run: all three criteria met (`3.16` σ, growth `3.21×`, comparator `0.23` σ), with the comparator's weak absolute discrimination reported as a limit on the claim's strength | — | `docs/V1.5-PART6-SWEEP.md` |

Parts 1–4 produced no implementation: five ledger entries found by *designing against*
the framework rather than building on it, E-45 marked derived-not-measured. Part 5(1) kept
the loop design-only but ran its inputs, its dry-run and the E-47 measurement — which
confirmed E-47's mechanism and refuted two of its claims. Part 5(2) triaged E-48 (the
degeneracy is a property of the *statistic*, and both implemented domains are degenerate at
opposite extremes) and declared a **third domain** — `src/omi_domains/sdl/`, a third decision
kind, with no operator and no campaign.

**v1.5 planning is closed and has its own track record: `docs/V15-PLANNING-RECORD.md`** — the
purpose extension, composition in five parts, the decision loop's two dark diagnostics, the E-53/E-55
interruption, the discovery domain, and Part 6's pre-registered result with both comparator
separations. Read it before the individual part documents.

M11 is the headline. Its account is `docs/M11-RECORD.md`; the two sweeps are
`docs/M11.4-EXTRAPOLATION.md` and `docs/M11.5-EXTRAPOLATION.md`, each preceded by a
pre-registration committed before its sweep existed.

## Live documents vs snapshots (read the header)

- **Live** (no commit stamp, corrected in place, always current): `CLAUDE.md`,
  `docs/COVERAGE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `docs/V1.4-EDITS.md`,
  `docs/PHYSICS-ADEQUACY.md`, `docs/M11-RECORD.md`, `docs/FIGURE-SOURCES.md`, this file.
- **Snapshots** (commit-stamped, corrected only by dated addendum): `docs/REVIEW_PACK.md`
  (`e43d858`, M0–M9 — predates M10/M11, see its addendum), `build/REVIEW-EXTRACT.md`,
  `docs/V15-PLANNING-RECORD.md`, `docs/V1.5-PART6-SWEEP.md`,
  `docs/M11.4-EXTRAPOLATION.md` and both `*-PREREGISTRATION.md` (each stamps its commit).

Two live documents were corrected *against M11's result*: `docs/PHYSICS-ADEQUACY.md`
§3.4 (its central "constitutive structure buys reach" claim, refuted and narrowed)
and `docs/V1.4-EDITS.md` §11's buy-physics row (a second gap: the validity signal is
on the wrong axis). E-32's own verdict block carries the same update.

## What the conformance levels do and do not certify

OMI-0/1/2 (`src/omi/conformance.py`, Spec §9.1) are a **reporting-completeness**
ladder: they certify that the diagnostics the framework requires were *produced and
reported*, **not** that predictions are accurate. Flagship reaches **OMI-1** with
real evidence; contrast reaches **OMI-0**, honestly blocked at OMI-1 on one item (no
erasure operator exists in that domain — a property of the physics, not a failure).
**Neither domain claims OMI-2**: the M9 machinery exists but no reachability
certificate or prospective trial is wired into a `ConformanceInputs` yet. A green
conformance level is never a claim that the chain predicts well.

## What this repository does NOT contain (`docs/V1.4-EDITS.md` §12)

By declared scope (CLAUDE.md §9 anti-goals), never attempted, so the build has
*nothing to say* about the framework's claims here — neither confirming nor denying:

- **Tier II boundary-value problems / FE² coupling** (except the Tier I½ exception,
  ADR-035). Every Tier II *performance* readout claim is unexercised.
- **Hybrid mode/guard/jump-map evolution** (Spec §5.1) — a hybrid control programme
  was declared (E-24) but never simulated.
- **Body-indexed state and the registration operator** (Spec §5.2) — which is *why*
  Core §2.5 (§2, the largest finding) was never going to be resolved here.
- **Closure-defect measurement** (Spec §6), **closed-loop confounding** (Spec §5.3),
  the **linear-Gaussian dichotomy proof** (Core §3.9), **compute-budget/modality
  numbers** (Spec §3.7, §12).

And two limits of what *was* built: **two domains with operators** — flagship plus a thin
contrast (the generality claim rests on those two, on M10's interface-fillability sketches,
and now on a **third domain declared but not built**: `src/omi_domains/sdl/` fills all seven
items and the decision-extension refinements with no operator behind them, which is evidence for
fillability and not for prediction) — and **no real neural-operator training at scale**:
analytic operators are ground truth throughout (CLAUDE.md §2: the operators are not the
point).

## What is scoped but not built

`docs/ARITY-REDESIGN-BRIEF.md` — Core §4's seven items under pressure from ten ledger entries,
organised into **five decisions** (two restructure, three additive), with the re-baselining plan,
the diff retirements, the sketch re-derivation and the three-stage sequencing. It also records the
one published comparability claim that cannot be honestly retired — Core §7.2's row-to-item
mapping, whose replacement does not exist because the comparison itself ceases to be meaningful.

**Stages 1 and 2 are now executed; Stage 3 is not.** Stage 1 (ADR-070) added the scope, lineage
and symmetry declarations on wrapper classes, leaving `omi.interface.diff` untouched. Stage 2
(ADR-071) **split Core §4 item 1 into 1a and 1b**, so this repository's interface declares eight
items where v1.3 issues seven, `diff` gained a `declared_parameters` key, `diff_result` was retired
with no replacement, and the audit baseline moved to a second generation
(`audit/baselines/redesign-items8.json`; see `audit/BASELINES.md`). Stage 3 — the `observe()`
staleness lint (E-59) — remains unbuilt. Read the brief for the plan and ADR-070/ADR-071 for what
was actually built, including two places where the brief's cost model was wrong.

## The reproduction path

`REPRODUCE.md` (repo root) — clean clone to every headline number, with commands,
expected output, and runtimes, verified in a fresh virtualenv. `docs/FIGURE-SOURCES.md`
— every result that could become a figure, its source, its regenerating command, and
the caveat that must travel with it.
