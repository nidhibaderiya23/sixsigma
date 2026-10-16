# Plan: Response Watch (Team ERG)
Statistics first, then the tool, then the screens. Formulas and known answers: `SPEC.md` section 4. Started Fri 17:53.

## Tasks
1. **H-01 SPEC** (`SPEC.md`) - 30 min. Test: `grep -c "FILL IN[.,]" SPEC.md` prints 0.
2. **H-02 data** (`data/`) - 60 min. `make_data.py` (seed 42) writes `calls_baseline.csv`, `calls_demo.csv`,
   `calls_messy.csv`, `actions_demo.csv`, and `data/README.md` is the codebook.
   Test: rerunning gives identical files; D's turnout rises after day 15; the messy file has every listed defect.
3. **H-03 statistics** (`app/qc.py`, `tests/`, `app/requirements.txt`) - 3 h. One function per item, each with a
   known-answer and a degenerate test (SPEC 4):
   - `stage_times` (stage = later stamp - earlier stamp; flags missing or out of order) | degenerate: missing stamp.
   - `summary` (mean, type-7 percentiles, % on time) | degenerate: n = 1.
   - `imr_limits` (center ± 3 MR̄/1.128; MR upper 3.267 MR̄) | degenerate: constant gives None.
   - `xbar_s_limits` (x̄̄ ± 3σ_s/√nᵢ, σ_s = √mean(sᵢ²); S: (c₄ ± 3√(1 - c₄²))σ_s) | degenerate: a 1-call day.
   - `flag_rules` (Western Electric 1-4 + 6 rising; slow side = alarm) | degenerate: under 8 points.
   - `capability` (Ppk, Cpk upper on logs; hidden if flagged) | degenerate: constant.
   - `anova_zones`, `welch_before_after` (scipy, on logs) | degenerate: a group with 1 value.
   - `impact_estimate` (cap stage at city median, recount on time) and `suggest` (rules below).
4. **H-04 tool** (`app/`) - 4 h, in layers:
   - **L1:** role picker; dispatcher board (status tables, clocks, ordered buttons, reason codes, fleet,
     alerts, live map, simulate, history). It reads `data/` through `qc.py` only.
   - **L2:** supervisor Overview and Charts.
   - **L3:** Actions and Control.
   - Test: `testme.sh` starts it; one data file shows the same numbers as the H-03 tests.
5. **H-08 (first half) + H-06 deploy** (`.github/workflows/`, `app/manifest.json`, `app/.python-version`) -
   1 h, right after L1. You add `CONNECT_SERVER` and `CONNECT_API_KEY` as GitHub secrets yourselves.
   Test: the public URL answers 200 when logged out.
6. **H-05 demo** (`demo/README.md`) - 45 min. A walkthrough of each CSV with exact clicks, numbers and
   "how to read this".
7. **H-07 docs** (`README.md`, `app/README.md`, plus `docs/six_sigma.md` for Define and Measure: problem
   statement, critical-to-quality target, SIPOC, process map, data-quality plan) - 60 min.
   A teammate follows it from a fresh clone.
8. **H-08 check** (`.gitignore`) - 20 min. A fresh clone passes `testme` and pytest; `git grep -i api_key` finds no key.

## Suggestion rules (each tested with a table built to trigger only it)
Stage excess = max(0, stage time - stage target). A stage's share = its excess / the zone's total excess.
- Turnout share ≥ 50% in a flagged zone → "Review crew readiness at Zone X's station" (names a shift holding ≥ 40% of the excess and ≥ 1.5× its share of calls).
- Travel share ≥ 50%, ≥ 30% of late calls coded "unit from another zone", and the zone borrows units ≥ 1.5× the city rate → "Consider posting an extra ambulance in X during hours H".
- Travel share ≥ 50% and "traffic or road closure" is the top code (≥ 3 calls, ≥ 30% of late calls) → "Check road works and alternative routes in X".
- Processing 90th percentile > 64 s in an hour window with above-median calls per hour → "Add dispatcher cover in that window".
- One ambulance with ≥ 2 breakdowns in the period → "Schedule preventive maintenance for that ambulance".
- "Unclear address" in ≥ 20% of late calls → "Use an address-verification script".
- Slip-back alert: after an action, any flag on the after-action limits brings the zone back to amber or red.

## Decisions (approved by the team, Oct 16)
- Stages: processing, turnout and travel; the headline is dispatch to on scene. Reasons: automatic factors plus a code when late.
- Fields: ambulance ID and home zone, distance, dispatcher ID, weather. Dispatcher stats are by shift and workload, not by person.
- Roles: a start-page picker. Dispatcher: queue and status tables, fleet, alerts, live map, weekly and monthly history, full poka-yoke.
- Supervisor: Overview, Charts and Actions (not DMAIC tabs). Define and Measure live in the docs.
- Charts: I-MR, daily X̄-S (the course's method, not a p-chart), stage breakdown, capability, ANOVA and Welch (on logs).
- Actions: rules with an impact estimate, an action log, before/after, slip-back alerts. No Pareto, fishbone or control plan.
- Targets: NFPA 1710 (64 s, 60 s, 480 s; P1 = 9 min), P2 15 and P3 20 assumed, all editable. 6 zones; demo: D turnout and C travel.
- Live data comes from simulation plus manual entry, with a separate board per browser. There are two maps, live and history.

## Biggest risks
1. **Too much to build.** We build in layers and deploy after L1, so a working version always exists. L3 is cut first.
2. **A wrong statistic looks fine.** No screen work starts until H-03's known-answer tests pass, and every number on screen
   comes from `qc.py`.
3. **The deploy fails late.** We deploy right after L1, with Python 3.12 (this Mac has 3.15; Connect may not).
