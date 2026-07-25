"""Vocabulary lint: src/omi/ must contain no domain vocabulary.

Enforces CLAUDE.md §5 invariant 3 and ADR-006 (docs/DECISIONS.md): domain
terms live in src/omi_domains/, never in src/omi/. The banned list is seeded
from docs/OMI-v1_3-Core.md Appendix B (the general <-> domain glossary, both
the flagship and contrast instance columns) plus the explicit examples
CLAUDE.md §5 itself names ("coil", "austenitisation", "coating", "steel",
"battery"), and obvious inflections of each.

Multi-word glossary entries (e.g. "processing line", "concentration
overpotential") are banned as literal phrases rather than split into their
individual words, to avoid flagging generic words ("current", "voltage",
"temperature") that are too common in legitimate non-domain code to ban
outright — ADR-006 says the list "grows as domains are added," and finer
splitting can happen then, driven by an actual collision rather than
speculatively.

"campaign" (Appendix B's flagship instance of "provenance group") is
deliberately *not* banned, despite appearing in that column: Spec §1 and
§8 use "campaign" as the framework's own generic term (e.g. "the
sufficiency campaign," "campaign design") throughout the very sections
src/omi/sufficiency.py implements. Banning it would block legitimate
citation of the Specification's own vocabulary — a real collision found
while implementing M4, not a hypothetical one, so it is recorded here
rather than silently worked around.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_OMI = REPO_ROOT / "src" / "omi"

# Seeded from docs/OMI-v1_3-Core.md Appendix B (flagship + contrast columns)
# and CLAUDE.md §5's explicit examples. ADR-006: grows as domains are added.
BANNED_TERMS: tuple[str, ...] = (
    # --- flagship instance column ---
    "coil", "coils",
    "heat",
    "processing line",
    "alloy family", "alloy", "alloys",
    "austenitisation", "austenitization", "austenitise", "austenitize",
    "recrystallisation", "recrystallization",
    "solutionising", "solutionizing", "solutionise", "solutionize",
    "ebsd", "apt",
    "pyrometry",
    "em sensing",
    "coating", "coatings",
    "oxide", "oxides",
    "sheared edge",
    "residual stress",
    "outer fibre under plunger", "outer fiber under plunger",
    # --- contrast instance column ---
    "cell", "cells",
    "manufacturing lot",
    "charger", "duty profile",
    "chemistry platform",
    "tomography",
    "cross-sectional microscopy",
    "terminal current", "surface temperature",
    "sei", "cei",
    "collector interface",
    "concentration overpotential",
    "separator-adjacent electrode surface",
    # --- CLAUDE.md §5 invariant 3's own explicit examples ---
    "steel", "steels",
    "battery", "batteries",
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    term: str
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: banned term {self.term!r} in: {self.text.strip()}"


_TERM_PATTERNS = [
    (
        term,
        re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])",
            re.IGNORECASE,
        ),
    )
    for term in BANNED_TERMS
]
# Note: boundaries are alnum-only (not \b), so a banned term embedded in a
# snake_case identifier — "coil_id", "id_coil" — is still caught; \b would
# miss it because "_" counts as a word character and creates no boundary.


def find_banned_terms(root: Path) -> list[Violation]:
    """Scan every ``*.py`` file under *root* for banned domain vocabulary.

    Reports file and line, per docs/ROADMAP.md M0. Comments and docstrings
    are scanned along with code, since a domain term leaking into a comment
    is exactly as much of a leak as one in an identifier.
    """
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            for term, pattern in _TERM_PATTERNS:
                if pattern.search(line):
                    violations.append(Violation(path, lineno, term, line))
    return violations


def test_real_source_has_no_domain_vocabulary() -> None:
    """The actual src/omi/ tree must be clean — the lint CI enforces."""
    violations = find_banned_terms(SRC_OMI)
    assert not violations, "domain vocabulary found under src/omi/:\n" + "\n".join(
        str(v) for v in violations
    )


def test_scanner_detects_a_planted_violation(tmp_path: Path) -> None:
    """Fail half of the demonstration: a planted term must be caught."""
    planted = tmp_path / "leaky.py"
    planted.write_text(
        "def process(item_id: str) -> int:\n"
        '    """Doc without a citation. Refers to a coil in passing."""\n'
        "    return len(item_id)\n"
    )
    violations = find_banned_terms(tmp_path)
    assert len(violations) == 1
    assert violations[0].term == "coil"
    assert violations[0].line == 2


def test_scanner_is_clean_once_violation_removed(tmp_path: Path) -> None:
    """Pass half of the demonstration: removing the term clears the lint."""
    cleaned = tmp_path / "leaky.py"
    cleaned.write_text(
        "def process(item_id: str) -> str:\n"
        '    """Doc without a citation."""\n'
        "    return item_id\n"
    )
    violations = find_banned_terms(tmp_path)
    assert not violations
