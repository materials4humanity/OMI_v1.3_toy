# REPRODUCE.md — from a clean clone to every headline number

This file lets a reader go from a fresh clone to each headline result **without
reading source**. Every command below was executed in a fresh virtualenv against
this branch before this file was written; the outputs quoted are what that run
produced. Where a result comes from a script rather than a test, the script is
named.

Nothing here runs the network at runtime, trains a neural operator, or requires a
GPU. `torch` is an optional extra and is **not** needed for anything in this file.

---

## 0. Environment

- Python **≥ 3.11** (verified on 3.11.15).
- Dependencies are pinned in `pyproject.toml`: `numpy==2.1.3`, `scipy==1.14.1`,
  and — under the `dev` extra — `pytest==8.3.3`, `mypy==1.13.0`.
- Everything is deterministic under fixed seeds (see §7).

## 1. Clone, install, smoke-test

```bash
git clone <repo-url> omi && cd omi
git checkout claude/omi-m0-scaffolding-96j5cj

python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'          # ~17 s from wheels; numpy, scipy, pytest, mypy
```

Confirm the package imports and the suite runs:

```bash
python -c "import omi, omi_domains; print('ok')"     # -> ok
pytest -q                                            # ~560 s
```

Expected tail:

```
357 passed, 2 skipped in ~560s
```

The two skips are intentional (torch-optional paths with a numpy fallback; the
fallback itself is tested). Type-checking and lints:

```bash
mypy --config-file pyproject.toml src tests   # cold ~30 s, warm <1 s (on-disk .mypy_cache)
# -> Success: no issues found in 139 source files

pytest tests/lint -q                          # ~1 s -> 13 passed
```

> **Ordering caveat that will bite you if ignored.** `build/observations.json` is a
> git-ignored artifact **regenerated from scratch by every `pytest` invocation,
> including a partial one**. Running `pytest tests/lint` (13 tests) after a full run
> overwrites the 306-observation record with ~a dozen. Never judge the observation
> record or the audit gate (§6) except immediately after a **full** `pytest -q`.
> `scripts/check_audit_gate.sh` exists precisely to enforce this.

---

## 2. Headline: the M11.5 refutation (the paper's central negative result)

**Claim.** On an accumulated-strain hold-out gated in advance for discrimination,
declared constitutive forms buy no extrapolation reach: every declared-form
contestant is worse than a free-form operator, and an unchanged tabular baseline
beats them all.

```bash
python scripts/run_m11_5_extrapolation.py        # ~22 s
```

Expected (held-out RMSE, pooled over the held-out strains — the registered
criterion):

```
1_free_form                                       5.06181   0.09689
2_correct_form                                    8.10280   0.11412
3a_missing_mechanism                             69.54710   1.47032
3b_missing_dependence                             7.56449   0.73309
4_tabular_RidgeRegressor                         24.31240   0.38165
4_tabular_GradientBoostedTreeRegressor            3.26607   0.04182
```

and the verdict block:

```
1_free_form - 3a_missing_mechanism   gap -64.48528  tau 0.33089  WORSE
1_free_form - 3b_missing_dependence  gap  -2.50268  tau 0.32181  WORSE
1_free_form - 2_correct_form         gap  -3.04098  tau 0.31484  WORSE   (ceiling)
best baseline held-out RMSE: 3.2661 (4_tabular_GradientBoostedTreeRegressor)
NO BENEFIT on Generator C — and unlike M11.4 this null is INFORMATIVE.
```

The full narrative is `docs/M11.5-EXTRAPOLATION.md`; the pre-registration that
fixed the thresholds this script imports (and does not recompute) is
`docs/M11.5-PREREGISTRATION.md`, committed at `97621ac` before the sweep existed.

The same run also asserts the result structurally, if you prefer a pass/fail:

```bash
pytest tests/test_m11_5_extrapolation.py -q      # ~5 s -> 6 passed
```

## 3. Headline: the misspecification asymmetry

**Claim.** A missing *dependence* costs almost nothing; a missing *mechanism* is
catastrophic. This is the practitioner-facing result.

From the same `run_m11_5_extrapolation.py` output:

```
3a (missing mechanism) - 3b (missing dependence) = +61.98260
minimum effect worth catching = 0.62957
-> DIVERGENT: the benefit depends on WHICH kind
```

`+61.98` is measured against the **declared minimum effect of 0.63** (registered at
`97621ac`). It is a different comparison from the −64.49 gap in §2, which is
free-form-vs-3a against that comparison's own threshold τ = 0.331 — do not cross
the two. The per-strain curve shows 3a growing without bound (11.5 → 30.4 → 56.2 →
123.0) because it cannot saturate; the assertion is pinned in
`tests/test_m11_5_extrapolation.py::test_a_missing_mechanism_is_far_worse_than_a_missing_dependence`.

## 4. Headline: the error-cancellation diagnostic (E-42)

**Claim.** The declared forms do not lose through ignorance of their own physics.
Scored against a truth with the withheld term removed, the ranking inverts: the
correct form is *exact* and the winner is worst-but-one.

Same script, the diagnostic block:

```
contestant                                vs full truth   vs withheld-free
1_free_form                                     4.9652             3.7752
2_correct_form                                  8.2037             0.0000
4_tabular_GradientBoostedTreeRegressor          3.3052             8.5214
    withheld term magnitude on this draw: 6.5636
```

The winner (GBT) is first on the registered criterion and fourth against the
withheld-free truth; its extrapolation error (signed bias ≈ −7.49) nearly cancels
the withheld term (≈ −6.56). Pinned in
`tests/test_m11_5_extrapolation.py::test_the_declared_forms_lose_by_cancellation_not_by_ignorance`.
Filed as `docs/V1.4-EDITS.md` E-42.

## 5. Headline: the M11.4 vacuous-axis diagnosis (E-39/E-41)

**Claim.** M11.4 held out an axis (strain rate) along which the declared form makes
no differing prediction, satisfying every Spec §9.3 requirement while unable to
discriminate. The gate that catches this refuses M11.4's axis and admits M11.5's.

```bash
python scripts/run_m11_4_extrapolation.py        # ~4 min (8 seeds, unvectorised)
```

The diagnostic block shows every contestant's held-out error is the withheld term
itself, and — against a drag-free truth — the *free-form* arm is best (0.0773)
while the correct declared form is 0.3390: the declared form has nothing to say
along that axis. The gate's retro-validation is the fast path:

```bash
pytest tests/test_holdout_discrimination.py -q   # ~50 s -> 5 passed
```

which asserts the gate returns `INERT_AXIS` on M11.4's strain-rate axis (axis
signal exactly 0.000, all three criteria failing) and `DISCRIMINATING` on M11.5's
accumulated-strain axis (divergence 14.57 against a bar of 2.0). Narratives:
`docs/M11.4-EXTRAPOLATION.md`, `docs/V1.4-EDITS.md` E-39 and E-41.

## 6. Headline: E-38's validity catch (a real modelling error, no oracle)

**Claim.** The declared-validity-range mechanism caught Koistinen–Marburger being
applied at the soak temperature — 5.71× outside its declared window — on first
application, with the correct action attached and no oracle involved.

```bash
pytest "tests/test_flagship_constitutive.py::test_the_report_catches_koistinen_marburger_applied_at_the_soak_temperature" -q
# <1 s -> 1 passed
```

Narrative: `docs/V1.4-EDITS.md` E-38 (a Confirmation, not a defect).

## 7. Headline: the audit-gate invariance across all M11 changes

**Claim.** Every observation recorded before M11 touched `src/omi/` is byte-identical
today; M11 only *added* observations. This is what licenses calling the extension
composition-over-modification (ADR-042).

The baseline — 267 observations from a full run at `57f7db8` (the last commit
before `src/omi/` was touched by the proposed-v1.4 extension) — is committed at
`audit/pre-m11-observations.json`, so the check is one step from a clean clone:

```bash
scripts/check_audit_gate.sh audit/pre-m11-observations.json \\
    audit/e53-label-changes.json                               # ~570 s (runs the full suite)
```

Expected:

```
baseline observations : 267
current observations  : 306
MISSING from current  : 0
CHANGED vs baseline   : 0
newly added (expected): 39
AUDIT-PRESERVATION GATE: PASS
```

The committed baseline is authentic: it was regenerated from a fresh checkout of
`57f7db8` and is byte-identical to the copy taken during M11. To reproduce the
baseline itself rather than trust the committed file:

```bash
git worktree add --detach /tmp/omi-57f7db8 57f7db8
python3 -m venv /tmp/omi-57f7db8/.venv
/tmp/omi-57f7db8/.venv/bin/pip install -e '/tmp/omi-57f7db8[dev]'
(cd /tmp/omi-57f7db8 && .venv/bin/python -m pytest -q)   # -> 251 passed, 2 skipped
# /tmp/omi-57f7db8/build/observations.json is the 267-observation baseline
git worktree remove --force /tmp/omi-57f7db8
```

## 8. Determinism

Every stochastic path takes an explicit `numpy.random.Generator` seeded from a
fixed base (CLAUDE.md §7); there is no reliance on global RNG state. Two
consequences a reader can check:

- **Two full runs produce byte-identical observations.** After a `pytest -q`,
  `build/observations.json` from one run equals the next, field for field
  (verified: 306 observations, identical across two runs).
- The scripted form, comparing suite *stdout* across two runs, is:

  ```bash
  scripts/check_determinism.sh        # runs pytest twice, diffs -> "Determinism check passed"
  ```

A discrepancy between two runs would mean a stochastic path escaped its seeded
generator — that is a defect in a framework about uncertainty quantification, and
CI runs the suite twice to catch it.

## 9. What each headline costs, at a glance

| Result | Command | Runtime | Expected |
|---|---|---|---|
| install | `pip install -e '.[dev]'` | ~17 s | (wheels) |
| full suite | `pytest -q` | ~560 s | 357 passed, 2 skipped |
| types | `mypy --config-file pyproject.toml src tests` | ~30 s cold | Success, 139 files |
| lints | `pytest tests/lint -q` | ~1 s | 13 passed |
| M11.5 refutation + asymmetry + cancellation | `python scripts/run_m11_5_extrapolation.py` | ~22 s | §2–§4 above |
| M11.5 structural assertions | `pytest tests/test_m11_5_extrapolation.py -q` | ~5 s | 6 passed |
| M11.4 vacuous-axis diagnosis | `python scripts/run_m11_4_extrapolation.py` | ~4 min | §5 above |
| hold-out gate retro-validation | `pytest tests/test_holdout_discrimination.py -q` | ~50 s | 5 passed |
| E-38 validity catch | `pytest "…::test_the_report_catches_koistinen_marburger_applied_at_the_soak_temperature" -q` | <1 s | 1 passed |
| audit-gate invariance | `scripts/check_audit_gate.sh audit/pre-m11-observations.json audit/e53-label-changes.json` | ~570 s | PASS: 0 undeclared, 4 declared label changes, 2 retirements, no numeric movement |
| determinism | `scripts/check_determinism.sh` | ~220 s | passed |
| v1.5 Part 5(1) figures | `python scripts/run_v15_part5_1.py` | ~10 min | `docs/V1.5-PART5-1.md` |
| Part 5(1) §5.1 diagnostic trace | `pytest tests/oracles/test_contrast_diagnostic_trace.py -q` | ~60 s | 7 passed |
| Part 5(1) §5.2 statistic dry-run | `pytest tests/oracles/test_statistic_dry_run.py -q` | ~115 s | 5 passed |
| Part 5(1) §5.3 E-47 measurement | `pytest tests/oracles/test_parameter_ridge.py -q` | ~33 s | 6 passed |
| Part 5(2) §5.2a E-48 triage | `pytest tests/oracles/test_share_threshold_degeneracy.py -q` | ~4 s | 6 passed |
| Part 5(2) SDL declaration | `pytest tests/test_sdl_declaration.py -q` | <1 s | 12 passed |
| E-53 fork comparison | `pytest tests/oracles/test_e53_option_comparison.py -q` | ~12 s | 6 passed |
| E-54 settled (decaying sensitivity) | `pytest tests/oracles/test_known_decaying_sensitivity.py -q` | ~4 s | 6 passed |

The eight v1.5 Part 5(1), 5(2) and E-53-milestone rows were added after this file's fresh-virtualenv run and were
verified in the development environment rather than in a clean one — stated rather than
folded in, since the rest of the table carries the stronger guarantee. They add no
dependency, so the difference is a claim about what was checked, not about what would
work. Their results are written up in `docs/V1.5-PART5-1.md`, `docs/V1.5-PART5-2.md` and
`docs/V1.5-E53-DECISION.md` and `docs/V1.5-E53-FIX.md`, all live documents.

**The audit gate now takes a second argument.** ADR-061 changed what the observed/inferred
label means, so four label-valued observations moved and two numeric label-filtered ones were
retired. `audit/e53-label-changes.json` enumerates all six with before/after values and reasons;
the gate reports them separately, refuses a numeric *change*, requires a retirement to name a
present replacement, and still FAILS on anything undeclared (ADR-062).

## 10. If something does not reproduce

- **A number differs in the last digit(s).** Check your numpy/scipy versions match
  the pins; BLAS differences can perturb the far decimals of the sweep figures.
  The *verdicts* (WORSE/EFFECT, PASS/FAIL, DIVERGENT/comparable) are robust to this
  and are what the assertions test — the qualitative claims, never the frozen
  figures (CLAUDE.md §7).
- **The audit gate reports MISSING or CHANGED.** That is the signal ADR-042 is
  built to raise: a pre-existing observation moved, so a change claimed to be inert
  was not. It is a finding, not a nuisance — do not re-baseline to silence it.
- **`observations.json` looks tiny or the gate FAILs right after a lint run.** You
  ran a partial suite last; re-run the full `pytest -q` (or just use
  `scripts/check_audit_gate.sh`, which runs the full suite for you).
