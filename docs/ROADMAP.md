# ROADMAP.md

Milestones, dependencies and exit gates. **Stop and report at every gate.**

## The ordering argument

Two decisions shape this ladder, and both are deliberate.

**Learning is late.** The obvious instinct is to build neural operators first,
because that is the visible machine-learning content. Resist it. The
framework's distinctive claims are about *measurement* — sufficiency,
observability, erasure, tails, calibration — and every one of them can be
developed and tested against **analytic operators**, which are faster, exactly
differentiable, and supply ground truth. Learning is one interchangeable
approximation class plugged in at M7. Building it first would shape the
substrate around a surrogate's needs and leave the measurement machinery
untested.

**Two domains early.** The instantiation interface (Core §4) is the mechanism
by which the framework's generality claim is made checkable. An interface built
against one domain is shaped to that domain. The contrast domain — no erasure
operators, usage-determined control, `Γ`-dominated state — is chosen precisely
because it inverts the flagship, and it must exist before the interface is
called stable.

Milestones M2–M4 correspond to the three Specification sections with complete
derivations (§1, §3, §4 — see `COVERAGE.md` Part III). They can be built
without inventing framework. Everything after M6 requires ADRs.

---

## M0 — Foundation

**Deliverable.** A repository that cannot silently do the wrong thing.

- `pyproject.toml`, `src/` layout, Python ≥ 3.11, pinned deps, offline.
- `src/omi/gaps.py`: `NotSpecified` exception carrying a `COVERAGE.md` id;
  a registry of every gap referenced in code.
- CI: lint, type-check, test, **run the suite twice and diff** (determinism).
- Vocabulary lint: fail if a banned domain term appears under `src/omi/`.
- Citation lint: every public function docstring cites `Core §x` or `Spec §x`.
- Coverage lint: every `NotSpecified` cites a live id in `COVERAGE.md`.
- `docs/DECISIONS.md` seeded with the ADR template.
- `tests/oracles/__init__.py` with the oracle protocol (a system exposing
  `truth()` alongside its observable interface) and **one** worked oracle to
  establish the pattern.

**Exit gate.** CI green on an empty framework. The three lints demonstrably
fail on a deliberately-planted violation, then pass once removed. Report the
verified `COVERAGE.md` (see PROMPT-01) before proceeding.

---

## M1 — Substrate

**Deliverable.** A typed chain that runs, on two domains.

- `state.py` — slot schema `(m, z, ν, Γ)`; `Metric` as a first-class object
  with aleatoric-sigma normalisation as default; `Ensemble` on `𝒫(𝒮)`.
- `operators.py` — `EvolutionOperator` protocol: `.step`, `.lift` (pushforward
  and Markov kernel), `.lipschitz` (local spectrum in a *declared* metric),
  `.is_erasure`. Semigroup identity checkable (Core §3.3).
- `readouts.py` — `Readout` declaring type (0/1/2) and class (A/B); Type-1
  returns an operator with memory; Class B carries a volume argument.
- `chain.py` — composition at the level of measures; rollout; trajectory
  recording.
- `omi_domains/flagship/` and `omi_domains/contrast/` — analytic operators
  only, each declaring the seven interface items of Core §4 in order.

**Exit gate.** Both domains run end to end. Interface declarations are
machine-diffable and the diff reproduces Core §7.2's inversion table.
Vocabulary lint passes. Semigroup residual ≈ 0 for analytic operators.

---

## M2 — Erasure and composition · *first distinctive claim*

**Deliverable.** Core §3.9's consequences become measurable.

- `erasure.py` — erasure measurement on ensembles; surviving subspace;
  **investigate OQ-2** (operator-level vs component-level) and record the
  outcome in `COVERAGE.md` Part IV.
- Error compounding: rollout-length error curves; Lipschitz spectra reported
  with their metric attached.
- **Investigate OQ-5** (metric dependence).

**Refuse:** `L_phys × L_num` decomposition (S-2.5, PASS-B) — the estimation
procedure is unwritten. Report the total only, with the metric declared.

**Exit gate.** Oracle with designed rank-`r` contraction: measurement recovers
`r` and the surviving subspace. OQ-2 and OQ-5 answered with evidence.

---

## M3 — Observability · *second distinctive claim*

**Deliverable.** Spec §3 in full. The highest-value module in the repository.

- Matrix-free Gramian by JVP/VJP; `Φ` never formed (S-3.5).
- Posterior covariance; Prop 3.1 as a documented *upper bound*, never quoted as
  achieved precision.
- Danger score; the four-way triage.
- **Observed vs inferred split, actually computed** — accumulate the Gramian
  term-by-term, retain per-term contributions, classify each eigendirection by
  concentration of information across `j`. *Inferred* directions are the
  framework's distinctive output and what no tabular baseline recovers; they
  are reported separately and prominently.
- Value of information by Woodbury; placement is A-optimal **on the readout,
  not on the state**.
- Worst case over an operating window, not the nominal point (S-3.6).

**Exit gate.** Blind-spot oracle: a designed unobservable direction appears in
`ker 𝐆`. Erasure-truncation oracle: rank(`𝐆_post`) ≤ `r`. Triage reproduces on
both domains, and the contrast domain's poor observation suite shows a
materially different dangerous set.

---

## M4 — Sufficiency · *third distinctive claim*

**Deliverable.** Axiom S becomes a constructive algorithm (Core §2.2).

- Deficit estimator with the three-term decomposition (S-1.2). **A raw response
  gap must not be obtainable from the public API.**
- `ProbeSet` with declared decompositions; **investigate OQ-1** (probe vs
  contrast); a `discriminating()` check that fails a probe set which can detect
  insufficiency but not separate two candidates.
- Augmentation loop (S-1.5), consuming the variance term from M3.
- Blocking-term trichotomy (S-1.7) — variance / learning / bias.

**Refuse:** campaign power analysis worked values (S-8, PASS-C) — formula only,
no numbers.

**Exit gate.** Known-insufficiency oracle: deficit recovers the constructed
gap; deficit ≈ 0 when matching on the full state; the raw statistic
demonstrably over-states. OQ-1 answered.

---

## M5 — Assimilation

**Deliverable.** Fusion dissolved; the chain as a partially observed Markov
process.

- EnKF along the chain; ensemble smoother; innovation sequence as drift
  monitor (Core §3.8, S-10 proposition only).
- Demonstrate a latent variable that no instrument measures becoming
  *inferred* — closing the loop with M3's classification.

**Exit gate.** Oracle with a known latent trajectory: smoother recovers it
within stated intervals. Innovation monitor detects a planted drift.

---

## M6 — Class B

**Deliverable.** Spec §4 in full. Independent of M2–M5; may be parallelised.

- Driver/tail separation with the join threshold and stability diagnostics.
- Tail transfer `ξ_D = β ξ_a`; the sanity check reproducing a known scaling.
- `N_eff` and dimensional reduction; `ℓ_D` estimation **with its error bar** —
  it is biased low on short domains and biasing it low over-predicts the size
  effect.
- Subset simulation and conditional generative sampling.
- The four-rung validation ladder, with the fractography rung runnable first.
- **Investigate OQ-3** (competing risks).

**Exit gate.** Known-tail oracle recovers `β ξ_a` across four `(α, β)` pairs
including a weakly-amplifying case. Ranking inversion reproduces. OQ-3
answered.

---

## M7 — Conformance OMI-0/1

**Deliverable.** The framework's own requirements, executable.

- `conformance.py` generating an OMI-0/1/2 report from a declared chain.
- The report **refuses to claim a level whose requirements are unmet**, and
  carries the declared metric alongside every metric-dependent quantity.
- The nine automated checks of S-9.2, each returning a residual not a pass/fail.

This is the forcing function that tells you whether the API is right: if a
requirement is awkward to emit, the abstraction above it is wrong.

**Exit gate.** OMI-0 claimable for both domains; OMI-1 for the flagship.
Attempting to claim OMI-2 fails with a specific list of unmet requirements.

---

## M8 — Learning

**Deliverable.** Neural operators as a pluggable approximation class.

- DeepONet / FNO behind the `EvolutionOperator` protocol; the analytic
  operators remain and remain the test oracle.
- Hard constraints as architecture (S-2.2), tested off-manifold with
  out-of-range controls.
- Training objectives (S-2.3) including semigroup consistency; stability-aware
  training (S-2.4); rollout-length curves.
- Grouped splits enforced at the data-loader level.

**Refuse:** backward error budgeting (S-2.6) and the refusal trigger (S-2.7),
both PASS-B.

**Exit gate.** A learned operator passes the same oracle tests as its analytic
counterpart, at stated tolerance. Constraint satisfaction holds off-manifold.
Rollout curve reported.

---

## M9 — Inverse design → OMI-2

**Deliverable.** Constrained optimal control with honest output contracts.

- Control parameterised in apparatus settings, never desired driving paths.
- CVaR / probability-of-conformance objectives; solution *sets* with trade-off
  structure; trust region.
- Invariant-based non-reachability certificates plus nearest reachable state
  (S-7.1 is PASS-B — **ADR required**).
- Decision layer (S-7.3, PASS-C — **ADR required**), including **OQ-4**:
  report which term makes a feasible set empty.
- Control inverse vs structure inverse kept distinct.

**Exit gate.** Known-unreachability oracle: certificate fires exactly outside
the bound. Infeasible-specification oracle: the binding term is correctly
identified. OQ-4 answered.

---

## M10 — Paper evidence

**Deliverable.** The evidence a framework paper needs and this repository
does not yet have. Every milestone through M9 is inward-facing (does the
implementation work); M10 is outward-facing (does the implementation supply
what a v1.4 paper needs to argue generality, competitiveness, and
falsifiability). Runs after Phase 3 of the post-M9 remediation work; do not
begin it before then.

### M10.1 — Four interface-only sketches (Spec §11.4)

Core §1.1 claims eight domain families; two are implemented and both are
physically adjacent. The generality claim rests on the interface being
fillable, and a filled declaration is evidence even with no code behind it
(CLAUDE.md §5 invariant 11).

One page each, seven items in Core §4 order, no implementation:

- **Layer-wise additive processing** — hybrid structure and body-indexed
  state at their most extreme.
- **Device yield** — Class B volume scaling should recover the classical
  defect-density model, making this independent confirmation of §3.6's
  mathematics from a field that has used it for decades.
- **Crystallisation and formulation** — polymorph selection as a bifurcating
  evolution operator, dissolution as a Class B readout.
- **One deliberately awkward case, chosen at M10.1 time** — a domain the
  interface is expected to *strain*, since a sketch that fills too easily
  proves less than one that exposes a missing slot.

Machine-diffable against the two implemented domains (reuse
`omi.interface.diff`). Any item a sketch cannot fill is a finding for
`docs/V1.4-EDITS.md`, and a more valuable one than a clean fill.

### M10.2 — Baseline characterisation (Spec §9.3, `[Pass C]`)

Spec §9.3 requires comparison against gradient-boosted trees and tabular
regression, and asks for a scored go/no-go table it does not supply. Both
domains are ground-truth simulators, so this is answerable without field
data — and answerable better than one dataset would allow.

Sweep the regime rather than running a single comparison: process-window
width relative to measurement noise, labelled-record count, and presence of
geometry-dependent (Type-2) responses. Report where tabular wins, where the
operator graph wins, and where the crossover sits. Include
**inverse-design hit rate**, not only forward accuracy — that is the axis
on which tabular models are structurally incapable rather than merely
worse, and it is the framework's real claim.

The honest outcome is the valuable one. Spec §9.3 already states that
narrow-window, densely-instrumented, forward-prediction-only production is a
case for *not* using OMI. Quantifying where that boundary falls converts a
qualitative caveat into a result.

### M10.3 — Falsification thresholds (Core §6.1, Spec §9.4, `[Pass D]`)

Core §6.1 lists six falsification criteria and the framework says of itself
that a criterion without a tolerance is not falsifiable (`docs/V1.4-EDITS.md`
E-11 records that only one of six is currently operationalised). Supply, at
minimum, the *procedure* for setting each threshold per application, derived
from decision sensitivity, plus worked values for both implemented domains.

### M10.4 — Finalise `docs/V1.4-EDITS.md`

As a standalone document that reads correctly without the repository —
quoting rather than cross-referencing, since its audience is the framework's
authors, not this code.

**Exit gate.** Four sketches declared and diffed. The go/no-go table
populated with the regime boundary identified. Thresholds procedure with
worked values. `docs/V1.4-EDITS.md` complete and self-contained.

---

## Milestone dependency graph

```
M0 ──► M1 ──┬──► M2 ──► M3 ──► M4 ──► M5 ──┐
            │                              ├──► M7 ──► M8 ──► M9 ──► M10
            └──► M6 ─────────────────────  ┘
```

M6 is independent of M2–M5 and may run in parallel. M7 requires M2–M6. M9
requires M7 and benefits from M8 but does not require it — analytic operators
are differentiable and sufficient for the control problem. M10 requires M9
and the post-M9 remediation phases (docs/DECISIONS.md, docs/V1.4-EDITS.md)
to have run first.
