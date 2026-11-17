# mdl-engine v0.2 — First Run of the Deterministic and Temporal Layers
### Results memo. Companion to the implication-engine design (§5–6, build step "v2") and the learning-curve problem setup (§5–6, task "T3").
**Prepared 16 Nov 2026; §1.1 revised 17 Nov 2026 after checking the tables. Code: `mdl-engine-0.2.zip` (16 passing tests). All numbers below are reproducible with `python -m mdl_engine`.**

---

## 0. What now exists

A tested Python package that turns the two design memos into running code:

- **Physics layer:** %SQ normalization, Voc/Jsc/FF gain decomposition, one-diode low-light projection (50–1000 W/m², 200–1000 lux), thermal prior, homogeneous-material compliance arithmetic, transferability operator, and an Implication Ledger entry builder. Verdict fields are emitted empty for human ratification.
- **Temporal layer:** a distribution-free record-count test of "World B", a static-tail null simulation, an exact Bayesian changepoint, the gate backtest, and a window-calibration simulator.
- **Seed data:** nine events and four record series, each row carrying its provenance and a `verify` flag where it has not been checked against a primary source.

---

## 1. Findings that change something

### 1.1 The record history depends on which clock you read (resolved against the tables, 17 Nov 2026)

Checked against Efficiency Tables v62 and v64 directly. The tables' small-area ("notable exceptions") kesterite rows are:

| Certified | Efficiency | Area | Voc / Jsc / FF | Group, lab |
|---|---|---|---|---|
| Apr 2023 (v62) | 14.9% | 0.2694 cm² (da) | 555.4 mV / 36.93 / 72.5% | IoP-CAS, NPVM |
| Apr 2024 (v64) | 15.1% | 0.2697 cm² (da) | 529.9 mV / 38.44 / 74.0% | IoP-CAS, NPVM |

The Mg-ordering paper (14.9% certified; arXiv April 2024; Nature Energy 12 November 2025) is the April 2023 certificate, published in a journal about 2.5 years later. So the project ledger's "2025: 14.9%" is a publication date, and a 15.1% cell was already certified in April 2024, before the 2026 results the pitch treats as the frontier.

| Basis | Records since 2022 | Increments (abs. pts) | Rate |
|---|---|---|---|
| Publication-dated (project ledger) | 6 | +1.2, +0.4, +0.7, +0.14, +0.06, +0.2 | 0.46 pts/yr from 2023 |
| Certification-dated (tables, designated area) | 4, one unverified | +0.4, +1.9, +0.2, +0.2 | 0.13 pts/yr after April 2023 |

Consequences:
- **"Roughly one point per year since 2022" is not supported on either clock.** Publication-dated it is 0.46–0.6 pts/yr. Certification-dated, nearly all the gain is the single 13.0 → 14.9 step certified by April 2023; since then the certified frontier has moved +0.2 (to 15.1, April 2024) plus the unverified 15.3 claim. Restate Act III and Appendix A.
- **"Three distinct mechanisms inside ~18 months" is a publication-clock statement.** The certificates span April 2023 to 2026.
- **Cui et al.'s 15.04% is not a record on the certification clock**: it sits below the 15.1% certified in April 2024. Its significance is the 602 mV Voc, not the headline efficiency. (The two are not strictly comparable: the tables row is designated-area, the papers quote total-area. That is failure mode F2, and it needs one sentence wherever the ledger is shown.)
- **The draft 2-year gate is fired today on certified data.** No in-tables record has exceeded the April 2024 entry, so a silence-only gate with W = 2 fired in April 2026 and stays fired unless the 15.3% claim is confirmed. This is the strongest live argument for the two-signal gate.
- **Measured pipeline lag (F1):** certificate → arXiv 12 months → journal 31 months for the 14.9% result. Publication dating runs far behind certification here, the opposite direction from the memo's assumption that tables lag claims.
- **The 15.1% step was current-led with a voltage loss:** Voc fell 25 mV while Jsc and FF rose. A narrower bandgap is the likely reading; it is not a diode-quality gain.

Still open: the v61 certificate date for 13.0%; the value of the new CAS kesterite entry in v66 (press reports conflict); what v65, v67 and v68 list; whether the Joule 2026 "15.1% certified" paper is the April 2024 certificate.

### 1.2 The memo's extreme-value argument needs one correction, and the corrected version is stronger

The learning-curve memo says that under a static distribution, record increments shrink. That holds only for tails lighter than exponential; with an exponential tail, increments do not shrink at all. The assumption-free signature of World B is the **count** of records: for independent draws from any fixed distribution, the expected number of new records while cumulative attempts grow from N₀ to N₁ is ln(N₁/N₀).

Probability of seeing at least k new records under a static distribution:

| k records | attempts ×1.3 | ×2 | ×3 | ×10 | multiplication needed for p ≥ 0.05 |
|---|---|---|---|---|---|
| 3 | 0.003 | 0.033 | 0.099 | 0.40 | 2.3× |
| 4 | 0.0002 | 0.006 | 0.026 | 0.20 | 3.9× |
| 5 | <0.0001 | 0.001 | 0.005 | 0.08 | 7.2× |
| 6 | <0.0001 | 0.0001 | 0.001 | 0.03 | 13.6× |

"Attempts" means all record-grade campaigns in the field's history. For pure resampling to explain five records, the field would have had to do about seven times its entire prior cumulative effort inside four years. This is the quotable null-model number, it needs no tail assumption, and it applies on either clock (4 certified records need about a fourfold multiplication; 6 published ones about fourteenfold). Caveat: it assumes independent attempts; successive records from one lineage are not independent, which is exactly what the F6 lineage count is for.

The tail simulation agrees: reaching 15.04% from 12.6% under a static distribution has probability ≤1.5% for tail scales ≤0.5 points even at 3× attempts, and only becomes plausible (~30%) with a 0.8-point tail **and** a 10× attempt surge.

### 1.3 The changepoint is real on one clock and not robust on the other

Bayesian single changepoint on annual record counts, 2014–2026:
- Publication-dated: most probable year 2023 (posterior 0.48), Bayes factor ≈ 20 over no change, rate 0.09 → 1.2 records/yr.
- Certification-dated: Bayes factor ≈ 1.2. No evidence of a rate change on annual counts, because the certified records are spread one per year (2022, 2023, 2024, 2026).
- Including the 2010–13 IBM run, the single-changepoint model is weak (Bayes factor ≈ 1.5) because the history has three regimes, not two.

θ₁ is therefore "supported, conditional on the dating basis", not established.

### 1.4 Frontier silence cannot carry the gate at any reasonable window

False-fire probability of the silence signal alone over a 9-year latent-progress plateau (hidden capability rising 0.25 pts/yr):

| Record-grade attempts per year | W = 2 | W = 3 | W = 4 | W = 5 |
|---|---|---|---|---|
| 0.5 (incumbent at capability) | 1.00 | 0.96 | 0.77 | 0.51 |
| 1 | 0.99 | 0.81 | 0.46 | 0.21 |
| 2 | 0.90 | 0.43 | 0.13 | 0.02 |
| 4 | 0.58 | 0.09 | 0.005 | 0.001 |
| any rate, outlier incumbent (+1 pt) | 1.00 | 1.00 | 1.00 | 0.6–0.95 |

The memo's expectation of W ≈ 3 years for <10% false fires holds only if the field makes about four certification-grade attempts a year and the standing record is not an outlier. In the 2014 situation (IBM's hydrazine cell sitting above the field) no window up to 4 years is safe. This confirms the two-signal design and says the window must be calibrated on the leading indicators, which means the shadow-tables dataset is on the critical path for the gate, not optional.

### 1.5 Equal STC efficiency does not determine low-light behaviour, and the engine can now show by how much

Two ~15.4% devices:
- **Cui et al. (Voc 602 mV, FF 68.9%).** Gain versus the 12.6% benchmark is 79% Voc, 27% Jsc, −6% FF: diode-quality-led, as the seed entry said. But with only Voc/Jsc/FF known, every one-diode fit consistent with those numbers spans a retention of **0.23 to 0.81 at 100 W/m²**. The STC triple alone cannot rank the device for a facade.
- **A 15.4% device with a published diode fit (n 1.42, Rsh ≈ 970 Ω·cm²).** Retains 0.93 / 0.85 / 0.76 at 400 / 200 / 100 W/m² — good for VIPV and BIPV. Indoors it collapses to **~1% at 1000 lux**, because the indoor photocurrent (~0.12 mA/cm²) times Rsh is only ~0.11 V. The same device with Rsh of 10, 30, 100 kΩ·cm² would give 6.8%, 8.2%, 8.8%.

Two usable consequences:
- **A design target for the interior product line:** shunt resistance ≳ 30 kΩ·cm² at low light. A 1-sun fit of ~1 kΩ·cm² is fine outdoors and fatal indoors. (Caveat: Rsh fitted at 1 sun can understate the dark value, so this is a pessimistic bound until measured.)
- **The cheapest high-value measurement is confirmed:** intensity-dependent Voc and a low-light J–V on a 15%-generation device collapses the 0.23–0.81 band to a line. Suns-Voc needs no new hardware beyond neutral-density filters.

### 1.6 Compliance arithmetic, computed

| Layer | Restricted element | wt% | × over limit | VIPV | BIPV | Interior |
|---|---|---|---|---|---|---|
| CdS buffer | Cd | 77.8 | 7,781× | FAIL | moot | FAIL |
| Cd-alloyed absorber (30% on Zn site) | Cd | 7.4 | 744× | FAIL | moot | FAIL |
| FAPbI₃ perovskite absorber | Pb | 32.7 | 327× | FAIL | moot | FAIL |
| CZTSSe + Zn(O,S) buffer (P₀ target) | none | — | — | pass | moot | pass |

Every seed kesterite record uses CdS, so every one is blocked for VIPV and interior as published. The sign flip of Exhibit B is reproduced by code.

### 1.7 Smaller items

- The ≥1 cm² tables row moved 12.1% → 13.45% (v62 → v64) with Voc *falling* 27 mV; the gain came from FF and Jsc. Either the bandgap narrowed or this was not a diode-quality gain. Worth a look in the source.
- A 2026 Nature Materials paper from the Meng group reports certified 14.2% at 1 cm² and a 13.0% module at 10.5 cm². That supersedes the 10.1% module figure in the pitch (Act III, Appendix A) if confirmed.

---

## 2. Known limits of this run

- **%SQ is computed against a 5772 K blackbody, not AM1.5G**, because the workspace could not download the ASTM G173 table. Kesterite reads ~52% of SQ at 15.45%; the true AM1.5G figure will be lower (roughly 47–48%). Voc deficits are reliable; cross-bandgap %SQ comparisons are not yet. Fix: `python -m mdl_engine --spectrum astmg173.csv`.
- Several seed J–V values come from press coverage or memory, and several bandgaps are assumed. Each is marked in `events.json`.
- The "fitted 15.4%" device (ref. 30 of PMC12417543) is consistent with the Mg-ordering lab champion (15.4%, certified 14.9%) but that is not confirmed.
- Signal 2 of the gate (leading indicators) is implemented as an interface but has no data behind it yet.
- The blind-spot map reads "not yet assessed" for all nine events: the data-flag fields need an extraction pass.

## 3. Next actions, in order

1. **Restate the slope and the record ledger in the pitch** using §1.1, and finish T0 for v61 and v65–v68.
2. Drop in the ASTM G173 file and re-run for true %SQ.
3. Replace press J–V values with the papers' certified values; trace the fitted device.
4. Add suns-Voc / low-light J–V to the M0 protocol (unblocks §1.5 for every future device).
5. Begin the shadow-distribution dataset; it is what the gate window is calibrated on.
6. Amend the learning-curve memo §2 with the record-count formulation (§1.2 above).

## Sources

- [pv magazine: All solar cell efficiencies at a glance (Tables v62)](https://www.pv-magazine.com/2023/06/22/all-solar-cell-efficiencies-at-a-glance-updated)
- [Solar cell efficiency tables (Version 62), NREL copy](https://nrel.gov/docs/fy23osti/86382.pdf)
- [Solar cell efficiency tables (Version 64), NREL copy](https://nrel.gov/docs/fy24osti/90199.pdf)
- [PMC12417543: kesterite loss analysis with one-diode fit table](https://pmc.ncbi.nlm.nih.gov/articles/PMC12417543)
- [Meng group, Nature Materials 2026, 10.1038/s41563-026-02703-6](https://www.iop.cas.cn/xwzx/kydt/202608/P020260824322432154071.pdf)
- [Wang et al., arXiv 2404.05974 (Mg-ordering, 15.4% / certified 14.9%)](https://www.arxiv.org/pdf/2404.05974)
- [Nature Index record for the Mg-ordering paper (published 12 Nov 2025)](https://www.nature.com/nature-index/article/10.1038/s41560-025-01902-w)
- [CAS news release on the 15.45% / 15.04% result](https://english.cas.cn/newsroom/research-news/202602/t20260226_1151206.shtml)
- [Secondary coverage giving the lab-champion J–V values](https://www.academicjobs.com/research-publication-news/cztsse-solar-cells-cas-15percent-efficiency-record-or-academicjobs-6701)
