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

**Pinned by.** `tests/oracles/test_known_blind_spot.py` (a designed
unobservable direction must land in the unidentifiable/marginalisable or
dangerous cells, never "observed") and the domain triage tests
(`tests/test_domain_triage.py`).

---

## Open questions

Not decisions — hypotheses the code should settle. Full statements in
`COVERAGE.md` Part IV. Record outcomes here when resolved.

| id | Question | Milestone | Status |
|---|---|---|---|
| OQ-1 | Fingerprint: single probe or contrast between probes? | M4 | open |
| OQ-2 | Erasure completeness: operator-level or component-level? | M2 | partially answered — see COVERAGE.md Part IV |
| OQ-3 | Class B under competing defect populations | M6 | open |
| OQ-4 | Does inverse design report which variance is binding? | M9 | open |
| OQ-5 | Metric dependence of reported `L` | M2 | answered — see COVERAGE.md Part IV |

When one resolves: record the evidence, update `COVERAGE.md`, and if it implies
a framework edit, state the proposed wording so it can be carried to v1.4.
