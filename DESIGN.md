---
name: ERGent v2, Refined command center
description: A dark dispatch-room interface for Ithaca EMS. Blue-slate surfaces layered by tone, one Star of Life blue accent, and hyperlegible type for clocks and IDs.
colors:
  bg-deep: "#07090d"
  bg: "#0a0d12"
  surface: "#11161e"
  surface-2: "#171d27"
  surface-3: "#1e2531"
  surface-4: "#262e3c"
  well: "#0d1117"
  edge: "#1a212b"
  line: "#1f2632"
  line-2: "#2b3442"
  ctl: "#5a667c"
  text: "#e7ebf1"
  text-2: "#a3adbc"
  text-3: "#8a96a8"
  accent: "#336ae6"
  accent-hover: "#2c62dc"
  accent-press: "#2757c7"
  accent-text: "#7aa6ff"
  status-green: "#4fcf8e"
  status-amber: "#f0b43c"
  status-red: "#f26b61"
  status-grey: "#6b7688"
  chart-line: "#9dbcf5"
  chart-limit: "#7d889a"
  stage-processing: "#d6e0f2"
  stage-turnout: "#8ea9db"
  stage-travel: "#4a6aa8"
typography:
  page-title:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  hero:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "56px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.035em"
  card-title:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 650
    lineHeight: 1.25
  body:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
  small:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.4
  caption:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "11.5px"
    fontWeight: 600
    lineHeight: 1.2
  number:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  clock:
    fontFamily: "Atkinson Hyperlegible Mono, ui-monospace, monospace"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
rounded:
  tag: "4px"
  control: "6px"
  row: "8px"
  card: "10px"
  modal: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  3xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    height: "34px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    height: "30px"
  row-button:
    backgroundColor: "{colors.surface-3}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    height: "30px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "20px"
  row:
    backgroundColor: "{colors.surface-2}"
    rounded: "{rounded.row}"
    padding: "10px 14px"
  tag:
    backgroundColor: "{colors.surface-4}"
    textColor: "{colors.text-2}"
    rounded: "{rounded.tag}"
    height: "19px"
  chip:
    backgroundColor: "{colors.surface-3}"
    textColor: "{colors.text}"
    rounded: "{rounded.tag}"
    height: "24px"
  input:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    height: "34px"
---

# Design System: ERGent v2, Refined command center

## Overview

ERGent is worked in a 911 dispatch room at 3 AM: a dimmed room, several monitors, a dispatcher who
has been awake for hours and must see which call is late in one glance. The same screens are shown
this afternoon on a 1024 px classroom projector, which washes out dark tones. The scene forces a dark
interface with low glare and high clarity, and it forces steps between surfaces that survive a
projector.

The world is the evolution of v1's dark look, done with restraint: near-black blue-slate surfaces
layered by tone instead of borders, one brand accent, and type chosen for legibility under fatigue.
Status is the only loud colour on the page. Mode: **Operate**. The tool should disappear into the
task; brand lives in precise details.

**Signature move: the instrument strip.** Every live count sits in one segmented panel divided by
hairlines (never a row of separate cards), and every running clock is set in Atkinson Hyperlegible
Mono at a fixed width, so the board reads like a departures board of clocks against quiet slate. A
clock only turns amber or red when it carries that status.

## Colors

Strategy: **Restrained.** Tinted neutrals from one blue-slate hue, one accent, and the status ramp.

### Primary

- **Star of Life blue** `#336ae6` (`--accent`): the EMS emblem's blue, brightened for dark UI. Used
  for primary actions (Simulate a shift, Save, a call's next step: Dispatch, En route, On scene), the
  current tab indicator, the checked radio, and the selected date. White text on it is 4.8:1.
  Hover `#2c62dc`, pressed `#2757c7`. As text or a focus ring on dark: `#7aa6ff` (7.5:1).
- v1's coral `#ff6b5b` was retired: it sat too close to the status red, so a coral Pause button next
  to a red clock read as an alarm.

### Neutral

| Token | Hex | Role |
|---|---|---|
| `--bg-deep` | `#07090d` | top bar |
| `--bg` | `#0a0d12` | page canvas |
| `--surface` | `#11161e` | cards, toolbars, modals; every chart's background |
| `--surface-2` | `#171d27` | rows, inputs, wells inside cards |
| `--surface-3` | `#1e2531` | tags, chips, popovers, notifications |
| `--surface-4` | `#262e3c` | hover on surface-3, selected segment |
| `--edge` | `#1a212b` | a card's single edge (keeps cards apart on a projector) |
| `--line` / `--line-2` | `#1f2632` / `#2b3442` | dividers, then popover edges |
| `--ctl` | `#5a667c` | form-control and outline-button edge, 3.1:1 on surface |
| `--text` / `--text-2` / `--text-3` | `#e7ebf1` / `#a3adbc` / `#8a96a8` | 15:1, 8:1, 6:1 on surface |

### Status (fixed meaning)

Green `#4fcf8e` on track, amber `#f0b43c` watch (above 80% of a target), red `#f26b61` past target,
grey `#6b7688` no data. Used for dots, clock numerals, verdict chips, map fills and flagged chart
points, and nothing else. All pass 4.5:1 as text on every surface.

### Named Rules

- **The accent never means status.** Blue is an action or a selection; it never colours a number.
- **Status is never colour alone.** Every dot sits beside a word, a clock or a count.
- **Live rows carry their status in the surface.** A live row past target gets a 10% red mix of
  `--surface-2`; amber gets 6%. Resolved rows stay neutral so the list does not shout.

## Typography

**Atkinson Hyperlegible Next** (UI) and **Atkinson Hyperlegible Mono** (clocks), from Google Fonts.
The Braille Institute drew them for low-vision readers: 0 and O, 1, l and I, B and 8 are never
alike. That is the reason no other face satisfies here: call IDs (`C01892`, `LIVE-20261017-002`),
unit IDs (`M-B1`, `M-D1`) and times are exactly those glyphs, read under fatigue and on a projector.
Both faces slash the zero; that is intentional and not switched off.

### Hierarchy

| Role | Face | Size / weight | Where |
|---|---|---|---|
| Hero | Next | 56 / 700, -0.035em | start page |
| Page title | Next | 28 / 700, -0.02em | Live board, History |
| Card title | Next | 16 / 650 | every card |
| Body | Next | 14 / 400, 1.45 | text, rows |
| Small | Next | 12.5 / 400 | row subtitles, legends |
| Caption | Next | 11.5 / 600 | clock captions, labels |
| Number | Next, tabular | 28 / 700 (23 in a card) | count strip, statistics |
| Clock | Mono | 22 / 600 | running and final clocks; 13 / 500 for date and time chips and unit IDs |

### Named Rules

- **Mono is for things that tick or identify** (clocks, timestamps, unit IDs, the as-of date).
  Quantities use the sans with tabular figures, so `6.3` never spreads into `6 . 3`.
- **No uppercase tracked labels.** Labels are sentence case at 11.5 to 12.5 px; the hierarchy comes
  from size, weight and tone.
- Fixed px scale (ratio about 1.2); no fluid type in the product.

## Layout

- Shell: max width 1376 px, 32 px side padding (24 px at 1180 px and below, 16 px at 640 px).
- Spacing on a 4 px base: 4, 8, 12, 16, 20, 24, 32. Card gap 16 px; row gap 6 px; card padding 20 px.
- Top bar (darkest layer, sticky above 1180 px) holds the brand, role chips, simulation controls and
  Switch role. Underline tabs sit under it with a hairline across the work area.
- Dispatcher: count strip, then the call process in order (1 Log a call, 2 Incoming, 3 Dispatched,
  4 En route), Ambulances beside the live map (the map grows to the ambulance card's height, up to
  560 px), then 5 Resolved. Step numbers stay because the sequence is the call's life.
- Supervisor: one toolbar row of controls at 1440 px; control chart left, statistics and map right.
- At 1180 px and below (the 1024 px projector): the top bar stops being sticky, Ambulances and the
  map stack, History's chart takes the full width above Suggested actions. At 992 px all grids stack.

## Elevation & Depth

Depth is tonal: canvas, then surface, then surface-2 rows, then surface-3 tags. No card shadows.
Only things that float get a shadow: modals, the date picker, map tooltips and notifications use
`0 12px 32px rgba(0,0,0,.45), 0 2px 6px rgba(0,0,0,.35)`. The modal backdrop is `#020306` at 72%.

## Shapes

Tags 4 px, controls 6 px, rows and wells 8 px, cards 10 px, modals 12 px. No pills: squared corners
read as instruments, and rounded pills read as friendly consumer chips.

## Components

### Buttons

- **Primary** (`.btn-primary`): accent fill, white text, 6 px radius. One per area.
- **Row action** (`.rw-btn`): surface-3 fill with the `--ctl` edge, 30 px tall. A call's next step
  (Dispatch, En route, On scene) takes the accent fill; Clear and Log this action stay neutral.
- **Secondary / outline** (`.btn-default`, `.rw-linkbtn`): transparent with the `--ctl` edge.
- **Ghost** (`.rw-btn-ghost`): Out of service on a unit card; text-3 on surface-3.
- Focus: a 2 px `#7aa6ff` ring, offset 2 px, on every control.

### Chips and tags

- **Chip** (`.rw-chip`): 24 px, 4 px radius, surface-3, 12 px / 600, optional 7 px status dot. The
  date and time chips use the mono.
- **Tag** (`.rw-tag`): 19 px, surface-4, 11 px / 600, text-2. Red and amber tags tint text and fill.
- **Count** (`.rw-count`): 22 px, surface-3, tabular.

### Cards / containers

`.rw-card`: surface, 1 px edge, 10 px radius, 20 px padding. Nothing nests a box in a box: the
statistics inside a card are cells divided by hairlines, like the count strip.

### Inputs / fields

Surface-2 fill, `--ctl` edge, 34 px tall (30 px in the top bar), 6 px radius. Focus: accent-text
ring and edge. The Chart choice (Daily chart / Every call) is a segmented control built on the real
radio inputs.

### Navigation

Underline tabs: text-2, current tab text with a 2 px accent bar on the hairline.

### Live row

`.rw-row`: surface-2, 8 px radius, 58 px minimum height. Status dot, title (ID and tags), subtitle,
actions, then right-aligned mono clocks with a caption beneath.

### Charts

Matplotlib, drawn on `#11161e` so a chart is part of its card. Data series `#9dbcf5`; center line
and control limits `#7d889a` (limits dashed); the target is the solid amber line (the copy calls it
the amber line); flagged points red; an action is a green vertical line. Stages, in call order, are
one blue-slate ramp: processing `#d6e0f2`, turnout `#8ea9db`, travel `#4a6aa8`, with a hairline of
the surface between segments. Boxes `#1a212c` with `#7d889a` edges. Titles 11 to 12 pt semibold.
SVG charts keep text as text (`svg.fonttype: none`) and the page draws it in Atkinson.

### Map

Esri Dark Gray tiles, tinted to blue-slate with a CSS filter and dimmed to 66% so status fills read.
Zone outlines `#c3cddc` at 1.25 px (2.5 px on hover); fills are the status colours at 42%. Zone
letters sit in squared dark labels in the mono. Zoom controls, attribution and tooltips use the
surface tokens.

## Do's and Don'ts

### Do:

- Use a status colour only when the thing on screen is on track, watch or past target.
- Put live numbers in the count strip or in mono clocks; keep their widths fixed.
- Keep the accent for the one next step in each area.
- Check every new pair of colours for 4.5:1 text and 3:1 controls.

### Don't:

- Don't bring back the faint background grid, pills, uppercase tracked labels or the coral accent.
- Don't put boxes inside cards; divide with hairlines.
- Don't colour a chart series amber, green or red unless it is the target, an action or a flag.
- Don't animate anything that is not a state change; transitions are 150 to 200 ms and are switched
  off under `prefers-reduced-motion`.
