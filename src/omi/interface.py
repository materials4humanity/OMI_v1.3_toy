"""The seven-item instantiation interface (Core §4), expressed as a shared,
diffable declaration.

Cites Core §4: "Generality is a claim, and claims require a mechanism... a
domain enters the framework by supplying seven items." ADR-016
(docs/DECISIONS.md) fixes the declaration's shape here in domain-neutral
code; the *content* of a declaration is supplied by each domain in
``omi_domains/*/interface.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum, auto

from omi.state import StateSchema


@dataclass(frozen=True)
class InstantiationDeclaration:
    """Core §4's seven items, in the Core's own order, as one comparable
    object (ADR-016) — so two domains declared in this shape can be diffed
    mechanically (Core §4: "it is comparative... which is what converts a
    collection of examples into evidence of generality")."""

    state_schema: StateSchema
    """Item 1: occupants of each slot (components/dimensions live on the
    schema itself); which slots are empty is queryable via
    :meth:`~omi.state.StateSchema.is_empty`."""

    control_space: str
    """Item 2: 𝒰 and 𝒰_adm, including whether a control inverse exists at
    all (Core §4 item 2 — determined here)."""

    erasure_inventory: tuple[str, ...]
    """Item 3: names of operators declared as erasures. Empty means no
    erasure operators — condition (b) of the error-control dichotomy (Core
    §3.9) must then be satisfied some other way, and the declaration should
    say how (put that in :attr:`observation_suite` or prose elsewhere)."""

    readout_catalogue: tuple[str, ...]
    """Item 4: every target response, named with its type (0/1/2) and class
    (A/B), e.g. ``"hardness: Type-0/Class-A"``."""

    observation_suite: tuple[str, ...]
    """Item 5: available modalities."""

    invariants: tuple[str, ...]
    """Item 6: conservation laws / monotone functionals available as hard
    constraints (→ Spec §5) and reachability certificates (Core §5)."""

    scale_structure: str
    """Item 7: where homogenisation is applied, between which scales, and
    (once measured, at M2+) the closure defect ``‖𝒟_λ‖``."""


class SpecificationVersion(Enum):
    """Which **claim target** a conformance result is stated against — an issued
    specification, or a named proposed extension (Spec §9.1; ADR-042, ADR-067).

    **A member is named by a version number only when that version is issued.** OMI
    v1.3 is issued, so `V1_3` carries one. Nothing beyond it has been issued, so the
    two extensions this repository proposes are named by *what they propose* rather
    than by a number that has not been assigned — see ADR-067 and CLAUDE.md §8. That
    is `docs/V1.4-EDITS.md` E-43 applied to this enum: E-43's finding is that a level
    plus a version is still not self-describing because the version does not carry
    the framework's *purpose*, and a target named for its purpose does.

    Spec §9.1 requires that "an implementation MUST state its level" and does
    not require it to state the version that level is claimed against. That is
    a framework gap (`docs/V1.4-EDITS.md` E-35): OMI-0/1/2 are defined by the
    rows of §9.1's table, and a framework revision changes those rows, so a
    level name is **not self-describing** — a claim of OMI-1 against one version
    is not a claim of OMI-1 against another. This enum is the carrier that lets
    a report state it, by the same discipline Core §3.9 imposes on
    metric-dependent quantities: a quantity whose meaning depends on a declared
    choice travels with that choice (CLAUDE.md §5 invariant 1).
    """

    V1_3 = "v1.3"
    """OMI v1.3 as specified in `docs/OMI-v1_3-Core.md` and
    `docs/OMI-v1_3-Implementation-Spec.md`. Every conformance result, oracle and
    audit finding this repository produced through M10 is a v1.3 result."""

    PROPOSED_CONSTITUTIVE_EXTENSION = "proposed-constitutive-extension"
    """The proposed **constitutive-form** extension (ADR-042 – ADR-045): a domain may
    declare that an operator follows a named constitutive form, valid over a declared
    range. Built *alongside* v1.3 rather than replacing it, and carried by
    :class:`omi.proposed.declaration.ExtendedDeclaration`.

    Marked "proposed" because **no specification issues it**. It was called
    `PROPOSED_V1_4` until ADR-067; that name attached a version number to an unissued
    carrier, and the number it borrowed is reserved for whatever specification is
    actually issued next."""

    PROPOSED_DECISION_EXTENSION = "proposed-decision-extension"
    """The proposed **decision** extension (ADR-048 – ADR-060): the coupled-quantity,
    role and attainability declarations, plus the statement of which decision the chain
    supports. Built *alongside* the constitutive extension by the same composition
    discipline (:class:`omi.proposed.decision.DecisionExtendedDeclaration`; ADR-059).

    A third member rather than a re-use of
    :attr:`PROPOSED_CONSTITUTIVE_EXTENSION`, because `docs/V1.4-EDITS.md` E-35's
    finding is that a level name is not self-describing without the target it is
    claimed against — and that argument does not stop applying at the second
    extension. A domain declaring the decision refinements is not making a
    constitutive-extension claim. Named for its purpose rather than `PROPOSED_V1_5`
    per ADR-067."""


class InvariantKind(Enum):
    """Item 6's invariants are declared as free-text names (ADR-016); this is
    the minimum structural type ADR-034 (docs/DECISIONS.md, superseding
    ADR-003) requires before two domains' invariant *lists* can be compared
    for more than incidental string difference: whether each declared
    invariant is a conservation law or a monotonicity constraint (Spec §5's
    two hard-constraint categories that apply here — see
    :mod:`omi.constraints`)."""

    CONSERVATION = auto()
    MONOTONICITY = auto()


def classify_invariant(name: str) -> InvariantKind:
    """Classify a declared invariant's name by kind (ADR-034).

    A keyword heuristic on the declared name for Core §4 item 6's
    invariants, not a claim about the invariant's semantics beyond what
    Spec §2.2's two relevant hard-constraint categories already require
    domains to state: every declared invariant here is either a
    conservation law or a monotonicity constraint. A name matching neither
    keyword is refused rather than guessed at — this is a naming-convention
    check, not a Specification gap, so it raises :class:`ValueError`, not
    :class:`~omi.gaps.NotSpecified`.
    """
    lowered = name.lower()
    if "conserv" in lowered:
        return InvariantKind.CONSERVATION
    if "monoton" in lowered:
        return InvariantKind.MONOTONICITY
    raise ValueError(
        f"invariant {name!r} names neither a conservation law nor a monotonicity "
        "constraint by its own declared name (expected 'conserv...' or 'monoton...' "
        "to appear in it) — classify_invariant refuses to guess"
    )


def diff(a: InstantiationDeclaration, b: InstantiationDeclaration) -> dict[str, bool]:
    """Per-item: whether *a* and *b* declare something different (Core §4:
    interface declarations are "comparative"; ADR-016).

    Mechanical equality per field — every field is either directly
    comparable data (:class:`~omi.state.StateSchema`, a string, a tuple of
    strings), so "different" needs no domain-specific judgement call.

    One additional key, ``"invariants_structural"`` (ADR-034), compares the
    *multiset of invariant kinds* (:func:`classify_invariant`) rather than
    the literal declared names: two domains that each declare one
    conservation law and one monotonicity constraint, under different
    names, are not structurally inverted on item 6 even though the literal
    ``"invariants"`` key above reports them as different. Naming alone must
    not be mistaken for a structural inversion.
    """
    result = {f.name: getattr(a, f.name) != getattr(b, f.name) for f in fields(InstantiationDeclaration)}
    a_kinds = sorted(classify_invariant(name).name for name in a.invariants)
    b_kinds = sorted(classify_invariant(name).name for name in b.invariants)
    result["invariants_structural"] = a_kinds != b_kinds
    return result


_SCOPE_FEATURES: tuple[str, ...] = (
    "control_axis",
    "hidden_state",
    "structure_mediated_response",
    "recurring_decision_under_uncertainty",
)
"""Core §1.1's three scope features, plus the fourth ADR-048 proposes for the decision
extension. Named here once so :class:`ScopeDeclaration` and its tests cannot drift apart
on what the declarable set is (`docs/V1.4-EDITS.md` E-44)."""


@dataclass(frozen=True)
class ScopeDeclaration:
    """Whether a domain evidences Core §1.1's scope test, and where it stops mattering
    (`docs/V1.4-EDITS.md` E-44, E-52; ADR-069).

    **Two findings, one object, because both are "the interface has nothing to say
    about this."** E-44: Core §1.1 states a scope test and Core §4 states a
    declaration, and nothing connects them — no item asks a domain to assert it is in
    scope, so a domain that satisfies the test and a domain that does not produce
    identical declarations. ADR-048 read flagship's and contrast's declarations for
    scope evidence, found none, and concluded neither was in scope for the decision
    extension; **both are**, and the declarations simply could not say so. E-52: none
    of the seven items hosts the criterion under which an instantiation stops being
    the right description — Core §3.9's "declare out of scope" reached *during*
    operation rather than at design time.

    **Not folded into item 6.** An invariant is a conservation statement the chain
    *satisfies*; a scope-exit criterion is a decision about when to stop believing the
    chain satisfies anything. Core §4's own text distinguishes the two, and hosting a
    stopping rule among conservation laws would let a domain claim an end-of-life
    criterion by listing a conservation law — the satisfiable-without-the-property
    shape `docs/V1.4-EDITS.md` §4 documents nine times over.

    **Additive, not a restructuring of any of Core §4's seven items** — this is a
    field on the decision extension, not on :class:`InstantiationDeclaration`, so
    `diff()` and every comparability result it has produced are untouched by this
    class existing (ADR-069's own note on why C, D and E land here rather than on the
    seven-item carrier).
    """

    control_axis_evidence: str = ""
    """One-line justification naming which declared item evidences a control axis
    (E-44's table: item 2, control space — "strong but implicit"). Empty means
    undeclared, not absent; Core §1.1's test may still hold, the declaration simply
    does not say so."""
    hidden_state_evidence: str = ""
    """Ditto for internal state not directly observable (E-44's table: items 1 and
    5, jointly — "weak")."""
    structure_mediated_response_evidence: str = ""
    """Ditto for responses mediated by structure (E-44's table: item 4 — "weak", a
    Type-0 readout is consistent with mediation and does not establish it)."""
    recurring_decision_under_uncertainty_evidence: str = ""
    """ADR-048's proposed fourth feature, specific to the decision extension. E-44's
    finding is sharpest here: this feature "has no interface item at all, not even a
    weak one" under v1.3's seven items alone."""
    scope_exit_criterion: str = ""
    """E-52's item: the declared bound — on a readout value, on accumulated state, or
    on measured residual deficit — beyond which this instantiation MUST be reported
    out of scope rather than evaluated.

    **Empty is a meaningful value, not a missing one**, per E-52's own proposed
    wording: "A domain that declares no scope-exit criterion is claiming its
    instantiation is valid without limit." So this field is never required to be
    non-empty; :meth:`declares_scope_exit` reports which case a reader is looking at
    without editorialising on whether that is acceptable."""

    def evidenced_features(self) -> tuple[str, ...]:
        """Which of Core §1.1's scope features carry a non-empty justification
        (E-44's own proposed wording: "MUST be able to point... to the item that
        evidences it"). Sorted for determinism, not for any priority among them."""
        evidence = {
            "control_axis": self.control_axis_evidence,
            "hidden_state": self.hidden_state_evidence,
            "structure_mediated_response": self.structure_mediated_response_evidence,
            "recurring_decision_under_uncertainty": self.recurring_decision_under_uncertainty_evidence,
        }
        return tuple(sorted(name for name in _SCOPE_FEATURES if evidence[name].strip()))

    def undeclared_features(self) -> tuple[str, ...]:
        """The complement of :meth:`evidenced_features` against Core §1.1's scope
        features — what E-44's finding calls a domain "telling you something" by
        silence, in the same sense an unfilled Core §4 item 3 or item 6 does."""
        evidenced = set(self.evidenced_features())
        return tuple(name for name in _SCOPE_FEATURES if name not in evidenced)

    @property
    def declares_scope_exit(self) -> bool:
        """Whether :attr:`scope_exit_criterion` is non-empty (Core §3.9's "declare
        out of scope"). `False` is not an error — it is the claim E-52's proposed
        wording names: unlimited validity."""
        return bool(self.scope_exit_criterion.strip())
