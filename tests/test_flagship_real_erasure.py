"""Phase 3.1 (docs/ROADMAP.md): `measure_erasure`/`component_recoverability`
run against the flagship's own declared erasure operator, `HEATING_AND_SOAK`
(`is_erasure=True`), rather than only against the synthetic diagonal oracle
in `tests/oracles/known_erasure.py`. Cites Core §3.9, Spec §3.2
(Proposition 3.2), ADR-017 (docs/DECISIONS.md).

`HEATING_AND_SOAK` is a real, finite-rate exponential decay, not the
oracle's exact-zero-gain construction — its "erasure" is a large but finite
damping (``exp(-5)`` over its own control duration), never an exact
singular Jacobian entry. This is exactly the case ADR-017 anticipates by
reporting the full spectrum alongside the numerical rank rather than
inventing a threshold: at the default (machine-epsilon-scale) tolerance,
`measure_erasure` reports full rank here, and the qualitative erasure is
only visible by reading the spectrum, not the rank statistic.
"""

from __future__ import annotations

import numpy as np

from omi.erasure import component_recoverability, measure_erasure
from omi.operators import Control
from omi.state import Metric

from omi_domains.flagship.build import build_incoming_ensemble
from omi_domains.flagship.operators import HEATING_AND_SOAK
from omi_domains.flagship.state import FLAGSHIP_SCHEMA

from tests.conftest import ObservationRecorder

HEATING_CONTROL = Control(0.0, 1.0, lambda t: np.array([8.0]))


def test_heating_and_soak_erasure_is_full_rank_at_default_tolerance_but_visible_in_the_spectrum(
    observe: ObservationRecorder,
) -> None:
    """`HEATING_AND_SOAK`'s erasure is real (Core §7.1: "erases z and most of
    m") but not exact — the two damped directions have singular value
    ``exp(-5) ~ 0.0067``, genuinely nonzero, not underflowed to zero. ADR-017
    rejects inventing a threshold to call this "erased" numerically; the
    honest report is: full rank at the default tolerance, and a ~150x gap in
    the spectrum that a reader inspects to make the qualitative call Core
    §3.9's `L ≪ 1` asks for. This is the first time this repository's rank
    statistic has been run against an operator whose erasure is finite-rate
    rather than exact-zero, and the result is a genuine (not engineered)
    finding: the rank alone says nothing here; the spectrum says everything.
    """
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(200, rng)
    metric = Metric.from_ensemble(incoming)
    state = incoming[0]

    measurement = measure_erasure(HEATING_AND_SOAK, state, HEATING_CONTROL, metric)

    observe("rank", measurement.rank, "7 at default (ADR-017) tolerance — full rank, not reduced")
    observe("spectrum", measurement.spectrum, "two values near exp(-5)~0.0067, rest >= 0.74")
    observe("tol", measurement.tol, "machine-epsilon scale (ADR-017 default)")
    assert measurement.rank == 7

    # The two smallest singular values are three orders of magnitude below
    # the weakest surviving one — Core §3.9's qualitative L << 1, readable
    # from the spectrum even though the rank statistic doesn't isolate it.
    assert measurement.spectrum[-1] < 0.01
    assert measurement.spectrum[-2] < 0.01
    assert measurement.spectrum[-3] > 0.5

    names = [f"{slot.name}.{name}" for slot, name, _dim in FLAGSHIP_SCHEMA.components]
    surviving = measurement.surviving_basis
    smallest_two_directions = {
        names[int(np.argmax(np.abs(surviving[:, j])))] for j in (surviving.shape[1] - 1, surviving.shape[1] - 2)
    }
    observe(
        "smallest_two_singular_directions",
        sorted(smallest_two_directions),
        "== {prior_deformation, substructure_density} (Core §7.1's own claim)",
    )
    assert smallest_two_directions == {"M.prior_deformation", "Z.substructure_density"}


def test_heating_and_soak_component_recoverability_cannot_see_the_erasure_at_all(
    observe: ObservationRecorder,
) -> None:
    """Per-component recoverability (R-squared of post-step regressed on
    pre-step) is a correlation measure — scale-invariant for a noiseless
    deterministic operator. `HEATING_AND_SOAK` is exactly that (no process
    noise anywhere in this repository's analytic operators), so every
    component whose Jacobian entry is nonzero, however small, reads back as
    R^2 = 1.0 regardless of how much magnitude it lost. This extends OQ-2's
    M2 finding (previously shown only on the synthetic diagonal oracle,
    `tests/oracles/known_erasure.py` — "a naive fraction-of-variance-
    retained reading... calls the small-gain component erased, while
    operator-level rank and per-component recoverability agree with each
    other" — i.e. R^2 already couldn't see it there either) to a real
    domain for the first time: recoverability is blind to the erasure here
    too, for the same underlying reason, and the erasure signal lives
    entirely in `measure_erasure`'s spectrum, never in this diagnostic.
    `accumulated_hardening`'s R^2 = 0.0 is a *different*, unrelated
    degenerate-input artefact (constant across the incoming ensemble,
    `build_incoming_ensemble`), not a second erasure detection — reported
    separately so the two are not conflated.
    """
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(200, rng)

    r_squared = {}
    for slot, name, _dim in FLAGSHIP_SCHEMA.components:
        r_squared[f"{slot.name}.{name}"] = component_recoverability(
            HEATING_AND_SOAK, incoming, HEATING_CONTROL, slot, name
        )
    observe("component_recoverability", r_squared, "see docstring: R^2 uniform except one degenerate-input case")

    erased_by_spectrum = {"M.prior_deformation", "Z.substructure_density"}
    degenerate_input = {"Z.accumulated_hardening"}
    for component, value in r_squared.items():
        if component in degenerate_input:
            assert value == 0.0, f"{component}: expected 0.0 (degenerate constant input), got {value}"
        else:
            assert value > 0.999, f"{component}: expected ~1.0 (R^2 blind to magnitude loss), got {value}"

    # The point of this test: R^2 does NOT distinguish the two
    # spectrum-erased components from the rest.
    for component in erased_by_spectrum:
        assert r_squared[component] > 0.999, (
            f"{component} is heavily damped in the spectrum (~0.0067 singular value) "
            f"but component_recoverability still reports R^2={r_squared[component]:.4f} — "
            "confirming recoverability cannot see this erasure at all."
        )
