"""Supervisor screens for ERGent: Charts and Actions.

Charts answers "what is happening, and why?": a control bar (chart, zone,
priority, dataset, as-of date, chart period, targets), one control chart on the
left with the city statistics and zone map on the right, then the delay by stage,
the zone comparison and each zone's capability. Actions answers "how do we fix
it, and did it work?" (the Six Sigma Improve and Control steps).

Every card has one plain title. Short interpretations sit behind "More info"
toggles. Every statistic comes from qc.py and every chart from charts.py; this
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
from shiny.module import resolve_id  # noqa: E402

import charts  # noqa: E402
import qc  # noqa: E402
import zonemap  # noqa: E402
from ui_dispatcher import card_head, chip, get_calls, icon, tag  # noqa: E402

DATASETS = {"demo": "Ithaca demo (42 days)", "baseline": "Ithaca baseline (28 days)",
            "messy": "Messy file (3 days)"}
PRIORITY_CHOICES = {str(p): f"Priority {p}: {name}" for p, name in qc.PRIORITY_NAME.items()}
PERIODS = {"14": "Last 14 days", "28": "Last 28 days", "42": "Last 42 days"}
ZONE_CHOICES = {z: f"Zone {z} · {qc.ZONE_NAMES[z]}" for z in qc.ZONES}
VIEWS = {"xbar": "Daily chart", "ind": "Every call"}
STATUS_WORD = {"green": "On track", "amber": "Worth a look", "red": "Act now",
               "unknown": "Not enough data"}
STAGE_WORD = {"processing": "Dispatch processing", "turnout": "Crew turnout", "travel": "Travel"}
RULE_NAME = {"S1": "Crew readiness", "S2": "Coverage", "S3": "Routes", "S4": "Dispatcher cover",
             "S5": "Maintenance", "S6": "Address checks"}

STYLE = ""      # the supervisor styles live in www/rw.css (v5 "Cayuga Report")


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


def _row(sev, title, sub):
    return ui.div(ui.span(class_="rw-dot"),
                  ui.div(ui.div(*title, class_="rw-row-title") if isinstance(title, (list, tuple))
                         else ui.div(title, class_="rw-row-title"),
                         ui.div(sub, class_="rw-row-sub"), class_="rw-row-main"),
                  class_="rw-row", **{"data-sev": sev})


def _card(title, *body, right=None):
    return ui.div(card_head("", title, right), *body, class_="rw-card")


def _empty(text):
    return ui.div(text, class_="rw-empty")


def _more(*content):
    """A 'More info' toggle with a short interpretation (2-3 sentences)."""
    return ui.tags.details(ui.tags.summary("More info"),
                           ui.div(*content, class_="rw-moreinfo-body"), class_="rw-moreinfo")


def _p(text):
    return ui.tags.p(text)


def _span(start, end):
    return f"{start:%b %d} – {end:%b %d}" if start is not None and end is not None else ""


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


def _control_bar():
    """The shared controls (supervisor namespace), shown at the top of the Charts tab."""
    return ui.div(ui.div(
        ui.input_radio_buttons("view", "Chart", VIEWS, selected="xbar", inline=True),
        ui.input_select("zone", "Zone", ZONE_CHOICES, selected="D", width="240px"),
        ui.input_select("priority", "Priority", PRIORITY_CHOICES, selected="1", width="230px"),
        ui.input_select("dataset", "Dataset", DATASETS, selected="demo", width="210px"),
        ui.input_date("as_of", "As of", value="2026-10-12", width="140px"),
        ui.input_select("period", "Chart period", PERIODS, selected="28", width="150px"),
        ui.input_action_button("edit_targets", "Targets", class_="rw-btn rw-btn-ghost"),
        class_="rw-chartbar"), class_="rw-card rw-toolbar")


# ---- Charts ---------------------------------------------------------------------------------------------------

@module.ui
def charts_ui():
    return ui.div(
        ui.div(
            _card("Control chart", ui.output_ui("chart_area"), ui.output_ui("chart_more")),
            ui.div(_card("Statistics", ui.output_ui("stats")),
                   _card("Zone map", zonemap.map_div(resolve_id("ithaca_map"),
                                                     click_input=resolve_id("map_click"),
                                                     height="300px"),
                         ui.output_ui("zone_map_more")),
                   ui.output_ui("issues"), class_="rw-sup-side"),
            class_="rw-sup-grid"),
        ui.div(
            _card("Delay by stage", ui.output_ui("share_range"), ui.output_ui("share_svg"),
                  ui.output_ui("share_more")),
            _card("Zone comparison", ui.output_ui("tests")),
            class_="rw-two"),
        _card("Capability", ui.output_ui("capability")))


@module.server
def charts_server(input, output, session, ctx):

    @reactive.calc
    def period():
        st = ctx.upto()
        return None if st is None else qc.last_days(st, ctx.period_days())

    @reactive.calc
    def period_start():
        p = period()
        return None if p is None or not len(p) or p["date"].isna().all() else p["date"].min()

    @reactive.calc
    def daily_calc():
        st, start = ctx.upto(), period_start()
        if st is None or start is None:
            return None
        chart = qc.daily_xbar_s(st, ctx.zone(), ctx.priority(), baseline_days=ctx.period_days(),
                                baseline_start=start)
        out = chart[chart["date"] >= start].copy() if len(chart) else chart
        out.attrs.update(chart.attrs)
        return out

    @reactive.calc
    def ind_calc():
        st, start = ctx.upto(), period_start()
        if st is None or start is None:
            return None
        data = qc.imr_chart(st, ctx.zone(), ctx.priority(), baseline_days=ctx.period_days(),
                            baseline_start=start)
        out = data[data["date"] >= start].reset_index(drop=True) if len(data) else data
        out.attrs.update(data.attrs)
        return out

    @render.ui
    def chart_area():
        if ctx.view() == "ind":
            return ui.output_plot("ind_plot", height="400px")
        return ui.output_plot("daily_plot", height="430px")

    @render.plot(alt="Daily X-bar and S control chart for the chosen zone")
    def daily_plot():
        chart = daily_calc()
        if chart is None:
            return charts.empty(ctx.why())
        acts = ctx.actions_upto()
        when = [pd.Timestamp(d) for d in acts[acts["zone"] == ctx.zone()]["date"]]
        return charts.daily_chart(chart, ctx.zone(), action_dates=when, target_min=ctx.target_min())

    @render.plot(alt="Control chart of every call for the chosen zone")
    def ind_plot():
        data = ind_calc()
        if data is None:
            return charts.empty(ctx.why())
        return charts.individuals_chart(data, ctx.zone(), ctx.target_min())

    @render.ui
    def chart_more():
        z = ctx.zone()
        if ctx.view() == "ind":
            data = ind_calc()
            if data is None or not len(data):
                return None
            n, late = int(data["beyond"].sum()), int((data["response_min"] > ctx.target_min()).sum())
            return _more(_p(f"Each dot is one call. {n} calls were above the upper control limit "
                            f"(unusual delays worth checking one by one) and {late} missed the "
                            f"{ctx.target_min():.0f}-min target (amber line)."))
        chart = daily_calc()
        if chart is None or not len(chart):
            return None
        slow = chart[chart["alarm"]]
        center = chart["x_center_min"].iloc[0]
        first = (f"Each dot is one day's typical response in Zone {z}; the center line ({center:.1f} "
                 "min) is the mean of the days shown and the dashed lines are ±3 standard deviations.")
        if len(slow):
            second = (f" On {len(slow)} day(s) the zone was outside that range (red dots), so "
                      "something changed.")
        else:
            second = " No day was outside that range."
        h = ctx.health()
        row = h.set_index("zone").loc[z] if h is not None else None
        third = ""
        if row is not None and row["p90_recent"] is not None and row["p90_recent"] > ctx.target_min():
            third = (f" But its 90th percentile ({row['p90_recent']:.1f} min) misses the "
                     f"{ctx.target_min():.0f}-min target, so check the delay by stage.")
        return _more(_p(first + second + third))

    @render.ui
    def stats():
        p = period()
        if p is None:
            return _empty(ctx.why())
        calls = p[p["valid"] & (p["priority"] == ctx.priority())]
        s = qc.summary(calls["response_min"], ctx.target_min())
        health = ctx.health()
        flagged = int(health["status"].isin(["amber", "red"]).sum()) if health is not None else 0
        on_time = s["pct_on_time"]
        return ui.div(
            ui.div(_span(period_start(), ctx.as_of()) + f" · {s['n']} calls, all zones",
                   class_="rw-subtitle"),
            ui.div(
                _kpi("Average", _num(s["mean"], 1, " min"), "clock"),
                _kpi("Standard deviation", _num(s["sd"], 1, " min"), "chart"),
                _kpi("On time", _num(on_time, 0, "%"), "route",
                     "red" if on_time is not None and on_time < 90 else None),
                _kpi("Zones flagged", f"{flagged} / 6", "pin", "amber" if flagged else None),
                class_="rw-stats"),
            _more(_p(f"The average and standard deviation of response time for priority "
                     f"{ctx.priority()} calls in the chart period. On time = share of calls within "
                     f"{ctx.target_min():.0f} min; the goal is at least 90%.")))

    @reactive.effect
    async def _paint_map():
        h = ctx.health()
        if h is None:
            return
        zones = {}
        for r in h.itertuples():
            sev = r.status if r.status in ("green", "amber", "red") else "grey"
            lines = list(r.reasons)
            if isinstance(r.top_stage, str) and r.top_stage in STAGE_WORD:
                lines.insert(0, f"Main delay: {STAGE_WORD[r.top_stage].lower()}")
            zones[r.zone] = {"sev": sev, "status": STATUS_WORD[r.status], "lines": lines}
        await zonemap.update(session, session.ns("ithaca_map"), zones)

    @reactive.effect
    @reactive.event(input.map_click)
    def _pick_zone():
        ctx.set_zone(input.map_click())

    @render.ui
    def zone_map_more():
        return _more(_p("Ithaca, NY, in six illustrative zones, coloured over the last 7 days. Red means "
                        "a real change on the chart and a 90th percentile over the target; amber means one "
                        "of the two. Hover a zone for the reason; click it to chart it."))

    @render.ui
    def issues():
        st = ctx.upto()
        if st is None:
            return None
        bad = qc.data_issues(st)
        if not len(bad):
            return None
        rows = [_row("amber", [r.call_id, tag(f"Zone {r.zone}")], r.issue)
                for r in bad.head(20).itertuples()]
        return _card(f"Data quality ({len(bad)} left out)", ui.div(*rows, class_="rw-rows"))

    @reactive.calc
    def breakdown():
        p = period()
        return None if p is None else qc.stage_breakdown(p, ctx.priority(), ctx.targets())

    @render.ui
    def share_range():
        return ui.div(f"{_span(period_start(), ctx.as_of())} · priority {ctx.priority()}",
                      class_="rw-subtitle")

    @render.ui
    def share_svg():
        bd = breakdown()
        if bd is None:
            return _empty(ctx.why())
        return ui.div(ui.HTML(charts.stage_share_svg(bd)), class_="rw-svg")

    @render.ui
    def share_more():
        bd = breakdown()
        if bd is None or not len(bd):
            return None
        row = bd.set_index("zone").loc[ctx.zone()]
        shares = {s: row[f"{s}_share"] for s in qc.STAGES}
        top = max(shares, key=shares.get)
        lead = (f"In Zone {ctx.zone()}, {STAGE_WORD[top].lower()} causes {shares[top]:.0%} of the "
                "minutes over target." if row[f"{top}_excess_min"] > 0 else
                f"In Zone {ctx.zone()}, no stage is over its target.")
        return _more(_p(lead + " Each bar splits a zone's minutes over target into dispatch, crew "
                        "turnout and travel. Hover a bar to see its numbers."))

    @render.ui
    def tests():
        p = period()
        if p is None:
            return _empty(ctx.why())
        a = qc.zone_anova(p, ctx.priority())
        if not a["ok"]:
            return ui.div(f"Not enough data to compare zones ({a['message']}).", class_="rw-answer")
        means = {z: math.exp(m) for z, m in a["means"].items()}
        slow, fast = max(means, key=means.get), min(means, key=means.get)
        answer = (f"Yes. Zone {slow} is typically {means[slow]:.1f} min against {means[fast]:.1f} min "
                  f"in Zone {fast}; a gap this big is very unlikely to be chance." if a["p"] < 0.05
                  else "No clear difference: the gaps between zones could be chance.")
        return ui.div(ui.div(answer, class_="rw-answer"), _more(
            _p(f"One-way ANOVA on log response time: F = {a['F']:.2f}, p = {a['p']:.2g}. A p below "
               "0.05 means the zones really differ."),
            ui.output_plot("normal", height="220px")))

    @render.plot(alt="Normal probability plot of log response times for the chosen zone")
    def normal():
        p = period()
        if p is None:
            return charts.empty(ctx.why())
        calls = p[p["valid"] & (p["priority"] == ctx.priority()) & (p["zone"] == ctx.zone())]
        return charts.normal_plot(qc.normality(np.log(calls["response_min"])), ctx.zone())

    @render.ui
    def capability():
        st = ctx.upto()
        if st is None:
            return _empty(ctx.why())
        cap = qc.zone_capability(st, ctx.priority(), ctx.targets(), period_days=ctx.period_days())
        rows, nums = [], []
        for r in cap.itertuples():
            v = qc.capability_verdict(r, ctx.target_min())
            rows.append(ui.div(ui.span(f"Zone {r.zone}", class_="rw-row-title"),
                               ui.span(chip(v["label"], v["tone"] if v["tone"] != "grey" else None)),
                               ui.span(v["text"], class_="rw-row-sub"), class_="rw-verdict"))
            pct = qc.ppk_to_pct(r.ppk)
            nums.append(ui.tags.tr(ui.tags.td(f"Zone {r.zone}"),
                                   ui.tags.td(_num(r.ppk, 2) if r.shown else "–"),
                                   ui.tags.td(_num(r.cpk, 2) if r.shown else "–"),
                                   ui.tags.td(_num(pct, 1, "%") if r.shown else "–")))
        table = ui.div(ui.tags.table(
            ui.tags.thead(ui.tags.tr(*[ui.tags.th(h) for h in ("Zone", "Ppk", "Cpk", "Expected on time")])),
            ui.tags.tbody(*nums), class_="rw-table"), class_="rw-table-wrap")
        return ui.div(ui.div(*rows, class_="rw-verdicts"), _more(
            _p("How reliably each zone's calls arrive within the target. Ppk uses the spread of all "
               "calls and Cpk the spread within each day; Ppk 0.43 means about 90% on time."),
            table))


# ---- Actions -------------------------------------------------------------------------------------------------------

@module.ui
def actions_ui():
    return ui.div(
        ui.output_ui("context"),
        ui.output_ui("slip"),
        ui.div(_card("Suggested actions", ui.output_ui("suggestions")),
               _card("Actions taken", ui.output_ui("log"),
                     ui.input_action_button("add_manual", "Log an action", class_="rw-btn rw-btn-ghost")),
               class_="rw-two"),
        ui.div(_card("Before and after", ui.output_plot("ba_chart", height="380px")),
               _card("Result", ui.output_ui("pick_action"), ui.output_ui("result")),
               class_="rw-two rw-two-ba"))


@module.server
def actions_server(input, output, session, ctx):

    @render.ui
    def context():
        return ui.div(f"{qc.CITY} · {DATASETS[ctx.dataset()]} · {PRIORITY_CHOICES[str(ctx.priority())]} · as of "
                      f"{ctx.as_of():%b %d} (change these on the Charts tab)", class_="rw-ctxline")

    @reactive.calc
    def found():
        st = ctx.upto()
        if st is None:
            return []
        return qc.suggest(st, ctx.actions_upto(), ctx.priority(), ctx.targets(),
                          period_days=ctx.period_days())

    @render.ui
    def slip():
        st = ctx.upto()
        if st is None:
            return None
        alerts = qc.slip_back(st, ctx.actions_upto(), ctx.priority())
        if not alerts:
            return None
        rows = [_row("red", [f"Zone {a['zone']}", tag("Slipping back", "red")], a["text"]) for a in alerts]
        return _card("Slip-back alerts", ui.div(*rows, class_="rw-rows"))

    @render.ui
    def suggestions():
        items = found()
        if ctx.upto() is None:
            return _empty(ctx.why())
        if not items:
            return _empty("No suggested actions for this period.")
        rows = []
        for i, s in enumerate(items):
            imp = s["impact"]
            impact = (f"Estimate: on time {imp['pct_on_time_before']:.0f}% → {imp['pct_on_time_after']:.0f}%"
                      if imp and imp["pct_on_time_before"] is not None else "")
            logged = s["status"] != "new"
            button = (tag(s["status"].capitalize()) if logged else
                      ui.tags.button("Log this action", type="button", class_="rw-btn",
                                     onclick=f"Shiny.setInputValue('{session.ns('log_sug')}', {i}, "
                                             "{priority: 'event'})"))
            rows.append(ui.div(
                ui.span(class_="rw-dot"),
                ui.div(ui.div(tag(RULE_NAME.get(s["rule"], s["rule"])),
                              tag("Citywide" if s["zone"] == "All" else f"Zone {s['zone']}"),
                              s["text"], class_="rw-row-title"),
                       ui.div(s["evidence"], class_="rw-row-sub"),
                       ui.div(impact, class_="rw-row-sub") if impact else None, class_="rw-row-main"),
                ui.div(button, class_="rw-row-actions"),
                class_="rw-row", **{"data-sev": "green" if logged else "amber"}))
        return ui.div(ui.div(*rows, class_="rw-rows"), _more(_p(
            "Each suggestion comes from a fixed rule on the data, with its evidence. The estimate is a "
            "best case if that stage were typical; qualified staff decide.")))

    def _action_modal(zone, stage, description, date):
        return ui.modal(
            ui.div(ui.input_select("m_zone", "Zone", {"All": "Citywide", **ZONE_CHOICES}, selected=zone),
                   ui.input_select("m_stage", "Stage", dict(STAGE_WORD), selected=stage),
                   ui.input_date("m_date", "Start date", value=date), class_="rw-controls"),
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
            ui.modal_show(_action_modal(s["zone"], s["stage"], s["text"],
                                        (ctx.as_of() + pd.Timedelta(days=1)).date()))

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
        new = {"action_id": f"A{len(acts) + 1}", "date": str(input.m_date()), "zone": input.m_zone(),
               "stage": input.m_stage(), "description": input.m_desc().strip() or "(no description)",
               "owner": input.m_owner().strip() or "EMS supervisor"}
        ctx.actions.set(pd.concat([acts, pd.DataFrame([new])], ignore_index=True))
        ui.modal_remove()
        ui.notification_show(f"Action {new['action_id']} logged for {new['date']}.", duration=4)

    @render.ui
    def log():
        acts = ctx.actions()
        if not len(acts):
            return _empty("No actions logged yet.")
        when = ctx.as_of()
        rows = []
        for a in acts.itertuples():
            later = when is not None and pd.Timestamp(a.date) > when
            rows.append(_row("grey" if later else "green",
                             [a.action_id, tag("Citywide" if a.zone == "All" else f"Zone {a.zone}"),
                              tag(STAGE_WORD.get(a.stage, a.stage)),
                              tag("After the as-of date") if later else None],
                             f"{a.date}: {a.description} ({a.owner})"))
        return ui.div(*rows, class_="rw-rows")

    @render.ui
    def pick_action():
        acts = ctx.actions()
        zoned = acts[acts["zone"] != "All"]
        if not len(zoned):
            return _empty("Log a zone action to see its result.")
        choices = {a.action_id: f"{a.action_id}: Zone {a.zone}, {a.date}" for a in zoned.itertuples()}
        when = ctx.as_of()
        done = [a.action_id for a in zoned.itertuples() if when is None or pd.Timestamp(a.date) <= when]
        return ui.input_select("which", "Action", choices, selected=(done or list(choices))[-1])

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
        rows = [("Mean", _num(b["mean"], 1, " min"), _num(a["mean"], 1, " min")),
                ("Standard deviation", _num(b["sd"], 1, " min"), _num(a["sd"], 1, " min")),
                ("On time", _num(b["pct_on_time"], 0, "%"), _num(a["pct_on_time"], 0, "%")),
                ("Calls", str(b["n"]), str(a["n"]))]
        table = ui.div(ui.tags.table(
            ui.tags.thead(ui.tags.tr(ui.tags.th(""), ui.tags.th("Before"), ui.tags.th("After"))),
            ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(c) for c in r]) for r in rows]),
            class_="rw-table rw-ba-table"), class_="rw-table-wrap")
        test = (f"Welch's t-test: t = {t['t']:.2f}, p = {t['p_one_sided']:.2g}." if t["ok"]
                else f"No test: {t['message']}.")
        steady = "The new level is steady." if ba["in_control_after"] else "Not steady yet."
        return ui.div(ui.div(chip(ba["verdict"].capitalize(), tone), class_="rw-btnrow"), table,
                      _more(_p(f"We compare the 14 days before the action with the days after. {test} "
                               f"{steady}")))

    @render.plot(alt="Daily chart of the zone before and after the action")
    def ba_chart():
        act, st = chosen(), ctx.upto()
        if act is None or st is None:
            return charts.empty("Pick an action to see its chart")
        start = qc.last_days(st, ctx.period_days())["date"].min()
        chart = qc.daily_xbar_s(st, act["zone"], ctx.priority(), baseline_days=ctx.period_days(),
                                baseline_start=start)
        chart = chart[chart["date"] >= start] if len(chart) else chart
        return charts.before_after_chart(chart, act["zone"], pd.Timestamp(act["date"]),
                                         target_min=ctx.target_min())


#: (tab label, module id, ui function, server function), in tab order.
TABS = (
    ("Charts", "charts", charts_ui, charts_server),
    ("Actions", "actions", actions_ui, actions_server),
)


@module.ui
def supervisor_ui():
    panels = [ui.nav_panel("Charts", _control_bar(), charts_ui("charts")),
              ui.nav_panel("Actions", actions_ui("actions"))]
    return ui.div(
        ui.tags.style(STYLE),
        # Shiny skips hidden plots; opening a "More info" toggle makes it look again.
        ui.tags.script("document.addEventListener('toggle', function (e) {"
                       " if (e.target.tagName === 'DETAILS' && e.target.open)"
                       " window.dispatchEvent(new Event('resize')); }, true);"),
        ui.navset_pill(*panels, id="tabs"),
        class_="rw-supervisor")


@module.server
def supervisor_server(input, output, session):

    targets = reactive.Value(dict(qc.TARGETS, response=dict(qc.TARGETS["response"])))

    @reactive.effect
    @reactive.event(input.edit_targets)
    def _targets_modal():
        t = targets()
        ui.modal_show(ui.modal(
            ui.div(ui.input_numeric("t_p1", "Priority 1 target (min)", t["response"][1] / 60, min=1, step=0.5),
                   ui.input_numeric("t_p2", "Priority 2 target (min)", t["response"][2] / 60, min=1, step=0.5),
                   ui.input_numeric("t_p3", "Priority 3 target (min)", t["response"][3] / 60, min=1, step=0.5),
                   ui.input_numeric("t_proc", "Processing target (s)", t["processing"], min=10, step=1),
                   ui.input_numeric("t_turn", "Turnout target (s)", t["turnout"], min=10, step=1),
                   class_="rw-controls"),
            ui.div("Defaults: NFPA 1710 for priority 1; priorities 2 and 3 are our assumptions.",
                   class_="rw-subtitle"),
            title="Targets",
            footer=ui.TagList(ui.modal_button("Cancel"),
                              ui.input_action_button("t_save", "Save", class_="btn-primary")),
            easy_close=True))

    @reactive.effect
    @reactive.event(input.t_save)
    def _save_targets():
        def pos(v, default):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return default
            return v if v > 0 else default
        old = targets()
        targets.set({"processing": pos(input.t_proc(), old["processing"]),
                     "turnout": pos(input.t_turn(), old["turnout"]),
                     "response": {p: pos(getattr(input, f"t_p{p}")(), old["response"][p] / 60) * 60
                                  for p in (1, 2, 3)}})
        ui.modal_remove()

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
        return qc.zone_health(st, priority(), targets(), actions=actions_upto(),
                              period_days=period_days())

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

    def set_zone(z):
        if z in qc.ZONES:
            ui.update_select("zone", selected=z, session=session)

    ctx = SimpleNamespace(targets=targets, stages=stages, upto=upto, why=why, priority=priority,
                          set_zone=set_zone,
                          target_min=target_min, as_of=as_of, period_days=period_days,
                          dataset=input.dataset, zone=input.zone, view=input.view,
                          actions=actions, actions_upto=actions_upto, health=health)
    for _, mod_id, _, server_fn in TABS:
        server_fn(mod_id, ctx)
