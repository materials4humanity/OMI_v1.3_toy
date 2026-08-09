"""The discovery domain's operators, measured (ADR-064).

ADR-060 declared this domain with no operator; ADR-064 discharges that deferral because
Part 6's gate requires the vacuity precondition to be re-verified on a *runnable* chain.
What is asserted here is what the operators claim about themselves — the declared erasure,
the declared invariant, and the declared forms actually being consumed — not any campaign
result, which lives in `tests/oracles/test_discovery_campaign.py`.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.erasure import measure_erasure
from omi.operators import Control, lipschitz_report
from omi.state import Ensemble, Metric, Slot, State

from omi_domains.sdl.build import (
    CALCINATION_HOLD,
    CALCINATION_TEMPERATURE,
    build_chain,
    build_incoming_ensemble,
    sample_attainable_compositions,
)
from omi_domains.sdl.forms import SINTERING_EXPONENT, SINTERING_RATE
from omi_domains.sdl.interface import SDL_V13_CORE
from omi_domains.sdl.operators import Calcination, PRECURSOR_FEEDTHROUGH
from omi_domains.sdl.readouts import DeactivationOnset, Selectivity, TurnoverFrequency
from omi_domains.sdl.state import SDL_SCHEMA
from tests.conftest import ObservationRecorder

N_FORMULATIONS = 80
ERASURE_RTOL = 1.0e-2
"""Declared relative rank tolerance. **Required, and E-19 is why**: the spectrum below has one
value near 15 and six near `PRECURSOR_FEEDTHROUGH`, so at the machine-epsilon default of
ADR-017 the rank reads 6 and the erasure is invisible. E-19's finding is exactly that Spec
§3.2's rank bound is vacuous for a real, finite-rate erasure and that the tolerance which
fixes it is itself a declared, metric-dependent choice. Declared here rather than passed
inline for that reason."""


@pytest.fixture(scope="module")
def precursor_population() -> Ensemble:
    """Dried precursors across many attainable formulations — the *incoming population* the
    declared metric is built from (CLAUDE.md invariant 1).

    Across formulations, not within one: with a single composition every component except
    pore accessibility is constant by construction, so the metric would be degenerate and the
    erasure measurement would be reading a scaling artefact rather than the operator.
    """
    rng = np.random.default_rng(4)
    compositions = sample_attainable_compositions(N_FORMULATIONS, rng)
    support = build_incoming_ensemble(N_FORMULATIONS, rng)
    rows = [
        build_chain(composition, 0)
        .rollout(Ensemble(SDL_SCHEMA, support.particles[i][None, :]))
        .ensembles[1]
        .particles[0]
        for i, composition in enumerate(compositions)
    ]
    return Ensemble(SDL_SCHEMA, np.stack(rows))


@pytest.fixture(scope="module")
def calcination_control() -> Control:
    return Control(0.0, CALCINATION_HOLD, lambda t: np.array([CALCINATION_TEMPERATURE]))


def test_calcination_erases_six_of_seven_directions_at_the_declared_tolerance(
    precursor_population: Ensemble, calcination_control: Control, observe: ObservationRecorder
) -> None:
    """The declared erasure, **measured** rather than taken on `is_erasure`'s word (Core §3.4;
    Spec §3.2's Proposition 3.2).

    The mechanism is that every post-calcination component is set by composition and the
    calcination programme, so only `PRECURSOR_FEEDTHROUGH` of the precursor state survives —
    except the loading, which the domain declares conserved.
    """
    rng = np.random.default_rng(0)
    compositions = sample_attainable_compositions(1, rng)
    metric = Metric.from_ensemble(precursor_population)
    state = State(SDL_SCHEMA, precursor_population.particles.mean(axis=0))
    measurement = measure_erasure(
        Calcination(composition=compositions[0]), state, calcination_control, metric, rtol=ERASURE_RTOL
    )

    observe("sdl_calcination_erasure_rank", measurement.rank, f"== 1 of {SDL_SCHEMA.size}")
    observe("sdl_calcination_spectrum", measurement.spectrum, "one value >> 1, six near feedthrough")
    observe("sdl_calcination_erasure_tol", measurement.tol, f"declared rtol {ERASURE_RTOL}")

    assert measurement.rank == 1, (
        "the declared erasure should leave exactly one surviving direction — the conserved "
        f"loading — got rank {measurement.rank}"
    )
    suppressed = measurement.spectrum[1:]
    assert np.all(suppressed < 10.0 * PRECURSOR_FEEDTHROUGH), (
        "the erased directions should sit at the declared feed-through scale; a value far above "
        "it means the operator carries precursor information the declaration does not admit"
    )
    surviving = measurement.surviving_basis[:, 0]
    assert SDL_V13_CORE.state_schema is SDL_SCHEMA, "the declaration and the operators must share one schema"
    loading_index = SDL_SCHEMA.slice_for(Slot.M, "dispersed_phase_loading").start
    assert abs(surviving[loading_index]) > 0.99, (
        "the surviving direction should be the conserved dispersed-phase loading"
    )


def test_the_erasure_collapses_rank_while_amplifying_its_surviving_direction(
    precursor_population: Ensemble, calcination_control: Control, observe: ObservationRecorder
) -> None:
    """**The finding, and it is filed as E-56 rather than tidied away here.**

    Core §3.4 (and CLAUDE.md's vocabulary table restating it) define an erasure operator by
    *two* properties at once: an image of substantially lower effective dimension, and
    `L << 1`. This operator satisfies the first as completely as an operator can — six of
    seven directions gone — and **violates the second by more than an order of magnitude**,
    because the one surviving direction is amplified in the declared metric.

    The metric is the invariant-1 default (aleatoric standard deviation across the incoming
    population), so `L` reads as "how much does a one-sigma incoming variation grow", and the
    answer is that a one-sigma spread in loading becomes a many-sigma spread in site density.
    That is a real property of calcination, not a scaling artefact: converting a dilute
    precursor into a dispersed oxide phase is an amplification.

    The number depends on the declared metric — E-33's territory — so what is asserted is the
    qualitative claim: rank collapse and gain contraction are independent, and this operator
    separates them.
    """
    rng = np.random.default_rng(0)
    compositions = sample_attainable_compositions(1, rng)
    metric = Metric.from_ensemble(precursor_population)
    state = State(SDL_SCHEMA, precursor_population.particles.mean(axis=0))
    report = lipschitz_report(
        Calcination(composition=compositions[0]), state, calcination_control, metric
    )

    observe("sdl_calcination_lipschitz", float(report.spectrum[0]), "> 1 — an erasure that amplifies")
    assert report.spectrum[0] > 1.0, (
        "this test exists to record that the declared erasure amplifies its surviving "
        "direction; if that stops being true the E-56 finding needs re-measuring, not deleting"
    )


def test_calcination_conserves_the_declared_invariant(
    precursor_population: Ensemble, calcination_control: Control, observe: ObservationRecorder
) -> None:
    """`metal_mass_conservation_across_calcination`, one of the domain's three declared
    invariants (Core §4 item 6).

    An erasure that violated it would not be a more complete erasure; it would be a wrong
    operator (ADR-064).
    """
    rng = np.random.default_rng(1)
    compositions = sample_attainable_compositions(6, rng)
    worst = 0.0
    for composition in compositions:
        before = State(SDL_SCHEMA, precursor_population.particles[0])
        after = Calcination(composition=composition).step(before, calcination_control)
        drift = abs(
            float(after.get(Slot.M, "dispersed_phase_loading")[0])
            - float(before.get(Slot.M, "dispersed_phase_loading")[0])
        )
        worst = max(worst, drift)

    observe("sdl_calcination_mass_drift", worst, "== 0 exactly")
    assert worst == 0.0, "the declared conservation invariant is violated by the operator"


def test_evaluation_integrates_the_declared_coarsening_form_in_its_own_variable(
    observe: ObservationRecorder
) -> None:
    """`Evaluation` must move `d^n` by the declared rate times the elapsed time, not `d`
    (Spec §2.2; ADR-043's "a form you cannot evaluate is not a declaration").

    Checked against the declared constants rather than against a re-typed copy, so the
    operator and the form cannot drift apart.
    """
    rng = np.random.default_rng(2)
    composition = sample_attainable_compositions(1, rng)[0]
    support = build_incoming_ensemble(1, rng)
    trajectory = build_chain(composition, 2).rollout(support)

    sizes = [
        float(State(SDL_SCHEMA, trajectory.ensembles[k].particles[0]).get(Slot.M, "mean_particle_size")[0])
        for k in (2, 3, 4)
    ]
    increments = [
        sizes[i + 1] ** SINTERING_EXPONENT - sizes[i] ** SINTERING_EXPONENT for i in range(2)
    ]

    observe("sdl_coarsening_increments_in_d_cubed", increments, "equal to each other and > 0")
    assert increments[0] > 0.0, "the declared coarsening form should increase the particle size"
    assert abs(increments[1] - increments[0]) < 1.0e-9 * increments[0], (
        "the increment in the declared linearising variable should be constant per interval; a "
        "varying one means the operator integrated d rather than d^n"
    )
    assert SINTERING_RATE > 0.0


def test_every_declared_readout_evaluates_on_a_real_trajectory(observe: ObservationRecorder) -> None:
    """The three entries of the domain's `readout_catalogue` (Core §3.5), evaluated on a
    chain rather than declared and never run — which is what ADR-060 could not do."""
    rng = np.random.default_rng(3)
    composition = sample_attainable_compositions(1, rng)[0]
    support = build_incoming_ensemble(24, rng)
    final = build_chain(composition, 4).rollout(support).ensembles[-1]

    values = {
        "turnover_frequency": TurnoverFrequency()(final)[:, 0],
        "selectivity": Selectivity()(final)[:, 0],
        "deactivation_onset": DeactivationOnset()(final)[:, 0],
    }
    observe(
        "sdl_readout_means",
        {name: float(v.mean()) for name, v in values.items()},
        "all finite; turnover and selectivity strictly positive",
    )
    assert all(np.all(np.isfinite(v)) for v in values.values())
    assert values["turnover_frequency"].mean() > 0.0
    assert 0.0 < values["selectivity"].mean() <= 1.0
    assert np.all(values["deactivation_onset"] >= 0.0), "a clamped hazard cannot be negative"
