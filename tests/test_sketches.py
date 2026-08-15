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

from omi.interface import INTERFACE_ITEMS, InstantiationDeclaration, diff
from omi.state import Slot

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION
from omi_domains.sketches.device_yield import DEVICE_YIELD_DECLARATION, DEVICE_YIELD_SCHEMA
from omi_domains.sketches.catalyst_under_operation import (
    CATALYST_UNDER_OPERATION_DECLARATION,
    CATALYST_UNDER_OPERATION_SCHEMA,
)
from omi_domains.sketches.crystallisation_formulation import (
    CRYSTALLISATION_FORMULATION_DECLARATION,
    CRYSTALLISATION_FORMULATION_SCHEMA,
)
from omi_domains.sketches.layerwise_additive import (
    LAYERWISE_ADDITIVE_DECLARATION,
    LAYERWISE_ADDITIVE_SCHEMA,
)

from tests.conftest import ObservationRecorder

_ALL_DIFF_KEYS = {item.field for item in INTERFACE_ITEMS} | {"invariants_structural"}
"""Every key `omi.interface.diff` produces, **derived from the item list** rather than
listed by hand (ADR-071).

Was `_ALL_SEVEN_ITEMS`, a literal, until Stage 2 split item 1 and made it stale — the same
hand-pinning failure `docs/V1.4-EDITS.md` E-01 records for Core §7.2's mapping, in this
file. Deriving it means a future item change moves these assertions automatically instead of
requiring eight edits, and `invariants_structural` is added explicitly because it is the one
key that is *not* an item (ADR-034's structural companion, deliberately not generalised to
other items — see `omi.interface.diff`)."""


def test_device_yield_declaration_is_a_real_instantiation_declaration() -> None:
    """Sanity check on ADR-038's shape requirement: a sketch is a real,
    fully-populated ``InstantiationDeclaration`` (every item, eight since ADR-071),
    not a partial stand-in."""
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
    assert set(result) == _ALL_DIFF_KEYS


def test_device_yield_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(DEVICE_YIELD_DECLARATION, CONTRAST_DECLARATION)
    observe("device_yield_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS

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
    assert set(result) == _ALL_DIFF_KEYS


def test_layerwise_additive_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(LAYERWISE_ADDITIVE_DECLARATION, CONTRAST_DECLARATION)
    observe("layerwise_additive_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS

    # Layer-wise additive's erasure (hot_isostatic_pressing) is terminal, not
    # mid-chain like flagship's -- still non-empty, unlike contrast's.
    assert LAYERWISE_ADDITIVE_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_layerwise_additive_diff_with_itself_is_empty() -> None:
    result = diff(LAYERWISE_ADDITIVE_DECLARATION, LAYERWISE_ADDITIVE_DECLARATION)
    assert not any(result.values())


def test_crystallisation_formulation_declaration_is_a_real_instantiation_declaration() -> None:
    """Same shape check as the first two sketches, ADR-038."""
    assert isinstance(CRYSTALLISATION_FORMULATION_DECLARATION, InstantiationDeclaration)
    assert CRYSTALLISATION_FORMULATION_DECLARATION.state_schema is CRYSTALLISATION_FORMULATION_SCHEMA
    assert CRYSTALLISATION_FORMULATION_DECLARATION.erasure_inventory != ()
    assert len(CRYSTALLISATION_FORMULATION_DECLARATION.readout_catalogue) > 0
    assert len(CRYSTALLISATION_FORMULATION_DECLARATION.observation_suite) > 0
    assert len(CRYSTALLISATION_FORMULATION_DECLARATION.invariants) > 0


def test_crystallisation_formulation_schema_occupies_all_four_slots() -> None:
    """All four slots fill without forcing here too (docs/SKETCHES.md) --
    unlike layer-wise additive, this sketch's nu strain (E-22's addendum)
    is about typing, not about an empty slot; both sketches share that
    same distinction."""
    from omi.state import Slot

    for slot in Slot:
        assert not CRYSTALLISATION_FORMULATION_SCHEMA.is_empty(slot), f"{slot.value} unexpectedly empty"


def test_crystallisation_formulation_diffs_against_flagship(observe: ObservationRecorder) -> None:
    result = diff(CRYSTALLISATION_FORMULATION_DECLARATION, FLAGSHIP_DECLARATION)
    observe("crystallisation_formulation_vs_flagship_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS


def test_crystallisation_formulation_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(CRYSTALLISATION_FORMULATION_DECLARATION, CONTRAST_DECLARATION)
    observe("crystallisation_formulation_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS

    # Crystallisation's erasure is mid-chain (like flagship's), unlike
    # contrast's declared absence -- and unlike device yield's/layer-wise
    # additive's terminal-only candidates.
    assert CRYSTALLISATION_FORMULATION_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_crystallisation_formulation_diff_with_itself_is_empty() -> None:
    result = diff(CRYSTALLISATION_FORMULATION_DECLARATION, CRYSTALLISATION_FORMULATION_DECLARATION)
    assert not any(result.values())


def test_catalyst_under_operation_declaration_is_a_real_instantiation_declaration() -> None:
    """Same shape check as every other sketch, ADR-038."""
    assert isinstance(CATALYST_UNDER_OPERATION_DECLARATION, InstantiationDeclaration)
    assert CATALYST_UNDER_OPERATION_DECLARATION.state_schema is CATALYST_UNDER_OPERATION_SCHEMA
    assert CATALYST_UNDER_OPERATION_DECLARATION.erasure_inventory != ()
    assert len(CATALYST_UNDER_OPERATION_DECLARATION.readout_catalogue) > 0
    assert len(CATALYST_UNDER_OPERATION_DECLARATION.observation_suite) > 0
    assert len(CATALYST_UNDER_OPERATION_DECLARATION.invariants) > 0


def test_catalyst_under_operation_schema_leaves_m_and_nu_empty() -> None:
    """The deliberately awkward sketch (docs/SKETCHES.md, ROADMAP M10.1):
    Gamma is almost the entire state, z is minimal, and m/nu are
    genuinely empty -- the first time `StateSchema.is_empty` has ever
    been exercised returning True anywhere in this repository (every
    prior domain and sketch asserts `not is_empty(...)` for all four
    slots; grep confirms no prior test ever asserted the True case).
    This is the direct, mechanical answer to whether Core §4 item 1's
    "which slots are empty" is more than a formality: it is -- the
    schema carries and reports this correctly.
    """
    assert CATALYST_UNDER_OPERATION_SCHEMA.is_empty(Slot.M)
    assert not CATALYST_UNDER_OPERATION_SCHEMA.is_empty(Slot.Z)
    assert CATALYST_UNDER_OPERATION_SCHEMA.is_empty(Slot.NU)
    assert not CATALYST_UNDER_OPERATION_SCHEMA.is_empty(Slot.GAMMA)

    # Gamma dominant by construction; z minimal (one component).
    assert len(CATALYST_UNDER_OPERATION_SCHEMA.names(Slot.GAMMA)) == 4
    assert len(CATALYST_UNDER_OPERATION_SCHEMA.names(Slot.Z)) == 1


def test_catalyst_under_operation_diffs_against_flagship(observe: ObservationRecorder) -> None:
    result = diff(CATALYST_UNDER_OPERATION_DECLARATION, FLAGSHIP_DECLARATION)
    observe("catalyst_under_operation_vs_flagship_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS


def test_catalyst_under_operation_diffs_against_contrast(observe: ObservationRecorder) -> None:
    result = diff(CATALYST_UNDER_OPERATION_DECLARATION, CONTRAST_DECLARATION)
    observe("catalyst_under_operation_vs_contrast_diff", result, "recorded, not asserted against a pattern")
    assert set(result) == _ALL_DIFF_KEYS

    assert CATALYST_UNDER_OPERATION_DECLARATION.erasure_inventory != ()
    assert CONTRAST_DECLARATION.erasure_inventory == ()


def test_catalyst_under_operation_diff_with_itself_is_empty() -> None:
    """The diff mechanism itself is unaffected by empty slots -- confirms
    the mechanical half of docs/SKETCHES.md's "does the machinery break"
    question, for the one piece of machinery an interface-only sketch can
    actually exercise (StateSchema/diff, not erasure/triage/Class B,
    which need a real operator this sketch deliberately does not build).
    """
    result = diff(CATALYST_UNDER_OPERATION_DECLARATION, CATALYST_UNDER_OPERATION_DECLARATION)
    assert not any(result.values())


# --- Item 1b: the four fillability verdicts, re-derived at ADR-071 -----------
#
# CLAUDE.md invariant 11 makes each sketch's fillability verdict evidence for the
# generality claim, so splitting item 1 means each verdict is re-ESTABLISHED rather
# than reformatted. These tests record the outcome of that re-derivation. The
# reasoning behind each verdict lives in the sketch module's own
# `ParameterRole.justification` — free text there, checked for existence here.


def test_every_sketch_fills_item_1b(observe: ObservationRecorder) -> None:
    """**The re-derivation's headline: all four sketches fill item 1b, and no prior
    verdict changed** (docs/V1.4-EDITS.md E-46; ADR-071).

    Each sketch declares at least one operator-family index with a justification against
    E-46's four-property test. No sketch's *existing* verdict moved, because no sketch's
    schema had to give anything up: every component in all four schemas is genuinely
    transported by some operator, so the split re-charters item 1a without relocating
    content out of it.

    **Recorded with its own caveat, because "all four fill" is weaker evidence than it
    looks.** An item that everything fills may be well-posed or may be too loose to
    discriminate. What keeps this from being vacuous is the negative case next door:
    `FLAGSHIP_DECLARATION` — the domain E-29 was written about — declares item 1b *empty*,
    so the item does separate declarations rather than accepting anything.
    """
    filled = {
        "device_yield": DEVICE_YIELD_DECLARATION,
        "layerwise_additive": LAYERWISE_ADDITIVE_DECLARATION,
        "crystallisation_formulation": CRYSTALLISATION_FORMULATION_DECLARATION,
        "catalyst_under_operation": CATALYST_UNDER_OPERATION_DECLARATION,
    }
    counts = {name: len(d.declared_parameters) for name, d in filled.items()}
    observe("sketch_item_1b_parameter_counts", counts, "every sketch >= 1")
    observe(
        "sketch_item_1b_verdicts_changed",
        0,
        "0 -- no pre-existing fillability verdict moved under the re-charter",
    )
    observe(
        "flagship_item_1b_is_the_negative_case",
        len(FLAGSHIP_DECLARATION.declared_parameters),
        "0 -- so item 1b is not filled by everything",
    )

    for name, declaration in filled.items():
        assert declaration.declared_parameters, f"{name} declares no operator-family index"
        for parameter in declaration.declared_parameters:
            assert parameter.justification.strip(), f"{name}'s {parameter.name} has no justification"
            assert parameter.indexes, f"{name}'s {parameter.name} indexes nothing"

    assert FLAGSHIP_DECLARATION.declared_parameters == (), (
        "flagship's empty item 1b is what stops 'all four sketches fill it' from being "
        "evidence that the item accepts anything (docs/V1.4-EDITS.md E-29)"
    )


def test_no_sketch_schema_lost_a_component_to_item_1b() -> None:
    """The measured half of the re-derivation (ADR-071).

    `docs/ARITY-REDESIGN-BRIEF.md` §4 predicted no verdict would flip because no sketch
    schema carries a parameterisation-like component — every occupant is genuinely evolving
    state. Checked rather than assumed: an occupant that had to move to item 1b would mean a
    sketch's item-1a content changed, which is the case where a verdict *could* flip.
    """
    for schema, declaration in (
        (DEVICE_YIELD_SCHEMA, DEVICE_YIELD_DECLARATION),
        (LAYERWISE_ADDITIVE_SCHEMA, LAYERWISE_ADDITIVE_DECLARATION),
        (CRYSTALLISATION_FORMULATION_SCHEMA, CRYSTALLISATION_FORMULATION_DECLARATION),
        (CATALYST_UNDER_OPERATION_SCHEMA, CATALYST_UNDER_OPERATION_DECLARATION),
    ):
        occupants = {name for _, name, _ in schema.components}
        parameters = {p.name for p in declaration.declared_parameters}
        assert not (occupants & parameters), (
            f"a quantity is declared in both item 1a and item 1b: {sorted(occupants & parameters)}"
        )


def test_device_yield_separates_an_index_from_a_state_on_one_physical_object(
    observe: ObservationRecorder,
) -> None:
    """The sharpest single illustration the four sketches produce of what the split buys
    (`docs/V1.4-EDITS.md` E-29; ADR-071).

    The chamber's *identity* is an operator-family index (item 1b); the same chamber's
    *seasoning state* evolves run to run and is an item-1a `z` occupant. Before the split
    both were item 1 content with nothing distinguishing them, which is E-29's finding
    exactly: "static by design" and "should evolve but does not" had identical structural
    signatures.
    """
    parameters = {p.name for p in DEVICE_YIELD_DECLARATION.declared_parameters}
    occupants = {name for _, name, _ in DEVICE_YIELD_SCHEMA.components}
    observe("device_yield_chamber_identity_is_a_parameter", "tool_chamber_identity" in parameters, "True")
    observe("device_yield_chamber_state_is_an_occupant", "chamber_seasoning_state" in occupants, "True")

    assert "tool_chamber_identity" in parameters
    assert "chamber_seasoning_state" in occupants


def test_layerwise_additive_does_not_use_item_1b_to_paper_over_e21(
    observe: ObservationRecorder,
) -> None:
    """A deliberate non-declaration, pinned so a later reader cannot mistake the split for
    a fix to something it does not fix (`docs/V1.4-EDITS.md` E-21; ADR-071).

    This sketch's standing finding is that its state is a field over a body under
    construction, which `StateSchema` cannot represent. The build geometry is fixed per build
    and would superficially qualify as an item-1b index, so declaring it there would make an
    unrepresentable structure look declared. It is deliberately not declared, and this test
    is what keeps that deliberate.
    """
    parameters = {p.name for p in LAYERWISE_ADDITIVE_DECLARATION.declared_parameters}
    observe("layerwise_item_1b_names", sorted(parameters), "feedstock only -- geometry deliberately absent")
    assert parameters == {"feedstock_powder_batch"}
