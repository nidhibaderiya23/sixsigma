# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Dispatcher on shift** at the 911 EMS dispatch center of Ithaca, NY. Works the live board under
  time pressure, often at night in a dimmed room across several monitors. Needs to see at a glance
  which open call is running late and press the next step for it.
- **EMS operations supervisor** (primary user in the spec). At the start of each shift, and when a
  flag fires, decides which zone needs attention, which stage is causing it (dispatch processing,
  crew turnout or travel), which fix to try, and later whether the fix worked.
- **Non-expert readers of the statistics**: the professor and classmates at the Cornell Six Sigma
  Hackathon showcase, usually seeing the app on a 1024 px projector.

## Product Purpose

ERGent (Team ERG) replaces the 911 center's monthly averages with live stage clocks, percentiles,
control charts and capability verdicts per zone, so slow outliers are caught, the stage that causes
them is named, and the zone that needs resolution is flagged. Success: a dispatcher spots a late call
in seconds, and a supervisor can explain every number on screen.

## Operating Context

- Shiny for Python app; two roles picked on a start page (Dispatcher, Supervisor).
- Dispatcher: Live board (log a call, incoming / dispatched / en route / resolved lists with running
  clocks, ambulance columns, a live Leaflet zone map) and History (box chart by zone, suggested
  actions). A shift replay ("Simulate a shift") drives the board for demos.
- Supervisor: Charts (control bar, daily X-bar and S chart, statistics, zone map, delay by stage,
  zone comparison, capability) and Actions (suggested actions, action log, before and after).
- Six illustrative zones A to F laid over Ithaca; they are not official EMS districts.

## Capabilities and Constraints

- Every statistic comes from `app/qc.py` and is unit tested; the UI only draws and formats.
- Status colours have one fixed meaning: green on track, amber watch (above 80% of a target), red
  past target. They are used for status only.
- The target line (NFPA 1710 spec limit) is amber on every chart, and the copy refers to it as the
  amber line.
- The team approved short, professional texts; designs change markup and styling, not wording.
- Fonts from Google Fonts only; scripts limited to Leaflet (unpkg); no new Python packages.

## Brand Commitments

- Name: ERGent, by Team ERG. A pulse-line mark.
- Dark interface for the dispatch room.

## Evidence on Hand

- Synthetic call data in `data/` (demo 42 days, baseline 28 days, a messy 3-day file), labelled
  "Synthetic data" in the supervisor header. No real call records exist; none may be presented as real.

## Product Principles

1. Correct statistics first; a plain page around a correct analysis beats a polished wrong one.
2. Status is never decoration: a colour on screen always means on track, watch or past target.
3. Every number shown can be explained by the team in one sentence.
4. The tool suggests; qualified staff decide.

## Accessibility & Inclusion

WCAG AA contrast, visible keyboard focus, `prefers-reduced-motion` respected. Must read on a 1024 px
projector and at 1440 px. Status is never carried by colour alone (dots sit beside words and clocks).
