"""The Part 5(1) §5.2 statistic dry-run: which candidate separates model insufficiency
from exploration noise, and does its reading **grow** along the axis (ADR-057,
docs/DECISIONS.md).

Structural assertions only, at a reduced replicate count so the suite stays fast. The
reported figures come from `scripts/run_v15_statistic_dry_run.py` at the module's declared
`N_REPLICATES`; what is asserted here is that the three **verdicts** are what the record
says, which is the part a later change could silently break. The verdicts were checked to
be identical at 16 and at 40 replicates before this file was written.

No threshold is fixed here. `REQUIRED_GROWTH` below is this file's own declared bar for
asserting that a candidate diverges *at all*; Part 6's pre-registration owns the
thresholds the real claim is judged against, in its own earlier commit (ADR-057).
"""

from __future__ import annotations

import numpy as np
import pytest

import tests.oracles.contrast_insufficiency as dryrun
from tests.conftest import ObservationRecorder

REQUIRED_GROWTH = 2.0
"""A doubling of the separation across the probe reach. Declared here, not imported from
a pre-registration that does not exist yet."""

TEST_REPLICATES = 16
"""Reduced from the module default so the suite cost stays proportionate.

Sixteen and not fewer, and the floor was found rather than chosen: at twelve replicates
`parameter_spread` flips from `ADVERSE` to `PARALLEL` — still rejected, but for a
different reason — so twelve is below the count at which the *reasons* are stable even
though the selection is. The assertions below are on verdicts and signs rather than on
values, because the values do widen."""


@pytest.fixture(scope="module")
def verdicts() -> tuple[dryrun.DryRunVerdict, ...]:
    original = dryrun.N_REPLICATES
    dryrun.N_REPLICATES = TEST_REPLICATES
    try:
        return dryrun.dry_run(required_growth=REQUIRED_GROWTH)
    finally:
        dryrun.N_REPLICATES = original


def _by_name(verdicts: tuple[dryrun.DryRunVerdict, ...], name: str) -> dryrun.DryRunVerdict:
    return next(v for v in verdicts if v.candidate == name)


def test_the_axis_carries_signal_and_the_signal_grows(
    verdicts: tuple[dryrun.DryRunVerdict, ...], observe: ObservationRecorder
) -> None:
    """E-41's first criterion, checked before any candidate is read.

    The planted insufficiency must actually move the observable, and move it *more* at the
    far depth — otherwise the axis is inert and every growth ratio below is measuring
    noise. Measured in units of the observation noise, so "the axis carries signal" is a
    statement about detectability rather than about a raw magnitude.
    """
    first = verdicts[0]
    observe("axis_signal_near_noise_widths", first.axis_signal_near, "> 1.0")
    observe("axis_signal_far_noise_widths", first.axis_signal_far, "> near, and > 1.0")

    assert first.axis_signal_near > 1.0, "the insufficiency is below the noise even at the near depth"
    assert first.axis_signal_far > first.axis_signal_near, (
        "the planted insufficiency does not grow with campaign depth, so campaign depth is "
        "an inert axis for it and no candidate can show a rising trend"
    )


def test_the_sufficiency_deficit_detects_perfectly_and_cannot_be_scored_for_divergence(
    verdicts: tuple[dryrun.DryRunVerdict, ...], observe: ObservationRecorder
) -> None:
    """**Candidate 1: a perfect detector whose divergence is undefined, and which falls.**

    Two findings in one measurement, and they pull in opposite directions.

    The deficit is *exactly zero* in every null-arm replicate — Spec §1.2's estimator is
    clamped at zero and a sufficient state leaves nothing above the clamp — so the null
    arm has no scatter, the sigma-unit separation is unbounded, and E-41's ratio criterion
    cannot be evaluated at all. That is a fourth failure mode E-41's three-verdict enum
    does not name, and it arises precisely *because* the statistic is a good detector.

    And on the one reading that is well defined — the candidate's own magnitude under Arm
    I — the deficit **falls** as the campaign deepens. The mechanism is not subtle: pairs
    matched on a declared state that has been evolving under the latent for longer are
    implicitly matched on the latent too, so the missing variable becomes *less* visible
    the further the campaign runs. A practitioner running the deficit late in a campaign
    concludes the state is sufficient.
    """
    deficit = _by_name(verdicts, "deficit")
    observe("deficit_verdict", deficit.verdict, "== SEPARATION_UNBOUNDED")
    observe("deficit_separation_near", deficit.separation_near, "not finite (null arm has no scatter)")
    observe("deficit_growth_ratio", deficit.growth_ratio, "nan -- criterion unevaluable")
    observe("deficit_arm_i_mean_near", deficit.arm_i_mean_near, "> arm_i_mean_far")
    observe("deficit_arm_i_mean_far", deficit.arm_i_mean_far, "< arm_i_mean_near")
    observe("deficit_arm_i_growth", deficit.arm_i_growth, "< 1.0 -- the statistic falls")

    assert deficit.verdict == dryrun.SEPARATION_UNBOUNDED
    assert not np.isfinite(deficit.separation_near)
    assert np.isnan(deficit.growth_ratio)
    assert deficit.arm_i_growth < 1.0, (
        "the deficit now rises with campaign depth, which would make it a viable candidate "
        "and reverse the mechanism recorded above"
    )


def test_the_innovation_bias_is_the_selected_candidate(
    verdicts: tuple[dryrun.DryRunVerdict, ...], observe: ObservationRecorder
) -> None:
    """**Candidate 2, selected: it separates the arms, diverges along the axis, and beats
    the Spec §9.3 baseline.**

    All three of E-41's criteria pass in order, and the win over the tabular baseline is
    real but not overwhelming — a gradient-boosted tree's own held-out residual scale is
    itself a strong insufficiency detector here, which is worth knowing before Part 6
    rests a claim on the chain-based statistic.

    Note what the selected statistic is *not*: it is the **signed** mean innovation, close
    to the CUSUM variant ADR-026 rejected as the default drift monitor, and not the NIS
    chi-squared statistic the repository actually implements. A sign-blind scale test
    passes a sequence biased by exactly the amount the model's own covariance predicts.
    """
    bias = _by_name(verdicts, "innovation_bias")
    observe("innovation_bias_verdict", bias.verdict, "== DISCRIMINATING")
    observe("innovation_bias_separation_near", bias.separation_near, "> 1.0 null-arm sigma")
    observe("innovation_bias_separation_far", bias.separation_far, "> baseline separation")
    observe("innovation_bias_growth_ratio", bias.growth_ratio, f"> {REQUIRED_GROWTH}")
    observe("innovation_bias_arm_i_growth", bias.arm_i_growth, "> 1.0 in its own units too")
    observe("baseline_separation_far", bias.baseline_separation_far, "narrative; the comparator")
    observe("baseline_growth_ratio", bias.baseline_growth, "narrative; the comparator's own divergence")

    assert bias.verdict == "DISCRIMINATING"
    assert bias.growth_ratio > REQUIRED_GROWTH, "the selected candidate does not diverge along the axis"
    assert bias.separation_far > bias.baseline_separation_far, (
        "the tabular baseline separates the arms at least as well at the far depth, so the "
        "chain-based statistic buys nothing and the selection is wrong"
    )
    assert bias.arm_i_growth > 1.0, (
        "the statistic's own magnitude does not rise with depth, so its separation growth "
        "is coming from a shrinking null arm rather than from a rising signal"
    )


def test_the_parameter_spread_is_beaten_by_the_tabular_baseline(
    verdicts: tuple[dryrun.DryRunVerdict, ...], observe: ObservationRecorder
) -> None:
    """**Candidate 3, rejected: it diverges, and a gradient-boosted tree does better.**

    An honest negative, and the reason is structural rather than a tuning failure. Only
    two of the declared operator's rates are identifiable from the one evaluable
    observation modality, and the rate the latent modulates that reaches the *target* —
    `porosity_rate` — is not among them: `potential` is a function of lithium inventory
    loss and interface resistance and of nothing else. So the parameter spread is fitted
    on the half of the defect the observation suite can see and evaluated on the
    observable, never on the target.

    That is not a refutation of ADR-055's parameter triage, which is designed against a
    declared **constitutive form** with named parameters and an out-of-envelope influence
    evaluation. It is a finding about this domain: the reduced form of the statistic that
    contrast can support is not the statistic ADR-055 specifies.
    """
    spread = _by_name(verdicts, "parameter_spread")
    observe("parameter_spread_verdict", spread.verdict, "== ADVERSE")
    observe("parameter_spread_separation_near", spread.separation_near, "narrative")
    observe("parameter_spread_separation_far", spread.separation_far, "<= baseline separation")
    observe("parameter_spread_growth_ratio", spread.growth_ratio, f"> {REQUIRED_GROWTH} but adverse anyway")
    observe("parameter_spread_arm_i_growth", spread.arm_i_growth, "narrative; near 1 -- barely moves")

    assert spread.verdict == "ADVERSE"
    assert spread.separation_far <= spread.baseline_separation_far, (
        "the parameter spread now beats the baseline, which would make it a second viable "
        "candidate and change the selection"
    )


def test_exactly_one_candidate_is_selected(
    verdicts: tuple[dryrun.DryRunVerdict, ...], observe: ObservationRecorder
) -> None:
    """The dry-run's purpose: pick a candidate and establish it is not inert.

    Reported as a set rather than as three separate outcomes, because "one of three
    passed" is the result and a later change that makes two pass is as much a problem as
    one that makes none pass — the dry-run would no longer be selecting.
    """
    outcomes = {v.candidate: v.verdict for v in verdicts}
    selected = [name for name, verdict in outcomes.items() if verdict == "DISCRIMINATING"]
    observe("all_verdicts", outcomes, "exactly one DISCRIMINATING")
    observe("selected_candidate", selected, "== ['innovation_bias']")
    observe("dry_run_summaries", [v.summary() for v in verdicts], "narrative; the full record")

    assert selected == ["innovation_bias"], (
        f"the dry-run no longer selects exactly one candidate: {outcomes}"
    )
