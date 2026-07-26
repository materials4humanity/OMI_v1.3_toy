"""Grouped train/test split (Spec §9.3; CLAUDE.md §5 invariant 6):
docs/ROADMAP.md M8 — "Grouped splits enforced at the data-loader level."
"""

from __future__ import annotations

import numpy as np

from omi.learning import TrainingRecord, grouped_train_test_split
from omi.operators import Control

_CONTROL = Control(0.0, 1.0, lambda t: np.array([1.0]))


def _make_records(n_groups: int, records_per_group: int) -> list[TrainingRecord]:
    records = []
    for g in range(n_groups):
        for _r in range(records_per_group):
            state = np.array([float(g)])
            records.append(
                TrainingRecord(
                    group_id=f"group{g}",
                    initial_state=state,
                    controls=(_CONTROL,),
                    true_trajectory=(state, state),
                )
            )
    return records


def test_no_group_straddles_both_train_and_test() -> None:
    records = _make_records(n_groups=10, records_per_group=3)
    train, test = grouped_train_test_split(records, test_fraction=0.3, rng=np.random.default_rng(0))

    train_groups = {r.group_id for r in train}
    test_groups = {r.group_id for r in test}
    assert train_groups.isdisjoint(test_groups)


def test_every_record_is_placed_exactly_once() -> None:
    records = _make_records(n_groups=8, records_per_group=2)
    train, test = grouped_train_test_split(records, test_fraction=0.25, rng=np.random.default_rng(1))
    assert len(train) + len(test) == len(records)
    assert set(id(r) for r in train).isdisjoint(set(id(r) for r in test))


def test_test_fraction_is_approximately_honoured_at_the_group_level() -> None:
    records = _make_records(n_groups=20, records_per_group=1)
    train, test = grouped_train_test_split(records, test_fraction=0.25, rng=np.random.default_rng(2))
    test_groups = {r.group_id for r in test}
    assert 3 <= len(test_groups) <= 7  # ~25% of 20 groups, some rounding slack


def test_split_is_deterministic_given_the_same_generator_seed() -> None:
    records = _make_records(n_groups=10, records_per_group=2)
    train_a, test_a = grouped_train_test_split(records, test_fraction=0.3, rng=np.random.default_rng(7))
    train_b, test_b = grouped_train_test_split(records, test_fraction=0.3, rng=np.random.default_rng(7))
    assert {r.group_id for r in train_a} == {r.group_id for r in train_b}
    assert {r.group_id for r in test_a} == {r.group_id for r in test_b}
