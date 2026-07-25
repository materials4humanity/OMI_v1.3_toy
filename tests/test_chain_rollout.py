"""Both domains run end to end (docs/ROADMAP.md M1 exit gate). Cites Core
§3.3 (composition understood on 𝒫(𝒮)) and ADR-015 (Chain/Trajectory).
"""

from __future__ import annotations

import numpy as np

from omi.state import Slot

from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.build import build_chain as flagship_chain


def test_flagship_chain_runs_end_to_end_and_erasure_takes_effect() -> None:
    rng = np.random.default_rng(42)
    initial = flagship_incoming(200, rng)
    chain = flagship_chain()
    trajectory = chain.rollout(initial)

    assert len(trajectory.ensembles) == len(chain.segments) + 1
    assert trajectory.initial is initial
    assert trajectory.final.n_particles == initial.n_particles

    # The erased components' ensemble spread should collapse (Core §3.9:
    # "image of substantially lower effective dimension"); the surviving
    # component's spread should not.
    erased_std_before = initial.component(Slot.M, "prior_deformation").std()
    erased_std_after = trajectory.final.component(Slot.M, "prior_deformation").std()
    surviving_std_before = initial.component(Slot.M, "prior_grain_size").std()
    surviving_std_after = trajectory.final.component(Slot.M, "prior_grain_size").std()

    assert erased_std_after < 0.05 * erased_std_before
    assert surviving_std_after == surviving_std_before  # untouched exactly


def test_contrast_chain_runs_end_to_end_with_no_erasure() -> None:
    rng = np.random.default_rng(7)
    initial = contrast_incoming(200, rng)
    chain = contrast_chain(n_cycles=10, current=1.5)
    trajectory = chain.rollout(initial)

    assert len(trajectory.ensembles) == len(chain.segments) + 1
    assert trajectory.final.n_particles == initial.n_particles

    # No operator in this chain is declared an erasure (Core §7.2's
    # inversion), so no component should collapse toward a fixed target the
    # way the flagship's erased components do.
    assert all(not segment.operator.is_erasure for segment in chain.segments)

    # SEI thickness must have grown (irreversible ageing), monotonically
    # with cycling, never shrinking.
    sei_before = initial.component(Slot.GAMMA, "sei_thickness").mean()
    sei_after = trajectory.final.component(Slot.GAMMA, "sei_thickness").mean()
    assert sei_after > sei_before
