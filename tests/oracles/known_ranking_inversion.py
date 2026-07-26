"""The known-ranking-inversion oracle (CLAUDE.md §7; docs/ROADMAP.md M6): two
materials whose specimen-thickness ranking flips as the process-zone
thickness sweeps across their differing driver correlation lengths — the
quantitative content of Core §3.6's claim that "the two-tier formulation
explains why rankings invert between specimen thicknesses" (Spec §4.4,
Proposition 4.2).

Construction: both materials share the weakest-link formula
``P_fail = 1 - (1 - p0)**N_eff`` (Spec §4.1's object, in its simplest
per-unit form), but differ in *both* their driver correlation length
``ℓ_D`` and their per-unit severity ``p0`` — Proposition 4.2's dimensional
reduction (``N_eff`` shrinking with volume more slowly once ``ℓ_D`` exceeds
the process-zone thickness) changes each material's effective count at a
different thickness, so a material with many, individually-mild weak links
can be overtaken by a material with few, individually-severe ones once
reduction engages differently for each.
"""

from __future__ import annotations

from dataclasses import dataclass

from omi.classb import n_eff

VOLUME = 1000.0

MATERIAL_A_CORRELATION_LENGTH = 0.2
MATERIAL_A_UNIT_SEVERITY = 1e-5

MATERIAL_B_CORRELATION_LENGTH = 3.0
MATERIAL_B_UNIT_SEVERITY = 1e-2

THICK_ZONE_THICKNESS = 5.0
THIN_ZONE_THICKNESS = 0.5


@dataclass(frozen=True)
class KnownRankingInversionOracle:
    """Cites CLAUDE.md §7's oracle philosophy and docs/ROADMAP.md M6's
    "ranking inversion reproduces" exit-gate requirement."""

    volume: float = VOLUME
    correlation_length_a: float = MATERIAL_A_CORRELATION_LENGTH
    severity_a: float = MATERIAL_A_UNIT_SEVERITY
    correlation_length_b: float = MATERIAL_B_CORRELATION_LENGTH
    severity_b: float = MATERIAL_B_UNIT_SEVERITY

    def failure_probability(
        self, material: str, process_zone_thickness: float
    ) -> float:
        """``P_fail = 1 - (1 - p0)**N_eff`` at a declared process-zone
        thickness (Spec §4.1's object; :func:`~omi.classb.n_eff` supplies
        the dimensionally-reduced count, Proposition 4.2)."""
        if material == "A":
            ell, p0 = self.correlation_length_a, self.severity_a
        elif material == "B":
            ell, p0 = self.correlation_length_b, self.severity_b
        else:
            raise ValueError(f"unknown material {material!r}")
        count = n_eff(self.volume, ell, process_zone_thickness)
        return float(1.0 - (1.0 - p0) ** count)

    def truth(self) -> tuple[float, float]:
        """The two process-zone thicknesses at which this oracle is
        constructed to show opposite rankings: ``(thick, thin)`` —
        material A is the weaker (higher failure probability) specimen at
        the thick zone, material B at the thin zone."""
        return THICK_ZONE_THICKNESS, THIN_ZONE_THICKNESS
