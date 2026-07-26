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

| id | Core § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised |
|---|---|---|---|---|---|---|---|
| C-2.1 | §2.1 | Axiom S; sufficiency test by matched-history pairs | SPEC (concept) → Spec §8 for campaign | `sufficiency.py` | `src/omi/sufficiency.py` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship, matched-pair campaign) |
| C-2.2 | §2.2 | State selection as measurable bias–variance | **PASS-B** in Core, but **estimators are SPEC** in Spec §1 | `sufficiency.py` — implement via S-1, not from Core | `src/omi/sufficiency.py` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) |
| C-2.3 | §2.3 | Two primitives; fusion is not a primitive | CLAIM | test: no fusion API exists | — (absence claim; nothing to implement) | — (no test asserts the absence directly; a repo-wide grep for "fusion" turns up zero matches, which is the honest state of the "test" this row's own Repo column describes) | — |
| C-2.4 | §2.4 | Two tiers, material and component | CLAIM | Tier II is an anti-goal; Tier I only | — (anti-goal, CLAUDE.md §9) | — | — |
| C-2.5 | §2.5 | Body-indexed state | **PASS-C** | anti-goal; state is per material point | — (anti-goal, CLAUDE.md §9) | — | — |
| C-2.6 | §2.6 | Property vs performance by invariance | SPEC | `readouts.py` typing | `src/omi/readouts.py` (`ReadoutClass`, Type 0/1/2 taxonomy) | — (no synthetic oracle for the invariance property itself) | `tests/test_readouts.py` (flagship: `AggregateHardness`/`ExtractHardness` Type-0/1 identity; contrast: `DendriteRisk` Class B) |
| C-3.1 | §3.1 | Four-slot state schema | SPEC | `state.py` | `src/omi/state.py` | — (structural; nothing to recover against a constructed truth) | `tests/test_chain_rollout.py`, `tests/test_semigroup.py` (flagship, contrast) |
| C-3.2 | §3.2 | Spaces and type discipline | SPEC | `state.py`, `chain.py` | `src/omi/state.py`, `src/omi/chain.py` | — (structural) | `tests/test_chain_rollout.py` (flagship, contrast) |
| C-3.3 | §3.3 | Evolution; pushforward/kernel lift; semigroup identity | SPEC | `operators.py` | `src/omi/operators.py` | — (structural identity, not a recovered quantity) | `tests/test_semigroup.py` (flagship: `HEATING_AND_SOAK`, `TRANSFER`; contrast: `CYCLING`) |
| C-3.4 | §3.4 | Hybrid continuous–discrete structure | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — |
| C-3.5 | §3.5 | Readout types 0/1/2 | SPEC | `readouts.py` | `src/omi/readouts.py` | — | `tests/test_readouts.py` (flagship, contrast) |
| C-3.6 | §3.6 | Class A/B; tail-index transfer; dimensional reduction | SPEC → Spec §4 | `classb.py` | `src/omi/classb.py` | `tests/oracles/test_known_tail.py`, `tests/oracles/test_known_ranking_inversion.py`, `tests/test_classb_competing_risks.py` | `tests/test_readouts.py::test_contrast_dendrite_risk_is_class_b_and_weakest_link_works` (contrast, `weakest_link` only); `tests/test_conformance_omi2_refusal.py` (contrast, `validate_volume_scaling_exponent` at 3 volumes — see S-4.4); ten of `src/omi/classb.py`'s sixteen public symbols (`join_driver_tail`, `join_diagnostics`, `estimate_correlation_length`, `ValidationLadderResult`, etc.) have no domain test and no oracle test at all, per S-4.1/S-4.2/S-4.6 below |
| C-3.7 | §3.7 | Homogenisation; closure defect *definition*; RG scope | SPEC (definition) / **PASS-C** (measurement, Spec §6) | definition only | — (definition only; `measure_closure_defect` in `src/omi/conformance.py` is an unconditional refusal stub, not an implementation of the definition) | — | — |
| C-3.8 | §3.8 | Assimilation; Gramian; danger score; erasure truncation | SPEC → Spec §3 | `observability.py`, `assimilate.py` | `src/omi/observability.py`, `src/omi/assimilate.py` | `tests/oracles/test_known_blind_spot.py`, `tests/oracles/test_erasure_truncates_gramian.py`, `tests/oracles/test_known_latent_trajectory.py`, `tests/test_innovation_drift_monitor.py` | `tests/test_domain_triage.py` (flagship, contrast) exercises `src/omi/observability.py`'s Gramian/danger-triage only; `src/omi/assimilate.py`'s EnKF/smoother/drift-monitor has no domain test (its oracles — `tests/oracles/known_latent_trajectory.py`, `tests/oracles/known_drift.py` — are synthetic schemas, not `omi_domains`) |
| C-3.9a | §3.9 | Error compounding bound; erasure definition and consequences | SPEC | `erasure.py`, `operators.py` | `src/omi/erasure.py`, `src/omi/operators.py` (`.is_erasure`) | `tests/oracles/test_known_erasure.py` | `tests/test_error_compounding.py` (flagship, `HEATING_AND_SOAK`) demonstrates the damping *effect* directly on perturbed states, but never calls `src/omi/erasure.py`'s `measure_erasure`/`component_recoverability` — those two functions are called from exactly one place in the repo, `tests/oracles/test_known_erasure.py` |
| C-3.9b | §3.9 | **Error-control dichotomy** (erasure or observation) | **PASS-B** | test only; do not implement a scoping check | — (deliberately no scoping-check module) | — | `tests/test_conformance_flagship.py::test_flagship_matched_pair_deficit_is_at_noise_level` (flagship) exercises condition (a) only; condition (b) — continuous assimilation controlling error where no erasure exists — is untested on the contrast domain: `tests/test_conformance_contrast.py` only checks `erasure_inventory == ()` declaratively, no contrast-domain assimilation campaign runs anywhere |
| C-3.9c | §3.9 | **Refusal criterion**; `L_phys × L_num` | **PASS-B** → Spec §2.5–2.7 | refuse | `src/omi/operators.py::amplification_decomposition` (unconditional `NotSpecified`, cites S-2.5) | — (nothing to verify; the function always refuses) | `tests/test_lipschitz_report.py::test_amplification_decomposition_refuses_citing_s_2_5` (flagship, `HEATING_AND_SOAK`) — the refusal path itself is domain-exercised, not the (nonexistent) decomposition |
| C-4 | §4 | Seven-item instantiation interface | SPEC | `omi_domains/*/interface.py` — ADR-034 (docs/DECISIONS.md) supersedes ADR-003's pinning test: Core §7.2's seven rows name six distinct Core §4 items, not seven, and `interface.diff()` now also reports a structural (kind-based) comparison for item 6's invariants alongside the literal one | `src/omi/interface.py`, `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` | — (no synthetic oracle; the cross-domain diff is the check) | `tests/test_interface_diff.py` (flagship, contrast) |
| C-5a | §5 | Inverse design as constrained optimal control | SPEC (formulation) | `inverse.py` | `src/omi/inverse.py` | `tests/oracles/test_known_unreachability.py`, `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py`, `tests/test_inverse_apparatus_parameterisation.py` | — (no test anywhere imports both `omi.inverse` and `omi_domains`; confirmed by grep — this is the OMI-2 gap flagged in `build/REVIEW-EXTRACT.md` §1/§4) |
| C-5b | §5 | Reachability certificates | **PASS-B** → Spec §7.1 | ADR-031: linear `Φ`, exact halfspace projection | `src/omi/inverse.py` (`ReachabilityCertificate`, `achievable_bound`, `is_provably_unreachable`, `nearest_reachable_state`) | `tests/oracles/test_known_unreachability.py` | — (same gap as C-5a) |
| C-5c | §5 | Decision layer within the degenerate set | **PASS-C** → Spec §7.3 | ADR-033: probability of conformance, CVaR, OQ-4 | `src/omi/inverse.py` (`probability_of_conformance`, `cvar`, `asymmetric_cost`, `select_best_candidate`, `diagnose_infeasibility`) | `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py` | — (same gap as C-5a) |
| C-6.1 | §6.1 | Six falsification criteria | **PASS-D** (thresholds) | criteria as tests; thresholds via ADR | `src/omi/sufficiency.py` (`BlockingTerm.BIAS`, `diagnose_blocking_term`) implements **one of six** criteria (criterion 1, bias-blocked exhaustion); the other five are not operationalised as checks anywhere in the repo | `tests/test_sufficiency_augmentation_loop.py` (not under `tests/oracles/`, despite testing an estimator against a constructed scenario — a naming/placement inconsistency worth fixing) | — |
| C-6.2 | §6.2 | Open problems (research questions, not framework claims) | CLAIM | non-implementable; distinct from DECISIONS.md's OQ-1..OQ-5, which are hypotheses this repo generates from reading the specs, not Core's own list — do not conflate the two when recording outcomes | — (non-implementable by definition) | — | — |
| C-7 | §7 | Two instantiations, declared and diffable | **PASS-D** | `omi_domains/` | `src/omi_domains/flagship/`, `src/omi_domains/contrast/` | — (the diff itself is the verification, see C-4) | `tests/test_interface_diff.py`, `tests/test_chain_rollout.py` (flagship, contrast) |
| C-8 | §8 | Positioning against prior art | **PASS-D** | no code implication — literature positioning only; logged for completeness since the text carries an explicit `[Pass D]` marker | — (no code implication) | — | — |

---

## Part II — Specification procedures

Same verification axis as Part I (see the note above Part I's table).

| id | Spec § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised |
|---|---|---|---|---|---|---|---|
| S-1.1 | §1.1 | Three-term error decomposition | SPEC | `sufficiency.py` | `src/omi/sufficiency.py` (`DeficitResult`) | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) |
| S-1.2 | §1.2 | **Deficit estimator** `δ² = E[(ρ_A−ρ_B)²] − 2σ²_rep − Σ(∂ρ/∂s)²E[Δs²]` | SPEC | `sufficiency.py` — the only public route to a deficit | `src/omi/sufficiency.py::sufficiency_deficit` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) |
| S-1.3 | §1.3 | Variance term = Σ danger scores | SPEC | requires `observability.py` | `src/omi/sufficiency.py::variance_term` | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) |
| S-1.4 | §1.4 | Learning error from rollout curve at matched budget | SPEC | requires learning milestone | `src/omi/sufficiency.py::learning_error` — unconditionally returns `0.0` regardless of arguments (it takes none); ADR-023 declares this correct for analytic-only chains, but the function has no path that ever returns anything else, including when the chain contains a learned operator (M8's `src/omi/learning.py`) — Phase 3.2 tracks fixing this | — | — |
| S-1.5 | §1.5 | Augmentation loop (pseudocode given) | SPEC | `sufficiency.py` | `src/omi/sufficiency.py::augmentation_loop` | `tests/test_sufficiency_augmentation_loop.py` (not under `tests/oracles/`, despite testing against a constructed scenario) | — |
| S-1.6 | §1.6 | Divergence fingerprint table | SPEC | `sufficiency.py` — see OQ-1 | `src/omi/sufficiency.py::ProbeSet`, `discriminating` | `tests/oracles/test_known_insufficiency.py` (OQ-1 evidence) | — |
| S-1.7 | §1.7 | Blocking-term trichotomy | SPEC | `sufficiency.py` | `src/omi/sufficiency.py::BlockingTerm`, `diagnose_blocking_term` | `tests/test_sufficiency_augmentation_loop.py` | — |
| S-1.8 | §1.8 | Worked demonstration | **PASS-D** | oracle test | `src/omi/sufficiency.py::sufficiency_deficit` (same as S-1.1/S-1.2) | `tests/oracles/test_known_insufficiency.py` | `tests/test_conformance_flagship.py` (flagship) |
| S-2.1 | §2.1 | Approximation class and caveats; no composition theorem | SPEC | `operators.py` docs; `learning.py` (DeepONet-style branch/trunk, ADR-029) | `src/omi/learning.py::DeepONetOperator` | `tests/test_learning_gradient_check.py` (hand-rolled backprop vs finite difference) | `tests/test_learning_oracle.py` (contrast, `CYCLING`) |
| S-2.2 | §2.2 | Hard structural constraints | SPEC | `constraints.py` — positivity, simplex, monotonicity, conservation implemented; symmetry left to domains (ADR-030); thermodynamic admissibility (GENERIC/port-Hamiltonian) not implemented, scope limitation per ADR-030 | `src/omi/constraints.py` | `tests/test_constraints.py` (off-manifold, adversarial-scale checks; not under `tests/oracles/`) | — (confirmed by grep: `src/omi/learning.py` never imports `src/omi/constraints.py` — the constraint layers are implemented but not architecturally wired into the one learned operator the repo has, which is in tension with CLAUDE.md §5 invariant 5's "hard constraints are architecture, never loss penalties") |
| S-2.3 | §2.3 | Training objectives | SPEC | `learning.py` — data fidelity + semigroup-consistency penalty; closure-defect/manifold/reachability regularisation terms not applicable (S-6/manifold learning out of scope) | `src/omi/learning.py::train_deeponet`, `_record_loss_and_grads`, `_semigroup_consistency_loss_and_grads` | `tests/test_learning_gradient_check.py` | `tests/test_learning_oracle.py::test_semigroup_consistency_training_reduces_the_learned_operators_own_residual` (contrast) |
| S-2.4 | §2.4 | Stability-aware training; rollout reporting | SPEC | `learning.py` — multi-step pushforward training, noise injection, spectral-norm capping, rollout-length curve (reuses `conformance.rollout_length_error_curve`); manifold projection not implemented, scope limitation per ADR-029 | `src/omi/learning.py::train_deeponet` | — | `tests/test_learning_oracle.py::test_rollout_length_error_curve_reported_for_the_learned_operator` (contrast) |
| S-2.5 | §2.5 | **Amplification decomposition `L_phys × L_num`; local spectrum** | **PASS-B** | *"To be written: estimation procedure…"* → ADR or refuse | `src/omi/operators.py::amplification_decomposition` (refusal stub), `LipschitzReport`/`lipschitz_report` (the local-spectrum half, which is implemented) | — (nothing to verify for the refusal; `lipschitz_report` has no dedicated oracle) | `tests/test_lipschitz_report.py` (flagship, `HEATING_AND_SOAK`) |
| S-2.6 | §2.6 | **Backward error budgeting** | **PASS-B** | *"To be written: the backward recursion"* → refuse | — (no stub function exists for this specific sub-procedure; refusal is implicit via S-2.5's `amplification_decomposition` covering the same PASS-B gap in this repo's implementation) | — | — |
| S-2.7 | §2.7 | **Refusal criterion; trigger condition** | **PASS-B** | *"To be written: the trigger condition"* → refuse | `src/omi/operators.py::amplification_decomposition` (same refusal stub as S-2.5/C-3.9c) | — | `tests/test_lipschitz_report.py::test_amplification_decomposition_refuses_citing_s_2_5` (flagship) |
| S-3.1 | §3.1 | Observability Gramian construction; Prop 3.1 | SPEC | `observability.py` | `src/omi/observability.py::compute_gramian` | `tests/oracles/test_known_blind_spot.py` | `tests/test_domain_triage.py` (flagship, contrast) |
| S-3.2 | §3.2 | Erasure truncates the Gramian; Prop 3.2, Cor 3.3 | SPEC | `observability.py`, `erasure.py` | `src/omi/observability.py::compute_gramian` (Gramian half); `src/omi/erasure.py` (erasure half) | `tests/oracles/test_erasure_truncates_gramian.py` | — (no domain test combines a declared erasure with a downstream Gramian; `tests/test_domain_triage.py` computes Gramians on both domains but flagship's declared erasure precedes the sensors it uses, not measured jointly, and the erasure-truncation *effect* is checked separately and only qualitatively in `tests/test_error_compounding.py`) |
| S-3.3 | §3.3 | Danger score; four-way triage; observed vs inferred | SPEC | `observability.py` — see OQ-2 | `src/omi/observability.py::danger_triage`, `Triage` | `tests/oracles/test_known_latent_trajectory.py::test_hidden_direction_is_classified_inferred_by_m3_triage` (the only oracle test that reaches `Triage.INFERRED` specifically) | `tests/test_domain_triage.py` (flagship, contrast) reaches `dangerous_set()` and the unresolved-danger-fraction comparison, but neither domain test asserts a full `Triage` classification (`OBSERVED`/`INFERRED`/etc. per direction) the way the oracle test does — whether `Triage.INFERRED` ever appears on a *real* domain is untested (Phase 3.3 tracks this) |
| S-3.4 | §3.4 | Value of information; Woodbury; placement | SPEC | `observability.py` | `src/omi/observability.py::value_of_information`, `best_placement` | `tests/test_observability_voi.py::test_woodbury_voi_matches_brute_force_reinversion` (a genuine constructed-truth check, but the file is not under `tests/oracles/`) | — |
| S-3.5 | §3.5 | Matrix-free computation by JVP/VJP | SPEC | `observability.py` | `src/omi/observability.py::propagate_jvp`, `propagate_vjp` | `tests/test_observability_jvp_vjp.py` (adjoint identity + agreement with a dense product; not under `tests/oracles/`) | indirectly only — `compute_gramian` calls `propagate_vjp` internally and is domain-exercised (`tests/test_domain_triage.py`), but no domain test calls `propagate_jvp`/`propagate_vjp` directly or checks the adjoint identity against a real operator's Jacobian |
| S-3.6 | §3.6 | Trajectory dependence; worst case over window | SPEC | `observability.py` | `src/omi/observability.py::worst_case_over_window` | `tests/test_observability_voi.py::test_worst_case_over_window_returns_the_most_dangerous_trajectory` (synthetic two-scenario comparison) | — |
| S-3.7 | §3.7 | Modality catalogue | **PASS-C** | domain-supplied | — (no catalogue structure beyond a tuple of strings on `InstantiationDeclaration.observation_suite`) | — | `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` (declared as strings; not verified against any catalogue schema, because none exists) |
| S-4.1 | §4.1 | Class B object: failure driver field, `max D > D_c` | SPEC | `classb.py` | `src/omi/classb.py::JoinedTailModel`, `JoinDiagnostics` | — (zero test references anywhere in the repo, confirmed by grep) | — |
| S-4.2 | §4.2 | Driver/tail separation; join threshold; diagnostics | SPEC | `classb.py` | `src/omi/classb.py::join_driver_tail`, `join_diagnostics` | — (zero test references anywhere in the repo, confirmed by grep) | — |
| S-4.3 | §4.3 | Tail transfer `ξ_D = β ξ_a`; Prop 4.1; sanity check | SPEC | `classb.py` — see OQ-3 | `src/omi/classb.py::tail_index_transfer`, `estimate_tail_index_hill` | `tests/oracles/test_known_tail.py`, `tests/test_classb_competing_risks.py` (OQ-3) | — (no domain test calls `tail_index_transfer` or `estimate_tail_index_hill`; the only classb function exercised on a real domain is `validate_volume_scaling_exponent`, see S-4.6) |
| S-4.4 | §4.4 | `N_eff`; dimensional reduction; Prop 4.2 | SPEC | `classb.py` — isotropic scalar `ℓ_D` only; anisotropic/directional `ℓ_D` (Spec's explicit banded-structure requirement) not yet implemented, per ADR-027 | `src/omi/classb.py::n_eff`, `estimate_correlation_length` | `tests/oracles/test_known_ranking_inversion.py` (`n_eff` only — `estimate_correlation_length` has zero test references anywhere) | — (`validate_volume_scaling_exponent`, S-4.6's domain evidence, does not call `n_eff` internally — it fits an exponent from caller-supplied data and compares against a caller-supplied predicted exponent, confirmed by reading its body) |
| S-4.5 | §4.5 | Rare-event sampling: subset simulation, conditional generative | SPEC | `classb.py` | `src/omi/classb.py::subset_simulation` | `tests/test_classb_subset_simulation.py` (not under `tests/oracles/`) | — |
| S-4.6 | §4.6 | Four-rung validation ladder | SPEC | `classb.py` | `src/omi/classb.py::ValidationLadderResult`, `validate_bulk_distribution` (rung 1–2), `validate_psi_by_fractography` (rung 3), `validate_volume_scaling_exponent` (rung 4) | — (rungs 1–3 have zero test references anywhere in the repo, confirmed by grep; `ValidationLadderResult` itself is never constructed anywhere) | `tests/test_conformance_omi2_refusal.py::_contrast_class_b_volume_scaling_residual` (contrast, `DendriteRisk`, rung 4 only, at 3 volumes — not the ≥3-thicknesses-straddling-`ℓ_D` sweep Phase 2.3 calls for) |
| S-5.1 | §5.1 | Hybrid systems | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — |
| S-5.2 | §5.2 | Body-indexed state; registration operator | **PASS-C** | anti-goal | — (anti-goal, CLAUDE.md §9) | — | — |
| S-5.3 | §5.3 | Data reality; closed-loop confounding; grouped splits | **PASS-C** (remedies) / SPEC (grouped splits) | grouped splits only | `src/omi/learning.py::grouped_train_test_split` | `tests/test_learning_grouped_split.py` (disjointness, group-count checks; synthetic records, not under `tests/oracles/`) | `tests/test_learning_oracle.py` (contrast) |
| S-6 | §6 | **Closure-defect measurement** | **PASS-C** — entire section | refuse | `src/omi/conformance.py::measure_closure_defect` (unconditional `NotSpecified`) | — (nothing to verify; the function always refuses) | — (called with no arguments in `tests/test_conformance.py`; never wired into an actual conformance report with real scale-bridging data — matches `build/REVIEW-EXTRACT.md`'s finding) |
| S-7.0 | §7.0 | `ℳ_real` vs `ℳ_reach` | SPEC | `inverse.py` | `src/omi/inverse.py` (conceptual basis for the whole module; `nearest_reachable_state`'s docstring cites `ℳ_reach` directly — not a standalone function) | `tests/oracles/test_known_unreachability.py` | — (same OMI-2 gap as C-5a) |
| S-7.1 | §7.1 | **Reachability certificates** | **SPEC** (certificate definition and verification, given a domain-declared `Φ`) / **PASS-B** (the practical hierarchy for constructing or selecting `Φ`; nearest-reachable-state computation) | `inverse.py` — ADR-031 restricts `Φ` to linear functionals; verification and nearest-reachable-state both implemented on that scope; general nonlinear `Φ` and the forward-sampling/over-approximation hierarchy rungs remain unimplemented | `src/omi/inverse.py::ReachabilityCertificate`, `achievable_bound`, `is_provably_unreachable`, `nearest_reachable_state` | `tests/oracles/test_known_unreachability.py` | — (same OMI-2 gap as C-5a) |
| S-7.2 | §7.2 | **Apparatus parameterisation** | **SPEC** (the "parameterise in apparatus settings, never driving paths" requirement — enforceable as an architectural invariant) / **PASS-C** (constraint-manifold construction, rate limits, mixed-integer handling) | `inverse.py` — ADR-032's `ApparatusParameterization` enforces the requirement structurally for a box `𝒰_adm`; coupled/rate-limited manifold construction and mixed-integer handling remain unimplemented | `src/omi/inverse.py::ApparatusParameterization` | `tests/test_inverse_apparatus_parameterisation.py` (structural checks, not under `tests/oracles/`) | — (same OMI-2 gap as C-5a) |
| S-7.3 | §7.3 | **Decision layer** | **PASS-C** | `inverse.py` — ADR-033: probability of conformance, CVaR, asymmetric cost, candidate selection, and OQ-4's infeasibility diagnosis | `src/omi/inverse.py::probability_of_conformance`, `cvar`, `asymmetric_cost`, `select_best_candidate`, `diagnose_infeasibility` | `tests/oracles/test_known_infeasible_specification.py`, `tests/test_inverse_decision_layer.py` | — (same OMI-2 gap as C-5a) |
| S-8 | §8 | **Sufficiency campaign; power analysis** | **SPEC** (power-analysis formula `n ≈ 2(z_{1-α/2}+z_{1-β})²(σ/δ)²`; campaign-matrix design principle) / **PASS-C** (worked numeric values per response class; pre-simulation prediction of which pairs diverge) | formula usable directly; ADR required for worked values | `src/omi/sufficiency.py::required_sample_size` | — (zero test references anywhere in the repo, confirmed by grep — the function is implemented but entirely untested) | — |
| S-9.1 | §9.1 | Conformance levels OMI-0/1/2 | SPEC | `conformance.py` | `src/omi/conformance.py::ConformanceLevel`, `generate_report` | — (structural) | `tests/test_conformance_flagship.py` (flagship, reaches OMI-1), `tests/test_conformance_contrast.py` (contrast, reaches OMI-0 only) |
| S-9.2 | §9.2 | Automated test suite (nine checks) | SPEC | `conformance.py`, CI | `src/omi/conformance.py::automated_check_suite` | — | `tests/test_conformance.py::test_automated_check_suite_reports_unavailable_checks_with_a_reason_not_silently` (flagship) |
| S-9.3 | §9.3 | Baselines; grouped splits; prospective validation | SPEC / **PASS-C** (go-no-go table) | `conformance.py` | partial — grouped splits (`src/omi/learning.py::grouped_train_test_split`, see S-5.3) implemented; a distinct baseline-comparison or prospective-validation function is not implemented, only a completeness-gate requirement name in `src/omi/conformance.py` | — | `tests/test_learning_oracle.py` (contrast, grouped splits only) |
| S-9.4 | §9.4 | **Falsification thresholds** | **PASS-D** | ADR per application | — (deliberately, PASS-D) | — | — |
| S-9.5 | §9.5 | Uncertainty taxonomy; calibration reporting | SPEC | `conformance.py` | `src/omi/conformance.py::calibration_report` | `tests/test_conformance.py::test_calibration_report_distinguishes_well_calibrated_from_overconfident_ensembles` (synthetic ensembles) | `tests/test_conformance_flagship.py` (flagship, hardness-rollout calibration) |
| S-10 | §10 | Operations; innovation drift; lifecycle | **PASS-C** (procedure) / SPEC (proposition) | `assimilate.py` — innovation sequence (SPEC) + NIS chi-squared drift monitor (ADR-026 declares the procedure); recalibration/champion-challenger/rollback remain unimplemented anti-goals | `src/omi/assimilate.py::innovation_drift_monitor` | `tests/test_innovation_drift_monitor.py` (synthetic `tests/oracles/known_drift.py` oracle; not under `tests/oracles/` despite testing against a constructed planted-drift scenario) | — |
| S-11 | §11 | Full instantiation declarations | **PASS-D** | `omi_domains/` | `src/omi_domains/flagship/interface.py`, `src/omi_domains/contrast/interface.py` | — (same as C-4) | `tests/test_interface_diff.py` (flagship, contrast) |
| S-12 | §12 | **Reference implementation architecture** | **PASS-C** | **this repo is the synthesis — ADR every choice** | — (describes the whole repository; no single module to cite) | — | — |

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
> **Proposed wording for v1.4 (Spec §1.6):** rows in the divergence
> fingerprint table should name *contrasts between paired-probe responses*
> (e.g. "antisymmetric under forward/reversed reversal → kinematic
> variable") rather than "which single probe diverges" — the latter is
> unreliable exactly for the directional-variable case the table most wants
> to catch.

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

> **Status: partially answered at M2** (`tests/oracles/test_known_erasure.py`).
> The first hypothesis is confirmed with evidence: on a diagonal (non-mixing)
> designed-rank Jacobian with one full-gain, one small-gain (0.15), and one
> exactly-zero-gain component, a naive "fraction of variance retained"
> reading calls the small-gain component >95% erased, while the
> operator-level rank (`omi.erasure.measure_erasure`, via SVD) and a
> per-component recoverability estimate (`omi.erasure.component_recoverability`,
> R² of post-step regressed on pre-step — operationalising the "residual
> variance explained by upstream variables" candidate; mutual information is
> not implemented) **agree with each other** and correctly call it fully
> surviving/assimilable (R² > 0.999). The naive heuristic is the one that is
> wrong, not the operator-level/component-level split as such.
>
> **Refined open question, not yet tested:** the oracle above is diagonal —
> each named component aligns with exactly one singular direction, so
> operator-level rank and per-component recoverability could not help but
> agree. The genuinely open case is a *mixing* erasure (non-diagonal
> Jacobian, surviving subspace spanning a linear combination of several named
> components) — there, does operator-level rank still predict per-component
> influence, or does the framework need a per-component projection onto the
> surviving subspace as a distinct diagnostic? Left open for M3+
> (`observability.py`'s Gramian gives the natural machinery for this).
>
> **Second hypothesis (Core §2.2's suppression rule for surviving
> components) is deferred to M4**, when `sufficiency.py` exists to test it
> against.
>
> **Proposed wording for v1.4 (Core §3.9 consequence 3):** append a caveat —
> "Erasure completeness must not be read off a component's raw magnitude or
> variance reduction: a component can lose most of its magnitude and remain
> exactly recoverable. Use mutual information or residual variance explained
> (R²) against the pre-erasure state, not the component's own scale."

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

**Proposed wording for v1.4 (Spec §4.3, after Proposition 4.1):** append a
requirement — "Where more than one defect population plausibly contributes
to the same driver, each population's tail index MUST be measured and
transferred separately (`ξ_{D,p} = β_p·ξ_{a,p}`) and combined via the
competing-risks survival product; fitting a single pooled tail index across
populations of differing severity is non-conforming, since the fit is
dominated by whichever population is most numerous in the fitting window,
not by whichever population actually governs the design point."

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

**Proposed wording for v1.4 (Spec §7.3, as an explicit requirement):**
append — "When the decision layer's feasible set is empty, an
implementation MUST report which of trust region, apparatus admissibility
(`𝒰_adm`), or aleatoric spread is responsible, checked in that order (a
violation earlier in the order makes the later checks not yet meaningful).
Reporting only that the set is empty is non-conforming."

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
> meaningful rather than an artifact of unit choice. No framework edit is
> proposed — Core §3.9 / Spec §2.5 already require a declared metric; this
> investigation demonstrates why, with a constructed counterexample to the
> "just read the raw Jacobian" alternative.

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
