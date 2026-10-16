#!/usr/bin/env python3
"""Response Watch: make the synthetic test datasets.

Run from anywhere:   python data/make_data.py
It writes five files next to this script. All data is invented. The random
numbers come from numpy's default_rng with seed 42, so a rerun gives
byte-identical files.

    units.csv           12 ambulances, 2 per zone
    calls_baseline.csv  28 days, stable process, nothing planted
    calls_demo.csv      42 days, same city, with four planted problems
    calls_messy.csv     about 60 calls, 3 days, with data defects
    actions_demo.csv    the one fix logged in the demo

The column list, zones, targets and shifts come from app/qc.py (and every reason
code is checked against it), so the data and the app cannot drift apart.
See data/README.md for the codebook.
"""

import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))
import qc  # noqa: E402  (needs the path line above)

SEED = 42
START = date(2026, 9, 1)            # day 1 of every file
ZONES = qc.ZONES                    # A..F on a 3x2 grid:  A B C / D E F

# --- the city -------------------------------------------------------------------
# Grid position (row, column) of each zone. Zones that share an edge are adjacent.
GRID = {"A": (0, 0), "B": (0, 1), "C": (0, 2), "D": (1, 0), "E": (1, 1), "F": (1, 2)}
ADJACENT = {z: [o for o in ZONES if abs(GRID[z][0] - GRID[o][0]) + abs(GRID[z][1] - GRID[o][1]) == 1]
            for z in ZONES}
HOME_UNITS = {z: [f"M-{z}1", f"M-{z}2"] for z in ZONES}      # 2 ambulances per zone
ALL_UNITS = [u for z in ZONES for u in HOME_UNITS[z]]

# Dispatchers work in shifts (qc.shift_of): 8 people, 2 or 3 per shift.
SHIFT_DISPATCHERS = {"day": ["DSP-01", "DSP-02", "DSP-03"],
                     "evening": ["DSP-04", "DSP-05", "DSP-06"],
                     "night": ["DSP-07", "DSP-08"]}

# Weight of each hour of the day (hour 0 to 23). Quiet 02-05, busiest 16-19.
HOUR_WEIGHTS = np.array([0.9, 0.7, 0.35, 0.30, 0.30, 0.40,      # 00-05
                         0.60, 0.80, 1.00, 1.10, 1.10, 1.10,     # 06-11
                         1.20, 1.20, 1.30, 1.50, 2.00, 2.40,     # 12-17
                         2.20, 1.80, 1.50, 1.30, 1.20, 1.10])    # 18-23
HOUR_P = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()

# --- the process (all times in seconds, distances in km) -----------------------------
CALLS_PER_ZONE_DAY = 16             # Poisson mean
PRIORITY_P = [0.45, 0.35, 0.20]     # P1, P2, P3
WEATHER_BLOCK = ["clear"] * 10 + ["rain"] * 3 + ["snow"]   # 71% / 21% / 7% per 14 days
WEATHER_TRAVEL = {"clear": 1.00, "rain": 1.07, "snow": 1.15}

PROCESSING_MEDIAN, PROCESSING_SIGMA = 40.0, 0.20    # call received -> dispatched
TURNOUT_MEDIAN, TURNOUT_SIGMA = 42.0, 0.25          # dispatched -> en route
DISTANCE_MEDIAN, DISTANCE_SIGMA = 2.8, 0.30         # km, for a unit from the home zone
ADJACENT_KM = (1.0, 2.0)                            # extra km when the unit is from next door
ADJACENT_CHOSEN = 0.0               # chance a neighbour's unit is picked even when a home unit is free.
                                    # 0: neighbour calls happen only when both home units are busy
                                    # (about 11% of calls); the draw stays so the random stream is fixed
SPEED_MEDIAN = {1: 42.0, 2: 36.0, 3: 32.0}          # km/h; P2 and P3 run without lights and sirens
SPEED_SIGMA = 0.12
ZONE_DISTANCE_FACTOR = {z: 1.0 for z in ZONES}      # typical trip length by zone ...
ZONE_DISTANCE_FACTOR["C"] = 1.08                    # ... zone C is the biggest zone: trips are 8% longer
SCENE_MINUTES = (20, 50)                            # on scene -> cleared

# --- planted signals (calls_demo.csv only) -------------------------------------------
D_SLOW_DAYS = (15, 28)              # zone D turnout is worse on these days (1-based)
D_TURNOUT_ADD = (60, 90)            # seconds added on every shift
D_NIGHT_FACTOR = 3.0                # night turnout is 3x the day and evening problem level
C_ROADWORKS_FROM_DAY = 20           # zone C, weekdays 16:00-19:00
C_ROADWORKS_HOURS = (16, 19)
C_ROADWORKS_FACTOR = 1.6
C_ROADWORKS_SIGMA = 0.25            # day-to-day spread of the slow-down (lognormal sigma)
PEAK_PROCESSING_HOURS = (17, 19)    # all zones, weekdays 17:00-19:00
PEAK_PROCESSING_FACTOR = 1.6
BREAKDOWN_UNIT = "M-B2"
BREAKDOWN_DATES = [date(2026, 9, 10), date(2026, 9, 24), date(2026, 10, 5)]
BREAKDOWN_EXTRA_S = 360             # +6 minutes of travel

NIGHT_HOURS = (22, 6)

# The one fix that is logged in the demo.
ACTIONS = [{
    "action_id": "A1", "date": "2026-09-29", "zone": "D", "stage": "turnout",
    "description": "Night crew readiness review at Station D: crew sleeps at the station, "
                   "new turnout drill",
    "owner": "EMS supervisor",
}]


# --- helpers -------------------------------------------------------------------------

def is_night(hour):
    return hour >= NIGHT_HOURS[0] or hour < NIGHT_HOURS[1]


def make_weather(rng, n_days):
    """Citywide weather per day. Each 14-day block holds exactly 10 clear, 3 rain
    and 1 snow day in random order, so the mix is the same in every two weeks."""
    days = []
    while len(days) < n_days:
        block = list(WEATHER_BLOCK)
        rng.shuffle(block)
        days.extend(block)
    return days[:n_days]


def draw_reason(u):
    """Delay reason when no cause is known: traffic 65%, crew not ready 25%, unclear address 10%."""
    if u < 0.65:
        return "traffic_or_road_closure"
    if u < 0.90:
        return "crew_not_ready"
    return "unclear_address"


def travel_seconds(km, priority, weather, speed_noise, factor=1.0):
    speed = SPEED_MEDIAN[priority] * speed_noise            # km/h
    return int(round(km / speed * 3600 * WEATHER_TRAVEL[weather] * factor))


# --- the simulator -------------------------------------------------------------------

def simulate(rng, n_days, weather, counts=None, planted=False):
    """Make the calls of n_days days. Returns a list of dicts sorted by call_received.

    counts  : array [n_days, 6] of calls per day and zone (default: Poisson(16)).
    planted : True adds the four demo problems (zone D turnout, zone C road works,
              peak-hour dispatcher overload, three breakdowns of M-B2).
    """
    if counts is None:
        counts = rng.poisson(CALLS_PER_ZONE_DAY, size=(n_days, len(ZONES)))
    day_idx = np.repeat(np.repeat(np.arange(n_days), len(ZONES)), counts.ravel())
    zone_idx = np.repeat(np.tile(np.arange(len(ZONES)), n_days), counts.ravel())
    n = len(day_idx)

    # Every random number is drawn up front, one array per quantity, so the stream
    # (and therefore the files) never depends on the order calls are processed in.
    hour = rng.choice(24, size=n, p=HOUR_P)
    second = rng.integers(0, 3600, size=n)
    priority = rng.choice([1, 2, 3], size=n, p=PRIORITY_P)
    proc_base = rng.lognormal(np.log(PROCESSING_MEDIAN), PROCESSING_SIGMA, size=n)
    turn_base = rng.lognormal(np.log(TURNOUT_MEDIAN), TURNOUT_SIGMA, size=n)
    dist_base = rng.lognormal(np.log(DISTANCE_MEDIAN), DISTANCE_SIGMA, size=n)
    extra_km = rng.uniform(*ADJACENT_KM, size=n)
    speed_noise = rng.lognormal(0.0, SPEED_SIGMA, size=n)
    scene = rng.integers(SCENE_MINUTES[0] * 60, SCENE_MINUTES[1] * 60 + 1, size=n)
    u_adjacent = rng.random(n)
    u_pick = rng.random(n)
    u_zone = rng.random(n)
    u_disp = rng.random(n)
    u_reason = rng.random(n)
    d_add = rng.uniform(*D_TURNOUT_ADD, size=n)
    works_noise = rng.lognormal(0.0, C_ROADWORKS_SIGMA, size=n)

    day0 = datetime(START.year, START.month, START.day)
    received = [day0 + timedelta(days=int(d), hours=int(h), seconds=int(s))
                for d, h, s in zip(day_idx, hour, second)]
    order = sorted(range(n), key=lambda i: (received[i], zone_idx[i], i))

    busy_until = {u: datetime.min for u in ALL_UNITS}     # when each ambulance is free again
    pending_breakdowns = set(BREAKDOWN_DATES) if planted else set()
    rows = []

    for i in order:
        zone = ZONES[zone_idx[i]]
        day = int(day_idx[i]) + 1                          # 1-based day number
        h = int(hour[i])
        pri = int(priority[i])
        wx = weather[int(day_idx[i])]
        when = received[i]
        weekday = when.weekday() < 5
        targets = qc.stage_targets(pri)

        # 1. processing
        proc = proc_base[i]
        if planted and weekday and PEAK_PROCESSING_HOURS[0] <= h < PEAK_PROCESSING_HOURS[1]:
            proc *= PEAK_PROCESSING_FACTOR
        processing = max(5, int(round(proc)))
        dispatched = when + timedelta(seconds=processing)

        # 2. which ambulance
        breakdown = False
        if (planted and zone == "B" and pri == 1 and h >= 10 and when.date() in pending_breakdowns
                and busy_until[BREAKDOWN_UNIT] <= dispatched):
            km = max(0.5, round(float(dist_base[i]) * ZONE_DISTANCE_FACTOR[zone], 1))
            base_travel = travel_seconds(km, pri, wx, speed_noise[i])
            if base_travel + BREAKDOWN_EXTRA_S > targets["travel"]:    # it will really be late
                breakdown = True
                pending_breakdowns.discard(when.date())
        if breakdown:
            unit, steps = BREAKDOWN_UNIT, 0
        else:
            unit, steps, dispatched = choose_unit(zone, u_adjacent[i] < ADJACENT_CHOSEN, u_pick[i],
                                                  u_zone[i], dispatched, busy_until)
            processing = int((dispatched - when).total_seconds())
        neighbour = steps > 0
        km = float(dist_base[i]) * ZONE_DISTANCE_FACTOR[zone] + float(extra_km[i]) * steps
        km = max(0.5, round(km, 1))

        # 3. turnout
        turn = turn_base[i]
        if planted and zone == "D" and D_SLOW_DAYS[0] <= day <= D_SLOW_DAYS[1]:
            turn += d_add[i]
            if is_night(h):
                turn *= D_NIGHT_FACTOR
        turnout = max(10, int(round(turn)))

        # 4. travel
        factor = 1.0
        roadworks = (planted and zone == "C" and day >= C_ROADWORKS_FROM_DAY and weekday
                     and C_ROADWORKS_HOURS[0] <= h < C_ROADWORKS_HOURS[1])
        if roadworks:
            factor = C_ROADWORKS_FACTOR * works_noise[i]
        travel = travel_seconds(km, pri, wx, speed_noise[i], factor)
        if breakdown:
            travel += BREAKDOWN_EXTRA_S

        en_route = dispatched + timedelta(seconds=turnout)
        on_scene = en_route + timedelta(seconds=travel)
        cleared = on_scene + timedelta(seconds=int(scene[i]))
        busy_until[unit] = cleared

        # 5. delay reason: only when a stage is late; the code that matches the cause
        late = {}
        if processing > targets["processing"]:
            late["processing"] = (processing - targets["processing"]) / targets["processing"]
        if turnout > targets["turnout"]:
            late["turnout"] = (turnout - targets["turnout"]) / targets["turnout"]
        if travel > targets["travel"]:
            late["travel"] = (travel - targets["travel"]) / targets["travel"]
        reason = ""
        if breakdown:
            reason = "ambulance_breakdown"                    # planted: always coded
        elif late:
            worst = max(late, key=late.get)                  # the stage that is latest, relatively
            if worst == "turnout":
                reason = "crew_not_ready"
            elif worst == "travel" and roadworks:
                reason = "traffic_or_road_closure"
            elif worst == "travel" and neighbour:
                reason = "unit_from_another_zone"
            elif worst == "travel" and wx != "clear":
                reason = "weather"
            else:
                reason = draw_reason(u_reason[i])

        shift = qc.shift_of(h)
        pool = SHIFT_DISPATCHERS[shift]
        rows.append({
            "zone": zone, "priority": pri,
            "call_received": when, "dispatched": dispatched, "en_route": en_route,
            "on_scene": on_scene, "cleared": cleared,
            "unit_id": unit, "unit_home_zone": unit[2], "distance_km": km,
            "dispatcher_id": pool[int(u_disp[i] * len(pool))], "weather": wx,
            "delay_reason": reason,
        })

    for k, row in enumerate(rows, start=1):
        row["call_id"] = f"C{k:05d}"
    return rows


def choose_unit(zone, neighbour_first, u_pick, u_zone, dispatched, busy_until):
    """Pick a free ambulance. Home zone first (unless the dispatcher picks a neighbour);
    if both home units are busy, a free unit from an adjacent zone; if those are busy
    too (rare), the nearest free unit anywhere. Returns (unit, steps) where steps is
    how many zones away the unit's home is (0 = home zone, 1 = next door)."""
    nbrs = ADJACENT[zone]
    k = int(u_zone * len(nbrs))
    nbrs = nbrs[k:] + nbrs[:k]
    groups = [HOME_UNITS[zone]] + [HOME_UNITS[z] for z in nbrs]
    if neighbour_first:
        groups = groups[1:] + groups[:1]
    far = sorted((z for z in ZONES if z != zone and z not in nbrs), key=lambda z: steps_between(zone, z))
    groups += [HOME_UNITS[z] for z in far]
    for units in groups:
        free = [u for u in units if busy_until[u] <= dispatched]
        if free:
            unit = free[int(u_pick * len(free))]
            return unit, steps_between(zone, unit[2]), dispatched
    unit = min(ALL_UNITS, key=lambda u: (busy_until[u], steps_between(zone, u[2])))
    return unit, steps_between(zone, unit[2]), busy_until[unit] + timedelta(seconds=5)


def steps_between(a, b):
    return abs(GRID[a][0] - GRID[b][0]) + abs(GRID[a][1] - GRID[b][1])


# --- the messy file ------------------------------------------------------------------

def make_messy(rng):
    """About 60 calls over 3 days with data defects (see data/README.md)."""
    n_days = 3
    weather = ["clear", "rain", "clear"]
    counts = rng.poisson(4.4, size=(n_days, len(ZONES)))
    counts[1, ZONES.index("E")] = 0               # no zone E calls on day 2
    counts[:, ZONES.index("F")] = [1, 0, 1]       # zone F has only 2 calls in the file
    rows = simulate(rng, n_days, weather, counts=counts, planted=False)

    # 1. A real but extreme outlier: priority 1, 25 minutes from dispatch to on scene.
    #    Pick a day-2 call from a busy zone whose ambulance has no call right after it.
    candidates = []
    for r in rows:
        if r["priority"] == 1 and r["call_received"].day == 2 and r["zone"] in ("A", "B", "C", "D"):
            clash = [o for o in rows if o["unit_id"] == r["unit_id"] and o is not r
                     and r["call_received"] < o["dispatched"] < r["cleared"] + timedelta(hours=1)]
            if not clash:
                candidates.append(r)
    outlier = candidates[int(rng.integers(len(candidates)))]
    turnout = int((outlier["en_route"] - outlier["dispatched"]).total_seconds())
    outlier["distance_km"] = 8.4
    outlier["on_scene"] = outlier["dispatched"] + timedelta(seconds=25 * 60)
    outlier["cleared"] = outlier["on_scene"] + timedelta(minutes=34)
    outlier["delay_reason"] = "traffic_or_road_closure"      # bridge closed, long detour
    assert 25 * 60 - turnout > qc.stage_targets(1)["travel"]

    # 2. Defects go into clean calls that have no delay reason and are not from zone F.
    pool = [r for r in rows if r is not outlier and r["delay_reason"] == "" and r["zone"] != "F"]
    picks = rng.choice(len(pool), size=7, replace=False)
    blank_enroute = [pool[i] for i in picks[:3]]
    scene_early = [pool[i] for i in picks[3:5]]
    dispatch_early = pool[picks[5]]
    duplicated = pool[picks[6]]

    for r in blank_enroute:
        r["en_route"] = None                                   # crew never pressed "en route"
    for r in scene_early:                                      # "on scene" pressed before "en route"
        r["on_scene"] = max(r["dispatched"] + timedelta(seconds=1),
                            r["en_route"] - timedelta(seconds=int(rng.integers(5, 30))))
    dispatch_early["dispatched"] = dispatch_early["call_received"] - timedelta(
        seconds=int(rng.integers(10, 40)))                     # clock out of sync

    at = rows.index(duplicated)
    rows.insert(at + 1, dict(duplicated))                      # the same row twice
    return rows


# --- writing -------------------------------------------------------------------------

def fmt_time(t):
    return "" if t is None else t.strftime("%Y-%m-%d %H:%M:%S")


def write_calls(path, rows):
    assert {r["delay_reason"] for r in rows} - {""} <= set(qc.REASON_CODES), "unknown reason code"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(qc.CALL_COLUMNS)
        for r in rows:
            out = []
            for col in qc.CALL_COLUMNS:
                v = r[col]
                if col in qc.TIMESTAMPS:
                    v = fmt_time(v)
                elif col == "distance_km":
                    v = f"{v:.1f}"
                out.append(v)
            w.writerow(out)


def write_table(path, header, records):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for rec in records:
            w.writerow([rec[h] for h in header])


def main():
    rng = np.random.default_rng(SEED)

    units = [{"unit_id": u, "home_zone": u[2]} for u in ALL_UNITS]
    write_table(HERE / "units.csv", ["unit_id", "home_zone"], units)

    baseline = simulate(rng, 28, make_weather(rng, 28), planted=False)
    write_calls(HERE / "calls_baseline.csv", baseline)

    demo = simulate(rng, 42, make_weather(rng, 42), planted=True)
    write_calls(HERE / "calls_demo.csv", demo)

    messy = make_messy(rng)
    write_calls(HERE / "calls_messy.csv", messy)

    write_table(HERE / "actions_demo.csv",
                ["action_id", "date", "zone", "stage", "description", "owner"], ACTIONS)

    for name, rows in [("units.csv", units), ("calls_baseline.csv", baseline),
                       ("calls_demo.csv", demo), ("calls_messy.csv", messy),
                       ("actions_demo.csv", ACTIONS)]:
        print(f"wrote data/{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
