"""OMI-2 refusal test: docs/ROADMAP.md M7 exit gate — "Attempting to claim
OMI-2 fails with a specific list of unmet requirements."

Both domains are missing the two M9 items (reachability certificates,
inverse.py; a prospective inverse-design trial) — neither module exists
yet. The contrast domain can additionally supply the Class B volume-scaling
validation (Spec §4.4), since `DendriteRisk` is its only Class-B readout
(`omi_domains/contrast/readouts.py`); the flagship cannot, honestly, because
it declares no Class-B readout at all — Tier II geometry-dependent readouts
are an anti-goal for it (CLAUDE.md §9). The two domains' unmet lists are
therefore expected to differ by exactly that one item, not coincidentally
identical.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.classb import validate_volume_scaling_exponent
from omi.conformance import ConformanceInputs, ConformanceLevel, ConformanceNotMet, generate_report
from omi.state import Metric

from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.contrast.readouts import DendriteRisk
from omi_domains.flagship.build import build_chain as flagship_chain
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION

from tests.test_conformance_contrast import _contrast_inputs_without_sufficiency
from tests.test_conformance_flagship import _flagship_calibration
from tests.test_conformance_flagship import _flagship_rollout_curve
from tests.test_conformance_flagship import _flagship_triage
from tests.test_conformance_flagship import _matched_pair_sufficiency_campaign
from tests.test_conformance_flagship import _semigroup_residuals as _flagship_semigroup_residuals

M9_ONLY_UNMET = {"reachability_certificates_reported", "prospective_inverse_design_trial_reported"}


def _contrast_class_b_volume_scaling_residual(rng: np.random.Generator) -> float:
    incoming = contrast_incoming(2000, rng)
    chain = contrast_chain(n_cycles=5, current=2.0)
    final = chain.rollout(incoming).final
    readout = DendriteRisk()
    base = readout(final)[:, 0]
    d_c = float(np.quantile(base, 0.9))

    volumes = np.array([1.0, 4.0, 16.0])
    failure_probabilities = np.array(
        [np.mean(readout.weakest_link(final, n_sub, 2000, rng) > d_c) for n_sub in (1, 4, 16)]
    )
    return validate_volume_scaling_exponent(volumes, failure_probabilities, predicted_exponent=1.0)


def test_flagship_omi_2_fails_with_exactly_the_m9_items_plus_no_class_b_readout() -> None:
    """All OMI-1 evidence is supplied (reusing tests/test_conformance_flagship.py's
    own helpers), isolating the OMI-2-specific gap: the two M9 items, plus
    Class B volume-scaling validation, which the flagship cannot supply at
    all since it declares no Class-B readout."""
    rng = np.random.default_rng(0)
    incoming = flagship_incoming(50, rng)
    metric = Metric.from_ensemble(incoming)
    chain = flagship_chain()
    inputs = ConformanceInputs(
        declaration=FLAGSHIP_DECLARATION,
        metric=metric,
        rollout_error_curve=_flagship_rollout_curve(np.random.default_rng(1), metric, chain),
        semigroup_residuals=_flagship_semigroup_residuals(np.random.default_rng(2)),
        sufficiency_result=_matched_pair_sufficiency_campaign(np.random.default_rng(3)),
        triage_result=_flagship_triage(np.random.default_rng(4)),
        calibration=_flagship_calibration(np.random.default_rng(5)),
    )
    report = generate_report(inputs)
    assert report.claim(ConformanceLevel.OMI_1) is ConformanceLevel.OMI_1

    with pytest.raises(ConformanceNotMet) as excinfo:
        report.claim(ConformanceLevel.OMI_2)

    unmet_names = {r.name for r in excinfo.value.unmet_requirements}
    assert unmet_names == M9_ONLY_UNMET | {"class_b_volume_scaling_validation_at_3plus_volumes"}


def test_contrast_omi_2_fails_with_only_the_m9_items_once_class_b_is_supplied() -> None:
    """Unlike the flagship, contrast has a Class-B readout and can supply
    the volume-scaling validation itself — narrowing its OMI-2 unmet list
    to exactly the two genuinely-unbuilt-until-M9 requirements, not three.
    (OMI-1's own sufficiency-test item is deliberately left unmet here,
    per tests/test_conformance_contrast.py's module docstring, so this test
    only asserts the OMI-2-*specific* items rather than requiring OMI-1
    itself to be reached.)"""
    base_inputs = _contrast_inputs_without_sufficiency()
    inputs = ConformanceInputs(
        declaration=base_inputs.declaration,
        metric=base_inputs.metric,
        rollout_error_curve=base_inputs.rollout_error_curve,
        semigroup_residuals=base_inputs.semigroup_residuals,
        triage_result=base_inputs.triage_result,
        calibration=base_inputs.calibration,
        class_b_volume_scaling_residual=_contrast_class_b_volume_scaling_residual(np.random.default_rng(1)),
    )
    report = generate_report(inputs)

    with pytest.raises(ConformanceNotMet) as excinfo:
        report.claim(ConformanceLevel.OMI_2)

    unmet_names = {r.name for r in excinfo.value.unmet_requirements}
    assert unmet_names == M9_ONLY_UNMET | {"sufficiency_test_run_and_reported"}


def test_neither_domain_can_claim_omi_2_today() -> None:
    """The exit gate's own summary claim, checked directly."""
    rng = np.random.default_rng(0)
    for declaration, incoming_fn in (
        (FLAGSHIP_DECLARATION, flagship_incoming),
        (CONTRAST_DECLARATION, contrast_incoming),
    ):
        metric = Metric.from_ensemble(incoming_fn(20, rng))
        report = generate_report(ConformanceInputs(declaration=declaration, metric=metric))
        with pytest.raises(ConformanceNotMet):
            report.claim(ConformanceLevel.OMI_2)
