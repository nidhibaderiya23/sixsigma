# DESIGN.md: ERGent v6, "Ops console"

A dense, dark graphite console for a dim 911 dispatch room. One screen holds the whole shift:
panes tile the viewport and meet on 1 px seams, rows read like a table, clocks and IDs are set
in a monospace, and green / amber / red appear only as status lamps. Mode: **Operate**.

Source of truth for the tokens: `app/www/rw.css` (`:root`). Chart constants: `app/charts.py`.
Map colours: the `--map-*` variables, read by `app/www/zonemap.js`.

## 1. Physical scene
Dispatchers sit at multi-monitor consoles in a low-light room and glance at this board between
the CAD and the radio; supervisors read it at the start of a shift; the class sees it on a 1024 px
projector. Dark ground (less glare in a dim room), high-contrast ink, status that reads at a glance.

## 2. Colour (strategy: restrained neutrals + a tinted shell band + status lamps)

| Token | Value | Role |
|---|---|---|
| `--bg` | `#0d0f11` | page ground |
| `--shell` | `#0f151b` | header and tab rail: a blue-graphite band that runs edge to edge |
| `--panel` | `#14171a` | panes |
| `--panel-2` | `#1a1e22` | pane heads, table heads, raised controls, tooltips |
| `--inset` | `#0a0c0e` | inputs, wells, unit cells, map ground |
| `--hover` | `#1d2227` | row and control hover |
| `--line` | `#252a2f` | 1 px seams and row dividers |
| `--line-2` | `#343a41` | tags, chips, outlines that are not controls |
| `--ctl-line` | `#616a74` | form-control borders (3.3:1 on panes, WCAG 1.4.11) |
| `--text` | `#e6e9ec` | primary ink (14.8:1 on panes) |
| `--text-2` | `#a3abb4` | labels, secondary text (7.7:1) |
| `--text-3` | `#8d96a0` | captions, empty states (6.0:1) |
| `--accent` | `#4cc2ff` | signal cyan: focus ring, selection, active tab, the primary button (dark ink `#04121b` on it, 9.5:1) |
| `--green` | `#3fd68a` | status: on track |
| `--amber` | `#ffb547` | status: watch (above 80 % of a target); also the target line in charts (the app's text calls it "amber line") |
| `--red` | `#ff6b62` | status: past target |
| `--grey` | `#7d8691` | status: no data / not applicable |
| `--amber-soft`, `--red-soft` | 16 % tints | lit readout grounds |
| `--red-wash` | 7 % red | ground of a live row that is past target |

Rules: status hues never decorate; the accent never means status; secondary text is tinted grey,
never below 4.5:1. Text selection, scrollbars and the focus ring are themed from these tokens.

## 3. Type

- **Barlow Semi Condensed** (Google Fonts, 400/500/600/700): labels, titles, prose. A
  semi-condensed grotesk from road-sign lettering: open forms that stay legible at 12-14 px and
  fit more words per column than a regular-width sans.
- **JetBrains Mono** (400/500/600): clocks, call and unit IDs, counts, KPI numbers, table values,
  dates and speeds. Tabular, with a 0 that never reads as O. Never used as decoration.
- Fixed px scale, ratio about 1.15: `--fs-cap` 12 (captions, labels, tags), `--fs-ui` 13 (controls,
  row subtitles), `--fs-body` 14 (body, row titles), `--fs-title` 15 (pane titles), `--fs-page` 18
  (page titles), `--fs-num` 22 (stat numbers); clocks 15 px mono semibold; the live clock 15 px.
  Nothing on screen is smaller than 12 px.
- Uppercase only for the wordmark and the role chip.

## 4. Space, shape, structure

- 4 / 8 px grid; pane padding 12 px; pane head 32 px; control height 28 px; row buttons 24 px.
- Radii: `--r1` 2 px (panes, controls, tags, lamps 1 px), `--r2` 3 px (notifications),
  `--r3` 4 px (modals). No pills.
- **Tiled boards**: `.rw-board`, `.rw-sup-board`, `.rw-two`, `.rw-hist-grid` are grids with
  `gap: 1px` on a `--line` ground, so panes meet on hairline seams instead of floating cards.
- Shell: header band (44 px) and tab rail (36 px, 2 px cyan underline on the active tab), both
  full-bleed.

### Dispatcher live board (1440 x 900, no page scroll)
Page head (title, date chip, live clock chip, Download) / command row: **Log a call** inline form
+ 5-cell stat strip / a 12-column board, rows fixed at 268 px and 372 px so nothing jumps while
the shift runs: Incoming (4) | Dispatched (4) | En route (4), then Ambulances (5) | Zone map (3) |
Resolved (4). Lists scroll inside their pane and keep their scroll position (`data-rw-key`); pane heads never
shrink, and a scroll-driven bottom fade (`--rw-fade`, no JS) shows there is more below until the end.
At 1024 px: a 6-column board, rows 252 / 396 / 260 px (three lists, then Ambulances 4 + map 2,
then Resolved full width).

### Supervisor Charts
Control bar in one row / a 3-column board: Control chart (span 2) | Statistics + Zone map, then
Delay by stage | Zone comparison | Capability. At 1024 px: chart full width, then Statistics |
map, Delay | Comparison, Capability full width.

## 5. Components

- **Pane** (`.rw-card` + `.rw-card-head`): `--panel` body, 32 px `--panel-2` head with a 1 px
  rule; the title at 15 px semibold, a mono count (`.rw-count`) on the right; step badges
  (`.rw-step`, the call process 1-5) are 18 px cyan-outlined mono squares.
- **Stat strip** (`.rw-kpis`, `.rw-kpi`, `.rw-stats`): cells on 1 px seams, label left in
  `--text-2`, mono number right; no icons.
- **Row** (`.rw-row`): one shared grid `8px | 1fr | actions | clocks`; 46 px minimum, 1 px
  divider, hover `--hover`. Title = mono ID + tags; subtitle 13 px `--text-2`. A container query
  moves the unit picker and buttons to a second line when a pane is narrower than 560 px.
- **Lamp** (`.rw-dot`): an 8 px square with a 1 px radius, coloured by status.
- **Severity-lit readout** (signature): `.rw-clock` / `.rw-final` are mono cells. On track:
  plain ink. Watch: amber numerals on `--amber-soft`. Past target, live: a solid red cell with
  dark numerals; a stopped (resolved) late clock: red numerals on `--red-soft`. rw.js repaints
  `data-sev` every second, so the light changes in place.
- **Tag** (`.rw-tag`): 18 px, 1 px `--line-2` outline, 12 px semibold `--text-2`; red/amber
  variants only for status (Breakdown, No unit free).
- **Chip** (`.rw-chip`): 24 px boxed label; the role chip in caps, the mode chip (SIM 120x /
  LIVE 1x) in mono; the clock chip 28 px with a 15 px mono time.
- **Buttons**: primary = cyan fill, dark ink (one per area: Simulate a shift, Save); default =
  `--panel-2` with a `--ctl-line` outline; ghost = transparent with a `--line-2` outline (Targets,
  Log an action, Out of service). Focus: 2 px cyan outline, 2 px offset.
- **Controls**: selects and inputs on `--inset`, 28 px, 2 px radius, custom chevron in `--text-2`,
  cyan border + 1 px ring on focus. Radio groups render as a segmented control (checked =
  cyan tint + 2 px cyan underline). Number-like selects (speed, start time, unit picker, date) in
  mono.
- **Fleet** (`.rw-ucols`): status groups stacked as table sections (lamp, label, mono count);
  an empty group is one line ("None"); unit cells are one line (mono ID, zone, Out of service).
- **Verdicts** (`.rw-verdicts`): a 3-column grid with subgrid rows (zone | chip | sentence), so a
  long verdict chip never overlaps its sentence.
- **More info** (`details.rw-moreinfo`): a 16 px boxed +/- and a 13 px label; the body is an
  `--inset` well, 14 px at 1.5 line height, max 72ch.
- **Tables** (`.rw-table`): `--panel-2` head in 12 px semibold, original case (Ppk, Cpk), 5 px x
  10 px cells, mono values, row hover.
- **Bootstrap parts**: modals (`--panel`, `--panel-2` head, 4 px radius, no backdrop blur),
  notifications (one 40 px line, `--panel-2`, a status lamp on the text line: cyan info, amber
  warning, red error; 6 px apart; below a dialog's backdrop, except an error, which stays above it;
  scoped under `#shiny-notification-panel` because Shiny injects its own toast styles later),
  the date picker (dark, mono days, cyan selected day), Shiny busy indicators in cyan.

## 6. Charts (matplotlib, `app/charts.py`)

- Ground `BG #14171a` (the pane colour), ink `FG #e6e9ec`, axes and ticks `MUTED #a3abb4`,
  grid `GRID #252a2f`.
- Data series `LINE #62a8ff`; control limits dashed `MUTED`; the target (a spec limit) solid
  `AMBER`; flagged points `RED`; "check the data" amber rings; a logged action `ACTION #b9a8ff`
  (an event, not a status); box plots `BOX_FACE #1f2429` with `MUTED` edges.
- Stages (categorical, fixed order, no status hues): processing `#9085e9` violet, turnout
  `#d55181` magenta, travel `#3987e5` blue, with 1 px pane-coloured gaps between segments.
- Text: SVG charts use `svg.fonttype = "none"` and name Barlow Semi Condensed first, so the
  browser draws chart text in the page font; PNG charts render with an installed condensed face
  (Avenir Next Condensed on macOS, DejaVu Sans elsewhere). Ticks 9 pt and legends 9 pt (12 px).
- Inline SVG charts are sized to draw near 1:1 where they sit (stage share 4.4 x 2.5 in, capped
  at 520 px; zone box 7.4 x 3.0 in, capped at 760 px, title 10.5 pt), so their text stays about
  12-14 px at 1024 and 1440. At 1280 px and up the History chart pane is 784 px wide and the
  suggestions take the rest. The normal-plot title puts the Shapiro-Wilk p on a second line.

## 7. Map (Leaflet, `app/www/zonemap.js`)

- Esri Dark Gray canvas tiles (`--map-tiles: dark`), zone outlines `--map-line #cfd5db` at
  1.25 px (2.5 px on hover), fills from `--map-green/amber/red/grey` at 46 % (grey 20 %).
- Zone letters are 26 px dark squares with a mono letter; tooltips use `--panel-2` with a 1 px
  `--line-2` border; zoom buttons and attribution are themed; a resize refits without animation.

## 8. Motion and accessibility

- Only state transitions: 150-200 ms colour and background changes (rows, buttons, tabs, lit
  readouts). No entrance animation. `prefers-reduced-motion: reduce` removes transitions.
- WCAG AA: every text token is 6:1 or better on its ground; control borders 3.3:1; visible
  2 px cyan focus everywhere (selects, buttons, tabs, segmented radios, role buttons).
- Breakpoints: 1280 (supervisor board to 2 columns), 1100 (dispatcher board to 6 columns),
  860 (one column), 640 (phone).
