"""Neural operators as a pluggable approximation class: a DeepONet-style
branch/trunk network behind the `EvolutionOperator` protocol, its training
(data fidelity, multi-step pushforward, noise injection, semigroup-
consistency, spectral-norm control), and grouped train/test splitting.

Cites Core §3.9 (the interchangeable approximation class) and Spec §2 in
full: §2.1 the approximation class and its caveats, §2.3 training
objectives, §2.4 stability-aware training. ADR-029 (docs/DECISIONS.md)
fixes the architecture (branch/trunk, adapted to a finite output dimension)
and the decision to implement entirely in numpy, with no torch dependency
anywhere in this milestone. §2.5-2.7 remain `[Pass B]` and are not
implemented here (docs/ROADMAP.md M8: "Refuse").

CLAUDE.md §1: the neural operators are not the point, they are one
interchangeable approximation class — every analytic operator this module
trains against remains the test oracle (ADR-001).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from omi.operators import Control, EvolutionOperator
from omi.state import FloatArray, State

Layer = tuple[FloatArray, FloatArray]
"""One MLP layer: `(W, b)` with `W` shape `(out, in)`, `b` shape `(out,)`."""

_LayerCache = tuple[FloatArray, FloatArray, FloatArray]
"""Per-layer forward cache: `(input, pre_activation, post_activation)`."""


def _init_mlp_layers(sizes: Sequence[int], rng: np.random.Generator) -> tuple[Layer, ...]:
    """He-scaled random initialisation (`W ~ N(0, 1/fan_in)`), a standard,
    uncited-number-free default for a `tanh`-activated network (Spec §2.1:
    the architecture is a stated design choice, not a framework claim)."""
    layers = []
    for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
        w = rng.normal(0.0, 1.0 / np.sqrt(fan_in), size=(fan_out, fan_in))
        b = np.zeros(fan_out)
        layers.append((w, b))
    return tuple(layers)


def _mlp_forward(
    x: FloatArray, layers: Sequence[Layer], final_linear: bool
) -> tuple[FloatArray, list[_LayerCache]]:
    """Forward pass through an MLP, caching each layer's input and pre/post
    activation for :func:`_mlp_jacobian_from_cache` and :func:`_mlp_backward`."""
    cache: list[_LayerCache] = []
    a = x
    n_layers = len(layers)
    for i, (w, b) in enumerate(layers):
        a_prev = a
        z = w @ a_prev + b
        is_last = i == n_layers - 1
        a = z if (is_last and final_linear) else np.tanh(z)
        cache.append((a_prev, z, a))
    return a, cache


def _mlp_jacobian_from_cache(cache: Sequence[_LayerCache], layers: Sequence[Layer], final_linear: bool) -> FloatArray:
    """The MLP's exact Jacobian with respect to its input (Core §3.3's
    `F_k`; here, the learned operator's own tangent map), by chaining each
    layer's exact Jacobian `diag(tanh'(z)) @ W` — the network is a fixed,
    small differentiable function, so this is exact, not a finite-
    difference estimate (ADR-001's principle applied to a learned operator's
    own forward function)."""
    n_in = cache[0][0].shape[0]
    jac = np.eye(n_in)
    n_layers = len(layers)
    for i, (w, _b) in enumerate(layers):
        _a_prev, z, _a = cache[i]
        is_last = i == n_layers - 1
        if is_last and final_linear:
            layer_jac = w
        else:
            dact = 1.0 - np.tanh(z) ** 2
            layer_jac = dact[:, np.newaxis] * w
        jac = layer_jac @ jac
    return jac


def _mlp_backward(
    d_out: FloatArray, layers: Sequence[Layer], cache: Sequence[_LayerCache], final_linear: bool
) -> tuple[list[Layer], FloatArray]:
    """Reverse-mode backprop (Spec §2.3's training objectives require
    gradient-based fitting; this is the from-scratch numpy implementation
    ADR-029 commits to instead of a torch dependency): given `d(loss)/d(out)`,
    returns per-layer `(dW, db)` and `d(loss)/d(input)`."""
    grads: list[Layer] = []
    delta = d_out
    n_layers = len(layers)
    for i in reversed(range(n_layers)):
        w, _b = layers[i]
        a_prev, _z, a = cache[i]
        is_last = i == n_layers - 1
        delta_z = delta if (is_last and final_linear) else delta * (1.0 - a**2)
        d_w = np.outer(delta_z, a_prev)
        d_b = delta_z
        grads.append((d_w, d_b))
        delta = w.T @ delta_z
    grads.reverse()
    return grads, delta


@dataclass(frozen=True)
class DeepONetParams:
    """A branch/trunk network's parameters (Spec §2.1's approximation
    class; ADR-029): the branch encodes `(state, control, dt)` into a
    latent code; the trunk encodes each of `state_dim` output-component
    indices (one-hot) into a latent code of the same dimension; the output
    is their inner product plus a bias."""

    branch_layers: tuple[Layer, ...]
    trunk_layers: tuple[Layer, ...]
    output_bias: FloatArray
    state_dim: int
    control_dim: int
    latent_dim: int


def init_deeponet_params(
    state_dim: int,
    control_dim: int,
    rng: np.random.Generator,
    latent_dim: int = 16,
    hidden_dim: int = 16,
) -> DeepONetParams:
    """Initialise a :class:`DeepONetParams` (Spec §2.1; ADR-029): branch
    input is `state_dim + control_dim + 1` (state, control, `dt`); trunk
    input is `state_dim` (one-hot query index)."""
    branch_layers = _init_mlp_layers(
        [state_dim + control_dim + 1, hidden_dim, hidden_dim, latent_dim], rng
    )
    trunk_layers = _init_mlp_layers([state_dim, hidden_dim, latent_dim], rng)
    output_bias = np.zeros(state_dim)
    return DeepONetParams(branch_layers, trunk_layers, output_bias, state_dim, control_dim, latent_dim)


def _branch_input(params: DeepONetParams, state_values: FloatArray, control: Control) -> FloatArray:
    u = control(control.t0)
    dt = np.array([control.duration])
    return np.concatenate([state_values, u, dt])


_StepCache = tuple[FloatArray, list[_LayerCache], FloatArray, list[list[_LayerCache]], FloatArray]
"""``(branch_input, branch_cache, T, trunk_caches, branch_output)``."""


def _apply_step_with_cache(
    params: DeepONetParams, state_values: FloatArray, control: Control
) -> tuple[FloatArray, _StepCache]:
    """One branch/trunk forward pass (ADR-029), caching everything
    :func:`_backward_step` needs."""
    branch_input = _branch_input(params, state_values, control)
    b_out, branch_cache = _mlp_forward(branch_input, params.branch_layers, final_linear=True)

    n = params.state_dim
    trunk_caches: list[list[_LayerCache]] = []
    t_rows = []
    for j in range(n):
        query = np.zeros(n)
        query[j] = 1.0
        t_out, t_cache = _mlp_forward(query, params.trunk_layers, final_linear=False)
        trunk_caches.append(t_cache)
        t_rows.append(t_out)
    t_matrix = np.stack(t_rows, axis=0)

    output = t_matrix @ b_out + params.output_bias
    return output, (branch_input, branch_cache, t_matrix, trunk_caches, b_out)


@dataclass
class Grads:
    """Gradients (or Adam moment estimates) for Spec §2.3's training
    objectives, shaped exactly like :class:`DeepONetParams` — a plain,
    mutable parallel structure so :func:`_accumulate` and :func:`_adam_step`
    need no untyped dict access."""

    branch: list[Layer]
    trunk: list[Layer]
    bias: FloatArray


def _zero_grads(params: DeepONetParams) -> Grads:
    branch = [(np.zeros_like(w), np.zeros_like(b)) for w, b in params.branch_layers]
    trunk = [(np.zeros_like(w), np.zeros_like(b)) for w, b in params.trunk_layers]
    bias = np.zeros_like(params.output_bias)
    return Grads(branch, trunk, bias)


def _accumulate(grads: Grads, branch: list[Layer], trunk: list[Layer], bias: FloatArray) -> None:
    for idx, (d_w, d_b) in enumerate(branch):
        grads.branch[idx] = (grads.branch[idx][0] + d_w, grads.branch[idx][1] + d_b)
    for idx, (d_w, d_b) in enumerate(trunk):
        grads.trunk[idx] = (grads.trunk[idx][0] + d_w, grads.trunk[idx][1] + d_b)
    grads.bias = grads.bias + bias


def _backward_step(
    params: DeepONetParams, d_output: FloatArray, cache: _StepCache
) -> tuple[list[Layer], list[Layer], FloatArray, FloatArray]:
    """Backprop through one branch/trunk forward call: returns
    `(branch_grads, trunk_grads, bias_grad, d_input_state)`, the last being
    the gradient with respect to this step's *input state* — what a
    multi-step (pushforward) or semigroup-consistency computation chains
    into the previous step's output (ADR-029)."""
    _branch_input_value, branch_cache, t_matrix, trunk_caches, b_out = cache
    d_b = t_matrix.T @ d_output
    d_t = np.outer(d_output, b_out)
    bias_grad = d_output.copy()

    branch_grads, d_branch_input = _mlp_backward(d_b, params.branch_layers, branch_cache, final_linear=True)

    trunk_grads = [(np.zeros_like(w), np.zeros_like(b)) for w, b in params.trunk_layers]
    for j in range(params.state_dim):
        t_layer_grads, _d_query = _mlp_backward(d_t[j], params.trunk_layers, trunk_caches[j], final_linear=False)
        for idx, (d_w, d_b_) in enumerate(t_layer_grads):
            trunk_grads[idx] = (trunk_grads[idx][0] + d_w, trunk_grads[idx][1] + d_b_)

    d_input_state = d_branch_input[: params.state_dim]
    return branch_grads, trunk_grads, bias_grad, d_input_state


@dataclass(frozen=True)
class DeepONetOperator(EvolutionOperator):
    """A trained (or untrained) branch/trunk network behind the
    `EvolutionOperator` protocol (Core §3.3; ADR-029): the pluggable
    approximation class docs/ROADMAP.md M8 calls for. `is_erasure` is
    declared by whatever this instance stands in for, per ADR-012 — a
    learned operator does not discover erasure, it approximates a specific
    analytic operator that already declares it.
    """

    params: DeepONetParams
    erasure: bool = False

    @property
    def is_erasure(self) -> bool:
        """Declared by the caller (ADR-012), not discovered (Core §3.9)."""
        return self.erasure

    def step(self, state: State, control: Control) -> State:
        """The branch/trunk forward pass (Core §3.3; Spec §2.1)."""
        output, _cache = _apply_step_with_cache(self.params, state.values, control)
        return State(state.schema, output)

    def jacobian(self, state: State, control: Control) -> FloatArray:
        """The network's exact tangent map (Core §3.3's `F_k`), via
        :func:`_mlp_jacobian_from_cache` — not a finite-difference estimate."""
        branch_input = _branch_input(self.params, state.values, control)
        _b_out, branch_cache = _mlp_forward(branch_input, self.params.branch_layers, final_linear=True)
        branch_jac = _mlp_jacobian_from_cache(branch_cache, self.params.branch_layers, final_linear=True)
        branch_jac_wrt_state = branch_jac[:, : self.params.state_dim]

        n = self.params.state_dim
        t_rows = []
        for j in range(n):
            query = np.zeros(n)
            query[j] = 1.0
            t_out, _t_cache = _mlp_forward(query, self.params.trunk_layers, final_linear=False)
            t_rows.append(t_out)
        t_matrix = np.stack(t_rows, axis=0)

        return t_matrix @ branch_jac_wrt_state


@dataclass(frozen=True)
class TrainingRecord:
    """One multi-step training example (Spec §2.4's pushforward training):
    a labelled short rollout, grouped by provenance so
    :func:`grouped_train_test_split` can enforce CLAUDE.md §5 invariant 6."""

    group_id: str
    initial_state: FloatArray
    controls: tuple[Control, ...]
    true_trajectory: tuple[FloatArray, ...]
    """Length ``len(controls) + 1``; ``true_trajectory[0]`` is
    `initial_state`."""


def grouped_train_test_split(
    records: Sequence[TrainingRecord], test_fraction: float, rng: np.random.Generator
) -> tuple[list[TrainingRecord], list[TrainingRecord]]:
    """Split by `group_id`, never by record (Spec §9.3: "Never randomly.
    Group by provenance unit, batch, campaign and composition family";
    CLAUDE.md §5 invariant 6: "enforced at the data-loader level so a random
    split is structurally impossible") — every record from one group lands
    entirely in train or entirely in test.
    """
    groups = sorted({r.group_id for r in records})
    order = rng.permutation(len(groups))
    shuffled = [groups[i] for i in order]
    n_test_groups = max(1, int(round(len(shuffled) * test_fraction))) if shuffled else 0
    test_groups = set(shuffled[:n_test_groups])
    train = [r for r in records if r.group_id not in test_groups]
    test = [r for r in records if r.group_id in test_groups]
    return train, test


def _record_loss_and_grads(
    params: DeepONetParams, record: TrainingRecord, noise_std: float, rng: np.random.Generator
) -> tuple[float, Grads]:
    """Multi-step pushforward loss and gradients for one record (Spec §2.4:
    "training MUST target rollout accuracy, not one-step accuracy" —
    ``current`` is always the *model's own* previous prediction, truncated
    backpropagation through the record's own length): mean squared error
    over every step, differentiated back through the whole rollout.
    Gaussian noise (Spec §2.4) is added to the initial condition.
    """
    current = record.initial_state.copy()
    if noise_std > 0.0:
        current = current + rng.normal(0.0, noise_std, size=current.shape)

    step_caches: list[tuple[_StepCache, FloatArray]] = []
    total_loss = 0.0
    for k, control in enumerate(record.controls):
        output, cache = _apply_step_with_cache(params, current, control)
        target = record.true_trajectory[k + 1]
        diff = output - target
        total_loss += float(np.mean(diff**2))
        step_caches.append((cache, diff))
        current = output

    grads = _zero_grads(params)
    d_next_state = np.zeros(params.state_dim)
    n_steps = len(record.controls)
    for k in reversed(range(n_steps)):
        cache, diff = step_caches[k]
        # The returned loss averages each step's mean-squared-error over
        # n_steps, so every step's direct contribution to the gradient
        # needs that same 1/n_steps factor — d_next_state, arriving from a
        # later step's already-scaled d_output, needs no extra factor here.
        d_output = (2.0 / (params.state_dim * n_steps)) * diff + d_next_state
        branch_grads, trunk_grads, bias_grad, d_input_state = _backward_step(params, d_output, cache)
        _accumulate(grads, branch_grads, trunk_grads, bias_grad)
        d_next_state = d_input_state

    return total_loss / max(n_steps, 1), grads


def _semigroup_consistency_loss_and_grads(
    params: DeepONetParams, state_values: FloatArray, whole_control: Control, first_control: Control, second_control: Control
) -> tuple[float, Grads]:
    """Spec §2.3's semigroup-consistency training term (Core §3.3's
    identity, applied to the *learned* operator itself, not against
    external data): penalises the discrepancy between applying the network
    once over the whole interval and applying it twice over the split
    sub-intervals — differentiated through both computation paths, since
    both depend on the same parameters.
    """
    direct_out, direct_cache = _apply_step_with_cache(params, state_values, whole_control)
    mid_out, mid_cache = _apply_step_with_cache(params, state_values, first_control)
    composed_out, composed_cache = _apply_step_with_cache(params, mid_out, second_control)

    diff = direct_out - composed_out
    loss = float(np.mean(diff**2))
    n = params.state_dim
    d_direct = (2.0 / n) * diff
    d_composed = -(2.0 / n) * diff

    grads = _zero_grads(params)
    branch_grads, trunk_grads, bias_grad, _ = _backward_step(params, d_direct, direct_cache)
    _accumulate(grads, branch_grads, trunk_grads, bias_grad)
    branch_grads2, trunk_grads2, bias_grad2, d_mid = _backward_step(params, d_composed, composed_cache)
    _accumulate(grads, branch_grads2, trunk_grads2, bias_grad2)
    branch_grads3, trunk_grads3, bias_grad3, _ = _backward_step(params, d_mid, mid_cache)
    _accumulate(grads, branch_grads3, trunk_grads3, bias_grad3)

    return loss, grads


@dataclass(frozen=True)
class _AdamState:
    m: Grads
    v: Grads
    t: int


def _adam_init(params: DeepONetParams) -> _AdamState:
    return _AdamState(_zero_grads(params), _zero_grads(params), 0)


def _adam_step(
    params: DeepONetParams,
    grads: Grads,
    state: _AdamState,
    learning_rate: float,
    spectral_cap: float | None,
    beta1: float = 0.9,
    beta2: float = 0.999,
    eps: float = 1e-8,
) -> tuple[DeepONetParams, _AdamState]:
    """One Adam update step (Kingma & Ba 2015 — a standard, named optimiser,
    not an invented convention), followed by Spec §2.4's "spectral
    normalisation or explicit Lipschitz control": every weight matrix whose
    spectral norm exceeds *spectral_cap* is rescaled down to it.
    """
    t = state.t + 1

    def _update_layers(
        layers: tuple[Layer, ...], grad_layers: list[Layer], m_layers: list[Layer], v_layers: list[Layer]
    ) -> tuple[tuple[Layer, ...], list[Layer], list[Layer]]:
        new_layers = []
        new_m = []
        new_v = []
        for (w, b), (d_w, d_b), (m_w, m_b), (v_w, v_b) in zip(layers, grad_layers, m_layers, v_layers):
            m_w2 = beta1 * m_w + (1 - beta1) * d_w
            m_b2 = beta1 * m_b + (1 - beta1) * d_b
            v_w2 = beta2 * v_w + (1 - beta2) * d_w**2
            v_b2 = beta2 * v_b + (1 - beta2) * d_b**2
            m_hat_w = m_w2 / (1 - beta1**t)
            m_hat_b = m_b2 / (1 - beta1**t)
            v_hat_w = v_w2 / (1 - beta2**t)
            v_hat_b = v_b2 / (1 - beta2**t)
            new_w = w - learning_rate * m_hat_w / (np.sqrt(v_hat_w) + eps)
            new_b = b - learning_rate * m_hat_b / (np.sqrt(v_hat_b) + eps)
            if spectral_cap is not None:
                spectral_norm = np.linalg.norm(new_w, ord=2)
                if spectral_norm > spectral_cap:
                    new_w = new_w * (spectral_cap / spectral_norm)
            new_layers.append((new_w, new_b))
            new_m.append((m_w2, m_b2))
            new_v.append((v_w2, v_b2))
        return tuple(new_layers), new_m, new_v

    new_branch, new_m_branch, new_v_branch = _update_layers(
        params.branch_layers, grads.branch, state.m.branch, state.v.branch
    )
    new_trunk, new_m_trunk, new_v_trunk = _update_layers(
        params.trunk_layers, grads.trunk, state.m.trunk, state.v.trunk
    )

    new_m_bias = beta1 * state.m.bias + (1 - beta1) * grads.bias
    new_v_bias = beta2 * state.v.bias + (1 - beta2) * grads.bias**2
    m_hat_bias = new_m_bias / (1 - beta1**t)
    v_hat_bias = new_v_bias / (1 - beta2**t)
    new_bias = params.output_bias - learning_rate * m_hat_bias / (np.sqrt(v_hat_bias) + eps)

    new_params = DeepONetParams(new_branch, new_trunk, new_bias, params.state_dim, params.control_dim, params.latent_dim)
    new_state = _AdamState(
        Grads(new_m_branch, new_m_trunk, new_m_bias),
        Grads(new_v_branch, new_v_trunk, new_v_bias),
        t,
    )
    return new_params, new_state


@dataclass(frozen=True)
class TrainingReport:
    """Loss trajectory (Spec §2.4: "error as a function of rollout length
    MUST be reported" — this is the *training* loss curve; the *rollout-
    length* curve itself is `omi.conformance.rollout_length_error_curve`,
    reused unchanged against a trained `DeepONetOperator`)."""

    data_fidelity_loss: tuple[float, ...]
    semigroup_consistency_loss: tuple[float, ...]


def train_deeponet(
    params: DeepONetParams,
    records: Sequence[TrainingRecord],
    rng: np.random.Generator,
    n_epochs: int = 200,
    learning_rate: float = 0.01,
    noise_std: float = 0.0,
    spectral_cap: float | None = 4.0,
    semigroup_weight: float = 0.1,
    semigroup_probe: tuple[FloatArray, Control, Control, Control] | None = None,
) -> tuple[DeepONetParams, TrainingReport]:
    """Train a :class:`DeepONetParams` by full-batch Adam (Spec §2.3's data-
    fidelity term, via :func:`_record_loss_and_grads`'s multi-step
    pushforward loss over *records*, plus Spec §2.3's semigroup-consistency
    term via :func:`_semigroup_consistency_loss_and_grads` when
    *semigroup_probe* is given — `(state, whole_control, first_control,
    second_control)`, the same split-interval convention
    `operators.semigroup_residual` checks at evaluation time). Spec §2.4's
    noise injection and spectral-norm cap are applied every step (ADR-029).
    """
    adam_state = _adam_init(params)
    data_losses = []
    semigroup_losses = []

    for _epoch in range(n_epochs):
        grads = _zero_grads(params)
        epoch_data_loss = 0.0
        for record in records:
            loss, record_grads = _record_loss_and_grads(params, record, noise_std, rng)
            epoch_data_loss += loss
            _accumulate(grads, record_grads.branch, record_grads.trunk, record_grads.bias)
        epoch_data_loss /= max(len(records), 1)

        epoch_semigroup_loss = 0.0
        if semigroup_probe is not None and semigroup_weight > 0.0:
            state_values, whole_control, first_control, second_control = semigroup_probe
            sg_loss, sg_grads = _semigroup_consistency_loss_and_grads(
                params, state_values, whole_control, first_control, second_control
            )
            epoch_semigroup_loss = sg_loss
            weighted_branch = [(w * semigroup_weight, b * semigroup_weight) for w, b in sg_grads.branch]
            weighted_trunk = [(w * semigroup_weight, b * semigroup_weight) for w, b in sg_grads.trunk]
            weighted_bias = sg_grads.bias * semigroup_weight
            _accumulate(grads, weighted_branch, weighted_trunk, weighted_bias)

        params, adam_state = _adam_step(params, grads, adam_state, learning_rate, spectral_cap)
        data_losses.append(epoch_data_loss)
        semigroup_losses.append(epoch_semigroup_loss)

    return params, TrainingReport(tuple(data_losses), tuple(semigroup_losses))
