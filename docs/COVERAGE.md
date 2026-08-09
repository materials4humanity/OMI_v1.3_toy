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

The three columns after **Repo** are the verification axis (Phase 1.2,
docs/DECISIONS.md ADR-034): whether the row is implemented in code, whether a
constructed-truth oracle validates the estimator, and whether a declared
domain (`omi_domains/flagship` or `omi_domains/contrast`) exercises it
end-to-end. `—` means not claimed, with the reason inline; anything else
names the evidence (`tests/lint/test_coverage_evidence.py` enforces that
every non-`—` cell contains at least one backtick path, and that every
backtick path in this table exists).

**Depends on** (added after a full sweep of every row, prompted by the
discovery that S-4.4's validation needs C-2.5, `docs/V1.4-EDITS.md` E-14):
whether *validating* this row — not merely reading it — requires machinery
from a *different* row whose own status is PASS-B/C/D. SPEC status is not
transitive through dependencies: a row can be fully derived and still
unbuildable if what checks it cites an undissolved gap elsewhere. `—` means
this row was checked against the full PASS-B/C/D list and no such dependency
was found (a plain `—` marks a row whose own status is itself PASS-B/C/D —
it is a provider for other rows' dependencies, not a dependent); a named row
means the dependency was found and is explained inline. No row in either
table below is left unassessed, though the depth of each check varies (see
the sweep note at the end of Part II).

| id | Core § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised | Depends on |
|---|---|---|---|---|---|---|---|---|
| C-2.1 | §2.1 | Axiom S; sufficiency test by matched-history pairs | SPEC (concept) → Spec §8 for campaign | `sufficiency.py` | `src/omi/sufficiency.py` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship, matched-pair campaign) | — |
| C-2.2 | §2.2 | State selection as measurable bias–variance | **PASS-B** in Core, but **estimators are SPEC** in Spec §1 | `sufficiency.py` — implement via S-1, not from Core | `src/omi/sufficiency.py` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) | — |
| C-2.3 | §2.3 | Two primitives; fusion is not a primitive | CLAIM | test: no fusion API exists | — (absence claim; nothing to implement) | — (no test asserts the absence directly; a repo-wide grep for "fusion" turns up zero matches, which is the honest state of the "test" this row's own Repo column describes) | — | — |
| C-2.4 | §2.4 | Two tiers, material and component | CLAIM | Tier II is an anti-goal; Tier I only | — (anti-goal, CLAUDE.md §9) | — | — | — |
| C-2.5 | §2.5 | Body-indexed state | **PASS-C** | anti-goal; state is per material point | — (anti-goal, CLAUDE.md §9) | — | `src/omi_domains/sketches/layerwise_additive.py` (E-21, M10.1: item 1 forced to a Tier I stand-in) | — (own status PASS-C; a provider row — but see `docs/V1.4-EDITS.md` E-22: §2.5's own repair formula, read literally against §3.1's `ν` definition, mis-types `ν` even independent of body-indexing being available at all) |
| C-2.6 | §2.6 | Property vs performance by invariance | SPEC | `readouts.py` typing | `src/omi/readouts.py` (`ReadoutClass`, Type 0/1/2 taxonomy) | — (no synthetic oracle for the invariance property itself) | `tests/test_readouts.py` (flagship: `AggregateHardness`/`ExtractHardness` Type-0/1 identity; contrast: `DendriteRisk` Class B); `tests/test_flagship_classb_bend.py` (flagship: `bend_angle`, a genuine Type-2 performance requiring geometry — Core §2.6's distinction was previously untestable since no Type-2 readout existed) | **C-2.5** (PASS-C) — the general (non-Tier-I½) case needs richer/body-indexed geometry; the Tier I½-bounded instance (`BendAngle`) validates without it |
| C-3.1 | §3.1 | Four-slot state schema | SPEC | `state.py` | `src/omi/state.py` | — (structural; nothing to recover against a constructed truth) | `tests/test_chain_rollout.py`, `tests/test_semigroup.py` (flagship, contrast) | — (this row's own SPEC status is sound; `docs/V1.4-EDITS.md` E-22 finds a defect one section over, in Core §2.5's repair of this schema for extended bodies, not in §3.1's four-slot definition itself) |
| C-3.2 | §3.2 | Spaces and type discipline | SPEC | `state.py`, `chain.py` | `src/omi/state.py`, `src/omi/chain.py` | — (structural) | `tests/test_chain_rollout.py` (flagship, contrast) | — |
| C-3.3 | §3.3 | Evolution; pushforward/kernel lift; semigroup identity | SPEC | `operators.py` | `src/omi/operators.py` | — (structural identity, not a recovered quantity) | `tests/test_semigroup.py` (flagship: `HEATING_AND_SOAK`, `TRANSFER`; contrast: `CYCLING`) | — |
| C-3.4 | §3.4 | Hybrid continuous–discrete structure | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — | — (own status PASS-C; a provider, not a dependent, row — but `docs/V1.4-EDITS.md` E-24 confirms this gap does **not** block Core §4 item 2 (control space) for a hybrid domain, only the *evolution*/simulation side; do not mark a domain's item 2 blocked on this row by analogy with C-2.5's genuine block on item 1, E-21/E-22) |
| C-3.5 | §3.5 | Readout types 0/1/2 | SPEC | `readouts.py` — ADR-035 (docs/DECISIONS.md) adds `ComponentReadout`/`Type2Geometry`, the first concrete Type-2 base (Tier I½, bounded); `ReadoutType` is now a class attribute on all three readout bases (`FunctionalReadout`/`ConstitutiveReadout`/`ComponentReadout`), no longer referenced nowhere outside its own definition | `src/omi/readouts.py` | — | `tests/test_readouts.py` (flagship, contrast, Type-0/1); `tests/test_flagship_classb_bend.py` (flagship, Type-2 via `BendAngle`, the first domain-exercised Type-2 readout in the repository) | **C-2.5** (PASS-C) — same as C-2.6: general Type-2 needs richer geometry; the Tier I½ case does not |
| C-3.6 | §3.6 | Class A/B; tail-index transfer; dimensional reduction | SPEC → Spec §4 | `classb.py` | `src/omi/classb.py` | `tests/oracles/test_known_tail.py`, `tests/oracles/test_known_ranking_inversion.py`, `tests/test_classb_competing_risks.py` | `tests/test_readouts.py::test_contrast_dendrite_risk_is_class_b_and_weakest_link_works` (contrast, `weakest_link` only); `tests/test_conformance_omi2_refusal.py` (contrast, `validate_volume_scaling_exponent` at 3 volumes); `tests/test_flagship_classb_bend.py` + `src/omi_domains/flagship/classb_bend.py` (flagship, Tier I½/ADR-035, Phase 2.3): the first Type-2/Class-B readout (`BendAngle`) exercised against a real, spatially-correlated driver field — nine of `src/omi/classb.py`'s ten previously-dead symbols are now called from production domain code; `SubsetSimulationResult` remains the only one with zero name references anywhere (its constructor function, `subset_simulation`, is exercised by `tests/test_classb_subset_simulation.py`, but nothing names the result type itself) | **C-2.5** (PASS-C) — confirmed this session: Prop 4.2's *emergent* dimensional-reduction claim needs body-indexed state (`docs/V1.4-EDITS.md` E-14); the formula-self-consistency half does not |
| C-3.7 | §3.7 | Homogenisation; closure defect *definition*; RG scope | SPEC (definition) / **PASS-C** (measurement, Spec §6) | definition only | — (definition only; `measure_closure_defect` in `src/omi/conformance.py` is an unconditional refusal stub, not an implementation of the definition) | — | — | — (own status SPEC/PASS-C mixed; the measurement half is itself the PASS-C row) |
| C-3.8 | §3.8 | Assimilation; Gramian; danger score; erasure truncation | SPEC → Spec §3 | `observability.py`, `assimilate.py` | `src/omi/observability.py`, `src/omi/assimilate.py` | `tests/oracles/test_known_blind_spot.py`, `tests/oracles/test_erasure_truncates_gramian.py`, `tests/oracles/test_known_latent_trajectory.py`, `tests/oracles/test_known_drift.py`, `tests/oracles/test_known_empty_slot.py` (M10.1 follow-up: `measure_erasure`, `compute_gramian`, `danger_triage` all run correctly, recovering exact known-by-construction values, on a schema where `m`/`z`/`ν` are all empty and only `Γ` is occupied — none of this machinery assumes a populated slot; answers, at oracle scale, the question `docs/SKETCHES.md`'s catalyst-under-operation sketch left untestable at domain scale) | `tests/test_domain_triage.py` (flagship, contrast) exercises `src/omi/observability.py`'s Gramian/danger-triage only; `src/omi/assimilate.py`'s EnKF/smoother/drift-monitor has no domain test (its oracles — `tests/oracles/known_latent_trajectory.py`, `tests/oracles/known_drift.py` — are synthetic schemas, not `omi_domains`) | — |
| C-3.9a | §3.9 | Error compounding bound; erasure definition and consequences | SPEC | `erasure.py`, `operators.py` | `src/omi/erasure.py` (`measure_erasure`, `component_recoverability`, and — new at Phase 3.4 — `component_surviving_overlap`, a pure geometric per-component diagnostic, OQ-2/E-18), `src/omi/operators.py` (`.is_erasure`) | `tests/oracles/test_known_erasure.py` (diagonal); `tests/oracles/test_known_mixing_erasure.py` (Phase 3.4, mixing: rank recovered exactly, but per-component overlap — `0.833`/`0.833`/`0.333` designed, recovered to within `0.01` — is not derivable from rank alone, answering OQ-2's deferred half) | `tests/test_error_compounding.py` (flagship, `HEATING_AND_SOAK`) demonstrates the damping *effect* directly on perturbed states; `tests/test_flagship_real_erasure.py` (Phase 3.1, flagship, `HEATING_AND_SOAK`): the first domain-exercise of `measure_erasure`/`component_recoverability` themselves, not only the oracle's exact-zero-gain construction — finds `measure_erasure` reports full rank (7/7) at ADR-017's default tolerance since `HEATING_AND_SOAK`'s decay is finite (`exp(-5)~0.0067`), never exactly zero, with the erasure visible only by reading the spectrum (a ~150x gap, correctly isolating `prior_deformation`/`substructure_density`); and finds `component_recoverability` (R², correlation-based) cannot see the erasure at all on this noiseless deterministic operator — R²≈1.0 for every non-degenerate component regardless of how much magnitude it lost, extending OQ-2's M2 finding (previously shown only on the synthetic oracle) to a real domain |
| C-3.9b | §3.9 | **Error-control dichotomy** (erasure or observation) | **PASS-B** | test only; do not implement a scoping check | — (deliberately no scoping-check module) | — | `tests/test_conformance_flagship.py::test_flagship_matched_pair_deficit_is_at_noise_level` (flagship) exercises condition (a) only; condition (b) — continuous assimilation controlling error where no erasure exists — is untested on the contrast domain: `tests/test_conformance_contrast.py` only checks `erasure_inventory == ()` declaratively, no contrast-domain assimilation campaign runs anywhere | — (own status PASS-B; a provider, not a dependent, row) — `docs/V1.4-EDITS.md` E-23 (M10.1, layer-wise additive sketch): condition (b)'s own wording does not require the observations counted toward it to occur *during* the chain, so a domain can declare a rich but strictly terminal (post-chain) observation suite and appear to satisfy (b) while satisfying it not at all; the same sketch's only declared erasure is also terminal, so both conditions can fail invisibly at once |
| C-3.9c | §3.9 | **Refusal criterion**; `L_phys × L_num` | **PASS-B** → Spec §2.5–2.7 | refuse | `src/omi/operators.py::amplification_decomposition` (unconditional `NotSpecified`, cites S-2.5) | — (nothing to verify; the function always refuses) | `tests/test_lipschitz_report.py::test_amplification_decomposition_refuses_citing_s_2_5` (flagship, `HEATING_AND_SOAK`) — the refusal path itself is domain-exercised, not the (nonexistent) decomposition | — (own status PASS-B; a provider, not a dependent, row; see S-2.5) |
| C-4 | §4 | Seven-item instantiation interface | SPEC | `omi_domains/*/interface.py` — ADR-034 (docs/DECISIONS.md) supersedes ADR-003's pinning test: Core §7.2's seven rows name six distinct Core §4 items, not seven, and `interface.diff()` now also reports a structural (kind-based) comparison for item 6's invariants alongside the literal one. Item 4b (per-Class-B-readout driver field/defect population/physics map Ψ) is now filled for the flagship's `bend_angle` (Phase 2.2, ADR-035) — the first domain to fill 4b at all; the contrast's `dendrite_risk` (Type-0/Class-B) still does not declare it | `src/omi/interface.py`, `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` | — (no synthetic oracle; the cross-domain diff is the check) | `tests/test_interface_diff.py` (flagship, contrast); `tests/test_flagship_classb_bend.py::test_flagship_declares_bend_angle_with_item_4b_filled` (flagship, item 4b specifically) | — (the interface-declaration/diff claim itself needs no PASS machinery; the OMI-2-level dependency lives at S-9.3, not here) |
| C-5a | §5 | Inverse design as constrained optimal control | SPEC (formulation) | `inverse.py` | `src/omi/inverse.py` — **correction (M10.2/ADR-040, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-28)**: through M9 this cell's plain file reference obscured that the module contained no search/optimisation procedure at all — `ReachabilityCertificate` checks an already-produced candidate (necessary conditions only), `ApparatusParameterization.sample_admissible` is uniform forward-sampling, and the decision layer selects among already-produced candidates; nothing searched `𝒰_adm` for one. Core §5's own formulation is "constrained *optimal control*" — an optimisation problem — so the module's central object was, in this specific sense, unimplemented at the M9 exit gate, not merely partially implemented. `gradient_control_search` (ADR-040) now supplies a genuine, if narrow, instance: projected gradient descent for a differentiable scalar forward map against a single target, box-constrained via `ApparatusParameterization.bounds`. It does not integrate with `ReachabilityCertificate` or the decision layer (a caller wires them together manually, as `tests/test_baseline_characterisation.py` does), and has no multi-objective, vector-target, or coupled-manifold form | `tests/oracles/test_known_unreachability.py`, `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py`, `tests/test_inverse_apparatus_parameterisation.py` — **`gradient_control_search` itself has no dedicated oracle-style test** (no known-optimum synthetic check under `tests/oracles/`): it is exercised only through `tests/test_baseline_characterisation.py`'s applied contrast harness, against a piecewise-linear monotone operator with a known flat region, not a clean isolated convergence check with a trivial analytic answer | **partially closed** (M10.2/ADR-040): `tests/test_baseline_characterisation.py` now imports both `omi.inverse` (`ApparatusParameterization`, `gradient_control_search`) and `omi_domains` (contrast, flagship) — the literal "zero test imports both" gap flagged in `build/REVIEW-EXTRACT.md` §1/§4 no longer holds without qualification. Still true, and unaffected by this: `ReachabilityCertificate` and the decision layer (`probability_of_conformance`/`cvar`/`asymmetric_cost`/`diagnose_infeasibility`) are never constructed or run against a real domain readout anywhere in this repository — the closure is narrow, covering only the apparatus-parameterisation/gradient-search half of C-5a, not C-5b/C-5c | — (C-5b/C-5c are this same section's own sub-parts, not a distinct cross-row dependency) |
| C-5b | §5 | Reachability certificates | **PASS-B** → Spec §7.1 | ADR-031: linear `Φ`, exact halfspace projection | `src/omi/inverse.py` (`ReachabilityCertificate`, `achievable_bound`, `is_provably_unreachable`, `nearest_reachable_state`) | `tests/oracles/test_known_unreachability.py` | — (same gap as C-5a) | — (own status PASS-B; a provider, not a dependent, row) |
| C-5c | §5 | Decision layer within the degenerate set | **PASS-C** → Spec §7.3 | ADR-033: probability of conformance, CVaR, OQ-4 | `src/omi/inverse.py` (`probability_of_conformance`, `cvar`, `asymmetric_cost`, `select_best_candidate`, `diagnose_infeasibility`) | `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py` | — (same gap as C-5a) | — (own status PASS-C; a provider, not a dependent, row) |
| C-6.1 | §6.1 | Six falsification criteria | **PASS-D** (thresholds) — **threshold-setting procedure now supplied** (M10.3, docs/ROADMAP.md; ADR-041, docs/DECISIONS.md) | criteria as tests; thresholds via ADR | `src/omi/sufficiency.py` (`BlockingTerm.BIAS`, `diagnose_blocking_term`) implements **one of six** criteria (criterion 1, bias-blocked exhaustion); the other five are not operationalised as checks anywhere in the repo. `src/omi/inverse.py::decision_sensitive_threshold` (ADR-041) is the general threshold-setting procedure Spec §9.4 asks for — decision-sensitivity-derived (Spec §7.3's cost/CVaR machinery), applied with worked numeric values to criterion 1 and criterion 3's checkable symptom only; criteria 2, 4, 5, 6 are stated moot, not worked | `tests/test_sufficiency_augmentation_loop.py` (not under `tests/oracles/`, despite testing an estimator against a constructed scenario — a naming/placement inconsistency worth fixing); `tests/test_inverse_decision_layer.py` (`decision_sensitive_threshold` verified against a numerical expected-cost sweep) | — | Full criterion-by-criterion audit in `docs/V1.4-EDITS.md` E-16: criterion 1 evaluable now (no dependency) — worked in `docs/M10.3-FALSIFICATION-THRESHOLDS.md` §2; criterion 2 **blocked** on C-3.7/S-6 (PASS-C, closure-defect measurement); criterion 3 **partially** blocked on S-2.5/S-2.6/S-2.7 (PASS-B, "after all stabilisation measures" is unmet without them — the symptom alone is checkable, worked in M10.3 §3); criterion 4 **blocked** on S-9.3 (PASS-C, narrowed by M10.2/ADR-040 but not closed) and S-7.1 (PASS-B); criterion 5 **still blocked** post-Phase-3.2 — `learning_error`'s stub is fixed (ADR-036) but `augmentation_loop` has no `Chain` to call it with, so `BlockingTerm.LEARNING` can never be produced regardless; criterion 6 **blocked** on C-3.9b (PASS-B — it *is* that row). Four of six not fully evaluable today; E-16 proposes Core §6.1 be qualified accordingly. |
| C-6.2 | §6.2 | Open problems (research questions, not framework claims) | CLAIM | non-implementable; distinct from DECISIONS.md's OQ-1..OQ-5, which are hypotheses this repo generates from reading the specs, not Core's own list — do not conflate the two when recording outcomes | — (non-implementable by definition) | — | — | — (own status CLAIM; but `docs/V1.4-EDITS.md` E-22 bears directly on this row's fifth-slot sub-question — "whether the four-slot schema is complete, or whether some domain requires a fifth" — via M10.1's three sketches: no domain needed a fifth slot; `ν` in the existing four is mistyped instead. E-22 proposes this open problem be restated to ask whether the four slots are correctly *typed*, not only whether a fifth is needed) |
| C-7 | §7 | Two instantiations, declared and diffable | **PASS-D** | `omi_domains/` | `src/omi_domains/flagship/`, `src/omi_domains/contrast/` | — (the diff itself is the verification, see C-4) | `tests/test_interface_diff.py`, `tests/test_chain_rollout.py` (flagship, contrast) | — (own status PASS-D; a provider, not a dependent, row) |
| C-8 | §8 | Positioning against prior art | **PASS-D** | no code implication — literature positioning only; logged for completeness since the text carries an explicit `[Pass D]` marker | — (no code implication) | — | — | — (own status PASS-D; a provider, not a dependent, row) |

---

## Part II — Specification procedures

Same verification axis as Part I (see the note above Part I's table).

| id | Spec § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised | Depends on |
|---|---|---|---|---|---|---|---|---|
| S-1.1 | §1.1 | Three-term error decomposition | SPEC | `sufficiency.py` | `src/omi/sufficiency.py` (`DeficitResult`) | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) | — |
| S-1.2 | §1.2 | **Deficit estimator** `δ² = E[(ρ_A−ρ_B)²] − 2σ²_rep − Σ(∂ρ/∂s)²E[Δs²]` | SPEC | `sufficiency.py` — the only public route to a deficit | `src/omi/sufficiency.py::sufficiency_deficit` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) | — |
| S-1.3 | §1.3 | Variance term = Σ danger scores | SPEC | requires `observability.py` | `src/omi/sufficiency.py::variance_term` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) | — (depends on `observability.py`, S-3.x, itself SPEC not PASS) |
| S-1.4 | §1.4 | Learning error from rollout curve at matched budget | SPEC | `sufficiency.py` (ADR-036, Phase 3.2) | `src/omi/sufficiency.py::learning_error(chain)`: `0.0` for a purely analytic chain, `NotSpecified` citing S-1.4 when the chain contains a `DeepONetOperator` — no longer a silent `0.0` regardless of content (E-02, docs/V1.4-EDITS.md), but a genuine rollout-length-curve-at-matched-budget measurement remains unbuilt, since neither `Chain` nor `DeepONetOperator` retains the ground-truth reference it would need (ADR-036's "What would change this") | — (no oracle for a refusal path; the zero-for-analytic case is structural) | `tests/test_sufficiency_learning_error.py` (flagship, all-analytic `build_chain()` for the zero case; a synthetic, untrained `DeepONetOperator` for the refusal case, since neither declared domain trains a learned operator against a real chain — S-2.1's own gap) | — (own status SPEC; the refusal is a documented architectural limit, not a missing PASS-row derivation) |
| S-1.5 | §1.5 | Augmentation loop (pseudocode given) | SPEC | `sufficiency.py` | `src/omi/sufficiency.py::augmentation_loop` | `tests/test_sufficiency_augmentation_loop.py` (not under `tests/oracles/`, despite testing against a constructed scenario) | — | — |
| S-1.6 | §1.6 | Divergence fingerprint table | SPEC | `sufficiency.py` — see OQ-1 | `src/omi/sufficiency.py::ProbeSet`, `discriminating` | `tests/oracles/test_known_insufficiency.py` (OQ-1 evidence) | — | — |
| S-1.7 | §1.7 | Blocking-term trichotomy | SPEC | `sufficiency.py` | `src/omi/sufficiency.py::BlockingTerm`, `diagnose_blocking_term` | `tests/test_sufficiency_augmentation_loop.py` | — | — |
| S-1.8 | §1.8 | Worked demonstration | **PASS-D** | oracle test | `src/omi/sufficiency.py::sufficiency_deficit` (same as S-1.1/S-1.2) | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) | — (own status PASS-D; a provider, not a dependent, row) |
| S-2.1 | §2.1 | Approximation class and caveats; no composition theorem | SPEC | `operators.py` docs; `learning.py` (DeepONet-style branch/trunk, ADR-029) | `src/omi/learning.py::DeepONetOperator` | `tests/test_learning_gradient_check.py` (hand-rolled backprop vs finite difference) | `tests/test_learning_oracle.py` (contrast, `CYCLING`) | — |
| S-2.2 | §2.2 | Hard structural constraints | SPEC | `constraints.py` — positivity, simplex, monotonicity, conservation implemented; symmetry left to domains (ADR-030); thermodynamic admissibility (GENERIC/port-Hamiltonian) not implemented, scope limitation per ADR-030 | `src/omi/constraints.py` | `tests/test_constraints.py` (off-manifold, adversarial-scale checks; not under `tests/oracles/`); **proposed-v1.4 sixth category (M11.2-M11.3, beyond Spec):** `tests/oracles/known_envelope.py`, `tests/oracles/test_known_envelope.py` — declared constitutive forms with a validated range known by construction, `src/omi/proposed/constitutive.py`, per ADR-043 and `docs/V1.4-EDITS.md` E-32; exercised on real physics by `src/omi_domains/flagship_constitutive/forms.py` (five canonical forms, three two-sided windows and one one-sided, one approximate edge) with `tests/test_flagship_constitutive.py`. **Not an implementation of §2.2**: §2.2 names five categories and none is a constitutive form, so this is a proposed *addition* carrying evidence, reachable only through `omi.proposed` and stamped `SpecificationVersion.PROPOSED_V1_4` | — (confirmed by grep: `src/omi/learning.py` never imports `src/omi/constraints.py` — the constraint layers are implemented but not architecturally wired into the one learned operator the repo has, which is in tension with CLAUDE.md §5 invariant 5's "hard constraints are architecture, never loss penalties") | — (thermodynamic admissibility is an unimplemented sub-item of this SPEC section, ADR-030, not a distinct PASS row) |
| S-2.3 | §2.3 | Training objectives | SPEC | `learning.py` — data fidelity + semigroup-consistency penalty; closure-defect/manifold/reachability regularisation terms not applicable (S-6/manifold learning out of scope) | `src/omi/learning.py::train_deeponet`, `_record_loss_and_grads`, `_semigroup_consistency_loss_and_grads` | `tests/test_learning_gradient_check.py` | `tests/test_learning_oracle.py::test_semigroup_consistency_training_reduces_the_learned_operators_own_residual` (contrast) | — |
| S-2.4 | §2.4 | Stability-aware training; rollout reporting | SPEC | `learning.py` — multi-step pushforward training, noise injection, spectral-norm capping, rollout-length curve (reuses `conformance.rollout_length_error_curve`); manifold projection not implemented, scope limitation per ADR-029 | `src/omi/learning.py::train_deeponet` | — | `tests/test_learning_oracle.py::test_rollout_length_error_curve_reported_for_the_learned_operator` (contrast) | — |
| S-2.5 | §2.5 | **Amplification decomposition `L_phys × L_num`; local spectrum** | **PASS-B** | *"To be written: estimation procedure…"* → ADR or refuse | `src/omi/operators.py::amplification_decomposition` (refusal stub), `LipschitzReport`/`lipschitz_report` (the local-spectrum half, which is implemented) | — (nothing to verify for the refusal; `lipschitz_report` has no dedicated oracle) | `tests/test_lipschitz_report.py` (flagship, `HEATING_AND_SOAK`) | — (own status PASS-B; a provider, not a dependent, row) |
| S-2.6 | §2.6 | **Backward error budgeting** | **PASS-B** | *"To be written: the backward recursion"* → refuse | — (no stub function exists for this specific sub-procedure; refusal is implicit via S-2.5's `amplification_decomposition` covering the same PASS-B gap in this repo's implementation) | — | — | — (own status PASS-B; a provider, not a dependent, row) |
| S-2.7 | §2.7 | **Refusal criterion; trigger condition** | **PASS-B** | *"To be written: the trigger condition"* → refuse | `src/omi/operators.py::amplification_decomposition` (same refusal stub as S-2.5/C-3.9c) | — | `tests/test_lipschitz_report.py::test_amplification_decomposition_refuses_citing_s_2_5` (flagship) | — (own status PASS-B; a provider, not a dependent, row) |
| S-3.1 | §3.1 | Observability Gramian construction; Prop 3.1 | SPEC | `observability.py` | `src/omi/observability.py::compute_gramian` | `tests/oracles/test_known_blind_spot.py` | `tests/test_domain_triage.py` (flagship, contrast) | — |
| S-3.2 | §3.2 | Erasure truncates the Gramian; Prop 3.2, Cor 3.3 | SPEC | `observability.py`, `erasure.py` | `src/omi/observability.py::compute_gramian` (Gramian half); `src/omi/erasure.py` (erasure half) | `tests/oracles/test_erasure_truncates_gramian.py` | — (no domain test combines a declared erasure with a downstream Gramian; `tests/test_domain_triage.py` computes Gramians on both domains but flagship's declared erasure precedes the sensors it uses, not measured jointly, and the erasure-truncation *effect* is checked separately and only qualitatively in `tests/test_error_compounding.py`) | — |
| S-3.3 | §3.3 | Danger score; four-way triage; observed vs inferred vs **unresolved** (criterion corrected at the E-53 milestone, ADR-061) | SPEC | `observability.py` — see OQ-2 | `src/omi/observability.py::danger_triage`, `Triage` | `tests/oracles/test_known_latent_trajectory.py::test_hidden_direction_is_classified_inferred_by_m3_triage` (the only oracle test that reaches `Triage.INFERRED` specifically) | `tests/test_domain_triage.py` (flagship, contrast), Phase 3.3(c): now asserts the **full** `Triage` classification on both domains, not only `dangerous_set()`. **Corrected at the E-53 milestone (ADR-061):** at `time_index=0` (both domains' own query convention) the reachable set is `INFERRED`/`DANGEROUS`/**`UNRESOLVED`**, and the third is the correction — a direction to which no observation contributes has an undefined dominance ratio and now abstains, where the superseded share rule swept it into `INFERRED` through its else-branch. On flagship that moved the domain's **two largest danger scores** out of the inferred set, which is `docs/V1.4-EDITS.md` E-55 and the reason the framework's differentiator must be cited as a per-direction ratio rather than as a count. Previously recorded here as: only `INFERRED`/`DANGEROUS` are reachable at all — `OBSERVED` needs a near-diagonal sensor (none exists at k=0 in either domain's declared suite) and `OBSERVED_BUT_IRRELEVANT`/`MARGINALISABLE` need sub-median influence, impossible once `influence_median == 0.0` (confirmed for both domains — low-dimensional target sets leave over half the eigendirections at exactly-zero influence). `Triage.INFERRED` does appear on both, weighted-checked on contrast per its poor-observation-suite hypothesis, but with ~zero danger score there — present as a label, not as a dangerous-and-specifically-inferred demonstration. ADR-020 (docs/DECISIONS.md) updated with this confirmation of a risk it already named. Also Phase 3.3(b): flagship's target set now includes `bend_angle` (`BendAngleAtReferenceGeometry`, ADR-037) per Spec §3.3's re-run rule; the dangerous set does not materially reorder, because `BendAngle`'s Jacobian at the declared reference geometry is numerically near-identical to `AggregateHardness`'s (both are functionals of the same constitutive operator, whose state-dependence doesn't vary with the applied control) | — (OQ-2's open mixing-erasure question is a separate, unresolved investigation, not a PASS-row dependency) |
| S-3.4 | §3.4 | Value of information; Woodbury; placement | SPEC | `observability.py` | `src/omi/observability.py::value_of_information`, `best_placement` | `tests/test_observability_voi.py::test_woodbury_voi_matches_brute_force_reinversion` (a genuine constructed-truth check, but the file is not under `tests/oracles/`) | — | — |
| S-3.5 | §3.5 | Matrix-free computation by JVP/VJP | SPEC | `observability.py` | `src/omi/observability.py::propagate_jvp`, `propagate_vjp` | `tests/test_observability_jvp_vjp.py` (adjoint identity + agreement with a dense product; not under `tests/oracles/`) | indirectly only — `compute_gramian` calls `propagate_vjp` internally and is domain-exercised (`tests/test_domain_triage.py`), but no domain test calls `propagate_jvp`/`propagate_vjp` directly or checks the adjoint identity against a real operator's Jacobian | — |
| S-3.6 | §3.6 | Trajectory dependence; worst case over window | SPEC | `observability.py` | `src/omi/observability.py::worst_case_over_window` | `tests/test_observability_voi.py::test_worst_case_over_window_returns_the_most_dangerous_trajectory` (synthetic two-scenario comparison) | — | — |
| S-3.7 | §3.7 | Modality catalogue | **PASS-C** | domain-supplied | — (no catalogue structure beyond a tuple of strings on `InstantiationDeclaration.observation_suite`) | — | `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` (declared as strings; not verified against any catalogue schema, because none exists) | — (own status PASS-C; a provider, not a dependent, row) |
| S-4.1 | §4.1 | Class B object: failure driver field, `max D > D_c` | SPEC | `classb.py` | `src/omi/classb.py::JoinedTailModel`, `JoinDiagnostics` | — (no oracle; the driver-field construction is domain content, not framework content, to test against a constructed truth) | `tests/test_flagship_classb_bend.py` (flagship): `BendAngle`'s outer-fibre response across a spatially-correlated `inclusion_content` population is Spec §4.1's driver field, `D_c` = `classb_bend.DRIVER_THRESHOLD` | — |
| S-4.2 | §4.2 | Driver/tail separation; join threshold; diagnostics | SPEC | `classb.py` | `src/omi/classb.py::join_driver_tail`, `join_diagnostics` | — (no oracle) | `tests/test_flagship_classb_bend.py` + `src/omi_domains/flagship/classb_bend.py::run_bend_classb_campaign` (flagship): `join_driver_tail`/`join_diagnostics` run on the real driver field at a declared `threshold_quantile=0.9` | — (this session's E-15: the `p0` gap found here is estimator sampling noise/an unreported uncertainty class, not a missing PASS-row dependency) |
| S-4.3 | §4.3 | Tail transfer `ξ_D = β ξ_a`; Prop 4.1; sanity check | SPEC | `classb.py` — see OQ-3 | `src/omi/classb.py::tail_index_transfer`, `estimate_tail_index_hill` | `tests/oracles/test_known_tail.py`, `tests/test_classb_competing_risks.py` (OQ-3) | — (no domain test calls `tail_index_transfer` or `estimate_tail_index_hill`; the only classb function exercised on a real domain is `validate_volume_scaling_exponent`, see S-4.6) | — (OQ-3 is answered, not a PASS row) |
| S-4.4 | §4.4 | `N_eff`; dimensional reduction; Prop 4.2 | SPEC | `classb.py` — isotropic scalar `ℓ_D` only; anisotropic/directional `ℓ_D` (Spec's explicit banded-structure requirement) not yet implemented, per ADR-027 | `src/omi/classb.py::n_eff`, `estimate_correlation_length` | `tests/oracles/test_known_ranking_inversion.py` (`n_eff` only, and only as a self-consistency check of the formula's own two-regime structure — see `docs/V1.4-EDITS.md` E-14) | `tests/test_flagship_classb_bend.py` (flagship, Phase 2.3): `estimate_correlation_length` run on `BendAngle`'s real driver field (not a hand-supplied `ℓ_D`); bulk regime — three thicknesses above `ℓ_D` — validated by genuine Monte Carlo sampling against the real `BendAngle` (V1.4-EDITS.md E-12), residual sampling-noise-sized, not ~0; thin regime — three thicknesses below `ℓ_D` — remains a formula-identity check only (`n_eff`'s own in-plane-regime algebra), explicitly **not** read as reproducing Prop 4.2's suppression as an emergent effect: `test_thin_regime_dimensional_reduction_is_not_empirically_validated` is permanently skipped, citing Core §2.5's body-indexed state (anti-goal, CLAUDE.md §9) as what a genuine emergent check would require — see `docs/V1.4-EDITS.md` E-14 | **C-2.5** (PASS-C) — confirmed, `docs/V1.4-EDITS.md` E-14 |
| S-4.5 | §4.5 | Rare-event sampling: subset simulation, conditional generative | SPEC | `classb.py` | `src/omi/classb.py::subset_simulation` | `tests/test_classb_subset_simulation.py` (not under `tests/oracles/`) | — | — |
| S-4.6 | §4.6 | Four-rung validation ladder | SPEC | `classb.py` | `src/omi/classb.py::ValidationLadderResult`, `validate_bulk_distribution` (rung 1–2), `validate_psi_by_fractography` (rung 3), `validate_volume_scaling_exponent` (rung 4) | — (no oracle; the ladder validates a domain's real data against its own model, which has no independent constructed truth to check the *validator* against) | `tests/test_conformance_omi2_refusal.py::_contrast_class_b_volume_scaling_residual` (contrast, `DendriteRisk`, rung 4 only, at 3 volumes); `tests/test_flagship_classb_bend.py` + `src/omi_domains/flagship/classb_bend.py::run_bend_classb_campaign` (flagship, Phase 2.3): `ValidationLadderResult` constructed for the first time anywhere in the repo, combining rung 1 (`validate_bulk_distribution`, an independent draw of the same generative model), rung 3 (`validate_psi_by_fractography`, the fitted tail model's predicted exceedances vs. independently-simulated specimen maxima — "simulable here since we know which defect initiated failure"), and rung 4 at six thicknesses straddling the estimated `ℓ_D` (three per regime, not the single fixed-regime 3-volume sweep the contrast test uses) | **C-2.5** (PASS-C) — inherited via rung 4's thin-regime use of `n_eff`, same root cause as S-4.4 (E-14) |
| S-5.1 | §5.1 | Hybrid systems | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — | — (own status PASS-C; a provider, not a dependent, row) |
| S-5.2 | §5.2 | Body-indexed state; registration operator | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — | — (own status PASS-C; a provider, not a dependent, row) |
| S-5.3 | §5.3 | Data reality; closed-loop confounding; grouped splits | **PASS-C** (remedies) / SPEC (grouped splits) | grouped splits only | `src/omi/learning.py::grouped_train_test_split` | `tests/test_learning_grouped_split.py` (disjointness, group-count checks; synthetic records, not under `tests/oracles/`) | `tests/test_learning_oracle.py` (contrast) | — (the grouped-splits half doesn't depend on the unimplemented remedies half of its own row) |
| S-6 | §6 | **Closure-defect measurement** | **PASS-C** — entire section | refuse | `src/omi/conformance.py::measure_closure_defect` (unconditional `NotSpecified`) | — (nothing to verify; the function always refuses) | — (called with no arguments in `tests/test_conformance.py`; never wired into an actual conformance report with real scale-bridging data — matches `build/REVIEW-EXTRACT.md`'s finding) | — (own status PASS-C; a provider, not a dependent, row) |
| S-7.0 | §7.0 | `ℳ_real` vs `ℳ_reach` | SPEC | `inverse.py` | `src/omi/inverse.py` (conceptual basis for the whole module; `nearest_reachable_state`'s docstring cites `ℳ_reach` directly — not a standalone function) | `tests/oracles/test_known_unreachability.py` | — (same OMI-2 gap as C-5a) | **S-7.1** (PASS-B) — `ℳ_reach`'s general construction needs the certificate hierarchy S-7.1 doesn't yet have beyond the linear-Φ rung |
| S-7.1 | §7.1 | **Reachability certificates** | **SPEC** (certificate definition and verification, given a domain-declared `Φ`) / **PASS-B** (the practical hierarchy for constructing or selecting `Φ`; nearest-reachable-state computation) | `inverse.py` — ADR-031 restricts `Φ` to linear functionals; verification and nearest-reachable-state both implemented on that scope; general nonlinear `Φ` and the forward-sampling/over-approximation hierarchy rungs remain unimplemented | `src/omi/inverse.py::ReachabilityCertificate`, `achievable_bound`, `is_provably_unreachable`, `nearest_reachable_state` | `tests/oracles/test_known_unreachability.py` | — (same OMI-2 gap as C-5a) | — (own status SPEC/PASS-B mixed; the practical-hierarchy half is itself the PASS-B row) |
| S-7.2 | §7.2 | **Apparatus parameterisation** | **SPEC** (the "parameterise in apparatus settings, never driving paths" requirement — enforceable as an architectural invariant) / **PASS-C** (constraint-manifold construction, rate limits, mixed-integer handling) | `inverse.py` — ADR-032's `ApparatusParameterization` enforces the requirement structurally for a box `𝒰_adm`; coupled/rate-limited manifold construction and mixed-integer handling remain unimplemented; **now also the box `gradient_control_search` (ADR-040) projects onto**, the first thing in this module to actually search `𝒰_adm` rather than sample or check it | `src/omi/inverse.py::ApparatusParameterization` | `tests/test_inverse_apparatus_parameterisation.py` (structural checks, not under `tests/oracles/`) | **domain-exercised** (M10.2/ADR-040, correcting "same OMI-2 gap as C-5a"): `tests/test_baseline_characterisation.py::_contrast_apparatus` builds a real `ApparatusParameterization` for contrast's `𝒰_adm` and uses it with `gradient_control_search` — box-bounds only, matching this row's own PASS-C scope (no coupled manifold, no mixed-integer case exercised) | — (own status SPEC/PASS-C mixed; the manifold-construction half is itself the PASS-C row) |
| S-7.3 | §7.3 | **Decision layer** | **PASS-C** | `inverse.py` — ADR-033: probability of conformance, CVaR, asymmetric cost, candidate selection, and OQ-4's infeasibility diagnosis | `src/omi/inverse.py::probability_of_conformance`, `cvar`, `asymmetric_cost`, `select_best_candidate`, `diagnose_infeasibility` | `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py` | — (same OMI-2 gap as C-5a) | — (own status PASS-C; a provider, not a dependent, row) |
| S-8 | §8 | **Sufficiency campaign; power analysis** | **SPEC** (power-analysis formula `n ≈ 2(z_{1-α/2}+z_{1-β})²(σ/δ)²`; campaign-matrix design principle) / **PASS-C** (worked numeric values per response class; pre-simulation prediction of which pairs diverge) | formula usable directly; ADR required for worked values | `src/omi/sufficiency.py::required_sample_size` | — (zero test references anywhere in the repo, confirmed by grep — the function is implemented but entirely untested) | — | — (zero test references is an execution gap, not a cross-row PASS dependency) |
| S-9.1 | §9.1 | Conformance levels OMI-0/1/2 | SPEC | `conformance.py` | `src/omi/conformance.py::ConformanceLevel`, `generate_report`, `compare_reports` | — (structural) | `tests/test_conformance_flagship.py` (flagship, reaches OMI-1), `tests/test_conformance_contrast.py` (contrast, reaches OMI-0 only), `tests/test_v14_boundary.py` (M11.1: version carried, cross-version comparison refused) | **Gap found and filled beyond Spec, M11.1**: §9.1 requires an implementation to state its *level* and never the framework *version* the level is claimed against, so a level name is not self-describing once the level table's rows can change (`docs/V1.4-EDITS.md` E-35). `ConformanceReport` now carries a required `SpecificationVersion` and `compare_reports` refuses across versions (ADR-042). This is an addition **beyond** what §9.1 specifies, not an implementation of it — recorded here so a reader does not mistake the field for a Spec requirement |
| S-9.2 | §9.2 | Automated test suite (nine checks) | SPEC | `conformance.py`, CI | `src/omi/conformance.py::automated_check_suite` | — | `tests/test_conformance.py::test_automated_check_suite_reports_unavailable_checks_with_a_reason_not_silently` (flagship) | — |
| S-9.3 | §9.3 | Baselines; grouped splits; prospective validation | SPEC / **PASS-C** (go-no-go table) — **go-no-go table now supplied** (M10.2, docs/ROADMAP.md) | `conformance.py`, `baseline.py` | grouped splits (`src/omi/learning.py::grouped_train_test_split`, see S-5.3) implemented; baseline comparison now implemented: `src/omi/baseline.py` (`RidgeRegressor`, `GradientBoostedTreeRegressor`, `inverse_design_hit_rate`, ADR-039) — a distinct prospective-validation function (predicting a genuinely future/unseen campaign, as opposed to a held-out random sample) is still not implemented | — (no synthetic oracle; the comparison runs against flagship's own ground-truth simulator, which is itself the "truth" the go/no-go table is scored against) | `tests/test_baseline_characterisation.py` (flagship: structure-inverse sweep over composition, since both declared readouts are control-invariant, E-26; contrast: control-inverse sweep over `current`, sensitivity confirmed first); full sweeps in `scripts/run_m10_2_baseline_sweep.py`/`scripts/run_m10_2_contrast_control_inverse_sweep.py`, results in `docs/M10.2-BASELINE-CHARACTERISATION.md`: flagship's structure-inverse regime — tabular (ridge) wins 16/18 configurations on RMSE. Contrast's control-inverse regime, first pass (unconstrained operator graph, naive grid search) — in-trust all three models are competitive; past the trust region only ridge generalises, the gradient-boosted-tree baseline and the (unconstrained) operator graph both fail to extrapolate indistinguishably from each other at every record count tested. Direct diagnosis (ADR-040 addendum, `docs/M10.2-BASELINE-CHARACTERISATION.md`) found this shared `0.50` was two different mechanisms, not one: GBT's is a pure grid-search tie-break artifact (its predictions are exactly constant past the training range); the operator graph's was a genuine, if insufficient, range-compression undershoot. **Re-run performed** (ADR-040): a hard-constrained monotone operator (`src/omi/constraints.py`'s `monotone_increasing`, not a soft penalty) inverted by a new `gradient_control_search` (`src/omi/inverse.py`, previously absent from this module — confirmed by grep before building it) under `𝒰_adm` with the trust region reported as an active per-search diagnostic. In-trust, the constrained operator is now the best-fitting model at every record count tested. Past the trust region, the constrained operator's search genuinely leaves `𝒰_trust` (unlike GBT's fixed tie-break point) but then stalls on a **third** distinct mechanism: its own local gradient vanishes in the flat, "no evidence of further increase" region the hard constraint defaults to past the training data, so the search has nothing left to climb. Ridge's extrapolation win is retained, unchanged in ordering, and read as well-matched inductive bias rather than a defeat for the (now constrained, still net-worse-at-extrapolating-here) operator graph. `𝒰_adm`/`𝒰_trust` remain this investigation's own stated assumptions, not values either domain declares numerically — see `docs/V1.4-EDITS.md` E-27. **A second, independent defect in this section found at M11.4** (`docs/M11.4-EXTRAPOLATION.md`; ADR-045): §9.3's extrapolation prescription — "hold out entire regions of the control space" — was satisfied in full (held-out strain rates `[20, 200]` against `KOCKS_MECKING`'s declared window `[1e-3, 10]`, extrapolation factor min 3.02 / median 11.88 / max 38.34, grouped and never random) and the resulting comparison was **vacuous**: the declared form has no strain-rate dependence at all, so along the held-out axis candidate and baseline agree by construction, and every contestant's held-out RMSE fell in `[7.21, 7.53]` against a withheld-term magnitude of 7.18. Against a drag-free ground truth the *free-form* arm scores 0.077 versus the correct declared form's 0.339, which is the diagnostic. §9.3 nowhere requires the held-out region to be one where the models under comparison differ, so a conforming test can be incapable of discriminating — `docs/V1.4-EDITS.md` **E-39**. **The precondition E-39 proposes is now executable** (M11.5; ADR-045 as amended, ADR-047): `src/omi/proposed/holdout.py::check_hold_out_discriminates` gates a hold-out before it is registered, on in-envelope data only, and **implementing it corrected E-39's own proposed wording** — "materially different predictions" cannot separate the vacuous axis from the usable one (far-point disagreement 0.354 against 0.472, the same order), whereas the withheld-free truth's variation along the axis (0.000 against 3.806) and the disagreement's growth (1.05 against 14.57) separate them decisively. Filed as **E-41**, which supersedes E-39's wording; E-39's finding stands. **The gated re-run (M11.5, `docs/M11.5-EXTRAPOLATION.md`) then found a third defect in this section**: §9.3 scores forward accuracy against the full truth, which rewards a contestant whose extrapolation error cancels the withheld physics. Measured, the ranking inverts by three places at both ends — the correct declared form is exact against a withheld-free truth (0.0000, 1st) and finishes 4th on §9.3's criterion, while the winning tabular baseline is 4th on withheld-free fidelity and 1st on the criterion, its −7.49 signed bias nearly annihilating the withheld term's −6.56. Filed as **E-42**, with the consequence that on field data, where the withheld physics cannot be isolated, a win by cancellation and a win by understanding are indistinguishable. **Substantively, the gated experiment refuted the declared-form claim**: every declared-form arm scored worse than the free-form operator by margins one to two hundred times τ, and a missing *mechanism* (69.55) proved far worse than declaring no form at all while a missing *dependence* (7.56) cost almost nothing | `tests/test_learning_oracle.py` (contrast, grouped splits only); `tests/test_m11_4_extrapolation.py` (E-39's mechanism asserted directly: the withheld term is identically zero in-envelope and active outside, every held-out query is outside the declared window, and the declared form — bare and fitted — is exactly constant along the held-out axis while the generator is not); `tests/test_holdout_discrimination.py` (E-41's retro-validation: the gate refuses M11.4's axis on all three criteria and admits M11.5's, and disagreement magnitude is shown unable to separate them); `tests/test_m11_5_extrapolation.py` (the fair-axis experiment's structure and E-42's mechanism: the withheld term is inert in-envelope, every held-out point is outside the declared window, the declared form varies along *this* axis and diverges from the baseline across it, contestant 1 is sublinear in strain and so a genuine operator rather than a scaled surface, the ranking inverts between the two truths by measured signed bias, and a missing mechanism is more than five times worse than a missing dependence with error growing along the axis) | **S-7.1** (PASS-B) — chased this session: `ReachabilityCertificate`'s `Φ(s)=w·s` is architecturally linear-only (ADR-031), so a domain whose only declared item-6 invariant is nonlinear could never construct one with this repo's `inverse.py`. **Revised, `docs/V1.4-EDITS.md` E-17**: Spec's own text (§7.1's definition box, chased fully) already restricts "reachability certificate" to the sound kind, so this is not a Spec-text gap. `conformance.py`'s `reachability_certificates` field — previously `tuple[str, ...]`, entirely decoupled from `omi.inverse.ReachabilityCertificate` — is now typed `tuple[ReachabilityCertificate, ...] \| None`, closing the loophole structurally; no existing test's conformance level changed, since none supplied a non-`None` value. E-17 proposes Spec §9.1 also restate the soundness requirement inline (not only by cross-reference), which remains open. **A fourth defect in this section found at v1.5 Part 6** (`docs/V1.5-PART6.md` §3; ADR-065): E-41's replacement precondition names a *baseline comparison* as its third criterion, and for a **pre-registered comparative** claim the baseline comparison **is** the registered quantity — so evaluating criterion 3 before the thresholds exist is a peek, and declining to evaluate it reports a two-criterion precondition under a three-criterion name. Filed as **E-58**, with the repair (declare the contrast criterion 3 is evaluated on, and require it to differ from the registered claim's) and the caveat that a two-arm comparative experiment may have no auxiliary contrast at all. Separately, a **Gaussian-process acquisition comparator** was added (`src/omi/baseline.py::GaussianProcessRegressor`, `expected_improvement`, ADR-065) in a role distinct from §9.3's two named tabular baselines, which are unchanged everywhere they are already used — so no existing baseline number is re-based and ADR-057's refusal is scoped rather than overturned. |
| S-9.4 | §9.4 | **Falsification thresholds** | **PASS-D** | ADR per application | — (deliberately, PASS-D) | — | — | — (own status PASS-D; a provider, not a dependent, row) |
| S-9.5 | §9.5 | Uncertainty taxonomy; calibration reporting | SPEC | `conformance.py` | `src/omi/conformance.py::calibration_report` | `tests/test_conformance.py::test_calibration_report_distinguishes_well_calibrated_from_overconfident_ensembles` (synthetic ensembles) | `tests/test_conformance_flagship.py` (flagship, hardness-rollout calibration) | — |
| S-10 | §10 | Operations; innovation drift; lifecycle | **PASS-C** (procedure) / SPEC (proposition) | `assimilate.py` — innovation sequence (SPEC) + NIS chi-squared drift monitor (ADR-026 declares the procedure); recalibration/champion-challenger/rollback remain unimplemented anti-goals | `src/omi/assimilate.py::innovation_drift_monitor` | `tests/oracles/test_known_drift.py` (Phase 3.4: moved under `tests/oracles/` and renamed to match `tests/oracles/known_drift.py`'s own pairing, the naming/placement inconsistency every other row here used to note); `tests/oracles/test_discovery_campaign.py` (the second monitor's null-arm calibration) | — | — (own status PASS-C/SPEC mixed; the procedure half is itself the PASS-C row) **A second declared monitor was added at v1.5 Part 6** (ADR-063): the standardised signed innovation mean `z_n = |mean(d)| / sqrt(mean(S)/n)`, pooled over a campaign, against a standard-normal reference. ADR-026's windowed chi-squared monitor is **unchanged and still the default** — ADR-026's own rejection paragraph pre-authorised a second sign-aware monitor, and its objection (a slack parameter with no Spec basis) does not apply to a standardised mean. The two have different null hypotheses: NIS asks whether the innovations have the predicted *magnitude*, `z_n` whether they have the predicted *mean*, and Spec §10 names neither functional. Measured null calibration on the discovery domain: realised/predicted innovation sd `1.0023`, null `z` mean `0.926` against `E|Z| = 0.798` — mildly over-dispersed by within-campaign correlation, so a control limit is taken from the measured null distribution rather than from the normal quantile (`docs/V1.5-PART6.md` §4). |
| S-11 | §11 | Full instantiation declarations | **PASS-D** | `omi_domains/` | `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` | — (same as C-4) | `tests/test_interface_diff.py` (flagship, contrast) | — (own status PASS-D; a provider, not a dependent, row) |
| S-11.4 | §11.4 | Four interface-only sketches (M10.1, docs/ROADMAP.md) | **PASS-D** — 4 of 4 written, gate met | ADR-038 (docs/DECISIONS.md): `src/omi_domains/sketches/<name>.py`, prose in `docs/SKETCHES.md` | `src/omi_domains/sketches/device_yield.py`, `src/omi_domains/sketches/layerwise_additive.py`, `src/omi_domains/sketches/crystallisation_formulation.py`, `src/omi_domains/sketches/catalyst_under_operation.py` | — (no synthetic oracle; the cross-domain diff against flagship/contrast is the check, same as C-4/S-11) | `tests/test_sketches.py` (all four sketches) | **C-2.5** (PASS-C) — the layer-wise additive sketch's item 1 (state schema) is a forced Tier I approximation for exactly the reason S-4.4/S-4.6 already name: no body-indexed state representation exists to declare the domain's actual, growing-body state faithfully. New finding, not merely a repeat of S-4.4's: this blocks the *declaration* itself (item 1), not only downstream Class-B validation — `docs/V1.4-EDITS.md` E-21. Separately, `docs/V1.4-EDITS.md` E-22 (confirmed on a third, independent domain — crystallisation and formulation's `supersaturation`, Core §3.1's own named example of `ν`) finds `ν` itself, not the body-indexing repair alone, is mis-typed by Core §2.5's literal formula, in two distinct ways (spatial degeneracy and coupling direction). The fourth sketch (catalyst under operation) confirms `StateSchema.is_empty` behaves correctly on a genuinely empty slot — never previously exercised as `True` anywhere in this repository — and explicitly left open whether downstream numerical machinery (erasure/triage/Class B) tolerates near-empty schemas, since that requires an implementation the sketch itself deliberately does not build. **Answered at oracle scale**: `tests/oracles/known_empty_slot.py`/`test_known_empty_slot.py` (M10.1 follow-up) run `measure_erasure`, `compute_gramian`, and `danger_triage` against a minimal chain on a genuinely `m`/`z`/`ν`-empty, `Γ`-only schema — all three run to completion, recovering exact known-by-construction values, with nothing assuming a populated slot |
| S-12 | §12 | **Reference implementation architecture** | **PASS-C** | **this repo is the synthesis — ADR every choice** | — (describes the whole repository; no single module to cite) | — | — | — (own status PASS-C; a provider, not a dependent, row) |

**Note on the "Depends on" sweep.** Every row in both tables above was
checked. Most SPEC rows' "—" reflects a direct comparison against the full
PASS-B/C/D list with no forced dependency found; a handful (C-6.1
specifically) required reading the underlying Core/Spec text criterion-by-
criterion rather than relying on this table's own prose, which is why C-6.1
carries three named dependencies where a shallower pass would have shown
none. Two named dependencies were confirmed by direct code/test
investigation this session (S-4.4→C-2.5 and S-9.3→S-7.1, both with their own
`docs/V1.4-EDITS.md` entries or an explicit no-new-entry finding); the
remainder (C-2.6, C-3.5, C-3.6, S-4.6, S-7.0, C-6.1's three) follow from the
same reasoning applied to structurally similar rows and were not each
independently re-verified by a fresh code investigation — treat those as
sound but not separately re-confirmed.

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

This section records *investigation outcomes* — which oracle tested which
hypothesis, what the measured result was. Proposed v1.4 wording for each
resolved question now lives in `docs/V1.4-EDITS.md`, not here; each entry
below points to its ledger entry rather than restating the wording.

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

> **Status: answered at M4** (`tests/oracles/test_known_insufficiency.py`).
> Confirmed with a constructed kinematic-type hidden variable whose effect
> on the response has *equal magnitude* under forward and reversed
> subsequent driving, differing only in sign: running the sufficiency
> deficit estimator under either single probe alone recovers the *same*
> deficit (ratio within 30% at 8000 pairs, expected to converge to 1 with
> more data) — so "reversed driving only" is false of this variable even
> though it is exactly the directional/kinematic type Spec §1.6's table
> means to name. A single-probe reading would therefore report "insufficient"
> correctly but could not distinguish this candidate from a non-directional
> one showing the same single-probe divergence — confirmed directly:
> `discriminating()` on the naive single-probe signature returns `False` for
> two candidates tuned to share one probe's divergence, while the
> symmetric/antisymmetric decomposition (ADR-022, docs/DECISIONS.md)
> correctly separates them.
>
> **Proposed wording for v1.4:** moved to `docs/V1.4-EDITS.md` E-03.

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

> **Status: answered — diagonal case at M2, mixing case at Phase 3.4**
> (`tests/oracles/test_known_erasure.py`; `tests/oracles/
> test_known_mixing_erasure.py`). The first hypothesis is confirmed with
> evidence: on a diagonal (non-mixing) designed-rank Jacobian with one
> full-gain, one small-gain (0.15), and one exactly-zero-gain component, a
> naive "fraction of variance retained" reading calls the small-gain
> component >95% erased, while the operator-level rank
> (`omi.erasure.measure_erasure`, via SVD) and a per-component
> recoverability estimate (`omi.erasure.component_recoverability`, R² of
> post-step regressed on pre-step — operationalising the "residual variance
> explained by upstream variables" candidate; mutual information is not
> implemented) **agree with each other** and correctly call it fully
> surviving/assimilable (R² > 0.999). The naive heuristic is the one that is
> wrong, not the operator-level/component-level split as such.
>
> **Deferred half, answered at Phase 3.4 (docs/ROADMAP.md).** The oracle
> above is diagonal — each named component aligns with exactly one singular
> direction, so operator-level rank and per-component recoverability could
> not help but agree. Built a genuinely *mixing* erasure oracle (a symmetric
> rank-2 Jacobian whose surviving subspace and kernel both span linear
> combinations of all three named components, none axis-aligned,
> `tests/oracles/known_mixing_erasure.py`): operator-level rank (the single
> integer 2) is silent on per-component influence — the three components'
> designed overlaps with the surviving subspace are `0.833`, `0.833`,
> `0.333` respectively, none 0 or 1. `component_recoverability` gives an
> intermediate, correctly-ordered but not numerically identical picture
> (`~0.78`, `~0.76`, `~0.33`); a new function,
> `omi.erasure.component_surviving_overlap` (a pure geometric projection
> needing no ensemble), recovers the designed values to within `0.01`.
> **Answer: operator-level rank does not predict per-component influence
> under a mixing erasure, and a per-component projection is a genuinely
> distinct, needed diagnostic** — added to `src/omi/erasure.py` rather than
> left as a finding with no corresponding capability.
>
> **Second hypothesis (Core §2.2's suppression rule for surviving
> components) is deferred to M4**, when `sufficiency.py` exists to test it
> against.
>
> **Proposed wording for v1.4:** moved to `docs/V1.4-EDITS.md` E-04 (the
> diagonal-erasure half) and E-18 (the mixing-erasure half, now answered).

**OQ-3 — Competing risks in Class B. Answered M6.**
Spec §4.3 transfers a tail index from one defect population. With several
populations of differing `α` and `β`, survival is `∏ₚ[1−Fₚ]^{Nₚ}` and no single
`ξ` describes the range of interest.
**Test:** two-population oracle; check whether a single-`ξ` fit misestimates
the design-point exceedance probability.

**Evidence.** `tests/test_classb_competing_risks.py`: a common, light-tailed
population (`α=5`, 10,000 members) and a rare, heavy-tailed population
(`α=1.5`, 10 members) drive the same component. At a design point deep enough
that the rare population's heavier tail dominates (its total exceedance
contribution `N·F(d)` exceeds the common population's, despite 1000x fewer
members), pooling every descriptor and fitting one Hill tail index —
exactly what a practitioner unaware of the two populations would do —
underestimates the true, competing-risk-aware failure probability
(`omi.classb.competing_risk_survival`, `∏ₚ[1−Fₚ]^{Nₚ}`) by several orders of
magnitude (observed ratio > 1000x in the constructed case). The pooled fit's
tail index lands close to the *common* population's own `α` because the top
order-statistic window used for fitting is filled overwhelmingly by its far
greater count, even though every individual common-population value is
smaller than the rare population's.

**Answer.** Yes — a single-`ξ` fit misestimates the design-point exceedance
probability, severely and in the unsafe direction (underestimation), whenever
a rare population's tail is heavier than a common population's. This is not a
corner case to caveat; it is the generic behaviour of pooling under
competing risks.

**Proposed wording for v1.4:** moved to `docs/V1.4-EDITS.md` E-05.

**OQ-4 — Does inverse design report *which* variance is binding? Answered M9.**
Spec §7.3 selects within a feasible set. When the set is empty — e.g. aleatoric
spread wider than the specification window — the useful output is which term
made it empty: aleatoric (reduce incoming variation), `𝒰_adm` (apparatus
limits), or trust region (surrogate not calibrated there).
**Test:** oracle with an arithmetically infeasible specification.

**Evidence.** `omi.inverse.diagnose_infeasibility` (ADR-033) checks the
three candidate terms in a fixed, principled order — trust region, then
control/`𝒰_adm`, then aleatoric spread at a declared coverage fraction —
and `tests/oracles/test_known_infeasible_specification.py` constructs four
scenarios (one per binding term, plus a genuinely feasible case) sharing
one linear response model, each engineered so exactly one term is
responsible; the diagnostic recovers the constructed truth in all four.

**Answer.** Yes — inverse design can and should report which term binds,
not merely that the set is empty. The three terms are logically ordered,
not merely enumerable: a trust-region violation means the model was never
asked to extrapolate there (a modelling-scope question), a control
violation means the apparatus cannot reach the window regardless of noise
(a capability question), and only when both are satisfied does the
aleatoric question ("is incoming variation too wide") become meaningful at
all. Checking them in any other order, or reporting all three
simultaneously as an unordered set, would obscure this dependency.

**Proposed wording for v1.4:** moved to `docs/V1.4-EDITS.md` E-06.

**OQ-5 — Metric dependence of every reported `L`.**
Core §3.9 and the erasure definition (`L ≪ 1`) are metric-dependent statements,
and the state has heterogeneous units. Spec §2.5 requires a local spectrum
rather than a global bound but does not fix the metric.
**Test:** rescale a slot; confirm every reported `L` changes; confirm the
aleatoric-sigma normalisation makes them comparable across slots.

> **Status: answered at M2** (`tests/oracles/test_metric_dependence.py`, the
> test ADR-002 names). A fixed linear coupling (raw off-diagonal coefficient
> 0.01, one component's natural scale 100x the other's) demonstrates both
> halves directly:
>
> 1. **Every reported `L` changes with the declared metric.** The same
>    operator's local spectrum differs substantially between a bare/unit
>    metric (`scale = [1, 1]`) and the default aleatoric-sigma metric — not
>    an approximation, a different matrix gets SVD'd.
> 2. **The bare metric hides real coupling; the declared one reveals it.**
>    Scaled by the bare metric, the off-diagonal term reads as negligible
>    (< 0.02) next to the diagonal (1.0) — a naive, metric-blind conclusion.
>    Scaled by the aleatoric-sigma metric, the same raw coefficient reads as
>    fully as strong as the diagonal (> 0.5), which matches direct empirical
>    perturbation: moving each component by its own one-sigma moves the
>    readout by a comparable amount for both (ratio within a factor of 2),
>    not the ~100x discrepancy a raw comparison would show.
>
> This confirms ADR-002's default (aleatoric-sigma non-dimensionalisation)
> does what it is meant to: make cross-component comparison physically
> meaningful rather than an artifact of unit choice.
>
> **Proposed wording for v1.4:** none — recorded as a deliberate confirmation
> in `docs/V1.4-EDITS.md` E-07, not a silently-dropped investigation.

---

## Maintaining this file

- When a `[Pass B]`/`[Pass C]` is resolved upstream in a new framework version,
  change the status and remove the ADR that stood in for it.
- When an open question is settled by a test, record the outcome here and in
  `DECISIONS.md`, and propose the framework edit as a new entry in
  `docs/V1.4-EDITS.md` (CLAUDE.md §10) — not inline here.
- Every `NotSpecified` raised in the codebase must cite an id in this table.
  A CI check enforces it.
- **Core Appendix B (the general ↔ domain glossary) carries its own
  `[Pass A, in progress]` marker** — it is not a claims/procedure row and has
  none here, but it is load-bearing for the vocabulary lint (`ADR-006`,
  `tests/test_vocabulary.py`): the banned-term seed list is drawn from it and
  is therefore necessarily partial. The lint must stay trivially extensible
  (a list, not a hardcoded pattern) rather than treating Appendix B as
  exhaustive, and the seed list should grow as `omi_domains/` grows.
