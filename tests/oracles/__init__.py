"""The oracle protocol (CLAUDE.md §7; ADR-004, ADR-009 in docs/DECISIONS.md).

Cites Core §3.9: the framework's own stance is that an unverified answer is
worse than a refusal, and that applies to this codebase's estimators as much
as to the framework's procedures. For every quantity OMI requires to be
measured, this package holds a synthetic system whose answer is known by
*construction* — an oracle — so an estimator can be checked against a truth
that does not depend on the estimator being correct.

An oracle is anything exposing ``truth()``, and nothing else is fixed at this
level (ADR-009): each concrete oracle's "normal interface" — what it samples,
evolves, or exposes for the estimator under test to consume — is specific to
what it is checking, and is documented in its own module.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Oracle(Protocol):
    """Structural protocol every oracle in this package satisfies.

    Cites Core §3.9 (module docstring): ``truth()`` returns the constructed
    ground-truth answer, in whatever type is natural for the oracle at hand
    (a scalar, a subspace, a trajectory, ...). A concrete oracle is not
    required to subclass this — satisfying the shape is enough, which is why
    this is a :class:`typing.Protocol` rather than an ``ABC`` (ADR-009).
    """

    def truth(self) -> Any:
        """Return the answer this oracle was constructed to have."""
        ...
