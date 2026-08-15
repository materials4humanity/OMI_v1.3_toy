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

**Status.** Superseded by ADR-034 (docs/DECISIONS.md) for the pinning-test
half only — the decision to build two domains chosen to invert each other
stands unchanged; what ADR-034 corrects is the mechanical claim "differ on
at least six of seven items," which conflated Core §7.2's seven *table
rows* with Core §4's seven *interface items* (they are not the same seven).
**Gap.** C-7 (PASS-D) **Milestone.** M1

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

**Pinned by.** `tests/test_interface_diff.py` — see ADR-034 for the corrected
form of this pin (the declared interfaces invert on exactly the six Core §4
items Core §7.2's own table names, checked by name rather than by count).

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

**Amendment (M4).** "Campaign" was seeded from Appendix B's flagship column
("provenance group" → "heat, campaign") but turned out to collide with the
Specification's *own* generic vocabulary: Spec §1 and §8 use "campaign" for
the framework-level concept (the sufficiency campaign), not the
metallurgical provenance-group sense, and `src/omi/sufficiency.py`
legitimately needs to cite it. Removed from the banned list; "heat" stays
banned, since Core/Spec never use it as a generic term (they say "thermal").
This is exactly ADR-006's "grows as domains are added" working in reverse —
a real collision, found while implementing, corrected instead of worked
around.

---

## ADR-007 — Type checker: mypy in strict mode

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M0

**What the framework leaves open.**
ROADMAP M0 requires "type-check" in CI and CLAUDE.md §8 requires "type hints
throughout," but neither the Core nor the Spec names a tool, and Spec §12
(reference architecture) does not reach this level of build tooling at all.

**Decision.**
`mypy --strict` over `src/` and `tests/`, run as its own CI job. Config lives
in `pyproject.toml` under `[tool.mypy]`. Slot and type/class taxonomies are
enums (CLAUDE.md §8), which strict mypy checks exhaustively when `match`
statements are used — a direct enforcement of "typed, not stringly-typed"
without extra tooling.

**Alternatives rejected.**
*pyright.* Faster and arguably better inference in editors, but its strict
CLI mode is oriented around `pyrightconfig.json` rather than `pyproject.toml`
and its plugin story for the dataclass/enum-heavy style this codebase uses is
thinner than mypy's. Nothing here is framework-mandated either way; mypy is
chosen for `pyproject.toml`-native configuration and long-standing default
status for library packages, not because pyright is deficient.

**What would change this.** A concrete mypy limitation hit during M1+ (e.g.
variance issues with the `EvolutionOperator` protocol) that pyright resolves
and mypy cannot, even with `--strict` relaxed locally.

**Pinned by.** the `typecheck` CI job (`mypy src tests`); it must exit 0 on
the empty M0 framework.

---

## ADR-008 — Test layout: lint tests plant and remove their own violations

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M0

**What the framework leaves open.**
ROADMAP M0 requires the three lints to be "demonstrably" shown failing on a
planted violation and passing once removed, but does not say how that
demonstration is captured so it stays true (rather than being a one-time
manual transcript that silently rots).

**Decision.**
Lint tests live in `tests/lint/` (`test_vocabulary.py`, `test_citations.py`,
`test_gap_citations.py`). Each lint test is structured as a pair: an
implementation function (`find_banned_terms`, `find_uncited_docstrings`,
`find_uncited_gap_ids`) that scans a given source tree and returns violations,
plus a pytest test that (a) asserts zero violations against the real
`src/omi/`, and (b) writes a temporary module containing one planted
violation, asserts the scanner catches it, then removes the temp module. Both
directions of the fail→pass demonstration are therefore executable on every
CI run, not just performed once by hand.

**Alternatives rejected.**
*A one-off shell transcript checked into the repo.* Rejected — it is exactly
the kind of assertion that silently stops being true after a refactor, which
is the failure mode CLAUDE.md's gap discipline exists to prevent applied to
tooling itself.
*Git history as the evidence* (commit a violation, then commit its removal).
Rejected — not re-verifiable in CI on every run, and it pollutes history with
a deliberately broken intermediate commit.

**What would change this.** Nothing structural; new lints follow the same
pattern.

**Pinned by.** the lint tests themselves — `tests/lint/test_vocabulary.py`,
`tests/lint/test_citations.py`, `tests/lint/test_gap_citations.py`.

---

## ADR-009 — Oracle protocol expressed as a minimal `Protocol`, not a base class

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M0

**What the framework leaves open.**
CLAUDE.md §7 and ROADMAP M0 require an oracle to expose "the system's normal
interface plus a `truth()`," but oracles across milestones wrap unrelated
"normal interfaces" — a tail oracle samples and maps; a sufficiency oracle
evolves matched-history pairs; a blind-spot oracle exposes a Gramian. Nothing
in the Spec fixes how that common shape is expressed in code.

**Decision.**
`tests/oracles/__init__.py` defines a `runtime_checkable typing.Protocol`
named `Oracle` with exactly one member: `truth() -> Any`, documented to return
"the constructed ground-truth answer, whatever type is natural for this
oracle." Each concrete oracle (e.g. the known-tail oracle) is an ordinary
class that happens to satisfy the protocol; its actual "normal interface"
(sampling, evolving, whatever the oracle needs) is specific to it and
documented in its own module, not forced into a shared shape.

**Alternatives rejected.**
*An ABC with abstract methods for both the normal interface and `truth()`.*
Rejected because the "normal interface" is not one thing across oracle types
— a shared ABC would either be empty (offering nothing beyond `Protocol`) or
would force unrelated oracles (tail, blind-spot, insufficiency) into a common
method surface they don't naturally share, which is inventing structure the
framework does not require.

**What would change this.** If a second protocol member turns out to be
common to every oracle built through M6 (e.g. a shared `seed`/`rng` accessor),
it gets added to `Oracle` then, pinned by a new test.

**Pinned by.** `tests/oracles/__init__.py`'s own conformance assertion, and
`tests/oracles/test_known_tail.py::test_isinstance_oracle_protocol`.

---

## ADR-010 — The gap registry parses `COVERAGE.md`'s tables by line-oriented regex

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M0

**What the framework leaves open.**
ROADMAP M0 and CLAUDE.md §4 require "a registry of every gap referenced in
code," parsed from `docs/COVERAGE.md` rather than duplicated in Python, but
neither document specifies a parsing method — `COVERAGE.md` is prose-and-tables
Markdown, not a machine format.

**Decision.**
`src/omi/gaps.py` reads `docs/COVERAGE.md` (located by searching upward from
the module's own file for a directory containing `docs/COVERAGE.md`, so it
works regardless of the caller's working directory) and extracts every id in
the first column of a Markdown table row via a line-anchored regex
(`^\|\s*([A-Za-z][\w.\-]*)\s*\|`), restricted to the table bodies of Part I
and Part II (bounded by the `## Part` headings), skipping header/separator
rows. The result is a `frozenset[str]` cached for the process lifetime.

**Alternatives rejected.**
*A full Markdown parser (e.g. `markdown-it-py`, `mistune`) to walk a real
table AST.* Rejected as a dependency (and a `pyproject.toml` pin) bought for a
document whose table format is simple, stable, and entirely under this
project's own control.
*A YAML/JSON file mirroring the ids, regenerated from `COVERAGE.md` by a
script.* Rejected — this is exactly the duplication the roadmap forbids;
a generated mirror is still a second copy that can drift if the generation
step is skipped.

**What would change this.** `COVERAGE.md`'s table format changing shape
(e.g. splitting into per-part files) — the regex and file-location search
would need updating together, in one place.

**Pinned by.** `tests/test_gap_registry.py` — asserts known ids (e.g.
`"S-1.2"`, `"C-3.1"`) are present and an invented id (e.g. `"S-99.9"`) is
absent, directly against the real `docs/COVERAGE.md`.

---

## ADR-011 — State is a flat array plus a schema, not a nested dict

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M1

**What the framework leaves open.**
Core §3.1 fixes the four slots `(m, z, ν, Γ)` and Core §3.2 fixes the
abstract spaces, but neither fixes a concrete data representation. Spec §12
sketches `State` as "named slots... mode label; body index" without saying
how a slot's named components are laid out in memory.

**Decision.**
A `State` wraps one flat `numpy.ndarray` of floats plus a `StateSchema` — an
ordered mapping from `(slot, component name)` to a slice of that array.
Domains declare their schema (interface item 1) by naming components per
slot with a dimension each; `State.get(slot, name)` slices the flat array.
Metric scaling, Jacobians, and SVDs therefore all operate on one plain array
shape.

**Alternatives rejected.**
*A nested dict of arrays per slot* (`state.m["texture"]`). Rejected: natural
to read, but every numeric routine (Jacobian, metric scaling, SVD) would need
to flatten/unflatten repeatedly, and the flattening order would become an
undeclared implicit contract. Making the flat array primary and dict-like
access a view onto it removes the duplication.

**What would change this.** Field-valued slots (spatially resolved `m`, per
Core §2.5's body-indexed state) would need a richer per-slot tensor/mesh
representation — out of scope while that PASS-C remains an anti-goal.

**Pinned by.** `tests/test_state_schema.py`.

---

## ADR-012 — `EvolutionOperator` is an ABC: `step` is domain-supplied, `lift`/`lipschitz` are computed, `is_erasure` is declared

**Status.** Accepted **Gap.** none — implementation choice, informed by C-3.9a/S-3.x **Milestone.** M1

**What the framework leaves open.**
Spec §12 names `.step`, `.lift`, `.lipschitz_estimate`, `.is_erasure` as the
protocol surface but does not say which are domain-supplied versus generic
machinery.

**Decision.**
`EvolutionOperator` is an ABC. A concrete domain operator supplies `step`
(the elementary map) and declares `is_erasure` as a fixed boolean — matching
how Core §7.1's table declares erasure per stage from domain knowledge, not
from a computed numeric threshold. `jacobian` defaults to a central
finite-difference estimate (plain numerics, not a framework claim); domains
may override it with an exact analytic derivative, which ADR-001 flags as
eventually necessary for trustworthy M3 observability oracles. `lift`
(pushforward to `𝒫(𝒮)`, by looping `step` over particles) and `lipschitz`
(SVD of the metric-scaled Jacobian — Spec §2.5's *local* spectrum, not a
global bound) are both generic, provided by the base class from
`step`/`jacobian`.

**Alternatives rejected.**
*A `Protocol` requiring all four methods on every operator.* Rejected —
`lift` and `lipschitz` are entirely mechanical given `step`/`jacobian`;
forcing every domain operator to reimplement them invites drift (one loops
particles wrong, another computes the SVD differently) for no benefit.
*Computing `is_erasure` from a numeric rank/singular-value cutoff.* Rejected
— Core §3.9 says only "substantially lower effective dimension" and `L ≪ 1`;
picking a cutoff now would invent a threshold the Specification doesn't give,
exactly what ADR-005 forbids. Quantitative erasure completeness is M2's
`erasure.py`.

**What would change this.** M2's erasure-completeness measurement may find a
domain-declared `is_erasure` disagrees with the measured rank — that is a
finding to report, not a reason to compute the flag differently now.

**Pinned by.** `tests/test_semigroup.py` (exercises `lift`/`lipschitz`
indirectly) and each domain's own operator tests.

---

## ADR-013 — `Control` is a callable over a declared interval

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M1

**What the framework leaves open.**
Core §3.2 requires controls to be "functions of time on an interval, not
scalars," but fixes no representation (piecewise-constant table, spline,
closed-form callable, ...).

**Decision.**
`Control` is a frozen dataclass wrapping a plain Python callable
`t -> np.ndarray` together with the declared interval `[t0, t1]`; calling
`control(t)` validates `t` is in range. This is the minimal thing satisfying
"function of time, not a scalar" without committing to a sampling or spline
representation no domain here needs yet.

**Alternatives rejected.**
*A fixed-grid array of samples.* Rejected — forces a sampling-rate decision
with no Spec basis, and the analytic operators in this reference
implementation want exact closed-form evaluation at arbitrary `t`, not
interpolation error.

**What would change this.** A domain needing a control with its own internal
state (e.g. a stateful controller) — the callable signature would need
widening.

**Pinned by.** `tests/test_control.py`.

---

## ADR-014 — Readouts: three distinct call shapes, not one interface; Class B computed by the literal weakest-link formula, not tail machinery

**Status.** Accepted **Gap.** S-4.2–S-4.6 deferred to M6; none for the taxonomy split itself **Milestone.** M1

**What the framework leaves open.**
Core §3.5 defines Type-0/1/2 with three genuinely different signatures
(`S → R^n`; `S → Op(U → R × S)`; `Op × 𝔅 → R`), not one shape. Class B's tail
machinery (Spec §4.2–4.6) is scheduled for M6, not M1.

**Decision.**
`readouts.py` declares `ReadoutType`/`ReadoutClass` enums plus separate base
classes matching each type's own signature: `FunctionalReadout` (Type-0) and
`ConstitutiveReadout` (Type-1). Type-2 is declared in the enum, for interface
declarations that need to name it, but has no concrete base class here — it
requires Tier II, an anti-goal (CLAUDE.md §9). A Class-B-flagged
`FunctionalReadout` accepts an explicit sub-element count `n_sub` standing in
for `V / V_0` and computes the weakest-link distribution directly from Core
§3.6's own formula `P(ρ_V > x) = [P(ρ_0 > x)]^N` by resampling the ensemble's
per-particle readout values — no driven-volume field, no tail extrapolation,
no join threshold. This is the literal SPEC-quality definition (C-3.6/S-4.1),
not the M6 refinement.

**Alternatives rejected.**
*One `Readout` ABC with a single abstract `__call__`.* Rejected — Type-2's
signature genuinely does not take a `State`; forcing a common signature would
misrepresent one branch's type.
*Implementing driver/tail separation (Spec §4.2) now.* Rejected — assigned to
M6; doing it now builds ahead of the roadmap's own ordering.

**What would change this.** M6 replacing the resampling-based Class B
computation with the driver/tail-separated, rare-event-sampled version — the
resampling version should then become the "naive" comparison baseline, not be
deleted.

**Pinned by.** `tests/test_readouts.py`.

---

## ADR-015 — `Chain` is a linear ordered sequence of segments for M1

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M1

**What the framework leaves open.**
Spec §12 names `Chain` (a mode-labelled DAG) as a core abstraction, but the
hybrid mode-labelling itself is Spec §5.1, PASS-C and an anti-goal for now
(CLAUDE.md §9).

**Decision.**
For M1, `Chain` is a linear ordered sequence of `(EvolutionOperator, Control)`
segments — the degenerate, single-mode case of a "mode-labelled DAG."
`Chain.rollout(initial_ensemble)` applies each segment's `.lift` in order and
returns a `Trajectory` recording *every* intermediate `Ensemble`, not just the
final one — needed later for rollout-length error curves (S-1.4/S-9.2) and
retrospective smoothing (Core §3.8).

**Alternatives rejected.**
*Building the general mode-labelled DAG now.* Rejected — Spec §5.1 is an
anti-goal; a linear chain is the honest subset that is actually specified
(Core §3.3's composition), and generalising to modes/guards without a
derivation would invent structure ahead of a PASS-C gap.

**What would change this.** Spec §5.1 being resolved (an ADR filling that gap,
or a framework revision).

**Pinned by.** `tests/test_chain_rollout.py`; `tests/test_semigroup.py` for
the composition identity itself.

---

## ADR-016 — Domain interfaces are a shared frozen dataclass, in Core §4's field order

**Status.** Accepted **Gap.** serves C-4/C-7 (PASS-D) **Milestone.** M1

**What the framework leaves open.**
Core §4 requires seven declared items but fixes no data structure. ADR-003
commits to two domains chosen to invert each other and to a diff test, but
not the declaration's shape.

**Decision.**
`src/omi/interface.py` (domain-neutral — the *shape* of a declaration is
framework machinery even though its *content* is domain-specific) defines an
`InstantiationDeclaration` frozen dataclass with seven fields in Core §4's
order: `state_schema`, `control_space`, `erasure_inventory`,
`readout_catalogue`, `observation_suite`, `invariants`, `scale_structure`.
Each of `omi_domains/*/interface.py` constructs one. A `diff(a, b)` function
reports, per field, whether the two declarations differ, making the
interface comparison in ADR-003's pinning test mechanical rather than
hand-written prose.

**Alternatives rejected.**
*Each domain freely shaping its own declaration object.* Rejected —
ADR-003's whole point is that a shared, fixed shape is what makes the diff a
mechanical fact instead of an assertion in prose.

**What would change this.** A third/fourth domain sketch (Core §7.3, Spec
§11.4) revealing the seven-item shape doesn't generalise.

**Pinned by.** `tests/test_interface_diff.py` (ADR-003's pinning test).

---

## ADR-017 — Numerical rank tolerance for erasure measurement, always reported alongside the full spectrum

**Status.** Accepted **Gap.** none — implementation choice, informed by C-3.9a/S-3.2 **Milestone.** M2

**What the framework leaves open.**
Core §3.9 defines an erasure by "image of substantially lower effective
dimension" and `L ≪ 1`; Spec §3.2's Proposition 3.2 talks about "Jacobian
rank `r`" as though rank were unambiguous. For an exact (symbolic) matrix
rank is well-defined; for a numerically computed Jacobian (finite difference
or floating point), distinguishing a "zero" singular value from a small
positive one requires a tolerance the Specification does not give a number
for.

**Decision.**
`measure_erasure` computes the metric-scaled Jacobian's singular values and
determines numerical rank with the same convention `numpy.linalg.matrix_rank`
uses by default: singular values below `max(M, N) * eps * σ_max` are treated
as zero, with the tolerance itself exposed as an optional parameter. This is
a standard numerical-linear-algebra convention, not a framework-specific
invented threshold — the same reasoning ADR-012 already applied to
finite-difference Jacobians. Critically, the **full singular-value spectrum
is always reported alongside the rank**, so a qualitative judgement of
"is this `L ≪ 1`, or just below whatever tolerance was chosen" stays
inspectable rather than being silently collapsed into one integer.

**Alternatives rejected.**
*Picking a fixed absolute cutoff (e.g. `1e-3`) as "the" erasure threshold.*
Rejected — that would be inventing the numeric content of "substantially
lower" and "`≪ 1`" that Core deliberately leaves qualitative, exactly what
ADR-005 forbids doing to a framework claim.
*Refusing to compute a rank at all until Core supplies a threshold.*
Rejected — unlike `L_phys × L_num` (S-2.5, genuinely `[Pass B]`, no
estimation procedure of any kind given), *numerical* rank is a solved,
standard problem once a matrix is in hand; the open part is only the
*qualitative* judgement of whether that rank constitutes "substantially
lower," which this ADR leaves to the reader of the reported spectrum, not to
a hidden constant.

**What would change this.** A domain whose Jacobian is so ill-conditioned
that the standard tolerance convention misclassifies genuine near-kernel
directions — would need a domain-declared tolerance override, still reported.

**Pinned by.** `tests/oracles/test_known_erasure.py` — a Jacobian with a
designed exact rank recovers that rank and the correct surviving subspace.

---

## ADR-018 — Φ is never formed as a chained matrix product; the Gramian itself is materialised densely at these toy state dimensions

**Status.** Accepted **Gap.** none — implementation choice, informed by S-3.5 (SPEC) **Milestone.** M3

**What the framework leaves open.**
Spec §3.5 requires: "Never form `Φ_{j,k}`. All quantities reduce to
matrix–vector products... `Φ_{j,k}v` is a forward JVP, `Φ_{j,k}^*w` a
reverse VJP... Randomised or Lanczos eigensolvers recover the leading `r`
directions in `O(r)` Gramian actions." This is a fully specified procedure
(SPEC, not a gap) — but it targets high-dimensional learned operators, where
forming `Φ_{j,k}` (a product of many segment Jacobians) or the full Gramian
matrix would be computationally infeasible. This reference implementation's
analytic operators have state dimensions in the single digits.

**Decision.**
Two things, kept distinct. **(1) `Φ_{j,k}` itself is never formed as a
chained matrix product**, at any state dimension — `propagate_jvp` /
`propagate_vjp` always apply each segment's own Jacobian to a *vector*, one
segment at a time, in forward (JVP) or reverse (VJP) order; the segments'
Jacobians are never multiplied together. This is the literal, scale-independent
content of "never form `Φ_{j,k}`," and it is honoured regardless of how small
the toy state is. **(2) The Gramian `G_k` and its per-sensor terms are
materialised as dense matrices**, built by applying the JVP/VJP action to
every standard basis vector. This is a reference-implementation concession
justified by the toy state dimension (≤ 10): materialising an `n×n` matrix
from `n` JVP/VJP evaluations costs `O(n)` actions, which is cheap here, and a
dense matrix is what the four-way triage (which needs the *complete*
eigenspectrum, not just the leading `r` directions) and the observed/inferred
per-term breakdown both consume directly. The Lanczos path Spec §3.5
recommends for recovering only the *leading* `r` directions at scale is
additionally implemented (`leading_eigenpairs_via_lanczos`, using
`scipy.sparse.linalg.eigsh` against a `LinearOperator` built from the same
JVP/VJP primitives) and tested for agreement with the dense computation —
so both computational strategies Spec §3.5 discusses exist, and an
implementation moving to high-dimensional learned operators at M8 would drop
concession (2), not concession (1).

**Alternatives rejected.**
*Only ever using the Lanczos/`LinearOperator` path, never materialising a
dense Gramian.* Rejected for M3 — the observed/inferred classification and
the complete four-way triage need every eigendirection's per-term
provenance, which the leading-`r` Lanczos path does not by itself supply
without additional deflation machinery Spec §3.5 does not derive.

**What would change this.** State dimensions large enough that dense
materialisation stops being cheap — i.e., exactly the regime Spec §3.5 is
written for, arriving with learned operators at M8.

**Pinned by.** `tests/test_observability_jvp_vjp.py` (Φ is never chained —
segment Jacobians are applied one at a time) and
`tests/test_observability_lanczos.py` (Lanczos and dense agree on the
leading eigenvalues of a known Gramian).

---

## ADR-019 — The observability prior covariance defaults to the declared metric's aleatoric variance

**Status.** Accepted **Gap.** none — implementation choice **Milestone.** M3

**What the framework leaves open.**
Spec §3.1 requires a prior covariance `P_k^0` to form the posterior
`P_k = ((P_k^0)^{-1} + G_k)^{-1}`, but does not say what `P_k^0` should be by
default.

**Decision.**
`P_k^0 = diag(metric.scale ** 2)` — the same aleatoric standard deviation
ADR-002 already uses to build the default `Metric`, squared into a variance.
This reuses an existing, already-declared quantity rather than introducing a
new one: "how much does this component vary across the incoming population
absent any information" is exactly what an aleatoric-sigma prior means, and
it keeps the prior expressed in the same declared metric that every
downstream Lipschitz constant and erasure measurement already carries
(CLAUDE.md §5 invariant 1).

**Alternatives rejected.**
*An uninformative (infinite / very large) prior.* Rejected — it would make
`P_k` insensitive to genuine prior domain knowledge (e.g. a component known
to vary only a little) and makes the posterior numerically degenerate in
directions with literally zero information, which is precisely the erased
subspace erasure.py already characterises.

**What would change this.** A domain wanting a genuinely different prior
(e.g. from a previous assimilation cycle, Core §3.8's recursive filtering) —
supported by passing an explicit `P_k^0` instead of the default.

**Pinned by.** `tests/test_observability_gramian.py`.

---

## ADR-020 — Danger-score triage and observed/inferred thresholds are conventions, always reported alongside their continuous scores

**Status.** Accepted **Gap.** none — implementation choice, informed by S-3.3 (SPEC) **Milestone.** M3

**What the framework leaves open.**
Spec §3.3 gives the danger score formula and the 2×2 triage exactly
(influential/non-influential × identifiable/unidentifiable), and
distinguishes *observed* from *inferred* by whether "a single near-diagonal
term `j ≈ k` dominates" the Gramian sum. None of "influential," "small
`v^*Pv`," or "dominates" is given a number.

**Decision.**
Two threshold conventions, both parameters (overridable), both always
reported alongside the raw continuous quantity they categorise so the label
is never the only thing kept:

1. **Influential / non-influential and identifiable / unidentifiable:**
   split at the *median* of, respectively, the influence scores
   (`v_i^* S_k^* W S_k v_i`) and the residual-uncertainty scores
   (`v_i^* P_k v_i`) across all eigendirections of `P_k` at this index —
   inclusively on both sides (`influence >= median`, `uncertainty <= median`),
   so that a direction tied exactly at the median (unavoidable with few
   directions, e.g. two components equally influential) is not silently
   excluded from "influential" by a strict inequality. A median split is
   scale-free (unlike an absolute cutoff, which would silently encode units)
   and answers a well-posed question — "is this direction more or less
   influential/uncertain than a typical direction here" — without inventing a
   physical threshold Core does not supply.
2. **Observed vs. inferred:** "near-diagonal" (`j ≈ k`) is operationalised as
   `time_index` within a declared window of `k` — default window 0, the most
   literal reading (only an observation *at* `k` itself counts as
   near-diagonal). A direction is *observed* if the near-diagonal
   observations together supply more than 50% of that direction's total
   Gramian quadratic form; otherwise, if identifiable at all, it is
   *inferred*. This was tightened during implementation: an earlier version
   compared against whichever instrumented index happened to be *nearest in
   time*, however far that was — which made "observed" the default outcome
   whenever only one, arbitrarily distant, sensor existed, defeating the
   distinction. The window-based reading is what makes "inferred" achievable
   at all, which is the point (CLAUDE.md §3: inferred directions are "the
   framework's distinctive contribution").
3. **Worst case over an operating window (Spec §3.6):** given triage results
   from an ensemble of nominal trajectories, "worst" means the single
   trajectory with the largest total danger score (`Σ_i 𝒟_i`); that
   trajectory's *entire* triage is returned, rather than taking an
   elementwise max of per-direction diagnostics across trajectories. Per-
   direction eigenbases come from different linearisation points and are not
   directly comparable component-by-component, so mixing them would not be
   a meaningful "direction" at all.

**Alternatives rejected.**
*Absolute, hand-picked cutoffs (e.g. "influence > 1.0").* Rejected — would
depend on the declared metric's units in a way a median split does not, and
would be exactly the invented-number problem ADR-005 and ADR-017 both avoid.

**What would change this.** A domain where the median split produces an
unhelpful triage (e.g. a strongly bimodal influence distribution where the
median falls inside a cluster) — the convention is a parameter, not hard-coded.

**Confirmed at Phase 3.3 (docs/ROADMAP.md).** The anticipated failure mode
above materialises on *both* declared domains, for a related but distinct
reason: when a declared target set is low-dimensional relative to state
size (true of both flagship's and contrast's current readouts), well over
half the eigendirections carry *exactly zero* influence, pushing
`influence_median` to exactly `0.0` — combined with the inclusive `>=`
comparison, every direction becomes "influential" by definition, so
`Triage.OBSERVED_BUT_IRRELEVANT` and `Triage.MARGINALISABLE` are
structurally unreachable at that query point. Separately, at `time_index=0`
with every declared sensor placed strictly downstream in both domains,
`Triage.OBSERVED` is also unreachable (no near-diagonal observation
exists). Only two of the four cells — `INFERRED` and `DANGEROUS` — are ever
populated on either domain's own first full-classification check
(`tests/test_domain_triage.py::test_full_triage_classification_is_asserted_for_both_domains`).
This is not a new defect — it is exactly the parameter-sensitivity this ADR
already names as a possibility — but it had never been checked against real
domain data before Phase 3.3, since prior tests asserted only
`dangerous_set()`, which cannot reveal that two whole categories were
unreachable.

**Pinned by.** `tests/oracles/test_known_blind_spot.py` (a designed
unobservable direction must land in the unidentifiable/marginalisable or
dangerous cells, never "observed") and the domain triage tests
(`tests/test_domain_triage.py`).

---

## ADR-021 — Matched-pair campaign data is plain arrays; the raw response gap is never independently exposed

**Status.** Accepted **Gap.** none — implementation choice, informed by S-1.2 (SPEC) **Milestone.** M4

**What the framework leaves open.**
Spec §1.2 gives the deficit estimator as a formula over expectations
(`E[(ρ_A-ρ_B)²]`, `σ²_rep`, `E[(s_{A,j}-s_{B,j})²]`) but not a data
structure for the matched-history pairs a real or simulated campaign
produces.

**Decision.**
`sufficiency_deficit` takes plain arrays: per-pair responses
`response_a`/`response_b`, per-pair matched-component differences
(`matched_component_diffs`, shape `(n_pairs, n_matched)`), a precomputed
sensitivity vector (`response_jacobian`, one entry per matched component —
callers obtain this from `observability.sensitivity_operator`, tying M4 to
M3 the way Spec §1 itself is scoped: "depends on §3"), and a separately
estimated `repeat_variance`. This keeps the estimator a pure function of
already-collected campaign data, decoupled from *how* a campaign generates
that data (real instrumentation, or an oracle's synthetic simulation).

The empirical mean of squared response differences
(`E[(ρ_A-ρ_B)²]`) is computed *inside* `sufficiency_deficit` and returned
only as one field of a `DeficitResult` dataclass that always also carries
the correction terms and the clamped, corrected deficit. **No public
function returns this raw quantity by itself** — docs/ROADMAP.md M4:
"a raw response gap must not be obtainable from the public API." A caller
who wants the raw number must construct it themselves from the same input
arrays, at which point it is visibly their own computation, not this
module's.

**Alternatives rejected.**
*A `MatchedPair` object per pair, with a campaign-runner class.* Rejected —
adds a class hierarchy around what the formula treats as four vectors, and
tempts a `campaign.raw_gap()` convenience method that would violate the
no-standalone-raw-gap requirement above.

**What would change this.** A real campaign's data-loading layer, once one
exists (Spec §5.3's provenance-grouped storage) — it would produce these
same arrays, not replace them.

**Pinned by.** `tests/oracles/known_insufficiency.py` /
`tests/oracles/test_known_insufficiency.py`.

---

## ADR-022 — The probe set decomposes into symmetric/antisymmetric parts, resolving OQ-1

**Status.** Accepted **Gap.** OQ-1 **Milestone.** M4

**What the framework leaves open.**
Spec §1.6's fingerprint table identifies a missing component by *which*
probe among a set shows divergence (e.g. "reversed driving only →
kinematic/directional variable"). OQ-1 (docs/COVERAGE.md Part IV)
hypothesised that this single-probe reading is unreliable for genuinely
directional (kinematic) hidden variables, which can affect *both* forward
and reversed probes equally in magnitude — with the informative signal
being in how the two probes' responses combine, not in whether either one
alone "diverges."

**Decision.**
`ProbeSet` carries the four raw values (`forward_a`, `forward_b`,
`reversed_a`, `reversed_b`) and exposes `symmetric_gap` (the difference
between the pairs' *averaged* forward/reversed responses) and
`antisymmetric_gap` (the difference between their forward/reversed
*half-differences*). A kinematic/directional hidden variable that flips
sign under reversal shows up entirely in `antisymmetric_gap`, with
`symmetric_gap ≈ 0`; a non-directional hidden variable shows the reverse.
`discriminating(signatures, tolerance)` takes the `(symmetric_gap,
antisymmetric_gap)` signature for each of several *candidate* missing
components and fails (returns `False`) if any two candidates' signatures
are not distinguishable at the declared tolerance — operationalising Spec
§1.6's own design requirement ("MUST discriminate between candidate
components, not merely detect divergence").

**Alternatives rejected.**
*Keep the single-probe table as the whole story, add symmetric/antisymmetric
as an extra diagnostic.* Rejected once `tests/oracles/test_known_insufficiency.py`
showed why: a single "does the reversed probe diverge" check gives the
*same* answer (yes) for both a kinematic and a non-kinematic hidden
variable in the oracle's construction, so it cannot discriminate between
candidates — exactly OQ-1's hypothesised failure mode, confirmed with
evidence, not left as speculation.

**What would change this.** A third candidate type (e.g. thermally
activated, Spec §1.6's other row) needing a third probe axis — the
decomposition would need generalising beyond a single forward/reversed
pair, which is out of scope for this M4 investigation.

**Pinned by.** `tests/oracles/test_known_insufficiency.py`.

---

## ADR-023 — Augmentation-loop candidates are schema components; learning error is exactly zero for analytic operators

**Status.** Accepted **Gap.** none — implementation choice; Err_learn informed by ADR-001 **Milestone.** M4

**What the framework leaves open.**
Spec §1.5's augmentation loop pseudocode operates on an abstract "candidate
pool `Z`" and a "state description `S`," without fixing what either is in
code. Spec §1.4's `Err_learn` requires training a candidate model at
matched data budget and reading its rollout-length error — meaningless
without a learned model to train.

**Decision.**
A candidate is a `(Slot, str)` naming one component to add to a
`StateSchema` — the same schema object already used everywhere else
(ADR-011). `augmentation_loop` takes a callable `sufficiency_test:
StateSchema -> DeficitResult`, a callable `variance_delta: StateSchema ->
float` (in practice backed by `observability.variance_term`, per
docs/ROADMAP.md M4: "consuming the variance term from M3"), and a candidate
pool of such pairs; it implements Spec §1.5's seven steps literally,
returning which candidates were accepted and — critically — *which term
blocked* (Spec §1.7's trichotomy) when the loop stops with residual bias.

`learning_error` always returns exactly `0.0`. This is not a placeholder
standing in for a future estimate — ADR-001 commits every module through M7
to exact analytic operators, which are not fit to any data budget and so
have no learning error by construction; `0.0` is the *correct* value for
this instantiation, not an approximation of one that will change. Spec
§1.4's actual rollout-curve procedure applies once M8 introduces learned
operators behind the same protocol, at which point `learning_error` gets a
real implementation, not a corrected one.

**Alternatives rejected.**
*Raise `NotSpecified` for `Err_learn`.* Rejected — S-1.4 is fully derived
(SPEC), not a gap; nothing about the procedure is missing, it simply has no
nonzero value to report before a learned operator exists. Refusing would
misrepresent a milestone dependency as a specification gap.

**What would change this.** M8's learned operators, at which point
`learning_error` is replaced with a genuine rollout-length-curve measurement
at matched data budget.

**Pinned by.** `tests/oracles/test_known_insufficiency.py` (the augmentation
loop accepting/rejecting the hidden variable correctly) and ADR-001's own
pin.

---

## ADR-024 — The EnKF reuses `state.Ensemble`/`EvolutionOperator.lift`; analysis is the standard stochastic (perturbed-observation) update

**Status.** Accepted **Gap.** none — implementation choice, informed by C-3.8/S-3.1 (SPEC) **Milestone.** M5

**What the framework leaves open.**
Core §3.8 states that "the assimilation of measurements into a state
estimate is a filtering algorithm assembled from evolution and readout
operators," and docs/ROADMAP.md M5 names "EnKF along the chain" as the
deliverable, but neither Core nor Spec gives ensemble Kalman filter update
equations — Spec §3.1 gives only the *linearised*, deterministic Gramian
form (`P_k = ((P_k^0)^{-1} + G_k)^{-1}`), which is the population/Fisher-
information object M3 already computes, not a recursive filter over a
single realised trajectory of noisy observations.

**Decision.**
`assimilate.py` uses the standard textbook ensemble Kalman filter (Evensen):

1. **Representation.** The forecast and analysis ensembles are plain
   `state.Ensemble` instances — no new ensemble type. Forecast is exactly
   `EvolutionOperator.lift` (already generic pushforward over particles,
   ADR-012); nothing new is needed to advance an ensemble through a chain
   segment.
2. **Analysis update.** At an instrumented index, given a forecast ensemble
   `{s_i^f}`, sample mean `s̄^f` and covariance `P^f` (empirical, over
   particles), and a readout `H` (a `FunctionalReadout`, reusing M3's typing
   rather than a new observation-operator class):
   `K = P^f H'^T (H' P^f H'^T + R)^{-1}` where `H' = H.jacobian(s̄^f)` is the
   readout's own linearisation (already required by `FunctionalReadout`,
   M3), and each particle is updated as
   `s_i^a = s_i^f + K(y_i - H(s_i^f))` with **perturbed observations**
   `y_i = y + ε_i`, `ε_i ~ N(0, R)` (the classical stochastic EnKF, chosen
   over a square-root/deterministic variant because it needs no matrix
   square root and its sampling noise is exactly the standard textbook
   price paid for an unbiased ensemble covariance update — not a numerical
   shortcut peculiar to this repository).
3. **Linearised `H'` reuses `FunctionalReadout.jacobian`**, so an EnKF run
   through a chain of analytic operators is a linearised-innovation variant
   of the algorithm — appropriate given ADR-001 (analytic operators only
   through M7): the forecast step is the true nonlinear pushforward, only
   the *analysis* gain linearises the readout, which is exact when the
   readout is itself linear (true for every M1–M4 domain readout) and a
   standard, named approximation (extended-EnKF) otherwise.
4. **Process noise `Q`** is a parameter the caller supplies per segment
   (default zero, i.e. deterministic dynamics plus observation noise only)
   — Spec never specifies a `Q`, and forcing one would invent a number; a
   caller building an oracle with genuine process noise passes it explicitly
   and it is added to the forecast ensemble as i.i.d. per-particle noise
   before the next analysis.

**Alternatives rejected.**
*A deterministic/square-root EnKF (ETKF, EAKF).* Rejected for this
milestone — avoids the perturbed-observation sampling noise, but adds a
matrix square root and a rotation ambiguity neither Spec nor Core motivates;
revisit if the stochastic EnKF's extra sampling noise is ever shown to
corrupt a downstream oracle's tolerance.
*A particle filter.* Rejected — Spec §3.1's own posterior-covariance object
is explicitly linear-Gaussian (`P_k = ((P_k^0)^{-1}+G_k)^{-1}`); a particle
filter estimates a different (fully nonlinear, non-Gaussian) posterior that
nothing in Spec §3 asks for, and would need its own resampling-degeneracy
diagnostics that M5's exit gate does not exercise.

**What would change this.** A domain with strongly non-Gaussian, non-linear
readouts where the stochastic EnKF's Gaussian analysis visibly biases the
posterior mean relative to a ground truth the oracle can check.

**Pinned by.** `tests/oracles/known_latent_trajectory.py` /
`tests/oracles/test_known_latent_trajectory.py`.

---

## ADR-025 — The ensemble smoother is a single backward cross-covariance pass over the recorded trajectory, not a re-run filter

**Status.** Accepted **Gap.** none — implementation choice, informed by C-3.8 (SPEC, "retrospective inference... is the correct setting") **Milestone.** M5

**What the framework leaves open.**
Core §3.8 and Spec §3.1 motivate *why* smoothing matters (the Gramian's sum
over `j ≥ k` is "the smoothing object"; "retrospective inference... is
therefore the correct setting for latent-variable identifiability") but
give no smoother algorithm — Spec §3 is entirely about the deterministic
Fisher-information Gramian, not a recursive estimator over noisy data.

**Decision.**
An ensemble smoother in the sense of Evensen & van Leeuwen: because every
ensemble member of the EnKF's forecast/analysis trajectory is a *full path*
(the same particle index `i` is tracked through every chain segment,
`chain.rollout` already preserving per-particle identity end to end via
`Ensemble.particles` rows), the cross-covariance between an **earlier**
time's forecast state and a **later** time's observation is directly an
empirical sample covariance across those same particles — no re-linearisation
and no backward recursion through Jacobians is needed. Concretely,
`smooth(trajectory, observations)`:

1. Runs the forward EnKF filter once (ADR-024), recording the forecast
   ensemble at every chain index.
2. For each earlier index `k` and each observation at a later index
   `j > k` taken from the *same* particle trajectories, computes the
   cross-covariance `P_{k,j} = Cov(s_k^f, H(s_j^f))` empirically over
   particles, forms the smoothing gain
   `K_{k,j} = P_{k,j} H'^T (H' P_j^f H'^T + R)^{-1}`, and updates each
   particle's *earlier* state `s_{k,i}^s = s_{k,i}^f + K_{k,j}(y_i - H(s_{j,i}^f))`
   using the same perturbed-observation convention as the filter.
3. When several later observations bear on the same `k`, they are applied
   sequentially in time order, each smoothing the result of the previous —
   an ensemble-smoother analogue of sequential filtering, rather than a
   single joint update, since Spec gives no joint-information form to
   target.

This is the direct payoff of ADR-024's choice to carry ensembles as full
per-particle trajectories rather than independent per-time samples: without
that, cross-time covariance would not be computable at all.

**Alternatives rejected.**
*A Rauch–Tung–Striebel (RTS) backward recursion through the Jacobian
`Φ_{k+1,k}`.* Rejected — reintroduces exactly the chained-Jacobian-product
machinery ADR-018 built JVP/VJP to avoid, for no accuracy benefit here since
the ensemble already carries the needed cross-covariance directly.
*Re-running the filter with the full future observation set folded into an
augmented state.* Rejected — equivalent in the linear-Gaussian case but far
more code for a toy-scale chain, and it obscures which observation is doing
the smoothing work for the "latent variable becomes inferred" demonstration
this milestone requires.

**What would change this.** A chain long enough that per-particle-path
memory becomes the storage bottleneck, at which point a genuine backward
recursion (RTS/EnKS with Jacobians) would trade storage for the reintroduced
Φ machinery.

**Pinned by.** `tests/oracles/test_known_latent_trajectory.py` (smoother
recovers a known latent trajectory within a stated interval; the previously
unobserved/dangerous latent direction becomes `Triage.INFERRED` once the
smoother's reduced posterior variance is fed back through M3's
`danger_triage`).

---

## ADR-026 — Innovation drift monitoring instantiates S-10's proposition with the standard NIS chi-squared consistency test

**Status.** Accepted **Gap.** S-10 (Spec §10 procedure is **PASS-C**; the proposition itself is SPEC) **Milestone.** M5

**What the framework leaves open.**
Spec §10 states, as a proposition already covered by Core §3.8, that "the
innovation sequence is a sufficient statistic for model drift," but the
section is otherwise `[Pass C]`: "To be written: innovation-based drift
detection with control limits; scheduled recalibration; continual learning
with forgetting protection; champion/challenger deployment..." — i.e. the
*proposition* is SPEC and directly implementable (compute the innovation
sequence), but the *detection procedure* (what statistic, what control
limit) has no formula anywhere in either document.

**Decision.**
Per CLAUDE.md §4 move 2 (Decide, with an ADR, when a gap must be filled to
make progress): docs/ROADMAP.md's M5 exit gate explicitly requires
"innovation monitor detects a planted drift," so refusing outright would
block a named exit-gate deliverable. The chosen procedure is the
**normalised innovation squared (NIS) chi-squared consistency test**
(Bar-Shalom, Li & Kirubarajan — the standard, textbook Kalman-filter
innovation monitor, not an invented one):

1. At each instrumented index `j`, compute the innovation
   `d_j = y_j - H_j(s̄_j^f)` and the innovation covariance
   `S_j = H_j' P_j^f H_j'^T + R_j` (both already available from the EnKF
   forecast of ADR-024), and the scalar
   `NIS_j = d_j^T S_j^{-1} d_j`.
2. Under a correctly-specified model, `NIS_j` is chi-squared distributed
   with `dim(y_j)` degrees of freedom (a standard, textbook fact — not a
   framework claim, and not something this repository invents).
3. **Drift monitor.** Over a sliding window of the last `w` innovations
   (`w` a declared parameter, default 10), the monitor reports the mean
   NIS against the chi-squared distribution's expected value and a
   two-sided control limit at a declared confidence level (default 95%,
   `scipy.stats.chi2`), flagging drift when the windowed mean exits the
   control limits. Both the raw `NIS_j` sequence and the windowed
   statistic are always returned together (never only the boolean flag),
   matching the reporting discipline ADR-017/ADR-020 already established
   for other declared conventions.

This is recorded as a Decide-ADR, not folded silently into "the" innovation
sequence, because a different confidence level or window would change which
drifts are caught — exactly the kind of invented number CLAUDE.md §4
requires to be visible and challengeable rather than buried in code.

**Alternatives rejected.**
*CUSUM on the innovation mean.* Rejected for the default — better at
detecting small sustained biases, but needs a reference/slack parameter
Spec gives no basis for either; the chi-squared test needs only the
already-available `S_j`, so it is the smaller addition. A CUSUM variant is
not precluded and could be added as a second declared monitor later.
*Refuse entirely (`NotSpecified("S-10", ...)`).* Rejected as the sole
response — legitimate for the *scheduled recalibration / champion-
challenger / rollback* portions of Spec §10, which this milestone does not
touch and which remain unimplemented anti-goals for now, but not for the
drift-detection procedure itself, since the exit gate requires a working
demonstration and a standard, citable statistical test exists to instantiate
the SPEC proposition without inventing framework.

**What would change this.** A concrete published control-limit convention
appearing in a future Spec revision, at which point this ADR is superseded
rather than silently edited.

**Pinned by.** `tests/oracles/test_known_drift.py` (a planted drift
must trip the monitor; a nominal, undrifted run must not).

---

## ADR-027 — Class B numerics: join threshold, Hill tail estimator, correlation-length estimator, subset-simulation conventions, and validation-ladder scope

**Status.** Accepted **Gap.** none — S-4.1 through S-4.6 are all SPEC; every item below is a declared numerical convention within a fully derived formula, not a derivation gap **Milestone.** M6

**What the framework leaves open.**
Spec §4 is unusual among the sections this repository has implemented so
far: every subsection is marked SPEC in `docs/COVERAGE.md` (S-4.1–S-4.6), so
nothing here is refused or filled by a Decide-ADR resolving an actual
derivation gap. What Spec §4 leaves open is purely numerical, the same kind
of thing ADR-017/019/020 already record for other SPEC sections: §4.2 says
the join threshold sits at "typically the 90th to 95th percentile," not a
single number; §4.3 requires a "measured" tail index but names no estimator;
§4.4 requires \(\ell_D\) "from the two-point autocorrelation of the driver
field" without naming a crossing convention or an error-bar procedure, and
separately flags that it is "biased low on short domains" without a
correction; §4.5's subset simulation requires "modified Metropolis sampling"
without fixing a proposal or an input-space convention; §4.6's rung 2
("independently measured... and not by this framework") is explicitly
someone else's estimator, not this module's, so there is nothing to
implement there beyond accepting it as data.

**Decision.**

1. **Join threshold (§4.2):** default `threshold_quantile = 0.95` (the upper
   end of Spec's own stated 90th–95th range, preferring more bulk data under
   the manifold prior and less extrapolation asked of the tail transfer),
   always a caller-overridable parameter, always reported alongside the
   count of samples above it and a *sensitivity curve* — the exceedance
   probability at the design point recomputed at several thresholds spanning
   at least the required factor-of-two range — never a single cached number
   (matching CLAUDE.md §8's "never hardcode a narrative number").
2. **Tail-index estimator (§4.3):** the **Hill estimator**
   (Hill, 1975) — `alpha_hat = k / sum(log(X_(i)/X_(k+1)))` over the top `k`
   order statistics — chosen over a full GPD MLE because Spec's own
   Proposition 4.1 is stated for a regularly-varying (Pareto-type) tail, and
   Hill is the standard, simplest consistent estimator for exactly that tail
   class, with a textbook, citable finite-sample error rate
   (`sqrt(k)`-consistent). Default `k = ceil(0.1 * n)` (top 10% of samples),
   reusing the same "sits in the 90th–95th percentile" convention as the
   join threshold rather than inventing an unrelated number — both are the
   same underlying question ("how much of the sample counts as tail").
   `tail_index_transfer(xi_a, beta) = beta * xi_a` is Spec §4.3's boxed
   formula applied directly, with no numerics of its own to declare.
3. **Correlation length (§4.4):** \(\ell_D\) is read off the empirical,
   FFT-based autocorrelation of a supplied 1-D driver field as the lag at
   which the ACF first drops below \(1/e\) (the standard correlation-length
   convention for a field with no cleaner closed form to target), scaled by
   the field's declared sample spacing. The error bar is a block-bootstrap
   over non-overlapping sub-segments of the field (resampling segments
   with replacement, recomputing the crossing lag each time) — chosen over
   an analytic formula because none is given and a resampling estimate
   needs no distributional assumption. The **domain-length-to-\(\ell_D\)
   ratio** is always reported alongside the estimate: Spec's own text says
   the estimate is "biased low on short domains," so a short-domain warning
   is only honest if it is computed, not asserted; a ratio below a declared
   ratio of 10 is flagged as unreliable in the result rather than silently
   trusted. **Scope:** only the isotropic case (a single scalar \(\ell_D\))
   is implemented; Spec §4.4's anisotropic, directional \(\ell_D\)
   requirement for banded structures is not — this repository's toy driver
   fields are 1-D, and a directional extension has no oracle here to check
   it against yet. This is a scope limitation stated openly, not a
   Specification gap, and it is recorded here rather than silently doing
   less than S-4.4 while still marking the row fully implemented.
4. **Dimensional reduction (Prop 4.2):** `n_eff(volume, correlation_length,
   process_zone_thickness)` implements the boxed formula exactly:
   `volume / correlation_length**3` when `correlation_length <=
   process_zone_thickness` (uncorrelated/bulk regime — the case Spec calls
   "no change in the size-effect exponent"), else `(volume /
   process_zone_thickness) / correlation_length**2` (the reduced, in-plane
   regime). No convention is invented here; the formula's own two branches
   are exactly Spec's two cases.
5. **Subset simulation (§4.5):** the standard Au & Beck (2001) formulation
   in *standard-normal input space*: the caller supplies a performance
   function `evaluate: R^n -> R` (typically a Rosenblatt/probability-
   integral-transform composition of the physical generative model), inputs
   are drawn i.i.d. standard normal at level 0, and each subsequent level
   runs one Metropolis chain per surviving seed with a symmetric Gaussian
   proposal (default `proposal_std = 1.0`, since the input space is already
   standardised) accepting a proposal exactly when it both satisfies the
   current level's conditional-exceedance region and is accepted under the
   standard-normal density ratio (trivial here since a symmetric proposal
   about a standard-normal target reduces the ratio to 1 whenever the
   region condition holds — the acceptance rule Spec's "modified Metropolis"
   name refers to). Default `conditional_probability = 0.1`, `n_per_level =
   500` — Spec's own worked cost example ("`4 x 500` evaluations for `P_f ~
   10^-4`").
6. **Validation ladder (§4.6):** rungs 1, 3, and 4 are computed by this
   module (bulk-distribution residual; fractography residual, which sets a
   `voids_construction` flag when it fails at a stated tolerance per Spec's
   explicit "the entire construction is void" requirement; volume-scaling-
   exponent residual). **Rung 2 is not computed here at all** — Spec's own
   text says the defect-population tail is "independently measured by
   established characterisation methodology... and not by this framework,"
   so `classb.py` only accepts it as a caller-supplied value with its own
   error bar, exactly like `ADR-021`'s treatment of matched-pair campaign
   data as something the module consumes rather than generates.

**Alternatives rejected.**
*A GPD maximum-likelihood tail fit instead of Hill.* Rejected as the
default — more general (covers bounded and light tails too) but Spec §4.3's
own construction is explicitly regularly-varying/Pareto-type, and Hill is
the simpler, standard estimator for exactly that case; a GPD fit remains
available as `scipy.stats.genpareto` for a caller who needs the general
case, but is not what `tail_index_transfer`'s companion estimator uses by
default.
*An analytic correlation-length error bar (e.g. from a fitted correlation
model's own confidence interval).* Rejected — would require assuming a
parametric form (exponential, Gaussian) for the autocorrelation that Spec
does not require and a domain need not satisfy; block bootstrap is
assumption-free at the cost of needing several sub-segments.
*Full anisotropic \(\ell_D\) now.* Deferred, not rejected — see point 3;
revisit when a domain or oracle needs a directional driver field.

**What would change this.** A domain whose driver field is genuinely
multi-dimensional and anisotropic (Spec §4.4's banded-structure case) would
force the anisotropic extension; a domain whose defect tail is not
regularly varying would force a GPD (or other) fit in place of Hill.

**Pinned by.** `tests/oracles/test_known_tail.py` (Hill + transfer recovers
`beta * xi_a` across four `(alpha, beta)` pairs, docs/ROADMAP.md M6 exit
gate), `tests/oracles/test_known_ranking_inversion.py` (Prop 4.2's
dimensional reduction reproducing a specimen-thickness ranking inversion),
and `tests/test_classb_subset_simulation.py` (subset simulation recovers a
known exact exceedance probability at a fraction of direct-sampling cost).

---

## ADR-028 — Conformance is a reporting-completeness gate, not a numeric pass/fail; a dedicated `ConformanceNotMet` distinct from `NotSpecified`

**Status.** Accepted **Gap.** none — S-9.1/S-9.2/S-9.5 are SPEC; S-9.4 (falsification thresholds) is PASS-D and is refused, not answered, by this ADR **Milestone.** M7

**What the framework leaves open.**
Spec §9.1's level table (OMI-0/1/2) states *what must be reported* at each
level ("rollout-length error curve reported," "sufficiency test run and
reported," "‖𝒟_λ‖ wherever scale bridging occurs") but never a numeric
threshold any of these must clear — thresholds are a separate, explicitly
unspecified concern (S-9.4: "Each criterion... requires a stated tolerance
or a procedure for setting one per application. To be written."). Spec also
never says how a conformance module should be structured: whether it
recomputes every diagnostic itself, what exception a failed claim raises, or
how "wherever scale bridging occurs" is decided for a chain that, in this
repository, never actually executes a cross-scale operator.

**Decision.**

1. **Conformance is a completeness gate.** `generate_report` checks whether
   each level's required diagnostics are *present*, not whether any
   diagnostic's value clears a threshold. This reads Spec §9.1's table
   literally: every OMI-0/1/2 line item is phrased as "reported," "run and
   reported," or "declared" — never "below X." Numeric falsification
   thresholds are S-9.4's separate, PASS-D concern and remain out of scope
   here; a caller wanting threshold-gated pass/fail composes it on top of a
   `ConformanceReport`'s own residuals, exactly as CLAUDE.md §4 prefers
   (declare the number *and* the diagnostics that let a reader judge it,
   rather than this module inventing a threshold Spec does not supply).
2. **`ConformanceInputs` is a plain, caller-supplied bundle — never
   recomputed.** `conformance.py` does not re-run `sufficiency_deficit`,
   `danger_triage`, `semigroup_residual`, or anything else; it only checks
   that the caller has *already* produced each diagnostic (each field is
   `Optional`, `None` meaning "not produced"). This mirrors ADR-021's
   treatment of campaign data: the module consumes already-collected
   evidence, it does not generate it. The alternative — conformance.py
   owning the recomputation of every diagnostic across arbitrary chains —
   would duplicate every other module's API surface for no benefit, since
   the caller (a domain's own test/demonstration code) is exactly where
   that diagnostic was already computed for its own oracle tests.
3. **A dedicated `ConformanceNotMet` exception**, distinct from
   `omi.gaps.NotSpecified`. A failed level claim is not a Specification
   gap — it is "this chain has not yet produced the required evidence,"
   which is a different failure mode from "the Specification does not say
   how to do this." Raising `NotSpecified` for a missing diagnostic would
   misfile an evidentiary gap as a derivation gap and would corrupt the gap
   registry's `known_gap_ids()` bookkeeping (`gaps.py`'s tests assert every
   `NotSpecified` cites a live `COVERAGE.md` row; a conformance failure has
   no such row to cite).
4. **Closure defect is vacuously satisfied when no scale bridging is
   actually executed.** Both domains' `scale_structure` declarations
   describe a *fuller* eventual scope (flagship's Tier II, contrast's
   pack-level tier) than either chain actually runs at M1–M7 (Tier
   II/pack-level are anti-goals, never executed). `ConformanceInputs`
   therefore carries a `scale_bridging_occurs: bool` the caller sets
   describing the chain *as actually built*, not the domain's textual
   aspiration; the closure-defect requirement is satisfied whenever this is
   `False`, and requires a supplied `closure_defect` value (refused per S-6,
   an anti-goal — `docs/DECISIONS.md`'s anti-goal list) only when `True`.
   This is why neither domain is blocked on closure defect at M7: neither
   chain crosses a scale in the code that actually runs.
5. **Structural OMI-0 items** ("typed chain," "grouped splits enforced")
   are satisfied by construction rather than computed: `State`/`Ensemble`
   are typed dataclasses throughout (checked by `mypy --strict` in CI, not
   re-checked at report time), and no random-split code path exists
   anywhere in this repository (CLAUDE.md §5 invariant 6) — there being
   nothing to disprove, `ConformanceInputs.grouped_splits_enforced`
   defaults to `True` and is not computed from data, since there is no data
   loader yet to compute it from.
6. **New computational content lives in `conformance.py` itself**: the
   rollout-length error curve (a direct generalisation of M2's error-
   compounding demonstration to arbitrary chains, satisfying OMI-0's own
   line item) and the S-9.5 calibration diagnostics (PIT values, ensemble
   CRPS via the standard energy-score estimator, empirical interval
   coverage) — these have no existing home in an earlier module and their
   formulas are standard, named, textbook constructions Spec explicitly
   requires by name, not an invented convention.

**Alternatives rejected.**
*Conformance re-runs every diagnostic from a bare chain.* Rejected — see
point 2; also would force `conformance.py` to import every domain-neutral
module's full API just to orchestrate it, inverting the dependency
direction CLAUDE.md §6's architecture map implies (`conformance.py` sits
above the other modules, consuming their outputs).
*Numeric thresholds baked into level requirements (e.g. "deficit < 0.1").*
Rejected — exactly the invented-narrative-number problem CLAUDE.md §4 and
§8 warn against; S-9.4 is explicit that thresholds need a stated procedure
this repository does not have.
*Reusing `NotSpecified` for an unmet conformance requirement.* Rejected —
see point 3.

**What would change this.** A future milestone building genuine Tier
II/pack-level execution for either domain would flip
`scale_bridging_occurs` to `True` for that chain, at which point OMI-1
requires either a real closure-defect measurement (blocked — S-6 remains an
anti-goal) or a further ADR revisiting whether closure defect can be
partially bounded some other way.

**Pinned by.** `tests/test_conformance.py` (level-table mechanics,
`ConformanceNotMet` with a specific unmet list), `tests/test_conformance_flagship.py`
(OMI-1 achieved), `tests/test_conformance_contrast.py` (OMI-0 achieved, OMI-1
honestly blocked on the sufficiency test not yet run for this domain).

---

## ADR-029 — Neural operators live in a new `src/omi/learning.py`; a DeepONet-style branch/trunk network, implemented entirely in numpy with no torch dependency

**Status.** Accepted **Gap.** none — S-2.1, S-2.3, S-2.4 are SPEC; S-2.5–2.7 remain PASS-B and are refused, not touched here **Milestone.** M8

**What the framework leaves open.**
Spec §2.1 names DeepONet, FNO, and graph-based operators as the approximation
class but gives no architecture for this repository's finite-dimensional,
non-grid, non-graph toy states; CLAUDE.md's architecture map (§6) predates
M8 and reserves no filename for it; and CLAUDE.md §8's standing convention —
"torch optional with a numpy fallback that gives identical results. Never
import torch at module scope in `src/omi/`" — describes a policy for *if*
torch is used, not a requirement that a learned operator must use it at all.

**Decision.**

1. **New module, `src/omi/learning.py`.** `operators.py` holds the
   `EvolutionOperator` abstraction and its generic, domain-neutral lift/
   Lipschitz machinery; a full neural-operator implementation (network
   architecture, training loop, noise injection, spectral control) is
   substantial enough, and specific enough to *this* interchangeable
   approximation class (CLAUDE.md §2: "the neural operators are not the
   point... one interchangeable approximation class"), to warrant its own
   file rather than growing `operators.py` past its own abstraction.
2. **Architecture: DeepONet's branch/trunk decomposition, adapted to a
   finite output dimension.** A branch network encodes the input
   ``(state, control, dt)`` into a latent code `b in R^p`; a trunk network
   encodes each of the `n` *output component indices* (one-hot, since
   there is no continuous query domain here) into a latent code, forming a
   fixed `T in R^{n x p}` (recomputed from current trunk weights each
   call, since weights change during training); the output is
   `T @ b + bias`. This is the standard branch/trunk bilinear structure
   applied to a discrete, finite set of "sensor" outputs rather than a
   continuous function space — a legitimate, commonly-used DeepONet
   variant, not FNO (grid-structured field-to-field maps do not fit this
   repository's toy vector states, which is why FNO is not attempted here).
3. **No torch anywhere in this milestone's code.** The network, its
   forward pass, its exact Jacobian (via chained per-layer Jacobians —
   `diag(tanh'(z)) @ W` composed layer by layer, exact because the network
   is a fixed, small, differentiable function, not an approximation of one),
   and its training (hand-derived reverse-mode backprop, plain numpy) are
   implemented once, in numpy, with no second implementation to keep
   consistent. This satisfies CLAUDE.md §8's convention trivially rather
   than by comparison: there is nothing to fall back *from*, "torch
   optional" is honoured because torch is never required, and "identical
   results" needs no cross-backend equivalence test because only one
   backend exists. A torch-accelerated training backend remains a
   legitimate future addition (e.g. for a domain whose networks outgrow
   hand-rolled backprop), but this repository's toy-scale networks
   (branch/trunk each a two-hidden-layer MLP, tens to low hundreds of
   parameters) do not need it, and this environment cannot install torch to
   test it (no network at runtime) — writing an untested torch path would
   violate CLAUDE.md §10's "prefer a small correct module... to a large one
   without."
4. **Training procedure (Spec §2.3/§2.4).** Multi-step ("pushforward")
   training with truncated backpropagation through the unrolled network's
   own composition, so error is trained
   against rollout length, not one-step accuracy alone (Spec §2.4's own
   requirement, echoing CLAUDE.md §5 invariant 7); Gaussian noise injection
   on the training inputs at each step (Spec §2.4); a semigroup-consistency
   penalty reusing `operators.semigroup_residual` directly against the
   *learned* operator during training, not just at evaluation time (Spec
   §2.3 names this as a training-objective term, not only a diagnostic);
   and post-step spectral-norm capping on every weight matrix (Spec §2.4's
   "spectral normalisation or explicit Lipschitz control, tuned per
   segment" — implemented as a hard cap applied after each gradient step,
   the simplest faithful reading, with the cap itself a declared,
   overridable parameter per CLAUDE.md §4/§8's discipline against invented
   uncited numbers).
5. **Manifold projection (Spec §2.4) is not implemented.** Spec marks this
   "the strongest practical justification for manifold learning," but no
   manifold-learning machinery exists anywhere in this repository (it is
   not scheduled by docs/ROADMAP.md at any milestone) — implementing it
   now would be inventing a manifold-learning submodule with no oracle to
   check it against. Recorded as a stated scope limitation, not a silent
   omission.

**Alternatives rejected.**
*FNO instead of / alongside DeepONet.* Rejected — FNO targets grid-
structured field-to-field maps (Fourier modes over a spatial grid); neither
domain's toy state has that structure, and forcing a grid decomposition
onto a 5-7 dimensional flat vector would be a costume, not an
implementation.
*A torch-first implementation with a numpy fallback reimplementing the same
math.* Rejected — see point 3; two independent implementations of the same
forward/backward math is exactly the fragility CLAUDE.md §8's "identical
results" requirement exists to guard against, and this repository has no
way to test the torch half.
*Growing `operators.py` in place.* Rejected — see point 1.

**What would change this.** A domain whose state is genuinely grid- or
graph-structured (a real Tier II field, an actual mesh) would justify FNO or
a graph network; a network large enough that hand-rolled numpy backprop
becomes the bottleneck would justify an optional torch training backend,
added alongside (not replacing) the numpy forward pass every
`EvolutionOperator.step` call still uses.

**Pinned by.** `tests/test_learning_gradient_check.py` (analytic gradients
match finite-difference gradients, validating the hand-rolled backprop
itself), `tests/test_learning_oracle.py` (a trained `DeepONetOperator`
passes the same oracle checks as its analytic counterpart, per
docs/ROADMAP.md M8's exit gate).

---

## ADR-030 — `constraints.py` implements four of Spec §2.2's five hard-constraint categories; thermodynamic admissibility (GENERIC/port-Hamiltonian) is out of scope

**Status.** Accepted **Gap.** none — S-2.2 is SPEC; the *categories* are named, the specific parameterisation of each is an implementation choice **Milestone.** M8

**What the framework leaves open.**
Spec §2.2 names five categories of hard structural constraint (symmetry,
thermodynamic admissibility, range constraints, monotonicity, conservation)
and requires each be architecture, never a loss penalty, but gives no
specific parameterisation for any of them — "simplex parameterisation,"
"positivity," "monotone parameterisation or non-negative increments," and
"mass balance" are all named by their mathematical *shape*, not by a
formula.

**Decision.**
`constraints.py` implements four of the five categories as literal,
differentiable-where-needed reparameterisations, each a function
`unconstrained parameters -> constrained output`, so that violating the
constraint is not representable at all, not merely discouraged:

1. **Range/positivity** — `softplus` (`log(1+e^x)`), smooth, exactly
   positive, with an exact analytic derivative for the Jacobian chain.
2. **Range/simplex (fractions)** — `softmax`, exactly summing to one and
   componentwise non-negative by construction.
3. **Monotonicity** — cumulative sum of `softplus` increments: the
   ``i``-th output is ``initial + sum_{k<=i} softplus(delta_k)``, which is
   non-decreasing by construction regardless of the unconstrained
   ``delta``.
4. **Conservation** — an affine projection onto the hyperplane
   ``{x : sum(x) = total}``: ``x - (sum(x) - total) / n``, the closest point
   on that hyperplane in Euclidean distance, so any unconstrained vector is
   projected to one that exactly conserves the declared total.

**Symmetry** (equivariant architectures, permutation invariance) is declared
in the module but not given a concrete general-purpose layer here: an
equivariant layer's correct form depends on *which* group acts on *which*
state components, which is domain content (CLAUDE.md §5 invariant 3
forbids exactly this kind of domain-specific decision inside `src/omi/`).
A domain that needs symmetry declares its own equivariant layer in
`omi_domains/*/`, built from primitives here if useful (e.g. the
conservation projection is itself permutation-equivariant already, so it
transfers unmodified).

**Thermodynamic admissibility (GENERIC/port-Hamiltonian structure) is not
implemented.** Separating reversible and irreversible dynamics with a
guaranteed non-negative dissipation term is a substantially larger
undertaking than the other four categories — it requires committing to a
specific decomposition of the *learned operator's own dynamics* (not just a
reparameterisation of its output), which in turn requires deciding how a
GENERIC/port-Hamiltonian structure composes with the branch/trunk
architecture of ADR-029, a design question neither Spec nor Core resolves
and no oracle in this repository yet tests. Recorded here as a stated scope
limitation (docs/COVERAGE.md updated accordingly) rather than a rushed,
unverified implementation.

**Alternatives rejected.**
*Soft penalty terms added to the training loss instead of architecture.*
Rejected — this is precisely what Spec §2.2 says not to do ("a penalty
enforces physics where the training data live; an optimiser searching for
an optimal route finds precisely where enforcement is weak"), and
CLAUDE.md §5 invariant 5 states it as a non-negotiable.
*Clipping instead of a smooth reparameterisation for positivity/
monotonicity.* Rejected — clipping has a zero (or undefined) gradient at
the boundary, which would silently kill gradient-based training near the
constraint; `softplus` is smooth and strictly positive everywhere with a
well-defined derivative, needed for ADR-029's backprop to flow through it.

**What would change this.** A domain declaring a genuine symmetry group
acting on its state, at which point that domain's own equivariant layer
would be built (and, if it turns out generic, promoted here); a milestone
that specifically targets thermodynamic structure, with its own ADR
resolving how GENERIC/port-Hamiltonian composes with whatever operator
architecture is current at that time.

**Pinned by.** `tests/test_constraints.py` (each layer's constraint holds
by construction, checked off-manifold with adversarial out-of-range inputs
— docs/ROADMAP.md M8's exit gate: "constraint satisfaction holds
off-manifold").

---

## ADR-031 — Reachability certificates are restricted to linear functionals `Φ(s) = w·s`, giving an exact halfspace-projection nearest-reachable-state

**Status.** Accepted **Gap.** S-7.1 (Decide: the certificate/`Φ` *construction* and the nearest-reachable-state computation, both PASS-B — "to be written") **Milestone.** M9

**What the framework leaves open.**
Spec §7.1 gives the certificate's verification inequality exactly —
`Φ(s_{k+1}) ≤ Φ(s_k) + c(u_k)`, any target beyond the accumulated bound is
provably unreachable — and names candidate sources for `Φ` ("conservation
balances, monotone accumulations, equilibrium-limited fractions"), but its
own text says the practical hierarchy for *constructing or selecting* `Φ`,
and the nearest-reachable-state computation, are both `[Pass B]`, "to be
written."

**Decision.**
`Φ` is restricted to **linear functionals of the flat state vector**,
`Φ(s) = w · s` for a declared weight vector `w` (`ReachabilityCertificate`).
This is not an arbitrary restriction: every candidate Spec §7.1 itself
names is naturally linear in the state's own flat-array representation —
a conservation balance is a weighted sum of components summing to a
constant; a monotone accumulation (CLAUDE.md §3's `z`-slot driving
measures) is itself already one component of the state, i.e. `w` a one-hot
vector. Given a linear `Φ` and a declared per-step worst-case increment
`c_max_k` (itself domain-declared — Spec never gives a formula for
computing `sup_u c(u)` over `𝒰_adm` either, so this is accepted as an input,
not derived), the boxed inequality accumulates exactly:
`achievable_bound = Φ(s_0) + Σ_k c_max_k`, and `Φ(s_target) > achievable_bound`
is a sound, exact non-reachability certificate — no approximation beyond
what the caller already declared. The **nearest reachable state** is then
the exact Euclidean projection onto the halfspace `{s : w·s ≤ bound}`:
`s_target - ((w·s_target - bound) / ‖w‖²) · w` — closed-form, because the
constraint set (post-restriction) is a halfspace, not an approximation of
one.

**Alternatives rejected.**
*A general nonlinear `Φ`, with nearest-reachable-state found by numerical
optimisation.* Rejected — Spec's own candidate list is linear in every
example given, and a general nonlinear projection would need an iterative
solver with its own convergence caveats, adding machinery Spec does not
ask for and this milestone's oracle does not need.
*Learned reachable-set over-approximation (interval/zonotope/ellipsoidal),
per Spec's own "practical hierarchy."* Rejected for now — Spec explicitly
ranks this below invariant certificates ("sound, necessary conditions
only") in soundness, and Spec's own text says learned reachable sets "are
unsound and cannot discharge" the output contract; the hierarchy's
intermediate rungs are a real future extension, not required to satisfy
the SPEC-given inequality itself.

**What would change this.** A domain whose natural invariant is
genuinely nonlinear (e.g. a quadratic energy bound) would force a more
general `Φ` and a corresponding (likely iterative) nearest-point
computation.

**Pinned by.** `tests/oracles/test_known_unreachability.py` (docs/ROADMAP.md
M9 exit gate: "certificate fires exactly outside the bound").

---

## ADR-032 — Apparatus parameterisation is a structural wrapper: inverse design never receives a raw `Control`

**Status.** Accepted **Gap.** none — the requirement itself is SPEC; the wrapper shape is an implementation choice **Milestone.** M9

**What the framework leaves open.**
Spec §7.2's requirement is unconditional and already SPEC: "Inverse design
MUST be parameterised in apparatus settings, never in desired driving
paths. Optimising over idealised histories produces recipes the apparatus
cannot execute." COVERAGE.md's own note calls this "enforceable as an
architectural invariant," but Spec gives no shape for how that enforcement
is expressed in code — only the *general* constraint-manifold construction
(rate limits, mixed-integer handling) is `[Pass C]`.

**Decision.**
`ApparatusParameterization` wraps a domain-declared
`to_control: apparatus parameters (a small FloatArray) -> Control` together
with a declared admissible box (`𝒰_adm`, per-parameter `(low, high)`
bounds — the simplest non-trivial case of Spec §7.2's "structured
low-dimensional set"; a full constraint-manifold construction for coupled,
rate-limited apparatus geometry remains `[Pass C]` and is not attempted).
Every function in `inverse.py` that searches over controls — candidate
generation, the decision layer — takes an `ApparatusParameterization` and
an apparatus-parameter array, **never** a `Control` directly; a `Control`
only ever comes out of `to_control`, never goes in. This makes Spec §7.2's
requirement structurally true of this module's API, the same discipline
ADR-029 (M8) used for grouped splits: the violation is not merely
discouraged, the calling convention makes it inexpressible.

**Alternatives rejected.**
*Accepting an arbitrary `Control` in the optimiser and relying on a
docstring/convention not to construct one directly from an idealised
history.* Rejected — this is exactly the failure mode Spec warns against,
and CLAUDE.md's general preference (ADR-029) is for structural
impossibility over convention wherever the two are both available.

**What would change this.** A domain whose apparatus has genuine rate
limits or discrete/mixed-integer settings would extend
`ApparatusParameterization` with those constraints; Spec's own text says
"scenario enumeration is usually sufficient" for the discrete case, which
would layer on top of (not replace) the continuous box declared here.

**Pinned by.** `tests/test_inverse_apparatus_parameterisation.py`.

---

## ADR-033 — Decision layer: probability of conformance and CVaR by their standard formulas; OQ-4's infeasibility diagnosis as an ordered three-way check

**Status.** Accepted **Gap.** S-7.3 (Decide: PASS-C, "selects within the degenerate solution set... but does not resolve" how) **Milestone.** M9

**What the framework leaves open.**
Spec §7.3 names the objectives ("optimise probability of conformance...
not expected value," "carry asymmetric costs," "connect CVaR to the
conformance and defect-rate language") without formulas, and separately
poses OQ-4 (docs/COVERAGE.md Part IV): when the feasible set is empty,
which term is binding — aleatoric spread, `𝒰_adm` (apparatus limits), or
the trust region (surrogate not calibrated there)?

**Decision.**

1. **Probability of conformance** is the plain empirical fraction of a
   candidate's predictive ensemble landing inside the declared
   specification window — a direct Monte Carlo estimate reusing this
   repository's ensemble machinery (`omi.state.Ensemble`), not an invented
   convention.
2. **CVaR** is the standard formula (Rockafellar & Uryasev 2000): the mean
   of the worst `alpha`-fraction tail of a *loss* (higher = worse) —
   `mean(losses[losses >= quantile(losses, 1-alpha)])`. Callers needing a
   "worse = lower" quantity (e.g. a response that must stay *above* a
   floor) negate it first, the standard convention, not a new one.
3. **Asymmetric cost** is left as a plain piecewise-linear function of
   signed deviation from a target, with independently declared per-side
   slopes — Spec names the *requirement* ("asymmetric costs... differ by
   orders of magnitude") not a formula, and a piecewise-linear cost is the
   simplest object that is asymmetric by construction and needs no
   further justification.
4. **OQ-4's answer**: `diagnose_infeasibility` checks the three candidate
   binding terms in a fixed order, each a strictly necessary condition for
   the ones after it to even be checkable meaningfully:
   (a) **trust region** — does the specification window overlap the
   surrogate's declared validated domain at all? If not, nothing else
   matters: the model was never asked to extrapolate and answering "the
   controller can't get there" is not the same claim as "the model doesn't
   know," and Spec's own list keeps the two textually distinct.
   (b) **control / `𝒰_adm`** — within the trust-region overlap, does *any*
   achievable mean response land inside the specification window at all
   (ignoring aleatoric spread entirely, i.e. the noise-free question)? If
   not, the apparatus itself cannot reach the window regardless of
   incoming variation.
   (c) **aleatoric** — if an achievable mean does land inside the window,
   is the incoming population's spread nonetheless too wide to keep a
   declared coverage fraction inside it? This is the only one of the three
   whose remedy is "reduce incoming variation," per OQ-4's own framing.
   This ordering is a declared convention (an ADR, not a derivation):
   Spec poses the question but not the priority among the three when more
   than one might technically apply; checking trust region first and
   control second reflects that a modelling-domain violation and an
   apparatus-capability violation are prior, logically, to a statement
   about noise.

**Alternatives rejected.**
*Checking all three simultaneously and reporting a set rather than a single
binding term.* Rejected as the *default* — OQ-4 asks "which term," singular,
and a caller wanting the full diagnostic detail still has every intermediate
quantity (`achievable_mean_range`, `aleatoric_std`, the trust region and
specification window themselves) available in the result, not hidden by
the single-term summary.
*A coverage fraction of exactly 100% for the aleatoric check (i.e. the
whole distribution must fit).* Rejected — CLAUDE.md's own conventions
prefer a declared, parameterised coverage level (default matches the
"±3σ / 99.7%"-style, or a caller-declared fraction) over an invented exact
100%, which no real distribution with unbounded support (e.g. Gaussian
aleatoric noise) could ever satisfy.

**What would change this.** A domain where two binding terms are
genuinely simultaneous and the priority ordering hides real information —
at which point the full three-way breakdown (already computed internally)
should become the primary return value instead of a summary label.

**Pinned by.** `tests/oracles/test_known_infeasible_specification.py`
(docs/ROADMAP.md M9 exit gate: "the binding term is correctly identified");
OQ-4 marked answered in docs/COVERAGE.md Part IV.

---

## ADR-034 — Core §7.2's table maps to six of Core §4's seven items, not seven of seven; `interface.diff()` gains a structural check for invariants

**Status.** Accepted, supersedes ADR-003's pinning test **Gap.** C-4 (SPEC)
**Milestone.** Phase 1 (`build/REVIEW-EXTRACT.md` §3 finding)

**What the framework leaves open.**
Core §4 declares seven interface items. Core §7.2's own comparison table
(flagship vs. contrast) has seven *rows*, and ADR-003's pinning test read
"seven rows" as "seven items" and asserted `differing >= 6` against
`interface.diff()`'s seven dict keys directly. The review extraction
(`build/REVIEW-EXTRACT.md` §3) found this conflates two different lists:
Core §7.2's seven rows are "Erasure operators," "Observation suite,"
"Dominant slot," "Control axis," "Tier structure," "Class B," and "Nonlocal
slot ν" — and the last two both name the *state schema* (Core §4 item 1),
while item 6 (invariants) has no row in Core §7.2's table at all. So Core
§7.2's seven rows test exactly **six** of Core §4's seven items, not seven,
and the old pinning test's "6 of 7" threshold passed for the wrong reason:
it happened to also count `invariants` (item 6, untested by Core §7.2) as
differing, because the two domains name their invariants after different
physics. Two domains that named their invariants identically in *kind* but
differently in *string* would still have passed the old test — on an item
Core §7.2 never claims is inverted — which is exactly the kind of
naming-vs-structure conflation this repo's own gap discipline exists to
catch.

**Decision.**
Two changes, both in `src/omi/interface.py`:

1. `classify_invariant(name: str) -> InvariantKind` classifies a declared
   invariant's name as `CONSERVATION` or `MONOTONICITY` by keyword
   (`"conserv"` / `"monoton"` substrings), refusing (`ValueError`, not
   `NotSpecified` — this is a naming-convention check, not a Specification
   gap) on a name matching neither. `diff()` gains an additional key,
   `"invariants_structural"`, comparing the *sorted multiset of kinds*
   rather than the literal declared strings.
2. `tests/test_interface_diff.py` now asserts against Core §7.2's six named
   items **by name** (`erasure_inventory`, `observation_suite`,
   `state_schema`, `control_space`, `scale_structure`, `readout_catalogue`),
   via an explicit `CORE_7_2_ROW_TO_INTERFACE_ITEM` mapping table pinned by
   its own test, rather than a bare `differing >= 6` count over whatever
   keys `diff()` happens to return. A separate test demonstrates the case
   this ADR exists to catch directly: flagship and contrast's `invariants`
   literal-string diff is `True` (different names), but
   `invariants_structural` is `False` — both domains declare exactly one
   conservation law and one monotonicity constraint.

**Alternatives rejected.**
*Changing `InstantiationDeclaration.invariants`'s type from `tuple[str, ...]`
to a structured `tuple[(str, InvariantKind), ...]`.* Rejected for this ADR's
scope — that is a breaking change to ADR-016's declaration shape used by
both domains and by every existing consumer of `InstantiationDeclaration`,
and the task at hand only requires the *comparison* to be structural, not
the storage. `classify_invariant` derives the kind from the existing string
at diff time; if a future domain's invariant naming can't be classified by
keyword, that failure is the signal to revisit storage, not a reason to
change it pre-emptively.
*Leaving the pinning test as a bare count and just fixing the `invariants`
conflation by excluding it from the count.* Rejected — a bare count over an
unnamed subset of keys is exactly the failure mode here; naming the six
items explicitly is what makes the test re-derivable from Core §7.2's table
by inspection, and what stops a future field addition to
`InstantiationDeclaration` from silently changing what "6 of 7" means.

**What would change this.** A `[Pass A]` resolution of Core Appendix B (the
general↔domain glossary, per `docs/COVERAGE.md`'s note) that gives
invariants a richer typed vocabulary than "conservation or monotonicity" —
at which point `InvariantKind` gains members and `classify_invariant`'s
keyword heuristic is revisited.

**Pinned by.** `tests/test_interface_diff.py` —
`test_core_7_2s_seven_rows_cover_exactly_six_distinct_interface_items`,
`test_flagship_and_contrast_differ_on_exactly_the_six_items_core_7_2_names`,
`test_invariants_literal_diff_and_structural_diff_disagree`.

---

## ADR-035 — Tier I½: a bounded, structurally-fenced lift of the Tier II anti-goal, for one scalar-geometry, one-loading-mode Class B readout

**Status.** Accepted **Gap.** C-2.4 / C-3.6 (SPEC) — implementation choice,
partially lifting CLAUDE.md §9's Tier II anti-goal under a bounded,
structurally-enforced fence, not filling a Specification derivation gap
**Milestone.** Phase 2 (post-M9 remediation)

**What the framework leaves open.**
Core §3.6's Class B claim is that failure is governed by a driver field
coupling two tiers — material (Tier I) and component (Tier II) — through a
process-zone *volume* argument (`N_eff`'s dimensional reduction, Proposition
4.2). Through M9, every Class B readout in this repository has been Type-0
(no geometry at all): the contrast domain's `DendriteRisk` and the oracle
constructions in `tests/oracles/`. Core §7.1's own table declares the
flagship's bend angle as `Type-2, Class B` — the concrete case Class B's
volume argument is meant to be exercised on — but no Type-2 readout has ever
existed, because CLAUDE.md §9 bans "Tier II boundary value problems and FE²
coupling" outright, and a full component-scale solver is exactly that. The
result, confirmed in Phase 1's coverage-verification pass
(`docs/COVERAGE.md`, C-3.6 and S-4.1/S-4.2/S-4.4/S-4.6): ten of `classb.py`'s
sixteen public symbols have no domain test and no oracle test at all — the
machinery Core §3.6 is most distinctive about has only ever been exercised
against hand-supplied numbers, never a real driver field.

**Decision.**
**Tier I½** is a scoped exception to CLAUDE.md §9's Tier II anti-goal,
covering exactly: a Type-1 constitutive operator composed with **one scalar
geometry parameter and one loading mode**, evaluated by **through-thickness
quadrature**, returning a response *and* a process-zone volume. Nothing
else. Specifically, and enforced structurally rather than by convention:

- **No meshes, element assembly, equilibrium iteration, or solver of any
  kind.** Through-thickness quadrature is direct evaluation of the already-
  exact Type-1 operator at a handful of points along one axis, not
  discretisation of a boundary-value problem.
- **No contact or friction.**
- **Exactly one loading mode** (bending, via a linear through-thickness
  strain profile) — not a general loading-mode catalogue.
- **Geometry no richer than a thickness and a curvature.** Enforced by
  making the Type-2 geometry argument (`omi.readouts.Type2Geometry`) a
  frozen dataclass of exactly two scalar fields. If a domain ever needs to
  pass this class a mesh, an element connectivity table, or anything that
  is not a bare float, the fence has been breached — that is the signal to
  revisit this ADR, not to extend `Type2Geometry`.
- **Never called "Tier II" in code, docstrings, or reports.** "Tier I½"
  names exactly this bounded case; "Tier II" continues to name the banned,
  unbounded one, and the two must not be conflated by naming.

`src/omi/readouts.py` gains the domain-neutral half: `Type2Geometry` (the
two-scalar dataclass above) and `ComponentReadout` (ABC declaring
`evaluate(operator: ConstitutiveOperator, geometry: Type2Geometry) ->
tuple[FloatArray, float]` — response *and* process-zone volume, both
returned, never one hidden, since Core §3.6's claim is specifically that the
volume couples the tiers). `ReadoutType.TYPE_2` — declared at M1 but never
referenced outside its own definition until now — becomes each readout
base's own declared `readout_type` class attribute
(`FunctionalReadout.readout_type = ReadoutType.TYPE_0`,
`ConstitutiveReadout.readout_type = ReadoutType.TYPE_1`,
`ComponentReadout.readout_type = ReadoutType.TYPE_2`), so the enum is
actually load-bearing rather than declarative-only.
`src/omi_domains/flagship/readouts.py` gains the concrete instance,
`BendAngle(ComponentReadout)`: through-thickness quadrature of the existing
`HardnessConstitutiveOperator` under a linear strain profile
`ε(z) = curvature · z`, the outer-fibre (`z = ±thickness/2`) response as the
returned value, and the thickness-fraction where the local response exceeds
a declared threshold as the process-zone volume.

**Alternatives rejected.**
*Leave Tier II a complete anti-goal; accept that Class B's volume argument
stays untested on any geometry-bearing readout.* Rejected — Core §3.6's most
distinctive machinery (S-4.1 through S-4.6) would remain permanently
exercised only by hand-supplied numbers and a Type-0 contrast readout with
no geometry parameter at all, on a domain (flagship) that explicitly
declares a Type-2/Class-B response in Core §7.1's own table. That is a much
larger and more consequential gap than the bounded risk Tier I½ takes on.
*Implement a genuine (even simplified) finite-element solver for the
flagship.* Rejected outright — this is exactly Tier II/FE² coupling, and
CLAUDE.md §9's ban on it stands unchanged for anything beyond the bounded
case named above.
*Allow richer geometry (e.g. a width, a hole, a fillet radius) as a
convenience for a "more realistic" example.* Rejected — every additional
scalar is a step back toward a shape catalogue, which is a step back toward
a mesh. Two scalars is the fence; it is deliberately drawn tighter than the
minimum that would technically still avoid a solver.

**What would change this.** A domain or a finding that Tier I½'s bending
case cannot exercise Class B's dimensional-reduction claim meaningfully
(e.g. the outer-fibre driver field turns out degenerate under every
declared curvature); a future need for genuine contact, multiple loading
modes, or richer geometry, at which point this ADR is revisited and
possibly superseded, not silently extended by adding a field to
`Type2Geometry`.

**Pinned by.** `tests/test_flagship_classb_bend.py` (`Type2Geometry`
structurally rejects anything but two scalars; `BendAngle` returns both a
response and a process-zone volume; the wired Class B machinery below).

---

## ADR-036 — `learning_error(chain)` distinguishes "no learning error because the chain is analytic" from "no defensible estimate reachable"; it does not attempt to derive a learned operator's ground-truth comparison from the chain alone

**Status.** Accepted **Gap.** S-1.4 (SPEC) — implementation choice; E-02
(docs/V1.4-EDITS.md) is the underlying framework finding this responds to,
not resolves **Milestone.** Phase 3.2 (post-M9 remediation)

**What the framework leaves open.**
Spec §1.4 defines `Err_learn(𝒮)` as "measured from a learned model's
rollout-length curve at matched data budget" — implicitly, a comparison
between the learned operator's rollout and an analytic (ground-truth)
counterpart's rollout from the same initial condition. ADR-023 (M4) set
`learning_error()` to unconditionally return `0.0`, correct at the time
since every operator through M7 was exact analytic (ADR-001) and explicitly
deferred "a genuine measurement" to M8. M8 (`src/omi/learning.py`,
`DeepONetOperator`) introduced a learned operator, but never touched
`sufficiency.py` — `learning_error()` took (and still takes) zero
parameters, unconditionally returning `0.0` regardless of what chain, if
any, it is asked about. This is E-02's finding, restated in code: a section
marked SPEC has an implemented function that is only ever correct on the
trivial (all-analytic) sub-case, silently, with no signal that the sub-case
even holds.

The obstacle to a full fix is architectural, not a missing formula.
`tests/test_learning_oracle.py`'s own comparison
(`_learned_vs_analytic_rollout_curve`) computes exactly what Spec §1.4
wants — a learned operator's rollout against the contrast domain's analytic
`CYCLING` oracle, at every prefix length — but it needs the analytic
ground-truth operator as an explicit, separately-supplied argument, because
neither `Chain`/`Segment` nor `DeepONetOperator` itself retains any
reference to what a trained operator approximates. `DeepONetOperator`'s
only fields are its trained parameters and a caller-declared `erasure`
flag (ADR-012's pattern, not a ground-truth pointer); `TrainingReport`
stores loss history, not a rollout curve or a ground-truth handle. A
domain-neutral function given only a `Chain` — as CLAUDE.md §5 invariant 3
requires `sufficiency.py` to remain — has no channel to reach a domain's
analytic counterpart for a learned segment it finds. Building one (e.g.
requiring every `DeepONetOperator` to carry a reference to the operator it
was trained to approximate) is a real architectural extension, not a
one-line fix, and would need its own ADR weighing the cost against
alternatives — out of scope for closing this specific gap.

**Decision.**
`learning_error(chain: Chain) -> float` now takes the chain (previously,
no parameters at all). Behaviour:

- If no segment's operator is an instance of `omi.learning.DeepONetOperator`
  (the chain is purely analytic), return `0.0` — unchanged from ADR-023,
  and still the *correct* value for this case, documented as such rather
  than as a placeholder.
- If any segment's operator *is* a `DeepONetOperator`, raise `NotSpecified`
  citing S-1.4, naming the chain position of the learned segment. This is
  not a failure of this fix — it is the honest answer given what a `Chain`
  and a `DeepONetOperator` actually carry: no rollout-curve-at-matched-
  -budget estimate is derivable from the chain alone, because the
  comparison Spec §1.4 wants needs a ground-truth reference this
  repository's types do not retain anywhere reachable from a chain.

This closes E-02's actual complaint (a SPEC-derived function silently
wrong on a case it has no way of detecting) without inventing the
cross-module ground-truth-retention architecture a genuine measurement
would need. `sufficiency.py` gains a dependency on `omi.learning` for the
`DeepONetOperator` isinstance check only — both domain-neutral core
modules, no domain vocabulary crosses in either direction (CLAUDE.md §5
invariant 3 unaffected), and no circular import (`omi.learning` imports
neither `omi.sufficiency` nor `omi.chain`).

**Alternatives rejected.**
*Compute a rollout-length curve using `rollout_length_error_curve` (already
public in `conformance.py`) as a stand-in.* Rejected — that function
compares two *states* through the *same* chain (a composability/error-
-compounding curve), not a learned operator against its own analytic
ground truth; `TrainingReport`'s docstring claims this reuse is what M8
does, but `test_learning_oracle.py`'s own code contradicts that claim,
building a bespoke comparison instead because the signature genuinely
does not fit — reusing it here would silently compute the wrong quantity
under the right-sounding function name, worse than refusing.
*Extend `DeepONetOperator` to carry a reference to its ground-truth
operator, so `learning_error` can look it up and compute a real curve.*
Rejected for this ADR specifically, not permanently — it is a real,
worthwhile architectural change (and would fully satisfy Spec §1.4), but it
touches `learning.py`'s public type, every existing construction site of a
`DeepONetOperator`, and training entry points, which is a larger and
differently-scoped decision than "fix the function that currently lies by
omission." Flagged under "What would change this" below rather than
attempted inline.
*Leave `learning_error()` at zero parameters, unconditionally `0.0`.*
Rejected — this is E-02's status quo, and CLAUDE.md's own instruction for
this fix is explicit: "a silent constant is the one option that's not
acceptable."

**What would change this.** A future decision to extend
`DeepONetOperator` (or a wrapping type) with an explicit, typed reference
to the analytic operator it approximates — at which point the `raise
NotSpecified` branch above is replaced with a genuine rollout-length-curve
measurement reusing `test_learning_oracle.py`'s existing comparison logic,
promoted from a test helper into `sufficiency.py` or `conformance.py`
proper.

**Pinned by.** `tests/test_sufficiency_learning_error.py` (all-analytic
flagship chain returns `0.0`; a chain containing a `DeepONetOperator`
raises `NotSpecified` citing `"S-1.4"`).

---

## ADR-037 — A Type-2 readout is adapted to a Type-0/1-shaped triage target at one declared reference geometry, discarding the process-zone volume; `sensitivity_operator` itself is not extended to accept `ComponentReadout`

**Status.** Accepted **Gap.** none — implementation choice; Spec §3.3 does
not restrict target readouts by type, but this repository's
`sensitivity_operator`/`danger_triage` are typed `Sequence[FunctionalReadout]`
**Milestone.** Phase 3.3(b) (post-M9 remediation)

**What the framework leaves open.**
Spec §3.3 defines the sensitivity operator generically, for "target readouts
`ρ^(1),...,ρ^(M)`" with no restriction to a particular readout type — any
readout with a derivative with respect to state qualifies in principle.
CLAUDE.md invariant 10 and Spec §3.3's own requirement ("`𝒟_i` is defined
relative to a *declared* target set; if targets change, triage MUST be
re-run") both require flagship's triage to be re-run now that Phase 2 added
`bend_angle` to `FLAGSHIP_DECLARATION.readout_catalogue` — but `BendAngle`
(`ComponentReadout`, Type-2) has a structurally different `evaluate`
signature than `FunctionalReadout` (`evaluate(operator, geometry)` versus
`evaluate(state)`), and no `.jacobian(state)` method at all. M3's
`sensitivity_operator` (`src/omi/observability.py`) predates Phase 2's
Type-2 readouts by six milestones and is typed
`target_readouts: Sequence[FunctionalReadout]`, calling
`readout.jacobian(terminal_state)` uniformly — a genuine type mismatch,
discovered only now that a real Type-2 readout exists to attempt this with.

**Decision.**
`BendAngleAtReferenceGeometry` (`src/omi_domains/flagship/readouts.py`), a
`FunctionalReadout` wrapping a `BendAngle` instance at one declared,
fixed `Type2Geometry` (`thickness=1.0, curvature=2.0`, the same values
`classb_bend.py`'s own `REFERENCE_THICKNESS`/`REFERENCE_CURVATURE` use, for
consistency with the rest of the Class B campaign, not re-derived
independently to avoid a circular import between `readouts.py` and
`classb_bend.py`). Its `evaluate(state)` builds the bound
`HardnessConstitutiveOperator` from *state* (the same construction
`driver_field_for_sites` uses) and returns `BendAngle.evaluate(operator,
geometry)`'s response, **discarding the process-zone volume** — Spec
§3.3's `Dρ^(m)` wants a scalar response's derivative for the sensitivity
operator, not Class B's volume-coupling half, so nothing about that
argument is lost by omitting it here. `.jacobian` is not overridden — it
falls back to `FunctionalReadout`'s central-difference default (ADR-012),
since no analytic derivative through the geometry-fixed quadrature
composition has been derived; this is an honest numerical estimate, the
same convention every other undifferentiated readout in this repository
already uses, not a new precedent.

`sensitivity_operator`/`danger_triage` themselves are **not** extended to
accept `ComponentReadout` directly — that would require deciding how a
Type-2 readout's process-zone volume participates in a sensitivity
operator built for scalar responses, a larger question than "re-run
flagship's triage with the declared target set," and out of scope for
this specific remediation item.

**Alternatives rejected.**
*Add a `jacobian(operator, geometry)` method to `ComponentReadout` and
extend `sensitivity_operator` to dispatch on readout type.* Rejected for
this ADR — a real, larger design question (what does "sensitivity" mean
for a readout whose interface includes geometry as well as state; does the
process-zone volume also carry a danger score) that deserves its own
decision, not one folded into re-running an existing test with an expanded
target list.
*Skip `bend_angle` and re-run triage with the target set unchanged.*
Rejected — this is exactly the staleness CLAUDE.md invariant 10 and Spec
§3.3 forbid: the declared target set changed at Phase 2, and the existing
`tests/test_domain_triage.py` result predates it.

**What would change this.** A future decision to give `ComponentReadout` a
first-class sensitivity interface (the rejected alternative above), at
which point `BendAngleAtReferenceGeometry` becomes unnecessary and
`sensitivity_operator` accepts `bend_angle` directly, geometry included.

**Pinned by.** `tests/test_domain_triage.py` (flagship triage re-run with
`[AggregateHardness(), BendAngleAtReferenceGeometry()]`).

---

## ADR-038 — Interface-only sketches (M10.1): a flat module per sketch under `src/omi_domains/sketches/`, prose in `docs/SKETCHES.md`, "machine-diffable" means `omi.interface.diff` actually runs

**Status.** Accepted **Gap.** none — implementation choice; Spec §11.4 and
Core §7.3 require "a third and fourth short sketch, interface-only" and
ROADMAP M10.1 requires each be "machine-diffable against the two
implemented domains (reuse `omi.interface.diff`)," but neither states where
a no-implementation sketch's declaration should live or what "one page"
means as an artefact. **Milestone.** M10.1 (docs/ROADMAP.md)

**What the framework leaves open.** Spec §11.4 requires "one page each"
declaring the seven items of Core §4, with no implementation. ROADMAP
M10.1 additionally requires the result be machine-diffable, reusing
`omi.interface.diff` — but that function operates on
`omi.interface.InstantiationDeclaration` objects (ADR-016), not prose. A
sketch that is prose only would make "machine-diffable" aspirational
rather than true, and neither Spec nor ROADMAP say where the
Python-side declaration should live, given that every declaration this
repository has built so far (`omi_domains/flagship/interface.py`,
`omi_domains/contrast/interface.py`) is one file inside a full domain
package that also has `operators.py`, `readouts.py`, and `build.py` behind
it — exactly what Spec §11.4/Core §7.3 say a sketch must **not** have.

**Decision.**
- The "one page" lives in a new `docs/SKETCHES.md`: one `##` section per
  sketch domain, filling Core §4's seven items in the Core's own order —
  the same order ADR-016 already fixed `InstantiationDeclaration`'s fields
  in — plus a short framing paragraph (why this sketch, what it tests) and
  an honesty paragraph (which items filled cleanly, which strained, if
  any).
- Each sketch additionally gets one flat module,
  `src/omi_domains/sketches/<name>.py`, exporting exactly a `StateSchema`
  and an `InstantiationDeclaration` built from it — no `operators.py`, no
  `readouts.py`, no `build.py`. `src/omi_domains/sketches/` is a new
  sibling of `flagship/`/`contrast/`, not a thinner subpackage of either:
  a sketch is not an unfinished domain, it is deliberately a declaration
  and nothing else, and the directory boundary makes that structural
  rather than a convention someone has to remember not to violate later.
- "Machine-diffable" is operationalised as: `tests/test_sketches.py` calls
  `omi.interface.diff` between each sketch's declaration and both
  `FLAGSHIP_DECLARATION` and `CONTRAST_DECLARATION`, and records every
  per-item result via the `observe` fixture (CLAUDE.md §7, the R1.1
  convention) rather than asserting a specific expected diff pattern.
  This is deliberately weaker than `test_interface_diff.py`'s
  flagship-vs-contrast test, which pins "differs on six of seven items"
  (ADR-034) — that pin exists because flagship and contrast were
  *designed* to invert each other, a prior claim worth checking. A sketch
  carries no such prior claim; the test only needs to confirm the diff
  actually runs against real declaration objects and to put the resulting
  per-item comparison on record, not to assert what it should find.
- Any Core §4 item a sketch's own author judges cannot be filled without
  stretching is recorded directly in that sketch's `docs/SKETCHES.md`
  section — not silently smoothed into a clean-looking fill — and
  escalated to `docs/V1.4-EDITS.md` if the strain looks like it says
  something about the interface itself, per ROADMAP M10.1's own
  instruction ("Any item a sketch cannot fill is a finding for
  `docs/V1.4-EDITS.md`, and a more valuable one than a clean fill").

**Alternatives rejected.**
*Prose only, no Python object.* Rejected — this would make "machine-
diffable," ROADMAP's own phrase, false advertising: nothing would actually
invoke `omi.interface.diff`.
*A full `omi_domains/<name>/` package mirroring flagship/contrast's shape,
with stub `operators.py`/`readouts.py` raising `NotImplementedError`.*
Rejected — the stub files would misrepresent "no implementation" (a
deliberate scope boundary, Spec §11.4/Core §7.3) as "implementation not
yet written" (an open TODO), inviting a later contributor to fill them in
as if this were ordinary M-milestone work rather than paper evidence for
generality. A single flat module per sketch makes the interface-only
status structural, not a naming convention to remember.
*One shared `sketches.py` module holding all four sketches.* Rejected —
matches neither existing domain's one-module-per-declaration granularity,
and would make reviewing each sketch independently (ROADMAP's own
ordering — device yield first, then the others) harder than it needs to
be.

**What would change this.** A later decision to build one sketch out into
a full domain (operators, readouts, oracles) — itself a different kind of
decision than declaring the interface, needing its own ADR, at which
point that sketch would move out of `src/omi_domains/sketches/` into its
own package the way flagship/contrast are structured.

**Pinned by.** `tests/test_sketches.py`.

---

## ADR-039 — M10.2 baseline characterisation: numpy-only tabular baselines, a learned operator (not the exact simulator) as the operator-graph contestant, and the sweep/scoring design

**Status.** Accepted **Gap.** Spec §9.3 (`[Pass C]`) requires comparison
against "gradient-boosted trees and tabular regression" and a "scored
go/no-go table" but supplies neither an implementation nor a sweep/scoring
methodology. **Milestone.** M10.2 (docs/ROADMAP.md)

**What the framework leaves open.** Spec §9.3 names the baseline classes
(gradient-boosted trees, tabular regression) and the comparison axes in
prose (process-window width relative to measurement noise, labelled-
record count, presence of geometry-dependent responses) and requires
inverse-design hit rate alongside forward accuracy, but does not specify:
which tabular-baseline implementation to use, what the "operator graph"
side of the comparison actually is (the exact analytic simulator, which
has zero error by construction and would make the comparison vacuous, or
a *learned* operator trained under the same data budget as the tabular
models), how many levels each swept axis should take, or how a "hit" is
defined for inverse design.

**Decision.**
- **Tabular baselines are implemented from scratch in numpy/scipy**
  (`src/omi/baseline.py`): a closed-form ridge regressor and a boosted
  ensemble of depth-limited regression trees (greedy per-feature
  threshold search, boosted by fitting each successive tree to the
  current residual). No new pinned dependency (`scikit-learn` or
  equivalent) is added — CLAUDE.md §8 already commits this repository to
  "numpy + scipy required... torch optional with a numpy fallback," and
  `src/omi/learning.py` (ADR-029) already implements a full neural
  architecture from scratch for exactly this reason; a from-scratch GBT
  is a smaller instance of the same policy, not an exception to it.
- **The operator-graph contestant is a `DeepONetOperator` (M8,
  `src/omi/learning.py`), trained on the *same* record count as the
  tabular models at each swept configuration** — not the exact analytic
  simulator. Spec §9.3's comparison is about data efficiency and
  generalisation under a shared data budget; comparing a zero-error exact
  simulator against a data-fitted tabular model would not test that claim
  at all, and would trivially "win" every configuration for a reason
  unrelated to the framework's actual claim (operator structure, not
  omniscience). The exact simulator is retained as the *ground truth*
  every model (tabular and operator-graph alike) is scored against on a
  held-out test set — never as a contestant itself.
- **Sweep axes and levels**: labelled-record count `N ∈ {20, 50, 200}`;
  process-window-width-to-noise ratio `∈ {2, 10, 50}` (window width = the
  range of the swept control parameter used to generate training records;
  noise = the fixed label-noise standard deviation added at generation);
  readout type `∈ {AggregateHardness (Type-0), BendAngleAtReferenceGeometry
  (Type-2 adapted to a fixed reference geometry, ADR-037)}` for the
  geometry-dependence axis. Three small, deliberately tractable levels
  per axis, not an exhaustive grid — the exit criterion is "the go/no-go
  table populated with the regime boundary identified," which needs
  enough points to see a crossover, not a dense scan.
- **Inverse-design "hit"**: for a declared target response value, invert
  each trained model by grid search over the model's *own* predicted
  response as a function of the control parameter, select the control
  value whose predicted response is closest to the target, then evaluate
  the *true* simulator at that selected control. A "hit" is `|true
  achieved − target| < tolerance` (tolerance stated per run, not a single
  invented global constant) — this scores whether a model trained on N
  records supports search over control values it may not have seen
  directly, which forward RMSE alone does not test.
- **Report**: `docs/M10.2-BASELINE-CHARACTERISATION.md`, populated
  entirely from a single reproducible run's actual output (CLAUDE.md §8:
  "never hardcode a narrative number... anything quoted must be
  computed"), with the exact seed and configuration stated so the numbers
  are re-derivable, not merely asserted.

**Alternatives rejected.**
*Add `scikit-learn` as a pinned dependency.* Rejected — no network access
assumption should be built into a milestone's own deliverable when the
repository's stated convention (CLAUDE.md §8, ADR-029) is already to
implement ML machinery from scratch in numpy for exactly this class of
need, and a from-scratch GBT is a modest, bounded addition, not a
significant undertaking, at the depth/estimator counts this comparison
needs.
*Compare tabular baselines against the exact analytic simulator directly.*
Rejected — see Decision above; this would not test the claim Spec §9.3
is actually making (data efficiency, not omniscience).
*An exhaustive grid over many levels per axis.* Rejected as
disproportionate to the milestone's own exit criterion, which asks for a
located crossover, not a dense characterisation surface — three levels
per axis is the minimum that can show a trend and a crossover at all.

**What would change this.** If a future milestone needs a denser sweep or
a real (non-synthetic) dataset, this ADR's ground-truth-simulator
assumption ("both domains are ground-truth simulators, so this is
answerable without field data," docs/ROADMAP.md M10.2) would need
revisiting; that is out of scope here.

**Pinned by.** `tests/test_baseline_characterisation.py`;
`docs/M10.2-BASELINE-CHARACTERISATION.md`.

---

## ADR-040 — Re-running the contrast control-inverse comparison with a hard-constrained operator and a genuinely new gradient-based control search, since neither existed in `src/omi/inverse.py`

**Status.** Accepted **Gap.** Core §4.1/Spec §2.2 (hard constraints beat
soft penalties for exactly the inverse-design reason this comparison
tests) and Core §5 (the control inverse as an optimal-control problem)
both motivate this re-run; neither Spec nor this repository's own
`src/omi/inverse.py` supplies a gradient-based control-search procedure
to reuse. **Milestone.** M10.2 follow-up (docs/ROADMAP.md)

**Correcting a premise before designing anything.** The instruction to
"connect... `inverse.py`'s gradient-based control search" presupposes
that function already exists. It does not: a direct search
(`grep -n "gradient\|optimize\|scipy.optimize" src/omi/inverse.py`)
returns zero matches. `inverse.py` (ADR-031/032/033) supplies
reachability certificates (linear `Φ`, exact halfspace projection),
apparatus parameterisation (a structural box `𝒰_adm` wrapper), and a
decision layer (probability of conformance, CVaR, ordered infeasibility
diagnosis) — all of which operate on an *already-produced* candidate or
target, none of which searches `𝒰_adm` for one. This matches
`docs/COVERAGE.md`'s own S-7.1 row ("the practical hierarchy for
constructing or selecting `Φ`... remains unimplemented beyond the linear
rung") and Core §5's own citation of Spec §7.1's hierarchy
(forward-sampling → latent-space over-approximation → invariant
certificates) — none of which is "gradient descent through a
differentiable forward map." Building this is therefore new work, not a
reconnection of dormant machinery, and is reported to the user as such
rather than silently absorbed.

**Decision, in four parts.**

1. **The operator-graph contestant is rebuilt as a hard-constrained
   monotone function**, using `src/omi/constraints.py`'s existing
   `positive`/`monotone_increasing` reparameterisations directly (not a
   new constraint category): a fixed grid of `K=60` points spans `𝒰_adm`;
   a learnable vector of raw parameters passes through
   `monotone_increasing` (itself `positive` + cumulative sum) to produce
   a risk *profile* over the grid that is non-decreasing *by
   construction*, for any parameter values — violating monotonicity is
   not representable, matching Spec §2.2's own stated requirement for a
   hard constraint. Prediction at an arbitrary `current` is linear
   interpolation between the two nearest grid points (itself monotone,
   preserving the guarantee). Training minimises squared error against
   the same `𝒰_trust`-only records used for Ridge/GBT/the original
   DeepONet, by plain gradient descent using `constraints.py`'s own
   supplied exact gradients (`positive_grad`, chained through the
   cumulative sum) — no torch, matching CLAUDE.md §8/ADR-029's existing
   policy. Chosen over retrofitting `DeepONetOperator` itself: the
   branch/trunk architecture has no natural place to insert a
   monotonicity constraint on a scalar output without a larger redesign
   touching code every other M8 test depends on; a small, dedicated
   monotone regressor for this comparison keeps the change local and
   auditable.
2. **A genuinely new function, `gradient_control_search`, is added to
   `src/omi/inverse.py`** (not a test-only helper): given a differentiable
   scalar forward map and its exact gradient, a target, an
   `ApparatusParameterization` (supplying `𝒰_adm` as a box, ADR-032's
   existing shape), and an initial guess, it performs projected gradient
   descent on the squared residual, clipping the iterate back into
   `𝒰_adm`'s bounds at every step. This is squarely within Core §5's own
   framing ("the control inverse... is the optimal-control problem
   above") and is domain-neutral (CLAUDE.md §5 invariant 3): it takes a
   plain callable and a box, not a domain-specific model.
3. **The trust region is reported as an active diagnostic, not merely a
   sampling boundary for training data.** Core §5 states the trust
   region's purpose plainly: "restrict to where the surrogate is
   calibrated... the optimiser is an adversary that seeks the region
   where the surrogate is most confidently wrong." A search result whose
   solution lies outside `𝒰_trust` is flagged as such alongside the raw
   hit/miss score, rather than silently reported as an equal-status
   answer — this mirrors Spec §7.3/ADR-033's own ordered
   `diagnose_infeasibility` (trust region checked first, before
   control/`𝒰_adm`), applied here to a single-target search rather than a
   full specification window.
4. **Ridge and GBT are untouched** (ADR-039's own baselines, unchanged) —
   this re-run only replaces the operator-graph contestant and its search
   procedure; the comparison's baselines are not to be improved
   alongside it, per instruction.

**Alternatives rejected.**
*Retrofit `DeepONetOperator` itself with a monotone output layer.*
Rejected — touches shared M8 code every other learning.py test depends
on, for a change whose applicability (monotone scalar output) is specific
to this one comparison.
*Use `scipy.optimize` for the control search.* Rejected — would add a new
dependency path CLAUDE.md §8's numpy/scipy-only-plus-optional-torch
policy does not currently need; the search problem here (a smooth,
monotone, low-dimensional scalar function) does not require it, and a
plain projected-gradient loop is short, auditable, and consistent with
`learning.py`'s own from-scratch optimiser precedent (ADR-029).
*Skip the trust-region diagnostic and just report raw hit/miss.*
Rejected — Core §5's own text makes the trust region a first-class part
of the claim being tested (not merely a training-data sampling choice),
and Spec §7.3 already establishes the "report which boundary binds"
discipline (ADR-033) this re-run's diagnostic directly extends.

**What would change this.** A future decision to give `DeepONetOperator`
itself a general hard-constraint output layer (not specific to
monotonicity or to this comparison) would likely subsume the dedicated
monotone regressor built here; `gradient_control_search`'s box-only
`𝒰_adm` (via `ApparatusParameterization`, ADR-032) would need extending
if a future comparison needs the fully coupled constraint manifold Spec
§7.2 itself still leaves `[Pass C]`.

**Pinned by.** `tests/test_baseline_characterisation.py`
(`ConstrainedMonotoneOperator`, `run_contrast_control_inverse_config`'s
constrained variant); `src/omi/inverse.py::gradient_control_search`;
`docs/M10.2-BASELINE-CHARACTERISATION.md` §6 (revised).

---

## ADR-041 — Falsification threshold-setting procedure (Core §6.1/Spec §9.4), and which of the six criteria get worked values now

**Status.** Accepted **Gap.** Core §6.1 states its own text is `[Pass D]`:
"each criterion requires a stated threshold or a procedure for setting one
per application" (Spec §9.4, same marker: "threshold-setting derived from
decision sensitivity (§7.3)... to be written"). **Milestone.** M10.3
(docs/ROADMAP.md)

**Scope, decided before anything else.** `docs/V1.4-EDITS.md` E-16 audited
all six criteria against what this repository can actually evaluate:
criterion 1 fully evaluable now (no PASS-row dependency); criterion 3
partially (the symptom — super-linear rollout error — is checkable;
"after all stabilisation measures" is not, blocked on S-2.5/S-2.6/S-2.7);
criteria 2, 4, 5, 6 blocked on PASS-B/C rows with no code path to evaluate
them at all. Per instruction, this ADR supplies the threshold-setting
**procedure in full**, applicable to all six, but **worked numeric values
only for criteria 1 and 3's checkable half** — criteria 2, 4, 5, 6 get an
explicit **moot** statement naming the blocking row, not a placeholder
number. A threshold for a criterion with no measurement procedure behind
it would be exactly the "confident nonsense" CLAUDE.md §4 warns against:
a number with nothing computed to compare it to.

**The procedure.** Spec §9.4 ties threshold-setting to §7.3's decision
layer, which this repository already implements
(`probability_of_conformance`, `cvar`, `asymmetric_cost`,
`src/omi/inverse.py`, ADR-033). Applied to a falsification criterion whose
observable residual is `R`:

1. **Name the decision `R` gates** — what continues, or is refused/
   augmented/redesigned, if the criterion's condition holds.
2. **Declare the two wrong-decision costs** (`cost_miss`: wrongly
   continuing to trust something that has actually failed the criterion;
   `cost_false_alarm`: wrongly refusing/pausing when the criterion in fact
   holds), in Spec §7.3's `asymmetric_cost` sense — declared,
   application-specific inputs. Core and Spec do not supply these, exactly
   as `𝒰_adm`'s numeric bound is a declared input rather than a framework
   one (E-27, `docs/V1.4-EDITS.md`) — the same pattern, applied here to
   falsification rather than inverse design, and not itself a new
   V1.4-EDITS finding, since Spec §9.4's own text already anticipates "a
   procedure for setting one **per application**," not a value Core/Spec
   derive.
3. **Declare the minimum effect worth catching**, `minimum_effect` — the
   smallest true departure from "the criterion holds" an application cares
   to detect. Also declared, not derived.
4. **Estimate the residual estimator's own sampling variability**,
   `standard_error`, empirically (repeated-campaign variation, bootstrap,
   or an oracle's known-truth calibration) at the declared campaign size —
   this is a measured fact about the estimator, not a declared input.
5. **Set the threshold** via `src/omi/inverse.py::decision_sensitive_threshold`
   (new this ADR): the Bayes-optimal boundary between `N(0,
   standard_error²)` ("the residual is noise") and `N(minimum_effect,
   standard_error²)` ("a real effect of at least `minimum_effect`"), under
   the declared asymmetric costs — the standard likelihood-ratio-test
   result for two equal-variance Gaussians, `τ = minimum_effect/2 +
   (standard_error²/minimum_effect) · ln(cost_false_alarm/cost_miss)`, not
   an invented formula (verified against a numerical expected-cost sweep,
   `tests/test_inverse_decision_layer.py`).
6. **Report the threshold's sensitivity** to the declared cost ratio and
   `minimum_effect` — this, not a single number, is what makes the
   procedure "per application" (Spec §9.4's own phrase): §10 below shows a
   case where the ratio moves τ by 4× and one where it is essentially
   inert, and the difference itself is the reportable finding.

**Worked values (docs/M10.3-FALSIFICATION-THRESHOLDS.md).**

- **Criterion 1** (sufficiency, bias-blocked): `standard_error` measured
  from 20 independent replications of flagship's own real matched-pair
  campaign (`tests/test_conformance_flagship.py::_matched_pair_sufficiency_campaign`,
  `n_pairs=2000` each) and, separately, of the known-insufficiency oracle's
  calibration campaign (`tests/oracles/known_insufficiency.py`,
  `n_pairs=8000`, truth `4.5`, recovered `4.509 ± 0.054` across 20 reps —
  the estimator itself is trustworthy at this precision). Two illustrative
  `minimum_effect` declarations are shown side by side, computed with the
  same formula and flagship's own measured `standard_error = 0.0161`: at
  `minimum_effect=1.0` the threshold is essentially insensitive to the
  declared cost ratio (`τ ≈ 0.499` either way, since `standard_error ≪
  minimum_effect`); at `minimum_effect=0.05` (comparable to
  `standard_error`) the threshold moves from `0.0095` to `0.0405` as the
  declared cost ratio flips end to end — flagship's own measured deficit
  (mean `0.0109` across the same 20 reps) sits below the first threshold,
  straddles the second depending on which cost ratio is declared. Both
  are genuine, computed consequences of the declared inputs, not tuned to
  produce either outcome.
- **Criterion 3's checkable symptom** (super-linear rollout error growth):
  measured directly on both domains' current, wholly-analytic chains via
  `omi.conformance.rollout_length_error_curve`, using an "excess over
  linear extrapolation" statistic (`e_last − n_steps · e_first`) across 30
  replications each. Both are **deterministic and strongly negative**
  (flagship `−0.0337`, effectively zero sampling variance; contrast
  `−35.0`, likewise) — sub-linear or flat, not merely "not super-linear."
  Given `standard_error ≈ 0`, the threshold collapses to
  `minimum_effect/2` regardless of the declared cost ratio, and the
  measured excess sits far below it for any `minimum_effect` an
  application would plausibly declare — the procedure is shown applied,
  but the conclusion does not depend on the declared inputs the way
  criterion 1's does, and that contrast (decision-sensitive vs.
  decision-robust) is itself reported, not glossed over.
- **Criteria 2, 4, 5, 6: stated moot**, not worked. No threshold is
  computed for a residual this repository cannot yet measure — citing
  E-16's own blocking rows (2→S-6/C-3.7; 4→S-9.3/S-7.1, status-updated
  this session but not closed; 5→`augmentation_loop`'s schema-only design,
  E-16; 6→C-3.9b, "test only; do not implement a scoping check" by this
  repository's own design). A number here would be uninterpretable rhetoric
  dressed as a measurement, exactly what CLAUDE.md §4 forbids.

**Alternatives rejected.** *A single universal threshold per criterion,
independent of application.* Rejected — Spec §9.4's own text asks for "a
procedure for setting one **per application**," which a single fixed
number is not; the sensitivity report (step 6) is the actual deliverable.
*Deriving thresholds from Core/Spec directly, without declared inputs.*
Rejected — neither document supplies cost or minimum-effect figures (the
same reason `𝒰_adm` needed E-27); inventing them without declaring them as
assumptions would misrepresent this repository's own choice as the
framework's. *Filling in illustrative numbers for the four moot criteria
so the table looks complete.* Rejected — this is precisely the
"plausible-looking implementation of an underived procedure" CLAUDE.md §4
calls worse than a refusal.

**What would change this.** Criteria 2, 5, 6 unblock only when their named
PASS-row closes (closure-defect measurement, `augmentation_loop`'s
chain-derived learning term, and a deliberate design decision to implement
the error-control-dichotomy scoping check respectively) — none is this
ADR's to resolve. Criterion 4 unblocks further once a second chain is
exercised under genuine search machinery (this ADR's own worked value for
criterion 1 already demonstrates the pattern the third would need) and, in
the limit, only partially — Spec's "prospective" requirement needs real
execution no synthetic-simulator repository can supply.

**Pinned by.** `src/omi/inverse.py::decision_sensitive_threshold`;
`tests/test_inverse_decision_layer.py` (closed-form verified against a
numerical expected-cost sweep); `docs/M10.3-FALSIFICATION-THRESHOLDS.md`.

---

## ADR-042 — The v1.3/v1.4 boundary: versioned claims and composition, not a directory

**Status.** Accepted — **design only; this ADR authorises no code.**
**Finding.** `docs/V1.4-EDITS.md` E-35, filed before this ADR per CLAUDE.md §10.
**Milestone.** M11.1 (docs/ROADMAP.md)

**The problem.** Adding a constitutive declaration changes Core §4's interface,
which makes anything built on it a **v1.4** implementation. This repository's
OMI-0/1 conformance results, its fourteen oracles, and all thirty-four
`V1.4-EDITS.md` findings are **v1.3** results, and they are the asset — the paper
says "here is v1.3 implemented and audited, here is the proposed extension, here
is the evidence it works." An extension that silently invalidates the audit
destroys more than it adds.

**Rejected framing, recorded because it was the first answer.** The obvious
mechanism is a directory boundary: put the extension in `src/omi_v14/`, or in
`src/omi/proposed/`, and keep the import graph one-directional. Every version of
this answers the question *where does the code live*, which is the wrong
question. Code placement is reversible by anyone who moves a file, it is enforced
by convention rather than by the artefact, and — decisively — it does not handle
the case the extrapolation experiment actually needs: **the same domain evaluated
under both interfaces** (ADR-045's contestants 1 versus 2/3). A directory
boundary forces two copies of a domain to express that.

**Decision, in three parts.**

**1. The repository stays v1.3-conformant.** No existing conformance claim,
oracle, or finding is restated as a v1.4 result. The extension is built
*alongside*, marked proposed-v1.4, and carries its own evidence.

**2. Versioned claims — the boundary is a declared field of every result, not a
location.** `ConformanceReport` gains a required `specification_version`, and
comparison or carry-forward across differing versions is **refused** rather than
silently permitted, following `omi.interface.classify_invariant`'s established
precedent of raising rather than guessing when a declaration does not settle the
question.

This is the repository's own pattern for exactly this class of problem, not new
machinery: CLAUDE.md invariant 1 and Core §3.9 require every metric-dependent
quantity to travel with its metric, which is why `ConformanceReport` already
carries `metric` and why `LipschitzReport` exists at all rather than a bare
spectrum array. A conformance level is *specification-dependent* in precisely the
same way a Lipschitz constant is metric-dependent — the level name OMI-1 is
stable while the table rows defining it are not (E-35). Declaring the version is
the same move as declaring the metric, applied to a different dependency.

Why this beats the directory: the guarantee is **positive** (each result states
what it claims) rather than **negative** (no import crosses a line); it survives
refactoring, because a field cannot be relocated out of existence; and it makes
the v1.3↔v1.4 comparison the deliverable rather than a hazard to be managed —
two reports on one domain, differing in one declared field, is exactly what
ADR-045 needs to measure.

**3. Composition, not modification.** `ExtendedDeclaration` **wraps** an
`InstantiationDeclaration` and adds the new items, exposing a `.v13_core`
projection back to the seven-item object. Consequences, all of which are the
reason for the choice:

- v1.3's `omi.interface.diff` and every test that calls it are untouched **by
  construction**, not by care.
- ADR-044's requirement that "the diff comes out near-identical except for item
  6 and the constitutive declaration" becomes **structurally guaranteed** rather
  than an outcome to hope for and then check.
- The extension is additive by type, so no v1.3 field changes meaning — which is
  the property that keeps the audit citable.

**Code placement.** `src/omi/proposed/`, for readability. This is explicitly
**not** the mechanism, and the ADR records that so a later reader does not
mistake the directory for the guarantee.

**An import-direction lint test was considered and declined.** The
domain-vocabulary lint (`tests/lint/`) exists because "no domain noun in
`omi/`" has no per-result carrier — there is nothing an individual value can
state about itself to discharge it, so a static check is the only available
mechanism. Version provenance is not like that: part 2 gives every result a
carrier, and a second, weaker guarantee for the same property is maintenance
cost without additional assurance. If part 2 is ever weakened to an optional
field, this decision should be revisited.

**Cost, stated plainly.** Part 2 touches v1.3 code. It changes **no v1.3
result** — it annotates them — but `ConformanceReport` gains a required field
mid-audit, and four conformance test modules need mechanical constructor
updates (`tests/test_conformance*.py`). That cost is accepted: an unversioned
report is E-35's defect, and leaving it in place to avoid touching tests would
be preserving the letter of the audit at the expense of its meaning.

**What would change this decision.** If the constitutive extension turned out to
need to *modify* rather than *extend* a v1.3 object — if a declared constitutive
form changed what an existing item means, rather than adding an item — then
composition would not be available and a genuine fork would be required. Nothing
in E-32's proposed role-scoped split does this: 6a–6c keep their existing content
and 6d is new. The moment a proposed edit changes an existing item's semantics,
reopen this ADR.

**What tests would pin it** (design; not written here). Comparing two reports
whose `specification_version` differs raises. `ExtendedDeclaration(...)
.v13_core` diffs against `FLAGSHIP_DECLARATION` with exactly the same result
flagship's own declaration produces. Every pre-existing conformance test passes
with `specification_version` set to v1.3, and its recorded observations are
unchanged — the audit-preservation check, and the one that must be run first.

---

## ADR-043 — Constitutive form declaration: the extension point's design

**Status.** Accepted — **design only; no code.**
**Finding.** `docs/V1.4-EDITS.md` E-32 (role-scoped split of item 6; the
validity-range mechanism is already specified in E-32's proposed wording).
**Milestone.** M11.2 (docs/ROADMAP.md)

**What is being extended, and why item 6 cannot simply be widened.** Spec §2.2
names five hard-constraint categories, none of which is a domain constitutive
form, and Core §4 item 6 does not merely lack a place for one — it **refuses one
by name**, which this build's faithful classifier demonstrates: `classify_
invariant` raises on `koistinen_marburger_martensite_kinetics` and its siblings,
correctly, because a transformation-kinetics law is neither a conservation
balance nor a monotone functional. Item 6 also serves two roles with different
mathematical requirements — hard constraints (Spec §2.2) *and* reachability
certificates (Spec §7.1) — so adding a constitutive form to it would silently
widen the pool §7.1 draws certificates from, which is unsound: a functional form
for an operator is not a scalar functional of state with a provable per-step
accumulation bound.

**Decision. Build against E-32's role-scoped split**, not a sub-item:

| Sub-item | Content | Roles |
|---|---|---|
| 6a | Conservation laws | hard constraint **and** certificate |
| 6b | Monotone functionals | hard constraint **and** certificate |
| 6c | Equilibrium-limited fractions at attainable driving | certificate; hard constraint where the bound is structural |
| **6d** | **Declared constitutive forms** | **hard constraint ONLY — MUST NOT be read as a certificate** |

**The declaration's fields.** Minimum five, and the design choice in each:

- **`form`** — the functional form's identity as a **typed** value (enum member or
  registered named form), *not* free text. This is the one place the design
  deliberately departs from item 6's existing convention: item 6's free-text
  names are exactly why `classify_invariant` had to become a keyword heuristic
  that refuses rather than guesses, and repeating that mistake in a category whose
  whole purpose is to carry structure would be a self-inflicted wound.
- **`parameters`** — fitted values, each with its provenance.
- **`validity_range`** — **the load-bearing field.** See below.
- **`provenance`** — the source establishing the form (a citation, not a claim).
- **`governs`** — which state components, and which operator, the form constrains.

**The validity report IS the mechanism for `V1.4-EDITS.md` §10's "buy physics"
row, which currently has none. This is the design's connection to the framework's
stated purpose, and it is stated first because without it the field reads as a
modelling convenience.**

The framework's purpose includes telling a practitioner which purchase to make
next. `docs/V1.4-EDITS.md` §10 audits that claim against the ledger and finds six
interventions diagnosed and **four** supplied with machinery: buy sensing has the
danger score and value of information (Spec §3.3, §3.4), buy data has the
learning-error term (§1.4), run experiments has sufficiency campaigns (§8), and
declare out of scope has the error-control dichotomy and the refusal apparatus.
**Buy characterisation and buy physics have nothing at all** — and five ledger
entries each block those two rows.

An operator constrained to a declared form MUST report **where the current
evaluation sits relative to that form's validated range**: a per-input
extrapolation factor, the binding input, and which space it binds in. That is a
practitioner feedback channel of a kind nothing in Core or Spec can currently
emit — *this evaluation is 2.3× outside the validated envelope of this
relationship, on the state-space bound* — and it converts an unanswerable question
into a computed number: **should I buy physics here, and for which relationship?**

Two consequences follow from taking that framing seriously rather than treating it
as a nice property:

- The report is **not** an internal diagnostic that happens to be exposed. It is
  the output the category exists to produce, which is why it is a required
  reporting obligation in E-32's proposed Spec §2.2 wording and not an optional
  extra.
- It is the **only** one of §10's two empty rows this extension fills. Buy
  characterisation stays empty: E-31's suite declaration is a precondition for
  costing a characterisation purchase, but no pricing mechanism follows from it,
  and this ADR does not invent one. M11 should not be described as closing the
  gap §10 documents — it closes half of it, and the half it leaves open is
  recorded as an open framework question rather than an implementation backlog
  item.

**Design decisions recorded.**

1. **A result dataclass, never a bare float** (CLAUDE.md §8): per-input factors,
   the binding input, the declared range, and the form's identity travel together.
2. **Reported, never enforced.** A query outside the range is *surfaced*, not
   refused. Refusing would make the operator unusable exactly where inverse
   design must probe, and E-28 is the standing evidence that off-manifold search
   is where the interesting failures live — a constraint that blocks the
   optimiser rather than informing it repeats that composition failure in a new
   place.
3. **Chain composition: elementwise worst, and name which segment binds.** A
   chain-level extrapolation report is the worst factor over segments *plus the
   segment responsible*, mirroring E-06's "report which term blocks, in order"
   discipline rather than returning an unattributed maximum.
4. **`classify_invariant`'s refusal is preserved, not relaxed.** Under 6a–6d it
   must still refuse to classify a 6d member as a certificate kind. That refusal
   is now *correct by specification* rather than incidentally correct, and it
   acquires a test asserting it.
5. **`n_eff`-style regime reporting for the range itself**: where a form has
   multiple validity regimes (Hall–Petch's coarse-grain regime versus its
   fine-grain breakdown), the report names the regime, not only the distance.

**Validity is declared in BOTH control space and state space, and the report
names which bound binds. Decided, not authorial** (amended before M11.1; the
earlier `[authorial-choice]` marking is withdrawn). This is settled by the
metallurgy of ADR-044's own five forms, not by preference, and the reasoning is
recorded here so it does not read as one:

| Form | Control-space bound | State-space bound |
|---|---|---|
| Hall–Petch | **none exists** | breakdown at fine grain size — the bound is on `d` itself |
| Kocks–Mecking | strain-rate and temperature window of the fit | dislocation-density saturation, where `k₁√ρ ≈ k₂ρ` |
| JMAK | isothermal-hold window of the fit | impingement breakdown as `X → 1`, where the fixed-nucleation assumption fails |
| Grain growth | temperature window of the Arrhenius fit | abnormal-growth onset, a state condition on the size distribution |
| Koistinen–Marburger | quench-path window | competing-transformation onset — a state condition on what has already formed |

**Hall–Petch is the decisive case.** Its breakdown at very fine grain size is
purely a condition on the state — grain size is a state component, not a control
— and it has *no* control-space expression at all: no furnace setting or transfer
speed names the boundary, because the same setting produces a validated or an
invalidated regime depending on what the material already is. A control-only
design therefore **cannot represent one of ADR-044's five forms**, which settles
the question by elimination rather than by taste.

The converse also holds and matters for the report's shape: Kocks–Mecking's
rate and temperature bounds are genuinely control-space (you leave the fitted
regime by driving harder or hotter, whatever the current state), while its
saturation bound is genuinely state-space. A single form spanning both is the
common case, not the exception, which is why the report must name **which bound
binds** rather than returning one number: "outside the fitted temperature window"
and "past dislocation saturation" are different findings that call for different
actions — the first is a process-control problem, the second means the form has
run out of physics.

**The split determines the practitioner ACTION, not merely the bound's
provenance — and this is why it must be legible in the report's output rather
than only in the declaration.** The two violations differ in whether *anything
the framework already has* can respond to them:

| Binding space | What it means | Actionable within existing machinery? |
|---|---|---|
| **Control** | The declared form is still valid for this material state; the driving programme has left the window the form was fitted over. | **Yes.** This is a control-inverse problem (Core §5): the setpoint can be moved back inside the window, and `omi.inverse`'s apparatus parameterisation and `𝒰_adm` box already express the search. The extrapolation warning is a *constraint to add to that search*. |
| **State** | No admissible control recovers validity. The material is in a condition the form was never fitted to describe, and driving differently does not change that — the form has run out of physics. | **No.** Nothing in Core or Spec responds to it. This is a *buy physics* signal in the strict sense: the only remedies are a different declared form, a wider fit, or an honest refusal (`omi.gaps.NotSpecified`). |

So the report must expose the binding space as a first-class field with its
actionability, not merely record which bound was tightest. A caller receiving
"2.3× outside the envelope" and nothing else cannot tell whether to re-run the
control inverse with a tightened constraint or to stop and commission physics —
and those are not variations of one response, they are the difference between a
problem the framework can already solve and one it can only report. Collapsing
them into a single scalar would reproduce, in a new place, exactly the failure
E-06 documents for inverse design: an unordered infeasibility number that cannot
say which of several terms is responsible, when the terms call for different
purchases.

A consequence worth stating for `docs/V1.4-EDITS.md` §10: only the *state-space*
half of this report is genuinely new capability. The control-space half routes
into machinery that already exists (Core §5's control inverse), which means M11's
contribution to the **buy physics** row is narrower than "the row now has a
mechanism" — it is specifically that a state-space validity violation becomes
*visible and attributable*, where previously it was indistinguishable from a
control-space one and both were invisible.

**Amended before M11.3: one-sided windows, and the form signature.** Two
questions that would have become defects the extrapolation experiment was built
on, settled here rather than discovered later.

**(i) One-sided validity is the common case, not a corner case, and needs an
explicit declaration.** At least three of ADR-044's five forms are one-sided:
Hall–Petch breaks at fine grain size with no upper limit, JMAK's impingement
breakdown is approached only from below, and Koistinen–Marburger applies on one
side of its transformation start only. The half-widths-from-centre convention has
no centre for these, and the "a missing bound raises" rule would force declaring a
fabricated opposite limit — a claim no source made.

So `UNBOUNDED` is an explicit declaration, distinct from a missing bound. This
follows the framework's own precedent for the identical problem: Core §4 item 3
requires a domain with no erasure operators to declare the empty inventory *and*
state how the dichotomy's condition (b) is met instead, and E-26 argues the same
for a control inverse — an explicitly empty response is a legal, required
declaration, never an omission. An omitted *value at report time* is still
refused, since an unchecked bound hides violations; only the *edge* may be
declared absent.

**The factor rule for a one-sided window: `1 + (distance past the declared edge)
/ fitted_scale`, and exactly `1.0` anywhere inside.** Both rules give `1.0` at the
boundary and `> 1` outside, so `outside_envelope` means one thing regardless of
which applied. Justification for the two choices inside it:

- *Why a declared `fitted_scale` rather than the bound's own magnitude.* A factor
  of `(value − high)/|high|` would change if a domain reported the same physical
  bound in different units — exactly the unit-dependence E-33 measured at sixteen
  orders of magnitude for the semigroup residual, and exactly what CLAUDE.md
  invariant 1 exists to prevent. The domain declares what "far" means, as it
  declares a metric. The scale is *required* for a one-sided window and *forbidden*
  for a two-sided one, so which rule produced a reported number is never ambiguous.
- *Why flat `1.0` inside rather than a graded interior reading.* A one-sided window
  supplies no interior reference point: with no opposite edge there is no centre to
  measure from, so any graded interior value would be measured from a point the
  source never established. A flat `1.0` says honestly that the declaration
  supports the query and nothing more. The cost is real and is stated in the
  docstring: for a one-sided bound the report answers "am I outside, and by how
  much" and *not* "how close to the edge am I". A caller needing the latter needs a
  source that establishes both edges.

**(ii) There IS one shared form signature, and it collapses a distinction that
matters — so the distinction is declared alongside it.** Kocks–Mecking is a rate
law in accumulated strain, JMAK an explicit closed-form solution in time,
Hall–Petch algebraic in a state component with no time in it at all. All three are
expressible as `Callable[[Mapping[str, float]], FloatArray]` — named quantities in,
response array out — and that is the signature `evaluate` now takes, keyed by the
same names the validity bounds use so the quantities a form consumes and the
quantities its range is declared over cannot drift apart.

But that signature is silent about whether the returned number is **a rate to be
integrated** or **a level to be used directly**, and using one where the other is
expected is a silent dimensional error rather than a raised one. So `FormKind`
(`RATE_LAW` / `EXPLICIT_SOLUTION` / `ALGEBRAIC`) is a required field. This is the
move Core §3.5 already makes for readouts — three types sharing a codomain family,
separated by a declared tag rather than by the caller guessing. **`form` is
therefore not a union; it is one signature plus a declared interpretation.**

**What "typed, not free text" then guarantees, and the residual it does not
close.** It guarantees the form exists, is evaluable, declares a non-empty and
non-fabricated range, and states whether its output is a rate or a level. It does
**not** guarantee the callable computes what the declared name says: a caller can
declare a form under a canonical name and supply an arbitrary function. That is
E-17's good-faith residual recurring — `ReachabilityCertificate` is typed as the
sound `Φ(s)=w·s` artefact, which stops a forward-sampling result being passed off
as a certificate, and still cannot stop a caller constructing one for an invariant
that does not hold. Typing raises the floor on what can be passed off; it does not
reach good faith. Recorded here and in the module docstring rather than repaired,
because the check that would close it is empirical — validating the form against
data in the regime it claims, which is Spec §4.6's ladder discipline applied to a
declared form — and is not proposed as part of this ADR.

**(iii) An approximate edge is declarable, and the report says when one binds.**
Not every validity edge is a sharp physical limit. Some are boundaries where a
*competing mechanism* takes over, and those depend on the route taken to reach
them — cooling rate, hold time, path — so the edge is genuinely fuzzy rather than
imprecisely known. `EdgeKind` (`SHARP` / `APPROXIMATE`) is declared **per edge**,
not per bound, because one window commonly has one of each: a transformation-start
temperature is sharp physics while the boundary where a competing transformation
intervenes during the same quench is not.

The default is `SHARP`, deliberately: declaring an edge approximate is a positive
statement about what the source establishes, so a domain that has not considered it
gets the stronger, checkable claim rather than a silent hedge.

The report carries `binding_edge_kind`, so a factor of `1.05` against a
competing-mechanism boundary cannot be read as a violation of a sharp limit — that
figure is inside the edge's own uncertainty, and a consumer unable to see the
difference would report the edge's fuzziness as a finding. **A fuzzy bound honestly
declared is worth more than a precise one invented**, and this is what makes that
principle structural rather than advisory: the alternative — forcing a
competing-mechanism boundary to be declared as a clean number — fabricates
precision the source never had.

**What tests would pin it** (design). An oracle whose validated envelope is known
by construction, asserting the reported extrapolation factor equals the
constructed one — the same discipline as every `tests/oracles/` member — with a
**second, one-sided** constructed window for the rule above, and a **third with one
sharp and one approximate edge** whose factors are symmetric so the declared kind
is demonstrably doing the work rather than the magnitude. An off-manifold test
asserting the report *surfaces* rather than raises. A test asserting `centre` and
`half_width` raise for a one-sided window rather than returning a plausible
number. A test asserting `classify_invariant` still refuses a 6d member.

---

## ADR-044 — The constitutive variant domain: a sibling, never a replacement

**Status.** Accepted — **design only; no domain code.**
**Milestone.** M11.3 (docs/ROADMAP.md)

**Decision.** `src/omi_domains/flagship_constitutive/` as a **sibling** of
`flagship`. The analytic flagship is **untouched**, which preserves every M0–M9
oracle result that used it — the erasure measurement, the triage, the Class B
bend campaign, the OMI-1 claim. Both domains declare the same seven items so
they are machine-diffable, and the diff is expected to come out near-identical
except for item 6 and the constitutive declaration. **That expectation is the
experiment**: it makes the comparison a controlled test of exactly what the
extension adds, and ADR-042's `.v13_core` projection is what makes it
structurally guaranteed rather than checked after the fact.

**The five canonical forms, with their real validity boundaries** — the
boundaries matter more than the forms, because they are what ADR-043's mechanism
reports against:

| Form | Expression | Where it breaks |
|---|---|---|
| Kocks–Mecking dislocation evolution | `dρ/dγ = k₁√ρ − k₂ρ` | outside the fitted strain-rate and temperature regime; at high rate (dislocation drag); where dynamic recrystallisation intervenes |
| Grain growth | `dⁿ − d₀ⁿ = k₀ exp(−Q/RT)·t`, `n ≈ 2–3` | abnormal growth; strong solute drag |
| JMAK recrystallisation | `X = 1 − exp(−ktⁿ)` | assumes a fixed nucleation and growth mode — breaks when the mechanism changes |
| Koistinen–Marburger | `f_m = 1 − exp(−α(Ms − T))`, `α ≈ 0.011 K⁻¹` | athermal by construction; breaks where isothermal bainite intervenes |
| Hall–Petch + forest hardening | hardness readout | Hall–Petch breaks at very fine grain size |

**A recorded physics upgrade, and an honest note on what it replaces.** The
current flagship hardness readout uses `20/(1 + |grain_size|)` — a hyperbolic
surrogate that is *structurally right* (monotone decreasing in grain size) and
*wrong in exponent* (Hall–Petch is `σ₀ + k/√d`). The variant uses the real form.
The surrogate is not a defect in the v1.3 build, which never claimed calibrated
metallurgy, but the difference should be stated rather than quietly corrected,
because it is one of the things the extension buys.

**A side effect worth naming as a deliverable.** Phase 1 measured that three
flagship components — `prior_grain_size`, `inclusion_content` and
`accumulated_hardening` — carry `rate == 0.0` under **both** flagship operators,
so no declared operator transports them (the measurement behind E-29). In the
variant they acquire real kinetics. Two consequences:

1. The control inverse becomes **non-vacuous**, so E-26's finding gets a domain
   where it can be **exercised** rather than only detected — which E-26's own
   entry names as what it is waiting for.
2. **Flagship itself stays broken, deliberately.** It is the audit baseline and
   E-29's recorded evidence, and repairing it would delete the only instance in
   this repository of a domain satisfying all seven interface items while being
   physically inert. The variant repairs the physics *in a sibling*; the defect
   remains documented and reproducible in the original.

**Scope fence.** No new erasure operators; no Tier II; no mesh, solver, or
equilibrium iteration; same chain topology with kinetics substituted. Every
CLAUDE.md §9 anti-goal continues to apply, and Tier I½'s ADR-035 fence is
unchanged. The variant's conformance reports carry
`specification_version = proposed-v1.4` (ADR-042), so its level claims can never
be mixed with flagship's.

**What would change this decision.** If the five forms could not be fitted to
produce a chain whose v1.3-core declaration diffs near-identically against
flagship's — if declaring real kinetics forced a different state schema, for
instance — then the controlled comparison is lost and the variant would need to
be justified on its own terms instead. Check the diff early, before fitting
anything.

**Amended at M11.3: the prediction above was wrong, and the correction is the
milestone's main finding.** The diff does not isolate item 6 — it is **empty**,
because v1.3 has no way to express "this domain declares constitutive forms" at
all. Both available roads are closed: naming the forms in item 6 makes
`omi.interface.diff` *raise* (`classify_invariant` refuses the name, correctly),
and declaring them outside the seven items makes the two cores identical. The
variant therefore takes the second road, with its v1.3 core constructed field by
field *from flagship's own declaration object*, so "the cores are identical" is true
by construction and the emptiness is a property of v1.3's expressive range rather
than of two hand-written declarations happening to agree. Recorded in
`docs/V1.4-EDITS.md` E-32 as a measured consequence.

**Two other things M11.3 found, both worth the record.** First, the validity
machinery caught a real modelling error on its first application to real physics: a
first version applied Koistinen–Marburger at the soak temperature, and the
extrapolation report flagged the query at `5.71×` outside its declared window with a
`CONTROL_INVERSE` action — correctly, since a soak above `Ms` is a temperature at
which no athermal transformation occurs. The form moved to the transfer stage, where
the piece cools through the window in which it holds. That is the category doing the
job this ADR argued for, on its own author. Second, a first grain-growth
parameterisation was physically shaped and **numerically inert** — the Arrhenius
factor produced no measurable growth at the declared soak temperature — and a first
Kocks–Mecking declaration bounded `stored_density` in physical m⁻² while the toy's
state component carries a dimensionless index, so every in-range query read as
sitting at the far edge of an enormous window. Both are calibration failures rather
than physics ones, both are recorded in the affected forms' `provenance`, and the
second is why `forms.py` now states explicitly that a bound must be declared in the
units the state actually carries.

**A typing consequence, resolved by composition like everything else in ADR-042.**
`extrapolation_report` is *not* added to `omi.operators.EvolutionOperator`: doing so
would give every v1.3 operator an attribute it does not implement and would put a
proposed-v1.4 obligation on a v1.3 base class. It is a `runtime_checkable` Protocol
(`omi.proposed.ConstitutivelyConstrained`) that an operator satisfies structurally,
so nothing in v1.3 changes and callers can still ask the question type-safely.

**What M11.3 did NOT do, stated so the gate is not over-read.** `inclusion_content`
— the third of the three components Phase 1 measured at `rate == 0.0` — is still
static, in both domains, deliberately. Inclusions are inert second-phase particles
over this chain, so it is a genuine *parameter* in E-29's proposed sense rather than
an un-transported state component. Declaring kinetics for it to make the audit look
complete would be inventing physics, and the test asserts it stays static so the
choice cannot drift silently.

---

## ADR-045 — The extrapolation experiment: does declared physics buy reach?

**Status.** Accepted — **design only. Do not run.**
**Milestone.** M11.4 (docs/ROADMAP.md)

**What the experiment is for.** To test whether constraining an operator to a
declared constitutive form buys **extrapolation reach** outside the training
envelope — the claim the whole v1.4 extension rests on. Its design decides
whether the answer means anything, so the design is recorded before any code.

**Two generators, in a fixed order. Amended before M11.1: the order is the
inverse of this ADR's first version, and the reason is attributability.**

**Generator A — PRIMARY: a canonical form plus one named unmodelled term.**
Kocks–Mecking as the backbone plus a single, named, deliberately-withheld term —
a strain-rate-dependent drag contribution — active in part of the control range.
Every contestant fits its own parameters from the same in-envelope data; no
contestant is given the withheld term.

**Generator B — FOLLOW-UP: a multi-mechanism composite.** Several mechanisms with
coupling **no single declared form expresses** — Kocks–Mecking coupled to
concurrent JMAK recrystallisation that *consumes* stored dislocation density, with
grain growth feeding back into the Hall–Petch term.

**Why A first.** The two generators answer different questions, and only one of
them can produce an interpretable *negative*. Against A, the missing physics is a
**single named term**, so every gap is attributable: if contestant 3 beats
contestant 1, the benefit is traceable to declaring a form that is right about
everything except one identified contribution. Against B, the misspecification is
**diffuse** — contestant 2 is wrong everywhere by a little rather than wrong in one
identifiable way — and an ambiguous `1 ≈ 2 ≈ 3` outcome would be
*unattributable*: it cannot distinguish "declared forms do not buy reach" from
"declared forms buy reach but coupling-blindness consumed it" from "the fits were
poor." Establishing the mechanism on a localised, named absence and *then* asking
whether the benefit survives realistic coupling-blindness is the ordering that
makes both outcomes readable.

**Consequences of the ordering, stated so the follow-up is not treated as a
fallback:**

- Generator B is a **robustness check on an established result**, not a rescue
  attempt for an ambiguous one. It runs whether or not A is clean.
- **If A shows no benefit, B is unnecessary and that is itself the finding.** A
  declared form that cannot beat a free-form operator when the only missing physics
  is one named term will not do better when the missing physics is an entire
  coupling. Report A's negative and stop; do not run B in the hope of a different
  answer, which would be exactly the post-hoc search ADR-041's pre-registration
  discipline exists to prevent.
- **Report both, never pooled.** A measures whether the mechanism works at all; B
  measures whether it survives realistic conditions. A single combined figure
  would answer neither.

**Both generators avoid E-12's circularity, and it is worth being explicit about
why that is the binding constraint on either.** E-12 found that Spec §4.6 rung 4
could be "validated" by fitting a formula against data generated by that same
formula, recovering it to machine precision by construction rather than by
measurement. An extrapolation experiment whose ground truth *is* contestant 2's
form would reproduce that failure at larger scale, and contestant 2's win would be
an identity rather than a result. Generator A is therefore **not** bare Kocks–
Mecking: the withheld drag term is what keeps contestant 2 an approximation rather
than an exact recovery, and it is the minimum departure that achieves this. A
generator that differed from contestant 2's form by *nothing* would be circular; A
differs by exactly one named term, which is the smallest non-circular design and
hence the most attributable.

**Contestants — the same four against each generator, held out over a region of
control space. Every contestant sees identical ground truth within a generator;
results are never pooled across generators:**

1. **Free-form operator, generic constraints only** — the v1.3 incumbent
   (`omi.learning` + `omi.constraints`).
2. **Constitutively-constrained, correct form, parameters fitted** — "correct"
   meaning the canonical form, *not* the generator: against Generator A it lacks
   the withheld drag term, against Generator B it lacks the coupling. A strong
   prior and expected to win, but not an identity — see the circularity note
   above. A calibration arm, not the claim.
3. **Constitutively-constrained, deliberately misspecified** — **the realistic
   case and the one that matters**, because real declared physics is canonically
   right and locally wrong.
4. **Tabular baselines from `baseline.py`, unchanged** — the honest external
   comparator, exactly as M10.2 used them.

**Contestant 3 gets two arms, designed rather than chosen between, reported
separately and never pooled:**

- **3a — a missing mechanism**: Kocks–Mecking with the recovery term `−k₂ρ`
  dropped.
- **3b — a missing dependence**: a temperature-dependent parameter treated as
  constant.

They fail differently — 3a degrades monotonically with accumulated strain, 3b
with thermal excursion — so a pooled figure would hide which kind of
misspecification the extension does and does not survive. That distinction is
the practically useful one for a reader deciding whether to declare a form they
are only partly sure of.

**Hold-out design.**

- **Grouped by control-space region, never randomly** (CLAUDE.md invariant 6, and
  structurally impossible to violate at the loader level). A declared region of
  `𝒰_adm` is withheld entirely.
- **The held-out region must lie partly outside the declared validity ranges**, so
  ADR-043's extrapolation report is *exercised* rather than merely present. An
  experiment held out only inside the envelope would test interpolation and call
  it reach.
- **Rollout-length error curves for every contestant** (invariant 7), never
  one-step error alone.
- **Class B readouts return distributions** (invariant 4), with extrapolation
  ratio and join threshold stated.
- **The extrapolation factor is reported alongside every error figure**, so error
  can be plotted against declared-envelope distance. That plot is the claim.
- **Seeded generators throughout; every measured quantity recorded via the
  `observe` fixture** (CLAUDE.md §7), not only the verdict.

**The claim structure, stated before running so it cannot be read post hoc.**
Reported per generator, and the generator is part of every quoted figure:

| Comparison | Generator | What it measures |
|---|---|---|
| **gap(3, 1) and gap(3, 4)** | **A** | **the claim the paper would actually make**: does canonically-right-locally-wrong declared physics beat a free-form operator and a tabular baseline outside the envelope, when the missing physics is one named term |
| gap(2, 3a) and gap(2, 3b) | A | robustness to form misspecification, by kind, attributable because the absence is localised |
| gap(2, 1) | A | the ceiling, for context only |
| gap(3, 1) and gap(3, 4) | B | whether A's benefit **survives** realistic coupling-blindness — a robustness check on an established result, not a second attempt at the claim |
| any comparison | A vs B | **not computed.** The generators differ in what they withhold, so a cross-generator gap has no interpretation. |

**Pre-registration.** Thresholds are set via ADR-041's
`decision_sensitive_threshold` **before** either sweep runs, with the declared
minimum effect and cost ratio recorded in the design document, and the *same*
thresholds applied to both generators. A threshold chosen after seeing the
residuals is not a threshold; a threshold re-chosen for Generator B after seeing
Generator A is worse, because it would convert the robustness check into a search.

### Amendment (after M11.4, before M11.5) — a hold-out must be shown to discriminate before it is registered

**This amendment generalises past the experiment that occasioned it, so it is
written as a standing requirement rather than as an M11.5 detail.**

M11.4 ran this design exactly as specified and produced a null that turned out to
be **uninformative rather than negative** (`docs/M11.4-EXTRAPOLATION.md`;
`docs/V1.4-EDITS.md` E-39). The cause was in the hold-out, not the hypothesis: the
axis withheld was strain rate, and Kocks–Mecking has no strain-rate dependence, so
the declared form predicted a constant along exactly the axis the experiment varied.
Candidate and baseline agreed **by construction rather than by measurement**, and no
effect size could have been detected however large.

Nothing above forbade that. The hold-out design section required the region to be
grouped, to lie partly outside the declared validity ranges, and to be withheld
entirely — every one of which M11.4 satisfied. The missing precondition is added
here:

> **REQUIREMENT (hold-out discrimination).** Before a hold-out is registered, it
> MUST be shown that the declared-form contestant and the free-form contestant
> **diverge along the held-out axis** — that their disagreement *grows* as the axis
> is pushed, rather than sitting at an offset already visible in-envelope. The
> check is M11.4's own post-hoc diagnostic, promoted to a precondition: fit both
> contestants on in-envelope data and score them, at two probe points along the
> axis, against a ground truth **with the withheld term removed**. If the axis
> carries no signal, or the two track it together, the comparison is vacuous
> *regardless of effect size* and the axis MUST be rechosen. A registered hold-out
> that has not passed this check is not pre-registered, it is merely early.

Four points about how the requirement is discharged, each of which is a decision
in its own right:

1. **The check is executable, not a note.** `omi.proposed.holdout` implements it as
   `check_hold_out_discriminates`, returning a result dataclass with every
   criterion and the numbers behind it. E-39 proposes wording for Spec §9.3; this
   repository's contribution is a runnable version of that wording, which is
   stronger evidence for the proposal than the proposal is for itself.
2. **Building it corrected E-39's own proposed wording, and that correction is the
   more valuable half.** E-39 proposed requiring the candidate and baseline to make
   "materially different predictions" across the held-out region. Implemented
   literally — disagreement measured against a declared minimum effect — **the
   criterion cannot separate the two axes this repository has run.** Under the same
   dry-run discipline, M11.4's vacuous strain-rate axis shows disagreement
   0.339 → 0.354; M11.5's usable accumulated-strain axis shows 0.032 → 0.472. Those
   far-point magnitudes are the same order, so no bar admits one without admitting
   the other. E-39's wording is not merely imprecise; it is inoperable.

   Two quantities do separate them. The withheld-free truth's own variation along
   the axis is **exactly 0.000** on the vacuous axis against 3.806 on the usable
   one — Kocks–Mecking has no strain-rate dependence and neither did the physics it
   was scored against, so nothing there could distinguish any model from any other.
   And the disagreement's *growth* separates them by a factor of fourteen: 1.05
   against 14.57. On a vacuous axis the two models are parallel, differing by an
   offset the training data already exhibits, and going further reveals nothing.
   An extrapolation test is a question about what happens as you go further, so its
   precondition has to be about growth rather than difference. Filed as
   `docs/V1.4-EDITS.md` **E-41**; the corrected wording supersedes E-39's for the
   paper. M11.4's axis fails **all three** of the implemented criteria, which is
   the retro-validation that the check is discriminating rather than decorative.
3. **The check runs strictly in-envelope, on a dry-run split along the candidate
   axis.** It may not touch the region that will actually be held out. The
   temptation is real — scoring on the true hold-out against a withheld-free truth
   is a *more* direct measurement — but in a synthetic study the withheld term's
   contribution is known, so that quantity and the pre-registered one differ by a
   subtraction the experimenter can perform. An in-envelope dry run leaks nothing
   and separates the two axes by a factor of fifteen, which is margin enough that
   the loss of fidelity costs nothing. A check that cannot be run before the sweep
   is not a precondition.
4. **Three failure modes, kept distinct, because they call for different
   responses.** *Inert axis*: the withheld-free truth barely moves along the axis,
   so there is no physics here for either model to get right — M11.4's failure at
   its root, and its clean truth was **exactly** constant along the rate axis.
   *Parallel models*: the truth moves but both models track it together. *Adverse*:
   they diverge, but the candidate is worse than the baseline even against the
   withheld-free truth, so its structure is doing harm rather than work along this
   axis. The third is a real finding and a different experiment from the one this
   ADR describes; it must not be run as though it were. Collapsing the three into a
   bool would repeat in miniature the confusion CLAUDE.md invariant 8 exists to
   prevent.

**A consequence for the free-form contestant that is easy to miss.** Contestant 1's
fairness is defined *relative to the held-out axis*, not in the abstract. M11.4 gave
it `ln γ̇` as a feature precisely so it had the chance to learn the withheld
rate-dependent physics. Changing the held-out axis therefore **obliges** a
re-specification of contestant 1 for the new axis; carrying the old one over
unchanged would satisfy the letter of "the same four contestants" while converting
the incumbent into a straw man. Whenever the axis changes, state explicitly what
contestant 1 was given so that it is not one.

**The negative result is a deliverable, and it terminates the experiment.** If
`gap(3, 1) ≤ 0` on **Generator A** — misspecified declared physics does no better
than a free-form operator with generic constraints outside the envelope, when the
only withheld physics is a single named term — then the extension's value
proposition fails. Report it, file it in `docs/V1.4-EDITS.md` as a correction to
E-32's own argument, and **do not run Generator B**: a form that cannot beat
free-form under the most favourable non-circular conditions available will not do
better when an entire coupling is missing, and running B at that point would be
looking for a more agreeable answer rather than a more informative one.

The experiment is designed to be able to return that negative honestly:
contestant 1 is not a straw man, and contestant 4 is unchanged from the baseline
characterisation that already beat parts of this repository's own machinery.

---

## ADR-046 — Where a declared constitutive form lives, so Core §4's comparability survives

**Status.** Accepted. Decides the question M11.3 raised; supersedes ADR-043's
"6d" placement (ADR-043's *content* stands, only the sub-item's location changes).
**Finding.** `docs/V1.4-EDITS.md` E-32, with the M11.3 measurement.
**Milestone.** M11.3 exit, before M11.4.

**The problem, measured rather than argued.** Core §4 makes cross-declaration
comparability the mechanism that "converts a collection of examples into evidence
of generality." M11.3 established that no way of declaring a constitutive form
preserves it: naming the forms in item 6 makes `omi.interface.diff` raise, and
declaring them outside the seven items makes two substantially different domains
diff as identical. A decision is needed, not only a record.

**The deciding measurement, taken before choosing.** A declaration naming a
constitutive form in item 6 **cannot be diffed against itself**:

```
diff(d, d)  ->  ValueError: ... classify_invariant refuses to guess
```

That is not a comparison failure between two domains; it is the declaration
failing to be a well-formed input to Core §4's own comparative machinery at all.
It settles option (a) below on its own.

**Options weighed.**

**(a) Role-aware `diff`** — item 6 stays the home; `diff` gains classification so
constitutive entries are compared as constitutive rather than passed to
`classify_invariant`. *Rejected.* Two independent reasons. First, the measurement
above: under (a) the v1.3 core stops being a valid v1.3 declaration — it is
un-diffable by v1.3 tooling even against itself — which breaks the property
ADR-042's composition guarantee rests on and makes this repository's v1.3 audit
uncitable for the variant. Second, `diff` is v1.3 code, so a role-aware version
would have to live in `omi.proposed` anyway; (a) therefore incurs (b)'s cost of a
new declaration surface *without* (b)'s benefit of leaving v1.3 intact.

**(b) A new interface item for constitutive forms.** *Chosen.* Item 6 keeps its two
roles and its two categories exactly as v1.3 has them, so a v1.3 core remains a
valid, diffable v1.3 declaration; the new item is diffable on its own terms; and the
extension is purely additive, which is ADR-042's composition principle applied at
the interface level rather than only in code.

**(c) `diff` reports incomparability instead of raising.** *Adopted as a separate,
smaller proposal, not as the answer.* It does not restore comparability — a diff
saying "incomparable on dimension X" reports that two declarations differ without
reporting how, which is barely more than the current blindness, and Core §4 needs
the comparison to be informative rather than merely non-fatal. But it fixes a real
brittleness that (b) leaves untouched and that generalises past this entry: Core §4
asserts declarations are comparative and never states what the comparison does with
a dimension it cannot classify, so the mechanism is fragile to **any** future
extension, not just this one. Proposed as part (3) of E-32's revised wording.

**On the arity objection, which is the strongest argument against (b).** Adding an
eighth item is a larger claim than E-32 made on its own. It is not a larger claim
than the ledger already makes: E-29 proposes an eighth item (Parameters) for an
independent reason, and §1's finding 5 already asks whether the seven items are a
closed list, noting that "five independent gaps of the same shape suggest the number
seven is doing more work than the content supports." Choosing (b) does not introduce
that question — it forces it to be answered, which is the more useful outcome for
v1.4 and is what a decision is for.

**And (b) is what this repository already built**, which is worth stating plainly
rather than presenting the choice as free: `ExtendedDeclaration(v13_core,
constitutive_forms)` is structurally an eighth item already. So M11.3's "the cores
are identical" finding is an artefact of the eighth item living *outside* the seven
where v1.3's diff cannot see it — not of the content being inexpressible. The
decision is to say so in the framework rather than leave the repository's structure
implying it.

**What changes in the ledger.** E-32's proposed wording is revised: item 6 is
role-scoped to **6a–6c** (the split still fixes §7.1's omitted third candidate
kind), constitutive forms become a **new item**, and part (3) proposes the
comparability failure mode Core §4 never states. The M11.3 measurement is recorded
as what forced the revision — a proposed wording changed by a measurement is the
ledger working as intended, not a defect in the earlier proposal.

**What this repository implements.** Nothing new: the extension already carries the
forms outside the seven items, which is (b). `omi.interface.diff` is **not**
changed — that is v1.3 code, and (c) is a proposed framework edit rather than a
repository change (ADR-042). The one repository consequence is that
`omi.proposed.item6`'s `CONSTITUTIVE_FORM` member now documents itself as a *new
item* rather than as sub-item 6d.

**What would change this decision.** If v1.4's authors settle finding 5's
closed-list question in favour of seven fixed items, (b) is unavailable and (c)
becomes the fallback — with the cost, stated above, that the comparison then reports
difference without reporting its content. If that happens, E-32's revised wording
should be re-read as proposing 6d after all, and this ADR superseded rather than
edited.

**Pinned by.** `tests/test_flagship_constitutive.py::test_the_two_v13_cores_are_indistinguishable`
and `::test_the_other_road_is_closed_too_diff_refuses_an_honest_item_6` — the two
halves of the measurement this decision rests on.

---

## ADR-047 — The fair-axis experiment: hold out accumulated strain, where the declared form has content

**Status.** Accepted.
**Milestone.** M11.5 (docs/ROADMAP.md)
**Depends on.** ADR-045 as amended (the hold-out-discrimination requirement),
ADR-043 (the declaration), ADR-046 (where the form lives).

**What changed and what did not.** M11.4's design error was the *axis*, not the
experiment. ADR-045's four contestants, two misspecification arms, cost ratio,
threshold procedure, ceiling caveat and negative-result-is-a-deliverable rule all
carry over unchanged. This ADR records the three things that must change with the
axis, and one that must change *because* the axis changed.

### 1. The held-out axis is accumulated strain

Kocks–Mecking's content is a **balance between storage and recovery** that produces
saturation, and saturation is a statement about accumulated strain. That is the
axis along which the declared form makes a prediction a generic surface does not
have: `ρ → (k₁/k₂)²` as `γ` grows, rather than continued growth. Holding out long
deformation programmes therefore tests the form where it says something, which is
exactly what M11.4 failed to do.

Training draws `γ ∈ [0.1, 1.0]`; evaluation draws `γ ∈ [2.0, 6.0]`. Grouped by
region, never randomly (CLAUDE.md invariant 6). The other control axes — strain
rate and temperature — are sampled from the **same** ranges in training and
evaluation, so accumulated strain is the *only* thing withheld and every gap
remains attributable in ADR-045's sense.

**This is a control-space region in Core §3.2's sense**, not a time index: `𝒰`'s
elements are functions of time and the total imposed strain is a property of the
programme, so "programmes that deform further than the apparatus has been run
before" is a region of `𝒰_adm`, withheld entirely.

### 2. The withheld term is one the declared form can see

**Generator C.** Kocks–Mecking with a temperature-dependent recovery coefficient,
plus one named withheld term — **dynamic recrystallisation above a critical
accumulated strain**:

```
dρ/dγ = k₁√ρ − k₂(T)·ρ − k_drx·ρ·max(0, γ − γ_c)
```

Three properties, each load-bearing:

- **Identically zero below `γ_c`, and `γ_c` is set at the upper edge of the
  training range.** So over the whole training set contestant 2's form is *exactly*
  the generator's and its in-envelope error is parameter estimation only — the
  property that made Generator A attributable, preserved verbatim.
- **It is a departure the declared form is dimensionally capable of representing
  wrongly.** DRX consumes stored dislocation density, so the withheld term is
  proportional to `ρ` — the same shape as Kocks–Mecking's own recovery term. A
  fitted declared form can therefore *partly absorb* it by inflating `k₂`. This is
  what the user's requirement asks for and it is what makes 3a and 3b
  interpretable: 3a has no removal term at all and cannot absorb any of it, 3b has
  one but cannot make it temperature-dependent. Against a withheld term the form
  could not represent in any parameterisation, both arms would fail identically and
  the comparison would collapse back toward M11.4's.
- **It is not bare Kocks–Mecking** (ADR-045's circularity constraint, E-12):
  contestant 2 remains an approximation, not an identity.

`γ_c` is a constant rather than temperature-dependent. Physically it does fall with
temperature, and making it do so would sharpen 3b's disadvantage — which is the
reason not to. One named withheld term with one parameter keeps attribution clean;
adding a second dependence would buy a bigger effect at the cost of the property
M11.4's post-mortem showed matters most.

### 3. Contestant 1 must be re-specified for the new axis, and it is the crux

ADR-045's amendment makes this an obligation; here is what was done. M11.4's
contestant 1 was a response surface fitted at unit strain and extrapolated as
`surface(q) × γ` — **linear in accumulated strain by construction**. On a strain
hold-out that is not a baseline, it is a straw man: it cannot saturate, so the
declared form would beat it for a reason that has nothing to do with declared
physics and everything to do with an extrapolation rule nobody would choose.

M11.4's γ=4 rollout observation — the "untested hypothesis" that document recorded
— is therefore **suspect on exactly this ground**, and M11.5 is the test of it. It
is entirely possible that the 2× separation at γ=4 was an artefact of `surface × γ`
rather than evidence for declared physics. If so, that is a finding and it is
recorded as one.

**Contestant 1 for M11.5 is a free-form rate law, integrated.** A generic
polynomial surface in `(ρ, ln γ̇, T/T_ref)` giving `dρ/dγ`, with positivity of the
state enforced architecturally (`omi.constraints`, never a penalty — CLAUDE.md
invariant 5), advanced by the **same integrator at the same step count** as every
declared-form contestant. This is the honest v1.3 incumbent: OMI's free-form
operator is a *learned evolution operator that is stepped and composed*
(`omi.learning` + `omi.chain`), not a direct input-to-output regression. It gets no
declared form, but it does get the structural fact that evolution accumulates —
and an integrated rate law that learns `f(ρ) < 0` for large `ρ` **can** saturate.

That makes M11.5 a much harder test than M11.4 and the result correspondingly worth
more. It is also the honest one: if the declared form's advantage disappears once
the baseline is allowed to be an operator rather than a surface, then the advantage
was never about declared physics.

**The tabular baselines (contestant 4) keep their character deliberately.** They
gain `γ` as a feature and are fitted across the in-envelope strain range, which is
the natural tabular use, but they remain direct regressors — because that is what a
tabular baseline *is*, and M10.2 already characterised how such models extrapolate.
Turning them into integrators would make them a second copy of contestant 1 and
delete the external comparator.

### 4. The declared form is published as a second object, not an amended one

Registering a hold-out outside the declared window requires `KOCKS_MECKING` to
declare a bound in accumulated strain — which it should, since the strain window is
where DRX intervenes and the form's temperature bound already names that mechanism.
It cannot simply be added: ADR-043 requires every declared bound to receive a value
at `report()` time, so extending a form's validity range **breaks every existing
caller**. M11.5 therefore declares `KOCKS_MECKING_STRAIN_WINDOWED` alongside the
original rather than amending it, leaving M11.3's and M11.4's artefacts byte-stable.

The consequence is worth stating rather than absorbing: **declared validity ranges
as designed here are append-hostile.** A domain that learns its form has a limit it
had not previously declared must either break its consumers or publish a second
form, and then Core §4's item-6 comparison sees two forms where the physics is one.
This is a consequence of ADR-043's strictness (a missing value raises rather than
being skipped), which remains the right default — silently ignoring an undeclared
bound is how a validity range stops meaning anything. But the refinement path is
missing, and that is a gap in the *extension's* design rather than in the Spec.
Filed as `docs/V1.4-EDITS.md` E-40.

### The claim structure, unchanged from ADR-045 and restated so it is not re-read post hoc

`gap(3, 1)` and `gap(3, 4)` on Generator C are **the claim**. `gap(2, 3a)` and
`gap(2, 3b)` are robustness by misspecification kind. `gap(2, 1)` is the **ceiling,
reported with ADR-045's caveat and never as the headline**. Rollout-length curves
for every contestant; extrapolation factor reported alongside every error figure.
Thresholds via ADR-041, registered in their own commit before any sweep code exists.

**A negative result here means something, and that is the whole point of M11.5.**
M11.4's null was uninformative because the axis was vacuous. Once the
discrimination check passes, a null says what it appears to say: that declaring a
constitutive form buys no extrapolation reach over a free-form *operator* on an axis
where the form demonstrably has content. That is a real result about the v1.4
extension's central claim and it goes in the paper as one.

---

## ADR-048 — v1.5's purpose extension: the framework decides what to do next, and prediction becomes a means

**Status.** Accepted — **declaration only. No Core or Spec text is edited by this
ADR, and no code changes.**
**Track.** v1.5 planning, Part 1 (`docs/V1.5-PLANNING-BRIEF.md` records the brief).
**Supersedes nothing.** Extends the scope every prior ADR was written under.

### The decision

**v1.3's purpose is representing and learning PSR linkages. v1.5's purpose is
deciding what to do next under uncertainty.** Prediction is retained in full and
demoted to a *means*; the diagnostics become the product.

This is a scope change and not a feature, so it is declared here rather than
allowed to accumulate. Every ADR from ADR-001 to ADR-047 was written under the
v1.3 purpose; none is withdrawn, but each is now read against a larger objective,
and where that changes what an ADR should have decided, the change is recorded as
a new ADR rather than by editing the old one.

### What the extension promotes and what it demotes

The framework's existing machinery does not change; its **ranking** changes, and
the ranking was previously implicit in prose rather than declared. Making it
explicit is most of this ADR's content.

| Machinery | v1.3 standing | v1.5 standing |
|---|---|---|
| Danger-score triage (Core §3.8, Spec §3.3) | one diagnostic among several | **spine** — it is the per-direction answer to "what do I not know that matters" |
| The intervention table (`docs/V1.4-EDITS.md` §11) | a reading *of* the ledger | **spine** — the six practitioner interventions are the output space |
| Refusal criterion (Core §3.9) | a credibility argument | **spine** — a first-class deliverable, on equal footing with an answer |
| Blocking trichotomy (Spec §1.7) | sufficiency bookkeeping | **spine** — it names which purchase the deficit implies |
| Asymmetric costs / decision layer (Spec §7.3) | selects within a degeneracy | **spine** — supplies the objective the rest is ranked against |
| Class B machinery (Core §3.6, Spec §4) | "one of its main practical payoffs" | **supporting result** |
| Erasure analysis (Core §3.9 condition (a), Spec §2) | headline v1.3 result | **supporting result** |
| Forward accuracy, rollout curves, calibration | what the framework is judged on | **necessary but not sufficient** — inputs to a decision, not the deliverable |

**Demotion is not deletion, and this must not be misread.** Class B distributions
and erasure inventories remain required at their existing conformance levels and
remain fully tested. What changes is that they no longer answer the framework's
top-level question on their own. A v1.5 implementation that reports a beautiful
Class B tail and cannot say which measurement to buy next has not delivered.

**Why the demotion is defensible rather than fashionable.** M11 supplies the
argument. `docs/V1.4-EDITS.md` **E-42** measured a case where forward accuracy
against the full truth ranked six models *opposite* to their fidelity to the
physics they expressed — the winner was fourth of six on the quantity that
mattered and first on the quantity being scored. If the framework's own
prescribed criterion (Spec §9.3) can inverse-rank models, then forward accuracy
cannot be the top-level objective without qualification. The purpose extension is
the principled version of a correction M11 forced empirically.

### Existing conformance results: the user's recommendation, accepted, with a mechanism

**Accepted as proposed.** Existing conformance results remain **valid and citable
as v1.3-purpose results**; v1.5 conformance is a **separate claim**; existing
results are **not** silently reinterpreted. Concretely: flagship's OMI-1 and
contrast's OMI-0 stand unchanged and unqualified *as v1.3 claims*, and neither
becomes a v1.5 claim by the passage of time or the merging of this branch.

Three points make this more than an assurance.

1. **The mechanism already exists, and this is its second consumer.**
   `omi.conformance.ConformanceReport` carries a required
   `omi.interface.SpecificationVersion`, and `compare_reports` refuses to compare
   across versions with no suppression flag (E-35, ADR-042). That was built at
   M10.4 for a smaller reason — that an archived level name is not
   self-describing once a second version exists. The purpose extension is a
   larger instance of exactly that shape, and it validates E-35's proposal rather
   than needing new machinery. A v1.5 report will carry `PROPOSED_DECISION_EXTENSION` and will
   therefore be structurally incomparable with the archived v1.3 results.

2. **But version-stamping is only sufficient if purpose is monotone with version,
   and it is not.** A v1.3-purpose chain can be re-reported under a v1.5 version
   stamp without ever declaring a decision; a v1.5 decision layer can be bolted
   onto a chain whose conformance evidence was gathered for prediction. The
   version stamp does not separate those. **A conformance claim needs a declared
   *purpose*, not only a declared version.** Filed as a framework finding —
   `docs/V1.4-EDITS.md` **E-43** — because it is a defect in Spec §9.1's text and
   not merely in this repository's implementation of it.

3. **The audit-preservation gate is the enforcement.** Every observation recorded
   before M11 is byte-identical today (267 audited `(test, name)` pairs — ADR-069 — `audit/baselines/v13-items7.json`,
   ADR-042). The same discipline applies to v1.5: the purpose extension must not
   move a single pre-existing measured quantity, and if it does, that is the
   signal the extension was not the additive change this ADR claims. The gate is a
   standing requirement of the v1.5 track, not a milestone check.

### Proposed rewording of Core §1.1 and the Abstract — proposed, NOT applied

Recorded here so it can be reviewed as text before anyone edits the framework
documents. **Neither document is touched by this ADR.**

**Abstract, opening sentence — proposed replacement.**

> OMI is a physics-informed mathematical framework for **deciding what to do next
> in PSR systems under uncertainty**: systems of structured matter whose internal
> organisation evolves under driving conditions, and whose measurable responses
> are mediated by that organisation. It represents and learns
> Process–Structure–Response linkages as a directed graph whose nodes are
> infinite-dimensional state spaces and whose edges are operators — and it treats
> that representation as a **means**. The framework's product is a set of
> declared, measured diagnostics that say which action the current evidence
> supports: which quantity is dangerous, which measurement would resolve it,
> which purchase the residual deficit implies, and when to refuse. Prediction
> serves those diagnostics; it is not the deliverable.

**Core §1.1 Scope — proposed replacement of the three-feature test with four.**

The existing test (control axis; hidden internal state; structure-mediated
response) is a test for **representability**. It is silent on whether there is
anything to decide, and a framework whose purpose is deciding must scope on that.
Proposed fourth feature:

> - a **decision under uncertainty** — a recurring choice among actions
>   (set a control, commission a measurement, buy data, change the material,
>   refuse) whose consequences are **asymmetric**, so that the cost of being
>   wrong in one direction differs from the other.

With the consequence stated plainly, as §1.1 already does for its exclusions:

> A system exhibiting the first three features but not the fourth is
> **representable but not a v1.5 subject**: OMI will model it and will have
> nothing to recommend. Claiming such systems would make the purpose
> unfalsifiable, in the same way that claiming domains with no control axis
> would have weakened v1.3.

**A consequence for this repository's own domains, stated rather than discovered
later.** Neither flagship nor contrast presents a real decision at each step —
both are fixed chains evaluated once. Under the proposed §1.1 they satisfy three
of four features. That is precisely why v1.5 adds a sibling domain with a
controllable composition axis and a decision at each step (Part 5), and it means
**Core §7.3's generality argument does not yet cover the v1.5 purpose.** Recorded
now so Part 5 is understood as filling a declared gap rather than adding a third
example for its own sake.

> **AMENDMENT (before Part 2). The paragraph immediately above is wrong, and the
> error is instructive enough to correct in place rather than quietly.**
>
> It applies a **system-level scope test to an implementation**. Proposed §1.1
> opens "The framework applies to **systems** exhibiting … features together" — the
> test is on the domain being modelled, not on how deeply this repository simulates
> it. That flagship and contrast are each built here as a single forward chain
> evaluated once is a fact about `build.py`, not about whether a rolling line or a
> cell under service presents a recurring asymmetric decision. Conflating the two
> is precisely the class of error this ledger exists to catch, and it produced a
> false conclusion about the framework's own generality evidence.
>
> **Corrected finding: both existing domains satisfy the fourth feature.**
>
> **Contrast (usage decision) — qualifies.** *Recurring*: `CyclingStep` models one
> usage interval under a held current, and service is a sequence of them; the
> erasure inventory is **empty** and `sei_thickness_monotone_nondecreasing` is a
> declared invariant, so state accumulates irreversibly and each interval's choice
> is carried forward. Sequential choice with irreversible accumulation is the
> canonical decision-under-uncertainty setting, not a marginal instance.
> *Actions*: item 2 declares a usage-determined `𝒰` bounded by manufacturer limits
> (set a control); item 5's suite is genuinely poor and M3 **measured** contrast
> leaving a larger fraction of target variance dangerous than flagship
> (`contrast_unresolved_danger_fraction` > `flagship_unresolved_danger_fraction`,
> `tests/test_domain_triage.py`), so commissioning a measurement is live and
> already priced; `dendrite_risk` is Type-0/**Class B**, so derate-or-retire is
> available. *Asymmetric*: a Class B rare-event failure distribution against
> conservative derating is the asymmetry Core §5's decision layer already names.
>
> **Flagship (process decision) — also qualifies, and needs no composition axis to
> do so.** A line sets a grade and route per unit; the actions are apparatus
> settings (process inverse), a measurement from a rich suite where `ΔV_c/cost` is
> the framework's one priced intervention, and rework/downgrade/scrap as refusal.
> The asymmetry is **already written into the Spec**: §7.3 requires carrying "field
> failure, downgrade, rework, and re-run" as costs that "differ by orders of
> magnitude." Part 6's composition axis adds a *second, different* decision — what
> to make — rather than supplying the first.
>
> **So Core §7.3's argument survives the purpose extension at the level of scope**,
> and v1.5's generality evidence is two decision *kinds* (usage and process), not
> zero. Item 14 of the inaccuracy table below is revised accordingly.
>
> **What does not survive, and it is a weaker claim than the one withdrawn.**
> Scope is satisfied; **demonstration is not.** No domain's declaration expresses
> its decision — there is no interface item for it, which is item 4 of the table
> below — and no implementation has been driven through a decision loop. So §7.3
> establishes that the framework's *structure* covers two decision kinds, and does
> not yet establish that its *decision machinery* works on either.
>
> **Consequence for Part 5, restated.** The SDL domain is no longer filling a scope
> gap. It is (a) the domain where the decision loop is actually exercised rather
> than declared, and (b) a **third** decision kind — campaign/discovery, deciding
> what to make — alongside usage and process. Both are better reasons than the one
> this ADR originally gave, and Part 5 should be designed against them.
>
> **A distinct framework finding fell out of the correction and is filed as E-44**:
> §1.1's scope features are never declared and never checked, three of the four are
> only *indirectly* evidenced by interface items, and the fourth has no item at all
> — so a domain in scope whose declaration is silent about the decision is
> indistinguishable from a domain out of scope. This ADR's original error is the
> worked example of that defect biting a careful reader.

### The ledger's target version, and its name

The standing requirement asks whether v1.5 supersedes v1.4 as the target, and
records that this is itself a decision.

**Decided: v1.5 is the target; the ledger keeps one continuous numbering and
keeps its current filename.** New entries continue at **E-43**; no number is ever
reused; the file remains `docs/V1.4-EDITS.md`.

The filename is now imprecise, and that is the lesser cost. It is retained
because **two commit-stamped snapshots cite that path** (`docs/REVIEW_PACK.md`,
`build/REVIEW-EXTRACT.md`) and CLAUDE.md §10 forbids editing a snapshot's body —
a rename would leave those citations permanently dangling with no legal
correction available. Splitting into a second file was rejected for a different
reason: the ledger's provenance discipline (implementation-attempt vs
`[domain-assessment]`) and its "never renumbered, never reused" rule both work
because there is exactly one place to look. The mitigation is a header note in the
ledger recording that its target is v1.5 and why the v1.4 name persists — the
same treatment E-34's retired number already receives.

### Consequences

- **Nothing in Core or Spec is edited by this ADR.** The rewording above is a
  proposal for review; the inaccuracy list below is its evidence.
- **Every subsequent v1.5 ADR is read against the extended purpose**, and where a
  v1.3-era ADR would now decide differently, a new ADR supersedes it explicitly.
- **Two new obligations attach to any future v1.5 conformance work**: a declared
  purpose on the report (E-43), and a declared decision plus intervention set on
  the instantiation (which is Core §4's item count, below).
- **The v1.3 results are frozen, not reinterpreted.** `docs/M11-RECORD.md`,
  `docs/M10.2-BASELINE-CHARACTERISATION.md` and the conformance demonstrations
  remain v1.3-purpose evidence and are cited as such.

### Sections whose text the extension makes inaccurate

The gate deliverable. **Primary** = the text becomes *false* under the extended
purpose. **Secondary** = the text becomes *incomplete or misranked*. **Wording** =
a collision or a version-scoped headline. Nothing below is edited yet.

| # | Section | Kind | What breaks |
|---|---|---|---|
| 1 | Core Abstract ¶1 | **Primary** | "a framework for representing and learning PSR linkages" is the purpose statement; under v1.5 that is the means |
| 2 | Core §1.1 Scope | **Primary** | the three-feature test is a representability test and is not sufficient to scope a decision framework — a system can pass all three and present nothing to decide |
| 3 | Core §1.2 Claims | **Primary** | the claim list omits the decision product entirely; and the non-claims omit the one v1.5 most needs (OMI does not claim the recommended action is optimal, only that it is accounted and its basis declared) |
| 4 | Core §4 interface | **Primary** | "a domain enters by supplying **seven** items… Nothing else is required, and **nothing less suffices**" — under v1.5 the declaration must also carry the decision (targets with asymmetric costs) and the available intervention set. The count is wrong and "nothing less suffices" is false. Collides with the eighth-item proposals already open in E-32, E-40 and ADR-046 |
| 5 | Core §5 decision layer **[Pass C]** | **Primary** | "**A corollary** reorganises the whole error budget — accuracy requirements derive from the decision." Under v1.5 this is not a corollary, it is the organising principle. The word is the defect |
| 6 | Core §6.1 falsification | **Primary** | all six criteria test representational or predictive adequacy; **not one falsifies the decision claim.** A v1.5 implementation could satisfy all six and be useless for deciding, or fail criterion 4 and be valuable. Criterion 4 ("fail to beat tabular baselines on forward accuracy and prospective hit rate") now scores the demoted quantity — and E-42 measured that this criterion can rank models opposite to their physical fidelity |
| 7 | Spec §9.1 conformance | **Primary** | OMI-0/1/2 require no declared decision, no intervention set, no evaluation of the refusal criterion, and no triage-to-action mapping. An implementation can reach **OMI-2 and deliver nothing the v1.5 purpose asks for.** This is where the "v1.3 results stay v1.3 claims" decision does its work |
| 8 | Core §1 Introduction ¶2 | Secondary | "OMI replaces tabular mappings with an operator-graph representation" presents the representational contribution as *the* contribution |
| 9 | Core §2.2 state selection | Secondary | framed as a bias–variance optimisation for *learnability*; under v1.5 the objective is decision-relevance, which is Spec §7.3's cost machinery — the facility E-36 found exists and is never applied |
| 10 | Core §3.6 Class B | Secondary | presents the two-tier coupling as "one of its main practical payoffs"; that ranking is now demoted to supporting |
| 11 | Core §3.9 dichotomy + refusal | Secondary | erasure analysis demoted; refusal *promoted* but its text presents refusal as a credibility argument ("more credible than one that always answers") rather than as a primary deliverable |
| 12 | Core §5 inverse taxonomy | Secondary | control/structure is incomplete — "deciding what to do next" includes deciding what to *make*, which is Part 3's composition inverse |
| 13 | Core §6.2 open problems | Secondary | the list is entirely representational |
| 14 | Core §7.3 what the contrast establishes | Secondary | **revised by the amendment above.** Both domains *do* satisfy the fourth scope feature (contrast: usage decision; flagship: process decision, its costs already enumerated in Spec §7.3), so §7.3's argument survives at the level of scope and covers two decision kinds. What §7.3's text does not say, and now must, is that scope coverage is not demonstration: no declaration expresses its decision and no implementation has been driven through a decision loop, so the section overstates what two instantiations establish *for the v1.5 purpose* while understating the coverage they do have |
| 15 | Core §8 positioning | Secondary | positions against representational lineages (MKS, ICME, assimilation, neural operators). The v1.5 neighbours are Bayesian experimental design, active learning / BO, value of information, and sequential decision-making under model uncertainty. The **[Pass D]** lineage note is inadequate in a new direction |
| 16 | Core Appendix C | Secondary | summary of structural claims, written against the old purpose |
| 17 | Spec §1.7 blocking trichotomy | Secondary | promoted to spine, but its three branches (sensing / data / falsification) do not cover the intervention table's six rows |
| 18 | Spec §3.3–§3.4 danger score, VOI | Secondary | promoted to spine; `ΔV_c/cost` being the framework's *only* priced intervention is presented as a feature and is now a defect (E-36) |
| 19 | Spec §7.3 asymmetric costs | Secondary | scoped by its first line to selecting among process *routes*; under v1.5 it must supply the objective for intervention selection. E-36 proposed this; the purpose extension makes it mandatory |
| 20 | Spec §9.3 baselines / "the honest case" | Secondary | the justification list is ordered with forward accuracy first; and this section already carries three measured defects (E-39, E-41, E-42) — the purpose extension adds a fourth pressure on the same text |
| 21 | Spec §9.4 falsification thresholds **[Pass D]** | Secondary | scoped to Core §6.1's six criteria; grows if §6.1 gains a decision criterion |
| 22 | Spec §12 architecture | Secondary | the component list is a prediction pipeline |
| 23 | Core §2.6 properties/performances | Wording | "regarded as equivalent for a given **purpose**" now collides with the framework's own declared purpose; Core §0.2 is the precedent for resolving exactly this kind of collision |
| 24 | Core Abstract ¶2–4 | Wording | "Version 1.3 makes the framework domain-neutral…", "Three new results carry the version" — version-scoped headlines, stale rather than false |
| 25 | Spec header, allocation rule | Wording | "Core holds everything falsifiable, Spec everything executable" survives, but the decision diagnostics are simultaneously a claim and a procedure; the partition needs re-checking rather than assuming |

**Seven primary, twelve secondary, three wording.** Two of the seven primary items
(Core §4's item count, Spec §9.1's level table) are already under independent
pressure from M11's findings, which is evidence the purpose extension is
surfacing a strain that was there rather than creating one.

**Pinned by.** Nothing yet — this ADR is a declaration, and the first thing that
pins it is Part 2's construction being designed against the extended purpose.

---

## ADR-049 — The declared-domain construction: one object for `ν` and for `c̄`, with a declared coupling direction and declared tracked dimensions

**Status.** Accepted — **design only. No implementation, no domain code.**
**Track.** v1.5 planning, Part 2. Consumed by Part 3 (composition) without
modification; a parallel mechanism for `c̄` would be an architectural error.
**Reads.** `docs/V1.4-EDITS.md` §2 in full, E-22 (both proposed wordings), E-25.
**Does not resolve.** Core §2.5. That remains an anti-goal (CLAUDE.md §9) and the
root of four ledger entries; resolving it is a research programme, not a
prerequisite for this construction.

### The problem, stated once for both consumers

E-22 found that Core §2.5's repair — `s : X_body → S`, "evolution acts pointwise or
with local coupling" — is correct for `m`, `z` and `Γ` and **wrong for `ν`**, because
Core §3.1 defines `ν` as the one slot that "pointwise evolution operators cannot
own." Three structurally unrelated domains exposed it independently, and the third
(crystallisation's well-mixed supersaturation) forced a revision of E-22's own first
proposal: "a field over the body" over-localises a quantity with **no local value at
all**, just as §2.5's formula over-localises one with a nonlocal one.

Part 3's composition decomposition `c(x) = c̄ + δc(x)` needs the identical object for
`c̄`: a mean over a **declared** domain, which may be the whole body, a declared
region, or a single global value. **These are one construction.** They are grouped in
ledger §2 for the same reason: both trace to Core §2.5, and both are asking the same
question — *over what does this quantity have a value, and how is it coupled to the
states that do have per-point values?*

### The construction: three declarations, attached to an existing interface item

**Design constraint honoured deliberately: this adds no interface item.** Core §4
item 1 already asks for "occupants of each slot, with resolution limits, and which
slots are empty." Resolution limits are the seed of this construction; the three
declarations below are a **refinement of item 1**, not an eighth item. Given the
arity pressure documented below, adding to it would have been the wrong move.

#### 1. `DeclaredDomain` — over what the quantity has a value

A **per-quantity** declaration, not a property of the framework. Three kinds,
covering exactly the cardinalities E-22's revised proposal requires:

| Kind | Meaning | E-22's worked case |
|---|---|---|
| `GLOBAL_POINT` | the trivial one-point domain; a single shared value, no local value exists even in principle | crystallisation's well-mixed supersaturation |
| `REGIONS` | a declared finite collection of named subdomains, each carrying one value | the intermediate case E-22 named as "not yet observed but not excluded" |
| `FIELD` | a value at every point of a declared dimension set | layer-wise additive's part-scale stress |

Formally, this is E-22's proposed wording (1 of 2) made declarable:
`s : X_body → (m, z, Γ)` — a genuine section, evolving pointwise or with local
coupling exactly as §2.5 says — **coupled to** `q : X_q → 𝒱_q` via a declared
coupling operator, with `X_q` declared independently and *not* fixed to either
`X_body` or a point.

#### 2. `CouplingDirection` — how it is coupled, which is independent of where

E-22's proposed wording (2 of 2), adopted as a taxonomy with **per-case obligations**,
because the entry's own argument is that a corrected spatial type with the wrong
coupling dynamics "is no better than the current under-declaration."

| Direction | What it means | What the declaration MUST supply | The check it makes possible |
|---|---|---|---|
| `DETERMINED_BY` | instantaneous function of the point states; eliminable in principle as a derived quantity | the **closure map** from point states (and controls) to the value | **closure residual**: the value at step `k` must be reproducible from the point states at `k` alone |
| `DEPLETED_BY` | conservation-coupled; carries its own dynamical state and memory; not eliminable | the **conserved quantity**, the **aggregation functional** over the population, its **own initial condition**, and any **replenishment flux** | **conservation residual** over a closed step |
| `INTERMEDIATE` | spatially extended, but primarily history-determined rather than conservation-depleted | the **history functional** it is determined by, **and** a statement of why neither pure case applies | closure residual against accumulated history rather than instantaneous state |
| `INVARIANT` | constant over the chain; indexes the operator family and is transported by nothing | the **domain over which constancy is claimed**, and whether that domain is closed | **constancy residual** along the chain |

**`INVARIANT` is a fourth case E-22 did not name, and it is added for a reason
rather than for symmetry.** Part 3's `c̄` is constant along the chain *by
definition*, and the brief states that "constancy is checkable and a violation means
the declaration is wrong." That is nearly right and the construction sharpens it: a
mean over a **closed** domain is constant by conservation, so a constancy violation
does not simply mean "the declaration is wrong" — it means **the domain is open and
the coupling should have been declared `DEPLETED_BY`**. Decarburisation is the worked
instance: mean carbon over a surface layer is not constant, because solute leaves
through a boundary. The constancy check therefore yields a *specific* corrective
diagnosis rather than a bare failure, which is the difference between a test and a
diagnostic.

**A consequence worth flagging rather than claiming.** `INVARIANT` coupling is,
structurally, E-29's missing **static-parameter** category — a quantity that
parameterises operators without being transported by them. If that identification
holds, this construction partially addresses a `[domain-assessment]` finding as a
side effect. It is **not** claimed closed here: E-29 is about the *schema* having no
slot, and Part 3's role declaration (parameter / control / state) is where the
identification either holds or does not. Recorded for Part 3 to settle, not resolved
in Part 2.

#### 3. `TrackedDimensions` — at what resolution, with a required justification

A declared subset of a closed dimension set — `THROUGH_THICKNESS`, `IN_PLANE`,
`FULL_3D`, `NONE` — with a **required, non-empty justification** string.

This is Spec §4.4's dimensional-reduction argument arriving on a different axis. For
planar product, through-thickness is where composition gradients live
(decarburisation, interdiffusion, mid-plane segregation) and in-plane is effectively
uniform, so a 1-D profile captures the real behaviour at a fraction of a 3-D field's
cost.

**The justification is required at every kind, including `GLOBAL_POINT`, and that is
where it matters most.** A `GLOBAL_POINT` declaration with `tracked = NONE` is an
assertion of spatial uniformity, and *that* is the assumption which became an
unexamined default in v1.3 — the point-valued state was never declared, so nobody had
to defend it. Per E-44, an undeclared modelling choice that no diff can see is
precisely the defect class this repository keeps finding. Requiring the justification
where the declaration is most degenerate is what stops the degenerate case being the
silent default again.

**Stated honestly: a free-text justification field checks nothing by itself**, and
E-17 and E-31 both warn about exactly this — a good-faith string that satisfies a
requirement without establishing the property. What the field buys is that the choice
becomes **visible to `interface.diff`**, so two implementations claiming operator
reuse can be compared on it. That is weaker than a check and stronger than silence,
and it is the honest description.

### Scope discipline

Declare the full construction; implement a strict subset.

| Case | v1.5 |
|---|---|
| `GLOBAL_POINT`, any coupling | **implement** |
| `REGIONS` with exactly one region | **implement** |
| `REGIONS` with more than one region | **refuse** — `NotSpecified` citing `C-2.5` |
| `FIELD`, any dimension set | **refuse** — `NotSpecified` citing `C-2.5` |
| `DEPLETED_BY` lifted over an ensemble | **refuse** — `NotSpecified` citing `C-3.3`; see E-25 below |

The refusals are CLAUDE.md §4's move 1, which is always legal, and they cite live
`docs/COVERAGE.md` row ids as `omi.gaps.NotSpecified` requires. **The formalism says
more than the code does**, which has been the pattern throughout and is why the
ledger has value.

### E-25 becomes detectable, and is not fixed

**This is the construction's strongest single payoff and it is worth more than the
`ν` fix.**

E-25 established that Core §3.3's lift is **linear in the measure** — pushforward of
a fixed map, and a Markov kernel `K_k(s,·)` with no `μ` argument — and that a
`depleted-by` quantity requires a mean-field (McKean–Vlasov) lift that Core neither
names nor provides. It also established that this repository's
`EvolutionOperator.lift` calls `step` once per particle with no reference to the
ensemble, and that the tension has been avoided "**by accident of how the two
mechanisms evolved, not by a stated policy**."

Declaring the coupling direction converts that accident into a **stated policy with a
detectable violation.** The unsound configuration is now expressible as a predicate:

> coupling is `DEPLETED_BY` **and** the quantity is shared across the particles of an
> ensemble being lifted.

That is exactly the configuration in which `.lift()` produces ensemble-mean physics —
which CLAUDE.md invariant 2 already forbids ("Type errors here silently produce
ensemble-mean physics, which is wrong for every Class B readout"). v1.5 therefore
**refuses** that configuration rather than computing it, citing `C-3.3`.

**v1.5 does not fix E-25.** No mean-field lift is supplied and none is designed here.
What changes is that the defect moves from *silently avoided* to *loudly refused*, and
per the brief a declaration that surfaces a known-unfixed defect is worth more than
one that hides it. The corollary E-25 left open — that Core §3.6's independence
assumption for sub-volumes is itself questionable when the same coupling is present —
becomes detectable by the same predicate and is likewise not fixed.

### The interface arity question: one decision, now under eight pressures

The brief names four. There are **eight**, and the count matters because it is the
argument against patching serially.

| # | Pressure | Source | What it wants |
|---|---|---|---|
| 1 | static parameter has no slot | E-29 `[domain-assessment]` | a parameter category — possibly met by `INVARIANT` coupling above |
| 2 | symmetry group undeclarable | E-30 `[domain-assessment]` | an item |
| 3 | characterisation suite undeclarable | E-31 `[domain-assessment]` | an item — **explicitly out of scope for v1.5** |
| 4 | constitutive form refused by name | E-32 `[domain-assessment]`, ADR-046 | ADR-046 already chose "a new interface item" |
| 5 | declarations cannot be refined | E-40 | a lineage field or item |
| 6 | scope features never declared | E-44 | a scope declaration |
| 7 | decision and intervention set undeclarable | ADR-048 | item(s) carrying targets with asymmetric costs |
| 8 | composition role, descriptor metric, composition-dependent validity | Part 3 | item(s) |

And the arity is **already** not clean before any of these: E-01 found Core §7.2's own
comparison table names **six** of the seven items, and ADR-034 superseded ADR-003's
pinning test over exactly that discrepancy.

**The decision this implies, stated and deliberately not taken:** Core §4's arity is
**one decision under eight pressures** and must be taken once, as a redesign of the
interface, rather than as eight appended items accumulated in the order the pressures
happened to arrive. Eight serial patches would produce a fifteen-item checklist whose
grouping reflects this repository's discovery order rather than the physics — which is
the failure mode the ledger's own root-cause grouping was created to avoid
(`docs/V1.4-EDITS.md` §0: "[N] entries in discovery order is a log; grouped by
cause, it is a diagnosis" — the count there is live and rises as entries are filed).

**Part 2 resolves none of them, and adds no ninth.** That is why this construction
attaches to item 1 rather than proposing an item of its own. The arity redesign is
recorded here as a standing open question and is v1.6 business at the earliest.

### Consequences

- Part 3 consumes `DeclaredDomain`, `CouplingDirection` and `TrackedDimensions`
  unchanged for `c̄`. If Part 3 finds it needs a variant, that is evidence this ADR
  got the construction wrong and it supersedes rather than extends.
- No interface item is added; item 1's "resolution limits" is refined.
- Three refusal paths exist and all cite live coverage rows.
- E-22's proposed wording (2 of 2) was rated **medium-high** confidence precisely
  because "Core's own text would need to commit to this specific taxonomy rather than
  some other framing." **v1.5 commits to it.** That converts a proposal into a
  decision, and the thing that could be wrong is the taxonomy's cut, not its
  necessity — recorded so a reviewer knows which part is load-bearing choice rather
  than derivation.

**Pinned by.** Nothing yet — design only. The first thing that would pin it is a
`GLOBAL_POINT` + `DEPLETED_BY` declaration refusing an ensemble lift, which is the
E-25 detection above and the natural first test when implementation begins.

### Amendment (at the Part 2 gate) — two questions settled before Part 3

#### A. The tracked-dimension justification is a known weakness, not a solved requirement

Restated so it cannot be read as discharged: **a free-text justification field is
satisfiable by an arbitrary string.** That is E-17's lesson exactly — a caller can
declare a form *named* Koistinen–Marburger with an arbitrary callable — and it
applies here one level down. The field is **visible to `interface.diff`** and
therefore comparable across implementations claiming operator reuse; it is **not**
inspectable by the type system and **nothing verifies it is true**. Weaker than a
check, stronger than silence, and recorded as an open weakness.

**A machine-checkable candidate, recorded as a candidate and explicitly not closing
the question.** Carry an **enumerated reason code** alongside the free text, naming
*why* a dimension is untracked. The value of the enumeration is not tidiness — it is
that **three of the four codes name machinery that already exists or is already
proposed**, so the code converts unfalsifiable prose into a claim that points at its
own check:

| Reason code | Meaning | What could check it |
|---|---|---|
| `NOT_LOAD_BEARING` | variation exists and is resolvable but moves no declared readout | **checkable today** — Spec §3.3's observability triage; an untracked direction with zero influence on the declared target set is exactly the `OBSERVED_BUT_IRRELEVANT`/marginalisable classification |
| `UNIFORM_BY_PROCESS` | the process makes the dimension uniform | checkable *if* the domain declares the symmetry that makes it so — which is **E-30**'s missing category |
| `BELOW_RESOLUTION` | variation exists but is finer than the instrument can see | checkable against the characterisation suite — which is **E-31**'s missing category, and out of scope for v1.5 |
| `OUT_OF_SCOPE` | deliberately excluded with the cost accepted | **not checkable, and that is honest** — this is the refusal case, and naming it as such is better than dressing it as one of the other three |

`NOT_LOAD_BEARING` is the interesting one: it is checkable with machinery this
repository already has, which means the enum is not a promissory note in at least
one case.

**Why this does not close the question.** The enum is itself satisfiable by choosing
the wrong code — a domain can declare `NOT_LOAD_BEARING` where the truth is
`BELOW_RESOLUTION`, and nothing catches it. That is E-17's good-faith residual
recurring, and recording it is the honest stopping point. Deciding the enumeration
is an implementation-time choice needing its own ADR; it is **not** taken here.

#### B. Part 3 fits the current seven items. No reorder, and no ninth pressure

Tested per addition rather than asserted.

| Part 3 addition | Home | New item? |
|---|---|---|
| **Role: control** | **item 2** — control space and `𝒰_adm`, already declares exactly this | no |
| **Role: state** | **item 1** — which slot `δc` occupies | no |
| **Role: parameter** | **ADR-049's `INVARIANT` coupling**, attached to item 1 | no — see the charter caveat below |
| **Descriptor metric** | a **field on ADR-049's coupled-quantity declaration**, beside domain and tracked dimensions | no |
| **Composition-dependent validity** | a **refinement of the item ADR-046 already decided to add** (pressure 4) | no — extends an existing pressure, does not create one |

Three of these deserve their reasoning shown.

**The parameter role, and why it addresses E-29 rather than adding a pressure.**
E-29's complaint is verbatim: Core §6.2 "asks how much of an operator is
'composition-*parameterised*', so the framework has the word and no place to declare
a parameter." ADR-049's `INVARIANT` coupling **is** that place — a quantity with its
own declared domain, constant along the chain, transported by no operator, indexing
the operator family. E-29's part 2 (a readout depending only on parameters cannot be
flagged) also becomes detectable: a readout whose arguments are all
`INVARIANT`-coupled is mechanically identifiable. So the parameter role consumes an
existing pressure instead of creating a new one.

**The descriptor metric belongs beside domain and tracked dimensions because it is
the same kind of declaration.** Domain answers *over what* the quantity has a value;
tracked dimensions answer *at what resolution*; the descriptor basis answers *in what
coordinates*. All three are representation declarations on one quantity, so the
descriptor basis is a third field on one object rather than a new interface item.

**The charter caveat, stated so it can be overruled.** ADR-049 widened item 1 from
"state schema" to "state schema **plus the quantities coupled to it**" in order to
host `ν`'s domain and coupling — legitimate, since `ν` is a slot occupant. Part 3
leans on that widening to host a quantity that is **not** state at all. That is a
further stretch of item 1's charter, and whether item 1 should be *renamed* is
arity-redesign business, not Part 3's.

**The condition under which this verdict flips:** if item 1's charter is judged unable
to cover a non-state quantity, the parameter role becomes a **ninth** pressure and the
arity redesign must move ahead of Part 3. Recorded explicitly so that judgement is
available to a reviewer rather than buried in a design that assumed the generous
reading.

> **The flip condition was exercised at the Part 3 gate, and the strict reading was
> taken. Filed as `docs/V1.4-EDITS.md` E-46.**
>
> The reviewer's judgement: **item 1's charter does not cover a non-state quantity.**
> ADR-049's widening is legitimate for `ν` — which evolves, is assimilated, and carries
> a per-particle value in the ensemble — and illegitimate for `c̄`, which does none of
> those and is a fixed index on the operator family. Hosting both under item 1 means a
> reader encounters *what the material is* and *what the operator is parameterised by*
> with nothing in the declaration distinguishing them.
>
> **No reorder.** Part 3's ADRs (050–054) are written so the parameter role
> **relocates rather than rewrites**: the declaration's content — declared domain,
> coupling direction, tracked dimensions, descriptor basis — is unchanged by where it
> is hosted, and only the item number moves. E-46 is therefore evidence carried into
> the arity redesign, not a trigger to redo Part 3.
>
> **The pressure count is now recorded both ways rather than settled**, because the
> difference between them *is* the question the redesign must answer:
>
> - **Generous reading** (item 1 stretches): eight pressures, the parameter role
>   absorbs E-29, **seven** remain.
> - **Strict reading** (the reviewer's, and the one taken): `INVARIANT` coupling gives
>   the parameter a *representation* but not a *home*, so **E-29 is unresolved**, and
>   the charter question is an **additional** pressure. **Nine.**
>
> Picking one here would smuggle the redesign's central settlement into a Part 3
> caveat. What is not in doubt on either reading: **the redesign cannot be done by
> appending**, because the count itself moves on a judgement that appending would never
> surface. E-46's proposed wording splits item 1 into `1` (state schema) and `1b`
> (operator parameterisation) rather than widening it, with the deliberate provision
> that one physical quantity may appear on both sides when the regions are named —
> carbon is a parameter in the bulk and a depleted state variable in a decarburising
> layer simultaneously (ADR-051).

---

## ADR-050 — The composition decomposition `c = c̄ + δc`: what is constant, what evolves, and what makes the split checkable

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 3.1. Consumes ADR-049 unchanged.
**Scope.** Implement `c̄` plus sub-resolution `δc` in `z`. Resolved bands stay
declarable and unimplemented.

### The decomposition

$$c(x) = \bar{c} + \delta c(x)$$

**`c̄` — the mean over a declared domain.** It is an ADR-049
coupled-quantity declaration with `coupling = INVARIANT`, and that is the whole
content of "constant along the chain by definition." It indexes the operator family;
no operator transports it.

**`δc(x)` — the fluctuation field.** Ordinary state, evolving under ordinary
operators, living in whichever slot its length scale puts it in: sub-resolution
clustering in `z`, resolved segregation bands in `m`, boundary segregation in `Γ`.
Nothing new is required for `δc` — it is item 1's existing business.

### The constancy check, and what a violation actually means

ADR-049's `INVARIANT` case supplies a **constancy residual** along the chain. The
brief's reading — "a violation means the declaration is wrong" — is nearly right, and
the construction sharpens it into a *specific* diagnosis rather than a bare failure:

> A mean over a **closed** domain is constant by conservation. So a constancy
> violation does not mean the declaration is arbitrary nonsense; it means **the
> declared domain is open**, and the coupling should have been `DEPLETED_BY` with a
> declared boundary flux.

**Decarburisation is the worked instance**: mean carbon over a surface layer is not
constant, because carbon leaves through a free surface. Interdiffusion across a
coating interface is the second. In both cases the correct repair is not "fix `c̄`" but
"re-declare the domain as open and name the flux" — which the coupling taxonomy can
express and the v1.3 schema cannot.

### The projection scale is the load-bearing declaration, and nothing currently detects a mismatch

The split between `c̄` and `δc` is set by a **declared projection scale**, which is
itself a function of the characterisation suite (`docs/PHYSICS-ADEQUACY.md` §3.3):
what counts as "mean" versus "fluctuation" depends on what the instrument resolves.

**Operator reuse between two implementations is valid only if their splits match, and
no mechanism detects a mismatch.** Two chains can declare the same `c̄` descriptor
values, the same operators, and the same readouts, while having drawn the `c̄`/`δc`
line at different length scales — in which case the operators are not the same
operator and reuse is unsound. This is the same shape as E-33's unit-dependence
finding: a quantity compared across implementations without its basis travelling with
it.

The projection scale is therefore declared as part of `c̄`'s ADR-049 tracked-dimension
declaration, and **`interface.diff` must surface it**. That makes a mismatch visible
without making it checkable — the honest position, and the same one ADR-049 took for
the justification field.

**Filed as a framework finding.** The projection scale is a declarable modelling
choice that determines whether operator reuse is sound, and Core §4 has no item for
it — the characterisation suite that fixes it is **E-31**, already out of scope for
v1.5. This decomposition makes the dependency explicit rather than resolving it, and
the new finding (that operator *reuse* silently depends on it) is filed as **E-45**.

### Consequences

- `c̄` requires no new machinery beyond ADR-049.
- `δc` in `z` is implementable now; resolved bands in `m` require `FIELD` domains,
  which ADR-049 refuses citing `C-2.5`.
- The constancy residual is the first concrete check ADR-049's `INVARIANT` case
  yields, and it is the natural first test when implementation begins.

---

## ADR-051 — Chemistry's role is declared per species per region, and the same quantity takes different roles in different chains

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 3.2.

### The decision

A composition species' **role** is a per-species, per-region declaration, not a
property of the framework or of the species:

| Role | Meaning | Interface home |
|---|---|---|
| **Parameter** | fixed for the chain; indexes the operator family | ADR-049's `INVARIANT` coupling (item 1's refinement) |
| **Control** | set by the experimenter; lives in `𝒰_adm` | **item 2**, unchanged |
| **State** | evolves under some operator | **item 1**, which slot |

**The same quantity takes different roles in different chains, and the interface must
express both without either being the default.** Bulk carbon is a *parameter* in a
hot-stamping chain — fixed by the incoming coil, indexing every transformation
operator — and a *control* in a discovery campaign, where the experimenter sets it per
sample. Neither reading is more correct; what is wrong is a framework that hard-codes
one.

**Per-region, not only per-species.** The same species can hold different roles in
different declared regions of one chain: carbon is a parameter in the bulk and a
`DEPLETED_BY` state variable in a decarburising surface layer, simultaneously. This is
why the role attaches to the (species, region) pair and why ADR-049's `REGIONS` domain
kind is what makes the declaration expressible at all.

### What this closes

**E-29's part 1, the missing parameter category.** E-29's own words: Core §6.2 "asks
how much of an operator is 'composition-*parameterised*', so the framework has the
word and no place to declare a parameter." The Parameter role, realised as `INVARIANT`
coupling, is that place.

**E-29's part 2 becomes detectable.** E-29 also found that "a readout depending only
on parameters cannot be flagged." With roles declared, a readout whose arguments are
all Parameter-role quantities is **mechanically identifiable** — it is a readout of the
grade, not of the process, and Core §2.6's property/performance distinction says that
is a legitimate case that must not be confused with a defect. The declaration
separates them.

**Not claimed: transfer.** Whether an operator fitted at one parameter value predicts
another is composition-family transfer, explicitly **out of scope for v1.5** and the
v1.6 question. The Parameter role is its *precondition*, not its answer, and coupling
the two would make both unreviewable.

---

## ADR-052 — `c̄` is declared over physics descriptors, with raw fractions as the underlying space

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 3.3.

### The decision

`c̄`'s value is declared in a **descriptor basis** — carbon equivalent, `Ms`,
hardenability index, stacking-fault energy, valence electron count — with **raw mass
or atomic fractions declared as the underlying space**. Both are carried; the
descriptors are the metric, the fractions are the ground truth.

This is a third field on ADR-049's coupled-quantity declaration, beside domain and
tracked dimensions, because it is the same kind of declaration: domain answers *over
what*, tracked dimensions *at what resolution*, descriptor basis *in what
coordinates*.

### The reason is checkability, not convenience

> *"This operator depends on chemistry only through carbon equivalent"* is a
> **falsifiable claim**.

It is testable by holding out a composition that varies other elements **at fixed
CE**. That is the whole argument, and it is why the descriptor basis is not a
presentational choice:

- **Raw fractions give a meaningless metric.** A one-sigma change in carbon and a
  one-sigma change in nickel are not comparable quantities, so any distance in
  fraction space is arbitrary — which CLAUDE.md invariant 1 already forbids for
  Lipschitz constants and trust radii, and which applies identically here.
- **A learned embedding gives no transfer guarantee and fails silently across a phase
  boundary.** It will interpolate smoothly through a region where the physics does
  not, and nothing in the embedding announces it.
- **A declared descriptor basis states which functionals the operator claims to depend
  on**, which is a claim about argument structure and therefore refutable.

**Structurally this is Axiom S on a second axis.** Axiom S says evolution depends on
history only through the current state; the descriptor claim says evolution depends on
composition only through the declared descriptors. Both are sufficiency claims about a
projection, and both are falsified the same way — by finding two inputs that agree on
the projection and disagree on the response.

### Two obligations that follow

**The hold-out must pass E-41's vacuity gate first.** A composition hold-out varying
other elements at fixed CE is exactly the kind of axis that can be *inert*: if the
withheld variation moves no declared readout, the test satisfies Spec §9.3 in full and
measures nothing. `omi.proposed.holdout.check_hold_out_discriminates` is the
precondition, and applying it here is not optional — M11.4 is what happens otherwise.

**The simplex constraint is architecture, never a penalty.** Components sum to one,
which is precisely the treatment phase fractions already receive
(`omi.constraints.simplex`, CLAUDE.md invariant 5). A composition *inverse* is an
optimiser searching composition space, and CLAUDE.md invariant 5's reasoning applies
verbatim: "an optimiser searching for an optimal route finds precisely where
enforcement is weak." Off-manifold constraint tests are required, not optional.

---

## ADR-053 — The composition inverse: a third inverse problem that falls out of the formalism

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 3.4a.

### The decision

Core §5 declares two inverse problems — the **control inverse** (target response →
driving programme, with process and usage instances) and the **structure inverse**
(target response → state). The composition decomposition yields a **third**:

> **Composition inverse** — target response → chemistry. Its output is a declared
> `c̄` in the descriptor basis, which must then be checked for realisability
> (does an alloy with these descriptors exist and can it be made?) exactly as the
> structure inverse's output must be fed to a control inverse and may be certified
> unreachable there.

**This is materials discovery, and it now falls out of the formalism rather than being
bolted on.** That is the claim worth making carefully: the composition inverse is not
a new mechanism but the same constrained-optimal-control problem of Core §5 with the
Parameter-role quantities moved from the fixed index into the decision variables.

### Why it is genuinely third rather than a relabelled structure inverse

The two are distinguishable by what certifies infeasibility, which is the criterion
Core §5 itself uses to separate its existing pair:

| Inverse | Decision variable | Infeasibility certificate |
|---|---|---|
| control | `u ∈ 𝒰_adm` | apparatus constraint manifold |
| structure | `s ∈ 𝒮` | `s ∉ 𝓜_reach` plus nearest reachable state |
| **composition** | `c̄` in the descriptor basis | **the descriptors are not jointly attainable by any real alloy**, or the resulting chemistry leaves the declared mechanism set's validity region (ADR-054) |

The third certificate has no analogue in the existing pair, which is the evidence that
it is a distinct problem rather than a renaming. **Conflating them produces
unrealisable answers** in exactly the way Core §5 warns about for its own two: a
composition inverse that ignores descriptor attainability returns beautiful,
unmeltable alloys.

### Consequences

- The Part 5 SDL domain is the natural vehicle: a discovery campaign is a composition
  inverse run repeatedly under a decision.
- Core §5's taxonomy becomes incomplete as written — recorded as item 12 of ADR-048's
  inaccuracy table, now with a specific replacement rather than a note.
- The descriptor-attainability certificate is **not designed here**. It needs a
  declared attainable region in descriptor space, which no domain currently supplies,
  and inventing one would be the improvisation CLAUDE.md §4 forbids.

---

## ADR-054 — Validity ranges become functions over composition space, and the regime-boundary check that follows

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 3.4b. **Extends** ADR-043's validity mechanism; this is
a genuine extension, not a reuse.

### The decision

A declared constitutive form's validity interval is **a function over composition
space**, not a pair of numbers.

`Ms` is not universal. Koistinen–Marburger's `α` is not universal. Both depend on
chemistry, so ADR-043's `ValidityBound(low, high)` — two floats — is structurally
unable to express a bound that moves as `c̄` moves. The extension:

> `ValidityBound`'s edges become **callables over the declared descriptor basis**,
> evaluated at the declaring domain's `c̄`, with the same `EdgeKind`
> (`SHARP` / `APPROXIMATE`) and the same one-sided/two-sided rules ADR-043 established.

**Why this is an extension rather than a reuse, stated plainly because ADR-043's
machinery superficially looks sufficient.** ADR-043's `extrapolation_factor` divides a
distance by a *fixed* half-width or a *declared* `fitted_scale`. If the window itself
moves with composition, then the factor is a ratio of two composition-dependent
quantities, and the question "am I outside the window" has a different answer at every
`c̄`. E-40's finding bites here too: a form whose window is a function cannot be
refined into one whose window is a pair of numbers, or vice versa, without breaking
every caller.

### The regime-boundary check

The extension yields a new diagnostic, and it is the one that matters for the v1.5
purpose:

> **Does the proposed chemistry still support my declared mechanism set?**

A composition inverse (ADR-053) proposes a `c̄`. Crossing a phase boundary can
**invalidate a declared mechanism** — the form was fitted where that mechanism
operated, and at the proposed chemistry a different one does. The check evaluates every
declared form's composition-dependent validity at the proposed `c̄` and reports which
forms, if any, no longer apply.

**This is M11's finding arriving on the composition axis, and the connection is
load-bearing rather than decorative.** M11.5 measured that a declared form with an
**incomplete mechanism set** is far worse than no declared form at all — 69.55 against
a free-form operator's 5.06, a gap of +61.98 between the two misspecification arms
against a declared minimum effect of 0.63. The regime-boundary check is the mechanism
by which *composition change* causes exactly that incompleteness: the mechanism set was
complete for the fitted chemistry and is incomplete for the proposed one.

**So the check is a refusal, not a warning.** Per ADR-048, the refusal criterion is
spine rather than credibility argument, and M11.5's magnitude is the argument for
treating a regime-boundary crossing as grounds to refuse a composition-inverse
proposal rather than to annotate it.

### What this does not do

- It does not decide **where** the phase boundaries are. That is domain physics, and a
  domain must declare it.
- It does not address whether an operator **transfers** across the boundary — out of
  scope, v1.6.
- It inherits ADR-049's `INVARIANT` constancy check: if `c̄` is not constant along the
  chain, the validity functions are being evaluated at a moving argument, and the
  regime-boundary check's result is not well-defined. **The constancy residual is a
  precondition for this check**, which is a dependency between two Part 3 ADRs worth
  naming rather than discovering later.

---

## ADR-055 — Parameter equifinality: extending the observability triage from state directions to declared-form parameters

**Status.** Accepted — **design only.**
**Track.** v1.5 planning, Part 4.
**Distinct from M11's finding**, and the distinction is the reason this exists.

### The failure this addresses, and why it is not M11's

M11.5 measured what happens when a declared form's **mechanism set is incomplete**:
69.55 against a free-form operator's 5.06. This is a different failure with the same
symptom:

> **The form is complete. The parameters are unidentifiable along the axis being
> extrapolated.**

Fit Kocks–Mecking's `k₁` and `k₂` in-envelope and **many pairs fit equally well** —
because in-envelope the response is dominated by the storage term and the recovery
term is barely exercised. Those pairs imply **different saturation levels**
`(k₁/k₂)²`, and saturation is precisely what extrapolation along accumulated strain
approaches. So the fit is excellent, the form is right, the query is inside every
declared window, and the extrapolated prediction is arbitrary within a range nothing
reports.

**Nothing in the current framework would flag it.** Filed as `docs/V1.4-EDITS.md`
**E-47**.

**The two failures land on different rows of the intervention table** (ADR-048's
spine), which is the cleanest demonstration that they are distinct rather than two
readings of one thing:

| Failure | Diagnosis | Intervention |
|---|---|---|
| M11's — mechanism missing | the declared physics is incomplete for the regime | **buy physics** |
| this one — parameters unidentifiable | the declared physics is right and under-determined | **buy sensing / run experiments** — and it names *which* measurement |

### The construction

Same Fisher-information construction, same danger score, **different object**.

| | Spec §3.3's existing triage | this extension |
|---|---|---|
| object | state directions (eigenvectors of `P_k`) | **declared-form parameter directions** (eigenvectors of the parameter posterior) |
| information | observability Gramian `𝐆` over state | **parameter Fisher matrix** `Σ_j (∂y_j/∂θ)ᵀ R_j⁻¹ (∂y_j/∂θ)` from in-envelope residuals |
| influence | `v* S* W S v` — target-variance contribution | target-readout sensitivity to `θ`, **evaluated at the extrapolation query** |
| uncertainty | `v* P_k v` | the parameter posterior's own eigenvalue |
| danger score | influence × uncertainty | **unchanged** |
| labels | `Triage`'s four-way split | **unchanged** |

### Reuse verdict, stated plainly as the gate requires

**It reuses the decision layer and needs a new information layer.** Neither "pure
reuse" nor "fully parallel" is accurate, and claiming either would be wrong.

**Reuses, essentially unchanged:** eigendecomposition of the posterior;
`influence × uncertainty`; `Triage`'s four-way labelling and the median-threshold
convention (ADR-020); `TriageResult.dangerous_set()`'s ranked output;
`value_of_information` and `best_placement` — "which measurement would disambiguate
the parameters" *is* VOI computed against the parameter Gramian, with no new
mathematics.

**Requires a genuinely new construction, for three reasons that are not cosmetic:**

1. **The derivative is with respect to a different object.** `propagate_jvp(chain,
   nominal, k, j, v)` perturbs the *state at index k* and reads at `j`. A parameter
   perturbation **has no `k`**: `θ` enters every operator that declares that form, at
   every index it appears, simultaneously. The sensitivity is a sum over all such
   indices, not a propagation from one. The existing signature cannot express it.
2. **The evaluation point is outside the envelope, and that is the entire point.**
   State triage asks "is this direction identifiable *here*." Parameter triage asks
   "is this parameter identifiable **along the axis I am extrapolating**." So
   information must be gathered **in-envelope** (where the data is) while influence is
   evaluated **out-of-envelope** (where the decision is). The existing machinery has
   one `nominal_trajectory` and no such pairing.
3. **The dangerous quantity is a divergence, not a magnitude at a point.** The
   equifinality signature is a parameter direction along which in-envelope fit is flat
   and extrapolated prediction is not — a ratio of two sensitivities at two different
   evaluation points.

**Point 3 is E-41 recurring, and the design should borrow rather than reinvent.**
E-41 established, by measurement, that the discriminating quantity for a hold-out is
**divergence along the axis** and not disagreement at a point — the vacuous and usable
axes showed the same absolute disagreement and differed by 14× in growth. Parameter
equifinality has the identical shape: parameters that **agree in-envelope and
disagree out-of-envelope**. So the two-point near/far probe structure of
`omi.proposed.holdout` is the right skeleton, and the parameter danger score should be
read as a divergence between the two probes rather than as a score at one.

### For a self-driving lab this is an experiment-selection signal, not a warning

The near-null direction of the parameter Fisher matrix is a *vector in parameter
space*, and VOI against that matrix ranks candidate measurements by how much they
would shrink it. So the output is **"measure this"** rather than "beware":

> `k₂` is unidentifiable from the in-envelope campaign; a single measurement at high
> accumulated strain would resolve it, and here is its value per unit cost.

That is the same `ΔV_c/cost` denominator Spec §3.4 already supplies — the framework's
**only** priced intervention (E-36) — now pointed at parameters. It is the most direct
connection between Part 4 and Part 6's campaign statistic, and Part 6's candidate
"parameter danger scores rising along the proposed direction" is exactly this quantity.

### Scope and what is not decided

- **Design only.** No implementation.
- **Thresholds are not chosen here.** ADR-041's `decision_sensitive_threshold` is the
  procedure and it needs a declared minimum effect and cost ratio, which belong to
  whichever experiment consumes this — not to the construction.
- **Free-form parameters are out of scope, and the reason is worth stating.** A
  free-form operator's coefficients are also unidentifiable, often more so. But they
  carry no physical meaning, so the actionable output ("measure the thing that pins
  `k₂`") has no analogue — the answer would be "measure everything." The diagnostic is
  useful *because* the parameters are declared and named, which is an argument for the
  declared-form category that M11.5's negative result did not supply.
- **It does not repair the identifiability.** It measures and names it. Per ADR-048,
  a diagnostic that says which purchase to make is the product.

## ADR-056 — The contrast decision loop: an *ordered* rule over four diagnostics, with the ablation that decides whether it is driven or decorated

**Status.** Accepted — **design only.** No loop implementation.
**Track.** v1.5 planning, Part 5(1), §5.1.
**Pins.** Nothing yet — deliberately. The measured diagnostic traces this ADR is
designed against were produced by the Part 5(1) dry-run harness
(`tests/oracles/contrast_insufficiency.py`), and they already decide three of the
four diagnostics' fates before a line of loop code exists.

### Why contrast, and what "driving" has to mean

Contrast is sequential by construction (`CyclingStep` over intervals), declares an
**empty erasure inventory** so state accumulates irreversibly, has the poorest
observation suite in the repository (one evaluable modality of three declared), and
already declares `dendrite_risk` as Type-0/Class-B, which supplies the asymmetric-cost
structure Spec §7.3 and ADR-041 need. Every ingredient the loop consumes is declared
by the domain rather than invented for the demonstration, which is the only reason the
demonstration means anything.

The requirement that shapes the whole design: **the loop must be driven by the
diagnostics, not annotated with them.** A loop whose action sequence is unchanged when
the diagnostics are replaced by constants has demonstrated nothing about the framework
— it has demonstrated that a state-dependent policy can be written on top of a chain,
which was never in doubt. So the ablation is part of the design, not a test written
afterwards, and §"The vacuity ablation" below fixes it.

### The action set, and the item that hosts none of it

The brief's framing is that the actions come from contrast's declared items 2 and 5.
Three of the four do. **The fourth does not, and that is a finding rather than a
detail.**

| Action | Declared home | Status |
|---|---|---|
| **set control** — choose next interval's current within `𝒰_adm` | item 2 (control space): "bounded by manufacturer charge/discharge limits" | declared |
| **derate** — narrow the admissible current band for the remainder | item 2, as a restriction of `𝒰_adm` | declared |
| **commission a measurement** — instrument the next interval with a declared modality | item 5 (observation suite): terminal current, voltage, surface temperature | declared, with one caveat below |
| **retire** — end the campaign; the chain is no longer in scope at the required precision | **no item** | **undeclarable** |

Retirement is Core §3.9's "declare out of scope" reached *during* operation rather
than at design time. Core §4's seven items declare what a domain *is* and what can be
*done to it*; none of them declares the criterion under which the instantiation stops
being the right description. The loop must nonetheless take the action, so this design
declares the retirement criterion in the **analysis**, alongside the target set
(CLAUDE.md invariant 10), and records the absence rather than quietly siting it under
item 6's invariants — an invariant is a conservation statement the chain must satisfy,
not a decision rule about when to stop trusting it. Filed as a framework finding.

**The caveat on item 5.** Contrast declares three observation modalities and the state
schema supports two: there is no state component standing in for *surface
temperature*, so a "commission the temperature sensor" action is declarable and not
evaluable. The loop's candidate-measurement pool is therefore smaller than the
declared suite, and the loop must say so rather than silently enumerating two of
three. This is the same shape as E-44 (a scope feature declared with no item behind
it) one level down: a modality declared with no state component behind it.

### The rule: ordered, not scored

At interval `k`, with the target set declared in advance (`dendrite_risk` as the
Class-B target, `terminal_voltage` as the Class-A target), the loop evaluates the four
diagnostics and takes the **first** action whose precondition holds:

1. **Retire** — the declared target leaves its declared specification band with
   probability above the declared tolerance (`omi.inverse.probability_of_conformance`
   over the Class-B predictive distribution, per CLAUDE.md invariant 4).
2. **Commission a measurement** — the blocking-term trichotomy
   (`omi.sufficiency.diagnose_blocking_term`, Spec §1.7) returns `VARIANCE`, **and**
   the best candidate placement's `ΔV_c/cost` (`omi.observability.value_of_information`,
   `best_placement`, Spec §3.4) exceeds the declared cost floor.
3. **Derate** — the asymmetric-cost threshold (ADR-041's
   `decision_sensitive_threshold(σ, δ, c_FA, c_miss)`) is crossed by the hazard's
   current posterior mean, with `c_miss ≫ c_FA` because a dendrite event is not
   symmetric with a lost cycle.
4. **Set control at nominal** — nothing above fired.

**Why ordered rather than a scored objective.** Spec §7.3 requires an infeasibility
report to say which of trust region, admissible control, or aleatoric spread binds,
*in order*; E-06's finding is that an unordered report cannot say which of three terms
is responsible when the three have a real dependency order, and §11 of the ledger
names that ordered diagnosis as "the closest thing the framework has to a general
intervention-selection mechanism." This loop is that mechanism applied to operations
instead of to inverse design, so it inherits the ordering rather than inventing a
weighted score whose weights no document supplies. A scored rule would also destroy
the ablation: with four terms in one sum, freezing one changes the sum a little and the
argmax rarely, so "did this diagnostic drive anything" becomes unanswerable.

**The drift monitor is a gate on the other three, not a fifth action.** If the
innovation monitor says the model is inconsistent with the data, then the posterior the
other three diagnostics are computed from is not trustworthy, so acting on it is worse
than not acting. When the monitor trips **upward** (innovations larger than the model
predicts — the model is wrong), the loop may only commission or retire; it may not
derate, because derating on a model known to be misspecified is acting confidently on
a quantity just declared unreliable. When it trips **downward** (innovations smaller
than predicted — the forecast covariance is overstated) the model is not wrong, it is
over-hedged, and the correct response is the opposite: the loop may proceed, and the
*commission* branch should be suppressed, because buying information to reduce an
uncertainty that is already overstated buys nothing.

`omi.assimilate.DriftReport` does not currently distinguish the two tails:
`drift_detected` is a boolean array and `any_drift` a boolean, so a lower-tail trip and
an upper-tail trip are indistinguishable to a caller. Since the two require **opposite**
responses, this design cannot be implemented against the current API without reading
`windowed_mean` against `lower_limit`/`upper_limit` by hand. Recorded here, filed as a
framework finding, and **not fixed** — Part 5(1) is design-only for the loop.

### What the measured traces already decide

Contrast's diagnostics were traced over a 24-interval campaign with per-interval
voltage telemetry (the numbers are in the Part 5(1) report and
`build/observations.json`). Three of four are decided before the loop exists:

| Diagnostic | Measured behaviour over the campaign | Can it drive a decision? |
|---|---|---|
| **Danger score / triage** | `influence_median` is **exactly 0.0** at every interval; the dangerous set holds three directions at every interval; total danger varies by 6×10⁻⁵ of its own mean across the campaign's interior; the label set changes at two of thirteen sampled intervals and **both changes are decided at machine precision** | **No — worse than no: it fires arbitrarily** |
| **Validity report** | contrast declares **no** constitutive form and **no** validity range; only `flagship_constitutive` implements `extrapolation_report` | **No** — structurally unavailable on this domain |
| **Innovation sequence** | per-window false-alarm rate on the null arm is at nominal (mean NIS 1.007), but `any_drift` fires on **38.5%** of null campaigns | **Yes, as a gate** — but not via `any_drift` |
| **Blocking trichotomy** | needs matched-pair campaign data, which contrast can supply | **Yes** — and it is the only one of the four that ranks a *purchase* |

**The triage failure is a threshold degeneracy, not a domain weakness, and it is
worth stating precisely.** ADR-020 classifies a direction as influential when
`influence ≥ influence_median`. Influence is a quadratic form `vᵀSᵀWSv`, hence
non-negative. On contrast more than half the directions have influence exactly zero —
`dendrite_risk` depends on two of seven components — so the median *is* zero and
`influence ≥ 0` is a tautology. Every direction is "influential", `MARGINALISABLE` and
`OBSERVED_BUT_IRRELEVANT` become unreachable, and the four-way triage collapses to the
two-way identifiability split. The pre-existing `test_domain_triage.py` already records
`contrast_influence_median == 0.0` and asserts it; what is new here is the
*consequence* — that a decision loop keyed on the triage's labels cannot fire on this
domain, and would not fire on any domain whose target set touches fewer than half the
state components, which is most domains.

**And there is a second, sharper degeneracy that the trace found and this design did not
anticipate.** The categorical output is not constant: the label set gains an `observed`
entry at two of thirteen sampled intervals. But it does not change because the
information changed. ADR-020 operationalises Spec §3.3's "one near-diagonal Gramian term
dominates" as a strict `share > 0.5` **with no margin**, and on contrast the share passes
smoothly through 0.5. At the interval where it does, two eigendirections with shares of
`0.5000000000596` and `0.4999999999856` — agreeing to eleven decimal places — receive
**different labels**, one `observed` and one `inferred`. That is the distinction Core
§3.8 describes as whether "the chain model, not any instrument, is doing the work", and
here it is decided by the sign of a rounding error. The smallest margin to the threshold
anywhere in the campaign is `1.4×10⁻¹¹`.

So the honest statement is not that the triage's categorical output cannot fire. It is
that **it fires arbitrarily**, which is a worse failure than silence: a loop keyed on the
labels would derate or commission at two intervals distinguished by nothing physical.
Both degeneracies push the same way and this design takes the same decision, but the
second is the stronger reason for it.

The total danger score's own jump at the **terminal** interval is separate and is
excluded from the flatness claim rather than folded into it: at the last index there is
no downstream observation left to propagate information from, so the posterior collapses
to the prior. A campaign that has ended is not a campaign a decision changes.

**Design consequence, taken rather than worked around.** The loop's step 2 is keyed on
the **blocking trichotomy and `ΔV_c/cost`**, both continuous, and *not* on the triage's
labels. The triage still supplies `variance_term` as the trichotomy's variance input,
so it is not removed from the loop — but it enters as a number, not as a category, and
the categorical output is reported as **never firing in the campaign's interior** rather
than quietly dropped.

### The vacuity ablation

The loop is run four times over the same seeded campaign:

- **full** — all diagnostics live;
- **frozen-`k`** — one diagnostic replaced by its own campaign median, holding the
  rest live, once per diagnostic;
- **all-frozen** — every diagnostic replaced by its campaign median.

The reported quantity is the **action-sequence edit distance** from *full*, per
ablation. A diagnostic whose frozen run reproduces *full* exactly drove no decision,
and is reported as such by name. If *all-frozen* reproduces *full*, the demonstration
is vacuous and that is the result — not a bug to be tuned away.

**Freezing at the median rather than at zero** is deliberate: zeroing a diagnostic
changes the *scale* of every threshold comparison and would guarantee a different
action sequence for a reason that has nothing to do with information content. The
median preserves the magnitude and removes only the time variation, which is the
property under test.

### Alternatives rejected

*A scored objective over the four diagnostics.* Rejected: no document supplies the
weights, and it makes the ablation uninterpretable (above).

*Adding a declared constitutive form to contrast so the validity report can fire.*
Rejected for Part 5(1): it is domain code, the brief forbids it here, and the absence
is more informative than the patch — a domain can be fully OMI-0 conformant and still
have no validity signal available to an operational loop.

*Siting the retirement criterion under item 6 (invariants).* Rejected: an invariant is
a conservation law the chain satisfies; a retirement rule is a decision about when to
stop believing the chain. Conflating them would let a domain claim it had declared an
end-of-life criterion by listing a conservation law, which is exactly the
satisfiable-without-the-property shape §4 of the ledger documents nine times.

*Keying step 2 on `dangerous_set()`.* Rejected on the measurement: the set is
non-empty and constant at every interval, so it carries no decision information on
this domain.

### What would change this decision

A revision of ADR-020's median split that is well-defined when the influence
distribution is more than half zero — a positive-influence-conditional median, or an
absolute floor in declared target-variance units — would restore the categorical
triage as a driver and change step 2. So would a `DriftReport` that reports which
control limit was crossed, which would let the drift gate be implemented against the
API rather than around it.

---

## ADR-057 — The statistic dry-run: two arms, a null-sigma separation, and why E-41's check cannot be called on a diagnostic

**Status.** Accepted — **design, and executed.**
**Track.** v1.5 planning, Part 5(1), §5.2.
**Pins.** `tests/oracles/contrast_insufficiency.py`,
`tests/oracles/test_statistic_dry_run.py`.
**Fixes no thresholds.** Part 6's pre-registration happens in Part 6, in its own
earlier commit. This ADR selects a candidate and establishes that it is not inert.

### What the statistic has to do

Part 6's claim needs a statistic that separates **model insufficiency** from
**exploration noise**: an acquisition loop that keeps proposing and keeps failing must
be distinguishable from one that is merely sampling a noisy surface. Both look like
"the model is not improving". Only the first is a finding.

So the dry-run runs **two arms** over the same seeded contrast campaign:

| Arm | Construction | What a good statistic reads |
|---|---|---|
| **N** (noise only) | the declared state is sufficient; only observation noise | low |
| **I** (insufficiency) | a per-cell latent **outside the declared schema** modulates the SEI growth rate; observation noise identical to Arm N | high, and **rising with campaign depth** |

**Why a hidden latent and not a wrong rate constant.** The first design planted a
porosity-dependent SEI rate — the truth's `sei_rate` multiplied by a function of
electrode porosity, which the declared operator lacks. That is an *operator* error, not
a *state* insufficiency: porosity is in the declared schema, so matching on the full
declared state still determines the future, Axiom S still holds, and the sufficiency
deficit is correctly **zero**. It would have made candidate 1 look inert for a reason
that had nothing to do with candidate 1. The planted defect must be a genuine
state-space insufficiency for the sufficiency deficit to be the right instrument at
all, which is itself worth recording: *"the model is insufficient"* names two different
failures, and Spec §1's machinery addresses exactly one of them.

The latent is a scalar per cell, drawn once, constant over the campaign — so it is a
hidden **state** component in Core §3.1's sense (Axiom S fails without it) rather than
a noise process, and Arm N is the same generator with its variance set to zero. One
code path, one switch, matching how `strain_experiment.labels(..., k_drx=0.0)` produces
M11.5's withheld-free truth.

### The three candidates, made precise

Each is evaluated at a **near** and a **far** campaign depth, both reached by cycling
the same declared chain — no extrapolation outside anything declared, because the
question is whether the statistic's reading *grows*, not whether the chain is valid
there.

1. **`deficit` — sufficiency deficit trending upward.** Matched pairs are formed by
   matching on the **observable** history (the voltage trajectory), which is what a real
   campaign can match on and which leaves the unobserved components free to differ —
   Spec §1.2's own point that "matching is performed on measurable proxies, never on the
   state itself". Reported as `DeficitResult.deficit_squared` with all three terms
   (ADR-021), never the raw gap.
2. **`innovation_bias` — innovations biased rather than white.** The **signed mean**
   innovation over a window, normalised by its own predicted standard error:
   `|mean(d)| / sqrt(mean(S)/n)`. Deliberately **not** the NIS chi-squared statistic
   `omi.assimilate.innovation_drift_monitor` computes: NIS is a squared, sign-blind
   scale test, and a sequence biased by exactly the amount the model's own covariance
   predicts passes it. This is close to the CUSUM variant ADR-026 rejected as the
   default monitor, and the dry-run is the right place to find out whether the rejected
   alternative is the one an SDL claim needs.
3. **`parameter_spread` — parameter danger rising along the proposed direction.** The
   declared operator's rate parameters are refitted on data up to the current depth over
   many seeds; the statistic is the implied predictive spread of the declared target at
   **twice** the current depth (the direction an acquisition proposing "cycle harder"
   would move in), normalised by the same spread evaluated in-window. This is ADR-055's
   parameter triage in its smallest honest form — a spread, not yet a danger score,
   because the influence-times-uncertainty product needs the parameter information
   matrix ADR-055 designs and Part 5(1) does not build. Reported as what it is.

### The gate: E-41's criterion shape, with quantities a statistic can have

E-41's divergence criterion is the standing requirement and it applies here: a
candidate that is **flat** is inert regardless of its magnitude. The three criteria are
kept in E-41's order and with E-41's meanings:

| Criterion | Quantity | Fails as |
|---|---|---|
| the axis carries signal | how far the **planted insufficiency itself** moves between the two depths, in the observable's own noise units — Arm I's and Arm N's observable trajectories differenced | `INERT_AXIS` |
| the statistic diverges | `growth_ratio = separation(far) / separation(near)` | `PARALLEL` |
| the candidate has content | `separation_omi(far)` against `separation_baseline(far)` | `ADVERSE` |

with the **separation** defined in null-arm sigma units:

> `separation(depth) = |mean S(Arm I) − mean S(Arm N)| / sd S(Arm N)`

**Why null-arm sigma units.** The three candidates have incommensurable natural units
(a squared response gap, a dimensionless t-ratio, a normalised spread), and E-41's own
lesson is that a *magnitude* cannot be compared across cases — the M11.4/M11.5 disagreements
were 0.354 against 0.472, the same order, on a vacuous and a usable axis respectively.
Dividing by the null arm's own scatter makes every candidate's reading "how many
noise-widths does insufficiency move this statistic", which is the only common unit the
three share, and it is the same reasoning CLAUDE.md invariant 1 gives for
non-dimensionalising by aleatoric standard deviation.

**The growth ratio is the reported quantity, not the separation.** A statistic with a
huge but constant separation is a *detector* and not a *trend*, and Part 6's claim is
about a loop that keeps failing as it keeps proposing — which is a trend. This is E-41
verbatim: "an extrapolation test measures what happens as you go further; its
precondition has to be about divergence, not difference."

### Why `check_hold_out_discriminates` is not called

`omi.proposed.holdout.check_hold_out_discriminates` implements exactly these three
criteria in exactly this order, and this ADR does **not** call it. Its parameters are
six prediction arrays and it scores them by RMSE against a withheld-free **truth**. A
diagnostic statistic has no truth to be scored against — it has *arms*. Passing
per-seed statistic values into slots named `candidate_near` and
`truth_without_withheld_term_far` would compile and would compute numbers whose names
lied about what they were, which is worse than a sibling.

So a sibling report is written with the quantities named for what they are, citing E-41
for the criterion structure. **This is a finding about E-39/E-41's proposed Spec §9.3
wording, not about this repository's module:** the precondition was derived for
comparing two *models* over a held-out region, and v1.5's own experiment needs the same
precondition for a *diagnostic statistic*. The proposed wording as it stands does not
reach the case the next milestone requires. Filed as a framework finding.

### Baselines

Spec §9.3 requires comparison against gradient-boosted trees and tabular regression;
ADR-039 built both in numpy. The brief says "GP-baseline"; **this repository has no
Gaussian-process baseline and one is not added** — CLAUDE.md §8 forbids a new pinned
dependency for a comparison the Spec already specifies differently, and inventing a GP
here would make the dry-run's baseline arm incomparable with M10.2's and M11's, which
are the only baseline numbers in the repository. `GradientBoostedTreeRegressor` is used
as the primary baseline and `RidgeRegressor` as the second, exactly as at M11.5. The
substitution is recorded rather than silently made.

The baseline's reading of each statistic is the same statistic computed from the
baseline's own residuals in place of the chain's: a tabular surrogate fitted on the
same observable history, with its held-out residual gap standing in for the deficit,
its signed residual mean for the innovation bias, and its across-seed predictive
spread for the parameter spread. A baseline that separates the arms as well as the
chain does means the chain's diagnostic bought nothing, which is the `ADVERSE` verdict
and a real result.

### Alternatives rejected

*Use the NIS drift monitor as candidate 2.* Rejected as the candidate, kept as a
measurement. It is sign-blind (above), and its campaign-level aggregate `any_drift`
fires on 38.5% of null campaigns because it is a maximum over nineteen windowed tests
with no multiplicity correction. Both facts are reported; neither is fixed here.

*One arm plus a threshold.* Rejected: with one arm there is no way to separate
insufficiency from noise, which is the entire requirement. The two-arm construction is
what makes the null-sigma denominator available.

*Deciding the winner on separation magnitude.* Rejected — E-41's finding, applied to
this ADR's own choice.

### What would change this decision

A candidate whose growth ratio passes but whose baseline arm also passes would move the
choice to a fourth candidate rather than to a threshold, since a statistic a tabular
surrogate reproduces is not evidence about the framework. And a `DriftReport` that
separated its two tails would make candidate 2 implementable from the existing monitor
rather than beside it.

---

## ADR-058 — Measuring E-47: the parameter metric, and why orientation rather than width is the reported quantity

**Status.** Accepted — **design, and executed.**
**Track.** v1.5 planning, Part 5(1), §5.3.
**Pins.** `tests/oracles/test_parameter_ridge.py`.
**Measures** `docs/V1.4-EDITS.md` E-47, which ADR-055 designed and filed as
**Untested**.

### What has to be shown, and what would refute it

E-47 claims a declared constitutive form can be complete, in-window, excellently
fitted, and still have parameters that are unidentifiable **along the axis being
extrapolated**, so the extrapolated prediction is arbitrary within a range nothing
reports. Its worked instance is Kocks–Mecking: fit `k₁` and `k₂` where recovery is
barely exercised and many pairs fit equally well, implying different saturation levels
`(k₁/k₂)²` — and saturation is what extrapolation along accumulated strain approaches.

**A wide posterior is not the claim.** A parameter posterior that is wide in a direction
the extrapolated prediction does not depend on is harmless, and reporting only the width
would confirm E-47 on evidence that does not distinguish the harmful case from the
harmless one. The claim is specifically about **alignment**. So the reported quantity is
the angle between the ridge and the direction the extrapolation is sensitive to, and the
in-envelope angle is reported beside it as the control.

The measurement can refute the entry in a way the entry stands corrected rather than
deleted: if the ridge is real but **orthogonal** to the extrapolation-sensitive
direction, E-47's mechanism exists and its consequence does not, and the entry says so.

### The construction

The declared form is M11.5's contestant 2 — canonical Kocks–Mecking with the
temperature-dependent recovery coefficient, `θ = (k₁, k₂₀, p)`, whose **mechanism set
is complete for the training region by construction**: `TRAIN_STRAINS` all sit at or
below `GEN_GAMMA_C`, so Generator C's withheld recrystallisation term is identically
zero there. M11's failure is therefore absent by construction rather than by assumption,
which is what makes this a measurement of a *different* failure.

Fits are repeated over many seeds on the **same** in-envelope design of experiment with
**observation noise added**, which is the one thing M11.5 did not have: its contestant 2
recovered `k₁ = 8.000, k₂₀ = 2.000` exactly because its training labels were noiseless,
and E-47's confidence statement rests on the claim that with noise the same fit becomes
a ridge. That claim is what is being tested.

Noise is **relative** (a fixed fraction of each label's own magnitude) rather than
absolute, because the integrated stored density spans an order of magnitude across the
query ensemble and a constant absolute noise would weight the low-`ρ` queries out of the
fit entirely — an artefact of the noise model, not of the physics.

### The declared metric, which is load-bearing here

An angle between two directions in parameter space depends on how the parameters are
scaled, so CLAUDE.md invariant 1 applies with full force and the metric is declared:

> **Parameters are non-dimensionalised by their own true values**, `θ̃ᵢ = θᵢ / θᵢ*`, so
> a displacement reads as a *fractional* change in that parameter.

**Why not the invariant-1 default.** The default is to non-dimensionalise by the
aleatoric standard deviation across the incoming population. Here the closest analogue
would be the across-seed standard deviation of the fitted parameters — which is
*derived from the very covariance whose anisotropy is being measured*. Scaling by it
would force the diagonal of the covariance to unity and destroy the anisotropy the
measurement exists to find. The true-value scale is fixed independently of the
measurement, is available because this is a synthetic study, and is the honest choice;
the fact that a real study has no `θ*` to divide by is a limitation of the measurement
and is reported as one rather than hidden. A real study would use the nominal declared
`parameters` dict (ADR-043), which for a fitted form is the best available stand-in and
differs from `θ*` by exactly the bias the measurement is about.

### The three reported quantities

1. **Is it a ridge?** The condition number `λ₁/λ_min` of the across-seed parameter
   covariance in declared units, with the per-parameter fractional standard deviations
   beside it. A condition number near 1 means an isotropic cloud and no ridge, and E-47's
   premise fails before its consequence is reached.
2. **Where does the ridge point?** `alignment(γ) = |cos∠(v₁, e(γ))|` where `v₁` is the
   covariance's leading eigenvector — the least-constrained direction — and `e(γ)` is the
   leading right-singular vector of `∂ŷ(γ)/∂θ̃` at `θ*` over the query ensemble: the
   direction in parameter space the prediction at accumulated strain `γ` is most sensitive
   to. Reported as a **curve** over `γ` from the envelope edge outward, not at one point,
   so "the ridge rotates into the extrapolation direction as you push along the axis" is
   either visible or absent.
3. **What does it cost?** The across-seed spread of the predicted response at the far
   `γ`, against the same spread in-envelope and against the fit residual — the "range
   nothing reports", in the response's own units. Plus the across-seed spread of the
   saturation level `(k₁/k₂₀)²`, which is E-47's own named quantity.

The in-envelope alignment is the control and is expected to be **low** almost by
construction: `v₁` is approximately the null direction of the in-envelope Jacobian, so it
is nearly orthogonal to what the in-envelope prediction is sensitive to. That is why the
fit residual is excellent. The whole question is whether `e(γ)` **rotates away** from
`e(γ_envelope)` as `γ` grows, and by enough to bring `v₁` into it.

### The ADR-043 report is checked separately, and against the unwindowed form

E-47's bullet list claims the validity report can be **clean** while all this is true.
That is checkable directly and is checked against `KOCKS_MECKING` — which declares
bounds on strain rate, temperature and stored density and **none on accumulated
strain** — rather than against `KOCKS_MECKING_STRAIN_WINDOWED`. This is not
cherry-picking the favourable form: the unwindowed declaration is the one the source
actually establishes, the windowed sibling exists only because M11.5 needed the strain
bound made explicit (E-40), and the whole point of E-47's bullet is that a form can be
*silent* about the axis being extrapolated. The stored-density bound may nonetheless
bind, since saturation `(k₁/k₂₀)²` approaches the declared ceiling of 20 at the low end
of the temperature window. **Whichever way it comes out is reported, per query, as a
fraction** — not restricted to a temperature sub-range that would make the bullet true,
which would be adjusting the case to fit the criterion.

### What is *not* measured, and named as such

E-47's bullet "the state-direction triage reports a clean dangerous set" is not measured
here. It is a claim about Spec §3.3 run on the M11 chain, and measuring it would require
wiring a `ConformanceInputs` for a chain built for a different purpose. The entry's
status is updated to reflect exactly which of its bullets carry measurements and which
remain argued.

### Alternatives rejected

*A Laplace approximation / Fisher information at the fitted optimum.* Rejected as the
primary: it is cheaper and it assumes the very local quadratic structure whose anisotropy
is the finding, so a ridge it reports could be an artefact of the approximation. The
across-seed refit is the E-15 precedent (300 reseeds turning an inferred mechanism into a
demonstrated one) and it makes no such assumption. The Fisher matrix is a legitimate
*second* reading and is out of scope here.

*Reporting posterior width alone.* Rejected — it is the thing the brief specifically
identifies as insufficient, and it cannot separate a harmful ridge from a harmless one.

*Scaling parameters by their across-seed standard deviation.* Rejected: it destroys the
measured quantity (above).

### What would change this decision

A refutation — a real ridge orthogonal to the extrapolation direction — narrows E-47
rather than removing it, and the entry is corrected in place. A finding that the cloud is
isotropic at every plausible noise level would remove E-47's premise, and the entry
would be withdrawn to a confirmation like E-07.

## ADR-059 — The v1.5 declaration carrier: composition applied a second time, and a third `SpecificationVersion`

**Status.** Accepted — declaration implemented; no operator, no campaign.
**Track.** v1.5 planning, Part 5(2).
**Pins.** `tests/test_sdl_declaration.py`, `tests/test_extended_boundary.py` (unchanged and still passing, which is the property this ADR exists to preserve).

### The decision

`omi.proposed.decision.DecisionExtendedDeclaration` **holds** a `ExtendedDeclaration` whole, which
holds a v1.3 `InstantiationDeclaration` whole. Three layers, each nesting the last, none
modifying it. And `SpecificationVersion` gains a third value, `PROPOSED_DECISION_EXTENSION`, exposed as a
read-only property so a v1.5 declaration cannot be constructed claiming to be v1.4.

### Why nesting rather than fields with defaults

Adding v1.5's fields to `ExtendedDeclaration` with defaults would compile, break nothing,
and be wrong for the reason ADR-042 already gave once:

- **`omi.interface.diff` must keep receiving a v1.3 object.** Core §4's comparability claim
  — "it is comparative... which is what converts a collection of examples into evidence of
  generality" — is carried by that function, and M11's diff evidence was established against
  it. Nesting preserves it *by construction* rather than by care.
- **`specification_version` must stay unrepresentable-wrong.** ADR-042 made it a property
  rather than a field precisely so a v1.4 declaration could not be constructed as v1.3. A
  v1.4 object carrying v1.5's fields would return `PROPOSED_CONSTITUTIVE_EXTENSION` while making a v1.5 claim,
  which is E-35's defect reintroduced by the code that exists to fix it.
- **A domain a version apart must differ only in what that version adds.** Three domains,
  one per layer, is a controlled measurement of each extension. Fields-with-defaults makes
  v1.4 and v1.5 domains structurally identical and distinguishable only by which optional
  fields happen to be populated.

**The generalisation, stated because it will be needed again:** the composition discipline
is not a one-off for v1.4. Every future extension nests, and the version enum grows a value.
The cost is one indirection per layer; the benefit is that no published comparability result
ever needs re-establishing.

### What the carrier holds

| Field | Source | What it realises |
|---|---|---|
| `v14_core` | ADR-042 | the whole v1.4 declaration, including its constitutive forms |
| `coupled_quantities` | ADR-049, ADR-052 | domain, coupling, tracked dimensions + justification, descriptor basis + underlying space, closure note |
| `species_roles` | ADR-051 | role per (species, region) |
| `attainable_region` | ADR-053 | the object ADR-053 said no domain supplied |
| `decision_kind` | ADR-048, E-43 | which of Core §5's decisions the chain serves |

Three queries make the design claims checkable rather than assertable: `roles_for` (one
species' roles across regions), `parameter_only_species` (E-29's part 2, mechanically),
and `quantities_with_coupling` (the predicate E-25's refusal needs).

### One decision made against a first attempt, and it is the useful part

The pairwise-exclusion constraint's **product budget** was first written as a module
constant in `omi/proposed/v15.py`. It was moved into the domain's own declaration when the
first realistic formulation inside the attainable region was certified `EXCLUDED_PAIR` by
it. **The fix was not to retune the constant** — that would be adjusting a criterion to make
a case fit, which the standing requirements forbid. It was to notice that the constant was
in the wrong place:

> "Cannot both be high" is a claim about a particular chemistry — where the two coordinates'
> ranges sit and where their interaction actually bites. A fixed budget in domain-neutral
> code is a domain claim on the wrong side of CLAUDE.md invariant 3, and a number no domain
> ever had to defend, which is E-44's shape.

So the exclusion is now a `(a, b, budget, reason)` quadruple, the budget is domain-declared
with its basis stated, and an exclusion with a non-positive budget or an empty reason is
refused at construction — an unexplained constraint on a practitioner's search is the
unsourced-assertion shape ADR-043 rejects for constitutive forms.

### Alternatives rejected

*Fields with defaults on the v1.4 carrier.* Rejected — three reasons above.

*A flat `DecisionExtendedDeclaration` reproducing all v1.3 and v1.4 fields.* Rejected: it makes
every existing test's `diff` call a special case and re-opens exactly the comparability
question ADR-042 closed.

*Reusing `PROPOSED_CONSTITUTIVE_EXTENSION` for both extensions.* Rejected: E-35's argument is that a level
name needs its version, and two extensions sharing a version label make a v1.5 claim
indistinguishable from a v1.4 one — the defect, one layer up.

*Enumerated reason codes for `tracked_justification`.* Not implemented, deliberately. It is
a live candidate accepted at the Part 3 gate as needing **its own** decision, and folding it
in here would settle by convenience a question that was explicitly left open.

### What would change this decision

A v1.4 document actually being published, at which point `PROPOSED_CONSTITUTIVE_EXTENSION` becomes `V1_4` and
the nesting's middle layer stops being provisional. Or a demonstration that the indirection
costs more in reader effort than the comparability guarantee is worth — which would be an
argument for flattening at a *release* boundary, never mid-track.

---

## ADR-060 — The discovery domain: a third decision kind, declared and not built

**Status.** Accepted — **declaration only. No evolution operator, no campaign.**
**Track.** v1.5 planning, Part 5(2).
**Pins.** `tests/test_sdl_declaration.py` (12 checks).
**Is not** where the decision machinery gets proved. Part 5(1) did that, and reported that
two of four diagnostics do not currently drive anything.

### What it is, and why it is genuinely third

A supported heterogeneous catalyst formulated from a multi-metal precursor, calcined, then
evaluated. The claim that it is a *third* case rests on one property, and it is the control
axis:

| Domain | Control axis | Decision | Inverse problem |
|---|---|---|---|
| flagship | **apparatus**-determined | which route to run on a given material | process (control) inverse |
| contrast | **usage**-determined | how to operate a given artefact | usage (control) inverse |
| **discovery** | **acquisition**-determined | **what to make** | **composition inverse** (ADR-053) |

The third axis is not a variation on the first two. An apparatus operator follows a route
and a service duty cycle is imposed by the application; an acquisition policy *chooses the
next thing to exist*. That is what moves the Parameter-role quantities out of the fixed index
and into the decision variables, which is exactly ADR-053's definition of the composition
inverse. Composition is therefore the primary designed variable here rather than a
constant — which no existing domain exercises.

**Every one of Core §4's seven items differs from both existing domains** (measured, not
asserted: `test_the_declaration_differs_from_both_existing_domains_on_every_item`). A third
domain that agreed on several items would add little, since the existing pair was chosen to
invert each other.

### What it declares that neither existing domain does

**1. Constitutive forms with composition-dependent validity** — two of them
(`LANGMUIR_HINSHELWOOD`, `PARTICLE_COARSENING`), so the chain-level worst-case aggregation
`worst_extrapolation` has something to aggregate; a single-form domain cannot exercise it.
Plus ADR-054's second-order declaration: `COMPOSITION_VALIDITY_INTERVAL`, the descriptor
interval over which those validity ranges are *themselves* claimed to hold.

**2. Species roles per region** — and the promoter is `CONTROL` in the bulk and `STATE` in
the surface layer, **simultaneously, in one chain**. ADR-051's central claim was that the
same quantity takes different roles and that a framework hard-coding one is wrong; this is
the first declaration in the repository where it is exercised rather than argued. Support is
`PARAMETER` in both regions and is therefore returned by `parameter_only_species()`, making
E-29's part 2 mechanical: a readout depending only on it is a readout of the grade, not of
the process.

**3. An attainable region** — the object ADR-053 explicitly declined to design a certificate
for, because none existed and inventing one would be improvisation. Descriptor bounds,
underlying-space bounds, a simplex constraint, one declared pairwise exclusion with its
mechanism and its budget, and a prose route note. Its report names **which** constraint bound
across four distinct verdicts, which is what makes the composition inverse a third inverse
problem by Core §5's own separating criterion rather than a relabelled structure inverse.

**4. `GLOBAL_POINT` on a fourth independent domain** — pore-network accessibility has no
local value even in principle, which is E-22's revised case, the one that forced its first
proposed wording (a field over the body) to be withdrawn.

### Carrying Part 5(1)'s negative results forward, as required

**The validity report goes from dark to live, and the declaration says exactly what that
buys.** On contrast it was structurally unavailable: no declared form, nothing to report
against. Here the report exists, aggregates over two forms, and names for a given evaluation
which declared bound binds and in which space — so `ValidityAction` can distinguish
*re-run the control inverse* from *buy physics*, which on contrast it could not do at all.

**What it still cannot do is say whether the mechanism set is complete for the regime.** That
is M11.5's measured finding and the reason §11's buy-physics row reads "signalled on the
wrong axis". Declaring forms makes the diagnostic live; it does not make it sufficient. Said
here so Part 6 inherits the limit rather than discovering it.

**The triage stays degenerate, and this domain moves it to the other extreme rather than
fixing it.** §5.2a measured that which degeneracy the near-diagonal share exhibits tracks one
declared property: whether the chain declares an erasure. This domain declares one —
calcination genuinely destroys precursor-history information — so it is **predicted** to sit
at flagship's extreme, shares pinned at 0 or 1, margin ~0.5, rather than on contrast's
rational ladder. That is not a rescue: both extremes are degenerate, and the observed/inferred
label will be near-trivial here for the opposite reason. The prediction is recorded and
asserted now (`test_the_erasure_inventory_is_non_empty_which_predicts_the_e48_extreme`) so
Part 6 cannot mistake a trivial `observed` for an informative one.

**The influence-median degeneracy (E-48's first half) is *not* escaped either.** This domain
declares three target readouts over a seven-component state, so more than half the
eigendirections will again have exactly zero influence and the median split will again be a
tautology. Nothing in this declaration changes that, and nothing in it should — E-48's fix is
a framework decision, and pre-empting it in a domain declaration would hide the defect behind
a domain choice.

### What is deliberately absent

No `EvolutionOperator`. The erasure inventory names `CALCINATION` as a string, which is what
item 3 asks for, and no operator implements it. The constitutive forms *are* evaluable, and
that is not a contradiction: ADR-043 requires it — "a form you cannot evaluate is not a
declaration, it is an assertion" — and a declared form is a functional relationship, not an
operator that advances a state.

ADR-054's **refusal** outside `COMPOSITION_VALIDITY_INTERVAL` is likewise declared and not
implemented, because the refusal belongs to the operator that consumes the form. What is
declared is the interval the refusal would fire outside.

### Alternatives rejected

*An alloy-design domain.* Rejected: it would be a third *metallurgical* domain, overlapping
flagship's vocabulary and stage structure, so the generality claim would gain the least from
exactly the place it needs the most.

*Declaring no erasure, to escape §5.2a's flagship extreme.* Rejected as dishonest. Calcination
erases precursor history; declaring otherwise to land on a different degeneracy would be
choosing the physics to suit the diagnostic. The prediction is recorded instead.

*One region instead of two.* Rejected: ADR-051's per-region claim is only exercised where a
species holds different roles in different regions, and one region cannot exhibit it.

*Naming real elements.* Rejected: it would imply a calibration this declaration does not have.
The content is the role structure and the attainable region, not a particular chemistry — the
same discipline `flagship_constitutive.forms` states for its parameter values.

### What would change this decision

A measurement showing the acquisition-determined axis is operationally the same as the
apparatus-determined one would collapse the third decision kind into the first and remove this
domain's reason to exist. Part 6 is where that becomes checkable.

## ADR-061 — E-53 resolved: single-term dominance with abstention, both conventions declared per domain, and the reporting obligation that stops abstention becoming an escape

**Status.** Accepted — **design only. No fix implemented.**
**Track.** v1.5 planning, E-53 milestone.
**Resolves.** `docs/V1.4-EDITS.md` E-53's `[authorial-choice]`, and E-48's proposed-wording fork.
**Pins.** `tests/oracles/test_e53_option_comparison.py` (6 checks), which measures the fork rather than implementing the choice.
**Does not change** `omi.observability.danger_triage`. Part 6 remains unauthorized.

### The decision

**Option 2 with option 3's abstention.** `observed` iff
`max_{k ≤ j ≤ k+w} q_j > ρ · max_{j > k+w} q_j`; `inferred` iff the near-diagonal
contribution vanishes at the declared numerical tolerance while the direction is
identifiable from the total; **`unresolved`** whenever the ratio sits within a declared band
of `ρ`, or when neither side contributes. `ρ`, the band, the window `w` and the tolerance are
**all declared per domain** and travel with every reported classification.

### Why, and the honest limit of the claim

The brief's reading — option 2 plus abstention, with abstention the more important half — is
**accepted**, and the measurement supports it more specifically than the argument did.

**Option 2 removes the ladder, and that is measured rather than argued.** The near-diagonal
share walks `1/12, 1/10, 1/8, 1/6, 1/4, 1/2` across contrast's interior and lands exactly on
`0.5`. The dominance ratio is **`1.0` at every one of those indices**, to nine figures — the
spread across indices is below `10⁻⁶`. The ladder was an artefact of *summing over a window
and dividing by a total*; comparing two contributions that happen to be equal has no index
dependence at all.

**What option 2 does *not* do is remove a declared number, and the ADR says so.** `ρ` is
declared and it changes the answer: at `ρ = 1` — the most literal reading of *dominates* —
contrast's ratio of `1.0` sits *on* the criterion and abstains; at `ρ = 1.5` it reads
`inferred` decisively. So the honest claim is about the **margin**, not about parameter
elimination:

| | old | new |
|---|---|---|
| the declared quantity | share vs `0.5` | ratio vs `ρ` |
| distance from the criterion on contrast | **`1.4×10⁻¹¹`** | **`0.5`** at `ρ = 1.5`, or **`0`** at `ρ = 1`, where it abstains |
| index dependence | six distinct values | one |

A criterion approached to `10⁻¹¹` is decided by rounding. A criterion approached to `0.5`, or
approached to `0` *and abstaining there*, is decided by the physics or by an explicit refusal.

**Option 1 is rejected on measurement, not on taste.** The support test labels every contrast
direction `observed`, including where the near-diagonal share is `1/12` — 8% of the
information near-diagonal, 92% downstream. Spec §3.3's word *dominates* would then carry no
content. It remains the cheapest option and the ADR records that it was rejected for making
the distinction vacuous rather than for needing a number.

**The abstention is the more important half, and here is the sharpest reason.** At `ρ = 1`,
reporting *"the near-diagonal and downstream maxima are equal to eleven figures; this
direction is neither observed nor inferred"* is true and actionable — it says the chain
distributes this direction's information evenly, which is a fact about the chain. Forcing a
label there reports a rounding error as a physical finding. This is Core §3.9's refusal
discipline and CLAUDE.md §4's rule turned on the framework's own diagnostic, which is where
this repository has repeatedly found it was not being applied.

### The window: declared, not eliminated

Measured, and the answer is the one that prevents a partial repair being reported as a whole
one. **Option 2 does not eliminate the window.** Same chain, same indices, same criterion:

| window | ratio | verdict at `ρ = 1.5` |
|---|---|---|
| `0` | `~10⁻³³` | `inferred` |
| `1` | `1.0` | `inferred` |
| `2` | `1.0` and `inf` | `inferred` **and `observed`** |

So `near_diagonal_window` remains a free parameter spanning the answer, and it **must be
declared per domain with a justification**, exactly as E-48's proposed wording (extended at
the Part 5(2) triage) already requires. Fixing the threshold and leaving the window free
would repair one of the two compounding conventions and report it as both.

**What does improve is the character of the dependence.** Under the share, the window and the
threshold compounded into a label decided at machine precision. Under option 2 each window
gives a *decisive* reading (`~0`, `1`, `inf`), so the window becomes a visible modelling
choice that a reader can disagree with rather than a hidden tie-breaker.

### The reporting obligation that keeps abstention honest

**Abstention has almost no cost in code and one real cost in the conformance ladder**, and
the second is the reason for this clause.

The cost that was feared did not materialise: **nothing numeric in this repository consumes
the label.** `value_of_information`, `best_placement`, `worst_case_over_window` and
`variance_term` are functions of the Gramian, the prior and the danger scores;
`dangerous_set()` filters on `DANGEROUS`, which is decided by the influence/uncertainty
median split (E-48's *first* half) and not by the near-diagonal share. Measured structurally:
the same chain's numeric outputs are byte-identical across three window values that change
every label.

The cost that does exist is different. Spec §9.1's OMI-1 line item
`observability_triage_with_dangerous_set_declared` checks that a triage was **reported**, not
what it says. So a domain whose every direction abstains would satisfy OMI-1 with a triage
that establishes nothing — a new instance of the satisfiable-without-the-property shape §4 of
the ledger documents nine times, introduced by the fix intended to make the diagnostic honest.

**So the decision carries a reporting obligation**: an implementation adopting abstention MUST
report the **fraction of evaluated directions that abstained**, and Spec §9.1's OMI-1 item MUST
require that fraction alongside the triage. Abstention is then a measured property of the
chain rather than a way to satisfy a checklist by declining to answer.

### The publication consequence, stated plainly

**This reaches the papers, and not through the numbers.** Core §3.8 calls inferred directions
the case "which no tabular model can recover", and Spec §3.3 calls them "the framework's
distinctive contribution". That is the central argument for the operator graph over a
baseline, and it is currently stated as a **categorical count** — how many directions are
inferred.

No option preserves that form. Under any of the three, the label's population changes, and
under option 2 with abstention some directions carry no label at all. The claim has to become
a **measured quantity**: *"these directions' information accrues predominantly downstream, by
a dominance ratio of X"*, which is falsifiable and reportable where a count of labelled
directions is neither.

**The good news is that the substantive reading barely moves on the two implemented domains.**
Under option 2 at `ρ = 1.5`, contrast reads `inferred` at all twelve readings and flagship
reads `observed` wherever its erasure leaves only near-diagonal information — the same
substantive answer the current criterion gives at eleven of contrast's twelve readings. The
one reading that changes is the arbitrary flip. So the papers' *conclusion* survives; the form
of its statement does not.

### Alternatives rejected

*Option 1 alone.* Rejected on measurement (above).

*Option 3 alone — keep the share, add a band.* Rejected: it leaves the operationalisation
mismatched with Spec's own words in both directions (a sum where Spec says a single term, a
magnitude where Spec says a support condition), so it makes an arbitrary label honest without
making it correct.

*Option 2 with a framework-fixed `ρ`.* Rejected for the reason ADR-059 records about the
exclusion budget: where dominance begins is a property of a chain's sensitivity structure, so
a framework constant would be a domain claim in the wrong place and a number no domain had to
defend.

*Eliminating the window by fixing `w = 0`.* Tempting, because at `w = 0` contrast reads a
decisive `inferred` and the "single near-diagonal term" is literally the term at `k`. Rejected:
it would make `observed` unreachable for any chain whose readout at index `k` has no
sensitivity to the direction in question — which is contrast's case at every index, and which
is a property of the *readout*, not of the information structure. Choosing the window to make
one domain's answer clean is adjusting a criterion to fit a case.

### Implemented at the E-53 fix, with four choices this ADR did not anticipate

**1. The share is retained and reported, and is no longer the criterion.**
`DirectionDiagnostic.near_diagonal_share` stays; `dominance_ratio` is added beside it and the
label is computed from the ratio. Dropping the share would break the audit trail of every
result that quoted it, and it remains a legible summary.

**2. A framework `DEFAULT_CONVENTION` exists, and its justification string says a domain should
not use it.** Making the convention a required argument would change every call site at once and
destroy the audit gate's ability to show that no number moved. The default reproduces the most
literal reading of Spec §3.3 (window 0) with `ρ = 1.5`, and all three domains declare their own.

**3. `UNRESOLVED` is returned when the ratio is *undefined*, not only when it is inside the
band** — and that is where the substantive correction turned out to be. A direction classed
identifiable by the *uncertainty median* while carrying no Gramian information has no ratio;
Spec §3.3's "inferred" requires identifiability *from the total*, which it lacks. On flagship
that moved the domain's **two largest danger scores** out of the inferred set. Filed as
`docs/V1.4-EDITS.md` **E-55**, and it is the sharpest evidence for this ADR that the milestone
produced: the count the framework cites as its differentiator included directions no
observation informs.

**4. Core and Spec were NOT edited.** The E-53 milestone's brief asked for Core §3.8 and Spec
§3.3 to be reworded. They are the v1.3 specification **under audit**, not repository-owned
documents: every one of the ledger's entries cites a location in them, and editing the text
would make those citations unverifiable and make this repository the framework's author rather
than its implementer. The replacement wording lives where the repository's conventions put it —
E-53's and E-55's `Proposed wording` fields — and the four repository-owned documents that
restate the criterion (`CLAUDE.md`, `docs/ROADMAP.md`, `docs/COVERAGE.md`,
`docs/FIGURE-SOURCES.md`) were reworded in place, with `docs/REVIEW_PACK.md` corrected by dated
addendum.

### What would change this decision

A chain whose dominance ratio sits *stably* near its declared `ρ` — neither at `1` nor at
`0`/`inf` — would show that option 2's margin advantage is domain-specific rather than
structural, and would strengthen option 3's band from a safeguard into the load-bearing part.
Neither implemented domain provides one, and E-54 records why: both sit at extremes of the
error-control dichotomy, and the interior case may be rarer than the statistic's continuous
form suggests.

## ADR-062 — The audit gate gains **declared exceptions**, refuses numeric ones, and requires a retirement to name its replacement

**Status.** Accepted — implemented.
**Track.** v1.5 planning, the E-53 fix.
**Pins.** `scripts/check_audit_gate.sh`, `audit/e53-label-changes.json`.

### The problem ADR-061 created

ADR-042's audit-preservation gate exists so that a change to `src/omi/` cannot move a
previously-reported number silently: any movement is a FAIL and the instruction is to reopen the
ADR rather than re-baseline. ADR-061 changes the observed/inferred **criterion**, which is an
approved change to what a reported *label* means. Some label-valued observations therefore must
move.

That leaves three options and two of them are bad. Blocking the change makes the gate a veto on
approved work. Switching the gate off, or re-baselining, destroys the property it protects and
would do so at exactly the moment the repository is touching its most-cited diagnostic.

### The decision

**Enumerate every moved observation in advance**, in a declared-exceptions file naming its
before value, its after value and its reason. The gate then reports declared movements
separately and **still FAILS on any undeclared one**. Nothing changes silently; an approved
change is expressible.

Two guards make that more than a rubber stamp, and both were added because the first version
was one:

**1. A declared CHANGE may not be numeric.** This is the mechanical form of the claim ADR-061
rests on — that a label moved and a computed quantity did not. A numeric observation taking a
new value under its old name is not a relabelling, and a mechanism that could wave it through
would be worse than no mechanism, because it would carry the gate's authority. Bools are
exempted deliberately: in this repository's observations `True`/`False` are categorical readings,
not measurements.

**2. A RETIREMENT must name a replacement, and the replacement must be present in the run.**
Retirement is the honest handling for a *numeric* observation whose value is a label-filtered
list: its numbers did not move, but the filter selecting them did, so the list would have.
Withdrawing the name and reissuing under a new one makes that visible where reusing the name
would hide it. Without the replacement check, "retired" would be a way to delete an inconvenient
observation, so the guard is not optional.

**The distinction between the two is the whole design.** A `changed` numeric observation is
readable under its old name and returns a different number — the failure the gate exists to
prevent. A `retired` one is not readable under its old name at all, its old value is recorded
verbatim in the exceptions file, and its successor is named. The audit trail survives by
construction rather than by trust.

### What it caught, which is why the guards are in the ADR

The first version of this mechanism refused *all* numeric exceptions and therefore failed on the
two retirements — `contrast_inferred_directions_danger_scores` and
`flagship_inferred_directions_danger_scores`, both numeric-valued. That failure was correct
about the danger and wrong about the case, and the fix was to make the distinction explicit
rather than to relax the refusal. Recorded because the alternative — widening the refusal's
exemption until the run passed — is precisely how a gate becomes decorative.

### Alternatives rejected

*Re-baseline at the E-53 commit.* Rejected: it discards the 267-row invariance record
that makes every M11 result citable, in exchange for convenience at a single commit.

*A `--allow-label-changes` flag.* Rejected: a boolean cannot say *which* observations were
expected to move or *why*, so it grants blanket permission and leaves no record. The whole value
is in the enumeration.

*Splitting observations into numeric and categorical streams at record time.* Rejected as
larger and later: it would touch the `observe` fixture and every test that uses it, and the
distinction is only needed at comparison time. The `is_numeric` check does it there. Worth
revisiting if a second criterion change arrives.

### What would change this decision

A second declared-exception file arriving for an unrelated change would be the signal that
label semantics are churning rather than being corrected once — at which point the right move is
a versioned baseline per criterion rather than an accumulating exception list.

---

## ADR-063 — The **standardised signed innovation mean** is declared as a *second* monitor on Spec §10's sufficient statistic; ADR-026 is extended, not superseded

**Status.** Accepted **Gap.** S-10 (Spec §10's procedure is `[Pass C]`; the *proposition* is SPEC) **Track.** v1.5 planning, Part 6.
**Pins.** `tests/oracles/test_discovery_campaign.py`; ADR-026's own pin (`tests/oracles/test_known_drift.py`) is unchanged and still passes.

### The question this ADR exists to answer

Part 5(1)'s dry-run selected `innovation_bias` — the **signed** mean innovation over a
window, normalised by its own predicted standard error — as the only one of three candidates
that both diverged along the axis and beat the Spec §9.3 baseline
(`docs/V1.5-PART5-1.md` §3). ADR-026 chose the **NIS chi-squared consistency test** as the
drift monitor and, under *Alternatives rejected*, turned down "CUSUM on the innovation mean".
A signed statistic on the innovation mean therefore looks like the thing ADR-026 refused, and
Part 6's brief is explicit that if ADR-026's reasoning still holds this needs a superseding
ADR rather than a footnote.

**It does not need one, and the reason is in ADR-026's own text.** Two separate points, and
both have to hold:

**1. ADR-026 pre-authorised exactly this.** Its rejection paragraph ends: *"A CUSUM variant is
not precluded and could be added as a second declared monitor later."* The rejection is scoped
to *the default* — which statistic the framework's one drift monitor should be — and not to the
class of sign-sensitive statistics. So the instrument is a new ADR declaring a **second**
monitor. Nothing in ADR-026 is withdrawn: `innovation_drift_monitor` keeps the chi-squared
convention, keeps its window and confidence defaults, and remains what
`docs/ROADMAP.md` M5's exit gate is satisfied by.

**2. ADR-026's specific objection does not transfer, because the selected statistic is not a
CUSUM.** The objection was mechanical and narrow: CUSUM *"needs a reference/slack parameter
Spec gives no basis for either"*. A CUSUM accumulates `max(0, C_{i-1} + d_i − k)` against a
decision interval `h`, so it carries two invented numbers. The selected statistic is

> `z_n = |mean(d_1..d_n)| / sqrt(mean(S_1..S_n) / n)`

— a standardised mean, with **no slack, no reset and no accumulator**. Its scale comes from
`S_j`, the innovation covariance the filter already computes and the same quantity ADR-026's
own statistic divides by; its reference is zero, which is what Spec §10's proposition asserts
the innovation sequence has as its mean under a correctly specified model. So it introduces
**no parameter ADR-026 does not already accept.** What it shares with CUSUM is only the
*motivation* ADR-026 credited — "better at detecting small sustained biases". The motivation
transfers; the objection does not.

Stated plainly because the distinction is the whole disposition: **ADR-026's reasoning still
holds, and the statistic it holds against is a different statistic.**

### Decision

Declare the standardised signed innovation mean as a second monitor, with these conventions:

1. **Statistic.** `z_n` above, over the innovations pooled across the declared campaign — not
   over a sliding window. The window is ADR-026's convention for a *drift* question ("has the
   model changed since interval `k`"); this monitor answers a *campaign* question ("is the
   model biased over the campaign so far"), and a sliding window would discard the accumulation
   that makes `n` the axis.
2. **Reference distribution.** Standard normal, so a control limit is a normal quantile — as
   textbook and as citable as ADR-026's chi-squared limit, and for the same reason: this
   repository must not invent a distribution for a statistic it invented a use for.
3. **Reported together, never alone.** The signed mean, the pooled predicted variance, `n`, and
   the resulting `z_n` are all returned. ADR-026's reporting discipline verbatim; and the
   *sign* is retained in the report even though the statistic takes an absolute value, because
   E-49's finding is precisely that a monitor which records no direction cannot say which
   response is indicated.
4. **No threshold here.** The control limit is a pre-registered quantity and belongs to Part
   6's pre-registration, in its own earlier commit.

### Why the two monitors are not redundant, measured rather than argued

NIS is `d^T S^{-1} d`, squared and therefore sign-blind. A sequence whose innovations are
biased by *exactly* the amount the model's own covariance predicts has `E[NIS] ≈ 1 + bias²/S`
and passes a two-sided chi-squared window test at any ordinary confidence level, while `z_n`
grows as `√n`. That asymmetry is the reason the dry-run rejected the existing monitor as a
candidate and it is what this ADR buys: **the two monitors have different null hypotheses.**
NIS asks whether the innovations have the predicted *magnitude*; `z_n` asks whether they have
the predicted *mean*. A framework whose stated proposition is that the innovation sequence is a
sufficient statistic for drift needs both, and Spec §10 names neither.

### Alternatives rejected

*Supersede ADR-026 and make the signed statistic the default.* Rejected. The default monitor is
answering the question `docs/ROADMAP.md` M5 asked and answers it correctly; replacing it would
retire a passing oracle to make room for a statistic selected for a different question. Two
declared monitors with stated scopes is the honest structure, and it is the one ADR-026
anticipated.

*Add it as a field on `DriftReport`.* Rejected for this gate, and the reason is E-49: that
report already conflates a per-window statistic with a per-campaign aggregate, and bolting a
third statistic onto it would deepen the conflation this repository has filed as a framework
defect. The monitor lives beside it until E-49 has a disposition.

*Implement it as a CUSUM after all, to test ADR-026's rejection directly.* Rejected as out of
scope rather than as wrong. It would need the slack parameter ADR-026 refused to invent, and
Part 6 does not need it — but it remains the honest way to settle whether the *stronger*
sequential test would do better, and it is recorded as an open alternative rather than as a
closed one.

### What would change this decision

A Spec revision naming a functional of the innovation sequence would supersede both this ADR
and ADR-026 together. And a measurement showing `z_n` fires on correctly specified campaigns at
a rate materially above its declared limit would put it where E-49 puts `any_drift`: a sound
statistic with an unsound aggregate. Part 6's null arm is where that becomes visible, and it is
pre-registered as a reported quantity rather than as a check that may be skipped.

---

## ADR-064 — The discovery domain's three operators, with calcination as a **measured** erasure

**Status.** Accepted **Gap.** none for the operators themselves (Core §3.2/§3.3 are SPEC); ADR-060's deferral is what is being discharged **Track.** v1.5 planning, Part 6.
**Pins.** `tests/test_sdl_operators.py`.

### Why they are built now, having been deliberately absent

ADR-060 declared the discovery domain with **no** evolution operator and said the operator was
"Part 6's work". Part 6's gate requires the vacuity precondition to be re-verified *on the
domain the claim will be made on*, because a statistic that discriminates on one chain and is
inert on another is M11.4's failure exactly. That check cannot be run against a declaration.
So the operators are built, and nothing else about ADR-060's deliberate absences changes:
ADR-054's out-of-interval **refusal** is still not implemented, and the Tier II anti-goals are
untouched.

### The three operators

| operator | what it does | `is_erasure` |
|---|---|---|
| `Preparation` | impregnation and drying: the recipe becomes a dried precursor state | `False` |
| `Calcination` | thermal treatment: the oxide's dispersion is set by composition and temperature | **`True`** |
| `Evaluation` | reaction at a declared condition, with time-on-stream deactivation | `False` |

**Composition is a field of the operator, not a component of the state.** This is ADR-051's
Parameter role and ADR-046's separation realised in code: the operator *family* is indexed by
composition, and a campaign chooses which member to instantiate. Putting composition in
`SDL_SCHEMA` would type a fixed index as a state, which is the mis-typing E-46 separates; and
it is what makes ADR-053's composition inverse a third inverse problem rather than a relabelled
structure inverse — the decision variable is an operator index, not a state.

**Calcination's erasure is measured, not asserted.** The mechanism is that the calcined
dispersion is thermodynamically set: every post-calcination component is a function of
composition and the calcination programme, plus a small feed-through of the incoming precursor
state. The exception is `dispersed_phase_loading`, which is conserved exactly — the domain's own
declared invariant `metal_mass_conservation_across_calcination`. So the Jacobian has one
singular value near unity and the rest near the feed-through coefficient, and the erasure
measurement must recover an effective rank of **one out of seven**. That is asserted by the
oracle rather than by this ADR's prose.

### The one design choice that is not physics, and is declared as such

The feed-through coefficient (`PRECURSOR_FEEDTHROUGH`) is a declared number with no Spec basis.
It sets *how complete* the erasure is, and therefore what `measure_erasure` reports. It is
declared at the module level with its consequence stated, not buried in an expression, and the
oracle asserts the qualitative claim (rank one, `L ≪ 1`) rather than the value — CLAUDE.md §7's
rule about not freezing tuning constants.

### Alternatives rejected

*Make calcination erase every component including loading.* Rejected: it would contradict the
domain's own declared invariant. An erasure that violates a declared conservation law is not a
more complete erasure, it is a wrong operator.

*Put composition in the state schema so the chain is a single closed system.* Rejected — see
above; it would also make the attainable region a constraint on a state, which would collapse
the composition inverse into the structure inverse and remove the domain's reason to exist
(ADR-060).

*Use the declared constitutive forms as the operators.* Rejected as a category error, on
ADR-060's own wording: a declared form is a functional relationship, not an operator that
advances a state. The forms are *consumed* by `Evaluation` — `PARTICLE_COARSENING` sets the
size increment and `LANGMUIR_HINSHELWOOD` is what the turnover readout evaluates — which is
what makes the validity report live on a real trajectory rather than on a hypothetical query.

### What would change this decision

A domain that needed composition to *evolve* — reactive loss of a volatile promoter, say —
would need it in the state, and the Parameter/State distinction would then have to be declared
per species per region rather than per species. ADR-051 already provides that shape, and this
domain's own `promoter` is `CONTROL` in the bulk and `STATE` in the surface layer, so the
structure is exercised; what is not exercised is a species that changes role *along* the chain.

---

## ADR-065 — A **Gaussian-process acquisition comparator**, built in numpy, with Expected Improvement; ADR-057's refusal is scoped rather than overturned

**Status.** Accepted **Gap.** S-9.3 (Spec §9.3 names baselines and does not name an acquisition comparator) **Track.** v1.5 planning, Part 6.
**Pins.** `tests/oracles/test_discovery_campaign.py`.

### What ADR-057 refused, and why this is not that

ADR-057 declined to add a Gaussian process and the reason was specific: Spec §9.3 *requires*
gradient-boosted trees and tabular regression, ADR-039 built both in numpy, and substituting a
GP into the **baseline arm** would make the dry-run's baseline numbers incomparable with
M10.2's and M11.5's — the only baseline numbers in the repository.

Part 6's claim names a GP-based acquisition as the thing that cannot attribute a failing
campaign to model insufficiency. A comparative claim cannot be evaluated without its
comparator. But the role is different, and the difference is what preserves ADR-057:

| role | instrument | unchanged? |
|---|---|---|
| Spec §9.3 **regression baseline** | `GradientBoostedTreeRegressor`, `RidgeRegressor` | **yes** — still the only §9.3 baselines, still comparable with M10.2 and M11.5 |
| Part 6 **acquisition comparator** | `GaussianProcessRegressor` + Expected Improvement | new, and named for what it is |

So ADR-057's refusal is **scoped, not overturned**: no §9.3 baseline number changes, and no
existing comparison is re-based. And no new dependency arrives — the GP is written in numpy
exactly as ADR-039's baselines were, for exactly ADR-039's reason.

### The design, and why each choice is the fair one

**Kernel.** Anisotropic squared-exponential (ARD) plus a fitted white-noise term, on
standardised inputs. ARD rather than isotropic because the composition coordinates have
genuinely different scales — the promoter is bounded at 0.08 and the support at 1.0 — and an
isotropic kernel on unequal ranges is a weakened opponent for a reason that has nothing to do
with the claim. Spec §9.3's own requirement is a fair baseline, and M11 established that a
weakened one produces an uninterpretable result.

**Hyperparameters by marginal likelihood**, refitted at every campaign step over a declared
grid of length scales and noise levels. This is the standard practice and it matters *more*
than usual here: the fitted noise level is the GP's own best insufficiency signal, so fixing it
would hand the framework the comparison by construction.

**Acquisition: Expected Improvement**, in closed form against the incumbent best. Chosen over
UCB because UCB needs an exploration weight `β` and there is no basis for a value — which is
ADR-026's slack-parameter objection applied to the comparator, and applying this repository's
own standard to the opponent is the point. EI needs only the incumbent, which the campaign
already has. Thompson sampling was the other candidate and is rejected below.

### What the GP is expected to do well — stated in advance, as the brief requires

The GP will handle in-distribution predictive uncertainty **better than the framework chain
does**. It is fitted to the observed objective directly, so it is calibrated on exactly the
quantity the campaign optimises, while the chain predicts through a declared state and inherits
every error in that declaration. It will also find good compositions faster early on, because
EI on a smooth response surface is very effective and the chain contributes nothing to the
*search*. The claim is **not** that the GP predicts worse.

**The claim is about attribution, and the mechanism is stated now so the experiment cannot be
read as having discovered it afterwards.** A GP that meets unexplained variance absorbs it into
its fitted noise term `σ̂_n`. That term rises whether the variance comes from a missing state
variable or from noisier measurements, and it **converges** as the campaign lengthens in both
cases. The framework's statistic divides a signed mean by a *model-predicted* standard error, so
a persistent bias makes it grow as `√n` while zero-mean measurement scatter leaves it `O(1)`
however large the scatter is. That is the whole difference: the GP has no predicted covariance
to be inconsistent with, because it fits its own.

### Can the experiment distinguish "worse" from "cannot attribute"? Yes — and only because of a third arm

**Stated plainly, because the brief asks for it now rather than later: a two-arm experiment
cannot evaluate this claim.** With a null arm and an insufficiency arm, `σ̂_n` separates the
arms perfectly well, so a two-arm design would either show both instruments working or show the
GP working better, and neither reading bears on attribution.

The claim's contrast is *insufficiency versus exploration noise*, so the experiment needs an arm
that **is** exploration noise: a third arm with no hidden variable and inflated observation
noise, calibrated so the GP's `σ̂_n` reads the same as in the insufficiency arm. The registered
comparison is then arm I against arm X, and:

- if the framework statistic separates I from X and `σ̂_n` does not, the claim stands;
- if neither separates them, the claim fails and the framework's diagnostic is no better than
  the GP's on the one contrast it was built for;
- if both separate them, the claim fails in the more interesting way — the GP could attribute
  after all.

All three are publishable and the second and third are pre-committed as such in the
pre-registration.

### One consequence for E-41's precondition, recorded rather than worked around

E-41's third criterion is `separation_candidate(far)` against `separation_baseline(far)` — a
**baseline comparison**. On this experiment the baseline comparison *is* the registered claim.
So criterion 3 cannot be evaluated at gate time without looking at the pre-registered quantity,
and the gate therefore reports criteria 1 and 2 (axis signal, divergence) on the I-versus-N
axis and defers criterion 3 to the sweep. This is a property of E-41's wording meeting a
pre-registered comparative experiment, not a licence taken here, and it is filed as a framework
finding rather than resolved by relaxing the criterion.

### Alternatives rejected

*Thompson sampling instead of EI.* Rejected: it makes the campaign's sample sequence a random
draw from the posterior, so two arms sharing a seed no longer share a trajectory and the
"one generator, one switch" property that makes the arms comparable is lost.

*Give the GP the declared state as features.* Rejected as unfair in the *other* direction — it
would be a hybrid, not the GP-based acquisition the claim names, and a comparator built partly
out of the thing it is being compared against cannot separate the two.

*Let the framework chain drive the campaign too, as a second policy.* Rejected for this gate.
It is a different and larger experiment (which *policy* finds better materials), it would need
the composition inverse wired to the acquisition, and the registered claim is about diagnosis
rather than about search. The GP drives both arms; the framework watches. That also removes any
suspicion that the framework's diagnostic looks good because it chose favourable samples.

### What would change this decision

A measurement showing `σ̂_n` *does* grow with campaign length under insufficiency and not under
noise would refute the mechanism above and the claim with it, before any threshold is applied.
It is a reported quantity for that reason.

---

## ADR-066 — The planted insufficiency is a **hidden state component set at a known step**, and the campaign axis is the number of samples

**Status.** Accepted **Gap.** S-1.2 / S-8 (Spec §8 sizes a campaign; nothing specifies how a campaign-level diagnostic is validated) **Track.** v1.5 planning, Part 6.
**Pins.** `tests/oracles/test_discovery_campaign.py`.

### The construction

A scalar `precursor_texture` per sample, drawn at **preparation** and **absent from
`SDL_SCHEMA`**. It scales the coarsening rate that `Evaluation` applies, multiplicatively as
`exp(τ)`. Arm N draws it with zero variance, so the three arms are one generator with two
switches.

**It is a state insufficiency and not an operator error, and Part 5(1)'s lesson is why that
sentence is here.** The dry-run's first construction planted a porosity-dependent rate — an
operator error over a *declared* component — so matching on the full declared state still
determined the future, Axiom S still held, and the sufficiency deficit was correctly zero. The
statistic would have been measured against the wrong object. Here the added quantity is outside
the declared schema by construction: two samples with identical declared post-calcination state
and identical evaluation control have different futures, which is Axiom S failing with respect
to the declared state (Core §2.1).

**Introduced at a known step**, so the ground truth of *where* is known and not inferred:
`Preparation` sets it, `Calcination` passes it through, `Evaluation` consumes it.

### Why `exp(τ)` and not `1 + τ`

`τ` has mean zero, so a linear effect would cancel in the campaign mean and the signed statistic
would be reading a zero-mean quantity — the statistic would fail for an arithmetic reason rather
than a physical one. A multiplicative-exponential rate is the ordinary way an unobserved
texture enters a thermally activated process, and `E[exp(τ)] = e^{σ²/2} > 1`, so the population
coarsens *faster on average* than the declared model predicts. The declared model is therefore
biased in a fixed direction, which is what the monitor is for.

Recorded because it is a real constraint on the class of insufficiencies this statistic can
see: **a signed monitor detects insufficiencies with a non-zero mean effect, and is blind to
symmetric ones.** That is a limitation of the selected statistic, it is stated in the
pre-registration as a scope limit, and it is not a defect of the construction.

### The axis is the number of samples, and the growth mechanism is arithmetic

`z_n = |mean(d)| / sqrt(mean(S)/n)`. Under a persistent bias `b`, `z_n ≈ |b|√n / sd`, so the
statistic **grows as `√n`**. Under zero-mean scatter of any size, it stays `O(1)`. So the
divergence E-41 requires is not an empirical hope here — it is the statistic's own scaling, and
the growth ratio between a near and a far campaign length is predicted in closed form as
`√(n_far / n_near)` before anything is run. Measured against that prediction, the way
`tests/oracles/known_decaying_sensitivity.py` measures the dominance ratio against
`λ^{−2(w+1)}`.

**Near and far are prefixes of one campaign, not two campaigns.** A campaign of 32 samples
contains the campaign of 8 samples that produced it, so reading the statistic at both depths
costs one run and removes the seed-to-seed difference between the two depths — which would
otherwise be a confound on exactly the quantity being measured.

### Arm X and its calibration — **amended before the thresholds were committed**

Arm X inflates the observation noise and plants nothing. It is matched to arm I on the
**variance of the declared model's innovations** — the unexplained scatter a practitioner would
actually see — with the inflation factor solved in closed form (innovation variance is affine in
the squared inflation, so two grid points determine it exactly) at a declared seed set disjoint
from the sweep's, and then **held fixed**. The solved value and the two matched variances are
recorded in `tests/oracles/part6_thresholds.py`, which is committed with the pre-registration
rather than with this ADR: the rule belongs to the design and the numbers belong to the
registered commit.

The two arms therefore have **equal unexplained scatter, and only one has a biased mean.** That
is the decomposition the whole claim turns on, stated as a property of the construction.

**This ADR's first version calibrated arm X on the comparator's own fitted noise, and that was
circular.** Matching the GP's reading between arms I and X *sets* the numerator of the GP's
separation to approximately zero — so "the GP cannot attribute" would have been true by
construction rather than measured, and the experiment would have had only one real criterion
while reporting three. Caught while drafting the pre-registration, and recorded here rather than
quietly fixed, because a reader of the earlier text would otherwise draw a stronger conclusion
from the result than it supports.

Matching on the innovation variance keeps **both** instruments' readings as outcomes:

- it does not fix the framework statistic, which is a function of the innovation *mean*;
- it does not fix the comparator's statistic, which is a fitted noise level on a surface over
  composition, not a moment of the declared model's residual.

It is also design information of the kind M11.5's pre-registration §5 established as admissible:
a property of the *generator*, computed by running it and differencing, with no contestant
scored and no registered comparison evaluated. The calibration is performed in the
pre-registration commit and disclosed there.

**A consequence worth stating in advance, because it is favourable and therefore suspect.** The
solved inflation is small, because the latent's contribution to innovation *variance* is modest
while its contribution to the innovation *mean* is not. So arm X will look much like arm N to any
variance-based diagnostic. That is the honest content of the claim — a bias and a
scatter are different things, and only an instrument with a predicted covariance can tell them
apart — but it also means the experiment is measuring a construction in which the discriminable
signal is a mean shift. A different insufficiency, contributing mostly variance, would not be
detected by this statistic at all. Already recorded above as the scope limit; repeated here
because the calibration is where it becomes quantitative.

### Alternatives rejected

*Make the latent a function of composition.* Rejected, and it is the trap Part 5(1) fell into
in a different disguise: a latent determined by the recipe is a mis-specified operator, since
composition is a declared operator index. It would also make the insufficiency detectable by
the GP, which fits the objective as a function of composition — so the experiment would be
measuring whether the GP's feature set covers the defect, not whether it can attribute one.

*Plant the insufficiency in the erasure's own destroyed subspace.* Rejected as uninformative:
calcination erases the declared precursor state, so a latent it also erased could not reach the
readout and no statistic could see it. What is *interesting* — and is reported as a finding
rather than designed around — is that the declared erasure does not erase this latent at all,
because the latent templates the dispersion. An erasure declared over the declared state says
nothing about a variable that is not in it.

*Use campaign depth in evaluation intervals instead of samples.* Rejected: the claim is about a
campaign, and a campaign's length is how many things were made. Time on stream is a within-sample
axis and is held fixed so the sample count is the only thing that moves.

### What would change this decision

A measured `z_n` that does **not** track `√n` under arm I would mean the bias is not persistent
— most likely because the filter absorbs it — and the construction would need the bias made
structural rather than the threshold made loose. That comparison against the closed form is a
gate quantity for that reason, not a post-hoc check.

---

## ADR-067 — Version numbers name **issued** specifications only; a proposed change is named by what it proposes

**Status.** Accepted **Gap.** none — this is a repository naming convention, not a framework gap **Track.** housekeeping, before the arity redesign.
**Pins.** `tests/test_extended_boundary.py`; the citation lint (`tests/lint/test_citations.py`) catches any stale identifier.

### The tangle

Nothing beyond **OMI v1.3 has ever been issued.** Despite that, this repository had:

- a class `ProposedV14Declaration` carrying the constitutive-form extension;
- a class `ProposedV15Declaration` carrying the decision extension;
- enum members `SpecificationVersion.PROPOSED_V1_4` and `PROPOSED_V1_5`;
- a module `omi/proposed/v15.py` and a test `tests/test_v14_boundary.py`.

Two things are wrong with that, and the second is the load-bearing one.

**"v1.4" was attached to an unissued carrier.** If a v1.4 specification is issued and its
contents differ from ADR-042 – ADR-045's extension — which is likely, since the extension is a
*proposal* and this repository's own ledger argues for changes it does not contain — then every
identifier above lies about what it carries, and the number is burnt.

**And the numbering does not have to be spent.** No published artefact uses "v1.4" or "v1.5" as
an issued version. So reserving both costs nothing and skips nothing.

### Decision

**Version numbers name issued specifications only. A proposed change is named by what it
proposes.**

| was | is |
|---|---|
| `ProposedV14Declaration` | `ExtendedDeclaration` |
| `ProposedV15Declaration` | `DecisionExtendedDeclaration` |
| `SpecificationVersion.PROPOSED_V1_4` | `PROPOSED_CONSTITUTIVE_EXTENSION` |
| `SpecificationVersion.PROPOSED_V1_5` | `PROPOSED_DECISION_EXTENSION` |
| `src/omi/proposed/v15.py` | `src/omi/proposed/decision.py` |
| `tests/test_v14_boundary.py` | `tests/test_extended_boundary.py` |

`SpecificationVersion.V1_3` keeps its number, because v1.3 **is** issued — which is the rule
working rather than an exception to it. The enum's own docstring is reworded from "which version"
to "which **claim target**".

### Why the enum members were renamed too, and not carved out

The narrower option was to rename only the carrier classes and leave the enum, with a stated
carve-out ("a `PROPOSED_` prefix marks a target that is not an issued version"). Rejected,
because it produces the **worst** of the three states: a version-free carrier stamping
version-named claims. A reader of `ExtendedDeclaration` marked `PROPOSED_V1_4` learns that the
repository knows the name is wrong and applied the knowledge in one place.

**And renaming them implements `docs/V1.4-EDITS.md` E-43 rather than working around it.** E-43's
finding is that a conformance level plus a framework *version* is still not self-describing,
because the version does not carry the framework's **purpose** — two reports at the same level
and version can be answering different questions. A target named
`PROPOSED_DECISION_EXTENSION` carries its purpose in the name. So the rename is not cosmetic;
it is the smallest available step toward what E-43 asks for.

### What is deliberately **not** renamed

**`docs/V1.4-EDITS.md` keeps its filename**, and this is a requirement rather than a
convenience. The path is cited from **commit-stamped snapshots** — `docs/REVIEW_PACK.md`,
`build/REVIEW-EXTRACT.md`, the M11.4 and M11.5 documents — which CLAUDE.md §10 forbids editing.
Renaming the file would break citations in documents that cannot be repaired. Its header note
already records that the target version moved. The same argument protects the eight
`docs/V1.5-*.md` filenames.

**ADR titles keep their version numbers** (ADR-042 "The v1.3/v1.4 boundary", ADR-048 "v1.5's
purpose extension", ADR-059 "The v1.5 declaration carrier"). An ADR is a dated record of a
decision as it was taken; retitling one falsifies the record and breaks every citation to it.
Same for **track names** — "v1.5 planning" labels a body of work whose documents are named for
it and cited from snapshots — and for **commit titles**, which `REPRODUCE.md`,
`audit/README.md` and `scripts/check_audit_gate.sh` quote when they name the audit baseline's
commit (`57f7db8`, "M10.4 Part B: plan the proposed-v1.4 constitutive track"). A quoted commit
message is unchangeable by construction.

**`docs/V15-PLANNING-RECORD.md` is a snapshot and was not touched**, so it still says
`SpecificationVersion` gained `PROPOSED_V1_5`. That remains an accurate record of the name at
that commit and needs no addendum; a reader following the snapshot rule expects exactly this.

### Alternatives rejected

*Rename the ledger file to something version-free.* Rejected — see above; the snapshot rule
makes it impossible to do without breaking unrepairable citations.

*Number the extensions `v1.4-draft`, `v1.5-draft`.* Rejected: it still spends the numbers, and a
draft number invites the same confusion one indirection later.

*Do nothing until a specification is actually issued.* Rejected because the cost only grows. The
arity redesign will rename these carriers anyway, and doing both in one commit makes the diff
unreadable — which is the ordinary argument for separating a mechanical rename from a
substantive change.

### What would change this decision

An issued v1.4 whose contents *are* ADR-042 – ADR-045's extension would make
`PROPOSED_CONSTITUTIVE_EXTENSION` the historical name of something that now has a number, at
which point a `V1_4` member is added and the proposed one is retired with a pointer — the same
retire-and-reissue discipline ADR-062 applies to observations.

---

## ADR-068 — Erasure completeness is **two quantities**, and Core §3.9's condition (a) is **refused** without a sufficiency deficit

**Status.** Accepted **Gap.** none in Spec's own text — both targets are SPEC-marked, which is what makes this a *correction* rather than a gap fill **Track.** the E-56/E-57 repair, after v1.5 planning closed.
**Pins.** `tests/test_erasure_two_quantities.py` (6 checks). `tests/test_sdl_operators.py` and `tests/test_flagship_real_erasure.py` are unchanged and still pass — the repair is additive.

### Two independent repairs, one commit, because they are one finding read twice

`docs/V1.4-EDITS.md` E-56 and E-57 are §1's seventh headline finding. They are separate defects
and the code changes do not depend on each other, but both concern what an erasure measurement
licenses, so splitting the commit would put half a repair in the tree.

### E-56 — `ErasureCompleteness`, and a `__bool__` that raises

Core §3.4 defines an erasure operator by an image of substantially lower effective dimension
**and** `L ≪ 1`, joined as one definition. Measured on the discovery domain's calcination: rank
**1 of 7** at a declared tolerance, surviving-subspace gain **14.44**. The first clause holds as
completely as the rank criterion admits; the second is violated by more than an order of
magnitude, because the surviving direction is the domain's own declared conservation invariant —
which is exactly where a mass-conserving operator's gain must live.

So `ErasureMeasurement.completeness()` returns an `ErasureCompleteness` carrying
`effective_rank`, `state_dimension`, `tolerance`, `surviving_gain`, `erased_gain` and the
`metric`, with `dimension_collapsed` and `gain_contracted` as **two separate** booleans and a
`summary()` that always states both.

**`__bool__` raises `TypeError`, and that refusal is the substance of the repair.** The brief was
explicit: where a caller expects a single verdict it must receive both or refuse, and no combined
score may be synthesised. A combined score would bake Core §3.4's own conflation into this
repository, where it would then be mistaken for the framework's position — CLAUDE.md §4's
standing objection to plausible-looking implementations of underspecified things. Raising is the
only enforcement that survives a later caller who has not read this ADR.

**No existing caller had to change.** Surveyed before writing: `conformance.py` has no erasure
line item at all, and `EvolutionOperator.is_erasure` is a *declaration* (a domain saying what it
believes) rather than a measurement, so it stays a bool. Every consumer in `tests/` and
`scripts/` already read `rank` and `spectrum` separately. So this repair adds a safer reading and
removes none — and the fact that nothing consumed a single verdict is itself worth recording,
because it means the conflation lived in the *definition* and in the prose, never in a call site.

### E-57 — `condition_a_claim` refuses by default

Core §3.9 offers a dichotomy: error accumulation is controlled either by an erasure operator, or
by observation density sufficient for assimilation to correct drift. Condition (a) is stated as a
property of the operators. It is not. An erasure acts on a basis of the **declared** state; a
quantity outside that state is not in its Jacobian's domain, so no amount of rank collapse says
anything about it. Measured: a chain declaring the rank-1-of-7 erasure above still has unbounded
campaign error, `z_n` growing `1.72 → 4.00`.

`condition_a_claim(completeness, evidence=None)` therefore returns an `ErrorControlClaim` whose
verdict is one of five, checked **in order** so the reported reason is the first thing that
actually blocks (Spec §7.3's ordered diagnosis, and E-06's finding that an unordered report
cannot say which term is responsible):

| verdict | when |
|---|---|
| `REFUSED_DIMENSION_NOT_COLLAPSED` | §3.4's first clause fails |
| `REFUSED_GAIN_NOT_CONTRACTED` | §3.4's second clause fails — E-56's case |
| `REFUSED_STATE_UNTESTED` | **the default**: no deficit supplied |
| `REFUSED_DEFICIT_ABOVE_THRESHOLD` | the state was tested and found insufficient |
| `CLAIMABLE` | both clauses hold and the state was tested sufficient |

**Refusing by default rather than assuming is the whole repair.** The common case is that nobody
supplied a deficit, and under the old reading that silently meant "the bound holds". It now means
"the precondition is unverified", which is what CLAUDE.md §4 says a framework that knows when to
refuse is worth more for.

### `StateSufficiencyEvidence` takes a value and a provenance, not a `DeficitResult`

`omi.erasure` does **not** import `omi.sufficiency`, and that is deliberate rather than a
dependency-cycle workaround (there is no cycle — checked). What condition (a) needs is *evidence
that the declared state was tested*, not a particular estimator's output type. A caller using a
different deficit estimator, or a published number from a prior campaign, can supply it. The
`threshold` is caller-supplied because Spec §1 specifies no universal value and inventing one
here would be improvisation; `provenance` is validated non-empty, on ADR-043's reasoning that a
number without a source is an assertion rather than a measurement.

### Alternatives rejected

*Return a single `is_complete` bool computed as `dimension_collapsed and gain_contracted`.*
Rejected — that *is* the combined score, and it would make an operator that collapses six of
seven directions indistinguishable from one that collapses none.

*Default `condition_a_claim` to claimable when no deficit is given, with a warning.* Rejected: a
warning is not a refusal, and the failure mode E-57 documents is precisely a reader taking the
bound as established.

*Put the claim in `conformance.py` instead.* Rejected for now, and the reason is sequencing: the
arity redesign restructures what the declaration items are and therefore what OMI-0/1/2 certify.
Wiring a new conformance line item before that lands would be work done twice. The claim object
exists and is unwired, which is stated rather than hidden.

*Edit Core §3.4 and Core §3.9.* Refused, as throughout: they are the v1.3 specification under
audit. The proposed wording is already in E-56 and E-57.

### What would change this decision

A domain declaring an erasure that is complete in **both** senses *and* carrying a measured
deficit would produce this repository's first `CLAIMABLE` verdict on real physics. None of the
three domains does today — flagship's erasure contracts but no deficit is wired to it, and
calcination fails the gain clause — so the `CLAIMABLE` branch is currently exercised only by a
constructed case, and that limit is recorded in the test rather than smoothed over.

---

## ADR-069 — The audit gate is re-keyed on `(test, name)`; the baseline moves to a versioned scheme, and the trigger for it was ADR-062's own

**Status.** Accepted **Gap.** none — this is a repository verification-tooling defect, not a framework gap **Track.** arity-redesign Stage 1, before any interface field is touched.
**Pins.** `scripts/check_audit_gate.sh` (rewritten); `audit/BASELINES.md`; `audit/baselines/v13-items7.json`.

### Two decisions, one commit, because the second was made possible by verifying the first

E-60 found that the audit gate's `{name: row}` comparison silently drops any observation whose
name is shared by more than one test — 44 of the v1.3 baseline's 267 rows, 16.5%, never
compared. Fixing the keying and re-baselining are one piece of work: the repair has to be
verified *before* a new baseline is frozen under it, or the freeze would just be trusting the
same class of defect one level up.

### The keying repair

`before = {(o["test"], o["name"]): o for o in baseline}` — a tuple key, guarded: the script now
refuses to run at all if either the baseline or the current run has a duplicate `(test, name)`
pair, rather than silently keeping the last one. Declared exceptions (`audit/e53-label-changes.json`)
stay named by `name` alone — ADR-061's format is unchanged — resolved to a `(test, name)` pair
at gate time, and refused as **ambiguous** if the name resolves to more than one pair. No
declared-exception file has needed to name a test explicitly so far, because no declared name is
currently duplicated; the guard exists for the day one is.

**Verified before trusting it.** All 44 previously-uncompared rows were checked against a fresh
full-suite run, matched by the new key: **44 of 44 byte-identical, zero drift.** The full
267-row baseline re-keyed the same way showed exactly the four `changed` / two `retired` rows
E-53's own declared exceptions already name, and nothing else undeclared. So the repair changed
*what was checked*, not *what the checks found* — every number this repository has reported
under the old keying was correct; the guarantee behind it was 16% narrower than stated.

### The versioned-baseline scheme

`audit/pre-m11-observations.json` moves to `audit/baselines/v13-items7.json` — a `git mv`, not a
copy, so the file's history is preserved — with a new `audit/BASELINES.md` naming the generation,
the criterion it was produced under, and the commit it was frozen at.

**Why now, and why this is the right trigger rather than a convenient one.** ADR-062 stated its
own limit explicitly: *"A second declared-exception file arriving for an unrelated change would
be the signal that label semantics are churning rather than being corrected once — at which
point the right move is a versioned baseline per criterion rather than an accumulating exception
list."* The arity redesign is that second file — its Decisions A and B will restructure Core §4
item 1 and item 6, an interface change with nothing to do with E-53's observed/inferred
criterion. Adding a second exception file for it, alongside `e53-label-changes.json`, would be
exactly the churn ADR-062 named. A versioned baseline is the alternative it already specified.

**What a versioned baseline means for a reader, concretely — see `audit/BASELINES.md`'s own
statement, restated here because it is the operative content of this ADR.** A generation is
never edited in place. A claim stated against `v13-items7` — "flagship and contrast differ on
all seven items" — is checkable forever under exactly that criterion, at any commit that still
carries the file, by running the gate against it. It is *not* comparable against a later
generation's run; the generation label is what makes that mistake visible rather than silent,
on the same principle ADR-061's `superseded_label()` already established for a changed criterion.

The observation-count invariant becomes **per generation** rather than global: each generation's
own row count is its reference point, and "current minus baseline" is only meaningful within one
generation. Comparing today's run's total against `v13-items7`'s 267 and calling the gap
"drift" would be exactly the error a versioned scheme exists to prevent.

### Alternatives rejected

*Fix the keying, keep one exception file, add E-60's fix to it.* Rejected: E-60 is not a label
semantics change, it is a bug in the comparison mechanism itself. Filing it as a declared
exception would misrepresent what happened — nothing about any observation's *meaning* changed,
the *comparison* was wrong — and ADR-062's declared-exception machinery exists specifically for
meaning changes.

*Re-baseline at the current commit without checking the 44 first.* Rejected, and this was the
most important call in this ADR: freezing a new baseline without first verifying the previously
-shadowed rows would mean trusting the repaired keying on faith at the exact moment its own
repair is what makes trust checkable. The verification runs *before* the freeze in this ADR's
own ordering for that reason.

*Leave `audit/pre-m11-observations.json`'s name unchanged, only move directories.* Rejected:
the old name asserted "the M11 baseline," singular, which stops being true the moment a second
generation exists. `v13-items7` names the criterion, which is what a reader needs to know to use
it correctly, and what the old name never stated.

### What would change this decision

A `(test, name)` collision inside a future full-suite run — the same test recording the same
observation name twice — would mean this key is not sufficient either, and the gate is written
to fail loudly rather than silently in that case specifically so the next repair has the same
evidence this one did.

---

## ADR-070 — Arity redesign Stage 1: Decisions C, D and E land on wrapper classes, not on `InstantiationDeclaration` — a correction of the brief's own prediction

**Status.** Accepted **Gap.** none — declares how three already-decided repairs (E-30, E-40,
E-44/E-52) and one deferred wiring (ADR-068) are placed. **Track.** arity-redesign Stage 1.
**Pins.** `src/omi/interface.py` (`ScopeDeclaration`); `src/omi/proposed/decision.py`
(`SymmetryGroupAction`, `DecisionExtendedDeclaration.scope` /
`.symmetry_group_actions`); `src/omi/proposed/constitutive.py` (`ConstitutiveForm.refines` /
`.refinement_note`); `src/omi/conformance.py` (`ConformanceInputs.error_control_claim`,
`ConformanceReport.error_control_claim`); `src/omi_domains/sdl/interface.py` (`SDL_DECLARATION`
populated); `tests/test_arity_stage1_additive.py`.

### The correction, stated first because it changes what the rest of this ADR has to justify

`docs/ARITY-REDESIGN-BRIEF.md` §7's staging table predicted: *"Decisions C, D, E: new items, no
charter changes. `diff` gains keys; no existing key's value moves"* — i.e., that Stage 1 would
add fields directly to `InstantiationDeclaration`, so `omi.interface.diff()`'s output dict would
grow new entries (all `False`, since no domain populates them differently yet) without disturbing
the seven existing ones.

**That is not what was built, and the deviation was a deliberate design decision made during
implementation, not an oversight.** All three additive pieces instead land on wrapper classes:

- `ScopeDeclaration` (Decision C) is a new field on `DecisionExtendedDeclaration`, not on
  `InstantiationDeclaration`.
- `SymmetryGroupAction` (Decision E) is likewise a `DecisionExtendedDeclaration` field
  (`symmetry_group_actions`).
- `ConstitutiveForm.refines` / `.refinement_note` (Decision D) are fields on the *form* object
  already carried inside `ExtendedDeclaration.constitutive_forms` — a tuple element's shape
  changed, not the seven-item carrier.

**Consequence: `omi.interface.diff()` is untouched — not "gains keys that are all `False`",
literally unchanged, same nine keys it has always returned.** Every one of the nine `diff`-dict
observations `tests/test_interface_diff.py` and `tests/test_sdl_declaration.py` record is
identical after this stage to before it. Where the brief predicted Stage 1 would be "where the
versioned baseline is *written* rather than an exception declared" because appended keys would
move every diff-dict observation — that trigger did not fire, because nothing about `diff()`'s
own field list moved. (The versioned baseline was adopted anyway, in ADR-069, for the unrelated
E-60 keying repair; Stage 1 inherits it but did not need to invoke it a second time.)

### Why wrapper placement, not the brief's predicted direct placement

1. **ADR-042's precedent already answered this question once.** `ExtendedDeclaration` and
   `DecisionExtendedDeclaration` exist specifically so a proposed extension's fields do not touch
   `InstantiationDeclaration` — "composition, not modification" is that ADR's own name for the
   mechanism. C, D and E are exactly the kind of proposed, unissued content that pattern was built
   for; routing them around it would have meant maintaining two different answers to "how does a
   proposed field get added" inside one milestone.

2. **The seven items are Core §4's literal carrier, and Core is claims, not procedure (CLAUDE.md
   §1).** A scope-exit criterion, a symmetry-group declaration, and a lineage note between two
   constitutive forms are not among Core §4's seven named items — E-44 and E-52 say so explicitly
   ("no item at all, not even a weak one"; "none of the seven items hosts the criterion"). Adding
   them as an eighth, ninth and tenth field to `InstantiationDeclaration` would have made this
   repository's implementation assert a Core §4 extension that Core §4 itself does not state E-52's
   *proposed* wording does say "add an eighth item" — but that is a proposal for the next issued
   specification, not licence for this repository's code to pre-empt it by editing the literal
   carrier Core §4 defines today. Composing around it, the way `ExtendedDeclaration` already does
   for item 6d, keeps the distinction between "what v1.3 declares" and "what this repository
   proposes adding" visible in the type structure rather than only in prose.

3. **Zero risk to the nine `diff`-dict baseline observations, as a consequence rather than a goal.**
   Not the reason for the choice — (1) and (2) are — but it is the outcome the brief predicted
   would cost a baseline rewrite, and this design pays nothing for it.

### What this does and does not settle for Stage 2

**This precedent does not extend to Decisions A and B.** A re-charters Core §4 item 1's contents
and B splits item 6; both are stated *changes to what the seven items themselves mean*, which is
a different kind of edit from adding a field beside them — A and B cannot be done by wrapping,
because the thing being changed is the wrapped object itself. Nothing in this ADR should be read
as evidence that Stage 2 can also avoid touching `InstantiationDeclaration` or `diff()`; §7's
staging table's premise that A and B require the interface change stands unchanged. This ADR
corrects Stage 1's *mechanism*, not Stage 2's.

### The four pieces of Stage 1, briefly (full detail in the pinned modules' docstrings)

- **`ScopeDeclaration`** (E-44, E-52): four scope-feature justification strings plus a
  `scope_exit_criterion`, with `evidenced_features()` / `undeclared_features()` reporting which of
  Core §1.1's features a domain's declaration evidences. Empty is a meaningful value throughout
  (E-52's own wording: undeclared exit criterion is a claim of unlimited validity, not a missing
  one).
- **`SymmetryGroupAction`** (E-30, Decision E, deliberately half-closed): a domain can now name a group and the
  components it acts on. `omi.state.Metric` is unchanged — this closes only "declare the group",
  not "make the metric quotient by it"; the second half is out of scope for an additive stage
  because it would change `Metric`'s own computation.
- **`ConstitutiveForm.refines` / `.refinement_note`** (E-40, Decision D): `KOCKS_MECKING_STRAIN_WINDOWED` now
  structurally declares `refines=KOCKS_MECKING.name` — the actual worked case E-40 documents,
  exercised rather than only described in prose.
- **`error_control_claim` on `ConformanceInputs` / `ConformanceReport`** (ADR-068's deferred half,
  now Decision C's per the brief): carried through `generate_report()` unmodified. **Deliberately
  not wired into `_LEVEL_REQUIREMENTS`** — whether condition (a)'s claimability should gate an
  OMI-0/1/2 level is a restructuring question (it would be a new item in the level table, which is
  what the brief's own §6 caveat on `test_conformance.py` names), not this stage's. Confirmed by
  `tests/test_arity_stage1_additive.py`: `highest_claimable_level()` and every `RequirementStatus`
  are byte-identical with and without a supplied `error_control_claim`.

  **This closes a second predicted cost as well as the `diff` one.** The brief's §6 table flagged
  `test_conformance.py`'s 9 tests as moving from mechanical to logic *"unless [this stage] adds an
  item to the OMI level table."* It did not; the field is carried, not gated. So that file's 9
  tests remain mechanical for this stage, contrary to the brief's conditional prediction — a second
  place where implementation diverged from the plan's stated cost, in the direction of less cost
  rather than more.

### SDL's declaration, the fourth site

`SDL_DECLARATION` is the only decision-extension declaration built so far, so it is Stage 1's one
occupied test bed for `scope`: all four scope features are evidenced (`decision_kind` names the
campaign decision directly; `z`'s two components are documented in `state.py` as unresolved by any
declared modality — the strongest case among the three domains) and a scope-exit criterion is
declared against the existing `attainable_region` bound. `symmetry_group_actions` is declared
empty with a stated reason: no built domain declares an orientation-like field.

### Alternatives rejected

*Follow the brief literally: add the three fields to `InstantiationDeclaration`.* Rejected for the
reasons in the "why wrapper placement" section above — it would have contradicted ADR-042's own
established pattern and asserted a Core §4 extension the framework has not issued.

*Wire `error_control_claim` into `_LEVEL_REQUIREMENTS` now, since the field already exists.*
Rejected: gating a level is exactly the kind of "what OMI-0/1/2 certify" change ADR-068 named as
belonging to the restructuring decisions, and doing it quietly inside an "additive" stage would
misrepresent the stage boundary the user authorised.

### What would change this decision

If Stage 2's restructuring later needs to promote any of `ScopeDeclaration`,
`SymmetryGroupAction`, or the `refines` lineage onto `InstantiationDeclaration` itself — e.g.
because a future issued specification actually adopts E-52's proposed eighth item — that
promotion is Stage 2 or Stage 3's decision to make explicitly, with its own baseline
consequences, not a silent consequence of this ADR.

---

## ADR-071 — Arity redesign Stage 2: Core §4 item 1 is **split** into 1a and 1b, and the parameter role is declared under 1b rather than on a wrapper

**Status.** Accepted **Gap.** none — implements `docs/V1.4-EDITS.md` E-46's proposed wording,
which is written out in full there. **Track.** arity-redesign Stage 2.
**Pins.** `src/omi/interface.py` (`ParameterRole`, `InstantiationDeclaration.declared_parameters`
and its `__post_init__`, `INTERFACE_ITEMS`, `CORE_7_2_ROWS`, the three derivation helpers);
`tests/test_interface_diff.py` (rebuilt); `tests/test_sketches.py`; all three domain declarations
and all four sketches.

### A note on letters, so the record stays legible

`docs/ARITY-REDESIGN-BRIEF.md` §0 labels the **item-1 split as Decision A** and **item 6's split
as Decision B**. The authorisation for this stage used "B" for the item-1 split and "A" for the
parameter role carried inside it. What was built is unambiguous and is what this ADR records:
**item 1 split into 1a/1b, with the parameter role declared under 1b; item 6 untouched.** Item 6's
split (E-32/ADR-046's role-scoping) is *not* part of Stage 2 — ADR-046 already records that the
constitutive-form category is carried outside the item list by `ExtendedDeclaration`, and nothing
here changes item 6's two roles or its two categories.

### The decision, and why the parameter role is *inside* the split rather than beside it

Two options were live, and Stage 1 had just established a precedent for the one not taken.

**(a) `ParameterRole` under the split item 1b — chosen.** Item 1 becomes 1a (state schema) and 1b
(declared parameters) on `InstantiationDeclaration` itself.

**(b) `ParameterRole` on a wrapper**, the way ADR-070 placed `ScopeDeclaration`,
`SymmetryGroupAction` and `ConstitutiveForm.refines` — leaving item 1 as issued. *Rejected.*

**The argument that decides it is that (b) would leave a parameter declarable in two places at
once, which is the ambiguity the split exists to remove.** E-46's finding is not "there is nowhere
to declare a parameter" — a wrapper answers that. It is that item 1's charter covers two
categorically different declarations and *distinguishes them nowhere*, so a domain could put its
parameterisation in either place and `omi.interface.diff` would report two identical domains as
different. A wrapper reproduces exactly that: item 1's charter would still stretch over both
readings, and a domain could declare a parameter as a slot occupant or on the wrapper, with
nothing preferring either. E-46's own text anticipates this — "appending cannot surface a
mis-typing inside an existing item; only re-chartering can."

E-46's four-property table is the authority for *which* side a quantity falls on, and it is a
table about the quantity, not about the carrier: `c̄` answers **which member of the operator family
this is**, not **what the state of this body is**. The split is that distinction made structural.

**Stage 1's wrapper precedent does not extend here, and ADR-070 said so in advance.** ADR-070's
"what this does and does not settle" section states that its precedent "does not extend to
Decisions A and B... because the thing being changed is the wrapped object itself." That held.

### What this costs, stated rather than discovered later

**1. `InstantiationDeclaration` is no longer a literal v1.3 seven-item object.** ADR-042's
composition-over-modification invariant is deliberately broken for item 1 — the first time in this
repository. Consequences, all accepted:

- `SpecificationVersion.V1_3` now names v1.3's **level table** (Spec §9.1's rows, unchanged) rather
  than v1.3's item list. A `ConformanceReport` stamped `V1_3` is still a true claim about which
  requirements were met; it is no longer a claim that the declaration behind it has v1.3's shape.
  **No new enum member was added**, deliberately: the level table is what the version stamps, and
  minting `PROPOSED_ITEM_SPLIT` would imply the extensions' composition discipline was preserved
  here when it was not.
- `ExtendedDeclaration.v13_core` and `DecisionExtendedDeclaration` still wrap whatever the item
  declaration is, so their projection property is unaffected — but the field's *name* now overstates
  what it holds, and its docstring says so rather than being renamed (renaming would churn three
  domains and every test for a cosmetic gain).

**2. Decision A ceases to be independently revertible**, which the authorisation accepted
explicitly and which is correct on its own terms: a parameter role without a charter distinguishing
state from index is the under-declaration E-29 reported, so the two were never separately useful.

**3. The audit baseline moves to a new generation.** `diff()` gains a `declared_parameters` key, so
the nine `diff`-dict observations move by construction. Under ADR-069's versioned scheme this needs
no declared exception: `audit/baselines/v13-items7.json` stays valid and audited forever as the
v1.3-criterion generation, and `audit/baselines/redesign-items8.json` is frozen at this commit.

**4. `diff_result` is retired with no replacement**, and this is the retirement ADR-062's guard
would have blocked. It recorded the raw `diff()` dict under two tests, one of which pinned ADR-034's
seven-rows-onto-six mapping — a claim that is now *computed* from the item list rather than written
down, so there is no hand-written assertion left for an observation to pin. The comparison ceased
to exist rather than moved. `docs/ARITY-REDESIGN-BRIEF.md` §2 identified this in advance as the one
claim that could not be honestly retired, and the versioned-baseline scheme dissolves it exactly as
that section predicted: nothing is deleted, because the observation remains audited in the
generation whose criterion it was true under.

### What was built

- **`ParameterRole`** — `name`, `indexes` (required non-empty: a parameter indexing nothing
  parameterises nothing, and naming the operators is the declaration's falsifiable half),
  `justification` (required, against E-46's four-property test), plus `constant_over`,
  `descriptor_basis`/`underlying_space` (ADR-052's rule travels with the quantity) and
  `also_state_in_regions`.
- **The mutual-exclusion check** in `InstantiationDeclaration.__post_init__`, which is what makes
  the split remove an ambiguity rather than relocate it: a name in both items 1a and 1b is refused
  unless `also_state_in_regions` declares the dual role, per E-46's carbon-in-a-decarburising-layer
  clause. Exercised on constructed declarations in `tests/`, not by contorting a domain.
- **`INTERFACE_ITEMS`, `CORE_7_2_ROWS`** and three derivation helpers — the item list as data, so
  the numbering, the charters and the §7.2 mapping have one authority. This is E-01 converted from a
  presentation defect into a standing check, and it reported the new count on its first run without
  being asked.
- **`declared_parameters` required with no default**, on ADR-042's reasoning for
  `specification_version`: a default would let a domain that *has* an index silently declare none,
  which is the omission E-46 found item 1 unable to surface. `()` is a positive claim.

### The domain declarations, and the finding in them

| declaration | item 1b | note |
|---|---|---|
| `flagship` | **empty** | The domain E-29 was written about, and the only empty 1b anywhere. Its three de-facto-static components stay in 1a; repairing that is out of scope per E-29 itself |
| `contrast` | `cell_design` | Newly declarable: a graphite cell and a lithium-metal cell under one usage programme were previously indistinguishable declarations |
| `sdl` | `mean_composition` | **Relocated** from the decision extension's `INVARIANT`-coupled `CoupledQuantityDeclaration`, not duplicated — two homes is the ambiguity the split removes. `MEAN_COMPOSITION` removed for the same reason |
| four sketches | all fill | Verdicts re-derived per CLAUDE.md invariant 11; see `docs/SKETCHES.md` |

**The finding: item 1b's polarity inverts item 3's.** On erasure inventory the flagship is rich and
the contrast empty — Core §7.2's headline inversion. On item 1b the contrast declares and the
flagship does not. The domain with the strongest claim to needing the item is the one whose
declaration leaves it empty, because its parameters are mis-typed into 1a. Pinned by
`test_item_1b_inverts_the_two_domains_in_the_opposite_direction_to_item_3`.

### What filling item 1b discovered: E-61

Declaring `mean_composition` on the discovery domain produced a quantity that is **legitimately
item-1b content per chain and item-2 content per campaign** — the acquisition policy's decision
variable and the chain's fixed index are the same thing, and Core §4 states no scope at which a
declaration is written. Filed as **E-61** in `docs/V1.4-EDITS.md` before deciding how the code
would cope, per CLAUDE.md §10. The code copes by recording the scope in free text and nothing more:
inventing a `scope` field would improvise across a framework gap (CLAUDE.md §4), and the ledger
entry carries the proposed wording instead. **The mutual-exclusion check deliberately does not
extend to 1b-versus-2**, because unlike 1a-versus-1b the dual membership there is legitimate.

### Alternatives rejected

*Wrapper placement (option b).* Above — it preserves the ambiguity the split exists to remove.

*Append an item 8 "operator parameterisation", leaving item 1 whole.* Rejected on E-46's own
argument: item 1's charter would still cover both things, so the mis-typing would remain
undetectable and the new item would merely add a second legal home.

*A fifth state slot.* Rejected by E-29's own reasoning, quoted in `ParameterRole`'s docstring: a
slot subjects a parameter to pushforward, Axiom S, erasure and assimilation, all vacuous for a
quantity nothing transports.

*Add a `declared_parameters_structural` companion key to `diff()`,* mirroring
`invariants_structural`. Rejected: ADR-034 added that key because it had a *measurement* — two
domains declaring one invariant structure under different names. No equivalent measurement exists
for parameters, so the key would assert which parameter declarations count as structurally alike on
no evidence.

*Split item 6 in the same commit.* Out of scope, and ADR-046 already settled where constitutive
forms live. Bundling it would have produced one diff in which a real movement and a deliberate one
are indistinguishable — the failure the audit gate exists to prevent.

### Is eight stable? **No — and three pressures now sit on the wrong side of this decision**

Stated because the question was asked directly before Stage 3, and the answer is a finding about
this repository's own consistency rather than only a forecast.

**The count does not move for E-31.** Its proposed wording *replaces item 1's parenthetical* — the
characterisation method that fixes the `m`/`z` boundary is content **inside** item 1a, not a new
item. Filling it would enrich 1a and leave the count at eight.

**The count moves for three others, by their own proposed wording:**

| pressure | its proposed wording asks for | where this repository puts it today |
|---|---|---|
| E-30 (symmetry group) | "Add a **new declaration item** — deliberately not a sub-item of item 6" | `DecisionExtendedDeclaration.symmetry_group_actions` (wrapper, ADR-070) |
| E-32 / ADR-046 (constitutive form) | ADR-046 chose "(b) a **new interface item**", noting it "makes the interface eight items" | `ExtendedDeclaration.constitutive_forms` (wrapper, ADR-042/ADR-043) |
| E-52 (scope-exit criterion) | "Add an **eighth item** to Core §4: 8. Scope-exit criterion" | `ScopeDeclaration.scope_exit_criterion` on the decision extension (wrapper, ADR-070) |

If all three land as framework items on top of this split, the interface is **eleven** items, not
eight. So eight is a waypoint, not a resting point, and any document or test that treats it as
settled is wrong in the same way a hardcoded "seven" was — which is why `INTERFACE_ITEMS` exists and
why CLAUDE.md §5 invariant 11 now forbids writing the count as a literal.

**The inconsistency this exposes, stated plainly.** This repository now holds three declarations on
wrapper classes whose own ledger entries propose them as *items*, and one declaration (the parameter
role) as an item on the reasoning that a wrapper would leave it declarable in two places. Those two
treatments cannot both be right in general. The distinguishing argument is available and is the one
this ADR rests on: **a wrapper is safe where the content has no competing home in the item list, and
unsafe where it does.** Item 1's charter already stretched over the parameter — that is E-46's whole
finding — so a wrapper created a second legal home. Nothing in items 1a–7 stretches over a symmetry
group, a constitutive form (item 6 *refuses* one by name, per E-32) or a scope-exit criterion (E-52
checks all seven and finds no host), so no wrapper for those creates an ambiguity.

That argument is coherent, but it is a *repository* argument and the framework does not make it. If
the next issued specification adopts E-30, E-32 and E-52 as items while leaving item 1 whole, this
repository will have split the one item the framework kept and wrapped the three it promoted —
exactly inverted. **Flagged here rather than resolved, because resolving it means deciding what the
next specification does, which is not this repository's call.**

### What would change this decision

If the next issued specification declines E-46's split and keeps seven items, this repository's
carrier diverges from the issued interface on item 1, and the honest response is to move
`ParameterRole` back onto a wrapper and re-open the ambiguity as a *stated* framework gap rather
than a silently-repaired one. That reversal is what the `v13-items7` baseline generation exists to
make checkable: the pre-split comparability results remain verifiable under their own criterion.

---

## Open questions

Not decisions — hypotheses the code should settle. Full statements in
`COVERAGE.md` Part IV. Record outcomes here when resolved.

| id | Question | Milestone | Status |
|---|---|---|---|
| OQ-1 | Fingerprint: single probe or contrast between probes? | M4 | answered — see COVERAGE.md Part IV |
| OQ-2 | Erasure completeness: operator-level or component-level? | M2, deferred half at Phase 3.4 | answered — see COVERAGE.md Part IV |
| OQ-3 | Class B under competing defect populations | M6 | answered — see COVERAGE.md Part IV |
| OQ-4 | Does inverse design report which variance is binding? | M9 | answered — see COVERAGE.md Part IV |
| OQ-5 | Metric dependence of reported `L` | M2 | answered — see COVERAGE.md Part IV |

When one resolves: record the evidence, update `COVERAGE.md`, and if it implies
a framework edit, state the proposed wording so it can be carried to v1.4.
