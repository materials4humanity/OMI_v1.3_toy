"""Refusal machinery for procedures the Specification does not derive.

Cites Core §3.9: "A framework that knows when to refuse is more credible than
one that always answers." This module is the code-level enforcement of that
stance (CLAUDE.md §4, ADR-005 in docs/DECISIONS.md): reaching an unspecified
procedure raises :class:`NotSpecified` rather than guessing.
"""

from __future__ import annotations

import re
from pathlib import Path

_ID_ROW = re.compile(r"^\|\s*([A-Za-z][\w.\-]*)\s*\|")
_PART_HEADING = re.compile(r"^##\s+Part\s+([IVX]+)\b")
_NON_ID_FIRST_VALUES = frozenset({"id", "---"})


def _find_repo_root(start: Path) -> Path:
    """Search upward from *start* for the directory containing docs/COVERAGE.md.

    Cites Core §3.9 (module docstring); this is project tooling rather than a
    framework procedure. ADR-010 (docs/DECISIONS.md) records why the registry
    parses the document directly instead of duplicating its table.
    """
    for candidate in (start, *start.parents):
        if (candidate / "docs" / "COVERAGE.md").is_file():
            return candidate
    raise FileNotFoundError(
        f"could not locate docs/COVERAGE.md above {start} — "
        "the gap registry cannot be built without it"
    )


def _parse_coverage_ids(text: str) -> frozenset[str]:
    """Extract every id in the first column of a COVERAGE.md table row.

    Cites Core §3.9 (module docstring). Restricted to Part I and Part II,
    the only sections whose first table column is a stable id (ADR-010,
    docs/DECISIONS.md) — Part III and Part IV are prose and would otherwise
    contaminate the id set with heading fragments.
    """
    ids: set[str] = set()
    in_id_part = False
    for line in text.splitlines():
        heading = _PART_HEADING.match(line)
        if heading:
            in_id_part = heading.group(1) in ("I", "II")
            continue
        if not in_id_part:
            continue
        match = _ID_ROW.match(line)
        if not match:
            continue
        candidate = match.group(1)
        if candidate in _NON_ID_FIRST_VALUES or set(candidate) == {"-"}:
            continue
        ids.add(candidate)
    return frozenset(ids)


_registry_cache: frozenset[str] | None = None


def known_gap_ids() -> frozenset[str]:
    """Return every id declared in docs/COVERAGE.md's gap register.

    Cites Core §3.9: refusal at a gap must cite a real row, so callers (chiefly
    :class:`NotSpecified` and ``tests/lint/test_gap_citations.py``) can
    validate against this. Parses ``docs/COVERAGE.md`` directly rather than
    duplicating its table in Python (docs/ROADMAP.md M0; ADR-010).
    """
    global _registry_cache
    if _registry_cache is None:
        root = _find_repo_root(Path(__file__).resolve())
        text = (root / "docs" / "COVERAGE.md").read_text(encoding="utf-8")
        _registry_cache = _parse_coverage_ids(text)
    return _registry_cache


class NotSpecified(Exception):
    """Raised when code reaches a procedure the Specification does not derive.

    Cites Core §3.9: the framework's own position is that refusing is more
    credible than answering badly (ADR-005, docs/DECISIONS.md), and this
    exception is that position enforced in code. It carries the id of the
    corresponding row in ``docs/COVERAGE.md``, the framework section the gap
    lives in, and a short statement of what is missing.

    There are exactly three legal responses to reaching a gap (CLAUDE.md §4),
    and the exception message states all three so a reader is never left to
    guess at them:

      1. **Refuse.** Accept this exception and stop here — always acceptable.
      2. **Decide.** Write an ADR in ``docs/DECISIONS.md`` declaring a choice,
         then implement against it.
      3. **Escalate.** If the gap needs framework-level resolution rather than
         an implementation choice, record it as an open question in
         ``docs/DECISIONS.md`` and stop.
    """

    def __init__(self, coverage_id: str, section: str, missing: str) -> None:
        known = known_gap_ids()
        if coverage_id not in known:
            raise ValueError(
                f"{coverage_id!r} is not a row id in docs/COVERAGE.md; "
                "NotSpecified must cite a live id "
                "(see tests/lint/test_gap_citations.py)"
            )
        self.coverage_id = coverage_id
        self.section = section
        self.missing = missing
        message = (
            f"{section} ({coverage_id}) is not specified: {missing}\n"
            "\n"
            "Three legal moves at a gap (CLAUDE.md §4):\n"
            "  1. Refuse — accept this and stop here; always acceptable.\n"
            "  2. Decide — write an ADR in docs/DECISIONS.md, then implement "
            "the declared choice.\n"
            "  3. Escalate — record an open question in docs/DECISIONS.md "
            "if this needs framework-level resolution.\n"
            f"See docs/COVERAGE.md, row {coverage_id}, for the gap's status."
        )
        super().__init__(message)
