"""Known-composition-drift oracle: a chain whose domain-mean drift is fixed by
construction, so ADR-050's constancy residual has a right answer (ADR-076).

Follows `tests/oracles/`'s standing discipline (CLAUDE.md §7): the quantity the estimator
must recover is *chosen here*, and the test asserts recovery rather than asserting a figure
someone once observed.

**What is known by construction.** The open operator subtracts `boundary_flux × duration`
from the domain-mean deviation at every step and nothing else touches it, so after `steps`
steps of duration `dt` the drift is exactly

    drift = boundary_flux × dt × steps

with no discretisation error and no dependence on the coarsening rate — the coarsening acts
on a different component. The closed operator does not write the deviation at all, so its
drift is exactly `0.0`, not "small". Both answers are exact, which is what makes this an
oracle rather than a regression fixture.

**Why an exactly-zero arm matters.** ADR-050's argument is that a mean over a *closed*
domain is constant *by conservation*. An arm whose drift were merely small would not
distinguish "conserved" from "nearly conserved", and the whole diagnosis — a violation means
the declared domain is open — rests on that distinction being sharp.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.operators import Control
from omi.state import State

from omi_domains.flagship_composition.operators import (
    BoundaryLossRedistribution,
    ConservativeRedistribution,
)
from omi_domains.flagship_composition.state import (
    COMPOSITION_SCHEMA,
    DELTA_C_MEAN_INDEX,
    SUBSTRUCTURE_INDEX,
)

COARSENING_RATE = 0.4
"""Shared by both arms, so any difference between them is attributable to the flux alone."""

PLANTED_FLUX = 0.015
"""The boundary flux the open arm loses per unit time. The number is arbitrary; that the
oracle knows it exactly is the point."""

STEP_DURATION = 0.5
STEPS = 6

INITIAL_SUBSTRUCTURE = 1.0
INITIAL_DEVIATION = 0.0
"""The deviation starts at zero: a well-declared closed domain has no mean offset from its
own declared mean. The open arm's drift is therefore also its absolute value, which keeps the
arithmetic in the test readable."""


@dataclass(frozen=True)
class KnownDriftTruth:
    """The answers fixed by construction (CLAUDE.md §7)."""

    closed_drift: float
    open_drift: float
    steps: int


def truth() -> KnownDriftTruth:
    """Exact drifts, computed from the declared construction rather than measured."""
    return KnownDriftTruth(
        closed_drift=0.0,
        open_drift=PLANTED_FLUX * STEP_DURATION * STEPS,
        steps=STEPS,
    )


def _initial_state() -> State:
    values = np.zeros(COMPOSITION_SCHEMA.size)
    values[SUBSTRUCTURE_INDEX] = INITIAL_SUBSTRUCTURE
    values[DELTA_C_MEAN_INDEX] = INITIAL_DEVIATION
    return State(schema=COMPOSITION_SCHEMA, values=values)


def _control() -> Control:
    return Control(0.0, STEP_DURATION, lambda t: np.array([1.0]))


def closed_arm_deviations() -> tuple[float, ...]:
    """Deviation trajectory under the conservative operator — exactly constant."""
    operator = ConservativeRedistribution(coarsening_rate=COARSENING_RATE)
    state, control = _initial_state(), _control()
    trajectory = [float(state.values[DELTA_C_MEAN_INDEX])]
    for _ in range(STEPS):
        state = operator.step(state, control)
        trajectory.append(float(state.values[DELTA_C_MEAN_INDEX]))
    return tuple(trajectory)


def open_arm_deviations() -> tuple[float, ...]:
    """Deviation trajectory under the boundary-loss operator — drifts by the planted flux."""
    operator = BoundaryLossRedistribution(
        coarsening_rate=COARSENING_RATE, boundary_flux=PLANTED_FLUX
    )
    state, control = _initial_state(), _control()
    trajectory = [float(state.values[DELTA_C_MEAN_INDEX])]
    for _ in range(STEPS):
        state = operator.step(state, control)
        trajectory.append(float(state.values[DELTA_C_MEAN_INDEX]))
    return tuple(trajectory)


def substructure_change() -> tuple[float, float]:
    """`(initial, final)` substructure density under the **conservative** operator.

    Exposed so a test can confirm the closed arm is not a no-op: the conservative operator
    changes the state substantively while leaving the domain mean exactly alone, which is the
    substantive claim rather than the trivial one.
    """
    operator = ConservativeRedistribution(coarsening_rate=COARSENING_RATE)
    state, control = _initial_state(), _control()
    initial = float(state.values[SUBSTRUCTURE_INDEX])
    for _ in range(STEPS):
        state = operator.step(state, control)
    return initial, float(state.values[SUBSTRUCTURE_INDEX])
