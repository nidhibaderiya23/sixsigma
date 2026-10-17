"""Supervisor screens: Overview, Charts and Actions.

Overview answers "is everything okay?", Charts answers "what is happening, and
why?", and Actions answers "how do we fix it, and did it work?" (the Six Sigma
Improve and Control steps). A settings card above the tabs picks the dataset,
priority, as-of date and targets; the Charts tab has its own control bar (chart
toggle, zone, as-of date kept in sync, chart period, jump to).

Screens show results only. Explanations for a supervisor who is new to Six
Sigma sit behind "More info..." toggles, with short questions and answers.

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
VIEWS = {"xbar": "Daily chart (X̄-S)", "imr": "Every call (I-MR)"}
JUMPS = {"": "Jump to…", "before": "Sep 28 (before the fix)", "latest": "The latest day"}
STATUS_WORD = {"green": "On track", "amber": "Worth a look", "red": "Act now",
               "unknown": "Not enough data"}
STAGE_WORD = {"processing": "Dispatcher processing", "turnout": "Crew turnout", "travel": "Travel"}
STAGE_PLAIN = {"processing": "the dispatcher sending the ambulance",
               "turnout": "the crew getting the ambulance moving",
               "travel": "the drive to the scene"}
RULE_NAME = {"S1": "Crew readiness", "S2": "Coverage", "S3": "Routes", "S4": "Dispatcher cover",
             "S5": "Maintenance", "S6": "Address checks"}
DEMO_BEFORE_FIX = "2026-09-28"

STYLE = """
.rw-moreinfo { margin-top: 12px; }
.rw-moreinfo > summary { cursor: pointer; color: var(--muted, #9aa0a6); font-size: 13px;
  list-style: none; display: inline-flex; align-items: center; gap: 6px; }
.rw-moreinfo > summary::-webkit-details-marker { display: none; }
.rw-moreinfo > summary::before { content: "+"; display: inline-grid; place-items: center;
  width: 18px; height: 18px; border: 1px solid rgba(255,255,255,0.18); border-radius: 50%; font-size: 12px; }
.rw-moreinfo[open] > summary::before { content: "–"; }
.rw-moreinfo-body { margin-top: 10px; padding: 12px 14px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  font-size: 13.5px; line-height: 1.6; color: var(--fg, #f2f2f0); }
.rw-moreinfo-body p { margin: 0 0 8px; }
.rw-faq { margin: 8px 0 0; }
.rw-faq dt { font-weight: 600; margin-top: 8px; }
.rw-faq dd { margin: 2px 0 0; color: var(--muted, #9aa0a6); }
.rw-chartbar { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
.rw-chartbar .shiny-input-container { width: auto; margin-bottom: 0; }
.rw-chartbar .shiny-input-radiogroup .shiny-options-group { display: flex; gap: 6px; }
.rw-chartbar .shiny-input-radiogroup label.radio-inline,
.rw-chartbar .shiny-input-radiogroup .form-check { margin: 0; }
.rw-verdict { display: grid; grid-template-columns: 90px 190px minmax(0, 1fr); gap: 10px;
  align-items: center; padding: 8px 0; border-top: 1px solid rgba(255,255,255,0.06); }
.rw-verdict:first-child { border-top: 0; }
.rw-answer { font-size: 15px; line-height: 1.55; }
@media (max-width: 640px) { .rw-verdict { grid-template-columns: 70px minmax(0, 1fr); }
  .rw-verdict > :last-child { grid-column: 1 / -1; } }
"""


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


def _more(*content):
    """A 'More info...' toggle; the explanation stays hidden until clicked."""
    return ui.tags.details(ui.tags.summary("More info…"),
                           ui.div(*content, class_="rw-moreinfo-body"), class_="rw-moreinfo")


def _faq(pairs):
    """Questions and answers for someone new to Six Sigma."""
    items = []
    for q, a in pairs:
        items += [ui.tags.dt(q), ui.tags.dd(a)]
    return ui.tags.dl(*items, class_="rw-faq")


def _p(text):
    return ui.tags.p(text)


# ---- settings shared by every tab -------------------------------------------------------------------

def _settings_ui():
    return ui.div(
        card_head("Settings", "What you are looking at"),
        ui.div(
            ui.input_select("dataset", "Dataset", DATASETS, selected="demo"),
            ui.input_select("priority", "Priority", PRIORITY_CHOICES, selected="1"),
            ui.input_date("as_of", "As of", value="2026-10-12"),
            class_="rw-controls"),
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
                _more(_faq([
                    ("Where do the targets come from?",
                     "Priority 1 uses NFPA 1710, the US standard: 64 s to send the ambulance, 60 s for "
                     "the crew to get moving and 8 min to drive, each met by 90% of calls, so 9 min from "
                     "dispatch to arrival. The priority 2 and 3 targets are our own assumptions."),
                    ("What is the baseline?",
                     "A stretch of normal days (by default the first 14) that sets each zone's normal "
                     "range on the control charts. The charts then ask: are later days still normal?"),
                ]))),
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
        if not s["n"]:
            return ui.div(tiles, class_="rw-stack")
        story = (f"In the last 7 days up to {ctx.as_of():%b %d}, the average call took "
                 f"{s['mean']:.1f} min. But 1 in 10 patients waited more than {s['p90']:.1f} min, "
                 f"and 1 in 20 more than {s['p95']:.1f} min ({s['n']} priority {ctx.priority()} calls).")
        return ui.div(tiles, _more(_p(story), _faq([
            ("Why not just the average?",
             "A few very slow calls hide inside a good-looking average. The 90th and 95th percentiles "
             "show how long the slowest patients waited, which is what the prompt worries about."),
            ("What is the 90th percentile?",
             "Sort the calls from fastest to slowest: 9 in 10 arrived faster than this number. The "
             f"standard says it should be under {ctx.target_min():.0f} min."),
            ("What is 'On time'?",
             f"The share of calls that arrived within {ctx.target_min():.0f} min of dispatch. The goal "
             "is at least 90%."),
        ])), class_="rw-stack")

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
        return _card("Zones", "Zone health", ui.div(*rows, class_="rw-rows"), _more(_faq([
            ("What do the colors mean?",
             "Red, act now: the zone's control chart shows a real change AND its 90th percentile "
             "misses the target. Amber, worth a look: one of the two. Green: neither. "
             "It looks at the last 7 days."),
            ("What is a 'real change'?",
             "The zone's daily times broke one of the control-chart rules: for example a day far "
             "outside its normal range, or many days in a row above normal. One weak sign on its own "
             "is shown but does not turn the zone amber, to avoid false alarms."),
            ("What should I do with a red zone?",
             "Open Charts, pick that zone, and look at the stage breakdown to see which part of the "
             "call is slow. Then check the Actions tab for a suggestion."),
        ])))

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
                     _more(_p("The tiles sit like the city: zones A, B and C on the top row, D, E and "
                              "F below. A flagged tile names the stage of the call that causes most "
                              "of the delay.")))

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
        return _card("Data quality", f"{len(bad)} call(s) left out of the statistics",
                     ui.div(*rows, class_="rw-rows"),
                     _more(_p("These records have a missing or out-of-order time, a duplicate ID, a "
                              "zero response time, or an unknown zone or priority. They are never "
                              "counted, so one bad record cannot distort a chart.")))


# ---- Charts: what is happening, and why? ---------------------------------------------------------------------

@module.ui
def charts_ui():
    bar = ui.div(
        ui.input_radio_buttons("view", "Chart", VIEWS, selected="xbar", inline=True),
        ui.input_select("zone", "Zone", ZONE_CHOICES, selected="D", width="130px"),
        ui.input_date("c_as_of", "As of", value="2026-10-12", width="150px"),
        ui.input_select("period", "Chart period", PERIODS, selected="28", width="150px"),
        ui.input_select("jump", "Jump", JUMPS, selected="", width="200px"),
        class_="rw-chartbar")
    return ui.div(
        ui.div(ui.div(eyebrow("Charts"), ui.h2("What is happening, and why?", class_="rw-page-title")),
               class_="rw-page-head"),
        ui.div(bar, class_="rw-card"),
        ui.panel_conditional(
            "input.view === 'xbar'",
            _card("Control chart", "Daily average and spread (X̄-S)",
                  ui.output_plot("daily", height="430px"), ui.output_ui("daily_more"))),
        ui.panel_conditional(
            "input.view === 'imr'",
            _card("Control chart", "Every call (I-MR, log scale)",
                  ui.output_plot("imr", height="430px"), ui.output_ui("imr_more"))),
        ui.div(
            _card("Stage breakdown", "Which stage causes the delays",
                  ui.output_plot("share", height="300px"), ui.output_ui("share_more")),
            _card("Stage breakdown", "Median minutes in each stage",
                  ui.output_plot("medians", height="300px")),
            class_="rw-two"),
        ui.div(
            _card("Capability", "Can each zone meet the target?", ui.output_ui("capability")),
            _card("Tests", "Do the zones really differ?", ui.output_ui("tests")),
            class_="rw-two"))


@module.server
def charts_server(input, output, session, ctx):

    # -- keep the chart bar's as-of date and the settings card's in step ------------------------------
    @reactive.effect
    def _follow_settings():
        when, rng = ctx.as_of(), ctx.date_range()
        if when is None or rng is None:
            return
        with reactive.isolate():
            mine = input.c_as_of()
        ui.update_date("c_as_of", value=when.date() if str(mine) != str(when.date()) else None,
                       min=rng[0], max=rng[1])

    @reactive.effect
    @reactive.event(input.c_as_of, ignore_init=True)
    def _push_to_settings():
        if input.c_as_of() and ctx.as_of() is not None and str(input.c_as_of()) != str(ctx.as_of().date()):
            ctx.set_as_of(input.c_as_of())

    @reactive.effect
    @reactive.event(input.jump, ignore_init=True)
    def _jump():
        choice = input.jump()
        if not choice:
            return
        rng = ctx.date_range()
        if choice == "before":
            ctx.set_as_of(DEMO_BEFORE_FIX)
        elif choice == "latest" and rng is not None:
            ctx.set_as_of(rng[1])
        ui.update_select("jump", selected="")

    def period_days():
        return int(input.period())

    @reactive.calc
    def period():
        st = ctx.upto()
        return None if st is None else qc.last_days(st, period_days())

    @reactive.calc
    def period_start():
        p = period()
        return None if p is None or not len(p) else p["date"].min()

    @reactive.calc
    def daily_calc():
        st = ctx.upto()
        if st is None:
            return None
        chart = qc.daily_xbar_s(st, input.zone(), ctx.priority(), ctx.base_days(), ctx.base_start())
        start = period_start()
        out = chart[chart["date"] >= start].copy() if len(chart) and start is not None else chart
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
    def daily_more():
        chart = daily_calc()
        z = input.zone()
        if chart is None or not len(chart):
            return None
        slow, fast = chart[chart["alarm"]], chart[chart["check"]]
        if len(slow):
            names = sorted({f[:-1] for fired in slow["rules"] for f in fired if f.endswith("+")})
            says = (f"On {len(slow)} day(s), starting {slow['date'].min():%b %d}, Zone {z} was slower "
                    f"than its normal range ({'; '.join(qc.RULE_TEXT[r] for r in names)}). That is too "
                    "much to be bad luck: something changed in how this zone works. The stage "
                    "breakdown below shows which part of the call got slower.")
        else:
            says = (f"Zone {z} stayed inside its normal range every day of this period: the ups and "
                    "downs are just normal day-to-day variation, and nothing needs fixing.")
        if len(fast):
            says += (f" On {len(fast)} day(s) it was unusually fast (hollow amber circles): check "
                     "those records before trusting them.")
        if chart.attrs.get("baseline_note"):
            says += " Note: " + chart.attrs["baseline_note"] + "."
        center = chart["x_center_min"].iloc[0]
        lo, hi = chart["x_lcl_min"].iloc[0], chart["x_ucl_min"].iloc[0]
        return _more(_p(says), _faq([
            ("What is each dot?",
             "One day: the typical (geometric average) response time of that day's calls."),
            ("What is the center line (the mean)?",
             f"Zone {z}'s normal level: the average of its daily dots during the baseline days, "
             f"about {center:.1f} min."),
            ("What are the dashed lines?",
             f"The normal range, about {lo:.1f} to {hi:.1f} min. It comes from how much the "
             "baseline days moved from one day to the next (3 standard deviations each side), so "
             "almost every normal day falls inside. The lines stay fixed, so every day is judged "
             "the same way."),
            ("What does a red dot mean?",
             "That day broke a rule: it was beyond the dashed line, or part of a run such as "
             "8 days in a row above the center. A real change is likely. Investigate it."),
            ("What is the bottom panel?",
             "How spread out each day's calls were. A jump means some calls that day were much "
             "slower than others."),
            ("Why isn't the 9-minute target on this chart?",
             "This chart asks whether the zone changed. The target is about single calls, so "
             "it is on the I-MR chart."),
            ("What is the green line?", "A logged action (a fix). Days after it should come down."),
        ]))

    @reactive.calc
    def imr_calc():
        st = ctx.upto()
        if st is None:
            return None
        imr = qc.imr_chart(st, input.zone(), ctx.priority(), ctx.base_days(), ctx.base_start())
        start = period_start()
        out = imr[imr["date"] >= start].reset_index(drop=True) if len(imr) and start is not None else imr
        out.attrs.update(imr.attrs)
        return out

    @render.plot(alt="Individuals and moving range chart of every call's response time")
    def imr():
        data = imr_calc()
        if data is None:
            return charts.empty(ctx.why())
        return charts.imr_chart(data, input.zone(), ctx.target_min())

    @render.ui
    def imr_more():
        data = imr_calc()
        if data is None or not len(data):
            return None
        n = int(data["beyond"].sum())
        late = int((data["response_min"] > ctx.target_min()).sum())
        says = (f"{len(data)} calls in this period. {n} were extreme delays (red dots, above the upper "
                f"dashed line): each is worth looking at one by one. {late} calls took longer than the "
                f"{ctx.target_min():.0f}-min target.")
        return _more(_p(says), _faq([
            ("What is each dot?", "One call, in the order the calls came in."),
            ("What are the dashed lines?",
             "The normal range for a single call, from the baseline calls. A call above the top "
             "line is an extreme delay with a special cause (a breakdown, a wrong address...)."),
            ("What is the amber line?",
             f"The {ctx.target_min():.0f}-min target from the standard. It is a requirement, not "
             "something the process decides. Calls above it missed the target."),
            ("Why a log scale?",
             "Response times have a long slow tail. The log scale makes the normal range fair "
             "on both sides."),
            ("What is the bottom panel?",
             "The jump between one call and the next. A huge jump points to one unusual call."),
        ]))

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
    def share_more():
        bd = breakdown()
        if bd is None or not len(bd):
            return None
        row = bd.set_index("zone").loc[input.zone()]
        shares = {s: row[f"{s}_share"] for s in qc.STAGES}
        top = max(shares, key=shares.get)
        if row[f"{top}_excess_min"] > 0:
            says = (f"In Zone {input.zone()}, {shares[top]:.0%} of the minutes over target come from "
                    f"{STAGE_PLAIN[top]} ({STAGE_WORD[top].lower()}). That is where a fix would help most.")
        else:
            says = f"In Zone {input.zone()}, no stage is over its target in this period."
        start = period_start()
        span = f"{start:%b %d} to {ctx.as_of():%b %d}" if start is not None else ""
        return _more(_p(says), _faq([
            ("What are the three stages?",
             "Processing: the call comes in until the dispatcher sends an ambulance (target 64 s). "
             "Turnout: the crew gets the ambulance moving (target 60 s). Travel: the drive to the "
             "scene (target = the response target minus 60 s)."),
            ("What does a bar show?",
             "Each zone's minutes over target, split by stage, so you can see which stage to fix."),
            ("Which days are counted?", f"The chart period: {span}, priority {ctx.priority()}."),
        ]))

    @render.ui
    def capability():
        st = ctx.upto()
        if st is None:
            return _empty(ctx.why())
        cap = qc.zone_capability(st, ctx.priority(), ctx.targets(), ctx.base_days(), ctx.base_start(),
                                 period_days=period_days())
        rows, detail = [], []
        for r in cap.itertuples():
            v = qc.capability_verdict(r, ctx.target_min())
            tone = v["tone"] if v["tone"] in ("amber", "red") else None
            rows.append(ui.div(ui.span(f"Zone {r.zone}", class_="rw-row-title"),
                               ui.span(chip(v["label"], v["tone"] if v["tone"] != "grey" else None)),
                               ui.span(v["text"], class_="rw-row-sub"), class_="rw-verdict"))
            pct = qc.ppk_to_pct(r.ppk)
            detail.append(ui.tags.tr(ui.tags.td(f"Zone {r.zone}"),
                                     ui.tags.td(_num(r.ppk, 2) if r.shown else "–"),
                                     ui.tags.td(_num(r.cpk, 2) if r.shown else "–"),
                                     ui.tags.td(_num(pct, 1, "%") if r.shown else "–"),
                                     ui.tags.td(_num(r.shapiro_p, 3))))
        numbers = ui.div(ui.tags.table(
            ui.tags.thead(ui.tags.tr(*[ui.tags.th(h) for h in ("Zone", "Ppk", "Cpk", "Expected on time",
                                                              "Shapiro p")])),
            ui.tags.tbody(*detail), class_="rw-table"), class_="rw-table-wrap")
        return ui.div(ui.div(*rows), _more(
            _p("The reading is based on how spread out each zone's response times are compared with "
               "the target: the narrower the spread below the target, the more reliably calls arrive "
               "on time."),
            _faq([
                ("What does 'Can't judge yet' mean?",
                 "The zone's times changed during the period, so a single reliability score would "
                 "mislead. Fix the cause first, then judge again."),
                ("For the curious: the numbers",
                 "Ppk uses the spread of all calls; Cpk uses the spread within each day. Both are on "
                 "log minutes, upper side only. Expected on time = Φ(3 × Ppk): 0.43 means about 90%, "
                 "1.0 means 99.87%. Shapiro p above 0.05 means the log times look normal enough."),
            ]),
            numbers))

    @render.ui
    def tests():
        p = period()
        if p is None:
            return _empty(ctx.why())
        a = qc.zone_anova(p, ctx.priority())
        if not a["ok"]:
            return ui.div(ui.div(f"Not enough data to compare zones: {a['message']}.", class_="rw-answer"))
        means = {z: math.exp(m) for z, m in a["means"].items()}
        slowest = max(means, key=means.get)
        fastest = min(means, key=means.get)
        if a["p"] < 0.05:
            answer = (f"Yes. Zone {slowest} is typically {means[slowest]:.1f} min against "
                      f"{means[fastest]:.1f} min in Zone {fastest}: differences this big are very "
                      "unlikely to be chance.")
        else:
            answer = ("No clear difference: the gaps between zones are small enough to be "
                      "ordinary chance.")
        calls = p[p["valid"] & (p["priority"] == ctx.priority()) & (p["zone"] == input.zone())]
        norm = qc.normality(np.log(calls["response_min"]))
        return ui.div(
            ui.div(answer, class_="rw-answer"),
            _more(
                _p("Typical time per zone (geometric mean, minutes): "
                   + ", ".join(f"{z} {m:.1f}" for z, m in means.items()) + "."),
                _faq([
                    ("How do we know it's not chance?",
                     f"A one-way ANOVA compares the zones on log response time: F = {a['F']:.2f} "
                     f"(df {a['df_between']}, {a['df_within']}), p = {a['p']:.2g}. A p below 0.05 means "
                     "differences this large would almost never happen by chance."),
                    ("Is the method fair for this data?",
                     f"It assumes log times are roughly normal. For Zone {input.zone()} the "
                     f"Shapiro-Wilk p is {_num(norm['p'], 3)} (the plot below should be close to a "
                     "straight line)."),
                ]),
                ui.output_plot("normal", height="240px")))

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
            return None
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
                     _more(_faq([
                         ("Where do suggestions come from?",
                          "Fixed if-then rules on the numbers, each shown with its evidence: for example "
                          "'turnout causes most of a flagged zone's delay → review crew readiness'."),
                         ("What is the estimate?",
                          "A best case: what % on time would be if that stage were as fast as the city's "
                          "typical call. Real results will be smaller."),
                         ("Who decides?",
                          "You do. The tool flags and suggests; qualified staff decide what to change."),
                     ])),
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
            return _empty("Log a zone action to check its result.")
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
        verdict = ui.div(chip(ba["verdict"].capitalize(), tone), class_="rw-btnrow")
        tiles = ui.div(
            _kpi("Median before", _num(b["median"], 1, " min")),
            _kpi("Median after", _num(a["median"], 1, " min")),
            _kpi("On time before", _num(b["pct_on_time"], 0, "%")),
            _kpi("On time after", _num(a["pct_on_time"], 0, "%")),
            class_="rw-kpis rw-kpis-4")
        stable = ("The new level is steady: the zone's chart after the action shows no warning signs."
                  if ba["in_control_after"] else
                  "The zone's chart after the action still shows warning signs, or there are too few "
                  "days yet.")
        if t["ok"]:
            test = (f"Welch's t-test, one-sided, on log response time: t = {t['t']:.2f}, df = "
                    f"{t['df']:.0f}, p = {t['p_one_sided']:.2g} ({t['n_before']} calls in the 14 days "
                    f"before, {t['n_after']} after).")
        else:
            test = f"Test not run: {t['message']}."
        return ui.div(verdict, tiles, _more(_p(stable), _faq([
            ("How do we know it really improved?",
             "We compare the 14 days before the action with the days after it. 'Improved' means "
             "the drop is too large to be chance. " + test),
            ("What does 'steady' mean?",
             "After a fix the chart gets new limits from the days after the action. If no rule "
             "fires, the zone has settled at its new, better level. This is the Control step."),
        ])))

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
        ui.tags.style(STYLE),
        # Shiny skips hidden plots; opening a "More info..." toggle makes it look again.
        ui.tags.script("document.addEventListener('toggle', function (e) {"
                       " if (e.target.tagName === 'DETAILS' && e.target.open)"
                       " window.dispatchEvent(new Event('resize')); }, true);"),
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
    def date_range():
        df, _ = raw()
        if df is None:
            return None
        days = df["call_received"].dropna().dt.normalize()
        return days.min().date(), days.max().date()

    @reactive.calc
    def priority():
        return int(input.priority())

    @reactive.calc
    def target_min():
        return targets()["response"][priority()] / 60.0

    @reactive.calc
    def as_of():
        return pd.Timestamp(input.as_of()).normalize() if input.as_of() else None

    def set_as_of(value):
        """Move the shared as-of date (used by the Charts tab's own date and jump menu)."""
        ui.update_date("as_of", value=value, session=session)

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
        rng = date_range()
        if rng is None:
            return
        first, last = rng
        ui.update_date("as_of", value=last, min=first, max=last)
        ui.update_date("base_start", value=first, min=first, max=last)

    ctx = SimpleNamespace(targets=targets, stages=stages, upto=upto, why=why, priority=priority,
                          target_min=target_min, as_of=as_of, set_as_of=set_as_of,
                          date_range=date_range, base_start=base_start, base_days=base_days,
                          actions=actions, actions_upto=actions_upto, health=health)
    for _, mod_id, _, server_fn in TABS:
        server_fn(mod_id, ctx)
