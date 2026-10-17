# PRODUCT: ERGent (version 7, "Friendly modern")

## What it is
ERGent is Team ERG's quality-control tool for the 911 EMS dispatch center of Ithaca, NY
(Cornell Six Sigma Hackathon, prompt "Emergency Response"). It is a Shiny for Python app with two
roles, picked on a start page:

- **Dispatcher**: a live board. Log a call, then follow it through incoming, dispatched, en route
  and resolved, each with a running clock against its target; see the ambulances by status and a
  live zone map of Ithaca; replay a shift ("Simulate a shift"). The History tab shows response time
  by zone (box chart) and suggested actions.
- **Supervisor**: the Charts tab (control bar, daily X-bar and S control chart, statistics, zone
  map, delay by stage, zone comparison, capability) and the Actions tab (suggested actions, action
  log, before and after).

Every number on screen comes from `app/qc.py`; the data is synthetic and labelled as such.

## Users and their scene
- **Dispatchers** work under time pressure and glance at the board between calls: the state of
  every open call must read in a second, and status colour must mean only status.
- **Supervisors**, plus **classmates and a professor** who are not statistics experts, read the
  charts. This afternoon they see it on a classroom projector (1024 px wide) and laptops (1440 px)
  in a lit room. That scene asks for a light theme with strong text contrast.

## Mode
Operate (app UI). Familiar controls and layout; the design lives in type, colour, spacing and
detail, never in new affordances.

## Fixed product truth (do not change)
- Every Shiny input and output id, every feature, button and number.
- The wording of the texts (short, professional, team-approved).
- Status colours: green = on track, amber = watch (over 80% of a target), red = past a target.
  They are used for status only.
- Statistics in `qc.py`, the shift model in `simulator.py`, the zones in `zonemap.py`, tests, data.

## Brand commitments
- Name: ERGent, by Team ERG. Logo: the pulse line in a rounded tile.
- Version 7 direction (pinned by the team brief): **Friendly modern**, an approachable
  health-tech product: warm, clear and reassuring, never childish.

## Direction contract (v7)
- THESIS: a calm, light clinical product that makes a live 911 board feel legible to a first-time
  user; it refuses the dark command-center wall and the generic grey admin template.
- OWN-WORLD: lake-mist ground, white raised panels with soft shadows instead of borders, one
  Cayuga-lake blue for actions and selection, status shown as soft tinted pills with darker ink;
  Figtree with tabular figures; 14-24 px radii.
- STORY: a dispatcher sees which call is late at a glance; a supervisor sees which zone needs
  attention and why, and can explain each number to the class.
- FIRST VIEWPORT: white app bar (logo tile, name, role chip, controls), a segmented tab control,
  then the page title with live clocks, a row of icon-tiled counts, and the working cards.
- FORM: the existing two-role Shiny layout, restyled; seed: none (unavailable).
- FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the
  verdict, DESIGN.md, and every shipping raster carrying its provenance.
