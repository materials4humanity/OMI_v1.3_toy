"""Convenience factory: the constitutive variant's chain (Core §7.1's stage
table; M11.3, ADR-044).

Same topology as `omi_domains.flagship.build`: incoming unit -> heating and soak
-> transfer. Only the operators differ, which is the point of the variant.
"""

from __future__ import annotations

import numpy as np

from omi.chain import Chain, Segment
from omi.operators import Control

from omi_domains.flagship_constitutive.operators import (
    CONSTITUTIVE_HEATING_AND_SOAK,
    CONSTITUTIVE_TRANSFER,
)


def build_constitutive_chain(soak_time: float = 1.0, transfer_time: float = 0.3) -> Chain:
    """Heating-and-soak then transfer, each driven over its own interval (Core
    §3.3's composition; Core §7.1's stage table).

    The control here is a strain-rate-like driving intensity, which is one of
    `KOCKS_MECKING`'s declared control-space bounds — so the extrapolation report
    responds to it (Spec §2.2's proposed reporting obligation).
    """
    soak = Control(0.0, soak_time, lambda t: np.array([1.0]))
    transfer = Control(0.0, transfer_time, lambda t: np.array([1.0]))
    return Chain((Segment(CONSTITUTIVE_HEATING_AND_SOAK, soak), Segment(CONSTITUTIVE_TRANSFER, transfer)))
