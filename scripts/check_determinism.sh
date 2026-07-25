#!/usr/bin/env bash
# Determinism harness (docs/ROADMAP.md M0; CLAUDE.md §7): run the test suite
# twice and diff the output. A flaky test in a framework about uncertainty
# quantification is worse than no test, so every stochastic helper must take
# an explicit numpy.random.Generator (never global RNG state) and this script
# is what makes a violation of that visible in CI.
set -euo pipefail

RUN1="$(mktemp)"
RUN2="$(mktemp)"
trap 'rm -f "$RUN1" "$RUN2"' EXIT

strip_wall_clock() {
    # Wall-clock duration legitimately differs between runs and carries no
    # determinism signal — strip it before diffing, not before running.
    sed -E 's/[0-9]+\.[0-9]+s\b//g; s/ in [0-9.]+ seconds?//g'
}

pytest -q --color=no "$@" 2>&1 | strip_wall_clock > "$RUN1"
pytest -q --color=no "$@" 2>&1 | strip_wall_clock > "$RUN2"

if diff -u "$RUN1" "$RUN2"; then
    echo "Determinism check passed: two independent runs produced identical output."
    exit 0
else
    echo "Determinism check FAILED: the suite produced different output across two runs." >&2
    echo "This means some stochastic path is not seeded via an explicit numpy.random.Generator." >&2
    exit 1
fi
