"""Part 6's registered sweep: the `INSUFFICIENT`-versus-`NOISY` contrast, judged against the
thresholds committed in an earlier commit.

Every threshold is **imported** from `tests.oracles.part6_thresholds` rather than restated, so a
value cannot drift between the pre-registration and the run. The registered contrast is imported
too, and asserted, so this module cannot quietly evaluate a different one.

The rule, from `docs/V1.5-PART6-PREREGISTRATION.md` §4.2, unchanged:

1. `separation(innovation_mean_z; I vs X) >= REQUIRED_SEPARATION` at `FAR_SAMPLES`
2. `growth(separation; NEAR -> FAR) >= REQUIRED_GROWTH`
3. `separation(gp_noise_excess_ratio; I vs X) < COMPARATOR_CEILING` at `FAR_SAMPLES`

**Each criterion is reported as met or not met, never folded into a single verdict** — the sweep's
brief is explicit about that, and a summary label is what would let a partial result read as a
whole one.

**The comparator's two separations are reported side by side** (§5's pre-committed null handling):
its reading on the registered contrast *and* on the insufficiency-versus-null contrast, so
"blind" and "merely noisy" are distinguishable in the output rather than in the interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.state import FloatArray

import tests.oracles.discovery_campaign as campaign
import tests.oracles.part6_thresholds as thresholds

SWEEP_SEEDS = tuple(range(campaign.N_REPLICATES))
"""Seeds `0 .. 23`, as the pre-registration declares. Disjoint from the calibration's
`2000 .. 2023` and from the null-distribution replicates' `1000 ..`, so no campaign both set a
threshold and is judged by one."""


@dataclass(frozen=True)
class CriterionOutcome:
    """One registered criterion, reported as met or not met with its own numbers.

    Never reduced to a boolean alone: the value, the threshold and the direction of the
    comparison all travel, because a criterion reported as a bare pass/fail cannot be audited
    against the pre-registration without re-running the sweep."""

    name: str
    measured: float
    threshold: float
    comparison: str
    """`">="` or `"<"` — the registered direction, so the reader does not have to infer it."""

    @property
    def met(self) -> bool:
        if self.comparison == ">=":
            return bool(self.measured >= self.threshold)
        if self.comparison == "<":
            return bool(self.measured < self.threshold)
        raise ValueError(f"unrecognised comparison {self.comparison!r}")

    @property
    def margin(self) -> float:
        """How far the measurement sits from its threshold, signed so positive is met.

        Reported whatever the outcome, on E-41's own discipline: a failing criterion's margin
        says whether it was close."""
        return (
            self.measured - self.threshold if self.comparison == ">=" else self.threshold - self.measured
        )

    def line(self) -> str:
        status = "MET" if self.met else "NOT MET"
        return (
            f"{self.name}: {self.measured:.4f} {self.comparison} {self.threshold} "
            f"-> {status} (margin {self.margin:+.4f})"
        )


@dataclass(frozen=True)
class SweepResult:
    """The registered sweep's full output. Every field is reported, met or not."""

    framework_separation_near: float
    framework_separation_far: float
    framework_growth: float
    framework_mean_insufficient_near: float
    framework_mean_insufficient_far: float
    framework_mean_noisy_near: float
    framework_mean_noisy_far: float
    framework_mean_null_far: float

    comparator_separation_registered: float
    """`gp_noise_excess_ratio`, `INSUFFICIENT` vs `NOISY` — criterion 3's quantity."""
    comparator_separation_null_contrast: float
    """The same statistic, `INSUFFICIENT` vs `NULL` — §5's pre-committed companion reading."""
    comparator_mean_insufficient_far: float
    comparator_mean_noisy_far: float
    comparator_mean_null_far: float

    calibration_variance_insufficient: float
    calibration_variance_noisy: float
    """The two arms' innovation variances **as realised on the sweep's own seeds**, so the
    match the calibration claimed can be checked on the campaigns actually judged rather than
    only on the calibration's."""

    best_found_insufficient: float
    best_found_noisy: float
    best_found_null: float
    """The campaigns' incumbent objectives — the comparator's *search* quality, reported because
    ADR-065 promises the GP searches well and omitting it would be arguing rather than
    measuring."""

    @property
    def criteria(self) -> tuple[CriterionOutcome, ...]:
        return (
            CriterionOutcome(
                "criterion 1  framework separation at far",
                self.framework_separation_far,
                thresholds.REQUIRED_SEPARATION,
                ">=",
            ),
            CriterionOutcome(
                "criterion 2  framework separation growth",
                self.framework_growth,
                thresholds.REQUIRED_GROWTH,
                ">=",
            ),
            CriterionOutcome(
                "criterion 3  comparator separation at far",
                self.comparator_separation_registered,
                thresholds.COMPARATOR_CEILING,
                "<",
            ),
        )

    @property
    def comparator_separation_ratio(self) -> float:
        """`separation(I vs NULL) / separation(I vs NOISY)` for the comparator.

        **Computed after the sweep ran, and marked as such.** It is not part of any registered
        criterion and it did not exist when :attr:`comparator_reading` was written. It is here
        because `comparator_reading`'s gate reuses criterion 3's `1.0` ceiling for a second,
        different purpose, and at the registered replicate count the null-contrast separation
        landed at `0.9937` — a hundredth below — so a crude gate flipped on nothing. That is the
        same "decided at machine precision" failure this repository filed as E-48 in another
        context, and the honest response is to report the quantity that actually discriminates
        rather than to rewrite the label that fired.

        `comparator_reading` is left exactly as it was written before the run. Both are reported.
        """
        registered = self.comparator_separation_registered
        if registered <= 0.0:
            return float("inf")
        return self.comparator_separation_null_contrast / registered

    @property
    def comparator_reading(self) -> str:
        """Which of §5's readings the comparator's own two separations support.

        The distinction the sweep's brief asks to be visible in the output: a comparator that
        cannot separate insufficiency from *nothing* is not evidence that it cannot *attribute*.
        """
        registered = self.comparator_separation_registered
        null_contrast = self.comparator_separation_null_contrast
        if null_contrast < thresholds.COMPARATOR_CEILING:
            return (
                "AMBIGUOUS: the comparator does not clear one sigma on the null contrast either, "
                "so it may be too noisy for either reading rather than unable to attribute"
            )
        if registered < thresholds.COMPARATOR_CEILING:
            return (
                "ATTRIBUTION-BLIND: the comparator separates insufficiency from nothing "
                f"({null_contrast:.4f} sigma) and not from noise ({registered:.4f} sigma)"
            )
        return (
            "ATTRIBUTING: the comparator separates insufficiency from noise "
            f"({registered:.4f} sigma), so the claim's comparative half fails"
        )


def _separation(arm_values: FloatArray, nuisance_values: FloatArray) -> float:
    """`|mean(arm) - mean(nuisance)| / sd(nuisance)` — nuisance-arm sigma units, ADR-057's
    convention, reused unchanged so every reading in Parts 5 and 6 sits on one scale."""
    return campaign.separation(arm_values, nuisance_values)


def run_sweep(n_replicates: int | None = None) -> SweepResult:
    """Run the registered sweep.

    Three arms on the same seeds — `INSUFFICIENT`, `NOISY` at the calibrated inflation, and
    `NULL` for the companion reading. Near and far are prefixes of one campaign per seed
    (ADR-066), so no seed-to-seed difference sits between the two lengths.
    """
    assert thresholds.REGISTERED_CONTRAST == ("insufficient", "noisy"), (
        "the registered contrast is not the one this sweep evaluates; the pre-registration is "
        "authoritative and a mismatch is a bug, not a choice"
    )
    seeds = SWEEP_SEEDS[: n_replicates or len(SWEEP_SEEDS)]

    insufficient = [campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.INSUFFICIENT, s) for s in seeds]
    noisy = [
        campaign.run_campaign(
            campaign.FAR_SAMPLES, campaign.Arm.NOISY, s, noise_inflation=thresholds.NOISE_INFLATION
        )
        for s in seeds
    ]
    null = [campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.NULL, s) for s in seeds]

    def framework(campaigns: list[campaign.Campaign], length: int) -> FloatArray:
        return np.array(
            [campaign.innovation_mean_report(c.prefix(length)).z for c in campaigns], dtype=np.float64
        )

    def comparator(campaigns: list[campaign.Campaign], length: int) -> FloatArray:
        return np.array(
            [campaign.gp_noise_report(c.prefix(length)).excess_ratio for c in campaigns],
            dtype=np.float64,
        )

    def innovation_variance(campaigns: list[campaign.Campaign]) -> float:
        return float(
            np.concatenate([np.concatenate([s.innovations for s in c.samples]) for c in campaigns]).var()
        )

    near, far = campaign.NEAR_SAMPLES, campaign.FAR_SAMPLES
    f_i_near, f_i_far = framework(insufficient, near), framework(insufficient, far)
    f_x_near, f_x_far = framework(noisy, near), framework(noisy, far)
    f_n_far = framework(null, far)
    c_i_far, c_x_far, c_n_far = comparator(insufficient, far), comparator(noisy, far), comparator(null, far)

    separation_near = _separation(f_i_near, f_x_near)
    separation_far = _separation(f_i_far, f_x_far)
    growth = (
        separation_far / separation_near
        if separation_near > 0.0
        else (float("inf") if separation_far > 0.0 else 1.0)
    )

    return SweepResult(
        framework_separation_near=separation_near,
        framework_separation_far=separation_far,
        framework_growth=growth,
        framework_mean_insufficient_near=float(f_i_near.mean()),
        framework_mean_insufficient_far=float(f_i_far.mean()),
        framework_mean_noisy_near=float(f_x_near.mean()),
        framework_mean_noisy_far=float(f_x_far.mean()),
        framework_mean_null_far=float(f_n_far.mean()),
        comparator_separation_registered=_separation(c_i_far, c_x_far),
        comparator_separation_null_contrast=_separation(c_i_far, c_n_far),
        comparator_mean_insufficient_far=float(c_i_far.mean()),
        comparator_mean_noisy_far=float(c_x_far.mean()),
        comparator_mean_null_far=float(c_n_far.mean()),
        calibration_variance_insufficient=innovation_variance(insufficient),
        calibration_variance_noisy=innovation_variance(noisy),
        best_found_insufficient=float(np.mean([campaign.best_found(c) for c in insufficient])),
        best_found_noisy=float(np.mean([campaign.best_found(c) for c in noisy])),
        best_found_null=float(np.mean([campaign.best_found(c) for c in null])),
    )
