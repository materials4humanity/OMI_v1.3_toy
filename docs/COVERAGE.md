# COVERAGE.md — the gap register

**What the framework specifies, what it does not, and what this repository does
about each.** Consult before implementing any Specification section.

Status codes:

| Code | Meaning | Legal action |
|---|---|---|
| **SPEC** | Fully derived in the Specification. Formulas, procedures, thresholds present. | Implement directly. |
| **PASS-B** | Result stated, derivation missing. *The procedure is unknown.* | Refuse (`NotSpecified`), or write an ADR and implement a declared choice. |
| **PASS-C** | Structure known, synthesis and numbers missing. | ADR required for any parameter you pick. |
| **PASS-D** | Needs a worked instantiation or demonstration. | Supplied by `omi_domains/`, not by `omi/`. |
| **CLAIM** | A Core claim with no procedure attached. Nothing to implement; may be *tested*. | Write a test, not a module. |

`id` is the stable reference used by `omi.NotSpecified` and by ADRs.

---

## Part I — Core claims

| id | Core § | Content | Status | Repo |
|---|---|---|---|---|
| C-2.1 | §2.1 | Axiom S; sufficiency test by matched-history pairs | SPEC (concept) → Spec §8 for campaign | `sufficiency.py` |
| C-2.2 | §2.2 | State selection as measurable bias–variance | **PASS-B** in Core, but **estimators are SPEC** in Spec §1 | `sufficiency.py` — implement via S-1, not from Core |
| C-2.3 | §2.3 | Two primitives; fusion is not a primitive | CLAIM | test: no fusion API exists |
| C-2.4 | §2.4 | Two tiers, material and component | CLAIM | Tier II is an anti-goal; Tier I only |
| C-2.5 | §2.5 | Body-indexed state | **PASS-C** | anti-goal; state is per material point |
| C-2.6 | §2.6 | Property vs performance by invariance | SPEC | `readouts.py` typing |
| C-3.1 | §3.1 | Four-slot state schema | SPEC | `state.py` |
| C-3.2 | §3.2 | Spaces and type discipline | SPEC | `state.py`, `chain.py` |
| C-3.3 | §3.3 | Evolution; pushforward/kernel lift; semigroup identity | SPEC | `operators.py` |
| C-3.4 | §3.4 | Hybrid continuous–discrete structure | **PASS-C** | anti-goal |
| C-3.5 | §3.5 | Readout types 0/1/2 | SPEC | `readouts.py` |
| C-3.6 | §3.6 | Class A/B; tail-index transfer; dimensional reduction | SPEC → Spec §4 | `classb.py` |
| C-3.7 | §3.7 | Homogenisation; closure defect *definition*; RG scope | SPEC (definition) / **PASS-C** (measurement, Spec §6) | definition only |
| C-3.8 | §3.8 | Assimilation; Gramian; danger score; erasure truncation | SPEC → Spec §3 | `observability.py`, `assimilate.py` |
| C-3.9a | §3.9 | Error compounding bound; erasure definition and consequences | SPEC | `erasure.py`, `operators.py` |
| C-3.9b | §3.9 | **Error-control dichotomy** (erasure or observation) | **PASS-B** | test only; do not implement a scoping check |
| C-3.9c | §3.9 | **Refusal criterion**; `L_phys × L_num` | **PASS-B** → Spec §2.5–2.7 | refuse |
| C-4 | §4 | Seven-item instantiation interface | SPEC | `omi_domains/*/interface.py` |
| C-5a | §5 | Inverse design as constrained optimal control | SPEC (formulation) | `inverse.py` |
| C-5b | §5 | Reachability certificates | **PASS-B** → Spec §7.1 | ADR required |
| C-5c | §5 | Decision layer within the degenerate set | **PASS-C** → Spec §7.3 | ADR required |
| C-6.1 | §6.1 | Six falsification criteria | **PASS-D** (thresholds) | criteria as tests; thresholds via ADR |
| C-6.2 | §6.2 | Open problems (research questions, not framework claims) | CLAIM | non-implementable; distinct from DECISIONS.md's OQ-1..OQ-5, which are hypotheses this repo generates from reading the specs, not Core's own list — do not conflate the two when recording outcomes |
| C-7 | §7 | Two instantiations, declared and diffable | **PASS-D** | `omi_domains/` |
| C-8 | §8 | Positioning against prior art | **PASS-D** | no code implication — literature positioning only; logged for completeness since the text carries an explicit `[Pass D]` marker |

---

## Part II — Specification procedures

| id | Spec § | Content | Status | Repo |
|---|---|---|---|---|
| S-1.1 | §1.1 | Three-term error decomposition | SPEC | `sufficiency.py` |
| S-1.2 | §1.2 | **Deficit estimator** `δ² = E[(ρ_A−ρ_B)²] − 2σ²_rep − Σ(∂ρ/∂s)²E[Δs²]` | SPEC | `sufficiency.py` — the only public route to a deficit |
| S-1.3 | §1.3 | Variance term = Σ danger scores | SPEC | requires `observability.py` |
| S-1.4 | §1.4 | Learning error from rollout curve at matched budget | SPEC | requires learning milestone |
| S-1.5 | §1.5 | Augmentation loop (pseudocode given) | SPEC | `sufficiency.py` |
| S-1.6 | §1.6 | Divergence fingerprint table | SPEC | `sufficiency.py` — see OQ-1 |
| S-1.7 | §1.7 | Blocking-term trichotomy | SPEC | `sufficiency.py` |
| S-1.8 | §1.8 | Worked demonstration | **PASS-D** | oracle test |
| S-2.1 | §2.1 | Approximation class and caveats; no composition theorem | SPEC | `operators.py` docs |
| S-2.2 | §2.2 | Hard structural constraints | SPEC | `constraints.py` |
| S-2.3 | §2.3 | Training objectives | SPEC | learning milestone |
| S-2.4 | §2.4 | Stability-aware training; rollout reporting | SPEC | learning milestone |
| S-2.5 | §2.5 | **Amplification decomposition `L_phys × L_num`; local spectrum** | **PASS-B** | *"To be written: estimation procedure…"* → ADR or refuse |
| S-2.6 | §2.6 | **Backward error budgeting** | **PASS-B** | *"To be written: the backward recursion"* → refuse |
| S-2.7 | §2.7 | **Refusal criterion; trigger condition** | **PASS-B** | *"To be written: the trigger condition"* → refuse |
| S-3.1 | §3.1 | Observability Gramian construction; Prop 3.1 | SPEC | `observability.py` |
| S-3.2 | §3.2 | Erasure truncates the Gramian; Prop 3.2, Cor 3.3 | SPEC | `observability.py`, `erasure.py` |
| S-3.3 | §3.3 | Danger score; four-way triage; observed vs inferred | SPEC | `observability.py` — see OQ-2 |
| S-3.4 | §3.4 | Value of information; Woodbury; placement | SPEC | `observability.py` |
| S-3.5 | §3.5 | Matrix-free computation by JVP/VJP | SPEC | `observability.py` |
| S-3.6 | §3.6 | Trajectory dependence; worst case over window | SPEC | `observability.py` |
| S-3.7 | §3.7 | Modality catalogue | **PASS-C** | domain-supplied |
| S-4.1 | §4.1 | Class B object: failure driver field, `max D > D_c` | SPEC | `classb.py` |
| S-4.2 | §4.2 | Driver/tail separation; join threshold; diagnostics | SPEC | `classb.py` |
| S-4.3 | §4.3 | Tail transfer `ξ_D = β ξ_a`; Prop 4.1; sanity check | SPEC | `classb.py` — see OQ-3 |
| S-4.4 | §4.4 | `N_eff`; dimensional reduction; Prop 4.2 | SPEC | `classb.py` |
| S-4.5 | §4.5 | Rare-event sampling: subset simulation, conditional generative | SPEC | `classb.py` |
| S-4.6 | §4.6 | Four-rung validation ladder | SPEC | `classb.py` |
| S-5.1 | §5.1 | Hybrid systems | **PASS-C** | anti-goal |
| S-5.2 | §5.2 | Body-indexed state; registration operator | **PASS-C** | anti-goal |
| S-5.3 | §5.3 | Data reality; closed-loop confounding; grouped splits | **PASS-C** (remedies) / SPEC (grouped splits) | grouped splits only |
| S-6 | §6 | **Closure-defect measurement** | **PASS-C** — entire section | refuse |
| S-7.0 | §7.0 | `ℳ_real` vs `ℳ_reach` | SPEC | `inverse.py` |
| S-7.1 | §7.1 | **Reachability certificates** | **SPEC** (certificate definition and verification, given a domain-declared `Φ`) / **PASS-B** (the practical hierarchy for constructing or selecting `Φ`; nearest-reachable-state computation) | verification only, given a declared `Φ`; ADR (or refuse) for construction |
| S-7.2 | §7.2 | **Apparatus parameterisation** | **SPEC** (the "parameterise in apparatus settings, never driving paths" requirement — enforceable as an architectural invariant) / **PASS-C** (constraint-manifold construction, rate limits, mixed-integer handling) | requirement is testable now; ADR required for manifold construction |
| S-7.3 | §7.3 | **Decision layer** | **PASS-C** | ADR |
| S-8 | §8 | **Sufficiency campaign; power analysis** | **SPEC** (power-analysis formula `n ≈ 2(z_{1-α/2}+z_{1-β})²(σ/δ)²`; campaign-matrix design principle) / **PASS-C** (worked numeric values per response class; pre-simulation prediction of which pairs diverge) | formula usable directly; ADR required for worked values |
| S-9.1 | §9.1 | Conformance levels OMI-0/1/2 | SPEC | `conformance.py` |
| S-9.2 | §9.2 | Automated test suite (nine checks) | SPEC | `conformance.py`, CI |
| S-9.3 | §9.3 | Baselines; grouped splits; prospective validation | SPEC / **PASS-C** (go-no-go table) | `conformance.py` |
| S-9.4 | §9.4 | **Falsification thresholds** | **PASS-D** | ADR per application |
| S-9.5 | §9.5 | Uncertainty taxonomy; calibration reporting | SPEC | `conformance.py` |
| S-10 | §10 | Operations; innovation drift; lifecycle | **PASS-C** (procedure) / SPEC (proposition) | drift monitor only |
| S-11 | §11 | Full instantiation declarations | **PASS-D** | `omi_domains/` |
| S-12 | §12 | **Reference implementation architecture** | **PASS-C** | **this repo is the synthesis — ADR every choice** |

---

## Part III — What this means for build order

Counting: **the three modules with complete derivations are state selection
(S-1.x), observability (S-3.x) and Class B (S-4.x).** Those are also the
framework's most distinctive claims. They can be built without inventing
anything, and they are where the codebase earns its keep.

Everything touching *learning stability* (S-2.5–2.7), *scale bridging* (S-6),
*inverse design machinery* (S-7.1–7.3) and *campaign design* (S-8) requires
invention and must be gated behind ADRs — even though S-7.1, S-7.2 and S-8 each
contain a directly implementable kernel (certificate verification, the
apparatus-settings parameterisation requirement, and the power-analysis
formula respectively). The ADR gate applies to the part of each section that
is still synthesis, not to the whole section indiscriminately.

Note **S-12 is itself PASS-C**: the reference architecture is a sketch. The
class design in this repository is therefore a contribution, not a
transcription, and every structural choice needs an ADR.

---

## Part IV — Open questions

Candidate refinements surfaced while reading. Each is a hypothesis to be
*tested by the code*, not an assumption to build on. Do not treat these as
framework text. (These are distinct from Core §6.2's own "Open problems" list,
row C-6.2 — that list is the framework's own research agenda; the list below
is ours, generated by reading Core and Spec against each other.)

**OQ-1 — Is the divergence fingerprint a probe or a contrast?**
Spec §1.6 identifies missing components by *which probe* shows divergence
(e.g. "reversed driving only → kinematic variable"). Hypothesis: for a
kinematic variable both forward and reversed probes diverge, and what
discriminates is the *decomposition* of the probe response — symmetric part
matched, antisymmetric part diverging. If true, §1.6's rows should name
contrasts between probe responses rather than single probes, and the
`discriminating()` requirement in §1.6 becomes checkable.
**Test:** oracle with a known kinematic hidden variable; check whether the
single-probe rule yields a false negative.

**OQ-2 — Is erasure completeness operator-level or component-level?**
Core §3.9 consequence 3 offers "mutual information between pre- and
post-erasure states, *or* residual variance explained by upstream variables".
Hypothesis: these answer different questions and both are needed — a component
can lose 85% of its magnitude while the residual remains a deterministic
function of the input, hence still assimilable. Further hypothesis: erasure is
component-wise, so the suppression rule in Core §2.2 ("a deficit upstream of an
erasure is not a reason to enlarge the state") fails for surviving components.
**Test:** oracle with designed per-component contraction; check whether a
single operator-level rank predicts downstream influence.

**OQ-3 — Competing risks in Class B.**
Spec §4.3 transfers a tail index from one defect population. With several
populations of differing `α` and `β`, survival is `∏ₚ[1−Fₚ]^{Nₚ}` and no single
`ξ` describes the range of interest.
**Test:** two-population oracle; check whether a single-`ξ` fit misestimates
the design-point exceedance probability.

**OQ-4 — Does inverse design report *which* variance is binding?**
Spec §7.3 selects within a feasible set. When the set is empty — e.g. aleatoric
spread wider than the specification window — the useful output is which term
made it empty: aleatoric (reduce incoming variation), `𝒰_adm` (apparatus
limits), or trust region (surrogate not calibrated there).
**Test:** oracle with an arithmetically infeasible specification.

**OQ-5 — Metric dependence of every reported `L`.**
Core §3.9 and the erasure definition (`L ≪ 1`) are metric-dependent statements,
and the state has heterogeneous units. Spec §2.5 requires a local spectrum
rather than a global bound but does not fix the metric.
**Test:** rescale a slot; confirm every reported `L` changes; confirm the
aleatoric-sigma normalisation makes them comparable across slots.

---

## Maintaining this file

- When a `[Pass B]`/`[Pass C]` is resolved upstream in a new framework version,
  change the status and remove the ADR that stood in for it.
- When an open question is settled by a test, record the outcome here and in
  `DECISIONS.md`, and propose the framework edit.
- Every `NotSpecified` raised in the codebase must cite an id in this table.
  A CI check enforces it.
- **Core Appendix B (the general ↔ domain glossary) carries its own
  `[Pass A, in progress]` marker** — it is not a claims/procedure row and has
  none here, but it is load-bearing for the vocabulary lint (`ADR-006`,
  `tests/test_vocabulary.py`): the banned-term seed list is drawn from it and
  is therefore necessarily partial. The lint must stay trivially extensible
  (a list, not a hardcoded pattern) rather than treating Appendix B as
  exhaustive, and the seed list should grow as `omi_domains/` grows.
