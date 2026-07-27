"""The known-empty-slot oracle (CLAUDE.md §7; docs/ROADMAP.md M10.1): a
minimal Gamma-only chain -- m, z, and nu all declared empty (Core §4 item
1) -- for running ``measure_erasure``, ``compute_gramian``, and
``danger_triage`` against a schema this extreme, at oracle scale rather
than domain scale. Answers, with a real operator rather than only an
interface declaration, the question ``docs/SKETCHES.md``'s catalyst-
under-operation sketch (the fourth M10.1 sketch) explicitly left open:
whether any of this machinery assumes a populated m, z, or nu.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import Observation
from omi.operators import Control, EvolutionOperator
from omi.readouts import FunctionalReadout, ReadoutClass
from omi.state import Ensemble, FloatArray, Slot, State, StateSchema

SCHEMA = StateSchema(((Slot.GAMMA, "surface_state_a", 1), (Slot.GAMMA, "surface_state_b", 1)))
"""m, z, and nu are all empty -- only Gamma is occupied, and even Gamma
itself has just two components. The sharpest schema this repository has
declared anywhere: sketch 4 (catalyst under operation) kept z minimal but
non-empty; this oracle, unconstrained by physical plausibility, goes
further."""

NULL_CONTROL = Control(0.0, 1.0, lambda t: np.array([0.0]))

DAMPING: FloatArray = np.diag([1.0, 0.3])
"""A plain, full-rank diagonal map -- not a designed erasure (is_erasure
is False below). This oracle tests the generic machinery on an
empty-slot schema, not erasure detection itself, which
tests/oracles/known_erasure.py already covers."""


@dataclass(frozen=True)
class GammaOnlyOperator(EvolutionOperator):
    """Exact linear dynamics on the Gamma-only state, known by
    construction."""

    @property
    def is_erasure(self) -> bool:
        return False

    def step(self, state: State, control: Control) -> State:
        return State(state.schema, DAMPING @ state.values)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        return DAMPING


class GammaSensor(FunctionalReadout):
    """Observes ``surface_state_a`` alone."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        return state.values[0:1]

    def jacobian(self, state: State) -> FloatArray:
        return np.array([[1.0, 0.0]])


class GammaTarget(FunctionalReadout):
    """A declared target readout: a linear combination of both Gamma
    components, so danger_triage has something with nonzero influence
    over both directions to weight against."""

    readout_class = ReadoutClass.A

    def evaluate(self, state: State) -> FloatArray:
        a, b = state.values
        return np.array([a + 2.0 * b])

    def jacobian(self, state: State) -> FloatArray:
        return np.array([[1.0, 2.0]])


class KnownEmptySlotOracle:
    """Cites CLAUDE.md §7's oracle discipline."""

    def __init__(self) -> None:
        self.schema = SCHEMA
        self.chain = Chain((Segment(GammaOnlyOperator(), NULL_CONTROL),))
        self.sensor = Observation("gamma_sensor", GammaSensor(), np.array([[0.01]]), time_index=1)
        self.target = GammaTarget()

    def build_ensemble(self, n: int, rng: np.random.Generator) -> Ensemble:
        particles = rng.normal(loc=1.0, scale=0.3, size=(n, self.schema.size))
        return Ensemble(self.schema, particles)

    def truth(self) -> FloatArray:
        """The operator's own exact Jacobian singular values, known by
        construction -- what measure_erasure's spectrum must recover."""
        return np.array([1.0, 0.3])
