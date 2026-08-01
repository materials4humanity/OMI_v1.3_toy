"""M11.4's gate: the extrapolation experiment's design properties hold, and the
null it produced is pinned as *uninformative* rather than as evidence
(ADR-045, docs/DECISIONS.md; `docs/M11.4-EXTRAPOLATION.md`; E-39).

These tests assert the experiment's **structure**, not the headline numbers: the
hold-out really is outside the declared window, the withheld term really is absent
in-envelope and active out of it, and — the finding — the held-out axis is one
along which the declared form makes no differing prediction, which is what made
the comparison vacuous.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.baseline import root_mean_squared_error
from omi_domains.flagship_constitutive import experiment as exp
from omi_domains.flagship_constitutive.forms import KOCKS_MECKING

from tests.conftest import ObservationRecorder


def test_the_withheld_term_is_zero_in_envelope_and_active_outside(
    observe: ObservationRecorder,
) -> None:
    """Generator A's design property (ADR-045): the withheld drag term vanishes over
    the whole training region, so contestant 2's form is *exactly* the generator's
    there and its in-envelope error is parameter estimation only. Above the
    reference rate the term bites."""
    rng = np.random.default_rng(0)
    for region, expect_active in ((exp.IN_ENVELOPE_RATE, False), (exp.HELD_OUT_RATE, True)):
        queries = exp.sample_queries(200, region, rng)
        with_term = exp.labels(queries)
        saved = exp.GEN_K_DRAG
        try:
            exp.GEN_K_DRAG = 0.0
            without = exp.labels(queries)
        finally:
            exp.GEN_K_DRAG = saved
        magnitude = float(np.mean(np.abs(with_term - without)))
        observe(
            f"withheld_term_magnitude_{'held_out' if expect_active else 'in_envelope'}",
            magnitude,
            "identically zero in-envelope by construction; large outside",
        )
        if expect_active:
            assert magnitude > 1.0
        else:
            assert magnitude == pytest.approx(0.0, abs=1e-12)


def test_every_held_out_query_is_outside_the_declared_window(
    observe: ObservationRecorder,
) -> None:
    """ADR-045 requires the held-out region to lie outside the declared validity
    range, so the extrapolation report is exercised rather than merely present."""
    queries = exp.sample_queries(400, exp.HELD_OUT_RATE, np.random.default_rng(7000))
    factors = [
        KOCKS_MECKING.report(
            {"strain_rate": q.strain_rate, "temperature": q.temperature, "stored_density": q.rho_0}
        ).worst_factor
        for q in queries
    ]
    observe(
        "held_out_extrapolation_factors",
        {"min": min(factors), "median": float(np.median(factors)), "max": max(factors)},
        "all > 1: every evaluation point is outside the declared range",
    )
    assert min(factors) > 1.0


def test_the_declared_form_is_constant_along_the_held_out_axis(
    observe: ObservationRecorder,
) -> None:
    """**E-39's mechanism, asserted rather than asserted-about.**

    Kocks–Mecking has no strain-rate dependence, so along the axis M11.4 held out,
    the declared form predicts the same value everywhere. That is why the comparison
    could not discriminate: the candidate and the baseline agree by construction
    across the held-out region, and Spec §9.3 never requires that they should not.
    """
    # The declared form itself, swept along the held-out axis with every other
    # argument held fixed.
    rates = np.geomspace(exp.HELD_OUT_RATE[0], exp.HELD_OUT_RATE[1], 20)
    declared = np.array(
        [
            np.asarray(
                KOCKS_MECKING.evaluate(
                    {"stored_density": 3.0, "strain_rate": float(rate), "temperature": 900.0}
                )
            ).item()
            for rate in rates
        ]
    )

    # And the *fitted* contestant that carries that form, so the property is shown
    # to survive parameter estimation rather than holding only for the bare callable.
    train = exp.sample_queries(120, exp.IN_ENVELOPE_RATE, np.random.default_rng(1000))
    correct = exp.fit_correct_form(train, exp.labels(train))
    fitted = np.array(
        [
            correct.predict(exp.Query(rho_0=3.0, strain_rate=float(rate), temperature=900.0), 1.0)
            for rate in rates
        ]
    )

    # The generator, swept identically, does vary — otherwise the held-out axis
    # would carry no signal at all and the comparison would be vacuous for a
    # second, less interesting reason.
    truth = np.array([exp.generator_a(3.0, float(rate), 900.0) for rate in rates])

    observe(
        "declared_form_spread_across_held_out_axis",
        {
            "declared_form": float(np.ptp(declared)),
            "fitted_correct_form": float(np.ptp(fitted)),
            "generator": float(np.ptp(truth)),
        },
        "declared and fitted spreads exactly zero; generator's is not",
    )
    assert float(np.ptp(declared)) == pytest.approx(0.0, abs=1e-12)
    assert float(np.ptp(fitted)) == pytest.approx(0.0, abs=1e-12)
    assert float(np.ptp(truth)) > 1.0


def test_the_null_is_uninformative_because_every_error_is_the_withheld_term(
    observe: ObservationRecorder,
) -> None:
    """The measurement behind E-39 and behind `docs/M11.4-EXTRAPOLATION.md` §2.

    Two facts together make the null uninformative rather than negative. Every
    contestant's held-out error is essentially the withheld term's own magnitude,
    and against a ground truth with that term removed the **free-form** arm beats
    the **correct declared form** — because along the held-out axis there is no
    physics for the declared form to know.

    Asserted qualitatively (CLAUDE.md §7): the spread must be small relative to the
    errors, and free-form must win the drag-free comparison. The figures are
    recorded, not frozen.
    """
    train = exp.sample_queries(120, exp.IN_ENVELOPE_RATE, np.random.default_rng(1000))
    y_train = exp.labels(train)
    free_form = exp.fit_free_form(train, y_train)
    correct = exp.fit_correct_form(train, y_train)

    held = exp.sample_queries(400, exp.HELD_OUT_RATE, np.random.default_rng(7000))
    y_full = exp.labels(held)
    saved = exp.GEN_K_DRAG
    try:
        exp.GEN_K_DRAG = 0.0
        y_nodrag = exp.labels(held)
    finally:
        exp.GEN_K_DRAG = saved

    errors = {}
    for contestant in (free_form, correct):
        predicted = np.array([contestant.predict(q, 1.0) for q in held])
        errors[contestant.label] = {
            "vs_full": root_mean_squared_error(predicted, y_full),
            "vs_drag_free": root_mean_squared_error(predicted, y_nodrag),
        }
    withheld = float(np.mean(np.abs(y_full - y_nodrag)))
    spread = abs(errors[free_form.label]["vs_full"] - errors[correct.label]["vs_full"])

    observe(
        "null_is_uninformative",
        {"withheld_magnitude": withheld, "free_form": errors[free_form.label],
         "correct_form": errors[correct.label], "spread_vs_full": spread},
        "spread << withheld magnitude; free-form wins the drag-free comparison",
    )

    # Every contestant's held-out error IS the withheld term, to within their spread.
    assert spread < 0.2 * withheld
    # And the baseline extrapolates the non-withheld physics better than the correct
    # declared form — the signature that the declared form has nothing to say here.
    assert errors[free_form.label]["vs_drag_free"] < errors[correct.label]["vs_drag_free"]


def test_generator_a_is_not_bare_kocks_mecking(observe: ObservationRecorder) -> None:
    """E-12's circularity, avoided by construction (ADR-045): a generator differing
    from contestant 2's form by nothing would recover it to machine precision. The
    withheld term is the minimum non-circular departure."""
    q = exp.Query(rho_0=3.0, strain_rate=100.0, temperature=900.0)
    with_term = exp.generator_a(q.rho_0, q.strain_rate, q.temperature)
    saved = exp.GEN_K_DRAG
    try:
        exp.GEN_K_DRAG = 0.0
        without = exp.generator_a(q.rho_0, q.strain_rate, q.temperature)
    finally:
        exp.GEN_K_DRAG = saved
    observe("generator_departs_from_the_declared_form", abs(with_term - without),
            "non-zero: the generator is not the contestant's own form")
    assert abs(with_term - without) > 1.0
