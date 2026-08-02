"""M11.5's gate: the fair-axis experiment's design properties hold, and its
negative result is pinned as *informative* — the thing M11.4's was not
(ADR-047, docs/DECISIONS.md; `docs/M11.5-EXTRAPOLATION.md`; E-41, E-42).

These tests assert the experiment's **structure and mechanism**, not its headline
numbers: the withheld term is inert in-envelope and active outside, every held-out
point is outside the declared window, the declared form is *not* constant along
this axis (M11.4's fault, absent here), the free-form contestant is a genuine
operator rather than a surface extrapolated linearly, and the declared forms' loss
is error cancellation rather than ignorance of their own physics.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.baseline import GradientBoostedTreeRegressor, root_mean_squared_error
from omi_domains.flagship_constitutive import strain_experiment as sx
from omi_domains.flagship_constitutive.experiment import Query
from omi_domains.flagship_constitutive.forms import KOCKS_MECKING_STRAIN_WINDOWED

from tests.conftest import ObservationRecorder

N_TRAIN = 120
N_EVAL = 400


def _train_and_fit() -> tuple[list[Query], sx.Contestant, sx.Contestant]:
    train = sx.sample_queries(N_TRAIN, np.random.default_rng(1000))
    y_train = sx.labels(train, sx.TRAIN_STRAINS)
    return train, sx.fit_free_form(train, y_train), sx.fit_correct_form(train, y_train)


def test_the_withheld_term_is_zero_in_envelope_and_active_outside(
    observe: ObservationRecorder,
) -> None:
    """Generator C's design property (ADR-047), carried over from Generator A: the
    withheld recrystallisation term vanishes over the whole training region, so
    contestant 2's form is *exactly* the generator's there. Past the critical strain
    it bites."""
    queries = sx.sample_queries(200, np.random.default_rng(0))
    magnitudes = {}
    for name, strains in (("in_envelope", sx.TRAIN_STRAINS), ("held_out", sx.HELD_OUT_STRAINS)):
        full = sx.labels(queries, strains)
        clean = sx.labels(queries, strains, k_drx=0.0)
        magnitudes[name] = float(np.mean(np.abs(full - clean)))
    observe(
        "m11_5_withheld_term_magnitude",
        magnitudes,
        "identically zero in-envelope by construction; large outside",
    )
    assert magnitudes["in_envelope"] == pytest.approx(0.0, abs=1e-12)
    assert magnitudes["held_out"] > 1.0


def test_every_held_out_point_is_outside_the_declared_window(
    observe: ObservationRecorder,
) -> None:
    """ADR-045 requires the held-out region to lie outside the declared validity
    range, so the extrapolation report is exercised rather than merely present."""
    queries = sx.sample_queries(50, np.random.default_rng(7000))
    factors = [
        KOCKS_MECKING_STRAIN_WINDOWED.report(
            {
                "strain_rate": q.strain_rate,
                "temperature": q.temperature,
                "stored_density": q.rho_0,
                "accumulated_strain": strain,
            }
        ).worst_factor
        for strain in sx.HELD_OUT_STRAINS
        for q in queries
    ]
    observe(
        "m11_5_held_out_extrapolation_factors",
        {"min": min(factors), "median": float(np.median(factors)), "max": max(factors)},
        "all > 1: every held-out point is outside the declared strain window",
    )
    assert min(factors) > 1.0


def test_the_declared_form_is_not_constant_along_this_axis(
    observe: ObservationRecorder,
) -> None:
    """**M11.4's fault, shown absent.** There the declared form predicted the same
    value everywhere along the held-out axis, which is why the comparison could not
    discriminate. Here the declared form's prediction varies strongly with
    accumulated strain, and — the part that matters — it varies *differently* from
    the free-form baseline's.
    """
    _, free_form, correct = _train_and_fit()
    probe = sx.sample_queries(200, np.random.default_rng(4242))
    declared = correct.predict(probe, sx.HELD_OUT_STRAINS)
    baseline = free_form.predict(probe, sx.HELD_OUT_STRAINS)

    declared_spread = float(np.ptp(declared.mean(axis=1)))
    disagreement_near = root_mean_squared_error(declared[0], baseline[0])
    disagreement_far = root_mean_squared_error(declared[-1], baseline[-1])

    observe(
        "m11_5_declared_form_varies_along_the_axis",
        {
            "declared_form_spread": declared_spread,
            "disagreement_at_nearest_held_out_strain": disagreement_near,
            "disagreement_at_furthest": disagreement_far,
        },
        "declared form varies along the axis, and diverges from the baseline across it",
    )
    assert declared_spread > 1.0
    assert disagreement_far > disagreement_near


def test_the_free_form_contestant_is_an_operator_not_a_scaled_surface(
    observe: ObservationRecorder,
) -> None:
    """ADR-047's fairness requirement, asserted rather than asserted-about.

    M11.4's contestant 1 predicted `surface(q) × γ`, exactly linear in accumulated
    strain, which on a strain hold-out is a straw man. This one is an integrated rate
    law, so its prediction must be **sublinear** in γ where the truth saturates —
    which is only possible for a model that can represent a negative rate.
    """
    _, free_form, _ = _train_and_fit()
    probe = sx.sample_queries(200, np.random.default_rng(4242))
    predicted = free_form.predict(probe, (1.0, 6.0)).mean(axis=1)
    linear_extrapolation = predicted[0] * 6.0
    ratio = float(predicted[1] / linear_extrapolation)
    observe(
        "m11_5_free_form_is_sublinear_in_strain",
        {"at_gamma_1": float(predicted[0]), "at_gamma_6": float(predicted[1]),
         "linear_would_give": float(linear_extrapolation), "ratio": ratio},
        "far below a linear-in-strain extrapolation: the baseline saturates",
    )
    assert ratio < 0.5


def test_the_declared_forms_lose_by_cancellation_not_by_ignorance(
    observe: ObservationRecorder,
) -> None:
    """**E-42's mechanism, measured.** The correct declared form is exactly right
    about the physics it expresses and still loses the registered criterion, because
    its competitors' extrapolation errors partially cancel the withheld term and its
    own do not.

    Asserted qualitatively (CLAUDE.md §7): the declared form must be the *better* of
    the two against the withheld-free truth and the *worse* against the full truth,
    and the winner's cancellation must be visible as a signed bias of opposite sign
    to its full-truth bias. The figures are recorded, not frozen.
    """
    train, _, correct = _train_and_fit()
    y_train = sx.labels(train, sx.TRAIN_STRAINS)
    winner = sx.fit_tabular(train, y_train, GradientBoostedTreeRegressor())

    held = sx.sample_queries(N_EVAL, np.random.default_rng(7000))
    full = sx.labels(held, sx.HELD_OUT_STRAINS)
    clean = sx.labels(held, sx.HELD_OUT_STRAINS, k_drx=0.0)
    withheld_bias = float(np.mean(full - clean))

    scores = {}
    for contestant in (correct, winner):
        predicted = contestant.predict(held, sx.HELD_OUT_STRAINS)
        scores[contestant.label] = {
            "rmse_vs_full": root_mean_squared_error(predicted, full),
            "rmse_vs_withheld_free": root_mean_squared_error(predicted, clean),
            "bias_vs_withheld_free": float(np.mean(predicted - clean)),
            "bias_vs_full": float(np.mean(predicted - full)),
        }

    observe(
        "m11_5_ranking_inverts_between_the_two_truths",
        {"withheld_term_signed_effect": withheld_bias, **scores},
        "declared form best on the physics it expresses, worse on the registered criterion",
    )

    declared = scores[correct.label]
    baseline = scores[winner.label]
    # Right about its own physics...
    assert declared["rmse_vs_withheld_free"] < baseline["rmse_vs_withheld_free"]
    # ...and still loses the registered criterion.
    assert declared["rmse_vs_full"] > baseline["rmse_vs_full"]
    # The winner's error against the expressible physics points the same way as the
    # withheld term, which is what cancellation means.
    assert baseline["bias_vs_withheld_free"] * withheld_bias > 0.0
    # And cancellation leaves it closer to the full truth than to the clean one.
    assert abs(baseline["bias_vs_full"]) < abs(baseline["bias_vs_withheld_free"])


def test_a_missing_mechanism_is_far_worse_than_a_missing_dependence(
    observe: ObservationRecorder,
) -> None:
    """§3's actionable finding: the two misspecification arms are not comparable, and
    the gap is in the direction of harm. 3a cannot saturate, so its error grows
    without bound along the held-out axis; 3b's does not."""
    train = sx.sample_queries(N_TRAIN, np.random.default_rng(1000))
    y_train = sx.labels(train, sx.TRAIN_STRAINS)
    mechanism = sx.fit_missing_mechanism(train, y_train)
    dependence = sx.fit_missing_dependence(train, y_train)

    held = sx.sample_queries(N_EVAL, np.random.default_rng(7000))
    full = sx.labels(held, sx.HELD_OUT_STRAINS)
    errors = {
        c.label: root_mean_squared_error(c.predict(held, sx.HELD_OUT_STRAINS), full)
        for c in (mechanism, dependence)
    }
    per_strain = {
        c.label: [
            root_mean_squared_error(c.predict(held, sx.HELD_OUT_STRAINS)[i], full[i])
            for i in range(len(sx.HELD_OUT_STRAINS))
        ]
        for c in (mechanism, dependence)
    }
    observe(
        "m11_5_misspecification_kind_matters",
        {"pooled": errors, "per_strain": per_strain, "strains": list(sx.HELD_OUT_STRAINS)},
        "missing mechanism an order of magnitude worse, and growing with strain",
    )
    assert errors[mechanism.label] > 5.0 * errors[dependence.label]
    # A model with no removal term cannot saturate: its error must grow across the
    # held-out range, where the one that retains a removal term stays bounded.
    growth = per_strain[mechanism.label][-1] / per_strain[mechanism.label][0]
    assert growth > 5.0
