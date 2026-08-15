"""The `observe()` staleness checker, tested against constructed cases (`docs/V1.4-EDITS.md`
E-59; ADR-072).

**Why this file tests the checker rather than the record.** The record
(`build/observations.json`) is written at `pytest_sessionfinish`, so a test reading it during the
run reads the *previous* run's file — the ordering hazard `scripts/check_audit_gate.sh` exists to
prevent, and one this repository has been bitten by twice. The live record is instead checked at
record time by the `observe` fixture itself, which raises. What is left to test here is the
checker's own judgement, and it is tested the way every estimator in this repository is
(CLAUDE.md §7): against cases whose right answer is fixed by construction.

**The regression case is E-59's own instance**, verbatim from the entry: a bound reading
`"proposed-v1.5"` beside a value reading `"proposed-decision-extension"`, which the full suite
passed over at 374 tests before and after and which `grep` found by accident.
"""

from __future__ import annotations

from typing import Any

from tests.observation_bounds import check_observation, check_observations


def _observation(value: Any, bound: str) -> dict[str, Any]:
    return {"test": "constructed", "name": "q", "value": value, "units": None, "bound": bound}


# --- the historical instance -------------------------------------------------


def test_e59s_own_instance_is_caught() -> None:
    """**The regression case.** E-59's measured divergence, reproduced exactly: ADR-067 renamed
    the enum member, the recorded value followed, the bound did not, and nothing noticed.
    """
    rule, violation = check_observation(
        _observation("proposed-decision-extension", "proposed-v1.5")
    )
    assert rule == "bare_literal"
    assert violation is not None
    assert "proposed-v1.5" in violation.bound
    assert "proposed-decision-extension" in violation.detail


def test_the_same_observation_passes_once_the_bound_is_updated() -> None:
    """The other half of the regression: the checker must accept the *repaired* form, or it
    would force the bound to be deleted rather than corrected."""
    rule, violation = check_observation(
        _observation("proposed-decision-extension", "proposed-decision-extension")
    )
    assert rule == "bare_literal"
    assert violation is None


# --- rule 1: relational numerics --------------------------------------------


def test_relational_numeric_bounds_are_evaluated() -> None:
    """A bound like `"< 0.05"` becomes executable rather than decorative."""
    assert check_observation(_observation(0.01, "< 0.05"))[1] is None
    assert check_observation(_observation(0.3, "< 0.05"))[1] is not None
    assert check_observation(_observation(14.44, "> 1.0"))[1] is None
    assert check_observation(_observation(0.5, "> 1.0"))[1] is not None
    assert check_observation(_observation(1, "== 1"))[1] is None
    assert check_observation(_observation(2, "== 1"))[1] is not None


def test_much_less_than_is_read_as_the_plain_inequality() -> None:
    """`<<` is this repository's shorthand (an erased-subspace gain recorded as `"<< 1"`).
    Checked as `<`: *how much* smaller is a judgement the bound does not quantify, and inventing
    a factor would be the improvisation CLAUDE.md §4 forbids."""
    assert check_observation(_observation(1e-3, "<< 1"))[1] is None
    assert check_observation(_observation(5.0, "<< 1"))[1] is not None


def test_a_bare_number_is_read_as_an_equality_claim() -> None:
    """Bounds are written as bare numbers throughout (`"0"`, `"8"`), which is an equality claim
    with the operator left implicit."""
    assert check_observation(_observation(0, "0 -- nothing moved"))[1] is None
    assert check_observation(_observation(3, "0 -- nothing moved"))[1] is not None


def test_booleans_are_not_treated_as_numbers() -> None:
    """`True`/`False` are categorical readings here, not measured quantities — the same
    convention `scripts/check_audit_gate.sh` uses when refusing a numeric declared exception.
    Without this, `True` would silently satisfy `"== 1"`."""
    rule, violation = check_observation(_observation(True, "== 1"))
    assert rule is None and violation is None


# --- rule 2/3 boundary: literal claim versus prose that quotes ---------------


def test_a_quoted_literal_must_appear_in_the_value() -> None:
    assert check_observation(_observation(["support"], "== ('support',)"))[1] is None
    assert check_observation(_observation(["promoter"], "== ('support',)"))[1] is not None


def test_prose_that_merely_quotes_a_word_is_skipped_not_flagged() -> None:
    """**Triaged in on the lint's first run, and the reason the rule is scoped this way.**

    The first run flagged `"best is the 'good' candidate"` against a value of `[0.0, 1.0]` —
    a false positive: the quoted word names a candidate in a sentence, it is not a claim that
    the string `good` is in the value. The discriminator is what survives removing the quoted
    spans: punctuation alone means a literal claim, a sentence means prose. Fixed by narrowing
    the rule rather than by excepting the case, per `docs/ARITY-REDESIGN-BRIEF.md` §5's
    instruction to triage the first run's failures rather than suppress them.
    """
    rule, violation = check_observation(_observation([0.0, 1.0], "best is the 'good' candidate"))
    assert rule is None and violation is None


def test_a_bound_referencing_other_expressions_is_skipped() -> None:
    """`"ratios['sensor_b'] > 10 * ratios['sensor_a_again']"` is a real bound in this suite. It
    is a claim about two *other* recorded quantities, not about this value, and the checker
    cannot evaluate it — so it is skipped rather than guessed at."""
    rule, violation = check_observation(
        _observation([1.0, 20.0], "ratios['sensor_b'] > 10 * ratios['sensor_a_again']")
    )
    assert rule is None and violation is None


def test_prose_bounds_are_skipped() -> None:
    for bound in ("narrative only", "all six Core §7.2-named items are True", "each > 0"):
        rule, violation = check_observation(_observation(1.0, bound))
        assert violation is None, f"{bound!r} should not be flagged"


def test_commentary_after_a_dash_is_not_part_of_the_bound() -> None:
    """This repository writes `"0 -- no verdict moved"` throughout. The checkable claim is the
    part before the dash; treating the whole string as prose would discard most of the
    coverage the lint has."""
    rule, _ = check_observation(_observation(0, "0 -- no pre-existing fillability verdict moved"))
    assert rule == "relational_numeric"


# --- coverage is a reported quantity, not an implied one ---------------------


def test_the_report_states_its_own_coverage() -> None:
    """**A checker whose coverage is unstated reads as a guarantee it does not give**, which is
    the same class of defect E-59 records. `BoundCheckReport` carries the per-rule checked
    counts and the skipped total so the blind spot is visible."""
    report = check_observations(
        [
            _observation(0.01, "< 0.05"),
            _observation("x", "x"),
            _observation(1.0, "narrative only"),
        ]
    )
    assert report.total == 3
    assert report.checkable == 2
    assert report.skipped == 1
    assert report.checked["relational_numeric"] == 1
    assert report.checked["bare_literal"] == 1
    assert 0.0 < report.coverage < 1.0
    assert report.violations == ()
