"""Interface-only domain sketches (Spec §11.4, Core §7.3 [Pass D], ROADMAP
M10.1) — evidence that the instantiation interface (Core §4) is
fillable outside `flagship`/`contrast`.

ADR-038 (docs/DECISIONS.md) fixes this package's shape: each module here
exports exactly a ``StateSchema`` and an ``InstantiationDeclaration`` (Core
§4's items) and nothing else — no ``operators.py``, ``readouts.py``,
or ``build.py``. A sketch is a declaration, deliberately not a domain; the
prose "one page" for each lives in ``docs/SKETCHES.md``, in Core §4 order.
"""
