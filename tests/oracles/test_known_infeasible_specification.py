"""Known-infeasible-specification oracle test: docs/ROADMAP.md M9 exit gate
— "Infeasible-specification oracle: the binding term is correctly
identified. OQ-4 answered."
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.inverse import diagnose_infeasibility

from tests.oracles import Oracle
from tests.oracles.known_infeasible_specification import (
    ALL_SCENARIOS,
    ALEATORIC_SCENARIO,
    CONTROL_SCENARIO,
    FEASIBLE_SCENARIO,
    TRUST_REGION_SCENARIO,
    InfeasibleSpecificationScenario,
    KnownInfeasibleSpecificationOracle,
    achievable_mean_range,
)


def test_known_infeasible_specification_oracle_satisfies_the_protocol() -> None:
    assert isinstance(KnownInfeasibleSpecificationOracle(TRUST_REGION_SCENARIO), Oracle)


@pytest.mark.parametrize(
    "scenario", [TRUST_REGION_SCENARIO, CONTROL_SCENARIO, ALEATORIC_SCENARIO, FEASIBLE_SCENARIO]
)
def test_diagnose_infeasibility_recovers_the_constructed_binding_term(
    scenario: InfeasibleSpecificationScenario,
) -> None:
    oracle = KnownInfeasibleSpecificationOracle(scenario)
    rng = np.random.default_rng(0)
    mean_range = achievable_mean_range(scenario.apparatus, n=5000, rng=rng)

    diagnosed = diagnose_infeasibility(
        scenario.spec_window, scenario.trust_region, mean_range, scenario.aleatoric_std, scenario.coverage_fraction
    )

    assert diagnosed == oracle.truth()


def test_all_four_scenarios_are_mutually_distinct() -> None:
    """Sanity check on the oracle's own construction: the four scenarios
    must actually exercise four different outcomes, not coincide."""
    expected_terms = {s.expected for s in ALL_SCENARIOS}
    assert len(expected_terms) == 4
