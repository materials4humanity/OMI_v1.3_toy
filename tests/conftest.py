"""Shared pytest fixtures.

CLAUDE.md §7: a test that checks a measured quantity against a bound must
record the quantity, not only the pass/fail verdict — otherwise the number
an assertion was compared to survives (in the source) but the number that
was actually *observed* when the suite ran does not, and re-deriving it
later requires re-running code rather than reading a record.

``build/observations.json`` is the record. It is a git-ignored build
artefact (see ``.gitignore``), regenerated from scratch by every test-suite
run — never hand-edited, never committed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pytest

_OBSERVATIONS: list[dict[str, Any]] = []
_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "build" / "observations.json"


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of a measured quantity to something
    ``json.dumps`` accepts, without rounding or otherwise editorialising it."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return str(value)


class ObservationRecorder(Protocol):
    def __call__(self, name: str, value: Any, bound: str, units: str | None = None) -> None: ...


@pytest.fixture
def observe(request: pytest.FixtureRequest) -> ObservationRecorder:
    """Record a named observation for the current test: the measured value,
    the bound it was checked against (as written in the assertion, e.g.
    ``"< 0.05"`` or ``"truth().rank"``), and units where the quantity has
    any. Call it *before* the assertion so the value is on record even if
    the assertion then fails.
    """

    def _record(name: str, value: Any, bound: str, units: str | None = None) -> None:
        _OBSERVATIONS.append(
            {
                "test": request.node.nodeid,
                "name": name,
                "value": _jsonable(value),
                "units": units,
                "bound": bound,
            }
        )

    return _record


def pytest_sessionstart(session: pytest.Session) -> None:
    _OBSERVATIONS.clear()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(_OBSERVATIONS, indent=2) + "\n")
