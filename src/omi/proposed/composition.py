"""The composition decomposition `c(x) = c̄ + δc(x)`, as declarable objects (proposed
extension; ADR-050, ADR-052, ADR-075, ADR-076, docs/DECISIONS.md).

Cites Core §3.1 (the `m` slot's "composition fields" and the `z` slot's sub-resolution
path-dependent quantities), Core §6.2 (its own open problem on operators that are
"composition-**parameterised**"), Spec §2.2 (the range constraint — "simplex
parameterisation for fractions") and Core §4 item 1b as ADR-071 split it.

**What the split is.** `c̄` is the mean over a declared domain. It indexes the operator
family, no operator transports it, and it is declared as item 1b's
:class:`~omi.interface.ParameterRole` — **not** as an ADR-049 coupled quantity. ADR-050
said the latter; ADR-075 supersedes it on `docs/V1.4-EDITS.md` E-46's four-property test,
and routing `c̄` back through the coupled-quantity construction is prohibited because it
re-creates the second declaration site ADR-071 removed. `δc(x)` is ordinary state in
whichever slot its length scale puts it in, and ADR-049's construction applies to *it*
in full.

**Three things this module supplies and one it deliberately does not.**

1. :class:`DescriptorMap` — named functionals of an underlying fraction vector (ADR-052),
   with Spec §2.2's simplex constraint applied **as architecture** rather than validated
   (CLAUDE.md invariant 5).
2. :class:`~omi.interface.ProjectionScale` — re-exported here for convenience and **defined
   in `omi.interface`**, because Core §4 item 1 asks for resolution limits and ADR-074 wanted
   E-31's characterisation method declared. It is load-bearing for the reason ADR-050 gives:
   operator reuse between two implementations is sound only if their `c̄`/`δc` splits match, and
   nothing detects a mismatch (`docs/V1.4-EDITS.md` E-45).
3. :func:`constancy_residual` — ADR-050's check, whose verdict is a *diagnosis* (the
   declared domain is open) rather than a pass/fail.

It does **not** supply an attainability certificate over descriptor space. Given a target
descriptor tuple, whether *any* composition maps to it is ADR-053's certificate and is
stage C3's; the simplex here removes only the forward failure mode. See ADR-076.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Sequence

import numpy as np

from omi.constraints import simplex
from omi.interface import ProjectionScale
from omi.state import FloatArray

__all__ = [
    "ProjectionScale",
    "DescriptorMap",
    "MeanComposition",
    "CompositionMetric",
    "ConstancyVerdict",
    "ConstancyReport",
    "constancy_residual",
]


@dataclass(frozen=True)
class DescriptorMap:
    """Named functionals of an underlying fraction vector — ADR-052's declaration, with
    Spec §2.2's simplex constraint applied as architecture (ADR-076).

    **Why descriptors at all.** ADR-052's reasoning: "this operator depends on chemistry only
    through carbon equivalent" is a **falsifiable** claim — it is refuted by holding the
    descriptors fixed, varying the underlying fractions, and observing the operator move. The
    alternatives (raw fractions alone, or descriptors alone) are not falsifiable in that way,
    which is why both are carried.

    **The simplex is structural.** :meth:`fractions_of` routes unconstrained coordinates
    through `omi.constraints.simplex`, which is componentwise non-negative and sums to exactly
    one *for any real input*. So no caller can evaluate descriptors at a fraction vector off
    the simplex — the constraint is satisfied by construction, not validated (CLAUDE.md
    invariant 5: "hard constraints are architecture, never loss penalties"). ADR-076 records
    why this is cheaper than the certificate it partly replaces, and what it leaves for
    ADR-053: the *inverse* question, whether any composition attains a requested descriptor
    tuple, is untouched by a forward constraint.
    """

    underlying: tuple[str, ...]
    """Names of the raw fractions, in the order :meth:`fractions_of` returns them."""
    descriptors: tuple[str, ...]
    """Names of the declared functionals, in the order :meth:`evaluate` returns them."""
    evaluate: Callable[[FloatArray], FloatArray]
    """Fractions (on the simplex) → descriptor values. Held as a callable for the same reason
    `ConstitutiveForm.evaluate` is (Spec §2.2): a map that cannot be evaluated is an assertion
    rather than a declaration."""
    provenance: str
    """The source establishing the functionals — a citation, not a claim."""

    def __post_init__(self) -> None:
        if len(self.underlying) < 2:
            raise ValueError(
                f"an underlying space of {len(self.underlying)} coordinate(s) has no simplex to "
                "constrain: declare at least two fractions (Spec §2.2)"
            )
        if not self.descriptors:
            raise ValueError("a descriptor map with no descriptors declares nothing (ADR-052)")
        if not self.provenance.strip():
            raise ValueError(
                "a descriptor map must declare its provenance: an unsourced functional is an "
                "assertion, the same discipline ADR-043 applies to a constitutive form"
            )

    def fractions_of(self, unconstrained: FloatArray) -> FloatArray:
        """Unconstrained coordinates → fractions **on the simplex** (Spec §2.2; ADR-076).

        This is the architectural constraint: the result is non-negative and sums to one for
        any real input, so an off-simplex composition is unrepresentable rather than rejected.
        """
        if unconstrained.shape != (len(self.underlying),):
            raise ValueError(
                f"expected {len(self.underlying)} unconstrained coordinates for "
                f"{self.underlying}, got shape {unconstrained.shape}"
            )
        return simplex(unconstrained)

    def descriptors_of(self, unconstrained: FloatArray) -> FloatArray:
        """Unconstrained coordinates → descriptor values, through the simplex (Spec §2.2's
        range constraint; ADR-052, ADR-076). The only route into :attr:`evaluate` this class
        offers, deliberately."""
        values = self.evaluate(self.fractions_of(unconstrained))
        if values.shape != (len(self.descriptors),):
            raise ValueError(
                f"descriptor map declared {len(self.descriptors)} descriptors "
                f"{self.descriptors} but evaluate returned shape {values.shape}"
            )
        return values

    def named_descriptors_of(self, unconstrained: FloatArray) -> Mapping[str, float]:
        """:meth:`descriptors_of`, keyed by declared name — the form a validity range's
        `report` consumes (Spec §2.2's proposed sixth category;
        `omi.proposed.constitutive.ValidityRange`)."""
        return dict(zip(self.descriptors, (float(v) for v in self.descriptors_of(unconstrained))))


@dataclass(frozen=True)
class MeanComposition:
    """`c̄` — the mean over a declared domain, with its projection scale and whether the
    domain is declared **closed** (Core §4 item 1b as ADR-071 split it; Core §6.2's
    "composition-parameterised"; ADR-050, ADR-075, ADR-076).

    Carried *inside* an item-1b :class:`~omi.interface.ParameterRole`'s declaration rather
    than beside it, so a reader who has the parameter has the scale that makes it comparable.
    """

    region: str
    """The declared domain the mean is taken over. Named, because ADR-050's whole diagnosis
    turns on whether *this* domain is closed."""
    unconstrained: FloatArray
    """The composition's coordinates before the simplex — the honest storage form, since the
    simplex is where the constraint lives (:meth:`DescriptorMap.fractions_of`)."""
    descriptor_map: DescriptorMap
    projection_scale: ProjectionScale
    domain_declared_closed: bool
    """Whether the domain is declared closed to the species in question.

    **This is the field the constancy residual is judged against**, and declaring it `False` is
    a legitimate declaration, not a defect: an open domain with a named flux is ADR-050's
    correct repair for a drifting mean, not its failure mode."""
    closure_note: str = ""
    """Why the domain is closed, or — where it is not — what crosses the boundary. Required
    when :attr:`domain_declared_closed` is `False`: an open domain whose flux is unnamed is
    exactly the under-declaration ADR-050's repair asks to be replaced."""

    def __post_init__(self) -> None:
        if not self.region.strip():
            raise ValueError("a mean composition must name the domain it is a mean over (ADR-050)")
        if not self.domain_declared_closed and not self.closure_note.strip():
            raise ValueError(
                f"the domain {self.region!r} is declared OPEN with no closure note: ADR-050's "
                "repair for a drifting mean is to re-declare the domain as open AND NAME THE "
                "FLUX, so an open declaration without the flux is the same under-declaration "
                "one step along"
            )

    def fractions(self) -> FloatArray:
        """The mean composition as fractions on the simplex (Spec §2.2's range constraint)."""
        return self.descriptor_map.fractions_of(self.unconstrained)

    def descriptor_values(self) -> Mapping[str, float]:
        """The mean composition in its declared descriptor basis (ADR-052; Core §6.2)."""
        return self.descriptor_map.named_descriptors_of(self.unconstrained)


@dataclass(frozen=True)
class CompositionMetric:
    """A distance over **descriptor** space, with its declared normalisation (Core §3.2's
    metric-declaration requirement, applied to composition rather than to `𝒮`; ADR-052's
    "descriptors as the metric over `c̄`"; CLAUDE.md invariant 1).

    ADR-052 makes descriptors the metric over `c̄`, and until stage C1 only the *basis* was
    declared — no distance existed. This is that distance.

    **The scale vector is declared, not inferred**, for invariant 1's reason: every distance
    in this repository is metric-dependent and the metric travels with any quantity quoted in
    it. The convention matches `omi.state.Metric`'s default — non-dimensionalise each
    descriptor by its spread across the incoming population, so a distance of 1 reads as "one
    population sigma in this descriptor".
    """

    descriptors: tuple[str, ...]
    scale: FloatArray
    """Per-descriptor normalisation, strictly positive."""
    basis: str
    """What the scale was computed from, in words. Required: a normalisation with no stated
    basis makes the distance uninterpretable, which is E-33's finding."""

    def __post_init__(self) -> None:
        if self.scale.shape != (len(self.descriptors),):
            raise ValueError(
                f"scale shape {self.scale.shape} does not match {len(self.descriptors)} descriptors"
            )
        if np.any(self.scale <= 0.0):
            raise ValueError("every descriptor scale must be strictly positive")
        if not self.basis.strip():
            raise ValueError(
                "a composition metric must state what its normalisation was computed from "
                "(CLAUDE.md invariant 1; docs/V1.4-EDITS.md E-33)"
            )

    def distance(self, left: Mapping[str, float], right: Mapping[str, float]) -> float:
        """Scale-normalised Euclidean distance between two descriptor tuples (Core §3.2's
        metric requirement, applied over composition; ADR-052).

        Refuses a tuple missing a declared descriptor rather than skipping it — a silently
        omitted coordinate is a distance computed in a different space than the one declared.
        """
        missing = [d for d in self.descriptors if d not in left or d not in right]
        if missing:
            raise ValueError(
                f"no value supplied for declared descriptor(s) {missing}: a distance over a "
                "subset of the declared basis is a distance in a different space"
            )
        difference = np.array([left[d] - right[d] for d in self.descriptors], dtype=float)
        return float(np.linalg.norm(difference / self.scale))


class ConstancyVerdict(Enum):
    """What a constancy residual over `c̄ + δc` means (Core §3.1's conservation reading of a
    closed domain; ADR-050; ADR-076).

    **Three members, not two, and that is the decision.** ADR-050: a violation "does not mean
    the declaration is arbitrary nonsense; it means the declared domain is open, and the
    coupling should have been `DEPLETED_BY` with a declared boundary flux." A pass/fail cannot
    express the case where a domain is *declared* open and duly drifts, which is consistent.
    """

    CONSISTENT_CLOSED = "consistent_closed"
    """Declared closed, and the mean holds within tolerance — conservation as expected."""

    CONSISTENT_OPEN = "consistent_open"
    """Declared **open** with a named flux, and the mean drifts. Consistent: this is what an
    open domain does, and the declaration said so."""

    OPEN_DOMAIN_UNDECLARED = "open_domain_undeclared"
    """Declared closed, and the mean drifts anyway. **The diagnosis, not a bare failure**: the
    declared domain is open. ADR-050's repair is to re-declare it open and name the flux, not
    to adjust `c̄`."""

    SUSPECT_CLOSED_DECLARATION = "suspect_closed_declaration"
    """Declared **open** with a named flux, and the mean does *not* drift. Not an error — a
    flux may be genuinely negligible over the interval measured — but the declaration claims
    something the measurement does not exhibit, so it is reported rather than passed."""


@dataclass(frozen=True)
class ConstancyReport:
    """ADR-050's constancy residual, with the diagnosis and the repair it implies (Core §3.1;
    Spec §2.2's conservation category, which is what a closed domain's mean rests on)."""

    verdict: ConstancyVerdict
    max_absolute_drift: float
    """Largest deviation of the domain mean from its initial value, over the trajectory."""
    tolerance: float
    """The declared bound the drift was judged against. Supplied by the caller: Spec specifies
    no universal value and inventing one here would be the improvisation CLAUDE.md §4 forbids."""
    region: str
    declared_closed: bool
    means: tuple[float, ...]
    """The measured domain means, step by step — recorded so the *shape* of a drift (monotone
    loss versus a wobble) is readable rather than collapsed into one number."""
    diagnosis: str

    @property
    def consistent(self) -> bool:
        """Whether the measurement agrees with what the declaration claimed (Core §3.1's
        conservation reading; ADR-050)."""
        return self.verdict in (ConstancyVerdict.CONSISTENT_CLOSED, ConstancyVerdict.CONSISTENT_OPEN)


def constancy_residual(
    domain_means: Sequence[float],
    *,
    tolerance: float,
    region: str,
    declared_closed: bool,
) -> ConstancyReport:
    """ADR-050's constancy check over the **domain mean of `c̄ + δc`** (Core §3.1; Spec §2.2's
    conservation category; ADR-076).

    *domain_means* is the mean of the full composition over the declared domain at each step of
    a chain — not `c̄` alone. **Computing the residual over `c̄` alone would be vacuous**: `c̄` is
    a parameter, trivially constant by construction, so a residual over it measures nothing.
    What conservation constrains, and what an open boundary actually moves, is the domain mean
    of the sum.

    The verdict is a diagnosis: see :class:`ConstancyVerdict`. Where a closed domain drifts, the
    repair named is ADR-050's — re-declare the domain open and name the flux — and not an
    adjustment to `c̄`.
    """
    if len(domain_means) < 2:
        raise ValueError(
            "a constancy residual needs at least two steps to have a drift: got "
            f"{len(domain_means)}"
        )
    if not (tolerance >= 0.0):
        raise ValueError(f"tolerance must be non-negative, got {tolerance}")

    means = tuple(float(m) for m in domain_means)
    drift = max(abs(m - means[0]) for m in means)
    held = drift <= tolerance

    if declared_closed and held:
        verdict = ConstancyVerdict.CONSISTENT_CLOSED
        diagnosis = (
            f"the mean over {region!r} held to {drift:.6g} <= {tolerance:.6g}; the domain is "
            "declared closed and behaves so — conservation as expected (ADR-050)"
        )
    elif declared_closed and not held:
        verdict = ConstancyVerdict.OPEN_DOMAIN_UNDECLARED
        diagnosis = (
            f"the mean over {region!r} drifted by {drift:.6g} > {tolerance:.6g} while the domain "
            "is declared CLOSED. ADR-050's diagnosis: the declared domain is OPEN. The repair is "
            "to re-declare it open and name the boundary flux (a DEPLETED_BY coupling on the "
            "fluctuation field), NOT to adjust c-bar — c-bar indexes the operator family and is "
            "not what moved"
        )
    elif not declared_closed and not held:
        verdict = ConstancyVerdict.CONSISTENT_OPEN
        diagnosis = (
            f"the mean over {region!r} drifted by {drift:.6g} and the domain is declared OPEN "
            "with a named flux — consistent, and the case a pass/fail verdict cannot express"
        )
    else:
        verdict = ConstancyVerdict.SUSPECT_CLOSED_DECLARATION
        diagnosis = (
            f"the mean over {region!r} held to {drift:.6g} <= {tolerance:.6g} while the domain is "
            "declared OPEN. Not an error — the declared flux may be negligible over this interval "
            "— but the declaration claims a transport the measurement does not exhibit, so it is "
            "reported rather than passed"
        )

    return ConstancyReport(
        verdict=verdict,
        max_absolute_drift=drift,
        tolerance=tolerance,
        region=region,
        declared_closed=declared_closed,
        means=means,
        diagnosis=diagnosis,
    )
