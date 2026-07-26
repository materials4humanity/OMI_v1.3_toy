"""Gradient check: the hand-rolled backprop in `omi.learning` (ADR-029,
docs/DECISIONS.md — no torch dependency, so this is the only correctness
check these gradients get) must match finite differences, for both the
multi-step pushforward loss (Spec §2.4) and the semigroup-consistency loss
(Spec §2.3).
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from omi.learning import (
    DeepONetParams,
    Layer,
    _record_loss_and_grads,
    _semigroup_consistency_loss_and_grads,
    init_deeponet_params,
    TrainingRecord,
)
from omi.operators import Control
from omi.state import FloatArray

EPS = 1e-5


def _perturb_branch_layer(params: DeepONetParams, layer_index: int, new_layer: Layer) -> DeepONetParams:
    branch = params.branch_layers[:layer_index] + (new_layer,) + params.branch_layers[layer_index + 1 :]
    return DeepONetParams(branch, params.trunk_layers, params.output_bias, params.state_dim, params.control_dim, params.latent_dim)


def _perturb_trunk_layer(params: DeepONetParams, layer_index: int, new_layer: Layer) -> DeepONetParams:
    trunk = params.trunk_layers[:layer_index] + (new_layer,) + params.trunk_layers[layer_index + 1 :]
    return DeepONetParams(params.branch_layers, trunk, params.output_bias, params.state_dim, params.control_dim, params.latent_dim)


def _numeric_weight_gradient(
    loss_fn: Callable[[DeepONetParams], float], params: DeepONetParams, layer_index: int, is_branch: bool
) -> FloatArray:
    layers = params.branch_layers if is_branch else params.trunk_layers
    w, b = layers[layer_index]
    perturb = _perturb_branch_layer if is_branch else _perturb_trunk_layer
    numeric = np.zeros_like(w)
    for i in range(w.shape[0]):
        for j in range(w.shape[1]):
            w_plus = w.copy()
            w_plus[i, j] += EPS
            loss_plus = loss_fn(perturb(params, layer_index, (w_plus, b)))
            w_minus = w.copy()
            w_minus[i, j] -= EPS
            loss_minus = loss_fn(perturb(params, layer_index, (w_minus, b)))
            numeric[i, j] = (loss_plus - loss_minus) / (2 * EPS)
    return numeric


def _make_params_and_record() -> tuple[DeepONetParams, TrainingRecord]:
    rng = np.random.default_rng(0)
    state_dim, control_dim = 3, 1
    params = init_deeponet_params(state_dim, control_dim, rng, latent_dim=4, hidden_dim=5)
    control1 = Control(0.0, 1.0, lambda t: np.array([2.0]))
    control2 = Control(0.0, 0.5, lambda t: np.array([1.0]))
    initial = rng.normal(0.0, 1.0, state_dim)
    true_trajectory = (initial, initial + 0.1, initial + 0.2)
    record = TrainingRecord("g1", initial, (control1, control2), true_trajectory)
    return params, record


def test_multistep_pushforward_branch_gradient_matches_finite_difference() -> None:
    params, record = _make_params_and_record()
    _loss, grads = _record_loss_and_grads(params, record, noise_std=0.0, rng=np.random.default_rng(0))

    def loss_fn(p: DeepONetParams) -> float:
        loss, _ = _record_loss_and_grads(p, record, noise_std=0.0, rng=np.random.default_rng(0))
        return loss

    numeric = _numeric_weight_gradient(loss_fn, params, layer_index=0, is_branch=True)
    assert np.max(np.abs(grads.branch[0][0] - numeric)) < 1e-8


def test_multistep_pushforward_trunk_gradient_matches_finite_difference() -> None:
    params, record = _make_params_and_record()
    _loss, grads = _record_loss_and_grads(params, record, noise_std=0.0, rng=np.random.default_rng(0))

    def loss_fn(p: DeepONetParams) -> float:
        loss, _ = _record_loss_and_grads(p, record, noise_std=0.0, rng=np.random.default_rng(0))
        return loss

    numeric = _numeric_weight_gradient(loss_fn, params, layer_index=0, is_branch=False)
    assert np.max(np.abs(grads.trunk[0][0] - numeric)) < 1e-8


def test_multistep_pushforward_bias_gradient_matches_finite_difference() -> None:
    params, record = _make_params_and_record()
    _loss, grads = _record_loss_and_grads(params, record, noise_std=0.0, rng=np.random.default_rng(0))

    numeric = np.zeros_like(params.output_bias)
    for i in range(params.output_bias.shape[0]):
        bias_plus = params.output_bias.copy()
        bias_plus[i] += EPS
        params_plus = DeepONetParams(
            params.branch_layers, params.trunk_layers, bias_plus, params.state_dim, params.control_dim, params.latent_dim
        )
        loss_plus, _ = _record_loss_and_grads(params_plus, record, 0.0, np.random.default_rng(0))

        bias_minus = params.output_bias.copy()
        bias_minus[i] -= EPS
        params_minus = DeepONetParams(
            params.branch_layers, params.trunk_layers, bias_minus, params.state_dim, params.control_dim, params.latent_dim
        )
        loss_minus, _ = _record_loss_and_grads(params_minus, record, 0.0, np.random.default_rng(0))

        numeric[i] = (loss_plus - loss_minus) / (2 * EPS)

    assert np.max(np.abs(grads.bias - numeric)) < 1e-8


def test_semigroup_consistency_branch_gradient_matches_finite_difference() -> None:
    rng = np.random.default_rng(0)
    state_dim, control_dim = 3, 1
    params = init_deeponet_params(state_dim, control_dim, rng, latent_dim=4, hidden_dim=5)
    whole = Control(0.0, 1.0, lambda t: np.array([2.0]))
    first = Control(0.0, 0.5, lambda t: np.array([2.0]))
    second = Control(0.5, 1.0, lambda t: np.array([2.0]))
    state_values = rng.normal(0.0, 1.0, state_dim)

    _loss, grads = _semigroup_consistency_loss_and_grads(params, state_values, whole, first, second)

    def loss_fn(p: DeepONetParams) -> float:
        loss, _ = _semigroup_consistency_loss_and_grads(p, state_values, whole, first, second)
        return loss

    numeric = _numeric_weight_gradient(loss_fn, params, layer_index=0, is_branch=True)
    assert np.max(np.abs(grads.branch[0][0] - numeric)) < 1e-7
