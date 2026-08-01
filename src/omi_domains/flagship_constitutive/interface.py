"""The constitutive variant's declaration (Core §4; M11.3, ADR-044).

Two objects, and the relationship between them is the finding:

- :data:`CONSTITUTIVE_V13_CORE` — the Core §4 seven items. **Byte-identical to
  `omi_domains.flagship`'s declaration**, and that is not laziness — see below.
- :data:`CONSTITUTIVE_DECLARATION` — that core wrapped in
  `omi.proposed.ProposedV14Declaration` with the five declared forms
  (`forms.py`) filling proposed item 6d.

**ADR-044 predicted the v1.3 diff would isolate item 6. Measured, the diff is
EMPTY, and that is the stronger result.** The ADR expected the two domains'
seven-item declarations to "come out near-identical except for item 6 and the
constitutive declaration." Attempting it showed both available roads are closed:

1. *Declare the forms inside item 6.* `omi.interface.classify_invariant` refuses
   any invariant name that is neither a conservation law nor a monotone functional
   — correctly, under v1.3's two categories — and `omi.interface.diff` calls it on
   every invariant of both declarations. So a domain that honestly names its
   declared forms in item 6 **cannot be diffed against any other domain at all**:
   `diff` raises. The comparative machinery Core §4 calls "what converts a
   collection of examples into evidence of generality" refuses the declaration.
2. *Declare them outside the seven items* — the road taken here. Then the two
   v1.3 cores are **identical in every item**, while the domains differ by five
   declared constitutive forms, a real Hall-Petch exponent in place of a
   hyperbolic surrogate, and kinetics for two components flagship never
   transports.

So v1.3's interface cannot see the difference between a domain with declared
constitutive forms and one without, in either direction: declaring it breaks the
diff, and not declaring it makes the diff blind. That is a measured consequence of
`docs/V1.4-EDITS.md` E-32, recorded there, and it is sharper than E-32's original
"no place to put it" — there is a place, and putting anything in it disables the
comparison.

What this does *not* claim: the variant is not a better instantiation of v1.3. It
is the same instantiation with kinetics substituted, and its conformance claims are
proposed-v1.4 (Spec §9.1; `docs/V1.4-EDITS.md` E-35).
"""

from __future__ import annotations

from dataclasses import fields

from omi.interface import InstantiationDeclaration
from omi.proposed import ProposedV14Declaration

from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship_constitutive.forms import DECLARED_FORMS

CONSTITUTIVE_V13_CORE = InstantiationDeclaration(
    **{f.name: getattr(FLAGSHIP_DECLARATION, f.name) for f in fields(InstantiationDeclaration)}
)
"""The v1.3-core declaration, constructed **from flagship's own declaration
object** field by field rather than restated (Core §4).

Built this way deliberately: it makes "the two v1.3 cores are identical" true by
construction and impossible to drift, so the emptiness of the diff is a property of
v1.3's expressive range rather than an artefact of two hand-written declarations
happening to agree. Every difference between the two domains lives in
:data:`CONSTITUTIVE_DECLARATION`'s extension, which is exactly where v1.3 has no
vocabulary — see the module docstring."""

CONSTITUTIVE_DECLARATION = ProposedV14Declaration(
    v13_core=CONSTITUTIVE_V13_CORE,
    constitutive_forms=DECLARED_FORMS,
)
"""The proposed-v1.4 declaration: the seven items plus item 6d (Core §4; ADR-043).
`.v13_core` projects back to the object above, so v1.3's `omi.interface.diff`
operates on it unchanged — and returns "no differences", which is the finding."""
