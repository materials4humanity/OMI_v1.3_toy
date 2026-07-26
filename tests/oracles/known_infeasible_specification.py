"""The known-infeasible-specification oracle (CLAUDE.md §7; docs/ROADMAP.md
M9; OQ-4, docs/DECISIONS.md Open Questions): four scenarios sharing one
linear response model (`response = gain * u` under an apparatus-parameter
`u`), each constructed so that exactly one of the three candidate binding
terms — trust region, control/`𝒰_adm`, aleatoric spread — determines
feasibility, and a fourth where the specification is genuinely feasible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.inverse import ApparatusParameterization, BindingTerm
from omi.operators import Control

RESPONSE_GAIN = 2.0


def _apparatus(u_high: float) -> ApparatusParameterization:
    return ApparatusParameterization(
        to_control=lambda p: Control(0.0, 1.0, lambda t: p),
        parameter_dim=1,
        bounds=((0.0, u_high),),
    )


def achievable_mean_range(
    apparatus: ApparatusParameterization, n: int, rng: np.random.Generator
) -> tuple[float, float]:
    """The true achievable *noise-free* mean-response range over `𝒰_adm`
    (Spec §7.0's `ℳ_reach`, forward-sampled): `response = gain * u` is
    monotone in `u`, so this recovers the exact range as `n` grows."""
    samples = apparatus.sample_admissible(n, rng)
    responses = RESPONSE_GAIN * samples[:, 0]
    return float(responses.min()), float(responses.max())


@dataclass(frozen=True)
class InfeasibleSpecificationScenario:
    name: str
    apparatus: ApparatusParameterization
    trust_region: tuple[float, float]
    spec_window: tuple[float, float]
    aleatoric_std: float
    coverage_fraction: float
    expected: BindingTerm


TRUST_REGION_SCENARIO = InfeasibleSpecificationScenario(
    name="trust_region",
    apparatus=_apparatus(10.0),
    trust_region=(0.0, 15.0),
    spec_window=(18.0, 20.0),
    aleatoric_std=0.5,
    coverage_fraction=0.997,
    expected=BindingTerm.TRUST_REGION,
)
"""Achievable range [0, 20] would otherwise reach the window, but the
surrogate's declared trust region [0, 15] does not even overlap
[18, 20] — the model was never validated there at all."""

CONTROL_SCENARIO = InfeasibleSpecificationScenario(
    name="control",
    apparatus=_apparatus(5.0),
    trust_region=(0.0, 20.0),
    spec_window=(12.0, 14.0),
    aleatoric_std=0.5,
    coverage_fraction=0.997,
    expected=BindingTerm.CONTROL,
)
"""Trust region [0, 20] fully covers the window, but the apparatus itself
(`𝒰_adm` bounded at `u_high=5`) can only reach responses in [0, 10] —
the window [12, 14] is provably out of the apparatus's reach regardless
of aleatoric spread."""

ALEATORIC_SCENARIO = InfeasibleSpecificationScenario(
    name="aleatoric",
    apparatus=_apparatus(10.0),
    trust_region=(0.0, 20.0),
    spec_window=(9.9, 10.1),
    aleatoric_std=1.0,
    coverage_fraction=0.997,
    expected=BindingTerm.ALEATORIC,
)
"""An achievable mean of exactly 10 (`u=5`) sits inside the window, but
the window is only 0.2 wide while the aleatoric spread is 1.0 — no
achievable operating point keeps the declared coverage fraction inside
such a narrow window."""

FEASIBLE_SCENARIO = InfeasibleSpecificationScenario(
    name="feasible",
    apparatus=_apparatus(10.0),
    trust_region=(0.0, 20.0),
    spec_window=(8.0, 12.0),
    aleatoric_std=0.05,
    coverage_fraction=0.997,
    expected=BindingTerm.NONE,
)
"""A genuinely feasible specification: wide trust region, achievable mean
range spans the window, and aleatoric spread is small relative to it."""

ALL_SCENARIOS = (TRUST_REGION_SCENARIO, CONTROL_SCENARIO, ALEATORIC_SCENARIO, FEASIBLE_SCENARIO)


class KnownInfeasibleSpecificationOracle:
    """Cites CLAUDE.md §7's oracle philosophy and docs/ROADMAP.md M9's
    "the binding term is correctly identified" exit gate (OQ-4)."""

    def __init__(self, scenario: InfeasibleSpecificationScenario) -> None:
        self.scenario = scenario

    def truth(self) -> BindingTerm:
        return self.scenario.expected
