"""The `observe()` staleness checker — `docs/V1.4-EDITS.md` E-59, scheduled by
`docs/ARITY-REDESIGN-BRIEF.md` §5 and built at ADR-072.

**The defect it closes.** `observe(name, value, bound)` records what was measured, what it
came out as, and the bound it was checked against. The third is free text: nothing parses it,
nothing compares it to the value, no assertion reads it. So the two drift apart and every
check still passes. E-59's measured instance: a bound reading `"proposed-v1.5"` survived
ADR-067's rename beside a value reading `"proposed-decision-extension"`, and the suite passed
at 374 before and after. It was found by `grep`, sweeping for something else.

**What this module does and deliberately does not do.** It refuses to guess. A bound is
checked only when it is *mechanically* a claim about the value — a relational numeric, a bare
literal, or a quoted literal — and every other bound is **skipped and counted**, so the
lint's own coverage is a reported quantity rather than an implied one. A checker that silently
examined 5% of bounds while reading as a guarantee would be the same class of defect E-59
records (CLAUDE.md §7's "an assertion that pins a bound but discards the number").

See :data:`RULES` for the three rules and ADR-072 for why each is scoped as it is.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, TypeGuard

RULES = ("relational_numeric", "bare_literal", "quoted_literal")
"""The three checkable forms. Named so :class:`BoundCheckReport` can report coverage per rule
rather than as one aggregate — a lint whose coverage is one number cannot say which kind of
bound it is blind to (ADR-072)."""

_PROSE_SEPARATORS = ("--", "—", " -- ")
"""Everything after one of these is commentary, not a bound. This repository writes bounds like
``"0 -- no pre-existing fillability verdict moved"`` throughout, so the checkable claim is the
part before the dash and the rest is deliberately unparsed."""

_RELATIONAL = re.compile(
    r"^(==|!=|<<|>>|<=|>=|<|>)\s*(-?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)$"
)
_QUOTED = re.compile(r"'([^']*)'|\"([^\"]*)\"")
_NUMERIC = re.compile(r"^-?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?$")
_ALPHABETIC = re.compile(r"[A-Za-z]")

_RELATIVE_TOLERANCE = 1e-9
"""For float comparison only. Tight because a bound and a value that were genuinely compared
agree to within representation error; a loose tolerance would let a real divergence pass as a
rounding difference."""


@dataclass(frozen=True)
class BoundViolation:
    """One observation whose stated bound contradicts its recorded value (E-59)."""

    test: str
    name: str
    rule: str
    value: Any
    bound: str
    detail: str

    def __str__(self) -> str:
        return (
            f"{self.test}::{self.name} [{self.rule}] "
            f"bound {self.bound!r} vs value {self.value!r}: {self.detail}"
        )


@dataclass(frozen=True)
class BoundCheckReport:
    """Violations plus **coverage**, because the second is what makes the first meaningful."""

    violations: tuple[BoundViolation, ...]
    checked: dict[str, int]
    skipped: int
    total: int

    @property
    def checkable(self) -> int:
        return sum(self.checked.values())

    @property
    def coverage(self) -> float:
        """Fraction of observations whose bound was mechanically checkable. **Reported, never
        asserted against a target**: raising it means writing bounds to please a lint, which is
        the wrong direction of fit."""
        return self.checkable / self.total if self.total else 0.0


def _checkable_part(bound: str) -> str:
    text = bound
    for separator in _PROSE_SEPARATORS:
        text = text.split(separator)[0]
    return text.strip()


def _is_number(value: Any) -> TypeGuard[int | float]:
    """Bools excluded: `True`/`False` are categorical readings in this repository's
    observations, not measured quantities (the same convention `scripts/check_audit_gate.sh`
    applies when refusing a numeric declared exception)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _relational_holds(operator: str, left: float, right: float) -> bool:
    if operator == "==":
        return math.isclose(left, right, rel_tol=_RELATIVE_TOLERANCE, abs_tol=0.0) or left == right
    if operator == "!=":
        return not math.isclose(left, right, rel_tol=_RELATIVE_TOLERANCE, abs_tol=0.0)
    # `<<` and `>>` are this repository's shorthand for "much less/greater than" (e.g. an
    # erased-subspace gain recorded as `<< 1`). Checked as the plain inequality: how much
    # smaller is a judgement the bound does not quantify, and inventing a factor here would
    # be the improvisation CLAUDE.md §4 forbids.
    if operator in ("<", "<<"):
        return left < right
    if operator in (">", ">>"):
        return left > right
    if operator == "<=":
        return left <= right
    return left >= right


def check_observation(observation: dict[str, Any]) -> tuple[str | None, BoundViolation | None]:
    """Check one observation's bound against its value (E-59; ADR-072).

    Returns ``(rule_applied, violation)``. ``rule_applied`` is ``None`` when the bound is not
    mechanically a claim about the value — prose, a reference to another expression, or a
    comparison this checker declines to interpret. **Skipping is the default and is not a
    failure**: the alternative is guessing what a sentence asserts.
    """
    bound = str(observation.get("bound", ""))
    value = observation.get("value")
    checkable = _checkable_part(bound)
    if not checkable:
        return None, None

    def violation(rule: str, detail: str) -> BoundViolation:
        return BoundViolation(
            test=str(observation.get("test", "?")),
            name=str(observation.get("name", "?")),
            rule=rule,
            value=value,
            bound=bound,
            detail=detail,
        )

    # Rule 1 — a relational claim about a number.
    relational = _RELATIONAL.match(checkable)
    if relational is not None:
        operator, literal = relational.group(1), relational.group(2)
        if not _is_number(value):
            return None, None
        if not _relational_holds(operator, float(value), float(literal)):
            return "relational_numeric", violation(
                "relational_numeric", f"{value} {operator} {literal} is false"
            )
        return "relational_numeric", None

    # Rule 3 (before rule 2, because a quoted literal may sit inside `== (...)`) — every
    # literal the bound quotes must appear in the value.
    #
    # Applied ONLY when the bound is structurally a literal claim, not prose that happens to
    # quote a word. The discriminator is what survives removing the quoted spans: for
    # `== ('support',)` that is `== (,)`, punctuation alone; for `best is the 'good' candidate`
    # it is `best is the candidate`, which is a sentence *about* a candidate rather than an
    # assertion that the string `good` is in the value. Triaged in on the lint's first run,
    # which flagged exactly that bound against a value of `[0.0, 1.0]` (ADR-072).
    quoted = [a or b for a, b in _QUOTED.findall(checkable)]
    if quoted and not _ALPHABETIC.search(_QUOTED.sub("", checkable)):
        haystack = json.dumps(value, default=str)
        missing = [literal for literal in quoted if literal and literal not in haystack]
        if missing:
            return "quoted_literal", violation(
                "quoted_literal", f"quoted literal(s) {missing} absent from the recorded value"
            )
        return "quoted_literal", None

    # Rule 2 — the bound *is* a bare literal naming the expected value. E-59's own instance.
    bare = checkable[2:].strip() if checkable.startswith("==") else checkable
    if bare and not _NUMERIC.match(bare) and " " not in bare and isinstance(value, str):
        if bare != value:
            return "bare_literal", violation(
                "bare_literal", f"bound names {bare!r} but the recorded value is {value!r}"
            )
        return "bare_literal", None

    # A bare numeric with no operator, e.g. `"0"` or `"8"`, read as an equality claim.
    if _NUMERIC.match(bare) and _is_number(value):
        if not _relational_holds("==", float(value), float(bare)):
            return "relational_numeric", violation(
                "relational_numeric", f"bound states {bare} but the recorded value is {value}"
            )
        return "relational_numeric", None

    return None, None


def check_observations(observations: list[dict[str, Any]]) -> BoundCheckReport:
    """Check a whole observation record (E-59; ADR-072)."""
    violations: list[BoundViolation] = []
    checked = {rule: 0 for rule in RULES}
    skipped = 0
    for observation in observations:
        rule, violation = check_observation(observation)
        if rule is None:
            skipped += 1
            continue
        checked[rule] += 1
        if violation is not None:
            violations.append(violation)
    return BoundCheckReport(
        violations=tuple(violations),
        checked=checked,
        skipped=skipped,
        total=len(observations),
    )
