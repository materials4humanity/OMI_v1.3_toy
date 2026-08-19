"""Declared constitutive forms: Core §4 item 6d and Spec §2.2's proposed sixth
hard-constraint category (proposed constitutive extension; ADR-043, docs/DECISIONS.md).

Cites Spec §2.2 (the five existing hard-constraint categories, none of which is
a domain constitutive form), Core §4 item 6 (role-scoped by
:mod:`omi.proposed.item6`), Core §5 (the control inverse an in-window violation
routes into) and Core §3.9 (why a constraint that carries shape outside the
training envelope is the only one of the categories that buys reach).
`docs/V1.4-EDITS.md` E-32 is the finding this module implements the proposal for.

**What the category is for, stated first because it is easy to mistake this for a
modelling convenience.** Of Spec §2.2's five categories, none carries the
*shape* of a response outside the envelope the training data occupy — they
constrain range, sum, monotonicity and balance, all of which hold everywhere and
none of which says what the response looks like where no data live. A declared
functional form does. That is the whole argument for the category, and it is why
the **validity range** rather than the form is the load-bearing field: a form
without a declared range makes an unbounded claim, which is worse than no form at
all.

**The report is the output the category exists to produce.** An operator
constrained to a declared form reports where the current evaluation sits relative
to the validated range, which is the mechanism for `docs/V1.4-EDITS.md` §10's
*buy physics* row — a row with no machinery in v1.3. See
:class:`ExtrapolationReport` for why the *binding space* is a first-class field:
the two spaces call for different interventions, and only one is actionable
inside the machinery this repository already has.

**What "typed, not free text" does and does not guarantee — the good-faith
residual, recorded rather than papered over.** A declared form carries an
evaluable callable and a :class:`FormKind`, so the framework can check that the
form *exists*, that it is evaluable, that its declared range is non-empty and
non-fabricated, and whether its output is a rate or a level. It **cannot** check
that the callable computes what the declared name says: nothing prevents a caller
from declaring a form under a canonical name and supplying an arbitrary
function. This is exactly the residual `docs/V1.4-EDITS.md` E-17 already names
for reachability certificates — `omi.inverse.ReachabilityCertificate` is typed as
the sound `Φ(s)=w·s` artefact, which stops a *forward-sampling result* being
passed off as a certificate, and still cannot stop a caller constructing one for
an invariant that does not hold. Typing raises the floor on what can be passed
off; it does not close the gap to good faith, and no type in this module claims
otherwise. The check that would close it is empirical, not structural — validating
the form against data in the regime it claims — which is Spec §4.6's ladder
discipline applied to a declared form, and is not proposed here.

No domain vocabulary appears here (CLAUDE.md §5 invariant 3): this module
supplies the category, and a domain supplies the forms that fill it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Mapping, Protocol, runtime_checkable

from omi.operators import Control
from omi.state import FloatArray, Slot, State


class ValiditySpace(Enum):
    """Which space a declared validity bound is expressed in (ADR-043).

    Both are required, and the distinction is not bookkeeping: it determines
    whether a violation is reachable by Core §5's control inverse. A form whose
    breakdown condition is a property of the state alone has no control-space
    expression at all — the same driving programme is inside or outside its
    validated regime depending on what the state already is — so a design
    admitting only control bounds cannot represent such a form.
    """

    CONTROL = "control"
    """A bound on the driving programme (`𝒰`, Core §3.2): the window of controls
    the form was fitted over. Leaving it is a control-inverse problem (Core §5)."""

    STATE = "state"
    """A bound on the state (`𝒮`, Core §3.1): the region of state space the form
    was fitted over. Leaving it is **not** recoverable by any admissible control
    — the form has run out of physics."""


class ValidityAction(Enum):
    """What a practitioner can do about an extrapolation report (Core §5;
    `docs/V1.4-EDITS.md` §10's intervention axis).

    Carried as an explicit field rather than left for the caller to infer from
    the binding space, because inferring it requires knowing the rule and the
    rule is the finding. Collapsing the three into a single "outside the
    envelope" scalar would reproduce, for declared physics, exactly the defect
    E-06 documents for inverse design: an unordered number that cannot say which
    of several terms is responsible when the terms call for different purchases.
    """

    WITHIN_ENVELOPE = "within_envelope"
    """Every declared bound is satisfied. No action; the form's claim is
    supported by whatever established it."""

    CONTROL_INVERSE = "control_inverse"
    """A control-space bound binds. The form remains valid for this state; the
    driving programme has left the fitted window, and Core §5's control inverse
    can search for a programme inside it. **Actionable with existing
    machinery** — `omi.inverse`'s apparatus parameterisation already expresses
    the search, and this report supplies a constraint to add to it."""

    BUY_PHYSICS = "buy_physics"
    """A state-space bound binds. No admissible control recovers validity: the
    state is outside the region the form describes. The remedies are a different
    declared form, a wider fit, or an honest refusal
    (`omi.gaps.NotSpecified`) — none of which the framework can currently price
    (§10's maturity reading: this signals, it does not value)."""


class Unbounded(Enum):
    """An explicitly declared *absence* of a bound on one side of a validity
    window (ADR-043, amended before M11.3; Spec §2.2's "stated validity range").

    **Distinct from a missing bound, deliberately.** A form whose established
    range has no upper limit — the source establishes validity above some
    threshold and says nothing above it — must be able to say so. Without this,
    the only ways to declare such a form are to invent a fake upper limit, which
    fabricates a claim the source never made, or to omit the bound, which
    `ValidityRange.report` refuses because an omitted bound cannot be checked.
    Neither is acceptable, so the absence is declared explicitly.

    This follows the framework's own established pattern for the same problem:
    Core §4 item 3 requires a domain with no erasure operators to declare the
    empty inventory *and* how the error-control dichotomy's condition (b) is
    satisfied instead, and `docs/V1.4-EDITS.md` E-26 argues the same for a
    control inverse — "an explicitly empty response is a legal, required
    declaration," never an omission.
    """

    UNBOUNDED = "unbounded"


UNBOUNDED = Unbounded.UNBOUNDED
"""Module-level alias, so a declaration reads ``high=UNBOUNDED`` (Spec §2.2)."""


@dataclass(frozen=True)
class CompositionDependentEdge:
    """A validity-window edge that is a function over composition rather than a fixed
    number (ADR-054; ADR-078 Decision 1).

    **Why a bound needs a third edge kind, not just two floats.** ADR-054's finding is
    that a form's fitted edge can be a property of *which member of the operator
    family* is being evaluated — Core §4 item 1b's parameter (ADR-071, ADR-052's
    descriptor basis) — rather than a constant of the form itself, so a bound expressed
    as ``float | Unbounded`` cannot represent a window that moves as that parameter
    moves. ADR-054's own extension, made concrete here: "`ValidityBound`'s edges
    become **callables over the declared descriptor basis**." Resolving one needs a
    composition, which :meth:`ValidityRange.report` receives as ``evaluated_at`` and
    this class itself does not carry — the same separation :attr:`ConstitutiveForm
    .evaluate` keeps from the state/control values it is evaluated against.

    No domain vocabulary appears here, per this module's own discipline (CLAUDE.md §5
    invariant 3): the worked physics is ADR-054's and ADR-078 Decision 2's, not this
    type's.
    """

    evaluate: Callable[[Mapping[str, float]], float]
    """Descriptor name → edge value (ADR-054), evaluated at a declared composition.
    One float out, unlike :attr:`ConstitutiveForm.evaluate`'s array-valued signature,
    which covers a whole response rather than a single edge."""
    provenance: str
    """The source establishing how this edge depends on composition — a citation, not
    a claim, on the same discipline :attr:`ConstitutiveForm.provenance` already states
    for the form the edge belongs to (ADR-054; ADR-078)."""

    def __post_init__(self) -> None:
        if not self.provenance:
            raise ValueError(
                "a composition-dependent edge declares no provenance: ADR-054's "
                "extension requires the source establishing how the edge depends on "
                "composition, since an unsourced dependence is an assertion rather "
                "than a declaration"
            )


BoundEdge = float | Unbounded | CompositionDependentEdge
"""One edge of a declared validity window: a number, explicitly :data:`UNBOUNDED`, or
a :class:`CompositionDependentEdge` whose value is a function of composition rather
than a constant (Spec §2.2; ADR-043; ADR-054 and ADR-078 Decision 1 for the third
case)."""


class EdgeKind(Enum):
    """Whether a declared window edge is a sharp physical limit or an
    approximate, route-dependent boundary (ADR-043, amended before M11.3; Spec
    §2.2's "stated validity range").

    **Why an approximate edge must be declarable as such.** Some validity edges
    are sharp: a form that does not apply above a transformation start temperature
    has an edge fixed by the physics of that transformation. Others are boundaries
    where a *competing mechanism* takes over, and those depend on the route taken
    to reach them — cooling rate, hold time, path — so the edge is genuinely fuzzy
    rather than merely imprecisely known. Forcing a fuzzy boundary to be declared
    as a clean number fabricates precision the source never had, and **a fuzzy
    bound honestly declared is worth more than a precise one invented.**

    The consequence is a reporting obligation, not just a label: an extrapolation
    factor slightly above ``1.0`` against an approximate edge is not evidence of a
    violation, because the edge itself is not known to that resolution. A consumer
    that cannot tell the two apart will read noise as a finding, which is the
    failure mode `docs/V1.4-EDITS.md` §6 documents nine times over in other
    diagnostics.
    """

    SHARP = "sharp"
    """The edge is a physical limit, known to better resolution than the queries
    being reported against it."""

    APPROXIMATE = "approximate"
    """The edge is a competing-mechanism or route-dependent boundary. A factor
    near ``1.0`` against this edge is not resolvable from being inside the
    window, and MUST NOT be reported as a violation without saying so."""


class FormKind(Enum):
    """What a declared form's :attr:`ConstitutiveForm.evaluate` output *means*
    (ADR-043, amended before M11.3; Core §3.3's evolution operators and Core
    §3.5's constitutive readouts).

    **Why this exists: the shared signature collapses a distinction that
    matters.** Canonical constitutive forms do not have one shape. Some are rate
    laws, stated as a derivative with respect to an accumulated driving measure;
    some are explicit closed-form solutions in elapsed time; some are algebraic
    relations among state components with no time in them at all. All three can
    be expressed with the *same* signature — a map from named quantities to a
    response array — and that is the signature
    :attr:`ConstitutiveForm.evaluate` uses, so the framework needs exactly one.

    But a shared signature is silent about whether the returned number is a
    **rate to be integrated** or a **level to be used directly**, and using one
    where the other is expected is a silent, dimensionally-wrong composition
    rather than an error. So the semantics are *declared* alongside the
    signature. This is the same move Core §3.5 already makes for readouts: three
    types sharing a codomain family, distinguished by a declared tag rather than
    by the caller guessing.
    """

    RATE_LAW = "rate_law"
    """The output is a derivative with respect to a declared accumulated driving
    measure, and MUST be consumed by an integrator. Composing it as though it
    were a level is dimensionally wrong."""

    EXPLICIT_SOLUTION = "explicit_solution"
    """The output is the integrated quantity itself, as a closed-form function of
    elapsed driving. Already integrated; MUST NOT be integrated again."""

    ALGEBRAIC = "algebraic"
    """The output is a relation among state components with no accumulation in
    it — a function of the current state alone, in Core §3.1's sense."""


@dataclass(frozen=True)
class ValidityBound:
    """One declared bound of a form's validated range (ADR-043; Spec §2.2's
    proposed sixth category, whose reporting obligation names "the form's stated
    validity range").

    *name* is domain-supplied, following the same convention as
    `omi.state.StateSchema`'s component names: the label is the domain's, the
    structure around it is the framework's.

    **Two-sided and one-sided windows use different factor rules, and the
    difference is declared rather than inferred** (see
    :meth:`extrapolation_factor`). A one-sided window has no centre, so it must
    declare a :attr:`fitted_scale` to say what "far past the bound" means in its
    own units; a two-sided window must not, because its half-width already says
    so and two competing scales would leave the reported factor ambiguous.
    """

    name: str
    space: ValiditySpace
    low: BoundEdge
    high: BoundEdge
    regime: str = ""
    """Optional label for the regime this bound delimits, where a form has more
    than one (ADR-043 point 5, mirroring `omi.classb.n_eff`'s two-regime
    reporting: a bound that separates regimes should say which, not only how
    far)."""
    low_kind: EdgeKind = EdgeKind.SHARP
    """Whether the lower edge is sharp or an approximate, route-dependent
    boundary (:class:`EdgeKind`; Spec §2.2). Per-edge rather than per-bound,
    because a single window can have one sharp edge fixed by physics and one fuzzy
    edge set by a competing mechanism — which is the common case for a
    transformation window, not an exotic one."""
    high_kind: EdgeKind = EdgeKind.SHARP
    """Whether the upper edge is sharp or approximate (:class:`EdgeKind`; Spec
    §2.2)."""
    fitted_scale: float | None = None
    """The declared extent of the fitted range, in the bound's own units —
    **required for a one-sided window and forbidden for a two-sided one**
    (Spec §2.2; ADR-043).

    Required because a one-sided window has no half-width to measure
    extrapolation in, and forbidden on a two-sided window because the half-width
    already supplies that unit. Declared rather than derived from the bound's own
    magnitude for the same reason Core §3.9 requires a metric to be declared: a
    factor computed as ``(value - high) / |high|`` would change if the domain
    reported the same physical bound in different units, which is precisely the
    unit-dependence `docs/V1.4-EDITS.md` E-33 measured at sixteen orders of
    magnitude for the semigroup residual. The domain states what "far" means."""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a validity bound must be named")
        if self.low is UNBOUNDED and self.high is UNBOUNDED:
            raise ValueError(
                f"bound {self.name!r} declares both edges UNBOUNDED, which is not a bound at "
                "all — a form with no limit in this quantity should omit the bound and declare "
                "its range in whatever quantity the source does limit (Spec §2.2)"
            )
        if not self.is_one_sided:
            if self.is_composition_dependent:
                # At least one edge is a CompositionDependentEdge and the window is
                # two-sided (neither edge is UNBOUNDED), so `high > low` cannot be
                # checked until both edges are resolved against a composition.
                # ValidityRange.report() resolves this bound via dataclasses.replace()
                # before use (ADR-078 Decision 1), which reconstructs a ValidityBound
                # with both edges as plain floats and re-runs this __post_init__ on
                # THAT instance — so the check is deferred, not skipped.
                pass
            else:
                low, high = float(self.low), float(self.high)  # type: ignore[arg-type]
                if not high > low:
                    raise ValueError(f"bound {self.name!r} needs high > low, got [{low}, {high}]")
            if self.fitted_scale is not None:
                raise ValueError(
                    f"bound {self.name!r} is two-sided and also declares a fitted_scale: the "
                    "half-width already supplies the extrapolation unit, and two competing "
                    "scales would make the reported factor ambiguous"
                )
        else:
            if self.fitted_scale is None:
                raise ValueError(
                    f"bound {self.name!r} is one-sided and declares no fitted_scale: a one-sided "
                    "window has no half-width, so nothing says what 'far past the bound' means "
                    "in this quantity's units (ADR-043)"
                )
            if self.fitted_scale <= 0.0:
                raise ValueError(f"bound {self.name!r} needs a positive fitted_scale")

    @property
    def is_one_sided(self) -> bool:
        """Whether exactly one edge of this window is declared :data:`UNBOUNDED`
        (Spec §2.2's "stated validity range"; ADR-043)."""
        return (self.low is UNBOUNDED) != (self.high is UNBOUNDED)

    @property
    def is_composition_dependent(self) -> bool:
        """Whether either edge is a :class:`CompositionDependentEdge` (Spec §2.2's
        "stated validity range"; ADR-054; ADR-078 Decision 1).

        ``True`` means this bound cannot be evaluated without a composition supplied
        as ``evaluated_at`` to :meth:`ValidityRange.report` — checked there, not here,
        since this bound does not receive ``evaluated_at`` directly (ADR-078
        Decision 1)."""
        return isinstance(self.low, CompositionDependentEdge) or isinstance(
            self.high, CompositionDependentEdge
        )

    @property
    def centre(self) -> float:
        """Midpoint of the validated window (Spec §2.2's "stated validity
        range").

        Raises for a one-sided window: there is no centre, and returning a
        plausible number would be inventing one — the same discipline
        `omi.interface.classify_invariant` applies when a declaration does not
        settle the question.
        """
        if self.is_one_sided:
            raise ValueError(
                f"bound {self.name!r} is one-sided and has no centre; use "
                "extrapolation_factor, which applies the one-sided rule"
            )
        return 0.5 * (float(self.low) + float(self.high))  # type: ignore[arg-type]

    @property
    def half_width(self) -> float:
        """Half-width of the validated window, the unit a two-sided
        extrapolation factor is measured in (Spec §2.2). Raises for a one-sided
        window, which has none — see :attr:`fitted_scale`."""
        if self.is_one_sided:
            raise ValueError(
                f"bound {self.name!r} is one-sided and has no half-width; its extrapolation "
                "unit is the declared fitted_scale"
            )
        return 0.5 * (float(self.high) - float(self.low))  # type: ignore[arg-type]

    def violated_edge(self, value: float) -> str | None:
        """Which edge *value* falls outside — ``"low"``, ``"high"``, or ``None``
        when inside the declared window (Spec §2.2).

        Needed because :meth:`extrapolation_factor` is a magnitude and does not
        say which side, and the two edges of one window can differ in
        :class:`EdgeKind` — so a consumer cannot tell whether a reported violation
        is against a sharp limit or a fuzzy boundary without this.
        """
        if not isinstance(self.low, Unbounded) and value < float(self.low):  # type: ignore[arg-type]
            return "low"
        if not isinstance(self.high, Unbounded) and value > float(self.high):  # type: ignore[arg-type]
            return "high"
        return None

    def edge_kind(self, value: float) -> EdgeKind | None:
        """The :class:`EdgeKind` of the edge *value* violates, or ``None`` inside
        the window (Spec §2.2; ADR-043)."""
        edge = self.violated_edge(value)
        if edge is None:
            return None
        return self.low_kind if edge == "low" else self.high_kind

    def extrapolation_factor(self, value: float) -> float:
        """How far *value* sits outside the declared window (Spec §2.2's "stated
        validity range"; ADR-043). **Two rules, both giving exactly ``1.0`` at
        the boundary and ``> 1`` outside it**, so `outside_envelope` has one
        meaning regardless of which applied:

        - **Two-sided window:** ``|value - centre| / half_width``. Graded inside
          as well as outside, so ``0.4`` reads as "40% of the way from centre to
          the edge" and ``2.3`` as "2.3× the half-width from centre". This is the
          convention Class B already uses for its own extrapolation ratio
          (CLAUDE.md §5 invariant 4), reused rather than re-invented.
        - **One-sided window:** ``1 + (distance past the declared edge) /
          fitted_scale``, and exactly ``1.0`` anywhere inside. Chosen over the
          alternatives because a one-sided window supplies no natural interior
          scale: there is no centre to measure from, so *any* graded interior
          reading would have to invent a reference point the source never
          established. Reporting a flat ``1.0`` inside states honestly that the
          declaration supports the query and says nothing further, while the
          exterior reading remains quantitative in units the domain declared.

        The consequence is worth stating plainly: for a one-sided bound this
        report answers "am I outside, and by how much" and **not** "how close to
        the edge am I". A caller wanting the latter needs a two-sided window,
        which means a source that establishes both edges.
        """
        if not self.is_one_sided:
            return abs(value - self.centre) / self.half_width
        assert self.fitted_scale is not None  # guaranteed by __post_init__
        if self.high is UNBOUNDED:
            # Window is [low, ∞): the violation is falling *below* low.
            excess = float(self.low) - value  # type: ignore[arg-type]
        else:
            # Window is (-∞, high]: the violation is rising *above* high.
            excess = value - float(self.high)  # type: ignore[arg-type]
        return 1.0 + max(0.0, excess) / self.fitted_scale


@dataclass(frozen=True)
class ExtrapolationReport:
    """Where an evaluation sits relative to a declared form's validated range
    (ADR-043; Spec §2.2's proposed reporting obligation).

    A result dataclass rather than a bare float (CLAUDE.md §8): the per-bound
    factors, the binding bound, the space it binds in and the action it implies
    all travel together, because a caller receiving only "2.3× outside" cannot
    tell whether to re-run the control inverse with a tightened constraint or to
    stop and commission physics — and those are not variations of one response.
    """

    form_name: str
    factors: dict[str, float]
    """Per-bound extrapolation factor, keyed by the bound's declared name."""
    binding_bound: ValidityBound | None
    """The bound with the largest factor, or ``None`` when no bounds were
    declared — which :class:`ConstitutiveForm` forbids at construction, so
    ``None`` here means the report was built directly rather than from a form."""

    @property
    def worst_factor(self) -> float:
        """The largest per-bound factor (Spec §2.2): ``≤ 1`` means every declared
        bound is satisfied."""
        return max(self.factors.values()) if self.factors else 0.0

    @property
    def outside_envelope(self) -> bool:
        """Whether any declared bound is exceeded (Spec §2.2's extrapolation
        warning condition)."""
        return self.worst_factor > 1.0

    @property
    def binding_space(self) -> ValiditySpace | None:
        """Which space the binding bound lives in — Core §3.1's state space or
        Core §3.2's control space (ADR-043) — or ``None`` inside the envelope,
        where nothing binds and the question does not arise."""
        if not self.outside_envelope or self.binding_bound is None:
            return None
        return self.binding_bound.space

    binding_edge_kind: EdgeKind | None = None
    """The :class:`EdgeKind` of the edge the binding bound violates, or ``None``
    inside the envelope (Spec §2.2; ADR-043).

    Carried so an :attr:`~EdgeKind.APPROXIMATE` edge cannot be read as a sharp
    violation: a factor of ``1.05`` against a competing-mechanism boundary is
    within the edge's own uncertainty, and a consumer that cannot see the
    difference will report noise as a finding."""

    @property
    def edge_is_approximate(self) -> bool:
        """Whether the binding violation is against an approximate edge (Spec
        §2.2). ``False`` inside the envelope, where nothing binds."""
        return self.binding_edge_kind is EdgeKind.APPROXIMATE

    @property
    def action(self) -> ValidityAction:
        """The practitioner action this report implies (Core §5;
        `docs/V1.4-EDITS.md` §10) — the field that makes the control/state split
        legible in the output rather than only in the declaration."""
        space = self.binding_space
        if space is None:
            return ValidityAction.WITHIN_ENVELOPE
        if space is ValiditySpace.CONTROL:
            return ValidityAction.CONTROL_INVERSE
        return ValidityAction.BUY_PHYSICS

    @property
    def actionable_by_control_inverse(self) -> bool:
        """Whether Core §5's control inverse can respond to this report.

        ``True`` only for a control-space violation. Inside the envelope there is
        nothing to act on, and for a state-space violation no admissible control
        recovers validity — reporting both as "not actionable" would be
        accurate but useless, which is why :attr:`action` distinguishes three
        cases and this property distinguishes two.
        """
        return self.action is ValidityAction.CONTROL_INVERSE


def _resolve_edge(
    edge: BoundEdge, bound_name: str, evaluated_at: Mapping[str, float] | None
) -> BoundEdge:
    """Resolve one edge of a bound against a supplied composition (ADR-054; ADR-078
    Decision 1).

    A fixed edge (a number or :data:`UNBOUNDED`) passes through untouched. A
    :class:`CompositionDependentEdge` needs *evaluated_at* to resolve against — the
    one thing this function checks before calling the edge's ``evaluate``, since
    :class:`ValidityBound` does not carry ``evaluated_at`` itself (ADR-078 Decision 1:
    the bound "should not need to know about `evaluated_at` directly"). Only
    :meth:`ValidityRange.report` calls this.
    """
    if not isinstance(edge, CompositionDependentEdge):
        return edge
    if evaluated_at is None:
        raise ValueError(
            f"bound {bound_name!r} declares a composition-dependent edge but no "
            "evaluated_at was supplied to report(): resolving the edge needs a "
            "composition, and this is a malformed call rather than a diagnosis "
            "(ADR-078 Decision 1) — distinct from a missing state/control value, "
            "which is checked separately above"
        )
    try:
        return float(edge.evaluate(evaluated_at))
    except KeyError as exc:
        raise ValueError(
            f"bound {bound_name!r}'s composition-dependent edge needs descriptor "
            f"{exc.args[0]!r}, which evaluated_at does not supply: resolving the edge "
            "needs the composition value its evaluate() reads (ADR-078 Decision 1)"
        ) from exc


@dataclass(frozen=True)
class ValidityRange:
    """A declared form's validated range: bounds in Core §3.1's state space,
    Core §3.2's control space, or both (Spec §2.2's "stated validity range";
    ADR-043)."""

    bounds: tuple[ValidityBound, ...]

    def __post_init__(self) -> None:
        names = [b.name for b in self.bounds]
        if len(names) != len(set(names)):
            raise ValueError("validity bound names must be unique within a range")

    def spaces(self) -> frozenset[ValiditySpace]:
        """Which of Core §3.1's state space and Core §3.2's control space this
        range constrains (ADR-043: both are legal, and declaring only one is
        legal too — a form genuinely bounded in one space should say so)."""
        return frozenset(b.space for b in self.bounds)

    def report(
        self,
        form_name: str,
        values: Mapping[str, float],
        *,
        evaluated_at: Mapping[str, float] | None = None,
    ) -> ExtrapolationReport:
        """Evaluate every declared bound against *values* (Spec §2.2's reporting
        obligation), keyed by bound name.

        Every declared bound MUST have a value. A missing one raises rather than
        being skipped: a bound silently omitted from the report is a bound whose
        violation cannot be seen, which is precisely the "diagnostic blind to its
        own dominant input" shape `docs/V1.4-EDITS.md` §6 documents eight times
        over. Extra values are ignored — a caller may pass a whole state or
        control vector.

        *evaluated_at* resolves any :class:`CompositionDependentEdge` among the
        declared bounds against a composition, before either edge is used (ADR-054;
        ADR-078 Decision 1). Required exactly when at least one bound is
        :attr:`~ValidityBound.is_composition_dependent`; omitting it, or omitting a
        descriptor name a composition-dependent edge needs, raises — a malformed
        call, distinct from the missing-*values* check above, and distinct from
        ADR-078 Decision 3's regime verdict (that is a diagnosis with an answer; this
        is nothing to evaluate at all). A bound declared with only ``float |
        Unbounded`` edges is unaffected by this parameter and needs no
        *evaluated_at*.
        """
        missing = [b.name for b in self.bounds if b.name not in values]
        if missing:
            raise ValueError(
                f"no value supplied for declared validity bound(s) {missing}: a bound "
                "without a value cannot be checked, and skipping it would hide the "
                "violation the report exists to surface"
            )
        # Resolve composition-dependent edges before any bound is used below, so
        # extrapolation_factor()/edge_kind() only ever see plain floats or UNBOUNDED
        # (ADR-078 Decision 1) — ValidityBound's own methods stay unmodified and
        # unaware of evaluated_at, per the ADR's own placement constraint. A bound
        # with no composition-dependent edge is reused as-is (same object, not a
        # copy), which is what keeps every pre-existing report() call byte-identical.
        resolved = [
            replace(
                b,
                low=_resolve_edge(b.low, b.name, evaluated_at),
                high=_resolve_edge(b.high, b.name, evaluated_at),
            )
            if b.is_composition_dependent
            else b
            for b in self.bounds
        ]
        factors = {b.name: b.extrapolation_factor(values[b.name]) for b in resolved}
        binding = max(resolved, key=lambda b: factors[b.name]) if resolved else None
        edge_kind = binding.edge_kind(values[binding.name]) if binding is not None else None
        return ExtrapolationReport(form_name, factors, binding, edge_kind)


@dataclass(frozen=True)
class ConstitutiveForm:
    """A declared constitutive form — Core §4 item 6d, Spec §2.2's proposed sixth
    hard-constraint category (ADR-043; `docs/V1.4-EDITS.md` E-32).

    **A bound object, not a label.** ADR-043 departs deliberately from item 6's
    existing free-text convention here, and :attr:`evaluate` is why: a form you
    cannot evaluate is not a declaration, it is an assertion. v1.3's item 6 takes
    free-text names, which is exactly why `omi.interface.classify_invariant` had
    to become a keyword heuristic that refuses rather than guesses; repeating
    that in a category whose entire purpose is to carry structure would be
    self-inflicted.
    """

    name: str
    """Domain-supplied identity of the functional form (same convention as
    `omi.state.StateSchema`'s component names)."""
    kind: FormKind
    """What :attr:`evaluate`'s output means (Core §3.3, Core §3.5) — required,
    because the shared signature below cannot express it and a rate used as a
    level is a silent dimensional error rather than a raised one."""
    evaluate: Callable[[Mapping[str, float]], FloatArray]
    """The form itself: a map from named quantities to a response array. One
    signature covers rate laws, explicit solutions and algebraic relations alike
    (see :class:`FormKind`), and the keys are the same names
    :attr:`validity`'s bounds use, so the quantities a form consumes and the
    quantities its range is declared over cannot drift apart.

    Holding the callable is what makes the declaration checkable rather than
    assertable (Spec §2.2): a form that cannot be evaluated is an assertion."""
    parameters: Mapping[str, float]
    """Fitted parameter values (Spec §2.2's "its fitted parameter values")."""
    validity: ValidityRange
    """The load-bearing field (ADR-043): a form without a declared range makes an
    unbounded claim."""
    provenance: str
    """The source establishing the form — a citation, not a claim (Spec §2.2)."""
    governs: tuple[tuple[Slot, str], ...]
    """Which state components (Core §3.1's slots) this form governs."""
    refines: str | None = None
    """The :attr:`name` of a previously published form this one **refines**
    (`docs/V1.4-EDITS.md` E-40; ADR-069) — physics unchanged, what is claimed about it
    narrowed or extended.

    **The worked case this closes.** `KOCKS_MECKING_STRAIN_WINDOWED` was published
    *alongside* `KOCKS_MECKING` rather than as an edit to it, because
    `ValidityRange.report` requires a value for every declared bound and a form's
    range therefore cannot be extended without breaking every caller that evaluates
    the original with the original's keys. Before this field, `omi.interface.diff`
    (and any cross-domain comparison of item 6d) saw two forms where the physics is
    one — a refinement misread as a disagreement. Declaring `refines` lets a
    consumer distinguish them without inventing a mutable range.

    `None` is an **independent** declaration: two domains whose forms both leave
    this unset genuinely disagree if their content differs, in the ordinary sense
    `omi.interface.diff` already gives that word."""
    refinement_note: str = ""
    """What changed, required non-empty whenever :attr:`refines` is set — E-40's own
    proposed wording: "stating which items changed." Not required when `refines` is
    `None`, since there is nothing to explain."""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a declared constitutive form must be named")
        if not self.provenance:
            raise ValueError(
                f"form {self.name!r} declares no provenance: Spec §2.2's proposed category "
                "requires the source establishing the form, since an unsourced form is an "
                "assertion rather than a declaration"
            )
        if not self.governs:
            raise ValueError(f"form {self.name!r} governs no state component, so it constrains nothing")
        if not self.validity.bounds:
            raise ValueError(
                f"form {self.name!r} declares no validity bounds: an unbounded form makes an "
                "unbounded claim, which is the failure the validity range exists to prevent "
                "(ADR-043) — declare the range the source actually establishes"
            )
        if self.refines is not None and not self.refinement_note.strip():
            raise ValueError(
                f"form {self.name!r} declares refines={self.refines!r} with no refinement_note: "
                "E-40's proposed wording requires stating WHICH ITEMS CHANGED, since a refinement "
                "asserting nothing is indistinguishable from an unexplained edit"
            )
        if self.refines == self.name:
            raise ValueError(f"form {self.name!r} cannot refine itself")

    def report(
        self,
        values: Mapping[str, float],
        *,
        evaluated_at: Mapping[str, float] | None = None,
    ) -> ExtrapolationReport:
        """Where the current evaluation sits relative to this form's validated
        range (Spec §2.2's reporting obligation; ADR-043).

        **Reported, never enforced.** A query outside the range is surfaced, not
        refused: refusing would make the operator unusable exactly where inverse
        design must probe, and `docs/V1.4-EDITS.md` E-28 is the standing evidence
        that a constraint blocking the optimiser rather than informing it
        composes into a new failure.

        *evaluated_at* is a straight pass-through to :meth:`ValidityRange.report`
        (ADR-078 Decision 1), so a composition-dependent form is reached through the
        same front door as every other form rather than by a caller reaching past
        this method into :attr:`validity` directly. `None` — the default, and every
        existing call site's value — behaves exactly as before this parameter
        existed: a form with no :class:`CompositionDependentEdge` among its declared
        bounds never looks at it.
        """
        return self.validity.report(self.name, values, evaluated_at=evaluated_at)


class RegimeVerdict(Enum):
    """Whether a proposed composition still sits inside the descriptor interval a
    declared mechanism set's validity ranges were established for (Spec §2.2's
    proposed sixth category; ADR-054; ADR-078 Decision 3).

    Two members, not :class:`ValidityAction`'s four-way space/action split. This check
    answers a categorical question about the *chemistry itself*, prior to and
    independent of any one form's own control/state validity ranges — there is no
    analogue here of a control-space violation being actionable while a state-space one
    is not, because nothing about *where the descriptor interval was established* names
    an admissible-control remedy the way a control-space bound does.
    """

    WITHIN_INTERVAL = "within_interval"
    """Every declared descriptor sits inside its interval. The mechanism set the
    interval was established for is presumed to still apply, and a composition-
    dependent form's own :meth:`ValidityRange.report` is meaningful for this
    composition."""

    OUTSIDE_INTERVAL = "outside_interval"
    """At least one declared descriptor has left its interval. ADR-054's diagnosis: the
    proposed chemistry may support a different mechanism than the one the form's
    validity ranges were fitted for, so those ranges are no longer a claim about this
    composition at all — not a graded warning, per ADR-054's own "a refusal, not a
    warning"."""


@dataclass(frozen=True)
class RegimeReport:
    """Where a proposed composition sits relative to a declared composition-validity
    interval (Spec §2.2's proposed reporting obligation; ADR-054; ADR-078 Decision 3).

    A result dataclass rather than a bare verdict (CLAUDE.md §8), on the same reasoning
    :class:`ExtrapolationReport` states for itself: a caller receiving only
    ``OUTSIDE_INTERVAL`` cannot tell which descriptor is responsible or by how much, and
    a regime finding without that is a flag with nothing to act on.
    """

    verdict: RegimeVerdict
    binding_descriptor: str | None
    """Which declared descriptor sits furthest outside its interval, or ``None`` when
    every descriptor is within (:attr:`RegimeVerdict.WITHIN_INTERVAL`)."""
    factor: float | None
    """The binding descriptor's two-sided extrapolation factor — the same
    ``|value - centre| / half_width`` convention :meth:`ValidityBound
    .extrapolation_factor` uses for a two-sided window, since a
    ``COMPOSITION_VALIDITY_INTERVAL``-shaped entry is a plain ``(low, high)`` pair
    rather than a :class:`ValidityBound`. ``None`` when :attr:`verdict` is
    ``WITHIN_INTERVAL``."""
    interval: Mapping[str, tuple[float, float]]
    """The declared interval this report was checked against, carried alongside the
    verdict so a consumer does not need the caller's own copy to interpret it."""


def check_composition_regime(
    descriptors: Mapping[str, float], interval: Mapping[str, tuple[float, float]]
) -> RegimeReport:
    """Whether *descriptors* still sits inside the composition-validity interval a
    declared mechanism set's validity ranges were established for (Spec §2.2's
    proposed sixth category; ADR-054; ADR-078 Decision 3).

    **Returns a verdict; does not raise.** This repository's existing split is:
    **raise** when the framework has nothing to say (`omi.gaps.NotSpecified` for a
    `[Pass B]`/`[Pass C]` gap, `amplification_decomposition`'s refusal when the
    decomposition is ill-posed) and **return a verdict** when it has something
    specific to say that a caller acts on, possibly repeatedly, inside a loop
    (:class:`ExtrapolationReport`, :class:`ValidityAction`, `AttainabilityVerdict`). A
    regime-boundary finding is the second case: "this mechanism set no longer applies,
    here is which descriptor and by how much" is content, not absence. The
    missing-descriptor case below is the *first* case — nothing to check is a
    malformed call, not a diagnosis, and is deliberately a different failure mode from
    the verdict this function otherwise returns.

    This is not in tension with ADR-054's own language calling the check "a refusal,
    not a warning": that is a **policy conclusion** about what a caller should do with
    `OUTSIDE_INTERVAL` — treat the composition as inadmissible — not a claim that the
    check must be a raised exception to *be* a refusal.

    **A calling-convention requirement, not a structurally enforced one**
    (:meth:`ConstitutiveForm.report`'s own "reported, never enforced" stance, restated
    here for the check that precedes it): `check_composition_regime` is called
    **before** :meth:`ValidityRange.report` on a composition-dependent form, and a
    caller finding `OUTSIDE_INTERVAL` MUST treat the form's subsequent report as not
    meaningful. Nothing here stops a caller calling `report()` anyway — the
    composition-inverse machinery (ADR-053, ADR-077) needs to be able to probe exactly
    this boundary, and a check that refused to compose with a direct `report()` call
    would be unusable for the one purpose it exists to serve.

    Every descriptor named in *interval* MUST have a value in *descriptors*; a missing
    one raises, on the same style :meth:`ValidityRange.report`'s own missing-value
    check uses — nothing to check is not a finding.
    """
    missing = [name for name in interval if name not in descriptors]
    if missing:
        raise ValueError(
            f"no value supplied for declared composition-validity descriptor(s) {missing}: "
            "a descriptor without a value cannot be checked, and skipping it would hide "
            "the regime violation this check exists to surface"
        )
    factors = {
        name: abs(descriptors[name] - 0.5 * (low + high)) / (0.5 * (high - low))
        for name, (low, high) in interval.items()
    }
    if not factors or max(factors.values()) <= 1.0:
        return RegimeReport(RegimeVerdict.WITHIN_INTERVAL, None, None, interval)
    binding = max(factors, key=lambda name: factors[name])
    return RegimeReport(RegimeVerdict.OUTSIDE_INTERVAL, binding, factors[binding], interval)


@runtime_checkable
class ConstitutivelyConstrained(Protocol):
    """An operator constrained to declared forms, which therefore reports where it
    sits relative to their validated ranges (Spec §2.2's proposed obligation;
    ADR-043).

    **A structural Protocol rather than a widening of
    `omi.operators.EvolutionOperator`**, and that is ADR-042's
    composition-over-modification principle applied to behaviour rather than to
    data. Adding this method to the v1.3 ABC would give every v1.3 operator an
    attribute it does not implement, and would make a v1.3 base class carry a
    constitutive-extension obligation — the modification the boundary exists to avoid. As a
    Protocol, an operator satisfies it by having the method, nothing in v1.3
    changes, and a caller can still ask the question in a type-safe way.
    """

    def extrapolation_report(self, state: State, control: Control) -> "ChainExtrapolationReport":
        """Where this operator's declared forms sit relative to their validated
        ranges (Spec §2.2; ADR-043)."""
        ...


@dataclass(frozen=True)
class ChainExtrapolationReport:
    """Chain-level extrapolation: the worst factor over segments, **and which
    segment is responsible** (ADR-043 point 3).

    Naming the binding segment mirrors Spec §7.3's ordered infeasibility
    diagnosis (`omi.inverse.diagnose_infeasibility`, and
    `docs/V1.4-EDITS.md` E-06's finding that an unattributed maximum cannot
    support a decision): a chain reported as "3.1× outside" without saying where
    tells a practitioner nothing they can act on.
    """

    per_segment: dict[str, ExtrapolationReport]
    binding_segment: str | None

    @property
    def worst_factor(self) -> float:
        """The largest factor over every segment (Spec §2.2)."""
        return max((r.worst_factor for r in self.per_segment.values()), default=0.0)

    @property
    def outside_envelope(self) -> bool:
        """Whether any segment's form is outside its declared range (Spec §2.2)."""
        return self.worst_factor > 1.0

    @property
    def action(self) -> ValidityAction:
        """The binding segment's implied action (Core §5; `docs/V1.4-EDITS.md`
        §10) — the chain's action is the binding segment's, not an aggregate,
        since a purchase is made against one relationship at a time."""
        if self.binding_segment is None:
            return ValidityAction.WITHIN_ENVELOPE
        return self.per_segment[self.binding_segment].action


def worst_extrapolation(reports: Mapping[str, ExtrapolationReport]) -> ChainExtrapolationReport:
    """Compose per-segment extrapolation reports into a chain-level one (Core
    §3.3's composition; ADR-043 point 3).

    Elementwise worst over segments, with the binding segment named. Returns a
    report whose :attr:`~ChainExtrapolationReport.binding_segment` is ``None``
    when every segment is inside its envelope.
    """
    if not reports:
        return ChainExtrapolationReport({}, None)
    per_segment = dict(reports)
    binding = max(per_segment, key=lambda name: per_segment[name].worst_factor)
    if not per_segment[binding].outside_envelope:
        return ChainExtrapolationReport(per_segment, None)
    return ChainExtrapolationReport(per_segment, binding)
