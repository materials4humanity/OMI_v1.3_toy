"""Semigroup residual ≈ 0 for analytic operators — the docs/ROADMAP.md M1
exit-gate criterion. Cites Core §3.3: composing sub-interval evolution must
reproduce whole-interval evolution for the state-augmented dynamics.

Both domains' operators are exact closed-form flows (ADR-012's rationale,
ADR-001's build-order argument), so the residual should land at floating-
point precision, not merely "small" — that is what distinguishes an exact
analytic flow from an approximate numerical integrator.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.operators import Control, semigroup_residual
from omi.state import Slot, State

from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.state import CONTRAST_SCHEMA
from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

from tests.conftest import ObservationRecorder

FLOATING_POINT_TOLERANCE = 1e-9


@pytest.mark.parametrize("t_mid", [0.1, 0.37, 0.5, 0.9])
def test_flagship_heating_and_soak_is_semigroup_exact(t_mid: float, observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(0)
    state = State(FLAGSHIP_SCHEMA, rng.normal(loc=5.0, scale=2.0, size=FLAGSHIP_SCHEMA.size))
    control = Control(0.0, 1.0, lambda t: np.array([8.0]))
    residual = semigroup_residual(HEATING_AND_SOAK, state, control, t_mid)
    observe("residual", residual, f"< {FLOATING_POINT_TOLERANCE}", units=f"t_mid={t_mid}")
    assert residual < FLOATING_POINT_TOLERANCE


@pytest.mark.parametrize("t_mid", [0.05, 0.15, 0.25])
def test_flagship_transfer_is_semigroup_exact(t_mid: float, observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(1)
    state = State(FLAGSHIP_SCHEMA, rng.normal(loc=5.0, scale=2.0, size=FLAGSHIP_SCHEMA.size))
    control = Control(0.0, 0.3, lambda t: np.array([1.0]))
    residual = semigroup_residual(TRANSFER, state, control, t_mid)
    observe("residual", residual, f"< {FLOATING_POINT_TOLERANCE}", units=f"t_mid={t_mid}")
    assert residual < FLOATING_POINT_TOLERANCE


@pytest.mark.parametrize("t_mid", [0.2, 0.5, 0.8])
def test_contrast_cycling_step_is_semigroup_exact(t_mid: float, observe: ObservationRecorder) -> None:
    """The contrast operator's growth laws are nonlinear (sqrt accumulation)
    and its ν components are recomputed algebraically each step — this
    checks semigroup exactness survives both, not just the flagship's linear
    relaxation."""
    rng = np.random.default_rng(2)
    values = np.array(
        [
            0.30,  # electrode_porosity
            0.01,  # lithium_inventory_loss
            4.0,  # potential (placeholder, recomputed by the first step)
            0.0,  # concentration_overpotential (placeholder)
            0.02,  # sei_thickness
            0.02,  # cei_thickness
            0.05,  # collector_interface_resistance
        ]
    )
    state = State(CONTRAST_SCHEMA, values)
    control = Control(0.0, 1.0, lambda t: np.array([2.0]))
    residual = semigroup_residual(CYCLING, state, control, t_mid)
    observe("residual", residual, f"< {FLOATING_POINT_TOLERANCE}", units=f"t_mid={t_mid}")
    assert residual < FLOATING_POINT_TOLERANCE


def test_semigroup_residual_rejects_t_mid_outside_interval() -> None:
    rng = np.random.default_rng(3)
    state = State(FLAGSHIP_SCHEMA, rng.normal(size=FLAGSHIP_SCHEMA.size))
    control = Control(0.0, 1.0, lambda t: np.array([1.0]))
    with pytest.raises(ValueError):
        semigroup_residual(HEATING_AND_SOAK, state, control, t_mid=1.5)
    with pytest.raises(ValueError):
        semigroup_residual(HEATING_AND_SOAK, state, control, t_mid=0.0)
