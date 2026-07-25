"""Chain composition at the level of measures: rollout and trajectory
recording.

Cites Core §3.3 (composition of evolution operators, understood on
``𝒫(𝒮)``) and Core §3.9 (the composed forward map ``𝒢_PSR``). ADR-015
(docs/DECISIONS.md) fixes M1's ``Chain`` as a linear ordered sequence of
segments — the degenerate, single-mode case of Spec §12's mode-labelled DAG,
which stays out of scope while hybrid structure (Spec §5.1) is an anti-goal.
"""

from __future__ import annotations

from dataclasses import dataclass

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble


@dataclass(frozen=True)
class Segment:
    """One ``(operator, control)`` step of a chain (Core §3.3)."""

    operator: EvolutionOperator
    control: Control


@dataclass(frozen=True)
class Trajectory:
    """The recorded result of a rollout: every intermediate ensemble, not
    just the final one.

    Needed downstream for rollout-length error curves (Spec §1.4/§9.2) and
    retrospective smoothing (Core §3.8) — both require the whole history, so
    ``Chain.rollout`` records it now rather than discarding it (ADR-015).
    """

    ensembles: tuple[Ensemble, ...]
    """``ensembles[0]`` is the initial ensemble; ``ensembles[i]`` is the
    result after segment ``i - 1``. Length is ``len(segments) + 1``."""

    @property
    def initial(self) -> Ensemble:
        """The pre-rollout ensemble (Core §3.3's initial state estimate)."""
        return self.ensembles[0]

    @property
    def final(self) -> Ensemble:
        """The post-rollout ensemble (Core §3.9's composed ``𝒢_PSR``, before
        any readout is applied)."""
        return self.ensembles[-1]


@dataclass(frozen=True)
class Chain:
    """An ordered sequence of evolution segments (ADR-015): the linear,
    single-mode case of Spec §12's mode-labelled DAG. Composition is
    understood at the level of measures (Core §3.3): each segment's
    ``.lift`` advances an :class:`~omi.state.Ensemble`, not a single state.
    """

    segments: tuple[Segment, ...]

    def rollout(self, initial: Ensemble) -> Trajectory:
        """Compose every segment's pushforward lift in order, recording each
        intermediate ensemble (Core §3.3; Core §3.9's ``𝒢_PSR``)."""
        ensembles = [initial]
        current = initial
        for segment in self.segments:
            current = segment.operator.lift(current, segment.control)
            ensembles.append(current)
        return Trajectory(tuple(ensembles))
