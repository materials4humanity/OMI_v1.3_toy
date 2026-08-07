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

## The ledger: `docs/V1.4-EDITS.md` (43 entries, grouped by root cause)

Entry IDs are permanent (E-34 was withdrawn into E-29 and its number retired, never
reused). §1 holds the authoritative counts and the entry locator. The groups:

- **§2 — Core §2.5, the body-indexed state.** The single most consequential gap; four
  entries trace to it (E-14, E-21, E-22, E-24, E-25).
- **§3 — Core §6.1's falsifiability claim** blocked by other unresolved rows (E-11, E-16).
- **§4 — declarations satisfiable without their property** (E-12, E-13, E-17, E-20,
  E-23, E-26, E-27, E-35, E-43). Nine entries, one shape.
- **§5 — the interface has no declarable category for something the physics needs**
  (E-29–E-32, E-40, E-44). Four of the five domain-assessment entries live here.
- **§6 — diagnostics blind to their own dominant error source** (E-03, E-04, E-18,
  E-05, E-06, E-15, E-19, E-33).
- **§7 — status markers over/understating completeness** (E-01, E-02, E-08, E-09, E-10).
- **§8 — defects between individually sound prescriptions** (E-28, E-36).
- **§9 — a principle the framework never states** (E-37, E-39, E-41, E-42) — enlarged
  by the M11 extrapolation track.
- **§10 — confirmations** (E-07 found nothing wrong; E-38 a proposal that worked).
- **§11** re-reads every entry by *which practitioner intervention it blocks* (buy
  sensing / characterisation / data / physics / run experiments / declare out of
  scope), and finds the framework prices only one of six.
- **§12** states what the build never attempted.

**Provenance matters and is not flattened:** 38 entries were found by *attempting to
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

M11 is the headline. Its account is `docs/M11-RECORD.md`; the two sweeps are
`docs/M11.4-EXTRAPOLATION.md` and `docs/M11.5-EXTRAPOLATION.md`, each preceded by a
pre-registration committed before its sweep existed.

## Live documents vs snapshots (read the header)

- **Live** (no commit stamp, corrected in place, always current): `CLAUDE.md`,
  `docs/COVERAGE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `docs/V1.4-EDITS.md`,
  `docs/PHYSICS-ADEQUACY.md`, `docs/M11-RECORD.md`, `docs/FIGURE-SOURCES.md`, this file.
- **Snapshots** (commit-stamped, corrected only by dated addendum): `docs/REVIEW_PACK.md`
  (`e43d858`, M0–M9 — predates M10/M11, see its addendum), `build/REVIEW-EXTRACT.md`,
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

And two limits of what *was* built: **one flagship + one thin contrast domain** (the
generality claim rests on two, and M10's interface-fillability sketches; a third
domain is future work), and **no real neural-operator training at scale** — analytic
operators are ground truth throughout (CLAUDE.md §2: the operators are not the point).

## The reproduction path

`REPRODUCE.md` (repo root) — clean clone to every headline number, with commands,
expected output, and runtimes, verified in a fresh virtualenv. `docs/FIGURE-SOURCES.md`
— every result that could become a figure, its source, its regenerating command, and
the caveat that must travel with it.
