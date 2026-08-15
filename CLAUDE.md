# CLAUDE.md

Persistent context for this repository. Read this fully before any task.
Read `docs/COVERAGE.md` before implementing anything from the Specification.

---

## 1. What this repository is

The reference implementation of **OMI v1.3** — a framework that models
process–structure–response linkages as a directed graph whose nodes are
infinite-dimensional state spaces and whose edges are operators.

Two primitives and one axiom:

- **Evolution operators** advance the state under controls.
- **Readout operators** extract observables from a state or trajectory.
- **Axiom S (sufficiency):** the state can be chosen large enough that future
  evolution depends on history only through the current state.

The framework is specified in two documents in `docs/`, with a strict
allocation rule that this repository also observes:

| Document | Holds | Rule |
|---|---|---|
| `OMI-v1_3-Core.md` | Claims | Everything **falsifiable** |
| `OMI-v1_3-Implementation-Spec.md` | Procedures | Everything **executable** |

Code implements the Spec. Docstrings that state a claim cite Core; docstrings
that state a procedure cite Spec. If you find yourself writing a *claim* in
code, you are inventing framework, not implementing it — see §4.

## 2. Prime directive

> **The job of this codebase is to make the framework's claims executable and
> falsifiable — not to produce good predictions.**

Every module exists to *measure* something the framework says must be measured
rather than assumed: sufficiency deficit, erasure completeness, closure defect,
observability, tail index, calibration, rollout error. A module that produces a
number without also producing the diagnostics that say whether the number can
be trusted is not finished.

Corollary, and it is load-bearing for build order: **the neural operators are
not the point.** They are one interchangeable approximation class. The
distinctive content is the measurement machinery around them. Learning is
therefore scheduled late (see `docs/ROADMAP.md`), and analytic operators serve
as stand-ins throughout — they are faster, exactly differentiable, and they
supply ground truth.

This repository is **evidence for the next issued framework specification and
its paper** — a general framework from which tools can be architected — not a
deployable prediction tool in itself. That reframes what its outputs are for.
The number that specification will carry is not assigned; see §8's naming rule
and ADR-067 for why nothing here claims it.

> **The codebase's primary outputs are evidence and *corrections*.** Where an
> implementation attempt shows a Specification section to be wrong,
> ill-posed, unbuildable as written, or more (or less) complete than its
> `[Pass X]` marker claims, **that discovery is a deliverable, not an
> obstacle.** Capture it. A framework revision derived from an honest
> implementation attempt is worth more than a module that quietly works
> around the problem.

## 3. Vocabulary

Use these terms exactly. They are defined in Core; do not coin synonyms.

| Term | Meaning |
|---|---|
| **State** `s = (m, z, ν, Γ)` | `m` resolved fields; `z` sub-resolution internal variables; `ν` nonlocal/self-consistent field; `Γ` surface and interface state |
| **Control** `u ∈ 𝒰` | Time-dependent driving programme. Elements are *functions of time*, not scalars. `𝒰_adm` is the admissible subset the apparatus imposes. |
| **Erasure operator** `ℰ` | Evolution operator whose image has substantially lower effective dimension, `L ≪ 1`. Bounds error accumulation. **Not** a hybrid-system jump map. |
| **Type 0 / 1 / 2** | Functional readout / operator-valued (constitutive) / component readout requiring geometry |
| **Class A / B** | Self-averaging (an RVE exists) / weakest-link extreme-value (no RVE exists) |
| **Property vs performance** | Property is invariant under configuration within a test class, i.e. a functional of the constitutive operator alone. Performance requires geometry. |
| **Slot occupant vs parameter** | Interface items 1a and 1b, split by ADR-071 (`docs/V1.4-EDITS.md` E-46, E-29). A **slot occupant** evolves under some operator, is assimilated from observations, and carries a per-particle value in `𝒫(𝒮)` — it answers *what is the material*. A **parameter** does none of the three and answers *which member of the operator family this is*. Declared as `omi.interface.ParameterRole`. Not a fifth slot: a slot would subject it to pushforward, Axiom S, erasure and assimilation, all vacuous for a quantity nothing transports. One physical quantity may hold both roles in different declared regions, but the dual declaration must say so. |
| **Sufficiency deficit** `δ` | The bias term from matched-history pairs, **decomposed** to remove repeat noise and imperfect matching |
| **Danger score** `𝒟ᵢ` | influence × residual uncertainty, per state direction, relative to *declared* targets |
| **Observed / inferred / unresolved** | A direction is *observed* if a **single** near-diagonal Gramian term exceeds the largest downstream term by a **declared** dominance factor `ρ`; *inferred* if the near-diagonal contribution vanishes while the direction is identifiable from the total — the chain model, not any instrument, is doing the work; ***unresolved*** if the ratio sits within a declared band of `ρ`, or if nothing contributes at all. The dominance factor, the band and the near-diagonal window are declared **per domain** with justifications, and the **abstained fraction is a required output** (ADR-061; V1.4-EDITS E-48, E-53). Never cite the *size* of the inferred set as evidence of chain-specific recovery — cite the per-direction dominance ratio (E-55) |
| **Control inverse / structure inverse** | Target response → driving programme / target response → state. Distinct problems; conflating them produces unrealisable designs. |
| **Closure defect** `𝒟_λ` | Non-commutation of coarse-graining with evolution. Measured, never assumed small. |

`m z ν Γ` are slot names, not variable names to be renamed for readability.
Keep them.

## 4. The gap discipline

**This is the most important section in this file.**

OMI v1.3 is a skeleton. Large parts of the Specification are explicitly
unwritten and carry markers:

- **`[Pass B]`** — result stated, derivation missing. *You do not know the
  procedure.*
- **`[Pass C]`** — structure known, synthesis and numbers missing. *You know
  the shape but not the parameters.*
- **`[Pass D]`** — needs a worked instantiation or demonstration.

`docs/COVERAGE.md` enumerates every one of them. **Consult it before
implementing anything.** When you reach a gap you have exactly three legal
moves, and improvising is not among them:

1. **Refuse.** Raise `omi.NotSpecified` with the Spec section and the
   `COVERAGE.md` row id. This is the default and it is always acceptable.
   A framework that knows when to refuse is more credible than one that always
   answers — that is the framework's own position (Core §3.9) and it applies to
   the code that implements it.
2. **Decide.** If the gap must be filled to make progress, write an ADR in
   `docs/DECISIONS.md` first: what the Spec leaves open, what you chose, what
   alternatives you rejected, what would change the decision, and what test
   pins it. Then implement. The ADR is the artefact, not the code.
3. **Escalate.** If the gap looks like it needs framework-level resolution
   rather than an implementation choice, add it to the open-questions section
   of `docs/DECISIONS.md` and stop.

Never silently interpolate across a `[Pass B]`. A plausible-looking
implementation of an underived procedure is worse than a `NotImplementedError`,
because it will be mistaken for the framework's position and it will propagate
into a paper.

## 5. Invariants

Non-negotiable. Violating any of these produces non-conforming output.

1. **Declare the metric.** Every Lipschitz constant, erasure measurement,
   trust radius and state distance is metric-dependent. The metric is a
   first-class object carried in every report that quotes such a quantity.
   Default: non-dimensionalise each component by its aleatoric standard
   deviation across the incoming population, so `L` reads as *"how much does a
   one-sigma incoming variation grow"*.
2. **Ensembles live on `𝒫(𝒮)`, not `𝒮`.** A statistical representative volume
   is a *measure*, not a state. Evolution is lifted by pushforward or Markov
   kernel. Type errors here silently produce ensemble-mean physics, which is
   wrong for every Class B readout.
3. **`omi/` contains no domain vocabulary.** No "coil", "austenitisation",
   "coating", "steel", "battery". Domain terms live in `omi_domains/`. This is
   enforced by a lint test. It mirrors the purge the framework performed on
   itself between v1.2 and v1.3, and it is what makes the generality claim
   checkable rather than asserted.
4. **Class B readouts return distributions, never point predictions**, with
   the extrapolation ratio and join threshold stated.
5. **Hard constraints are architecture, never loss penalties.** A penalty
   enforces physics where the training data live; an optimiser searching for an
   optimal route finds precisely where enforcement is weak. Constraint tests
   run off-manifold with out-of-range controls, because that is where inverse
   design goes.
6. **Never split randomly.** Group by provenance unit, batch, campaign,
   composition family — enforced at the data-loader level so a random split is
   structurally impossible, not merely discouraged.
7. **Report rollout-length error curves**, never one-step error alone. The gap
   between them is the honest measure of composability.
8. **Report which term blocks.** When state selection terminates with a
   residual deficit, distinguish variance-blocked (buy sensing) from
   learning-blocked (buy data) from bias-blocked (falsification). Only the
   third is a refutation. Conflating them is how a framework acquires an
   undeserved reputation for failure.
9. **Separate aleatoric from epistemic uncertainty.** They drive different
   decisions: robust design and specification limits, versus experimental
   design and characterisation budget.
10. **Targets are declared before analysis.** Danger scores, state selection
    and observability triage are all defined relative to a *declared* readout
    set. If the target set changes, the analysis is invalid and must be re-run.
11. **The generality claim is the paper's central bet, and its evidence is
    that the instantiation interface is fillable by domains outside the two
    implemented.** Interface declarations without implementations behind them
    — a sketch that fills, or fails to fill, Core §4's items for a
    domain neither `flagship` nor `contrast` covers — count as evidence for
    this claim and are explicitly in scope (see M10, `docs/ROADMAP.md`). A
    sketch that cannot fill an item is not a failed exercise; it is a finding
    for `docs/V1.4-EDITS.md`.

    **The item count is this repository's, not v1.3's, and it moves.** v1.3
    issues seven items; `omi.interface.InstantiationDeclaration` declares
    **eight** since ADR-071 split item 1 into 1a (state schema) and 1b
    (declared parameters), per `docs/V1.4-EDITS.md` E-46. Never hardcode the
    count: read `omi.interface.INTERFACE_ITEMS`, which is the single authority
    for the numbering, the charters and the Core §7.2 row mapping. A test or
    document that writes the count as a literal is the E-01 defect being
    recreated. **A changed count re-opens every sketch verdict** — each is
    evidence for this claim, so a new item means each verdict is
    re-established rather than reformatted.

## 6. Architecture

```
src/omi/                  domain-neutral framework — NO domain vocabulary
  state.py                State, slots, Metric, ensembles on 𝒫(𝒮)
  operators.py            EvolutionOperator: .step .lift .lipschitz .is_erasure
  readouts.py             Readout: type 0/1/2, class A/B, volume argument
  chain.py                mode-labelled DAG; composition at the level of measures
  constraints.py          hard structural constraints
  erasure.py              erasure measurement; surviving subspace
  sufficiency.py          deficit decomposition; probe sets; augmentation loop
  observability.py        Gramian; danger triage; observed/inferred/unresolved; VOI
  assimilate.py           EnKF; smoother; innovation drift monitor
  classb.py               driver/tail separation; N_eff; validation ladder
  inverse.py              constrained control; certificates; decision layer
  conformance.py          OMI-0/1/2 report generation
  gaps.py                 NotSpecified; the gap registry
  learning.py             neural operators (DeepONet-style); training; added M8 (ADR-029)
src/omi_domains/
  flagship/               metallurgical process chain (Core §7.1)
  contrast/               electrochemical cell under service (Core §7.2)
tests/
  oracles/                synthetic systems with known answers — see §7
docs/
  OMI-v1_3-Core.md        the framework: claims
  OMI-v1_3-Implementation-Spec.md   the framework: procedures
  COVERAGE.md             gap register — what is specified, what is not
  ROADMAP.md              milestones and exit criteria
  DECISIONS.md            ADR log and open questions
```

**Two domains from the start, not one.** The instantiation interface (Core §4)
is only testable with at least two domains, and the pair is chosen to *invert*
each other: the contrast domain has **no erasure operators** and a
usage-determined rather than apparatus-determined control axis. Building
against one domain shapes the interface to it and leaves the generality claim
unverified. The second domain may be thin, but it must exist before the
interface is called stable.

## 7. Testing philosophy

**Test estimators against constructed truth.** For every quantity the framework
requires to be measured, build a synthetic system where the answer is known by
construction, and assert the estimator recovers it. These live in
`tests/oracles/` and they are the reason to trust the codebase.

| Oracle | Construction | Estimator must recover |
|---|---|---|
| Known insufficiency | System with a hidden variable you control | Deficit ≈ known gap; deficit ≈ 0 when matching on the full state |
| Known erasure | Operator with designed rank-`r` Jacobian | Rank `r` and the surviving subspace |
| Known blind spot | Sensor suite orthogonal to a designed direction | That direction in `ker 𝐆` |
| Known tail | Pareto with known `α`, map with known `β` | `ξ_D = β ξ_a` |
| Known unreachability | Invariant with a computable bound | Certificate fires exactly outside |
| Known closure defect | Fine dynamics with an exactly-solvable projection | `‖𝒟_λ‖` |

Two further rules:

- **Assert qualitative claims, not printed figures.** *"The deficit collapses
  by two orders of magnitude after augmentation"* is a good test.
  *"The deficit equals 252.03"* is a bad one — it freezes tuning constants and
  breaks silently when physics is retuned.
- **Seed everything.** Every stochastic function takes an explicit generator.
  A flaky test in a framework about uncertainty quantification is worse than no
  test. CI runs the suite twice and compares.
- **A test that checks a measured quantity records the quantity, not only the
  verdict.** An assertion like `assert deficit < 0.05 * truth` pins a bound but
  discards the number that was actually observed when the suite ran — anyone
  auditing the claim later has to re-run the code to learn what "measured"
  meant. Use the `observe` fixture (`tests/conftest.py`) to record the name,
  the value, and the bound it was checked against, before the assertion.
  `build/observations.json` is the resulting record: a git-ignored build
  artefact, regenerated from scratch by every test-suite run, never hand-
  edited or committed.

## 8. Conventions

- Python ≥ 3.11, `src/` layout, `pyproject.toml`, no network at runtime.
- numpy + scipy required; torch **optional** with a numpy fallback that gives
  identical results. Never import torch at module scope in `src/omi/`.
- Type hints throughout. Slot and type/class taxonomies are enums, not strings.
- Every public function that returns a measured quantity also returns its
  diagnostics. Prefer a small result dataclass over a bare float.
- Never hardcode a narrative number in a docstring or report. Anything quoted
  must be computed.
- Cite the source section in the docstring: `Core §3.8` or `Spec §3.3`. A
  module with no citations is either inventing or restating.
- **Version numbers name issued specifications only** (ADR-067). OMI v1.3 is
  issued; nothing beyond it is. `SpecificationVersion` therefore names a
  **claim target**, and a target that is not an issued specification is named
  by *what it proposes* — `PROPOSED_CONSTITUTIVE_EXTENSION`,
  `PROPOSED_DECISION_EXTENSION` — never by a number that has not been
  assigned. The same holds for the carriers behind them
  (`ExtendedDeclaration`, `DecisionExtendedDeclaration`).

  Three things are outside the rule because they are **historical record**, and
  editing them would falsify it: **ADR titles**, **track names** (a body of
  work whose documents are named for it and cited from commit-stamped
  snapshots), and **quoted commit messages**. `docs/V1.4-EDITS.md` keeps its
  filename for the stronger reason that snapshots cite the path and §10 forbids
  editing them — its header note records that the target version moved.

## 9. Anti-goals

Do not build these. They are `[Pass B]`/`[Pass C]` in the framework and
building them from a one-line description produces confident nonsense.

- Tier II boundary value problems and FE² coupling — **except Tier I½**
  (ADR-035, docs/DECISIONS.md): a Type-1 constitutive operator composed with
  one scalar geometry parameter and one loading mode, evaluated by
  through-thickness quadrature, returning a response and a process-zone
  volume. No meshes, element assembly, equilibrium iteration, solver,
  contact/friction, more than one loading mode, or geometry richer than a
  thickness and a curvature — and never call it "Tier II." If a task needs
  any of those, it is Tier II, not Tier I½, and the anti-goal still applies.
- Hybrid mode/guard structure and jump maps (Spec §5.1)
- Body-indexed state and the registration operator (Spec §5.2)
- Closure-defect measurement procedure (Spec §6) — the *definition* is in
  Core §3.7 and may be implemented; the measurement procedure is not specified
- Closed-loop confounding remedies (Spec §5.3)
- The linear-Gaussian proof of the error-control dichotomy (Core §3.9)
- Compute-budget and modality catalogue numbers (Spec §3.7, §12)

If one of these blocks a task, say so and stop. Do not improvise a version
that looks finished.

## 10. How to work

- Follow `docs/ROADMAP.md`. **Stop at each milestone exit gate and report.**
  Do not begin the next milestone without confirmation.
- Before implementing a Spec section, check its row in `docs/COVERAGE.md`.
- When you make a choice the Spec does not dictate, write the ADR first.
- Prefer refusing to guessing. Prefer measuring to assuming. Prefer a small
  correct module with its diagnostics to a large one without.
- **When an implementation attempt finds a framework defect — a Core or Spec
  section that is wrong, ill-posed, unbuildable as written, or more or less
  complete than its `[Pass X]` marker claims — record it in
  `docs/V1.4-EDITS.md` *before* deciding how the code will cope with it.**
  The ADR that follows records this repository's implementation choice; the
  `V1.4-EDITS.md` entry records the separate, prior fact that the framework
  itself needs to change. Writing the code workaround first and the framework
  finding later (or never) is how a genuine defect gets silently absorbed
  into a repository-specific convention instead of reaching the paper it is
  evidence for.
- **Snapshot documents are corrected by addendum; live documents are
  corrected in place.** A document that stamps a commit SHA or commit range
  in its own header (`docs/REVIEW_PACK.md`, `build/REVIEW-EXTRACT.md`) is a
  point-in-time record of what was true *at that commit* — editing its body
  later to match new findings falsifies the record it exists to be. Correct
  it by appending a dated addendum that names what changed and why,
  immediately after the passage it corrects or in a clearly marked section,
  never by rewriting the original text. A document that describes the
  repository's *current* state with no commit stamp (`CLAUDE.md` itself,
  `docs/COVERAGE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`,
  `docs/V1.4-EDITS.md`) is live — it is supposed to always be accurate, so
  correct it in place the same way any other stale documentation gets fixed.
