"""Response Watch live-board logic: the call model, the fleet, zone tiles and the shift replay.

Pure Python: no Shiny and no plotting, so every rule here is unit-tested
(tests/test_simulator.py). The screens in ui_dispatcher.py only call this file and
draw the result. Targets and reason codes come from qc.py; nothing in this file
computes a percentile or any other statistic.

Time is always passed in as `now` (a naive datetime) instead of read from the
clock inside a function, so the same code runs on wall-clock time and on the
simulated clock of a shift replay.

A call moves one step at a time:
    received -> dispatched -> en route -> on scene -> cleared
and only the next step is allowed (poka-yoke). A step that ends a stage that ran
past its target needs a delay reason (qc.REASON_CODES) before it is accepted.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import qc  # noqa: E402

# ---- constants ---------------------------------------------------------------------

#: The five timestamps of a call, in the order they are stamped.
ORDER = qc.TIMESTAMPS

#: Status of a call from the timestamp that was stamped last.
STATUS_OF = {
    "call_received": "received",
    "dispatched": "dispatched",
    "en_route": "en_route",
    "on_scene": "on_scene",
    "cleared": "cleared",
}
STATUS_LABEL = {
    "received": "Waiting for dispatch",
    "dispatched": "Dispatched",
    "en_route": "En route",
    "on_scene": "On scene",
    "cleared": "Cleared",
}

#: The one button that is valid for a call in each status.
NEXT_ACTION = {
    "received": "dispatch",
    "dispatched": "en_route",
    "en_route": "on_scene",
    "on_scene": "clear",
}
ACTION_LABEL = {
    "dispatch": "Dispatch",
    "en_route": "En route",
    "on_scene": "On scene",
    "clear": "Clear",
}

#: Which stage each button ends (clear ends no timed stage).
ACTION_STAGE = {"dispatch": "processing", "en_route": "turnout", "on_scene": "travel"}

UNIT_LABEL = {
    "available": "Available",
    "dispatched": "Dispatched",
    "en_route": "En route",
    "on_scene": "On scene",
    "out_of_service": "Out of service",
}

#: A clock turns amber above this share of its target, red past the target.
AMBER_SHARE = 0.8

DEFAULT_DAY = "2026-09-20"
SPEEDS = (30, 60, 120)             # shift replay speeds
MANUAL_SPEEDS = (1, 10, 30, 60)    # clock speeds while calls are logged by hand

#: The shifts a replay can start at (hour of day).
START_HOURS = {0: "Midnight", 6: "Day shift, 06:00", 14: "Evening shift, 14:00",
               22: "Night shift, 22:00"}

MANUAL_DISPATCHER = "LIVE"


def default_fleet() -> list[tuple[str, str]]:
    """Two ambulances per zone (M-A1, M-A2 ... M-F2), used when data/units.csv is missing."""
    return [(f"M-{zone}{n}", zone) for zone in qc.ZONES for n in (1, 2)]


def load_units(path=None) -> list[tuple[str, str]]:
    """[(unit_id, home_zone)] from units.csv, or the 12-unit default list.

    Accepts a `unit_id` column and a home-zone column named `unit_home_zone`,
    `home_zone` or `zone`. Anything unreadable falls back to the default list.
    """
    try:
        if path is None:
            path = qc.find_data_dir() / "units.csv"
        df = pd.read_csv(path, dtype=str)
        zone_col = next((c for c in ("unit_home_zone", "home_zone", "zone")
                         if c in df.columns), None)
        if "unit_id" not in df.columns or zone_col is None:
            return default_fleet()
        units = [(str(u).strip(), str(z).strip())
                 for u, z in zip(df["unit_id"], df[zone_col])
                 if str(u).strip() and str(z).strip() in qc.ZONES]
        return units or default_fleet()
    except (OSError, ValueError, pd.errors.ParserError, FileNotFoundError):
        return default_fleet()


# ---- small helpers -----------------------------------------------------------------

_EPOCH = datetime(1970, 1, 1)


def epoch(dt: datetime) -> float:
    """Seconds since 1970-01-01 for a naive datetime (no time zone arithmetic)."""
    return (dt - _EPOCH).total_seconds()


def fmt_clock(seconds: float | None) -> str:
    """Whole seconds as m:ss, e.g. 75 -> '1:15'. Negative or missing -> '0:00'."""
    if seconds is None or seconds != seconds or seconds < 0:
        return "0:00"
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def fmt_time(dt: datetime | None) -> str:
    """HH:MM:SS of a timestamp, or an empty string."""
    return "" if dt is None else dt.strftime("%H:%M:%S")


def severity(elapsed_s: float | None, target_s: float) -> str:
    """'red' past the target, 'amber' above 80% of it, else 'green'."""
    if elapsed_s is None:
        return "green"
    if elapsed_s > target_s:
        return "red"
    if elapsed_s > AMBER_SHARE * target_s:
        return "amber"
    return "green"


_RANK = {"green": 0, "amber": 1, "red": 2}


def worst(*levels: str) -> str:
    """The most serious of several 'green' / 'amber' / 'red' levels."""
    return max(levels, key=_RANK.__getitem__, default="green")


# ---- the replay of one day of the demo file ------------------------------------------

def day_calls(calls_df: pd.DataFrame, day) -> pd.DataFrame:
    """The calls received on one calendar day, in the order they arrived."""
    d0 = pd.Timestamp(day).normalize()
    keep = calls_df["call_received"].dt.normalize() == d0
    return calls_df[keep].sort_values("call_received").reset_index(drop=True)


def available_days(calls_df: pd.DataFrame) -> list[str]:
    """Days (YYYY-MM-DD) that have at least one call, oldest first."""
    days = calls_df["call_received"].dropna().dt.normalize().drop_duplicates().sort_values()
    return [d.strftime("%Y-%m-%d") for d in days]


def pick_day(days: list[str], preferred: str = DEFAULT_DAY) -> str:
    """The preferred day if the file has it, else the newest day in the file."""
    if preferred in days:
        return preferred
    return days[-1] if days else preferred


def events_until(calls_df: pd.DataFrame, sim_time) -> pd.DataFrame:
    """Each call's state at a simulated time.

    Returns the calls already received at `sim_time` (call_received <= sim_time),
    in arrival order, with the same columns as qc.CALL_COLUMNS plus `status`
    ('received', 'dispatched', 'en_route', 'on_scene' or 'cleared'). Stamps that
    come after `sim_time` are blanked (NaT). The unit, distance and delay reason
    stay blank until the call has been dispatched / has reached the scene, as
    they would be in CAD.
    """
    t = pd.Timestamp(sim_time)
    df = calls_df.reindex(columns=list(qc.CALL_COLUMNS))
    out = df[df["call_received"] <= t].copy()
    status = pd.Series("received", index=out.index, dtype=object)
    for col in ORDER[1:]:
        reached = out[col].notna() & (out[col] <= t)
        out[col] = out[col].where(reached, pd.NaT)
        status[reached] = STATUS_OF[col]
    out["status"] = status
    not_dispatched = out["dispatched"].isna()
    for col in ("unit_id", "unit_home_zone", "distance_km"):
        out[col] = out[col].astype(object)
        out.loc[not_dispatched, col] = None
    no_arrival = out["on_scene"].isna()
    out["delay_reason"] = out["delay_reason"].astype(object)
    out.loc[no_arrival, "delay_reason"] = ""
    return out.sort_values("call_received", kind="stable").reset_index(drop=True)


class Replay:
    """A shift replay on a simulated clock. It never reads the real clock itself:
    the caller says how many real seconds went by (`advance`)."""

    def __init__(self, day_df: pd.DataFrame, speed: int = 60, start_hour: int = 0):
        if day_df.empty:
            raise ValueError("no calls on that day")
        self.day = day_df["call_received"].min().normalize()
        self.speed = int(speed)
        self.start_time = (self.day + pd.Timedelta(hours=int(start_hour))).to_pydatetime()
        # Calls that were already cleared before the start time are history, not part of the replay.
        day_df = day_df[~(day_df["cleared"] <= pd.Timestamp(self.start_time))]
        if day_df.empty:
            raise ValueError("no calls on that day after the start time")
        self.calls = day_df.reset_index(drop=True)
        self.sim_time = self.start_time
        last = day_df[list(ORDER)].max().max()      # the latest stamp of the day
        self.end_time = pd.Timestamp(last).to_pydatetime() + timedelta(seconds=1)
        self.running = False
        self.finished = False

    def start(self) -> None:
        if not self.finished:
            self.running = True

    def pause(self) -> None:
        self.running = False

    def set_speed(self, speed: int) -> None:
        self.speed = int(speed)

    def advance(self, real_seconds: float) -> None:
        """Move the simulated clock forward by real_seconds x speed (only while running)."""
        if not self.running or real_seconds <= 0:
            return
        self.sim_time = self.sim_time + timedelta(seconds=real_seconds * self.speed)
        if self.sim_time >= self.end_time:
            self.sim_time = self.end_time
            self.running = False
            self.finished = True

    @property
    def now(self) -> datetime:
        """The simulated clock, to the whole second."""
        return self.sim_time.replace(microsecond=0)

    def state(self) -> pd.DataFrame:
        return events_until(self.calls, self.sim_time)


# ---- the live call model --------------------------------------------------------------

class BoardError(ValueError):
    """A button press that is not allowed (wrong step, unit busy, unknown call ...)."""


class ReasonRequired(BoardError):
    """The stage ran past its target, so a delay reason must be given first."""

    def __init__(self, late: dict):
        super().__init__("A delay reason is required: the stage ran past its target.")
        self.late = late


@dataclass
class Call:
    """One call, with the qc.CALL_COLUMNS fields plus a few board-only fields."""

    call_id: str
    zone: str
    priority: int
    call_received: datetime
    dispatched: datetime | None = None
    en_route: datetime | None = None
    on_scene: datetime | None = None
    cleared: datetime | None = None
    unit_id: str = ""
    unit_home_zone: str = ""
    distance_km: float | None = None
    dispatcher_id: str = ""
    weather: str = ""
    delay_reason: str = ""
    source: str = "manual"            # "manual" (buttons) or "sim" (shift replay)
    breakdown: bool = False           # the assigned unit broke down on the way
    stage_reasons: dict = field(default_factory=dict)   # stage -> reason code

    @property
    def status(self) -> str:
        status = "received"
        for col in ORDER[1:]:
            if getattr(self, col) is not None:
                status = STATUS_OF[col]
        return status

    @property
    def targets(self) -> dict:
        return qc.stage_targets(self.priority)

    def elapsed(self, stage: str, now: datetime) -> float | None:
        """Seconds a stage has run (or ran): processing, turnout, travel or response."""
        start, end = {
            "processing": (self.call_received, self.dispatched),
            "turnout": (self.dispatched, self.en_route),
            "travel": (self.en_route, self.on_scene),
            "response": (self.dispatched, self.on_scene),
        }[stage]
        if start is None:
            return None
        return ((end or now) - start).total_seconds()

    def severity(self, now: datetime) -> str:
        """Colour of the call's current clock(s) against their targets."""
        tg = self.targets
        status = self.status
        if status == "received":
            return severity(self.elapsed("processing", now), tg["processing"])
        if status == "dispatched":
            return severity(self.elapsed("turnout", now), tg["turnout"])
        if status == "en_route":
            return worst(severity(self.elapsed("travel", now), tg["travel"]),
                         severity(self.elapsed("response", now), tg["response"]))
        if status == "on_scene":
            return severity(self.elapsed("response", now), tg["response"])
        return "green"


@dataclass
class World:
    """Calls and out-of-service units on one clock (the wall clock or the replay clock)."""

    calls: dict = field(default_factory=dict)       # call_id -> Call
    oos: dict = field(default_factory=dict)         # unit_id -> datetime it went out
    seq: int = 0


def late_stage(call: Call, action: str, now: datetime) -> dict | None:
    """The stage that this button press would end, if it ran past its target.

    Returns {"stage", "elapsed", "target"} (seconds), else None. Pressing On scene
    ends travel, but a total response past target counts as late too.
    """
    tg = call.targets
    if action == "dispatch":
        checks = [("processing", "processing")]
    elif action == "en_route":
        checks = [("turnout", "turnout")]
    elif action == "on_scene":
        checks = [("travel", "travel"), ("response", "travel")]
    else:
        return None
    for measure, stage in checks:
        elapsed = call.elapsed(measure, now)
        if elapsed is not None and elapsed > tg[measure]:
            return {"stage": stage, "measure": measure, "elapsed": elapsed,
                    "target": tg[measure]}
    return None


class ManualClock:
    """The clock for work done by hand: wall time at 1x, or faster at 10x, 30x, 60x.

    Pure: the caller passes in the monotonic time, so tests control it. Changing
    the speed continues from the current board time (the clock never jumps), and
    reset() goes back to a given wall time, keeping the speed.
    """

    def __init__(self, start: datetime, mono: float, speed: int = 1):
        self.base_time = start
        self.base_mono = mono
        self.speed = int(speed)

    def _exact(self, mono: float) -> datetime:
        return self.base_time + timedelta(seconds=(mono - self.base_mono) * self.speed)

    def now(self, mono: float) -> datetime:
        """The board time, to the whole second."""
        return self._exact(mono).replace(microsecond=0)

    def set_speed(self, speed: int, mono: float) -> None:
        self.base_time = self._exact(mono)
        self.base_mono = mono
        self.speed = int(speed)

    def reset(self, start: datetime, mono: float) -> None:
        self.base_time = start
        self.base_mono = mono


class Board:
    """The live board of one browser session: calls, units and zone tiles.

    There are two worlds, one on the wall clock and one on the replay clock, so
    that calls entered on one clock never mix with clocks of the other.
    """

    def __init__(self, units: list[tuple[str, str]] | None = None):
        self.units = list(units) if units else default_fleet()
        self.worlds = {"wall": World(), "sim": World()}
        self.mode = "wall"

    # -- worlds
    @property
    def world(self) -> World:
        return self.worlds[self.mode]

    def set_mode(self, mode: str) -> None:
        if mode not in self.worlds:
            raise ValueError(mode)
        self.mode = mode

    def reset_sim(self) -> None:
        """Forget the replay and every call entered on the replay clock."""
        self.worlds["sim"] = World()
        self.mode = "wall"

    def reset_all(self) -> None:
        """Back to an empty board: no calls (replay or manual), every unit available."""
        self.worlds = {"wall": World(), "sim": World()}
        self.mode = "wall"

    def calls(self) -> list[Call]:
        return list(self.world.calls.values())

    def get(self, call_id: str) -> Call:
        try:
            return self.world.calls[call_id]
        except KeyError:
            raise BoardError(f"Call {call_id} is not on the board.") from None

    # -- units
    def home_zone(self, unit_id: str) -> str:
        for uid, zone in self.units:
            if uid == unit_id:
                return zone
        raise BoardError(f"Unit {unit_id} is not in the fleet.")

    def fleet(self) -> list[dict]:
        """Every unit with its state: available, dispatched, en_route, on_scene or out_of_service."""
        busy: dict[str, tuple[int, str, str]] = {}
        rank = {"dispatched": 1, "en_route": 2, "on_scene": 3}
        for call in self.world.calls.values():
            status = call.status
            if call.unit_id and status in rank:
                cur = busy.get(call.unit_id)
                if cur is None or rank[status] > cur[0]:
                    busy[call.unit_id] = (rank[status], status, call.call_id)
        out = []
        for unit_id, zone in self.units:
            state, call_id = "available", ""
            if unit_id in busy:
                _, state, call_id = busy[unit_id]
            if unit_id in self.world.oos:
                state = "out_of_service"
            out.append({"unit_id": unit_id, "home_zone": zone, "state": state,
                        "call_id": call_id, "since": self.world.oos.get(unit_id)})
        return out

    def available_units(self, zone: str) -> list[dict]:
        """Available units for a call in `zone`, units from that home zone first."""
        free = [u for u in self.fleet() if u["state"] == "available"]
        free.sort(key=lambda u: (u["home_zone"] != zone, u["unit_id"]))
        return free

    def set_out_of_service(self, unit_id: str, now: datetime) -> list[str]:
        """Take a unit out of service. Open manual calls it is rolling to are flagged
        (reason ambulance_breakdown is recorded when the call reaches the scene).
        Returns the ids of the calls that were flagged."""
        self.home_zone(unit_id)       # raises for an unknown unit
        if unit_id in self.world.oos:
            raise BoardError(f"Unit {unit_id} is already out of service.")
        self.world.oos[unit_id] = now
        flagged = []
        for call in self.world.calls.values():
            if (call.unit_id == unit_id and call.source == "manual"
                    and call.status in ("dispatched", "en_route")):
                call.breakdown = True
                flagged.append(call.call_id)
        return flagged

    def back_in_service(self, unit_id: str) -> None:
        self.home_zone(unit_id)
        if unit_id not in self.world.oos:
            raise BoardError(f"Unit {unit_id} is not out of service.")
        del self.world.oos[unit_id]

    # -- calls: manual entry and the buttons
    def add_call(self, zone: str, priority: int, now: datetime) -> Call:
        """A new manual call. call_received is the clock; the id is generated."""
        if zone not in qc.ZONES:
            raise BoardError(f"Unknown zone {zone!r}.")
        if int(priority) not in qc.PRIORITIES:
            raise BoardError(f"Unknown priority {priority!r}.")
        self.world.seq += 1
        call_id = f"LIVE-{now:%Y%m%d}-{self.world.seq:03d}"
        call = Call(call_id=call_id, zone=zone, priority=int(priority),
                    call_received=now, dispatcher_id=MANUAL_DISPATCHER)
        self.world.calls[call_id] = call
        return call

    def needs_reason(self, call_id: str, action: str, now: datetime) -> dict | None:
        """Late-stage info if pressing `action` now needs a typed-in reason, else None.
        A call flagged for a breakdown gets its reason automatically."""
        call = self.get(call_id)
        late = late_stage(call, action, now)
        if late and not call.breakdown:
            return late
        return None

    def check(self, call_id: str, action: str, unit_id: str | None = None) -> Call:
        """Raise BoardError unless `action` is the next valid step for this call
        (and, for a dispatch, the unit is free). Returns the call."""
        call = self.get(call_id)
        if call.source != "manual":
            raise BoardError(f"Call {call_id} belongs to the shift replay and is read-only.")
        status = call.status
        if status == "cleared":
            raise BoardError(f"Call {call_id} is already cleared.")
        expected = NEXT_ACTION[status]
        if action != expected:
            raise BoardError(f"Call {call_id} is {STATUS_LABEL[status].lower()}; "
                             f"the next step is {ACTION_LABEL[expected]}.")
        if action == "dispatch":
            if not unit_id:
                raise BoardError("Choose a unit to dispatch.")
            unit = next((u for u in self.fleet() if u["unit_id"] == unit_id), None)
            if unit is None:
                raise BoardError(f"Unit {unit_id} is not in the fleet.")
            if unit["state"] != "available":
                raise BoardError(f"Unit {unit_id} is {UNIT_LABEL[unit['state']].lower()}.")
        return call

    def apply(self, call_id: str, action: str, now: datetime, *,
              reason: str | None = None, unit_id: str | None = None) -> Call:
        """Press a button. `now` is the time of the press, stamped from the clock.

        Raises BoardError when the press is not the next valid step, and
        ReasonRequired when the stage ran late and no valid reason was given.
        """
        call = self.check(call_id, action, unit_id)

        late = late_stage(call, action, now)
        if late:
            if call.breakdown:
                reason = "ambulance_breakdown"
            elif reason not in qc.REASON_CODES:
                raise ReasonRequired(late)
            call.stage_reasons[late["stage"]] = reason

        if action == "dispatch":
            call.dispatched = now
            call.unit_id = unit_id
            call.unit_home_zone = self.home_zone(unit_id)
        elif action == "en_route":
            call.en_route = now
        elif action == "on_scene":
            call.on_scene = now
            if call.breakdown:
                call.stage_reasons["travel"] = "ambulance_breakdown"
                call.breakdown = False
        elif action == "clear":
            call.cleared = now
        call.delay_reason = next((call.stage_reasons[s] for s in ("travel", "turnout", "processing")
                                  if s in call.stage_reasons), "")
        return call

    # -- shift replay
    def sync_replay(self, state: pd.DataFrame) -> None:
        """Replace the replay calls in the replay world with `state` (see events_until)."""
        world = self.worlds["sim"]
        world.calls = {cid: c for cid, c in world.calls.items() if c.source != "sim"}
        for rec in state.to_dict("records"):
            def stamp(col, rec=rec):
                v = rec.get(col)
                return None if v is None or pd.isna(v) else pd.Timestamp(v).to_pydatetime()

            def text(col, rec=rec):
                v = rec.get(col)
                return "" if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NA else str(v)

            dist = rec.get("distance_km")
            call = Call(
                call_id=str(rec["call_id"]), zone=str(rec["zone"]), priority=int(rec["priority"]),
                call_received=stamp("call_received"),
                dispatched=stamp("dispatched"), en_route=stamp("en_route"),
                on_scene=stamp("on_scene"), cleared=stamp("cleared"),
                unit_id=text("unit_id"), unit_home_zone=text("unit_home_zone"),
                distance_km=None if dist is None or pd.isna(dist) else float(dist),
                dispatcher_id=text("dispatcher_id"), weather=text("weather"),
                delay_reason=text("delay_reason"), source="sim")
            world.calls[call.call_id] = call

    # -- summaries for the screen
    def counts(self) -> dict:
        """Open calls per status and the number of available units."""
        out = {s: 0 for s in STATUS_LABEL}
        for call in self.world.calls.values():
            out[call.status] += 1
        out["units_available"] = sum(1 for u in self.fleet() if u["state"] == "available")
        return out

    def zone_tiles(self, now: datetime) -> list[dict]:
        """For each zone: open calls, free home-zone units and the worst clock colour."""
        fleet = self.fleet()
        tiles = []
        for zone in qc.ZONES:
            open_calls = [c for c in self.world.calls.values()
                          if c.zone == zone and c.status != "cleared"]
            level = worst(*[c.severity(now) for c in open_calls])
            free = sum(1 for u in fleet if u["home_zone"] == zone and u["state"] == "available")
            tiles.append({"zone": zone, "open": len(open_calls), "available": free,
                          "severity": level})
        return tiles

    def signature(self) -> tuple:
        """Changes whenever anything visible in the tables or the fleet changes
        (but not merely because time passed)."""
        calls = tuple(sorted((c.call_id, c.status, c.unit_id, c.breakdown, c.delay_reason)
                             for c in self.world.calls.values()))
        return (self.mode, calls, tuple(sorted(self.world.oos)))

    def time_signature(self, now: datetime) -> tuple:
        """Changes whenever a zone tile changes colour because of the clock."""
        return tuple((t["zone"], t["severity"]) for t in self.zone_tiles(now))

    def calls_frame(self, now: datetime | None = None, *, manual_only: bool = False,
                    all_worlds: bool = False) -> pd.DataFrame:
        """The board's calls in the qc.CALL_COLUMNS schema, with real timestamps (NaT = not yet).

        By default only the clock the board is showing; stamps after `now` are blanked.
        manual_only keeps the calls entered by hand (not the shift replay).
        """
        worlds = list(self.worlds.values()) if all_worlds else [self.world]
        rows = []
        for world in worlds:
            for c in world.calls.values():
                if manual_only and c.source != "manual":
                    continue
                row = {col: getattr(c, col) for col in qc.CALL_COLUMNS}
                for col in qc.TIMESTAMPS:
                    v = row[col]
                    row[col] = pd.NaT if v is None or (now is not None and v > now) else v
                rows.append(row)
        df = pd.DataFrame(rows, columns=list(qc.CALL_COLUMNS))
        for col in qc.TIMESTAMPS:
            df[col] = pd.to_datetime(df[col])
        return df.sort_values("call_received", kind="stable").reset_index(drop=True)

    def to_frame(self) -> pd.DataFrame:
        """Every call of the session (both clocks) in the qc.CALL_COLUMNS schema, for the
        CSV download: timestamps as text, blank = not stamped."""
        df = self.calls_frame(all_worlds=True)
        for col in qc.TIMESTAMPS:
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
        for col in qc.CALL_COLUMNS:
            if col not in qc.TIMESTAMPS:
                df[col] = df[col].astype(object).where(df[col].notna(), "")
        return df
