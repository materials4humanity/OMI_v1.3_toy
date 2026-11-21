# mdl-loop 0.4 — Anchoring the Final Recommendation
### Results memo. Follows the mdl-loop 0.2 memo (A8, §2.4 over-claim; §5 next action 3) and the M0 design note (§1.1 lookup). Same synthetic test surface as 0.1–0.3: every number below is a property of that surface, not of kesterite.
**Prepared 20 Nov 2026. Code: mdl-loop 0.4.0 (18 passing tests). Numbers are in `out/final_anchor_summary.json`, reproducible with `python -m mdl_loop.final_anchor --out out --seeds 24` (13 min on 4 cores). 24 seeds per cell.**
**Status 21 Nov 2026: the final anchor is now part of the C1 pre-registration. The two-campaign head-to-head that follows from it is in `mdl_loop_v0.5_results.md`. From 0.5 every driver pins BLAS to one thread (§5).**

---

## 0. What changed

The 0.2 memo found that the device-aware loop over-claims its device gain, because the recommended film has usually never been made into a device. In 0.4 the loop finishes one more film before it stops (`DeviceAwareGPBO.finalize`):

1. If no film of the recommended recipe has been made into a device, the most recent surviving film of that recipe is finished into an anchor device (6 cells, as for the other anchors).
2. The gap model is refitted.
3. The loop recommends again. Confirmation uses the new recommendation.

This costs one device and no furnace runs. It runs a single round. If the new recommendation is a different recipe with no device, the loop keeps it as it is (see §3).

**How 0.3 is measured against 0.4.** Each checkpoint runs the final step on a copy of the campaign, so the campaign that carries on is unchanged. The 0.3 answer from the same campaign is stored beside the 0.4 answer (`v03` in each checkpoint record). The comparison is therefore paired campaign by campaign. Where the recommendation did not change, the two answers are the same recipe.

**Primary power** is the ratified C1 rule: 4 confirmation runs against 4 literature-recipe runs, a margin above 5 meV QFLS, one-sided Welch at α = 0.05, 30 re-simulations per campaign. It uses common random numbers: each campaign gets the same confirmation draws in both versions. So power differences come only from changed recommendations. The table gives the paired difference with its standard error over campaigns.

**Over-claim** is the claimed device-Voc gain minus the true device-Voc gain of the recipe handed to confirmation. "Final pick anchored" is the share of campaigns in which that recipe has an anchor device at hand-over. In the 0.3 column this is the share where it already had one.

## 1. Results at 40 runs

| Cell | Over-claim median, 0.3 → 0.4 (mV) | Over-claim p90, 0.3 → 0.4 (mV) | True device gain median, 0.3 → 0.4 (mV) | Primary power, 0.3 → 0.4 (paired Δ ± SE) | Final pick anchored, 0.3 → 0.4 |
|---|---|---|---|---|---|
| M0 5 meV, poorer films noisier | 1.5 → 1.5 | 7.2 → 5.7 | 24.7 → 25.6 | 1.00 → 1.00 (+0.000 ± 0.000) | 0.08 → 0.62 |
| M0 8 meV, poorer films noisier | 6.2 → 5.5 | 14.5 → 13.5 | 20.9 → 21.0 | 0.94 → 0.94 (+0.001 ± 0.001) | 0.21 → 0.58 |
| M0 11 meV, poorer films noisier | 3.7 → 2.9 | 9.9 → 7.7 | 20.5 → 20.9 | 0.89 → 0.92 (+0.039 ± 0.026) | 0.21 → 0.83 |
| M0 15 meV, poorer films noisier | 4.3 → 2.9 | 12.8 → 13.0 | 15.0 → 15.8 | 0.70 → 0.62 (−0.075 ± 0.043) | 0.25 → 0.79 |
| M0 5 meV, constant noise | 0.8 → 1.1 | 4.9 → 3.8 | 25.1 → 25.1 | 1.00 → 1.00 (+0.000 ± 0.000) | 0.17 → 0.88 |
| M0 8 meV, constant noise | 1.7 → 1.5 | 11.1 → 10.5 | 19.6 → 20.6 | 0.93 → 0.94 (+0.015 ± 0.012) | 0.17 → 0.88 |
| M0 11 meV, constant noise | 3.3 → 1.4 | 20.7 → 7.7 | 16.0 → 18.9 | 0.79 → 0.86 (+0.071 ± 0.046) | 0.21 → 0.88 |
| M0 15 meV, constant noise | 5.7 → 4.8 | 11.3 → 10.7 | 18.4 → 18.5 | 0.69 → 0.71 (+0.024 ± 0.021) | 0.25 → 0.83 |
| Main sweep, 10 meV (nominal) | 5.8 → 4.8 | 12.6 → 11.0 | 20.3 → 20.8 | 0.74 → 0.78 (+0.035 ± 0.032) | 0.12 → 0.54 |

M0 rows are labelled by film-to-film sd as M0 measures it at the literature recipe (M0 note §1.1). The main-sweep row uses the 0.1/0.2 nominal noise.

**The final anchor removes some of the over-claim, not most of it.** The median over-claim fell in 7 of 9 cells and the 90th percentile in 8 of 9. In the 10 meV cell the memo's 0.2 §2.4 figure refers to, the median went from 5.8 to 4.8 mV and the 90th percentile from 12.6 to 11.0. The largest change was the 11 meV constant-noise cell: 3.3 → 1.4 median, 20.7 → 7.7 at the 90th percentile.

**True device gain barely moves.** The median rose by 0–2.9 mV per cell. Per campaign, the recommendation changed in 17–50% of campaigns. The paired mean change in device gain was between −0.1 and +2.7 mV, and in 8 of 9 cells some campaigns got worse while others got better.

**Primary power is unchanged within noise.** No cell's paired difference exceeds 2 standard errors. The largest are −0.075 ± 0.043 (15 meV, poorer films noisier) and +0.071 ± 0.046 (11 meV, constant noise), in opposite directions. The M0 go threshold (about 11 meV) does not move.

## 2. Results at 20 runs

At 20 runs the gap model has seen 6 anchors instead of 14, and the final anchor does more:

| Cell | Over-claim median, 0.3 → 0.4 (mV) | Over-claim p90, 0.3 → 0.4 (mV) | True device gain median, 0.3 → 0.4 (mV) | Primary power, 0.3 → 0.4 (paired Δ ± SE) | Final pick anchored, 0.3 → 0.4 |
|---|---|---|---|---|---|
| M0 5 meV, poorer films noisier | 4.8 → 3.2 | 21.1 → 8.4 | 16.1 → 17.2 | 0.99 → 0.99 (−0.001 ± 0.001) | 0.17 → 0.75 |
| M0 8 meV, poorer films noisier | 3.4 → 1.4 | 15.5 → 9.6 | 14.4 → 15.6 | 0.85 → 0.84 (−0.011 ± 0.045) | 0.25 → 0.71 |
| M0 11 meV, poorer films noisier | 6.8 → 4.2 | 20.7 → 8.0 | 13.9 → 17.7 | 0.81 → 0.82 (+0.004 ± 0.005) | 0.25 → 0.67 |
| M0 15 meV, poorer films noisier | 11.1 → 5.5 | 19.4 → 21.2 | 11.3 → 8.0 | 0.47 → 0.42 (−0.044 ± 0.037) | 0.29 → 0.67 |
| M0 5 meV, constant noise | 5.9 → 2.3 | 15.9 → 9.5 | 15.2 → 15.8 | 0.93 → 0.90 (−0.026 ± 0.025) | 0.33 → 0.71 |
| M0 8 meV, constant noise | 6.8 → 2.6 | 13.3 → 9.5 | 13.1 → 15.0 | 0.81 → 0.76 (−0.056 ± 0.046) | 0.21 → 0.75 |
| M0 11 meV, constant noise | 5.6 → 4.9 | 22.7 → 13.5 | 7.5 → 9.6 | 0.48 → 0.52 (+0.039 ± 0.049) | 0.21 → 0.88 |
| M0 15 meV, constant noise | 8.9 → 6.1 | 25.0 → 13.5 | 13.7 → 13.7 | 0.57 → 0.62 (+0.049 ± 0.034) | 0.33 → 0.88 |
| Main sweep, 10 meV (nominal) | 9.1 → 6.9 | 19.2 → 16.0 | 10.2 → 11.7 | 0.58 → 0.52 (−0.061 ± 0.051) | 0.12 → 0.62 |

The median over-claim fell in all 9 cells, and the 90th percentile in 8 of 9; it fell by a third or more in 7 of the 8 M0 cells. Primary power is again unchanged within 2 standard errors. These 20-run figures feed the two-campaign design (next step).

## 3. Sensitivity: repeat until the pick is anchored

A single round leaves the hand-over recipe without a device in 12–46% of campaigns at 40 runs. The share is highest in the 10 meV main-sweep cell, where re-recommendation moved to a different recipe without a device in half the campaigns. The same campaigns were therefore also finalized with up to 3 rounds (`finalize(max_rounds=3)`, recorded as `until_anchored`, not the 0.4 default):

| Cell, 40 runs | Over-claim median / p90, one round (mV) | Until anchored (mV) | Devices per campaign, one round / until anchored | Final pick anchored, one round / until anchored |
|---|---|---|---|---|
| M0 5 meV, poorer films noisier | 1.5 / 5.7 | 0.6 / 4.8 | 0.92 / 1.50 | 0.62 / 1.00 |
| M0 8 meV, poorer films noisier | 5.5 / 13.5 | 5.7 / 12.1 | 0.79 / 1.33 | 0.58 / 0.96 |
| M0 11 meV, poorer films noisier | 2.9 / 7.7 | 2.9 / 7.7 | 0.79 / 0.96 | 0.83 / 1.00 |
| M0 15 meV, poorer films noisier | 2.9 / 13.0 | 3.0 / 11.7 | 0.75 / 1.04 | 0.79 / 0.96 |
| M0 5 meV, constant noise | 1.1 / 3.8 | 1.1 / 3.8 | 0.83 / 0.96 | 0.88 / 1.00 |
| M0 8 meV, constant noise | 1.5 / 10.5 | 1.5 / 10.5 | 0.83 / 1.00 | 0.88 / 1.00 |
| M0 11 meV, constant noise | 1.4 / 7.7 | 0.8 / 7.6 | 0.79 / 0.92 | 0.88 / 1.00 |
| M0 15 meV, constant noise | 4.8 / 10.7 | 4.7 / 10.7 | 0.75 / 0.96 | 0.83 / 1.00 |
| Main sweep, 10 meV (nominal) | 4.8 / 11.0 | 4.2 / 9.4 | 0.88 / 1.42 | 0.54 / 0.96 |

Anchoring the hand-over recipe in 96–100% of campaigns barely changes the median over-claim (main cell 4.8 → 4.2 mV) and lowers the 90th percentile by up to 1.6 mV. **So what remains is not mainly the gap model guessing at a recipe with no device.** I have not split the residual between its candidate sources. Two candidates: the QFLS model's own winner's curse on the recipe it selects, and the scatter of a single anchor device (about 3 mV per film). Recording the QFLS and gap components of each claim separately would settle it. 0.4 keeps the one-round default, because the extra rounds cost 0.13–0.58 more devices per campaign for no clear gain in power or device gain.

## 4. What this changes

- **The claims rule stands** (0.2 memo §2.4): device gains are quoted from confirmation devices, never from the model. 0.4 makes the model's number less wrong at 20 runs, and only slightly less wrong at 40.
- **The ratified pre-registration needs one added line:** before confirmation, the recommended film is finished into an anchor device and the loop re-recommends. Budget: on average 0.75–0.92 extra devices per campaign at 40 runs (all cells), no extra furnace runs.
- **The M0 go threshold and the C1 power figures are unchanged.**

## 5. Reproducibility note

The 0.3 baseline in this run does not exactly match the figures the 0.2 memo printed for the same 10 meV cell. This run gives over-claim 5.8 / 12.6 mV (median / 90th percentile) and device gain 20.3 mV; the 0.2 memo printed 5.3 / 15.0 and 19.7. The cause is floating-point sensitivity to BLAS threading, not a code change:

- I ran the unmodified 0.3 code from the default branch, single-threaded, for seeds 0–3 of that cell. It reproduces this run's 0.3 records exactly: same recommendation, same claim to 6 decimals.
- Run multithreaded, seed 2's claim already differs in the third decimal.
- Over 40 sequential runs such differences can flip a recommendation, so a seeded campaign is reproducible only for a fixed BLAS thread count and library versions.

`final_anchor.py` pins BLAS to one thread (numpy 2.1.3, scipy 1.14.1, scikit-learn 1.9.1 here). The older drivers (`python -m mdl_loop`, `python -m mdl_loop.m0`) do not pin threads, so their published figures can be regenerated only approximately.

## 6. Limits

- Same synthetic surface and noise model as 0.1–0.3. On this surface the device-only loss is zero for low Se without top-layer Li, which is where the device-aware loop settles. That is why device gain and QFLS gain coincide in most campaigns.
- 24 seeds per cell. Medians and 90th percentiles over 24 campaigns move by about a millivolt between seed sets. Treat single-cell changes smaller than that as noise; the cross-cell pattern is the finding.
- Primary power here uses common random numbers and so differs slightly from the 0.2 memo and the M0 note, which used one generator across all campaigns. Compare 0.3 with 0.4 within this memo, not across memos.
- The OVAT arm is untouched and not re-run here.
