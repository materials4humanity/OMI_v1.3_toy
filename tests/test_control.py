"""Tests for omi.operators.Control (ADR-013: a callable over a declared
interval). Cites Core §3.2: controls are functions of time on an interval,
not scalars.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.operators import Control


def test_control_rejects_empty_or_inverted_interval() -> None:
    with pytest.raises(ValueError):
        Control(1.0, 1.0, lambda t: np.array([0.0]))
    with pytest.raises(ValueError):
        Control(1.0, 0.0, lambda t: np.array([0.0]))


def test_control_evaluates_within_interval() -> None:
    control = Control(0.0, 2.0, lambda t: np.array([t * 10.0]))
    np.testing.assert_array_equal(control(0.0), [0.0])
    np.testing.assert_array_equal(control(1.0), [10.0])
    np.testing.assert_array_equal(control(2.0), [20.0])


def test_control_rejects_evaluation_outside_interval() -> None:
    control = Control(0.0, 1.0, lambda t: np.array([1.0]))
    with pytest.raises(ValueError):
        control(-0.01)
    with pytest.raises(ValueError):
        control(1.01)


def test_control_duration() -> None:
    control = Control(0.5, 3.5, lambda t: np.array([0.0]))
    assert control.duration == 3.0
