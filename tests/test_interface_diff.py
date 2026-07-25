"""ADR-003's pinning test: the declared interfaces differ on at least six of
seven items, reproducing Core §7.2's inversion table. Cites Core §4 (the
seven-item interface is "comparative... which is what converts a collection
of examples into evidence of generality") and Core §7.2.
"""

from __future__ import annotations

from omi.interface import diff

from omi_domains.contrast.interface import CONTRAST_DECLARATION
from omi_domains.flagship.interface import FLAGSHIP_DECLARATION


def test_flagship_and_contrast_differ_on_at_least_six_of_seven_items() -> None:
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
    assert len(result) == 7
    differing = sum(result.values())
    assert differing >= 6, f"only {differing}/7 items differ: {result}"


def test_specific_inversions_named_in_core_section_7_2() -> None:
    """Core §7.2's table names these rows explicitly as inverted:
    erasure operators, observation suite, control axis, and (via the state
    schema) dominant slot and nonlocal slot occupant."""
    result = diff(FLAGSHIP_DECLARATION, CONTRAST_DECLARATION)
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
