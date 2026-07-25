"""Public API of the OMI v1.3 reference implementation.

Cites Core §3.9: the framework's stance that refusal at a gap is more
credible than an invented answer. M0 is scaffolding and discipline only
(docs/ROADMAP.md M0; CLAUDE.md §10) — no framework module (``state.py``,
``operators.py``, ...) exists yet, so the only export is the gap-discipline
primitive that everything downstream will raise.
"""

from omi.gaps import NotSpecified

__all__ = ["NotSpecified"]
