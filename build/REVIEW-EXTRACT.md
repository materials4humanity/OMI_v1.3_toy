# Review extract — OMI v1.3 reference implementation

Extraction only. Nothing in this document was fixed, tuned, or re-derived
to look better than the underlying record. Every row carries one of three
labels:

- **[RECORDED]** — exists in a committed file; path, commit SHA, line range given.
- **[RE-RUN]** — not durably recorded; executed now, command and raw output given.
- **[ABSENT]** — no record exists and none could be reconstructed; what was looked for and why it can't be rebuilt is stated.

Repository state for every [RECORDED] item below, unless a different SHA is
given inline: branch `claude/omi-m0-scaffolding-96j5cj`, HEAD `aa4e80f48809f39660d36ee4cf968117efc09927`, working tree clean at extraction time.

## Provenance census

| Label | Count |
|---|---|
| [RECORDED] | 61 |
| [RE-RUN] | 24 |
| [ABSENT] | 11 |
| **Total labelled items** | **96** |

Reading this ratio: roughly two-thirds of the specific quantities and claims
below were already sitting in a committed file at the exact number quoted
here. The remainder split between numbers that existed only as a threshold
in an assertion (not the observed value itself — a real and recurring
pattern below) and things that were never captured at all. No number in this
document was reconstructed from what the build "must have" produced; where
that was the only option, the row says [ABSENT].

---

## §1 — Open Question outcomes

### OQ-1 — Is the divergence fingerprint a probe or a contrast?

**[RECORDED]** Hypothesis, `docs/COVERAGE.md` at commit `c32b768` (the docs-seed
commit — this predates `55b764c`, the M0 code commit, and is the earliest
version of the file; there is no earlier one), lines 133–142:

> "Spec §1.6 identifies missing components by *which probe* shows divergence
> (e.g. "reversed driving only → kinematic variable"). Hypothesis: for a
> kinematic variable both forward and reversed probes diverge, and what
> discriminates is the *decomposition* of the probe response — symmetric part
> matched, antisymmetric part diverging. If true, §1.6's rows should name
> contrasts between probe responses rather than single probes, and the
> `discriminating()` requirement in §1.6 becomes checkable.
> **Test:** oracle with a known kinematic hidden variable; check whether the
> single-probe rule yields a false negative."

**[RECORDED]** What tested it: `tests/oracles/test_known_insufficiency.py`
(commit `c3e3245`), specifically `test_oq1_single_probe_direction_gives_the_same_deficit_either_way`
(lines 70–95) and `test_oq1_discriminating_signature_separates_kinematic_from_magnitude_type`
(lines 98–127), against `tests/oracles/known_insufficiency.py`'s
`KnownInsufficiencyOracle`.

**[RE-RUN]** The committed test only asserts `0.7 < ratio < 1.3` (line 95)
and two booleans (lines 126–127) — the actual observed quantities are not
recorded anywhere durable. Command: reproduced the test body's own calls
directly in a Python shell using the same seeds (`np.random.default_rng(10)`
forward, `np.random.default_rng(11)` reversed, `n_pairs=8000`). Raw output:

```
fwd deficit_squared 4.466107289695028
rev deficit_squared 4.554435479750852
ratio fwd/rev 0.9806061167298266
```

i.e. the forward-only and reversed-only deficits differ by under 2%, well
inside the committed 30%-band assertion. Separately, the constructed-gap
recovery test (`test_deficit_recovers_the_constructed_gap_for_the_incomplete_description`,
line 22, tolerance `< 0.15` relative, line 36) was re-run at seed 0:

```
deficit_squared 4.598042175613981 truth 4.5 rel_err 0.021787150136440146
```

— 2.2% relative error, against a 15% bound. And the full-state match test
(`test_deficit_is_near_zero_when_matching_on_the_full_state`, line 39,
bound `< 0.05 * truth`, line 51):

```
full-state deficit_squared 0.0 0.05*truth 0.225
```

— exactly zero, not merely under the bound.

**[RECORDED]** Proposed v1.4 wording, `docs/COVERAGE.md` lines 160–165 (current
tree, added at commit `c3e3245`):

> "rows in the divergence fingerprint table should name *contrasts between
> paired-probe responses* (e.g. "antisymmetric under forward/reversed
> reversal → kinematic variable") rather than "which single probe
> diverges" — the latter is unreliable exactly for the directional-variable
> case the table most wants to catch."

Status: answered at M4.

### OQ-2 — Is erasure completeness operator-level or component-level?

**[RECORDED]** Hypothesis, `docs/COVERAGE.md` at `c32b768`, lines 167–176:

> "Core §3.9 consequence 3 offers "mutual information between pre- and
> post-erasure states, *or* residual variance explained by upstream
> variables". Hypothesis: these answer different questions and both are
> needed — a component can lose 85% of its magnitude while the residual
> remains a deterministic function of the input, hence still assimilable.
> Further hypothesis: erasure is component-wise, so the suppression rule in
> Core §2.2 ("a deficit upstream of an erasure is not a reason to enlarge
> the state") fails for surviving components.
> **Test:** oracle with designed per-component contraction; check whether a
> single operator-level rank predicts downstream influence."

**[RECORDED]** What tested it: `tests/oracles/test_known_erasure.py`
(commit `c93aa34`), `test_oq2_naive_magnitude_heuristic_disagrees_with_recoverability`
(lines 64–102), against `tests/oracles/known_erasure.py`'s designed rank-2-of-3
diagonal Jacobian (one full-gain, one small-gain component at 0.15, one
exactly-zero-gain component).

**[RE-RUN]** The committed assertions are inequalities (`< 0.05`, `> 0.999`,
`> 0.9`, lines 93–102), not the observed values. Re-ran the test body at
seed 2:

```
naive_full 1.0 r2_full 1.0
naive_small 0.0225 r2_small 1.0
naive_erased 0.0 r2_erased 0.0
naive_small loss %% 97.75
```

— the small-gain component loses 97.75% of its variance by the naive
fraction-retained reading (`naive_small = 0.0225`), yet its recoverability
(`r2_small`) is `1.0`, identical to the untouched component's `1.0` and to
the operator-level rank's own classification. Rank check (`test_measured_rank_matches_the_designed_rank`,
line 22), re-run at seed 0:

```
measured rank 2 truth rank 2
```

**[RECORDED]** Proposed v1.4 wording, `docs/COVERAGE.md` lines 205–209
(commit `c93aa34`):

> "Erasure completeness must not be read off a component's raw magnitude or
> variance reduction: a component can lose most of its magnitude and remain
> exactly recoverable. Use mutual information or residual variance
> explained (R²) against the pre-erasure state, not the component's own
> scale."

Status: partially answered at M2.

**Deferred part, precisely.** **[RECORDED]** `docs/COVERAGE.md` lines
191–199 (commit `c93aa34`):

> "the oracle above is diagonal — each named component aligns with exactly
> one singular direction, so operator-level rank and per-component
> recoverability could not help but agree. The genuinely open case is a
> *mixing* erasure (non-diagonal Jacobian, surviving subspace spanning a
> linear combination of several named components) — there, does
> operator-level rank still predict per-component influence, or does the
> framework need a per-component projection onto the surviving subspace as
> a distinct diagnostic? Left open for M3+."

**[ABSENT]** Whether this was revisited in M3–M9: searched all nine
milestones' ADRs (`docs/DECISIONS.md`, ADR-001 through ADR-033) and every
oracle under `tests/oracles/` for a non-diagonal/mixing erasure
construction. None exists — `tests/oracles/known_erasure.py`'s
`DiagonalErasureOperator` (the name states it) is the only erasure oracle in
the repository, at every milestone through M9. This is not a record that was
lost; no such record was ever created. The deferred half of OQ-2 remains
exactly as open now as it was at M2, five milestones and seven months of
build time later (by commit dates) — nothing in M3's own machinery
(`observability.py`'s Gramian, named in the deferral text as "the natural
machinery for this") was ever pointed at it.

### OQ-3 — Competing risks in Class B

**[RECORDED]** Hypothesis, `docs/COVERAGE.md` at `c32b768`, lines 210–216
(header text only; the "Answered M6" tag was added later):

> "Spec §4.3 transfers a tail index from one defect population. With
> several populations of differing `α` and `β`, survival is `∏ₚ[1−Fₚ]^{Nₚ}`
> and no single `ξ` describes the range of interest.
> **Test:** two-population oracle; check whether a single-`ξ` fit
> misestimates the design-point exceedance probability."

**[RECORDED]** What tested it: `tests/test_classb_competing_risks.py`
(commit `8b67ec0`) — note this file is **not** under `tests/oracles/`; it
constructs its own two-population setup inline (`COMMON_POPULATION`,
`RARE_POPULATION`, lines 24–28) reusing `tests/oracles/known_tail.py`'s
`KnownTailOracle` as a component, not as its own oracle file.

**[RE-RUN]** The committed assertion (`test_oq3_a_single_pooled_tail_fit_badly_underestimates_the_design_point_risk`,
line 74) checks `true_probability / naive_probability > 100` (line 86) — a
threshold, not the observed ratio, which `docs/COVERAGE.md` separately
narrates as "observed ratio > 1000x" without citing where that number was
recorded. Re-ran the exact computation at seed 7:

```
f_common 3.2000000000000005e-09 f_rare 0.00282842712474619
true_probability 0.027958078982639467
xi_pooled 0.18943888029604758 alpha_pooled 5.2787474167775885
naive_probability 1.0765586147098993e-05
ratio true/naive 2596.9862300691675
```

The re-run ratio (2597x) is consistent with the narrated ">1000x," but the
narration itself cannot be traced to a captured run — it is very likely the
same computation reported once during development and paraphrased into
prose, but that specific run's output was never committed. The 2597x figure
above is this document's own fresh measurement, not a recovery of the
original one.

**[RECORDED]** Proposed v1.4 wording, `docs/COVERAGE.md` lines 239–246:

> "Where more than one defect population plausibly contributes to the same
> driver, each population's tail index MUST be measured and transferred
> separately (`ξ_{D,p} = β_p·ξ_{a,p}`) and combined via the competing-risks
> survival product; fitting a single pooled tail index across populations
> of differing severity is non-conforming, since the fit is dominated by
> whichever population is most numerous in the fitting window, not by
> whichever population actually governs the design point."

Status: answered at M6.

### OQ-4 — Does inverse design report *which* variance is binding?

**[RECORDED]** Hypothesis, `docs/COVERAGE.md` at `c32b768`, lines 248–253
(header text only):

> "Spec §7.3 selects within a feasible set. When the set is empty — e.g.
> aleatoric spread wider than the specification window — the useful output
> is which term made it empty: aleatoric (reduce incoming variation),
> `𝒰_adm` (apparatus limits), or trust region (surrogate not calibrated
> there).
> **Test:** oracle with an arithmetically infeasible specification."

**[RECORDED]** What tested it:
`tests/oracles/test_known_infeasible_specification.py` (commit `e43d858`),
`test_diagnose_infeasibility_recovers_the_constructed_binding_term`
(parametrised over four scenarios, lines 30–44), against
`tests/oracles/known_infeasible_specification.py`'s four constructed
scenarios (`TRUST_REGION_SCENARIO`, `CONTROL_SCENARIO`, `ALEATORIC_SCENARIO`,
`FEASIBLE_SCENARIO`).

**[RE-RUN]** This test's outcome is categorical (`diagnosed == oracle.truth()`,
an enum equality, line 44), so there is no continuous quantity to recover —
re-running reproduces only pass/fail. Command: `pytest tests/oracles/test_known_infeasible_specification.py -v`.
Output (all four parametrisations plus two non-parametrised tests):

```
tests/oracles/test_known_infeasible_specification.py::test_known_infeasible_specification_oracle_satisfies_the_protocol PASSED
tests/oracles/test_known_infeasible_specification.py::test_diagnose_infeasibility_recovers_the_constructed_binding_term[scenario0] PASSED
tests/oracles/test_known_infeasible_specification.py::test_diagnose_infeasibility_recovers_the_constructed_binding_term[scenario1] PASSED
tests/oracles/test_known_infeasible_specification.py::test_diagnose_infeasibility_recovers_the_constructed_binding_term[scenario2] PASSED
tests/oracles/test_known_infeasible_specification.py::test_diagnose_infeasibility_recovers_the_constructed_binding_term[scenario3] PASSED
tests/oracles/test_known_infeasible_specification.py::test_all_four_scenarios_are_mutually_distinct PASSED
6 passed
```

**[RECORDED]** Proposed v1.4 wording, `docs/COVERAGE.md` lines 273–278:

> "When the decision layer's feasible set is empty, an implementation MUST
> report which of trust region, apparatus admissibility (`𝒰_adm`), or
> aleatoric spread is responsible, checked in that order (a violation
> earlier in the order makes the later checks not yet meaningful).
> Reporting only that the set is empty is non-conforming."

Status: answered at M9.

### OQ-5 — Metric dependence of every reported `L`

**[RECORDED]** Hypothesis, `docs/COVERAGE.md` at `c32b768`, lines 280–285:

> "Core §3.9 and the erasure definition (`L ≪ 1`) are metric-dependent
> statements, and the state has heterogeneous units. Spec §2.5 requires a
> local spectrum rather than a global bound but does not fix the metric.
> **Test:** rescale a slot; confirm every reported `L` changes; confirm the
> aleatoric-sigma normalisation makes them comparable across slots."

**[RECORDED]** What tested it: `tests/oracles/test_metric_dependence.py`
(commit `c93aa34`), all four tests (lines 53–119), against a fixed linear
`CoupledOperator` (off-diagonal coefficient 0.01, one component's natural
scale 100x the other's, lines 19–44).

**[RE-RUN]** Every assertion in this file is an inequality against a fixed
threshold (`< 0.02`, `> 0.5`, `not np.allclose(..., rtol=0.1)`, `0.5 <
ratio < 2.0`) — none of the four tests prints or records the underlying
scaled values. Re-ran all four test bodies at their own seeds:

```
bare scaled[0,1] 0.01
metric.scale [ 1.00659679 99.94651303]
true scaled[0,1] 0.9929150827576698
spectrum_bare [1.0050125 0.9950125]
spectrum_true [1.62448434 0.61557996]
effect_from_a 1.0055353051153393 effect_from_b 1.001278787828312 ratio 0.995766914134816
```

The bare metric reads the coupling as `0.01` (negligible next to a
diagonal of `1.0`); the declared aleatoric-sigma metric reads the *same*
raw coefficient as `0.993` (as strong as the diagonal) — a ~99x change in
the reported number for an identical operator and an identical state,
solely from which metric is declared. The Lipschitz spectra differ
similarly (`[1.005, 0.995]` vs `[1.624, 0.616]`), and a one-sigma
perturbation on either component moves the readout by comparable amounts
(ratio `0.996`, not the ~100x a raw comparison would show).

**[RECORDED]** Proposed v1.4 wording: **there is none.** `docs/COVERAGE.md`
lines 305–310, verbatim:

> "This confirms ADR-002's default (aleatoric-sigma non-dimensionalisation)
> does what it is meant to: make cross-component comparison physically
> meaningful rather than an artifact of unit choice. **No framework edit is
> proposed** — Core §3.9 / Spec §2.5 already require a declared metric;
> this investigation demonstrates why, with a constructed counterexample to
> the "just read the raw Jacobian" alternative."

OQ-5 is the one open question of the five with a "Status: answered" block
but no corresponding v1.4 wording proposal — a real, stated asymmetry with
the other four, not an omission this document is filling in.

Status: answered at M2.

---

## §2 — Oracle results

**[RECORDED]** Nine oracle-construction files exist under `tests/oracles/`
(excluding `__init__.py` and the `test_*.py` files that consume them):
`known_blind_spot.py`, `known_drift.py`, `known_erasure.py`,
`known_infeasible_specification.py`, `known_insufficiency.py`,
`known_latent_trajectory.py`, `known_ranking_inversion.py`, `known_tail.py`,
`known_unreachability.py`.

| Oracle file | Truth constructed | Estimator recovered | Tolerance kind | Pass/fail/skip | COVERAGE id / Spec |
|---|---|---|---|---|---|
| `known_blind_spot.py` | A common-mode direction `(1,1,1)/√3` orthogonal to a differencing sensor by construction | The direction lies exactly in `ker(G)`; Gramian numerical rank is exactly 2, not 3 | Absolute (`< 1e-10` for the null-space action; exact-rank equality) | 4 passed (`test_known_blind_spot.py`) | S-3.1 / C-3.8 |
| `known_drift.py` | A scalar process with an exact, known change-point and ramp rate, filter's own model never includes the ramp | NIS-based drift monitor stays quiet pre-drift, trips persistently and decisively post-drift | Qualitative/ordinal (fraction flagged, `> 5x` control limit) | 3 passed (`tests/test_innovation_drift_monitor.py` — **not** under `tests/oracles/`, see note below) | S-10 (proposition SPEC, procedure PASS-C, ADR-026) |
| `known_erasure.py` | A designed rank-2-of-3 diagonal Jacobian (full/small/zero gain) | Operator-level rank (2) and per-component R² (>0.999 surviving, <0.01 erased) | Exact rank equality; relative (R²) | 4 passed (`test_known_erasure.py`) | C-3.9a; OQ-2 |
| `known_infeasible_specification.py` | Four scenarios, each engineered so exactly one of trust-region/control/aleatoric is binding | `diagnose_infeasibility` recovers the constructed `BindingTerm` in all four | Categorical/ordinal | 6 passed (`test_known_infeasible_specification.py`) | S-7.3; OQ-4 |
| `known_insufficiency.py` | A hidden variable with an exactly known sufficiency-deficit gap under an incomplete state description | Deficit recovers the constructed gap (2.2% rel. error at 8000 pairs, re-run); deficit ≈ 0 on the full state | Relative (`< 15%`); absolute (`< 5%` of truth) | 7 passed (`test_known_insufficiency.py`) | C-2.1/S-1.2; OQ-1 |
| `known_latent_trajectory.py` | A partially observed linear system with an exactly known hidden-state trajectory | Smoother posterior mean within 3σ of truth at every step; error-of-magnitude reduction vs. raw prior; direction classified `Triage.INFERRED` | Statistical (3σ interval); qualitative (order-of-magnitude); categorical | 4 passed (`test_known_latent_trajectory.py`) | C-3.8/S-10 (proposition) |
| `known_ranking_inversion.py` | Two materials with different correlation lengths/severities, engineered to swap ranking at a specific process-zone thickness | The ranking genuinely inverts (sign flip in `P_fail(A)-P_fail(B)`); driven by dimensional reduction specifically (`n_eff` check) | Ordinal (sign) | 5 passed (`test_known_ranking_inversion.py`) | S-4.4, Prop. 4.2 |
| `known_tail.py` | Four `(α, β)` Pareto/power-law pairs with an exactly known transferred tail index `ξ_D = β·ξ_a` | Hill estimator + `tail_index_transfer` recovers `ξ_D` | Relative (`< 15% + 0.02` absolute floor) | 7 passed (`test_known_tail.py`) | S-4.3, Prop. 4.1 |
| `known_unreachability.py` | A linear invariant with an exactly known achievable bound after N steps | Certificate does not fire on the boundary, fires infinitesimally beyond it; nearest-point projection verified against a 20,000-point grid search | Absolute (exact boundary check); numerical (grid-search cross-check, `+1e-3` slack) | 7 passed (`test_known_unreachability.py`) | S-7.1 |

**[RECORDED]** Full-suite confirmation: `pytest tests/oracles/ -v`, 50 items,
`50 passed in 1.03s` (fresh run at HEAD `aa4e80f`; command and full listing
captured directly above and in the raw log this session produced —
included here as **[RE-RUN]** since the 50/50 count itself is not written
into any committed file, only individually-passing tests are).

**Note on `known_drift.py`.** It is the only one of the nine oracle
constructions whose test lives outside `tests/oracles/` —
`tests/test_innovation_drift_monitor.py` is a top-level file. Every other
oracle pairs `known_X.py` with `tests/oracles/test_known_X.py`. This is
recorded, not fixed (§6).

**Addendum (post-Phase-2 circularity review, not part of the original
extract above).** The `known_ranking_inversion.py` row's "COVERAGE id / Spec"
column cites "S-4.4, Prop. 4.2" without qualification; read alongside the
"Estimator recovered" column ("driven by dimensional reduction specifically
(`n_eff` check)"), this can be misread as the oracle validating Proposition
4.2's dimensional reduction as an empirical, emergent effect. It does not:
the oracle calls `n_eff` directly with hand-supplied `ℓ_D`/`p0` constants for
two materials, samples no driver field, and never calls
`estimate_correlation_length` — it checks that `n_eff`'s own two-regime
branch arithmetic produces the predicted sign-flip, which is a legitimate
formula-correctness check, not evidence of emergence from a real
spatially-correlated field. See `docs/V1.4-EDITS.md` E-14 and
`tests/oracles/test_known_ranking_inversion.py::test_ranking_inversion_is_not_empirically_validated_as_an_emergent_effect`
(added and permanently skipped, same review).

### The inverse table — measurements with no oracle behind them

**[RE-RUN]** Derived by AST-parsing every public (non-underscore) top-level
`class`/`def` in `src/omi/*.py` and checking whether the name appears
(word-boundary match) anywhere under `tests/oracles/`. Command: a Python
script reading `src/omi/*.py` via `ast.parse` and grepping
`tests/oracles/*.py`'s concatenated source; no committed record of this
count exists, so the whole table is a fresh measurement.

```
total public API symbols across src/omi/*.py (16 modules): 124
referenced (word-boundary) anywhere in tests/oracles/*.py: 37
NOT referenced in tests/oracles/: 87 (37 classes, 50 functions)
of those 87, NOT referenced anywhere under tests/ at all (no oracle, no unit test): 35
```

The 35 with **zero test reference anywhere in the repository** (class or
function name never appears in any file under `tests/`):

```
AnalysisResult, AugmentationResult, AugmentationStep, AutomatedCheckResult,
ConstitutiveOperator, CorrelationLengthResult, DecisionResult,
DirectionDiagnostic, ErasureMeasurement, FilterResult, Grads, GramianResult,
InstantiationDeclaration, JoinDiagnostics, JoinedTailModel, LipschitzReport,
ReadoutType, RequirementStatus, SubsetSimulationResult, TrainingReport,
ValidationLadderResult, component_dict, crps_ensemble,
diagnose_blocking_term, enkf_analysis, estimate_correlation_length,
finite_difference_jacobian, join_diagnostics, join_driver_tail,
learning_error, pit_values, required_sample_size,
validate_bulk_distribution, validate_psi_by_fractography, variance_term
```

This list is **not curated for severity** — it mixes three genuinely
different situations, which a reviewer should not collapse:

1. **Result/container dataclasses whose name never appears in a test file,
   but whose instances are constructed and inspected via attribute access**
   because the *function* that returns them is tested — e.g. `GramianResult`
   (returned by the extensively-tested `compute_gramian`), `ErasureMeasurement`
   (returned by the oracle-tested `measure_erasure`), `FilterResult`/`AnalysisResult`
   (returned by the oracle-tested `run_filter`/`enkf_analysis`),
   `LipschitzReport` (returned by the tested `lipschitz_report`),
   `SubsetSimulationResult` (returned by the tested `subset_simulation`),
   `TrainingReport` (returned by the tested `train_deeponet`),
   `DecisionResult`/`RequirementStatus` similarly. These are exercised, just
   not nameably so by a mechanical grep.
2. **Functions called only internally by another tested public function** —
   `crps_ensemble`/`pit_values` (called inside the tested `calibration_report`),
   `enkf_analysis` (inside the oracle-tested `run_filter`),
   `diagnose_blocking_term`/`learning_error` (inside the tested
   `augmentation_loop` — though see §5.2 for what `learning_error` actually
   returns regardless of being invoked).
3. **Genuinely never constructed or called by anything, anywhere, including
   internally** — verified individually by direct grep (not just the
   word-boundary sweep above) for: `variance_term` (only match in the whole
   repository is its own `def`, confirmed by
   `grep -rn "variance_term(" src/ tests/`); `ValidationLadderResult`
   (never constructed — no `ValidationLadderResult(` call site anywhere,
   including inside `classb.py` itself); `ReadoutType` (declared, but
   `ReadoutType.` never appears anywhere outside its own definition — not
   even a domain readout is tagged with it, despite `readouts.py`'s own
   `ReadoutType.TYPE_0`/`TYPE_1` having concrete classes); `join_driver_tail`,
   `join_diagnostics`, `JoinDiagnostics`, `JoinedTailModel`,
   `estimate_correlation_length`, `CorrelationLengthResult`,
   `validate_bulk_distribution`, `validate_psi_by_fractography`,
   `required_sample_size`, `component_dict` — all confirmed by direct grep
   to have no call site outside their own definition anywhere in `src/` or
   `tests/`.

Category 3 is the finding that matters: **Spec §4.2's entire driver/tail
join model (`join_driver_tail`, `join_diagnostics`, both result classes),
the `ℓ_D` correlation-length estimator specifically (`estimate_correlation_length`
— as distinct from `n_eff`, which the ranking-inversion oracle does call
directly with a hand-supplied `ℓ_D`), 3 of the 4 Spec §4.6 validation-ladder
rungs, and Spec §8's power-analysis formula (`required_sample_size`) have no
test evidence of any kind** — not an oracle, not a unit test, not even a
smoke-check that they run without raising. `docs/COVERAGE.md` and
`docs/DECISIONS.md` (ADR-027) describe these as implemented, which is true
at the level of "the function exists and is well-documented" — it is not
true at the level of "this repository has ever confirmed it computes the
right number."

`finite_difference_jacobian` deserves a precise split, not a blanket
"untested": **[RE-RUN]**, confirmed by grep —

- As `EvolutionOperator`'s generic default (`operators.py` line 106): never
  exercised, because every `EvolutionOperator` subclass in the entire
  repository (both domains, all nine oracles) overrides `jacobian()` with an
  exact analytic derivative. Confirmed: `grep -rln "EvolutionOperator)" src/
  tests/` lists every subclass; every one of those files also defines its
  own `jacobian`.
- As `FunctionalReadout`'s generic default (`readouts.py` line 71): **is**
  exercised, and by a real domain — `omi_domains/contrast/readouts.py`'s
  `DendriteRisk` class (lines 39–52) defines `evaluate` but **no**
  `jacobian` override, so every call to its Jacobian anywhere (including in
  `tests/test_domain_triage.py`'s real-domain triage, §4 below) silently
  runs the finite-difference fallback, not an analytic derivative. This is
  the only Class-B readout either domain declares, and its Jacobian has
  never been analytic.

---

## §3 — Interface diff

**[RECORDED]** The seven items, extracted directly from
`src/omi_domains/flagship/interface.py` and
`src/omi_domains/contrast/interface.py` (both introduced at commit
`9c3bd72`, unmodified since):

| Item | Flagship (`flagship/interface.py:9-33`) | Contrast (`contrast/interface.py:9-36`) |
|---|---|---|
| 1. State schema | `FLAGSHIP_SCHEMA` (imported from `flagship/state.py`) | `CONTRAST_SCHEMA` (imported from `contrast/state.py`) |
| 2. Control space | "Apparatus-controlled: heating intensity and transfer speed set by the processing line. U_adm bounded by furnace and mill capacity. A control inverse (process inverse) exists (Core §4 item 2)." | "Usage-determined: the charge/discharge duty cycle is set by the service application, not an apparatus operator. U_adm is bounded by manufacturer charge/discharge limits. The control inverse here is a usage inverse (Core §5), not a process inverse." |
| 3. Erasure inventory | `("heating_and_soak",)` | `()` |
| 4. Readout catalogue | `("aggregate_hardness: Type-0/Class-A", "hardness_constitutive: Type-1")` | `("terminal_voltage: Type-0/Class-A", "dendrite_risk: Type-0/Class-B")` |
| 5. Observation suite | `("in-die force/torque sensing (Type-0 readout of z)", "coating thickness gauge")` | `("terminal current", "voltage", "surface temperature")` |
| 6. Invariants | `("mass_conservation_across_transformation", "coating_thickness_monotone_nondecreasing")` | `("charge_conservation_coulomb_counting", "sei_thickness_monotone_nondecreasing")` |
| 7. Scale structure | "Tier I only at M1 (SVE-level analytic operators); Tier II (component BVP) is an anti-goal per CLAUDE.md §9 and is not implemented." | "Three-tier recursion (electrode -> cell -> pack, Core §7.2); only the electrode/cell tier is analytically modelled at M1, pack-level aggregation is not implemented." |

**[RE-RUN]** The falsifiable check — `omi.interface.diff(FLAGSHIP_DECLARATION,
CONTRAST_DECLARATION)`, called directly (not via the committed test, whose
own assertion is only `>= 6`, line 19 of `tests/test_interface_diff.py`, not
the exact count):

```
state_schema True
control_space True
erasure_inventory True
observation_suite True
invariants True
readout_catalogue True
scale_structure True
total differing: 7 / 7
```

**All seven items differ**, not six. This needs to be read carefully rather
than simply reported as "confirmed, even more strongly than claimed." Core
§7.2's own text (`docs/OMI-v1_3-Core.md`, the "behave oppositely on six of
seven items" table) lists **seven rows that are not the same seven items**
as Core §4's interface declaration: its rows are "Erasure operators,
Observation suite, Dominant slot, Control axis, Tier structure, Class B,
Nonlocal slot ν" — a different, informal comparison Core drew up itself.
Mapped onto the seven `InstantiationDeclaration` fields: "Dominant slot" and
"Nonlocal slot ν" are both sub-attributes of item 1 (state schema) — item 1
is covered *twice* in Core's own table — and item 6 (invariants) is **not
named in Core's table at all**. So "six of seven" cannot be checked as a
clean one-to-one correspondence against the code's seven declared items in
the first place; Core's own comparison and the interface's seven items are
two different lists that happen to both have seven entries.

Separately, `omi.interface.diff()` (`src/omi/interface.py:56`) does a plain
per-field `!=` on tuples/strings (its own docstring, quoted in
`docs/DECISIONS.md` ADR-016, calls this "mechanical equality per field").
That is why `invariants` reads as "differs": the two tuples are
`("mass_conservation_across_transformation", "coating_thickness_monotone_nondecreasing")`
and `("charge_conservation_coulomb_counting", "sei_thickness_monotone_nondecreasing")`
— different strings, but **the same structural kind** in both cases (one
conservation law, one monotonicity constraint). `diff()` cannot see that
identity of kind; it only sees unequal strings. Two domains with
*identical* invariant structure but different variable names would also
register as "differs" here. The mechanical 7/7 result is real and
reproducible, but it is not by itself evidence of the deep behavioural
inversion Core §7.2 describes — a naming difference alone is sufficient to
trip every field, and the test that pins this (`test_flagship_and_contrast_differ_on_at_least_six_of_seven_items`)
would pass even if that were the only source of difference.

Items Core's own table *does* name explicitly as inverted — erasure
operators, observation suite, control axis (all confirmed `True` above,
and substantively so: `erasure_inventory` differs in kind, not just
wording — `()` vs. a populated tuple) — do differ in the deep sense, not
merely the lexical one. No item that Core's table expects to differ fails
to differ.

---

## §4 — Evidence chain per distinctive claim

| Claim | Oracle validates the estimator | Module implements it | A domain exercises it end to end |
|---|---|---|---|
| Erasure (Core §3.9) | **Present** — `tests/oracles/known_erasure.py` + `test_known_erasure.py`, designed rank-2-of-3 Jacobian, exact rank/subspace recovery (§2 table) | **Present** — `src/omi/erasure.py`: `measure_erasure`, `component_recoverability` | **Absent** — **[RE-RUN]**, confirmed by grep: `measure_erasure` and `component_recoverability` are called from exactly one place in the entire repository, `tests/oracles/test_known_erasure.py`. Flagship declares `erasure_inventory=("heating_and_soak",)` and `HEATING_AND_SOAK` is a real operator with `is_erasure=True`, but its rank/surviving-subspace has never been *measured* by the module that exists to measure such a thing — only its *effect on a perturbation* has been checked directly, step-by-step, in `tests/test_error_compounding.py`, which does not call `erasure.py` at all. |
| Observability triage, incl. observed/inferred split (Core §3.8) | **Present** — `tests/oracles/known_blind_spot.py` (kernel membership), `tests/oracles/known_latent_trajectory.py` (a real `Triage.INFERRED` direction, confirmed constructed and recovered) | **Present** — `src/omi/observability.py`: `compute_gramian`, `danger_triage`, `Triage` | **Present, with a caveat.** `tests/test_domain_triage.py` runs `danger_triage` against both real domains (commit `caf0352`) and specifically checks `dangerous_set()` on both. But it never checks for a `Triage.INFERRED` direction in either domain's own result — only the synthetic oracle has ever been confirmed to produce one. Further: contrast's target readout in that test is `DendriteRisk`, whose Jacobian (per §2's `finite_difference_jacobian` finding) is a finite-difference approximation, not analytic — so the one real-domain triage result that could in principle show an inferred direction is built on a numerically approximated sensitivity, unlike every oracle in this row. |
| Sufficiency deficit (Core §2.1–2.2) | **Present** — `tests/oracles/known_insufficiency.py` + `test_known_insufficiency.py`, constructed gap recovered at 2.2% (re-run, §1) | **Present** — `src/omi/sufficiency.py`: `sufficiency_deficit`, `augmentation_loop` | **Present for flagship only.** `tests/test_conformance_flagship.py`'s `_matched_pair_sufficiency_campaign` (commit `61a5502`) builds a real matched-pair campaign on flagship's actual chain and `AggregateHardness` readout and calls `sufficiency_deficit` on it directly. **[RECORDED]**, `tests/test_conformance_contrast.py`'s own module docstring (lines 4–12) states plainly that no equivalent campaign was built for contrast, as a stated scope decision — this is the one gap in this row that is already self-documented in the codebase, not newly found here. |
| Class B tails and volume scaling (Core §3.6) | **Present** — `tests/oracles/known_tail.py` (tail transfer, §2 table) and `tests/oracles/known_ranking_inversion.py` (dimensional reduction / volume scaling) | **Present** — `src/omi/classb.py`: `tail_index_transfer`, `estimate_tail_index_hill`, `n_eff`, `validate_volume_scaling_exponent` | **Split.** Volume scaling: **present** — `tests/test_conformance_omi2_refusal.py` (commit `e43d858`) calls `validate_volume_scaling_exponent` against contrast's real `DendriteRisk` readout via `readout.weakest_link(...)` on an actual rolled-out ensemble. Tail transfer: **absent** — `tail_index_transfer`/`estimate_tail_index_hill` are called only against `KnownTailOracle`'s synthetic descriptors, never against any domain's own (nonexistent, in this toy) defect-population data; neither domain declares a measured defect population at all. |

The pattern across all four rows is the same shape: the estimator is
genuinely validated (oracle column is uniformly strong), and the module
genuinely exists (uniformly strong). The third column is where the record
runs out — never uniformly, but partially in every single row, and for
erasure specifically, completely.

---

## §5 — Targeted questions

**1. Does the flagship domain declare any Class B readouts under interface item 4?**

**[RECORDED]** No. `src/omi_domains/flagship/interface.py:17-20`:

```
readout_catalogue=(
    "aggregate_hardness: Type-0/Class-A",
    "hardness_constitutive: Type-1",
),
```

Two entries, both Class A or Type-1; zero Class-B, zero Type-2.

**[RECORDED]** Core §7.1's own table (`docs/OMI-v1_3-Core.md`, §7.1) lists
four "commercially decisive responses," of which it says "three... are
Type-2 performances; two are Class B": Hardness/tensile (Type-0, Class A),
**Bend angle (Type-2, Class B)**, Crash intrusion (Type-2), **Adhesion /
environmental cracking (Type-2, Class B)**. Neither Class-B entry the
framework's own worked example names is present in the code's declaration.

**[RECORDED]** What the declaration says instead: only item 7 (scale
structure) mentions the gap, and only in general terms —
`flagship/interface.py:29-32`: "Tier I only at M1 (SVE-level analytic
operators); Tier II (component BVP) is an anti-goal per CLAUDE.md §9 and is
not implemented." Nothing adjacent to item 4 itself (the readout catalogue)
states that Type-2/Class-B readouts are being omitted, or why — a reader of
item 4 alone would not learn that anything is missing; the explanation is
recoverable only by cross-referencing item 7's note with `CLAUDE.md` §9's
anti-goals list and ADR-014 (`docs/DECISIONS.md`, "Type-2 is declared in the
enum... but has no concrete base class here — it requires Tier II, an
anti-goal").

**2. Does `learning_error()` return a non-zero value for any input, after M8?**

**[RECORDED]** No, and it cannot: it takes no parameters at all.
`src/omi/sufficiency.py:83-94`:

```python
def learning_error() -> float:
    """...
    Every module through M7 (ADR-001, docs/DECISIONS.md) uses exact
    analytic operators, which are not fit to any data budget and therefore
    have no learning error by construction — this is the *correct* value
    for this instantiation, ``0.0``, not a placeholder standing in for a
    future estimate. Replaced by a genuine measurement once M8 introduces
    learned operators behind the same protocol.
    """
    return 0.0
```

The code path: called at `sufficiency.py:244`, inside `augmentation_loop`,
as `delta_learning = learning_error() - learning_error()` — always `0.0 -
0.0`. There is no branch anywhere that checks whether a chain contains a
`DeepONetOperator` (`src/omi/learning.py`, introduced at M8, commit
`2b7a3f0`) versus an analytic one. The docstring's own forward reference
("Replaced by a genuine measurement once M8 introduces learned operators")
was not fulfilled when M8 landed — `sufficiency.py` was not touched in
commit `2b7a3f0` at all (**[RE-RUN]**, confirmed: `git show --stat 2b7a3f0`
lists nine files, none of them `sufficiency.py`). The function reads
exactly as it did when ADR-023 wrote it at M4.

**3. What happens when `measure_closure_defect` is called — quote the code, and say whether anything in the test suite calls it?**

**[RECORDED]** `src/omi/conformance.py:158-172`:

```python
def measure_closure_defect(*_args: object, **_kwargs: object) -> float:
    """Refuses: Spec §6's closure-defect *measurement procedure* is `[Pass
    C]` in its entirety (docs/COVERAGE.md row S-6) — only the definition
    (Core §3.7) is specified, not how to estimate ``‖𝒟_λ‖`` from a chain.
    ...
    """
    raise NotSpecified(
        "S-6",
        "Spec §6",
        "the closure-defect measurement procedure has no derivation in the "
        "Specification; only the definition (Core §3.7) is given",
    )
```

It always raises. **[RECORDED]** Yes, one call site in the whole test
suite: `tests/test_conformance.py:82-83`, inside
`test_claiming_a_conformance_not_met_error_is_distinct_from_not_specified`:

```python
    with pytest.raises(NotSpecified):
        measure_closure_defect()
```

That is the entire extent of its exercise: confirming it raises the
expected exception, called with no arguments. It has never been invoked as
part of an actual conformance-report generation for either domain — both
domains declare `scale_bridging_occurs=False` (the default), so the
refusal's own guard condition is never even reached in either's real
report.

**4. Is there a committed test that asserts the two domains' interfaces differ on six of seven items?**

**[RECORDED]** Yes: `tests/test_interface_diff.py`, introduced at commit
`9c3bd72`. `test_flagship_and_contrast_differ_on_at_least_six_of_seven_items`
(lines 15–19):

```python
def test_flagship_and_contrast_differ_on_at_least_six_of_seven_items() -> None:
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    assert len(result) == 7
    differing = sum(result.values())
    assert differing >= 6, f"only {differing}/7 items differ: {result}"
```

Note the assertion is `>= 6`, a lower bound — it passes at 6 and would also
pass at 7 (which, per §3 above, is what actually happens). It does not
assert exactly 6, and does not fail on the "all seven differ merely by
naming" scenario described in §3.

**5. How many of `classb.py`'s public functions are called from anywhere under `src/omi_domains/`? List them, and list those called only from tests.**

**[RE-RUN]** Zero. Command: word-boundary grep of all 16 public
`classb.py` symbols against every file under `src/omi_domains/`. None
matched. `classb.py` is never imported by either domain's own source.

Called only from tests (i.e., reachable at all, but exclusively through
`tests/`, per the per-symbol check in §2): `tail_index_transfer`,
`estimate_tail_index_hill`, `n_eff`, `subset_simulation`,
`competing_risk_survival`, `validate_volume_scaling_exponent` — six of
sixteen. (`n_eff` is called by `tests/oracles/known_ranking_inversion.py`
and `tests/oracles/test_known_ranking_inversion.py` with a hand-supplied
`ℓ_D`, never by `estimate_correlation_length`, which nothing calls at all —
see §2.) The remaining ten (`JoinDiagnostics`, `JoinedTailModel`,
`join_driver_tail`, `join_diagnostics`, `CorrelationLengthResult`,
`estimate_correlation_length`, `SubsetSimulationResult`,
`ValidationLadderResult`, `validate_bulk_distribution`,
`validate_psi_by_fractography`) are called from nowhere at all — not tests,
not domains, not other parts of `classb.py` itself.

---

## §6 — Anything noticed and not fixed

- `omi.interface.diff()` reports the flagship/contrast interfaces differ on
  7/7 items, not the 6/7 Core §7.2 narrates — not because the code is wrong,
  but because Core's own "six of seven" table is a different seven-item
  list than the interface's seven declared items (§3), and `diff()`'s
  literal string inequality will register "differs" on `invariants` for two
  domains that are structurally identical in that field's *kind*.
- `learning_error()` takes zero parameters and cannot be told whether a
  learned operator is present; its own docstring promises replacement "once
  M8 introduces learned operators," and M8 shipped without that replacement
  — `sufficiency.py` was not touched in the M8 commit.
- `measure_closure_defect` is exercised by exactly one test, solely to
  confirm the exception type, never as part of a real conformance report.
- `omi.erasure.measure_erasure`/`component_recoverability` — the actual
  erasure-measurement machinery — have never been run against either
  domain's own declared erasure operator; only the synthetic oracle has
  been measured.
- `Triage.INFERRED` has never been confirmed to occur in a real domain's
  triage result; `tests/test_domain_triage.py` runs `danger_triage` on both
  domains but checks only `dangerous_set()`.
- Contrast's only Class-B readout, `DendriteRisk`, has no analytic
  `jacobian()` override and silently relies on the generic finite-difference
  fallback — the one real-domain sensitivity computation in this row is
  numerically approximate, unlike every oracle that exercises the same
  machinery.
- Ten of `classb.py`'s sixteen public symbols — including the entirety of
  Spec §4.2's driver/tail join model and three of four Spec §4.6
  validation-ladder rungs — have no test reference anywhere in the
  repository.
- `required_sample_size` (Spec §8's power-analysis formula) has zero test
  coverage of any kind.
- `ReadoutType`, the Type-0/1/2 enum, is never referenced by name anywhere
  outside its own definition — not by a domain, not by a test — despite
  Type-0 and Type-1 both having concrete implementing classes.
- `ValidationLadderResult` is declared but never constructed anywhere,
  including inside `classb.py` itself.
- OQ-2's deferred half (mixing/non-diagonal erasure) has had no oracle built
  against it in the five milestones since it was deferred at M2; the only
  erasure oracle in the repository remains diagonal by name and by
  construction.
- OQ-5 is the only one of the five open questions marked "answered" with no
  corresponding proposed v1.4 wording — the record explicitly states none
  is proposed, which is a real asymmetry with OQ-1/2/3/4, not an inconsistency
  introduced here.
- `known_drift.py` is the only oracle construction under `tests/oracles/`
  whose corresponding test lives outside that directory
  (`tests/test_innovation_drift_monitor.py`), breaking the naming/location
  pairing every other oracle in the suite follows.
- Neither domain has a conformance demonstration wiring a real reachability
  certificate or prospective inverse-design trial into a
  `ConformanceInputs`, even though `inverse.py` (M9) now provides the
  machinery — OMI-2 remains unclaimed for both domains for this reason,
  already flagged at the end of the M9 report and unchanged since.
- `docs/COVERAGE.md`'s OQ-3 narration ("observed ratio > 1000x") cites a
  specific quantity with no traceable committed run behind it; this
  document's own re-run (2597x) is consistent with it but is a fresh
  measurement, not a recovery of whatever run originally produced the
  "1000x" figure.
