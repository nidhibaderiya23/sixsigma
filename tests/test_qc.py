"""Tests for app/qc.py. Every expected number was worked by hand in SPEC.md section 4.

Run from the repo root:  .venv/bin/python -m pytest tests -q
"""

import math

import numpy as np
import pandas as pd
import pytest

from app import qc


# ---- helpers: build small call tables by hand -------------------------------------

def make_calls(rows):
    """rows: dicts with zone, priority, received (Timestamp str) and stage seconds
    processing, turnout, travel. Returns a raw calls DataFrame like a CSV."""
    out = []
    for i, r in enumerate(rows):
        t0 = pd.Timestamp(r.get("received", "2026-09-01 08:00")) + pd.Timedelta(minutes=i if "received" not in r else 0)
        disp = t0 + pd.Timedelta(seconds=r.get("processing", 40))
        enr = disp + pd.Timedelta(seconds=r.get("turnout", 40))
        ons = enr + pd.Timedelta(seconds=r.get("travel", 300))
        out.append({
            "call_id": r.get("call_id", f"T{i:05d}"), "zone": r.get("zone", "A"),
            "priority": r.get("priority", 1), "call_received": t0, "dispatched": disp,
            "en_route": enr, "on_scene": ons, "cleared": ons + pd.Timedelta(minutes=30),
            "unit_id": r.get("unit_id", "M-A1"), "unit_home_zone": r.get("zone", "A"),
            "distance_km": 3.0, "dispatcher_id": "DSP-01", "weather": "clear",
            "delay_reason": r.get("delay_reason", ""),
        })
    return pd.DataFrame(out)


def daily_calls(zone, days, per_day, travel_for_day, turnout_for_day=lambda d, k: 40,
                start="2026-09-01", **extra):
    """per_day calls per day; travel/turnout seconds from functions of (day, k)."""
    rows = []
    for d in range(days):
        for k in range(per_day):
            rows.append({"zone": zone, "received": pd.Timestamp(start) + pd.Timedelta(days=d, hours=8 + k),
                         "travel": travel_for_day(d, k), "turnout": turnout_for_day(d, k),
                         "call_id": f"{zone}{d:02d}{k:02d}", **extra})
    return rows


WOBBLE = [0, 25, -20, 10, -15, 30, -5, 15, -25, 5]   # seconds of ordinary variation


# ---- stage_times and data quality ----------------------------------------------------

def test_stage_times_hand_checked():
    calls = make_calls([{"processing": 30, "turnout": 50, "travel": 420}])
    st = qc.stage_times(calls)
    row = st.iloc[0]
    assert row["processing_s"] == 30
    assert row["turnout_s"] == 50
    assert row["travel_s"] == 420
    assert row["response_s"] == 470            # dispatched -> on scene = 50 + 420
    assert row["response_min"] == pytest.approx(470 / 60)
    assert bool(row["valid"]) and not bool(row["late"])   # 470 s <= 540 s target


def test_stage_times_flags_bad_calls():
    calls = make_calls([{"call_id": "OK"}, {"call_id": "DUP"}, {"call_id": "DUP"},
                        {"call_id": "MISS"}, {"call_id": "ORDER"}])
    calls.loc[calls["call_id"] == "MISS", "en_route"] = pd.NaT
    order = calls["call_id"] == "ORDER"
    calls.loc[order, "on_scene"] = calls.loc[order, "en_route"] - pd.Timedelta(seconds=10)
    st = qc.stage_times(calls)
    issues = dict(zip(range(len(st)), st["issue"]))
    assert issues[0] == ""
    assert issues[2] == "duplicate call_id"
    assert issues[3] == "missing en_route"
    assert issues[4] == "on_scene before en_route"
    assert list(qc.data_issues(st)["call_id"]) == ["DUP", "MISS", "ORDER"]


def test_stage_targets_travel_is_response_minus_turnout():
    assert qc.stage_targets(1)["travel"] == 480      # NFPA 1710 ALS travel
    assert qc.stage_targets(2)["travel"] == 840
    assert qc.stage_targets(3)["response"] == 1200


# ---- summary numbers ---------------------------------------------------------------------

def test_summary_hand_checked():
    # sorted [4..12, 20]; median position 4.5 -> 8.5; p90 position 8.1 -> 12 + 0.1*8;
    # p95 position 8.55 -> 12 + 0.55*8; on time <= 9 -> 6 of 10
    s = qc.summary([4, 5, 6, 7, 8, 9, 10, 11, 12, 20], target_min=9)
    assert s["n"] == 10
    assert s["mean"] == pytest.approx(9.2)
    assert s["median"] == pytest.approx(8.5)
    assert s["p90"] == pytest.approx(12.8)
    assert s["p95"] == pytest.approx(16.4)
    assert s["pct_on_time"] == pytest.approx(60.0)


def test_percentile_matches_numpy_linear():
    xs = [3.1, 9.4, 2.2, 7.7, 5.0, 6.6]
    for p in (0, 0.25, 0.5, 0.9, 0.95, 1):
        assert qc.percentile(xs, p) == pytest.approx(np.percentile(xs, p * 100, method="linear"))


def test_summary_degenerate():
    one = qc.summary([7.5], target_min=9)
    assert one["median"] == one["p90"] == one["p95"] == 7.5
    assert qc.summary([], target_min=9)["p90"] is None
    with pytest.raises(ValueError):
        qc.percentile([], 0.5)


# ---- I-MR -------------------------------------------------------------------------------------

def test_imr_limits_hand_checked():
    # MR = 2, 1, 4, 3 -> MR-bar 2.5; sigma = 2.5 / 1.128 = 2.2163; limits 12 -/+ 6.6489
    lim = qc.imr_limits([10, 12, 11, 15, 12])
    assert lim["ok"]
    assert lim["mr_bar"] == pytest.approx(2.5)
    assert lim["center"] == pytest.approx(12.0)
    assert lim["sigma"] == pytest.approx(2.5 / 1.128)
    assert lim["ucl"] == pytest.approx(18.6489, abs=1e-4)
    assert lim["lcl"] == pytest.approx(5.3511, abs=1e-4)
    assert lim["mr_ucl"] == pytest.approx(8.1675)


def test_imr_degenerate():
    flat = qc.imr_limits([5, 5, 5, 5])
    assert not flat["ok"] and flat["ucl"] is None and "no variation" in flat["message"]
    single = qc.imr_limits([5])
    assert not single["ok"] and "at least 2" in single["message"]


# ---- X-bar and S --------------------------------------------------------------------------------

def test_xbar_s_hand_checked():
    # means 4, 5, 6 -> 5; each sd 2 -> sigma_short sqrt((4+4+4)/3) = 2;
    # limits 5 -/+ 3*2/sqrt(3); c4(3) = 0.8862 -> S center 1.7725, upper 4.552, lower 0
    lim = qc.xbar_s_limits([[2, 4, 6], [3, 5, 7], [4, 6, 8]])
    assert lim["ok"]
    assert lim["xbbar"] == pytest.approx(5.0)
    assert lim["sigma_short"] == pytest.approx(2.0)
    g = lim["subgroups"][0]
    assert g["x_ucl"] == pytest.approx(8.4641, abs=1e-4)
    assert g["x_lcl"] == pytest.approx(1.5359, abs=1e-4)
    assert qc.c4(3) == pytest.approx(0.8862, abs=1e-4)
    assert g["s_center"] == pytest.approx(1.7725, abs=1e-4)
    assert g["s_ucl"] == pytest.approx(4.552, abs=1e-3)
    assert g["s_lcl"] == 0.0
    assert [s["z"] for s in lim["subgroups"]] == pytest.approx([-1 / (2 / math.sqrt(3)), 0, 1 / (2 / math.sqrt(3))])


def test_xbar_s_degenerate():
    flat = qc.xbar_s_limits([[3, 3, 3], [3, 3]])
    assert not flat["ok"] and "no variation" in flat["message"]
    singles = qc.xbar_s_limits([[3], [4]])
    assert not singles["ok"] and "2 or more" in singles["message"]
    mixed = qc.xbar_s_limits([[2, 4, 6], [5]])        # a 1-call day: x-bar point, no S point
    assert mixed["ok"]
    assert mixed["subgroups"][1]["z"] is not None and mixed["subgroups"][1]["s_ucl"] is None


# ---- flag rules -------------------------------------------------------------------------------------

def test_flag_rules_hand_checked():
    r = qc.flag_rules([0.5, 2.5, 0.3, 2.4])
    assert r[3] == ["R2+"] and r[2] == []          # 2.5 and 2.4: 2 of 3 beyond 2 sigma
    r = qc.flag_rules([0.1] * 8)
    assert r[7] == ["R4+"] and r[6] == []          # 8 in a row above center
    r = qc.flag_rules([1, 2, 3, 4, 5, 6])
    assert "R5+" in r[5] and "R5+" not in r[4]     # 6 rising in a row
    assert qc.flag_rules([3.5])[0] == ["R1+"]
    r = qc.flag_rules([0, 1.5, 1.2, 0.2, 1.1, 1.3])
    assert "R3+" in r[5]                           # 4 of the last 5 beyond 1 sigma


def test_flag_rules_fast_side_is_only_check():
    assert qc.flag_rules([-3.5])[0] == ["R1-"]
    assert qc.flag_rules([-0.1] * 8)[7] == ["R4-"]


def test_flag_rules_degenerate():
    assert qc.flag_rules([]) == []
    assert qc.flag_rules([0.2, -0.3, 0.1]) == [[], [], []]     # fewer than 8 points: no run rules


# ---- capability, tests ---------------------------------------------------------------------------------

def test_capability_hand_checked():
    # mean 8, sd sqrt(2.5) = 1.5811 -> Ppk = 4 / 4.7434 = 0.8433
    cap = qc.capability([6, 7, 8, 9, 10], usl=12)
    assert cap["ok"] and cap["ppk"] == pytest.approx(0.8433, abs=1e-4)
    assert qc.capability([6, 7, 8, 9, 10], usl=12, sigma_short=2)["cpk"] == pytest.approx(4 / 6)


def test_capability_degenerate():
    flat = qc.capability([7, 7, 7], usl=9)
    assert not flat["ok"] and flat["ppk"] is None and "no variation" in flat["message"]


def test_anova_hand_checked():
    # grand mean 3.5; SSB = 3*(2-3.5)^2 + 3*(5-3.5)^2 = 13.5; SSW = 2 + 2 = 4; F = 13.5 / (4/4)
    a = qc.anova_zones({"A": [1, 2, 3], "B": [4, 5, 6]})
    assert a["ok"] and a["ssb"] == pytest.approx(13.5) and a["ssw"] == pytest.approx(4.0)
    assert a["F"] == pytest.approx(13.5) and (a["df_between"], a["df_within"]) == (1, 4)
    assert a["p"] == pytest.approx(0.02131, abs=1e-4)


def test_anova_degenerate():
    a = qc.anova_zones({"A": [1, 2, 3], "B": [9]})
    assert not a["ok"] and a["dropped"] == ["B"]


def test_welch_hand_checked():
    # means 12 vs 8; each variance 4 -> se sqrt(4/3 + 4/3); t = 4 / 1.633 = 2.449; df = 4
    w = qc.welch_before_after([10, 12, 14], [6, 8, 10])
    assert w["ok"] and w["t"] == pytest.approx(2.4495, abs=1e-4) and w["df"] == pytest.approx(4.0)
    assert 0.03 < w["p_one_sided"] < 0.04


def test_welch_degenerate():
    assert not qc.welch_before_after([5], [4, 3])["ok"]
    assert not qc.welch_before_after([5, 5], [4, 4])["ok"]


# ---- impact estimate ---------------------------------------------------------------------------------------

def test_impact_hand_checked():
    # turnout 3, 1, 4, 1 min; travel 7, 7, 6, 9 min; target 9 min; cap turnout at 1 min
    # responses 10, 8, 10, 10 -> 1/4 on time; capped 8, 8, 7, 10 -> 3/4 on time
    calls = pd.DataFrame({"turnout_s": [180, 60, 240, 60], "travel_s": [420, 420, 360, 540]})
    imp = qc.impact_estimate(calls, "turnout", cap_s=60, target_s=540)
    assert imp["pct_on_time_before"] == pytest.approx(25.0)
    assert imp["pct_on_time_after"] == pytest.approx(75.0)
    assert imp["gain"] == pytest.approx(50.0)


def test_impact_degenerate():
    empty = pd.DataFrame({"turnout_s": [], "travel_s": []})
    assert qc.impact_estimate(empty, "turnout", 60, 540)["pct_on_time_before"] is None


# ---- daily chart, health, suggestions, before/after on built data ------------------------------------------

def test_daily_chart_flags_a_planted_shift():
    # 21 days of 6 calls; travel normal for 14 days, then +200 s from day 14 on
    rows = daily_calls("D", 21, 6, lambda d, k: 300 + WOBBLE[(d + k) % 10] + (200 if d >= 14 else 0))
    st = qc.stage_times(make_calls(rows))
    chart = qc.daily_xbar_s(st, "D", baseline_days=14)
    assert len(chart) == 21 and chart["baseline"].sum() == 14
    assert not chart[chart["baseline"]]["alarm"].any()
    assert chart[~chart["baseline"]]["alarm"].all()
    imr = qc.imr_chart(st, "D", baseline_days=14)
    assert imr["beyond"].sum() > 0 and not imr.attrs["message"]


def test_zone_health_and_turnout_suggestion():
    # Zone D: turnout jumps from 40 s to 260 s after day 14 (crew problem); Zone A stays normal
    turnout = lambda d, k: 40 + WOBBLE[(d + k) % 10] // 5 + (220 if d >= 14 else 0)
    rows = daily_calls("D", 21, 6, lambda d, k: 330 + WOBBLE[(d + k) % 10], turnout)
    rows += daily_calls("A", 21, 6, lambda d, k: 330 + WOBBLE[(d + k) % 10],
                        lambda d, k: 40 + WOBBLE[(d + k) % 10] // 5)
    st = qc.stage_times(make_calls(rows))
    health = qc.zone_health(st).set_index("zone")
    assert health.loc["D", "status"] == "red" and health.loc["D", "top_stage"] == "turnout"
    assert health.loc["A", "status"] == "green"
    sug = qc.suggest(st)
    assert [s["rule"] for s in sug] == ["S1"]
    assert sug[0]["zone"] == "D" and sug[0]["impact"]["gain"] > 0
    acts = pd.DataFrame([{"action_id": "A1", "date": "2026-09-16", "zone": "D", "stage": "turnout"}])
    assert qc.suggest(st, acts)[0]["status"] == "action logged on 2026-09-16"


def test_breakdown_suggestion_only():
    rows = daily_calls("B", 15, 4, lambda d, k: 330 + WOBBLE[(d + k) % 10])
    rows[5]["delay_reason"] = rows[30]["delay_reason"] = "ambulance_breakdown"
    for r in rows:
        r["unit_id"] = "M-B2"
    st = qc.stage_times(make_calls(rows))
    assert [s["rule"] for s in qc.suggest(st)] == ["S5"]


def test_before_after_and_slip_back():
    # Zone D: slow (travel 500 s) for 14 days, fixed (travel 330 s) from day 14
    rows = daily_calls("D", 28, 6, lambda d, k: (500 if d < 14 else 330) + WOBBLE[(d + k) % 10])
    st = qc.stage_times(make_calls(rows))
    ba = qc.before_after(st, "D", "2026-09-15")
    assert ba["verdict"] == "improved" and ba["test"]["p_one_sided"] < 0.001
    assert ba["after"]["median"] < ba["before"]["median"] and ba["in_control_after"]
    acts = pd.DataFrame([{"action_id": "A1", "date": "2026-09-15", "zone": "D", "stage": "travel"}])
    assert qc.slip_back(st, acts) == []
    # now it slips back from day 22
    rows = daily_calls("D", 28, 6, lambda d, k: (330 if d < 22 else 520) + WOBBLE[(d + k) % 10])
    st2 = qc.stage_times(make_calls(rows))
    alerts = qc.slip_back(st2, acts)
    assert len(alerts) == 1 and alerts[0]["zone"] == "D"


def test_stage_breakdown_shares():
    rows = [{"zone": "C", "received": "2026-09-01 08:00", "processing": 64, "turnout": 90, "travel": 540}]
    st = qc.stage_times(make_calls(rows))
    bd = qc.stage_breakdown(st).set_index("zone")
    # turnout 30 s over, travel 60 s over, processing 0 over -> shares 1/3 and 2/3
    assert bd.loc["C", "turnout_share"] == pytest.approx(1 / 3)
    assert bd.loc["C", "travel_share"] == pytest.approx(2 / 3)
    assert bd.loc["C", "processing_excess_min"] == 0


# ---- regressions from the stats review (fresh-context reviewer, Oct 16) ----------------------

FLOAT_CONSTANT = np.full(60, np.log(340 / 60))     # equal values with last-bit float noise


def test_float_constants_give_no_variation():
    assert not qc.imr_limits(FLOAT_CONSTANT)["ok"]
    assert not qc.capability(FLOAT_CONSTANT, usl=math.log(9))["ok"]
    assert not qc.xbar_s_limits([FLOAT_CONSTANT[:30], FLOAT_CONSTANT[30:]])["ok"]
    assert not qc.anova_zones({"A": FLOAT_CONSTANT[:33], "B": FLOAT_CONSTANT[33:]})["ok"]
    assert not qc.welch_before_after(FLOAT_CONSTANT[:33], FLOAT_CONSTANT[33:])["ok"]
    assert not qc.normality(FLOAT_CONSTANT)["ok"]


def test_constant_calls_through_the_pipeline():
    # every call exactly 340 s dispatch -> on scene (40 s turnout + 300 s travel)
    rows = daily_calls("D", 28, 6, lambda d, k: 300)
    st = qc.stage_times(make_calls(rows))
    chart = qc.daily_xbar_s(st, "D")
    assert len(chart) == 0 and "no variation" in chart.attrs["message"]
    cap = qc.zone_capability(st).set_index("zone")
    assert cap.loc["D", "ppk"] is None and not cap.loc["D", "shown"]
    assert qc.before_after(st, "D", "2026-09-15")["verdict"] == "not enough data"


def test_invalid_call_cannot_move_the_windows():
    rows = daily_calls("D", 21, 6, lambda d, k: 300 + WOBBLE[(d + k) % 10])
    clean = qc.stage_times(make_calls(rows))
    bad_rows = rows + [{"zone": "D", "received": "2025-01-01 08:00", "call_id": "OLD"},
                       {"zone": "D", "received": "2027-01-01 08:00", "call_id": "FUTURE"}]
    calls = make_calls(bad_rows)
    calls.loc[calls["call_id"].isin(["OLD", "FUTURE"]), "en_route"] = pd.NaT
    dirty = qc.stage_times(calls)
    assert (~dirty["valid"]).sum() == 2
    a, b = qc.daily_xbar_s(clean, "D"), qc.daily_xbar_s(dirty, "D")
    assert b.attrs["xbbar"] == pytest.approx(a.attrs["xbbar"]) and len(b) == len(a)
    assert list(qc.zone_health(dirty)["status"]) == list(qc.zone_health(clean)["status"])
    assert len(qc.last_days(dirty, 7)[lambda s: s["valid"]]) == len(qc.last_days(clean, 7))


def test_trend_rule_follows_plotted_values():
    z = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]              # z rising ...
    plotted = [1.0, 1.1, 1.2, 1.3, 1.4, 1.35]        # ... but the plotted average dips last
    assert "R5+" in qc.flag_rules(z)[5]
    assert "R5+" not in qc.flag_rules(z, trend=plotted)[5]


def test_before_after_reports_got_worse():
    rows = daily_calls("D", 28, 6, lambda d, k: (330 if d < 14 else 520) + WOBBLE[(d + k) % 10])
    st = qc.stage_times(make_calls(rows))
    assert qc.before_after(st, "D", "2026-09-15")["verdict"] == "got worse"


def test_zone_health_marks_slip_back():
    rows = daily_calls("D", 28, 6, lambda d, k: (330 if d < 22 else 520) + WOBBLE[(d + k) % 10])
    st = qc.stage_times(make_calls(rows))
    acts = pd.DataFrame([{"action_id": "A1", "date": "2026-09-15", "zone": "D", "stage": "travel"}])
    health = qc.zone_health(st, actions=acts).set_index("zone")
    assert health.loc["D", "status"] in ("amber", "red")
    assert "slipping back" in health.loc["D", "reasons"][0]


def test_ppk_to_pct_hand_checked():
    # Phi(3) = 0.99865; Phi(3 * 0.4272) = Phi(1.2816) = 0.90
    assert qc.ppk_to_pct(1.0) == pytest.approx(99.865, abs=1e-3)
    assert qc.ppk_to_pct(1.2816 / 3) == pytest.approx(90.0, abs=1e-2)
    assert qc.ppk_to_pct(None) is None


def test_chart_signal_stricter_amber_rule():
    # the team's Oct 16 decision: rule 1, or 2+ different rules; one weak rule alone does not count
    assert qc.chart_signal(["R1"])
    assert qc.chart_signal(["R2", "R4"])
    assert not qc.chart_signal(["R4"])
    assert not qc.chart_signal(["R5"])
    assert not qc.chart_signal([])


def test_capability_needs_enough_calls():
    rows = daily_calls("D", 3, 3, lambda d, k: 300 + WOBBLE[(d + k) % 10])    # 9 calls
    cap = qc.zone_capability(qc.stage_times(make_calls(rows))).set_index("zone")
    assert not cap.loc["D", "shown"] and cap.loc["D", "ppk"] is None
    assert "too few calls" in cap.loc["D", "message"]


def test_capability_judges_stability_with_the_real_baseline():
    # D slow from day 14 to 27, fixed from day 28; a 28-day period that starts AFTER the baseline
    rows = daily_calls("D", 42, 6, lambda d, k: (520 if 14 <= d < 28 else 330) + WOBBLE[(d + k) % 10])
    st = qc.stage_times(make_calls(rows))
    cap = qc.zone_capability(st, period_days=28).set_index("zone")
    assert not cap.loc["D", "stable"] and cap.loc["D", "ppk"] is None   # the slow days are in the period
    cap14 = qc.zone_capability(st, period_days=14).set_index("zone")
    assert cap14.loc["D", "stable"] and cap14.loc["D", "ppk"] is not None  # only the fixed days
