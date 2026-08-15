"""The proposed constitutive-form interface extension, built alongside v1.3 rather than
replacing it (Core §4's items; ADR-042, docs/DECISIONS.md).

**Nothing in this package is part of OMI v1.3.** Every conformance result,
oracle and audit finding this repository produced through M10 is a v1.3 result
(Spec §9.1), and the extension carries evidence for a candidate revision rather
than restating them. The boundary is enforced by two mechanisms, neither of
which is this directory:

1. **Versioned claims** — `omi.conformance.ConformanceReport` carries a required
   `omi.interface.SpecificationVersion`, and `omi.conformance.compare_reports`
   refuses to compare across versions (`docs/V1.4-EDITS.md` E-35).
2. **Composition, not modification** — :class:`~omi.proposed.declaration.ExtendedDeclaration`
   *wraps* a v1.3 `omi.interface.InstantiationDeclaration` and projects back to
   it, so v1.3's `omi.interface.diff` and every test calling it are untouched by
   construction.

This package's location is a readability choice and explicitly **not** the
guarantee (ADR-042 records why an import-direction lint was considered and
declined). A reader wanting to know whether a result is v1.3 should read the
result's own declared version, not the import path that produced it.
"""

from __future__ import annotations

from omi.proposed.constitutive import (
    UNBOUNDED,
    BoundEdge,
    ChainExtrapolationReport,
    ConstitutiveForm,
    ConstitutivelyConstrained,
    EdgeKind,
    ExtrapolationReport,
    FormKind,
    Unbounded,
    ValidityAction,
    ValidityBound,
    ValidityRange,
    ValiditySpace,
    worst_extrapolation,
)
from omi.proposed.declaration import ExtendedDeclaration
from omi.proposed.holdout import (
    HoldOutDiscriminationReport,
    HoldOutVerdict,
    check_hold_out_discriminates,
)
from omi.proposed.item6 import (
    CertificateRoleRefused,
    InvariantRole,
    InvariantSubItem,
    assert_certificate_eligible,
    certificate_eligible,
    roles_for,
)

__all__ = [
    "UNBOUNDED",
    "BoundEdge",
    "ChainExtrapolationReport",
    "CertificateRoleRefused",
    "ConstitutiveForm",
    "ConstitutivelyConstrained",
    "EdgeKind",
    "ExtrapolationReport",
    "FormKind",
    "HoldOutDiscriminationReport",
    "HoldOutVerdict",
    "InvariantRole",
    "InvariantSubItem",
    "ExtendedDeclaration",
    "Unbounded",
    "ValidityAction",
    "ValidityBound",
    "ValidityRange",
    "ValiditySpace",
    "assert_certificate_eligible",
    "check_hold_out_discriminates",
    "certificate_eligible",
    "roles_for",
    "worst_extrapolation",
]
