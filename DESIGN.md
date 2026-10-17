---
name: ERGent v3, Clinical light
description: A hospital-grade light console for Ithaca EMS dispatch and response-time quality review.
colors:
  canvas: "#eef1f5"
  surface: "#ffffff"
  inset: "#f6f8fa"
  hover: "#f0f3f7"
  line: "#dde3ea"
  line-strong: "#c5ced8"
  control: "#8592a0"
  ink: "#16212c"
  ink-2: "#3a4754"
  muted: "#556170"
  primary: "#0b6474"
  primary-hover: "#08535f"
  primary-press: "#064450"
  primary-tint: "#e3f1f3"
  primary-line: "#a9d0d6"
  band: "#0a4f5c"
  band-muted: "#c6e2e6"
  green: "#2f9e5e"
  green-ink: "#1d7044"
  green-tint: "#e6f4ea"
  amber: "#c98500"
  amber-ink: "#8a5300"
  amber-tint: "#fdf1d9"
  red: "#d1342b"
  red-ink: "#b42318"
  red-tint: "#fdecea"
  grey: "#8e99a5"
  chart-series: "#2a78d6"
  chart-target: "#b7791f"
  stage-processing: "#6250d6"
  stage-turnout: "#c8508a"
typography:
  display:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.25
  data:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.1
    fontFeature: "tnum"
  clock:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.15
    fontFeature: "tnum"
  body:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum"
  label:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.3
  caption:
    fontFamily: "Source Sans 3, Source Sans Pro, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.3
rounded:
  xs: "4px"
  sm: "6px"
  md: "8px"
  dialog: "10px"
  pill: "999px"
spacing:
  hairline: "1px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "22px"
  shell: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    height: "38px"
  button-row-action:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "4px 13px"
    height: "32px"
  button-row-action-hover:
    backgroundColor: "{colors.primary-tint}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    height: "38px"
  chip-flag-amber:
    backgroundColor: "{colors.amber-tint}"
    textColor: "{colors.amber-ink}"
    rounded: "{rounded.pill}"
    padding: "3px 11px"
  chip-flag-red:
    backgroundColor: "{colors.red-tint}"
    textColor: "{colors.red-ink}"
    rounded: "{rounded.pill}"
    padding: "3px 11px"
  chip-flag-green:
    backgroundColor: "{colors.green-tint}"
    textColor: "{colors.green-ink}"
    rounded: "{rounded.pill}"
    padding: "3px 11px"
  tag:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.xs}"
    padding: "1px 7px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "20px 22px"
  header-band:
    backgroundColor: "{colors.band}"
    textColor: "{colors.surface}"
    height: "64px"
---

# Design System: ERGent v3, Clinical light

## Overview

**Creative North Star: "The Lab Report"**

ERGent v3 is the quality console an EMS medical director would want on a bright desk and a class
would want on a washed-out projector: a cool grey canvas, white surfaces separated by hairlines,
and dark ink that survives any lamp. Everything in range reads in plain ink; anything out of range
carries a tinted flag, the way a clinical lab report prints normal values plainly and flags the
abnormal ones. One deep clinical teal owns the shell band, the primary action, selection and focus;
green, amber and red are reserved for status and mean on track, watch and past target.

It is an Operate surface: standard Bootstrap controls, underline tabs, a filter bar, tables and
lists. The world enters only through the type, the palette, the density and the one signature move.
Anti-references: version 1's dark command center (near-black, glow, tracked capitals, coral), the
floating-card SaaS dashboard, and costumes of clinical hardware (ECG paper, monitor bezels, crosses).

**Key Characteristics:**
- A full-width deep teal header band; everything else is light.
- Counts sit in a joined "vitals strip" (cells divided by 1px hairlines), never floating cards.
- Lists are flow sheets: rows separated by hairlines, no boxes.
- Status is a flag (tinted fill plus dark ink of the same hue), shown only when it carries meaning.
- One family, Source Sans 3, with tabular figures everywhere.

## Colors

Restrained palette with a committed shell: neutrals tinted slightly cool, one teal, and a reserved
status set.

### Primary
- **Clinical Teal** (#0b6474): primary buttons, active tab bar and text, segmented-control
  selection, row-action text, step badges, "More info" links, KPI icons, focus ring. White on it is
  6.8:1.
- **Deep Band Teal** (#0a4f5c): the header band only. White on it is 9.2:1; the band's secondary
  text is #c6e2e6 (6.8:1).
- **Teal Tint** (#e3f1f3) and **Teal Edge** (#a9d0d6): hover fills, step badges, row-action borders,
  the default notification.

### Neutral
- **Cool Canvas** (#eef1f5): the page ground and tag fills.
- **Surface White** (#ffffff): cards, dialogs, fields, charts.
- **Inset** (#f6f8fa): row hover, empty states, disclosure bodies, dialog footers.
- **Hairline** (#dde3ea) and **Strong Hairline** (#c5ced8): dividers, card borders, the vitals-strip
  grid, the tab rule.
- **Control Edge** (#8592a0): form-field and secondary-button borders (3.2:1 on white).
- **Ink** (#16212c, 16.3:1), **Ink 2** (#3a4754, labels and tags) and **Muted** (#556170, 6.3:1 on
  white, 5.6:1 on the canvas): all text.

### Status (reserved)
- **Green** dot #2f9e5e, ink #1d7044, tint #e6f4ea: on track (live clock mode, Reliable, Improved).
- **Amber** dot #c98500, ink #8a5300, tint #fdf1d9: watch (above 80% of a target, Worth a look,
  Just meets the standard, simulation mode).
- **Red** dot #d1342b, ink #b42318, tint #fdecea: past target (late clocks, Below the standard).
- **Grey** #8e99a5: not applicable or no data.

### Named Rules
**The Lab Flag Rule.** In-range values print in plain ink with no fill. Only an out-of-range value
gets a flag: its ink turns the status ink and it sits on the status tint (clocks, KPI numbers,
chips). Every status ink passes 5:1 on its own tint.

**The Reserved Status Rule.** Green, amber and red never decorate and never label a data category.
The chart stages use their own validated hues (violet, rose, blue).

## Typography

**Body, data and labels:** Source Sans 3 (Google Fonts, weights 400, 600, 700), fallback Source Sans
Pro, system-ui. A humanist sans: open apertures hold up when a projector washes out contrast, its
compact width fits five clock columns and unit chips at 1024 px, and its true tabular figures keep
running clocks from jittering (verified: 1111, 0000 and 7777 measure the same width).

`font-variant-numeric: tabular-nums` is set on the whole page. No uppercase tracking: labels are
sentence case.

### Hierarchy
- **Display** (700, 44px, 1.05): the ERGent title on the start page only.
- **Headline** (700, 26px, 1.2): page titles (Live board, History).
- **Title** (700, 18px, 1.25): card titles; dialog titles at 19px.
- **Data** (700, 32px; 28px in 4-cell strips and at 1200px or narrower; 26px in Statistics): KPI
  numbers.
- **Clock** (700, 22px, tabular): running and final clocks.
- **Body** (400, 15px, 1.45): everything else; row titles 15.5px 700, row subtitles 14px muted.
- **Label** (600, 14px, Ink 2): field labels, KPI labels, legends.
- **Caption** (600, 12.5px, Muted): clock captions, unit zones, tags.

### Named Rules
**The One Family Rule.** Source Sans 3 carries every role, including chart text: SVG charts keep
their text as text (`svg.fonttype = none`) so the browser sets it in the page font.

## Layout

- Shell: centred column, max 1360px, 32px side padding (24px at 1200px or narrower, 16px at 640px).
- The header band is full width; its content aligns to the same 1360px column.
- Card grid gap 16px; card padding 20px 22px; rows 11px vertical.
- Supervisor Charts at desktop: filter bar in one row (1320px and wider), then control chart
  (1.9fr) beside Statistics and the zone map (1fr), then Delay by stage beside Capability, then
  Zone comparison full width.
- Actions tab: Suggested actions beside Actions taken, then Before and after (1.55fr) beside Result.
- Rows holding charts or the map align to the top, so no card stretches half-empty.
- Projector width (1200px or narrower): every chart takes the full width (control chart, delay by
  stage, before and after) so its text stays legible; Statistics and the zone map sit side by side;
  the ambulance columns take 1.45fr of their row against the map's 1fr.
- At 992px and narrower all two-column rows stack and strips become two columns.
- `scrollbar-gutter: stable` so screens of different heights never shift sideways.

## Elevation & Depth

Flat and tonal: depth comes from white on grey and hairlines, with one quiet shadow.

### Shadow Vocabulary
- **Resting** (`box-shadow: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.05)`): cards,
  the vitals strip, role cards.
- **Pop** (`box-shadow: 0 12px 32px rgba(16,24,40,.16), 0 2px 6px rgba(16,24,40,.08)`): dialogs,
  notifications, the date picker, map tooltips.
- Dialog backdrop: ink at 42% opacity, no blur.

## Shapes

- Radius: 4px (tags, clock flags, unit buttons), 6px (buttons, fields, unit cards, map frame,
  disclosure bodies), 8px (cards, strips), 10px (dialogs), pill (chips and counts), circle (dots,
  step badges, zone labels).
- Borders are 1px hairlines; no coloured side stripes anywhere.

## Components

### Header band
Deep Band Teal, 64px tall. On the start page the band grows by 176px into a hero: the ERGent title in
white, the sub line in band muted, and the two role cards sitting across the band's lower edge. White logo tile (38px, 6px radius) with the teal pulse icon; "ERGent"
19px 700 white; the sub line 13px in band muted. Role chip translucent white; status chips use their
status tint. On the band, selects are white fields, the primary button inverts to white with band
text, and secondary buttons are white-outline ghosts. Focus ring on the band is white.

### Buttons
- **Shape:** 6px radius, 600 weight.
- **Primary:** Clinical Teal fill, white text; hover #08535f; pressed #064450.
- **Secondary:** white, Ink text, Control Edge border; hover canvas-tinted.
- **Row action** (Dispatch, En route, On scene, Clear, Log this action): white, teal text, teal edge
  border, 32px tall; hover teal tint.
- **Ghost** (Targets, Log an action, Out of service): teal text with a teal edge; inside unit cards
  muted ink on a hairline.
- **Focus:** 2px Clinical Teal outline, 2px offset. Disabled: 45% opacity.

### Chips and tags
- **Chip:** pill, 13px 600, 3px 11px. Neutral chips are white with a strong hairline; status chips
  are flags (status tint, status ink, status line) with an 8px dot.
- **Tag:** 4px radius, canvas fill, Ink 2, 12.5px 600 (Zone E, P3, Replay, Cleared); red and amber
  tags use their flag colours.

### Cards / Containers
- White, 8px radius, 1px Hairline border, Resting shadow, 20px 22px padding. One title per card
  (18px 700) with an optional count pill or control on the right. No nested cards: Statistics uses
  the vitals-strip grid inside its card.

### Vitals strip (signature)
KPI cells joined by 1px Hairline gaps on a single bordered, rounded strip: figures and labels only,
like a report (the corner icons in the markup are not shown). Number in Data type, label below in
Label type. A flagged number takes the Lab Flag.

### Flow-sheet rows
Status dot (10px), bold title with tags, muted subtitle, actions, then clocks right-aligned in
tabular figures with a caption under each. Rows are divided by hairlines; hover fills Inset. On the
dispatcher board titles truncate to one line; on the supervisor screens they wrap, so suggestions
and logged actions are read in full.

### Ambulance columns
Status columns (Available, Responding, On scene, Out of service) whose heads share one grid row
(subgrid), so their rules and "None" line up when a label wraps. Unit cards are white, 6px radius,
hairline border.

### Inputs / Fields
White, Control Edge border, 6px radius, 38px tall, 15px text. Hover darkens the border to Ink 2;
focus is a teal border plus a 3px teal ring at 22%. The unit picker uses the same chevron. The
Chart radio group is a segmented control (selected segment teal with white text).

### Navigation
Underline tabs on the canvas: 15.5px 600 Muted; hover Ink; active Clinical Teal with a 3px teal bar
on the 1px Strong Hairline rule.

### Dialogs and notifications
White dialog (max 560px), 10px radius, Pop shadow, Inset footer with Cancel (secondary) and the primary action.
Notifications: message in teal tint, warning in amber flag, error in red flag.

### Charts (matplotlib)
White ground, grid #e3e8ee, spines #c5ced8, ticks and labels Muted, titles Ink 600, date labels
flat. Data series #2a78d6; control limits dashed Muted; the target (spec) line amber #b7791f (the
approved text calls it "the amber line"); flagged days red #d1342b; the action marker Clinical Teal
#0b6474 with a white-backed label (teal means action); baseline shading ink at 4%. SVG charts set
their text a step larger (stage ticks 13.5, box-chart ticks 11.5) because they scale with the card. Stage bars: processing #6250d6,
turnout #c8508a, travel #2a78d6, with 1.2px white gaps (validated for colour-blind separation and
3:1 contrast). Box plots fill #e7eef6 with Muted edges.

### Zone map (Leaflet)
Esri light-grey canvas tiles; zone outlines #33475b; zone fills from the status dots (#2f9e5e,
#e0a100, #d1342b, grey #8e99a5); zone labels as white discs with a dark ring; tooltips as white
Pop cards in the page font.

## Do's and Don'ts

### Do:
- **Do** print in-range values in plain Ink and flag only out-of-range ones (The Lab Flag Rule).
- **Do** keep every figure tabular and every label sentence case.
- **Do** give charts the full width at 1200px or narrower.
- **Do** use Clinical Teal for action, selection and focus, and nothing else.

### Don't:
- **Don't** use green, amber or red for decoration or for data categories.
- **Don't** float KPI numbers in separate cards; join them in the vitals strip.
- **Don't** box list rows or nest cards.
- **Don't** add uppercase tracked labels, glow, gradients, blur or coloured side stripes.
- **Don't** bring back the dark command-center ground of version 1.
