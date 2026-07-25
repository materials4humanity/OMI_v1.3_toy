"""Gap-citation lint: every NotSpecified raised in the codebase cites an id
that exists in docs/COVERAGE.md.

Enforces CLAUDE.md §4 and ADR-005 (docs/DECISIONS.md): "CI enforces that
every NotSpecified cites a live id." This is checked statically (by scanning
call sites) rather than only at runtime, so an unreached ``raise`` branch is
still caught — ``omi.gaps.NotSpecified.__init__`` separately validates at
construction time (defense in depth), but a lint that only fired when a code
path executed would miss dead or rarely-hit refusals.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from omi.gaps import known_gap_ids

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    reason: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.reason}"


def _is_not_specified_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "NotSpecified"
    if isinstance(func, ast.Attribute):
        return func.attr == "NotSpecified"
    return False


def _cited_id(node: ast.Call) -> str | ast.expr | None:
    """Return the literal string passed as the gap id, or the raw node if
    the argument isn't a literal (which is itself a lint failure), or None
    if no argument was given at all."""
    arg: ast.expr | None
    if node.args:
        arg = node.args[0]
    else:
        arg = None
        for kw in node.keywords:
            if kw.arg == "coverage_id":
                arg = kw.value
                break
    if arg is None:
        return None
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return arg


def find_uncited_gap_ids(root: Path) -> list[Violation]:
    """Scan every ``*.py`` file under *root* for ``NotSpecified(...)`` calls
    whose cited id is missing, non-literal, or not a live COVERAGE.md row."""
    known = known_gap_ids()
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_not_specified_call(node):
                continue
            cited = _cited_id(node)
            if cited is None:
                violations.append(Violation(path, node.lineno, "NotSpecified raised with no id"))
            elif isinstance(cited, str):
                if cited not in known:
                    violations.append(
                        Violation(path, node.lineno, f"cites unknown id {cited!r}")
                    )
            else:
                violations.append(
                    Violation(path, node.lineno, "cites a non-literal id; cannot verify statically")
                )
    return violations


def test_real_source_cites_only_live_gap_ids() -> None:
    """The actual src/ tree must be clean — the lint CI enforces."""
    violations = find_uncited_gap_ids(SRC)
    assert not violations, "bad gap citations under src/:\n" + "\n".join(
        str(v) for v in violations
    )


def test_scanner_detects_a_planted_violation(tmp_path: Path) -> None:
    """Fail half of the demonstration: a made-up id must be caught."""
    planted = tmp_path / "refuser.py"
    planted.write_text(
        "from omi.gaps import NotSpecified\n"
        "\n"
        "def do_something() -> None:\n"
        '    """Cites Core §3.9 for the sake of this example."""\n'
        '    raise NotSpecified("Z-99.9", "Spec §99.9", "invented for the test")\n'
    )
    violations = find_uncited_gap_ids(tmp_path)
    assert len(violations) == 1
    assert "Z-99.9" in violations[0].reason


def test_scanner_is_clean_once_id_corrected(tmp_path: Path) -> None:
    """Pass half of the demonstration: citing a live id clears the lint."""
    fixed = tmp_path / "refuser.py"
    fixed.write_text(
        "from omi.gaps import NotSpecified\n"
        "\n"
        "def do_something() -> None:\n"
        '    """Cites Core §3.9 for the sake of this example."""\n'
        '    raise NotSpecified("S-2.5", "Spec §2.5", "estimation procedure not written")\n'
    )
    violations = find_uncited_gap_ids(tmp_path)
    assert not violations
