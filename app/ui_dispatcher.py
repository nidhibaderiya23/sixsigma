"""Dispatcher screens: the live board and the shift review (History tab).

The call model, the fleet, the clocks and the shift replay live in simulator.py
(pure Python, unit-tested); every percentile, limit and suggestion comes from
qc.py. This file only draws them and passes the button presses back.

State lives inside the server function, so every browser session has its own board.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import functools  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402

import pandas as pd  # noqa: E402
from shiny import module, reactive, render, req, ui  # noqa: E402
from shiny.module import resolve_id  # noqa: E402

import charts  # noqa: E402
import qc  # noqa: E402
import simulator as sim  # noqa: E402
import zonemap  # noqa: E402

#: How many cleared or on-scene calls the Resolved panel lists.
RESOLVED_SHOWN = 60

#: Seconds between refreshes of the History tab (shift window, suggestions, charts).
HISTORY_REFRESH_S = 5

SPEED_CHOICES = {str(s): f"{s}x" for s in sim.SPEEDS}
MANUAL_SPEED_CHOICES = {str(s): f"{s}x" for s in sim.MANUAL_SPEEDS}
START_CHOICES = {str(h): f"Start {h:02d}:00" for h in sim.START_HOURS}
ZONE_CHOICES = {z: f"{z} \u00b7 {qc.ZONE_NAMES[z]}" for z in qc.ZONES}
PRIORITY_CHOICES = {str(p): f"{p}: {qc.PRIORITY_NAME[p]}" for p in qc.PRIORITIES}
HISTORY_PRIORITY_CHOICES = {str(p): f"Priority {p}: {qc.PRIORITY_NAME[p]}" for p in qc.PRIORITIES}

#: Display names for the dispatcher_tips rules.
TIP_NAMES = {"T1": "Dispatch now", "T2": "Rebalance", "T3": "Cover", "T4": "Route",
             "T5": "Station alert", "T6": "Dispatcher load"}

# ---- shared building blocks (the supervisor screens use these too) ------------------------

_ICONS = {
    "pulse": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "send": '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    "route": '<polygon points="3 11 22 2 13 21 11 13 3 11"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "truck": ('<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>'
              '<circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>'),
    "info": ('<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/>'
             '<line x1="12" y1="8" x2="12.01" y2="8"/>'),
    "headset": ('<path d="M3 18v-6a9 9 0 0 1 18 0v6"/>'
                '<path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>'),
    "chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "arrow": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
}


def icon(name: str):
    """A small outline icon (inline SVG that takes the text colour)."""
    return ui.HTML(
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        + _ICONS[name] + "</svg>")


def eyebrow(text: str):
    """A tiny letter-spaced label (shown in capitals by the stylesheet)."""
    return ui.div(text, class_="rw-eyebrow")


def card_head(label: str, title: str, right=None, step: int | None = None):
    """A card's one title, with an optional element on the right.

    `label` is accepted so older calls still work, but it is ignored: a card shows one title.
    `step` puts a small numbered badge before the title (the steps of the call process).
    """
    badge = ui.span(str(step), class_="rw-step", **{"aria-label": f"Step {step}"}) if step else None
    return ui.div(ui.div(badge, ui.span(title), class_="rw-title"), right, class_="rw-card-head")


def chip(text, tone: str | None = None, **attrs):
    """A small pill, optionally with a coloured status dot."""
    dot = ui.span(class_="rw-dot", **{"data-tone": tone}) if tone else None
    extra = attrs.pop("class_", "")
    return ui.span(dot, text, class_=f"rw-chip {extra}".strip(), **attrs)


def placeholder_card(label: str, title: str, message: str):
    return ui.div(card_head(label, title), ui.div(message, class_="rw-empty"), class_="rw-card")


# ---- data files (read-only, shared between sessions; never changed after loading) ----------

def _data_path(name: str) -> Path | None:
    try:
        return qc.find_data_dir() / f"calls_{name}.csv"
    except FileNotFoundError:
        return None


@functools.lru_cache(maxsize=6)
def _read_calls(path: str, mtime: float) -> pd.DataFrame:
    return qc.load_calls(path)


@functools.lru_cache(maxsize=6)
def _read_stages(path: str, mtime: float) -> pd.DataFrame:
    return qc.stage_times(qc.load_calls(path))


def get_calls(name: str, stages: bool = False):
    """(DataFrame, "") for data/calls_<name>.csv, or (None, why) if it cannot be shown.

    With stages=True the frame has the qc.stage_times columns, else the raw calls.
    """
    path = _data_path(name)
    if path is None or not path.is_file():
        return None, "Data not generated yet"
    try:
        reader = _read_stages if stages else _read_calls
        return reader(str(path), path.stat().st_mtime), ""
    except Exception as exc:  # a bad file should show a message, not a stack trace
        return None, f"Could not read {path.name}: {exc}"


# ---- rows for the live board ------------------------------------------------------------------

def _attrs(**kw):
    """Turn data_foo=1 into {'data-foo': '1'} (None values are dropped)."""
    return {k.replace("_", "-"): str(v) for k, v in kw.items() if v is not None}


def tag(text: str, tone: str | None = None):
    cls = "rw-tag" + (f" rw-tag-{tone}" if tone else "")
    return ui.span(text, class_=cls)


def clock_box(label: str, since: datetime, target_s: float, now: datetime):
    """A running clock: the browser repaints it every second from the server clock."""
    elapsed = (now - since).total_seconds()
    return ui.div(
        ui.span(sim.fmt_clock(elapsed), class_="rw-clock",
                **_attrs(data_since=sim.epoch(since), data_target=target_s,
                         data_sev=sim.severity(elapsed, target_s))),
        ui.span(label, class_="rw-cap"), class_="rw-clockbox")


def final_box(label: str, seconds: float, target_s: float):
    """A stopped clock (a finished stage)."""
    return ui.div(
        ui.span(sim.fmt_clock(seconds), class_="rw-final",
                **_attrs(data_sev=sim.severity(seconds, target_s))),
        ui.span(label, class_="rw-cap"), class_="rw-clockbox")


def row(call, sub: str, *, actions=(), clocks=(), live=True, sev="green", extra_tags=()):
    """One dark inset row: status dot, bold title + muted subtitle, buttons, clocks."""
    title = ui.div(call.call_id, tag(f"Zone {call.zone}"), tag(f"P{call.priority}"),
                   *extra_tags, class_="rw-row-title")
    attrs = {"data-sev": sev}
    if live:
        attrs["data-live"] = "1"
    return ui.div(
        ui.span(class_="rw-dot"),
        ui.div(title, ui.div(sub, class_="rw-row-sub"), class_="rw-row-main"),
        ui.div(*actions, class_="rw-row-actions") if actions else None,
        ui.div(*clocks, class_="rw-row-clocks") if clocks else None,
        class_="rw-row", **attrs)


def action_button(label: str, action: str, call_id: str, pick_id: str | None = None,
                  disabled: bool = False):
    attrs = {"data-rw-action": action, "data-rw-call": call_id}
    if pick_id:
        attrs["data-rw-pick"] = pick_id
    return ui.tags.button(label, type="button", class_="rw-btn", disabled=disabled or None, **attrs)


def unit_picker(call, available: list[dict], selected: str | None):
    """Available units only, units from the call's own zone listed first."""
    home = [u for u in available if u["home_zone"] == call.zone]
    other = [u for u in available if u["home_zone"] != call.zone]

    def opt(u, plain):
        label = u["unit_id"] if plain else f"{u['unit_id']} (zone {u['home_zone']})"
        return ui.tags.option(label, value=u["unit_id"], selected=(u["unit_id"] == selected) or None)

    groups = []
    if home:
        groups.append(ui.tags.optgroup(*[opt(u, True) for u in home], label=f"Home zone {call.zone}"))
    if other:
        groups.append(ui.tags.optgroup(*[opt(u, False) for u in other], label="Other zones"))
    return ui.tags.select(*groups, id=f"rwpick-{call.call_id}", class_="rw-select rw-unit-pick",
                          **{"data-rw-call": call.call_id, "aria-label": "Unit to dispatch"})


def list_card(label: str, title: str, rows: list, empty: str, host: dict, total: int | None = None,
              step: int | None = None, scroll_key: str | None = None):
    """A card with a count and a list of rows. With scroll_key the list scrolls (max 360 px) and
    keeps its scroll position when it is redrawn; the header and count stay outside it."""
    count = ui.span(str(len(rows) if total is None else total), class_="rw-count")
    if rows and scroll_key:
        body = ui.div(*rows, class_="rw-rows rw-scroll", **{"data-rw-key": scroll_key})
    elif rows:
        body = ui.div(*rows, class_="rw-rows")
    else:
        body = ui.div(empty, class_="rw-empty")
    return ui.div(card_head(label, title, count, step=step), body, class_="rw-card", **host)


def _day_label(iso: str) -> str:
    return pd.Timestamp(iso).strftime("%b %d")


# ---- the simulation controls (shown in the page header) ----------------------------------------

@module.ui
def sim_controls_ui():
    """Compact simulation controls for the header. Call it with the dispatcher's id
    ("dispatcher") so the dispatcher's server reads these inputs."""
    return ui.div(
        ui.input_select("sim_day", "Day", choices={sim.DEFAULT_DAY: _day_label(sim.DEFAULT_DAY)}),
        ui.input_select("sim_speed", "Speed", choices=SPEED_CHOICES, selected="60"),
        ui.input_select("sim_start", "Start at", choices=START_CHOICES, selected="0"),
        ui.input_action_button("sim_toggle", "Simulate a shift", class_="btn-primary btn-sm"),
        ui.input_action_button("sim_reset", "Reset", class_="btn-default btn-sm"),
        class_="rw-simbar")


# ---- the live board ----------------------------------------------------------------------------

def _zone_map_card():
    """The live Ithaca map: zones coloured by their worst open call; click a zone to log a call there."""
    legend = ui.div(
        ui.span(ui.span(class_="rw-dot", **{"data-tone": "green"}), "On track"),
        ui.span(ui.span(class_="rw-dot", **{"data-tone": "amber"}), "Above 80% of a target"),
        ui.span(ui.span(class_="rw-dot", **{"data-tone": "red"}), "Past a target"),
        class_="rw-legend")
    return ui.div(card_head("", "Zone map", right=ui.span(qc.CITY, class_="rw-muted")),
                  zonemap.map_div(resolve_id("live_map"), click_input=resolve_id("map_click"),
                                  height="300px"),
                  legend, class_="rw-card")


def _live_board_ui():
    log_call = ui.div(
        card_head("", "Log a call", step=1),
        ui.div(
            ui.input_select("new_zone", "Zone", choices=ZONE_CHOICES),
            ui.input_select("new_priority", "Priority", choices=PRIORITY_CHOICES),
            ui.input_select("manual_speed", "Clock speed", choices=MANUAL_SPEED_CHOICES, selected="1"),
            ui.input_action_button("new_call", "Add call", class_="btn-default"),
            class_="rw-controls rw-controls-call"),
        class_="rw-card")

    return ui.TagList(
        ui.div(
            ui.h2("Live board", class_="rw-page-title"),
            ui.div(ui.output_ui("clock_chip"),
                   ui.download_button("download_calls", "Download calls (CSV)",
                                      class_="btn-default btn-sm"),
                   class_="rw-btnrow"),
            class_="rw-page-head"),
        ui.output_ui("kpis"),
        # 2 x 2: log a call | incoming, dispatched | en route
        ui.div(log_call, ui.output_ui("incoming"), ui.output_ui("dispatched"), ui.output_ui("en_route"),
               class_="rw-two"),
        ui.div(ui.output_ui("fleet"), _zone_map_card(), class_="rw-two"),
        ui.div(ui.output_ui("resolved"), style="margin-top:16px"),
    )


@module.ui
def dispatcher_ui():
    return ui.div(
        ui.navset_pill(
            ui.nav_panel("Live board", _live_board_ui()),
            ui.nav_panel("History", history_ui("history")),
            id="tabs"),
        class_="rw-dispatcher")


@module.server
def dispatcher_server(input, output, session, active):
    """The dispatcher's board. `active` is a reactive that is True while this view is shown.

    Returns a reactive giving the clock label for the header, e.g. "LIVE 1x" or "SIM 60x".
    """
    board = sim.Board(sim.load_units())
    st = {"replay": None, "last": None, "picks": {}, "pending": None,
          "sig": None, "tsig": None, "v": 0, "tv": 0,
          "clock": sim.ManualClock(datetime.now(), time.monotonic(), 1)}
    version = reactive.Value(0)        # bumps when a call or unit changes
    timever = reactive.Value(0)        # bumps when time alone changes a zone tile colour
    sim_state = reactive.Value("stopped")      # stopped, running, paused or finished
    mode_label = reactive.Value("LIVE 1x")

    # ---- clock and state helpers ---------------------------------------------------------------

    def now() -> datetime:
        """The board clock: the replay's simulated time, else the manual clock."""
        replay = st["replay"]
        if replay is not None:
            return replay.now
        return st["clock"].now(time.monotonic())

    def bump() -> None:
        """Tell the screens something changed (only if it really did)."""
        sig = board.signature()
        if sig != st["sig"]:
            st["sig"] = sig
            st["v"] += 1
            version.set(st["v"])

    def bump_time() -> None:
        tsig = board.time_signature(now())
        if tsig != st["tsig"]:
            st["tsig"] = tsig
            st["tv"] += 1
            timever.set(st["tv"])

    def notify(message: str, kind: str = "message", duration: float = 5) -> None:
        ui.notification_show(message, type=kind, duration=duration)

    def set_label() -> None:
        replay = st["replay"]
        mode_label.set(f"LIVE {st['clock'].speed}x" if replay is None else f"SIM {replay.speed}x")

    @reactive.calc
    def history_visible():
        return bool(active()) and input.tabs() == "History"

    history_server("history", visible=history_visible, board=board, now=now)

    # ---- the one-second tick ------------------------------------------------------------------------

    @reactive.effect
    async def _tick():
        running = sim_state() == "running"
        if not (active() or running):
            return                      # nobody is watching and no replay is running
        reactive.invalidate_later(1)
        mono = time.monotonic()
        replay = st["replay"]
        if replay is not None and replay.running:
            replay.advance(mono - st["last"] if st["last"] else 0)
            board.sync_replay(replay.state())
            if replay.finished:
                sim_state.set("finished")
        st["last"] = mono
        bump()
        bump_time()
        await session.send_custom_message("rw_clock", {"now": sim.epoch(now())})

    # ---- simulate a shift --------------------------------------------------------------------------------

    @reactive.effect
    def _data_for_simulator():
        calls, _ = get_calls("demo")
        if calls is None:
            ui.update_select("sim_day", choices={"": "No data"})
            return
        days = sim.available_days(calls)
        ui.update_select("sim_day", choices={d: _day_label(d) for d in days},
                         selected=sim.pick_day(days))

    @reactive.effect
    @reactive.event(input.sim_toggle)
    def _sim_toggle():
        state = sim_state.get()
        replay = st["replay"]
        if state == "running":
            replay.pause()
            sim_state.set("paused")
        elif state == "paused":
            replay.set_speed(int(input.sim_speed()))
            replay.start()
            st["last"] = time.monotonic()
            sim_state.set("running")
        else:                                       # stopped or finished: start a fresh replay
            calls, why = get_calls("demo")
            if calls is None:
                notify(why or "Data not generated yet", "error")
                return
            days = sim.available_days(calls)
            day = input.sim_day()
            day = day if day in days else sim.pick_day(days)
            try:
                new = sim.Replay(sim.day_calls(calls, day), speed=int(input.sim_speed()),
                                 start_hour=int(input.sim_start()))
            except ValueError:
                notify(f"There are no calls on {day} after that start time.", "error")
                return
            board.reset_sim()
            board.set_mode("sim")
            st["replay"] = new
            st["picks"].clear()
            new.start()
            board.sync_replay(new.state())
            st["last"] = time.monotonic()
            sim_state.set("running")
        set_label()
        bump()
        bump_time()

    @reactive.effect
    @reactive.event(input.sim_reset)
    def _sim_reset():
        """Everything the dispatcher sees goes back to zero and the clock to wall time."""
        st["replay"] = None
        st["pending"] = None
        st["picks"].clear()
        board.reset_all()
        st["clock"].reset(datetime.now(), time.monotonic())     # keeps the chosen manual speed
        sim_state.set("stopped")
        set_label()
        bump()
        bump_time()
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.sim_speed, ignore_init=True)
    def _sim_speed():
        replay = st["replay"]
        if replay is not None:
            replay.set_speed(int(input.sim_speed()))
            set_label()

    @reactive.effect
    @reactive.event(input.manual_speed, ignore_init=True)
    def _manual_speed():
        # continues from the current board time, so the clock never jumps
        st["clock"].set_speed(int(input.manual_speed()), time.monotonic())
        set_label()
        bump_time()

    @reactive.effect
    def _toggle_label():
        label = {"stopped": "Simulate a shift", "running": "Pause", "paused": "Resume",
                 "finished": "Run again"}[sim_state()]
        ui.update_action_button("sim_toggle", label=label)

    # ---- manual calls and buttons --------------------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.new_call)
    def _new_call():
        try:
            call = board.add_call(input.new_zone(), int(input.new_priority()), now())
        except sim.BoardError as exc:
            notify(str(exc), "error")
            return
        notify(f"Call {call.call_id} logged for zone {call.zone}.")
        bump()
        bump_time()

    @reactive.effect
    @reactive.event(input.pick_change)
    def _remember_pick():
        p = input.pick_change()
        if p and p.get("call") and p.get("unit"):
            st["picks"][p["call"]] = p["unit"]

    def reason_modal(call, late):
        stage = {"processing": "Dispatch", "turnout": "Turnout", "travel": "Travel"}[late["stage"]]
        measure = "total response" if late["measure"] == "response" else stage.lower()
        return ui.modal(
            ui.p(f"The {measure} took {sim.fmt_clock(late['elapsed'])} "
                 f"(target {sim.fmt_clock(late['target'])}). Choose a reason to continue.",
                 class_="rw-small"),
            ui.input_select("reason", "Delay reason",
                            choices={"": "Choose a reason", **qc.REASON_CODES}, width="100%"),
            title=f"Why was this late? {call.call_id}",
            footer=ui.TagList(ui.modal_button("Cancel"),
                              ui.input_action_button("reason_ok", "Save reason and continue",
                                                     class_="btn-primary")),
            easy_close=False)

    @reactive.effect
    @reactive.event(input.row_action)
    def _row_action():
        p = input.row_action()
        action, call_id, unit_id = p.get("action"), p.get("call"), p.get("unit")
        t = now()
        try:
            if action == "oos":
                flagged = board.set_out_of_service(unit_id, t)
                if flagged:
                    notify(f"{unit_id} is out of service. Flagged {', '.join(flagged)}: the reason "
                           "ambulance breakdown is recorded when it arrives.", "warning", 8)
                else:
                    notify(f"{unit_id} is out of service.", "warning")
            elif action == "back":
                board.back_in_service(unit_id)
            elif action == "clear":
                call = board.check(call_id, "clear")
                st["pending"] = {"call": call_id, "action": "clear"}
                ui.modal_show(ui.modal(
                    ui.p(f"Clear call {call.call_id}? This closes the call and frees unit "
                         f"{call.unit_id}.", class_="rw-small"),
                    title=f"Clear call {call.call_id}?",
                    footer=ui.TagList(ui.modal_button("Keep open"),
                                      ui.input_action_button("clear_ok", "Clear call",
                                                             class_="btn-primary")),
                    easy_close=False))
            elif action in ("dispatch", "en_route", "on_scene"):
                pick = p.get("pick") or st["picks"].get(call_id)
                call = board.check(call_id, action, pick if action == "dispatch" else None)
                late = board.needs_reason(call_id, action, t)
                if late:
                    # the button press time is kept; the reason is added in the dialog
                    st["pending"] = {"call": call_id, "action": action, "time": t, "unit": pick}
                    ui.modal_show(reason_modal(call, late))
                else:
                    board.apply(call_id, action, t, unit_id=pick)
            else:
                return
        except sim.BoardError as exc:
            notify(str(exc), "error")
        bump()
        bump_time()

    @reactive.effect
    @reactive.event(input.reason_ok)
    def _reason_ok():
        pending = st["pending"]
        reason = input.reason()
        if not pending or pending["action"] == "clear":
            ui.modal_remove()
            return
        if not reason:
            notify("Choose a reason first.", "error")
            return
        try:
            board.apply(pending["call"], pending["action"], pending["time"],
                        reason=reason, unit_id=pending.get("unit"))
        except sim.BoardError as exc:
            notify(str(exc), "error")
        st["pending"] = None
        ui.modal_remove()
        bump()
        bump_time()

    @reactive.effect
    @reactive.event(input.clear_ok)
    def _clear_ok():
        pending = st["pending"]
        ui.modal_remove()
        if not pending or pending["action"] != "clear":
            return
        st["pending"] = None
        try:
            board.apply(pending["call"], "clear", now())
        except sim.BoardError as exc:
            notify(str(exc), "error")
        bump()
        bump_time()

    # ---- what the screen shows -----------------------------------------------------------------------------

    def host():
        return {"data-rw-input": session.ns("row_action"),
                "data-rw-pick-input": session.ns("pick_change")}

    @render.ui
    def clock_chip():
        sim_state()
        mode = mode_label()
        tone = "green" if mode == "LIVE 1x" else "amber"
        t = now()
        return ui.div(
            chip(ui.span(t.strftime("%Y-%m-%d"), class_="rw-nowdate"), None),
            chip(ui.span(t.strftime("%H:%M:%S"), class_="rw-nowtime"), tone),
            class_="rw-btnrow")

    @render.ui
    def kpis():
        version()
        c = board.counts()
        items = [("Waiting", c["received"], "clock"), ("Dispatched", c["dispatched"], "send"),
                 ("En route", c["en_route"], "route"), ("On scene", c["on_scene"], "pin"),
                 ("Units available", c["units_available"], "truck")]
        return ui.div(*[ui.div(ui.div(icon(ic), class_="rw-kpi-icon"),
                               ui.div(str(n), class_="rw-kpi-num"),
                               ui.div(label, class_="rw-kpi-label"), class_="rw-kpi")
                        for label, n, ic in items], class_="rw-kpis")

    def calls_with(status):
        return sorted((c for c in board.calls() if c.status == status),
                      key=lambda c: getattr(c, {"received": "call_received"}.get(status, status)))

    @render.ui
    def incoming():
        version()
        t = now()
        rows = []
        for c in calls_with("received"):
            tg = c.targets
            if c.source == "manual":
                free = board.available_units(c.zone)
                ids = {u["unit_id"] for u in free}
                chosen = st["picks"].get(c.call_id)
                chosen = chosen if chosen in ids else (free[0]["unit_id"] if free else None)
                if free:
                    actions = [unit_picker(c, free, chosen),
                               action_button("Dispatch", "dispatch", c.call_id, f"rwpick-{c.call_id}")]
                else:
                    actions = [tag("No unit free", "amber")]
            else:
                actions = [tag("Replay")]
            rows.append(row(c, f"Waiting for dispatch, target {sim.fmt_clock(tg['processing'])}",
                            actions=actions, sev=c.severity(t),
                            clocks=[clock_box("Waiting", c.call_received, tg["processing"], t)]))
        return list_card("", "Incoming calls", rows, "No calls waiting.", host(), step=2)

    @render.ui
    def dispatched():
        version()
        t = now()
        rows = []
        for c in calls_with("dispatched"):
            tg = c.targets
            actions = [action_button("En route", "en_route", c.call_id)] if c.source == "manual" \
                else [tag("Replay")]
            rows.append(row(c, f"Needs to roll: unit {c.unit_id}, target {sim.fmt_clock(tg['turnout'])}",
                            actions=actions, sev=c.severity(t),
                            clocks=[clock_box("Turnout", c.dispatched, tg["turnout"], t)],
                            extra_tags=[tag("Breakdown", "red")] if c.breakdown else ()))
        return list_card("", "Dispatched", rows, "No calls waiting to roll.", host(), step=3)

    @render.ui
    def en_route():
        version()
        t = now()
        rows = []
        for c in calls_with("en_route"):
            tg = c.targets
            actions = [action_button("On scene", "on_scene", c.call_id)] if c.source == "manual" \
                else [tag("Replay")]
            home = "" if c.unit_home_zone in ("", c.zone) else f" (from zone {c.unit_home_zone})"
            rows.append(row(c, f"Unit {c.unit_id}{home}, travel target {sim.fmt_clock(tg['travel'])}",
                            actions=actions, sev=c.severity(t),
                            clocks=[clock_box("Travel", c.en_route, tg["travel"], t),
                                    clock_box("Total", c.dispatched, tg["response"], t)],
                            extra_tags=[tag("Breakdown", "red")] if c.breakdown else ()))
        return list_card("", "En route", rows, "No units on the road.", host(), step=4)

    @render.ui
    def resolved():
        """On scene means resolved: every call that reached the scene, with its final response.
        A Clear button stays on rows whose ambulance is still there (it frees the ambulance)."""
        version()
        t = now()
        done = sorted((c for c in board.calls() if c.status in ("on_scene", "cleared")),
                      key=lambda c: c.on_scene or c.cleared, reverse=True)
        rows = []
        for c in done[:RESOLVED_SHOWN]:
            tg = c.targets
            resp = c.elapsed("response", t)
            sev = sim.severity(resp, tg["response"]) if resp is not None else "green"
            reason = qc.REASON_CODES.get(c.delay_reason, "")
            if c.status == "cleared":
                sub = f"Unit {c.unit_id} · cleared {sim.fmt_time(c.cleared)}"
                actions = [tag("Cleared")]
            else:
                sub = f"Unit {c.unit_id} · on scene {sim.fmt_time(c.on_scene)}"
                actions = [action_button("Clear", "clear", c.call_id)] if c.source == "manual" \
                    else [tag("At the scene"), tag("Replay")]
            if reason:
                sub += f" · {reason}"
            clocks = [final_box("Response", resp, tg["response"])] if resp is not None else []
            rows.append(row(c, sub, live=False, sev=sev, actions=actions, clocks=clocks))
        card = list_card("", "Resolved", rows, "No calls on scene yet.", host(),
                         total=len(done), step=5, scroll_key="resolved")
        if len(done) > RESOLVED_SHOWN:
            card.children.append(ui.div(f"Latest {RESOLVED_SHOWN} of {len(done)} shown.", class_="rw-more"))
        return card

    @reactive.effect
    async def _paint_live_map():
        version()
        timever()
        words = {"green": "On track", "amber": "Watch", "red": "Past target"}
        zones = {}
        for tl in board.zone_tiles(now()):
            n, free = tl["open"], tl["available"]
            zones[tl["zone"]] = {"sev": tl["severity"], "status": words[tl["severity"]],
                                 "lines": [f"{n} open call{'s' if n != 1 else ''}",
                                           f"{free} unit{'s' if free != 1 else ''} available"]}
        await zonemap.update(session, session.ns("live_map"), zones)

    @reactive.effect
    @reactive.event(input.map_click)
    def _map_pick():
        """Clicking a zone on the map picks it in Log a call."""
        ui.update_select("new_zone", selected=input.map_click())

    @render.ui
    def fleet():
        """Ambulances in status columns: Available, Responding (dispatched + en route),
        On scene and Out of service. Each unit shows its home zone and its one action."""
        version()
        units = board.fleet()
        columns = [("available", "Available", "green"), ("responding", "Responding", "amber"),
                   ("on_scene", "On scene", "amber"), ("out_of_service", "Out of service", "red")]
        column_of = {"available": "available", "dispatched": "responding", "en_route": "responding",
                     "on_scene": "on_scene", "out_of_service": "out_of_service"}
        groups = {key: [] for key, _, _ in columns}
        for u in units:
            groups[column_of[u["state"]]].append(u)

        def chip_for(u):
            state = u["state"]
            if state == "out_of_service":
                button = ui.tags.button("Back in service", type="button", class_="rw-btn",
                                        **{"data-rw-action": "back", "data-rw-unit": u["unit_id"]})
            else:
                button = ui.tags.button("Out of service", type="button", class_="rw-btn rw-btn-ghost",
                                        **{"data-rw-action": "oos", "data-rw-unit": u["unit_id"]})
            which = ui.div(sim.UNIT_LABEL[state], class_="rw-u-state") \
                if state in ("dispatched", "en_route") else None
            title = f"{u['unit_id']}, home zone {u['home_zone']}" + (f", call {u['call_id']}" if u["call_id"] else "")
            return ui.div(
                ui.div(ui.span(u["unit_id"], class_="rw-u-id"),
                       ui.span(f"Zone {u['home_zone']}", class_="rw-u-zone"), class_="rw-u-top"),
                which, button, class_="rw-u", title=title)

        cols, weights = [], []
        for key, label, tone in columns:
            members = groups[key]
            body = ui.div(*[chip_for(u) for u in members], class_="rw-ucol-body") if members \
                else ui.div("None", class_="rw-ucol-none")
            cols.append(ui.div(
                ui.div(ui.span(class_="rw-dot", **{"data-tone": tone}), ui.span(label, class_="rw-ucol-label"),
                       ui.tags.b(str(len(members))), class_="rw-ucol-head"),
                body, class_="rw-ucol"))
            weights.append(max(1, -(-len(members) // 6)))     # a long column gets double width
        free = len(groups["available"])
        return ui.div(
            card_head("", "Ambulances", ui.span(f"{free} of {len(units)} free", class_="rw-count")),
            ui.div(*cols, class_="rw-ucols",
                   style="grid-template-columns:" + " ".join(f"minmax(0,{w}fr)" for w in weights)),
            class_="rw-card", **host())

    @render.download_button(
        filename=lambda: f"ergent_calls_{datetime.now():%Y%m%d_%H%M%S}.csv",
        media_type="text/csv")
    def download_calls():
        yield board.to_frame().to_csv(index=False)

    return mode_label


# ---- history tab: the current shift and the one before ------------------------------------------------

def _zone_words(zones: list[str]) -> str:
    """['C'] -> 'Zone C'; ['C', 'D'] -> 'Zones C and D'; ['A', 'C', 'D'] -> 'Zones A, C and D'."""
    if len(zones) == 1:
        return f"Zone {zones[0]}"
    return "Zones " + ", ".join(zones[:-1]) + f" and {zones[-1]}"


def chart_note_text(sub: pd.DataFrame) -> str:
    """One line under a zone chart: qc's message when there is nothing to chart, else the flags."""
    message = sub.attrs.get("message") or ""
    if message:
        return message[0].upper() + message[1:] + ("" if message.endswith(".") else ".")
    above = list(sub.loc[sub["flag"] == "above", "zone"])
    below = list(sub.loc[sub["flag"] == "below", "zone"])
    parts = [f"{_zone_words(above)} {'is' if len(above) == 1 else 'are'} slower than the city as a whole."
             if above else "No zone is slower than the city as a whole."]
    if below:
        parts.append(f"{_zone_words(below)} {'is' if len(below) == 1 else 'are'} faster than the city "
                     "as a whole (check the data).")
    return " ".join(parts)


@module.ui
def history_ui():
    chart_card = ui.div(
        card_head("", "Response time by zone",
                  ui.div(ui.input_select("priority", "Priority", choices=HISTORY_PRIORITY_CHOICES,
                                         selected="1"),
                         class_="rw-compact")),
        ui.div(ui.output_ui("chart"), class_="rw-svg"),
        ui.output_ui("chart_note"),
        class_="rw-card")

    return ui.div(
        ui.div(ui.h2("History", class_="rw-page-title"), class_="rw-page-head"),
        ui.output_ui("shift_line"),
        ui.output_ui("shift_kpis"),
        ui.div(chart_card, ui.output_ui("tips"), class_="rw-hist-grid"))


@module.server
def history_server(input, output, session, visible, board, now):
    """The shift review. Data: the demo file the simulation replays, plus the calls logged by
    hand, cut to the current and previous shift at the board clock by qc.shift_calls."""
    win_val = reactive.Value(None)      # {"window", "label", "missing"}; set only when it changes
    tips_val = reactive.Value(None)
    st = {"sig": None, "tips": None}

    @reactive.effect
    def _refresh():
        if not visible():
            return
        reactive.invalidate_later(HISTORY_REFRESH_S)
        t = now()
        demo, why = get_calls("demo", stages=True)
        manual = qc.stage_times(board.calls_frame(t, manual_only=True))
        stages = manual if demo is None else pd.concat([demo, manual], ignore_index=True)
        window = qc.shift_calls(stages, t)
        label = qc.shift_window(t)["label"]
        tips = qc.dispatcher_tips(window, board.calls_frame(t), board.fleet(), t)
        sig = (label, len(window), tuple(window["call_id"]), why)
        if sig != st["sig"]:
            st["sig"] = sig
            win_val.set({"window": window, "label": label, "missing": why if demo is None else ""})
        if tips != st["tips"]:
            st["tips"] = tips
            tips_val.set(tips)

    @reactive.calc
    def chosen():
        """(priority, qc.zone_subgroup_chart for it, the shift window) for the selected priority."""
        w = req(win_val())
        p = int(input.priority())
        return p, qc.zone_subgroup_chart(w["window"], p), w["window"]

    @render.ui
    def shift_line():
        w = win_val()
        if w is None:
            return ui.div("Loading the shift data\u2026", class_="rw-muted rw-small")
        extra = [ui.div(w["missing"] + ": only the calls you log by hand are shown.",
                        class_="rw-muted rw-small", style="margin-top:4px")] if w["missing"] else []
        return ui.div(ui.div(w["label"], class_="rw-shiftline"), *extra, style="margin-bottom:16px")

    @render.ui
    def shift_kpis():
        w = win_val()
        if w is None:
            return None
        window = w["window"]
        n = len(window)
        mean = sd = on_time = "\u2013"
        if n:
            s = qc.summary(window["response_min"], qc.TARGETS["response"][1] / 60.0)
            mean = f"{s['mean']:.1f}"
            sd = "\u2013" if s["sd"] is None else f"{s['sd']:.1f}"
            on_time = f"{100 * (1 - window['late'].mean()):.0f}%"
        items = [("Calls", str(n)), ("Mean (min)", mean), ("Standard deviation (min)", sd),
                 ("On time", on_time)]
        return ui.div(
            ui.div(*[ui.div(ui.div(value, class_="rw-kpi-num"), ui.div(label, class_="rw-kpi-label"),
                            class_="rw-kpi") for label, value in items],
                   class_="rw-kpis rw-kpis-4"),
            ui.p("All priorities. On time means within each call's own target.",
                 class_="rw-muted rw-small", style="margin:8px 0 0"))

    @render.ui
    def chart():
        """The zone chart as inline SVG; hovering a red point shows why that zone is slow."""
        p, sub, window = chosen()
        reasons = {z: qc.zone_delay_reason(window, z, p)
                   for z in sub.loc[sub["flag"] == "above", "zone"]}
        return ui.HTML(charts.zone_box_svg(sub, p, qc.TARGETS["response"][p] / 60.0, reasons))

    @render.ui
    def chart_note():
        return ui.p(chart_note_text(chosen()[1]), class_="rw-muted rw-small", style="margin:8px 0 0")

    @render.ui
    def tips():
        """The dispatcher's suggestions, condensed: tags and short text, evidence in a small line."""
        items = tips_val()
        if items is None:
            return None
        rows = []
        for tip in items:
            tone = "red" if tip["rule"] == "T1" else "amber"
            where = "All zones" if tip["zone"] == "All" else f"Zone {tip['zone']}"
            rows.append(ui.div(
                ui.span(class_="rw-dot", **{"data-tone": tone}),
                ui.div(ui.div(tag(TIP_NAMES.get(tip["rule"], tip["rule"])), tag(where),
                              ui.span(tip["text"], class_="rw-tip-text"), class_="rw-row-title"),
                       ui.div(tip["evidence"], class_="rw-row-sub"), class_="rw-row-main"),
                class_="rw-row rw-row-wrap"))
        body = ui.div(*rows, class_="rw-rows") if rows else \
            ui.div("No suggestions right now.", class_="rw-empty")
        return ui.div(
            card_head("", "Suggested actions", ui.span(str(len(rows)), class_="rw-count")),
            body,
            ui.p("For the dispatcher's judgment; the tool decides nothing on its own.",
                 class_="rw-muted", style="margin:10px 0 0;font-size:11.5px"),
            class_="rw-card rw-tips")
