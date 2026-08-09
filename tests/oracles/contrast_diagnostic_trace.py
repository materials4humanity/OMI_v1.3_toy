"""Which of the four diagnostics ADR-056's decision loop consumes can actually **change**
over a contrast campaign — measured without implementing the loop.

Part 5(1) is design-only for the loop structure, so the loop is not built. What *is*
built is the trace of its inputs: the diagnostics evaluated at every interval of a
declared contrast campaign, so ADR-056's decision predicates can be evaluated against
recorded traces rather than guessed at. A diagnostic whose reading never moves cannot
change a decision, whatever rule is written on top of it — that conclusion needs the
trace, not the loop.

Cites Core §3.8 and Spec §3.3 (the triage), Spec §1.7 (the blocking trichotomy), Spec
§2.2 with ADR-043 (the validity report), Spec §10 (the innovation sequence), Core §7.2
(the contrast instantiation whose declared suite bounds all four).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from omi.assimilate import DataObservation, innovation_drift_monitor, run_filter
from omi.observability import (
    DEFAULT_CONVENTION,
    Observation,
    ObservedInferredConvention,
    TriageResult,
    compute_gramian,
    danger_triage,
    default_prior_covariance,
    nominal_trajectory,
)
from omi.proposed.constitutive import ConstitutivelyConstrained
from omi.state import Ensemble, FloatArray, Metric
from omi.sufficiency import variance_term

from omi_domains.contrast.build import build_chain, build_incoming_ensemble
from omi_domains.contrast.operators import CYCLING
from omi_domains.contrast.readouts import DendriteRisk, TerminalVoltage
from omi_domains.contrast.state import CONTRAST_SCHEMA

CAMPAIGN_DEPTH = 24
CURRENT = 2.0
N_CELLS = 200
VOLTAGE_NOISE_SD = 0.1
"""Telemetry noise for the drift-monitor trace. Larger than the dry-run's, matching a
deployment monitor reading a single cell's terminal voltage rather than a laboratory
measurement."""

DRIFT_WINDOW = 6
N_NULL_CAMPAIGNS = 200
"""Independent correctly-specified campaigns, for the drift monitor's null-arm rate.

A per-window false-alarm rate can only be compared against its nominal value with enough
campaigns that the comparison means something; 200 puts the standard error on a ~5% rate
at well under a percentage point."""

TARGETS = (DendriteRisk(),)
"""The declared target set, fixed before any of this is computed (CLAUDE.md invariant 10;
Spec §3.3's re-run rule)."""


OBSERVED_SHARE_THRESHOLD = 0.5
"""ADR-020's default near-diagonal share threshold, restated here so the margin measured
against it is not a hardcoded narrative number (CLAUDE.md §8)."""



def _convention(window: int) -> ObservedInferredConvention:
    """A convention differing from the framework default only in the window.

    The dominance factor and band are ADR-061's defaults: these measurements are about the
    **share** and about the window, so holding the other two at their defaults keeps the
    comparison one-dimensional.
    """
    return ObservedInferredConvention(
        dominance_factor=DEFAULT_CONVENTION.dominance_factor,
        abstention_band=DEFAULT_CONVENTION.abstention_band,
        near_diagonal_window=window,
        justification=(
            "Measurement scaffolding, not a domain declaration: the window is swept because "
            "E-48's finding is that it spans the answer, and the other two are held at "
            "ADR-061's defaults so only one convention varies."
        ),
    )


SUPERSEDED_SHARE_THRESHOLD = 0.5
"""ADR-020's threshold, **superseded by ADR-061** and retained here deliberately.

The measurements in this module are the *evidence for* ADR-061. If they were re-pointed at
ADR-061's criterion they would stop being that evidence — a repository cannot show why it
changed a criterion using only the criterion it changed to. So the superseded rule is
re-expressed locally, below, and applied to the share `danger_triage` still reports.
"""


def superseded_label(direction: object) -> str:
    """ADR-020's observed/inferred rule, applied to a direction's reported share.

    Reproduces exactly what `danger_triage` returned before ADR-061: `observed` iff the
    near-diagonal **sum** exceeded half the **total**, `inferred` otherwise. Only the
    observed/inferred axis is reproduced; `dangerous` and `marginalisable` come from the
    identifiability/influence medians and ADR-061 did not touch them, so the live label is
    used for those.
    """
    label = getattr(direction, "label")
    if label.value not in ("observed", "inferred", "unresolved"):
        return str(label.value)
    share = getattr(direction, "near_diagonal_share")
    if share is not None and share > SUPERSEDED_SHARE_THRESHOLD:
        return "observed"
    return "inferred"

@dataclass(frozen=True)
class TriageTrace:
    """The triage's reading at every interval, with the quantities ADR-056's step 2 was
    moved off the labels because of."""

    intervals: tuple[int, ...]
    influence_medians: tuple[float, ...]
    label_sets: tuple[tuple[str, ...], ...]
    total_danger: tuple[float, ...]
    dangerous_counts: tuple[int, ...]
    shares: tuple[tuple[float, ...], ...]
    """Per-interval near-diagonal shares of every direction that has one — the quantity
    the `OBSERVED`/`INFERRED` split is decided by (Spec §3.3; ADR-020)."""
    split_labels: tuple[tuple[tuple[float, str], ...], ...]
    """Per-interval ``(share, label)`` pairs, so a label can be checked against the share
    that produced it rather than against the interval it appeared at."""

    @property
    def modal_label_set(self) -> tuple[str, ...]:
        """The label set the campaign sits at for most of its length."""
        counts: dict[tuple[str, ...], int] = {}
        for labels in self.label_sets:
            counts[labels] = counts.get(labels, 0) + 1
        return max(counts, key=lambda key: counts[key])

    @property
    def intervals_where_labels_differ(self) -> tuple[int, ...]:
        """Intervals whose label set is not the modal one."""
        return tuple(
            k for k, labels in zip(self.intervals, self.label_sets) if labels != self.modal_label_set
        )

    @property
    def smallest_threshold_margin(self) -> float:
        """The smallest ``|share − threshold|`` anywhere in the campaign.

        This is the quantity that decides whether the `OBSERVED`/`INFERRED` split is
        carrying information or floating-point noise. A margin at machine precision means
        two directions in numerically the same situation receive different labels.
        """
        margins = [
            abs(share - OBSERVED_SHARE_THRESHOLD) for row in self.shares for share in row
        ]
        return min(margins) if margins else float("inf")

    @property
    def label_disagreement_at_equal_shares(self) -> tuple[float, ...]:
        """Share values at which **both** labels occur within one interval, to numerical
        tolerance — the direct demonstration that the split is not carrying information.

        Returns the share values involved, empty if no interval contains two directions
        whose shares agree to `1e-6` but whose labels differ.
        """
        found: list[float] = []
        for row in self.split_labels:
            for i, (share_i, label_i) in enumerate(row):
                for share_j, label_j in row[i + 1 :]:
                    if abs(share_i - share_j) < 1.0e-6 and label_i != label_j:
                        found.extend((share_i, share_j))
        return tuple(found)

    @property
    def influence_median_is_identically_zero(self) -> bool:
        """Whether ADR-020's median split is degenerate at every interval.

        Influence is a quadratic form and therefore non-negative, so a median of exactly
        zero makes `influence >= influence_median` a tautology: every direction is
        "influential", and `MARGINALISABLE`/`OBSERVED_BUT_IRRELEVANT` become unreachable.
        """
        return all(m == 0.0 for m in self.influence_medians)

    @property
    def label_set_ever_changes(self) -> bool:
        """Whether the triage's *categorical* output moves at all over the campaign.

        It does — at isolated intervals. Whether those changes carry information is a
        different question, answered by :attr:`smallest_threshold_margin` and
        :attr:`label_disagreement_at_equal_shares`, and the answer is no.
        """
        return len(set(self.label_sets)) > 1

    @property
    def danger_relative_range(self) -> float:
        """Spread of the total danger score across the interior of the campaign, relative
        to its own mean.

        The terminal interval is excluded: at the last index there is no downstream
        observation to propagate information from, so the posterior collapses to the prior
        and the danger score jumps for a structural reason rather than an informational
        one. Including it would report a decision-relevant swing that no decision could
        act on.
        """
        interior = np.array(self.total_danger[:-1])
        return float((interior.max() - interior.min()) / interior.mean())


def triage_trace(*, seed: int = 0, step: int = 2) -> TriageTrace:
    """Trace the danger-score triage at every *step*-th interval of a declared campaign,
    with per-interval voltage telemetry (Spec §3.3; Core §3.8).

    Triage is taken at the **current** interval looking forward, not at index 0, because
    that is the reading an operational loop has: given what has been observed so far,
    which directions of the state now in front of me are influential and unidentifiable.
    """
    rng = np.random.default_rng(seed)
    ensemble = build_incoming_ensemble(N_CELLS, rng)
    metric = Metric.from_ensemble(ensemble)
    prior = default_prior_covariance(metric)
    chain = build_chain(n_cycles=CAMPAIGN_DEPTH, current=CURRENT)
    nominal = nominal_trajectory(chain, ensemble[0])
    sensors: Sequence[Observation] = [
        Observation(f"voltage_{k}", TerminalVoltage(), np.array([[VOLTAGE_NOISE_SD**2]]), time_index=k)
        for k in range(1, CAMPAIGN_DEPTH + 1)
    ]

    intervals, medians, labels, danger, counts = [], [], [], [], []
    shares, split_labels = [], []
    for k in range(0, CAMPAIGN_DEPTH + 1, step):
        gramian = compute_gramian(chain, nominal, k, sensors)
        result: TriageResult = danger_triage(
            chain, nominal, k, gramian, prior, list(TARGETS), sensors, convention=_convention(1)
        )
        intervals.append(k)
        medians.append(result.influence_median)
        labels.append(tuple(sorted({superseded_label(d) for d in result.directions})))
        danger.append(variance_term(result))
        counts.append(len(result.dangerous_set()))
        with_share = [d for d in result.directions if d.near_diagonal_share is not None]
        shares.append(tuple(float(d.near_diagonal_share) for d in with_share))  # type: ignore[arg-type]
        split_labels.append(
            tuple((float(d.near_diagonal_share), superseded_label(d)) for d in with_share)  # type: ignore[arg-type]
        )

    return TriageTrace(
        intervals=tuple(intervals),
        influence_medians=tuple(medians),
        label_sets=tuple(labels),
        total_danger=tuple(danger),
        dangerous_counts=tuple(counts),
        shares=tuple(shares),
        split_labels=tuple(split_labels),
    )


def validity_report_is_available() -> bool:
    """Whether contrast's declared operator can produce ADR-043's extrapolation report.

    A structural question, answered by asking the operator rather than by measuring
    anything: `ConstitutivelyConstrained` (Spec §2.2's proposed obligation) is a
    Protocol, so an operator either has the method or does not. Contrast declares no
    constitutive form, so one of ADR-056's four diagnostics is unavailable on this domain
    — not because the loop is badly designed but because the domain declares nothing to
    report against.
    """
    return isinstance(CYCLING, ConstitutivelyConstrained)


@dataclass(frozen=True)
class DriftNullRate:
    """The innovation monitor's behaviour on **correctly specified** campaigns (Spec §10;
    ADR-026).

    Both rates are reported because they answer different questions and only one of them
    is nominal: a loop keyed on the per-window flag sees roughly the declared false-alarm
    rate, and a loop keyed on the campaign-level aggregate sees a maximum over many
    windowed tests with no multiplicity correction.
    """

    n_campaigns: int
    confidence: float
    mean_nis: float
    """Should sit near 1.0 under a correct model — the calibration check that has to pass
    before either rate below means anything."""
    per_window_flag_rate: float
    any_drift_rate: float
    """Fraction of null campaigns for which `DriftReport.any_drift` is `True`."""
    lower_tail_windows: int
    upper_tail_windows: int
    """Split by which control limit was crossed — the distinction `DriftReport` does not
    record, and which ADR-056's drift gate needs because the two require **opposite**
    responses."""


def drift_null_rate(*, confidence: float = 0.95) -> DriftNullRate:
    """Measure the drift monitor's null-arm rates over `N_NULL_CAMPAIGNS` correctly
    specified campaigns (Spec §10; ADR-026's declared NIS convention).

    Truth is one cell of the same declared population the filter is initialised from, and
    the model the filter runs *is* the model that generated it — so every flag raised here
    is a false alarm by construction.
    """
    chain = build_chain(n_cycles=CAMPAIGN_DEPTH, current=CURRENT)
    flags, any_drift, nis_means = [], 0, []
    lower = upper = 0
    for seed in range(N_NULL_CAMPAIGNS):
        rng = np.random.default_rng(seed)
        ensemble = build_incoming_ensemble(N_CELLS, rng)
        nominal = nominal_trajectory(chain, ensemble[0])
        observations = [
            DataObservation(
                name=f"voltage_{k}",
                readout=TerminalVoltage(),
                noise_covariance=np.array([[VOLTAGE_NOISE_SD**2]]),
                time_index=k,
                value=TerminalVoltage().evaluate(nominal.ensembles[k][0])
                + rng.normal(0.0, VOLTAGE_NOISE_SD, size=1),
            )
            for k in range(1, CAMPAIGN_DEPTH + 1)
        ]
        result = run_filter(chain, ensemble, observations, rng)
        analyses = [result.analyses[k] for k in sorted(result.analyses)]
        report = innovation_drift_monitor(analyses, window=DRIFT_WINDOW, confidence=confidence)
        flags.append(float(report.drift_detected.mean()))
        any_drift += int(report.any_drift)
        nis_means.append(float(np.mean(report.nis_sequence)))
        lower += int(np.sum(report.windowed_mean < report.lower_limit))
        upper += int(np.sum(report.windowed_mean > report.upper_limit))

    return DriftNullRate(
        n_campaigns=N_NULL_CAMPAIGNS,
        confidence=confidence,
        mean_nis=float(np.mean(nis_means)),
        per_window_flag_rate=float(np.mean(flags)),
        any_drift_rate=any_drift / N_NULL_CAMPAIGNS,
        lower_tail_windows=lower,
        upper_tail_windows=upper,
    )


def terminal_voltage_trajectory(depth: int = 40, *, seed: int = 0) -> FloatArray:
    """Mean terminal voltage over *depth* intervals of the declared chain at the current
    this repository's contrast tests use throughout.

    Measured for the scope-exit finding: the declared operator drives its own observable
    readout negative within a few dozen intervals, and **no** declared item bounds it —
    contrast declares no constitutive form and therefore no validity range, item 4's
    readout catalogue carries no specification limits, item 2's admissible set is declared
    in words rather than numbers, and neither declared invariant is violated. Nothing in
    the seven items distinguishes a cell still in its modelled regime from one whose model
    has left physical validity.
    """
    rng = np.random.default_rng(seed)
    ensemble = build_incoming_ensemble(N_CELLS, rng)
    chain = build_chain(n_cycles=depth, current=CURRENT)
    nominal = nominal_trajectory(chain, ensemble[0])
    return np.array(
        [float(TerminalVoltage().evaluate(nominal.ensembles[k][0])[0]) for k in range(depth + 1)]
    )


def evaluable_observation_modalities() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Contrast's declared observation suite split into what the state schema can
    actually supply and what it cannot (Core §4 item 5; Core §7.2).

    Returns ``(evaluable, declared_but_unevaluable)``. A modality declared with no state
    component behind it is a candidate measurement the loop can name and cannot cost, so
    the candidate pool is smaller than the declaration — reported rather than silently
    enumerated.
    """
    component_names = {name for _, name, _ in CONTRAST_SCHEMA.components}
    # The declared suite, from CONTRAST_DECLARATION.observation_suite, mapped onto the
    # state components a readout would have to read.
    supported = {
        "voltage": "potential",
        "terminal current": None,  # a control, not a state component: known exactly
        "surface temperature": "temperature",
    }
    evaluable, missing = [], []
    for modality, component in supported.items():
        if component is None or component in component_names:
            evaluable.append(modality)
        else:
            missing.append(modality)
    return tuple(evaluable), tuple(missing)
