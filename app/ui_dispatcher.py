"""Dispatcher screens: the live board and the history tab.

The call model, the fleet, the alerts and the shift replay live in simulator.py
(pure Python, unit-tested); every percentile and summary comes from qc.py. This
file only draws them and passes the button presses back.

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
from shiny import module, reactive, render, ui  # noqa: E402

import qc  # noqa: E402
import simulator as sim  # noqa: E402

#: The share of calls that should be on time (NFPA 1710), used only to colour a dot.
ON_TIME_GOAL = 90.0

#: How many resolved calls the live board lists.
RESOLVED_SHOWN = 10

SPEED_CHOICES = {str(s): f"{s}x" for s in sim.SPEEDS}
START_CHOICES = {str(h): label for h, label in sim.START_HOURS.items()}
ZONE_CHOICES = {z: z for z in qc.ZONES}
PRIORITY_CHOICES = {"1": "1 (life-threatening)", "2": "2", "3": "3"}

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


def card_head(label: str, title: str, right=None):
    """Eyebrow label above a bold title, with an optional element on the right."""
    return ui.div(ui.div(eyebrow(label), ui.div(title, class_="rw-title")), right,
                  class_="rw-card-head")


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


def list_card(label: str, title: str, rows: list, empty: str, host: dict, total: int | None = None):
    count = ui.span(str(len(rows) if total is None else total), class_="rw-count")
    body = ui.div(*rows, class_="rw-rows") if rows else ui.div(empty, class_="rw-empty")
    return ui.div(card_head(label, title, count), body, class_="rw-card", **host)


# ---- the live board ----------------------------------------------------------------------------

def _live_board_ui():
    sim_card = ui.div(
        card_head("Simulation", "Simulate a shift"),
        ui.p("Replay one day of the demo data on a fast clock. Calls move through the board "
             "at the times in the file.", class_="rw-muted rw-small"),
        ui.div(
            ui.input_select("sim_day", "Day", choices={sim.DEFAULT_DAY: sim.DEFAULT_DAY}),
            ui.input_select("sim_speed", "Speed", choices=SPEED_CHOICES, selected="60"),
            ui.input_select("sim_start", "Start at", choices=START_CHOICES, selected="0"),
            class_="rw-controls"),
        ui.div(
            ui.input_action_button("sim_toggle", "Simulate a shift", class_="btn-primary"),
            ui.input_action_button("sim_reset", "Reset", class_="btn-default"),
            class_="rw-btnrow", style="margin-top:14px"),
        ui.output_ui("sim_note"),
        class_="rw-card")

    new_call = ui.div(
        card_head("New call", "Log a call"),
        ui.p("The received time is stamped from the clock. Then work the call with the buttons "
             "below.", class_="rw-muted rw-small"),
        ui.div(
            ui.input_select("new_zone", "Zone", choices=ZONE_CHOICES),
            ui.input_select("new_priority", "Priority", choices=PRIORITY_CHOICES),
            ui.input_action_button("new_call", "Add call", class_="btn-default"),
            class_="rw-controls"),
        class_="rw-card")

    return ui.TagList(
        ui.div(
            ui.div(eyebrow("Live board"), ui.h2("Calls in progress", class_="rw-page-title")),
            ui.div(ui.output_ui("clock_chip"),
                   ui.download_button("download_calls", "Download calls (CSV)",
                                      class_="btn-default btn-sm"),
                   class_="rw-btnrow"),
            class_="rw-page-head"),
        ui.output_ui("kpis"),
        ui.div(sim_card, new_call, class_="rw-two"),
        ui.div(
            ui.div(ui.output_ui("incoming"), ui.output_ui("dispatched"), ui.output_ui("en_route"),
                   ui.output_ui("on_scene"), ui.output_ui("resolved"), class_="rw-stack"),
            ui.div(ui.output_ui("zone_map"), ui.output_ui("alerts"), ui.output_ui("fleet"),
                   class_="rw-stack"),
            class_="rw-grid"),
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

    Returns a reactive giving the clock mode label ("LIVE" or "SIM 60x") for the header.
    """
    board = sim.Board(sim.load_units())
    st = {"replay": None, "last": None, "picks": {}, "pending": None,
          "sig": None, "tsig": None, "v": 0, "tv": 0}
    version = reactive.Value(0)        # bumps when a call or unit changes
    timever = reactive.Value(0)        # bumps when time alone changes an alert or a tile colour
    sim_state = reactive.Value("stopped")      # stopped, running, paused or finished
    mode_label = reactive.Value("LIVE")

    history_server("history")

    # ---- clock and state helpers ---------------------------------------------------------------

    def now() -> datetime:
        replay = st["replay"]
        if replay is not None:
            return replay.now
        return datetime.now().replace(microsecond=0)

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
        mode_label.set("LIVE" if replay is None else f"SIM {replay.speed}x")

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
            ui.update_select("sim_day", choices={"": "Data not generated yet"})
            return
        days = sim.available_days(calls)
        ui.update_select("sim_day", choices=days, selected=sim.pick_day(days))

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
                notify(f"There are no calls on {day}.", "error")
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
        st["replay"] = None
        st["picks"].clear()
        board.reset_sim()
        sim_state.set("stopped")
        set_label()
        bump()
        bump_time()

    @reactive.effect
    @reactive.event(input.sim_speed, ignore_init=True)
    def _sim_speed():
        replay = st["replay"]
        if replay is not None:
            replay.set_speed(int(input.sim_speed()))
            set_label()

    @reactive.effect
    def _toggle_label():
        label = {"stopped": "Simulate a shift", "running": "Pause", "paused": "Resume",
                 "finished": "Replay this day again"}[sim_state()]
        ui.update_action_button("sim_toggle", label=label)

    @render.ui
    def sim_note():
        state = sim_state()
        calls, why = get_calls("demo")
        if calls is None:
            return ui.p(why or "Data not generated yet", class_="rw-muted rw-small",
                        style="margin:12px 0 0")
        replay = st["replay"]
        if state == "stopped" or replay is None:
            text = ("Pick a day, a speed and a start time, then start. Replayed calls are read-only; "
                    "calls you add use the same clock.")
        else:
            text = (f"Replaying {replay.day:%Y-%m-%d} at {replay.speed}x"
                    f"{' (finished)' if state == 'finished' else ''}. Speed changes apply now; "
                    "reset to change the day or the start time.")
        return ui.p(text, class_="rw-muted rw-small", style="margin:12px 0 0")

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
            ui.p(f"Call {call.call_id}: the {measure} took {sim.fmt_clock(late['elapsed'])}, "
                 f"past the {sim.fmt_clock(late['target'])} target. Choose a reason to continue. "
                 "The time you pressed the button is kept.", class_="rw-small"),
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
        tone = "green" if mode == "LIVE" else "amber"
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
        return list_card("Queue", "Incoming calls", rows, "No calls waiting.", host())

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
        return list_card("Needs to roll", "Dispatched", rows, "No calls waiting to roll.", host())

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
        return list_card("Travelling", "En route", rows, "No units on the road.", host())

    @render.ui
    def on_scene():
        version()
        t = now()
        rows = []
        for c in calls_with("on_scene"):
            tg = c.targets
            resp = c.elapsed("response", t)
            sev = sim.severity(resp, tg["response"])
            actions = [action_button("Clear", "clear", c.call_id)] if c.source == "manual" \
                else [tag("Replay")]
            status = "within target" if sev != "red" else "past target"
            rows.append(row(c, f"Unit {c.unit_id}, response {status} ({sim.fmt_clock(tg['response'])})",
                            actions=actions, live=False, sev=sev,
                            clocks=[final_box("Response", resp, tg["response"])]))
        return list_card("At the scene", "On scene", rows, "No units on scene.", host())

    @render.ui
    def resolved():
        version()
        t = now()
        done = sorted((c for c in board.calls() if c.status == "cleared"),
                      key=lambda c: c.cleared, reverse=True)
        rows = []
        for c in done[:RESOLVED_SHOWN]:
            tg = c.targets
            resp = c.elapsed("response", t)
            late = resp is not None and resp > tg["response"]
            reason = qc.REASON_CODES.get(c.delay_reason, "")
            sub = f"Unit {c.unit_id} · cleared {sim.fmt_time(c.cleared)}"
            if reason:
                sub += f" · {reason}"
            clocks = [final_box("Response", resp, tg["response"])] if resp is not None else []
            rows.append(row(c, sub, live=False, sev="red" if late else "green", clocks=clocks))
        card = list_card("This session", "Resolved", rows, "Nothing resolved yet.", host(),
                         total=len(done))
        if len(done) > RESOLVED_SHOWN:
            card.children.append(ui.div(f"Showing the latest {RESOLVED_SHOWN} of {len(done)}. "
                                        "Download the calls to see all of them.", class_="rw-more"))
        return card

    @render.ui
    def zone_map():
        version()
        timever()
        tiles = board.zone_tiles(now())
        words = {"green": "On track", "amber": "Watch", "red": "Past target"}
        cells = []
        for tl in tiles:
            n, free = tl["open"], tl["available"]
            cells.append(ui.div(
                ui.div(ui.span(tl["zone"], class_="rw-tile-letter"), ui.span("Zone", class_="rw-tile-cap"),
                       class_="rw-tile-top"),
                ui.div(ui.div(f"{n} open call{'s' if n != 1 else ''}", class_="rw-tile-line"),
                       ui.div(f"{free} unit{'s' if free != 1 else ''} available", class_="rw-tile-line"),
                       ui.div(words[tl["severity"]], class_="rw-tile-status")),
                class_="rw-tile", **{"data-sev": tl["severity"]}))
        legend = ui.div(
            ui.span(ui.span(class_="rw-dot", **{"data-tone": "green"}), "On track"),
            ui.span(ui.span(class_="rw-dot", **{"data-tone": "amber"}), "Above 80% of a target"),
            ui.span(ui.span(class_="rw-dot", **{"data-tone": "red"}), "Past a target"),
            class_="rw-legend")
        return ui.div(card_head("Zones", "Live zone map"), ui.div(*cells, class_="rw-map"), legend,
                      class_="rw-card")

    @render.ui
    def alerts():
        version()
        timever()
        items = board.alerts(now())
        rows = []
        for a in items:
            tone = a["severity"] if a["active"] else "grey"
            rows.append(ui.div(
                ui.span(class_="rw-dot", **{"data-tone": tone}),
                ui.div(ui.div(a["title"], class_="rw-row-title"), ui.div(a["sub"], class_="rw-row-sub"),
                       class_="rw-row-main"),
                ui.div(ui.span(sim.fmt_time(a["raised_at"]), class_="rw-final",
                               style="font-size:14px;font-weight:600"),
                       ui.span("Raised" if a["active"] else "Resolved", class_="rw-cap"),
                       class_="rw-clockbox"),
                class_="rw-row"))
        body = ui.div(*rows, class_="rw-rows", style="max-height:340px;overflow-y:auto") if rows \
            else ui.div("No alerts. Everything is inside its target.", class_="rw-empty")
        active_n = sum(1 for a in items if a["active"])
        return ui.div(card_head("Live alerts", "Newest first",
                                ui.span(f"{active_n} active", class_="rw-count")), body, class_="rw-card")

    @render.ui
    def fleet():
        version()
        units = board.fleet()
        rows = []
        for u in units:
            state = u["state"]
            tone = {"available": "green", "out_of_service": "red"}.get(state, "amber")
            sub = f"Zone {u['home_zone']} · {sim.UNIT_LABEL[state]}"
            if u["call_id"]:
                sub += f" · {u['call_id']}"
            if state == "out_of_service":
                button = ui.tags.button("Back in service", type="button", class_="rw-btn",
                                        **{"data-rw-action": "back", "data-rw-unit": u["unit_id"]})
            else:
                button = ui.tags.button("Out of service", type="button", class_="rw-btn rw-btn-ghost",
                                        **{"data-rw-action": "oos", "data-rw-unit": u["unit_id"]})
            rows.append(ui.div(
                ui.span(class_="rw-dot", **{"data-tone": tone}),
                ui.div(ui.div(u["unit_id"], class_="rw-row-title"), ui.div(sub, class_="rw-row-sub"),
                       class_="rw-row-main"),
                button, class_="rw-unit"))
        free = sum(1 for u in units if u["state"] == "available")
        return ui.div(card_head("Fleet", "Ambulances", ui.span(f"{free} of {len(units)} free",
                                                                  class_="rw-count")),
                      ui.div(*rows, class_="rw-fleet"), class_="rw-card", **host())

    @render.download_button(
        filename=lambda: f"response_watch_calls_{datetime.now():%Y%m%d_%H%M%S}.csv",
        media_type="text/csv")
    def download_calls():
        yield board.to_frame().to_csv(index=False)

    return mode_label


# ---- history tab -----------------------------------------------------------------------------------

@module.ui
def history_ui():
    controls = ui.div(
        ui.div(
            ui.input_select("dataset", "Dataset",
                            choices={"demo": "Demo (planted problems)", "baseline": "Baseline (stable)"}),
            ui.input_select("period", "Period", choices={"7": "Last 7 days", "30": "Last 30 days"}),
            ui.input_select("priority", "Priority", choices=PRIORITY_CHOICES),
            class_="rw-controls"),
        class_="rw-card")
    return ui.div(
        ui.div(ui.div(eyebrow("History"), ui.h2("How zones performed", class_="rw-page-title")),
               class_="rw-page-head"),
        controls,
        ui.div(ui.output_ui("history_body"), style="margin-top:16px"))


def _fmt1(v) -> str:
    return "–" if v is None or pd.isna(v) else f"{v:.1f}"


def _fmt0(v) -> str:
    return "–" if v is None or pd.isna(v) else f"{v:.0f}"


@module.server
def history_server(input, output, session):
    @render.ui
    def history_body():
        dataset, days, pri = input.dataset(), int(input.period()), int(input.priority())
        stages, why = get_calls(dataset, stages=True)
        if stages is None:
            return placeholder_card("History", "No data to show", why or "Data not generated yet")

        window = qc.last_days(stages, days)
        if window["date"].notna().sum() == 0:
            return placeholder_card("History", "No data to show", "That file has no valid calls.")
        first, last = window["date"].min(), window["date"].max()
        target_min = qc.stage_targets(pri)["response"] / 60.0

        zones = qc.zone_summary(window, pri)
        trs = []
        for r in zones.itertuples():
            pct = r.pct_on_time
            tone = "grey" if r.n == 0 or pd.isna(pct) else ("green" if pct >= ON_TIME_GOAL else "red")
            label = "All zones" if r.zone == "All" else f"Zone {r.zone}"
            trs.append(ui.tags.tr(
                ui.tags.td(label),
                ui.tags.td(str(int(r.n))),
                ui.tags.td(_fmt1(r.mean)), ui.tags.td(_fmt1(r.median)),
                ui.tags.td(_fmt1(r.p90)), ui.tags.td(_fmt1(r.p95)),
                ui.tags.td(ui.span(class_="rw-dot", **{"data-tone": tone}), f"{_fmt0(pct)}%"
                           if not pd.isna(pct) else "–"),
                class_="rw-total" if r.zone == "All" else None))
        head = ui.tags.tr(*[ui.tags.th(h) for h in (
            "Zone", "Calls", "Average (min)", "Median (min)", "90th percentile (min)",
            "95th percentile (min)", "On time")])
        summary_card = ui.div(
            card_head("Priority " + str(pri), "Response time by zone",
                      ui.span(f"{first:%b %d} to {last:%b %d, %Y}", class_="rw-count")),
            ui.p(f"Response is dispatch to on scene. On time means within {target_min:g} minutes. "
                 f"Goal: at least {ON_TIME_GOAL:.0f}% on time. The average is shown for comparison "
                 "only; the median and the 90th and 95th percentiles show the slow tail.",
                 class_="rw-muted rw-small"),
            ui.div(ui.tags.table(ui.tags.thead(head), ui.tags.tbody(*trs), class_="rw-table"),
                   class_="rw-table-wrap"),
            class_="rw-card")

        done = window[window["valid"] & (window["priority"] == pri) & window["cleared"].notna()]
        done = done.sort_values("cleared", ascending=False).head(20)
        rows = []
        for r in done.itertuples():
            late = bool(r.late)
            reason = qc.REASON_CODES.get(r.delay_reason, "")
            sub = f"{r.call_received:%Y-%m-%d %H:%M} · unit {r.unit_id}" + (f" · {reason}" if reason else "")
            rows.append(ui.div(
                ui.span(class_="rw-dot", **{"data-tone": "red" if late else "green"}),
                ui.div(ui.div(r.call_id, tag(f"Zone {r.zone}"), tag("Late" if late else "On time",
                                                                    "red" if late else None),
                              class_="rw-row-title"),
                       ui.div(sub, class_="rw-row-sub"), class_="rw-row-main"),
                ui.div(ui.span(f"{r.response_min:.1f}", class_="rw-final",
                               **{"data-sev": "red" if late else "green"}),
                       ui.span("minutes", class_="rw-cap"), class_="rw-clockbox"),
                class_="rw-row"))
        recent_card = ui.div(
            card_head("Resolved calls", "20 most recent",
                      ui.span(str(len(rows)), class_="rw-count")),
            ui.div(*rows, class_="rw-rows") if rows else ui.div("No resolved calls in this period.",
                                                               class_="rw-empty"),
            class_="rw-card", style="margin-top:16px")
        return ui.TagList(summary_card, recent_card)
