"""Tests for app/simulator.py: the shift replay and the live board rules.

The replay is checked on a tiny hand-made table of 2 calls at 4 chosen times.
The board rules (one valid button at a time, a reason when a stage runs late,
the breakdown flag, the fleet order) are checked on a few manual calls.
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest

# Import through the `app` package (pytest.ini puts the repo root on the path).
from app import simulator as sim
from app import qc

T0 = datetime(2026, 9, 20, 8, 0, 0)


def at(seconds):
    """A time `seconds` after 08:00:00 on the test day."""
    return T0 + timedelta(seconds=seconds)


def two_calls() -> pd.DataFrame:
    """Two calls on 2026-09-20 (times in seconds after 08:00:00).

    call A (zone C, P1): received 0, dispatched 60, en route 120, on scene 600, cleared 1800
    call B (zone D, P2): received 300, dispatched 330, en route 420, on scene 1200, cleared 2400
    """
    def row(cid, zone, pri, stamps, unit, home, reason=""):
        r = {"call_id": cid, "zone": zone, "priority": pri, "unit_id": unit,
             "unit_home_zone": home, "distance_km": 3.5, "dispatcher_id": "D1",
             "weather": "clear", "delay_reason": reason}
        for col, s in zip(qc.TIMESTAMPS, stamps):
            r[col] = at(s)
        return r

    df = pd.DataFrame([
        row("A", "C", 1, (0, 60, 120, 600, 1800), "M-C1", "C"),
        row("B", "D", 2, (300, 330, 420, 1200, 2400), "M-A2", "A", "unit_from_another_zone"),
    ])
    return df[list(qc.CALL_COLUMNS)]


# ---- events_until: each call's state at a chosen time ---------------------------------

def test_events_until_before_any_call_is_empty():
    state = sim.events_until(two_calls(), at(-1))
    assert len(state) == 0


def test_events_until_state_of_both_calls_at_four_times():
    calls = two_calls()

    # 1) 90 s: call A was dispatched at 60 s; call B has not arrived yet.
    s1 = sim.events_until(calls, at(90))
    assert list(s1["call_id"]) == ["A"]
    assert list(s1["status"]) == ["dispatched"]
    assert pd.isna(s1.loc[0, "en_route"])              # future stamps are blanked
    assert s1.loc[0, "unit_id"] == "M-C1"               # the unit is known once dispatched

    # 2) 330 s: A is en route; B was received at 300 s and dispatched exactly now (<=).
    s2 = sim.events_until(calls, at(330))
    assert dict(zip(s2["call_id"], s2["status"])) == {"A": "en_route", "B": "dispatched"}

    # 3) 1000 s: A is on scene (600 s); B is en route (420 s) and not yet on scene (1200 s).
    s3 = sim.events_until(calls, at(1000))
    assert dict(zip(s3["call_id"], s3["status"])) == {"A": "on_scene", "B": "en_route"}
    assert s3.loc[s3["call_id"] == "B", "delay_reason"].iloc[0] == ""   # not yet at the scene

    # 4) 2000 s: A is cleared (1800 s); B is on scene (1200 s) and not yet cleared (2400 s).
    s4 = sim.events_until(calls, at(2000))
    assert dict(zip(s4["call_id"], s4["status"])) == {"A": "cleared", "B": "on_scene"}
    assert s4.loc[s4["call_id"] == "B", "delay_reason"].iloc[0] == "unit_from_another_zone"


def test_events_until_keeps_the_call_schema_and_does_not_change_its_input():
    calls = two_calls()
    before = calls.copy()
    state = sim.events_until(calls, at(2000))
    assert list(state.columns) == list(qc.CALL_COLUMNS) + ["status"]
    pd.testing.assert_frame_equal(calls, before)


def test_day_calls_and_default_day():
    calls = two_calls()
    other = calls.copy()
    other["call_id"] = ["X", "Y"]
    for col in qc.TIMESTAMPS:
        other[col] = other[col] + pd.Timedelta(days=1)
    both = pd.concat([calls, other], ignore_index=True)
    assert sim.available_days(both) == ["2026-09-20", "2026-09-21"]
    assert list(sim.day_calls(both, "2026-09-21")["call_id"]) == ["X", "Y"]
    assert sim.pick_day(["2026-09-20", "2026-09-21"]) == "2026-09-20"
    assert sim.pick_day(["2026-09-01", "2026-09-02"]) == "2026-09-02"   # default day missing


# ---- the replay clock -----------------------------------------------------------------

def test_replay_runs_at_speed_pauses_and_finishes():
    r = sim.Replay(two_calls(), speed=60)
    assert r.now == datetime(2026, 9, 20, 0, 0, 0)       # starts at midnight
    r.advance(10)
    assert r.now == datetime(2026, 9, 20, 0, 0, 0)       # not running yet: the clock waits
    r.start()
    r.advance(10)
    assert r.now == datetime(2026, 9, 20, 0, 10, 0)      # 10 real seconds x 60
    r.set_speed(120)
    r.advance(5)
    assert r.now == datetime(2026, 9, 20, 0, 20, 0)      # 5 s x 120 = 10 more minutes
    r.pause()
    r.advance(100)
    assert r.now == datetime(2026, 9, 20, 0, 20, 0)
    r.start()
    r.advance(100000)                                    # past the last stamp (08:40:00)
    assert r.finished and not r.running
    assert r.now >= at(2400)
    assert set(r.state()["status"]) == {"cleared"}


def test_replay_can_start_at_a_shift():
    r = sim.Replay(two_calls(), speed=30, start_hour=6)
    assert r.now == datetime(2026, 9, 20, 6, 0, 0)


def test_replay_leaves_out_calls_cleared_before_the_start_time():
    calls = two_calls()
    calls.loc[calls["call_id"] == "A", "cleared"] = datetime(2026, 9, 20, 5, 0, 0)   # done by 05:00
    r = sim.Replay(calls, speed=60, start_hour=6)
    assert list(r.calls["call_id"]) == ["B"]                 # A is history, B comes later
    late = calls.copy()
    late["cleared"] = datetime(2026, 9, 20, 5, 0, 0)
    with pytest.raises(ValueError):                          # nothing left to replay
        sim.Replay(late, speed=60, start_hour=6)


# ---- the live board: calls and buttons --------------------------------------------------

def make_board() -> sim.Board:
    return sim.Board(units=[("M-A1", "A"), ("M-A2", "A"), ("M-B1", "B"), ("M-C1", "C")])


def test_manual_call_is_stamped_from_the_clock_and_gets_an_id():
    board = make_board()
    call = board.add_call("C", 1, at(0))
    assert call.call_received == at(0)
    assert call.call_id == "LIVE-20260920-001"
    assert call.status == "received"
    assert board.add_call("A", 2, at(5)).call_id == "LIVE-20260920-002"
    with pytest.raises(sim.BoardError):
        board.add_call("Z", 1, at(0))
    with pytest.raises(sim.BoardError):
        board.add_call("A", 4, at(0))


def test_only_the_next_valid_step_is_accepted():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    with pytest.raises(sim.BoardError):                  # cannot skip dispatch
        board.apply(cid, "en_route", at(10))
    board.apply(cid, "dispatch", at(30), unit_id="M-A1")
    with pytest.raises(sim.BoardError):                  # cannot dispatch twice
        board.apply(cid, "dispatch", at(31), unit_id="M-A2")
    with pytest.raises(sim.BoardError):                  # cannot jump to on scene
        board.apply(cid, "on_scene", at(40))
    board.apply(cid, "en_route", at(60))
    board.apply(cid, "on_scene", at(300))
    board.apply(cid, "clear", at(900))
    with pytest.raises(sim.BoardError):                  # a cleared call stays cleared
        board.apply(cid, "clear", at(901))
    call = board.get(cid)
    assert (call.dispatched, call.en_route, call.on_scene, call.cleared) == (
        at(30), at(60), at(300), at(900))
    assert call.unit_id == "M-A1" and call.unit_home_zone == "A"
    assert call.delay_reason == ""                       # nothing ran late


def test_dispatch_needs_an_available_unit():
    board = make_board()
    one = board.add_call("A", 1, at(0)).call_id
    two = board.add_call("A", 1, at(1)).call_id
    with pytest.raises(sim.BoardError):
        board.apply(one, "dispatch", at(10))             # no unit chosen
    board.apply(one, "dispatch", at(10), unit_id="M-A1")
    with pytest.raises(sim.BoardError):                  # M-A1 is busy now
        board.apply(two, "dispatch", at(11), unit_id="M-A1")
    with pytest.raises(sim.BoardError):
        board.apply(two, "dispatch", at(11), unit_id="M-Z9")


def test_unit_picker_lists_home_zone_units_first_and_only_available_ones():
    board = make_board()
    first = board.add_call("B", 1, at(0)).call_id
    assert [u["unit_id"] for u in board.available_units("B")] == ["M-B1", "M-A1", "M-A2", "M-C1"]
    assert [u["unit_id"] for u in board.available_units("A")] == ["M-A1", "M-A2", "M-B1", "M-C1"]
    board.apply(first, "dispatch", at(5), unit_id="M-B1")
    assert "M-B1" not in [u["unit_id"] for u in board.available_units("B")]
    board.set_out_of_service("M-A1", at(6))
    assert [u["unit_id"] for u in board.available_units("A")] == ["M-A2", "M-C1"]


def test_late_stage_needs_a_reason_and_keeps_the_press_time():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    assert board.needs_reason(cid, "dispatch", at(64)) is None        # exactly on target
    late = board.needs_reason(cid, "dispatch", at(70))
    assert late["stage"] == "processing" and late["target"] == 64
    with pytest.raises(sim.ReasonRequired):
        board.apply(cid, "dispatch", at(70), unit_id="M-A1")
    with pytest.raises(sim.ReasonRequired):                           # not a real code
        board.apply(cid, "dispatch", at(70), unit_id="M-A1", reason="because")
    assert board.get(cid).status == "received"                        # nothing was accepted
    board.apply(cid, "dispatch", at(70), unit_id="M-A1", reason="unclear_address")
    assert board.get(cid).dispatched == at(70)
    assert board.get(cid).delay_reason == "unclear_address"


def test_turnout_and_travel_reasons_and_which_one_is_kept():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    board.apply(cid, "dispatch", at(70), unit_id="M-A1", reason="unclear_address")
    board.apply(cid, "en_route", at(70 + 61), reason="crew_not_ready")   # turnout 61 s > 60 s
    # P1 travel target is 480 s; arriving after 500 s is late.
    assert board.needs_reason(cid, "on_scene", at(131 + 500))["stage"] == "travel"
    board.apply(cid, "on_scene", at(131 + 500), reason="traffic_or_road_closure")
    call = board.get(cid)
    assert call.stage_reasons == {"processing": "unclear_address", "turnout": "crew_not_ready",
                                  "travel": "traffic_or_road_closure"}
    assert call.delay_reason == "traffic_or_road_closure"             # travel wins


def test_total_response_past_target_also_needs_a_reason():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    board.apply(cid, "dispatch", at(10), unit_id="M-A1")
    board.apply(cid, "en_route", at(110), reason="crew_not_ready")     # turnout 100 s > 60 s
    # Travel of 470 s is inside its 480 s target, but dispatch -> on scene = 570 s > 540 s.
    arrive = at(110 + 470)
    late = board.needs_reason(cid, "on_scene", arrive)
    assert late["measure"] == "response" and late["stage"] == "travel"
    with pytest.raises(sim.ReasonRequired):
        board.apply(cid, "on_scene", arrive)
    board.apply(cid, "on_scene", arrive, reason="traffic_or_road_closure")
    assert board.get(cid).stage_reasons["travel"] == "traffic_or_road_closure"
    # An on-target arrival needs no reason: turnout 60 s + travel 480 s = 540 s exactly.
    other = board.add_call("B", 1, at(1000)).call_id
    board.apply(other, "dispatch", at(1010), unit_id="M-B1")
    board.apply(other, "en_route", at(1070))
    assert board.needs_reason(other, "on_scene", at(1070 + 480)) is None


def test_breakdown_flags_the_call_and_records_the_reason_on_arrival():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    board.apply(cid, "dispatch", at(10), unit_id="M-A1")
    board.apply(cid, "en_route", at(40))
    assert board.set_out_of_service("M-A1", at(100)) == [cid]
    assert board.get(cid).breakdown
    assert board.fleet()[0]["state"] == "out_of_service"
    # Late arrival: the reason is filled in by the breakdown flag, no typing needed.
    assert board.needs_reason(cid, "on_scene", at(40 + 900)) is None
    board.apply(cid, "on_scene", at(40 + 900))
    assert board.get(cid).delay_reason == "ambulance_breakdown"
    # Even an on-time arrival records the breakdown.
    board2 = make_board()
    c2 = board2.add_call("A", 1, at(0)).call_id
    board2.apply(c2, "dispatch", at(10), unit_id="M-A1")
    board2.apply(c2, "en_route", at(40))
    board2.set_out_of_service("M-A1", at(50))
    board2.apply(c2, "on_scene", at(100))
    assert board2.get(c2).delay_reason == "ambulance_breakdown"


def test_out_of_service_and_back_in_service_rules():
    board = make_board()
    board.set_out_of_service("M-B1", at(0))
    with pytest.raises(sim.BoardError):
        board.set_out_of_service("M-B1", at(1))
    with pytest.raises(sim.BoardError):
        board.back_in_service("M-A1")
    with pytest.raises(sim.BoardError):
        board.set_out_of_service("M-Z9", at(1))
    board.back_in_service("M-B1")
    assert {u["unit_id"]: u["state"] for u in board.fleet()}["M-B1"] == "available"


def test_fleet_states_follow_the_call():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    state = lambda: {u["unit_id"]: u["state"] for u in board.fleet()}["M-A1"]   # noqa: E731
    assert state() == "available"
    board.apply(cid, "dispatch", at(10), unit_id="M-A1")
    assert state() == "dispatched"
    board.apply(cid, "en_route", at(30))
    assert state() == "en_route"
    board.apply(cid, "on_scene", at(300))
    assert state() == "on_scene"
    board.apply(cid, "clear", at(600))
    assert state() == "available"


# ---- clock colours, zone tiles and alerts --------------------------------------------------

def test_severity_thresholds():
    assert sim.severity(51, 64) == "green"      # 80% of 64 = 51.2
    assert sim.severity(52, 64) == "amber"
    assert sim.severity(64, 64) == "amber"      # red only past the target
    assert sim.severity(65, 64) == "red"
    assert sim.fmt_clock(75) == "1:15" and sim.fmt_clock(-5) == "0:00"
    assert sim.worst("green", "red", "amber") == "red"


def test_zone_tiles_colour_and_counts():
    board = make_board()
    board.add_call("A", 1, at(0))                       # waiting
    board.add_call("B", 1, at(0))
    tiles = {t["zone"]: t for t in board.zone_tiles(at(10))}
    assert tiles["A"]["severity"] == "green" and tiles["A"]["open"] == 1
    assert tiles["A"]["available"] == 2 and tiles["C"]["open"] == 0 and tiles["C"]["available"] == 1
    tiles = {t["zone"]: t for t in board.zone_tiles(at(55))}       # 55 s > 80% of 64 s
    assert tiles["A"]["severity"] == "amber"
    tiles = {t["zone"]: t for t in board.zone_tiles(at(65))}       # past 64 s
    assert tiles["A"]["severity"] == "red" and tiles["B"]["severity"] == "red"
    assert tiles["D"]["severity"] == "green"


def test_alerts_are_newest_first_and_resolve():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    assert board.alerts(at(60)) == []                                   # 60 s < 64 s: nothing yet
    board.set_out_of_service("M-C1", at(200))
    alerts = board.alerts(at(300))
    assert [a["kind"] for a in alerts] == ["unit", "queue"]             # unit 200 s, queue 64 s
    assert alerts[1]["active"] and alerts[1]["raised_at"] == at(64)
    board.apply(cid, "dispatch", at(310), unit_id="M-A1", reason="unclear_address")
    queue = [a for a in board.alerts(at(320)) if a["kind"] == "queue"][0]
    assert not queue["active"]                                          # resolved, stays in the log
    board.apply(cid, "en_route", at(400), reason="crew_not_ready")      # turnout 90 s > 60 s
    kinds = {a["kind"]: a["active"] for a in board.alerts(at(401))}
    assert kinds["turnout"] is False


def test_signature_ignores_time_but_sees_changes():
    board = make_board()
    cid = board.add_call("A", 1, at(0)).call_id
    first = board.signature()
    assert board.signature() == first
    board.apply(cid, "dispatch", at(5), unit_id="M-A1")
    assert board.signature() != first


# ---- the replay world and the CSV download --------------------------------------------------

def test_replay_calls_fill_the_replay_world_and_are_read_only():
    board = make_board()
    board.add_call("A", 1, at(0))                       # a wall-clock call
    board.set_mode("sim")
    replay = sim.Replay(two_calls(), speed=60, start_hour=8)
    replay.sim_time = at(1000)
    board.sync_replay(replay.state())
    assert board.mode == "sim"
    assert {c.call_id: c.status for c in board.calls()} == {"A": "on_scene", "B": "en_route"}
    with pytest.raises(sim.BoardError):
        board.apply("A", "clear", at(1001))             # replay calls cannot be pressed
    assert {u["unit_id"]: u["state"] for u in board.fleet()}["M-C1"] == "on_scene"
    # the wall-clock call is hidden while the replay runs and comes back after Reset
    board.reset_sim()
    assert board.mode == "wall"
    assert [c.status for c in board.calls()] == ["received"]


def test_to_frame_has_the_qc_schema_and_blank_for_unstamped():
    board = make_board()
    cid = board.add_call("C", 2, at(0)).call_id
    board.apply(cid, "dispatch", at(30), unit_id="M-C1")
    df = board.to_frame()
    assert list(df.columns) == list(qc.CALL_COLUMNS)
    row = df.iloc[0]
    assert row["call_received"] == "2026-09-20 08:00:00"
    assert row["dispatched"] == "2026-09-20 08:00:30"
    assert row["en_route"] == "" and row["delay_reason"] == ""
    assert row["unit_id"] == "M-C1" and row["unit_home_zone"] == "C" and row["priority"] == 2


def test_default_fleet_is_twelve_ambulances():
    fleet = sim.default_fleet()
    assert len(fleet) == 12 and fleet[0] == ("M-A1", "A") and fleet[-1] == ("M-F2", "F")
