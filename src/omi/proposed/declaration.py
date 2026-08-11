"""The proposed constitutive-extension declaration: a wrapper around Core §4's seven items.

Cites Core §4 (the seven-item instantiation interface) and Spec §9.1 (the
conformance level table whose version a claim must state). ADR-042
(docs/DECISIONS.md) fixes the composition-over-modification choice this module
exists to realise; `docs/V1.4-EDITS.md` E-35 is the finding that motivated it,
and E-32 is the finding whose proposed category M11.2 will add here.
"""

from __future__ import annotations

from dataclasses import dataclass

from omi.interface import InstantiationDeclaration, SpecificationVersion
from omi.proposed.constitutive import ConstitutiveForm


@dataclass(frozen=True)
class ExtendedDeclaration:
    """A constitutive-extension instantiation declaration, expressed as a v1.3
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
    - Two domains declared in this shape — one v1.3, one constitutive-extension — differ
      *only* in what the extension adds, which is what makes a diff between them
      a controlled measurement of the extension itself rather than of two
      unrelated declarations (ADR-044's variant domain relies on this).

    **The extension was introduced empty at M11.1 and gained its first field at
    M11.2.** That ordering was the point rather than premature abstraction: the
    diff-preservation property above was established on an *empty* extension, so
    when :attr:`constitutive_forms` arrived the same check re-ran and any
    disturbance to Core §4's comparability was attributable to that addition
    alone. A wrapper introduced together with its content could not separate the
    two, and the property is re-checked on every later addition for the same
    reason.
    """

    v13_core: InstantiationDeclaration
    """The unmodified Core §4 seven-item declaration. Frozen and shared, not
    copied: this is the same object a v1.3 domain declares."""

    constitutive_forms: tuple[ConstitutiveForm, ...] = ()
    """Core §4 item 6d: declared constitutive forms (ADR-043; Spec §2.2's
    proposed sixth hard-constraint category; `docs/V1.4-EDITS.md` E-32).

    Defaults to empty, and **an empty declaration is legal and meaningful**
    rather than an omission: per E-32's proposed wording, "a domain with no
    established constitutive form for a given operator MUST declare 6d empty for
    it; an empty declaration is legal and required, and is itself the statement
    that operators for that step carry generic structure only and should not be
    expected to extrapolate in form." A default of ``()`` therefore encodes a
    claim rather than an absence of one — which is the opposite of the reasoning
    that made `specification_version` a *required* field, and the difference is
    that here the empty case has a defensible meaning and there it does not."""

    @property
    def specification_version(self) -> SpecificationVersion:
        """Always :attr:`~omi.interface.SpecificationVersion.PROPOSED_CONSTITUTIVE_EXTENSION`
        (Spec §9.1's level claim needs a version — `docs/V1.4-EDITS.md` E-35).

        A read-only property rather than a field, so it cannot be constructed as
        `V1_3`: a declaration carrying the extension is not a v1.3 declaration,
        and making that unrepresentable is cheaper than checking for it.
        """
        return SpecificationVersion.PROPOSED_CONSTITUTIVE_EXTENSION
