"""Domain triage comparison (docs/ROADMAP.md M3 exit gate): "Triage
reproduces on both domains, and the contrast domain's poor observation suite
shows a materially different dangerous set." Extended at Phase 3.3 (docs/
ROADMAP.md): flagship's target set is re-run with `bend_angle` included
(CLAUDE.md invariant 10, Spec §3.3: "𝒟_i is defined relative to a *declared*
target set; if targets change, triage MUST be re-run" — the target set
changed at Phase 2 and this file predated that), and the full `Triage`
classification is asserted for both domains, not only `dangerous_set()`.

Flagship gets two sensors (force/torque mid-chain, a coating gauge at the
end) matching its declared "rich, multi-modal" observation suite (Core
§7.1). Contrast gets exactly one (terminal voltage, at the end only) — Core
§7.2's declared inversion, "genuinely poor" — since this toy model has no
state component standing in for the third declared modality (surface
temperature) at all, which is itself an honest reflection of how thin a
"poor observation suite" can be.
"""

from __future__ import annotations

import numpy as np

from omi.observability import (
    Observation,
    Triage,
    TriageResult,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.state import Metric

from omi_domains.contrast.build import build_chain as contrast_chain
from omi_domains.contrast.build import build_incoming_ensemble as contrast_incoming
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi_domains.flagship.build import build_chain as flagship_chain
from omi_domains.flagship.build import build_incoming_ensemble as flagship_incoming
from omi_domains.flagship.readouts import (
    AggregateHardness,
    BendAngleAtReferenceGeometry,
    CoatingGauge,
    ForceTorqueSensor,
)

from tests.conftest import ObservationRecorder

FLAGSHIP_TARGETS = [AggregateHardness(), BendAngleAtReferenceGeometry()]
"""Phase 3.3(b): includes `bend_angle` (ADR-037), the target set as
currently declared in `FLAGSHIP_DECLARATION.readout_catalogue` — the old,
single-target `[AggregateHardness()]` list this file used through Phase 2
is now stale by Spec §3.3's own re-run rule."""


def test_flagship_triage_runs_end_to_end() -> None:
    rng = np.random.default_rng(0)
    ensemble = flagship_incoming(100, rng)
    metric = Metric.from_ensemble(ensemble)
    chain = flagship_chain()
    nominal = nominal_trajectory(chain, ensemble[0])

    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(metric)
    result = danger_triage(chain, nominal, 0, gramian, prior, FLAGSHIP_TARGETS, sensors)

    assert len(result.directions) == ensemble.schema.size
    assert result.dangerous_set() is not None  # runs without error; may be empty


def test_contrast_triage_runs_end_to_end() -> None:
    rng = np.random.default_rng(1)
    ensemble = contrast_incoming(100, rng)
    metric = Metric.from_ensemble(ensemble)
    chain = contrast_chain(n_cycles=5, current=2.0)
    nominal = nominal_trajectory(chain, ensemble[0])

    sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=len(chain.segments)),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(metric)
    result = danger_triage(chain, nominal, 0, gramian, prior, [DendriteRisk()], sensors)

    assert len(result.directions) == ensemble.schema.size


def test_flagship_triage_with_bend_angle_does_not_materially_reorder_the_dangerous_set(
    observe: ObservationRecorder,
) -> None:
    """Phase 3.3(b): re-run with the expanded target set, and report whether
    the dangerous set changes, per the framework's own re-run rule.

    It does not, materially — every direction's danger score scales by
    (very close to) the same factor, and the ranking and triage labels are
    unchanged. The reason is itself the finding, not engineered: `BendAngle`
    at the declared reference geometry (`BendAngleAtReferenceGeometry`,
    ADR-037) and `AggregateHardness` are both functionals of the *same*
    `HardnessConstitutiveOperator`, and this domain's constitutive law's
    state-dependence does not vary with the applied control — so the two
    readouts' Jacobians are numerically near-identical (checked directly:
    max abs difference ~5e-9, pure finite-difference noise), and adding a
    near-duplicate target roughly doubles every influence term uniformly
    rather than discriminating among directions differently. Target
    declaration *would* be load-bearing here if flagship declared a second
    target with a genuinely different sensitivity structure — this one just
    is not, because of how the two readouts are constructed, not because
    target expansion is inert in general.
    """
    rng = np.random.default_rng(2)
    ensemble = flagship_incoming(100, rng)
    metric = Metric.from_ensemble(ensemble)
    chain = flagship_chain()
    nominal = nominal_trajectory(chain, ensemble[0])
    sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    gramian = compute_gramian(chain, nominal, 0, sensors)
    prior = default_prior_covariance(metric)

    old_result = danger_triage(chain, nominal, 0, gramian, prior, [AggregateHardness()], sensors)
    new_result = danger_triage(chain, nominal, 0, gramian, prior, FLAGSHIP_TARGETS, sensors)

    old_labels = [d.label for d in old_result.directions]
    new_labels = [d.label for d in new_result.directions]
    old_scores = np.array([d.danger_score for d in old_result.directions])
    new_scores = np.array([d.danger_score for d in new_result.directions])

    observe("old_target_labels", [label.value for label in old_labels], "== new_target_labels, same order")
    observe("new_target_labels", [label.value for label in new_labels], "== old_target_labels, same order")
    observe("old_dangerous_set_size", len(old_result.dangerous_set()), "== new_dangerous_set_size")
    observe("new_dangerous_set_size", len(new_result.dangerous_set()), "== old_dangerous_set_size")
    assert old_labels == new_labels
    assert len(old_result.dangerous_set()) == len(new_result.dangerous_set())

    # Not exactly 2x in general (BendAngleAtReferenceGeometry's Jacobian is
    # numerically close to, not exactly equal to, AggregateHardness's), but
    # tight enough to confirm uniform scaling rather than reordering.
    nonzero = old_scores > 0
    ratios = new_scores[nonzero] / old_scores[nonzero]
    observe("danger_score_ratio_new_over_old", ratios.tolist(), "nearly constant across directions")
    assert np.std(ratios) < 0.05 * np.mean(ratios)


def _label_set(result: TriageResult) -> set[str]:
    return {d.label.value for d in result.directions}


def test_full_triage_classification_is_asserted_for_both_domains(observe: ObservationRecorder) -> None:
    """Phase 3.3(c): assert on the full `Triage` classification, not only
    `dangerous_set()`, for both domains. Weighted toward contrast per the
    hypothesis that its poor observation suite and lack of erasure are
    exactly the condition (Core §3.8: "information accrues only through
    downstream terms") that should produce `Triage.INFERRED`.

    Finding, reported plainly rather than adjusted to look different: at
    `time_index=0` (the query point both domains' own existing tests use —
    "how identifiable is the incoming state"), only two of Spec §3.3's four
    categories are *reachable at all* for either domain, for two structural
    reasons, neither particular to Phase 3.3's changes:

    1. `Triage.OBSERVED` requires a "near-diagonal" observation — one at
       (within `near_diagonal_window` of) the query index. Both domains'
       declared sensor suites place every sensor strictly *after* index 0
       (flagship: indices 1, 2; contrast: index 5) — there is no near-
       diagonal observation to `time_index=0` in either domain, so
       `near_diagonal_share` is `None` for every direction and `OBSERVED`
       can never be assigned at this query point, in either domain.
    2. `Triage.OBSERVED_BUT_IRRELEVANT` and `Triage.MARGINALISABLE` both
       require a direction to be "not influential" (influence below the
       median). Both domains' target sets are low-dimensional relative to
       state size (flagship: two readouts built from the same three-
       component-sensitive constitutive operator; contrast: one scalar
       readout touching two components) — well over half of all
       eigendirections have *exactly zero* influence, pushing
       `influence_median` to exactly `0.0`, and the classifier's `>=`
       comparison then makes *every* direction "influential" by
       definition. Confirmed directly (`result.influence_median == 0.0`
       for both domains at this query point).

    So `Triage.INFERRED` does appear in both domains (see below), but this
    is not, by itself, the framework's distinctive case fully exercised —
    with `OBSERVED` structurally unreachable at this query point, every
    identifiable+influential direction is *automatically* `INFERRED` by
    elimination, not because a genuine near-diagonal alternative was ruled
    out for that specific direction. Contrast's `INFERRED` directions here
    also carry ~zero danger score (the single sensor and single target
    barely touch most directions) — present as a label, not as a
    demonstration that a *dangerous* direction is specifically inferred
    rather than observed. This is reported as the finding Phase 3.3(c)
    asks for, not adjusted to manufacture a stronger one.
    """
    flagship_rng = np.random.default_rng(2)
    flagship_ensemble = flagship_incoming(100, flagship_rng)
    flagship_metric = Metric.from_ensemble(flagship_ensemble)
    f_chain = flagship_chain()
    f_nominal = nominal_trajectory(f_chain, flagship_ensemble[0])
    f_sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    f_gramian = compute_gramian(f_chain, f_nominal, 0, f_sensors)
    f_prior = default_prior_covariance(flagship_metric)
    f_result = danger_triage(f_chain, f_nominal, 0, f_gramian, f_prior, FLAGSHIP_TARGETS, f_sensors)

    contrast_rng = np.random.default_rng(1)
    contrast_ensemble = contrast_incoming(100, contrast_rng)
    contrast_metric = Metric.from_ensemble(contrast_ensemble)
    c_chain = contrast_chain(n_cycles=5, current=2.0)
    c_nominal = nominal_trajectory(c_chain, contrast_ensemble[0])
    c_sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=len(c_chain.segments)),
    ]
    c_gramian = compute_gramian(c_chain, c_nominal, 0, c_sensors)
    c_prior = default_prior_covariance(contrast_metric)
    c_result = danger_triage(c_chain, c_nominal, 0, c_gramian, c_prior, [DendriteRisk()], c_sensors)

    f_labels = _label_set(f_result)
    c_labels = _label_set(c_result)
    observe("flagship_label_set", sorted(f_labels), "subset of {inferred, dangerous}; see docstring")
    observe("contrast_label_set", sorted(c_labels), "subset of {inferred, dangerous}; see docstring")
    observe("flagship_influence_median", f_result.influence_median, "== 0.0 (collapses OBSERVED_BUT_IRRELEVANT/MARGINALISABLE)")
    observe("contrast_influence_median", c_result.influence_median, "== 0.0 (same mechanism)")

    allowed = {
        Triage.OBSERVED.value,
        Triage.INFERRED.value,
        Triage.DANGEROUS.value,
        Triage.MARGINALISABLE.value,
        Triage.UNRESOLVED.value,
    }
    assert f_labels <= allowed
    assert c_labels <= allowed
    assert Triage.OBSERVED.value not in f_labels
    assert Triage.OBSERVED.value not in c_labels
    assert f_result.influence_median == 0.0
    assert c_result.influence_median == 0.0

    # ADR-061: both domains now report UNRESOLVED at this index, and the reason is
    # substantive rather than presentational. At time_index 0 with the framework
    # default window of 0 there is no near-diagonal observation in either declared
    # suite, so for a direction carrying no Gramian information at all the
    # dominance ratio is undefined -- and Spec 3.3's "inferred" requires the
    # direction to be identifiable FROM THE TOTAL, which it is not. The superseded
    # criterion swept those directions into `inferred` through its else-branch.
    observe("flagship_abstained_fraction", f_result.abstained_fraction, "> 0 -- ADR-061's required output")
    observe("contrast_abstained_fraction", c_result.abstained_fraction, "> 0 -- ADR-061's required output")
    assert f_result.abstained_fraction > 0.0
    assert c_result.abstained_fraction > 0.0

    # The corrected `inferred` sets, and the ones the superseded criterion reported.
    # Recorded under NEW names: the old names' values are declared audit-gate
    # exceptions (audit/e53-label-changes.json), and silently reusing a name whose
    # meaning changed is exactly what that file exists to prevent.
    c_inferred = list(c_result.inferred_set())
    f_inferred = list(f_result.inferred_set())
    observe(
        "contrast_inferred_danger_scores_adr061",
        [d.danger_score for d in c_inferred],
        "present (len > 0); ~zero, per docstring -- not evidence of a dangerous inferred direction",
    )
    observe(
        "flagship_inferred_danger_scores_adr061",
        [d.danger_score for d in f_inferred],
        "present (len > 0); ALL ZERO under ADR-061 -- see below",
    )
    observe(
        "flagship_unresolved_danger_scores_adr061",
        [d.danger_score for d in f_result.unresolved_set()],
        "narrative; contains flagship's two largest danger scores",
    )
    assert len(c_inferred) > 0
    assert len(f_inferred) > 0

    # **The correction that matters.** Under the superseded criterion flagship's two
    # LARGEST danger scores were reported as `inferred` -- the framework's own
    # differentiator, "what no tabular baseline can recover" (Core 3.8). They carry
    # no observational information at all: their dominance ratio is undefined
    # because neither near-diagonal nor downstream terms contribute. They were
    # classed identifiable by the uncertainty median (a tight PRIOR, not data),
    # which is E-48's first-half degeneracy. Asserting the correction so a later
    # change cannot silently re-inflate the differentiator.
    assert all(d.danger_score == 0.0 for d in f_inferred), (
        "flagship reports a nonzero-danger inferred direction again: check whether it "
        "carries real Gramian information or whether the else-branch is back"
    )
    assert max((d.danger_score for d in f_result.unresolved_set()), default=0.0) > 0.0


def _unresolved_danger_fraction(chain, nominal, prior, sensors, target_readouts) -> float:  # type: ignore[no-untyped-def]
    """What fraction of the *no-information* target variance (using the bare
    prior, as if nothing were ever observed) is still sitting in directions
    the declared sensor suite leaves dangerous?

    Not a direction-count fraction: with a per-domain median split (ADR-020),
    roughly half of any domain's directions are "influential" and half
    "identifiable" *by construction*, so comparing dangerous-direction
    *counts* across two different domains compares two different medians,
    not sensing quality. Comparing variance against the common, sensor-free
    baseline (the prior) is a like-for-like measure across domains.
    """
    gramian = compute_gramian(chain, nominal, 0, sensors)
    result = danger_triage(chain, nominal, 0, gramian, prior, target_readouts, sensors)
    dangerous_variance = sum(d.danger_score for d in result.dangerous_set())

    no_sensors_gramian = compute_gramian(chain, nominal, 0, [])
    no_sensors_result = danger_triage(chain, nominal, 0, no_sensors_gramian, prior, target_readouts, [])
    total_unobserved_variance = sum(d.danger_score for d in no_sensors_result.directions)

    return dangerous_variance / total_unobserved_variance


def test_contrasts_poor_observation_suite_leaves_more_target_variance_dangerous(
    observe: ObservationRecorder,
) -> None:
    """The actual M3 exit-gate comparison: the contrast domain's poor,
    single-sensor observation suite must leave a materially larger fraction
    of its own no-sensor target variance dangerous (influential and
    unidentifiable, Spec §3.3) than the flagship's two-sensor suite does.

    Re-run with the expanded flagship target set (Phase 3.3(b)): the
    fraction is unaffected (a ratio is invariant to uniformly rescaling all
    directions' danger scores, and `BendAngleAtReferenceGeometry`'s addition
    does exactly that here — see the reordering test above), so the M3
    conclusion is unchanged, not merely re-checked.
    """
    flagship_rng = np.random.default_rng(2)
    flagship_ensemble = flagship_incoming(100, flagship_rng)
    flagship_metric = Metric.from_ensemble(flagship_ensemble)
    f_chain = flagship_chain()
    f_nominal = nominal_trajectory(f_chain, flagship_ensemble[0])
    f_sensors = [
        Observation("force_torque", ForceTorqueSensor(), np.array([[0.05]]), time_index=1),
        Observation("coating_gauge", CoatingGauge(), np.array([[0.01]]), time_index=2),
    ]
    f_prior = default_prior_covariance(flagship_metric)
    f_fraction = _unresolved_danger_fraction(f_chain, f_nominal, f_prior, f_sensors, FLAGSHIP_TARGETS)

    contrast_rng = np.random.default_rng(3)
    contrast_ensemble = contrast_incoming(100, contrast_rng)
    contrast_metric = Metric.from_ensemble(contrast_ensemble)
    c_chain = contrast_chain(n_cycles=5, current=2.0)
    c_nominal = nominal_trajectory(c_chain, contrast_ensemble[0])
    c_sensors = [
        Observation("terminal_voltage", TerminalVoltage(), np.array([[0.01]]), time_index=len(c_chain.segments)),
    ]
    c_prior = default_prior_covariance(contrast_metric)
    c_fraction = _unresolved_danger_fraction(c_chain, c_nominal, c_prior, c_sensors, [DendriteRisk()])

    observe("flagship_unresolved_danger_fraction", f_fraction, "< contrast_unresolved_danger_fraction")
    observe("contrast_unresolved_danger_fraction", c_fraction, "> flagship_unresolved_danger_fraction")

    assert c_fraction > f_fraction
