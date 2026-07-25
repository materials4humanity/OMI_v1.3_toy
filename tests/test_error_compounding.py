"""Error compounding is bounded by the chain's memory structure, not its
length (Core §3.9 consequence 1): "Errors incurred before an erasure do not
propagate past it, to the extent the erasure is complete." Demonstrated
directly on the flagship chain (heating_and_soak is a declared erasure,
transfer is not), rather than on a synthetic oracle — this is an M2
deliverable ("error compounding... become measurable"), not a new module.
"""

from __future__ import annotations

import numpy as np

from omi.state import Metric, Slot

from omi_domains.flagship.build import build_chain, build_incoming_ensemble
from omi_domains.flagship.operators import TRANSFER


def test_perturbation_before_the_erasure_is_damped_at_the_terminal_state() -> None:
    rng = np.random.default_rng(0)
    incoming = build_incoming_ensemble(200, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()

    baseline_state = incoming[0]
    perturbation = 5.0 * metric.scale[incoming.schema.slice_for(Slot.M, "prior_deformation")][0]
    perturbed_state = baseline_state.with_component(
        Slot.M,
        "prior_deformation",
        baseline_state.get(Slot.M, "prior_deformation") + perturbation,
    )

    # Manually roll a single particle through the same two segments, so we
    # can compare one perturbed trajectory against its unperturbed baseline.
    final_baseline = baseline_state
    final_perturbed = perturbed_state
    for segment in chain.segments:
        final_baseline = segment.operator.step(final_baseline, segment.control)
        final_perturbed = segment.operator.step(final_perturbed, segment.control)

    terminal_distance = metric.distance(final_baseline, final_perturbed)
    # The perturbation itself was 5 sigma; if it survived undamped the
    # terminal distance would be of that order. Erasure should crush it.
    assert terminal_distance < 0.5


def test_perturbation_after_the_erasure_survives_to_the_terminal_state() -> None:
    """The same magnitude of perturbation, injected on a component the
    erasure does not touch and which survives it (inclusion_content, Core
    §7.1), applied *after* heating_and_soak — transfer does not damp it at
    all (its own declared rate for that component is 0), so it should reach
    the terminal state essentially undamped.
    """
    rng = np.random.default_rng(1)
    incoming = build_incoming_ensemble(200, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()
    heating_segment, transfer_segment = chain.segments
    assert transfer_segment.operator is TRANSFER

    post_heating_baseline = heating_segment.operator.step(incoming[0], heating_segment.control)
    perturbation = 5.0 * metric.scale[incoming.schema.slice_for(Slot.Z, "inclusion_content")][0]
    post_heating_perturbed = post_heating_baseline.with_component(
        Slot.Z,
        "inclusion_content",
        post_heating_baseline.get(Slot.Z, "inclusion_content") + perturbation,
    )

    final_baseline = transfer_segment.operator.step(post_heating_baseline, transfer_segment.control)
    final_perturbed = transfer_segment.operator.step(post_heating_perturbed, transfer_segment.control)

    terminal_distance = metric.distance(final_baseline, final_perturbed)
    # Undamped: the post-erasure perturbation should reach the terminal
    # state at essentially its full injected size (5 sigma in one
    # component), unlike the pre-erasure case above.
    assert terminal_distance > 4.5


def test_pre_erasure_damping_is_much_stronger_than_post_erasure_propagation() -> None:
    """The qualitative claim itself (CLAUDE.md §7 prefers orderings to
    decimals): pre-erasure perturbations are damped by orders of magnitude
    more than post-erasure ones, for the same injected size."""
    rng = np.random.default_rng(2)
    incoming = build_incoming_ensemble(200, rng)
    metric = Metric.from_ensemble(incoming)
    chain = build_chain()
    heating_segment, transfer_segment = chain.segments

    baseline_state = incoming[0]
    pre_perturbation = 5.0 * metric.scale[incoming.schema.slice_for(Slot.M, "prior_deformation")][0]
    pre_perturbed_state = baseline_state.with_component(
        Slot.M, "prior_deformation", baseline_state.get(Slot.M, "prior_deformation") + pre_perturbation
    )
    final_baseline = baseline_state
    final_pre_perturbed = pre_perturbed_state
    for segment in chain.segments:
        final_baseline = segment.operator.step(final_baseline, segment.control)
        final_pre_perturbed = segment.operator.step(final_pre_perturbed, segment.control)
    pre_erasure_distance = metric.distance(final_baseline, final_pre_perturbed)

    post_heating_baseline = heating_segment.operator.step(baseline_state, heating_segment.control)
    post_perturbation = 5.0 * metric.scale[incoming.schema.slice_for(Slot.Z, "inclusion_content")][0]
    post_heating_perturbed = post_heating_baseline.with_component(
        Slot.Z, "inclusion_content", post_heating_baseline.get(Slot.Z, "inclusion_content") + post_perturbation
    )
    final_post_baseline = transfer_segment.operator.step(post_heating_baseline, transfer_segment.control)
    final_post_perturbed = transfer_segment.operator.step(post_heating_perturbed, transfer_segment.control)
    post_erasure_distance = metric.distance(final_post_baseline, final_post_perturbed)

    assert post_erasure_distance > 100 * pre_erasure_distance
