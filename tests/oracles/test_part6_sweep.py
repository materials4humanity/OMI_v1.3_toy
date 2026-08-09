"""Part 6's registered sweep, pinned.

The reported figures come from `scripts/run_v15_part6_sweep.py` at the module's declared
`N_REPLICATES` (24, the pre-registered count). These tests run at a reduced count so the suite
stays proportionate, and assert the **outcomes** — which is the part a later change could
silently break. The three criteria were checked to be met identically at 12, 16 and 24
replicates before this file was written.

Thresholds are imported, never restated (`tests.oracles.part6_thresholds`), so no assertion here
can drift from the pre-registration.
"""

from __future__ import annotations

import pytest

import tests.oracles.part6_sweep as sweep
import tests.oracles.part6_thresholds as thresholds
from tests.conftest import ObservationRecorder

TEST_REPLICATES = 12
"""Reduced from the pre-registered 24. Verified to give the same three outcomes at 12, 16 and
24 before this file existed — the *values* widen at the lower count, which is why the assertions
below are on outcomes and margins' signs rather than on magnitudes (CLAUDE.md §7)."""


@pytest.fixture(scope="module")
def result() -> sweep.SweepResult:
    return sweep.run_sweep(TEST_REPLICATES)


def test_the_sweep_evaluates_the_registered_contrast_and_no_other(
    result: sweep.SweepResult, observe: ObservationRecorder
) -> None:
    """The contrast is imported from the pre-registration and asserted inside `run_sweep`.

    Checked here as well because it is the one property that, if wrong, would make every number
    below meaningless while every number below still looked reasonable."""
    observe("part6_registered_contrast", list(thresholds.REGISTERED_CONTRAST), "insufficient vs noisy")
    observe("part6_noise_inflation", thresholds.NOISE_INFLATION, "the registered value, unchanged")
    assert thresholds.REGISTERED_CONTRAST == ("insufficient", "noisy")
    assert thresholds.NOISE_INFLATION == 1.160, (
        "the registered inflation factor has changed; the pre-registration commit is authoritative"
    )
    assert result.calibration_variance_insufficient > 0.0


def test_each_registered_criterion_is_met(
    result: sweep.SweepResult, observe: ObservationRecorder
) -> None:
    """The three criteria, **each recorded separately** with its own measured value, threshold and
    margin. Never a summary verdict: a single label is what would let a partial result read as a
    whole one."""
    for outcome in result.criteria:
        observe(
            f"part6_{outcome.name.split()[1]}_{outcome.name.split()[0]}",
            outcome.measured,
            f"{outcome.comparison} {outcome.threshold}",
        )
    unmet = [outcome.name for outcome in result.criteria if not outcome.met]
    observe("part6_unmet_criteria", unmet, "empty at 12, 16 and 24 replicates")
    assert not unmet, "; ".join(outcome.line() for outcome in result.criteria)


def test_the_framework_statistic_separates_the_two_nuisance_arms(
    result: sweep.SweepResult, observe: ObservationRecorder
) -> None:
    """The substantive content of the claim: the two arms carry equal unexplained scatter by
    construction, and only the biased one moves the statistic."""
    observe("part6_framework_z_insufficient_far", result.framework_mean_insufficient_far, "> noisy arm's")
    observe("part6_framework_z_noisy_far", result.framework_mean_noisy_far, "near the null arm's")
    observe("part6_framework_z_null_far", result.framework_mean_null_far, "reference E|Z| = 0.798")

    assert result.framework_mean_insufficient_far > result.framework_mean_noisy_far, (
        "the statistic reads the insufficiency arm no higher than the noise arm, which would mean "
        "it is responding to scatter rather than to bias"
    )
    assert result.framework_separation_far > result.framework_separation_near, (
        "the separation does not grow along the axis"
    )


def test_the_comparator_s_two_separations_are_reported_side_by_side(
    result: sweep.SweepResult, observe: ObservationRecorder
) -> None:
    """§5's pre-committed null handling: *blind* and *merely noisy* must be distinguishable in the
    output rather than in the interpretation.

    Both separations are recorded, and so is the ratio between them — which is marked in
    `part6_sweep.py` as computed **after** the run, because `comparator_reading`'s gate reuses
    criterion 3's ceiling for a second purpose and flipped on a hundredth at the registered
    replicate count. The label that fired is left as written; the discriminating quantity is
    reported beside it.
    """
    observe(
        "part6_comparator_separation_registered",
        result.comparator_separation_registered,
        f"< {thresholds.COMPARATOR_CEILING} (criterion 3)",
    )
    observe(
        "part6_comparator_separation_null_contrast",
        result.comparator_separation_null_contrast,
        "companion reading; not a criterion",
    )
    observe("part6_comparator_separation_ratio", result.comparator_separation_ratio, "> 1 — post-hoc")
    observe("part6_comparator_reading", result.comparator_reading, "recorded verbatim, whatever it says")
    observe(
        "part6_comparator_fitted_noise_by_arm",
        {
            "insufficient": result.comparator_mean_insufficient_far,
            "noisy": result.comparator_mean_noisy_far,
            "null": result.comparator_mean_null_far,
        },
        "insufficient and noisy close together, null below both",
    )

    assert result.comparator_separation_null_contrast > result.comparator_separation_registered, (
        "the comparator separates insufficiency from noise at least as well as from nothing, which "
        "would mean the registered claim's comparative half fails"
    )
    assert result.comparator_mean_noisy_far > result.comparator_mean_null_far, (
        "the comparator does not register the third arm's extra scatter at all, so the third arm "
        "is not the nuisance it was built to be"
    )


def test_the_calibration_holds_on_the_sweep_s_own_seeds(
    result: sweep.SweepResult, observe: ObservationRecorder
) -> None:
    """The arms were matched on innovation variance at seeds `2000..2023`; the sweep judges seeds
    `0..`. The match on the judged campaigns is therefore an **outcome**, and it is recorded
    because any residual mismatch is a small bias whose direction a reader is entitled to know.
    """
    mismatch = (
        result.calibration_variance_insufficient - result.calibration_variance_noisy
    ) / result.calibration_variance_insufficient
    observe("part6_calibration_variance_insufficient", result.calibration_variance_insufficient, "target")
    observe("part6_calibration_variance_noisy", result.calibration_variance_noisy, "matched to it")
    observe(
        "part6_calibration_relative_mismatch_signed",
        mismatch,
        "positive means the noise arm is the weaker nuisance — a bias toward the claim",
    )
    assert abs(mismatch) < 0.15, (
        f"the two arms' unexplained scatter differs by {mismatch:.1%} on the judged seeds, which is "
        "too far for them to be a matched pair; the construction, not the threshold, would need "
        "revisiting"
    )
