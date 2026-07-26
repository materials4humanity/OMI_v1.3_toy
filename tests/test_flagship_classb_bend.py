"""Tier I½ (ADR-035, docs/DECISIONS.md) and its Class B wiring (Phase 2.3):
the flagship's `BendAngle` — the first Type-2/Class-B readout this
repository has ever had — exercised end to end through `omi.classb`'s
driver/tail separation, correlation-length estimation, dimensional
reduction, and validation ladder, against a real (not hand-supplied) driver
field. Cites Core §3.6, Core §7.1, Spec §4 in full.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.readouts import ComponentReadout, ReadoutType, Type2Geometry
from omi_domains.flagship.classb_bend import (
    bulk_regime_thicknesses,
    run_bend_classb_campaign,
    thin_regime_thicknesses,
)
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.flagship.readouts import BendAngle, ExtractHardness

from tests.conftest import ObservationRecorder


def test_type2geometry_accepts_only_two_scalars() -> None:
    """ADR-035's structural fence: no third field (a mesh, an element
    table) can be passed without editing the dataclass itself."""
    Type2Geometry(thickness=1.0, curvature=0.5)  # both named, both scalars
    Type2Geometry(thickness=1.0)  # curvature defaults to 0.0 (flat, valid)

    with pytest.raises(TypeError):
        Type2Geometry(thickness=1.0, curvature=0.5, mesh="not allowed")  # type: ignore[call-arg]

    with pytest.raises(ValueError):
        Type2Geometry(thickness=0.0)


def test_bend_angle_is_type_2_class_b() -> None:
    readout = BendAngle()
    assert readout.readout_type is ReadoutType.TYPE_2
    assert isinstance(readout, ComponentReadout)


def test_bend_angle_returns_a_response_and_a_process_zone_volume(observe: ObservationRecorder) -> None:
    from omi.state import Slot, State

    from omi_domains.flagship.state import FLAGSHIP_SCHEMA

    values = np.zeros(FLAGSHIP_SCHEMA.size)
    values[FLAGSHIP_SCHEMA.slice_for(Slot.M, "prior_grain_size")] = 20.0
    values[FLAGSHIP_SCHEMA.slice_for(Slot.Z, "inclusion_content")] = 1.0
    state = State(FLAGSHIP_SCHEMA, values)
    operator = ExtractHardness()(state)
    geometry = Type2Geometry(thickness=1.0, curvature=2.0)

    readout = BendAngle()
    response, process_zone_volume = readout.evaluate(operator, geometry)

    observe("outer_fibre_response", response, "finite, positive")
    observe("process_zone_volume", process_zone_volume, "in [0, thickness]")
    assert response.shape == (1,)
    assert np.isfinite(response[0])
    assert 0.0 <= process_zone_volume <= geometry.thickness


def test_flagship_declares_bend_angle_with_item_4b_filled() -> None:
    catalogue_text = " ".join(FLAGSHIP_DECLARATION.readout_catalogue)
    assert "bend_angle" in catalogue_text
    assert "Type-2/Class-B" in catalogue_text
    # Item 4b: driver field, defect population, physics map Psi (Core §4).
    assert "driver field" in catalogue_text
    assert "defect population" in catalogue_text
    assert "physics map" in catalogue_text
    assert "inclusion_content" in catalogue_text


def test_bend_classb_campaign_runs_end_to_end(observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(0)
    result = run_bend_classb_campaign(rng)

    observe("correlation_length", result.correlation_length.correlation_length, "> 0, reliable")
    observe("correlation_length_reliable", result.correlation_length.reliable, "True")
    observe("domain_to_correlation_ratio", result.correlation_length.domain_to_correlation_ratio, "reported")
    assert result.correlation_length.correlation_length > 0.0
    assert result.correlation_length.reliable

    observe("xi_a_hat", result.xi_a_hat, "> 0 (measured from the defect population, not hand-supplied)")
    observe("xi_d_hat", result.xi_d_hat, "== xi_a_hat (beta=1.0, declared in item 4b)")
    assert result.xi_a_hat > 0.0
    assert result.xi_d_hat == pytest.approx(result.xi_a_hat)  # beta = 1.0

    observe("p0", result.p0, "in (0, 1), from the fitted join model")
    assert 0.0 < result.p0 < 1.0


def test_bulk_regime_failure_probability_increases_with_thickness(observe: ObservationRecorder) -> None:
    """n_eff's bulk-regime formula (volume/ell_D^3) grows with volume, so
    holding the per-site exceedance probability fixed, failure probability
    must strictly increase across the swept thicknesses (Proposition 4.2's
    ordinary, non-reduced size effect)."""
    rng = np.random.default_rng(0)
    result = run_bend_classb_campaign(rng)

    observe("bulk_thicknesses", bulk_regime_thicknesses(result.correlation_length.correlation_length), "> ell_D")
    observe("bulk_failure_probabilities", result.bulk_failure_probabilities, "strictly increasing")
    assert np.all(np.diff(result.bulk_failure_probabilities) > 0)

    observe("bulk_volume_scaling_residual", result.bulk_volume_scaling_residual, "~0 (predicted_exponent=1.0)")
    assert abs(result.bulk_volume_scaling_residual) < 1e-6


def test_thin_regime_failure_probability_is_suppressed_across_thickness(
    observe: ObservationRecorder,
) -> None:
    """Proposition 4.2's dimensional reduction: once thickness falls below
    the estimated correlation length, n_eff = area/ell_D^2 no longer depends
    on thickness at fixed footprint area — so failure probability must stay
    (near-)constant across the thin-regime sweep, "the size effect with
    respect to thickness is suppressed" (Spec §4.4)."""
    rng = np.random.default_rng(0)
    result = run_bend_classb_campaign(rng)

    observe("thin_thicknesses", thin_regime_thicknesses(result.correlation_length.correlation_length), "< ell_D")
    observe("thin_failure_probabilities", result.thin_failure_probabilities, "constant across thickness")
    assert np.allclose(result.thin_failure_probabilities, result.thin_failure_probabilities[0])

    observe("thin_volume_scaling_residual", result.thin_volume_scaling_residual, "~0 (predicted_exponent=0.0)")
    assert abs(result.thin_volume_scaling_residual) < 1e-6


def test_validation_ladder_is_constructed_with_finite_rungs(observe: ObservationRecorder) -> None:
    rng = np.random.default_rng(0)
    result = run_bend_classb_campaign(rng)
    ladder = result.validation_ladder

    observe("rung1_bulk_residual", ladder.bulk_residual, "finite, in [0, 1] (KS statistic)")
    observe("rung3_fractography_residual", ladder.fractography_residual, "finite, in [0, 1] (KS statistic)")
    observe("rung3_voids_construction", ladder.voids_construction, "bool")
    observe("rung4_volume_scaling_residual", ladder.volume_scaling_residual, "worse of the two regime residuals")

    assert 0.0 <= ladder.bulk_residual <= 1.0
    assert 0.0 <= ladder.fractography_residual <= 1.0
    assert isinstance(ladder.voids_construction, bool) or isinstance(ladder.voids_construction, np.bool_)
    assert ladder.volume_scaling_residual >= 0.0
