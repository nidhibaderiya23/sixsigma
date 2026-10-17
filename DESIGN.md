# DESIGN.md: ERGent v4, "Civic Ithaca"

A public-service identity, as if the City of Ithaca's emergency services had commissioned the
tool: a deep navy masthead, a warm-grey working area with white panels, and one safety orange.
Mode: **Operate**. The world lends type, palette, density and one signature move; the layout,
navigation and controls stay the standard ones a dispatcher or supervisor already knows.

Written from the built result. The source of truth for every value below is
`app/www/rw.css` (tokens on `:root`) and the constants at the top of `app/charts.py`.

## Direction

- **Thesis.** A civic instrument, not a command-center costume. It refuses the category default
  (near-black, neon accents, glowing edges) and the signage cliches (sirens, badges, Star of Life).
- **Scene.** A supervisor at a desk in daylight, a dispatcher at a console, and this afternoon a lit
  Cornell classroom watching a 1024 px projector. A light working area projects and prints far
  better than a dark one; the navy band carries the identity.
- **Own world.** US civic wayfinding and public-information design: navy street-name plates with a
  white keyline, the yellow diamond of a road warning sign, the USWDS heritage of Public Sans, the
  highway-sign lineage of Barlow.
- **Signature move: zone plates.** Every zone letter is a small navy street-name plate (white
  letter, white inner keyline): on the Leaflet map and on every "Zone C" / "Citywide" tag in the call
  queues, suggestions and logs. A dispatcher reads place the way they read a street sign.
- **Second rule: status as road-sign shapes.** Green circle = on track, yellow diamond = watch,
  red square = past target. A running clock past 80% of its target becomes a yellow caution plate;
  past the target, a red plate.
- Seed: none (the impeccable launcher was not run; the direction was pinned by the brief).

## Colour

Strategy: Restrained with a committed shell. Navy owns the masthead and tab band (about 10% of the
screen); the warm-grey ground and white panels carry the work; orange is rare; status colours
appear only where they mean something.

### Tokens

| Token | Value | Role | Contrast |
|---|---|---|---|
| `--navy-950` | `#0C2340` | masthead, zone plates, modal headers, selected segment, row-button ink | white on it 15.8:1 |
| `--navy-900` | `#12305A` | tab band | white 13.2:1 |
| `--navy-800` | `#1B3D6E` | selects and hover on navy, link colour | |
| `--navy-700` | `#26518C` | hover on navy selects | |
| `--navy-100` | `#DCE5F2` | text selection, pressed default buttons, today in the date picker | |
| `--on-navy-2` | `#B8C4D6` | secondary text on navy | 8.9:1 on masthead |
| `--ground` | `#EDEBE6` | the page (warm grey) | ink 13.2:1 |
| `--panel` | `#FFFFFF` | panels, inputs, modals | |
| `--inset` | `#F6F5F1` | empty states, More info bodies, unit chips, modal footers | |
| `--line` / `--line-soft` | `#DCD8CF` / `#E8E5DE` | panel borders / row dividers | |
| `--line-strong` | `#8C877D` | control borders | 3.6:1 on white (non-text 3:1) |
| `--ink` | `#13233B` | text | 15.8:1 on white |
| `--ink-2` | `#4B5566` | secondary text, labels | 7.5:1 white, 6.3:1 ground |
| `--orange` | `#F26B1D` | **primary actions and brand marks only** | navy text on it 5.2:1 |
| `--orange-hover` | `#FF8442` | primary hover | navy text 6.5:1 |
| `--ok` / `--ok-soft` / `--ok-ink` | `#1B7F45` / `#E2F1E7` / `#17663A` | on track | ok on white 5.0:1 |
| `--watch` / `--watch-edge` | `#F2C200` / `#6B5100` | watch: signal yellow with a dark edge | ink on yellow 9.4:1 |
| `--watch-soft` / `--watch-ink` | `#FFF3BF` / `#5C4600` | watch chips, tags, amber figures | 6.7:1+ |
| `--late` / `--late-soft` / `--late-ink` | `#C21F32` / `#FBE4E6` / `#A3172A` | past target | white on red 5.9:1 |
| `--none` | `#8A93A0` | grey / not applicable (a hollow circle) | 3.1:1 |
| `--focus` | `#2E6FD8` | focus ring on light surfaces | 4.8:1 white, 4.0:1 ground |

### Orange is never amber

The brand orange and the "watch" amber are kept apart on three axes, so a viewer never reads a
button as a warning or a warning as a button:

1. **Hue and lightness.** Orange sits at about 22 degrees and mid lightness; watch is a signal
   yellow at about 48 degrees, much lighter. On the charts the amber target line is a deep gold
   (`#A57C00`), still yellow-family, never orange.
2. **Shape.** Orange only fills rectangular buttons and the logo plate (and the round "go" arrow on
   the start page). Watch is always a **diamond** (dots, KPI markers, final clocks) or a caution
   plate with a dark edge, the way a road warning sign has a black border.
3. **Place.** Orange never appears in charts, maps, rows, chips or tags; amber never fills a control.

Green / amber / red are used for status only. The three stages on the delay chart are a blue family
(light to dark in call order: processing `#A9BCD6`, turnout `#5B82B5`, travel `#1B365D`), so
"turnout" no longer borrows the status amber as v1 did.

## Typography

Two families from Google Fonts, loaded once in `app/app.py`:

- **Barlow Semi Condensed** 500/600/700: the signage voice. Headings, small uppercase labels, chips,
  tags, figures (KPIs, clocks, counts), the wordmark. Barlow descends from California highway and
  plate lettering; the semi-condensed width fits dense labels and big clocks.
- **Public Sans** 400-700: the text and control face (body, row titles, buttons, inputs, notes). It
  is the US Web Design System's typeface, built for public services.
- Every figure uses `font-variant-numeric: tabular-nums` (both faces have true tabular figures,
  checked in the browser: "1111" and "0000" render the same width).

| Role | Face, weight, size / line | Notes |
|---|---|---|
| Start-page title | Barlow SC 700, 96 px / 0.95 | 54 px under 640 px |
| Page title (Live board, History) | Barlow SC 700, 30 px / 1.1 | |
| Wordmark | Barlow SC 700, 23 px | |
| Card title | Barlow SC 700, 19 px / 1.2 | |
| KPI figure | Barlow SC 600, 34 px (30 in 4-up, 27 in Statistics) | tabular |
| Running clock | Barlow SC 700, 23 px | tabular, plate-ready padding |
| Label / caption caps | Barlow SC 600, 12-12.5 px, +0.07em, uppercase | form labels, KPI labels, table heads, chips |
| Tag | Barlow SC 600, 12.5 px, +0.02em | |
| Body / UI | Public Sans 400-600, 14 px / 1.45 | row titles 14.5 px 600 |
| Prose (answers, More info) | Public Sans 400, 14-15.5 px / 1.55-1.6 | measure capped at 70-78ch |
| Meta | Public Sans 400, 12.5-13 px | |

## Space, shape, depth

- Spacing on a 4 px base: 4, 6, 8, 10, 12, 14, 16, 20, 24. Panels gap 16 px; panel padding
  18/20/20 px; page gutter 24 px (16 px under 640 px); content max width 1360 px.
- Radius: 6 px panels and modals, 4 px controls, 3 px tags, chips and plates. Sturdier than v1's
  12 px pills.
- Depth: one soft panel shadow (`0 1px 2px` navy at 6%); a lifted shadow only for things that float
  (role cards, menus, the map tooltip, notifications, modals).

## Components

- **Masthead** (`header.rw-masthead`): full-bleed navy band, content at 1360 px. Orange logo plate
  with the navy pulse mark, wordmark and sub-line, role and mode chips (outline on navy), then the
  shift-replay controls (navy selects with white chevrons, orange "Simulate a shift", outline Reset)
  and Switch role. Wraps to two lines at 1024 px.
- **Tab band** (`.nav-pills`): a second, lighter navy tier, full bleed. The open tab takes the
  page's ground colour and reads as a folder tab opening into the page.
- **Panels** (`.rw-card`): white, 1 px warm border, one title; numbered step badges (1-5) stay
  because the call process is a real sequence.
- **KPI strip** (`.rw-kpis`, `.rw-stats`): one ruled panel split by 1 px rules, label above figure,
  the figure pinned to the bottom so a wrapped label never misaligns a row. Amber and red figures
  carry their diamond or square.
- **Queues** (`.rw-rows`): a ruled list like a CAD screen, not boxes inside boxes. A live row past
  its target takes a soft red band. Between 641 and 1200 px a half-width row becomes two lines
  (call and clocks on top, buttons below) so the call ID and zone plate stay visible.
- **Clocks**: plain ink while on track; yellow caution plate past 80% of the target; red plate past
  the target. Finished clocks (Resolved) are history: text colour plus shape, no plate.
- **Chips**: rectangular plates, uppercase. Verdict chips (capability, before and after) take the
  soft status fill; the capability verdicts sit on a subgrid, so the widest chip ("Just meets the
  standard") sets the column for every row and can never overlap the sentence (the v1 defect).
- **Tags**: small outline labels; the zone tag is the navy street-name plate; red and amber tags
  use the soft fills.
- **Buttons**: one orange primary (navy text, bold) per context; row actions are navy outline that
  fill navy on hover; default and ghost buttons are white with a strong border. Bootstrap/bslib
  button variables are overridden (`--bs-btn-*`) so hover, focus and active states stay in palette.
- **Forms**: uppercase Barlow labels; white inputs with `--line-strong` borders, navy on hover, blue
  focus ring. The Chart radio group is a segmented control built on the real radios (keyboard and
  screen-reader behaviour unchanged). The bootstrap-datepicker is restyled (navy selected day).
- **Modals** (Targets, Log an action, delay reason, clear call): navy title band, white body, warm
  footer, Cancel as default, the action in orange. Backdrop is navy at 55%.
- **Notifications**: white plate with a lifted shadow; warning on soft yellow, error on soft red.
- **More info**: a navy text toggle with a square plus; the body is an inset panel.
- **Start page**: the navy band continues into a tall hero with the title; the two role cards sit
  across the band's lower edge, each with a navy icon plate and an orange go arrow.

## Charts (matplotlib, `app/charts.py`)

- White ground (`BG #ffffff`), navy ink titles (`FG #13233b`, bold), ticks and labels `#5b6472`
  (6:1), warm hairline grid `#e6e3dc`.
- Data series `LINE #1f4e8c` (civic navy-blue). Control limits dashed grey, centre line solid grey.
- Target (spec limit) is the amber family as a deep gold `#a57c00` (3.8:1 on white) so it stays
  "the amber line" the copy refers to and stays visible on white. Flagged days red `#c21f32`;
  "check the data" open gold circles; action lines green `#1b7f45`.
- Box plots: pale navy boxes `#e3eaf3` with grey edges, navy median, navy diamond means.
- SVG charts (zone box chart, delay by stage) set `svg.fonttype = "none"`, so the browser draws
  their text in Public Sans; the delay chart's text is enlarged because its 9-inch canvas is drawn
  smaller than life. PNG charts (daily X-bar and S, every call, before and after, normal plot) are
  rasterised by matplotlib in DejaVu Sans, the font it always has (also on Posit Connect).

## Map (Leaflet, `app/www/zonemap.js`)

- Esri World Light Gray tiles (`--map-tiles: light`), zone outlines in navy (`--map-line`), status
  fills from `--map-green`, `--map-amber` (signal yellow) and `--map-red` at 45% (v1: 38%) so the
  status still reads on a washed-out projector.
- Zone labels are the navy street-name plates (`.rw-zone-label`); the hover card (`.rw-map-tip`) is a
  white plate with a Barlow title. Zoom buttons and attribution restyled to match.
- The resize refit no longer animates (no zoom motion for a layout change) and a hidden map keeps
  its view instead of refitting at width 0.

## Motion

State changes only: 150-200 ms colour transitions on buttons, rows and clocks; a 2 px lift on the
role cards. `prefers-reduced-motion: reduce` removes every transition and the Leaflet zoom and fade
animations.

## Responsive

- 1440 px: everything on the planned grid; the supervisor control bar fits on one line.
- 1200 px and below (laptops, the 1024 px projector): the fleet board, the delay chart and the
  before-and-after chart take the full width (`.rw-two-wide`); half-width queue rows go to two lines.
- 992 px and below: all grids single column; KPI strips 2-up. 640 px and below: 16 px gutters,
  stacked role cards, stacked capability rows.

## Accessibility

- Every text pair meets WCAG AA (see the table); status never relies on colour alone (shape, text,
  plate); control borders meet 3:1.
- One visible focus ring everywhere: 2 px blue (`--focus`) on light surfaces, white on navy.
- `color-scheme: light`, `data-bs-theme="light"` (set in `rw.js`), themed selection and caret.

## Files

`app/www/rw.css` (the theme), `app/charts.py` (style constants only), `app/www/rw.js` (theme
attribute), `app/www/zonemap.js` (fallback colours, refit without animation), `app/app.py` (fonts,
favicon, version, masthead and start markup), `app/ui_dispatcher.py` and `app/ui_supervisor.py`
(classes, wrappers, the arrow icon and the zone-tag helper; the supervisor's inline style block now
lives in `rw.css`).
