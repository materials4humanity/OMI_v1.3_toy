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
    """Which version of Core and of the Specification a claim is made against
    (Spec §9.1; ADR-042, docs/DECISIONS.md).

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

    PROPOSED_V1_4 = "proposed-v1.4"
    """The proposed v1.4 interface extension (ADR-042 – ADR-045), built
    *alongside* v1.3 rather than replacing it. Marked "proposed" because no
    v1.4 document exists: this is a candidate extension carrying evidence, not
    a released specification."""


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
