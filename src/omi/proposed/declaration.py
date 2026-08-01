"""The proposed-v1.4 declaration: a wrapper around Core §4's seven items.

Cites Core §4 (the seven-item instantiation interface) and Spec §9.1 (the
conformance level table whose version a claim must state). ADR-042
(docs/DECISIONS.md) fixes the composition-over-modification choice this module
exists to realise; `docs/V1.4-EDITS.md` E-35 is the finding that motivated it,
and E-32 is the finding whose proposed category M11.2 will add here.
"""

from __future__ import annotations

from dataclasses import dataclass

from omi.interface import InstantiationDeclaration, SpecificationVersion


@dataclass(frozen=True)
class ProposedV14Declaration:
    """A proposed-v1.4 instantiation declaration, expressed as a v1.3
    declaration (Core §4's seven items) **plus** whatever the extension adds.

    **Composition, not modification** (ADR-042). The v1.3 declaration is held
    whole in :attr:`v13_core` rather than being reproduced field by field, which
    buys three properties that a modified or forked declaration type would not:

    - Core §4's `omi.interface.diff` and every test that calls it operate on
      :attr:`v13_core` unchanged, so v1.3's comparative evidence (Core §4: "it is
      comparative... which is what converts a collection of examples into
      evidence of generality") survives the extension **by construction** rather
      than by care.
    - No v1.3 field changes meaning, which is the property that keeps this
      repository's Spec §9.1 conformance results citable while a second version
      of the interface exists in the same tree.
    - Two domains declared in this shape — one v1.3, one proposed-v1.4 — differ
      *only* in what the extension adds, which is what makes a diff between them
      a controlled measurement of the extension itself rather than of two
      unrelated declarations (ADR-044's variant domain relies on this).

    **At M11.1 the extension is deliberately empty.** This class adds no fields
    to the seven items yet: M11.2 (ADR-043) adds the declared-constitutive-form
    category, and M11.3 (ADR-044) supplies a domain that fills it. Introducing
    the wrapper *before* it has content is the point rather than premature
    abstraction — it establishes the diff-preservation property on an empty
    extension, so that after each later addition the same check re-runs and any
    disturbance to Core §4's comparability is attributable to that addition
    alone. A wrapper introduced together with its content could not separate the
    two.
    """

    v13_core: InstantiationDeclaration
    """The unmodified Core §4 seven-item declaration. Frozen and shared, not
    copied: this is the same object a v1.3 domain declares."""

    @property
    def specification_version(self) -> SpecificationVersion:
        """Always :attr:`~omi.interface.SpecificationVersion.PROPOSED_V1_4`
        (Spec §9.1's level claim needs a version — `docs/V1.4-EDITS.md` E-35).

        A read-only property rather than a field, so it cannot be constructed as
        `V1_3`: a declaration carrying the extension is not a v1.3 declaration,
        and making that unrepresentable is cheaper than checking for it.
        """
        return SpecificationVersion.PROPOSED_V1_4
