"""ADR-034's pinning test, **rebuilt at ADR-071 so Core §7.2's comparison table is
regenerated from the item list rather than written down by hand.**

The claim is unchanged from ADR-034 (superseding ADR-003): the declared interfaces invert
on exactly the Core §4 items Core §7.2's own table names — not "six of the dict keys
`diff()` happens to produce," which conflates two distinct things. Cites Core §4 (the
interface is "comparative... which is what converts a collection of examples into evidence
of generality") and Core §7.2.

**What changed, and why it is E-01 rather than housekeeping.** This file used to carry
`CORE_7_2_ROW_TO_INTERFACE_ITEM` as a literal dict and assert `len(...) == 7` beside a
comment explaining that the seven rows cover only six items. That is `docs/V1.4-EDITS.md`
E-01's finding *pinned by hand*: a human wrote the mapping down, so re-chartering an item
made the literal stale with nothing noticing. The mapping now lives as data in
`omi.interface` (:data:`~omi.interface.INTERFACE_ITEMS`, :data:`~omi.interface.CORE_7_2_ROWS`)
and this module derives every count from it. **E-01 becomes a standing check**: the item
list and the published table can no longer disagree silently, and an item with no §7.2 row
is reported by name instead of being absorbed into a comment.

**`diff_result` is retired with no replacement** (ADR-071, following ADR-062's
retire-rather-than-mutate precedent). It recorded the raw `diff()` dict under two different
tests, and one of those recordings pinned ADR-034's seven-rows-onto-six mapping as a fact
about a seven-item interface. That mapping is now *computed* from the item list, so there is
no hand-written claim left for an observation to pin — the comparison it recorded has ceased
to exist rather than moved. Under the versioned-baseline scheme (ADR-069) nothing is
deleted: `diff_result` stays valid and audited forever in the `v13-items7` generation, and
simply does not exist in the eight-item generation.
"""

from __future__ import annotations

from omi.interface import (
    CORE_7_2_ROWS,
    INTERFACE_ITEMS,
    core_7_2_row_to_item,
    diff,
    interface_items_match_declaration,
    items_without_a_core_7_2_row,
)

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION

from tests.conftest import ObservationRecorder


def test_the_item_list_covers_exactly_the_declaration_fields() -> None:
    """**The consistency the whole derived scheme rests on** (ADR-071).

    If a field is added to :class:`~omi.interface.InstantiationDeclaration` without a
    matching :data:`~omi.interface.INTERFACE_ITEMS` entry, then the numbering, the charters
    and the §7.2 mapping are all silently wrong — which is the failure mode E-01 recorded,
    reintroduced one level up. This is the test that makes adding an item surface here
    rather than nowhere.
    """
    assert interface_items_match_declaration(), (
        "INTERFACE_ITEMS and InstantiationDeclaration's fields have diverged: every item "
        "must name exactly one field, in order"
    )


def test_the_core_7_2_mapping_is_derivable_and_every_published_row_is_claimed() -> None:
    """`core_7_2_row_to_item` raises unless each published row is named by exactly one
    item (Core §7.2; ADR-034's mapping, ADR-071). Calling it *is* the check."""
    mapping = core_7_2_row_to_item()
    assert set(mapping) == set(CORE_7_2_ROWS)


def test_core_7_2s_published_rows_cover_fewer_items_than_the_interface_declares(
    observe: ObservationRecorder,
) -> None:
    """**E-01, derived rather than asserted as a literal.**

    E-01's finding is that Core §7.2's table has seven rows covering strictly fewer than
    the interface's items, so the row count is not evidence about the item count. Both
    sides are now computed. The items with no row are reported by name, which is the part a
    hand-written comment could not keep true: item 6 (invariants) never had a row, and item
    1b did not exist when §7.2 was written, so the published table cannot name it.
    """
    mapping = core_7_2_row_to_item()
    covered = set(mapping.values())
    missing = items_without_a_core_7_2_row()

    observe("interface_item_count", len(INTERFACE_ITEMS), "8 since ADR-071 split item 1 into 1a/1b")
    observe("core_7_2_published_row_count", len(CORE_7_2_ROWS), "7 -- a fact about the issued v1.3 text")
    observe("core_7_2_distinct_items_covered", len(covered), "fewer than the declared item count")
    observe("interface_items_without_a_core_7_2_row", missing, "item 6 never had a row; item 1b postdates the table")

    assert len(CORE_7_2_ROWS) == 7
    assert len(covered) < len(INTERFACE_ITEMS), (
        "E-01's finding is that the published table covers fewer items than the interface "
        "declares; if that ever stops holding, E-01 is resolved and this test should say so"
    )
    # Two rows name item 1a (dominant slot, nonlocal slot), which is why the row count
    # exceeds the covered-item count -- ADR-034's original point.
    assert len(mapping) > len(covered)
    assert set(missing) == {"1b", "6"}


def test_flagship_and_contrast_differ_on_every_item_core_7_2_names(
    observe: ObservationRecorder,
) -> None:
    """The substantive claim, now driven by the derived mapping: every Core §4 item that
    §7.2 names as inverted is reported different by `diff()` (Core §7.2; ADR-034)."""
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    named_fields = {
        item.field for item in INTERFACE_ITEMS if item.core_7_2_rows
    }

    observe(
        "flagship_vs_contrast_per_item_diff",
        result,
        "every §7.2-named item True; recorded under the eight-item criterion",
    )
    for field in named_fields:
        assert result[field], f"Core §7.2 names an inversion on {field!r}, but diff() reports no difference"


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


def test_specific_inversions_named_in_core_section_7_2() -> None:
    """Core §7.2's table names these rows explicitly as inverted:
    erasure operators, observation suite, control axis, and (via the state
    schema) dominant slot and nonlocal slot occupant.

    Records no observation any more: the `diff_result` recording that stood here is
    retired with no replacement (ADR-071 — see this module's docstring), because the claim
    it pinned is now derived by the tests above. The assertions themselves are unchanged.
    """
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    assert result["erasure_inventory"]  # several, strong <-> none
    assert result["observation_suite"]  # rich, multi-modal <-> genuinely poor
    assert result["control_space"]  # apparatus-controlled <-> usage-determined
    assert result["state_schema"]  # dominant slot m,z <-> Gamma; nu residual stress <-> potential

    # The flagship declares an erasure; the contrast declares none at all —
    # the load-bearing inversion Core §3.9 / §7.2 turns on.
    assert FLAGSHIP_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_item_1b_inverts_the_two_domains_in_the_opposite_direction_to_item_3(
    observe: ObservationRecorder,
) -> None:
    """**The new item's first comparative reading, and it is not the one expected.**

    On item 3 (erasure inventory) the flagship is the rich declaration and the contrast is
    empty — Core §7.2's headline inversion. On item 1b the polarity is reversed: the
    contrast declares an operator-family index (its cell design) and the **flagship declares
    none**, because flagship's three de-facto-static components sit in item 1a instead
    (`docs/V1.4-EDITS.md` E-29, measured; see `omi_domains.flagship.interface`'s comment).

    Recorded because the flagship is the domain E-29 was *written about* — flat-rolled steel,
    where composition-as-operator-index is the paradigm case — so the domain with the
    strongest claim to needing item 1b is the one whose declaration leaves it empty. That is
    evidence about the item's value that a formatting pass could not produce.
    """
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    observe("item_1b_differs_flagship_vs_contrast", result["declared_parameters"], "True")
    observe("flagship_declared_parameter_count", len(FLAGSHIP_DECLARATION.declared_parameters), "0 -- E-29 unrepaired")
    observe("contrast_declared_parameter_count", len(CONTRAST_DECLARATION.declared_parameters), ">= 1")

    assert result["declared_parameters"]
    assert FLAGSHIP_DECLARATION.declared_parameters == ()
    assert CONTRAST_DECLARATION.declared_parameters != ()
    # The reversal against item 3, stated mechanically so it cannot be lost in prose.
    assert FLAGSHIP_DECLARATION.erasure_inventory != () and CONTRAST_DECLARATION.erasure_inventory == ()


def test_diff_of_a_declaration_with_itself_is_empty() -> None:
    """Sanity check on the diff mechanism itself, independent of domain
    content."""
    result = diff(FLAGSHIP_DECLARATION, FLAGSHIP_DECLARATION)
    assert not any(result.values())
