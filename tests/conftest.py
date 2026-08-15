"""Shared pytest fixtures.

CLAUDE.md §7: a test that checks a measured quantity against a bound must
record the quantity, not only the pass/fail verdict — otherwise the number
an assertion was compared to survives (in the source) but the number that
was actually *observed* when the suite ran does not, and re-deriving it
later requires re-running code rather than reading a record.

``build/observations.json`` is the record. It is a git-ignored build
artefact (see ``.gitignore``), regenerated from scratch by every test-suite
run — never hand-edited, never committed.

**The bound is checked at record time since ADR-072** (`docs/V1.4-EDITS.md` E-59). It used to
be free text that nothing read, so a bound and a value could drift apart with every check
still passing — measured once, on a bound that survived a rename beside a value that did not.
:func:`tests.observation_bounds.check_observation` now runs on each call and **raises**, so a
divergence fails the test that recorded it rather than sitting in the artefact.

Checking here rather than in a lint test that reads the finished file is deliberate: the file
is written at ``pytest_sessionfinish``, so any in-suite test reading it would be reading the
*previous* run's artefact — exactly the ordering hazard ``scripts/check_audit_gate.sh`` exists
to prevent, and one this repository has already been bitten by twice.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pytest

from tests.observation_bounds import check_observation

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
        observation = {
            "test": request.node.nodeid,
            "name": name,
            "value": _jsonable(value),
            "units": units,
            "bound": bound,
        }
        _, violation = check_observation(observation)
        if violation is not None:
            raise AssertionError(
                f"observe() bound contradicts the recorded value (docs/V1.4-EDITS.md E-59; "
                f"ADR-072): {violation}\n"
                "Either the bound is stale — update it to what was actually checked — or the "
                "measured quantity moved and the assertion below this call is about to fail "
                "too. Do not silence this by rewording the bound into prose: a bound that "
                "cannot be checked is the defect E-59 records."
            )
        _OBSERVATIONS.append(observation)

    return _record


def pytest_sessionstart(session: pytest.Session) -> None:
    _OBSERVATIONS.clear()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(_OBSERVATIONS, indent=2) + "\n")
