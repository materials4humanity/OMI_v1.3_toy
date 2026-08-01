"""Declared constitutive forms: Core §4 item 6d and Spec §2.2's proposed sixth
hard-constraint category (proposed-v1.4; ADR-043, docs/DECISIONS.md).

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

No domain vocabulary appears here (CLAUDE.md §5 invariant 3): this module
supplies the category, and a domain supplies the forms that fill it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping

from omi.state import FloatArray, Slot


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


@dataclass(frozen=True)
class ValidityBound:
    """One declared bound of a form's validated range (ADR-043; Spec §2.2's
    proposed sixth category, whose reporting obligation names "the form's stated
    validity range").

    *name* is domain-supplied, following the same convention as
    `omi.state.StateSchema`'s component names: the label is the domain's, the
    structure around it is the framework's.
    """

    name: str
    space: ValiditySpace
    low: float
    high: float
    regime: str = ""
    """Optional label for the regime this bound delimits, where a form has more
    than one (ADR-043 point 5, mirroring `omi.classb.n_eff`'s two-regime
    reporting: a bound that separates regimes should say which, not only how
    far)."""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a validity bound must be named")
        if not self.high > self.low:
            raise ValueError(f"bound {self.name!r} needs high > low, got [{self.low}, {self.high}]")

    @property
    def centre(self) -> float:
        """Midpoint of the validated window (Spec §2.2's "stated validity
        range")."""
        return 0.5 * (self.low + self.high)

    @property
    def half_width(self) -> float:
        """Half-width of the validated window, the unit the extrapolation factor
        is measured in (Spec §2.2)."""
        return 0.5 * (self.high - self.low)

    def extrapolation_factor(self, value: float) -> float:
        """How far *value* sits from the window centre, in half-widths (Spec
        §2.2's "stated validity range"; ADR-043).

        Exactly ``1.0`` at either edge of the declared range, below it inside,
        above it outside — so ``2.3`` reads directly as "2.3× the validated
        half-width from centre", and ``> 1`` is the extrapolation condition. This
        is the same convention Class B already uses for its own extrapolation
        ratio (CLAUDE.md §5 invariant 4), reused rather than re-invented.
        """
        return abs(value - self.centre) / self.half_width


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

    def report(self, form_name: str, values: Mapping[str, float]) -> ExtrapolationReport:
        """Evaluate every declared bound against *values* (Spec §2.2's reporting
        obligation), keyed by bound name.

        Every declared bound MUST have a value. A missing one raises rather than
        being skipped: a bound silently omitted from the report is a bound whose
        violation cannot be seen, which is precisely the "diagnostic blind to its
        own dominant input" shape `docs/V1.4-EDITS.md` §6 documents eight times
        over. Extra values are ignored — a caller may pass a whole state or
        control vector.
        """
        missing = [b.name for b in self.bounds if b.name not in values]
        if missing:
            raise ValueError(
                f"no value supplied for declared validity bound(s) {missing}: a bound "
                "without a value cannot be checked, and skipping it would hide the "
                "violation the report exists to surface"
            )
        factors = {b.name: b.extrapolation_factor(values[b.name]) for b in self.bounds}
        binding = max(self.bounds, key=lambda b: factors[b.name]) if self.bounds else None
        return ExtrapolationReport(form_name, factors, binding)


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
    evaluate: Callable[..., FloatArray]
    """The form itself. Holding it makes the declaration checkable rather than
    assertable (Spec §2.2)."""
    parameters: Mapping[str, float]
    """Fitted parameter values (Spec §2.2's "its fitted parameter values")."""
    validity: ValidityRange
    """The load-bearing field (ADR-043): a form without a declared range makes an
    unbounded claim."""
    provenance: str
    """The source establishing the form — a citation, not a claim (Spec §2.2)."""
    governs: tuple[tuple[Slot, str], ...]
    """Which state components (Core §3.1's slots) this form governs."""

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

    def report(self, values: Mapping[str, float]) -> ExtrapolationReport:
        """Where the current evaluation sits relative to this form's validated
        range (Spec §2.2's reporting obligation; ADR-043).

        **Reported, never enforced.** A query outside the range is surfaced, not
        refused: refusing would make the operator unusable exactly where inverse
        design must probe, and `docs/V1.4-EDITS.md` E-28 is the standing evidence
        that a constraint blocking the optimiser rather than informing it
        composes into a new failure.
        """
        return self.validity.report(self.name, values)


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
