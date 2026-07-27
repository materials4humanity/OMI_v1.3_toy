"""Phase 3.2 (docs/ROADMAP.md), ADR-036 (docs/DECISIONS.md): `learning_error`
now takes the chain and distinguishes "correctly zero, chain is analytic"
from "unknowable — chain has a learned operator, refuse citing S-1.4."
Fixes E-02's finding (docs/V1.4-EDITS.md): the function previously took no
arguments and returned `0.0` unconditionally, regardless of chain content.
"""

from __future__ import annotations

import numpy as np
import pytest

from omi.chain import Chain, Segment
from omi.gaps import NotSpecified
from omi.learning import DeepONetOperator, init_deeponet_params
from omi.operators import Control
from omi.sufficiency import learning_error

from omi_domains.flagship.build import build_chain as flagship_chain


def test_learning_error_is_zero_for_a_purely_analytic_chain() -> None:
    chain = flagship_chain()
    assert learning_error(chain) == 0.0


def test_learning_error_refuses_citing_s_1_4_when_the_chain_has_a_learned_operator() -> None:
    rng = np.random.default_rng(0)
    params = init_deeponet_params(state_dim=7, control_dim=1, rng=rng)
    learned = DeepONetOperator(params=params, erasure=False)
    control = Control(0.0, 1.0, lambda t: np.array([1.0]))
    chain = Chain((Segment(learned, control),))

    with pytest.raises(NotSpecified) as excinfo:
        learning_error(chain)
    assert "S-1.4" in str(excinfo.value)


def test_learning_error_refuses_even_when_the_learned_operator_is_not_the_first_segment() -> None:
    """The scan must check every segment, not only the first."""
    rng = np.random.default_rng(1)
    params = init_deeponet_params(state_dim=7, control_dim=1, rng=rng)
    learned = DeepONetOperator(params=params, erasure=False)
    control = Control(0.0, 1.0, lambda t: np.array([1.0]))

    analytic_chain = flagship_chain()
    mixed_chain = Chain(analytic_chain.segments + (Segment(learned, control),))

    with pytest.raises(NotSpecified):
        learning_error(mixed_chain)
