"""ADR-034's pinning test (docs/DECISIONS.md, superseding ADR-003): the
declared interfaces invert on exactly the six Core §4 items Core §7.2's own
table names — not "six of the seven dict keys `diff()` happens to produce,"
which conflates two distinct things (see ADR-034's mapping table). Cites
Core §4 (the seven-item interface is "comparative... which is what converts
a collection of examples into evidence of generality") and Core §7.2.
"""

from __future__ import annotations

from omi.interface import diff

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION

from tests.conftest import ObservationRecorder

# ADR-034's explicit mapping: each of Core §7.2's seven named rows onto the
# Core §4 interface item it actually tests. "Dominant slot" and "Nonlocal
# slot ν" both land on item 1 (state_schema) — Core §7.2's own table has
# seven rows but they cover only six of Core §4's seven items; item 6
# (invariants) has no row in Core §7.2's table at all.
CORE_7_2_ROW_TO_INTERFACE_ITEM = {
    "Erasure operators": "erasure_inventory",
    "Observation suite": "observation_suite",
    "Dominant slot": "state_schema",
    "Control axis": "control_space",
    "Tier structure": "scale_structure",
    "Class B": "readout_catalogue",
    "Nonlocal slot ν": "state_schema",
}


def test_core_7_2s_seven_rows_cover_exactly_six_distinct_interface_items() -> None:
    """Pins the mapping itself, independent of any diff computation: seven
    named rows, six distinct Core §4 items, because two rows both name the
    state schema."""
    distinct_items = set(CORE_7_2_ROW_TO_INTERFACE_ITEM.values())
    assert len(CORE_7_2_ROW_TO_INTERFACE_ITEM) == 7
    assert len(distinct_items) == 6
    assert "invariants" not in distinct_items


def test_flagship_and_contrast_differ_on_exactly_the_six_items_core_7_2_names(
    observe: ObservationRecorder,
) -> None:
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    named_items = set(CORE_7_2_ROW_TO_INTERFACE_ITEM.values())

    observe("diff_result", result, "all six Core §7.2-named items are True")
    for item in named_items:
        assert result[item], f"Core §7.2 names an inversion on {item!r}, but diff() reports no difference"


def test_invariants_literal_diff_and_structural_diff_disagree(observe: ObservationRecorder) -> None:
    """The case ADR-034 exists to catch: item 6 (invariants) has no row in
    Core §7.2's table, and the two domains' declared invariant *names*
    differ (so the literal ``"invariants"`` key is ``True``) purely because
    they are named after different physics — not because the domains
    disagree on invariant *structure*. Both declare exactly one conservation
    law and one monotonicity constraint, so ``"invariants_structural"`` must
    be ``False``: naming difference is not structural inversion.
    """
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)

    observe("invariants_literal_differs", result["invariants"], "True (different names)")
    observe("invariants_structural_differs", result["invariants_structural"], "False (same kind multiset)")

    assert result["invariants"], "the two domains name their invariants differently"
    assert not result["invariants_structural"], (
        "both domains declare one conservation law and one monotonicity constraint; "
        "naming difference alone must not register as a structural inversion"
    )


def test_specific_inversions_named_in_core_section_7_2(observe: ObservationRecorder) -> None:
    """Core §7.2's table names these rows explicitly as inverted:
    erasure operators, observation suite, control axis, and (via the state
    schema) dominant slot and nonlocal slot occupant."""
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    observe("diff_result", result, "narrative only, not asserted beyond named fields")
    assert result["erasure_inventory"]  # several, strong <-> none
    assert result["observation_suite"]  # rich, multi-modal <-> genuinely poor
    assert result["control_space"]  # apparatus-controlled <-> usage-determined
    assert result["state_schema"]  # dominant slot m,z <-> Gamma; nu residual stress <-> potential

    # The flagship declares an erasure; the contrast declares none at all —
    # the load-bearing inversion Core §3.9 / §7.2 turns on.
    assert FLAGSHIP_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_diff_of_a_declaration_with_itself_is_empty() -> None:
    """Sanity check on the diff mechanism itself, independent of domain
    content."""
    result = diff(FLAGSHIP_DECLARATION, FLAGSHIP_DECLARATION)
    assert not any(result.values())
