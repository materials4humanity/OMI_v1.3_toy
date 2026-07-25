# DECISIONS.md

Architecture decision records. **Every choice the Specification does not
dictate is recorded here before it is implemented.**

Spec §12 (reference architecture) is itself `[Pass C]` — a sketch, not a
design. The class structure of this repository is therefore a *contribution*
rather than a transcription, and it needs the same scrutiny as any framework
claim. That is what this file is for.

---

## Template

```markdown
## ADR-NNN — <short title>

**Status.** Proposed | Accepted | Superseded by ADR-NNN
**Date.** YYYY-MM-DD
**Gap.** COVERAGE id (e.g. S-7.1), or "none — implementation choice"
**Milestone.** M#

**What the framework leaves open.**
One paragraph. Quote the Spec line that stops short, if there is one.

**Decision.**
What we do. Specific enough to implement from.

**Alternatives rejected.**
At least one, with the reason. If you cannot name an alternative you have not
understood the choice.

**What would change this.**
The observation, result or framework revision that would reopen it.

**Pinned by.**
The test that fails if someone silently changes this.
```

---

## Seeded decisions

These were made when the repository was set up. They are open to challenge —
challenge them by writing a superseding ADR, not by editing these.

---

## ADR-001 — Analytic operators before learned ones

**Status.** Accepted **Gap.** none — build-order choice **Milestone.** M1

**What the framework leaves open.**
Spec §2.1 names neural operators as the approximation class but nothing
requires that the *reference implementation* use them to develop the
measurement machinery.

**Decision.**
Domains supply closed-form analytic evolution operators. Every module through
M7 is developed and tested against these. Learned operators enter at M8 behind
the same `EvolutionOperator` protocol, and the analytic operators remain as the
test oracle permanently.

**Alternatives rejected.**
*Learn first.* Rejected because it shapes the substrate around a surrogate's
needs, makes every downstream test dependent on training quality, and delays
the framework's distinctive claims behind an ML engineering problem. Also
because tangent maps through an analytic chain are exact, which is what makes
the observability oracles trustworthy.

**What would change this.**
A measurement that cannot be exercised without a learned operator. None is
currently known; the learning-error term (S-1.4) is the closest and it is
explicitly deferred to M8.

**Pinned by.** `tests/test_no_torch_at_import.py` — `src/omi/` imports cleanly
with torch uninstalled.

---

## ADR-002 — The metric is an object, not a module constant

**Status.** Accepted **Gap.** OQ-5 **Milestone.** M1

**What the framework leaves open.**
Core §3.9's error bound and the erasure definition (`L ≪ 1`) are
metric-dependent, and the state has heterogeneous units — densities, stresses,
thicknesses, fractions. Spec §2.5 requires a *local spectrum* rather than a
global bound but does not fix the metric. No section declares one.

**Decision.**
`Metric` is a first-class object carrying per-component non-dimensionalisation.
Default: each component scaled by its aleatoric standard deviation across the
declared incoming population, so `L` reads as *"how much does a one-sigma
incoming variation grow"*. Any result object quoting a Lipschitz constant,
erasure measurement, state distance or trust radius carries the metric that
produced it. Reports without it are non-conforming.

**Alternatives rejected.**
*A module-level `SCALE` array.* Rejected because it makes the metric invisible
in results and untestable, and because different target readouts may justify
different weightings.
*Wasserstein on descriptor measures ⊕ weighted Sobolev norms*, as Core §3.2
suggests. Not rejected — deferred. It is the right choice for field-valued
slots and should supersede this when fields arrive.

**What would change this.** Field-valued slots (M8+), which need a genuine
function-space norm rather than component scaling.

**Pinned by.** `tests/oracles/test_metric_dependence.py` — rescaling a slot
changes every reported `L`, and the default normalisation makes cross-slot
comparison stable.

---

## ADR-003 — Two domains from M1, chosen to invert each other

**Status.** Accepted **Gap.** C-7 (PASS-D) **Milestone.** M1

**What the framework leaves open.**
Core §7 declares two instantiations but marks the full declarations `[Pass D]`.
Nothing forces an implementation to build more than one.

**Decision.**
Both `flagship` (metallurgical process chain) and `contrast` (electrochemical
cell under service) exist from M1, declaring the seven interface items in the
same order so they are machine-diffable. The contrast may be thin — analytic,
low-fidelity — but it must exercise the inversions Core §7.2 tabulates: no
erasure operators, poor observation suite, `Γ`-dominated state,
usage-determined control.

**Alternatives rejected.**
*Flagship first, contrast later.* Rejected because an interface built against
one domain is shaped to it. The generality claim is the framework's main
structural bet and it is only checkable by the diff.

**What would change this.** Nothing short of abandoning the generality claim.

**Pinned by.** `tests/test_interface_diff.py` — the declared interfaces differ
on at least six of seven items, reproducing Core §7.2.

---

## ADR-004 — Oracle-based testing

**Status.** Accepted **Gap.** none — testing choice **Milestone.** M0

**What the framework leaves open.**
Spec §9.2 lists checks that return residuals but does not say how to know
whether an *estimator* is correct in the absence of ground truth.

**Decision.**
For every quantity the framework requires to be measured, `tests/oracles/`
contains a synthetic system with the answer known by construction, exposing
`truth()` alongside its normal interface. Estimators are asserted to recover
constructed truth. Assertions are qualitative (orders of magnitude, ranks,
orderings, sign) rather than exact figures, so tuning constants can change
without silently invalidating a claim.

**Alternatives rejected.**
*Regression tests against recorded output.* Rejected because they pin
implementation accidents rather than correctness, and freeze physics constants.

**What would change this.** Real data with independently measured latent state
— which would supplement, not replace, the oracles.

**Pinned by.** the oracle protocol test in `tests/oracles/__init__.py`.

---

## ADR-005 — Refusal is the default at a gap

**Status.** Accepted **Gap.** all PASS-B/PASS-C **Milestone.** M0

**What the framework leaves open.**
Roughly a third of the Specification is `[Pass B]`/`[Pass C]` — result stated,
procedure absent.

**Decision.**
Code reaching an unspecified procedure raises `omi.NotSpecified` citing the
`COVERAGE.md` id. Filling a gap requires an ADR first. CI enforces that every
`NotSpecified` cites a live id.

**Alternatives rejected.**
*Implement a reasonable default.* Rejected because a plausible implementation
of an underived procedure is indistinguishable from the framework's position to
anyone reading the code, and will propagate into a paper. The framework's own
stance (Core §3.9) is that refusing is more credible than answering badly; the
implementation should hold the same line.
*Leave `TODO` comments.* Rejected — invisible at runtime.

**What would change this.** Framework v1.4 resolving the pass.

**Pinned by.** `tests/test_gap_citations.py`.

---

## ADR-006 — `src/omi/` is domain-free, enforced by lint

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M0

**What the framework leaves open.**
Core purged domain vocabulary between v1.2 and v1.3 but nothing enforces the
purge in an implementation.

**Decision.**
A banned-term lint over `src/omi/`. Domain vocabulary lives only in
`src/omi_domains/`. The banned list starts from the Core Appendix B glossary
(both columns) and grows as domains are added.

**Alternatives rejected.**
*Convention and review.* Rejected — this exact leak is what v1.2 suffered from,
and it is cheap to make structural.

**What would change this.** Nothing.

**Pinned by.** `tests/test_vocabulary.py`, which must fail on a planted term.

---

## Open questions

Not decisions — hypotheses the code should settle. Full statements in
`COVERAGE.md` Part IV. Record outcomes here when resolved.

| id | Question | Milestone | Status |
|---|---|---|---|
| OQ-1 | Fingerprint: single probe or contrast between probes? | M4 | open |
| OQ-2 | Erasure completeness: operator-level or component-level? | M2 | open |
| OQ-3 | Class B under competing defect populations | M6 | open |
| OQ-4 | Does inverse design report which variance is binding? | M9 | open |
| OQ-5 | Metric dependence of reported `L` | M2 | open |

When one resolves: record the evidence, update `COVERAGE.md`, and if it implies
a framework edit, state the proposed wording so it can be carried to v1.4.
