"""The hold-out-discrimination check, retro-validated against the axis that
produced the defect it exists to prevent (ADR-045 as amended, docs/DECISIONS.md;
`docs/V1.4-EDITS.md` E-39, E-41).

A check that refuses nothing is decoration. The evidence that this one is
discriminating is that, run with identical discipline on the two axes this
repository has actually held out, it **refuses M11.4's and admits M11.5's** — and
that the criterion E-39 originally proposed does neither, because the two axes'
disagreement magnitudes are the same order.

These tests are part of M11.5's pre-registration: they run before any sweep code
exists, because a precondition that has not itself been verified cannot gate
anything.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.baseline import root_mean_squared_error
from omi.state import FloatArray
from omi.proposed.holdout import (
    HoldOutDiscriminationReport,
    HoldOutVerdict,
    check_hold_out_discriminates,
)
from omi_domains.flagship_constitutive import experiment as rate_axis
from omi_domains.flagship_constitutive import strain_experiment as strain_axis

from tests.conftest import ObservationRecorder

M11_4_FIT_RATES = (1.0e-2, 1.0)
"""M11.4's in-envelope training rates, restricted to their lower half so the dry
run has somewhere in-envelope left to probe — the same discipline M11.5's own
check uses on its axis."""
M11_4_NEAR_RATE = 1.0
M11_4_FAR_RATE = 5.0
"""Upper edge of the fitted region, and upper edge of M11.4's in-envelope range.
Both inside `KOCKS_MECKING`'s declared window; the true hold-out (rates 20–200) is
never touched."""


def _m11_4_axis_report(required_divergence: float = strain_axis.REQUIRED_DIVERGENCE) -> HoldOutDiscriminationReport:
    """Run the check on M11.4's strain-rate axis, using M11.4's own generator and
    contestants unmodified."""
    train = rate_axis.sample_queries(120, M11_4_FIT_RATES, np.random.default_rng(1000))
    y_train = rate_axis.labels(train)
    candidate = rate_axis.fit_correct_form(train, y_train)
    baseline = rate_axis.fit_free_form(train, y_train)

    noise_floor = max(
        root_mean_squared_error(np.array([candidate.predict(q, 1.0) for q in train]), y_train),
        root_mean_squared_error(np.array([baseline.predict(q, 1.0) for q in train]), y_train),
    )

    shape = rate_axis.sample_queries(400, (1.0, 1.0001), np.random.default_rng(3000))

    def at(rate: float) -> tuple[FloatArray, FloatArray, FloatArray]:
        probe = [
            rate_axis.Query(rho_0=q.rho_0, strain_rate=rate, temperature=q.temperature)
            for q in shape
        ]
        # Generator A's withheld drag term is identically zero below its reference
        # rate, so in-envelope labels ARE the withheld-free truth.
        return (
            np.array([candidate.predict(q, 1.0) for q in probe]),
            np.array([baseline.predict(q, 1.0) for q in probe]),
            rate_axis.labels(probe),
        )

    candidate_near, baseline_near, clean_near = at(M11_4_NEAR_RATE)
    candidate_far, baseline_far, clean_far = at(M11_4_FAR_RATE)
    return check_hold_out_discriminates(
        axis="strain_rate",
        candidate_near=candidate_near,
        baseline_near=baseline_near,
        candidate_far=candidate_far,
        baseline_far=baseline_far,
        truth_without_withheld_term_near=clean_near,
        truth_without_withheld_term_far=clean_far,
        noise_floor=noise_floor,
        required_divergence=required_divergence,
    )


def _m11_5_axis_report() -> HoldOutDiscriminationReport:
    return strain_axis.dry_run_discrimination(
        rng_train=np.random.default_rng(1000), rng_probe=np.random.default_rng(3000)
    )


def test_the_check_refuses_m11_4_s_axis(observe: ObservationRecorder) -> None:
    """**The retro-validation.** Applied to the axis that produced E-39, the check
    refuses it — and refuses it for the right reason.

    Kocks–Mecking has no strain-rate dependence, and neither does Generator A's
    truth once the withheld drag term is removed, so the axis carries *exactly* no
    signal: there was nothing along it for any model to be right or wrong about.
    """
    report = _m11_4_axis_report()
    observe(
        "m11_4_axis_discrimination",
        {
            "axis_signal": report.axis_signal,
            "disagreement_near": report.disagreement_near,
            "disagreement_far": report.disagreement_far,
            "divergence": report.divergence,
            "candidate_error": report.candidate_error,
            "baseline_error": report.baseline_error,
            "verdict": report.verdict.value,
        },
        "refused: the withheld-free truth is exactly constant along the strain-rate axis",
    )
    assert not report.usable
    assert report.verdict is HoldOutVerdict.INERT_AXIS
    assert report.axis_signal == pytest.approx(0.0, abs=1e-12)


def test_m11_4_s_axis_fails_every_criterion_not_only_the_first(
    observe: ObservationRecorder,
) -> None:
    """The check short-circuits at the first failure, so the verdict alone
    understates how badly that axis was suited. Measured individually, M11.4's axis
    fails all three: the truth is constant along it, the two models are parallel,
    and the declared form is the *worse* of the two at the physics it does express.

    The third is the one that stings and it is why `ADVERSE` exists as a separate
    verdict: on that axis, declaring the form was a liability.
    """
    report = _m11_4_axis_report()
    observe(
        "m11_4_axis_fails_all_three_criteria",
        {
            "inert": report.axis_signal <= report.noise_floor,
            "parallel": report.divergence < report.required_divergence,
            "adverse": report.candidate_error > report.baseline_error,
            "content_ratio": report.content_ratio,
        },
        "all three criteria fail independently",
    )
    assert report.axis_signal <= report.noise_floor
    assert report.divergence < report.required_divergence
    assert report.candidate_error > report.baseline_error


def test_the_check_admits_m11_5_s_axis(observe: ObservationRecorder) -> None:
    """M11.5's accumulated-strain axis passes, with margin, on data that never
    touches the region the sweep will hold out."""
    report = _m11_5_axis_report()
    observe(
        "m11_5_axis_discrimination",
        {
            "axis_signal": report.axis_signal,
            "disagreement_near": report.disagreement_near,
            "disagreement_far": report.disagreement_far,
            "divergence": report.divergence,
            "required_divergence": report.required_divergence,
            "candidate_error": report.candidate_error,
            "baseline_error": report.baseline_error,
            "noise_floor": report.noise_floor,
            "verdict": report.verdict.value,
        },
        "admitted: the truth varies along the axis and the two models diverge along it",
    )
    assert report.usable
    assert report.verdict is HoldOutVerdict.DISCRIMINATING
    assert report.divergence > report.required_divergence


def test_disagreement_magnitude_cannot_separate_the_two_axes(
    observe: ObservationRecorder,
) -> None:
    """**E-41, asserted rather than asserted-about.**

    E-39 proposed the precondition as "the candidate and the baselines make
    materially different predictions across the held-out region". The two axes'
    far-point disagreements are the same order of magnitude, so **no threshold on
    that quantity admits the usable axis without also admitting the vacuous one**.
    The wording is inoperable, not merely imprecise.

    Divergence separates them by more than an order of magnitude, which is why the
    implemented criterion is about growth.
    """
    vacuous = _m11_4_axis_report()
    usable = _m11_5_axis_report()

    observe(
        "magnitude_does_not_separate_but_divergence_does",
        {
            "vacuous_axis_disagreement_far": vacuous.disagreement_far,
            "usable_axis_disagreement_far": usable.disagreement_far,
            "magnitude_ratio": usable.disagreement_far / vacuous.disagreement_far,
            "vacuous_axis_divergence": vacuous.divergence,
            "usable_axis_divergence": usable.divergence,
            "divergence_ratio": usable.divergence / vacuous.divergence,
        },
        "magnitudes within a small factor; divergences separated by more than 10x",
    )

    # Same order of magnitude: any magnitude bar admitting one admits the other.
    assert 0.2 < usable.disagreement_far / vacuous.disagreement_far < 5.0
    # Divergence, by contrast, separates them decisively.
    assert usable.divergence / vacuous.divergence > 10.0


def test_the_check_refuses_a_probe_it_cannot_read(observe: ObservationRecorder) -> None:
    """A precondition that silently returns a verdict on degenerate input is worse
    than none (CLAUDE.md §4's preference for refusing over guessing)."""
    ones = np.ones(4)
    common = dict(
        axis="x",
        candidate_near=ones,
        baseline_near=ones,
        candidate_far=ones,
        baseline_far=ones,
        truth_without_withheld_term_near=ones,
        truth_without_withheld_term_far=ones,
        noise_floor=0.0,
    )
    refusals = 0
    for kwargs in (
        {**common, "required_divergence": 0.5},
        {**common, "required_divergence": 2.0, "noise_floor": -1.0},
        {**common, "required_divergence": 2.0, "candidate_far": np.ones(3)},
        {**common, "required_divergence": 2.0, **{k: np.array([]) for k in (
            "candidate_near", "baseline_near", "candidate_far", "baseline_far",
            "truth_without_withheld_term_near", "truth_without_withheld_term_far")}},
    ):
        with pytest.raises(ValueError):
            check_hold_out_discriminates(**kwargs)  # type: ignore[arg-type]
        refusals += 1
    observe("holdout_check_refusals", refusals, "all four degenerate inputs raise")
    assert refusals == 4
