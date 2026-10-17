# PRODUCT.md: ERGent (Team ERG)

## What it is

ERGent is a Shiny for Python quality-control tool for the 911 EMS dispatch center of
Ithaca, NY. It logs every call's timestamps live, replaces monthly averages with
percentiles and control charts that catch the slow outliers, splits each delay into
stages (dispatch processing, crew turnout, travel) to show why, and flags which zone
needs resolution. Built for the Cornell Six Sigma Hackathon (on-campus track).

## Who uses it, and where

| Role | Task | Scene |
|---|---|---|
| Dispatcher on shift | See which open call is running late right now; log, dispatch and clear calls | A dispatch console, under time pressure; glances, not reading |
| EMS operations supervisor | At the start of each shift: which zone needs attention, which stage causes it, which fix to try, and whether a fix worked | A desk in daylight, reading statistics with care |
| Classmates and the professor | Follow the statistics in a live demo | A lit classroom, a 1024 px projector |

Each person picks a role on the start page and gets their own screens:

- **Dispatcher:** Live board (log a call; incoming, dispatched, en route and resolved lists
  with running clocks; ambulance columns; a live zone map; a shift replay, "Simulate a
  shift"), and a History tab (box chart by zone, suggested actions).
- **Supervisor:** Charts (control bar, daily X-bar and S chart or every-call chart,
  statistics, zone map, delay by stage, zone comparison, capability) and Actions
  (suggested actions, action log, before and after).

## Mode

Operate. The tool must disappear into the task: scanability, consistency and familiar
controls outrank expression.

## Product truths that the design must keep

- Every number on screen comes from `qc.py`; the design never changes a value, a label
  or the approved wording.
- Green / amber / red mean on track / watch / past target, and are used for status only.
- The target line on charts is amber (the spec limit, NFPA 1710); control limits are
  dashed grey. The two are never confused.
- The data is synthetic and says so ("Synthetic data" chip on the supervisor screens).
- The zones are illustrative areas of Ithaca, not official EMS districts.

## Brand commitments

- Identity for version 4: "Civic Ithaca", as if the City of Ithaca's emergency services
  commissioned it. Deep navy and one safety orange; civic, sturdy and trustworthy.
- No kitsch: no sirens, no fake badges, no Star of Life, no emergency-light effects.
