"""ERGent (Team ERG): a Shiny for Python dashboard for a 911 EMS dispatch center.

Start page -> pick a role -> the dispatcher board or the supervisor screens.
Run it with ./testme.sh (or `python -m shiny run app.py --port 8000` from this folder).

Every statistic comes from qc.py; this file only wires the screens together.
Each browser session has its own live board (state lives inside server()).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shiny import App, reactive, render, ui  # noqa: E402

import qc  # noqa: E402  (all numbers on screen come from qc.py)
from ui_dispatcher import (chip, dispatcher_server, dispatcher_ui, icon,  # noqa: E402
                           sim_controls_ui)
from ui_supervisor import supervisor_server, supervisor_ui  # noqa: E402
import zonemap  # noqa: E402

HERE = Path(__file__).resolve().parent

#: Shown in the header; each saved version of the app sets its own.
VERSION = "v7"
WWW = HERE / "www"

FONTS = "https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap"

# A small pulse icon as the browser-tab icon (inline, so there is no file to serve).
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
           "fill='none' stroke='%23145ec1' stroke-width='2.4' stroke-linecap='round' "
           "stroke-linejoin='round'%3E%3Cpolyline points='22 12 18 12 15 21 9 3 6 12 2 12'/%3E%3C/svg%3E")


def role_button(input_id: str, icon_name: str, name: str, description: str):
    return ui.input_action_button(
        input_id,
        ui.TagList(ui.span(icon(icon_name), class_="rw-role-icon"),
                   ui.span(name, class_="rw-role-name"),
                   ui.span(description, class_="rw-role-desc"),
                   ui.span(icon("arrow"), class_="rw-role-go")),
        class_="rw-role")


start_page = ui.div(
    ui.div(
        ui.h1("ERGent"),
        ui.div(f"Team ERG \u00b7 {qc.CITY} EMS", class_="rw-hero-sub"),
        ui.div(
            role_button("pick_dispatcher", "headset", "I'm a dispatcher", "Work the live board."),
            role_button("pick_supervisor", "chart", "I'm a supervisor", "See which zone needs attention."),
            class_="rw-roles"),
        class_="rw-hero"))

header = ui.div(
    ui.div(icon("pulse"), class_="rw-logo"),
    ui.div(ui.div("ERGent", class_="rw-brand-name"),
           ui.div(f"Team ERG \u00b7 {qc.CITY} EMS dispatch \u00b7 {VERSION}", class_="rw-brand-sub")),
    ui.output_ui("header_chips"),
    ui.div(
        # the simulation controls live in the dispatcher module's namespace ("dispatcher")
        ui.panel_conditional("input.page === 'dispatcher'", sim_controls_ui("dispatcher")),
        ui.panel_conditional("input.page !== 'start'",
                             ui.input_action_link("switch_role", "Switch role", class_="rw-linkbtn")),
        class_="rw-header-end"),
    class_="rw-header")

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        ui.tags.link(rel="stylesheet", href=FONTS),
        ui.tags.link(rel="icon", href=FAVICON),
        ui.include_css(WWW / "rw.css", method="inline"),
        ui.include_js(WWW / "rw.js", method="inline"),
        zonemap.head()),
    ui.div(
        header,
        ui.navset_hidden(
            ui.nav_panel(None, start_page, value="start"),
            ui.nav_panel(None, dispatcher_ui("dispatcher"), value="dispatcher"),
            ui.nav_panel(None, supervisor_ui("supervisor"), value="supervisor"),
            id="page", selected="start"),
        class_="rw-shell"),
    title="ERGent")


def server(input, output, session):
    role = reactive.Value(None)        # None on the start page, then "dispatcher" or "supervisor"

    @reactive.calc
    def dispatcher_active():
        return role() == "dispatcher"

    mode = dispatcher_server("dispatcher", active=dispatcher_active)
    supervisor_server("supervisor")

    def go(name):
        role.set(name)
        ui.update_navset("page", selected=name)

    @reactive.effect
    @reactive.event(input.pick_dispatcher)
    def _pick_dispatcher():
        go("dispatcher")

    @reactive.effect
    @reactive.event(input.pick_supervisor)
    def _pick_supervisor():
        go("supervisor")

    @reactive.effect
    @reactive.event(input.switch_role)
    def _switch_role():
        go("start")

    @render.ui
    def header_chips():
        current = role()
        if current == "dispatcher":
            live = mode() == "LIVE 1x"          # green only for the real-time clock
            return ui.div(chip("Dispatcher", None),
                          chip(mode(), "green" if live else "amber"),
                          class_="rw-header-chips")
        if current == "supervisor":
            return ui.div(chip("Supervisor", None), chip("Synthetic data", "grey"),
                          class_="rw-header-chips")
        return None


# Posit Connect serves files in www/ next to this file; the CSS and JS are also inlined above.
app = App(app_ui, server, static_assets=WWW)
