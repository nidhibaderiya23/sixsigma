"""The How to use and About pages: static, opened from the header.

Every subsection is a closed dropdown (<details>) that shows only its title until clicked.
Team photos live in www/team/<first name>.jpg; a missing photo shows the initial instead.
"""

from __future__ import annotations

from pathlib import Path

from shiny import ui

TEAM_DIR = Path(__file__).resolve().parent / "www" / "team"

TEAM = [("Nidhi Baderiya", "MS MSE’27", "nidhi"),
        ("Zeba Haq", "MS CBE’27", "zeba"),
        ("Dhruv Bhandari", "MS MSE’27", "dhruv")]


def _drop(title, *body):
    """One closed dropdown: the title is a button; the body shows when it is opened."""
    return ui.tags.details(ui.tags.summary(ui.span(title, class_="rw-drop-title"),
                                           ui.span(class_="rw-drop-sign", **{"aria-hidden": "true"})),
                           ui.div(*body, class_="rw-drop-body"), class_="rw-drop")


def _group(label, *drops):
    return ui.tags.section(ui.h3(label, class_="rw-drop-group"), ui.div(*drops, class_="rw-drops"))


def _ul(*items):
    return ui.tags.ul(*[ui.tags.li(i) for i in items])


def _p(*parts):
    return ui.tags.p(*parts)


B = ui.tags.b


# ---- How to use ---------------------------------------------------------------------------------

def help_page():
    return ui.div(
        ui.div(ui.h2("How to use ERGent", class_="rw-page-title"),
               _p("Click a topic to open it."), class_="rw-info-head"),

        _group("Getting around",
               _drop("Choose a role",
                     _ul(ui.TagList(B("I'm a dispatcher"), ": the live board and the shift History."),
                         ui.TagList(B("I'm a supervisor"), ": control charts, zone health and actions."),
                         ui.TagList(B("Switch role"), " in the header goes back to the start page; ",
                                    B("How to use"), " and ", B("About"), " open from any page.")))),

        _group("Dispatcher",
               _drop("The live board",
                     _p("A call moves through five steps: ", B("1 Log a call"), " → ", B("2 Incoming calls"),
                        " → ", B("3 Dispatched"), " → ", B("4 En route"), " → ", B("5 Resolved"), "."),
                     _ul("Pick the zone and priority, then Add call.",
                         "Pick an ambulance and press Dispatch, then En route and On scene as the crew reports.",
                         "Only the next step's button is shown, so steps cannot be skipped.")),
               _drop("Clocks and colours",
                     _ul(ui.TagList(B("On track"), " (green circle): within the stage target."),
                         ui.TagList(B("Watch"), " (amber diamond): above 80% of the target."),
                         ui.TagList(B("Past target"), " (red square): the stage is late."),
                         "Priority 1 targets: dispatch 64 s, turnout 60 s, travel 8 min (9 min in total).")),
               _drop("Delay reasons",
                     _p("When a stage runs late, ERGent asks for a reason (for example traffic or crew not ready) "
                        "before the call moves on. On-time calls need no reason.")),
               _drop("Ambulances",
                     _p("Twelve ambulances in four columns: Available, Responding, On scene and Out of service. "
                        "Use ", B("Out of service"), " and ", B("Back in service"), " on a unit.")),
               _drop("Zone map",
                     _ul("Each Ithaca zone takes the colour of its worst open call.",
                         "Hover a zone for its open calls and free ambulances.",
                         "Click a zone to pick it in Log a call.")),
               _drop("Simulate a shift",
                     _p("Replay a real day of demo calls: choose ", B("Day"), ", ", B("Speed"), " (30x to 120x) and ",
                        B("Start"), ", then ", B("Simulate a shift"), ". Pause and Resume as needed; ", B("Reset"),
                        " clears the board.")),
               _drop("History",
                     _ul("The current and previous shift: calls, mean, standard deviation and on time.",
                         "Response time by zone: a red diamond is a zone slower than the city. Hover it for why.",
                         "Six tips for right now: Dispatch now, Rebalance, Cover, Route, Station alert and "
                         "Dispatcher load.")),
               _drop("Download calls",
                     _p("Saves every call on the board, with all its times, as a CSV file."))),

        _group("Supervisor",
               _drop("The control bar",
                     _p("Sets what both tabs show: ", B("Chart"), " (Daily chart or Every call), ", B("Zone"), ", ",
                        B("Priority"), ", ", B("Dataset"), ", ", B("As of"), " (the day you look from), ",
                        B("Chart period"), " (14, 28 or 42 days) and ", B("Targets"), ".")),
               _drop("Control chart",
                     _ul(ui.TagList(B("Daily chart"), ": each point is one day's average response for the zone, "
                                    "between its control limits. A red dot is a flagged day."),
                         ui.TagList(B("Every call"), ": each call in order, with the limits and the 9-minute "
                                    "target line."))),
               _drop("Statistics",
                     _p("Average, standard deviation, % on time and the number of zones flagged, for the chart "
                        "period and all zones.")),
               _drop("Zone map",
                     _ul("Each zone is coloured by its health: on track, worth a look or act.",
                         "Hover a zone for the reasons; click it to chart that zone.")),
               _drop("Delay by stage",
                     _p("For each zone, the share of minutes over target that comes from dispatch, crew turnout "
                        "and travel. The biggest part is where to look first. Hover a bar for its numbers.")),
               _drop("Capability",
                     _p("A plain verdict per zone: Very reliable, Reliable, Just meets the standard or Below the "
                        "standard, with about how many calls in 100 arrive within the target. ",
                        B("Can't judge yet"), " means the zone's times changed in the period; ",
                        B("Not enough calls"), " means fewer than 30.")),
               _drop("Zone comparison",
                     _p("Click the ", B("Zone comparison"), " button to see whether the zones really differ, "
                        "or whether the gap could be chance.")),
               _drop("Actions",
                     _ul(ui.TagList(B("Suggested actions"), ": a fix for each problem found, with its evidence "
                                    "and an estimate."),
                         ui.TagList(B("Log this action"), ": records the fix and its start date in ",
                                    B("Actions taken"), "."),
                         ui.TagList(B("Before and after"), " and ", B("Result"), ": Improved, No clear change yet, "
                                    "Got worse or Not enough data."),
                         "A slip-back alert appears if a fixed zone gets worse again.")),
               _drop("More info",
                     _p("Every card has a ", B("More info"), " toggle with a short explanation and the numbers "
                        "behind it."))),

        _group("The statistics in plain words",
               _drop("Percentiles and on time",
                     _p("The 90th percentile is the time 9 in 10 calls beat; % on time is the share within the "
                        "target. Ten calls can average 9.2 min while the 90th percentile is 12.8 min, so ERGent "
                        "never relies on the average alone.")),
               _drop("Why log minutes",
                     _p("Response times are skewed: most calls are quick, a few are very long. The charts and tests "
                        "work on the log of the minutes, which is close to normal, and show the results back in "
                        "minutes.")),
               _drop("Daily control chart (X̄-S)",
                     _ul("Center line: the mean of the daily averages in the chart period.",
                         "Control limits: the center ± 3 standard deviations of those daily averages.",
                         "The lower chart (S) watches the spread of calls within each day.")),
               _drop("Flag rules and zone health",
                     _ul("R1: a day beyond 3σ. R2: 2 of 3 beyond 2σ. R3: 4 of 5 beyond 1σ. "
                         "R4: 8 in a row on one side. R5: 6 in a row rising.",
                         "A chart signal needs R1, or two different rules, in the last 7 days.",
                         "Red: a chart signal and a 7-day 90th percentile over the target. Amber: one of the two. "
                         "Green: neither.")),
               _drop("Capability (Ppk and Cpk)",
                     _ul(ui.TagList(B("Ppk"), " = (target − average) ÷ (3 × overall spread), on log "
                                    "minutes. It includes day-to-day drift, so it shows how the zone is doing now."),
                         ui.TagList(B("Cpk"), " uses only the spread within each day: what the zone could do if "
                                    "it stayed steady. Cpk well above Ppk means the zone drifts."),
                         "Ppk 1.0 ≈ 99.9 in 100 calls on time; 0.43 ≈ 90 in 100 "
                         "(calls in 100 = Φ(3 × Ppk)).",
                         "Verdicts: Very reliable ≥ 99, Reliable ≥ 95, Just meets the standard ≥ 90, "
                         "Below the standard < 90 calls in 100.")),
               _drop("Zone comparison and before and after",
                     _ul(ui.TagList(B("Zone comparison"), ": a one-way ANOVA on log minutes across the zones."),
                         ui.TagList(B("Before and after"), ": Welch's t-test on log minutes, before and after the "
                                    "action's start date. A better time shows a change, not its cause."))),
               _drop("Targets",
                     _p("Priority 1: 9 minutes for 90% of calls (NFPA 1710). Priorities 2 and 3: 15 and 20 minutes "
                        "(our assumptions). Change them with ", B("Targets"), "."))),

        _group("Questions",
               _drop("Is this real data?",
                     _p("No. All calls are synthetic, made by a seeded script, and the zones are illustrative "
                        "areas of Ithaca, not official EMS districts.")),
               _drop("Why is the daily chart quiet while the map is amber?",
                     _p("The limits come from the chart period, so a long problem inside it widens its own limits. "
                        "The zone map, Capability and Zone comparison still catch it.")),
               _drop("Does ERGent decide what to do?",
                     _p("No. It flags and suggests, with the evidence. Qualified staff decide."))),
        class_="rw-help rw-info")


# ---- About ------------------------------------------------------------------------------------------

def _member(name, line, key):
    photo = TEAM_DIR / f"{key}.jpg"
    face = (ui.tags.img(src=f"team/{key}.jpg", alt=name, class_="rw-team-photo") if photo.exists()
            else ui.span(name[0], class_="rw-team-photo rw-team-initial", **{"aria-hidden": "true"}))
    return ui.div(face, ui.div(name, class_="rw-team-name"), ui.div(line, class_="rw-team-line"),
                  class_="rw-team-card")


def about_page():
    return ui.div(
        ui.div(ui.h2("About ERGent", class_="rw-page-title"),
               _p("Click a section to open it."), class_="rw-info-head"),
        ui.div(
            _drop("About the website",
                  _p("ERGent helps Ithaca's 911 EMS dispatch center see which zone is slow, which stage of the "
                     "call causes it, since when, and whether a fix worked."),
                  _p("A monthly average can look fine while some patients wait far too long. ERGent tracks every "
                     "call and every zone, every day, so those calls are no longer hidden.")),
            _drop("How it works",
                  _ul("Every call is timed from the moment it is received to when the ambulance reaches the scene.",
                      "Each response is split into dispatch, crew turnout and travel.",
                      "Daily control charts and capability show which zones are slow, and since when.",
                      "ERGent suggests a fix with its evidence, then checks whether it worked.")),
            ui.tags.section(ui.h3("About us", class_="rw-panel-title"),
                            ui.div(*[_member(*m) for m in TEAM], class_="rw-team"),
                            class_="rw-panel"),
            class_="rw-drops"),
        class_="rw-about rw-info")
