#!/usr/bin/env bash
# M11.1's audit-preservation gate (docs/ROADMAP.md; ADR-042, docs/DECISIONS.md),
# as one step so it cannot be run in the wrong order.
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
# DECLARED EXCEPTIONS. An approved change to what a reported LABEL means must be able to
# move label-valued observations without either blocking the change or switching the gate
# off. The third option is to enumerate every moved observation in advance, with its before
# and after values and its reason -- see audit/e53-label-changes.json (ADR-061). The gate
# reports declared movements separately and still FAILS on any undeclared one, so nothing
# changes silently. And it REFUSES an exception whose value is numeric: that is the
# mechanical form of the claim such a change rests on, that a label moved and a computed
# quantity did not.
#
# The baseline is a copy of build/observations.json taken from a full-suite run at
# the commit whose results are being preserved (for M11, 57f7db8 — the last commit
# before src/omi/ was touched by the proposed-v1.4 extension).

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


before = {o["name"]: o for o in baseline}
after = {o["name"]: o for o in current}

missing = sorted(set(before) - set(after))
changed = sorted(k for k in before if k in after and before[k] != after[k])
added = sorted(set(after) - set(before))

undeclared_missing = [n for n in missing if n not in declared_retired]
undeclared_changed = [n for n in changed if n not in declared_changed]
declared_but_unmoved = sorted(
    set(declared_changed) - set(changed)
) + sorted(n for n in declared_retired if n in after)
# A NUMERIC exception is refused for `changed` and allowed for `retired`, and the
# difference is the whole point of the distinction rather than a convenience. A `changed`
# numeric observation takes a new value under its OLD name, so a consumer reading that name
# gets a different number and cannot tell -- which is the failure the gate exists to
# prevent. A `retired` one is withdrawn: nothing reports under that name again, the old
# value is recorded verbatim here, and the replacement is named. So the audit trail is
# intact by construction.
numeric_exceptions = sorted(
    name for name, entry in declared_changed.items() if is_numeric(entry.get("after"))
)

# The loophole that would otherwise open: "retired" must not become a way to delete an
# inconvenient observation. Every retirement must name a replacement, and that replacement
# must actually be present in the current run.
retirements_without_replacement = sorted(
    name for name, entry in declared_retired.items() if not entry.get("replaced_by")
)
missing_replacements = sorted(
    f"{name} -> {entry['replaced_by']}"
    for name, entry in declared_retired.items()
    if entry.get("replaced_by") and entry["replaced_by"] not in after
)

print()
print(f"baseline observations : {len(baseline)}")
print(f"current observations  : {len(current)}")
print(f"declared exceptions   : {len(declared_changed)} changed, {len(declared_retired)} retired")
print(f"MISSING from current  : {len(missing)} ({len(undeclared_missing)} undeclared)")
for name in missing:
    tag = "DECLARED" if name in declared_retired else "UNDECLARED"
    print(f"    - [{tag}] {name}")
print(f"CHANGED vs baseline   : {len(changed)} ({len(undeclared_changed)} undeclared)")
for name in changed:
    tag = "DECLARED" if name in declared_changed else "UNDECLARED"
    print(f"    ~ [{tag}] {name}: {before[name]['value']} -> {after[name]['value']}")
print(f"newly added (expected): {len(added)}")
print()

failures = []
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
        "Declared exception(s) did not actually move: " + ", ".join(declared_but_unmoved) + "\n"
        "A stale exception is a licence to move an observation silently later. Remove it."
    )

if failures:
    print("AUDIT-PRESERVATION GATE: FAIL")
    for message in failures:
        print(message)
    raise SystemExit(1)

print("AUDIT-PRESERVATION GATE: PASS")
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
