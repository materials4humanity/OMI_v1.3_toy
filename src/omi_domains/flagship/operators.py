"""Analytic evolution operators for the flagship chain (Core §7.1).

Every operator here is an exact closed-form flow (diagonal linear relaxation
toward a control-derived target), so composing sub-intervals of a fixed
control programme reproduces the whole-interval result to floating-point
precision — this is what makes the M1 semigroup-residual exit-gate criterion
meaningful (Core §3.3) rather than an approximation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, State

from omi_domains.flagship.state import FLAGSHIP_SCHEMA


@dataclass(frozen=True)
class RelaxationOperator(EvolutionOperator):
    """``ds_i/dt = -rate_i * (s_i - target_i)``, ``target_i = target_gain_i *
    u`` for a scalar control ``u`` held constant over the queried interval.
    The closed form is exact, so this class is deliberately the same shape
    for every flagship stage (Core §3.3's semigroup identity is then exact by
    construction, not by luck).
    """

    rates: FloatArray
    target_gain: FloatArray
    erasure: bool

    def __post_init__(self) -> None:
        if self.rates.shape != (FLAGSHIP_SCHEMA.size,) or self.target_gain.shape != (
            FLAGSHIP_SCHEMA.size,
        ):
            raise ValueError("rates/target_gain must match the flagship schema size")
        if np.any(self.rates < 0):
            raise ValueError("relaxation rates must be non-negative")

    @property
    def is_erasure(self) -> bool:
        return self.erasure

    def step(self, state: State, control: Control) -> State:
        dt = control.duration
        u = control(control.t0)[0]
        target = self.target_gain * u
        decay = np.exp(-self.rates * dt)
        new_values = target + (state.values - target) * decay
        return State(state.schema, new_values)


# Component order (omi_domains/flagship/state.py): prior_deformation,
# prior_grain_size, substructure_density, inclusion_content,
# accumulated_hardening, levelling_field, coating_thickness.

HEATING_AND_SOAK = RelaxationOperator(
    rates=np.array([5.0, 0.0, 5.0, 0.0, 0.0, 0.3, 0.05]),
    target_gain=np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.02]),
    erasure=True,
)
"""Erases prior_deformation and substructure_density (Core §7.1: "erases z
and most of m"); prior_grain_size, inclusion_content and coating_thickness
survive (coating_thickness drifts slightly under a heating-intensity
control); levelling_field partially relaxes."""

TRANSFER = RelaxationOperator(
    rates=np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.02]),
    target_gain=np.zeros(FLAGSHIP_SCHEMA.size),
    erasure=False,
)
"""Short, well-instrumented (Core §7.1); only the levelling field and
coating continue to relax slightly, everything else is untouched."""
