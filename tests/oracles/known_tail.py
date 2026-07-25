"""The known-tail oracle (CLAUDE.md §7; Spec §4.3, Core §3.6).

The M0 pattern-establishing oracle: it needs no framework code (there is
none yet — docs/ROADMAP.md M0 is scaffolding only), just a defect-descriptor
population with a known Pareto tail and a declared power-law driver map.

Construction, per Spec §4.3 / Proposition 4.1: a defect descriptor ``a`` has
a regularly varying tail with index ``alpha_a`` (so, in generalised-Pareto
terms, Pickands shape ``xi_a = 1 / alpha_a``); the failure driver amplifies
as ``D = k * a**beta``. The truth this oracle carries is the resulting driver
tail shape ``xi_D = beta * xi_a``, exactly Spec §4.3's boxed result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class KnownTailOracle:
    """A defect descriptor with a known Pareto tail, mapped through a known
    power-law driver (Spec §4.3). ``truth()`` is the constructed
    generalised-Pareto shape ``xi_D = beta * xi_a`` implied by Proposition 4.1.

    Every sampling method takes an explicit ``numpy.random.Generator``
    (CLAUDE.md §7) — there is no module-level or global random state here.
    """

    alpha_a: float
    """Pareto tail index of the defect descriptor (Spec §4.3): ``P(a > x) ~ C x**-alpha_a``."""
    beta: float
    """Driver amplification exponent (Spec §4.3): ``D = k * a**beta``."""
    k: float = 1.0
    """Driver amplification scale."""
    x_m: float = 1.0
    """Pareto scale — the minimum attainable descriptor value."""

    def __post_init__(self) -> None:
        if self.alpha_a <= 0:
            raise ValueError("alpha_a (Pareto tail index) must be positive")
        if self.beta <= 0:
            raise ValueError("beta (driver amplification exponent) must be positive")
        if self.x_m <= 0:
            raise ValueError("x_m (Pareto scale) must be positive")

    def sample_descriptors(self, n: int, rng: np.random.Generator) -> FloatArray:
        """Draw ``n`` defect descriptors ``a ~ Pareto(alpha_a, x_m)``.

        Stands in for Spec §4.3's independently measured defect population.
        Takes an explicit generator (CLAUDE.md §7); no global RNG state.
        """
        raw = stats.pareto.rvs(self.alpha_a, size=n, random_state=rng)
        return self.x_m * np.asarray(raw, dtype=np.float64)

    def driver(self, a: FloatArray) -> FloatArray:
        """Apply the declared power-law driver map ``D = k * a**beta`` (Spec §4.3)."""
        return self.k * a**self.beta

    def sample_driver(self, n: int, rng: np.random.Generator) -> FloatArray:
        """Sample ``n`` driver values by composing :meth:`sample_descriptors`
        and :meth:`driver` — the two-stage construction Spec §4.3 describes."""
        return self.driver(self.sample_descriptors(n, rng))

    def truth(self) -> float:
        """Return the constructed generalised-Pareto shape ``xi_D = beta * xi_a``
        (Spec §4.3, Proposition 4.1), where ``xi_a = 1 / alpha_a``."""
        xi_a = 1.0 / self.alpha_a
        return self.beta * xi_a
