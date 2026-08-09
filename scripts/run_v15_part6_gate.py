#!/usr/bin/env python
"""Part 6's gate measurements, at full replicate counts.

Runs what this gate authorises and nothing more: the declared erasure on the discovery
domain, E-41's evaluable criteria for the framework statistic and for the GP comparator on the
`INSUFFICIENT`-versus-`NULL` axis, the closed-form divergence check, and the null-arm
calibration of the monitor.

**The `NOISY` arm is not touched.** It is the registered comparison and reading it here would
be a peek at the pre-registered quantity — M11.5's pre-registration §5 is the precedent for
why that matters and for disclosing it when it happens.

Usage: `python scripts/run_v15_part6_gate.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tests.oracles.discovery_campaign as campaign  # noqa: E402
from omi.erasure import measure_erasure  # noqa: E402
from omi.operators import Control, lipschitz_report  # noqa: E402
from omi.state import Ensemble, Metric, Slot, State  # noqa: E402
from omi_domains.sdl.build import (  # noqa: E402
    CALCINATION_HOLD,
    CALCINATION_TEMPERATURE,
    build_chain,
    build_incoming_ensemble,
    sample_attainable_compositions,
)
from omi_domains.sdl.operators import PRECURSOR_FEEDTHROUGH, Calcination  # noqa: E402
from omi_domains.sdl.state import SDL_SCHEMA  # noqa: E402

N_FORMULATIONS = 120
NULL_REPLICATES = 40
ERASURE_RTOL = 1.0e-2


def report_erasure() -> None:
    print("=== the declared erasure, measured (ADR-064; E-56) ===")
    rng = np.random.default_rng(4)
    compositions = sample_attainable_compositions(N_FORMULATIONS, rng)
    support = build_incoming_ensemble(N_FORMULATIONS, rng)
    rows = [
        build_chain(composition, 0)
        .rollout(Ensemble(SDL_SCHEMA, support.particles[i][None, :]))
        .ensembles[1]
        .particles[0]
        for i, composition in enumerate(compositions)
    ]
    population = Ensemble(SDL_SCHEMA, np.stack(rows))
    metric = Metric.from_ensemble(population)
    state = State(SDL_SCHEMA, population.particles.mean(axis=0))
    control = Control(0.0, CALCINATION_HOLD, lambda t: np.array([CALCINATION_TEMPERATURE]))
    operator = Calcination(composition=compositions[0])

    default = measure_erasure(operator, state, control, metric)
    declared = measure_erasure(operator, state, control, metric, rtol=ERASURE_RTOL)
    gain = lipschitz_report(operator, state, control, metric)

    print(f"  feed-through coefficient       {PRECURSOR_FEEDTHROUGH}")
    print(f"  spectrum                       {np.round(declared.spectrum, 6)}")
    print(f"  rank at ADR-017 default        {default.rank} of {SDL_SCHEMA.size}  (tol {default.tol:.3g})")
    print(f"  rank at declared rtol={ERASURE_RTOL} {declared.rank} of {SDL_SCHEMA.size}  (tol {declared.tol:.4g})")
    print(f"  L (largest singular value)     {gain.spectrum[0]:.4f}   <- E-56: >> 1")
    surviving = declared.surviving_basis[:, 0]
    index = SDL_SCHEMA.slice_for(Slot.M, "dispersed_phase_loading").start
    print(f"  surviving direction is loading  |cos| = {abs(surviving[index]):.6f}")


def report_vacuity_gate() -> None:
    print()
    print("=== E-41's evaluable criteria, on the discovery domain (ADR-065) ===")
    print(f"  campaign lengths {campaign.NEAR_SAMPLES} -> {campaign.FAR_SAMPLES} samples, "
          f"{campaign.N_REPLICATES} replicates per arm")
    readings = campaign.vacuity_gate()
    for reading in readings:
        print(f"  {reading.summary()}")
        print(f"      criteria 1-2, criterion 3 deferred: {reading.verdict(2.0)}")
    print(f"  all three criteria, INSUFFICIENT vs NULL only: "
          f"{campaign.gate_verdict(readings, 2.0)}")
    print("  criterion 3 on the REGISTERED contrast (INSUFFICIENT vs NOISY): deferred to the sweep")
    print(f"  closed-form growth floor (ADR-066): sqrt(n_far/n_near) = "
          f"{campaign.predicted_growth_ratio():.4f}")


def report_closed_form() -> None:
    print()
    print("=== the divergence against the closed form predicted first (ADR-066) ===")
    campaigns = [
        campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.INSUFFICIENT, s)
        for s in range(campaign.N_REPLICATES)
    ]
    near = [campaign.innovation_mean_report(c.prefix(campaign.NEAR_SAMPLES)) for c in campaigns]
    far = [campaign.innovation_mean_report(c) for c in campaigns]
    bias_near = abs(float(np.mean([r.signed_mean for r in near])))
    bias_far = abs(float(np.mean([r.signed_mean for r in far])))
    z_near = float(np.mean([r.z for r in near]))
    z_far = float(np.mean([r.z for r in far]))
    floor = campaign.predicted_growth_ratio()

    print(f"  signed mean innovation   {-bias_near:.5f} -> {-bias_far:.5f}  (x{bias_far / bias_near:.3f})")
    print(f"  direction                {far[0].direction}")
    print(f"  z                        {z_near:.3f} -> {z_far:.3f}  (x{z_far / z_near:.3f})")
    print(f"  predicted floor          x{floor:.3f}   (pure sqrt(n), constant bias)")
    print(f"  predicted with selection x{bias_far / bias_near * floor:.3f}")


def report_null_calibration() -> None:
    print()
    print("=== null-arm calibration of the second monitor (ADR-063; E-49) ===")
    innovations = []
    variances = []
    z_values = []
    for seed in range(NULL_REPLICATES):
        realised = campaign.run_campaign(campaign.FAR_SAMPLES, campaign.Arm.NULL, 1000 + seed)
        z_values.append(campaign.innovation_mean_report(realised).z)
        innovations.append(np.concatenate([s.innovations for s in realised.samples]))
        variances.append(np.concatenate([s.predicted_variance for s in realised.samples]))
    pooled = np.concatenate(innovations)
    predicted_sd = float(np.sqrt(np.concatenate(variances).mean()))

    print(f"  realised / predicted innovation sd  {pooled.std() / predicted_sd:.4f}   (1.0 = standardised)")
    print(f"  null z: mean {np.mean(z_values):.3f}  sd {np.std(z_values):.3f}  "
          f"95th pct {np.quantile(z_values, 0.95):.3f}")
    print("  reference: E|Z| = 0.798, sd|Z| = 0.603, |Z| 95th pct = 1.960")


def main() -> None:
    report_erasure()
    report_vacuity_gate()
    report_closed_form()
    report_null_calibration()


if __name__ == "__main__":
    main()
