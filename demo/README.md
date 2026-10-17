# Demo: ERGent on every test dataset

A step-by-step walkthrough of ERGent (version 2 and later; Ithaca, NY) that anyone can follow and get the same numbers. All
data is synthetic (see [`data/README.md`](../data/README.md)). Every number below comes from
`app/qc.py`. The "How to read it" lines are what to say to a judge.

## 0. Start the app

```bash
cd app && ./testme.sh
```

Open http://localhost:8000. You see the start page with two buttons: **I'm a dispatcher** and
**I'm a supervisor**. ("Switch role", top right, brings you back here.)

---

## 1. The demo city, before the fix (`data/calls_demo.csv`, as of Sep 28)

Click **I'm a supervisor**. The **control bar** at the top of **Charts** sets everything. Keep
**Dataset: Ithaca demo (42 days)**, **Priority 1: Life-threatening** and **Chart period: Last 28 days**,
and set **As of** to 2026-09-28 (type it, or pick it in the calendar).

Every card has one plain title. A **More info** toggle under it opens a short explanation.

### 1.1 Statistics and Zone map

| Statistics (Sep 01 to Sep 28, 1252 calls, all zones) | Shows |
|---|---|
| Average | 5.6 min |
| Standard deviation | 1.9 min |
| On time | 93% |
| Zones flagged | 1 / 6 |

- **Zone map:** **Zone D is amber ("Worth a look")**, labelled "Crew turnout". Hover the tile: "90th
  percentile 10.2 min vs. 9 min target; turnout causes 99% of minutes over target". Every other zone is
  green ("On track").

**How to read it:** the average (5.6 min) looks fine. Zone D alone is missing its target: its 90th
percentile is 10.2 min, and the delay is the crew getting out the door, not the drive.

### 1.2 The other Charts cards (zone selector: Zone D)

- **Control chart, Daily chart:** **no red dots.** Be upfront about this. The chart period is also the
  window that sets the control limits (a center of 5.9 min, a normal range of about 3.3 to 10.5 min).
  Zone D's slowdown began on Sep 15 and is inside that window, so it widens the limits and hides
  itself. The daily dots do sit above the center on most days from Sep 15 (up to 8.3 min).
  **How to read it:** read the daily chart together with the cards below. They do show the problem.
- **Control chart, Every call** (switch the Chart toggle): 211 calls. 2 are above the upper control
  limit, and 30 are over the amber 9-min target line. More info says: "Each dot is one call. 2 calls were
  above the upper control limit (unusual delays worth checking one by one) and 30 missed the 9-min
  target (amber line)."
- **Delay by stage** (Sep 01 – Sep 28, priority 1): Zone D's bar is 92% turnout (amber), while every
  other zone is mostly travel (blue). Hover a bar for its share, the minutes over target and the
  median time.
- **Zone comparison:** "Yes. Zone D is typically 6.0 min against 4.9 min in Zone A; a gap this big is
  very unlikely to be chance." More info shows the one-way ANOVA (F = 9.31, p = 1e-08) and the normal
  probability plot.
- **Capability:** A, B, C, E and F are **Reliable** (about 98, 96, 95, 96 and 96 calls in 100 within
  9 min). **Zone D is Below the standard**: "Only about 89 in 100 calls within 9 min." The Ppk numbers
  (A 0.68, B 0.60, C 0.54, D 0.42, E 0.57, F 0.58) are only in More info.
  **How to read it:** a zone needs about 90 in 100 on time to meet the standard. D does not.

### 1.3 Actions

The context line reads "Ithaca demo (42 days) · Priority 1: Life-threatening · as of Sep 28". Under
**Suggested actions**, in this order:
1. **Crew readiness, Zone D:** "Review crew readiness at Zone D's station, especially the night shift
   (50% of the turnout delay from 16% of the calls)". Estimate: on time 78% → 97%.
2. **Dispatcher cover, citywide:** "Add dispatcher cover during 17:00-19:00". Estimate: on time 68% →
   100% for processing in those hours.

Click **Log this action** on the Zone D suggestion. The dialog is prefilled with Zone D, crew turnout
and start date 2026-09-29. Click **Save action**. (The demo file already has this action as A1, so
you'll see "Already in the log as A1".) **Actions taken** lists A1, tagged "After the as-of date".
The **Result** card says "Not enough data": at Sep 28 the fix has not started yet.

**How to read it:** each suggestion is a fixed if-then rule, shown with its evidence. The impact is a
best-case estimate. A qualified person decides; the tool decides nothing.

---

## 2. The demo city, after the fix (as of Oct 12)

Set **As of** to 2026-10-12 (the default).

- **Statistics** (Sep 15 to Oct 12, 1251 calls): average 5.7 min, standard deviation 2.0 min, on time
  93%, zones flagged 1 / 6.
- **Zone map:** **Zone D is green again.** **Zone C is amber:** 90th percentile 9.2 min, with travel
  causing 88% of the minutes over target. This is the planted weekday rush-hour road works. Zone A is
  green, with "one weak signal (8 days in a row above normal, rule 4)" in its hover text.
- **Control chart:** pick Zone A: 4 red days (Oct 5 to 8).
- **Capability:** A is **Can't judge yet** ("Times changed in this period, so no score yet."). B is
  Reliable (about 95 in 100). C **Just meets the standard** (about 94 in 100: little margin). D is still
  **Below the standard** (about 89 in 100), because the 28-day period still contains the slow days
  before the fix. E and F are Reliable.
- **Zone comparison:** "Yes. Zone D is typically 6.0 min against 5.2 min in Zone A..."
- **Actions, Suggested actions:**
  - "Check road works and alternative routes in Zone C (weekdays 16:00-19:00)": 92% → 100%.
  - "Add dispatcher cover during 17:00-19:00": 60% → 100%.
- **Actions, Result** (the action list shows **A1: Zone D, 2026-09-29**):

| | Before | After |
|---|---|---|
| Mean | 7.2 min | 5.5 min |
| Standard deviation | 2.3 min | 1.8 min |
| On time | 78% | 97% |
| Calls | 113 | 98 |

The chip says **Improved**. In More info: Welch's t-test, t = 6.57, p = 2e-10, and "The new level is
steady." The **Before and after** chart marks the action with a green line.
- **Slip-back watch:** no zone is drifting back after a logged action, so the slip-back card does not
  appear.

**How to read it:** this is the Improve and Control steps of DMAIC. The fix is logged, the statistics
confirm it worked, and the tool keeps watching for a slide back.

---

## 3. The baseline city (`data/calls_baseline.csv`, stable)

In the control bar, choose **Dataset: Ithaca baseline (28 days)** (the as-of date moves to its last day,
Sep 28).

- **Statistics** (Sep 01 to Sep 28, 1266 calls): average 5.4 min, standard deviation 1.7 min, on time
  96%, zones flagged 1 / 6.
- **Zone map:** Zone C is amber, with a 90th percentile of 9.3 min against the 9-min target (travel
  causes 99% of its minutes over target). It is the biggest zone, with longer trips. All other zones
  are green.
- **Control chart (Zone D):** no red dots. Every call: 215 calls, none above the upper limit, 11 over
  the target.
- **Capability:** all six zones are **Reliable** (about 97, 96, 95, 96, 98 and 96 calls in 100 within
  9 min).
- **Zone comparison:** "No clear difference: the gaps between zones could be chance." (F = 2.11,
  p = 0.062, in More info.)
- **Actions:** "No suggested actions for this period."

**How to read it:** a stable city gives a quiet dashboard. That is the point of control limits: they do
not cry wolf.

---

## 4. The messy file (`data/calls_messy.csv`, data errors)

In the control bar, choose **Dataset: Messy file (3 days)** (the as-of date moves to Sep 3).

- **Data quality (7 left out):**
  - C00002 and C00008: on_scene before en_route;
  - C00004: duplicate call_id;
  - C00009, C00024 and C00045: missing en_route;
  - C00027: dispatched before call_received.
- **Statistics** (Sep 01 to Sep 03, 22 calls): average 6.0 min, standard deviation 4.4 min, on time
  95%.
- **Zone map:** zones C and F show "Not enough data". Zone B is amber because of a real, valid
  25-minute call (C00038): its 90th percentile is 16.0 min.
- **Capability:** no meaningless numbers. Zones A, B, D and E say **Not enough calls** ("Only 7 calls;
  30 are needed.", and 6, 4 and 4 calls for B, D and E). Zones C and F say **Can't judge** ("need at
  least 2 values").
- Nothing crashes, and no defective call enters any statistic.

**How to read it:** bad data is caught and listed, never silently averaged in. Mistake-proofing at the
source (the dispatcher's buttons) stops most of it from happening at all.

---

## 5. The dispatcher: live board and History

Click **Switch role**, then **I'm a dispatcher**. The header shows **ERGent** with the subtitle "Team
ERG · City EMS dispatch · v1". The simulation controls sit in the header, to the left of **Switch
role**: **Day** (default Sep 20), **Speed** (30x, 60x, 120x), **Start** (00:00, 06:00, 14:00, 22:00), a
coral **Simulate a shift** button and **Reset**. A chip shows the clock mode. Right now it says
`LIVE 1x` (real time).

1. **Header controls: Simulate a shift.** Choose Day Sep 16, Speed 120x and Start 06:00, then click
   **Simulate a shift**.
   - The chip changes to `SIM 120x`. The button becomes **Pause** (then **Resume**, and **Run again**
     when the day ends).
   - The board clock (the time chip on the Live board) now runs 120 times faster than real time.
2. **Watch the board.**
   - The top row counts Waiting, Dispatched, En route, On scene and Units available.
   - The cards are numbered in call order: **1 Log a call**, **2 Incoming calls**, **3 Dispatched**,
     **4 En route**, **5 Resolved**. Calls appear in card 2, then move to cards 3 and 4 at the times in
     the file. Replayed rows carry a **Replay** tag and no buttons: they are read-only.
   - Each running clock is green, turns amber above 80% of its stage target, and red past it. The
     **Zone map** tile of a zone takes the worst clock colour in it.
   - **Ambulances** are grouped in four status columns with counts: **Available**, **Responding**
     (dispatched or en route), **On scene** and **Out of service**.
   - A call that reaches the scene moves to **5 Resolved** (full width, scrolls, latest 60) with its
     final response time, tagged **At the scene** and **Replay**. A cleared call shows **Cleared**.
3. **History tab.** Click **History** while the simulation runs. It shows the current shift and the
   previous one, following the simulated clock, and refreshes about every 5 seconds.
   - At about 06:46 on the simulated clock, the label reads `Current: day shift 06:00-14:00, Sep 16 ·
     Previous: night shift 22:00-06:00, Sep 15`.
   - Four tiles come first: **Calls** (about 25), **Mean** (about 6.1 min), **Standard deviation**
     (about 2.3 min) and **On time** (about 88%), for all priorities. The numbers keep changing as the
     clock runs.
   - The **Response time by zone** chart is on the left (about 72% of the width). Its **Priority**
     dropdown starts at Priority 1. Choose **Priority 2: Urgent**: **Zone D is a red diamond.** **Hover
     it**: "Zone D is slower than the city: 9.3 min typical vs. 6.3 min. Main cause: crew turnout (100%
     of minutes over target). Top reason: crew not ready (2 of 2 late calls)." The note under the chart
     says Zone D is slower and that Zones E and F are faster than the city (check the data). Each zone
     is a box plot of its calls, the grey line is the city center, the dashed lines are each zone's
     control limits, and the amber line is the target.
   - On the right (about 28%) are the **Suggested actions**, one compact row each, with the evidence in
     muted type. Around then you should see a **Station alert** for Zone D ("Alert Zone D's station:
     crews are slow to get rolling", with a median turnout of about 6 minutes against the 1-minute
     target) and perhaps a **Route** tip for Zone A. The note reads "For the dispatcher's judgment; the
     tool decides nothing on its own."
   - **How to read it:** a red diamond is a zone slower than the city as a whole; hover it for the
     reason.
4. **Reset to zero.** Click **Reset**. All replay and hand-logged calls disappear. Waiting, Dispatched,
   En route and On scene all show 0, Units available shows 12, Resolved is empty, and the chip goes
   back to `LIVE 1x` on real time.
5. **Log a call by hand, at 60x.** On the **Live board**, in **1 Log a call**, choose Zone D, Priority
   **1: Life-threatening** and **Clock speed** 60x, then click **Add call**.
   - The chip says `LIVE 60x`. One real second is one minute on the board clock. (The board clock now
     runs ahead of real time, and the History shift label follows it.)
   - The call appears in **2 Incoming calls** with a unit picker (home-zone units first) and
     **Dispatch**. Its Waiting clock turns amber, then red past 1:04, within about a second.
   - Click **Dispatch**. The stage already ran late, so a dialog "Why was this late?" asks for one of
     the 6 delay reasons. Pick "Unclear address" and click **Save reason and continue**. The time you
     pressed the button is kept.
   - The call moves to **3 Dispatched**. Its turnout clock (target 1:00) turns red within a second or
     two. Click **En route** and give a reason ("Crew not ready"). It moves to **4 En route**, which
     shows Travel (target 8:00) and Total clocks. Click **On scene**. A response past its target also
     asks for a reason.
   - The call now sits in **5 Resolved** with its response time and a small **Clear** button. Click
     **Clear**, then confirm "Clear call ...?". The row shows **Cleared**, and the ambulance is free
     again.
   - Only the next valid button is ever shown. This is the poka-yoke.
6. **Ambulances.** In **Ambulances**, click **Out of service** on M-A1: the ambulance moves into the
   **Out of service** column and its count goes up. (If that ambulance is rolling to a call you logged,
   the call is flagged **Breakdown**, and the reason "Ambulance breakdown" is recorded when it
   arrives.) Open **History**. Within about 5 seconds a **Cover** suggestion appears: "Ask Zone B or
   Zone D to cover Zone A's calls", with the evidence "1 of Zone A's ambulances out of service: M-A1."
   Click **Back in service** to undo it. If a zone has no free ambulance and a neighbor has two or
   more, History shows a **Rebalance** suggestion instead.

**Download calls (CSV)** on the live board saves this session's calls in the same format as
`data/calls_*.csv`. On the real clock, History starts empty (the demo file ends on Oct 12) and fills
with the calls you log by hand.

---

## What each dataset proves

| File | Behavior | What the tool shows |
|---|---|---|
| `calls_demo.csv` | Planted problems: D turnout (Sep 15-28, fixed Sep 29), C rush-hour travel (from Sep 20), peak-hour dispatch overload, ambulance M-B2 breakdowns | D amber on the zone map and below the standard on capability, then fixed and confirmed; C amber with a routes suggestion; dispatcher-cover suggestion |
| `calls_baseline.csv` | Stable city | A quiet dashboard: one amber zone from its 90th percentile, capability Reliable for all zones, no suggestions |
| `calls_messy.csv` | 7 planted data errors, tiny zones, one extreme valid call | Errors listed and excluded; "not enough data" instead of fake numbers |
