# mdl-engine 0.2

Deterministic layer of the MDL implication engine (design memo sections 5-6) and the
temporal analysis from the learning-curve memo (sections 2, 5, 6). Pure Python:
numpy, scipy, matplotlib (charts only), pytest (tests only).

    python -m pytest -q            # 21 tests
    python -m mdl_engine --out out # ledger + temporal analysis + charts
    python -m mdl_engine --spectrum astmg173.csv   # use real AM1.5G for %SQ

| Module | Does | Design ref |
|---|---|---|
| `sq.py` | detailed-balance limit, %SQ, logit, Voc deficit | 5.1 |
| `decompose.py` | Voc/Jsc/FF shares of a gain | 5.2 |
| `diode.py` | one-diode fit, eta(G) to 50 W/m2 and 200-1000 lux, prior envelope | 5.2 |
| `thermal.py` | TC prior multiplier (flagged as borrowed) | 5.3 |
| `compliance.py` | wt% per homogeneous material, per-application gates | 5.4 |
| `transfer.py` | mechanism class x platform deltas -> retention band | 5.5 |
| `ledger.py` | event -> Implication Ledger entry (JSON + markdown) | 6 |
| `temporal.py` | record-count test, static-null simulation, changepoint, gate backtest, window calibration | LC memo 5-6 |

## Adding an event
Append to `mdl_engine/data/events.json`. Minimum: `id`, `headline`. Add `eg_ev` +
`device` (voc_v, jsc_ma, ff_pct; optional n, rs, rsh from a J-V fit) for physics,
`layers` (name + formula) for compliance, `mechanism` (class, route, configuration)
for transferability, `prev_id` for gain decomposition, `data_flags` for the
blind-spot map. Missing inputs are listed on the entry rather than guessed.

`values` records provenance per reported value: `{"value", "tier", "source",
"access", "verify", "unit"?, "note"?}`. `access` says how the value was read
(for example a table row as indexed by web search, when the publisher refused
automated access). `verify: true` marks anything not confirmed against a
source. The ledger copies `values` into `reported_values` and lists the
`verify: true` keys under `unverified`. Leave a layer stack out when the
buffer is not stated: the compliance gate then reads `unknown`, not `pass`.

Provenance tiers as used in the seed rows (the repository has no formal
definition; this is the reading the rows imply): **T1** an efficiency-table
row; **T2** a certified value reported in a paper, not (yet) read from a table;
**T3** an uncertified lab value or detail from a paper; **T4** press or other
secondary coverage; `assumed` for values entered without a source.

Every entry with Voc, Jsc, FF and an efficiency gets a `jv_check`: if
Voc x Jsc x FF misses the stated efficiency by more than 0.15 points, the entry
says so under `missing`, and its normalized shares and gain should not be used.

## Known limits (read before quoting numbers)
* **%SQ uses a 5772 K blackbody unless `--spectrum` is given.** It reads high and the
  bias varies with bandgap (the Pb-perovskite seed row shows Jsc/SQ > 1). Voc
  deficits are reliable; cross-bandgap %SQ comparisons are not until AM1.5G is loaded.
* Seed J-V values carry their provenance in `notes`; several are from secondary
  sources or assumed bandgaps.
* Indoor numbers assume a white LED (320 lm/W, 2.25 eV mean photon, EQE 0.85).
* Rsh fitted at 1 sun can understate low-light Rsh, so indoor projections from
  1-sun fits are pessimistic bounds until measured.
* Verdict fields are intentionally empty: a human ratifies.
