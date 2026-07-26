"""Coverage-evidence lint (Phase 1.2, docs/DECISIONS.md ADR-034): every row
of docs/COVERAGE.md's Implemented / Oracle-verified / Domain-exercised
columns is either explicitly unclaimed (an em-dash, optionally with a
parenthetical reason) or names at least one backtick-quoted path — and every
backtick-quoted path anywhere in those columns must actually exist. This is
what stops "implemented" and "verified" from silently collapsing into each
other again, the way CLAUDE.md's gap discipline stops a Spec gap being
silently interpolated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGE_MD = REPO_ROOT / "docs" / "COVERAGE.md"

VERIFICATION_COLUMNS = ("Implemented", "Oracle-verified", "Domain-exercised")

_BACKTICK = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Violation:
    line: int
    column: str
    reason: str

    def __str__(self) -> str:
        return f"line {self.line} [{self.column}]: {self.reason}"


def _split_row(line: str) -> list[str] | None:
    """Split a markdown table row into trimmed cells, or None if *line* is
    not a table row at all."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-+:?", c) for c in cells if c)


def _path_like_spans(cell: str) -> list[str]:
    """Backtick spans in *cell* that look like a file path (as opposed to a
    bare symbol name mentioned for context, e.g. `HEATING_AND_SOAK`)."""
    spans = []
    for span in _BACKTICK.findall(cell):
        head = span.split("::", 1)[0].split("#", 1)[0]
        if "/" in head or head.endswith(".py") or head.endswith(".md"):
            spans.append(head)
    return spans


def find_evidence_violations(text: str) -> list[Violation]:
    """Scan every markdown table in *text* that has Implemented /
    Oracle-verified / Domain-exercised columns, and validate each row's
    cells in those columns."""
    lines = text.splitlines()
    violations: list[Violation] = []

    header_indices: dict[str, int] | None = None
    for lineno, line in enumerate(lines, start=1):
        cells = _split_row(line)
        if cells is None:
            header_indices = None
            continue
        if _is_separator_row(cells):
            continue
        if all(col in cells for col in VERIFICATION_COLUMNS):
            header_indices = {col: cells.index(col) for col in VERIFICATION_COLUMNS}
            continue
        if header_indices is None:
            continue
        for column, index in header_indices.items():
            if index >= len(cells):
                violations.append(Violation(lineno, column, "row has too few cells for this table's header"))
                continue
            cell = cells[index]
            claimed = not cell.startswith("—")
            spans = _path_like_spans(cell)
            if claimed and not spans:
                violations.append(
                    Violation(lineno, column, f"claimed ({cell!r}) without a named backtick path")
                )
            for path in spans:
                if not (REPO_ROOT / path).exists():
                    violations.append(Violation(lineno, column, f"named path does not exist: {path!r}"))
    return violations


def test_coverage_md_evidence_columns_are_all_either_dashed_or_pathed_and_real() -> None:
    text = COVERAGE_MD.read_text(encoding="utf-8")
    violations = find_evidence_violations(text)
    assert not violations, "bad coverage-evidence citations in docs/COVERAGE.md:\n" + "\n".join(
        str(v) for v in violations
    )


def test_scanner_detects_a_claim_with_no_path() -> None:
    text = (
        "| id | Spec § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| Z-1 | §1 | thing | SPEC | `x.py` | yes | — | — |\n"
    )
    violations = find_evidence_violations(text)
    assert len(violations) == 1
    assert violations[0].column == "Implemented"
    assert "without a named backtick path" in violations[0].reason


def test_scanner_detects_a_named_path_that_does_not_exist() -> None:
    text = (
        "| id | Spec § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| Z-1 | §1 | thing | SPEC | `x.py` | `src/omi/does_not_exist_ZZZ.py` | — | — |\n"
    )
    violations = find_evidence_violations(text)
    assert len(violations) == 1
    assert "does not exist" in violations[0].reason


def test_scanner_is_clean_for_a_correctly_dashed_and_pathed_row() -> None:
    text = (
        "| id | Spec § | Content | Status | Repo | Implemented | Oracle-verified | Domain-exercised |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| Z-1 | §1 | thing | SPEC | `x.py` | `src/omi/state.py` | — (no oracle) | — |\n"
    )
    violations = find_evidence_violations(text)
    assert not violations
