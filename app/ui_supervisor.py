"""Supervisor screens: Overview, Charts and Actions.

Overview answers "is everything okay?", Charts answers "what is happening, and
why?", and Actions answers "how do we fix it, and did it work?" (the Six Sigma
Improve and Control steps). A settings card above the tabs picks the dataset,
priority, as-of date, period, targets and baseline; every tab reads them.

Each tab is one module pair (`<name>_ui()` and `<name>_server(ctx)`) listed in
TABS. Every statistic comes from qc.py and every chart from charts.py; this
file only arranges and formats them.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from shiny import module, reactive, render, ui  # noqa: E402

import charts  # noqa: E402
import qc  # noqa: E402
from ui_dispatcher import card_head, chip, eyebrow, get_calls, icon, tag  # noqa: E402

DATASETS = {"demo": "Demo city: 42 days, planted problems",
            "baseline": "Baseline city: 28 days, stable",
            "messy": "Messy file: 3 days, planted data errors"}
PRIORITY_CHOICES = {"1": "Priority 1 (life-threatening)", "2": "Priority 2", "3": "Priority 3"}
PERIODS = {"14": "Last 14 days", "28": "Last 28 days", "42": "Last 42 days"}
ZONE_CHOICES = {z: f"Zone {z}" for z in qc.ZONES}
STATUS_WORD = {"green": "On track", "amber": "Worth a look", "red": "Act now",
               "unknown": "Not enough data"}
STAGE_WORD = {"processing": "Dispatcher processing", "turnout": "Crew turnout", "travel": "Travel"}
RULE_NAME = {"S1": "Crew readiness", "S2": "Coverage", "S3": "Routes", "S4": "Dispatcher cover",
             "S5": "Maintenance", "S6": "Address checks"}
DEMO_BEFORE_FIX = "2026-09-28"


# ---- small formatting helpers (formatting only, no statistics) ------------------------------------

def _num(v, digits=1, unit=""):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return f"{v:.{digits}f}{unit}"


def _kpi(label, value, ic=None, tone=None):
    attrs = {"data-tone": tone} if tone else {}
    return ui.div(ui.div(icon(ic), class_="rw-kpi-icon") if ic else None,
                  ui.div(value, class_="rw-kpi-num", **attrs),
                  ui.div(label, class_="rw-kpi-label"), class_="rw-kpi")


def _row(sev, title, sub, right=None, right_cap=None):
    return ui.div(
        ui.span(class_="rw-dot"),
        ui.div(ui.div(*title, class_="rw-row-title") if isinstance(title, (list, tuple))
               else ui.div(title, class_="rw-row-title"),
               ui.div(sub, class_="rw-row-sub"), class_="rw-row-main"),
        ui.div(ui.div(ui.span(right, class_="rw-final", **{"data-sev": sev}),
                      ui.span(right_cap, class_="rw-cap"), class_="rw-clockbox"),
               class_="rw-row-clocks") if right is not None else None,
        class_="rw-row", **{"data-sev": sev})


def _card(label, title, *body, right=None):
    return ui.div(card_head(label, title, right), *body, class_="rw-card")


def _empty(text):
    return ui.div(text, class_="rw-empty")


def _note(text):
    return ui.div(text, class_="rw-small rw-muted rw-note")


# ---- settings shared by every tab -------------------------------------------------------------------

def _settings_ui():
    return ui.div(
        card_head("Settings", "What you are looking at"),
        ui.div(
            ui.input_select("dataset", "Dataset", DATASETS, selected="demo"),
            ui.input_select("priority", "Priority", PRIORITY_CHOICES, selected="1"),
            ui.input_date("as_of", "As of", value="2026-10-12"),
            ui.input_select("period", "Chart period", PERIODS, selected="28"),
            class_="rw-controls"),
        ui.div(
            ui.input_action_button("jump_before", "Jump to Sep 28 (before the fix)",
                                   class_="rw-btn rw-btn-ghost"),
            ui.input_action_button("jump_latest", "Jump to the latest day",
                                   class_="rw-btn rw-btn-ghost"),
            class_="rw-btnrow"),
        ui.accordion(
            ui.accordion_panel(
                "Targets and baseline",
                ui.div(
                    ui.input_numeric("t_p1", "Priority 1 target (min)", 9, min=1, max=60, step=0.5),
                    ui.input_numeric("t_p2", "Priority 2 target (min)", 15, min=1, max=90, step=0.5),
                    ui.input_numeric("t_p3", "Priority 3 target (min)", 20, min=1, max=120, step=0.5),
                    ui.input_numeric("t_proc", "Processing target (s)", 64, min=10, max=600, step=1),
                    ui.input_numeric("t_turn", "Turnout target (s)", 60, min=10, max=600, step=1),
                    ui.input_date("base_start", "Baseline start", value="2026-09-01"),
                    ui.input_numeric("base_days", "Baseline days", 14, min=5, max=28, step=1),
                    class_="rw-controls"),
                _note("Defaults come from NFPA 1710 for priority 1: 64 s processing, 60 s turnout and "
                      "480 s travel, each met by 90% of calls. The priority 2 and 3 targets are our "
                      "own assumptions. Control limits come from the baseline days, never from the target.")),
            open=False, id="settings_more"),
        class_="rw-card rw-settings")


def _load_actions(dataset: str) -> pd.DataFrame:
    cols = ["action_id", "date", "zone", "stage", "description", "owner"]
    if dataset != "demo":
        return pd.DataFrame(columns=cols)
    try:
        path = qc.find_data_dir() / "actions_demo.csv"
        acts = pd.read_csv(path, dtype=str) if path.is_file() else pd.DataFrame(columns=cols)
    except FileNotFoundError:
        acts = pd.DataFrame(columns=cols)
    return acts.reindex(columns=cols)


# ---- Overview: is everything okay? -----------------------------------------------------------------------

@module.ui
def overview_ui():
    return ui.div(
        ui.div(ui.div(eyebrow("Overview"), ui.h2("Is everything okay?", class_="rw-page-title")),
               class_="rw-page-head"),
        ui.output_ui("kpis"),
        ui.div(ui.output_ui("health"), ui.output_ui("history_map"), class_="rw-grid"),
        ui.output_ui("issues"))


@module.server
def overview_server(input, output, session, ctx):

    @render.ui
    def kpis():
        st = ctx.upto()
        if st is None:
            return _card("Overview", "Last 7 days", _empty(ctx.why()))
        week = qc.last_days(st, 7)
        calls = week[week["valid"] & (week["priority"] == ctx.priority())]
        s = qc.summary(calls["response_min"], ctx.target_min())
        health = ctx.health()
        flagged = int(health["status"].isin(["amber", "red"]).sum())
        on_time = s["pct_on_time"]
        tiles = ui.div(
            _kpi("Average (what 911 sees)", _num(s["mean"], 1, " min"), "clock"),
            _kpi("Median call", _num(s["median"], 1, " min"), "pulse"),
            _kpi("90th percentile", _num(s["p90"], 1, " min"), "chart",
                 "red" if s["p90"] and s["p90"] > ctx.target_min() else None),
            _kpi("95th percentile", _num(s["p95"], 1, " min"), "chart"),
            _kpi("On time", _num(on_time, 0, "%"), "route",
                 "red" if on_time is not None and on_time < 90 else None),
            _kpi("Zones flagged", f"{flagged} / {len(health)}", "pin",
                 "amber" if flagged else None),
            class_="rw-kpis rw-kpis-6")
        if s["n"]:
            msg = (f"The average says {s['mean']:.1f} min. But 1 in 10 patients waited more than "
                   f"{s['p90']:.1f} min, and 1 in 20 more than {s['p95']:.1f} min. "
                   f"Priority {ctx.priority()} target: {ctx.target_min():.0f} min for 90% of calls. "
                   f"{s['n']} calls, last 7 days up to {ctx.as_of():%b %d}.")
        else:
            msg = "No valid calls in the last 7 days."
        return ui.div(tiles, _note(msg), class_="rw-stack")

    @render.ui
    def health():
        h = ctx.health()
        if h is None:
            return _card("Zones", "Zone health", _empty(ctx.why()))
        rows = [_row(r.status if r.status != "unknown" else "grey",
                     [f"Zone {r.zone}", tag(STATUS_WORD[r.status],
                                            r.status if r.status in ("amber", "red") else None)],
                     "; ".join(r.reasons), _num(r.p90_recent, 1), "p90 min")
                for r in h.itertuples()]
        legend = _note("Last 7 days. Red: a flag rule fired AND the 90th percentile is over target "
                       "(act). Amber: one of the two (worth a look). Green: neither.")
        return _card("Zones", "Zone health", ui.div(*rows, class_="rw-rows"), legend)

    @render.ui
    def history_map():
        h = ctx.health()
        if h is None:
            return _card("Zones", "History map", _empty(ctx.why()))
        cells = []
        for r in h.itertuples():
            sev = r.status if r.status in ("green", "amber", "red") else "green"
            cells.append(ui.div(
                ui.div(ui.span(r.zone, class_="rw-tile-letter"), ui.span("Zone", class_="rw-tile-cap"),
                       class_="rw-tile-top"),
                ui.div(ui.div(f"p90 {_num(r.p90_recent, 1)} min", class_="rw-tile-line"),
                       ui.div((STAGE_WORD.get(r.top_stage, "") if r.top_stage else ""),
                              class_="rw-tile-line"),
                       ui.div(STATUS_WORD[r.status], class_="rw-tile-status")),
                class_="rw-tile", **{"data-sev": sev}))
        return _card("Zones", "History map (last 7 days)", ui.div(*cells, class_="rw-map"),
                     _note("A B C on the top row, D E F below. The tile names the stage behind "
                           "the delays when a zone is flagged."))

    @render.ui
    def issues():
        st = ctx.upto()
        if st is None:
            return None
        bad = qc.data_issues(st)
        if not len(bad):
            return _note("Data quality: every call in this period passed the checks.")
        rows = [_row("amber", [r.call_id, tag(f"Zone {r.zone}")], r.issue)
                for r in bad.head(20).itertuples()]
        return _card("Data quality", f"{len(bad)} call(s) left out of the statistics",
                     ui.div(*rows, class_="rw-rows"),
                     _note("Calls with missing or out-of-order times, duplicate IDs, a zero response "
                           "time or an unknown zone or priority are listed here and never counted."))


# ---- Charts: what is happening, and why? ---------------------------------------------------------------------

@module.ui
def charts_ui():
    return ui.div(
        ui.div(ui.div(eyebrow("Charts"), ui.h2("What is happening, and why?", class_="rw-page-title")),
               ui.input_select("zone", None, ZONE_CHOICES, selected="D", width="160px"),
               class_="rw-page-head"),
        _card("Control chart", "Daily average and spread (X-bar and S)",
              ui.output_plot("daily", height="430px"), ui.output_ui("daily_note")),
        _card("Control chart", "Every call (I-MR, log scale)",
              ui.output_plot("imr", height="430px"), ui.output_ui("imr_note")),
        ui.div(
            _card("Stage breakdown", "Which stage causes the delays",
                  ui.output_plot("share", height="300px"),
                  _note("Each bar splits a zone's minutes over target into processing, turnout and "
                        "travel. Stage targets: processing 64 s, turnout 60 s, travel = response "
                        "target minus 60 s.")),
            _card("Stage breakdown", "Median minutes in each stage",
                  ui.output_plot("medians", height="300px")),
            class_="rw-two"),
        ui.div(
            _card("Capability", "Can each zone meet the target?", ui.output_ui("capability")),
            _card("Tests", "Are the differences real?", ui.output_ui("tests"),
                  ui.output_plot("normal", height="260px")),
            class_="rw-two"))


@module.server
def charts_server(input, output, session, ctx):

    @reactive.calc
    def period():
        st = ctx.upto()
        return None if st is None else qc.last_days(st, ctx.period_days())

    @reactive.calc
    def daily_calc():
        st = ctx.upto()
        if st is None:
            return None
        chart = qc.daily_xbar_s(st, input.zone(), ctx.priority(), ctx.base_days(), ctx.base_start())
        start = qc.last_days(st, ctx.period_days())["date"].min()
        out = chart[chart["date"] >= start].copy() if len(chart) else chart
        out.attrs.update(chart.attrs)
        return out

    @render.plot(alt="X-bar and S control chart of daily response times for the chosen zone")
    def daily():
        chart = daily_calc()
        if chart is None:
            return charts.empty(ctx.why())
        acts = ctx.actions_upto()
        when = [pd.Timestamp(d) for d in acts[acts["zone"] == input.zone()]["date"]]
        return charts.daily_chart(chart, input.zone(), action_dates=when)


    @render.ui
    def daily_note():
        chart = daily_calc()
        if chart is None or not len(chart):
            return None
        flagged = chart[chart["alarm"]]
        parts = []
        if len(flagged):
            names = sorted({f[:-1] for fired in flagged["rules"] for f in fired if f.endswith("+")})
            parts.append(f"{len(flagged)} flagged day(s): " +
                         "; ".join(f"rule {r[1]}: {qc.RULE_TEXT[r]}" for r in names) + ".")
        else:
            parts.append("No flagged days in this period: the zone is behaving like its baseline.")
        if chart.attrs.get("baseline_note"):
            parts.append("Note: " + chart.attrs["baseline_note"] + ".")
        parts.append("How to read it: a red dot is a day when this zone was slower than its own normal "
                     "range. Limits widen on quiet days with few calls. The green line marks a logged "
                     "action.")
        return _note(" ".join(parts))

    @reactive.calc
    def imr_calc():
        st = ctx.upto()
        if st is None:
            return None
        imr = qc.imr_chart(st, input.zone(), ctx.priority(), ctx.base_days(), ctx.base_start())
        start = qc.last_days(st, ctx.period_days())["date"].min()
        out = imr[imr["date"] >= start].reset_index(drop=True) if len(imr) else imr
        out.attrs.update(imr.attrs)
        return out

    @render.plot(alt="Individuals and moving range chart of every call's response time")
    def imr():
        data = imr_calc()
        if data is None:
            return charts.empty(ctx.why())
        return charts.imr_chart(data, input.zone(), ctx.target_min())

    @render.ui
    def imr_note():
        data = imr_calc()
        if data is None or not len(data):
            return None
        n = int(data["beyond"].sum())
        late = int((data["response_min"] > ctx.target_min()).sum())
        return _note(f"{len(data)} calls. {n} beyond the upper control limit (extreme delays, "
                     f"special causes worth investigating one by one); {late} over the "
                     f"{ctx.target_min():.0f}-min target. The amber target line is a spec limit, "
                     "set by the standard; the dashed control limits come from the process itself.")

    @reactive.calc
    def breakdown():
        p = period()
        return None if p is None else qc.stage_breakdown(p, ctx.priority(), ctx.targets())

    @render.plot(alt="Share of minutes over target by stage for each zone")
    def share():
        bd = breakdown()
        return charts.empty(ctx.why()) if bd is None else charts.stage_share(bd)

    @render.plot(alt="Median minutes in each stage for each zone")
    def medians():
        bd = breakdown()
        return charts.empty(ctx.why()) if bd is None else charts.stage_breakdown(bd)

    @render.ui
    def capability():
        st = ctx.upto()
        if st is None:
            return _empty(ctx.why())
        cap = qc.zone_capability(st, ctx.priority(), ctx.targets(), ctx.base_days(), ctx.base_start(),
                                 period_days=ctx.period_days())
        head = ui.tags.tr(*[ui.tags.th(h) for h in ("Zone", "Ppk", "Cpk", "Expected on time",
                                                     "Stable", "Shapiro p")])
        trs = []
        for r in cap.itertuples():
            pct = qc.ppk_to_pct(r.ppk)
            trs.append(ui.tags.tr(
                ui.tags.td(f"Zone {r.zone}"),
                ui.tags.td(_num(r.ppk, 2) if r.shown else "–"),
                ui.tags.td(_num(r.cpk, 2) if r.shown else "–"),
                ui.tags.td(_num(pct, 1, "%") if r.shown else r.message),
                ui.tags.td("yes" if r.stable else tag("no", "red")),
                ui.tags.td(_num(r.shapiro_p, 3))))
        return ui.div(
            ui.div(ui.tags.table(ui.tags.thead(head), ui.tags.tbody(*trs), class_="rw-table"),
                   class_="rw-table-wrap"),
            _note("Upper side only: the target is an upper spec limit. Computed on log minutes. "
                  "Ppk uses the overall spread of all calls (sigma total); Cpk uses the spread within "
                  "each day, averaged over days (sigma short). Expected on time = Φ(3 × Ppk): Ppk 0.43 means about 90% "
                  "on time, 1.0 means 99.87%. Capability is only meaningful for a stable zone, so it "
                  "is hidden when the zone's chart has flags. Shapiro p above 0.05 means the log "
                  "times look normal; with hundreds of calls the test also flags small departures, "
                  "so check the probability plot under Tests too."))

    @render.ui
    def tests():
        p = period()
        if p is None:
            return _empty(ctx.why())
        a = qc.zone_anova(p, ctx.priority())
        if not a["ok"]:
            return _note(f"ANOVA: {a['message']}.")
        verdict = ("Zones really do differ (p < 0.05)." if a["p"] < 0.05
                   else "No evidence that zones differ (p ≥ 0.05).")
        means = ", ".join(f"{z} {math.exp(m):.1f}" for z, m in a["means"].items())
        return ui.div(
            ui.div(_kpi("F statistic", _num(a["F"], 2)),
                   _kpi("p-value", f"{a['p']:.2g}"),
                   _kpi("df", f"{a['df_between']}, {a['df_within']}"), class_="rw-kpis rw-kpis-3"),
            _note(f"One-way ANOVA of log response time across zones. {verdict} "
                  f"Typical (geometric mean) minutes: {means}. Below: is the chosen zone's log "
                  "response time close to normal?"))

    @render.plot(alt="Normal probability plot of log response times for the chosen zone")
    def normal():
        p = period()
        if p is None:
            return charts.empty(ctx.why())
        calls = p[p["valid"] & (p["priority"] == ctx.priority()) & (p["zone"] == input.zone())]
        return charts.normal_plot(qc.normality(np.log(calls["response_min"])), input.zone())


# ---- Actions: how do we fix it, and did it work? -------------------------------------------------------------------

@module.ui
def actions_ui():
    return ui.div(
        ui.div(ui.div(eyebrow("Actions"), ui.h2("How do we fix it, and did it work?",
                                                class_="rw-page-title")), class_="rw-page-head"),
        ui.output_ui("slip"),
        ui.output_ui("suggestions"),
        ui.div(
            _card("Action log", "What was done", ui.output_ui("log"),
                  ui.input_action_button("add_manual", "Log an action", class_="rw-btn rw-btn-ghost")),
            _card("Before and after", "Did it work?", ui.output_ui("pick_action"),
                  ui.output_ui("result")),
            class_="rw-two"),
        _card("Before and after", "The zone's daily chart around the action",
              ui.output_plot("ba_chart", height="430px")))


@module.server
def actions_server(input, output, session, ctx):

    @reactive.calc
    def found():
        st = ctx.upto()
        if st is None:
            return []
        return qc.suggest(st, ctx.actions_upto(), ctx.priority(), ctx.targets(),
                          baseline_days=ctx.base_days(), baseline_start=ctx.base_start())

    @render.ui
    def slip():
        st = ctx.upto()
        if st is None:
            return None
        alerts = qc.slip_back(st, ctx.actions_upto(), ctx.priority())
        if not alerts:
            return _note("Slip-back watch: no zone is drifting back after a logged action.")
        rows = [_row("red", [f"Zone {a['zone']}", tag("Slipping back", "red")], a["text"])
                for a in alerts]
        return _card("Control", "Slip-back alerts", ui.div(*rows, class_="rw-rows"))

    @render.ui
    def suggestions():
        items = found()
        if ctx.upto() is None:
            return _card("Improve", "Suggestions", _empty(ctx.why()))
        if not items:
            return _card("Improve", "Suggestions",
                         _empty("No suggestions: no zone or stage shows a pattern the rules look for."))
        rows = []
        for i, s in enumerate(items):
            imp = s["impact"]
            impact = (f"Estimate: on time {imp['pct_on_time_before']:.0f}% → "
                      f"{imp['pct_on_time_after']:.0f}% if this stage were typical"
                      if imp and imp["pct_on_time_before"] is not None else "")
            logged = s["status"] != "new"
            button = (tag(s["status"].capitalize(), None) if logged else
                      ui.tags.button("Log this action", type="button", class_="rw-btn",
                                     onclick=f"Shiny.setInputValue('{session.ns('log_sug')}', {i}, "
                                             "{priority: 'event'})"))
            rows.append(ui.div(
                ui.span(class_="rw-dot"),
                ui.div(ui.div(tag(RULE_NAME.get(s["rule"], s["rule"])),
                              tag("Citywide" if s["zone"] == "All" else f"Zone {s['zone']}"),
                              s["text"], class_="rw-row-title"),
                       ui.div(s["evidence"], class_="rw-row-sub"),
                       ui.div(impact, class_="rw-row-sub") if impact else None,
                       class_="rw-row-main"),
                ui.div(button, class_="rw-row-actions"),
                class_="rw-row", **{"data-sev": "green" if logged else "amber"}))
        return _card("Improve", "Suggestions from the data", ui.div(*rows, class_="rw-rows"),
                     _note("Each suggestion comes from a fixed if-then rule shown with its evidence. "
                           "The impact is a best-case estimate. Every suggestion is for review by "
                           "qualified staff; the tool decides nothing on its own."),
                     right=ui.span(str(len(items)), class_="rw-count"))

    def _action_modal(zone, stage, description, date):
        return ui.modal(
            ui.div(
                ui.input_select("m_zone", "Zone", {"All": "Citywide", **ZONE_CHOICES}, selected=zone),
                ui.input_select("m_stage", "Stage", {k: v for k, v in STAGE_WORD.items()},
                                selected=stage),
                ui.input_date("m_date", "Start date", value=date),
                class_="rw-controls"),
            ui.input_text_area("m_desc", "What was done", value=description, width="100%", rows=3),
            ui.input_text("m_owner", "Owner", value="EMS supervisor", width="100%"),
            title="Log an action",
            footer=ui.TagList(ui.modal_button("Cancel"),
                              ui.input_action_button("m_save", "Save action", class_="btn-primary")),
            easy_close=True)

    @reactive.effect
    @reactive.event(input.log_sug)
    def _log_suggestion():
        items = found()
        i = int(input.log_sug())
        if 0 <= i < len(items):
            s = items[i]
            day = (ctx.as_of() + pd.Timedelta(days=1)).date()
            ui.modal_show(_action_modal(s["zone"], s["stage"], s["text"], day))

    @reactive.effect
    @reactive.event(input.add_manual)
    def _log_manual():
        ui.modal_show(_action_modal("D", "turnout", "", ctx.as_of().date()))

    @reactive.effect
    @reactive.event(input.m_save)
    def _save():
        acts = ctx.actions().copy()
        same = acts[(acts["zone"] == input.m_zone()) & (acts["stage"] == input.m_stage())
                    & (acts["date"] == str(input.m_date()))]
        if len(same):
            ui.modal_remove()
            ui.notification_show(f"Already in the log as {same.iloc[0]['action_id']}.", duration=4)
            return
        new = {"action_id": f"A{len(acts) + 1}", "date": str(input.m_date()),
               "zone": input.m_zone(), "stage": input.m_stage(),
               "description": input.m_desc().strip() or "(no description)",
               "owner": input.m_owner().strip() or "EMS supervisor"}
        ctx.actions.set(pd.concat([acts, pd.DataFrame([new])], ignore_index=True))
        ui.modal_remove()
        ui.notification_show(f"Action {new['action_id']} logged for {new['date']}.", duration=4)

    @render.ui
    def log():
        acts = ctx.actions()
        if not len(acts):
            return _empty("No actions logged yet.")
        rows = [_row("green", [a.action_id, tag("Citywide" if a.zone == "All" else f"Zone {a.zone}"),
                               tag(STAGE_WORD.get(a.stage, a.stage))],
                     f"{a.date}: {a.description} ({a.owner})") for a in acts.itertuples()]
        return ui.div(*rows, class_="rw-rows")

    @render.ui
    def pick_action():
        acts = ctx.actions()
        zoned = acts[acts["zone"] != "All"]
        if not len(zoned):
            return _empty("Log a zone action to check its result.")
        choices = {a.action_id: f"{a.action_id}: Zone {a.zone}, {a.date}" for a in zoned.itertuples()}
        return ui.input_select("which", "Action", choices, selected=list(choices)[-1])

    @reactive.calc
    def chosen():
        acts = ctx.actions()
        if "which" not in input or not input.which():
            return None
        hit = acts[acts["action_id"] == input.which()]
        return None if not len(hit) else hit.iloc[0]

    @reactive.calc
    def check():
        act, st = chosen(), ctx.upto()
        if act is None or st is None:
            return None
        return qc.before_after(st, act["zone"], act["date"], ctx.priority(), targets=ctx.targets())

    @render.ui
    def result():
        ba = check()
        if ba is None:
            return None
        t, b, a = ba["test"], ba["before"], ba["after"]
        tone = {"improved": "green", "got worse": "red"}.get(ba["verdict"], "amber")
        verdict = ui.div(chip(ba["verdict"].capitalize(), tone), class_="rw-btnrow")
        tiles = ui.div(
            _kpi("Median before", _num(b["median"], 1, " min")),
            _kpi("Median after", _num(a["median"], 1, " min")),
            _kpi("On time before", _num(b["pct_on_time"], 0, "%")),
            _kpi("On time after", _num(a["pct_on_time"], 0, "%")),
            class_="rw-kpis rw-kpis-4")
        if t["ok"]:
            detail = (f"Welch's t-test, one-sided, on log response time: t = {t['t']:.2f}, "
                      f"df = {t['df']:.0f}, p = {t['p_one_sided']:.2g} ({t['n_before']} calls in the "
                      f"14 days before, {t['n_after']} after). ")
        else:
            detail = f"Test not run: {t['message']}. "
        control = ("After the action the zone's chart, with its own new limits, shows no flags: "
                   "the new level is stable." if ba["in_control_after"] else
                   "After the action the zone's chart still shows flags or has too few days yet.")
        return ui.div(verdict, tiles, _note(detail + control))

    @render.plot(alt="Daily chart of the zone before and after the action")
    def ba_chart():
        act, st = chosen(), ctx.upto()
        if act is None or st is None:
            return charts.empty("Pick an action to see its chart")
        chart = qc.daily_xbar_s(st, act["zone"], ctx.priority(), ctx.base_days(), ctx.base_start())
        return charts.before_after_chart(chart, act["zone"], pd.Timestamp(act["date"]))


#: (tab label, module id, ui function, server function), in tab order.
TABS = (
    ("Overview", "overview", overview_ui, overview_server),
    ("Charts", "charts", charts_ui, charts_server),
    ("Actions", "actions", actions_ui, actions_server),
)


@module.ui
def supervisor_ui():
    return ui.div(
        _settings_ui(),
        ui.navset_pill(*[ui.nav_panel(label, ui_fn(mod_id)) for label, mod_id, ui_fn, _ in TABS],
                       id="tabs"),
        class_="rw-supervisor")


@module.server
def supervisor_server(input, output, session):

    def _pos(v, default):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return default
        return v if v > 0 else default

    @reactive.calc
    def targets():
        return {"processing": _pos(input.t_proc(), 64), "turnout": _pos(input.t_turn(), 60),
                "response": {1: _pos(input.t_p1(), 9) * 60, 2: _pos(input.t_p2(), 15) * 60,
                             3: _pos(input.t_p3(), 20) * 60}}

    @reactive.calc
    def raw():
        return get_calls(input.dataset())

    @reactive.calc
    def why():
        return raw()[1] or "No data"

    @reactive.calc
    def stages():
        df, _ = raw()
        return None if df is None else qc.stage_times(df, targets())

    @reactive.calc
    def priority():
        return int(input.priority())

    @reactive.calc
    def target_min():
        return targets()["response"][priority()] / 60.0

    @reactive.calc
    def as_of():
        return pd.Timestamp(input.as_of()).normalize() if input.as_of() else None

    @reactive.calc
    def upto():
        st = stages()
        return None if st is None else qc.until(st, as_of())

    @reactive.calc
    def base_start():
        return pd.Timestamp(input.base_start()) if input.base_start() else None

    @reactive.calc
    def base_days():
        return int(_pos(input.base_days(), 14))

    @reactive.calc
    def period_days():
        return int(input.period())

    actions = reactive.Value(_load_actions("demo"))

    @reactive.calc
    def actions_upto():
        acts = actions()
        if not len(acts) or as_of() is None:
            return acts
        return acts[pd.to_datetime(acts["date"]) <= as_of()]

    @reactive.calc
    def health():
        st = upto()
        if st is None:
            return None
        return qc.zone_health(st, priority(), targets(), baseline_days=base_days(),
                              actions=actions_upto(), baseline_start=base_start())

    @reactive.effect
    @reactive.event(input.dataset)
    def _dataset_changed():
        actions.set(_load_actions(input.dataset()))
        df, _ = raw()
        if df is None:
            return
        days = df["call_received"].dropna().dt.normalize()
        first, last = days.min().date(), days.max().date()
        ui.update_date("as_of", value=last, min=first, max=last)
        ui.update_date("base_start", value=first, min=first, max=last)

    @reactive.effect
    @reactive.event(input.jump_before)
    def _jump_before():
        ui.update_date("as_of", value=DEMO_BEFORE_FIX)

    @reactive.effect
    @reactive.event(input.jump_latest)
    def _jump_latest():
        df, _ = raw()
        if df is not None:
            ui.update_date("as_of", value=df["call_received"].max().date())

    ctx = SimpleNamespace(targets=targets, stages=stages, upto=upto, why=why, priority=priority,
                          target_min=target_min, as_of=as_of, base_start=base_start,
                          base_days=base_days, period_days=period_days, actions=actions,
                          actions_upto=actions_upto, health=health)
    for _, mod_id, _, server_fn in TABS:
        server_fn(mod_id, ctx)
