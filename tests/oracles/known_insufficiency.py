"""The known-insufficiency oracle (CLAUDE.md §7; Core §2.1, Spec §1.2, §1.6).

A hidden, genuinely *directional* (kinematic-type) variable ``h``: the
response under subsequent driving is ``f(v) + c·h·sign(direction) + noise``,
where ``sign`` is ``+1`` under forward driving and ``-1`` under reversed —
so ``h``'s contribution has *equal magnitude* under both probes, only its
sign differs. This is deliberately the case OQ-1 (docs/COVERAGE.md Part IV)
worried the naive single-probe fingerprint table mishandles: checking either
probe alone finds the *same size* divergence, so "reversed driving only"
does not actually hold, yet the variable genuinely is directional/kinematic
— visible correctly only in the antisymmetric half of the two probes'
responses (ADR-022, docs/DECISIONS.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from omi.state import FloatArray
from omi.sufficiency import ProbeSet


@dataclass(frozen=True)
class KnownInsufficiencyOracle:
    """``ρ = a·v + c·h·sign(direction) + ε``. The visible component ``v`` is
    the candidate description under test; ``h`` is the hidden variable a
    sufficiency campaign must reveal."""

    a_coeff: float = 2.0
    hidden_coeff: float = 1.5
    hidden_std: float = 1.0
    matching_noise_std: float = 0.05
    measurement_noise_std: float = 0.2

    def response(self, v: float, h: float, direction: str, rng: np.random.Generator) -> float:
        sign = 1.0 if direction == "forward" else -1.0
        noise = rng.normal(scale=self.measurement_noise_std)
        return self.a_coeff * v + self.hidden_coeff * h * sign + noise

    def sample_incomplete_campaign(
        self, n_pairs: int, direction: str, rng: np.random.Generator
    ) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Matched on ``v`` only (with realistic imperfect matching); ``h``
        genuinely differs between the two specimens of each pair — this is
        the candidate description that Core §2.1's sufficiency test must
        show is insufficient."""
        v_nominal = rng.normal(size=n_pairs)
        v_a = v_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)
        v_b = v_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)
        h_a = rng.normal(scale=self.hidden_std, size=n_pairs)
        h_b = rng.normal(scale=self.hidden_std, size=n_pairs)

        response_a = np.array([self.response(v_a[i], h_a[i], direction, rng) for i in range(n_pairs)])
        response_b = np.array([self.response(v_b[i], h_b[i], direction, rng) for i in range(n_pairs)])
        matched_diffs = (v_a - v_b).reshape(-1, 1)
        return response_a, response_b, matched_diffs

    def sample_complete_campaign(
        self, n_pairs: int, direction: str, rng: np.random.Generator
    ) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Matched on both ``v`` and ``h`` — ``h`` is now identical between
        specimens (up to the same small matching noise as ``v``), so the
        candidate description is complete."""
        v_nominal = rng.normal(size=n_pairs)
        v_a = v_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)
        v_b = v_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)
        h_nominal = rng.normal(scale=self.hidden_std, size=n_pairs)
        h_a = h_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)
        h_b = h_nominal + rng.normal(scale=self.matching_noise_std, size=n_pairs)

        response_a = np.array([self.response(v_a[i], h_a[i], direction, rng) for i in range(n_pairs)])
        response_b = np.array([self.response(v_b[i], h_b[i], direction, rng) for i in range(n_pairs)])
        matched_diffs = np.stack([v_a - v_b, h_a - h_b], axis=1)
        return response_a, response_b, matched_diffs

    def response_jacobian_incomplete(self, direction: str) -> FloatArray:
        """``∂ρ/∂v`` only — the candidate description under test."""
        return np.array([self.a_coeff])

    def response_jacobian_complete(self, direction: str) -> FloatArray:
        """``∂ρ/∂v`` and ``∂ρ/∂h``."""
        sign = 1.0 if direction == "forward" else -1.0
        return np.array([self.a_coeff, self.hidden_coeff * sign])

    def repeat_variance(self, n_repeats: int, rng: np.random.Generator) -> float:
        """Fix ``(v, h, direction)``; repeat only the measurement noise —
        Spec §1.2's ``σ²_rep``."""
        responses = np.array([self.response(0.0, 0.0, "forward", rng) for _ in range(n_repeats)])
        return float(np.var(responses))

    def probe_set(self, h_a: float, h_b: float, v: float = 0.0) -> ProbeSet:
        """Both probes' responses for one matched pair, noise-free (for the
        OQ-1 fingerprint demonstration, which is about the deterministic
        structure of the effect, not sampling noise)."""
        forward_a = self.a_coeff * v + self.hidden_coeff * h_a
        forward_b = self.a_coeff * v + self.hidden_coeff * h_b
        reversed_a = self.a_coeff * v - self.hidden_coeff * h_a
        reversed_b = self.a_coeff * v - self.hidden_coeff * h_b
        return ProbeSet(forward_a, forward_b, reversed_a, reversed_b)

    def truth(self) -> float:
        """The constructed insufficiency variance for the incomplete
        candidate description: ``Var(h_a - h_b) = 2·hidden_std²``, scaled by
        the response coefficient — ``hidden_coeff² · 2 · hidden_std²``. Equal
        magnitude under either probe direction, which is the point (OQ-1)."""
        return self.hidden_coeff**2 * 2.0 * self.hidden_std**2
