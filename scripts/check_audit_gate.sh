#!/usr/bin/env bash
# The audit-preservation gate (docs/ROADMAP.md M11.1; ADR-042, ADR-062, ADR-069,
# docs/DECISIONS.md), as one step so it cannot be run in the wrong order.
#
# WHY THIS SCRIPT EXISTS. `build/observations.json` is regenerated from scratch by
# every test-suite run, including a partial one — so running `pytest tests/lint`
# after the full suite silently replaces 279 observations with 0, and a gate check
# made at that moment reports a catastrophic FAIL that is entirely an artefact of
# the ordering. That happened twice during M11 before this script existed. The
# baseline comparison must always be made immediately after a FULL run, which is
# what this enforces.
#
# Usage:
#   scripts/check_audit_gate.sh <baseline.json> [declared-exceptions.json ...]
#
# KEYING (ADR-069). Observations are compared by the pair (test, name), not by
# name alone. `docs/V1.4-EDITS.md` E-60 found that keying on name alone silently
# dropped 44 of the v1.3-era baseline's 267 rows from comparison, because 17 names
# are each recorded by more than one test and a `{name: row}` dict keeps only the
# last one written. `(test, name)` is unique in every baseline and every full-suite
# run checked so far; if a future baseline ever repeats a `(test, name)` pair this
# script FAILS LOUDLY rather than silently dropping one of them, which is the
# opposite failure mode from the one being fixed.
#
# DECLARED EXCEPTIONS. An approved change to what a reported LABEL means must be able to
# move label-valued observations without either blocking the change or switching the gate
# off. The third option is to enumerate every moved observation in advance, with its before
# and after values and its reason -- see audit/e53-label-changes.json (ADR-061). The gate
# reports declared movements separately and still FAILS on any undeclared one, so nothing
# changes silently. And it REFUSES an exception whose value is numeric: that is the
# mechanical form of the claim such a change rests on, that a label moved and a computed
# quantity did not.
#
# Declared exceptions are still named by NAME alone (ADR-061's format is unchanged), on
# the reasoning that a criterion change is usually about what a NAME means wherever it is
# reported, not about one particular test. If a declared name resolves to more than one
# (test, name) pair in the baseline the exception is AMBIGUOUS and the gate refuses it
# rather than guessing which occurrence was meant.
#
# VERSIONED BASELINES (ADR-069). ADR-062's own stated trigger has fired: a second
# declared-exception file for an unrelated change is the signal to move from an
# accumulating exception list to a baseline per criterion generation. `audit/baselines/`
# holds one frozen file per generation (`audit/BASELINES.md` names each one and the
# criterion it was produced under); this script always compares against exactly one
# baseline file, named on the command line, and never mixes generations.
#
# The baseline is a copy of build/observations.json taken from a full-suite run at
# the commit whose results are being preserved. `audit/baselines/v13-items7.json` is
# the v1.3, seven-item-interface generation, frozen at 57f7db8 -- the last commit
# before src/omi/ was touched by the proposed constitutive extension.

set -euo pipefail

BASELINE="${1:?usage: check_audit_gate.sh <baseline.json> [declared-exceptions.json ...]}"
shift
PYTHON="${PYTHON:-.venv/bin/python}"

if [ ! -f "$BASELINE" ]; then
    echo "baseline not found: $BASELINE" >&2
    exit 2
fi

echo "running the FULL suite (partial runs invalidate the comparison)..."
"$PYTHON" -m pytest -q

"$PYTHON" - "$BASELINE" "$@" <<'PY'
import json
import sys

baseline = json.load(open(sys.argv[1]))
current = json.load(open("build/observations.json"))

declared_changed: dict[str, dict[str, object]] = {}
declared_retired: dict[str, dict[str, object]] = {}
for path in sys.argv[2:]:
    document = json.load(open(path))
    for entry in document.get("changed", []):
        declared_changed[entry["name"]] = {**entry, "source": path}
    for entry in document.get("retired", []):
        declared_retired[entry["name"]] = {**entry, "source": path}


def is_numeric(value: object) -> bool:
    """Whether a declared exception is excepting a NUMBER rather than a label.

    Bools are excluded: `True`/`False` are categorical readings in this repository's
    observations, not measured quantities.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(is_numeric(v) for v in value)
    if isinstance(value, dict):
        return any(is_numeric(v) for v in value.values())
    return False


def key_of(observation: dict[str, object]) -> tuple[str, str]:
    """`(test, name)` -- ADR-069. Never `name` alone: E-60 found 44 of 267 baseline
    rows silently dropped from comparison under the old `{name: row}` keying, because
    17 names are each recorded by more than one test."""
    return (str(observation["test"]), str(observation["name"]))


before = {key_of(o): o for o in baseline}
after = {key_of(o): o for o in current}

if len(before) != len(baseline):
    print(
        f"FATAL: baseline has {len(baseline)} rows but only {len(before)} distinct "
        "(test, name) pairs -- a single test recorded the same observation name twice. "
        "This script refuses to guess which occurrence is meant."
    )
    raise SystemExit(2)
if len(after) != len(current):
    print(
        f"FATAL: this run produced {len(current)} rows but only {len(after)} distinct "
        "(test, name) pairs -- a single test recorded the same observation name twice."
    )
    raise SystemExit(2)

# Declared exceptions are still named by NAME alone (ADR-061's format). Resolve each
# declared name to the (test, name) key(s) it denotes in the relevant file; refuse if
# a name is ambiguous there, rather than silently picking one occurrence.
def names_index(rows: dict[tuple[str, str], dict[str, object]]) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = {}
    for key in rows:
        index.setdefault(key[1], []).append(key)
    return index


before_by_name = names_index(before)
after_by_name = names_index(after)

ambiguous_exceptions = sorted(
    name
    for name in set(declared_changed) | set(declared_retired)
    if len(before_by_name.get(name, [])) > 1
)

missing = sorted(set(before) - set(after))
changed = sorted(k for k in before if k in after and before[k] != after[k])
added = sorted(set(after) - set(before))


def resolve_declared(name: str, index: dict[str, list[tuple[str, str]]]) -> tuple[str, str] | None:
    keys = index.get(name, [])
    return keys[0] if len(keys) == 1 else None


declared_changed_keys = {
    resolve_declared(name, before_by_name): entry
    for name, entry in declared_changed.items()
    if resolve_declared(name, before_by_name) is not None
}
declared_retired_keys = {
    resolve_declared(name, before_by_name): entry
    for name, entry in declared_retired.items()
    if resolve_declared(name, before_by_name) is not None
}

undeclared_missing = [k for k in missing if k not in declared_retired_keys]
undeclared_changed = [k for k in changed if k not in declared_changed_keys]
declared_but_unmoved = sorted(
    (set(declared_changed_keys) - set(changed)) | {k for k in declared_retired_keys if k in after},
    key=lambda k: (k[1], k[0]),
)
numeric_exceptions = sorted(
    name for name, entry in declared_changed.items() if is_numeric(entry.get("after"))
)
retirements_without_replacement = sorted(
    name for name, entry in declared_retired.items() if not entry.get("replaced_by")
)
missing_replacements = sorted(
    f"{name} -> {entry['replaced_by']}"
    for name, entry in declared_retired.items()
    if entry.get("replaced_by") and entry["replaced_by"] not in {k[1] for k in after}
)

print()
print(f"baseline observations : {len(baseline)}")
print(f"current observations  : {len(current)}")
print(f"declared exceptions   : {len(declared_changed)} changed, {len(declared_retired)} retired")
print(f"MISSING from current  : {len(missing)} ({len(undeclared_missing)} undeclared)")
for key in missing:
    tag = "DECLARED" if key in declared_retired_keys else "UNDECLARED"
    print(f"    - [{tag}] {key[1]}  ({key[0]})")
print(f"CHANGED vs baseline   : {len(changed)} ({len(undeclared_changed)} undeclared)")
for key in changed:
    tag = "DECLARED" if key in declared_changed_keys else "UNDECLARED"
    print(f"    ~ [{tag}] {key[1]}: {before[key]['value']} -> {after[key]['value']}  ({key[0]})")
print(f"newly added (expected): {len(added)}")
print()

failures = []
if ambiguous_exceptions:
    failures.append(
        "Declared exception name(s) match MORE THAN ONE (test, name) pair in the baseline: "
        + ", ".join(ambiguous_exceptions) + "\n"
        "A criterion change must name which occurrence it means, or the gate cannot tell "
        "whether the right one moved."
    )
if undeclared_missing or undeclared_changed:
    failures.append(
        "A pre-existing observation moved WITHOUT being declared. Per ADR-042 this is the\n"
        "signal that the change was NOT as inert as claimed: reopen the ADR rather than\n"
        "re-baselining, or declare the movement with its reason if it is intended."
    )
if numeric_exceptions:
    failures.append(
        "A declared CHANGE excepts a NUMERIC observation: " + ", ".join(numeric_exceptions) + "\n"
        "The change mechanism exists for label-valued observations only. A computed quantity\n"
        "taking a new value under its old name is not a relabelling and must not be waved\n"
        "through as one -- retire the name and reissue under a new one instead."
    )
if retirements_without_replacement:
    failures.append(
        "Retirement(s) name no replacement: " + ", ".join(retirements_without_replacement) + "\n"
        "Retirement is withdrawal-and-reissue, not deletion. Without a named replacement it\n"
        "is a way to make an inconvenient observation disappear."
    )
if missing_replacements:
    failures.append(
        "Named replacement(s) absent from this run: " + ", ".join(missing_replacements) + "\n"
        "The replacement must actually be reported, or the retirement is a deletion."
    )
if declared_but_unmoved:
    failures.append(
        "Declared exception(s) did not actually move: "
        + ", ".join(k[1] for k in declared_but_unmoved) + "\n"
        "A stale exception is a licence to move an observation silently later. Remove it."
    )

if failures:
    print("AUDIT-PRESERVATION GATE: FAIL")
    for message in failures:
        print(message)
    raise SystemExit(1)

print("AUDIT-PRESERVATION GATE: PASS")
print(f"({len(before)} of {len(before)} baseline observations compared -- every (test, name) "
      "pair, not a name-deduplicated subset)")
if declared_changed or declared_retired:
    print(
        f"every undeclared observation is byte-identical; "
        f"{len(declared_changed)} label-valued observation(s) moved and "
        f"{len(declared_retired)} were retired, all declared in advance; "
        "no numeric observation moved"
    )
else:
    print("every pre-existing observation is byte-identical; only new ones were added")
PY
