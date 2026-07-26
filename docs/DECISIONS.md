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

**Pinned by.** `tests/test_innovation_drift_monitor.py` (a planted drift
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

## Open questions

Not decisions — hypotheses the code should settle. Full statements in
`COVERAGE.md` Part IV. Record outcomes here when resolved.

| id | Question | Milestone | Status |
|---|---|---|---|
| OQ-1 | Fingerprint: single probe or contrast between probes? | M4 | answered — see COVERAGE.md Part IV |
| OQ-2 | Erasure completeness: operator-level or component-level? | M2 | partially answered — see COVERAGE.md Part IV |
| OQ-3 | Class B under competing defect populations | M6 | answered — see COVERAGE.md Part IV |
| OQ-4 | Does inverse design report which variance is binding? | M9 | open |
| OQ-5 | Metric dependence of reported `L` | M2 | answered — see COVERAGE.md Part IV |

When one resolves: record the evidence, update `COVERAGE.md`, and if it implies
a framework edit, state the proposed wording so it can be carried to v1.4.
