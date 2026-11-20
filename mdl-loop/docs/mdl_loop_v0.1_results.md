# mdl-loop 0.1 — C1 Optimizer Validation and Run Budget (A7)
### Results memo. Companion to the next-stage plan (A4, new item A7, campaign C1), the v2 map (§7a, §8) and the literature plan (Tier 4: "validate optimizer choices against noisy emulated surfaces before spending real selenization runs").
**Status 19 Nov 2026: §2 was ratified as the hybrid rule and then amended by the 0.2 memo (`claude/mdl_loop_v0.2_results.md`), which adds anchor devices to the loop (A8). Read that memo for the current C1 pre-registration.**
**Prepared 18 Nov 2026. Code: `mdl-loop-0.1.zip` (12 passing tests). Every number below is in `out/summary.json` and is reproducible with `python -m mdl_loop --out out --seeds 24` (about 20 minutes on two cores).**

---

## 0. What now exists

- **Run schema (A4).** Cooling rate, chalcogen activity, ramp, intermediate hold, alkali species, dose and layer position are required fields. Each record gets a weighted completeness score: hidden parameters ×3, reproducibility metadata ×2, context ×1. A process record filled at the reporting rates of the Uppsala survey scores **0.39**. A simulated MDL run scores **0.95**; the remaining gap is SnSe pressure, which the first rig will not measure.
- **P₀ trajectory space.** Seven run-level parameters that every sample in a furnace run shares (ramp, intermediate hold temperature and time, anneal temperature and time, Se charge, cooling rate) and four sample-level parameters (Na, Li, Li layer position, Cu ratio). The anneal is capped at 560 °C. The starting point is the Nature Energy 2026 Mo-foil recipe: Li in the first layer only, Na 80 mM, Li 120 mM, 535 °C reached in about one minute, 20-minute hold.
- **Virtual kesterite v0.** A synthetic test surface, **not a model of kesterite**. It has mechanism-shaped loss terms, film failures, and device-only losses that QFLS cannot see. The literature recipe sits **39 meV** of QFLS below the surface optimum. An `interaction` switch produces a separable variant of the same surface.
- **Virtual furnace.** Each furnace run carries a random effect shared by all its samples (at half the film-to-film spread), plus film-to-film scatter that is larger for poor films, 3 meV of measurement scatter, and failures. Confirmation runs sit outside the search budget.
- **Two arms and three ablations.**
  - The loop: a GP with a learned noise term; a GP classifier for film survival; expected improvement × P(survive); Kriging-believer filling of the four slots; a replicated first run; the incumbent re-run every fifth run; and a lower-confidence-bound recommendation.
  - A *careful* OVAT control: it pools replicates of the incumbent, accepts a change only above one standard error, and re-measures the incumbent every fifth run, so it carries the same replicate overhead as the loop.
  - Ablations: a greedy OVAT, a noise-unaware BO, and a trust-region BO.
- **The power analysis.** It runs both arms over 24 seeds at film-to-film noise floors of 5, 10, 20 and 30 meV, with checkpoints from 10 to 40 runs.

---

## 1. Findings that change something

### 1.1 The loop beats a careful OVAT control at every noise floor, by less than a head-to-head test can reliably confirm

Median true QFLS gain over the literature recipe:

| M0 film σ | Loop @20 | OVAT @20 | Loop @40 | OVAT @40 | P(true gap > 5 meV) @40 | Power @40, 2 / 8 confirmation runs |
|---|---|---|---|---|---|---|
| 5 meV | 27.5 | 15.8 | 31.4 | 18.1 | 0.71 | 0.67 / 0.78 |
| 10 meV | 14.4 | 8.1 | 24.5 | 13.0 | 0.71 | 0.57 / 0.70 |
| 20 meV | 7.5 | 1.0 | 16.5 | 1.0 | 0.67 | 0.25 / 0.45 |
| 30 meV | 5.0 | 0.0 | 6.6 | 0.0 | 0.50 | 0.13 / 0.26 |

Power is for a one-sided Welch test at α = 0.05 on confirmation runs of each arm's recommended recipe, re-simulated 50 times per seed. The chance of the test pointing the wrong way is about 1% at 5 meV and 8–12% at 10 meV.

**Consequence.** C1's kill condition as written ("no separation from the control after a pre-registered number of runs") reaches 80% power at **no** budget up to 40 runs and **no** confirmation size up to 8 runs, even at a 5 meV noise floor. The limit is not confirmation noise. It is that campaigns differ from one another: at 10 meV, OVAT really does finish ahead in about a fifth of campaigns. A head-to-head kill rule would stop the loop in 22–43% of campaigns at σ ≤ 10 meV, even though the loop's median lead there is 12–18 meV, and in most campaigns above that.

**What works instead: an absolute primary criterion.** The test asks whether the loop's confirmed recipe beats the literature recipe, replicated in M0, by more than 5 meV. Its power at 40 runs with 4 confirmation runs is **1.00 at 5 meV, 0.81 at 10 meV, 0.34 at 20 meV**. The same test applied to the OVAT arm gives 0.83, 0.39 and 0.13, so it still separates the two methods. The loop-versus-OVAT difference stays as a reported estimate with an interval. §2 drafts this as the pre-registration.

### 1.2 M0 decides whether C1 is worth running: the target is film-to-film σ ≤ 10 meV

At 20 meV the loop's 40-run gain falls by about a third and OVAT's disappears. At 30 meV neither arm learns much in 40 runs. If M0 measures more than about 15 meV across furnace runs, the cheapest next step is process reproducibility (box history, Se charge geometry, ink age), not optimization. The measurement has to put replicates in *different* furnace runs. Replicates inside one run miss the run effect, which in this model is half the film-to-film spread.

### 1.3 The proxy can be optimized past the device

The loop pushed the Se charge to its upper bound in most campaigns (median 640 mg at σ ≤ 10 meV), because Se protects against Sn loss in the QFLS terms. On this surface excess Se also thickens MoSe₂, a loss that QFLS does not see. The QFLS lead does not carry through to anchor devices:

| M0 film σ | QFLS gap, loop − OVAT @40 | Device-Voc gap, loop − OVAT @40 | P(device gap > 0) |
|---|---|---|---|
| 5 meV | 12.1 | 6.4 | 0.67 |
| 10 meV | 17.5 | 1.4 | 0.58 |
| 20 meV | 10.0 | −0.3 | 0.50 |

The emulator builds this blind spot in by construction, so the size of the effect is not evidence. What the simulation does show is the mechanism the v2 map warns about ("an SDL amplifies its figure of merit, good or bad"). A blind spot in the proxy becomes a systematic bias once an optimizer pushes along it. An anchor device that only audits the loop catches the bias after the runs are spent. **Anchor results have to feed the loop**, as a constraint or a second fidelity. That is the proposed item A8.

### 1.4 Most of the loop's advantage is noise handling, not interactions

How much each arm over-claims its recommended recipe at 40 runs (claimed minus true, median):

| Arm | σ = 10 meV | σ = 20 meV |
|---|---|---|
| Noise-unaware BO (best single film) | 35 | 77 |
| Greedy OVAT (best four-film mean) | 23 | 54 |
| Careful OVAT | 8 | 21 |
| Loop (lower confidence bound) | 1.6 | 1.8 |

The greedy OVAT ratchets its incumbent upward on noise and then rejects real gains. The noise-unaware BO finishes no better than OVAT (14.6 vs 13.0 meV at σ = 10).

On the **separable** surface, where the interaction terms are switched off, the loop still led at 40 runs: 29.0 vs 14.2 meV, gap 16 meV, confirmation power 0.60–0.73. So on this surface the loop's edge comes from using four informative films per furnace run and from not believing single maxima. It does not come from exploiting interactions. Act IV/V of the pitch argues that trajectory-space interactions are what a loop exploits and a human cannot. This simulation neither supports nor refutes that; it supports the narrower claim of **noise-aware parallel search**. The interaction argument needs evidence from C1 itself.

### 1.5 Optimizer choices that failed here (the reason to test before spending runs)

- **Imputing failed films as low values** pushed GP length scales to their bounds, and the model assigned 45–83% of the variance to noise. A separate survival classifier fixed this.
- **A TuRBO-style trust region**, with its start design centred on the literature recipe, shrank too early: 20.2 vs 24.5 meV at 40 runs (σ = 10). It is kept as an option, off by default.

Each of these would have cost real selenization runs to discover.

### 1.6 The hidden-parameter lever was found by the loop and mostly missed by OVAT

At σ = 10 meV, the loop's recommended cooling rate fell below 15 °C/min in 88% of campaigns (median 2.0 °C/min). OVAT did so in 17% (median unchanged at the assumed 20 °C/min). The 13 meV that cooling is worth on this surface is an emulator choice. The pattern is still the A4 argument in miniature: a loop can only use a lever that is logged, and a cautious one-variable search reaches late variables with too little budget to accept small real gains.

---

## 2. Draft C1 pre-registration (for ratification)

| Item | Proposal |
|---|---|
| Precondition | M0 measures film-to-film σ ≤ 10 meV and run-to-run σ ≤ 5 meV, with replicates spread over at least 4 furnace runs |
| Arms | Loop vs careful OVAT, 40 furnace runs × 4 slots each, same start (literature Mo-foil recipe), same replicate overhead |
| Primary criterion | Loop's recommended recipe, confirmed over 4 furnace runs, beats the M0-replicated literature recipe by more than 5 meV QFLS (one-sided Welch, α = 0.05). Simulated power 0.81 at σ = 10 meV |
| Secondary | Loop − OVAT confirmed difference with a 90% interval; reported, not a kill trigger on its own |
| Kill condition | Primary fails at 40 runs **and** the secondary interval includes zero |
| Device guard | Anchor device on the incumbent every 10 runs; if the device Voc gain is less than half the QFLS gain, the loop takes the device result as a constraint (A8) |
| Budget | 2 × 40 search runs + 2 × 4 confirmation runs + 4 literature-replicate runs ≈ 92 furnace runs; about 9 weeks at an assumed two runs per working day |

Before ratification, the budget and power should be re-derived with M0's measured noise in place of the assumed values. That is a one-line change (`NoiseModel`) and a 20-minute rerun.

---

## 3. Known limits of this run

- **The emulator is a benchmark surface with chosen coefficients.** Results are conditional on its structure. The separable variant addresses one dependence (interactions); others are unexamined, including the size of the headroom, the shape of the noise, and where the optimum sits relative to the bounds. A second emulator with independently chosen terms would test robustness.
- **The noise is Gaussian** with a run effect and heteroscedastic film scatter. There is no drift over time (box ageing), no outliers, and no bad-calibration days.
- **The objective is QFLS alone.** Urbach energy is logged but not used, and there is no multi-objective or device-aware acquisition yet (A8).
- **24 seeds per cell**, so the power estimates carry roughly ±0.1.
- **The confirmation test ignores the furnace-run structure** (it pools films); a mixed-model test would be slightly more powerful.
- **This package is standalone.** It is not connected to the four Replit prototypes. `Lab.furnace_run` is the single interface a real rig or the hardware abstraction layer would replace.

## 4. Next actions, in order

1. Ratify or amend the §2 pre-registration. Changing the C1 kill condition from head-to-head to absolute-primary is the decision that matters.
2. Build A8: anchor-device feedback in the loop (a device-aware constraint or two-fidelity acquisition), then rerun §1.3.
3. Write M0's design as a document: replicates over at least 4 runs, the noise decomposition it must report, and the σ threshold from §1.2.
4. Simulate the two-campaign alternative (2 × 20 runs per arm from different starts) as another way to tame between-campaign variance.
5. Decide where this code lives: standalone, or folded into the Replit physics-ML prototype during the Phase I rebuild.
