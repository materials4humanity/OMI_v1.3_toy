"""Citation lint: every public function/class docstring under src/omi/ cites
Core §x or Spec §x.

Enforces CLAUDE.md §8: "Cite the source section in the docstring: Core §3.8
or Spec §3.3. A module with no citations is either inventing or restating."
Names starting with ``_`` are treated as private and exempt, matching Python
convention; dunder methods (``__init__`` etc.) are exempt for the same reason.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_OMI = REPO_ROOT / "src" / "omi"

CITATION_RE = re.compile(r"(Core|Spec)\s+§\d")


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    name: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.name!r} has no Core §x / Spec §x citation"


def _public_defs(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]:
    defs: list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                defs.append(node)
    return defs


def find_uncited_docstrings(root: Path) -> list[Violation]:
    """Scan every ``*.py`` file under *root* for uncited public definitions."""
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in _public_defs(tree):
            doc = ast.get_docstring(node)
            if not doc or not CITATION_RE.search(doc):
                violations.append(Violation(path, node.lineno, node.name))
    return violations


def test_real_source_is_fully_cited() -> None:
    """The actual src/omi/ tree must be clean — the lint CI enforces."""
    violations = find_uncited_docstrings(SRC_OMI)
    assert not violations, "uncited public definitions under src/omi/:\n" + "\n".join(
        str(v) for v in violations
    )


def test_scanner_detects_a_planted_violation(tmp_path: Path) -> None:
    """Fail half of the demonstration: an uncited public function is caught."""
    planted = tmp_path / "uncited.py"
    planted.write_text(
        "def compute_thing(x: int) -> int:\n"
        '    """Doubles x. No section citation here."""\n'
        "    return 2 * x\n"
    )
    violations = find_uncited_docstrings(tmp_path)
    assert len(violations) == 1
    assert violations[0].name == "compute_thing"


def test_scanner_is_clean_once_citation_added(tmp_path: Path) -> None:
    """Pass half of the demonstration: adding the citation clears the lint."""
    cited = tmp_path / "cited.py"
    cited.write_text(
        "def compute_thing(x: int) -> int:\n"
        '    """Doubles x. Cites Core §3.1 for the sake of this example."""\n'
        "    return 2 * x\n"
    )
    violations = find_uncited_docstrings(tmp_path)
    assert not violations
