# Demo: Response Watch on every test dataset

A step-by-step walkthrough that anyone can follow and get the same numbers. All data is synthetic
(see [`data/README.md`](../data/README.md)). Every number below comes from `app/qc.py`. The
"How to read it" lines are what to say to a judge.

## 0. Start the app

```bash
cd app && ./testme.sh
```

Open http://localhost:8000. You see the start page with two buttons: **I'm a dispatcher** and
**I'm a supervisor**. ("Switch role", top right, brings you back here.)

---

## 1. The demo city, before the fix (`data/calls_demo.csv`, as of Sep 28)

Click **I'm a supervisor**. In the Settings card, keep **Dataset: Demo city**, **Priority 1** and
**Chart period: Last 28 days**. Then click **Jump to Sep 28 (before the fix)**.

### 1.1 Overview: "Is everything okay?"

| Tile | Shows |
|---|---|
| Average (what 911 sees) | 5.8 min |
| Median call | 5.3 min |
| 90th percentile | 8.8 min |
| 95th percentile | 10.1 min |
| On time | 91% |
| Zones flagged | 1 / 6 |

- Zone health: **Zone D is red ("Act now")**. Its 90th percentile is 10.2 min against the 9-min
  target. Rules 1, 2, 3 and 4 fired, and turnout causes 99% of its minutes over target. Every other
  zone is green.
- The history map shows the D tile red, labelled "Crew turnout".

**How to read it:** the average (5.8 min) looks fine, but 1 in 20 patients waited over 10 minutes.
That is the prompt's "monthly averages hide fatal outliers". Only Zone D is out of control *and*
missing its target, and the delay is the crew getting out the door, not the drive.

### 1.2 Charts: "What is happening, and why?" (zone selector: Zone D)

- **Daily X̄-S chart:** red dots on 14 days: 2 inside the baseline (Sep 10-11) and every day from Sep 16 on. The daily average sits
  well above the dashed control limits. The note under it reports that 2 baseline days are flagged
  (Sep 10-11).
  **How to read it:** each dot is one day's typical response. The limits come from the first 14
  days. Red means "slower than this zone's own normal", a special cause.
- **I-MR chart:** 211 calls. 19 calls are beyond the upper control limit (extreme single delays),
  and 30 calls are over the amber 9-min target line.
  **How to read it:** the dashed lines are control limits, from the process. The amber line is the
  target, from the standard. They are different things.
- **Stage breakdown:** in the share chart, Zone D's bar is 92% turnout (amber), while every other
  zone is mostly travel (blue).
- **Capability:** Ppk is A 0.68, C 0.54, E 0.57 and F 0.58 (98.0%, 94.7%, 95.7% and 96.0%
  expected on time). Zones B and D show "not stable: capability is not meaningful".
  **How to read it:** capability is only fair to judge for a stable process. Ppk 0.43 is the point
  where 90% on time is just met.
- **Tests:** one-way ANOVA F = 9.31, p = 1e-08 (df 5, 1246): zones really differ. The normal
  probability plot shows how close Zone D's log times are to normal.

### 1.3 Actions: "How do we fix it, and did it work?"

Suggestions from the data:
1. **Crew readiness, Zone D:** "Review crew readiness at Zone D's station, especially the night
   shift (50% of the turnout delay from 16% of the calls)". Estimate: on time 78% → 97%.
2. **Dispatcher cover, citywide:** "Add dispatcher cover during 17:00-19:00". Estimate: on time
   68% → 100% for processing in those hours.

Click **Log this action** on the Zone D suggestion. The dialog is prefilled with Zone D, crew
turnout and start date 2026-09-29. Click **Save action**. (The demo file already has this action
as A1, so you'll see "Already in the log as A1".)

**How to read it:** each suggestion is a fixed if-then rule, shown with its evidence. The impact
is a best-case estimate. A qualified person decides; the tool decides nothing.

---

## 2. The demo city, after the fix (as of Oct 12)

Click **Jump to the latest day**.

- **Overview:** average 5.6, median 5.2, 90th percentile 7.9, 95th percentile 9.0, on time 95%.
  Zones flagged: 2 / 6.
  - **Zone D is green again.**
  - **Zone C is amber:** 90th percentile 9.2 min, with travel 88% of the minutes over target. This is
    the planted weekday rush-hour road works.
  - **Zone B is amber:** rules 2 and 4 fired, travel 91%. B covers for its struggling neighbors.
  - Zone A is green, with "one weak signal (rule 4): not enough on its own, keep watching".
- **Actions, suggestions:**
  - "Check road works and alternative routes in Zone C (weekdays 16:00-19:00)": 92% → 100%.
  - "Consider posting an extra ambulance in Zone B during 17:00-20:00": 93% → 100%.
  - "Add dispatcher cover during 17:00-19:00": still there.
- **Actions, before and after** (pick **A1: Zone D, 2026-09-29**):

| Number | Before | After |
|---|---|---|
| Median response | 6.8 min | 5.2 min |
| On time | 78% | 97% |

Verdict: **Improved**. Welch's t-test, one-sided, on log response time: t = 6.57, df = 207,
p = 2e-10 (113 calls before, 98 after). The after-period chart, with its own new limits, shows no
flags: **the new level is stable**. The chart below marks the action with a green line.
- **Slip-back watch:** "no zone is drifting back after a logged action."

**How to read it:** this is the Improve and Control steps of DMAIC. The fix is logged, the
statistics confirm it worked, and the tool keeps watching for a slide back.

---

## 3. The baseline city (`data/calls_baseline.csv`, stable)

In Settings, choose **Dataset: Baseline city** (the as-of date moves to its last day, Sep 28).

- **Overview:** average 5.5, median 5.1, 90th percentile 7.8, 95th percentile 9.3, on time 94%.
  - Zones flagged: 1 / 6. Zone C is amber, with a 90th percentile of 9.3 min against the 9-min
    target. It is the biggest zone, with longer trips; there are no chart flags.
  - All other zones are green.
- **Charts (Zone D):** no flagged days, and no I-MR call beyond the upper limit.
- **Capability:** shown for all six zones. Ppk is A 0.64, B 0.60, C 0.53, D 0.58, E 0.71 and F 0.58.
- **Tests:** ANOVA F = 2.11, p = 0.062, so there is no evidence that zones differ.
- **Actions:** no suggestions.

**How to read it:** a stable city gives a quiet dashboard. That is the point of control limits:
they do not cry wolf.

---

## 4. The messy file (`data/calls_messy.csv`, data errors)

In Settings, choose **Dataset: Messy file**.

- **Overview, data quality:** "7 call(s) left out of the statistics":
  - C00002 and C00008: on_scene before en_route;
  - C00004: duplicate call_id;
  - C00009, C00024 and C00045: missing en_route;
  - C00027: dispatched before call_received.
- **Zone health:** zones C and F show "Not enough data". Zone B is amber because of a real,
  valid 25-minute call (C00038): its 90th percentile is 16.0 min.
- **Charts:** capability prints no meaningless numbers: zones A, B, D and E say "too few calls for
  capability" (n = 7, 6, 4 and 4; need 30), and C and F say "need at least 2 values".
- Nothing crashes, and no defective call enters any statistic.

**How to read it:** bad data is caught and listed, never silently averaged in. Mistake-proofing at
the source (the dispatcher's buttons) stops most of it from happening at all.

---

## 5. The dispatcher's live board

Click **Switch role**, then **I'm a dispatcher**.

1. **Simulate a shift:** Day 2026-09-20, Speed 120x, Start at "Evening shift, 14:00". Click
   **Simulate a shift**.
   - The header chip turns to "SIM 120X" and the clock runs fast.
   - Calls appear in Incoming, then move through Dispatched, En route, On scene and Resolved at
     their recorded times.
   - Clocks turn amber at 80% of a stage target and red past it, and the zone map tiles change color.
   - Click **Reset** when done.
2. **Log a call by hand:** Zone D, Priority 1, then **Add call**. The received time is stamped from
   the clock. Pick a unit and click **Dispatch**.
   - Wait more than 60 seconds, then click **En route**: a dialog asks *why* turnout was late. Pick
     "Crew not ready" and save.
   - Then click **On scene**, then **Clear** (it asks for confirmation).
   - Only the next valid button is ever shown. This is the poka-yoke.
3. **Fleet board:** click **Out of service** on an en-route ambulance. Its call is flagged, and the
   reason "Ambulance breakdown" is recorded when it arrives.
4. **History tab:** Demo, last 7 days, priority 1. The All row shows 295 calls, average 5.6,
   median 5.2, 90th percentile 7.9, 95th percentile 9.0 and 94.9% on time. Zone C's row has the
   lowest on time (86.7%).
5. **Download calls (CSV):** saves this session's calls in the same format as `data/calls_*.csv`.

---

## What each dataset proves

| File | Behavior | What the tool shows |
|---|---|---|
| `calls_demo.csv` | Planted problems: D turnout (Sep 15-28, fixed Sep 29), C rush-hour travel (from Sep 20), peak-hour dispatch overload, ambulance M-B2 breakdowns | D red then fixed and confirmed; C amber with a routes suggestion; dispatcher-cover suggestion |
| `calls_baseline.csv` | Stable city | No chart flags; capability shown for all zones; no suggestions |
| `calls_messy.csv` | 7 planted data errors, tiny zones, one extreme valid call | Errors listed and excluded; "not enough data" instead of fake numbers |
