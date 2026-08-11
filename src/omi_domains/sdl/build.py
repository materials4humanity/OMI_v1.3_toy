"""Convenience factories for the discovery domain (ADR-064): a blank-support incoming
ensemble, a chain for one sample, and composition sampling inside the declared attainable
region.

Cites Core §3.2 (the chain), Core §5 as ADR-053 extends it (the composition inverse's
attainable region), and Spec §7.1 (admissible controls).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np

from omi.chain import Chain, Segment
from omi.operators import Control
from omi.proposed.decision import AttainabilityVerdict, AttainableRegion
from omi.state import Ensemble, FloatArray

from omi_domains.sdl.interface import SDL_DECLARATION
from omi_domains.sdl.operators import Calcination, Evaluation, Preparation, descriptors
from omi_domains.sdl.state import SDL_SCHEMA, SPECIES

DRYING_TEMPERATURE = 380.0
CALCINATION_TEMPERATURE = 720.0
CALCINATION_HOLD = 2.0
EVALUATION_TEMPERATURE = 550.0
EVALUATION_INTERVAL = 2500.0
"""The declared evaluation-condition defaults. Every one sits inside the declared validity
windows of `omi_domains.sdl.forms`, so a campaign that uses them is in-window by
construction and any validity-report firing is a real finding rather than a setup artefact.

**The evaluation interval is long against the calcination hold, and it has to be.** The
declared `PARTICLE_COARSENING` form is a power law in `d^n` with `n = 3`, so at the particle
sizes this domain's calcination produces (`d ~ 6`, `d^3 ~ 200`) the declared rate `k = 0.02`
moves the dispersion by nothing at all over a hold-length interval: time on stream has to be
of order `d^n / k` for coarsening to be a *measurable* deactivation rather than an
arithmetically present one. The alternative was to raise the declared form's rate constant,
which would mean editing a committed declaration to make an experiment work — the wrong
direction. The number is here, in the campaign's own conditions, where it belongs.
"""


def build_incoming_ensemble(n_particles: int, rng: np.random.Generator) -> Ensemble:
    """A population of blank support pellets from one batch (Core §4 item 1).

    The variation is **support-batch variation**, which is why the pore-network
    accessibility carries most of it: `support` is declared a `PARAMETER` in both regions
    (ADR-051), fixed for the campaign, so what varies pellet to pellet is texture rather
    than chemistry.
    """
    particles = np.stack(
        [
            np.zeros(n_particles),  # dispersed_phase_loading — nothing deposited yet
            np.full(n_particles, 1.0),  # mean_particle_size — no dispersed phase, unit index
            np.zeros(n_particles),  # active_site_density
            np.zeros(n_particles),  # defect_site_fraction
            rng.normal(loc=0.95, scale=0.02, size=n_particles).clip(0.05, 1.0),  # accessibility
            np.zeros(n_particles),  # support_interface_coverage
            np.zeros(n_particles),  # surface_reconstruction_index
        ],
        axis=1,
    )
    return Ensemble(SDL_SCHEMA, particles)


def build_chain(
    composition: Mapping[str, float],
    n_evaluation_intervals: int,
    *,
    coarsening_scale: float = 1.0,
    calcination_temperature: float = CALCINATION_TEMPERATURE,
) -> Chain:
    """One sample's chain: preparation, calcination, then *n_evaluation_intervals* of
    reaction (Core §3.2).

    `coarsening_scale` defaults to the declared model's `1.0`; the Part 6 construction is
    the only caller that moves it, and what it moves is a quantity `SDL_SCHEMA` does not
    carry (ADR-066).
    """
    drying = Control(0.0, 1.0, lambda t: np.array([DRYING_TEMPERATURE]))
    calcining = Control(0.0, CALCINATION_HOLD, lambda t: np.array([calcination_temperature]))
    reacting = Control(0.0, EVALUATION_INTERVAL, lambda t: np.array([EVALUATION_TEMPERATURE]))
    evaluation = Evaluation(coarsening_scale=coarsening_scale)
    return Chain(
        (
            Segment(Preparation(composition=composition), drying),
            Segment(Calcination(composition=composition), calcining),
        )
        + tuple(Segment(evaluation, reacting) for _ in range(n_evaluation_intervals))
    )


def region() -> AttainableRegion:
    """The domain's own declared attainable region, read off the declaration rather than
    re-typed (ADR-053; ADR-060)."""
    declared = SDL_DECLARATION.attainable_region
    if declared is None:  # pragma: no cover - the declaration always supplies one
        raise ValueError("the discovery domain declares an attainable region; none found")
    return declared


def is_attainable(composition: Mapping[str, float]) -> bool:
    """Whether *composition* sits inside the declared attainable region (Core §5;
    ADR-053).

    Uses the declaration's own `report`, so the answer is the certificate's answer and not
    a second implementation of the same constraints. **Reported, never enforced** is the
    region's own discipline; a caller that wants to restrict a search to attainable points
    — as a campaign does, because it can only make what exists — asks this question
    explicitly rather than having the region silently clip it.
    """
    fractions = dict(composition)
    return (
        region().report(descriptors(fractions), fractions).verdict is AttainabilityVerdict.ATTAINABLE
    )


def sample_attainable_compositions(n: int, rng: np.random.Generator) -> list[dict[str, float]]:
    """*n* compositions drawn uniformly from the declared underlying bounds, projected onto
    the declared simplex, and filtered to the attainable region.

    The simplex projection is **architecture, not a penalty** (CLAUDE.md invariant 5): a
    draw that does not sum to one is renormalised rather than scored, because a set of
    fractions summing to 1.03 is not a slightly wrong composition.

    Rejection sampling rather than a clever proposal, because the acceptance rate is a
    *reported* property of the declared region — a region that rejects almost everything is
    a finding about the declaration, and a proposal tuned to hide that would remove the
    evidence.
    """
    bounds = region().underlying_bounds
    accepted: list[dict[str, float]] = []
    attempts = 0
    while len(accepted) < n and attempts < 400 * n:
        attempts += 1
        raw = {name: float(rng.uniform(*bounds[name])) for name in SPECIES}
        total = sum(raw.values())
        candidate = {name: value / total for name, value in raw.items()}
        if is_attainable(candidate):
            accepted.append(candidate)
    if len(accepted) < n:  # pragma: no cover - the declared region is not this tight
        raise ValueError(
            f"only {len(accepted)} of {n} requested compositions were attainable in {attempts} "
            "draws; the declared region is tighter than the sampler assumes and that is a "
            "finding about the declaration, not something to widen silently"
        )
    return accepted


def composition_vector(composition: Mapping[str, float]) -> FloatArray:
    """The composition as a feature vector in the declared species order, for a comparator
    that takes plain arrays (`omi.baseline`)."""
    return np.array([composition[name] for name in SPECIES], dtype=np.float64)
