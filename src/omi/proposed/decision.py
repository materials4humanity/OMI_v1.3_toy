"""The proposed decision-extension declaration: the constitutive-extension declaration plus the coupled-quantity,
role and attainability declarations Parts 2–4 designed.

Cites Core §4 (the seven-item interface these refine rather than extend), Core §3.1
(the slot whose nonlocal member motivated the coupled-quantity construction), Core §5
(the inverse-problem taxonomy the attainable region completes), Spec §2.2 (declared
forms, whose validity region becomes a function over this space) and Spec §9.1 (the
level claim that needs a version).

**Composition, not modification, applied a second time** (ADR-042, ADR-059): a decision-extension
declaration *holds* a constitutive-extension declaration whole, which itself holds the v1.3 seven items
whole. So `omi.interface.diff` keeps operating on the v1.3 object unchanged, M11's
comparability evidence survives by construction, and two domains a version apart differ
only in what the later version adds.

Design only for the *content*: this module supplies the declarable shapes and the
checks that follow from them by arithmetic. It implements no operator and runs no
campaign.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from omi.interface import SpecificationVersion
from omi.proposed.declaration import ExtendedDeclaration

__all__ = [
    "SpeciesRole",
    "DeclaredDomainKind",
    "CouplingDirection",
    "TrackedDimensions",
    "CoupledQuantityDeclaration",
    "SpeciesRoleDeclaration",
    "AttainabilityVerdict",
    "AttainabilityReport",
    "AttainableRegion",
    "DecisionExtendedDeclaration",
]


class SpeciesRole(Enum):
    """What role a chemistry species plays in one declared region (ADR-051; Core §4
    items 1 and 2; `docs/V1.4-EDITS.md` E-29).

    The role attaches to a **(species, region) pair**, not to the species and not to the
    framework: the same quantity is a fixed index on the operator family in one chain and
    a decision variable in another, and neither reading is more correct. E-29's finding
    is that Core §6.2 uses the word "parameterised" while Core §4 supplies nowhere to
    declare a parameter; :attr:`PARAMETER` is that place.
    """

    PARAMETER = "parameter"
    """Fixed for the chain; indexes the operator family; transported by nothing. Realised
    as :attr:`CouplingDirection.INVARIANT` on item 1 (ADR-049)."""

    CONTROL = "control"
    """Set by the experimenter; lives in `𝒰_adm` (Core §4 item 2, unchanged)."""

    STATE = "state"
    """Evolves under some operator; occupies a slot of Core §3.1's state (item 1)."""


class DeclaredDomainKind(Enum):
    """Over *what* a coupled quantity has a value (ADR-049; Core §3.1's `ν`;
    `docs/V1.4-EDITS.md` E-22, E-25).

    Three cardinalities, covering exactly the cases E-22's revised proposal requires
    after a third domain forced its first proposal to be withdrawn: a quantity with no
    local value even in principle cannot be typed as a field over the body, and a
    quantity with a genuine per-point value cannot be typed as a single scalar.
    """

    GLOBAL_POINT = "global_point"
    """The trivial one-point domain: a single shared value, no local value exists."""

    REGIONS = "regions"
    """A declared finite collection of named subdomains, each carrying one value."""

    FIELD = "field"
    """A value at every point of a declared dimension set."""


class CouplingDirection(Enum):
    """*How* a coupled quantity is coupled to the point states, independently of where it
    lives (ADR-049; Core §3.1; `docs/V1.4-EDITS.md` E-22's second proposed wording, E-25).

    Each direction carries its own declaration obligation and its own residual check,
    because E-22's argument is that a corrected spatial type with the wrong coupling
    dynamics is no better than the original under-declaration.
    """

    DETERMINED_BY = "determined_by"
    """An instantaneous function of the point states; eliminable in principle. Checkable
    by a **closure residual**: the value at a step must be reproducible from that step's
    point states alone."""

    DEPLETED_BY = "depleted_by"
    """Conservation-coupled; carries its own dynamical state and memory; not eliminable.
    Checkable by a **conservation residual** over a closed step. This is the case Core
    §3.3's linear ensemble lift does not cover (E-25)."""

    INTERMEDIATE = "intermediate"
    """Spatially extended but primarily history-determined. Requires the history
    functional **and** a statement of why neither pure case applies."""

    INVARIANT = "invariant"
    """Constant along the chain; indexes the operator family. Checkable by a **constancy
    residual** — and a violation is diagnostic rather than merely negative: a mean over a
    *closed* domain is constant by conservation, so non-constancy means the declared
    domain is open and the coupling should have been :attr:`DEPLETED_BY` (ADR-050)."""


class TrackedDimensions(Enum):
    """At what spatial resolution a coupled quantity is tracked (ADR-049; Spec §4.4's
    dimensional-reduction argument arriving on a different axis).

    A closed set, so the choice is diffable across domains rather than free text. The
    justification beside it is not (see
    :attr:`CoupledQuantityDeclaration.tracked_justification`).
    """

    NONE = "none"
    IN_PLANE = "in_plane"
    THROUGH_THICKNESS = "through_thickness"
    FULL_3D = "full_3d"


@dataclass(frozen=True)
class CoupledQuantityDeclaration:
    """One quantity that is not owned by pointwise evolution: where it has a value, how
    it is coupled, at what resolution, and in what coordinates (ADR-049, ADR-052; Core
    §3.1; `docs/V1.4-EDITS.md` E-22, E-25, E-29).

    **A refinement of Core §4 item 1, not an eighth item** — item 1 already asks for
    "occupants of each slot, with resolution limits", and resolution limits are this
    construction's seed. `docs/V1.4-EDITS.md` E-46 records the separate finding that item
    1 is thereby hosting two structurally different declarations, and that the arity
    question is unresolved; this class is deliberately agnostic about where a revision
    puts it.
    """

    name: str
    domain_kind: DeclaredDomainKind
    coupling: CouplingDirection
    tracked: TrackedDimensions

    tracked_justification: str
    """Why this resolution is the right one — **required and non-empty at every kind**,
    including the degenerate one.

    A `GLOBAL_POINT` declaration tracked at `NONE` is an assertion of spatial uniformity,
    and that is exactly the assumption v1.3 never required anyone to defend (E-44). A
    free-text string **checks nothing by itself**, and E-17 and E-31 both warn about
    good-faith strings satisfying a requirement without establishing its property. What it
    buys is that the choice becomes visible to `omi.interface.diff`, so two
    implementations claiming operator reuse can be compared on it — weaker than a check,
    stronger than silence, and that is the honest description. An enumerated reason code
    beside the free text is a live candidate needing its own decision (ADR-049's Part 3
    gate) and is deliberately **not** implemented here.
    """

    regions: tuple[str, ...] = ()
    """Named subdomains, required when :attr:`domain_kind` is
    :attr:`DeclaredDomainKind.REGIONS` and forbidden otherwise."""

    descriptor_basis: tuple[str, ...] = ()
    """The coordinates the value is declared in (ADR-052): named functionals of the
    underlying space, not the underlying space itself.

    Empty is legal for a quantity that has no descriptor reading. Where it is non-empty
    it makes a **falsifiable claim about argument structure** — "this operator depends on
    chemistry only through these functionals" — testable by holding out a case that
    varies the underlying space at fixed descriptors."""

    underlying_space: tuple[str, ...] = ()
    """The ground-truth coordinates the descriptors are functionals of (ADR-052). Both are
    carried: the descriptors are the metric, these are the truth."""

    closure_note: str = ""
    """For :attr:`CouplingDirection.INVARIANT`, whether the domain over which constancy is
    claimed is **closed** — the field that turns a constancy violation into a specific
    corrective diagnosis rather than a bare failure (ADR-050)."""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a coupled quantity must be named")
        if not self.tracked_justification.strip():
            raise ValueError(
                f"quantity {self.name!r} declares no justification for tracked={self.tracked.value}: "
                "the justification is required at every kind, and most of all at the degenerate "
                "one, because an undeclared uniformity assumption is the defect class E-44 records"
            )
        if self.domain_kind is DeclaredDomainKind.REGIONS and not self.regions:
            raise ValueError(f"quantity {self.name!r} declares REGIONS with no named region")
        if self.domain_kind is not DeclaredDomainKind.REGIONS and self.regions:
            raise ValueError(
                f"quantity {self.name!r} names regions but its domain kind is "
                f"{self.domain_kind.value}; regions are meaningful only for REGIONS"
            )
        if self.descriptor_basis and not self.underlying_space:
            raise ValueError(
                f"quantity {self.name!r} declares a descriptor basis with no underlying space: "
                "ADR-052 requires both, since a descriptor without its ground truth cannot be "
                "held out against"
            )
        if self.coupling is CouplingDirection.INVARIANT and not self.closure_note.strip():
            raise ValueError(
                f"quantity {self.name!r} declares INVARIANT coupling without stating whether its "
                "domain is closed; without that, a constancy violation is a bare failure rather "
                "than the diagnosis ADR-050 makes it"
            )


@dataclass(frozen=True)
class SpeciesRoleDeclaration:
    """One species' role in one named region (ADR-051; Core §4 items 1–2).

    Per-region rather than per-species, because the same species holds different roles in
    different declared regions of one chain simultaneously — which is why the role
    attaches to the pair and why `REGIONS` is what makes the declaration expressible.
    """

    species: str
    region: str
    role: SpeciesRole
    note: str = ""

    def __post_init__(self) -> None:
        if not self.species or not self.region:
            raise ValueError("a role declaration needs both a species and a region")


class AttainabilityVerdict(Enum):
    """Why a requested point in descriptor space is or is not attainable (Core §5; ADR-053).

    An enum with distinct failures rather than a bool, for the reason CLAUDE.md invariant 8
    gives: the composition inverse's whole claim to being a *third* inverse problem is that
    its infeasibility certificate has no analogue in the other two, and a certificate that
    cannot say which constraint bound is not a certificate.
    """

    ATTAINABLE = "attainable"
    OUTSIDE_DESCRIPTOR_BOUNDS = "outside_descriptor_bounds"
    """A declared descriptor is outside the region any real member of the family occupies."""
    UNDERLYING_INFEASIBLE = "underlying_infeasible"
    """No point of the underlying space maps to these descriptors under the declared
    normalisation — the descriptors are individually plausible and jointly impossible."""
    EXCLUDED_PAIR = "excluded_pair"
    """A declared pairwise exclusion is violated."""
    OUTSIDE_ROUTE = "outside_route"
    """Attainable in principle and not by the declared preparation route."""


@dataclass(frozen=True)
class AttainabilityReport:
    """The measured basis for an :class:`AttainabilityVerdict`, never only the verdict
    (Core §5; CLAUDE.md §8).

    Every field is reported whatever the verdict, because a rejected request is
    informative: the margin says whether it was close, and which constraint bound says
    what a practitioner would have to change.
    """

    verdict: AttainabilityVerdict
    binding_constraint: str
    """The constraint with the largest violation, or ``"none"`` inside the region."""
    factors: Mapping[str, float]
    """Per-constraint violation factor; ``≤ 1`` means satisfied, by the same convention
    ADR-043 uses for validity bounds so the two reports read alike."""

    @property
    def attainable(self) -> bool:
        """Whether the requested point is attainable at all (Core §5's infeasibility
        question, as ADR-053 extends it to a third inverse problem)."""
        return self.verdict is AttainabilityVerdict.ATTAINABLE

    @property
    def worst_factor(self) -> float:
        """The largest per-constraint violation factor; `≤ 1` means every declared
        constraint is satisfied — the same scale Spec §2.2's validity report uses, so a
        practitioner reads one convention for both."""
        return max(self.factors.values()) if self.factors else 0.0


@dataclass(frozen=True)
class AttainableRegion:
    """The declared region of descriptor space that a real member of the family can
    occupy, and that the declared preparation route can reach (Core §5; ADR-053).

    **The object ADR-053 said no domain supplied.** ADR-053 designed the composition
    inverse and explicitly declined to design its infeasibility certificate, because the
    certificate needs a declared attainable region and inventing one for a domain that had
    not declared it would be the improvisation CLAUDE.md §4 forbids. A domain declaring
    this is what unblocks it.

    The certificate answers Core §5's own separating question — *what certifies
    infeasibility* — with something the control and structure inverses have no analogue
    for: not an apparatus constraint and not a reachability bound, but that the requested
    coordinates describe nothing that exists, or nothing this route can make.
    """

    descriptor_bounds: Mapping[str, tuple[float, float]]
    """Per-descriptor closed interval any real member occupies."""
    underlying_bounds: Mapping[str, tuple[float, float]]
    """Per-coordinate bounds on the underlying space (e.g. solubility limits)."""
    sums_to_one: tuple[str, ...] = ()
    """Underlying coordinates constrained to a simplex — a **structural** constraint, and
    architecture rather than a penalty (CLAUDE.md invariant 5): a normalisation violated
    by 3% is not a slightly wrong composition, it is not a composition."""
    excluded_pairs: tuple[tuple[str, str, float, str], ...] = ()
    """``(coordinate_a, coordinate_b, budget, reason)``: coordinates that cannot both be
    high, with the **product budget declared by the domain**.

    The budget is domain-supplied rather than a constant of this module, and that placement
    is the point. "Cannot both be high" is a claim about a particular chemistry — where the
    two coordinates' ranges are, and where their interaction actually bites — so a fixed
    budget here would be a domain claim living in domain-neutral code, which is the
    boundary CLAUDE.md invariant 3 draws. It would also be a number no domain had to
    defend, which is E-44's shape.

    A **product** rather than a sum, so the constraint is active only when both are high,
    which is what the phrase means."""
    route_note: str = ""
    """What the declared preparation route can and cannot reach, in prose — the one part of
    this declaration that is not machine-checkable, and marked as such rather than dressed
    up."""

    def __post_init__(self) -> None:
        if not self.descriptor_bounds:
            raise ValueError(
                "an attainable region with no descriptor bounds constrains nothing, which is the "
                "unbounded claim ADR-043 exists to prevent in the validity-range case"
            )
        for name, (low, high) in {**self.descriptor_bounds, **self.underlying_bounds}.items():
            if not low < high:
                raise ValueError(f"bound {name!r} is empty or inverted: ({low}, {high})")
        for a, b, budget, reason in self.excluded_pairs:
            if budget <= 0.0:
                raise ValueError(
                    f"exclusion {a!r}+{b!r} declares a non-positive product budget ({budget}), "
                    "which excludes every point including the origin"
                )
            if not reason.strip():
                raise ValueError(
                    f"exclusion {a!r}+{b!r} declares no reason: an exclusion without a mechanism "
                    "is an unexplained constraint on a practitioner's search, which is the "
                    "unsourced-assertion shape ADR-043 rejects for constitutive forms"
                )

    def report(self, descriptors: Mapping[str, float], underlying: Mapping[str, float]) -> AttainabilityReport:
        """Where a requested point sits relative to this region (Core §5; ADR-053).

        **Reported, never enforced**, by the same reasoning ADR-043 gives for validity
        ranges and E-28 measures independently: a constraint that blocks the optimiser
        rather than informing it composes into a new failure, and inverse design must be
        able to probe outside.

        Every declared bound MUST have a value; a missing one raises rather than being
        skipped, since a constraint silently omitted from a certificate is a constraint
        whose violation cannot be seen.
        """
        missing = [n for n in self.descriptor_bounds if n not in descriptors]
        missing += [n for n in self.underlying_bounds if n not in underlying]
        missing += [n for n in self.sums_to_one if n not in underlying]
        if missing:
            raise ValueError(
                f"no value supplied for declared constraint(s) {sorted(set(missing))}: an omitted "
                "constraint cannot be checked, and skipping it would hide the infeasibility the "
                "certificate exists to surface"
            )

        factors: dict[str, float] = {}
        for name, (low, high) in self.descriptor_bounds.items():
            factors[f"descriptor:{name}"] = _interval_factor(descriptors[name], low, high)
        for name, (low, high) in self.underlying_bounds.items():
            factors[f"underlying:{name}"] = _interval_factor(underlying[name], low, high)
        if self.sums_to_one:
            total = sum(underlying[n] for n in self.sums_to_one)
            factors["underlying:sums_to_one"] = abs(total - 1.0) / _SIMPLEX_TOLERANCE
        for a, b, budget, _ in self.excluded_pairs:
            product = underlying.get(a, 0.0) * underlying.get(b, 0.0)
            factors[f"excluded:{a}+{b}"] = product / budget

        binding = max(factors, key=lambda key: factors[key])
        if factors[binding] <= 1.0:
            return AttainabilityReport(AttainabilityVerdict.ATTAINABLE, "none", factors)
        if binding.startswith("descriptor:"):
            verdict = AttainabilityVerdict.OUTSIDE_DESCRIPTOR_BOUNDS
        elif binding.startswith("excluded:"):
            verdict = AttainabilityVerdict.EXCLUDED_PAIR
        else:
            verdict = AttainabilityVerdict.UNDERLYING_INFEASIBLE
        return AttainabilityReport(verdict, binding, factors)


_SIMPLEX_TOLERANCE = 1.0e-9
"""How far the declared simplex sum may drift before the point is not a composition at
all. Tight because this is a normalisation, not a physical bound (CLAUDE.md invariant 5)."""

def _interval_factor(value: float, low: float, high: float) -> float:
    """Violation factor for a closed interval: `≤ 1` inside, growing outside, on the same
    convention ADR-043's validity bounds use (Spec §2.2) so a practitioner reads one scale
    for both reports."""
    centre = 0.5 * (low + high)
    half_width = 0.5 * (high - low)
    return abs(value - centre) / half_width


@dataclass(frozen=True)
class DecisionExtendedDeclaration:
    """A decision-extension instantiation declaration: the constitutive extension's, plus the coupled-quantity, role
    and attainability declarations (Core §4; ADR-059).

    **The nesting is the point** (ADR-042 applied a second time). `omi.interface.diff`
    still receives a v1.3 :class:`~omi.interface.InstantiationDeclaration`, so every
    comparability result this repository has published survives unchanged, and a v1.3
    domain, a constitutive-extension domain and a decision-extension domain differ *only* in what each extension adds.
    """

    extended_core: ExtendedDeclaration
    coupled_quantities: tuple[CoupledQuantityDeclaration, ...] = ()
    species_roles: tuple[SpeciesRoleDeclaration, ...] = ()
    attainable_region: AttainableRegion | None = None
    decision_kind: str = ""
    """Which of Core §5's decisions this domain's chain exists to serve, in the domain's
    own words — process, usage, or campaign.

    Declared because `docs/V1.4-EDITS.md` E-43 found that a conformance level plus a
    framework version is still not self-describing without the *purpose* the claim is made
    for, and because the third kind is what this domain exists to exercise."""

    @property
    def specification_version(self) -> SpecificationVersion:
        """Always :attr:`~omi.interface.SpecificationVersion.PROPOSED_DECISION_EXTENSION` (Spec §9.1's
        level claim needs a version — `docs/V1.4-EDITS.md` E-35).

        A read-only property rather than a field, for the reason ADR-042 gives about the
        constitutive-extension carrier: a declaration carrying the decision extension is not a constitutive-extension declaration,
        and making that unrepresentable is cheaper than checking for it.
        """
        return SpecificationVersion.PROPOSED_DECISION_EXTENSION

    def roles_for(self, species: str) -> Mapping[str, SpeciesRole]:
        """Every declared region's role for one species (ADR-051; Core §4 item 1).

        The query that makes ADR-051's central claim checkable: a species holding
        different roles in different regions of the same chain is expressible, and a reader
        can see it rather than having to infer it.
        """
        return {d.region: d.role for d in self.species_roles if d.species == species}

    def parameter_only_species(self) -> tuple[str, ...]:
        """Species whose role is :attr:`SpeciesRole.PARAMETER` in every region they are
        declared in (ADR-051; Core §2.6's property/performance distinction).

        E-29's part 2 made mechanical: a readout depending only on these is a readout of
        the grade rather than of the process, which Core §2.6 says is a legitimate case
        that must not be confused with a defect.
        """
        by_species: dict[str, set[SpeciesRole]] = {}
        for declaration in self.species_roles:
            by_species.setdefault(declaration.species, set()).add(declaration.role)
        return tuple(
            sorted(name for name, roles in by_species.items() if roles == {SpeciesRole.PARAMETER})
        )

    def quantities_with_coupling(self, coupling: CouplingDirection) -> tuple[str, ...]:
        """Names of coupled quantities declared with *coupling* (ADR-049; Core §3.1).

        Used by the refusal E-25 requires: a `DEPLETED_BY` quantity shared across an
        ensemble needs a mean-field lift, which Core §3.3's linear pushforward does not
        provide, so an implementation must refuse rather than compute ensemble-mean physics.
        """
        return tuple(q.name for q in self.coupled_quantities if q.coupling is coupling)
