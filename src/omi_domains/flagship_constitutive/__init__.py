"""The constitutive variant of the flagship chain — a **sibling** of
`omi_domains.flagship`, not a replacement (M11.3; ADR-044, docs/DECISIONS.md).

`omi_domains.flagship` is untouched, which preserves every M0-M9 oracle result
that used it. This package declares the same Core §4 seven items, so the two are
machine-diffable and the diff comes out near-identical except for item 6 and the
constitutive declaration — which is what makes the comparison a controlled
measurement of what the extension adds rather than of two unrelated declarations.

**Everything here is the proposed constitutive extension** (Spec §9.1's level claim needs a version —
`docs/V1.4-EDITS.md` E-35): conformance reports built from this domain carry
`SpecificationVersion.PROPOSED_CONSTITUTIVE_EXTENSION`, so its level claims can never be mixed with
flagship's v1.3 ones.
"""
