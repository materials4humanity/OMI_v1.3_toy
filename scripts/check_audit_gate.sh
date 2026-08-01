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
#   scripts/check_audit_gate.sh <baseline.json>
#
# The baseline is a copy of build/observations.json taken from a full-suite run at
# the commit whose results are being preserved (for M11, 57f7db8 — the last commit
# before src/omi/ was touched by the proposed-v1.4 extension).

set -euo pipefail

BASELINE="${1:?usage: check_audit_gate.sh <baseline.json>}"
PYTHON="${PYTHON:-.venv/bin/python}"

if [ ! -f "$BASELINE" ]; then
    echo "baseline not found: $BASELINE" >&2
    exit 2
fi

echo "running the FULL suite (partial runs invalidate the comparison)..."
"$PYTHON" -m pytest -q

"$PYTHON" - "$BASELINE" <<'PY'
import json
import sys

baseline = json.load(open(sys.argv[1]))
current = json.load(open("build/observations.json"))

before = {o["name"]: o for o in baseline}
after = {o["name"]: o for o in current}

missing = sorted(set(before) - set(after))
changed = sorted(k for k in before if k in after and before[k] != after[k])
added = sorted(set(after) - set(before))

print()
print(f"baseline observations : {len(baseline)}")
print(f"current observations  : {len(current)}")
print(f"MISSING from current  : {len(missing)}")
for name in missing:
    print(f"    - {name}")
print(f"CHANGED vs baseline   : {len(changed)}")
for name in changed:
    print(f"    ~ {name}: {before[name]} -> {after[name]}")
print(f"newly added (expected): {len(added)}")
print()

if missing or changed:
    print("AUDIT-PRESERVATION GATE: FAIL")
    print(
        "A pre-existing observation moved. Per ADR-042 this is the signal that the\n"
        "change was NOT as inert as claimed: reopen the ADR rather than re-baselining."
    )
    raise SystemExit(1)

print("AUDIT-PRESERVATION GATE: PASS")
print("every pre-existing observation is byte-identical; only new ones were added")
PY
