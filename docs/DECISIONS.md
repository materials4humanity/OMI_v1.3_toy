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

**3. Composition, not modification.** `ProposedV14Declaration` **wraps** an
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
whose `specification_version` differs raises. `ProposedV14Declaration(...)
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

**What tests would pin it** (design). An oracle whose validated envelope is known
by construction, asserting the reported extrapolation factor equals the
constructed one — the same discipline as every `tests/oracles/` member. An
off-manifold test asserting the report *surfaces* rather than raises. A test
asserting `classify_invariant` still refuses a 6d member.

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
