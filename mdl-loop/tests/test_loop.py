import math

import numpy as np
import pytest

from mdl_loop.schema import RunRecord, AlkaliDose, completeness, typical_literature_record
from mdl_loop.space import P0_SPACE, LITERATURE_RECIPE
from mdl_loop.emulator import VirtualKesterite, NoiseModel, VOC_SQ_EV
from mdl_loop.lab import Lab, to_record
from mdl_loop.strategies import OVAT, GPBO
from mdl_loop.campaign import welch_one_sided, power_table, Job, run_job


def test_space_roundtrip_and_bounds():
    rng = np.random.default_rng(0)
    for x in P0_SPACE.sample(rng, 50):
        u = P0_SPACE.encode(x)
        assert u.shape == (P0_SPACE.dim,) and np.all(u >= -1e-9) and np.all(u <= 1 + 1e-9)
    assert P0_SPACE["anneal_c"].hi <= 560          # P0 thermal budget
    p = P0_SPACE["se_mg"]
    assert p.from_unit(p.to_unit(200.0)) == pytest.approx(200.0)


def test_run_level_split_matches_furnace_physics():
    assert set(P0_SPACE.run_names) == {"ramp_c_per_min", "inter_hold_c", "inter_hold_min",
                                       "anneal_c", "anneal_min", "se_mg", "cool_c_per_min"}
    assert "li_layer" in P0_SPACE.sample_names and "na_mM" in P0_SPACE.sample_names


def test_emulator_calibration():
    m = VirtualKesterite()
    lit = m.qfls(LITERATURE_RECIPE)
    x_opt, f_opt = m.optimum()
    assert 0.58 < lit < 0.65 and lit < f_opt < VOC_SQ_EV
    assert 25 < m.headroom_mev() < 55                  # meaningful but bounded headroom
    assert 0.0 < m.p_fail(LITERATURE_RECIPE) < 0.2
    # QFLS-optimal recipe pays a device-only MoSe2 penalty: the proxy has a blind spot
    assert m.device_voc(x_opt) < m.qfls(x_opt) - 0.03


def test_slow_cooling_orders_the_lattice():
    m = VirtualKesterite()
    fast = dict(LITERATURE_RECIPE, cool_c_per_min=40.0)
    slow = dict(LITERATURE_RECIPE, cool_c_per_min=2.0)
    assert m.urbach(slow) < m.urbach(fast) - 3
    assert m.qfls(slow) > m.qfls(fast)


def test_interaction_switch_removes_cross_terms():
    sep = VirtualKesterite(interaction=0.0)
    a = dict(LITERATURE_RECIPE, na_mM=20.0)
    b = dict(LITERATURE_RECIPE, na_mM=140.0)
    # with interaction off, Na no longer moves the phase-evolution index
    assert sep.terms(a)["_lambda"] == pytest.approx(sep.terms(b)["_lambda"])
    full = VirtualKesterite(interaction=1.0)
    assert full.terms(a)["_lambda"] != pytest.approx(full.terms(b)["_lambda"])


def test_furnace_run_shares_run_effect():
    m = VirtualKesterite(noise=NoiseModel(film_mev=0.0, run_frac=0.0, meas_mev=0.0, hetero=0.0))
    m.p_fail = lambda x: 0.0
    lab = Lab(m, np.random.default_rng(1))
    obs = lab.furnace_run(P0_SPACE.trajectory(LITERATURE_RECIPE),
                          [P0_SPACE.recipe(LITERATURE_RECIPE)] * 4)
    assert all(o.qfls == pytest.approx(m.qfls(LITERATURE_RECIPE)) for o in obs)
    with pytest.raises(ValueError):
        lab.furnace_run(P0_SPACE.trajectory(LITERATURE_RECIPE), [{}] * 5)


def test_confirm_does_not_consume_budget():
    m = VirtualKesterite()
    lab = Lab(m, np.random.default_rng(2))
    v = lab.confirm(LITERATURE_RECIPE, 2)
    assert lab.n_runs == 0 and lab.history == [] and len(v) <= 8


def test_completeness_weights_hidden_parameters():
    lit = completeness(typical_literature_record())
    assert lit["score"] < 0.5
    assert any("cool_c_per_min" in f for f in lit["missing"])
    m = VirtualKesterite()
    lab = Lab(m, np.random.default_rng(3))
    o = lab.furnace_run(P0_SPACE.trajectory(LITERATURE_RECIPE), [P0_SPACE.recipe(LITERATURE_RECIPE)])[0]
    rec = completeness(to_record(o))
    assert rec["score"] > 0.9 and rec["by_tier"]["A4"] == "9/10"   # SnSe pressure not measured
    # a record missing one A4 field loses more than one missing one context field
    base = to_record(o)
    a = completeness(RunRecord(**{**base.__dict__, "cool_c_per_min": None}))["score"]
    c = completeness(RunRecord(**{**base.__dict__, "buffer": None}))["score"]
    assert a < c


def test_ovat_moves_one_variable_at_a_time():
    m = VirtualKesterite(noise=NoiseModel(film_mev=1.0))
    lab = Lab(m, np.random.default_rng(4))
    s = OVAT(LITERATURE_RECIPE)
    for _ in range(6):
        s.step(lab)
    runs = {}
    for o in lab.history:
        runs.setdefault(o.run, []).append(o.x)
    for r, xs in runs.items():
        traj = {k: xs[0][k] for k in P0_SPACE.run_names}
        assert all({k: x[k] for k in P0_SPACE.run_names} == traj for x in xs)
        # inside one run, samples differ in at most one parameter
        varying = {k for k in P0_SPACE.names if len({x[k] for x in xs}) > 1}
        assert len(varying) <= 1


def test_loop_respects_shared_trajectory_and_improves_low_noise():
    m = VirtualKesterite(noise=NoiseModel(film_mev=3.0))
    rng = np.random.default_rng(5)
    lab = Lab(m, rng)
    s = GPBO(LITERATURE_RECIPE, rng)
    for _ in range(14):
        s.step(lab)
    for r in range(lab.n_runs):
        xs = [o.x for o in lab.history if o.run == r]
        assert all(P0_SPACE.trajectory(x) == P0_SPACE.trajectory(xs[0]) for x in xs)
    rec, _ = s.recommend(lab)
    assert m.qfls(rec) > m.qfls(LITERATURE_RECIPE)


def test_welch_and_power_table_shapes():
    assert welch_one_sided([10, 11, 12, 13], [0, 1, 2, 3]) < 0.01
    assert welch_one_sided([0, 1, 2, 3], [10, 11, 12, 13]) > 0.99
    fake = []
    for seed in range(3):
        for arm, g in (("loop", 20.0), ("ovat", 5.0)):
            fake.append({"arm": arm, "noise_mev": 10.0, "seed": seed, "interaction": 1.0,
                         "checkpoints": {"10": {"true_gain_mev": g, "device_gain_mev": g,
                                                "confirm_mev": [g + d for d in (-1, 0, 1, 2)]}}})
    t = power_table(fake)
    assert t[10.0][10]["power"] == 1.0 and t[10.0][10]["gap_median_mev"] == 15.0


def test_run_job_smoke():
    r = run_job(Job("ovat", 10.0, 0, budget=10))
    assert len(r["trace"]) == 10 and 10 in r["checkpoints"]


# ---------------------------------------------------------------- A8
def test_make_device_inherits_film_and_does_not_use_runs():
    from mdl_loop.lab import Lab
    m = VirtualKesterite(noise=NoiseModel(film_mev=10.0, device_mev=0.0))
    m.p_fail = lambda x: 0.0
    lab = Lab(m, np.random.default_rng(6))
    o = lab.furnace_run(P0_SPACE.trajectory(LITERATURE_RECIPE), [P0_SPACE.recipe(LITERATURE_RECIPE)])[0]
    v = lab.make_device(o)
    gap = m.qfls(o.x) - m.device_voc(o.x)
    assert v == pytest.approx(o.qfls - gap) and lab.n_runs == 1 and lab.n_devices == 1
    d = lab.confirm_device(LITERATURE_RECIPE, 2)
    assert len(d) == 8 and lab.n_devices == 1 and lab.n_runs == 1


def test_device_aware_loop_learns_the_se_penalty():
    from mdl_loop.strategies import DeviceAwareGPBO
    m = VirtualKesterite(noise=NoiseModel(film_mev=3.0))
    rng = np.random.default_rng(8)
    lab = Lab(m, rng)
    s = DeviceAwareGPBO(LITERATURE_RECIPE, rng)
    for _ in range(26):
        s.step(lab)
    for r in range(lab.n_runs):
        xs = [o.x for o in lab.history if o.run == r]
        assert all(P0_SPACE.trajectory(x) == P0_SPACE.trajectory(xs[0]) for x in xs)
    assert lab.n_devices >= 8 and s.gap_gp is not None
    lo = dict(LITERATURE_RECIPE, se_mg=200.0)
    hi = dict(LITERATURE_RECIPE, se_mg=640.0)
    g_lo, _ = s._gap(P0_SPACE.encode(lo)[None])
    g_hi, _ = s._gap(P0_SPACE.encode(hi)[None])
    assert g_hi[0] > g_lo[0]                     # the model has seen MoSe2 grow with Se
    rec, _ = s.recommend(lab)
    assert m.device_voc(rec) > m.device_voc(LITERATURE_RECIPE)


# ---------------------------------------------------------------- M0
def test_nested_estimates_recover_components():
    from mdl_loop.m0 import nested_estimates
    rng = np.random.default_rng(11)
    R, F, S = 400, 4, 3
    y = (rng.normal(0, 4.0, (R, 1, 1)) + rng.normal(0, 8.0, (R, F, 1)) + rng.normal(0, 3.0, (R, F, S)))
    e = nested_estimates(y)
    assert e["film"] == pytest.approx(8.0, rel=0.08)
    assert e["run"] == pytest.approx(4.0, rel=0.15)
    assert e["spot"] == pytest.approx(3.0, rel=0.05)


def test_noise_for_maps_measured_to_nominal():
    from mdl_loop.m0 import noise_for
    hom = noise_for(10.0, 0.0)
    het = noise_for(10.0, 1.0)
    assert hom.film_mev == pytest.approx(10.0)
    assert het.film_mev < hom.film_mev                       # optimal films are quieter
    m = VirtualKesterite(1.0, het)
    assert 1000 * m.film_sd_ev(LITERATURE_RECIPE) == pytest.approx(10.0, rel=1e-6)
    assert m.run_sd_ev() == pytest.approx(0.005)


# ---------------------------------------------------------------- 0.4: final anchor
def test_finalize_anchors_the_recommendation_without_furnace_runs():
    from mdl_loop.strategies import DeviceAwareGPBO
    m = VirtualKesterite(noise=NoiseModel(film_mev=10.0))
    rng = np.random.default_rng(9)
    lab = Lab(m, rng)
    s = DeviceAwareGPBO(LITERATURE_RECIPE, rng)
    for _ in range(12):
        s.step(lab)
    runs, devs = lab.n_runs, lab.n_devices
    f = s.finalize(lab)
    assert lab.n_runs == runs
    assert lab.n_devices == devs + (0 if f["pre_anchored"] else 1)
    assert f["device_made"] == (not f["pre_anchored"])
    pre = [o for o in lab.history if o.x == f["pre_rec"] and not o.failed]
    assert any(not math.isnan(o.device) for o in pre)           # the pre-final pick is now anchored
    assert f["rec_changed"] == (f["rec"] != f["pre_rec"])
    assert f["final_anchored"] or f["rec_changed"]


def test_checkpoint_finalize_leaves_the_campaign_unchanged():
    a = run_job(Job("loop-dev", 10.0, 3, budget=10))
    b = run_job(Job("loop-dev", 10.0, 3, budget=10, final_anchor=False))
    assert a["trace"] == b["trace"]
    assert a["checkpoints"][10]["v03"] == b["checkpoints"][10]       # 0.3 record is exact
    cp = a["checkpoints"][10]
    assert cp["final_anchor"]["devices_made"] <= 1
    assert cp["until_anchored"]["final_anchor"]["devices_made"] <= 3
    assert cp["until_anchored"]["final_anchor"]["devices_made"] >= cp["final_anchor"]["devices_made"]
    assert a == run_job(Job("loop-dev", 10.0, 3, budget=10))          # seeded


# ---------------------------------------------------------------- 0.5: two-campaign head-to-head
def test_alternative_start_is_seeded_and_distinct():
    from mdl_loop.m0 import start_recipe
    assert start_recipe(3, 0) == LITERATURE_RECIPE
    a, b = start_recipe(3, 1), start_recipe(3, 1)
    assert a == b and a != LITERATURE_RECIPE and start_recipe(4, 1) != a
    assert a["li_layer"] == LITERATURE_RECIPE["li_layer"]          # categorical settings kept
    assert all(P0_SPACE[k].lo <= a[k] <= P0_SPACE[k].hi for k in P0_SPACE.names if k != "li_layer")


def test_stratified_test_is_antisymmetric_and_detects_a_shift():
    from mdl_loop.two_campaign import stratified_p
    rng = np.random.default_rng(12)
    hi = [(rng.normal(10, 1, 8), rng.normal(0, 1, 8)) for _ in range(2)]
    p, prev = stratified_p(hi)
    assert p < 1e-6 and prev > 1 - 1e-6
    q, qrev = stratified_p([(b, a) for a, b in hi])
    assert q == pytest.approx(prev) and qrev == pytest.approx(p)
    assert stratified_p([(np.array([1.0]), np.array([0.0, 1.0]))] * 2) == (1.0, 1.0)
