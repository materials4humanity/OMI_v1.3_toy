# The composition milestone — design brief

**Live document** (CLAUDE.md §10). **A brief, not an execution.** Nothing here is implemented;
each stage's implementation is a separate authorisation, and each stage writes its own ADR before
its code (CLAUDE.md §4).

**What it is.** The v1.5 planning track produced seven composition decisions (ADR-049 – ADR-054,
plus ADR-071's item-1b placement), all recorded **design only**. This brief derives which are
already built, prices what is left, and stages it. The starting state was derived from the
repository rather than from any account of it — and that derivation changed four of the seven
answers.

**Standing constraints.** Core and Spec stay unedited. The interface stays at **eight items**
(ADR-073); any stage that needs a ninth **stops and reports** instead.

---

## 1. Derived starting state

| # | decision | ADR | status | evidence |
|---|---|---|---|---|
| 1 | `c(x) = c̄ + δc(x)` decomposition | ADR-050 | **absent** | No `c_bar`, `delta_c`, or composition-band component anywhere in `src/`. No schema carries one; `sdl/state.py` excludes composition deliberately |
| 2 | roles per species per region | ADR-051 | **implemented + tested** | `SpeciesRole`, `SpeciesRoleDeclaration`, `roles_for()`, `parameter_only_species()`; SDL declares promoter as `CONTROL` in bulk and `STATE` in surface layer, `tests/test_sdl_declaration.py` |
| 3 | descriptors as the metric over `c̄` | ADR-052 | **half — basis declared, metric absent** | `descriptor_basis` + `underlying_space` on both `ParameterRole` and `CoupledQuantityDeclaration`, with ADR-052's refusal enforced (descriptors without underlying space raise). But **no distance over descriptor space exists** — `omi.state.Metric` is over `𝒮`, not over `c̄` |
| 4 | `ParameterRole` under item 1b | ADR-071 | **implemented + tested** | Required field on `InstantiationDeclaration`, mutual-exclusion check, SDL populates it |
| 5 | declared-domain construction serving `ν` **and** `c̄` | ADR-049 | **serves `ν` only — and that is now correct** | `CoupledQuantityDeclaration`/`DeclaredDomainKind`/`CouplingDirection`/`TrackedDimensions` exist and serve `ν`. ADR-071 moved `c̄` to `ParameterRole`. See §2 |
| 6 | composition-dependent validity ranges | ADR-054 | **half — interval declared, mechanism absent** | `COMPOSITION_VALIDITY_INTERVAL` declares the second-order interval in SDL. But `ValidityBound.low/high` are scalar `BoundEdge`s, not functions over composition, and the refusal is **explicitly not implemented** — that module's own docstring says so |
| 7 | composition inverse as a third inverse problem | ADR-053 | **absent as an inverse; attainability substantially built** | `src/omi/inverse.py` contains **zero** composition references. But `AttainableRegion.report()` returns a verdict, the binding constraint and per-constraint factors, over four `AttainabilityVerdict` cases — exercised in `tests/test_sdl_declaration.py` |

### Two things the derivation found that were not in the brief for it

**(a) An unregistered implementation, and it is not the one anyone was looking for.**
`src/omi/proposed/item6.py` implements E-32's item-6 role-scoping in full — `InvariantSubItem`
(6a/6b/6c plus `CONSTITUTIVE_FORM`), `InvariantRole`, `certificate_eligible`,
`assert_certificate_eligible` — exported from `omi.proposed` and exercised by
`tests/oracles/test_known_envelope.py`. **ADR-073 recorded it as "decided and scheduled, not yet
implemented" three commits ago.** It was invisible because it appeared in **no `docs/COVERAGE.md`
row**, and neither did `ParameterRole`, `SpeciesRole`, `CoupledQuantityDeclaration`,
`AttainableRegion` or `COMPOSITION_VALIDITY_INTERVAL`. All are now registered under `C-4-prop`.

Worse than the bookkeeping: ADR-073's Half A proposed adding a third member to
`omi.interface.InvariantKind`, which would have **modified v1.3's classifier and destroyed the
measurement E-32 rests on** — that module's docstring states the refusal "is the evidence E-32 rests
on". ADR-073 is amended in place with both corrections.

**(b) ADR-053's stated blocker is discharged.** It declined to design the descriptor-attainability
certificate because "it needs a declared attainable region in descriptor space, **which no domain
currently supplies**". SDL has supplied one since ADR-060. What is still missing is narrower and
named in §4.

## 2. ADR-049 versus ADR-071 — reconciled in ADR-075, before any code

ADR-049 is titled "one object for `ν` and for `c̄`" and warns that "a parallel mechanism for `c̄`
would be an architectural error". ADR-071 built exactly that parallel mechanism. **ADR-075 settles
it: ADR-071 is right and ADR-049 is superseded on that claim only**, because E-46 — filed between
them — refutes ADR-049's premise with a four-property test showing `c̄` and `ν` are different kinds
of declarable thing. ADR-049's construction itself stands, unchanged, for `ν` and for `δc`.

**This is a prohibition on the implementation, not a note:** no stage may route `c̄` back through
`CoupledQuantityDeclaration`. That would re-create the second declaration site ADR-071 removed.

## 3. Nothing here moves the item count

Checked per decision, against `omi.interface.INTERFACE_ITEMS`:

| decision | lands on | item count |
|---|---|---|
| `c̄` | item **1b**, as a `ParameterRole` — already exists | +0 |
| `δc` | item **1a**, as `z`-slot schema components | +0 |
| species roles, declared domain | `DecisionExtendedDeclaration` (wrapper) | +0 |
| descriptor basis + metric | `ParameterRole` (1b) and a new metric object, which is not a declaration | +0 |
| composition-dependent validity | `ConstitutiveForm`, carried on `ExtendedDeclaration` (wrapper) | +0 |
| composition inverse + certificate | `omi/proposed/` — an inverse is not a declaration at all | +0 |

**Confirmed: none. The interface stays at eight.**

**One stop condition, and it is live.** `docs/V1.4-EDITS.md` **E-61** finds items 1b and 2 both
legitimately hosting one quantity at different declaration scopes — a *competing home*, which by
ADR-073's criterion is the one shape that justifies a new item. Composition is where E-61 was found
(SDL's `c̄` is a per-chain index and a per-campaign control). **If any stage finds itself needing to
resolve E-61 by adding an item, it stops and reports rather than adding it.**

## 4. The staged design

### Stage C1 — the decomposition, declared and made checkable

**Content.** `c̄` and `δc` declared on a domain, with ADR-050's constancy claim turned into a
measurement.

- **A new variant package** (ADR-075 Decision 2), not a retrofit — `flagship_composition/`,
  declaring `c̄` in item 1b and `δc` in `z`, so **no existing schema changes and no existing
  observation moves**.
- **The constancy check** is the falsifiable content, and it is the whole point of the stage:
  `c̄` is *constant along the chain by definition*, so a chain that moves it is mis-declared. The
  check measures `c̄` along a rollout and refuses beyond a declared tolerance.
- **The descriptor metric** (ADR-052's missing half): a distance over descriptor space, carrying its
  own declared normalisation, since CLAUDE.md invariant 1 applies to any distance. Needed by C3.
- **Oracle** (CLAUDE.md §7): a chain with `c̄` constant by construction and a sibling with a planted
  drift of known size — the check must separate them and recover the drift magnitude.

**Gate.** Full suite; `mypy --strict`; lints; audit gate against `redesign-items8` with **zero moved
observations** (additions only). If any pre-existing observation moves, the variant package has
touched something it should not have — stop and report.

### Stage C2 — composition-dependent validity, and the refusal ADR-054 asks for

**Content.** The mechanism behind the interval SDL already declares.

- `ValidityRange` gains a **second-order region over composition**: the range over which the
  first-order bounds are themselves claimed to hold.
- **The refusal**: a query inside a form's window but outside its composition region is **refused,
  not annotated with a factor** — ADR-054's rule, on the stated reasoning that annotating implies
  the range still means something. This is a behaviour change, not an addition.
- Worked case: `Ms` and Kocks–Mecking's `α` are not universal, which is ADR-054's own motivating
  example and lives in `flagship_constitutive`.

**Risk, and it is the reason this is its own stage.** The refusal changes `report()`'s behaviour on a
shared object used by `flagship_constitutive` and `sdl`. Validity and `worst_extrapolation`
observations **may move**. **The stage measures the movement before landing anything** and reports it;
if rows move, that is a third generation, decided explicitly rather than absorbed.

**Gate.** As C1, plus: the measured list of moved observations, with each either explained as intended
or investigated. No re-freeze without the report.

### Stage C3 — the composition inverse and its attainability certificate

**Content.** ADR-053's third inverse problem, now unblocked.

- **`AttainabilityCertificate`**, the analogue of `omi.inverse.ReachabilityCertificate`. What exists
  (`AttainableRegion.report()`) supplies the verdict, the binding constraint and the factors. What is
  **missing** is Core §5's other half — the **nearest attainable composition**, the analogue of
  `nearest_reachable_state`, which `omi.inverse` provides for the structure inverse and nothing
  provides for composition. That needs C1's descriptor metric, which is why it cannot come earlier.
- **The inverse itself**: target response → `c̄` in the descriptor basis, with the certificate on
  infeasibility. Placed in `omi/proposed/`, because Core §5's taxonomy names two inverses and has no
  competing home for a third — ADR-073's placement principle, applied.
- **Oracle**: a target whose descriptors are jointly unattainable by construction; the certificate
  must fire *exactly* outside, and name which of ADR-053's two grounds (descriptor attainability, or
  C2's validity region) bound.

**Gate.** As C1, plus the oracle above, plus an explicit statement of whether the certificate
discharges Core §5's output contract or only part of it.

### Which stage the composition inverse belongs in, and whether it needs the certificate

**C3, last, and the ordering is forced rather than chosen.** Two hard dependencies:

1. It needs `c̄` **declared** before `c̄` can be a decision variable — C1.
2. ADR-053's own certificate table names *two* infeasibility grounds, and the second is "the
   resulting chemistry leaves the declared mechanism set's validity region **(ADR-054)**" — which is
   C2. Building the inverse before C2 gives it a certificate that can only fire on half its grounds.

**Yes, it needs the certificate, and the certificate is now designable.** ADR-053 left it undesigned
for one stated reason — no declared attainable region — and SDL supplies one. The remaining gap is
the nearest-attainable-composition, not the verdict. **A composition inverse without the certificate
is the failure ADR-053 names in as many words**: "a composition inverse that ignores descriptor
attainability returns beautiful, unmeltable alloys."

## 5. Sequencing and what stays out

**C1 → C2 → C3**, gate between each, no stage begun without the previous stage's gate reported.

**Explicitly out of scope for all three:** Tier II and FE² coupling (CLAUDE.md §9); any chemistry
whose declaration would need a ninth item (stop and report instead); resolving E-61; the metric
quotient of OQ-6; and repairing `flagship`'s three de-facto-static components (E-29 part 2), which is
its own decision and would entangle two findings if done here.

**A note on what "chemistry" means in this milestone.** No claim is made that the declared forms,
descriptors or attainable regions are calibrated against real materials data. They are toy physics
with declared provenance, on the same footing as every other operator here (CLAUDE.md §2: the
operators are not the point). The measurement machinery around them is the deliverable.
