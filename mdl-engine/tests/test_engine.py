import math, json
from importlib import resources
import pytest
from mdl_engine import sq, diode, decompose, compliance, transfer, temporal as T, ledger


def test_sq_blackbody_sane():
    s = sq.sq_limit(1.34)
    assert 29.5 < s.eta_pct < 31.5          # 5772 K blackbody optimum ~30-31%
    assert s.voc_v < 1.34 and 0.85 < s.ff < 0.92
    # Voc_SQ rises ~1 V per eV of gap
    assert sq.sq_limit(1.5).voc_v - sq.sq_limit(1.1).voc_v == pytest.approx(0.4, abs=0.04)


def test_sq_custom_spectrum_matches_blackbody_when_fed_blackbody():
    import numpy as np
    from mdl_engine.constants import Q, KB, H, C, T_SUN
    e = np.linspace(0.3, 6, 6000)
    ej = e * Q
    flux = sq._PREF * ej**2 / np.expm1(ej / (KB * T_SUN)) * sq._bb_dilution() * Q * 1e-4
    spec = sq.Spectrum("bb-tab", tuple(e), tuple(flux))
    assert sq.sq_limit(1.1, spec).eta_pct == pytest.approx(sq.sq_limit(1.1).eta_pct, rel=2e-3)


def test_normalize_identities():
    n = sq.normalize(1.10, 0.602, 37.2, 68.9)
    assert n["eta_pct"] == pytest.approx(15.43, abs=0.01)
    assert n["voc_deficit_eg_mv"] == pytest.approx(498, abs=0.5)
    prod = n["voc_over_sq"] * n["jsc_over_sq"] * n["ff_over_sq"]
    assert prod == pytest.approx(n["pct_sq"] / 100, abs=0.005)


def test_gain_shares_sum_and_label():
    g = decompose.gain_decomposition({"voc_v": 0.5134, "jsc_ma": 35.2, "ff_pct": 69.8},
                                     {"voc_v": 0.602, "jsc_ma": 37.2, "ff_pct": 68.9})
    assert g["share_voc"] + g["share_jsc"] + g["share_ff"] == pytest.approx(1, abs=0.02)
    assert g["label"].startswith("diode-quality")
    j = decompose.gain_decomposition({"voc_v": 0.5, "jsc_ma": 30, "ff_pct": 70},
                                     {"voc_v": 0.5, "jsc_ma": 36, "ff_pct": 70})
    assert j["label"].startswith("current-led")


def test_diode_roundtrip_and_ideal_slope():
    p = diode.fit_from_metrics(0.558, 37.4, 73.6, n=1.42, rs=0.38)
    r = diode.simulate(p)
    assert r["voc_v"] == pytest.approx(0.558, abs=1e-4)
    assert r["jsc_ma"] == pytest.approx(37.4, abs=1e-3)
    assert r["ff_pct"] == pytest.approx(73.6, abs=0.02)
    # no shunt, no Rs: Voc drops n*kT/q*ln(10) per decade
    q = diode.DiodeParams(37.0, 1e-6, 1.5, 0.0, 1e9)
    dv = diode.simulate(q, 1.0)["voc_v"] - diode.simulate(q, 0.1)["voc_v"]
    assert dv == pytest.approx(1.5 * 0.025693 * math.log(10), rel=2e-3)


def test_shunt_kills_indoor_but_not_one_sun():
    good = diode.project_low_light(0.558, 37.4, 73.6, n=1.42, rs=0.38, rsh=1e5)
    leaky = diode.project_low_light(0.558, 37.4, 73.6, n=1.42, rs=0.38, rsh=970.9)
    gi = good["projection"]["indoor"]["1000lux"]["eta_pct"]
    li = leaky["projection"]["indoor"]["1000lux"]["eta_pct"]
    assert gi > 5 * li
    assert abs(good["projection"]["stc"]["eta_pct"] - leaky["projection"]["stc"]["eta_pct"]) < 0.5


def test_intensity_dependent_ideality_hurts():
    a = diode.project_low_light(0.558, 37.4, 73.6, n=1.42, rs=0.38, rsh=1e5)
    b = diode.project_low_light(0.558, 37.4, 73.6, n=1.42, rs=0.38, rsh=1e5, dn_per_decade=0.3)
    k = "100W/m2"
    assert b["projection"]["outdoor"][k]["retention"] < a["projection"]["outdoor"][k]["retention"]


def test_envelope_flags_prior():
    r = diode.project_low_light(0.602, 37.2, 68.9)
    assert "class-prior" in r["provenance"] and r["n_feasible"] > 5
    e = r["outdoor_retention"]["100W/m2"]
    assert e["min"] <= e["median"] <= e["max"] <= 1.0


def test_infeasible_ff():
    assert diode.fit_from_metrics(0.5, 35, 86.0, n=2.0, rs=1.0) is None


def test_compliance_arithmetic():
    assert compliance.weight_fractions("CdS")["Cd"] == pytest.approx(77.8, abs=0.1)
    c = compliance.check_stack([{"name": "abs", "formula": "Cu2Zn0.7Cd0.3SnS4"}])
    h = c["layers"][0]["restricted"][0]
    assert 5 < h["wt_pct"] < 9 and h["times_over"] > 500
    assert c["gates"]["VIPV"]["gate"] == "FAIL" and c["gates"]["BIPV"]["gate"] == "moot"
    ok = compliance.check_stack([{"name": "abs", "formula": "Cu2ZnSn(S0.2Se0.8)4"},
                                 {"name": "buf", "formula": "ZnO0.7S0.3"}])
    assert ok["gates"]["VIPV"]["gate"] == "pass" and ok["gates"]["interior"]["gate"] == "pass"
    assert compliance.weight_fractions("CH3NH3PbI3")["Pb"] == pytest.approx(33.4, abs=0.2)


def test_formula_parser():
    assert compliance.parse_formula("Cu2ZnSn(S0.25Se0.75)4") == {
        "Cu": 2, "Zn": 1, "Sn": 1, "S": 1.0, "Se": 3.0}
    with pytest.raises(ValueError):
        compliance.parse_formula("Xx2O")


def test_transferability_ordering():
    hi = transfer.transferability("bulk growth-kinetics", "solution-molecular-ink", "substrate")
    lo = transfer.transferability("contact/optics", "vacuum", "superstrate")
    assert hi["band"] == "HIGH" and lo["band"] in ("LOW", "NONE") and lo["score"] < hi["score"]
    ov = transfer.transferability("contact/optics", "vacuum", "superstrate",
                                  override={"score": 0.9, "reason": "test"})
    assert ov["band"] == "HIGH" and "OVERRIDE" in ov["reasons"][-1]


def test_record_count_theory_matches_simulation():
    # distribution-free: mean new records = ln(ratio)
    sim = T.simulate_static_null(12.6, 99, 200, 1800, tail_scale=0.5, n_sim=4000)
    assert sim["mean_new_records"] == pytest.approx(math.log(10), rel=0.08)
    assert T.record_count_test(4, 3)["p_value"] < 0.05 < T.record_count_test(4, 10)["p_value"]
    assert T.record_count_test(1, T.ratio_needed(1))["p_value"] == pytest.approx(0.05, abs=0.01)


def test_changepoint_finds_planted_change():
    years = list(range(2000, 2020)); counts = [0] * 12 + [2, 1, 2, 3, 1, 2, 2, 1]
    cp = T.poisson_changepoint(years, counts)
    assert cp["map_year"] == 2012 and cp["log10_bayes_factor_vs_no_change"] > 1
    assert sum(cp["posterior"].values()) == pytest.approx(1, abs=1e-3)


def test_gate_backtest_reproduces_memo():
    ev = [(2013.9, 12.6), (2023.28, 13.8), (2024.45, 14.2)]
    assert T.gate_backtest(ev, 2, 2026)[0] == (2015.9, 2023.28)
    # two-signal: leading indicators alive throughout -> never fires
    assert T.gate_backtest(ev, 2, 2026, leading_alive=lambda t: True) == []
    # indicators stall 2018-2020 only
    fired = T.gate_backtest(ev, 2, 2026, leading_alive=lambda t: not (2018 <= t < 2020))
    assert fired == [(2018.15, 2020.15)] or (2017.9 <= fired[0][0] <= 2018.2 and 2019.9 <= fired[0][1] <= 2020.2)


def test_seed_ledger_runs_and_flips_sign():
    ev = json.loads(resources.files("mdl_engine.data").joinpath("events.json").read_text())
    es = {e["id"]: e for e in ledger.run(ev)}
    y = es["yin_2025_cd_gradient"]["applications"]
    assert y["VIPV"]["deterministic_sign"].startswith("BLOCKED") and y["BIPV"]["gate"]["gate"] == "moot"
    assert es["p0_target_stack"]["applications"]["VIPV"]["gate"]["gate"] == "pass"
    assert es["cui_2026"]["gain"]["label"].startswith("diode-quality")
    assert es["rival_pb_perovskite"]["applications"]["VIPV"]["gate"]["gate"] == "FAIL"
    for e in es.values():
        assert e["human_ratification"]["net_sign"] is None
        ledger.render_markdown(e)


# ---------------------------------------------------------------- A6 ledger entries
def _a6_entries():
    import json
    from importlib import resources
    from mdl_engine import ledger
    ev = json.loads(resources.files("mdl_engine.data").joinpath("events.json").read_text())
    return {e["id"]: e for e in ledger.run(ev)}


def test_zto_entry_is_the_first_cd_free_device_pass():
    E = _a6_entries()
    g = E["zto_ees_2026"]["applications"]
    assert g["VIPV"]["gate"]["gate"] == "pass" and g["interior"]["gate"]["gate"] == "pass"
    devices_passing = [i for i, e in E.items() if e.get("compliance")
                       and e["compliance"]["gates"]["VIPV"]["gate"] == "pass"
                       and i != "p0_target_stack"]                     # design target, not a device
    assert devices_passing == ["zto_ees_2026"]


def test_unknown_stack_leaves_gates_undetermined_not_passed():
    E = _a6_entries()
    for i in ("flex_mo_ne_2026", "flex_module_ne_2026", "tables_v68_1cm2", "module_v68"):
        assert all(a["gate"]["gate"] == "unknown" for a in E[i]["applications"].values())


def test_value_provenance_and_unverified_list_reach_the_entry():
    E = _a6_entries()
    z = E["zto_ees_2026"]
    assert z["reported_values"]["eta_certified_pct"]["value"] == 13.90
    assert not z["reported_values"]["eta_certified_pct"]["verify"]
    assert "eta_lab_pct" in z["unverified"] and "eta_certified_pct" not in z["unverified"]


def test_jv_check_flags_rows_that_do_not_reproduce_their_efficiency():
    E = _a6_entries()
    assert E["tables_v68_1cm2"]["jv_check"]["consistent"] is False
    assert "jsc_ma" in E["tables_v68_1cm2"]["unverified"]
    others = [e["jv_check"]["consistent"] for i, e in E.items() if "jv_check" in e and i != "tables_v68_1cm2"]
    assert others and all(others)


def test_same_certificate_has_the_same_date_in_every_series():
    import json
    from importlib import resources
    R = json.loads(resources.files("mdl_engine.data").joinpath("records.json").read_text())
    t = {k: r["t"] for k in ("table_dated_small_area", "certification_dated_mixed_area")
         for r in R[k] if r["eta"] == 14.9}
    assert len(set(t.values())) == 1 and 2023.25 <= t["certification_dated_mixed_area"] < 2023.34   # April
