"""Whether a held-out region can discriminate between two model classes at all
— `docs/V1.4-EDITS.md` E-39's proposed Spec §9.3 wording, made executable **and
corrected in the making** (E-41).

Spec §9.3 requires that "extrapolation tests hold out entire regions of the
control space or whole composition variants, not scattered points". It is right
about what it forbids and silent about a precondition that turns out to be
load-bearing: the held-out region must be one the candidate and the baseline
actually resolve differently. M11.4 satisfied §9.3 in full — region not points,
grouped not random, genuinely outside the declared validity window — and produced
a comparison that could not have detected any effect
(`docs/M11.4-EXTRAPOLATION.md`).

**E-39 proposed the precondition as "the candidate and the baselines make
materially different predictions across the held-out region". Implementing it
showed that reading to be inoperable**, and the correction is this module's main
content. Measured on the two axes this repository has run, with the same dry-run
discipline on each — fit in-envelope, probe at the fitted region's upper edge and
again at the envelope's:

| Axis | truth's own signal | disagreement, near → far | divergence |
|---|---|---|---|
| M11.4, strain rate (**vacuous**) | **0.000** | 0.339 → 0.354 | **1.05** |
| M11.5, accumulated strain (**usable**) | 3.806 | 0.032 → 0.472 | **14.57** |

**Disagreement magnitude does not separate the two axes**: 0.354 against 0.472 is
the same order, so any bar low enough to admit the usable axis also admits the
vacuous one. E-39's criterion as worded is therefore not merely imprecise, it
cannot be operationalised — there is no threshold on "materially different
predictions" that gets these two cases right.

Two quantities do separate them, decisively. The clean truth's own variation along
the axis is **exactly zero** on the vacuous one: Kocks–Mecking has no strain-rate
dependence and neither did the physics it was scored against, so there was nothing
along that axis for any model to get right. And the two models are *parallel*
there — they differ by an offset established in-envelope that does not grow as the
axis is pushed, so the hold-out reveals nothing the training data did not already
show. An extrapolation test measures what happens as you go **further**; its
precondition has to be about divergence, not difference.

Three ways an axis can fail, kept distinct because they call for different
responses (:class:`HoldOutVerdict`): the physics may not vary along the axis at
all, the two model classes may track it together, or the candidate may be actively
worse along it.

Deliberately domain-neutral and deliberately ignorant of *which* axis is being
held out: it consumes predictions and a reference truth, so it applies to any
extrapolation comparison, not only to constitutive forms.

**Cites.** Spec §9.3 (the prescription this qualifies); Core §3.9 (why
extrapolation reach, rather than in-envelope fit, is the property a composed chain
is judged on); ADR-045 as amended, ADR-047 (docs/DECISIONS.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from omi.baseline import root_mean_squared_error
from omi.state import FloatArray

__all__ = [
    "HoldOutVerdict",
    "HoldOutDiscriminationReport",
    "check_hold_out_discriminates",
]


class HoldOutVerdict(Enum):
    """Why a candidate hold-out is or is not usable (Spec §9.3's splitting
    prescription, which this qualifies; `docs/V1.4-EDITS.md` E-39, E-41; ADR-045 as
    amended).

    An enum with three distinct failures rather than a bool, for the reason
    CLAUDE.md invariant 8 gives about blocked state selection: collapsing failures
    that call for different responses is how a diagnosis becomes useless. An inert
    axis is a fact about the *physics*, parallel models a fact about the *model
    classes*, and adversity a finding about the *candidate*.
    """

    DISCRIMINATING = "discriminating"
    """All criteria met. The comparison can distinguish the two model classes, and
    a null from it would be a real negative rather than an artefact."""

    INERT_AXIS = "inert_axis"
    """The withheld-free truth barely varies along this axis, so there is no
    physics here for either model to get right or wrong. **Rechoose the axis.**
    This is M11.4's failure at its root: Kocks–Mecking has no strain-rate
    dependence and neither did the truth it was scored against, once the withheld
    term was removed."""

    PARALLEL_MODELS = "parallel_models"
    """The truth varies along the axis but the two model classes track it
    together: their disagreement does not grow with distance along the axis, so it
    is an offset already visible in-envelope rather than a divergence the hold-out
    would reveal. **Rechoose the axis** — or accept that these two model classes
    are, for this quantity, the same model."""

    ADVERSE = "adverse"
    """The models diverge, but the candidate is *worse* than the baseline even
    against a truth with the withheld term removed — along this axis the
    candidate's structure is not doing work, it is doing harm. A real finding, and
    a different experiment from the one ADR-045 describes: running the registered
    comparison here would report a null whose cause is the candidate's own misfit
    rather than an absence of extrapolation benefit."""


@dataclass(frozen=True)
class HoldOutDiscriminationReport:
    """The measured basis for a :class:`HoldOutVerdict`, not only the verdict
    (Spec §9.3; CLAUDE.md §8: a measured quantity travels with its diagnostics).

    Every field is reported whatever the verdict, because a rejected axis is
    informative — the margin by which it failed says whether it was close.
    """

    axis: str
    """The quantity that would be held out, named by the caller. Recorded because
    E-39's proposed reporting obligation requires a report to state which axis was
    held out and why the candidate is expected to differ along it."""

    axis_signal: float
    """How far the **withheld-free truth itself** moves between the near and far
    probe points. Zero means the axis is inert: the physics does not depend on the
    quantity being withheld, so no model can distinguish itself along it."""

    disagreement_near: float
    """RMSE between candidate and baseline predictions at the near probe point."""

    disagreement_far: float
    """RMSE between candidate and baseline predictions at the far probe point."""

    candidate_error: float
    """Candidate's RMSE against the withheld-free truth at the far probe point —
    how well it captures the physics it *does* claim to express."""

    baseline_error: float
    """Baseline's RMSE against the same withheld-free truth."""

    noise_floor: float
    """The scale below which a difference is not evidence — supplied by the caller
    as the larger of the two contestants' in-envelope fit residuals. Declared
    rather than assumed, for the reason CLAUDE.md invariant 1 gives about
    metrics: a ratio is meaningless without the scale it is measured against."""

    required_divergence: float
    """The declared minimum growth factor the disagreement must show across the
    probe reach. Registered by the caller before the check runs."""

    verdict: HoldOutVerdict

    @property
    def divergence(self) -> float:
        """`disagreement_far / disagreement_near` — the quantity that actually
        separates a usable axis from a vacuous one (Spec §9.3; E-41).

        Infinite when the two models agree exactly at the near point and diverge
        further out, which is a strong pass rather than an error; ``1.0`` when they
        agree exactly at both, which is the degenerate parallel case.
        """
        if self.disagreement_near <= 0.0:
            return float("inf") if self.disagreement_far > 0.0 else 1.0
        return self.disagreement_far / self.disagreement_near

    @property
    def content_ratio(self) -> float:
        """`baseline_error / candidate_error` against the withheld-free truth at
        the far probe point (Spec §9.3's baseline comparison): how much better the candidate's declared structure is
        at the physics it does express. Above 1 the candidate is doing work along
        this axis; below 1 its structure is a liability here.

        Infinite when the candidate is exactly right — the degenerate case a caller
        should notice rather than have smoothed over. It arises whenever the
        training region is noiseless and the candidate's form is exactly the
        generator's there, which is a property of a synthetic study and not of any
        real one.
        """
        if self.candidate_error == 0.0:
            return float("inf")
        return self.baseline_error / self.candidate_error

    @property
    def usable(self) -> bool:
        """Whether the hold-out may be registered (Spec §9.3)."""
        return self.verdict is HoldOutVerdict.DISCRIMINATING

    def summary(self) -> str:
        """One-line human-readable form, so a pre-registration document can quote
        the numbers without a human retyping them (Spec §9.3; CLAUDE.md §8)."""
        return (
            f"axis {self.axis!r}: signal {self.axis_signal:.4f}; disagreement "
            f"{self.disagreement_near:.5f} -> {self.disagreement_far:.5f} "
            f"(divergence {self.divergence:.3f} vs required {self.required_divergence:.3f}); "
            f"candidate/baseline error on withheld-free truth "
            f"{self.candidate_error:.4f}/{self.baseline_error:.4f}; "
            f"noise floor {self.noise_floor:.5f} -> {self.verdict.value.upper()}"
        )


def check_hold_out_discriminates(
    *,
    axis: str,
    candidate_near: FloatArray,
    baseline_near: FloatArray,
    candidate_far: FloatArray,
    baseline_far: FloatArray,
    truth_without_withheld_term_near: FloatArray,
    truth_without_withheld_term_far: FloatArray,
    noise_floor: float,
    required_divergence: float,
) -> HoldOutDiscriminationReport:
    """Decide whether a candidate hold-out can discriminate between two model
    classes, **before** the hold-out is registered — the precondition Spec §9.3's
    splitting paragraph omits, and Core §3.9's reach question in operational form
    (`docs/V1.4-EDITS.md` E-39, E-41; ADR-045 as amended).

    All arrays are evaluated at two probe points reached by pushing along the
    candidate axis **while staying inside the training envelope** — a dry run,
    never the region that will actually be withheld. *near* is the closer probe
    point and *far* the further one. The caller owns that split; this function
    cannot check it, and a caller who passes the true hold-out gets a number that
    has seen the answer. ADR-045's amendment records why the in-envelope version is
    the right one nonetheless: it leaks nothing, and it separates the two axes this
    repository has run by a factor of fifteen.

    Both contestants are scored against a truth with the deliberately withheld
    physics **removed**, rather than against the full truth, because the full truth
    contains a term neither has — precisely the quantity that made every M11.4
    contestant look equally wrong and hid that they were not equally informative.

    Criteria, checked in this order:

    1. **The axis carries signal.** The withheld-free truth must itself move
       between the two probe points by more than *noise_floor*. Otherwise
       :attr:`HoldOutVerdict.INERT_AXIS`.
    2. **The models diverge.** Their disagreement must grow across the probe reach
       by at least *required_divergence*, and must exceed *noise_floor* at the far
       point. Otherwise :attr:`HoldOutVerdict.PARALLEL_MODELS`.
    3. **The candidate has content.** It must be at least as accurate as the
       baseline against the withheld-free truth at the far point. Otherwise
       :attr:`HoldOutVerdict.ADVERSE`.

    The order matters: an inert axis makes the divergence ratio meaningless, and
    parallel models make the sign of a tiny error difference uninformative, so each
    criterion is only read once the ones before it have passed.

    Raises for mismatched shapes, an empty probe, a negative *noise_floor* or a
    *required_divergence* below 1, rather than returning a verdict computed from
    nothing. A required divergence below 1 would ask the disagreement to *shrink*
    along the axis, which no extrapolation argument wants.
    """
    arrays = {
        "candidate_near": np.asarray(candidate_near, dtype=float),
        "baseline_near": np.asarray(baseline_near, dtype=float),
        "candidate_far": np.asarray(candidate_far, dtype=float),
        "baseline_far": np.asarray(baseline_far, dtype=float),
        "truth_without_withheld_term_near": np.asarray(truth_without_withheld_term_near, dtype=float),
        "truth_without_withheld_term_far": np.asarray(truth_without_withheld_term_far, dtype=float),
    }
    shapes = {name: value.shape for name, value in arrays.items()}
    if len(set(shapes.values())) != 1:
        raise ValueError(f"every probe array must cover the same points, got shapes {shapes}")
    if arrays["candidate_near"].size == 0:
        raise ValueError(f"probe region for axis {axis!r} is empty; nothing to check")
    if noise_floor < 0.0:
        raise ValueError(f"noise_floor must be non-negative, got {noise_floor}")
    if required_divergence < 1.0:
        raise ValueError(
            f"required_divergence must be at least 1.0, got {required_divergence}: a value below "
            "1 asks the two models to converge along the axis, which is the opposite of what an "
            "extrapolation test needs"
        )

    axis_signal = root_mean_squared_error(
        arrays["truth_without_withheld_term_far"], arrays["truth_without_withheld_term_near"]
    )
    disagreement_near = root_mean_squared_error(arrays["candidate_near"], arrays["baseline_near"])
    disagreement_far = root_mean_squared_error(arrays["candidate_far"], arrays["baseline_far"])
    candidate_error = root_mean_squared_error(
        arrays["candidate_far"], arrays["truth_without_withheld_term_far"]
    )
    baseline_error = root_mean_squared_error(
        arrays["baseline_far"], arrays["truth_without_withheld_term_far"]
    )

    report = HoldOutDiscriminationReport(
        axis=axis,
        axis_signal=axis_signal,
        disagreement_near=disagreement_near,
        disagreement_far=disagreement_far,
        candidate_error=candidate_error,
        baseline_error=baseline_error,
        noise_floor=noise_floor,
        required_divergence=required_divergence,
        verdict=HoldOutVerdict.DISCRIMINATING,
    )

    if axis_signal <= noise_floor:
        verdict = HoldOutVerdict.INERT_AXIS
    elif disagreement_far <= noise_floor or report.divergence < required_divergence:
        verdict = HoldOutVerdict.PARALLEL_MODELS
    elif candidate_error > baseline_error:
        verdict = HoldOutVerdict.ADVERSE
    else:
        verdict = HoldOutVerdict.DISCRIMINATING

    return HoldOutDiscriminationReport(
        axis=report.axis,
        axis_signal=report.axis_signal,
        disagreement_near=report.disagreement_near,
        disagreement_far=report.disagreement_far,
        candidate_error=report.candidate_error,
        baseline_error=report.baseline_error,
        noise_floor=report.noise_floor,
        required_divergence=report.required_divergence,
        verdict=verdict,
    )
