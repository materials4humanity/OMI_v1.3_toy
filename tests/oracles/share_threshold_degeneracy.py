"""E-48 triage: is the near-diagonal share's `1.4×10⁻¹¹` margin a property of contrast's
construction, or of the statistic itself?

Part 5(2) §5.2a. Measures the share's **value set** on both implemented domains and on a
lengthened flagship composition, and the same direction's label as ADR-020's declared
`near_diagonal_window` varies. Nothing is fixed here — the fix is a decision.

**Known by construction, which is what makes this an oracle** (CLAUDE.md §7): on contrast
the exact share is predictable in closed form from the chain's structure alone, before any
Gramian is computed, and on flagship it is predictable to be degenerate at the opposite
extreme. Both predictions are asserted, so the finding is a measured property of the
statistic rather than an observation about two particular numbers.

Cites Spec §3.3 (the observed/inferred criterion, quoted verbatim in
:data:`SPEC_CRITERION`), Core §3.8 (the distinction it operationalises), Core §3.9 (the
error-control dichotomy, whose condition-(b) class is exactly the class where the
degeneracy bites).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

import numpy as np

from omi.chain import Chain, Segment
from omi.observability import (
    Observation,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.state import Ensemble, FloatArray, Metric

from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi_domains.flagship.build import build_chain as flagship_chain
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.operators import HEATING_AND_SOAK, TRANSFER
from omi_domains.flagship.readouts import (
    AggregateHardness,
    BendAngleAtReferenceGeometry,
    CoatingGauge,
    ForceTorqueSensor,
)
from omi.operators import Control

SPEC_CRITERION = (
    "a direction is observed if a single near-diagonal term (j ~ k) dominates, and "
    "inferred if information accrues only through sum_{j > k}"
)
"""Spec §3.3's criterion, quoted so the comparison against ADR-020's implementation is
against the text rather than against a paraphrase of it."""

OBSERVED_SHARE_THRESHOLD = 0.5
"""ADR-020's declared threshold. Restated rather than hardcoded in prose (CLAUDE.md §8)."""

CONTRAST_DEPTH = 24
CONTRAST_CURRENT = 2.0
CONTRAST_NOISE_VARIANCE = 0.01
N_PARTICLES = 200


@dataclass(frozen=True)
class ShareReading:
    """One eigendirection's near-diagonal share at one index, with the label it produced
    and its distance from the threshold."""

    index: int
    share: float
    label: str
    window: int

    @property
    def margin(self) -> float:
        return abs(self.share - OBSERVED_SHARE_THRESHOLD)

    @property
    def as_fraction(self) -> str:
        """The share as the simplest rational within `1e-9` — the diagnostic that says
        whether the value set is discrete."""
        return str(Fraction(self.share).limit_denominator(1000))


def _readings(
    chain: Chain,
    ensemble: Ensemble,
    sensors: Sequence[Observation],
    targets: Sequence[object],
    indices: Sequence[int],
    window: int,
) -> tuple[ShareReading, ...]:
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    nominal = nominal_trajectory(chain, ensemble[0])
    out: list[ShareReading] = []
    for k in indices:
        gramian = compute_gramian(chain, nominal, k, sensors)
        result = danger_triage(
            chain, nominal, k, gramian, prior, list(targets), sensors, near_diagonal_window=window  # type: ignore[arg-type]
        )
        for direction in result.directions:
            if direction.near_diagonal_share is not None:
                out.append(
                    ShareReading(k, float(direction.near_diagonal_share), direction.label.value, window)
                )
    return tuple(out)


def _contrast_setup() -> tuple[Chain, Ensemble, list[Observation]]:
    ensemble = contrast_incoming(N_PARTICLES, np.random.default_rng(0))
    chain = contrast_chain(n_cycles=CONTRAST_DEPTH, current=CONTRAST_CURRENT)
    sensors = [
        Observation(f"voltage_{j}", TerminalVoltage(), np.array([[CONTRAST_NOISE_VARIANCE]]), time_index=j)
        for j in range(1, CONTRAST_DEPTH + 1)
    ]
    return chain, ensemble, sensors


def contrast_share_ladder(window: int = 1) -> tuple[ShareReading, ...]:
    """Contrast's shares over the campaign's interior.

    Predicted in closed form by :func:`predicted_contrast_share` before any Gramian is
    formed, which is what makes this an oracle rather than an observation.
    """
    chain, ensemble, sensors = _contrast_setup()
    return _readings(
        chain, ensemble, sensors, [DendriteRisk()], range(12, CONTRAST_DEPTH, 2), window
    )


def predicted_contrast_share(index: int, depth: int = CONTRAST_DEPTH) -> float:
    """`1/(depth − index)` — contrast's exact share, derivable from the chain's structure
    without computing anything.

    `CyclingStep` advances `lithium_inventory_loss` and
    `collector_interface_resistance` by **state-independent constant increments**, and
    `TerminalVoltage` reads `potential`, an affine function of exactly those two. So the
    sensitivity of every downstream observation to a perturbation at *index* is
    **identical**, every relevant Gramian term contributes the same quadratic form, and
    the share collapses to a ratio of term counts — a rational with a small denominator.

    Since the ratio walks `1/(depth − index)` as the index advances, it passes through
    **exactly** `1/2` at `index = depth − 2`, whatever the numbers are. This is generic
    for any chain whose Jacobian is state-independent and non-contracting on the observed
    components — the erasure-free, additive class, which is precisely Core §3.9's
    condition-(b) class.
    """
    return 1.0 / (depth - index)


def contrast_term_contributions(index: int = CONTRAST_DEPTH - 2) -> tuple[FloatArray, FloatArray]:
    """Per-observation Gramian quadratic-form contributions along the direction whose
    label is in question, and their shares of the total.

    The direct evidence for :func:`predicted_contrast_share`'s mechanism: if the
    contributions are equal, the share is a count ratio and lands on the threshold
    exactly rather than near it.
    """
    chain, ensemble, sensors = _contrast_setup()
    prior = default_prior_covariance(Metric.from_ensemble(ensemble))
    nominal = nominal_trajectory(chain, ensemble[0])
    gramian = compute_gramian(chain, nominal, index, sensors)
    result = danger_triage(
        chain, nominal, index, gramian, prior, [DendriteRisk()], sensors, near_diagonal_window=1
    )
    direction = next(d for d in result.directions if d.near_diagonal_share is not None)
    v = direction.eigenvector
    total = float(v @ gramian.total @ v)
    contributions = np.array(
        [float(v @ gramian.terms[f"voltage_{j}"] @ v) for j in range(index, CONTRAST_DEPTH + 1)]
    )
    return contributions, contributions / total


def contrast_label_by_window(index: int = CONTRAST_DEPTH - 2) -> dict[int, tuple[ShareReading, ...]]:
    """The same direction, the same chain, the same index — labelled at three values of
    ADR-020's `near_diagonal_window`.

    The window is a second convention Spec §3.3 does not supply: it operationalises
    "`j ≈ k`", and Spec gives no basis for choosing it. If the label moves across the whole
    range as the window varies, then the threshold is not the only undeclared quantity
    deciding the classification.
    """
    chain, ensemble, sensors = _contrast_setup()
    return {
        window: _readings(chain, ensemble, sensors, [DendriteRisk()], [index], window)
        for window in (0, 1, 2)
    }


def flagship_declared_shares(window: int = 1) -> tuple[ShareReading, ...]:
    """Flagship's shares on its **declared** chain, with its declared two-sensor suite.

    Expected to be degenerate at the *opposite* extreme from contrast:
    `HEATING_AND_SOAK` is a declared erasure operator, so a perturbation's sensitivity to
    downstream observations is either preserved or annihilated, never smoothly divided.
    """
    ensemble = flagship_incoming(N_PARTICLES, np.random.default_rng(0))
    chain = flagship_chain()
    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    targets = [AggregateHardness(), BendAngleAtReferenceGeometry()]
    return _readings(chain, ensemble, sensors, targets, range(0, len(chain.segments) + 1), window)


def flagship_constitutive_shares(window: int = 1) -> tuple[ShareReading, ...]:
    """The same reading on the M11 constitutive chain — the repository's third chain, and
    the only one that declares constitutive forms.

    Checked because it is the domain an SDL-style validity report would run on, and because
    it shares flagship's structure for one specific reason:
    `CONSTITUTIVE_HEATING_AND_SOAK.is_erasure` is `True`. If the degeneracy tracks the
    erasure declaration rather than the domain, this chain must land at flagship's extreme
    and not contrast's.
    """
    from omi_domains.flagship_constitutive.build import build_constitutive_chain

    ensemble = flagship_incoming(N_PARTICLES, np.random.default_rng(0))
    chain = build_constitutive_chain()
    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    targets = [AggregateHardness(), BendAngleAtReferenceGeometry()]
    return _readings(chain, ensemble, sensors, targets, range(0, len(chain.segments) + 1), window)


def flagship_lengthened_shares(repeats: int = 12, window: int = 1) -> tuple[ShareReading, ...]:
    """The same flagship operators composed into a chain as long as contrast's, so the two
    domains are compared at equal length rather than at their declared lengths.

    **Not flagship's declared chain**, and the difference is stated rather than folded in:
    flagship declares two segments (Core §7.1's stage table) and this composes twelve
    copies of the pair. It is a fair test of the *statistic* — the same operators, the same
    per-index telemetry contrast gets — and it is not a claim about the flagship domain.
    """
    heating = Control(0.0, 1.0, lambda t: np.array([8.0]))
    transfer = Control(0.0, 0.3, lambda t: np.array([1.0]))
    segments: list[Segment] = []
    for _ in range(repeats):
        segments.extend((Segment(HEATING_AND_SOAK, heating), Segment(TRANSFER, transfer)))
    chain = Chain(tuple(segments))
    ensemble = flagship_incoming(N_PARTICLES, np.random.default_rng(0))
    depth = len(chain.segments)
    sensors = [
        Observation(f"force_torque_{j}", ForceTorqueSensor(), np.array([[0.05]]), time_index=j)
        for j in range(1, depth + 1)
    ]
    targets = [AggregateHardness(), BendAngleAtReferenceGeometry()]
    return _readings(chain, ensemble, sensors, targets, range(12, depth, 2), window)
