"""Convenience factory: build a contrast incoming ensemble and chain.

Cites Core §7.2: a fresh cell's initial state, then a service duty cycle
made of repeated cycling steps.
"""

from __future__ import annotations

import numpy as np

from omi.chain import Chain, Segment
from omi.operators import Control
from omi.state import Ensemble

from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.state import CONTRAST_SCHEMA


def build_incoming_ensemble(n_particles: int, rng: np.random.Generator) -> Ensemble:
    """A population of nominally-fresh cells (Core §7.2): near-zero ageing
    state with small manufacturing variation."""
    particles = np.stack(
        [
            rng.normal(loc=0.30, scale=0.02, size=n_particles),  # electrode_porosity
            rng.normal(loc=0.0, scale=0.001, size=n_particles).clip(min=0),  # lithium_inventory_loss
            np.full(n_particles, 4.0),  # potential (placeholder, recomputed on first step)
            np.zeros(n_particles),  # concentration_overpotential (placeholder)
            rng.normal(loc=0.01, scale=0.002, size=n_particles).clip(min=0),  # sei_thickness
            rng.normal(loc=0.01, scale=0.002, size=n_particles).clip(min=0),  # cei_thickness
            rng.normal(loc=0.05, scale=0.005, size=n_particles),  # collector_interface_resistance
        ],
        axis=1,
    )
    return Ensemble(CONTRAST_SCHEMA, particles)


def build_chain(n_cycles: int, current: float = 1.0, cycle_duration: float = 1.0) -> Chain:
    """A duty cycle of ``n_cycles`` identical charge/discharge segments
    (Core §7.2's usage-determined control axis)."""
    control = Control(0.0, cycle_duration, lambda t: np.array([current]))
    return Chain(tuple(Segment(CYCLING, control) for _ in range(n_cycles)))
