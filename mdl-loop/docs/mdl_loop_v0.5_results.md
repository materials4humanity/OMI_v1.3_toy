# mdl-loop 0.5 — Two 20-Run Campaign Pairs versus One 40-Run Pair
### Results memo. Follows the 0.1 memo (§1.1: a single head-to-head cannot reach 80% power; §4 item 4), the 0.2 memo (§0 "Funders" line; §5 next action 4) and the 0.4 memo (final anchor, now in the C1 pre-registration). Same synthetic test surface as 0.1–0.4: every number below is a property of that surface, not of kesterite.
**Prepared 21 Nov 2026. Code: mdl-loop 0.5.0 (20 passing tests). Numbers are in `out/two_campaign_summary.json`, reproducible with `python -m mdl_loop.two_campaign --out out --seeds 24 --workers 4` (about 15 min on 4 cores; BLAS pinned to one thread, numpy 2.1.3, scipy 1.14.1, scikit-learn 1.9.1). 24 seeds per cell.**

---

## 0. Answer

**No.** At the same total furnace runs, two independent 20-run campaign pairs, combined, do not give a stronger loop-versus-OVAT comparison than one 40-run pair on this surface:

- **Power** is lower in 6 of the 8 M0 lookup cells and higher in 2, by less than one standard error in both.
- **No design reaches 80% power in any cell.** The highest is 0.67, for one 40-run pair.
- **The wrong-way rate** is lower in 1 cell and higher in 7.
- **The device-level lead** of the loop's hand-over recipe is smaller with two 20-run pairs in 7 of 8 cells.

The reason, measured in §3: averaging two campaigns does reduce the campaign-to-campaign spread of the true gap, but on this surface the loop's lead over OVAT is smaller after 20 runs than after 40. That costs more than the averaging gains.

## 1. Design

**Arms.** The 0.4 device-aware loop (A8 anchors plus the final anchor) and the careful OVAT control, both run by `m0.run_lookup`. The noise levels are the M0 lookup cells: film-to-film sd as M0 measures it at the literature recipe (5, 8, 11, 15 meV), run-to-run at half that, under both noise-shape assumptions.

**Campaigns per cell and seed.** Four campaigns:
- **Pair A:** loop and OVAT, 40 runs, from the literature recipe. Its 20-run checkpoint, final anchor included, is pair A at 20 runs.
- **Pair B:** loop and OVAT, 20 runs, from an alternative start with its own random streams.

The alternative start (`m0.start_recipe`) perturbs the literature recipe's continuous parameters by 0.1 sd in unit coordinates and keeps its categorical settings. It is drawn per seed, shared by both arms of the pair, and chosen without reference to the emulator's truth. Its true QFLS sits −5.0 / +1.0 / +12.8 meV (10th / 50th / 90th percentile) from the literature recipe.

**Designs at equal runs per arm.** Both designs use 40 search runs and 4 confirmation runs per arm:

| Design | Search runs per arm | Confirmation | Test |
|---|---|---|---|
| One 40-run pair | 40 | 4 runs of the hand-over recipe | One-sided Welch, loop > OVAT, α = 0.05 |
| Two 20-run pairs | 2 × 20 | 2 runs of each pair's hand-over recipe | Stratified: mean of the two within-pair differences, Welch–Satterthwaite SE, one-sided, α = 0.05 |

**Outputs.**
- **Power** is the share of campaigns × confirmation re-draws in which the test favours the loop.
- **Wrong-way rate** is the share in which the reversed one-sided test favours OVAT.
- **The device-level difference** is the true device-Voc gap, loop minus OVAT, of the recipes handed over (the mean of the two pairs for the two-pair design).

Confirmation uses common random numbers: each (campaign, arm) has its own generator and simulates 4 single confirmation runs per re-draw (50 re-draws), and a design that uses k runs takes the first k. The two designs share pair A, so their difference is paired by seed. The tables give it with its standard error over the 24 seeds.

## 2. Results

### 2.1 Head-to-head power and wrong-way rate

| M0 film sd at literature recipe | Power, one 40-run pair | Power, two 20-run pairs | Δ ± SE | Wrong-way, one 40-run pair | Wrong-way, two 20-run pairs | Δ ± SE |
|---|---|---|---|---|---|---|
| 5 meV, poorer films noisier | 0.51 | 0.58 | +0.065 ± 0.111 | 0.07 | 0.08 | +0.013 ± 0.045 |
| 8 meV, poorer films noisier | 0.36 | 0.45 | +0.090 ± 0.091 | 0.21 | 0.07 | −0.144 ± 0.074 |
| 11 meV, poorer films noisier | 0.67 | 0.57 | −0.107 ± 0.081 | 0.02 | 0.06 | +0.033 ± 0.022 |
| 15 meV, poorer films noisier | 0.44 | 0.41 | −0.032 ± 0.071 | 0.11 | 0.20 | +0.095 ± 0.066 |
| 5 meV, constant noise | 0.52 | 0.47 | −0.057 ± 0.092 | 0.22 | 0.24 | +0.021 ± 0.086 |
| 8 meV, constant noise | 0.53 | 0.36 | −0.176 ± 0.100 | 0.12 | 0.16 | +0.038 ± 0.070 |
| 11 meV, constant noise | 0.39 | 0.32 | −0.079 ± 0.082 | 0.07 | 0.13 | +0.060 ± 0.041 |
| 15 meV, constant noise | 0.50 | 0.31 | −0.188 ± 0.058 | 0.06 | 0.07 | +0.008 ± 0.027 |

**One 40-run pair: power 0.36–0.67, wrong-way 0.02–0.22. Two 20-run pairs: power 0.31–0.58, wrong-way 0.06–0.24.**

- **Single-cell differences:** most are within 2 SE. Only the 15 meV constant-noise cell (−0.188 ± 0.058) is clearly lower. The finding is the pattern across cells: lower in 6 of 8, never above 0.58.
- **Wrong-way rate:** this is how often a design would tell a funder that OVAT is better. It is a correct statement about the two recipes when OVAT's recipe really is ahead in QFLS, which happens in 4–42% of campaigns (§2.2). It is still the wrong conclusion about the methods, given the loop's median lead. The two-pair design lowers it only in the 8 meV, poorer-films-noisier cell (0.21 → 0.07).
- **The 0.1 memo §1.1 finding holds with the 0.4 loop:** a single 40-run head-to-head against OVAT stays well below 80% power at every M0 noise level.

### 2.2 Device-level and QFLS difference of the hand-over recipes

| M0 film sd | Device gap median, one 40-run pair (mV) | P(device gap > 0) | Device gap median, two 20-run pairs (mV) | P(device gap > 0) | QFLS gap median, 40 / two 20 (meV) | P(QFLS gap < 0), 40 / two 20 |
|---|---|---|---|---|---|---|
| 5 meV, poorer films noisier | 11.0 | 0.83 | 4.1 | 0.75 | 3.0 / 4.4 | 0.29 / 0.25 |
| 8 meV, poorer films noisier | 5.5 | 0.71 | 2.6 | 0.71 | 2.7 / 5.4 | 0.42 / 0.17 |
| 11 meV, poorer films noisier | 10.7 | 0.88 | 8.3 | 0.79 | 9.8 / 8.4 | 0.04 / 0.17 |
| 15 meV, poorer films noisier | 7.3 | 0.75 | 3.9 | 0.62 | 6.2 / 8.2 | 0.29 / 0.29 |
| 5 meV, constant noise | 10.6 | 0.79 | 3.2 | 0.79 | 4.3 / 3.1 | 0.29 / 0.38 |
| 8 meV, constant noise | 3.6 | 0.62 | 5.0 | 0.67 | 7.8 / 3.2 | 0.29 / 0.33 |
| 11 meV, constant noise | 6.9 | 0.83 | 1.7 | 0.58 | 5.6 / 2.5 | 0.25 / 0.42 |
| 15 meV, constant noise | 11.2 | 0.83 | 5.4 | 0.71 | 11.2 / 4.4 | 0.21 / 0.21 |

These are true (emulator) gaps, not confirmed ones. One 40-run pair puts the loop's recipe ahead at the device level in 62–88% of campaigns, by a median 3.6–11.2 mV. Two 20-run pairs put it ahead in 58–79%, by a median 1.7–8.3 mV. So most of the loop's device-level lead in a 40-run pair is built after run 20. I have not tested why. One candidate is that the gap model has 6 anchors at run 20 against 14 at run 40 (0.2 memo §2.1 describes how anchors steer the loop away from excess Se).

### 2.3 Reference and sensitivity rows

| M0 film sd | One 20-run pair (half the search runs), power / wrong-way | Two 20-run pairs, pooled Welch | Two 20-run pairs, 4 conf. runs per recipe (+4 runs per arm) |
|---|---|---|---|
| 5 meV, poorer films noisier | 0.52 / 0.12 | 0.54 / 0.03 | 0.66 / 0.10 |
| 8 meV, poorer films noisier | 0.41 / 0.15 | 0.39 / 0.05 | 0.56 / 0.08 |
| 11 meV, poorer films noisier | 0.61 / 0.07 | 0.53 / 0.04 | 0.66 / 0.07 |
| 15 meV, poorer films noisier | 0.36 / 0.29 | 0.40 / 0.18 | 0.49 / 0.24 |
| 5 meV, constant noise | 0.36 / 0.36 | 0.41 / 0.19 | 0.53 / 0.29 |
| 8 meV, constant noise | 0.42 / 0.22 | 0.32 / 0.15 | 0.44 / 0.19 |
| 11 meV, constant noise | 0.26 / 0.19 | 0.29 / 0.11 | 0.39 / 0.15 |
| 15 meV, constant noise | 0.47 / 0.09 | 0.28 / 0.06 | 0.40 / 0.08 |

- **Pooled Welch:** treating the four recipes' films as one sample per arm gives lower power than the stratified test in every cell. It also gives a lower wrong-way rate in every cell, because the between-recipe spread inflates its variance.
- **More confirmation:** giving each 20-run recipe 4 confirmation runs (4 more runs per arm than the 40-run design) lifts two-pair power above the single 40-run pair in 4 of 8 cells, one of them by +0.003. The maximum is 0.66. Even with extra runs, no design reaches 80%.

## 3. Why splitting does not help here

Per cell: the mean and sd over seeds of the true QFLS gap (loop − OVAT) of the hand-over recipes, and their ratio, which is roughly what the head-to-head test can resolve.

| M0 film sd | One 40-run pair: mean / sd (ratio), meV | Pair A at 20 runs | Pair B, 20 runs | Two 20-run pairs (mean of A and B) | corr(A at 20, B) |
|---|---|---|---|---|---|
| 5 meV, poorer films noisier | 4.3 / 5.2 (0.82) | 3.5 / 5.0 (0.70) | 4.9 / 7.7 (0.63) | 4.2 / 4.4 (0.95) | −0.08 |
| 8 meV, poorer films noisier | 2.0 / 7.6 (0.26) | 3.0 / 6.9 (0.44) | 5.9 / 9.5 (0.62) | 4.5 / 4.7 (0.94) | −0.37 |
| 11 meV, poorer films noisier | 10.2 / 6.6 (1.55) | 8.7 / 9.2 (0.94) | 7.1 / 11.9 (0.60) | 7.9 / 7.2 (1.11) | −0.10 |
| 15 meV, poorer films noisier | 9.0 / 15.8 (0.57) | 1.5 / 19.1 (0.08) | 7.5 / 14.8 (0.51) | 4.5 / 14.2 (0.32) | 0.39 |
| 5 meV, constant noise | 3.8 / 8.0 (0.47) | 0.8 / 11.2 (0.07) | 4.5 / 10.0 (0.45) | 2.7 / 7.0 (0.38) | −0.13 |
| 8 meV, constant noise | 6.1 / 9.1 (0.66) | 3.0 / 10.8 (0.27) | 4.2 / 10.9 (0.39) | 3.6 / 8.0 (0.45) | 0.09 |
| 11 meV, constant noise | 6.4 / 9.6 (0.68) | 1.3 / 8.8 (0.14) | 4.9 / 9.9 (0.49) | 3.1 / 7.0 (0.44) | 0.10 |
| 15 meV, constant noise | 9.4 / 9.9 (0.95) | 8.9 / 11.4 (0.78) | 1.0 / 11.6 (0.09) | 4.9 / 6.9 (0.71) | −0.27 |

- **The averaging works as intended.** The two pairs are close to independent (correlation −0.37 to +0.39), and averaging them shrinks the sd to roughly 1/√2 of a single 20-run pair.
- **The averaging does not raise the ratio.** The mean gap of the two-pair design is smaller than the 40-run pair's in 7 of 8 cells, and its ratio ends up higher only in the two cells where its power is higher (5 and 8 meV, poorer films noisier).
- **The 24-seed estimates are noisy.** The ratios move by tenths between seed sets.
- **The mechanism matters for funders.** Splitting helps only if a campaign's lead is mostly in place by its midpoint. On this surface it is not, and the shortfall is largest for the device-level lead.

## 4. What this changes

- **The 0.2 memo's "Funders" line stands, but not as a way to save runs.** Running the same 40-run budget as two 20-run pairs does not give a more decisive head-to-head. On this surface, "a second pair of campaigns" has to mean a second full-length pair, about 44 more furnace runs per arm. That design was not simulated here; it is the next run if a funder-grade head-to-head is still wanted.
- **The C1 pre-registration is unchanged.** The absolute primary (beat the literature baseline by > 5 meV QFLS) remains the kill criterion. The loop-versus-OVAT comparison remains a reported secondary with an interval. Its 40-run power of 0.36–0.67 at the M0 noise levels, with a wrong-way rate of 0.02–0.22, is why it cannot carry a kill rule.

## 5. Limits

- **Same synthetic surface and noise model as 0.1–0.4.** Whether the lead grows between runs 20 and 40 is a property of this surface and these strategies, and it decides the answer. A surface where the loop's lead saturates by run 20 would favour splitting.
- **The alternative start is one choice:** a 0.1-sd perturbation, continuous parameters only. A start further from the literature recipe adds start-to-start variance, which a single pair cannot average out, so the comparison could move. A start nearer it brings pair B closer to a replicate of pair A.
- **24 seeds per cell.** Power estimates per cell carry roughly ±0.1, and paired differences carry the standard errors shown.
- **The Welch tests pool films** and ignore the furnace-run structure of confirmation, as in 0.1–0.4. A mixed-model test would be somewhat more powerful for every design.
- **Only the M0 lookup cells were run.** The main-sweep noise levels were not.
