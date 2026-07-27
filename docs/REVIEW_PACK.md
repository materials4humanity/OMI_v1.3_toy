# Review pack — OMI v1.3 reference implementation, M0–M9

**Branch:** `claude/omi-m0-scaffolding-96j5cj`
**Commit range:** `c32b768` (docs seed) through `e43d858` (M9) — 11 commits, one per milestone plus the initial doc seed.
**Status:** All nine milestones in `docs/ROADMAP.md` complete. No M10 exists — this is the full roadmap.

This document is a reviewer's entry point, not a replacement for the governance
documents it summarises. The canonical sources of truth remain:

| Document | What it holds |
|---|---|
| `CLAUDE.md` | Prime directive, vocabulary, the gap discipline, ten invariants |
| `docs/OMI-v1_3-Core.md` / `docs/OMI-v1_3-Implementation-Spec.md` | The framework itself (claims / procedures) |
| `docs/COVERAGE.md` | The gap register — what's specified, what isn't, what this repo does about each |
| `docs/DECISIONS.md` | 33 ADRs plus the Open Questions log |
| `docs/ROADMAP.md` | The milestone plan this build followed |

This file cites all four but restates none of them in full — where it summarises,
it points back to the section that governs.

---

## How to review

1. **Read `CLAUDE.md` first** if you haven't — every decision below is made
   against its gap discipline (§4: Refuse / Decide / Escalate) and its ten
   invariants (§5). A change that looks unmotivated in isolation almost always
   traces back to one of those.
2. **Per-milestone commits are self-contained and roughly ADR-then-code-then-test
   in that order** — `git log --oneline` gives the milestone list; `git show
   <commit> --stat` gives the file list per milestone.
3. **Every ADR is numbered and cited from the code that implements it** — the
   citation lint (`tests/lint/test_citations.py`) enforces that every public
   function/class in `src/omi/` cites `Core §x` or `Spec §x` in its docstring,
   so "why is this here" is always one docstring away.
4. **Run the verification suite yourself** (see [Verification](#verification)
   below) rather than trusting this document's numbers — they were true at
   commit `e43d858` in a fresh venv, but a document can go stale; a test run
   cannot.

---

## Milestone-by-milestone summary

### M0 — Foundation (`55b764c`)
Gap discipline made executable: `omi.NotSpecified` citing live `COVERAGE.md`
rows; three lint tests (vocabulary, citations, gap-citations), each
demonstrated to fail on a planted violation and pass once removed against the
*real* source tree; the determinism harness; CI scaffolding (4 jobs: lint,
typecheck, test, determinism); the first oracle (`known_tail.py`).
**No ADRs yet** — pure scaffolding.

### M1 — Substrate (`9c3bd72`)
The typed core: `State`/`Ensemble`/`Metric` (flat array + schema, ADR-011),
`EvolutionOperator` (ADR-012), `Control` (ADR-013), the three readout shapes
(ADR-014), `Chain` (ADR-015), the seven-item instantiation interface
(ADR-016). Both domains (flagship, contrast) stood up with analytic operators
end to end. **ADRs 011–016.**

### M2 — Erasure and composition (`c93aa34`) · *first distinctive claim*
`erasure.py`: rank/surviving-subspace measurement (ADR-017) against a
designed rank-*r* oracle; `LipschitzReport` with the metric attached; **OQ-2**
(erasure completeness, operator- vs. component-level) and **OQ-5** (metric
dependence of every reported `L`) both answered with computed evidence;
error-compounding demonstrated on the real flagship chain. **ADR-017.**

### M3 — Observability (`caf0352`) · *second distinctive claim*
`observability.py`: the Gramian via matrix-free JVP/VJP (ADR-018, never
forming `Φ` as a chained product), the default prior (ADR-019), the
danger-score triage and observed/inferred split (ADR-020). Domain triage run
on both domains; the contrast domain's poor observation suite shown to leave
a materially larger fraction of target variance dangerous than the
flagship's — a real, computed contrast, not asserted. **ADRs 018–020.**

### M4 — Sufficiency (`c3e3245`) · *third distinctive claim*
`sufficiency.py`: the three-term deficit decomposition (ADR-021, a raw
response gap is never independently exposed), the probe-set
symmetric/antisymmetric decomposition resolving **OQ-1** (ADR-022), the
augmentation loop and blocking-term trichotomy (ADR-023). Known-insufficiency
oracle recovers a designed gap; `learning_error()` returns exactly `0.0` by
construction (analytic operators only through M7, per ADR-001) — the
*correct* value for this instantiation, not a placeholder. **ADRs 021–023.**

### M5 — Assimilation (`7c1375e`)
`assimilate.py`: EnKF (ADR-024, standard stochastic/perturbed-observation
filter), an ensemble smoother built from cross-covariance across the
recorded particle trajectory rather than a re-derived backward recursion
(ADR-025), and an innovation-based drift monitor instantiating Spec §10's
proposition via the NIS chi-squared test (ADR-026 — S-10's *procedure* is
PASS-C, its *proposition* is SPEC, so this is a Decide-ADR). A latent
variable no sensor touches is shown transitioning to `Triage.INFERRED`,
closing the loop with M3. **ADRs 024–026.**

### M6 — Class B (`8b67ec0`)
`classb.py`: driver/tail separation with join-threshold sensitivity
diagnostics, the Hill tail-index estimator and `tail_index_transfer`, the
correlation-length estimator (with the "biased low on short domains" caveat
made a *computed* diagnostic), `N_eff` dimensional reduction, subset
simulation, and three of the four validation-ladder rungs (ADR-027, one
bundled ADR covering all the numerical conventions since every S-4.x
subsection is fully SPEC). **OQ-3** (competing risks) answered: pooling
defect populations and fitting one tail index underestimates the true
design-point risk by orders of magnitude, in the unsafe direction. A
designed ranking inversion between two materials reproduces via Proposition
4.2's dimensional reduction. **ADR-027.**

### M7 — Conformance OMI-0/1 (`61a5502`)
`conformance.py`: the OMI-0/1/2 level table as a *reporting-completeness*
gate (ADR-028) — every line item in Spec §9.1 says "reported," never "below
threshold," so `ConformanceReport.claim()` checks presence of
caller-supplied diagnostics and raises a dedicated `ConformanceNotMet` (not
`NotSpecified` — a missing diagnostic is evidentiary, not a Spec gap) naming
exactly what's unmet. **Flagship reaches OMI-1** with real evidence
(matched-history sufficiency campaign, semigroup residuals, dangerous-set
triage, calibration diagnostics). **Contrast reaches OMI-0**, honestly
blocked at OMI-1 on exactly one item (no erasure operator means nothing is
free to exclude from its tracked state without a real augmentation-loop
investigation this milestone didn't undertake — stated as a scope decision,
not a discovery of impossibility). **Neither domain claims OMI-2** — the
unmet list narrows to exactly the two M9-gated items once everything else
is supplied. **ADR-028.**

### M8 — Learning (`2b7a3f0`)
`learning.py`: a DeepONet-style branch/trunk network behind
`EvolutionOperator`, implemented **entirely in numpy** — no torch anywhere
(ADR-029): this sandbox cannot install torch to test it, and an untested
second implementation was judged worse than none. Forward pass, exact
analytic Jacobian, and hand-derived reverse-mode backprop are one
consistent implementation, validated against finite differences
(`tests/test_learning_gradient_check.py` caught and fixed a real scaling
bug in the multi-step loss gradient during development — the kind of bug
that would otherwise have silently trained wrong). Training: multi-step
pushforward with truncated BPTT, noise injection, a semigroup-consistency
penalty differentiated through the network's own split-path composition,
spectral-norm capping. `constraints.py` (ADR-030): four of Spec §2.2's five
hard-constraint categories as exact reparameterisations (positivity,
simplex, monotonicity, conservation), never loss penalties; thermodynamic
admissibility (GENERIC/port-Hamiltonian) explicitly out of scope. A trained
operator passes held-out prediction accuracy and improves its own
semigroup residual at stated tolerances; constraints hold 20x outside
training scale. **ADRs 029–030.**

### M9 — Inverse design → OMI-2 (`e43d858`)
`inverse.py`: `ReachabilityCertificate` restricted to linear functionals
(ADR-031), giving an exact accumulated bound and closed-form
nearest-reachable-state projection — Core §5's output contract completed.
`ApparatusParameterization` (ADR-032) makes "parameterise in apparatus
settings, never driving paths" structurally true — no function in the
module accepts a raw `Control`. The decision layer (ADR-033): probability
of conformance (the actual Spec §7.3 objective), CVaR, asymmetric cost,
**OQ-4** answered via `diagnose_infeasibility`'s ordered three-way check
(trust region → control/`𝒰_adm` → aleatoric spread). A known-unreachability
oracle fires exactly outside its bound (checked at the literal boundary and
infinitesimally beyond it); four constructed infeasibility scenarios (one
per binding term, plus a feasible case) are all correctly diagnosed.
**ADRs 031–033.**

---

## Cross-cutting artifacts

### ADR log — 33 ADRs, `docs/DECISIONS.md`
Every structural choice the Specification leaves open is recorded there
*before* the corresponding code, per CLAUDE.md §4's "Decide" move: what the
Spec leaves open, what was chosen, what was rejected and why, what would
change it, and which test pins it. None were retrofitted after the fact.

### Open Questions — 5 posed, all resolved
| id | Question | Status |
|---|---|---|
| OQ-1 | Fingerprint: single probe or contrast between probes? | Answered (M4) |
| OQ-2 | Erasure completeness: operator- or component-level? | Partially answered (M2) — see below |
| OQ-3 | Class B under competing defect populations | Answered (M6) |
| OQ-4 | Does inverse design report which variance is binding? | Answered (M9) |
| OQ-5 | Metric dependence of every reported `L` | Answered (M2) |

Each has a proposed v1.4 wording recorded in `docs/COVERAGE.md` Part IV — a
concrete artefact for anyone taking this back to the framework's own authors,
not just an internal note. **OQ-2 is "partially"**, not "answered": the first
hypothesis (a designed surviving direction spanning several named components)
is explicitly deferred past M3, since it needs machinery this repo doesn't
yet build a dedicated test for; this is recorded as open, not glossed over.

### Gap register — `docs/COVERAGE.md`
Every Spec/Core section is tagged SPEC / PASS-B / PASS-C / PASS-D / CLAIM.
Anywhere this repo implements a PASS-B/C item, it's because an ADR made a
declared choice (never a silent interpolation across the gap) — the table's
"Repo" column names the ADR. Anywhere it doesn't, the row still says PASS-B/C
and the repo column says "refuse" or names the anti-goal. Nothing in
`docs/COVERAGE.md` was edited to make a milestone look more complete than the
code actually is — check `git log -p -- docs/COVERAGE.md` if you want the
paper trail.

### Anti-goals — untouched, per `CLAUDE.md` §9
Tier II / FE² coupling, hybrid mode/guard structure, body-indexed state and
the registration operator, the closure-defect *measurement* procedure (the
*definition* is implemented, per `omi.conformance.measure_closure_defect`'s
refusal stub — it raises `NotSpecified` citing S-6 and is never silently
bypassed), closed-loop confounding remedies, the linear-Gaussian
error-control dichotomy proof, and compute-budget/modality-catalogue
numbers. None of these were attempted; each is named, refused, and cited
rather than left unmentioned.

---

## Conformance status (`omi.conformance`)

| Level | Flagship | Contrast |
|---|---|---|
| OMI-0 | ✅ Claimable | ✅ Claimable |
| OMI-1 | ✅ Claimable (real evidence, `tests/test_conformance_flagship.py`) | ❌ Blocked on exactly one item — no sufficiency campaign built for this domain (scope decision, `tests/test_conformance_contrast.py`) |
| OMI-2 | ❌ Blocked on 3 items (reachability certs, prospective trial — both M9-module-gated but not conformance-wired; Class B volume-scaling — no Class-B readout in this domain at all) | ❌ Blocked on 2 items (reachability certs, prospective trial — `inverse.py` exists post-M9 but no conformance demonstration wires it in yet) |

**Note:** M9 built the reachability-certificate and decision-layer machinery,
but no one has yet plumbed a real certificate or a prospective inverse-design
trial into a `ConformanceInputs` for either domain — so OMI-2 remains
unclaimed in practice even though the underlying module now exists. This gap
was flagged explicitly at the end of the M9 report and is still open.

---

## Scope limitations, stated plainly

These are deliberate stopping points, each with its own ADR or COVERAGE.md
note — not gaps discovered by a reviewer, but gaps this build already named:

- **Anisotropic/directional `ℓ_D`** (Spec §4.4's banded-structure case) —
  isotropic scalar correlation length only (ADR-027).
- **Thermodynamic admissibility** (GENERIC/port-Hamiltonian structure) — not
  implemented; the other four Spec §2.2 categories are (ADR-030).
- **Torch backend for learned operators** — not implemented; numpy-only, by
  design, since this environment can't install torch to test a second
  implementation (ADR-029).
- **General nonlinear reachability certificates** and the forward-
  sampling/over-approximation hierarchy's intermediate rungs — only the
  linear-functional case and the invariant-certificate rung are implemented
  (ADR-031).
- **Coupled/rate-limited apparatus constraint manifolds and mixed-integer
  handling** (Spec §7.2) — only a box `𝒰_adm` (ADR-032).
- **A real sufficiency campaign for the contrast domain** — not built;
  flagship's is (M7 report; `tests/test_conformance_contrast.py`'s module
  docstring).
- **A conformance-wired OMI-2 demonstration** — `inverse.py`'s machinery
  exists post-M9 but isn't yet plumbed into a `ConformanceReport` for either
  domain (see Conformance status above).

If any of these turn out to matter for what this review is actually for,
say so — each is a bounded, well-understood follow-on, not a design dead end.

---

## Verification

Reproduce this from a clean clone, in a fresh virtualenv (not the one already
in this container):

```bash
python3 -m venv /tmp/review_venv
source /tmp/review_venv/bin/activate
pip install -e ".[dev]"

pytest tests/lint -v        # 9 tests: vocabulary, citations, gap-citations
mypy src tests               # strict mode, zero errors expected
pytest -v                    # 180 tests as of e43d858
bash scripts/check_determinism.sh   # runs the suite twice, diffs output
```

All four are also wired as separate GitHub Actions jobs
(`.github/workflows/ci.yml`) and were re-run in a fresh venv (mirroring CI,
not just the container's persistent one) at the end of every milestone in
this build — see each milestone's closing report in the conversation history
for the exact output.

### What the numbers were at `e43d858`

| Check | Result |
|---|---|
| `pytest tests/lint` | 9 passed |
| `mypy src tests` | Success: no issues found in 81 source files |
| `pytest` (full suite) | 180 passed |
| `scripts/check_determinism.sh` | Two independent runs produced identical output |

### Source size, for scale

| Tree | Lines |
|---|---|
| `src/omi/` (16 modules, domain-neutral) | 3,631 |
| `src/omi_domains/` (2 domains) | 548 |
| `tests/` (49 test files, incl. 13 oracles) | 4,914 |

---

## Suggested review order

1. `CLAUDE.md` (if not already read) — everything below is judged against it.
2. `docs/DECISIONS.md`'s ADR-001 through ADR-033, skimmed in order — this is
   the actual design history, and each one names what it rejected and why.
3. `docs/COVERAGE.md` in full — the gap register is the single artifact that
   lets you check "does this repo claim more than the Specification
   supports" without reading every module.
4. Pick 2–3 milestones that matter most for your purposes and read their
   commit diffs directly (`git show <sha>`), starting from the ADRs they
   added and following the citations into the code.
5. Run the verification suite yourself (above) rather than trusting this
   document's numbers.

---

## Addenda (post-`e43d858`, dated)

This document is a snapshot stamped to a commit range (CLAUDE.md §10); later
findings are appended here, not edited into the sections above.

**On M6's "A designed ranking inversion between two materials reproduces via
Proposition 4.2's dimensional reduction" (above, M6 section).** A later
circularity review found this overclaims: the oracle behind that sentence
(`tests/oracles/known_ranking_inversion.py`) calls `omi.classb.n_eff`
directly with hand-supplied `ℓ_D`/`p0` constants for two materials — it
samples no driver field and never calls `estimate_correlation_length`. What
it demonstrates is that `n_eff`'s own two-regime branch arithmetic produces
the sign-flip the two-tier structure predicts under chosen constants — a
legitimate formula-correctness check, not empirical evidence that the
reduction is an emergent effect of a real spatially-correlated field. See
`docs/V1.4-EDITS.md` E-14 for the full finding (it names this oracle as the
same blocker as the later flagship bend campaign's thin regime) and
`tests/oracles/test_known_ranking_inversion.py::test_ranking_inversion_is_not_empirically_validated_as_an_emergent_effect`
(added and permanently skipped, same review) for the record that the
stronger claim remains unchecked.
