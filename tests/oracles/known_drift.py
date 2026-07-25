"""The known-drift oracle (CLAUDE.md §7; docs/ROADMAP.md M5): a scalar
process whose *true* dynamics develop an unmodeled linear ramp at a declared
change point, while the EnKF's dynamics model (``omi.assimilate``) stays
fixed at the identity throughout — a deliberate model/reality mismatch of
known location and magnitude, for checking that
``innovation_drift_monitor`` (Spec §10's proposition, ADR-026's declared
procedure) flags it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.assimilate import DataObservation
from omi.chain import Chain, Segment
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "x", 1),))
NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))

N_STEPS = 60
CHANGE_POINT = 30
RAMP_RATE = 0.4
OBSERVATION_NOISE_STD = 0.2


@dataclass(frozen=True)
class IdentityOperator1(EvolutionOperator):
    """The filter's dynamics model (Spec §3.1): a static state. Deliberately
    never includes the ramp the *true* generating process develops — that
    mismatch is the drift this oracle exists to plant."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return state

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.eye(1)


class XReadout(FunctionalReadout):
    """The only sensor: reads ``x`` directly."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "x")

    def jacobian(self, state: State) -> FloatArray:
        return np.array([[1.0]])


class KnownDriftOracle:
    """Cites CLAUDE.md §7's oracle philosophy and docs/ROADMAP.md M5's
    "innovation monitor detects a planted drift" exit-gate requirement.

    *with_drift* selects between the planted-drift truth (a ramp starting at
    :data:`CHANGE_POINT`) and a purely nominal truth (no ramp at all,
    identically matching the filter's model) — the contrast between the two
    is what the exit-gate test asserts on, rather than a single run's raw
    counts.
    """

    def __init__(self, with_drift: bool, n_steps: int = N_STEPS) -> None:
        self.schema = SCHEMA
        self.with_drift = with_drift
        self.n_steps = n_steps
        self.operator = IdentityOperator1()
        self.chain = Chain(tuple(Segment(self.operator, NULL_CONTROL) for _ in range(n_steps)))
        self.readout = XReadout()

    def true_trajectory(self) -> FloatArray:
        """The true, exactly-known ``x`` trajectory (Spec §3.1's ``{s̄_k}``):
        identically zero if :attr:`with_drift` is ``False``; a ramp starting
        at :data:`CHANGE_POINT` otherwise — the planted, known-by-
        construction model mismatch."""
        x_true = np.zeros(self.n_steps + 1)
        if self.with_drift:
            for k in range(self.n_steps + 1):
                if k >= CHANGE_POINT:
                    x_true[k] = RAMP_RATE * (k - CHANGE_POINT)
        return x_true

    def truth(self) -> FloatArray:
        """The planted change point and ramp rate, as a ``(change_point,
        ramp_rate)`` pair — ``(nan, nan)`` when :attr:`with_drift` is
        ``False``, since there is then no drift to locate."""
        if not self.with_drift:
            return np.array([np.nan, np.nan])
        return np.array([float(CHANGE_POINT), RAMP_RATE])

    def observations(self, rng: np.random.Generator) -> list[DataObservation]:
        """Noisy observations of ``x`` at every index (Spec §3.1's
        ``y_j = H_j(s_j) + η_j``), generated from :meth:`true_trajectory`."""
        x_true = self.true_trajectory()
        noise_covariance = np.array([[OBSERVATION_NOISE_STD**2]])
        obs = []
        for k in range(self.n_steps + 1):
            y = np.array([x_true[k]]) + rng.normal(0.0, OBSERVATION_NOISE_STD, size=1)
            obs.append(DataObservation(f"x_{k}", self.readout, noise_covariance, k, y))
        return obs

    def initial_ensemble(self, n_particles: int, rng: np.random.Generator) -> Ensemble:
        """A prior ensemble consistent with the (correctly specified, pre-
        drift) static model."""
        particles = rng.normal(0.0, 1.0, size=(n_particles, 1))
        return Ensemble(self.schema, particles)
