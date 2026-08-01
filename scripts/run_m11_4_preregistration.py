#!/usr/bin/env python3
"""M11.4's pre-registration pilot: measure the gap estimator's own sampling
variability and set the falsification thresholds, **before the sweep runs**
(ADR-045 requires the ordering; ADR-041 supplies the procedure).

**The integrity constraint this script exists to respect.** ADR-041's
`decision_sensitive_threshold` needs the *standard error of the criterion's own
residual estimator at the declared campaign size*. Here the criterion is a gap
between two contestants' held-out errors — so the naive way to estimate its
variability is to compute the gap on held-out data over several seeds, which
would mean looking at the very numbers the threshold is supposed to be set
before seeing.

So the pilot never touches the held-out region. It measures the gap estimator's
variability entirely **in-envelope**: train on one in-envelope draw, evaluate on a
*different, independent* in-envelope draw, repeat over seeds, and take the spread
of the resulting gap. That is the estimator's sampling variability at this
campaign size — a property of the estimator and the design, not of the effect —
and it is measurable without any held-out evaluation.

The consequence is stated rather than hidden: in-envelope variability may
understate the held-out variability, since extrapolation amplifies parameter
uncertainty. An understated standard error makes the threshold *tighter* and the
test *more* likely to declare an effect, so this choice is not
self-serving — it is the conservative direction for a null result and the
anti-conservative direction for a positive one. Any positive finding must be read
with that in mind, and the sweep report says so.

Run: python scripts/run_m11_4_preregistration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from omi.baseline import GradientBoostedTreeRegressor, RidgeRegressor, root_mean_squared_error  # noqa: E402
from omi.inverse import decision_sensitive_threshold  # noqa: E402
from omi_domains.flagship_constitutive.experiment import (  # noqa: E402
    HELD_OUT_RATE,
    IN_ENVELOPE_RATE,
    fit_correct_form,
    fit_free_form,
    fit_missing_dependence,
    fit_missing_mechanism,
    fit_tabular,
    labels,
    sample_queries,
)

N_TRAIN = 120
N_EVAL = 120
N_PILOT_SEEDS = 8

MINIMUM_EFFECT_FRACTION = 0.10
"""The declared minimum effect worth catching, as a fraction of **the magnitude of
the withheld physics itself** — see `_withheld_term_magnitude`. Declared by the
experimenter, as ADR-041 and E-27 require; the framework supplies no such number.

**A first version scaled this off contestant 1's IN-ENVELOPE RMSE and produced
`tau = 5.02`, larger than most of the errors being compared.** That was not a
formula failure — ADR-041's docstring predicts exactly it ("shrinking
minimum_effect toward standard_error makes tau increasingly sensitive... the two
classes are no longer easily separable by the estimator's own precision") — it was a
scale error: in-envelope every contestant does well, so an in-envelope RMSE is the
wrong yardstick for an extrapolation effect, and the declared delta came out 29x
smaller than the estimator's own noise. Recorded rather than quietly corrected,
because catching it *before* the sweep is what the pre-registration step is for."""

COST_FALSE_ALARM = 3.0
COST_MISS = 1.0
"""Declared asymmetric costs (Spec §7.3). A false alarm — claiming declared physics
buys reach when it does not — is set three times as costly as a miss, because the
false alarm is the direction that would put an unsupported claim into a paper,
and this experiment exists to support a claim. The ratio raises the threshold,
making a positive finding harder, which is the correct asymmetry for the party
that wants the positive finding."""


def _withheld_term_magnitude(rng: np.random.Generator, n: int = 400) -> float:
    """Mean absolute contribution of Generator A's **withheld drag term** over the
    held-out region — the size of the physics no contestant carries.

    **This is a property of the generator, which the experimenter authored, and not
    of any contestant's performance.** It is computed by running the generator twice,
    with and without the withheld term, and differencing. No contestant is fitted, no
    prediction is made, and no error is measured, so consulting it does not
    constitute looking at the result the threshold will judge. It is design
    information, and it is the only quantity available in advance that carries the
    right *scale* for an extrapolation effect.
    """
    from omi_domains.flagship_constitutive import experiment as exp

    queries = sample_queries(n, HELD_OUT_RATE, rng)
    with_drag = np.array([exp.generator_a(q.rho_0, q.strain_rate, q.temperature) for q in queries])

    saved = exp.GEN_K_DRAG
    try:
        exp.GEN_K_DRAG = 0.0
        without = np.array([exp.generator_a(q.rho_0, q.strain_rate, q.temperature) for q in queries])
    finally:
        exp.GEN_K_DRAG = saved

    return float(np.mean(np.abs(with_drag - without)))


def _fit_all(train, y_train):  # type: ignore[no-untyped-def]
    return [
        fit_free_form(train, y_train),
        fit_correct_form(train, y_train),
        fit_missing_mechanism(train, y_train),
        fit_missing_dependence(train, y_train),
        fit_tabular(train, y_train, RidgeRegressor()),
        fit_tabular(train, y_train, GradientBoostedTreeRegressor()),
    ]


def main() -> None:
    print("M11.4 PRE-REGISTRATION PILOT — in-envelope only, no held-out evaluation")
    print(f"campaign size: n_train={N_TRAIN}, n_eval={N_EVAL}, seeds={N_PILOT_SEEDS}")
    print(f"in-envelope strain rate: {IN_ENVELOPE_RATE}, held-out region NOT touched\n")

    per_seed: dict[str, list[float]] = {}
    for seed in range(N_PILOT_SEEDS):
        rng = np.random.default_rng(1000 + seed)
        train = sample_queries(N_TRAIN, IN_ENVELOPE_RATE, rng)
        y_train = labels(train)
        # An independent in-envelope draw: the estimator's variability includes
        # evaluation-set sampling, not only training-set sampling.
        evaluate = sample_queries(N_EVAL, IN_ENVELOPE_RATE, np.random.default_rng(5000 + seed))
        y_eval = labels(evaluate)

        for contestant in _fit_all(train, y_train):
            predicted = np.array([contestant.predict(q, 1.0) for q in evaluate])
            rmse = root_mean_squared_error(predicted, y_eval)
            per_seed.setdefault(contestant.label, []).append(rmse)

    print(f"{'contestant':26s} {'mean RMSE':>11s} {'sd':>10s}")
    print("-" * 50)
    for label, values in per_seed.items():
        print(f"{label:26s} {np.mean(values):11.5f} {np.std(values, ddof=1):10.5f}")

    # The criterion is a GAP between two contestants' errors, so its standard error
    # is the sd of the per-seed gap, and it is PER COMPARISON: a single global worst
    # would be driven by whichever arm happens to be noisiest (here 3a, whose own
    # in-envelope RMSE is ~2.4) and would impose that arm's noise on every other test.
    withheld = _withheld_term_magnitude(np.random.default_rng(99))
    minimum_effect = float(MINIMUM_EFFECT_FRACTION * withheld)

    print(f"\nwithheld drag term, mean |contribution| over the held-out region: {withheld:.6f}")
    print(f"  (generator-only quantity; no contestant fitted, no error measured)")
    print(f"minimum_effect = {MINIMUM_EFFECT_FRACTION:.0%} of that = {minimum_effect:.6f}")

    reference = "1_free_form"
    print(f"\nPER-COMPARISON thresholds vs {reference} (ADR-041):")
    header = f"{'comparison':44s} {'gap sd':>10s} {'tau':>10s}"
    print(header)
    print("-" * len(header))
    thresholds = {}
    for label, values in per_seed.items():
        if label == reference:
            continue
        sd = float(np.std(np.array(per_seed[reference]) - np.array(values), ddof=1))
        tau = decision_sensitive_threshold(
            standard_error=sd,
            minimum_effect=minimum_effect,
            cost_false_alarm=COST_FALSE_ALARM,
            cost_miss=COST_MISS,
        )
        thresholds[label] = (sd, tau)
        print(f"{reference + ' - ' + label:44s} {sd:10.5f} {tau:10.5f}")

    print("\n--- PRE-REGISTERED VALUES (ADR-041; committed before the sweep) ---")
    print(f"minimum_effect      = {minimum_effect:.6f}")
    print(f"cost_false_alarm    = {COST_FALSE_ALARM}")
    print(f"cost_miss           = {COST_MISS}")
    print("thresholds (per comparison):")
    for label, (sd, tau) in thresholds.items():
        print(f"    vs {label:40s} sd={sd:.5f}  tau={tau:.5f}")
    print("\nDecision rule, fixed now: a gap in held-out RMSE counts as a real effect")
    print("only if it exceeds that comparison's tau. The SAME values apply to")
    print("Generator B if it runs.")


if __name__ == "__main__":
    main()
