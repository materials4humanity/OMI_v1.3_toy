# M11 — The constitutive-form track: a refuted claim and three findings worth more

**Snapshot.** Generated at HEAD `eb809ff`, closing M11. The measured figures come
from `scripts/run_m11_4_extrapolation.py` and `scripts/run_m11_5_extrapolation.py`,
both reproducible unchanged at that commit; the underlying documents are
`docs/M11.4-PREREGISTRATION.md`, `docs/M11.4-EXTRAPOLATION.md`,
`docs/M11.5-PREREGISTRATION.md`, `docs/M11.5-EXTRAPOLATION.md`. Per CLAUDE.md §10
this is a point-in-time computed record: corrected by dated addendum below the
passage it corrects, never by rewriting the original text.

---

## 0. The headline

M11 built the interface extension that `docs/PHYSICS-ADEQUACY.md` §3.4 argued for —
a way for a domain to declare *"this operator follows Kocks–Mecking, valid over this
range"* — and then ran the experiment that document proposed and could not run:
hold out a region of control space entirely and see whether declared constitutive
structure buys extrapolation reach.

**It does not, as the claim was stated. The claim is refuted.** On a hold-out gated
in advance for its ability to discriminate, with thresholds registered in a prior
commit, every declared-form contestant scored *worse* than a free-form operator, and
an unchanged tabular baseline beat all of them.

**Three findings outrank that headline**, and they are the reason the milestone is
worth its cost:

1. **The asymmetry.** A missing *dependence* costs almost nothing; a missing
   *mechanism* is catastrophic — a gap of **+61.98** against a declared minimum
   effect of 0.63. Declaring a form whose mechanism set is incomplete is far worse
   than declaring no form at all. This is the practically actionable result.
2. **Error cancellation (E-42).** The declared forms did not lose through ignorance
   of their own physics. The correct form was **exact** against a truth with the
   withheld term removed and finished fourth of six; the winner was fourth on that
   measure and first on the criterion, its −7.49 bias nearly annihilating the
   withheld term's −6.56. Spec §9.3's criterion rewards being wrong in the right
   direction, and cannot tell that from being right.
3. **The axis precondition (E-41).** A hold-out satisfying every requirement Spec
   §9.3 states can be incapable of discriminating between the models compared. The
   first attempt at this experiment was exactly that, and the fix is a precondition
   the Spec does not contain — and which E-39's own proposed wording for it turned
   out not to express.

The framework contribution of M11 is therefore not "declared forms work" or "declared
forms do not work". It is: **the experiment that would decide it is harder to design
than Spec §9.3 admits, the criterion it prescribes is not measuring what it is taken
to measure, and completeness of the mechanism set — not the presence of a declaration
— is what governs the outcome.**

---

## 1. The claim as pre-registered

`docs/PHYSICS-ADEQUACY.md` §3.4, verified at M10.4 and filed as `V1.4-EDITS.md`
**E-32**, argued that Spec §2.2's five hard-constraint categories are all generic
mathematics and none is a domain constitutive law — and that reach outside the
training envelope comes precisely from constitutive structure, because the *shape* is
right where data is absent. It proposed a sixth category and named the experiment
that would test it. Its own verification block closed with: *"Not established: that
adding the category would deliver the reach it is argued to deliver."*

M11 built the category (M11.1–M11.3, ADR-042/043/046) and ran the test.

**ADR-045 fixed the design before any code.** Four contestants against a generator
withholding one named term:

| | Contestant | Declared form? |
|---|---|---|
| 1 | Free-form operator, generic constraints only — the v1.3 incumbent | no |
| 2 | Correct form, parameters fitted — **ceiling arm, explicitly not the claim** | yes |
| 3a | Missing *mechanism* | yes |
| 3b | Missing *dependence* | yes |
| 4 | Tabular baselines from `omi.baseline`, unchanged | no |

**The claim is `gap(3, 1)` and `gap(3, 4)`**: does canonically-right-locally-wrong
declared physics beat a free-form operator and a tabular baseline outside the
envelope? Contestant 2 is a calibration ceiling and carries a standing caveat against
being reported as the headline — a correct form with fitted parameters is a very
strong prior and its win would be close to structural.

Thresholds via ADR-041's `decision_sensitive_threshold`, with costs declared **against
the party wanting the positive finding**: a false alarm is three times as costly as a
miss, because a false alarm is what puts an unsupported claim into a paper. The ratio
raises τ and makes a positive result harder to obtain.

ADR-045 also fixed what a negative means: *"The negative result is a deliverable, and
it terminates the experiment."*

---

## 2. M11.4 — the vacuous axis, and how it was diagnosed

**Generator A** was Kocks–Mecking plus one withheld term: a strain-rate drag
contribution, identically zero below the declared window's upper edge and growing
above it. The hold-out was the strain-rate axis, `[20, 200]` against a declared window
of `[10⁻³, 10]` — extrapolation factor median 11.9, max 38.3, grouped and never
random. Thresholds were registered at `bd44bb6`, in a commit containing no sweep code.

**Every requirement Spec §9.3 states was met.** The result:

| Comparison | gap | τ | verdict |
|---|---|---|---|
| 1 − 3a | −0.211 | 0.389 | no effect |
| 1 − 3b | +0.104 | 0.367 | no effect |
| 1 − 2 (ceiling) | −0.018 | 0.352 | no effect |
| 1 − 4 Ridge / GBT | −0.010 / +0.059 | 0.352 / 0.353 | no effect |

Per ADR-045, Generator B was not run.

**The null was uninformative, and finding that out is what M11.4 delivered.** Every
contestant's held-out RMSE lay in `[7.21, 7.53]` — a spread of 0.31 — while the
withheld term's own magnitude over that region was 7.18. Every contestant's *entire*
held-out error was the withheld term. The diagnostic that settled it: scored against a
ground truth with the drag term removed, the **free-form** arm scored 0.077 and the
**correct declared form** 0.339.

The cause: **Kocks–Mecking has no strain-rate dependence.** Along the axis the
experiment varied, the declared form predicts a constant, and a free-form surface that
learned "output does not depend on rate" in-envelope reproduces that constant exactly.
Candidate and baseline agreed **by construction rather than by measurement**. No effect
size could have been detected.

That is `V1.4-EDITS.md` **E-39**: Spec §9.3 requires the held-out region to be a region
rather than scattered points, to be grouped, and to lie outside the envelope — and
never requires it to be a region where the models under comparison differ. A test can
satisfy the prescription in full and be vacuous.

**The second-order consequence, which is the part that reaches beyond this build.** A
null from a vacuous hold-out is indistinguishable from a null from a real absence of
effect. M11.4 separated them only by running a diagnostic against a *modified*
generator — available in a synthetic study, and not available on field data, where the
withheld physics is unknown by definition.

M11.4 also recorded a γ=4 rollout separation favouring declared forms as a
**pre-specified observation generating an untested hypothesis**, explicitly refusing to
apply thresholds registered for unit strain to a rollout gap seen afterwards. §4 below
reports what happened when it was tested properly.

---

## 3. M11.5 — the fair axis, gated before it was registered

ADR-045 gained a standing requirement: **before a hold-out is registered, show that the
declared-form candidate and the free-form baseline diverge along the held-out axis**,
measured in-envelope against a withheld-free truth. Implemented as
`omi.proposed.holdout.check_hold_out_discriminates`, domain-neutral, run before the
thresholds.

**The design.** Hold out **accumulated strain**, where Kocks–Mecking's storage/recovery
balance actually makes a prediction — saturation. Generator C withholds **dynamic
recrystallisation above a critical strain**, a term proportional to `ρ` and therefore
the same shape as the form's own recovery term, so a fitted declared form can *partly
absorb* it. Training `γ ∈ {0.25, 0.5, 0.75, 1.0}`, evaluation `γ ∈ {2, 3, 4, 6}`,
extrapolation factor 2.00 to 6.00. Strain rate and temperature drawn from identical
ranges on both sides, so accumulated strain is the only quantity withheld.

**Contestant 1 was re-specified, and ADR-047 records why that was obligatory rather
than optional.** M11.4's free-form arm extrapolated as `surface(q) × γ` — linear in
accumulated strain by construction, unable to saturate. On a strain hold-out that is a
straw man, and the declared form would have beaten it for a reason having nothing to do
with declared physics. Contestant 1 for M11.5 is a **free-form rate law, integrated** by
the same integrator at the same fixed step size, with non-negativity enforced in the
integrator rather than as a fitting penalty, fitted by the same optimiser with the same
tolerances. Its basis can represent a negative rate, so saturation is within its reach;
it is not given `√ρ`, which is the declared form's own content. Contestant 1's fairness
is defined *relative to the held-out axis*, and changing the axis obliges restating it.

### The gate refused the axis first — and the refusal was the finding

Implemented as E-39 literally proposes — disagreement measured against a declared
minimum effect — the check returned **VACUOUS on M11.5's axis** (0.353 against 0.656).
Rather than lower the bar, both axes were measured side by side under identical
discipline: fit in-envelope, probe at the fitted region's upper edge and again at the
envelope's, score against a withheld-free truth.

| | M11.4, strain rate (vacuous) | M11.5, accumulated strain |
|---|---|---|
| withheld-free truth's own variation along the axis | **0.00000** | 3.80564 |
| disagreement at fitted edge | 0.33865 | 0.03240 |
| disagreement at envelope edge | 0.35388 | 0.47193 |
| **divergence** | **1.045** | **14.567** |
| verdict | **INERT_AXIS** | **DISCRIMINATING** |

**The two far-point disagreements are the same order of magnitude.** No threshold on
"materially different predictions" admits the usable axis without also admitting the
vacuous one. E-39's proposed wording is not imprecise — it is **inoperable**. What
separates the two axes is whether the reference physics varies along the axis at all,
and whether the models *diverge* as the axis is pushed. An extrapolation test asks what
happens as you go further, so its precondition has to be about growth rather than
difference. `V1.4-EDITS.md` **E-41**, superseding E-39's wording; E-39's finding stands.

M11.4's axis fails **all three** implemented criteria independently — inert, parallel,
and adverse, the last meaning the correct declared form was the *worse* of the two at
the physics it does express (0.316 against 0.069). That is the retro-validation that
the gate discriminates rather than decorates
(`tests/test_holdout_discrimination.py`).

### The peek, and why it belongs here rather than in an appendix

**While building M11.5's machinery, a full held-out evaluation of all six contestants
was run in a scratch script before the thresholds existed.** That is a peek at the
pre-registered quantity. `docs/M11.5-PREREGISTRATION.md` §5 quotes every number that
was seen, in a table, in the pre-registration document itself — the document a reader
consults *before* the result.

Four things bound what it cost.

- **No design parameter changed in response.** The generator, the withheld term's
  strength, the strain sets, the control ranges, the contestants and their bases, and
  the campaign size are all as they were when that run was made.
- **Three things did change afterwards, none of them a response to a contestant's
  score.** The dry-run probe pair moved to the fitted region's edge on a stated
  principle; a numerical ceiling six orders of magnitude above any reachable value was
  added to the integrator after overflow warnings during the free-form fit; and the
  gate was rewritten for the reason in E-41. Because of the ceiling the sweep does not
  reproduce the peeked table exactly.
- **The direction cuts against the experimenter.** The peeked reading was *negative for
  declared forms* — free-form beating the correct declared form, a tabular baseline
  beating both. Pre-registration exists to stop an experimenter tuning a threshold
  until their preferred result clears it. A peek revealing a result contrary to the
  extension the repository is arguing for is not that failure mode.
- **The gate's first formulation was replaced after it refused this very axis**, which
  is the moment the discipline was actually under load. It was replaced by a different
  *measurement*, justified on principle before it was measured, and validated by
  refusing the axis it must refuse on all three criteria.

This is recorded in the narrative rather than in an appendix because **the disclosure
is the evidence**. A pre-registration that never records a deviation is either
describing work that had none or is not looking. What can be checked here is not that
the process was clean but that its deviations are enumerated, bounded, and pointed in
the direction that would embarrass the claim rather than flatter it.

---

## 4. The result, and the refutation

Criterion as registered: held-out RMSE **pooled** over all (query, strain) pairs at
`γ ∈ {2, 3, 4, 6}`. Thresholds imported from `97621ac`, not recomputed.

| Contestant | held-out RMSE | sd | declared form? |
|---|---|---|---|
| 4 tabular GBT | **3.26607** | 0.042 | no |
| 1 free-form rate law | **5.06181** | 0.097 | no |
| 3b missing dependence | 7.56449 | 0.733 | yes |
| 2 correct form (ceiling) | 8.10280 | 0.114 | yes |
| 4 tabular Ridge | 24.31240 | 0.382 | no |
| 3a missing mechanism | 69.54710 | 1.470 | yes |

| Comparison | gap | τ | verdict |
|---|---|---|---|
| **1 − 3a** | −64.485 | 0.331 | **WORSE** |
| **1 − 3b** | −2.503 | 0.322 | **WORSE** |
| 1 − 2 (ceiling) | −3.041 | 0.315 | WORSE |
| 1 − 4 Ridge | −19.251 | 0.316 | WORSE |
| 1 − 4 GBT | +1.796 | 0.317 | EFFECT, **for the baseline** |

**The claim is refuted.** `gap(3, 1)` and `gap(3, 4)` are not merely unsupported; they
are negative by margins one to two hundred times the registered threshold. The single
comparison that clears its threshold clears it in the tabular baseline's favour.

**The ceiling did not hold either.** Contestant 2 recovers the generator's parameters
exactly — `k₁ = 8.000`, `k₂₀ = 2.000`, `p = 1.500` — because the training region is
noiseless and the generator is exactly this form there. Its held-out error is therefore
the pure, irreducible cost of not knowing the withheld term, with no parameter
estimation mixed in. That ceiling is **8.10**, and two contestants carrying no declared
form at all are below it.

**Per-strain curves** (CLAUDE.md invariant 7; reported, not the registered criterion):
the ordering is stable across the whole held-out range, so the pooled figure hides no
crossover. Two shapes are worth naming — 3a's error grows without bound
(11.5 → 30.4 → 56.2 → **123.0**), the signature of a model that cannot saturate; GBT's
is flat and non-monotone (3.97 → 3.45 → 1.80 → 3.43), the signature of a model that is
not extrapolating at all.

**M11.4's untested hypothesis is now tested and refuted.** Against a free-form
contestant that is an operator rather than a scaled surface, the γ=4 separation
**reverses**: free-form 4.68 against the correct form's 8.22. The M11.4 observation was
an artefact of that baseline's extrapolation rule, as ADR-047 suspected it might be.
Recording it as untested was correct; it is now tested, and it does not survive.

### What the refutation does and does not license

It licenses: *declared constitutive forms, as this repository implemented the proposed
category and as Spec §9.3 prescribes measuring them, buy no extrapolation reach on this
axis and cost a great deal.*

It does not license *declared physics buys no reach*. One generator, one axis, one
domain, and **no observation noise** — which removes the mechanism by which declared
forms are conventionally argued to help, parsimony under limited data. That omission
was deliberate (it isolates reach from parsimony and is the conservative choice for the
claim) and it is the obvious next experiment.

---

## 5. Finding one: the misspecification asymmetry

M11.4 could not separate the two arms (+0.315 against a minimum effect of 0.702). M11.5
separates them by **+61.98**, and the reading is unambiguous.

| Arm | held-out RMSE | vs the correct form (8.10) |
|---|---|---|
| 3b — missing *dependence*: temperature-dependent recovery treated as constant | **7.56** | **better** |
| 3a — missing *mechanism*: recovery term dropped | **69.55** | 8.6× worse |

**A missing dependence costs nothing, and here it helps.** 3b's fitted constant
`k₂ = 1.701` sits below the true average, and the resulting under-prediction cancels
roughly a quarter of the withheld term. Declaring a form you are only partly sure of,
where the doubt is about a parameter's functional dependence, is close to free.

**A missing mechanism is catastrophic.** 3a has no removal term at all, so nothing
balances storage, it cannot saturate, and its error diverges along the held-out axis to
123.0 at γ=6 — thirteen times the free-form baseline, twenty-one times the tabular one.

**Declaring a form with a mechanism missing is far worse than declaring no form at
all.** That is the most actionable result of the M11 track, and it is a warning rather
than an endorsement. The extension's value proposition is **asymmetric**: small upside
for parameter-level doubt, very large downside for structural doubt. And a practitioner
cannot reliably tell which kind of doubt they have — that is precisely the situation in
which a declared form is attractive.

The corrected claim the evidence supports is therefore not "constitutive structure buys
reach" but **"constitutive structure buys reach only when the declared mechanism set is
complete for the held-out regime, and an incomplete mechanism set is worse than no
declaration"**. `docs/PHYSICS-ADEQUACY.md` §3.4 is corrected accordingly.

---

## 6. Finding two: the criterion rewards error cancellation (E-42)

The declared forms are not losing because they are wrong about their own physics.
Scored against a truth with the withheld recrystallisation removed — *how well does each
contestant capture everything it could in principle know?* — **the ranking inverts three
places at both ends**.

| Contestant | vs full truth (the §9.3 criterion) | vs withheld-free truth | signed bias vs withheld-free |
|---|---|---|---|
| tabular GBT | **3.27 — 1st** | 8.52 — 4th | **−7.487** |
| free-form operator | 5.06 — 2nd | 3.78 — 2nd | −2.702 |
| 3b missing dependence | 7.56 — 3rd | 5.44 — 3rd | −1.553 |
| **2 correct form** | **8.10 — 4th** | **0.0000 — 1st** | **+0.000** |
| tabular Ridge | 24.31 — 5th | 17.09 — 5th | +13.342 |
| 3a missing mechanism | 69.55 — 6th | 63.14 — 6th | +48.810 |

The withheld term reduces the truth by a mean of **−6.564**. **The winner wins by being
wrong in the right direction**: its −7.49 bias against the physics it should have
learned nearly annihilates the withheld term, leaving a full-truth bias of −0.92. It is
7.49 wrong about the physics and 0.92 wrong about the answer. The correct declared
form's bias against the physics it expresses is *exactly zero*, so it pays the withheld
term's cost in full and finishes fourth.

This is `V1.4-EDITS.md` **E-42** against Spec §9.3's baseline-comparison paragraph:
forward accuracy against the full truth mixes two quantities that behave differently —
what a model gets wrong about the physics it *can* express, and the cost of the physics
nobody gave it — and they can cancel hard enough to invert the ranking.

**The sting is the same one E-39 identified, in the opposite direction.** The diagnostic
that resolves it needs a generator you can modify. On field data the withheld physics is
unknown by definition, so a win by cancellation and a win by understanding are
indistinguishable — and this is worse than the null case, because a null invites
scrutiny and a win does not.

**E-42 does not un-refute the claim.** The registered criterion was held-out RMSE, the
registered claim was that declared forms would beat free-form and tabular contestants on
it, and they did not. A finding about the criterion arriving after the fact cannot undo
a claim made under it. What it does is make the *next* experiment's criterion a live
question rather than a settled one.

---

## 7. Finding three: the axis precondition (E-41), and what it cost to find

Stated in §3 as it arose. Recorded here as a finding in its own right because it is the
one with the widest reach beyond this milestone:

**Spec §9.3's extrapolation prescription is satisfiable in full by a test that cannot
discriminate**, and the natural repair — requiring the models to make "materially
different predictions" — cannot be operationalised, because the vacuous axis and the
usable one exhibit the same order of absolute disagreement. The quantities that work
are the reference physics' own variation along the axis, and the *growth* of the
models' disagreement across it.

The cost of finding this was one entire milestone. M11.4 was designed carefully, ran
correctly, satisfied every stated requirement, and produced a number that meant
nothing. That is worth stating plainly for the paper: **the precondition is not
pedantry, it is the difference between an experiment and a ritual**, and a framework
that prescribes extrapolation testing without it will produce nulls that its own users
cannot interpret.

---

## 8. Two smaller findings, recorded for completeness

**E-40 — declarations cannot be refined.** M11.5 needed one further validity bound on a
form declared at M11.3: an accumulated-strain window above which recrystallisation
intervenes. The bound is true and was simply not declared. It cannot be added: a
declared range that is checked at all must require a value for every bound it declares,
so extending one breaks every existing caller. The workaround is a sibling form — at
which point Core §4 item 6's comparison sees two forms where the physics is one. The
interface has no notion of a declaration's lineage.

**E-38, from M11.3 and confirmed by M11.5's design discipline.** The validity report
caught a genuine modelling error on its first application to real physics —
Koistinen–Marburger applied at soak temperature, 5.71× outside its declared window —
with the correct action attached and no oracle involved. That remains the strongest
positive evidence the extension produced, and §9 below weighs it against the negative.

---

## 9. What M11 leaves the framework

**The extension is built and it is not vindicated.** The declaration machinery works:
it is declarable, checkable, composable across a chain, and it caught a real error
unaided. What it does not do is what E-32 argued it would — buy reach.

**The honest summary for a v1.4 paper**, in one paragraph: *a declared constitutive form
supplies a checkable statement of where a relationship was validated, and that statement
catches misapplication which no generic constraint would catch. It does not, on the
evidence here, improve extrapolation accuracy, and where the declared mechanism set is
incomplete for the held-out regime it degrades it severely. The property that governs
the outcome is completeness of the mechanism set, which the framework provides no way to
declare, assess, or even signal — and the criterion the Specification prescribes for
measuring reach cannot distinguish a model that knows the physics from one whose errors
happen to cancel.*

Six ledger entries came out of this track: **E-38** (confirmation), **E-39** (the
vacuity gap), **E-40** (no refinement path), **E-41** (E-39's wording corrected),
**E-42** (the criterion rewards cancellation), and the earlier **E-35** on
cross-version comparability. Five of the six are things the framework must change; one
is a proposal that worked. That ratio is the milestone's actual output, and under
CLAUDE.md §2 it is the intended one.

## 10. Limitations, stated rather than concealed

- **One generator, one axis, one domain.** ADR-045's Generator B was not run — correctly,
  under its own rule — and no cross-generator comparison was computed.
- **No observation noise**, which removes the parsimony mechanism by which declared
  forms are conventionally argued to help. Deliberate, isolating, and conservative for
  the claim; also the most obvious thing the next experiment should change.
- **Standard errors measured in-envelope**, which may understate held-out variability
  and makes τ tighter. Every declared-form verdict is WORSE by one to two hundred times
  τ, so no verdict is sensitive to it.
- **The gate is a dry run at shorter reach** (`γ = 1.0`) than the sweep (`γ = 6.0`).
- **The gate's criterion is validated on the two cases that motivated it.** A criterion
  tested against a third, unseen axis would be stronger evidence, and that is not done
  here.
- **The peek**, §3, quantified in `docs/M11.5-PREREGISTRATION.md` §5.
- **The toy is a toy.** `docs/PHYSICS-ADEQUACY.md` §1 already says flagship cannot
  settle whether OMI extrapolates in a real process. Nothing here changes that; what M11
  measured is a designed synthetic case where the answer is knowable by construction,
  which is the only place a claim about *measurement machinery* can be tested at all.
