# Review extract — OMI v1.3 reference implementation

Extraction only. Nothing in this document was fixed, tuned, or re-derived
to look better than the underlying record. Every row carries one of three
labels:

- **[RECORDED]** — exists in a committed file; path, commit SHA, line range given.
- **[RE-RUN]** — not durably recorded; executed now, command and raw output given.
- **[ABSENT]** — no record exists and none could be reconstructed; what was looked for and why it can't be rebuilt is stated.

Repository state for every [RECORDED] item below, unless a different SHA is
given inline: branch `claude/omi-m0-scaffolding-96j5cj`, HEAD
`bbe279f4c36042aeec15b05e3d9f5af284468947`, working tree clean at extraction
time.

**This is a regeneration** (docs/ROADMAP.md Phase 3 gate), not a first
extraction — the previous version (HEAD `aa4e80f`) is superseded by this
file, not corrected in place (CLAUDE.md §10's snapshot rule: this document
itself stamps a commit and is therefore a snapshot; the *previous* snapshot
is not edited, this is a new one). Sections unaffected by Phase 2/3 work are
noted as carried forward rather than re-derived from first principles a
second time; sections that changed are re-verified fresh.

## Provenance census

| Label | Count (this extraction, HEAD `bbe279f`) | Count (previous, HEAD `aa4e80f`) | Δ |
|---|---|---|---|
| [RECORDED] | 58 | 61 | −3 |
| [RE-RUN] | 30 | 24 | +6 |
| [ABSENT] | 7 | 11 | −4 |
| **Total labelled items** | **95** | **96** | −1 |

Reading the delta: [ABSENT] dropped by 4 — four things that had "no record
exists" at the previous extraction now have one, because Phase 3 built the
missing capability rather than merely re-noting its absence (OQ-2's
deferred half; `learning_error`'s chain-awareness; `measure_erasure`/
`component_recoverability` run against a real domain; `DendriteRisk`'s
analytic Jacobian). [RE-RUN] rose because several of the *new* claims in
this extraction are themselves freshly-computed numbers with no committed
record of the specific figure (matching the previous document's own
pattern: assertions are inequalities, not the observed value). [RECORDED]
fell slightly because a few previously-[RECORDED] facts about *absence*
(e.g. "erasure.py's functions are called from exactly one place") are no
longer true and so no longer appear as recorded facts — they are replaced
by new [RE-RUN]/[RECORDED] entries about presence instead. The total item
count is roughly flat (~95 vs ~96): this is not a document that grew by
padding, it replaced stale findings with current ones at close to 1:1.

---

## §1 — Open Question outcomes

OQ-1, OQ-3, OQ-4, OQ-5: **unchanged since the previous extraction** — no
code or documentation touching these four was modified in Phase 2 or
Phase 3. Carried forward without re-verification; see HEAD `aa4e80f`'s
extraction (this repository's git history) for their full [RECORDED]/
[RE-RUN] evidence, which remains accurate since nothing it cites has
changed. Re-confirmed only that their status lines in `docs/DECISIONS.md`'s
Open Questions table are unchanged: **[RECORDED]**, `docs/DECISIONS.md`
lines 2113, 2115–2117 (current tree) — OQ-1/3/4/5 still read "answered", no
edit.

### OQ-2 — Is erasure completeness operator-level or component-level? Now fully answered.

**[RECORDED]** `docs/DECISIONS.md` line 2114 (current tree): `"OQ-2 |
Erasure completeness: operator-level or component-level? | M2, deferred
half at Phase 3.4 | answered — see COVERAGE.md Part IV"` — changed from
"partially answered" at the previous extraction.

**[RECORDED]** The deferred half (non-diagonal/mixing erasure) — open at
M2, still open through M9, still open through Phase 2 — was closed at
Phase 3.4. `tests/oracles/known_mixing_erasure.py` (this session): a
symmetric rank-2 Jacobian over three named components, built from three
mutually orthogonal directions verified orthonormal in
`MixingErasureOperator.__post_init__` (not merely asserted), none
axis-aligned — `(1,1,1)/√3` and `(1,-1,0)/√2` at singular values `1.0` and
`0.6`, `(1,1,-2)/√6` at exactly `0.0`.

**[RE-RUN]** Re-ran `tests/oracles/test_known_mixing_erasure.py` directly:

```
rank: 2
component_a: R^2=0.7847  surviving_overlap=0.8303
component_b: R^2=0.7606  surviving_overlap=0.8264
component_c: R^2=0.3280  surviving_overlap=0.3433
```

Operator-level rank (`2`) is a single integer; it cannot distinguish
`component_c`'s substantially lower recoverability from `component_a`/
`component_b`'s. `component_recoverability`'s R² and the new
`component_surviving_overlap`'s exact geometric projection agree in
*ordering* but not in *value* (a ~5-percentage-point gap for `a`/`b`) —
related, not interchangeable, diagnostics. **[RECORDED]** New function:
`src/omi/erasure.py` (`component_surviving_overlap`, added this session).

**[RECORDED]** Proposed v1.4 wording for the mixing-erasure half:
`docs/V1.4-EDITS.md` E-18 (new this session): "Where the erasure is not
diagonal in the declared component basis..., an implementation MUST supply
a per-component diagnostic... before reporting which named components
survive."

Status: **answered in full** (was: partially answered, deferred half open
since M2).

---

## §2 — Oracle results

**[RECORDED]** Ten oracle-construction files now exist under
`tests/oracles/` (was nine): the previous nine plus
`known_mixing_erasure.py` (Phase 3.4).

| Oracle file | Change since previous extraction |
|---|---|
| `known_blind_spot.py`, `known_erasure.py`, `known_infeasible_specification.py`, `known_insufficiency.py`, `known_latent_trajectory.py`, `known_unreachability.py`, `known_tail.py` | Unchanged. |
| `known_drift.py` | Its test (`tests/test_innovation_drift_monitor.py`) is **moved** to `tests/oracles/test_known_drift.py` (Phase 3.4) — the naming/location mismatch the previous extraction's §6 flagged is fixed, not merely re-noted. |
| `known_ranking_inversion.py` | Unchanged in construction; its module docstring and test file gained disclaiming language and a new permanently-skipped test after the circularity review between the two extractions (`docs/V1.4-EDITS.md` E-14) — not a Phase 3 change, carried from the intervening session. |
| `known_mixing_erasure.py` | **New** (Phase 3.4), see §1. |

**[RE-RUN]** Full-suite confirmation: `pytest tests/oracles/ -q`:

```
........................................s..................
58 passed, 1 skipped in 1.48s
```

(59 items total, up from 50 at the previous extraction; the one skip is
`tests/oracles/test_known_ranking_inversion.py`'s permanently-skipped
emergence test, predating this regeneration.)

**[RE-RUN]** The inverse table (public `src/omi/*.py` symbols with zero
test reference anywhere), re-derived by the same AST/grep method as the
previous extraction:

```
total public API symbols across src/omi/*.py: 129 (was 124)
NOT referenced in tests/oracles/: 89 (was 87)
of those, NOT referenced anywhere under tests/ at all: 32 (was 35)
```

Five symbols left the zero-reference list since the previous extraction:
`learning_error` (now called with a `Chain` argument and tested directly,
`tests/test_sufficiency_learning_error.py`, ADR-036), `ReadoutType` (now a
class attribute on every readout base and tested, ADR-035), `join_driver_tail`
(called from `src/omi_domains/flagship/classb_bend.py`'s production code,
domain-exercised via `tests/test_flagship_classb_bend.py` even though not
imported by name in that test file — the same "exercised, not nameably so"
pattern the previous extraction already distinguished for result
dataclasses), `estimate_correlation_length` (same), `finite_difference_jacobian`
(now imported by name in `tests/test_readouts.py`'s new Jacobian-verification
test, Phase 3.3(a)). Two symbols are new to the list: `InvariantKind`,
`classify_invariant` (ADR-034's structural interface-diff check, added
between the two extractions — exercised via `interface.diff()`'s own test
but not named directly in it, the same "container exercised without being
named" category as before).

**[RE-RUN]** `classb.py`'s domain-call count, re-derived: **13 of 16**
public symbols now called from `src/omi_domains/` (was 0 at the previous
extraction, before Phase 2 existed):

```
tail_index_transfer, estimate_tail_index_hill, JoinDiagnostics,
JoinedTailModel, join_driver_tail, join_diagnostics,
CorrelationLengthResult, estimate_correlation_length, n_eff,
ValidationLadderResult, validate_bulk_distribution,
validate_psi_by_fractography, validate_volume_scaling_exponent
```

Still not called from any domain: `subset_simulation`,
`competing_risk_survival`, `SubsetSimulationResult` (already documented in
`docs/COVERAGE.md`'s C-3.6 row as the three genuinely still-dead symbols).

`finite_difference_jacobian`'s split (previous extraction distinguished
"generic `EvolutionOperator` default: never exercised" from "generic
`FunctionalReadout` default: exercised only by `DendriteRisk`, whose
Jacobian was therefore always approximate") is **now different**:
`DendriteRisk` gained an exact analytic Jacobian at Phase 3.3(a)
(`src/omi_domains/contrast/readouts.py`) — it no longer falls back to
finite differences at all. The fallback is now exercised instead by
`BendAngleAtReferenceGeometry` (ADR-037, Phase 3.3(b)), a *new* readout
this regeneration introduces, which has no analytic derivative derived for
its geometry-fixed quadrature composition and says so in its own
docstring. The finding is not eliminated, it moved: exactly one real-domain
readout's Jacobian is still a finite-difference estimate, and it is a
different one than before.

---

## §3 — Interface diff

**[RECORDED]** Six of the seven items are **unchanged** since the previous
extraction. Item 4 (readout catalogue) changed for flagship:
`src/omi_domains/flagship/interface.py` (current tree) now reads:

```
readout_catalogue=(
    "aggregate_hardness: Type-0/Class-A",
    "hardness_constitutive: Type-1",
    "bend_angle: Type-2/Class-B — driver field ..., defect population "
    "inclusion_content ..., physics map Psi ...",
),
```

Three entries, not two — `bend_angle` (Phase 2.2, ADR-035) fills item 4b
for the first time in this repository (driver field, defect population,
physics map Ψ, all declared per Core §4). Contrast's item 4 is unchanged
(`dendrite_risk` still declares no 4b content).

**[RE-RUN]** `omi.interface.diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)`,
re-run directly:

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

Unchanged from the previous extraction (still 7/7, still for the same
reason: Core §7.2's own "six of seven" table names a different seven-item
list than the interface's own seven fields — ADR-034, already recorded,
not a new finding this regeneration).

---

## §4 — Evidence chain per distinctive claim

| Claim | Change since previous extraction |
|---|---|
| Erasure (Core §3.9) | **Domain column changed from Absent to Present.** `tests/test_flagship_real_erasure.py` (Phase 3.1) runs `measure_erasure`/`component_recoverability` against `HEATING_AND_SOAK` for the first time. Finding: `measure_erasure` reports full rank (7/7) at ADR-017's default tolerance (`HEATING_AND_SOAK`'s decay is finite, `exp(-5)≈0.0067`, never exactly zero) — the erasure is visible only in the spectrum, not the rank statistic; `component_recoverability` cannot see it at all (R²≈1.0 regardless of magnitude lost, the same blindness the M2 oracle already demonstrated, now shown on a real domain). Also new: the mixing-erasure oracle (§1) and `component_surviving_overlap`. |
| Observability triage (Core §3.8) | **Domain column's caveat changed, not resolved.** `tests/test_domain_triage.py` (Phase 3.3) now asserts the *full* `Triage` classification, not only `dangerous_set()`. Finding: at `time_index=0` (both domains' query convention), only `INFERRED`/`DANGEROUS` are reachable — `OBSERVED` needs a near-diagonal sensor (none exists at k=0 in either domain) and `OBSERVED_BUT_IRRELEVANT`/`MARGINALISABLE` need sub-median influence (impossible once `influence_median == 0.0`, true for both domains). `Triage.INFERRED` does appear on both, contrast's with ~zero danger score. `DendriteRisk`'s Jacobian is now analytic (Phase 3.3(a)), so contrast's triage sensitivity is no longer a finite-difference approximation — but the previous extraction's *caveat* (approximate sensitivity) is replaced by a *different* one (only half the triage table is reachable at this query point), not removed outright. |
| Sufficiency deficit (Core §2.1–2.2) | Unchanged. Contrast still has no matched-pair campaign (self-documented scope decision, unchanged). |
| Class B tails and volume scaling (Core §3.6) | Unchanged since the intervening (non-Phase-3) session's Phase 2 work, which is itself unchanged by Phase 3: `join_driver_tail`/`estimate_correlation_length` etc. are now domain-exercised (see §2's classb.py count), tail transfer is exercised on flagship's real driver field (`classb_bend.py`), not only the synthetic oracle. |

---

## §5 — Targeted questions

**1. Does the flagship domain declare any Class B readouts under interface item 4? *(Answer changed.)***

**[RECORDED]** **Yes, now.** `src/omi_domains/flagship/interface.py`
(current tree): `bend_angle: Type-2/Class-B` is declared, filling item 4b
(driver field, defect population, physics map Ψ) — this was the previous
extraction's headline finding (Core §7.1's own worked example names two
Class-B readouts the code declared zero of); Phase 2 (predating both Phase
3 and this regeneration, but postdating the previous extraction) closed it
for one of the two (`bend_angle`; `Adhesion/environmental cracking` remains
undeclared).

**2. Does `learning_error()` return a non-zero value for any input, after M8? *(Answer changed.)***

**[RECORDED]** **It now takes an argument and can refuse, though it still
never returns nonzero.** `src/omi/sufficiency.py` (current tree,
ADR-036): `learning_error(chain: Chain) -> float` — `0.0` for a purely
analytic chain (unchanged value, now an intentional branch rather than
the only possible outcome), `NotSpecified` citing `"S-1.4"` when the chain
contains a `DeepONetOperator`. **[RE-RUN]**,
`tests/test_sufficiency_learning_error.py`:

```
test_learning_error_is_zero_for_a_purely_analytic_chain PASSED
test_learning_error_refuses_citing_s_1_4_when_the_chain_has_a_learned_operator PASSED
test_learning_error_refuses_even_when_the_learned_operator_is_not_the_first_segment PASSED
```

A deeper, new finding surfaced fixing this (`docs/V1.4-EDITS.md` E-16,
updated): `augmentation_loop` (`src/omi/sufficiency.py`) operates entirely
on `StateSchema`, with no `Chain` available at all — its own
`delta_learning` term is hard-coded `0.0` regardless of `learning_error`'s
own fix, so `BlockingTerm.LEARNING` can never be produced by the
augmentation loop as currently designed. Core §6.1 criterion 5 (state-
selection has no interior optimum) remains blocked, now for this precisely
identified reason instead of the originally-named stub.

**3. What happens when `measure_closure_defect` is called?**

**[RECORDED]** **Unchanged.** Still an unconditional `NotSpecified`
(`src/omi/conformance.py`), still exercised by exactly one test confirming
only the exception type.

**4. Is there a committed test that asserts the two domains' interfaces differ on six of seven items?**

**[RECORDED]** Unchanged (`tests/test_interface_diff.py`, `>= 6` lower
bound, still passes at the actual `7`).

**5. How many of `classb.py`'s public functions are called from anywhere under `src/omi_domains/`? *(Answer changed.)***

**[RE-RUN]** **13 of 16, not 0.** See §2's re-derivation. This is Phase 2's
change (predating this regeneration but postdating the previous
extraction) — restated here because it is the single largest change to
this question's answer between the two extractions.

**6. (New question this regeneration.) Does `conformance.py`'s OMI-2 reachability-certificate check still accept an arbitrary label instead of inspecting a real artefact?**

**[RECORDED]** **No, fixed.** `src/omi/conformance.py` (current tree):
`ConformanceInputs.reachability_certificates` is now typed
`tuple[ReachabilityCertificate, ...] | None` (was `tuple[str, ...] | None`
at the previous extraction — `docs/V1.4-EDITS.md` E-17). No existing test
constructs this field with a non-`None` value in either state, so no
conformance level claimed by any current test changed; the fix closes the
loophole structurally, ahead of the first domain that actually supplies a
certificate.

---

## §6 — Anything noticed and not fixed

Items from the previous extraction, resolved between the two extractions
(not repeated here as open — moved to the closed list):

- ~~`learning_error()` takes zero parameters~~ — **fixed** (§5.2, ADR-036).
- ~~`measure_erasure`/`component_recoverability` never run against a real domain~~ — **fixed** (§4, Phase 3.1).
- ~~`Triage.INFERRED` never confirmed on a real domain~~ — **checked and reported** (§4, Phase 3.3(c)): it does appear, on both domains, but the full classification is only half-reachable at the query point used — see §4's entry; not a clean "fixed," a plain finding.
- ~~`DendriteRisk` has no analytic `jacobian()`~~ — **fixed** (§2, Phase 3.3(a)) — but see §2's note: the finite-difference fallback is now exercised by a *different* readout (`BendAngleAtReferenceGeometry`) instead.
- ~~OQ-2's deferred half has no oracle~~ — **fixed** (§1, Phase 3.4).
- ~~`known_drift.py`'s test breaks the naming/location pairing~~ — **fixed** (§2, Phase 3.4: moved and renamed).
- ~~Flagship declares no Class-B readout~~ — **fixed** (§5.1, Phase 2, predates this regeneration).
- ~~Zero of `classb.py`'s symbols called from domains~~ — **fixed** (§5.5, Phase 2).

Items still open, unchanged:

- `omi.interface.diff()` still reports 7/7, still for the same
  already-understood reason (§3).
- `measure_closure_defect` is still exercised only to confirm its
  exception type, never in a real conformance report.
- `required_sample_size` still has zero test coverage of any kind
  (confirmed still absent from the referenced-symbol list, §2).
- `ValidationLadderResult` is now constructed (Phase 2, flagship's Class B
  campaign) — **this one also moved from open to fixed** and should have
  been listed above; noted here to be explicit that the previous
  extraction's specific claim ("declared but never constructed anywhere")
  is no longer true.
- OQ-5 remains the only open question marked answered with no proposed
  v1.4 wording (unchanged; still a stated asymmetry, not an omission).
- Neither domain has a conformance demonstration wiring a real
  reachability certificate or prospective inverse-design trial into
  `ConformanceInputs` — unchanged; OMI-2 remains unclaimed for both
  domains for this reason. (`conformance.py`'s field is now correctly
  *typed* for this, §5.6 — typing readiness is not the same as a domain
  actually supplying one, and no domain does.)
- `docs/COVERAGE.md`'s OQ-3 narration ("observed ratio > 1000x") still has
  no traceable committed run behind the specific figure — unchanged, not
  touched by Phase 2 or 3.

New findings, this regeneration only:

- Reading the spectrum, not the rank statistic, is where `HEATING_AND_SOAK`'s
  declared erasure is actually visible — the numerical-rank tolerance
  (ADR-017) is calibrated for exact (or near-machine-epsilon) singular
  values, and a real, finite-rate decay operator's "erasure" is neither.
  This is the first time the rank statistic has been checked against a
  non-exact-zero erasure in this repository, and it does not detect it
  numerically at the default tolerance (by design, not by bug — ADR-017
  keeps the full spectrum precisely so this case stays inspectable).
- Only two of Spec §3.3's four triage categories are reachable at all on
  either domain's own triage-query convention (`time_index=0`, sensors
  placed strictly downstream) — `OBSERVED` needs a near-diagonal sensor
  that does not exist there in either domain, and
  `OBSERVED_BUT_IRRELEVANT`/`MARGINALISABLE` need sub-median influence,
  impossible once the influence median lands at exactly zero (true for
  both domains' low-dimensional target sets). ADR-020 already named this
  risk as a possibility; this regeneration is the first time it was
  checked against real domain data and confirmed to occur.
- Adding `bend_angle` to flagship's triage target set (Spec §3.3's own
  re-run requirement) does not reorder the dangerous set, because
  `BendAngleAtReferenceGeometry`'s Jacobian is numerically near-identical
  to `AggregateHardness`'s (both are functionals of the same constitutive
  operator, whose state-dependence does not vary with the applied
  control) — target declaration would be load-bearing with a genuinely
  differently-sensitive second target; this domain's actual two targets
  are not that.
- `augmentation_loop`'s `delta_learning` term is structurally always
  `0.0` (no `Chain` reaches it), independent of and unresolved by
  `learning_error`'s own fix — `BlockingTerm.LEARNING` can never be
  produced by this repository's augmentation loop as it is currently
  designed, which is new information for Core §6.1 criterion 5's status
  (`docs/V1.4-EDITS.md` E-16).
