---
name: ERGent v7
description: Friendly modern, an approachable health-tech look for Ithaca's 911 EMS dispatch board and its supervisor charts.
colors:
  ground: "#f0f5fb"
  surface: "#ffffff"
  inset: "#f3f7fc"
  inset-2: "#e8eef7"
  line: "#dee3eb"
  field: "#c3cbd7"
  field-strong: "#8993a2"
  ink: "#16202e"
  ink-2: "#3e4858"
  muted: "#5d6775"
  primary: "#145ec1"
  primary-strong: "#034da8"
  primary-ink: "#06489c"
  primary-soft: "#ddecff"
  primary-tint: "#eef6ff"
  green: "#2ea55c"
  green-ink: "#10703a"
  green-soft: "#ddf8e3"
  amber: "#f5a420"
  amber-ink: "#995600"
  amber-soft: "#fff2ce"
  red: "#e64343"
  red-ink: "#ba1d27"
  red-soft: "#ffe9e8"
  grey: "#9da5b1"
  grey-soft: "#eceff4"
  chart-green: "#21914e"
  chart-amber: "#e78d02"
  chart-red: "#db2b33"
  chart-grid: "#e5e8ed"
  stage-processing: "#886acf"
  stage-turnout: "#39b4dd"
  map-line: "#3a485d"
typography:
  hero:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "56px"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.035em"
  page-title:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  card-title:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    letterSpacing: "-0.01em"
  count:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 800
    fontFeature: "tnum"
  clock:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    fontFeature: "tnum"
  body:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  row-title:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
  label:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 600
  caption:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
rounded:
  sm: "10px"
  md: "14px"
  lg: "20px"
  xl: "24px"
  control: "12px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "14px"
  lg: "18px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    height: "40px"
    padding: "8px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-strong}"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "40px"
  row-action:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.control}"
    height: "36px"
    padding: "6px 15px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "22px 24px"
  list-row:
    backgroundColor: "{colors.inset}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
  tag:
    backgroundColor: "{colors.grey-soft}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    height: "22px"
  chip-status-red:
    backgroundColor: "{colors.red-soft}"
    textColor: "{colors.red-ink}"
    rounded: "{rounded.pill}"
    height: "30px"
  tab-active:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.control}"
  icon-tile:
    backgroundColor: "{colors.primary-tint}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    size: "44px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "42px"
---

# Design System: ERGent v7

## Overview

**Creative North Star: "The Calm Clinic Board"**

A live 911 board and a set of control charts, made to feel like a well-run modern clinic: a
light lake-mist room, white panels that rest on soft shadows, and one confident lake-blue that
marks what you can do and where you are. Status is the only other colour on screen, and it always
arrives as a soft tint with a darker ink, so a late call is unmistakable without the page ever
shouting.

It is built for first-time and non-expert readers (classmates, a professor, a new supervisor) and
for dispatchers who glance at it under time pressure: generous spacing, 36-42 px touch targets,
sentence-case labels instead of tracked capitals, tabular figures on every count and clock. It
refuses the dark command-center wall of v1 and the generic grey admin template; no gradients, no
glass, no emoji.

**Key characteristics:**
- Light, cool-tinted ground (`ground`) with white raised panels; depth from shadow, not borders.
- One primary (`primary`, Cayuga-lake blue) for actions, selection, focus and the measured series in charts.
- Green / amber / red mean on track / watch / past target, and nothing else.
- Figtree throughout, one family, with tabular figures for numbers.
- Icons sit on soft colour tiles; empty states show the stage's icon above the team's message.

## Colors

A restrained palette: tinted neutrals, one blue, and three status hues that each come in three strengths.

- **Ground / surface / inset**: the page (`ground`), panels (`surface`), and rows or tiles inside a panel (`inset`, `inset-2` for hover and tracks).
- **Ink**: `ink` for text and numbers (16:1 on white), `ink-2` for secondary text, `muted` for captions (5.7:1 on white, 5.2:1 on the ground).
- **Primary** `#145ec1`: buttons (white text 6.2:1), the active tab and role chip (`primary-soft` with `primary-ink`, 7.3:1), focus rings, icon tiles (`primary-tint`), the chart series.
- **Status**: the dot tone (`green`, `amber`, `red`) always has a 3 px halo of its soft tint; text in a status colour uses the ink strength (`green-ink`, `amber-ink`, `red-ink`, all 5.1-6.4:1 on their soft tint). A late call's whole row on the live board takes a faint tint (`#fff8e6` amber, `#fff1f0` red), and its clock becomes a tinted pill.
- **Charts** use deeper status tones that hold on white (`chart-*`), a soft grid, and two non-status stage colours (`stage-processing` violet, `stage-turnout` sky) beside the primary for travel, so no stage reads as a status.

## Typography

Figtree (Google Fonts, weights 400-800): a friendly geometric sans with a large x-height, open
apertures that hold up at 12 px on a projector, and true tabular figures (checked in the browser;
DM Sans and Lexend on Google Fonts have none). One family carries every role. Body is 15 px; the
ramp is 12 / 13.5 / 15 / 18 / 22 / 28 / 56 px, with weight (600 to 800) doing as much work as size.
Labels are sentence case; nothing is letter-spaced capitals. Every count, clock, table and chip
number uses `font-variant-numeric: tabular-nums`, so running clocks never jitter.

Charts: inline SVG charts keep their text as text (`svg.fonttype = "none"`) and name Figtree first,
so the browser draws them in the page font; PNG charts fall back to Helvetica Neue / Arial / DejaVu Sans.

## Layout

- Shell: max width 1320 px, 28 px side padding (20 px under 1180 px).
- App bar: one white rounded bar (logo tile, name, role chip, controls, Switch role); it wraps its controls to a second line on a 1024 px projector.
- Tabs: a segmented control under the app bar.
- Grids: the live board is 2 x 2 cards, then Ambulances | Zone map, then Resolved; the supervisor is chart (1.9 fr) | statistics and map (1 fr), then two halves, then Capability. Gaps 18 px (16 px under 1180 px). One column under 992 px.
- The Ambulances card is a container: under 520 px wide its four status columns become two by two.
- Rhythm: 6 / 10 / 14 / 18 / 24 px. Tight inside a group, 18 px between cards.

## Elevation & Depth

Soft, offset shadows over a near-invisible 1 px edge (`0 0 0 1px rgba(22,32,46,.045)`):
- `shadow-1` `0 1px 2px rgba(22,32,46,.05), 0 2px 8px -2px rgba(22,32,46,.06)`: panels, tabs, count tiles, white chips.
- `shadow-2` `0 1px 2px rgba(22,32,46,.05), 0 10px 28px -8px rgba(22,32,46,.14)`: role cards, map tooltip.
- `shadow-3` `0 2px 6px rgba(22,32,46,.06), 0 28px 56px -16px rgba(22,32,46,.28)`: dialogs, notifications, date picker, hovered role card.
- Rows and tiles inside a panel are flat tints (`inset`), never a second raised card.

## Shapes

Radii 10 (small buttons, clock pills), 12 (controls, icon tiles in rows), 14 (rows, map, empty states),
20 (panels, app bar), 24 (dialogs, role cards), pill (chips, tags, sim controls, Switch role). Status
dots are circles with a soft halo. Icons are 24-unit outline SVGs at 1.8 stroke (2.2 in the logo).

## Components

- **Buttons**: primary is solid blue with white text and a blue-tinted shadow; default is white with a 1 px `field` inset ring; row actions (Dispatch, En route, On scene, Clear, Log this action) are soft blue (`primary-soft` / `primary-ink`); ghost buttons are transparent with a ring. Hover darkens one step; focus shows a 2.5 px primary outline plus a 4 px soft ring.
- **Inputs and selects**: 42 px, white, 1 px `field-strong` border (3.1:1 on white, so the field edge passes WCAG non-text contrast), 12 px radius; focus turns the border blue with the soft ring. The sim controls are filled pills.
- **Radio "Chart" switch**: Bootstrap radios restyled as a segmented control (the real input stays on top, so click and keyboard work).
- **Count tiles**: icon tile (44 px, `primary-tint`) beside a 30 px tabular number and a sentence-case label. In Statistics the tiles are flat tints with a small icon tile at top right (hidden under 1180 px).
- **Rows**: tinted, 14 px radius, status dot with halo, bold id with tags that wrap rather than vanish, muted subtitle, clocks right-aligned; amber or red clocks become tinted pills.
- **Empty states**: the stage's icon on a white tile above the existing message, on an `inset` panel.
- **More info**: a soft blue pill with a white plus disc; the body opens on an `inset` panel at 72ch.
- **Capability verdicts**: a subgrid, so the zone, the verdict chip and the sentence keep their own columns at any width (fixes v1's chip overlapping the sentence).
- **Dialogs, notifications, date picker**: white, 24 / 16 px radius, `shadow-3`, no rules between header, body and footer; notifications carry a status dot (blue message, amber warning, red error).
- **Map**: Esri light-grey canvas tiles, zones filled with the status tone at 38% (grey 20%), slate outlines (`map-line`), white zone-letter discs, white rounded tooltips.

## Do's and Don'ts

- Do keep green / amber / red for status only; reach for the primary or the stage colours for anything else.
- Do pair every status colour with text (a label, a number or a legend).
- Do use tabular figures for anything that counts or ticks.
- Don't add borders to separate panels; use the ground, the shadow and spacing.
- Don't nest raised cards; inside a panel use the `inset` tint.
- Don't use letter-spaced capitals, eyebrows above headings, gradients, glass or emoji.
- Don't animate anything that redraws every second; motion is for hover and state changes only (160-220 ms, ease-out), and none under `prefers-reduced-motion`.
