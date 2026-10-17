# ERGent v5 — "Cayuga Report"

The app set like a printed statistical quality report: warm paper, near-black ink, one
accent, sections that open on an ink rule instead of sitting in boxes. The supervisor
screens read like a data page; the dispatcher board keeps every control standard and
puts status where the eye already is (the dot, the clock, a washed row).

Mode: **Operate** (the supervisor side leans to Read). Physical scene: a supervisor at a
desk in office light, and this afternoon a lit classroom with a 1024 px projector; a light
paper ground projects cleanly and keeps the charts readable. Source of truth for every
value below: `app/www/rw.css` (`:root`), `app/charts.py` (constants at the top),
`app/www/zonemap.js` (reads the `--map-*` variables).

## Direction contract

- **THESIS** — The app is a statistical quality report you can operate. Each section opens on a
  2px ink rule with a serif heading. It refuses v1's dark command-centre dashboard of
  boxed cards.
- **OWN-WORLD** — Paper, ink and hairlines. One "Cayuga blue" accent, used only for data,
  selection, the primary action and focus. Source Serif 4 headings over Public Sans
  figures. Status colours are muted and appear only where they carry meaning.
- **STORY** — The supervisor sees which zone is out of control or below standard, and
  why, then logs an action and checks the before/after result. The dispatcher sees at
  once which open call is past target and dispatches a free unit.
- **FIRST VIEWPORT** — A masthead (pulse mark, serif wordmark, role chips, controls) sits
  over a 2px ink rule. Text tabs follow on a hairline, then the page. The supervisor
  page opens with a parameters band, then the control chart beside the statistics and
  map. The dispatcher page opens with the "Live board" title, a key-figures strip, then
  the numbered call stages.
- **FORM** — An editorial report frame around standard web controls: Bootstrap selects,
  buttons, tabs and modals. Code-led, so there is no comp. Seed: none (unavailable;
  the launcher was not run).
- **FINISH** — Unreviewed and undocumented is unfinished. This build ends with the finish
  review, the verdict and DESIGN.md. It ships no new rasters.

## Colour (Restrained: tinted neutrals + one accent)

| Token | Value | Role | Contrast on paper |
|---|---|---|---|
| `--paper` | `#f7f4ed` | page ground, chart ground (`charts.BG`) | — |
| `--paper-2` | `#eeeae1` | second neutral: parameters band, hover | — |
| `--paper-3` | `#e5dfd3` | pressed, datepicker today | — |
| `--ink` | `#1b1a17` | text, section rules, map zone outlines (`charts.FG`) | 15.8:1 |
| `--ink-2` | `#3a3732` | secondary strong text | 10.8:1 |
| `--muted` | `#615c54` | labels, captions, axis text (`charts.MUTED`) | 6.0:1 |
| `--hair` | `#dcd6ca` | hairline rules between rows and figures | decorative |
| `--hair-strong` | `#c4bcae` | tag and unit-tile borders | decorative |
| `--control` | `#827a6d` | input and button borders | 3.9:1 (3.4:1 on the red wash) |
| `--accent` | `#1e4f7a` | Cayuga blue: data series, active tab, primary button, links, focus ring (`charts.LINE`) | 7.8:1 |
| `--accent-hover` | `#163c5e` | hover / pressed primary | 10.4:1 |
| `--accent-tint` | `#dbe5ee` | text selection | — |

**Status:** green, amber and red mean on track, watch and past target. They are used for
status only.

| Status | Text tone (≥4.5:1) | Mark tone (dots, fills, ≥3:1) | Map fill (`--map-*`, at 0.38 opacity) |
|---|---|---|---|
| green | `#2e6b41` | `#3f8a57` | `#3f8a57` |
| amber | `#8a5a00` | `#b07a1c` | `#c9952f` |
| red | `#a3302a` | `#c0443c` | `#c0443c` |
| grey (no data) | — | `#8c877e` | `#8c877e` |

`--red-wash` `#f6e2dd` is the background of a **live** row that is past target, and of the
error notification. Amber rows only get the dot and the clock colour.

## Type

- **Display / headings:** Source Serif 4 (Google Fonts, variable `opsz` 8–60, weights
  400–700). Optical size is automatic, so the 96 px title uses the display cut and the
  21 px headings use the text cut. Weight 600, no italics. It was chosen over Newsreader
  and Fraunces (training-data defaults) because it has true optical sizes.
- **UI, numbers, labels, chart text:** Public Sans (variable, 400–700). It is the
  U.S. Web Design System's UI face, derived from Libre Franklin, so it carries the
  newspaper-grotesque tone of a data page and is built for public-service interfaces. It
  has real tabular figures. Libre Franklin was tried first, but its Google build has no
  `tnum`, so the running clocks would jitter.
- Every figure (clocks, key figures, counts, tables, chart text) uses
  `font-variant-numeric: tabular-nums lining-nums`.
- Reading prose (the zone-comparison answer and the "More info" bodies) is set in the serif
  at 15.5–19 px, with a 46–68ch measure.

| Role | Face | Size / weight |
|---|---|---|
| Start-page title | serif | 96 px / 600, line-height 0.95, −0.03em |
| Page title (`.rw-page-title`) | serif | 34 px / 600 |
| Role name (start page) | serif | 32 px / 600 |
| Masthead wordmark | serif | 27 px / 600 |
| Modal title | serif | 22 px / 600 |
| Section heading (`.rw-title`) | serif | 21 px / 600 |
| Answer sentence (`.rw-answer`) | serif | 19 px / 400 |
| More-info body | serif | 15.5 px / 400, line-height 1.6 |
| Key figure (`.rw-kpi-num`) | sans | 34 px (dispatcher), 30 px (history), 28 px (supervisor stats) / 600 |
| Running clock (`.rw-clock`) | sans | 23 px / 600, tabular |
| Body / UI | sans | 14 px / 400–600 |
| Row sub, labels | sans | 12.5–13 px / 500 |
| Tags, captions (`.rw-tag`, `.rw-cap`) | sans | 11.5 px / 500–600 |

Labels are sentence case. There is no uppercase tracking and no eyebrows.

## Space and shape

- A 4-based scale: `--s1`–`--s8` = 4, 8, 12, 16, 24, 32, 40, 56 px.
- Shell: max 1320 px, 32 px gutters (24 px under 1180 px, 16 px under 640 px).
- Column gap 40 px (32 px under 1180 px). Sections in a grid: 40 px apart vertically.
- Radius 3 px on controls, tags, tiles and modals. Sections and rows have no radius and no
  box.
- Depth: only overlays (modals, the date picker, notifications, the map tooltip) carry a
  soft offset shadow. There is no backdrop blur; Shiny's 2 px blur is switched off.

## Components

- **Masthead** (`.rw-header`): pulse mark in accent, serif wordmark and a muted subline,
  role chips, controls on the right, with a 2px ink rule below.
- **Tabs** (`.nav-pills`): text tabs on a hairline. The active tab is ink at 600 with a 2px
  accent underline.
- **Section** (`.rw-card`): a 2px ink top rule with a serif heading. A step number
  (`.rw-step`) is a bold accent figure. The count (`.rw-count`) is a plain tabular figure
  on the right.
- **Parameters band** (`.rw-card.rw-toolbar`): a `--paper-2` band with no rule. At 1440 px
  the six controls and Targets fit on one line, through fixed widths per control.
- **Key figures** (`.rw-kpis`, `.rw-stats`): numbers on hairlines, with an ink rule above,
  a hairline below and vertical hairlines between. The tile icons are hidden.
- **Rows** (`.rw-row`): ruled like a timetable, with a hairline under each row. Each row has
  a status dot, a title and a muted sub-line, buttons, and the clocks on the right.
  `[data-live][data-sev=red]` gets the red wash. On the supervisor side rows wrap instead
  of truncating.
- **Tags** (`.rw-tag`): an 11.5 px label on a filled `--paper-2` slip with no outline, so a
  label never reads as a button. Red and amber variants are outlined in their status colour.
  The unit tiles' "Out of service" / "Back in service" buttons keep the `--control` outline.
- **Chips** (`.rw-chip`): a 12 px label with a hairline box and an optional status dot. In
  capability rows the chip loses its box and reads as "● Just meets the standard".
- **Capability** (`.rw-verdicts`): a three-column subgrid (zone, verdict, sentence), so the
  verdict column is as wide as its longest label. This fixes v1's chip/sentence overlap.
- **Buttons:** primary = accent fill with paper text. Default = paper with a `--control`
  border, `--paper-2` on hover. Ghost (`.rw-btn-ghost`) = accent text that gains a border
  on hover. Every button is 36 px in a control row (32 px in the masthead).
- **Inputs:** paper ground with a `--control` border. On focus: accent border plus a 2px
  accent outline. The native unit picker gets the same chevron as Bootstrap's select.
- **More info** (`details.rw-moreinfo`): an accent summary with a drawn CSS chevron that
  rotates on open. The body is serif, with a hairline on the left.
- **Modals:** paper, 1px ink border, 2px ink rule under the serif title, footer on a hairline.
- **Notifications:** paper with a 1px border in accent (message), amber (warning) or red on
  the red wash (error).
- **Date picker:** paper dropdown with an ink border. The selected day is accent, today is
  `--paper-3`.
- **Focus:** a 2px accent outline at a 2px offset everywhere (6px on the start-page role
  buttons).
- **Motion:** 150–200 ms colour and border transitions, plus the role arrow nudging 4 px.
  `prefers-reduced-motion` switches off all transitions and Leaflet's zoom animation.

## Known limits

- The PNG charts (Control chart, Before and after) are images, so they draw in the
  server's font: Helvetica Neue on a Mac, DejaVu Sans on Posit Connect. Bundling the
  Public Sans TTF and registering it with `matplotlib.font_manager.fontManager.addfont()`
  would match the page; that was out of this version's scope.

## Responsive

- **≤1180 px (the 1024 projector):** narrower gutters. The ambulance status columns stack
  (Available first). The parameters band wraps to two lines. Three charts take the full
  width so their text stays legible: Delay by stage (capped at 720 px), the History box
  chart (capped at 820 px), and Before and after on the Actions tab.
- **≤992 px:** every two-column grid stacks, and key figures go two per row.
- **≤640 px:** phone layout. Rows wrap, the masthead controls go under the brand, and the
  capability rows put the sentence under the zone and verdict.

## Charts (matplotlib, `app/charts.py` — styling only)

- Ground `BG` is the page paper, so a chart sits on the page like a printed figure.
  The left spine is off, the bottom spine is `#8c8477`, and the grid is light (`#e2ddd2`).
- The data series is in the accent (`LINE` `#1e4f7a`). The center line and control limits
  are muted ink (limits dashed). The target (spec) stays amber (`#b07a1c`) because the copy
  names "the amber line". Flagged points are red (`#b8372f`) and the action line is
  green (`#2e6b41`).
- Delay by stage runs light to dark through the accent, in time order (processing
  `#a9bccf`, turnout `#5f83a8`, travel `#1e4f7a`), with a paper gap between segments. No
  status colour is used for categories.
- The box chart's boxes are `#ebe6dc` with a muted edge and an ink median.
- Chart titles are regular weight in ink, so the serif section heading leads; the box
  chart keeps its bold priority title. The green "action" label sits on a paper patch, so
  the limit and target lines never strike through it.
- The SVG charts use `svg.fonttype = "none"`, so the browser draws their text in Public
  Sans with tabular figures. The PNG charts fall back to Helvetica Neue / Arial (DejaVu Sans
  on Linux).
- Delay by stage is drawn 6.2 in wide and the box chart 8 in wide, so their text stays
  around 10 px or more when the SVG is scaled into a half column at 1024 px.

## Map (Leaflet, `app/www/zonemap.js` reads the CSS variables)

- Esri Light Gray canvas tiles (`--map-tiles: light`) with the reference labels on top.
- Zone outlines in ink (`--map-line`), fills from `--map-green`, `--map-amber`, `--map-red`
  and `--map-grey`.
- Zone letters (`.rw-zone-label`) are paper discs with an ink hairline, in the sans at 700.
- The tooltip (`.rw-map-tip`) is opaque paper with an ink border and a soft shadow, at most
  230 px wide. Leaflet's control corner sits above the tooltip pane, so the zoom buttons
  fade out while a tooltip is open (`.rw-leaflet:has(.leaflet-tooltip)`).
- The map's frame is a 1px box-shadow, not a border. `zonemap.js` refits only when
  `offsetWidth > 0`, and a border keeps that true while the map has no width.
