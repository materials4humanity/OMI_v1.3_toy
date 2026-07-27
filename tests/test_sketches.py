"""M10.1 (docs/ROADMAP.md): interface-only sketches must be machine-diffable
against both implemented domains (reuse ``omi.interface.diff``), per ADR-038
(docs/DECISIONS.md). Unlike ``tests/test_interface_diff.py``'s flagship-vs-
contrast test — which pins a specific expected inversion pattern (ADR-034),
since the two were designed to invert each other — a sketch carries no such
prior claim: these tests only confirm the diff actually runs against real
declaration objects and record every per-item result (CLAUDE.md §7, the
R1.1 convention), not what the comparison should find.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, diff

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.sketches.device_yield import DEVICE_YIELD_DECLARATION, DEVICE_YIELD_SCHEMA
from omi_domains.sketches.layerwise_additive import (
    LAYERWISE_ADDITIVE_DECLARATION,
    LAYERWISE_ADDITIVE_SCHEMA,
)

from tests.conftest import ObservationRecorder

_ALL_SEVEN_ITEMS = {
    "state_schema",
    "control_space",
    "erasure_inventory",
    "readout_catalogue",
    "observation_suite",
    "invariants",
    "scale_structure",
    "invariants_structural",
}


def test_device_yield_declaration_is_a_real_instantiation_declaration() -> None:
    """Sanity check on ADR-038's shape requirement: a sketch is a real,
    fully-populated ``InstantiationDeclaration`` (all seven fields), not a
    partial stand-in."""
    assert isinstance(DEVICE_YIELD_DECLARATION, InstantiationDeclaration)
    assert DEVICE_YIELD_DECLARATION.state_schema is DEVICE_YIELD_SCHEMA
    assert DEVICE_YIELD_DECLARATION.erasure_inventory != ()
    assert len(DEVICE_YIELD_DECLARATION.readout_catalogue) > 0
    assert len(DEVICE_YIELD_DECLARATION.observation_suite) > 0
    assert len(DEVICE_YIELD_DECLARATION.invariants) > 0


def test_device_yield_schema_occupies_all_four_slots() -> None:
    """docs/SKETCHES.md records this as a finding in its own right: unlike
    the fourth, deliberately awkward sketch M10.1 reserves for testing
    Core §6.2's open fifth-slot question, this sketch's four-slot schema
    fills without forcing — no slot is empty."""
    from omi.state import Slot

    for slot in Slot:
        assert not DEVICE_YIELD_SCHEMA.is_empty(slot), f"{slot.value} unexpectedly empty"


def test_device_yield_diffs_against_flagship(observe: ObservationRecorder) -> None:
    result = diff(DEVICE_YIELD_DECLARATION, FLAGSHIP_DECLARATION)
    observe("device_yield_vs_flagship_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_SEVEN_ITEMS


def test_device_yield_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(DEVICE_YIELD_DECLARATION, CONTRAST_DECLARATION)
    observe("device_yield_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_SEVEN_ITEMS

    # Device yield declares an erasure candidate (cmp_planarization); contrast
    # declares none at all -- structurally closer to flagship on this one item,
    # which is expected (this sketch was not chosen to invert contrast).
    assert DEVICE_YIELD_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_device_yield_diff_with_itself_is_empty() -> None:
    """Sanity check on the diff mechanism itself, independent of domain
    content (mirrors test_interface_diff.py's own such check)."""
    result = diff(DEVICE_YIELD_DECLARATION, DEVICE_YIELD_DECLARATION)
    assert not any(result.values())


def test_layerwise_additive_declaration_is_a_real_instantiation_declaration() -> None:
    """Same shape check as device yield's, ADR-038: a sketch is a real,
    fully-populated declaration even when (as here) one field is a forced
    Tier I approximation rather than a genuine fill — see
    docs/SKETCHES.md and docs/V1.4-EDITS.md E-21."""
    assert isinstance(LAYERWISE_ADDITIVE_DECLARATION, InstantiationDeclaration)
    assert LAYERWISE_ADDITIVE_DECLARATION.state_schema is LAYERWISE_ADDITIVE_SCHEMA
    assert LAYERWISE_ADDITIVE_DECLARATION.erasure_inventory != ()
    assert len(LAYERWISE_ADDITIVE_DECLARATION.readout_catalogue) > 0
    assert len(LAYERWISE_ADDITIVE_DECLARATION.observation_suite) > 0
    assert len(LAYERWISE_ADDITIVE_DECLARATION.invariants) > 0


def test_layerwise_additive_schema_occupies_all_four_slots() -> None:
    """All four slots are occupied in the Tier I stand-in -- the strain
    this sketch records (docs/SKETCHES.md, E-21) is about the schema's
    point-valued *representation*, not about an empty slot; that
    distinction is itself worth pinning so the two kinds of strain (a
    missing slot vs. an unrepresentable indexing structure) are not
    conflated in a future reading of this test suite."""
    from omi.state import Slot

    for slot in Slot:
        assert not LAYERWISE_ADDITIVE_SCHEMA.is_empty(slot), f"{slot.value} unexpectedly empty"


def test_layerwise_additive_diffs_against_flagship(observe: ObservationRecorder) -> None:
    result = diff(LAYERWISE_ADDITIVE_DECLARATION, FLAGSHIP_DECLARATION)
    observe("layerwise_additive_vs_flagship_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_SEVEN_ITEMS


def test_layerwise_additive_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(LAYERWISE_ADDITIVE_DECLARATION, CONTRAST_DECLARATION)
    observe("layerwise_additive_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_SEVEN_ITEMS

    # Layer-wise additive's erasure (hot_isostatic_pressing) is terminal, not
    # mid-chain like flagship's -- still non-empty, unlike contrast's.
    assert LAYERWISE_ADDITIVE_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_layerwise_additive_diff_with_itself_is_empty() -> None:
    result = diff(LAYERWISE_ADDITIVE_DECLARATION, LAYERWISE_ADDITIVE_DECLARATION)
    assert not any(result.values())
