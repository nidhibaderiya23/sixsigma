# ERGent — product

ERGent is Team ERG's Cornell Six Sigma Hackathon tool: a Shiny for Python app for the
911 EMS dispatch center of **Ithaca, NY**. It tracks dispatch-to-on-scene response time
and tells a supervisor which zone needs attention and whether a fix worked. All data is
synthetic and labelled as such.

## Users and their scene

| Role | Who | Scene | Success |
|---|---|---|---|
| Dispatcher | A trained call-taker / dispatcher | Working a live board under time pressure, glancing between calls | Sees at once which open call is past its target, dispatches a free unit in two clicks |
| Supervisor | EMS shift supervisor | At a desk, reading the shift's statistics; this afternoon also projected to a class | Understands which zone is out of control or below standard, and why, without being a statistician |
| Classmates / professor | Non-expert readers | Reading a projected screen at 1024 px | Can follow every number and its plain-language interpretation |

## Surfaces and mode

- **Start page** — pick a role. Operate.
- **Dispatcher: Live board, History** — Operate, dense and glanceable. Running clocks,
  status dots, unit columns, live zone map, shift replay.
- **Supervisor: Charts, Actions** — Operate leaning to Read. A statistical quality report:
  X̄-S control chart, statistics, zone map, delay by stage, zone comparison (ANOVA),
  capability (Ppk / Cpk), suggested actions, action log, before/after test.

## Product truths the design must keep

- **Status colours mean status only:** green = on track, amber = watch (above 80% of a
  target), red = past target. Never used for decoration, brand or categories.
- The target (an NFPA 1710 spec limit) is the **amber line** on charts; control limits are
  dashed grey. The copy refers to "the amber line", so the target stays amber.
- Every number on screen comes from `app/qc.py`; the UI never computes statistics.
- Texts are short, professional and approved by the team; the design does not reword them.
- Every Shiny input/output id, feature and button stays as it is.
- Must work at 1440 px and on a 1024 px classroom projector; WCAG AA contrast, visible
  focus, reduced motion respected.

## Constraints

- Shiny for Python + Bootstrap 5 (bslib). Only Google Fonts and Leaflet (unpkg) load from
  outside. No new Python packages.
- Charts are matplotlib (PNG for the daily / every-call charts, inline SVG with hover
  tooltips for delay-by-stage and the zone box chart).
- The map is Leaflet with Esri canvas tiles; the script reads its colours from CSS variables.
