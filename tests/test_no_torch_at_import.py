"""torch must never be imported at module scope under src/omi/ (CLAUDE.md §8;
ADR-001, docs/DECISIONS.md — analytic operators come first, torch is an
optional extra that only arrives at M8 behind the same protocol).

Two checks: a static scan (imports inside a function body are lazy/deferred
and therefore allowed; anything that executes at import time — module level,
or a class body, since class bodies execute on import — is not), plus a
direct import of ``omi`` in this environment, which has no ``torch`` extra
installed at all, so a module-scope import anywhere in the package would
fail this test file's own collection.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_OMI = REPO_ROOT / "src" / "omi"


def _module_scope_torch_imports(node: ast.AST) -> list[int]:
    """Collect line numbers of torch imports that execute at import time.

    Recurses into everything except function bodies (``FunctionDef`` /
    ``AsyncFunctionDef``), since a torch import inside a function is deferred
    until that function is called — exactly the pattern an optional extra
    requires. Class bodies are still descended into: they execute when the
    module is imported, same as top-level statements.
    """
    lines: list[int] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(child, ast.Import) and any(
            alias.name == "torch" or alias.name.startswith("torch.") for alias in child.names
        ):
            lines.append(child.lineno)
        elif (
            isinstance(child, ast.ImportFrom)
            and child.module is not None
            and (child.module == "torch" or child.module.startswith("torch."))
        ):
            lines.append(child.lineno)
        else:
            lines.extend(_module_scope_torch_imports(child))
    return lines


def test_no_module_scope_torch_import_anywhere_under_src_omi() -> None:
    violations: list[str] = []
    for path in sorted(SRC_OMI.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno in _module_scope_torch_imports(tree):
            violations.append(f"{path}:{lineno}")
    assert not violations, "module-scope torch import found:\n" + "\n".join(violations)


def test_omi_imports_cleanly_with_torch_absent() -> None:
    """This environment has no torch installed at all (pyproject.toml keeps
    it as an optional extra) — so importing omi here already demonstrates
    the package does not require it."""
    assert "torch" not in sys.modules, "torch was already imported by something else in this session"
    module = importlib.import_module("omi")
    assert "torch" not in sys.modules, "importing omi pulled in torch"
    assert hasattr(module, "NotSpecified")
