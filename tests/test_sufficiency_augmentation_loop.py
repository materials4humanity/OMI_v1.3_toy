"""The augmentation loop (Spec §1.5) and the blocking-term trichotomy (Spec
§1.7), exercised directly against the known-insufficiency oracle's hidden
variable via injectable callables (ADR-023, docs/DECISIONS.md).
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from omi.sufficiency import BlockingTerm, DeficitResult, augmentation_loop, sufficiency_deficit
from omi.state import Slot, StateSchema

from tests.oracles.known_insufficiency import KnownInsufficiencyOracle

MINIMAL_SCHEMA = StateSchema(((Slot.M, "v", 1),))
AUGMENTED_SCHEMA = StateSchema(((Slot.M, "v", 1), (Slot.Z, "hidden", 1)))
HIDDEN_CANDIDATE = (Slot.Z, "hidden", 1)


def _make_sufficiency_test(
    oracle: KnownInsufficiencyOracle, rng: np.random.Generator
) -> Callable[[StateSchema], DeficitResult]:
    """A sufficiency_test callable (StateSchema -> DeficitResult) backed by
    the oracle: the minimal schema (v only) sees the hidden variable's
    insufficiency; the augmented schema (v, hidden) does not."""

    def sufficiency_test(schema: StateSchema) -> DeficitResult:
        n_pairs = 4000
        if schema.size == MINIMAL_SCHEMA.size:
            response_a, response_b, diffs = oracle.sample_incomplete_campaign(n_pairs, "reversed", rng)
            jacobian = oracle.response_jacobian_incomplete("reversed")
        else:
            response_a, response_b, diffs = oracle.sample_complete_campaign(n_pairs, "reversed", rng)
            jacobian = oracle.response_jacobian_complete("reversed")
        repeat_variance = oracle.repeat_variance(1000, rng)
        return sufficiency_deficit(response_a, response_b, diffs, jacobian, repeat_variance)

    return sufficiency_test


def test_augmentation_loop_accepts_the_hidden_variable_when_variance_cost_is_low() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(0)
    sufficiency_test = _make_sufficiency_test(oracle, rng)

    def variance_delta(schema: StateSchema) -> float:
        # Cheap to identify: a low, deliberately small variance cost.
        return 0.0 if schema.size == MINIMAL_SCHEMA.size else 0.1

    result = augmentation_loop(
        MINIMAL_SCHEMA,
        [HIDDEN_CANDIDATE],
        sufficiency_test,
        variance_delta,
        tolerance_bias_squared=0.2,
    )

    assert result.stopped_reason == "sufficient_at_tolerance"
    assert result.final_schema.size == AUGMENTED_SCHEMA.size
    accepted_names = [s.accepted_candidate for s in result.steps if s.accepted_candidate is not None]
    assert accepted_names == [(Slot.Z, "hidden")]


def test_augmentation_loop_rejects_the_candidate_when_variance_cost_is_too_high() -> None:
    """Spec §1.7's 'buy sensing' case: the needed component exists but its
    identification cost (ΔVar_est) exceeds the bias it would remove."""
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(1)
    sufficiency_test = _make_sufficiency_test(oracle, rng)

    def variance_delta(schema: StateSchema) -> float:
        # Prohibitively expensive to identify.
        return 0.0 if schema.size == MINIMAL_SCHEMA.size else 1000.0

    result = augmentation_loop(
        MINIMAL_SCHEMA,
        [HIDDEN_CANDIDATE],
        sufficiency_test,
        variance_delta,
        tolerance_bias_squared=0.2,
    )

    assert result.stopped_reason == "candidates_exhausted"
    assert result.blocking_term is BlockingTerm.VARIANCE
    assert result.final_schema.size == MINIMAL_SCHEMA.size


def test_augmentation_loop_reports_bias_blocked_when_pool_is_empty() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(2)
    sufficiency_test = _make_sufficiency_test(oracle, rng)

    result = augmentation_loop(
        MINIMAL_SCHEMA,
        [],
        sufficiency_test,
        lambda schema: 0.0,
        tolerance_bias_squared=0.2,
    )

    assert result.stopped_reason == "candidates_exhausted"
    assert result.blocking_term is BlockingTerm.BIAS


def test_augmentation_loop_stops_immediately_if_already_sufficient() -> None:
    oracle = KnownInsufficiencyOracle()
    rng = np.random.default_rng(3)
    sufficiency_test = _make_sufficiency_test(oracle, rng)

    result = augmentation_loop(
        MINIMAL_SCHEMA,
        [HIDDEN_CANDIDATE],
        sufficiency_test,
        lambda schema: 0.0,
        tolerance_bias_squared=1e9,  # trivially satisfied immediately
    )

    assert result.stopped_reason == "sufficient_at_tolerance"
    assert result.final_schema.size == MINIMAL_SCHEMA.size
    assert len(result.steps) == 1
