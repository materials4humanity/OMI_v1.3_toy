"""The constitutive variant's state schema (Core §4 item 1; M11.3, ADR-044).

**Deliberately the same object as `omi_domains.flagship`'s**, re-exported rather
than redefined. ADR-044 requires the two domains' v1.3-core declarations to differ
only in item 6 and the constitutive declaration, and item 1 is the state schema —
so sharing the object makes "item 1 is identical" true by construction rather than
by a comparison that could drift. The variant changes how components *evolve*
(`operators.py`), not what they are.
"""

from __future__ import annotations

from omi_domains.flagship.state import FLAGSHIP_SCHEMA

CONSTITUTIVE_SCHEMA = FLAGSHIP_SCHEMA
"""Core §4 item 1, shared with `omi_domains.flagship` exactly (see module
docstring)."""
