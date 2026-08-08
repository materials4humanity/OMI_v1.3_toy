"""E-47 measured (ADR-058, docs/DECISIONS.md): is the parameter posterior of a
complete, well-fitted, in-window declared form a **ridge**, and does that ridge point
along the axis being extrapolated?

`docs/V1.4-EDITS.md` E-47 was filed **Untested** at v1.5 Part 4. This file is the
measurement, and it **partly refutes the entry** — which is why every assertion below
pins the *narrowed* claim rather than the original. The mechanism and the rotation are
confirmed and robust; the alignment and the "arbitrary within a range" magnitude are
not, and the entry's "validity report is clean" bullet is refuted outright on its own
worked instance.

Asserting the correction, not only the confirmation, is deliberate: an entry narrowed
by measurement can be silently widened again by a later retune unless the narrowing has
a test holding it (CLAUDE.md §7 — assert the qualitative claim, and this claim now has
an upper bound as well as a lower one).
"""

from __future__ import annotations

import numpy as np

from tests.conftest import ObservationRecorder
from tests.oracles.known_parameter_ridge import (
    DECLARED_CEILING,
    PARAMETER_NAMES,
    RELATIVE_NOISE,
    RidgeMeasurement,
    measure,
)

_CACHE: dict[int, RidgeMeasurement] = {}


def _measurement(seed: int = 0) -> RidgeMeasurement:
    """One measurement per seed, shared across tests — 300 refits is ~16s and every
    test below reads a different facet of the same run rather than re-running it."""
    if seed not in _CACHE:
        _CACHE[seed] = measure(np.random.default_rng(seed))
    return _CACHE[seed]


def test_the_declared_form_recovers_its_true_parameters_and_fits_excellently(
    observe: ObservationRecorder,
) -> None:
    """E-47's precondition: the failure being measured is **not** a bad fit.

    The mechanism set is complete over the fitted region by construction (every
    training strain sits at or below the generator's recrystallisation onset), so if
    the fit were poor the measurement would be about something else entirely.
    """
    m = _measurement()
    bias = np.abs(m.fitted.mean(axis=0) / m.theta_true - 1.0)
    observe("parameter_metric", m.metric, "declared, per CLAUDE.md invariant 1")
    observe("fitted_mean", m.fitted.mean(axis=0), "each within 1% of theta_true")
    observe("fractional_bias_per_parameter", dict(zip(PARAMETER_NAMES, bias)), "each < 0.01")
    observe("injected_relative_noise", RELATIVE_NOISE, "narrative only, not asserted")
    observe("in_envelope_relative_residual", m.in_envelope_residual, f"< {RELATIVE_NOISE}")

    assert np.all(bias < 0.01), "the fit is biased, so this is not a pure identifiability measurement"
    assert m.in_envelope_residual < RELATIVE_NOISE, (
        "the in-envelope fit residual exceeds the injected noise, so the fit is struggling "
        "and E-47's 'excellent in-envelope fit' precondition does not hold"
    )


def test_the_parameter_posterior_is_a_ridge_not_a_ball(observe: ObservationRecorder) -> None:
    """E-47's premise, confirmed: noise on in-envelope labels does turn the fit into a
    strongly anisotropic cloud, exactly as the entry argued from M11.5's noiseless
    exact recovery.

    Measured in the **declared fractional metric** (ADR-058) — a condition number in
    parameter space is meaningless without it, since rescaling one parameter rescales
    the anisotropy.
    """
    m = _measurement()
    observe("parameter_covariance_eigenvalues", m.eigenvalues, "descending; lambda_1 >> lambda_min")
    observe("fractional_sd_per_parameter", dict(zip(PARAMETER_NAMES, m.fractional_sd)), "narrative only")
    observe("condition_number", m.condition_number, "> 50")
    observe("ridge_direction", m.ridge_direction, "narrative only, not asserted")

    assert m.condition_number > 50.0, (
        "the parameter cloud is near-isotropic, which would remove E-47's premise rather "
        "than its consequence"
    )


def test_the_ridge_rotates_toward_the_extrapolation_direction_but_never_aligns_with_it(
    observe: ObservationRecorder,
) -> None:
    """**The measurement E-47 turns on, and the half that refutes it.**

    Confirmed: the ridge is nearly orthogonal to what the in-envelope prediction is
    sensitive to (which is *why* the fit residual is excellent), and it rotates
    steadily toward what the extrapolated prediction is sensitive to as accumulated
    strain grows. That rotation is the divergence-not-difference reading E-41 requires
    of any claim about going further, now measured on a second axis.

    Refuted: even at six times the envelope edge the alignment is far from 1. The
    ridge does **not** point along the extrapolation direction; it leans toward it.
    E-47's consequence is therefore real but bounded, and the assertion pins the bound.
    """
    m = _measurement()
    curve = [value for _, value in m.alignment_curve]
    observe("alignment_curve", m.alignment_curve, "monotone non-decreasing in gamma")
    observe("alignment_in_envelope", m.alignment_in_envelope, "< 0.15 (ridge is invisible in-envelope)")
    observe("alignment_far", m.alignment_far, "> 2x in-envelope AND < 0.5 (leans, does not align)")
    observe("alignment_growth", m.alignment_growth, "> 2.0")

    assert all(b >= a - 1.0e-9 for a, b in zip(curve, curve[1:])), (
        "the alignment curve is not monotone in accumulated strain, so 'the ridge rotates "
        "into the extrapolation direction' is not what is happening"
    )
    assert m.alignment_in_envelope < 0.15, (
        "the ridge is already aligned with the in-envelope sensitive direction, which would "
        "mean the in-envelope fit should have constrained it"
    )
    assert m.alignment_growth > 2.0, "the ridge does not rotate along the axis: E-47's consequence is inert"
    assert m.alignment_far < 0.5, (
        "the ridge IS aligned with the extrapolation direction at the far probe — E-47's "
        "original claim rather than the narrowed one this measurement supports; if this "
        "fires, widen the entry back and say why"
    )


def test_the_extrapolated_response_is_less_determined_than_the_fit_residual_suggests(
    observe: ObservationRecorder,
) -> None:
    """E-47's consequence in the response's own units: the "range nothing reports".

    The surviving form of the claim. The extrapolated prediction's across-refit spread
    exceeds the in-envelope fit residual several times over — so a practitioner reading
    the residual as the prediction's uncertainty is wrong by that factor — but it is a
    small percentage of the response, **not** an arbitrary range. Both halves are
    asserted.
    """
    m = _measurement()
    spread_ratio = m.response_spread_far / m.response_spread_in_envelope
    residual_ratio = m.response_spread_far / m.in_envelope_residual
    observe("response_relative_spread_in_envelope", m.response_spread_in_envelope, "narrative only")
    observe("response_relative_spread_far", m.response_spread_far, "> 2x in-envelope; < 0.10")
    observe("spread_growth_along_axis", spread_ratio, "> 2.0")
    observe("far_spread_over_in_envelope_fit_residual", residual_ratio, "> 2.0")
    observe("saturation_relative_spread", m.saturation_spread, "narrative only; E-47's named quantity")

    assert spread_ratio > 2.0, "the extrapolated spread does not grow along the axis"
    assert residual_ratio > 2.0, (
        "the extrapolated spread is within the in-envelope fit residual, so reading the "
        "residual as the prediction's uncertainty would not mislead — E-47's consequence absent"
    )
    assert m.response_spread_far < 0.10, (
        "the extrapolated response spread exceeds 10% — that would support E-47's original "
        "'arbitrary within a range' wording, which this measurement narrowed"
    )


def test_the_declared_validity_report_is_not_clean_at_the_far_probe(
    observe: ObservationRecorder,
) -> None:
    """**E-47's "report clean, factor <= 1" bullet, refuted on its own worked
    instance.**

    Checked against the **unwindowed** `KOCKS_MECKING`, which declares no bound on
    accumulated strain at all — the form E-47's bullet requires, and the one the source
    actually establishes (ADR-058 states why this is not cherry-picking). The bullet
    still fails: the declared **stored-density** ceiling binds for a substantial
    fraction of far-strain queries, because the saturation level the form predicts
    passes the declared ceiling at the cool end of the temperature window.

    So the framework is not silent here. It is silent for the *majority* of queries and
    it fires for the rest — and it fires for the wrong reason, since the density ceiling
    is a statement about a physical regime and not about whether the data pinned the
    parameters. The narrowed finding is stronger for being specific about which.
    """
    m = _measurement()
    observe("adr043_clean_fraction_at_far_strain", m.density_ceiling_clean_fraction, "0 < f < 1")
    observe("adr043_binding_bound_at_far", m.binding_bound_at_far, "== 'stored_density'")
    observe("declared_density_ceiling", DECLARED_CEILING, "narrative only; the declared bound")

    assert 0.0 < m.density_ceiling_clean_fraction < 1.0, (
        "the validity report is either uniformly clean or uniformly firing at the far probe; "
        "either would change E-47's bullet in a different direction than measured"
    )
    assert m.binding_bound_at_far == "stored_density", (
        "the bound that binds hardest at the far probe is not the declared saturation "
        "ceiling, so the mechanism behind the partial coverage is not the one recorded"
    )


def test_the_ridge_geometry_is_a_property_of_the_design_not_of_the_noise_level(
    observe: ObservationRecorder,
) -> None:
    """A second seed, because the whole finding is a geometry claim.

    The ridge's orientation is set by the design of experiment (which strains, which
    temperatures) and not by the noise magnitude, which only scales the cloud. If the
    alignment growth moved substantially with the seed, the measurement would be
    reporting a sampling artefact rather than a property of the fitted region.
    """
    a, b = _measurement(0), _measurement(1)
    observe("alignment_growth_seed_0", a.alignment_growth, "both > 2.0 and within 2x of each other")
    observe("alignment_growth_seed_1", b.alignment_growth, "both > 2.0 and within 2x of each other")
    observe("condition_number_seed_0", a.condition_number, "both > 50")
    observe("condition_number_seed_1", b.condition_number, "both > 50")

    assert a.alignment_growth > 2.0 and b.alignment_growth > 2.0
    assert 0.5 < a.alignment_growth / b.alignment_growth < 2.0, (
        "the alignment growth is seed-dependent, so it is not the geometric property this "
        "measurement claims to be reporting"
    )
