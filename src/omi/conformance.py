"""Conformance levels, the automated check suite, calibration diagnostics,
and the rollout-length error curve.

Cites Spec §9 in full: §9.1 the OMI-0/1/2 level table, §9.2 the nine
automated checks (each a residual, never a pass/fail), §9.5 the calibration
diagnostics an implementation MUST report. ADR-028 (docs/DECISIONS.md) fixes
what this module leaves open: conformance is a reporting-*completeness*
gate against Spec §9.1's own "reported"/"run and reported"/"declared"
wording, not a numeric threshold (S-9.4's falsification thresholds are a
separate, PASS-D concern this module explicitly refuses); every diagnostic a
level cites is supplied by the caller, never recomputed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Sequence

import numpy as np
from scipy import stats

from omi.chain import Chain
from omi.gaps import NotSpecified
from omi.interface import InstantiationDeclaration, SpecificationVersion
from omi.inverse import ReachabilityCertificate
from omi.observability import TriageResult
from omi.state import FloatArray, Metric, State
from omi.sufficiency import DeficitResult


class ConformanceLevel(IntEnum):
    """Spec §9.1's three conformance levels, ordered so a higher level's
    requirements are a strict superset of a lower one's ("OMI-1 = OMI-0 +
    ...")."""

    OMI_0 = 0
    OMI_1 = 1
    OMI_2 = 2


@dataclass(frozen=True)
class RequirementStatus:
    """One line item of Spec §9.1's level table, checked for presence
    (ADR-028) rather than for a numeric threshold — the detail string always
    says *why*, never just *whether*."""

    name: str
    citation: str
    level: ConformanceLevel
    satisfied: bool
    detail: str


@dataclass(frozen=True)
class CalibrationReport:
    """Spec §9.5's required calibration diagnostics — "MUST be reported, not
    only point-error metrics" — bundled together so none can be quoted
    without the others."""

    pit_values: FloatArray
    """The probability-integral-transform value per case: the fraction of
    that case's predictive ensemble at or below the observation. Uniform on
    ``[0, 1]`` under perfect calibration."""
    pit_uniformity_residual: float
    """Kolmogorov-Smirnov statistic of :attr:`pit_values` against
    ``Uniform(0, 1)`` — 0 is perfect calibration, never asserted as a
    pass/fail (CLAUDE.md §8)."""
    mean_crps: float
    """Mean continuous ranked probability score across cases (the standard
    ensemble/energy-score estimator)."""
    nominal_coverage_level: float
    empirical_coverage: float
    """Fraction of cases whose observation fell inside the
    :attr:`nominal_coverage_level` central credible interval of that case's
    predictive ensemble."""


def pit_values(predictive_samples: FloatArray, observations: FloatArray) -> FloatArray:
    """The probability-integral transform of each observation against its
    own case's predictive ensemble (Spec §9.5): ``PIT_i = (1/M) * #{x in
    ensemble_i : x <= observation_i}``, the empirical predictive CDF
    evaluated at the observation.
    """
    n_cases, _n_ensemble = predictive_samples.shape
    result = np.zeros(n_cases)
    for i in range(n_cases):
        result[i] = np.mean(predictive_samples[i] <= observations[i])
    return result


def crps_ensemble(samples: FloatArray, observation: float) -> float:
    """The continuous ranked probability score for one case's predictive
    ensemble (Spec §9.5), by the standard energy-score estimator (Gneiting &
    Raftery 2007): ``E|X - y| - (1/2) E|X - X'|`` for ``X, X'`` independent
    draws from the predictive ensemble.
    """
    n = samples.shape[0]
    term1 = float(np.mean(np.abs(samples - observation)))
    term2 = float(np.mean(np.abs(samples[:, np.newaxis] - samples[np.newaxis, :]))) / 2.0
    return term1 - term2


def empirical_coverage(
    predictive_samples: FloatArray, observations: FloatArray, nominal_level: float
) -> float:
    """The fraction of cases whose observation lands inside the
    *nominal_level* central credible interval of that case's own predictive
    ensemble (Spec §9.5's "empirical coverage of nominal intervals")."""
    n_cases, _n_ensemble = predictive_samples.shape
    alpha = 1.0 - nominal_level
    lower_q = alpha / 2.0
    upper_q = 1.0 - alpha / 2.0
    covered = 0
    for i in range(n_cases):
        lower, upper = np.quantile(predictive_samples[i], [lower_q, upper_q])
        if lower <= observations[i] <= upper:
            covered += 1
    return float(covered / n_cases)


def calibration_report(
    predictive_samples: FloatArray, observations: FloatArray, nominal_coverage_level: float = 0.9
) -> CalibrationReport:
    """Assemble Spec §9.5's calibration diagnostics for a batch of cases,
    each with its own ``(n_ensemble,)`` predictive sample and scalar
    observation."""
    pit = pit_values(predictive_samples, observations)
    ks_statistic, _p = stats.kstest(pit, "uniform")
    mean_crps = float(np.mean([crps_ensemble(predictive_samples[i], observations[i]) for i in range(len(pit))]))
    coverage = empirical_coverage(predictive_samples, observations, nominal_coverage_level)
    return CalibrationReport(pit, float(ks_statistic), mean_crps, nominal_coverage_level, coverage)


def rollout_length_error_curve(
    chain: Chain, baseline: State, perturbed: State, metric: Metric
) -> FloatArray:
    """The declared-metric distance between a baseline and a perturbed
    trajectory at every prefix length of *chain* (CLAUDE.md §5 invariant 7:
    "report rollout-length error curves, never one-step error alone" — the
    gap between the one-step and full-length entries is composability's
    honest measure). A direct generalisation of the M2 error-compounding
    demonstration (``tests/test_error_compounding.py``) to a chain of any
    length, satisfying OMI-0's own line item (Spec §9.1) generically —
    before M8 there is no learned-vs-analytic gap to plot, so this curve is
    the chain's own composability signature; once M8 introduces learned
    operators, the same function compares a learned rollout against its
    analytic (ground-truth) counterpart with no change to this code.
    """
    distances = np.zeros(len(chain.segments))
    b, p = baseline, perturbed
    for i, segment in enumerate(chain.segments):
        b = segment.operator.step(b, segment.control)
        p = segment.operator.step(p, segment.control)
        distances[i] = metric.distance(b, p)
    return distances


def measure_closure_defect(*_args: object, **_kwargs: object) -> float:
    """Refuses: Spec §6's closure-defect *measurement procedure* is `[Pass
    C]` in its entirety (docs/COVERAGE.md row S-6) — only the definition
    (Core §3.7) is specified, not how to estimate ``‖𝒟_λ‖`` from a chain.
    Called only when a chain genuinely crosses a scale
    (``ConformanceInputs.scale_bridging_occurs``); at M1-M7 neither declared
    domain's *executed* chain does (ADR-028), so this refusal is never
    exercised in this repository's own conformance demonstrations.
    """
    raise NotSpecified(
        "S-6",
        "Spec §6",
        "the closure-defect measurement procedure has no derivation in the "
        "Specification; only the definition (Core §3.7) is given",
    )


@dataclass(frozen=True)
class AutomatedCheckResult:
    """One of Spec §9.2's nine automated checks: a residual, or an
    explanation of why none is available yet — never a bare pass/fail
    (Spec §9.2: "Each returns a residual, not a pass/fail")."""

    name: str
    residual: float | None
    detail: str


@dataclass(frozen=True)
class ConformanceInputs:
    """Every diagnostic a conformance claim may cite (Spec §9.1), supplied
    by the caller from the modules that actually produce it (ADR-028) —
    `conformance.py` checks for presence, it does not compute these itself
    except for :attr:`rollout_error_curve` and :attr:`calibration`, which
    have no earlier home (built directly in this module).
    """

    declaration: InstantiationDeclaration
    metric: Metric
    specification_version: SpecificationVersion
    """Which version of Core and Spec the resulting claim is made against
    (Spec §9.1; `docs/V1.4-EDITS.md` E-35; ADR-042). Required with no default,
    deliberately: a default would let a proposed-v1.4 caller silently produce a
    report labelled v1.3, which is precisely the ambiguity E-35 names."""

    rollout_error_curve: FloatArray | None = None
    semigroup_residuals: FloatArray | None = None
    sufficiency_result: DeficitResult | None = None
    triage_result: TriageResult | None = None
    calibration: CalibrationReport | None = None
    grouped_splits_enforced: bool = True
    """Structural (ADR-028 point 5): no random-split code path exists
    anywhere in this repository (CLAUDE.md §5 invariant 6), so this is
    ``True`` by construction rather than computed from a data loader that
    does not yet exist."""

    scale_bridging_occurs: bool = False
    """Whether the *actually executed* chain crosses a scale (ADR-028 point
    4) — not whether the domain's declared scope eventually will."""
    closure_defect: float | None = None

    lipschitz_spectrum: FloatArray | None = None
    innovation_drift_residual: float | None = None
    adversarial_constraint_residual: float | None = None
    """Not available until M8 introduces `constraints.py`; ``None`` here is
    the honest, current state, not a placeholder standing in for a value."""

    class_b_volume_scaling_residual: float | None = None
    reachability_certificates: tuple[ReachabilityCertificate, ...] | None = None
    """Typed against `omi.inverse.ReachabilityCertificate` (docs/V1.4-EDITS.md
    E-17), not a bare label — Core §5 is unconditional that "learned
    reachable sets are unsound and cannot discharge this contract," and a
    string tuple gave the type system nothing to reject. This does not by
    itself guarantee the *content* of a supplied certificate is honest (a
    caller can still construct a `ReachabilityCertificate` for an invariant
    it does not actually hold), only that whatever is reported is at least
    an instance of the sound, `Φ(s)=w·s` artefact Spec §7.1 defines — not a
    forward-sampling result or any other unsound stand-in."""
    prospective_inverse_design_trial: tuple[float, float] | None = None
    """``(hit_rate, interval_calibration)`` — not available until M9."""


def automated_check_suite(inputs: ConformanceInputs) -> tuple[AutomatedCheckResult, ...]:
    """Spec §9.2's nine automated checks, each a residual where available
    and an explanation where not — runnable in CI, wired to whichever
    diagnostics *inputs* already carries rather than recomputed here
    (ADR-028)."""
    checks = []

    if inputs.semigroup_residuals is not None:
        checks.append(
            AutomatedCheckResult(
                "semigroup_consistency", float(np.max(inputs.semigroup_residuals)), "max residual across splits"
            )
        )
    else:
        checks.append(AutomatedCheckResult("semigroup_consistency", None, "no semigroup residuals supplied"))

    if inputs.sufficiency_result is not None:
        checks.append(
            AutomatedCheckResult(
                "matched_history_sufficiency", inputs.sufficiency_result.deficit_squared, "Spec §1.2 deficit_squared"
            )
        )
    else:
        checks.append(AutomatedCheckResult("matched_history_sufficiency", None, "no sufficiency test run"))

    if inputs.scale_bridging_occurs:
        if inputs.closure_defect is not None:
            checks.append(AutomatedCheckResult("closure_defect", inputs.closure_defect, "‖D_lambda‖"))
        else:
            checks.append(
                AutomatedCheckResult(
                    "closure_defect", None, "scale bridging occurs but S-6 is unspecified (refused)"
                )
            )
    else:
        checks.append(AutomatedCheckResult("closure_defect", None, "not applicable: no scale bridging executed"))

    if inputs.rollout_error_curve is not None:
        checks.append(
            AutomatedCheckResult(
                "rollout_length_error_curve",
                float(inputs.rollout_error_curve[-1]),
                "terminal entry of the curve; full curve in ConformanceInputs",
            )
        )
    else:
        checks.append(AutomatedCheckResult("rollout_length_error_curve", None, "no rollout error curve supplied"))

    if inputs.lipschitz_spectrum is not None:
        checks.append(
            AutomatedCheckResult(
                "local_lipschitz_spectrum", float(np.max(inputs.lipschitz_spectrum)), "largest singular value"
            )
        )
    else:
        checks.append(AutomatedCheckResult("local_lipschitz_spectrum", None, "no Lipschitz spectrum supplied"))

    if inputs.calibration is not None:
        checks.append(
            AutomatedCheckResult(
                "calibration", inputs.calibration.pit_uniformity_residual, "PIT-uniformity KS statistic"
            )
        )
    else:
        checks.append(AutomatedCheckResult("calibration", None, "no calibration report supplied"))

    if inputs.adversarial_constraint_residual is not None:
        checks.append(
            AutomatedCheckResult(
                "adversarial_constraint_satisfaction", inputs.adversarial_constraint_residual, "worst-case violation"
            )
        )
    else:
        checks.append(
            AutomatedCheckResult(
                "adversarial_constraint_satisfaction", None, "constraints.py not yet built (docs/ROADMAP.md M8)"
            )
        )

    if inputs.reachability_certificates is not None:
        checks.append(
            AutomatedCheckResult(
                "reachability_certificates", float(len(inputs.reachability_certificates)), "certificate count"
            )
        )
    else:
        checks.append(
            AutomatedCheckResult(
                "reachability_certificates", None, "inverse.py not yet built (docs/ROADMAP.md M9)"
            )
        )

    if inputs.innovation_drift_residual is not None:
        checks.append(
            AutomatedCheckResult("innovation_based_drift_monitoring", inputs.innovation_drift_residual, "NIS statistic")
        )
    else:
        checks.append(
            AutomatedCheckResult("innovation_based_drift_monitoring", None, "no innovation drift report supplied")
        )

    return tuple(checks)


_LEVEL_REQUIREMENTS: tuple[tuple[str, str, ConformanceLevel], ...] = (
    ("typed_chain_and_declared_interface", "Spec §9.1 (OMI-0)", ConformanceLevel.OMI_0),
    ("readouts_typed_and_classed", "Spec §9.1 (OMI-0)", ConformanceLevel.OMI_0),
    ("grouped_splits_enforced", "Spec §9.1 (OMI-0) / §9.3", ConformanceLevel.OMI_0),
    ("rollout_length_error_curve_reported", "Spec §9.1 (OMI-0)", ConformanceLevel.OMI_0),
    ("sufficiency_test_run_and_reported", "Spec §9.1 (OMI-1) / §8", ConformanceLevel.OMI_1),
    ("semigroup_residuals_reported", "Spec §9.1 (OMI-1) / §9.2", ConformanceLevel.OMI_1),
    ("observability_triage_with_dangerous_set_declared", "Spec §9.1 (OMI-1) / §3", ConformanceLevel.OMI_1),
    ("calibration_diagnostics_reported", "Spec §9.1 (OMI-1) / §9.5", ConformanceLevel.OMI_1),
    ("closure_defect_wherever_scale_bridging_occurs", "Spec §9.1 (OMI-1) / §6", ConformanceLevel.OMI_1),
    (
        "prospective_inverse_design_trial_reported",
        "Spec §9.1 (OMI-2) / §9.3",
        ConformanceLevel.OMI_2,
    ),
    ("reachability_certificates_reported", "Spec §9.1 (OMI-2) / §7.1", ConformanceLevel.OMI_2),
    (
        "class_b_volume_scaling_validation_at_3plus_volumes",
        "Spec §9.1 (OMI-2) / §4.4",
        ConformanceLevel.OMI_2,
    ),
)


def _check_satisfied(name: str, inputs: ConformanceInputs) -> tuple[bool, str]:
    if name == "typed_chain_and_declared_interface":
        return True, "State/Ensemble are typed dataclasses checked by mypy --strict in CI (ADR-028)"
    if name == "readouts_typed_and_classed":
        satisfied = len(inputs.declaration.readout_catalogue) > 0
        return satisfied, f"{len(inputs.declaration.readout_catalogue)} readout(s) declared"
    if name == "grouped_splits_enforced":
        return inputs.grouped_splits_enforced, "no random-split code path exists in this repository"
    if name == "rollout_length_error_curve_reported":
        return inputs.rollout_error_curve is not None, "ConformanceInputs.rollout_error_curve"
    if name == "sufficiency_test_run_and_reported":
        return inputs.sufficiency_result is not None, "ConformanceInputs.sufficiency_result"
    if name == "semigroup_residuals_reported":
        return inputs.semigroup_residuals is not None, "ConformanceInputs.semigroup_residuals"
    if name == "observability_triage_with_dangerous_set_declared":
        return inputs.triage_result is not None, "ConformanceInputs.triage_result"
    if name == "calibration_diagnostics_reported":
        return inputs.calibration is not None, "ConformanceInputs.calibration"
    if name == "closure_defect_wherever_scale_bridging_occurs":
        if not inputs.scale_bridging_occurs:
            return True, "not applicable: no scale bridging is executed by this chain (ADR-028 point 4)"
        return inputs.closure_defect is not None, "scale bridging occurs; closure defect must be supplied (S-6 refused if not)"
    if name == "prospective_inverse_design_trial_reported":
        return inputs.prospective_inverse_design_trial is not None, "not available until M9 (inverse.py)"
    if name == "reachability_certificates_reported":
        return inputs.reachability_certificates is not None, "not available until M9 (inverse.py)"
    if name == "class_b_volume_scaling_validation_at_3plus_volumes":
        return inputs.class_b_volume_scaling_residual is not None, "ConformanceInputs.class_b_volume_scaling_residual"
    raise AssertionError(f"unhandled requirement {name!r}")


@dataclass(frozen=True)
class ConformanceReport:
    """A full conformance report (Spec §9.1): every requirement's status,
    plus the metric every metric-dependent quantity in it is stated against
    (docs/ROADMAP.md M7: "carries the declared metric alongside every
    metric-dependent quantity")."""

    declaration: InstantiationDeclaration
    metric: Metric
    specification_version: SpecificationVersion
    """The version of Core and Spec this claim is made against (Spec §9.1,
    which requires the *level* and not the version — `docs/V1.4-EDITS.md` E-35;
    ADR-042). Carried for the same reason :attr:`metric` is: a report is a
    record intended to outlive the run that produced it, so every field a reader
    needs in order to evaluate the claim belongs in the report rather than in
    the repository state that surrounded it."""
    requirements: tuple[RequirementStatus, ...]

    def unmet(self, level: ConformanceLevel) -> tuple[RequirementStatus, ...]:
        """Requirements at or below *level* that are not satisfied (Spec §9.1)."""
        return tuple(r for r in self.requirements if r.level <= level and not r.satisfied)

    def highest_claimable_level(self) -> ConformanceLevel:
        """The highest level whose requirements are entirely satisfied
        (Spec §9.1: "MUST NOT claim a level whose reporting requirements it
        has not met")."""
        for level in (ConformanceLevel.OMI_2, ConformanceLevel.OMI_1, ConformanceLevel.OMI_0):
            if not self.unmet(level):
                return level
        raise ConformanceNotMet(ConformanceLevel.OMI_0, self.unmet(ConformanceLevel.OMI_0))

    def claim(self, level: ConformanceLevel) -> ConformanceLevel:
        """Return *level* if every requirement at or below it is satisfied;
        otherwise raise :class:`ConformanceNotMet` naming exactly which
        requirements are missing (Spec §9.1: "MUST NOT claim a level whose
        reporting requirements it has not met"; docs/ROADMAP.md M7: "the
        report refuses to claim a level whose requirements are unmet")."""
        unmet = self.unmet(level)
        if unmet:
            raise ConformanceNotMet(level, unmet)
        return level


class ConformanceNotMet(Exception):
    """Raised by :meth:`ConformanceReport.claim` when a level's requirements
    (Spec §9.1) are not all satisfied (ADR-028): distinct from
    `omi.gaps.NotSpecified`, since a missing diagnostic is an evidentiary
    gap in a specific report, not a Specification derivation gap."""

    def __init__(self, level: ConformanceLevel, unmet: Sequence[RequirementStatus]) -> None:
        self.level = level
        self.unmet_requirements = tuple(unmet)
        lines = "\n".join(f"  - {r.name} ({r.citation}): {r.detail}" for r in unmet)
        message = f"cannot claim {level.name}: {len(unmet)} requirement(s) unmet\n{lines}"
        super().__init__(message)


class ConformanceVersionMismatch(Exception):
    """Raised by :func:`compare_reports` when two reports were produced against
    different :class:`~omi.interface.SpecificationVersion` values (Spec §9.1;
    `docs/V1.4-EDITS.md` E-35; ADR-042).

    Distinct from both `omi.gaps.NotSpecified` (a Specification derivation gap)
    and :class:`ConformanceNotMet` (an evidentiary gap in one report): this is a
    *category* error in the comparison itself. The levels being compared do not
    denote the same requirements, so no answer — not even "they differ" — would
    be meaningful.
    """

    def __init__(self, left: SpecificationVersion, right: SpecificationVersion) -> None:
        self.left = left
        self.right = right
        super().__init__(
            f"refusing to compare conformance reports across specification versions: "
            f"{left.value} vs {right.value}. Spec §9.1's level names are defined by its "
            f"level table, and that table changes between versions, so the same level "
            f"name does not denote the same requirements in both (docs/V1.4-EDITS.md "
            f"E-35). State explicitly which rows changed and compare requirement by "
            f"requirement instead."
        )


def compare_reports(
    left: ConformanceReport, right: ConformanceReport
) -> dict[str, tuple[bool, bool]]:
    """Compare two conformance reports requirement by requirement (Spec §9.1),
    **refusing outright** when their specification versions differ (ADR-042).

    The refusal is the point of this function; the returned diff is its payload.
    Within one version the level table is fixed, so both reports carry the same
    requirement names and the result maps each name whose satisfaction *differs*
    to its ``(left, right)`` flags — an empty dict meaning the two reports agree
    on every requirement.

    Raises :class:`ConformanceVersionMismatch` when
    ``left.specification_version is not right.specification_version``. A caller
    that genuinely wants a cross-version comparison must do what Spec §9.1's
    proposed wording requires (`docs/V1.4-EDITS.md` E-35): state which rows of
    the level table changed, and compare the affected requirements explicitly.
    There is deliberately no flag to suppress this.
    """
    if left.specification_version is not right.specification_version:
        raise ConformanceVersionMismatch(left.specification_version, right.specification_version)

    left_status = {r.name: r.satisfied for r in left.requirements}
    right_status = {r.name: r.satisfied for r in right.requirements}
    if set(left_status) != set(right_status):
        raise ValueError(
            "reports share a specification version but not a requirement set — "
            "the level table is fixed within a version, so this indicates one "
            "report was not produced by generate_report"
        )
    return {
        name: (left_status[name], right_status[name])
        for name in left_status
        if left_status[name] != right_status[name]
    }


def generate_report(inputs: ConformanceInputs) -> ConformanceReport:
    """Build a full :class:`ConformanceReport` from already-collected
    diagnostics (Spec §9.1; ADR-028) — a completeness check against Spec
    §9.1's own table, not a re-derivation of any diagnostic. The declared
    :class:`~omi.interface.SpecificationVersion` is carried through from
    *inputs* onto the report, never inferred (ADR-042)."""
    requirements = tuple(
        RequirementStatus(name, citation, level, *_check_satisfied(name, inputs))
        for name, citation, level in _LEVEL_REQUIREMENTS
    )
    return ConformanceReport(
        declaration=inputs.declaration,
        metric=inputs.metric,
        specification_version=inputs.specification_version,
        requirements=requirements,
    )
