"""A composition-carrying variant of the flagship domain (ADR-075, ADR-076).

**A new package rather than a change to `flagship`,** on the `flagship_constitutive`
precedent and for the reason ADR-075 Decision 2 records: `δc` is a slot occupant, so
declaring it changes a `StateSchema`, and changing an existing schema changes its `size`
and therefore every metric-normalised quantity computed on it. `flagship`'s own
declaration, schema and operators are untouched, and no pre-existing observation moves.

What this package adds over `flagship`:

- `c̄` declared as item 1b's `ParameterRole`, carrying its descriptor map, its projection
  scale and whether its domain is closed (ADR-050, ADR-052, ADR-071).
- one **sub-resolution** `δc` occupant in `z` — and no resolved band anywhere, because
  resolved bands need `FIELD` domains that ADR-049 refuses citing `C-2.5` (ADR-076
  decision 4).
- two operators over that occupant, one conserving the domain mean and one with a declared
  boundary flux, so ADR-050's constancy residual has both of its cases on real physics
  rather than only in an oracle.
"""
