"""Known-envelope oracle: a declared constitutive form whose validated range is
fixed by construction, so the reported extrapolation factor has a right answer
(M11.2; ADR-043, docs/DECISIONS.md; `docs/V1.4-EDITS.md` E-32).

Follows `tests/oracles/`'s standing discipline (CLAUDE.md §7): the quantity the
estimator is supposed to recover is *chosen here*, and the test asserts the
estimator recovers it rather than asserting a figure someone once observed.

**What is known by construction.** Two bounds, one per space, with deliberately
different half-widths so a factor computed against the wrong bound cannot
accidentally agree:

- a **control-space** bound on ``drive`` over ``[0, 10]`` — centre 5, half-width 5
- a **state-space** bound on ``extent`` over ``[0, 2]`` — centre 1, half-width 1

So the factor for any queried pair is exact arithmetic: ``|drive - 5| / 5`` and
``|extent - 1| / 1``. The oracle's `truth()` returns those, and which bound binds
is therefore also known, which is what makes the *action* checkable rather than
merely the number.

The form itself is a bare affine response — the point of the oracle is the
envelope machinery, not the physics, and a form with interesting physics would
make the expected factors harder to state than the code computing them, which is
how an oracle stops being one. Real forms with real breakdown regimes arrive with
the domain at M11.3 (ADR-044).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.proposed.constitutive import (
    ConstitutiveForm,
    ValidityBound,
    ValidityRange,
    ValiditySpace,
)
from omi.state import FloatArray, Slot

CONTROL_LOW, CONTROL_HIGH = 0.0, 10.0
STATE_LOW, STATE_HIGH = 0.0, 2.0

CONTROL_CENTRE = 0.5 * (CONTROL_LOW + CONTROL_HIGH)
CONTROL_HALF_WIDTH = 0.5 * (CONTROL_HIGH - CONTROL_LOW)
STATE_CENTRE = 0.5 * (STATE_LOW + STATE_HIGH)
STATE_HALF_WIDTH = 0.5 * (STATE_HIGH - STATE_LOW)

SLOPE = 3.0
INTERCEPT = 1.0


def _affine_response(drive: float, extent: float) -> FloatArray:
    """The oracle's stand-in response (Spec §2.2: a declared form must be
    evaluable, not merely named — see `ConstitutiveForm.evaluate`)."""
    return np.array([INTERCEPT + SLOPE * drive - extent])


@dataclass(frozen=True)
class KnownEnvelopeTruth:
    """The answers fixed by construction (CLAUDE.md §7)."""

    control_factor: float
    state_factor: float
    binding_name: str
    binding_space: ValiditySpace
    outside_envelope: bool


def known_envelope_form() -> ConstitutiveForm:
    """A declared form with one bound in each of Core §3.2's control space and
    Core §3.1's state space (ADR-043; Spec §2.2's proposed sixth category)."""
    return ConstitutiveForm(
        name="affine_reference_form",
        evaluate=_affine_response,
        parameters={"slope": SLOPE, "intercept": INTERCEPT},
        validity=ValidityRange(
            (
                ValidityBound(
                    name="drive",
                    space=ValiditySpace.CONTROL,
                    low=CONTROL_LOW,
                    high=CONTROL_HIGH,
                    regime="fitted driving window",
                ),
                ValidityBound(
                    name="extent",
                    space=ValiditySpace.STATE,
                    low=STATE_LOW,
                    high=STATE_HIGH,
                    regime="fitted state region",
                ),
            )
        ),
        provenance="constructed for tests/oracles/known_envelope.py; no external source claimed",
        governs=((Slot.M, "extent"),),
    )


def truth(drive: float, extent: float) -> KnownEnvelopeTruth:
    """The extrapolation factors, the binding bound and the space it binds in,
    computed directly from the declared window rather than from the estimator
    under test (CLAUDE.md §7; Spec §2.2)."""
    control_factor = abs(drive - CONTROL_CENTRE) / CONTROL_HALF_WIDTH
    state_factor = abs(extent - STATE_CENTRE) / STATE_HALF_WIDTH
    if control_factor >= state_factor:
        binding_name, binding_space = "drive", ValiditySpace.CONTROL
    else:
        binding_name, binding_space = "extent", ValiditySpace.STATE
    return KnownEnvelopeTruth(
        control_factor=control_factor,
        state_factor=state_factor,
        binding_name=binding_name,
        binding_space=binding_space,
        outside_envelope=max(control_factor, state_factor) > 1.0,
    )
