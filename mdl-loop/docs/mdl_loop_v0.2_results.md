# mdl-loop 0.2 — Anchor Devices in the Loop (A8) and the Ratified C1 Pre-registration
### Results memo. Follows the mdl-loop 0.1 memo (A7) and amends its §2. Companion to the next-stage plan (A8, B1, C1) and the v2 map (§7a: "periodic anchor devices keep the proxy honest").
**Status 19 Nov 2026 (evening): the §3 precondition is restated in M0's units by `claude/M0_noise_floor_design.md` (go if the film-to-film 80% upper bound at the literature recipe is ≤ 13 meV; run-to-run becomes a flag).**
**Status 20 Nov 2026: §5 next action 3 is done in mdl-loop 0.4 (`mdl_loop_v0.4_results.md`). Anchoring the final recommendation removes only part of the §2.4 over-claim. The §2.4 claims rule stands. See the addendum at the end.**
**Status 21 Nov 2026: §5 next action 4 is done in mdl-loop 0.5 (`mdl_loop_v0.5_results.md`). At the same total furnace runs, two 20-run campaign pairs do not beat one 40-run pair. The §0 "Funders" second pair has to be a full-length pair (not simulated yet).**
**Prepared 19 Nov 2026. Code: `mdl-loop-0.2.zip` (14 passing tests). Numbers are in `out/summary.json`, reproducible with `python -m mdl_loop --out out --seeds 24`. Same synthetic test surface as 0.1; read every number as conditional on it.**

---

## 0. Decision recorded (19 Nov 2026)

C1's pass/fail rule is the **hybrid** proposed in the 0.1 memo:

- **Primary:** the loop's confirmed recipe beats the locked B3 literature baseline by more than **5 meV QFLS** (one-sided Welch, α = 0.05).
- **Secondary:** the loop-versus-OVAT difference, reported with a 90% interval.
- **Kill:** only if the primary fails at 40 runs *and* the secondary interval includes zero.
- **Baseline lock:** the B3 reproduction of the literature recipe is frozen before C1's first search run.
- **Funders:** a decisive head-to-head result, if one is needed, comes from a second pair of campaigns, not from more confirmation runs.

---

## 1. What A8 adds

`DeviceAwareGPBO` keeps the QFLS model and adds a second model of the **device-only loss**, the gap between a film's QFLS and its device Voc. This model learns only from films that were finished into anchor devices. Acquisition, the incumbent and the recommendation all use *predicted device Voc*: predicted QFLS minus predicted gap, with the two uncertainties added.

How anchors are placed:
- They cost no furnace runs. Every 5 runs after the initial design, two existing films are finished into devices, which comes to **14 anchor devices in a 40-run campaign**.
- The first cycle includes a literature-recipe film, which sets the device baseline.
- Each cycle includes the incumbent's film when one is unanchored.
- The rest go to promising films whose gap the model is least sure of.
- Each anchor film is scribed into 6 cells and averaged (8 mV cell-to-cell scatter, about 3 mV per film). With single cells, the gap model could not separate the Se effect from noise in early tests.

## 2. Findings

### 2.1 The device-aware loop recovers the device-level lead the QFLS loop lost

Median true device-Voc gain over the literature recipe, in mV:

| M0 film σ | QFLS loop @20 / @40 | Device-aware loop @20 / @40 | OVAT @20 / @40 |
|---|---|---|---|
| 5 meV | 14.1 / 16.0 | 17.0 / **20.7** | 8.7 / 9.7 |
| 10 meV | 6.4 / 11.1 | 11.4 / **19.7** | 5.1 / 8.6 |
| 20 meV | 0.1 / 3.4 | 3.2 / **6.4** | 1.0 / 1.0 |
| 30 meV | −0.2 / −0.6 | 3.3 / −0.7 | −0.4 / 0.0 |

At σ = 10 meV and 40 runs, the device-aware loop leads OVAT by a median **8.6 mV at the device level** (ahead in 71% of campaigns). The QFLS-only loop led by 1.4 mV.

The mechanism shows in the recipes. The QFLS loop drove the Se charge to its 640 mg bound, while the device-aware loop settled near **240 mg**. In exchange it gives up a few meV of QFLS: a median 4.6 meV less than the QFLS loop at σ = 10, but 7.1 mV more device Voc.

### 2.2 The ratified QFLS primary still works, with slightly less power

Power of the primary criterion (beat the literature recipe by > 5 meV QFLS) at 40 runs:

| M0 film σ | QFLS loop, 4 conf. runs | Device-aware loop, 4 conf. runs | Device-aware loop, 8 conf. runs |
|---|---|---|---|
| 5 meV | 1.00 | 0.96 | 0.98 |
| 10 meV | 0.81 | 0.74 | 0.75 |
| 20 meV | 0.34 | 0.26 | — |

The device-aware loop trades some QFLS for device Voc, so it clears a QFLS bar a little less often. More confirmation runs don't help: power levels off at the share of campaigns whose true gain exceeds the margin. **To keep 80% power with the device-aware loop, M0 needs film-to-film σ somewhat below 10 meV.** I did not run the levels between 5 and 10 meV, so B1's target should be "≤ 10 meV, aim for ≤ 7"; the next sweep should pin the value down.

### 2.3 A device-level primary is not yet affordable

The same absolute test on anchor devices (confirmation films finished into devices against 16 literature-recipe devices, > 5 mV margin) has 40-run power of **0.87 at 5 meV and 0.60 at 10 meV** for the device-aware loop. The QFLS-only loop scores 0.79 and 0.38; OVAT scores 0.49 and 0.27. A device-level head-to-head with OVAT is weaker still (0.51 at 10 meV).

Devices therefore separate the arms well, but they cannot carry the primary unless M0 lands near 5 meV. That supports keeping the ratified QFLS primary, with device results reported alongside.

### 2.4 The device model over-claims more than the QFLS model

The device-aware loop's claimed device gain exceeds the truth by a median **5.3 mV** at σ = 10 (90th percentile 15) and 13.5 mV at σ = 20. The QFLS loop over-claims its QFLS by 1.6 meV. Fourteen anchors spread over 13 dimensions leave the gap model under-sampled away from the anchored films, and the final recommendation is usually unanchored.

**Rule:** device-level claims come from confirmation devices, never from the model's prediction.

### 2.5 Nothing works at 30 meV

Neither loop nor OVAT makes device progress at σ = 30 meV in 40 runs. B1's precondition stands.

---

## 3. Ratified C1 pre-registration (supersedes 0.1 memo §2)

| Item | Setting |
|---|---|
| Precondition | M0 film-to-film σ ≤ 10 meV (aim ≤ 7) and run-to-run σ ≤ 5 meV, replicates over ≥ 4 furnace runs |
| Baseline | B3 literature reproduction, frozen before C1 starts |
| Loop arm | Device-aware loop (A8): 40 furnace runs × 4 slots, 2 anchor devices every 5 runs (14 total) |
| Control arm | Careful OVAT, 40 runs, same start and replicate overhead |
| Primary | Loop's recipe, confirmed over 4 furnace runs, beats the baseline by > 5 meV QFLS, one-sided Welch, α = 0.05 |
| Secondary | Loop − OVAT QFLS difference with a 90% interval; device-level confirmation of both arms' recipes, reported |
| Kill | Primary fails at 40 runs **and** the secondary interval includes zero |
| Claims rule | Device gains are quoted from confirmation devices only |
| Budget | ≈ 92 furnace runs (2 × 40 search + 2 × 4 confirmation + 4 baseline) plus 14 anchor devices and the confirmation devices; about 9 weeks at an assumed two runs per working day |

Re-derive the precondition, power and budget with M0's measured noise before the first C1 run.

## 4. Limits added by this run

- The device-only loss is an emulator term I chose (MoSe₂ growing with Se; surface Li hurting the front interface). A8 shows the mechanism works. How large the effect is in real devices comes only from B3/C3 devices.
- Anchors are modelled as free in furnace runs but not in time. Fourteen finished devices in nine weeks is a real workload for the device line or partner (C3).
- The gap model ignores any correlation between a film's QFLS noise and its device noise beyond inheriting the film's QFLS.

## 5. Next actions

1. Write the M0 design note (B1): run structure, the noise decomposition it must report, and the σ thresholds above.
2. Sweep σ between 5 and 10 meV and anchor cadence (1–3 per cycle) to fix the M0 target and the device budget.
3. Always anchor the final recommendation before confirmation, and test whether that removes most of the over-claim in §2.4.
4. Simulate the two-campaign head-to-head design for funders.
5. Then return to Stage A paper items: A2 (gate G2 rewrite) and A6 (ledger entries).

---

## Addendum, 20 Nov 2026 (mdl-loop 0.4)

This addendum adds to §2.4 and §5 item 3 and leaves the text above as written. Same synthetic surface; 24 seeds per cell; details in `mdl_loop_v0.4_results.md`.

- **§5 item 3 tested.** The device-aware loop now finishes the recommended film into an anchor device before stopping, refits the gap model and re-recommends. In the 10 meV cell at 40 runs, the median over-claim went from 5.8 to 4.8 mV and the 90th percentile from 12.6 to 11.0. True device gain went from 20.3 to 20.8 mV and primary power from 0.74 to 0.78 (paired difference +0.035 ± 0.032). Across the eight M0 lookup cells, the median over-claim at 40 runs fell in six. The change is larger at 20 runs.
- **It does not remove most of the over-claim.** Anchoring the hand-over recipe in 96–100% of campaigns (up to three rounds) leaves the median over-claim at 4.2 mV in the 10 meV cell. **The §2.4 rule stands:** device-level claims come from confirmation devices.
- **The §2.4 figures (5.3 / 15 mV) are not reproduced exactly** in the current environment. With BLAS pinned to one thread, the same 0.3 code gives 5.8 / 12.6 mV. The difference is floating-point sensitivity to BLAS thread count, not a code change (0.4 memo §5).
