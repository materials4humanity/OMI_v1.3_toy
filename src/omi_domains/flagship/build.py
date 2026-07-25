"""Convenience factory: build a flagship incoming ensemble and chain.

Cites Core §7.1's stage table: incoming unit (a prior on 𝒫(𝒮)) -> heating and
soak -> transfer.
"""

from __future__ import annotations

import numpy as np

from omi.chain import Chain, Segment
from omi.operators import Control
from omi.state import Ensemble

from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship.state import FLAGSHIP_SCHEMA


def build_incoming_ensemble(n_particles: int, rng: np.random.Generator) -> Ensemble:
    """The incoming unit's prior on 𝒫(𝒮) (Core §7.1): prior_deformation and
    substructure_density vary widely (about to be erased); prior_grain_size,
    inclusion_content and coating_thickness vary within a narrower,
    already-controlled range."""
    particles = np.stack(
        [
            rng.normal(loc=5.0, scale=1.5, size=n_particles),  # prior_deformation
            rng.normal(loc=20.0, scale=3.0, size=n_particles),  # prior_grain_size
            rng.normal(loc=3.0, scale=1.0, size=n_particles),  # substructure_density
            rng.normal(loc=1.0, scale=0.3, size=n_particles),  # inclusion_content
            np.zeros(n_particles),  # accumulated_hardening
            rng.normal(loc=0.0, scale=0.5, size=n_particles),  # levelling_field
            rng.normal(loc=10.0, scale=0.5, size=n_particles),  # coating_thickness
        ],
        axis=1,
    )
    return Ensemble(FLAGSHIP_SCHEMA, particles)


def build_chain(heating_intensity: float = 8.0, transfer_speed: float = 1.0) -> Chain:
    """Heating-and-soak then transfer, each driven by a constant scalar
    control over its own interval."""
    heating_control = Control(0.0, 1.0, lambda t: np.array([heating_intensity]))
    transfer_control = Control(0.0, 0.3, lambda t: np.array([transfer_speed]))
    return Chain(
        (
            Segment(HEATING_AND_SOAK, heating_control),
            Segment(TRANSFER, transfer_control),
        )
    )
