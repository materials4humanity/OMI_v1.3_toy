"""Lipschitz spectra reported with their metric attached (docs/ROADMAP.md
M2), and the refused L_phys x L_num decomposition (S-2.5, PASS-B). Cites
Core §3.9 / Spec §2.5.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.gaps import NotSpecified
from omi.operators import Control, amplification_decomposition, lipschitz_report
from omi.state import Metric

from omi_domains.flagship.build import build_incoming_ensemble
from omi_domains.flagship.operators import HEATING_AND_SOAK


def test_lipschitz_report_carries_the_metric_that_produced_it() -> None:
    rng = np.random.default_rng(0)
    ensemble = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(ensemble)
    control = Control(0.0, 1.0, lambda t: np.array([8.0]))

    report = lipschitz_report(HEATING_AND_SOAK, ensemble[0], control, metric)

    np.testing.assert_array_equal(report.spectrum, HEATING_AND_SOAK.lipschitz(ensemble[0], control, metric))
    assert report.metric is metric


def test_amplification_decomposition_refuses_citing_s_2_5() -> None:
    rng = np.random.default_rng(1)
    ensemble = build_incoming_ensemble(50, rng)
    metric = Metric.from_ensemble(ensemble)
    control = Control(0.0, 1.0, lambda t: np.array([8.0]))

    with pytest.raises(NotSpecified) as exc_info:
        amplification_decomposition(HEATING_AND_SOAK, ensemble[0], control, metric)

    assert exc_info.value.coverage_id == "S-2.5"
