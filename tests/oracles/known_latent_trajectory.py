"""The known-latent-trajectory oracle (CLAUDE.md §7; docs/ROADMAP.md M5): a
partially observed linear system whose hidden-state trajectory is known
exactly by construction, for checking the EnKF/smoother of
``omi.assimilate`` and for demonstrating a latent variable becoming
*inferred* per Core §3.8 / Spec §3.3 (M3's triage), closing the loop
between M3 and M5 as docs/ROADMAP.md M5 requires.

The state is ``(v, hidden)``: ``v`` (Core §3.1 slot ``m``, resolved field) is
directly observed; ``hidden`` (slot ``z``, sub-resolution, "not observable
directly; inferable only through dynamics", Core §3.1) is never touched by
any sensor. Dynamics couple them, ``v_{k+1} = v_k + hidden_k``,
``hidden_{k+1} = decay * hidden_k`` — a constant-velocity-style tracking
model, chosen because it is the textbook example of a state that is
observable only through the chain, not through any instrument (Core §3.8:
"the chain model, not any instrument, is doing the work").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.assimilate import DataObservation
from omi.chain import Chain, Segment
from omi.observability import Observation
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.M, "v", 1), (Slot.Z, "hidden", 1)))
NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))

DECAY = 0.85
N_STEPS = 12
HIDDEN_0_TRUE = 4.0
V_0_TRUE = 0.0
OBSERVATION_NOISE_STD = 0.3


@dataclass(frozen=True)
class CoupledOperator(EvolutionOperator):
    """``(v, hidden) -> (v + hidden, decay * hidden)`` — linear, exact
    Jacobian (ADR-001: analytic operators make an assimilation oracle
    trustworthy). ``hidden`` never appears in any readout below; it reaches
    an observation only by first driving ``v``."""

    decay: float

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        v, hidden = state.values
        return State(state.schema, np.array([v + hidden, self.decay * hidden]))

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return np.array([[1.0, 1.0], [0.0, self.decay]])


class VReadout(FunctionalReadout):
    """The only instrumented channel: reads ``v``, never ``hidden``."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.M, "v")

    def jacobian(self, state: State) -> FloatArray:
        return np.array([[1.0, 0.0]])


class HiddenReadout(FunctionalReadout):
    """Not a sensor — used only as the *declared target* (Spec §3.3: danger
    scores are defined relative to a declared target set) for M3's triage,
    since what this oracle cares about identifying is ``hidden`` itself."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.get(Slot.Z, "hidden")

    def jacobian(self, state: State) -> FloatArray:
        return np.array([[0.0, 1.0]])


class KnownLatentTrajectoryOracle:
    """Cites CLAUDE.md §7's "known latent trajectory" construction and
    docs/ROADMAP.md M5's exit gate."""

    def __init__(
        self,
        decay: float = DECAY,
        n_steps: int = N_STEPS,
        hidden_0: float = HIDDEN_0_TRUE,
        v_0: float = V_0_TRUE,
    ) -> None:
        self.schema = SCHEMA
        self.decay = decay
        self.n_steps = n_steps
        self.hidden_0 = hidden_0
        self.v_0 = v_0
        self.operator = CoupledOperator(decay)
        self.chain = Chain(tuple(Segment(self.operator, NULL_CONTROL) for _ in range(n_steps)))
        self.v_readout = VReadout()
        self.hidden_readout = HiddenReadout()

    def true_trajectory(self) -> tuple[FloatArray, FloatArray]:
        """Roll the exact, noiseless ``(v, hidden)`` trajectory (Spec §3.1's
        ``{s̄_k}``) from the declared initial condition — the ground truth
        this oracle exists to supply."""
        v = np.zeros(self.n_steps + 1)
        hidden = np.zeros(self.n_steps + 1)
        v[0], hidden[0] = self.v_0, self.hidden_0
        for k in range(self.n_steps):
            v[k + 1] = v[k] + hidden[k]
            hidden[k + 1] = self.decay * hidden[k]
        return v, hidden

    def truth(self) -> FloatArray:
        """The known latent (``hidden``) trajectory, indices ``0..n_steps``
        (docs/ROADMAP.md M5: "Oracle with a known latent trajectory")."""
        _, hidden = self.true_trajectory()
        return hidden

    def observations(self, rng: np.random.Generator) -> list[DataObservation]:
        """Noisy observations of ``v`` only, at every chain index, generated
        from :meth:`true_trajectory` (Spec §3.1: ``y_j = H_j(s_j) + η_j``) —
        the realised data an EnKF/smoother (``omi.assimilate``) consumes."""
        v_true, _ = self.true_trajectory()
        noise_covariance = np.array([[OBSERVATION_NOISE_STD**2]])
        obs = []
        for k in range(self.n_steps + 1):
            y = np.array([v_true[k]]) + rng.normal(0.0, OBSERVATION_NOISE_STD, size=1)
            obs.append(DataObservation(f"v_{k}", self.v_readout, noise_covariance, k, y))
        return obs

    def design_observations(self) -> list[Observation]:
        """The same instrumented indices expressed as M3's design-time
        :class:`~omi.observability.Observation` (no realised data) — for
        running ``omi.observability.danger_triage`` and demonstrating
        ``hidden``'s direction lands in :attr:`~omi.observability.Triage.INFERRED`,
        closing the loop with M3 per docs/ROADMAP.md M5."""
        noise_covariance = np.array([[OBSERVATION_NOISE_STD**2]])
        return [
            Observation(f"v_{k}", self.v_readout, noise_covariance, time_index=k)
            for k in range(1, self.n_steps + 1)
        ]

    def initial_ensemble(self, n_particles: int, rng: np.random.Generator) -> Ensemble:
        """A prior ensemble deliberately centred away from the true
        ``hidden_0`` (mean 0, wide spread) so recovering it is a genuine
        inference, not a restatement of the prior."""
        v = rng.normal(self.v_0, 0.5, size=n_particles)
        hidden = rng.normal(0.0, 3.0, size=n_particles)
        particles = np.stack([v, hidden], axis=1)
        return Ensemble(self.schema, particles)
