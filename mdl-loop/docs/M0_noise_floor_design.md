# M0 — Noise-Floor Campaign: Design Note (plan item B1)
### Design note. Companion to the next-stage plan (B1, B3, C1), the mdl-loop 0.1 and 0.2 memos (C1 power and pre-registration), and the v1 map §5 (where M0 can silently fail).
**Prepared 19 Nov 2026. The numbers come from `mdl_loop/m0.py` (mdl-loop 0.3). The C1-power lookup runs on the same synthetic test surface as the loop memos, so read those figures as conditional on it. The M0 sizing figures are plain statistics and do not depend on the surface.**

---

## 0. What M0 is for

M0 answers one question before any optimization starts: **is the process quiet enough for C1 to detect what it is looking for?** It measures how much the QFLS of the frozen literature recipe scatters between PL spots, between films in one furnace run, and between furnace runs. It also checks the hidden variables the v1 map warns about (box memory, ink age, slot position).

M0 has three further outputs:

1. **The C1 baseline**, a replicated literature-recipe distribution.
2. **The device-gap prior** for the A8 loop, from a handful of literature-recipe devices.
3. **MDL's first open dataset**: fully logged replicates of a 14%-class recipe, a direct reply to the survey finding that 1.5% of kesterite papers report a cooling rate.

## 1. Two corrections to earlier thresholds

**1.1 Thresholds must be stated in what M0 measures.** The C1 simulations set noise for an *optimal* film and let poorer films be noisier. M0 measures the *literature recipe*, which sits about 39 meV below the optimum. If poorer films are noisier, as the simulations assumed, the "≤ 7 meV" target in the 0.2 memo corresponds to about 10–11 meV measured at the literature recipe. I re-ran C1 directly in M0's units, under both assumptions (noisier poor films, and constant noise):

C1 at 40 runs per arm, with run-to-run sd set to half the film sd:

| Film-to-film sd measured at literature recipe | Primary power, device-aware loop (poorer films noisier / constant noise) | Primary power, OVAT (same) | Median device gain in mV, loop / OVAT (poorer films noisier · constant noise) |
|---|---|---|---|
| 5 meV | 1.00 / 1.00 | 1.00 / 0.96 | 24.7 / 13.9 · 23.6 / 15.8 |
| 8 meV | 0.93 / 0.93 | 0.95 / 0.83 | 18.6 / 15.1 · 21.4 / 14.5 |
| 11 meV | **0.92 / 0.81** | 0.56 / 0.59 | 20.9 / 9.8 · 17.5 / 11.5 |
| 15 meV | 0.63 / 0.69 | 0.29 / 0.30 | 15.0 / 5.8 · 19.5 / 6.3 |

The primary is the ratified rule: the confirmed recipe beats the literature baseline by > 5 meV QFLS, 4 confirmation runs, 4 baseline runs, one-sided Welch, α = 0.05.

**The go threshold in M0's units is about 11 meV film-to-film.** C1 keeps 80% power there under either assumption, so M0 does not need to settle which noise shape is true before C1 can start.

Two side results:
- Below about 8 meV, OVAT also passes the absolute test most of the time. At low noise the primary shows that progress happens; the case for the loop then rests on the secondary comparison and on device gains, where the loop leads by about 3–13 mV in every row.
- At 20 runs instead of 40, the device-aware loop's primary power is 0.78–0.81 at 8 meV and 0.57–0.88 at 11 meV.

**1.2 Run-to-run spread cannot be a hard gate.** The ratified precondition includes "run-to-run σ ≤ 5 meV". With run sd at half the film sd, 8 furnace runs estimate it so loosely that the 80% interval spans a factor of about 8, and 17% of M0 campaigns would estimate it as zero. Even 12 runs leave a factor of 4. **Proposal:** make run-to-run a *flag*, not a gate. If its estimate exceeds the film-to-film estimate, investigate the furnace and boxes before C1. The film-to-film estimate carries the decision.

## 2. Entry criteria

Plan change: **B3 bring-up comes before B1.** M0 has to measure the recipe C1 will start from, so that recipe must exist and be frozen first. M0 starts when all of these hold:

- [ ] The B3 literature recipe runs reliably on Mo foil. Films survive. The phase screen is clean on UV-excited Raman (for ZnS(e)) and on XRD.
- [ ] Recipe file v1.0 and the ink SOP are frozen and version-controlled. No edits during M0.
- [ ] The absolute-PL calibration for Mo foil is in place (generalized-Planck fit tolerant of tails, per-substrate outcoupling correction), with a reference sample defined.
- [ ] The A4 schema is live at ingestion and completeness ≥ 0.9 is enforced. Run order, box ID, slot position, ink batch and age, humidity and operator are mandatory.
- [ ] At least two graphite boxes are conditioned and labelled.

## 3. Design

### 3.1 Core block: noise components (8 furnace runs)

| Factor | Setting | Why |
|---|---|---|
| Recipe | Frozen literature recipe only | M0 measures noise, not effects |
| Furnace runs | **8** (12 if the schedule allows) | 8 runs estimate film-to-film sd to ±15% (relative sd 0.15); 4 runs give ±20% and a much weaker go/no-go rule (§4) |
| Films per run | 4 (every slot) | Film-to-film is the decision variable; 32 films give 24 degrees of freedom |
| PL spots per film | 3, fixed pattern | Separates measurement scatter from film scatter (impossible with 1 spot) for the price of a PL map |
| Days | ≥ 4, at most 2 runs per day | Day effects become part of the run effect, not hidden in it |
| Ink batches | 2, with ink age spanning fresh to about 5 days | Measures ink-age drift (v1 map §2d) |
| Boxes | 2, alternated A/B by run | Box differences show up as a contrast, not as noise |
| Slot position | Rotated across runs (4 × 4 Latin square, used twice) | Separates slot position from film identity |
| PL reference sample | Measured at the start and end of every PL session | Separates instrument drift from film scatter |
| Companion data | Urbach energy and PL peak on every spot; UV-Raman on one film per run; XRD on one film per day | Triangulates QFLS; catches secondary phases that could inflate PLQY (v1 map §5a) |

### 3.2 Probe block: hidden variables (2 runs, plus 2 optional)

- **Alkali memory (1 run + 1 follow-up).** One run in box A with films at the top of the C1 alkali range (Na 160 mM, Li 200 mM). The next run in box A uses the frozen recipe, compared against the core runs. This tests whether box residues carry over (v1 map §5c). If they do, C1 needs dedicated boxes per alkali level or a bake-out step between runs.
- **Noise-shape probe (optional, 2 runs).** Two runs of a deliberately weaker recipe (a shorter, cooler anneal, expected 20–30 meV lower). This shows whether poorer films are noisier, which sets the loop's noise model. §1.1 shows the go decision does not depend on it, so it can be skipped if time is short.

### 3.3 Device block (no extra runs)

Finish **4 core-block films into anchor devices**, one per day, 6 cells each. These give the literature-recipe device Voc and the QFLS-to-device gap. The gap replaces the loop's assumed prior (25 ± 15 mV) with a measured one. If the ZTO partner (C3) is not ready, use the CdS reference buffer and label the gap as CdS-stack.

**Total: 10 furnace runs (12 with the optional probe) and 4 devices, over about 1.5 weeks.**

## 4. Analysis and decision rule (pre-registered)

**Model.** Nested random effects: furnace run → film → PL spot. Box, ink age and day are fixed covariates, which is exploratory at 8 runs. Report the spot, film and run standard deviations with 80% intervals, the ink-age slope, the box contrast, the memory-probe shift with its interval, and the reference-sample drift.

**Go/no-go uses the film-to-film sd:**

| M0 result | Call | Operating characteristics (8 runs) |
|---|---|---|
| 80% upper bound ≤ 13 meV (the bound sits above the estimate, so this cap corresponds to true values of about 10–11 meV) | **Go:** start C1 as registered | Go probability: 1.00 if true sd is 8 meV, 0.81 at 10, 0.60 at 11, 0.05 at 15 |
| Upper bound > 13 meV and point estimate ≤ 15 meV | **Fix and re-measure:** a short reproducibility sprint on the largest component (spot → metrology; film → coating and ink; run → furnace and boxes), then repeat the core block | — |
| Point estimate > 15 meV | **Stop:** C1 as designed would have power ≤ 0.69; change the process before planning C1 | — |
| Run-to-run estimate > film-to-film estimate | **Flag:** investigate furnace, boxes and day effects before C1, whatever the film result | — |
| Memory probe shift > 2× the film sd | **Flag:** dedicated boxes or a bake-out step between C1 runs | — |

**Why the rule is conservative.** Starting C1 when the true noise is 15 meV wastes about 92 runs at roughly two-thirds power. Stopping when it is really 10–11 meV costs a one-week sprint and 8 runs to re-measure. The rule accepts the cheaper error more often: at 8 runs it says go only 60% of the time when the truth is 11 meV. With 12 core runs, the go probability at 10 meV rises from 0.81 to 0.91 and the false go at 15 meV falls to 0.03.

**Feed-forward to C1** (a 20-minute rerun):
1. Put M0's film and run estimates into `mdl_loop.m0.noise_for` and re-derive C1's power and budget.
2. Set the loop's gap prior from the M0 devices.
3. Keep C1's 4 contemporaneous baseline runs. Pool them with M0 only if M0 shows no drift with ink age or day.

## 5. What M0 does not do

- It does not test any recipe change. Effects belong to C1.
- It does not measure noise on steel. Steel gets its own short M0 block when C2 starts, since barrier pinholes add a variance source Mo foil lacks.
- It does not qualify the device line. Four devices give a gap prior, not a device-noise study.

## 6. Deliverables

1. The M0 dataset, published to the commons with full A4 metadata.
2. The variance-component report and the go/no-go call against §4.
3. The re-derived C1 power and budget.
4. The measured gap prior.
5. A one-paragraph methods note on the noise components of a solution-processed kesterite recipe on Mo foil. The v1 map and the Uppsala survey both say this is rarely reported.
