# ERGent (version 3): product context

## What it is

ERGent is Team ERG's quality-control tool for the 911 EMS dispatch center of Ithaca, NY
(Cornell Six Sigma Hackathon). It is a Shiny for Python app with two roles, picked on a start
page:

- **Dispatcher**: a live board. Log a call; incoming, dispatched, en route and resolved lists
  with running clocks; ambulance status columns; a live Leaflet zone map of Ithaca; a shift
  replay ("Simulate a shift"). A History tab shows a box chart by zone and suggested actions.
- **Supervisor**: a Charts tab (control bar, daily X-bar and S control chart, statistics,
  zone map, delay by stage, zone comparison, capability verdicts) and an Actions tab
  (suggested actions, action log, before and after).

Every number comes from `app/qc.py` and is tested. The data is synthetic and labelled so.

## Who uses it, and where

- **Dispatchers** under time pressure, on a console, glancing at clocks and statuses.
- **Supervisors / an EMS medical director** reviewing response-time quality at a desk in
  daylight, and **classmates and a professor** who are not statistics experts, reading the
  screens on a **classroom projector** (about 1024 px wide) that washes out dark and
  low-contrast UIs.

Scene sentence: a quality reviewer in a bright office, and a class watching a washed-out
projector in a lit room. That forces a light interface with high-contrast ink.

## Mode

**Operate** for every screen (app UI). Scanability, familiar controls and the real usage scene
outrank expression; the brand lives in precise details.

## Brand commitments

- Name: **ERGent**, by Team ERG. Version label in the header: `v3`.
- Status colours mean status only: **green = on track, amber = watch, red = past target**.
  Never used for decoration or for data categories.
- Texts are approved by the team (short, professional). Do not reword; fix only obvious typos.

## Constraints

- Do not change `qc.py`, `simulator.py`, `zonemap.py`, `tests/`, `data/`, `docs/`, any Shiny
  input or output id, any feature, button or number.
- No new Python packages; external scripts only Leaflet (unpkg) and Google Fonts.
- WCAG AA contrast, visible focus, `prefers-reduced-motion` respected; works at 1440 px and at
  1024 px. Bootstrap parts (selects, modals, notifications, date picker) follow the theme.

## Anti-references

- Version 1's dark "command center" (near-black ground, glowing accents, uppercase tracked
  labels, coral primary).
- The generic SaaS dashboard: same-size floating cards, hero metrics, gradient accents.
- Costumes of clinical hardware: ECG grid paper, monitor bezels, red-cross emblems.

## Direction contract (v3, "Clinical light"; development only, never shipped to the page)

THESIS: a hospital-grade light console where the data reads like a clinical report: plain ink
for what is in range, a tinted flag for what is not. It refuses the dark command center and the
floating-card SaaS dashboard.

OWN-WORLD: cool grey canvas, white surfaces with hairline rules, one deep clinical teal for the
shell band, primary actions, selection and focus; Source Sans 3 with tabular figures; status
as tinted chips (dark green, amber or red ink on a pale fill of the same hue).

STORY: the dispatcher sees at a glance which call is past target; the supervisor and the class
see which zone needs attention, why, and whether the fix worked, without decoding a dark UI.

FIRST VIEWPORT: a full-width teal header band (white ERGent mark, role and clock chips, the
replay controls, Switch role); underline tabs on the canvas; then the work: on the dispatcher
board a joined "vitals strip" of five counts, then Log a call beside Incoming calls; on the
supervisor screen the filter bar, then the control chart beside Statistics and the zone map.

FORM: signature move "flagged like a lab report": running clocks, KPI numbers, verdict and
status chips carry a tinted flag only when out of range. Direction pinned by the brief, so no
roll ran. seed: none (unavailable)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the
verdict, DESIGN.md, and every shipping raster carrying its provenance.
