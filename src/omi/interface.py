"""The instantiation interface (Core §4), expressed as a shared, diffable declaration
— **eight items as this repository now declares it**, not the seven Core §4 issues.

Cites Core §4: "Generality is a claim, and claims require a mechanism... a
domain enters the framework by supplying seven items." ADR-016
(docs/DECISIONS.md) fixes the declaration's shape here in domain-neutral
code; the *content* of a declaration is supplied by each domain in
``omi_domains/*/interface.py``.

**The count moved, deliberately and visibly (ADR-071).** Core §4 as issued in v1.3
names seven items and this module carried exactly seven until the arity redesign's
Stage 2. `docs/V1.4-EDITS.md` E-46's finding is that item 1's charter covers two
structurally different declarations — what the material *is*, and what the operator
family is *parameterised by* — and distinguishes them nowhere, so item 1 is split
here into **1a** (:attr:`InstantiationDeclaration.state_schema`) and **1b**
(:attr:`InstantiationDeclaration.declared_parameters`). Items 2–7 are untouched.

Unlike the constitutive and decision extensions (ADR-042, ADR-059), which compose
*around* this carrier and leave it byte-identical to v1.3's, this is a **modification
of the carrier itself**, and ADR-071 records why that was chosen over another wrapper:
a wrapper would leave a parameter declarable in two places at once, which is the very
ambiguity the split exists to remove. The cost is stated there too — an
`InstantiationDeclaration` is no longer a literal v1.3 seven-item object, so
:attr:`SpecificationVersion.V1_3` now names v1.3's *level table* rather than v1.3's
item list, and the audit baseline moves to a new generation
(`audit/baselines/`, ADR-069).
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum, auto

from omi.state import StateSchema


@dataclass(frozen=True)
class ParameterRole:
    """One quantity that **indexes the operator family** without being transported by
    any operator — item 1b's occupant (`docs/V1.4-EDITS.md` E-46, E-29; ADR-071).

    **The four-property test that puts a quantity here rather than in item 1a** is
    E-46's own table, and it is the whole content of the split. A slot occupant
    (item 1a) evolves under some operator, is assimilated from observations, and
    carries a per-particle value in `𝒫(𝒮)`; it answers *what is the material*. A
    parameter does none of the three and answers *which member of the operator family
    this is*. Core §6.2 already uses the word — "how much of an operator is
    composition-conditional versus composition-**parameterised**" — while Core §4
    supplied nowhere to declare one, which is E-29's finding one level up.

    **Not a fifth slot** (E-29 is explicit that a fifth slot is the wrong fix): a slot
    would subject a parameter to every claim the framework makes about state —
    pushforward under evolution, Axiom S sufficiency, erasure, assimilation — all
    vacuous or misleading for a quantity nothing transports.
    """

    name: str
    """The quantity's name, in the domain's own words. MUST NOT collide with a slot
    occupant name in item 1a unless :attr:`also_state_in_regions` says so — enforced
    by :meth:`InstantiationDeclaration.__post_init__`."""

    indexes: tuple[str, ...]
    """Which operators (or operator families) this quantity indexes, by name. Required
    non-empty: a parameter that indexes nothing constrains nothing, and declaring it
    would be the satisfiable-without-the-property shape `docs/V1.4-EDITS.md` §4
    documents repeatedly. This is also the falsifiable half of the declaration — a
    named operator either does or does not vary with this quantity."""

    justification: str
    """Why this is a parameter and not a slot occupant, against the four-property test
    above. Required non-empty, on the same discipline ADR-043 applies to a validity
    bound's ``regime``: an unexplained declaration is an assertion."""

    constant_over: tuple[str, ...] = ()
    """The declared regions over which the quantity is asserted constant (E-46's "the
    region over which it is asserted constant"). **Empty means constant over the whole
    chain**, which is a meaningful declaration rather than a missing one — the
    ordinary case for a grade, a design, or a feedstock batch."""

    descriptor_basis: tuple[str, ...] = ()
    """Named functionals the quantity is declared in, if any (ADR-052)."""

    underlying_space: tuple[str, ...] = ()
    """The raw coordinates behind :attr:`descriptor_basis`. Required whenever a
    descriptor basis is declared, for ADR-052's reason: the claim "the operator depends
    on this only through these functionals" is falsifiable exactly by varying the
    underlying space at fixed descriptors, which needs both to be declared."""

    also_state_in_regions: tuple[str, ...] = ()
    """The regions, if any, where this same physical quantity **is** a slot occupant.

    E-46's last clause made explicit: "an implementation that needs both for one
    physical quantity in different regions MUST declare it twice, once per region, and
    **say so**." Carbon is a parameter in the bulk and a depleted state variable in a
    decarburising surface layer simultaneously (ADR-051), so the split must permit the
    dual declaration — but only when it is stated here, so the case that is legitimate
    is distinguishable from the silent conflation item 1 currently allows."""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a declared parameter must be named")
        if not self.indexes:
            raise ValueError(
                f"parameter {self.name!r} indexes no operator, so it parameterises nothing: "
                "item 1b's content is precisely a quantity that indexes the operator family "
                "(docs/V1.4-EDITS.md E-46), and a parameter indexing nothing is not that"
            )
        if not self.justification.strip():
            raise ValueError(
                f"parameter {self.name!r} declares no justification: E-46's four-property test "
                "(does not evolve, is not assimilated, carries no per-particle value, answers "
                "'which operator family') is what distinguishes item 1b from item 1a, and a "
                "declaration that does not state its side of it is an assertion (ADR-043's "
                "discipline, applied here)"
            )
        if self.descriptor_basis and not self.underlying_space:
            raise ValueError(
                f"parameter {self.name!r} declares a descriptor basis with no underlying space: "
                "a descriptor without its ground truth cannot be held out against (ADR-052), so "
                "the claim 'the operator depends on chemistry only through these functionals' "
                "would not be falsifiable"
            )


@dataclass(frozen=True)
class InstantiationDeclaration:
    """Core §4's items, in the Core's own order, as one comparable object
    (ADR-016) — so two domains declared in this shape can be diffed
    mechanically (Core §4: "it is comparative... which is what converts a
    collection of examples into evidence of generality").

    **Eight items, not v1.3's seven** (ADR-071): item 1 is split into 1a and 1b per
    `docs/V1.4-EDITS.md` E-46. See this module's docstring for what that costs.
    :data:`INTERFACE_ITEMS` is the item list as data, and is the single place the
    numbering lives — read it rather than counting fields by hand.
    """

    state_schema: StateSchema
    """Item **1a**: occupants of each slot (components/dimensions live on the
    schema itself); which slots are empty is queryable via
    :meth:`~omi.state.StateSchema.is_empty`.

    Was item 1 entire until ADR-071. Its charter is now *only* what the material is —
    every occupant here is a quantity some operator transports."""

    declared_parameters: tuple[ParameterRole, ...]
    """Item **1b**: every quantity that indexes the operator family without being
    transported by any operator (`docs/V1.4-EDITS.md` E-46, E-29; ADR-071).

    **Required with no default, deliberately**, on the same reasoning ADR-042 gives for
    :attr:`~omi.conformance.ConformanceInputs.specification_version`: a default would let
    a domain that *has* an operator-family index silently declare none, which is exactly
    the omission E-46 found item 1 unable to surface. An empty tuple is a legal and
    meaningful declaration — "this domain declares no operator-family index" — and it is
    a positive claim a reader can disagree with, rather than a field nobody filled in."""

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

    def __post_init__(self) -> None:
        """Enforce E-46's mutual-exclusion clause between items 1a and 1b (ADR-071).

        **This check is why the split removes an ambiguity rather than relocating it.**
        E-46's proposed wording is explicit: "A quantity declared here MUST NOT appear as
        a slot occupant in item 1, and a quantity in item 1 MUST NOT be declared constant
        here" — with one stated exception, the same quantity holding both roles in
        different declared regions, which MUST be declared twice and *said so*. Without
        this check the eight-item interface would be strictly worse than the seven-item
        one it replaces: a domain could declare its parameterisation in either place, and
        `diff` would report two identical domains as different — E-46's own argument for
        why appending an item 8 would not have worked.
        """
        occupants = {name for _, name, _ in self.state_schema.components}
        seen: set[str] = set()
        for parameter in self.declared_parameters:
            if parameter.name in seen:
                raise ValueError(
                    f"item 1b declares {parameter.name!r} twice: one declaration per quantity, "
                    "with regions named on it (ParameterRole.constant_over), not one entry per region"
                )
            seen.add(parameter.name)
            if parameter.name in occupants and not parameter.also_state_in_regions:
                raise ValueError(
                    f"{parameter.name!r} is declared both as a slot occupant (item 1a) and as an "
                    "operator-family parameter (item 1b), with no regions named. E-46 permits one "
                    "physical quantity to hold both roles in different declared regions, but "
                    "requires the dual declaration to SAY SO: set "
                    "ParameterRole.also_state_in_regions to the regions where it is state. An "
                    "undeclared collision is the silent conflation the item-1 split exists to "
                    "remove (docs/V1.4-EDITS.md E-46; ADR-071)"
                )


CORE_7_2_ROWS: tuple[str, ...] = (
    "Erasure operators",
    "Observation suite",
    "Dominant slot",
    "Control axis",
    "Tier structure",
    "Class B",
    "Nonlocal slot ν",
)
"""The row labels of Core §7.2's published comparison table, as data (`docs/V1.4-EDITS.md`
E-01; ADR-034, ADR-071).

**Seven rows, and that number is a fact about the issued v1.3 text, not about this
interface.** §7.2's table compares the flagship and contrast domains row by row; E-01's
finding is that its seven rows do not correspond one-to-one with Core §4's items — two
rows both name the state schema, and some items get no row at all. Kept here rather than
in a test so the mapping in :data:`INTERFACE_ITEMS` and the published table it is mapped
against cannot drift apart in different files (E-01 as a standing obligation rather than a
hand-written literal)."""


@dataclass(frozen=True)
class InterfaceItem:
    """One item of the instantiation interface (Core §4), as data (ADR-071).

    Exists so the item list has exactly one authority. Before ADR-071 the item numbering
    lived in prose, the §7.2 mapping lived as a hand-written dict inside
    `tests/test_interface_diff.py`, and the count "seven" was asserted as a literal — so
    changing the interface left every one of them stale with nothing noticing, which is
    `docs/V1.4-EDITS.md` E-01 as a *presentation* defect. With the list as data, adding or
    re-chartering an item moves the derived mapping automatically and a new item with no
    §7.2 row is reported rather than silently absent."""

    number: str
    """The item's number in Core §4's ordering, as a string because the split makes
    ``"1a"``/``"1b"`` (ADR-071) as legitimate as ``"2"``."""

    field: str
    """The :class:`InstantiationDeclaration` field carrying it. Checked against
    ``dataclasses.fields`` — see :func:`interface_items_match_declaration`."""

    charter: str
    """What the item is for, in one line, paraphrasing Core §4's own text."""

    core_7_2_rows: tuple[str, ...] = ()
    """Which of :data:`CORE_7_2_ROWS` name this item. Empty means the published table has
    no row for it — which is itself E-01's finding and is *reported*, not treated as an
    error."""


INTERFACE_ITEMS: tuple[InterfaceItem, ...] = (
    InterfaceItem(
        number="1a",
        field="state_schema",
        charter="occupants of each slot (m, z, ν, Γ), with resolution limits, and which slots are empty",
        core_7_2_rows=("Dominant slot", "Nonlocal slot ν"),
    ),
    InterfaceItem(
        number="1b",
        field="declared_parameters",
        charter="every quantity that indexes the operator family without being transported by any operator",
    ),
    InterfaceItem(
        number="2",
        field="control_space",
        charter="𝒰 and 𝒰_adm, including whether a control inverse exists at all",
        core_7_2_rows=("Control axis",),
    ),
    InterfaceItem(
        number="3",
        field="erasure_inventory",
        charter="names of operators declared as erasures",
        core_7_2_rows=("Erasure operators",),
    ),
    InterfaceItem(
        number="4",
        field="readout_catalogue",
        charter="every target response, named with its type (0/1/2) and class (A/B)",
        core_7_2_rows=("Class B",),
    ),
    InterfaceItem(
        number="5",
        field="observation_suite",
        charter="available modalities",
        core_7_2_rows=("Observation suite",),
    ),
    InterfaceItem(
        number="6",
        field="invariants",
        charter="conservation laws and monotone functionals, as hard constraints and as reachability certificates",
    ),
    InterfaceItem(
        number="7",
        field="scale_structure",
        charter="where homogenisation is applied, between which scales, and the closure defect once measured",
        core_7_2_rows=("Tier structure",),
    ),
)
"""The interface's items, in Core §4's order, with item 1 split per ADR-071.

**Eight entries.** Item 6 keeps its two roles and its two categories exactly as v1.3 has
them — the item-6 split `docs/V1.4-EDITS.md` E-32 proposes is *not* part of this change
(ADR-046 records that the constitutive-form category is already carried outside the seven
items by :class:`omi.proposed.declaration.ExtendedDeclaration`)."""


def interface_items_match_declaration() -> bool:
    """Whether :data:`INTERFACE_ITEMS` covers exactly
    :class:`InstantiationDeclaration`'s fields, one entry each (Core §4; ADR-071).

    The consistency this whole scheme rests on: if a field is added to the declaration and
    not to the item list, the numbering, the charters and the §7.2 mapping are all silently
    wrong. Exposed as a function rather than asserted at import time so the failure is a
    test failure with a message, not an `ImportError` in unrelated code."""
    return [item.field for item in INTERFACE_ITEMS] == [f.name for f in fields(InstantiationDeclaration)]


def core_7_2_row_to_item() -> dict[str, str]:
    """Core §7.2's published rows mapped onto the interface items they name, **derived**
    from :data:`INTERFACE_ITEMS` rather than written down (`docs/V1.4-EDITS.md` E-01;
    ADR-034's mapping, ADR-071).

    Raises if a row in :data:`CORE_7_2_ROWS` is named by no item or by more than one:
    either is a defect in the mapping rather than a finding about the table, and guessing
    would reintroduce exactly the hand-maintained literal this replaces.
    """
    mapping: dict[str, str] = {}
    for item in INTERFACE_ITEMS:
        for row in item.core_7_2_rows:
            if row not in CORE_7_2_ROWS:
                raise ValueError(
                    f"item {item.number} claims Core §7.2 row {row!r}, which is not one of the "
                    f"published rows {CORE_7_2_ROWS}"
                )
            if row in mapping:
                raise ValueError(
                    f"Core §7.2 row {row!r} is claimed by both item {mapping[row]} and item "
                    f"{item.number}; a row names one item"
                )
            mapping[row] = item.number
    unclaimed = tuple(row for row in CORE_7_2_ROWS if row not in mapping)
    if unclaimed:
        raise ValueError(f"Core §7.2 rows named by no interface item: {unclaimed}")
    return mapping


def items_without_a_core_7_2_row() -> tuple[str, ...]:
    """Which Core §4 items the published Core §7.2 table has no row for (E-01; ADR-071).

    **This is E-01 converted from a presentation defect into a reported quantity.** The
    finding was that §7.2's seven rows cover fewer items than the interface declares; the
    number on each side of that sentence is now computed, so a change to either the table
    or the item list moves it instead of leaving a stale literal behind."""
    return tuple(item.number for item in INTERFACE_ITEMS if not item.core_7_2_rows)


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

    **Item 1b appears here as the ``"declared_parameters"`` key** (ADR-071), compared
    literally like every other item. No structural companion key is supplied for it, and
    that omission is deliberate: ``"invariants_structural"`` exists because ADR-034 had a
    *measurement* — two domains declaring the same invariant structure under different
    names — and no equivalent measurement exists for parameters yet. Inventing one would
    be asserting which parameter declarations count as structurally alike, which is a
    judgement no evidence here supports.
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
