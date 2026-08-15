"""Erasure measurement: rank, surviving subspace, and component-level
recoverability.

Cites Core §3.9 (the erasure definition and its three consequences) and
Spec §3.2 (Proposition 3.2, Corollary 3.3: an erasure of Jacobian rank ``r``
truncates the observability Gramian to rank ``r``, and kernel directions are
both unidentifiable and uninfluential downstream). ADR-017 (docs/DECISIONS.md)
fixes the numerical rank tolerance; OQ-2 (docs/COVERAGE.md Part IV,
docs/DECISIONS.md) is investigated by :func:`component_recoverability`
alongside the operator-level rank measurement in
``tests/oracles/test_known_erasure.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import Ensemble, FloatArray, Metric, Slot, State, StateSchema


@dataclass(frozen=True)
class ErasureMeasurement:
    """The metric-scaled Jacobian's singular-value spectrum, split into a
    surviving subspace (the row space — ``rank`` directions) and an erased
    subspace (the numerical kernel), per Spec §3.2's Proposition 3.2 /
    Corollary 3.3.

    The full spectrum is always carried alongside the integer ``rank``
    (ADR-017): whether a given rank deficiency is "substantially lower" — the
    qualitative content of Core §3.9's ``L ≪ 1`` — is a judgement for the
    reader of the spectrum, not a hidden constant.
    """

    spectrum: FloatArray
    """Singular values in descending order, length = ``min(state_dim, state_dim)``."""
    rank: int
    """Numerical rank at the declared tolerance (ADR-017)."""
    surviving_basis: FloatArray
    """``(state_dim, rank)``: right singular vectors spanning the surviving
    subspace — directions that remain identifiable and influential
    downstream (Spec §3.2 Corollary 3.3)."""
    erased_basis: FloatArray
    """``(state_dim, state_dim - rank)``: right singular vectors spanning the
    numerical kernel — unidentifiable from post-erasure data and without
    downstream influence (Spec §3.2 Corollary 3.3)."""
    metric: Metric
    """The declared metric the Jacobian was scaled by before the SVD (Core
    §3.9 / Spec §2.5: erasure measurement is metric-dependent)."""
    tol: float
    """The absolute singular-value threshold used for the rank cutoff
    (ADR-017) — reported, not hidden."""

    @property
    def surviving_gain(self) -> float:
        """Largest singular value on the surviving subspace — Core §3.9's ``L``
        (E-56; ADR-068). ``0.0`` when nothing survives."""
        return float(self.spectrum[0]) if self.rank > 0 and self.spectrum.size else 0.0

    @property
    def erased_gain(self) -> float:
        """Largest singular value on the erased subspace (Core §3.4; Spec §3.2): how
        completely the destroyed directions were destroyed (E-56; ADR-068). ``0.0`` when
        nothing is erased."""
        return float(self.spectrum[self.rank]) if self.rank < self.spectrum.size else 0.0

    def completeness(self) -> "ErasureCompleteness":
        """Completeness as **two quantities that cannot be summarised as one** (Core §3.4's
        two clauses; Spec §3.2's rank; E-56; ADR-068).

        The rank alone has been this repository's erasure verdict since M2, and on the
        first domain whose erasure is thermodynamic rather than decaying it was the wrong
        one — rank 1 of 7 with a surviving-subspace gain of 14.4. Prefer this over reading
        :attr:`rank` in isolation.
        """
        return ErasureCompleteness(
            effective_rank=self.rank,
            state_dimension=int(self.spectrum.size),
            tolerance=self.tol,
            surviving_gain=self.surviving_gain,
            erased_gain=self.erased_gain,
            metric=self.metric,
        )


@dataclass(frozen=True)
class ErasureCompleteness:
    """An erasure's completeness as **two independent quantities that may not be
    summarised as one** (`docs/V1.4-EDITS.md` E-56; ADR-068).

    Core §3.4 defines an erasure operator by an image of substantially lower effective
    dimension **and** ``L ≪ 1``, joined as though they were one property. They are not:
    the discovery domain's calcination collapses six of seven state directions while
    *amplifying* the seventh by more than an order of magnitude, because the surviving
    direction is that domain's own declared conservation invariant. An operator can
    satisfy either clause and violate the other.

    So this object reports both and **refuses to be reduced to one** — see
    :meth:`__bool__`. A caller that wants a verdict must state which clause it means.
    """

    effective_rank: int
    """Numerical rank of the metric-scaled Jacobian at :attr:`tolerance`."""
    state_dimension: int
    """The domain's dimension, so ``effective_rank`` is readable as ``r`` of ``n``."""
    tolerance: float
    """The absolute singular-value cutoff the rank was taken at (ADR-017) — reported,
    because E-19's finding is that a finite-rate erasure's rank is a function of it."""
    surviving_gain: float
    """Largest singular value **on the surviving subspace**, in :attr:`metric`.

    This is the ``L`` of Core §3.9's ``L ≪ 1``, and it is what decides whether the
    erasure *bounds* error: a direction that survives with gain above one carries error
    forward amplified, however many other directions were destroyed."""
    erased_gain: float
    """Largest singular value on the **erased** subspace — how completely the destroyed
    directions were destroyed, which is a different question from how many there were."""
    metric: Metric
    """The declared metric both gains are quoted in (CLAUDE.md invariant 1). Neither gain
    means anything without it."""

    def __bool__(self) -> bool:
        """Always raises. **This refusal is the point of the class** (ADR-068).

        `if completeness:` is a caller collapsing two independent measurements into one
        verdict, which is exactly the conflation E-56 records in Core §3.4's own
        definition. The alternative — synthesising a combined score — would bake the
        defect into this repository instead of surfacing it.
        """
        raise TypeError(
            "ErasureCompleteness has no single truth value: dimension collapse and gain "
            "contraction are independent properties (V1.4-EDITS E-56). Ask for "
            "`dimension_collapsed` or `gain_contracted` explicitly, or read "
            "`summary()`, which always states both."
        )

    @property
    def dimension_collapsed(self) -> bool:
        """Core §3.4's first clause: the image has lower effective dimension."""
        return self.effective_rank < self.state_dimension

    @property
    def gain_contracted(self) -> bool:
        """Core §3.4's second clause, and Core §3.9's condition (a): ``L < 1`` on the
        directions that survive."""
        return self.surviving_gain < 1.0

    def summary(self) -> str:
        """Both quantities, always together, in the order Core §3.4 states them."""
        return (
            f"rank {self.effective_rank} of {self.state_dimension} at tol "
            f"{self.tolerance:.4g} (dimension collapsed: {self.dimension_collapsed}); "
            f"surviving-subspace gain L = {self.surviving_gain:.4f} "
            f"(gain contracted: {self.gain_contracted}); erased-subspace gain "
            f"{self.erased_gain:.4g}"
        )


class ErrorControlVerdict(Enum):
    """Whether Core §3.9's condition (a) is claimable for a measured erasure
    (`docs/V1.4-EDITS.md` E-57; ADR-068)."""

    CLAIMABLE = auto()
    """Both clauses of §3.4 hold **and** the declared state has been tested for
    sufficiency."""
    REFUSED_STATE_UNTESTED = auto()
    """No sufficiency deficit was supplied. **The default, and not a failure of the
    operator**: a state-space erasure acts on a basis of `𝒮`, so it cannot bound error
    arising from a quantity outside `𝒮`, and whether such a quantity exists is what a
    deficit measures."""
    REFUSED_DIMENSION_NOT_COLLAPSED = auto()
    REFUSED_GAIN_NOT_CONTRACTED = auto()
    """Measured on a real chain: rank collapse without gain contraction concentrates
    error rather than bounding it."""
    REFUSED_DEFICIT_ABOVE_THRESHOLD = auto()
    """The declared state was tested and found insufficient at the declared threshold."""


@dataclass(frozen=True)
class StateSufficiencyEvidence:
    """That the **declared state** has been tested for sufficiency, and with what result
    (Spec §1.2's matched-pair deficit; ADR-068).

    Deliberately a value plus its provenance rather than a `DeficitResult`: `omi.erasure`
    does not depend on the deficit *estimator*, only on the fact that one was run. What
    condition (a) needs is evidence, not a particular implementation of it.
    """

    deficit_squared: float
    threshold: float
    """The declared bound the deficit is judged against. Supplied by the caller, because
    Spec §1 specifies no universal value and inventing one here would be the
    improvisation CLAUDE.md §4 forbids."""
    provenance: str
    """What produced the deficit — the probe set, the matching depth, the domain. A
    number with no provenance is not evidence."""

    def __post_init__(self) -> None:
        if not self.provenance.strip():
            raise ValueError(
                "a sufficiency deficit with no provenance is not evidence that the declared "
                "state was tested; name what measured it"
            )
        if self.deficit_squared < 0.0:
            raise ValueError(f"deficit_squared is non-negative by construction, got {self.deficit_squared}")

    @property
    def sufficient(self) -> bool:
        """Whether the declared state passed at :attr:`threshold` (Spec §1.2's deficit;
        Core §2.1's Axiom S is what it tests)."""
        return self.deficit_squared <= self.threshold


@dataclass(frozen=True)
class ErrorControlClaim:
    """Whether Core §3.9's condition (a) may be claimed, and why not where it may not
    (E-57; ADR-068). Every field is reported whatever the verdict."""

    verdict: ErrorControlVerdict
    completeness: ErasureCompleteness
    evidence: StateSufficiencyEvidence | None
    reason: str

    @property
    def claimable(self) -> bool:
        """Whether Core §3.9's condition (a) may be claimed on this evidence."""
        return self.verdict is ErrorControlVerdict.CLAIMABLE


def condition_a_claim(
    completeness: ErasureCompleteness,
    evidence: StateSufficiencyEvidence | None = None,
) -> ErrorControlClaim:
    """Whether a measured erasure supports Core §3.9's condition (a) (E-57; ADR-068).

    **Condition (a) has a precondition and Core §3.9 does not state it.** The section
    offers a dichotomy — error accumulation is controlled either by an erasure operator
    or by observation density sufficient for assimilation to correct drift — and presents
    the two as alternatives of equal standing. They are not. An erasure acts on a basis
    of the declared state; a quantity outside that state is not in its Jacobian's domain,
    so no amount of rank collapse says anything about it. Condition (b) *is* robust to an
    under-declared state, because assimilation acts on the observation residual.

    So condition (a) is conditional on Axiom S holding for the declared state — which is
    precisely what Core §1 and Spec §1 exist to **measure rather than assume**. With no
    *evidence* argument this function therefore **refuses** rather than assuming the bound
    holds: that refusal is the repair, and it is the default because an unsupplied deficit
    is the common case.

    Checked in order, so the reported reason is the first thing that actually blocks
    (Spec §7.3's ordered-diagnosis discipline, and E-06's finding that an unordered report
    cannot say which term is responsible).
    """
    if not completeness.dimension_collapsed:
        return ErrorControlClaim(
            ErrorControlVerdict.REFUSED_DIMENSION_NOT_COLLAPSED,
            completeness,
            evidence,
            f"the image is full rank ({completeness.effective_rank} of "
            f"{completeness.state_dimension}) at the declared tolerance, so no subspace is "
            "erased and Core §3.4's first clause does not hold",
        )
    if not completeness.gain_contracted:
        return ErrorControlClaim(
            ErrorControlVerdict.REFUSED_GAIN_NOT_CONTRACTED,
            completeness,
            evidence,
            f"the surviving subspace has gain L = {completeness.surviving_gain:.4f} >= 1 in "
            "the declared metric, so error in the directions that survive is amplified "
            "rather than bounded; destroying the other directions does not bound it (E-56)",
        )
    if evidence is None:
        return ErrorControlClaim(
            ErrorControlVerdict.REFUSED_STATE_UNTESTED,
            completeness,
            None,
            "no sufficiency deficit was supplied for the declared state, so Axiom S is "
            "untested and condition (a)'s precondition is unverified; an erasure cannot "
            "bound error from a variable outside the state space it acts on (E-57)",
        )
    if not evidence.sufficient:
        return ErrorControlClaim(
            ErrorControlVerdict.REFUSED_DEFICIT_ABOVE_THRESHOLD,
            completeness,
            evidence,
            f"the declared state was tested and found insufficient: deficit_squared "
            f"{evidence.deficit_squared:.6g} exceeds the declared threshold "
            f"{evidence.threshold:.6g} ({evidence.provenance})",
        )
    return ErrorControlClaim(
        ErrorControlVerdict.CLAIMABLE,
        completeness,
        evidence,
        f"both clauses of Core §3.4 hold and the declared state was tested sufficient "
        f"({evidence.provenance})",
    )


def measure_erasure(
    operator: EvolutionOperator,
    state: State,
    control: Control,
    metric: Metric,
    rtol: float | None = None,
) -> ErasureMeasurement:
    """Measure an operator's erasure rank and surviving subspace at
    ``(state, control)``, in the declared *metric* (Core §3.9; Spec §3.2's
    Proposition 3.2).

    *rtol*, if given, overrides the default numerical-rank tolerance
    (ADR-017): the absolute cutoff becomes ``spectrum[0] * rtol``. The
    default matches :func:`numpy.linalg.matrix_rank`'s own convention.
    """
    jacobian = operator.jacobian(state, control)
    scaled = jacobian * metric.scale[np.newaxis, :] / metric.scale[:, np.newaxis]
    _, spectrum, vt = np.linalg.svd(scaled)

    if rtol is None:
        rtol = max(scaled.shape) * np.finfo(scaled.dtype).eps
    tol = float(spectrum[0] * rtol) if spectrum.size else 0.0
    rank = int(np.sum(spectrum > tol))

    v = vt.T
    surviving = v[:, :rank]
    erased = v[:, rank:]
    return ErasureMeasurement(spectrum, rank, surviving, erased, metric, tol)


def component_recoverability(
    operator: EvolutionOperator,
    ensemble: Ensemble,
    control: Control,
    slot: Slot,
    name: str,
) -> float:
    """An empirical estimate of Core §3.9 consequence 3's "residual variance
    explained by upstream variables" for one named component, across
    *ensemble* — R-squared of the post-step value regressed on the pre-step
    value.

    This operationalises only one of Core's two named candidate measures
    (the other, mutual information, is not implemented — see OQ-2,
    docs/COVERAGE.md Part IV). R-squared equals the squared Pearson
    correlation for a least-squares linear fit with intercept, so it is
    computed directly from the correlation coefficient rather than via a
    separate regression routine.

    Returns 0.0 if either the pre- or post-step value is constant across the
    ensemble (correlation undefined; there is nothing for either variable to
    explain).
    """
    lifted = operator.lift(ensemble, control)
    pre = ensemble.component(slot, name)[:, 0]
    post = lifted.component(slot, name)[:, 0]
    if np.std(pre) == 0.0 or np.std(post) == 0.0:
        return 0.0
    correlation = np.corrcoef(pre, post)[0, 1]
    return float(correlation**2)


def component_surviving_overlap(measurement: ErasureMeasurement, schema: StateSchema, slot: Slot, name: str) -> float:
    """A named component's own squared overlap with the surviving subspace
    (Core §3.9 consequence 3; Spec §3.2 Corollary 3.3), ``‖P_survive e_i‖²``
    for ``e_i`` the component's standard basis direction in the flat state
    vector and ``P_survive`` the projector onto
    :attr:`ErasureMeasurement.surviving_basis`.

    Answers OQ-2's deferred question (docs/COVERAGE.md Part IV): for a
    *mixing* (non-diagonal) erasure, :func:`component_recoverability`'s
    univariate correlation and operator-level rank need not agree on
    per-component influence, because no named component need align with
    any single singular direction — every component can have a genuinely
    intermediate overlap with the surviving subspace, unlike the diagonal
    case (`tests/oracles/known_erasure.py`) where each component aligns
    with exactly one singular vector and the two measures cannot help but
    agree. This is a pure geometric projection, needing no ensemble at all,
    unlike :func:`component_recoverability` — a distinct diagnostic, not a
    replacement for it.

    Only defined for a single-dimensional component (as
    :func:`component_recoverability` already assumes); raises if *schema*
    declares *slot*.*name* with dimension other than 1.
    """
    index_slice = schema.slice_for(slot, name)
    if index_slice.stop - index_slice.start != 1:
        raise ValueError(f"{slot.value}.{name} is not a single-dimensional component")
    e_i = np.zeros(measurement.surviving_basis.shape[0])
    e_i[index_slice.start] = 1.0
    projection = measurement.surviving_basis @ (measurement.surviving_basis.T @ e_i)
    return float(np.dot(projection, projection))
