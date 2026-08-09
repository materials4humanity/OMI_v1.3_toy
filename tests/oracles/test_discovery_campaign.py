"""Part 6's gate checks on the discovery-domain campaign construction.

**These are the checks the gate authorises, and no more.** The pre-registered claim is a
comparison of the `INSUFFICIENT` arm against the `NOISY` arm; the `NOISY` arm is not
constructed or read anywhere in this file, because looking at it would be a peek at the
registered quantity (M11.5's pre-registration precedent, §5 of that document).

What is checked: that the planted insufficiency is a *state* insufficiency and moves the
observable; that E-41's evaluable criteria pass **on this domain** rather than only on
contrast; that the statistic's divergence matches the closed form ADR-066 predicted before
the run; that the monitor is calibrated on the null arm; and that the comparator is not a
straw man.

Replicate counts are reduced from the module defaults so the suite stays fast; the reported
figures come from `scripts/run_v15_part6_gate.py`. Assertions are on signs, orderings and
verdicts, per CLAUDE.md §7 — not on values, which widen at low replicate counts.
"""

from __future__ import annotations

import numpy as np
import pytest

import tests.oracles.discovery_campaign as campaign
from omi_domains.sdl.state import SDL_SCHEMA
from tests.conftest import ObservationRecorder

REQUIRED_GROWTH = 2.0
"""This file's own declared bar for asserting that a statistic diverges *at all*, carried over
from `tests/oracles/test_statistic_dry_run.py` so Part 5's and Part 6's gates read on one
scale. **Not** a pre-registered threshold: Part 6's pre-registration owns those, in its own
earlier commit."""

TEST_REPLICATES = 10
NULL_CALIBRATION_REPLICATES = 24


@pytest.fixture(scope="module")
def readings() -> tuple[campaign.VacuityReading, ...]:
    return campaign.vacuity_gate(n_replicates=TEST_REPLICATES)


@pytest.fixture(scope="module")
def insufficient_campaigns() -> tuple[campaign.Campaign, ...]:
    return tuple(
        campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.INSUFFICIENT, s)
        for s in range(TEST_REPLICATES)
    )


def _by_name(readings: tuple[campaign.VacuityReading, ...], name: str) -> campaign.VacuityReading:
    return next(r for r in readings if r.statistic == name)


def test_the_planted_defect_is_a_state_insufficiency_and_not_an_operator_error(
    observe: ObservationRecorder,
) -> None:
    """The construction's central property, checked rather than asserted in prose (ADR-066).

    `precursor_texture` must be **absent from the declared schema**, so that matching on the
    full declared state does not determine the future. Part 5(1)'s first construction failed
    exactly here — it planted a dependence on a *declared* component, Axiom S still held, and
    the sufficiency deficit was correctly zero.
    """
    names = {name for _, name, _ in SDL_SCHEMA.components}
    observe("sdl_schema_components", sorted(names), "must not contain precursor_texture")
    assert "precursor_texture" not in names, (
        "the planted latent is in the declared schema, which makes it an operator error rather "
        "than a state insufficiency — the object Spec §1's machinery does not address"
    )

    null = campaign.run_campaign(campaign.NEAR_SAMPLES, campaign.Arm.NULL, 0)
    insufficient = campaign.run_campaign(campaign.NEAR_SAMPLES, campaign.Arm.INSUFFICIENT, 0)
    observe("null_arm_textures", [s.texture for s in null.samples], "all exactly 0")
    observe(
        "insufficient_arm_textures",
        [s.texture for s in insufficient.samples],
        "all > 0 — a one-sided disorder density with a floor at zero",
    )
    assert all(s.texture == 0.0 for s in null.samples), "the null arm must plant nothing"
    assert all(s.texture > 0.0 for s in insufficient.samples), (
        "the latent is declared half-normal, so every draw is strictly positive; a zero-mean "
        "draw would make the population bias second order, which is the underpowered version "
        "of this construction the first attempt used"
    )


def test_the_axis_carries_signal_and_carries_more_of_it_at_the_far_length(
    readings: tuple[campaign.VacuityReading, ...], observe: ObservationRecorder
) -> None:
    """E-41's first criterion, re-verified **on the discovery domain** — the point of the gate.

    A statistic that discriminates on one chain and is inert on another is M11.4's failure, and
    Part 5(1)'s dry-run was on contrast. Note what the axis is here: the per-sample effect is
    constant by construction, and what grows is the accumulated evidence (see
    `discovery_campaign.axis_signal`).
    """
    first = readings[0]
    observe("discovery_axis_signal_near", first.axis_signal_near, "> 1.0 noise-widths")
    observe("discovery_axis_signal_far", first.axis_signal_far, "> near, and > 1.0")

    assert first.axis_signal_near > 1.0, "the planted insufficiency is below the noise even near"
    assert first.axis_signal_far > first.axis_signal_near, (
        "campaign length is an inert axis for the planted insufficiency, so no statistic on it "
        "can show a rising trend"
    )


def test_the_framework_statistic_diverges_on_the_discovery_domain(
    readings: tuple[campaign.VacuityReading, ...], observe: ObservationRecorder
) -> None:
    """E-41's second criterion for `innovation_mean_z` (ADR-063).

    **Two verdicts, on two contrasts, and the distinction is load-bearing.** With criterion 3
    omitted the verdict is `DIVERGING_BASELINE_DEFERRED`, which is not a pass — it names the
    criterion that was not evaluated. Criterion 3 *is* evaluable on the
    `INSUFFICIENT`-versus-`NULL` contrast, using the GP's separation on that same contrast, and
    it is evaluated: `DISCRIMINATING`. What remains deferred is criterion 3 on the **registered**
    contrast, `INSUFFICIENT`-versus-`NOISY`, where the baseline comparison *is* the claim and
    evaluating it now would be a peek (ADR-065). A favourable precondition on one contrast is
    not the claim on another.
    """
    reading = _by_name(readings, "innovation_mean_z")
    observe("discovery_innovation_separation_near", reading.separation_near, "in null-sigma units")
    observe("discovery_innovation_separation_far", reading.separation_far, "> near")
    observe("discovery_innovation_growth_ratio", reading.growth_ratio, f">= {REQUIRED_GROWTH}")
    observe(
        "discovery_innovation_verdict_deferred_criterion_3",
        reading.verdict(REQUIRED_GROWTH),
        "DIVERGING_BASELINE_DEFERRED",
    )
    observe(
        "discovery_innovation_verdict_on_the_null_contrast",
        campaign.gate_verdict(readings, REQUIRED_GROWTH),
        "DISCRIMINATING — all three criteria, INSUFFICIENT vs NULL only",
    )

    assert reading.verdict(REQUIRED_GROWTH) == "DIVERGING_BASELINE_DEFERRED", reading.summary()
    assert campaign.gate_verdict(readings, REQUIRED_GROWTH) == "DISCRIMINATING", (
        "on the INSUFFICIENT-vs-NULL contrast all three of E-41's criteria are evaluable, and "
        "the statistic must clear them there before the registered contrast is worth running: "
        + reading.summary()
    )


def test_the_divergence_matches_the_closed_form_predicted_before_the_run(
    insufficient_campaigns: tuple[campaign.Campaign, ...], observe: ObservationRecorder
) -> None:
    """ADR-066's closed form: a persistent bias makes `z_n` scale as `sqrt(n)`, so the growth
    ratio between the two campaign lengths is `sqrt(n_far / n_near)` — written down before
    anything ran, the way `tests/oracles/known_decaying_sensitivity.py` predicts the dominance
    ratio.

    **And the measurement narrows the prediction, which is the interesting part.** The pure
    `sqrt(n)` figure is a *lower bound* here, because the acquisition concentrates the campaign
    where the objective looks best and — under insufficiency — that is partly where the latent
    happened to help, so the per-sample bias itself grows along the axis. The check is therefore
    against `bias_growth * sqrt(n_far / n_near)`, with the pure form asserted as the floor.
    """
    near = [campaign.innovation_mean_report(c.prefix(campaign.NEAR_SAMPLES)) for c in insufficient_campaigns]
    far = [campaign.innovation_mean_report(c) for c in insufficient_campaigns]

    bias_near = abs(float(np.mean([r.signed_mean for r in near])))
    bias_far = abs(float(np.mean([r.signed_mean for r in far])))
    z_growth = float(np.mean([r.z for r in far]) / np.mean([r.z for r in near]))
    predicted_floor = campaign.predicted_growth_ratio()
    predicted_with_selection = (bias_far / bias_near) * predicted_floor

    observe("discovery_bias_growth", bias_far / bias_near, "> 1 — acquisition selection")
    observe("discovery_z_growth_measured", z_growth, f">= {predicted_floor} (closed-form floor)")
    observe("discovery_z_growth_predicted", predicted_with_selection, "within 25% of measured")

    assert z_growth >= predicted_floor * 0.9, (
        f"the statistic grows more slowly than sqrt(n) ({z_growth:.3f} against "
        f"{predicted_floor:.3f}), which means the bias is not persistent — most likely absorbed "
        "by within-sample assimilation, in which case the construction needs the bias made "
        "structural, not the threshold made loose"
    )
    assert abs(z_growth - predicted_with_selection) < 0.25 * predicted_with_selection, (
        f"measured growth {z_growth:.3f} against predicted {predicted_with_selection:.3f}"
    )
    assert all(r.direction == "model_over_predicts" for r in far), (
        "a disorder density that accelerates coarsening must make the declared model "
        "over-predict activity; the other sign would mean the latent enters with the wrong sense"
    )


def test_the_monitor_is_calibrated_on_the_null_arm(observe: ObservationRecorder) -> None:
    """ADR-063 declares the standard normal as the reference distribution, and E-49's finding —
    a monitor calibrated per window and consumed per campaign — is the reason to check it here
    rather than assume it.

    The two quantities that matter: the innovation spread against the filter's **own** predicted
    spread (which is what makes `z` standardised at all), and the null distribution of `z`
    against `E|Z| = sqrt(2/pi) = 0.798`.
    """
    innovations = []
    variances = []
    z_values = []
    for seed in range(NULL_CALIBRATION_REPLICATES):
        realised = campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.NULL, 1000 + seed)
        report = campaign.innovation_mean_report(realised)
        z_values.append(report.z)
        innovations.append(np.concatenate([s.innovations for s in realised.samples]))
        variances.append(np.concatenate([s.predicted_variance for s in realised.samples]))

    pooled = np.concatenate(innovations)
    predicted_sd = float(np.sqrt(np.concatenate(variances).mean()))
    dispersion = float(pooled.std() / predicted_sd)
    z_mean = float(np.mean(z_values))

    observe("discovery_null_innovation_dispersion", dispersion, "~1.0: realised sd / predicted sd")
    observe("discovery_null_z_mean", z_mean, "compare E|Z| = 0.798")
    observe("discovery_null_z_q95", float(np.quantile(z_values, 0.95)), "compare |Z| 95% = 1.96")

    assert 0.9 < dispersion < 1.1, (
        f"the filter's predicted innovation spread is off by {dispersion:.3f}x, so `z` is not "
        "standardised and the declared normal reference is the wrong one"
    )
    assert z_mean < 2.0 * 0.798, (
        f"the null arm's own statistic reads {z_mean:.3f} against a theoretical 0.798, which "
        "would make a normal-quantile control limit anti-conservative"
    )


def test_the_comparator_is_not_a_straw_man(
    readings: tuple[campaign.VacuityReading, ...], observe: ObservationRecorder
) -> None:
    """ADR-065 states in advance that the GP is expected to do several things well, and Spec
    §9.3's requirement is a *fair* baseline. This records the evidence rather than the promise.

    **The substantive check is the comparator's null-arm calibration, not a separation
    threshold.** A separation is a ratio and can be small because its denominator is large; what
    says the GP is a real instrument is that with nothing planted its fitted noise **equals the
    declared instrument precision**, and with an insufficiency planted it reads above it. Those
    two facts are what a fair opponent looks like.

    An earlier version of this test asserted `separation_far > 1.0`. At the reduced replicate
    count it passed; at the module's own count it reads ≈ 1.0 and the assertion was marginal.
    It was replaced with the calibration check rather than loosened — a threshold that a
    higher-fidelity run walks up to is a threshold measuring the wrong thing.
    """
    gp = _by_name(readings, "gp_noise_excess_ratio")
    observe("discovery_gp_null_excess_ratio_far", gp.null_mean_far, "~1.0 — correctly calibrated")
    observe("discovery_gp_excess_ratio_far", gp.mean_far, "> null arm's, and > 1.0")
    observe("discovery_gp_separation_far", gp.separation_far, "recorded, not asserted")
    observe("discovery_gp_growth_ratio", gp.growth_ratio, "recorded, not asserted")

    assert 0.75 < gp.null_mean_far < 1.35, (
        f"with nothing planted the GP's fitted noise reads {gp.null_mean_far:.3f} times the "
        "declared instrument precision; an opponent that misreads a known noise level is not a "
        "fair one in either direction"
    )
    assert gp.mean_far > gp.null_mean_far, (
        "the GP's fitted noise does not rise at all under a planted insufficiency, which would "
        "make it inert rather than absorbing — and an inert comparator makes the registered "
        "claim untestable rather than true"
    )
    assert gp.mean_far > 1.0, (
        "the GP's fitted noise is below the declared instrument precision even under a planted "
        "insufficiency, which would mean it is not absorbing the extra variance at all"
    )


def test_the_campaign_actually_optimises(observe: ObservationRecorder) -> None:
    """The comparator's *search* quality, reported because ADR-065 promises the GP searches well
    and a report that omitted it would be arguing rather than measuring.

    A campaign whose incumbent never improved would mean the acquisition is not working, and
    every diagnostic downstream would be reading a random design rather than a campaign.
    """
    realised = campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.NULL, 0)
    initial_best = max(
        float(s.observed_turnover[-1]) for s in realised.samples[: campaign.INITIAL_DESIGN]
    )
    final_best = campaign.best_found(realised)

    observe("discovery_initial_design_best", initial_best, "< final best")
    observe("discovery_campaign_best", final_best, "> initial design best")
    assert final_best > initial_best, (
        "the GP-EI acquisition never improved on its own random initial design, so the campaign "
        "is not a campaign and no diagnostic computed over it means what it says"
    )
