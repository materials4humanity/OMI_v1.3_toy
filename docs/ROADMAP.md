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

## M11 — The proposed-v1.4 constitutive track

**Planned at M10.4; designed in ADR-042 – ADR-045 (docs/DECISIONS.md); not
implemented.** This is the first milestone whose subject is an *extension to the
framework* rather than an implementation of it, and the ordering constraint that
governs it is unlike every earlier milestone's: **the v1.3 results must survive
it.** The repository's OMI-0/1 claims, fourteen oracles, and thirty-four ledger
findings are v1.3 results and are the evidence the paper rests on.

The question the track exists to answer: **does constraining an operator to a
declared constitutive form buy extrapolation reach outside the training
envelope?** That is the claim behind `docs/V1.4-EDITS.md` E-32, and it is the one
thing in the ledger whose resolution would give §10's *buy physics* row a
mechanism for the first time.

### M11.1 — The v1.3/v1.4 boundary (ADR-042)

`specification_version` as a required field on `ConformanceReport`, with
cross-version comparison refused; `ProposedV14Declaration` wrapping the
seven-item declaration with a `.v13_core` projection. The boundary is a declared
field of every result, not a directory.

**Exit gate.** Every pre-existing conformance test passes with
`specification_version` set to v1.3 and its recorded observations **unchanged** —
the audit-preservation check, which must pass before anything else in M11 is
written. Cross-version comparison raises. `.v13_core` diffs against
`FLAGSHIP_DECLARATION` identically to flagship's own declaration.

### M11.2 — The constitutive declaration (ADR-043)

Item 6 split by role (6a–6c certificate-eligible, 6d constitutive and
hard-constraint-only), and the declaration's five fields with `validity_range`
load-bearing. The operator reports where the current evaluation sits relative to
the validated envelope, as a result dataclass, surfaced and never enforced.

**Exit gate.** An oracle whose validated envelope is known by construction
recovers the reported extrapolation factor. Off-manifold queries surface rather
than raise. `classify_invariant` still refuses a 6d member — now correct by
specification rather than incidentally. **And the binding space is legible in the
output**: a control-space violation reports `CONTROL_INVERSE` (actionable within
Core §5's existing machinery), a state-space violation reports `BUY_PHYSICS`
(actionable by nothing the framework has), demonstrated by sweeping the entire
declared control window against an out-of-range state and showing every point
still reports `BUY_PHYSICS`.

### M11.3 — The constitutive variant domain (ADR-044)

`flagship_constitutive` as a sibling: Kocks–Mecking, grain growth, JMAK,
Koistinen–Marburger, Hall–Petch, each with its real validity boundary. Analytic
flagship untouched.

**Exit gate.** The v1.3-core diff against flagship comes out near-identical
except item 6 and the constitutive declaration — **checked before any parameter
is fitted**, since a failure there means the controlled comparison is lost. The
three components Phase 1 measured at `rate == 0.0` have real kinetics, so the
control inverse is non-vacuous and E-26 becomes exercisable rather than only
detectable. Flagship's own defect remains documented and reproducible.

### M11.4 — The extrapolation experiment (ADR-045)

Four contestants (free-form incumbent; correct form; misspecified form in two
arms; unchanged tabular baselines) against **two generators in a fixed order** —
**A, primary:** a canonical form plus one named withheld term, chosen because a
localised absence makes every gap attributable; **B, follow-up:** a
multi-mechanism composite whose coupling no declared form expresses, which tests
whether A's benefit survives realistic coupling-blindness. Held out over a
control-space region lying partly outside the declared validity ranges. Never
pooled, and no cross-generator comparison is computed.

**Exit gate.** Thresholds pre-registered via ADR-041 before either sweep runs, and
the same thresholds applied to both. Rollout-length curves for every contestant.
Error plotted against declared-envelope distance. On Generator A, `gap(3, 1)` and
`gap(3, 4)` reported as the claim and `gap(2, 3a)`/`gap(2, 3b)` as robustness by
misspecification kind. **A negative result on Generator A — misspecified declared
physics beating neither the free-form operator nor the tabular baselines — is a
deliverable and terminates the milestone**: it is filed as a correction to E-32's
own argument, and Generator B is *not* run, since a form that fails under the most
favourable non-circular conditions will not do better with a whole coupling
missing.

**Outcome — gate met, result negative, and the null is uninformative.**
`docs/M11.4-EXTRAPOLATION.md`. Thresholds were fixed in their own commit
(`bd44bb6`, `docs/M11.4-PREREGISTRATION.md`) before the sweep script existed, so
the ordering is auditable in `git log`. On Generator A neither misspecification
arm cleared its threshold against the free-form incumbent or either tabular
baseline; contestant 2 (correct form) is reported as a ceiling with ADR-045's
caveat and did not clear either. **Generator B was therefore not run**, per the
rule above. Rollout curves were produced for every contestant as required.

The milestone's substantive finding is *why* the null is uninformative rather
than negative: the held-out axis is strain rate, and Kocks–Mecking has no
strain-rate dependence, so the declared form makes no prediction along that axis
that differs from the free-form baseline's. Every contestant's held-out error is
the withheld term's own magnitude to within their spread. The design satisfies
Spec §9.3's prescription in full and is nonetheless incapable of discriminating —
filed as `docs/V1.4-EDITS.md` **E-39**. The γ=4 rollout gap (declared-form arms
retaining recovery at ≈18–20 versus ≈41 for free-form and both tabular
baselines) is recorded in that document as a **pre-specified observation
generating an untested hypothesis**, explicitly not as a result: the thresholds
were registered for held-out RMSE at unit strain, and applying them to a rollout
gap after seeing it would be the goalpost-moving the pre-registration exists to
prevent. Testing it needs a fresh pre-registration and a hold-out chosen so the
declared form and the baseline differ along the held-out axis.

### M11.5 — The fair-axis experiment (ADR-047)

M11.4's design error was the axis, not the experiment. ADR-045's contestants,
arms, costs, threshold procedure and ceiling caveat carry over unchanged; the
hold-out moves to **accumulated strain**, where Kocks–Mecking's storage/recovery
balance actually makes a prediction, and the withheld term becomes **dynamic
recrystallisation above a critical strain** — a departure the declared form is
dimensionally capable of representing wrongly, so the two misspecification arms
stay interpretable. ADR-045 gains a standing **hold-out-discrimination
requirement**, implemented as `omi.proposed.holdout` and run before registration.
Contestant 1 is re-specified as a free-form **rate law**, integrated, because
M11.4's `surface × γ` is a straw man on a strain hold-out.

**Exit gate.** The discrimination check passes on the new axis and refuses M11.4's,
before thresholds are registered. Thresholds registered in their own commit ahead
of the sweep. Per-strain curves for every contestant, with the pooled figure named
in advance as the registered criterion.

**Outcome — gate met; the claim is REFUTED, and this null is informative.**
`docs/M11.5-EXTRAPOLATION.md`. The gate admitted the strain axis at divergence
14.57 against a bar of 2.0 and refused M11.4's on all three criteria (axis signal
exactly 0.000), so the comparison could have detected an effect. It found none:
every declared-form arm is **worse** than the free-form operator — `gap(1, 3a)`
−64.49, `gap(1, 3b)` −2.50, ceiling `gap(1, 2)` −3.04, all against τ ≈ 0.32 — and
an unchanged tabular baseline is best of the six at 3.27.

Three findings came out of it. **Which kind of misspecification matters, and the
answer is +61.98**: a missing *dependence* costs almost nothing (7.56 against the
correct form's 8.10) while a missing *mechanism* is catastrophic (69.55, growing to
123.0 at γ=6 because it cannot saturate) — declaring a form with a mechanism
missing is far worse than declaring no form at all. **The declared forms lose by
error cancellation, not ignorance**: the correct form is exact against a
withheld-free truth (0.0000) and finishes fourth, while the winner is fourth on
that measure and first on the registered one, its −7.49 bias nearly annihilating
the withheld term's −6.56. Filed as **E-42**, with the sting that the diagnostic
needs a modifiable generator and so is unavailable on field data. And **M11.4's
untested γ=4 hypothesis is now tested and refuted** — the separation reverses once
the baseline is an operator rather than a surface, exactly as ADR-047 suspected.

Building the gate also corrected E-39's own proposed wording (**E-41**), and adding
one bound to a form declared at M11.3 exposed that declarations cannot be refined
without breaking every caller (**E-40**).

### M11 — closed

**Track record: `docs/M11-RECORD.md`**, a standalone account written at the close
of the milestone. It states the claim as pre-registered, M11.4's vacuous-axis
failure and its diagnosis, M11.5's result and the refutation, and the three
findings that outrank the headline — the misspecification asymmetry, error
cancellation (E-42), and the axis precondition (E-41) — together with the
pre-registration peek disclosed in the narrative rather than an appendix.

**Downstream corrections made on closing.** `docs/PHYSICS-ADEQUACY.md` §3.4 — the
section that argued for this extension and named this experiment — is corrected
in place under the live-document rule: its claim that constitutive structure buys
reach is refuted as stated, and narrowed to *"only when the declared mechanism set
is complete for the held-out regime; an incomplete set is worse than no
declaration"*. `docs/V1.4-EDITS.md` §11's buy-physics row records a second,
distinct gap alongside the pricing one: the validity report signals that you are
outside an envelope and says nothing about whether your mechanism set is complete,
and completeness is what the asymmetry shows actually governs the outcome.

No further M11 work. Generator B was not run and must not be run as a follow-up
to a refuted claim.

### Explicitly out of scope for M11

Directional `ℓ_D` (E-30 stands as a finding; the build-coverage gap is recorded
at `docs/COVERAGE.md` S-4.4), chemistry transfer, the characterisation-suite
declaration (E-31), and every CLAUDE.md §9 anti-goal. Each is real; none is
load-bearing for the constitutive question, and bundling them would make the
design unreviewable.

---

## Milestone dependency graph

```
M0 ──► M1 ──┬──► M2 ──► M3 ──► M4 ──► M5 ──┐
            │                              ├──► M7 ──► M8 ──► M9 ──► M10 ──► M11
            └──► M6 ─────────────────────  ┘
```

M6 is independent of M2–M5 and may run in parallel. M7 requires M2–M6. M9
requires M7 and benefits from M8 but does not require it — analytic operators
are differentiable and sufficient for the control problem. M10 requires M9
and the post-M9 remediation phases (docs/DECISIONS.md, docs/V1.4-EDITS.md)
to have run first.

M11 requires M10, and its sub-milestones are strictly ordered: M11.1's
audit-preservation gate protects everything M0–M10 produced, so it runs first and
a failure there stops the track. M11.2 needs M11.1's declaration wrapper to have
somewhere to put the new category; M11.3 needs M11.2's declaration to declare
against; M11.4 needs M11.3's domain to run on. Unlike M6's independence from
M2–M5, nothing in M11 may run in parallel.
