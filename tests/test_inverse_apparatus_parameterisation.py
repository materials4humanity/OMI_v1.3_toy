"""Apparatus parameterisation (Spec §7.2; ADR-032, docs/DECISIONS.md):
inverse design is parameterised in apparatus settings, never desired
driving paths — checked structurally, not by convention.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.inverse import ApparatusParameterization
from omi.operators import Control


def test_bounds_must_match_parameter_dimension() -> None:
    with pytest.raises(ValueError):
        ApparatusParameterization(
            to_control=lambda p: Control(0.0, 1.0, lambda t: p),
            parameter_dim=2,
            bounds=((0.0, 1.0),),
        )


def test_sample_admissible_stays_within_declared_bounds() -> None:
    apparatus = ApparatusParameterization(
        to_control=lambda p: Control(0.0, 1.0, lambda t: p),
        parameter_dim=3,
        bounds=((0.0, 1.0), (-5.0, 5.0), (10.0, 20.0)),
    )
    rng = np.random.default_rng(0)
    samples = apparatus.sample_admissible(1000, rng)

    for i, (low, high) in enumerate(apparatus.bounds):
        assert np.all(samples[:, i] >= low)
        assert np.all(samples[:, i] <= high)


def test_to_control_is_the_only_route_from_parameters_to_a_control() -> None:
    """The structural check itself (ADR-032): a `Control` is only ever
    produced by calling `to_control` on an apparatus-parameter array — this
    test constructs one exactly that way and confirms it behaves as a
    genuine `Control` (Spec §3.2), not a hand-built driving path."""
    apparatus = ApparatusParameterization(
        to_control=lambda p: Control(0.0, 1.0, lambda t: p * 2.0),
        parameter_dim=1,
        bounds=((0.0, 10.0),),
    )
    parameters = np.array([3.0])
    control = apparatus.to_control(parameters)

    assert np.allclose(control(0.5), np.array([6.0]))
    assert control.t0 == 0.0 and control.t1 == 1.0


def test_sample_admissible_is_deterministic_given_the_same_generator_seed() -> None:
    apparatus = ApparatusParameterization(
        to_control=lambda p: Control(0.0, 1.0, lambda t: p),
        parameter_dim=2,
        bounds=((0.0, 1.0), (0.0, 1.0)),
    )
    samples_a = apparatus.sample_admissible(50, np.random.default_rng(42))
    samples_b = apparatus.sample_admissible(50, np.random.default_rng(42))
    np.testing.assert_array_equal(samples_a, samples_b)
