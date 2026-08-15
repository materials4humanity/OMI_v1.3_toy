"""Crystallisation and formulation sketch (Spec §11.4, Core §7.3 [Pass D],
ROADMAP M10.1): batch cooling/antisolvent crystallisation, chosen because
polymorph selection is a genuinely bifurcating evolution operator and
dissolution is a natural Class B readout (docs/ROADMAP.md M10.1). Interface-
only per ADR-038 (docs/DECISIONS.md): no operators, no readouts, no build
function.

Written third specifically to test a prediction from E-21/E-22
(docs/V1.4-EDITS.md): Core §3.1 names supersaturation as its own worked
example of nu, and this domain's headline phenomenon (polymorph selection)
is itself supersaturation-driven, so nu is plausibly dominant here too. It
is -- see docs/SKETCHES.md's Crystallisation and formulation section and
E-22's addendum for the confirmed, three-domain finding.
"""

from __future__ import annotations

from omi.interface import InstantiationDeclaration, ParameterRole
from omi.state import Slot, StateSchema

CRYSTALLISATION_FORMULATION_SCHEMA = StateSchema(
    (
        (Slot.M, "particle_size_distribution_moments", 1),  # resolved: bulk PSD summary (laser diffraction)
        (Slot.M, "crystal_habit_descriptor", 1),  # resolved: aspect ratio/morphology from imaging
        (Slot.Z, "subcritical_nuclei_density", 1),  # sub-resolution: inferable only via induction-time dynamics
        (Slot.Z, "crystal_defect_density", 1),  # sub-resolution: dislocation/inclusion accumulation
        (Slot.NU, "supersaturation", 1),  # nonlocal: Core §3.1's own named example of nu
        (Slot.GAMMA, "crystal_surface_state", 1),  # controls dissolution rate and further growth
    )
)
"""One representative-batch, well-mixed-limit state. `supersaturation`
(nu) is Core §3.1's own worked example of a nonlocal/self-consistent
field, and -- confirmed here, the third domain in a row -- is plausibly
this domain's *dominant* slot: polymorph selection, the phenomenon this
sketch is chosen to test, is itself supersaturation-driven (classical
nucleation theory; Ostwald's rule of stages). See docs/V1.4-EDITS.md
E-22's addendum.
"""

CRYSTALLISATION_FORMULATION_DECLARATION = InstantiationDeclaration(
    state_schema=CRYSTALLISATION_FORMULATION_SCHEMA,
    declared_parameters=(
        ParameterRole(
            name="compound_and_solvent_system",
            indexes=(
                "crystal_growth_constitutive",
                "full_dissolution_recrystallization",
                "dissolution_time_to_90pct",
            ),
            justification=(
                "The predicted hard case, and it fills SUBSTANTIVELY rather than formally -- "
                "docs/ARITY-REDESIGN-BRIEF.md §4 named this sketch as the one likely to force "
                "either a real new declaration or a stated inability, on the grounds that a "
                "formulation's composition is exactly the quantity E-46 separates. It is a real "
                "declaration. The molecule's identity together with the solvent/antisolvent pair "
                "is fixed per formulation and decides WHICH POLYMORPHS EXIST AT ALL, which is a "
                "stronger form of operator-family indexing than a rate-constant shift: it fixes "
                "the discrete outcome set the bifurcating selection operator chooses among. "
                "Against E-46's four properties: nothing transports it, no in-line Raman/FBRM "
                "channel assimilates it, no per-crystal value exists for it, and it answers which "
                "member of the nucleation-and-growth family applies. "
                "The distinction this makes available and item 1 alone could not: the polymorph "
                "LANDSCAPE is a fixed index (1b) while the polymorph SELECTED on a given batch is "
                "an outcome of the evolution (item 1a's state, via supersaturation in nu). Those "
                "are different claims about the same word."
            ),
        ),
    ),
    control_space=(
        "Apparatus-controlled: cooling-rate profile, antisolvent addition "
        "rate, and seeding schedule as a time-dependent recipe. U_adm "
        "bounded by the crystalliser's equipment limits. A control "
        "(process) inverse exists: target polymorph/particle-size "
        "distribution -> cooling/seeding recipe -- a live crystallisation-"
        "process-design problem. Polymorph selection is a genuinely "
        "bifurcating evolution operator (small perturbations near the "
        "metastable-zone boundary select qualitatively different "
        "outcomes), which Core §3.9's own expansive-regime clause already "
        "names directly ('predict the invariant or the bifurcation label "
        "rather than the trajectory') -- this sketch does not strain "
        "against that clause, it is the clearest real-world instance of "
        "it found so far."
    ),
    erasure_inventory=("full_dissolution_recrystallization",),
    readout_catalogue=(
        "bulk_yield_mean: Type-0/Class-A",
        "crystal_growth_constitutive: Type-1",
        "dissolution_time_to_90pct: Type-0/Class-B; process-zone volume = "
        "the finished batch's particle population, fixed at evaluation "
        "time (dissolution testing runs on an isolated, dried sample, not "
        "the growing in-process population). "
        "Item 4b (Core §4): driver field = local particle-surface "
        "dissolution flux, correlated with the particle-size-distribution "
        "field; defect population = independently measured particle-size "
        "distribution (laser diffraction; heavy-tailed coarse fraction); "
        "physics map Psi = Noyes-Whitney/Hixson-Crowell dissolution "
        "kinetics (dissolution time proportional to particle radius "
        "squared for diffusion-limited dissolution), exponent read "
        "directly from that textbook model, not invented inside "
        "omi.classb.",
    ),
    observation_suite=(
        "in-line FBRM (focused beam reflectance -- real-time particle "
        "count/chord-length)",
        "in-line Raman/NIR spectroscopy (real-time polymorph "
        "identification and supersaturation monitoring)",
        "at-line laser diffraction (particle size distribution)",
    ),
    invariants=(
        "solute_mass_conservation_across_crystallisation",
        "cumulative_crystallised_mass_monotone_nondecreasing",
    ),
    scale_structure=(
        "Tier I only: a single representative-batch, well-mixed-limit "
        "population-balance-style state (classical supersaturation-driven "
        "growth/nucleation kinetics). Tier II (spatially-resolved CFD-"
        "coupled population balance, capturing genuine within-vessel "
        "supersaturation gradients in imperfectly-mixed crystallisers) "
        "remains an anti-goal per CLAUDE.md §9."
    ),
)
