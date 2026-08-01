"""Core §4 item 6, split by role (proposed-v1.4; ADR-043, docs/DECISIONS.md).

Cites Core §4 item 6 (invariants available as hard constraints and as
reachability certificates), Spec §2.2 (the five hard-constraint categories) and
Spec §7.1 (the candidate kinds a reachability certificate is drawn from).
`docs/V1.4-EDITS.md` E-32 is the finding: item 6 serves *two* roles with
different mathematical requirements while naming one undifferentiated list, and
it omits one of the three candidate kinds Spec §7.1 itself draws from.

**Why the split rather than a sub-item.** A reachability certificate must be a
scalar functional of state with a provable per-step accumulation bound (Spec
§7.1's `Φ(s_{k+1}) ≤ Φ(s_k) + c(u_k)`). A declared functional form for an
operator is not that, and cannot discharge Core §5's output contract. Adding one
to an undifferentiated item 6 would therefore silently widen the pool §7.1 draws
from, which is why E-32 proposes role-scoping instead of extension.

**v1.3's classifier is untouched.** `omi.interface.classify_invariant` continues
to refuse anything that is neither a conservation law nor a monotone functional,
which is correct under v1.3 and is the evidence E-32 rests on. This module is
the proposed-v1.4 replacement, not a relaxation of it.
"""

from __future__ import annotations

from enum import Enum


class InvariantRole(Enum):
    """The two roles Core §4 item 6 currently conflates (Spec §2.2 and Spec
    §7.1; `docs/V1.4-EDITS.md` E-32)."""

    HARD_CONSTRAINT = "hard_constraint"
    """Usable as an architectural constraint (→ Spec §2.2, `omi.constraints`)."""

    REACHABILITY_CERTIFICATE = "reachability_certificate"
    """Usable as a `Φ` with a provable per-step bound (→ Spec §7.1, Core §5,
    `omi.inverse.ReachabilityCertificate`)."""


class InvariantSubItem(Enum):
    """Core §4 item 6's proposed role-scoped sub-items (ADR-043; E-32's proposed
    wording). Values are the sub-item labels the proposed Core text uses, so a
    declaration and the framework document can be read against each other."""

    CONSERVATION = "6a"
    """A conservation balance. Both roles."""

    MONOTONICITY = "6b"
    """A monotone functional. Both roles."""

    EQUILIBRIUM_LIMITED_FRACTION = "6c"
    """An equilibrium-limited fraction at attainable driving levels. Certificate
    role always; hard-constraint role where the bound is structural. Spec §7.1
    names this kind and item 6 never did, which is half of E-32's finding — and
    v1.3's `omi.interface.classify_invariant` refuses it for exactly that
    reason, correctly."""

    CONSTITUTIVE_FORM = "6d"
    """A declared constitutive form. **Hard-constraint role only** (Spec §2.2's
    proposed sixth category); never a certificate."""


_ROLES: dict[InvariantSubItem, frozenset[InvariantRole]] = {
    InvariantSubItem.CONSERVATION: frozenset(InvariantRole),
    InvariantSubItem.MONOTONICITY: frozenset(InvariantRole),
    InvariantSubItem.EQUILIBRIUM_LIMITED_FRACTION: frozenset(InvariantRole),
    InvariantSubItem.CONSTITUTIVE_FORM: frozenset({InvariantRole.HARD_CONSTRAINT}),
}


class CertificateRoleRefused(Exception):
    """Raised when a sub-item is offered for the reachability-certificate role it
    cannot serve (Core §5's output contract; Spec §7.1; `docs/V1.4-EDITS.md`
    E-32).

    A distinct exception rather than a `ValueError` because the refusal is the
    mechanism E-32's proposed split exists to provide, and it should be greppable
    and catchable as such. It is *not* an `omi.gaps.NotSpecified`: the
    Specification is not silent here, it is being enforced.
    """

    def __init__(self, sub_item: InvariantSubItem) -> None:
        self.sub_item = sub_item
        super().__init__(
            f"interface item {sub_item.value} ({sub_item.name}) cannot serve the "
            "reachability-certificate role: Spec §7.1 requires a scalar functional of "
            "state with a provable per-step accumulation bound, and a declared "
            "constitutive form is a functional form for an operator, which cannot "
            "discharge Core §5's output contract (docs/V1.4-EDITS.md E-32)"
        )


def roles_for(sub_item: InvariantSubItem) -> frozenset[InvariantRole]:
    """The roles *sub_item* may serve (Core §4 item 6, role-scoped per ADR-043;
    Spec §2.2 and Spec §7.1)."""
    return _ROLES[sub_item]


def certificate_eligible(sub_item: InvariantSubItem) -> bool:
    """Whether *sub_item* may be drawn on for a reachability certificate (Spec
    §7.1's sourcing sentence, which E-32 proposes should read "items 6a–6c"
    rather than "item 6")."""
    return InvariantRole.REACHABILITY_CERTIFICATE in roles_for(sub_item)


def assert_certificate_eligible(sub_item: InvariantSubItem) -> None:
    """Raise :class:`CertificateRoleRefused` unless *sub_item* may serve the
    certificate role (Core §5; Spec §7.1).

    Call this at the point a certificate is *sourced* from a declaration, not
    where one is constructed: `omi.inverse.ReachabilityCertificate` is already
    typed as the sound `Φ(s)=w·s` artefact (E-17), so the gap this closes is
    upstream of it — choosing which declared invariants are eligible to become
    one at all.
    """
    if not certificate_eligible(sub_item):
        raise CertificateRoleRefused(sub_item)
