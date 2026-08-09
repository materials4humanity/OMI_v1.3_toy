"""E-54 settled: the observed/inferred criterion **does** discriminate on a chain whose
downstream sensitivity decays without vanishing, so the entry's strong form is refuted and
its narrow form goes to High.

E-54 stated two readings and marked the second Medium, because two domains chosen to invert
each other on the erasure axis cannot separate them:

- **narrow** — the two *declared* classes of Core §3.9's dichotomy are the degenerate
  extremes, and the distinction is informative in between;
- **strong** — the distinction is structurally uninformative across the board.

This oracle has a dial. The measurement below refutes the strong form.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import ObservationRecorder
from tests.oracles.known_decaying_sensitivity import (
    DECAY_SWEEP,
    GeometricDecay,
    predicted_dominance_ratio,
    read,
    sweep,
    turnover_decay,
)

DOMINANCE_FACTOR = 1.5
"""ADR-061's framework default, used unchanged: the question is whether *that* criterion
discriminates, so re-tuning it for this oracle would answer a different question."""


def test_the_construction_is_not_an_erasure_at_any_decay_rate(
    observe: ObservationRecorder,
) -> None:
    """The precondition that makes this an intermediate case rather than a third instance of
    flagship's.

    Core §3.9's condition (a) requires an image of substantially lower effective dimension.
    `GeometricDecay`'s Jacobian is `diag(λ, μ)`, full-rank for every positive factor — so
    sensitivity *decays* and is never annihilated, at any point of the sweep.
    """
    flags = {d: GeometricDecay(decay=d).is_erasure for d in DECAY_SWEEP}
    observe("decay_operator_is_erasure_by_rate", flags, "all False -- full-rank contraction")
    assert not any(flags.values())


def test_the_measured_ratio_matches_the_closed_form_at_every_decay_rate(
    observe: ObservationRecorder,
) -> None:
    """**The oracle claim**: `λ^{−2(w+1)}`, known before any Gramian is formed.

    Observation `j`'s Gramian contribution along the read direction is `λ^{2(j−k)}` with unit
    noise, so the largest near-diagonal term is the one at `k` and the largest downstream term
    is the one at `k+w+1`. A disagreement here would be a defect in the estimator rather than
    a surprise about the construction, which is what makes the discrimination result below
    trustworthy.
    """
    readings = sweep(dominance_factor=DOMINANCE_FACTOR)
    errors = {r.decay: r.relative_error for r in readings}
    observe("measured_dominance_ratios", {r.decay: r.measured_ratio for r in readings}, "== lambda^-2")
    observe("predicted_dominance_ratios", {r.decay: r.predicted_ratio for r in readings}, "closed form")
    observe("relative_errors_vs_closed_form", errors, "each < 1e-8")

    assert max(errors.values()) < 1.0e-8, (
        "the estimator disagrees with the closed form, so the sweep below is not measuring "
        "what it claims to measure"
    )
    assert predicted_dominance_ratio(0.5, 0) == 4.0


def test_the_criterion_discriminates_across_the_sweep_which_refutes_e54s_strong_form(
    observe: ObservationRecorder,
) -> None:
    """**E-54's strong form refuted.** The label is not constant across the sweep: it moves
    from `inferred` at low decay, through `unresolved` at the turnover, to `observed` at high
    decay — with a **locatable** turnover matching `ρ^{−1/2}` in closed form.

    So the observed/inferred distinction is *informative* on a chain with decaying-but-nonzero
    downstream sensitivity. What E-54 measured on flagship and contrast is a property of the
    two **declared classes** sitting at opposite extremes, not of the distinction itself.

    The abstention band earns its place here rather than only on contrast: it fires in a
    neighbourhood of the turnover, which is exactly where a label would be least defensible.
    """
    readings = sweep(dominance_factor=DOMINANCE_FACTOR)
    labels = {r.decay: r.label for r in readings}
    predicted_turnover = turnover_decay(DOMINANCE_FACTOR, 0)
    observe("label_by_decay_rate", labels, "inferred -> unresolved -> observed")
    observe("predicted_turnover_decay", predicted_turnover, "rho^(-1/2)")
    observe("distinct_labels_across_sweep", sorted(set(labels.values())), "three, not one")

    assert len(set(labels.values())) >= 3, (
        f"the criterion returns {sorted(set(labels.values()))} across the whole sweep, so it "
        "does not discriminate on an intermediate chain and E-54's STRONG form stands"
    )
    assert labels[max(DECAY_SWEEP)] == "inferred", "the low-decay end no longer reads inferred"
    assert labels[min(DECAY_SWEEP)] == "observed", "the high-decay end no longer reads observed"

    # The turnover is where it is predicted to be: every rate above it reads inferred or
    # abstains, every rate below reads observed or abstains.
    for decay, label in labels.items():
        if label == "unresolved":
            continue
        expected = "inferred" if decay > predicted_turnover else "observed"
        assert label == expected, (
            f"at decay={decay} the criterion reads {label}, but the closed-form turnover at "
            f"{predicted_turnover:.4f} predicts {expected}"
        )


def test_the_abstention_fires_in_a_neighbourhood_of_the_turnover(
    observe: ObservationRecorder,
) -> None:
    """Where the band earns its keep on a chain that is not degenerate.

    On contrast the abstention fires because two contributions are exactly equal. Here it
    fires because the ratio is genuinely close to the declared factor — the case the band was
    designed for, and one neither implemented domain provides.
    """
    readings = sweep(dominance_factor=DOMINANCE_FACTOR)
    abstained = [r for r in readings if r.label == "unresolved"]
    observe("abstained_decay_rates", [r.decay for r in abstained], "non-empty, near the turnover")
    observe("abstained_ratios", [r.measured_ratio for r in abstained], "within the band of 1.5")

    assert abstained, "the band never fires across the sweep, so it is untested on a non-degenerate chain"
    for r in abstained:
        assert abs(r.measured_ratio - DOMINANCE_FACTOR) <= 0.25 + 1.0e-9, (
            f"a direction abstained at ratio {r.measured_ratio}, which is outside the declared band"
        )


def test_the_superseded_share_also_varies_which_narrows_the_criticism_of_it(
    observe: ObservationRecorder,
) -> None:
    """An honest limit on how much of E-48 is a criticism of the *share* as such.

    The near-diagonal share also moves continuously across the sweep, from `0.147` to `0.99`.
    So the share is not broken in general: it is broken **at the extremes**, where it becomes a
    rational ladder or a boolean, and both implemented domains sit there. Recorded because the
    opposite claim — that the share is useless everywhere — would be an over-reading of E-48,
    and ADR-061's case rests on the margin and on Spec's own wording rather than on the share
    being uninformative.
    """
    readings = sweep(dominance_factor=DOMINANCE_FACTOR)
    shares = {r.decay: r.share for r in readings}
    spread = max(shares.values()) - min(shares.values())
    observe("share_by_decay_rate", shares, "varies continuously, 0.15 -> 0.99")
    observe("share_spread_across_sweep", spread, "> 0.5 -- the share discriminates here too")

    assert spread > 0.5, (
        "the share no longer varies across the sweep, which would make E-48 a criticism of the "
        "share in general rather than at the extremes"
    )
    assert all(0.0 < s < 1.0 for s in shares.values()), (
        "a share hit an endpoint, so this chain is not the strictly-interior case the oracle "
        "exists to supply"
    )


def test_a_wider_window_shifts_the_turnover_exactly_as_predicted(
    observe: ObservationRecorder,
) -> None:
    """The window's effect, on a chain where it is not degenerate — and it is a *shift*, not a
    span.

    At window `w` the turnover moves to `ρ^{−1/(2(w+1))}`, closer to 1, because a wider window
    admits more near-diagonal terms and the largest downstream term is further away. So on an
    intermediate chain the window changes *where* the criterion turns over rather than
    replacing the answer wholesale, which is a weaker dependence than E-48 measured on
    contrast — and it is why ADR-061 requires the window to be declared rather than treating it
    as fatal.
    """
    by_window = {
        w: (turnover_decay(DOMINANCE_FACTOR, w), read(0.9, window=w, dominance_factor=DOMINANCE_FACTOR))
        for w in (0, 1, 2)
    }
    observe(
        "turnover_by_window",
        {w: predicted for w, (predicted, _) in by_window.items()},
        "increases toward 1 with the window",
    )
    observe(
        "ratio_at_decay_0.9_by_window",
        {w: r.measured_ratio for w, (_, r) in by_window.items()},
        "== 0.9^-2(w+1)",
    )

    turnovers = [predicted for predicted, _ in by_window.values()]
    assert turnovers == sorted(turnovers), "the turnover no longer moves monotonically with the window"
    for w, (_, r) in by_window.items():
        assert abs(r.measured_ratio - predicted_dominance_ratio(0.9, w)) / r.predicted_ratio < 1.0e-8
