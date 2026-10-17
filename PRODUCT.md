# PRODUCT.md: ERGent (version 6, "Ops console")

## What it is
ERGent is Team ERG's statistical quality-control tool for the 911 EMS dispatch center of
Ithaca, NY (Cornell Six Sigma Hackathon, Health Systems prompt: Emergency Response). It logs
every call's timestamps live, replaces monthly averages with percentiles and control charts,
splits each delay into stages (dispatch processing, crew turnout, travel) and flags the zones
that need attention. A Shiny for Python app; every number comes from `app/qc.py`.

## Who uses it, and where
- **Dispatcher on shift (live board).** Seated at a multi-monitor console in a dim dispatch
  room, eyes moving between the CAD, the radio and this board, under time pressure. Needs to
  see in one glance which open call is running late, which unit is free and which zone is red.
- **EMS operations supervisor (Charts, Actions).** Same room or an office, at the start of a
  shift or when a flag fires. Reads the control chart, the statistics and the capability verdicts
  to decide which zone and which stage to fix, then checks whether the fix worked.
- **Classmates and the professor (demo).** Non-experts reading the statistics on a 1024 px
  laptop projector; every number must be explainable by the team.

## Surface mode
**Operate.** App UI: scanability, consistency and familiar controls outrank expression.

## Brand and product commitments
- Name: ERGent (Team ERG). City: Ithaca, NY. Version label in the header: `v6`.
- Green / amber / red mean on track / watch / past target, and are used for status only.
- Short, professional texts approved by the team: wording does not change.
- The statistics are the graded core; the UI never changes a number, a test or a feature.
- Synthetic data is labelled as synthetic ("Synthetic data" chip).

## Constraints
- Shiny for Python with Bootstrap 5 parts (selects, modals, notifications, date picker).
- Fonts from Google Fonts only; scripts only Leaflet (unpkg). No new Python packages.
- Must work at 1440 px and on a 1024 px projector; WCAG AA contrast, visible focus,
  `prefers-reduced-motion` respected.
