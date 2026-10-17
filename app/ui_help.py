"""The How to use and About pages: static Shiny UI only, no inputs, outputs or server logic.

Styles live in www/help.css, scoped under .rw-help and .rw-about. The statistical statements
follow the docstrings in qc.py and docs/manual/04-statistics-explained.md.
"""

from __future__ import annotations

import re

from shiny import ui

# ---- small building blocks ------------------------------------------------------------------

_ICONS = {
    "headset": ('<path d="M3 18v-6a9 9 0 0 1 18 0v6"/>'
                '<path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1'
                'a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>'),
    "chart": ('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>'
              '<line x1="6" y1="20" x2="6" y2="14"/>'),
    "swap": ('<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
             '<polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'),
}


def _icon(name: str):
    return ui.span(ui.HTML(
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
        + _ICONS[name] + "</svg>"), class_="rw-help-icon")


def _rich(text: str):
    """Plain text with **bold** spans (used for the app's own names of things)."""
    parts = re.split(r"\*\*(.+?)\*\*", text)
    return ui.TagList(*[ui.tags.strong(p) if i % 2 else p for i, p in enumerate(parts) if p])


def _p(text: str, cls: str | None = None):
    return ui.p(_rich(text), class_=cls)


def _shape(tone: str):
    """The status shape: green circle, amber diamond, red square, grey hollow circle."""
    return ui.span(class_="rw-dot", **{"data-tone": tone, "aria-hidden": "true"})


def _legend(tone: str, text: str):
    """One legend row: the status shape, then the words (one flex item)."""
    return ui.tags.li(_shape(tone), ui.span(_rich(text)))


def _chip(tone: str, label: str):
    return ui.span(_shape(tone), label, class_="rw-chip")


def _card(title: str, *body, kicker: str | None = None, icon: str | None = None,
          wide: bool = False, level: str = "h4"):
    head = ui.div(
        _icon(icon) if icon else None,
        ui.div(ui.div(kicker, class_="rw-help-kicker") if kicker else None,
               getattr(ui.tags, level)(title, class_="rw-help-card-title")),
        class_="rw-help-card-head")
    cls = "rw-card rw-help-card" + (" rw-help-wide" if wide else "")
    return ui.div(head, *body, class_=cls)


def _steps(*items, cls: str = "rw-help-steps"):
    """A numbered list for things that really are a sequence."""
    return ui.tags.ol(*[ui.tags.li(_rich(t)) for t in items], class_=cls)


def _bullets(*items):
    return ui.tags.ul(*[ui.tags.li(_rich(t)) for t in items], class_="rw-help-bullets")


def _terms(*pairs):
    """A definition list: (term, description) pairs."""
    rows = []
    for term, desc in pairs:
        rows += [ui.tags.dt(term), ui.tags.dd(_rich(desc))]
    return ui.tags.dl(*rows, class_="rw-help-terms")


def _note(text: str):
    return ui.div(_rich(text), class_="rw-help-note")


def _section(sid: str, kicker: str, title: str, intro: str | None, *content):
    return ui.tags.section(
        ui.div(ui.div(kicker, class_="rw-help-kicker"),
               ui.h3(title, id=sid, class_="rw-help-section-title"),
               _p(intro, "rw-help-intro") if intro else None,
               class_="rw-help-section-head"),
        *content,
        class_="rw-help-section", **{"aria-labelledby": sid})


def _grid(*cards, cls: str = "rw-help-grid"):
    return ui.div(*cards, class_=cls)


def _page_head(kicker: str, title: str, lead: str, toc=None):
    return ui.div(
        ui.div(kicker, class_="rw-help-kicker"),
        ui.h2(title, class_="rw-page-title"),
        _p(lead, "rw-help-lead"),
        toc,
        class_="rw-help-head")


def _toc(label: str, items):
    return ui.tags.nav(
        ui.div("On this page", class_="rw-help-kicker"),
        ui.tags.ul(*[ui.tags.li(ui.tags.a(text, href=f"#{sid}")) for sid, text in items]),
        class_="rw-help-toc", **{"aria-label": label})


# ---- How to use ------------------------------------------------------------------------------

_HELP_TOC = [
    ("help-roles", "Pick your role"),
    ("help-board", "Dispatcher: Live board"),
    ("help-history", "Dispatcher: History"),
    ("help-charts", "Supervisor: Charts"),
    ("help-actions", "Supervisor: Actions"),
    ("help-colours", "Reading the colours"),
    ("help-stats", "The statistics"),
    ("help-faq", "Questions"),
]


def _roles():
    return _section(
        "help-roles", "Start", "Pick your role",
        "ERGent has two views. Choose one on the start page.",
        _grid(
            _card("I'm a dispatcher",
                  _p("Work the calls happening now. You get two tabs: **Live board** for open calls, "
                     "and **History** for the current and previous shift."),
                  kicker="Dispatcher", icon="headset"),
            _card("I'm a supervisor",
                  _p("See which zone needs attention and why. **Charts** shows the zone and the slow "
                     "stage. **Actions** suggests fixes and checks whether they worked."),
                  kicker="Supervisor", icon="chart"),
            _card("Switch role",
                  _p("Click **Switch role** in the header at any time to go back and pick the other "
                     "view."),
                  kicker="Any time", icon="swap"),
        ))


def _call_step(n: int, title: str, text: str):
    return ui.tags.li(
        ui.div(ui.span(str(n), class_="rw-step", **{"aria-hidden": "true"}),
               ui.h4(title, class_="rw-help-card-title"), class_="rw-help-flow-head"),
        _p(text),
        class_="rw-card rw-help-flow-step")


def _board():
    return _section(
        "help-board", "Dispatcher", "The live board",
        "Every call moves through five numbered cards, in order. Only the next valid button is "
        "shown, so a call cannot skip a step. Times come from the board clock; you never type one.",
        ui.tags.ol(
            _call_step(1, "Log a call", "Choose the zone and the priority, then click **Add call**."),
            _call_step(2, "Incoming calls", "Pick an available ambulance on the row and click "
                       "**Dispatch**. Ambulances from the call's own zone come first."),
            _call_step(3, "Dispatched", "The crew is getting moving. Click **En route** when it "
                       "leaves."),
            _call_step(4, "En route", "The ambulance is on the road. Click **On scene** when it "
                       "arrives."),
            _call_step(5, "Resolved", "The call reached the scene and shows its final response "
                       "time. A call you logged has **Clear**, which frees its ambulance."),
            class_="rw-help-flow", **{"aria-label": "The five steps of a call"}),
        _grid(
            _card("Clocks",
                  _p("Every open call has a running clock with a target."),
                  ui.tags.ul(
                      _legend("green", ("**On track:** under 80% of the stage "
                                                        "target.")),
                      _legend("amber", ("**Watch:** past 80% of the target. The "
                                                        "clock becomes a yellow plate.")),
                      _legend("red", ("**Past target:** the stage is late. The "
                                                      "clock becomes a red plate.")),
                      class_="rw-help-legend"),
                  _p("Priority 1 targets: waiting 1:04, turnout 1:00, travel 8:00, total 9:00.",
                     "rw-help-meta")),
            _card("A reason only when late",
                  _p("If a stage ran past its target, ERGent asks **Why was this late?** before it "
                     "records your press. Pick one of six reasons and click **Save reason and "
                     "continue**."),
                  _p("The time you pressed the button is kept. A stage on time never asks.")),
            _card("Ambulances",
                  _p("All 12 ambulances, in four columns: **Available**, **Responding**, **On "
                     "scene** and **Out of service**."),
                  _p("Click **Out of service** after a breakdown, and **Back in service** when the "
                     "ambulance is ready again.")),
            _card("Zone map",
                  _p("The six Ithaca zones, A to F. A zone's colour is its worst open call."),
                  _bullets("**Hover** a zone for its open calls and free ambulances.",
                           "**Click** a zone to pick it in **Log a call**."),
                  _p("The zone outlines are illustrative, not official EMS districts.",
                     "rw-help-meta")),
            _card("Simulate a shift",
                  _p("Replay one day of the demo data on a fast clock, from the header."),
                  _steps("Choose the **Day**.",
                         "Choose the **Speed**: 30x, 60x or 120x.",
                         "Choose the **Start** time.",
                         "Click **Simulate a shift**. It becomes **Pause**, then **Resume**."),
                  _p("Replayed calls are read-only. Click **Reset** to clear the board or to pick "
                     "another day or start time.", "rw-help-meta")),
            _card("Download calls",
                  _p("**Download calls (CSV)** saves this session's calls as a spreadsheet file you "
                     "can open in Excel.")),
        ))


def _history():
    return _section(
        "help-history", "Dispatcher", "History",
        "History looks back over the current shift and the one before it. A shift is eight hours: "
        "day 06:00 to 14:00, evening 14:00 to 22:00, night 22:00 to 06:00. During a simulation it "
        "follows the simulated clock.",
        _grid(
            _card("Shift numbers",
                  _p("**Calls**, **Mean**, **Standard deviation** and **On time** for the two "
                     "shifts, counting calls that reached the scene.")),
            _card("Response time by zone",
                  _p("Each zone is a box holding the middle half of its calls, with a diamond for "
                     "its average. Use the **Priority** menu to switch priority."),
                  _note("A **red diamond** is a zone slower than the city as a whole. **Hover** it "
                        "to read why: its typical time, the main stage and the top delay reason."),
                  _p("The number under each zone letter is its calls. Few calls means wide limits, "
                     "so read those zones with care.", "rw-help-meta")),
            _card("Suggested actions",
                  _p("Six live tips, each with a zone tag and its evidence."),
                  _terms(("Dispatch now", "A call has waited over 64 s. It names the nearest free "
                                          "ambulance."),
                         ("Rebalance", "A zone has no free ambulance and a neighbour has two or "
                                       "more. Move one to stand by."),
                         ("Cover", "An ambulance is out of service. Ask the neighbouring zones to "
                                   "cover."),
                         ("Route", "A zone's typical travel is at least 1.25 times the city's. "
                                   "Check the route."),
                         ("Station alert", "A zone's typical turnout is over 60 s. Alert that "
                                           "station."),
                         ("Dispatcher load", "The 90th percentile of dispatch time is over 64 s. "
                                             "Ask for a second dispatcher.")),
                  _p("Tips are for the dispatcher's judgment. The tool decides nothing on its own.",
                     "rw-help-meta"),
                  wide=True),
        ))


def _charts():
    return _section(
        "help-charts", "Supervisor", "Charts",
        "Charts answers two questions: which zone needs attention, and which part of the call is "
        "slow.",
        _grid(
            _card("The control bar",
                  _p("It sets what both tabs show."),
                  _terms(("Chart", "**Daily chart** or **Every call**."),
                         ("Zone", "The zone the control chart shows. You can also click it on the "
                                  "map."),
                         ("Priority", "1 Life-threatening, 2 Urgent or 3 Non-urgent. Each has its "
                                      "own target."),
                         ("Dataset", "Demo, Baseline or Messy file. Messy file shows the **Data "
                                     "quality** card, which lists the calls left out and why."),
                         ("As of", "The \"today\" for every card. Later calls are ignored."),
                         ("Chart period", "The last 14, 28 or 42 days. It also sets the control "
                                          "limits."),
                         ("Targets", "Opens a dialog to view and change the targets.")),
                  _note("**Try the demo story:** choose **Demo** and set **As of** to 2026-09-28, "
                        "the day before the fix. Then set it to 2026-10-12 to see the result."),
                  wide=True),
            _card("Control chart",
                  _p("**Daily chart:** each dot is one day's typical response time. The dashed lines "
                     "are the control limits, the zone's normal range. A **red dot** is a flagged "
                     "day. The amber line is the target; a green line marks a logged action. The "
                     "lower panel shows each day's spread."),
                  _p("**Every call:** single calls in the order they came in. A red dot is one "
                     "unusually slow call.")),
            _card("Statistics",
                  _p("The chart period for all zones: **Average**, **Standard deviation**, **On "
                     "time** (the goal is at least 90%) and **Zones flagged** (amber or red, out of "
                     "6).")),
            _card("Zone map",
                  _p("Each zone's colour is its health over the last 7 days."),
                  _bullets("**Hover** a zone for the reasons, such as its 90th percentile against "
                           "the target.",
                           "**Click** a zone to chart it.")),
            _card("Delay by stage",
                  _p("One bar per zone, split into dispatch, crew turnout and travel. Each part is "
                     "that stage's share of the zone's minutes over target."),
                  _p("The biggest part is the stage to fix first. Hover a part for its minutes and "
                     "median time.")),
            _card("Capability",
                  _p("One plain verdict per zone: can it meet the target reliably?"),
                  ui.div(_chip("green", "Very reliable"), _chip("green", "Reliable"),
                         _chip("amber", "Just meets the standard"),
                         _chip("red", "Below the standard"), class_="rw-help-chips"),
                  _p("**Can't judge yet** means the zone's times changed in the period. **Not "
                     "enough calls** means fewer than 30.", "rw-help-meta")),
            _card("Zone comparison",
                  _p("Click the **Zone comparison** button to ask whether the zones really differ. "
                     "The answer is one sentence, such as \"a gap this big is very unlikely to be "
                     "chance\".")),
            _card("More info",
                  _p("Most cards have a **More info** toggle. It explains the card in two or three "
                     "sentences and shows the test numbers behind it.")),
        ))


def _actions():
    return _section(
        "help-actions", "Supervisor", "Actions",
        "Actions answers the next two questions: what should we try, and did it work? It uses the "
        "dataset, priority and date set on Charts.",
        _grid(
            _card("From suggestion to result",
                  _steps("**Suggested actions** lists fixes. Each has a tag (such as Crew readiness "
                         "or Routes), a zone, the evidence and an estimate of the on-time share if "
                         "that stage were as fast as the city's typical call. The estimate is a best "
                         "case.",
                         "Click **Log this action**. The form is filled in: zone, stage, start "
                         "date, what was done and owner. Edit it and click **Save action**.",
                         "**Actions taken** is the log. Click **Log an action** to add one by hand.",
                         "**Before and after** shows the zone's daily chart, with the action as a "
                         "green line.",
                         "**Result**: choose the action and read the verdict. The table compares "
                         "the 14 days before with up to 14 days after."),
                  wide=True),
            _card("Result verdicts",
                  ui.tags.ul(
                      _legend("green", ("**Improved:** the drop is too large to be "
                                                        "chance.")),
                      _legend("grey", ("**No clear change yet:** the change could "
                                                       "be chance.")),
                      _legend("red", ("**Got worse:** slower, by more than "
                                                      "chance.")),
                      _legend("grey", ("**Not enough data:** too few calls after "
                                                       "the action.")),
                      class_="rw-help-legend")),
            _card("Slip-back alerts",
                  _p("Appears only when a zone drifts back to its old problem after a logged fix. "
                     "That zone stays at least amber on the map.")),
            _card("Who decides",
                  _p("Every suggestion is for review by qualified staff. A better time after a fix "
                     "does not prove the fix caused it; staff judge the cause.")),
        ))


def _colours():
    return _section(
        "help-colours", "Status", "Reading the colours",
        "Status is always a colour and a shape, like a road sign, plus a word. Safety orange is "
        "only for buttons and never means a status.",
        _grid(
            _card("On track",
                  ui.div(_shape("green"), ui.span("Green circle"), class_="rw-help-swatch"),
                  _p("Nothing to do. A clock under 80% of its target, or a zone with no warning "
                     "sign.")),
            _card("Watch, or Worth a look",
                  ui.div(_shape("amber"), ui.span("Amber diamond"), class_="rw-help-swatch"),
                  _p("Take a look. A clock past 80% of its target, or a zone with one warning "
                     "sign.")),
            _card("Past target, or Act now",
                  ui.div(_shape("red"), ui.span("Red square"), class_="rw-help-swatch"),
                  _p("Act. A clock past its target, or a zone with both warning signs.")),
            _card("Not enough data",
                  ui.div(_shape("grey"), ui.span("Hollow grey circle"), class_="rw-help-swatch"),
                  _p("Too few calls to judge.")),
            cls="rw-help-grid rw-help-grid-4"))


def _stat(title: str, *paras: str, wide: bool = False):
    return _card(title, *[_p(t) for t in paras], wide=wide)


def _capability_card():
    return _card(
        "Capability",
        ui.div(
            ui.div(
                ui.h5("What it asks"),
                _p("Can this zone reliably meet its target, 9 minutes for priority 1? It looks at "
                   "the slow tail, not just the average."),
                ui.h5("Ppk: what the zone is doing now"),
                ui.div("Ppk = (upper limit − average) / (3 × overall spread)",
                       class_="rw-help-formula"),
                _p("It is computed on log minutes against ln(9 min). The overall spread includes "
                   "the drift from day to day, so Ppk describes the zone as it is."),
                ui.h5("Cpk: what the zone could do if steady"),
                _p("Cpk uses only the spread within each day. A big gap between Cpk and Ppk means "
                   "the zone drifts from day to day."),
                class_="rw-help-col"),
            ui.div(
                ui.h5("Reading the numbers"),
                _p("The app turns Ppk into \"about N in 100 calls within 9 min\" with "
                   "Φ(3 × Ppk), where Φ is the standard normal curve."),
                ui.tags.table(
                    ui.tags.caption("Ppk and the expected share of calls within the target"),
                    ui.tags.thead(ui.tags.tr(ui.tags.th("Ppk", scope="col"),
                                             ui.tags.th("Calls within target", scope="col"))),
                    ui.tags.tbody(*[ui.tags.tr(ui.tags.td(a), ui.tags.td(b)) for a, b in [
                        ("0.33", "83.9%"), ("0.43", "90.1%, the standard's line"),
                        ("0.50", "93.3%"), ("0.67", "97.8%"), ("1.00", "99.9%")]]),
                    class_="rw-help-table"),
                ui.h5("Verdicts"),
                ui.tags.ul(
                    ui.tags.li(_chip("green", "Very reliable"), ui.span("99 in 100 or more")),
                    ui.tags.li(_chip("green", "Reliable"), ui.span("95 in 100 or more")),
                    ui.tags.li(_chip("amber", "Just meets the standard"),
                               ui.span("90 in 100 or more")),
                    ui.tags.li(_chip("red", "Below the standard"), ui.span("under 90 in 100")),
                    class_="rw-help-verdicts"),
                class_="rw-help-col"),
            class_="rw-help-cols"),
        _note("**When there is no score.** Capability is hidden when the zone's times changed in "
              "the period (**Can't judge yet**), or when it has fewer than 30 calls (**Not enough "
              "calls**). In the demo data on Sep 28, Zone D gets about 89 in 100 calls within 9 "
              "min: **Below the standard**."),
        wide=True)


def _stats():
    return _section(
        "help-stats", "Reference", "The statistics in plain words",
        "Every number comes from one set of plain, tested functions. Times are shown in minutes.",
        _grid(
            _stat("Percentiles and % on time",
                  "The 90th percentile is the time that 9 in 10 calls beat. **On time** is the "
                  "share of calls within the target.",
                  "ERGent leads with these because the mean hides the slow tail. Ten calls can "
                  "average 9.2 min while their 90th percentile is 12.8 min and only 6 were on "
                  "time."),
            _stat("Why log minutes",
                  "Response times are skewed: most calls are quick and a few are very slow. Charts, "
                  "capability and tests run on the logarithm of the minutes, which pulls in that "
                  "tail.",
                  "Results are turned back into minutes, so a typical time is a geometric "
                  "average."),
            _stat("The daily X̄-S chart",
                  "Each point is one zone-day: the mean of that day's log minutes. The center is "
                  "the mean of the daily means in the chart period. The limits are the center "
                  "± 3 standard deviations of those daily means.",
                  "The S chart below watches the spread within each day. The limits show what is "
                  "normal for the zone; the target is a separate line."),
            _card("The flag rules",
                  _terms(("R1", "One day beyond 3 sigma."),
                         ("R2", "2 of the last 3 days beyond 2 sigma, on the same side."),
                         ("R3", "4 of the last 5 days beyond 1 sigma, on the same side."),
                         ("R4", "8 days in a row on the same side of the center."),
                         ("R5", "6 days in a row steadily rising, or falling.")),
                  _p("Only the slow side is an alarm; a fast day says \"check the data\". For zone "
                     "health, a chart signal needs R1, or two different rules, in the last 7 "
                     "days.")),
            _stat("Zone health",
                  "Each zone looks at the last 7 days. **Red** means a chart signal and a 7-day "
                  "90th percentile over the target. **Amber** means one of the two. **Green** "
                  "means neither.",
                  "A zone slipping back after a logged fix is at least amber."),
            _stat("Delay by stage",
                  "For each call, a stage's excess is its time over that stage's target, never "
                  "below zero. A stage's share is its total excess divided by the zone's total "
                  "over all three stages.",
                  "A stage that stays under its target has no share, even if it is slower than "
                  "the others."),
            _capability_card(),
            _stat("Zone comparison",
                  "A one-way ANOVA on the log times of each zone's calls asks whether the zones "
                  "really differ, or the gaps could be chance.",
                  "When p is below 0.05 the card says yes: \"a gap this big is very unlikely to be "
                  "chance\". It says that zones differ, not which one; the typical times show "
                  "that."),
            _stat("Before and after",
                  "Welch's t-test compares log times in the 14 days before an action with up to 14 "
                  "days from the action date on. It does not assume both periods have the same "
                  "spread.",
                  "**Improved** means a one-sided p below 0.05. It shows an apparent change, not "
                  "its cause."),
            _stat("Targets",
                  "Priority 1 follows NFPA 1710: 9 minutes from dispatch to arrival, met by at "
                  "least 90% of calls, so the 90th percentile should be at or under 9 min.",
                  "The 15 and 20 minute targets for priorities 2 and 3 are the team's own "
                  "assumptions. A supervisor can change every target with **Targets**."),
        ))


def _faq():
    qa = [
        ("Is this real data?",
         "No. All the data is synthetic, made by a script, with no real patients, addresses or "
         "names. The zones are illustrative areas of Ithaca, not official EMS districts."),
        ("Why is the daily chart quiet while the map is amber?",
         "The control limits come from the chart period. A problem that lasts through most of it "
         "widens the limits and can hide itself. The Zone map, Delay by stage, Capability and Zone "
         "comparison still catch it. In the demo data on Sep 28, Zone D shows no red dots, yet its "
         "90th percentile is 10.2 min and turnout causes 92% of its minutes over target."),
        ("Does the tool decide?",
         "No. ERGent flags and suggests. Qualified staff make every decision."),
        ("Is a control limit the same as the target?",
         "No. A control limit comes from the zone's own history and shows what is normal. The "
         "target comes from a standard and shows what is required. A zone can be normal and still "
         "miss the target."),
        ("Why does Capability say \"Can't judge yet\"?",
         "The zone's times changed during the period, so a reliability score would mislead. Find "
         "the cause first, then judge again."),
        ("Why is History empty?",
         "The demo data is from the past, so History starts empty in real time. It fills when you "
         "log calls or run **Simulate a shift**."),
    ]
    return _section(
        "help-faq", "Questions", "Frequently asked questions", None,
        _grid(*[_card(q, _p(a)) for q, a in qa], cls="rw-help-grid rw-help-grid-2"))


def help_page():
    """The How to use page: a short intro, then one section per part of the app."""
    return ui.div(
        _page_head(
            "Guide", "How to use ERGent",
            "ERGent shows where, why and since when ambulances run late in Ithaca. The dispatcher "
            "works the live calls; the supervisor finds the slow zone and checks each fix. This "
            "page walks through every part.",
            _toc("How to use, sections", _HELP_TOC)),
        _roles(), _board(), _history(), _charts(), _actions(), _colours(), _stats(), _faq(),
        class_="rw-help")


# ---- About --------------------------------------------------------------------------------------

_DMAIC = [
    ("D", "Define", "The targets: 9 minutes for priority 1, from NFPA 1710."),
    ("M", "Measure", "Each call's stages, with bad records left out and listed."),
    ("A", "Analyze", "Control chart, Delay by stage and Zone comparison."),
    ("I", "Improve", "Suggested actions and Log this action."),
    ("C", "Control", "Before and after, Result and slip-back alerts."),
]

_TEAM = ["Nidhi Baderiya", "Zeba Haq", "Dhruv Bhandari"]


def _member(name: str):
    return ui.div(
        ui.span(name[0], class_="rw-about-avatar", **{"aria-hidden": "true"}),
        ui.div(ui.h4(name, class_="rw-help-card-title"),
               ui.p("Role and program: to be added", class_="rw-help-meta")),
        class_="rw-card rw-about-member")


def about_page():
    """The About page: what ERGent is, and who built it."""
    return ui.div(
        _page_head(
            "About", "About ERGent",
            "A quality-control tool for 911 EMS dispatch in Ithaca, NY, built by Team ERG at the "
            "Cornell Six Sigma Hackathon."),
        ui.tags.section(
            ui.div(ui.div("The website", class_="rw-help-kicker"),
                   ui.h3("About the website", id="about-site", class_="rw-help-section-title"),
                   class_="rw-help-section-head"),
            _grid(
                _card("What it is",
                      _p("ERGent follows each emergency call from the moment it is received until "
                         "an ambulance is on scene, and measures every stage on the way.")),
                _card("Who it is for",
                      _p("The dispatcher who works the live calls, and the EMS operations "
                         "supervisor who looks for patterns and decides what to fix.")),
                _card("The problem",
                      _p("A monthly average hides where, why and since when ambulances run late. "
                         "Ten calls can average 9.2 minutes, close to a 9-minute target, while only "
                         "6 of them were on time.")),
                _card("What it shows",
                      _p("Which zone is slow, which stage causes it (dispatch, crew turnout or "
                         "travel), since when, and whether a fix worked.")),
                _card("How it works",
                      _p("It follows the Six Sigma DMAIC cycle. Control charts show when a zone "
                         "changed; capability shows whether it can meet the target reliably; a "
                         "before-and-after test checks each fix."),
                      ui.tags.ol(*[ui.tags.li(ui.span(letter, class_="rw-about-plate",
                                                      **{"aria-hidden": "true"}),
                                              ui.div(ui.tags.strong(word), ui.span(text)))
                                   for letter, word, text in _DMAIC],
                                 class_="rw-about-dmaic"),
                      _note("**Good to know.** All the data is synthetic, and the zones are "
                            "illustrative areas of Ithaca. ERGent flags and suggests; qualified "
                            "staff decide."),
                      wide=True),
                cls="rw-help-grid rw-help-grid-4"),
            class_="rw-help-section", **{"aria-labelledby": "about-site"}),
        ui.tags.section(
            ui.div(ui.div("The team", class_="rw-help-kicker"),
                   ui.h3("About us", id="about-us", class_="rw-help-section-title"),
                   _p("We are Team ERG, students in Cornell's SYSEN 5300 Six Sigma course. We built "
                      "ERGent at the Cornell Six Sigma Hackathon, Oct 16–17, 2026.",
                      "rw-help-intro"),
                   class_="rw-help-section-head"),
            ui.div(*[_member(n) for n in _TEAM], class_="rw-help-grid rw-about-team"),
            ui.p("Thank you to the SYSEN 5300 course staff for their teaching and support.",
                 class_="rw-about-thanks"),
            class_="rw-help-section", **{"aria-labelledby": "about-us"}),
        class_="rw-about")
