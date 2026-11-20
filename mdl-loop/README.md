# mdl-loop 0.3

The software half of campaign C1, built before any hardware exists (next-stage
plan items A4, A7, A8, plus the M0 design support for B1). It answers one question the plan leaves open:
**how many furnace runs does C1 need before "no separation from the OVAT control"
is a fair kill condition, and how does that number depend on the noise floor M0
will measure?**

    python -m pytest -q                      # 16 tests
    python -m mdl_loop.m0 --out out          # M0 lookup and sizing, ~15 min
    python -m mdl_loop --out out --seeds 24  # full sweep, ~30 min on 2 cores
    python -m mdl_loop --out out --report-only

| Module | Does |
|---|---|
| `schema.py` | Run record with the A4 hidden parameters as required fields; weighted completeness score (A4 x3, reproducibility x2, context x1) |
| `space.py` | P0 trajectory space: 7 run-level parameters shared by a furnace run, 4 sample-level (Na, Li, Li layer, Cu ratio); literature Mo-foil recipe |
| `emulator.py` | **Virtual kesterite v0**, a synthetic test surface (not a model of kesterite) with mechanism terms, failures, device-only losses, and an `interaction` switch |
| `lab.py` | Virtual furnace: shared trajectory per run, furnace-run random effect, heteroscedastic film noise, failures; confirmation runs outside the budget |
| `strategies.py` | OVAT control (replicated, line-searching, step-halving) and the loop (GP with learned noise, GP failure classifier, EI x P(survive), Kriging-believer slot filling, replicate-first, periodic incumbent confirmation, LCB recommendation) |
| `strategies.DeviceAwareGPBO` | A8: anchor devices (2 every 5 runs, 6 cells each) feed a GP of the device-only loss; acquisition and recommendation on predicted device Voc |
| `m0.py` | M0 support: C1 power indexed by noise *as M0 measures it* (literature recipe, both noise-shape assumptions); nested runs × films × spots variance components; go/no-go operating characteristics |
| `campaign.py` | Campaign driver, confirmation test (one-sided Welch at alpha 0.05), power tables, winner's-curse statistics |

## Read before quoting numbers
* The emulator is a benchmark surface. Its coefficients are choices, set so the
  literature recipe sits a few tens of mV of QFLS below the optimum
  (`VirtualKesterite().headroom_mev()`) with the headroom
  spread across several mechanisms. Results are conditional on that structure;
  the separable variant (`interaction=0`) is there to show how much they depend on it.
* Noise magnitudes are the unknowns M0 exists to measure. The sweep spans
  5-30 meV film-to-film, with a furnace-run effect at half that and 3 meV of
  measurement scatter.
* The QFLS optimum is not the device optimum (excess Se thickens MoSe2, which
  QFLS cannot see). Anchor devices are reported separately for that reason.
* Real C1 data replaces the emulator through `Lab.furnace_run`; the strategies
  and the schema do not change.

## Repository layout
* `out/` holds the summaries and charts behind the memos. The raw per-campaign
  results (`results.jsonl`, `m0_lookup.jsonl`, about 4.5 MB) are not committed;
  every campaign is seeded, so the two commands above regenerate them.
* `docs/` holds dated snapshots of the memos. The live copies are in the
  Materials Discovery Lab project (`claude/mdl_loop_v0.1_results.md`,
  `claude/mdl_loop_v0.2_results.md`, `claude/M0_noise_floor_design.md`).
  Correct a snapshot by dated addendum, not by editing its body.
* This package is independent of `src/omi` and of `mdl-engine`, and the root
  test suite does not collect it. Run its tests from this directory.
