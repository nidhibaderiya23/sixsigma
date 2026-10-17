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

Click **I'm a supervisor**. In the Settings card, keep **Dataset: Demo city** and **Priority 1**. The
jump menu lives on the **Charts** tab: open **Charts**, choose **Jump**, then **Sep 28 (before the
fix)**. The **As of** date in Settings follows (2026-09-28), and the Chart period stays at **Last 28
days**. Then click the **Overview** tab.

Screens show results only. Under most cards, a **More info...** toggle opens a plain-language
explanation (questions and answers). The numbers below come from the cards or from More info.

### 1.1 Overview: "Is everything okay?"

| Tile | Shows |
|---|---|
| Average (what 911 sees) | 5.8 min |
| Median call | 5.3 min |
| 90th percentile | 8.8 min |
| 95th percentile | 10.1 min |
| On time | 91% |
| Zones flagged | 2 / 6 |

- Zone health: **Zone D is red ("Act now")**. Rules 2, 3 and 4 fired (2 of 3 days well above normal, 4
  of 5 days above normal, 8 days in a row above normal). Its 90th percentile is 10.2 min against the
  9-min target, and turnout causes 99% of its minutes over target.
- **Zone C is amber ("Worth a look")**. Rules 1 and 2 fired (a day far beyond its normal range, and 2
  of 3 days well above normal), and travel causes 97% of its minutes over target. Its 90th percentile
  (8.5 min) is still under the target. This is the start of the planted rush-hour road works.
- Every other zone is green.
- The history map shows the D tile red, labelled "Crew turnout", and the C tile amber, labelled "Travel".
- **More info** under the tiles says: "In the last 7 days up to Sep 28, the average call took 5.8 min.
  But 1 in 10 patients waited more than 8.8 min, and 1 in 20 more than 10.1 min (323 priority 1
  calls)."

**How to read it:** the average (5.8 min) looks fine, but 1 in 20 patients waited over 10 minutes.
That is the prompt's "monthly averages hide fatal outliers". Zone D is both out of its normal range
*and* missing its target, and the delay is the crew getting out the door, not the drive.

### 1.2 Charts: "What is happening, and why?" (zone selector: Zone D)

The control bar has the chart toggle (**Daily chart (X̄-S)** or **Every call (I-MR)**), the zone,
**As of**, **Chart period** and the **Jump** menu.

- **Daily chart (X̄-S)** (the default): red dots on 11 days, every day from Sep 18 to Sep 28. The
  slowdown starts on Sep 15, and the chart needs a few days of evidence before it signals. No day in
  the baseline (Sep 1 to 14) is flagged. The dashed lines are fixed: a normal range of about 3.0 to
  8.5 min around a center of about 5.1 min, all taken from the 14 baseline days. The same lines judge
  every day.
  **How to read it:** each dot is one day's typical response. Red means "slower than this zone's own
  normal", a special cause. More info says: "On 11 day(s), starting Sep 18, Zone D was slower than its
  normal range (2 of 3 days well above normal; 4 of 5 days above normal; 8 days in a row above
  normal)."
- **Every call (I-MR)** (switch the toggle): 211 calls in the period. 19 calls are beyond the upper
  control limit (extreme single delays), and 30 calls are over the amber 9-min target line.
  **How to read it:** the dashed lines are control limits, from the process. The amber line is the
  target, from the standard. They are different things.
- **Stage breakdown:** in the share chart, Zone D's bar is 92% turnout (amber), while every other
  zone is mostly travel (blue).
- **Capability:** one plain verdict per zone. A, B, E and F are **Reliable** (about 98, 96, 96 and 96
  calls in 100 arrive within 9 min, comfortably above the 90% standard). C and D say **Can't judge
  yet**, because their times changed during the period. The Ppk and Cpk numbers (A 0.68, B 0.60, E
  0.57, F 0.58) are only in More info.
  **How to read it:** a reliability score is only fair for a stable zone. A flagged zone must be
  fixed first.
- **Tests:** "Yes. Zone D is typically 6.0 min against 4.9 min in Zone A: differences this big are very
  unlikely to be chance." More info shows the one-way ANOVA: F = 9.31, p = 1e-08 (df 5 and 1246), and
  the normal probability plot of the chosen zone.

### 1.3 Actions: "How do we fix it, and did it work?"

Suggestions from the data, in this order:
1. **Routes, Zone C:** "Check road works and alternative routes in Zone C (17:00-20:00)". Evidence: the
   top delay reason is traffic or road closure (3 of 8 late calls). Estimate: on time 93% → 100%.
2. **Crew readiness, Zone D:** "Review crew readiness at Zone D's station, especially the night shift
   (50% of the turnout delay from 16% of the calls)". Estimate: on time 78% → 97%.
3. **Dispatcher cover, citywide:** "Add dispatcher cover during 17:00-19:00". Estimate: on time 68% →
   100% for processing in those hours.

Click **Log this action** on the Zone D suggestion. The dialog is prefilled with Zone D, crew
turnout and start date 2026-09-29. Click **Save action**. (The demo file already has this action
as A1, so you'll see "Already in the log as A1".) The **Before and after** card says "Not enough
data" for now: at Sep 28 the fix has not started yet.

**How to read it:** each suggestion is a fixed if-then rule, shown with its evidence. The impact
is a best-case estimate. A qualified person decides; the tool decides nothing.

---

## 2. The demo city, after the fix (as of Oct 12)

On **Charts**, choose **Jump**, then **The latest day**.

- **Overview:** average 5.6, median 5.2, 90th percentile 7.9, 95th percentile 9.0, on time 95%.
  Zones flagged: 3 / 6.
  - **Zone D is green again.**
  - **Zone C is amber:** 90th percentile 9.2 min, with travel 88% of the minutes over target. This is
    the planted weekday rush-hour road works.
  - **Zone B is amber:** rules 2 and 4 fired, travel 91%. (The demo data plants three breakdowns of
    ambulance M-B2.)
  - **Zone A is amber:** rules 3 and 4 fired (a run of slow days from Oct 5 to 8), travel 81%.
- **Charts, Zone D:** 12 red days (Sep 18 to Sep 29) in the 28-day period, and a green line marking
  the logged action on Sep 29.
- **Actions, suggestions:**
  - "Consider posting an extra ambulance in Zone B during 17:00-20:00": 93% → 100%.
  - "Check road works and alternative routes in Zone C (weekdays 16:00-19:00)": 92% → 100%.
  - "Add dispatcher cover during 17:00-19:00": 60% → 100%.
- **Actions, before and after** (pick **A1: Zone D, 2026-09-29**):

| Number | Before | After |
|---|---|---|
| Median response | 6.8 min | 5.2 min |
| On time | 78% | 97% |

Verdict: **Improved**. In More info: Welch's t-test, one-sided, on log response time: t = 6.57,
df = 207, p = 2e-10 (113 calls before, 98 after). The after-period chart, with its own new limits,
shows no warning signs: **the new level is stable**. The chart below marks the action with a green
line.
- **Slip-back watch:** no zone is drifting back after a logged action, so the slip-back card does not
  appear.

**How to read it:** this is the Improve and Control steps of DMAIC. The fix is logged, the
statistics confirm it worked, and the tool keeps watching for a slide back.

---

## 3. The baseline city (`data/calls_baseline.csv`, stable)

In Settings, choose **Dataset: Baseline city** (the as-of date moves to its last day, Sep 28).

- **Overview:** average 5.5, median 5.1, 90th percentile 7.8, 95th percentile 9.3, on time 94%.
  - Zones flagged: 2 / 6, both mild.
  - Zone C is amber, with a 90th percentile of 9.3 min against the 9-min target. It is the biggest
    zone, with longer trips.
  - Zone D is amber for one chance alarm: a single day (Sep 26) fell beyond its normal range (rule 1).
  - All other zones are green.
- **Charts (Zone D):** one flagged day (Sep 26), and no I-MR call beyond the upper limit.
- **Capability:** A, B, E and F are **Reliable** (about 97, 96, 98 and 96 calls in 100 within 9 min).
  C and D say **Can't judge yet**: each had a flagged day.
- **Tests:** "No clear difference" (F = 2.11, p = 0.062, in More info).
- **Actions:** no suggestions.

**How to read it:** a stable city gives a mostly quiet dashboard. Even so, chance produces the
odd single-day flag, which is why amber means "worth a look" and not "act".

---

## 4. The messy file (`data/calls_messy.csv`, data errors)

In Settings, choose **Dataset: Messy file** (the as-of date moves to Sep 3).

- **Overview, data quality:** "7 call(s) left out of the statistics":
  - C00002 and C00008: on_scene before en_route;
  - C00004: duplicate call_id;
  - C00009, C00024 and C00045: missing en_route;
  - C00027: dispatched before call_received.
- **Zone health:** zones C and F show "Not enough data". Zone B is amber because of a real,
  valid 25-minute call (C00038): its 90th percentile is 16.0 min.
- **Charts:** capability prints no meaningless numbers. Zones A, B, D and E say **Not enough calls**
  ("Only 7 calls in this period: at least 30 are needed to judge", and 6, 4 and 4 calls for B, D and
  E). Zones C and F say **Can't judge** ("need at least 2 values"). The tests card says "No clear
  difference".
- Nothing crashes, and no defective call enters any statistic.

**How to read it:** bad data is caught and listed, never silently averaged in. Mistake-proofing at
the source (the dispatcher's buttons) stops most of it from happening at all.

---

## 5. The dispatcher: live board and History

Click **Switch role**, then **I'm a dispatcher**. The simulation controls sit in the header, to the left
of **Switch role**: **Day** (default Sep 20), **Speed** (30x, 60x, 120x), **Start** (00:00, 06:00,
14:00, 22:00), a coral **Simulate a shift** button and **Reset**. A chip next to the title shows the
clock mode. Right now it says `LIVE 1x` (real time).

1. **Header controls: Simulate a shift.** Keep Day Sep 20, choose Speed 120x and Start 14:00, then
   click **Simulate a shift**.
   - The chip changes to `SIM 120x`. The button becomes **Pause** (then **Resume**, and **Run again**
     when the day ends).
   - The board clock (the time chip at the top of the live board) now runs 120 times faster than
     real time.
2. **Watch the board.**
   - The top row counts Waiting, Dispatched, En route, On scene and Units available.
   - The call process is laid out as numbered steps: **1 Log a call**, **2 Incoming calls**, **3
     Dispatched**, **4 En route**, **5 Resolved**. Calls appear in step 2, then move to steps 3 and 4
     at the times in the file. Replayed rows carry a **Replay** tag and no buttons: they are
     read-only.
   - Each running clock is green, turns amber above 80% of its stage target, and red past it. The
     **Live zone map** tile of a zone takes the worst clock colour in it.
   - **Ambulances** are grouped in four status columns with counts: **Available**, **Responding**
     (dispatched or en route), **On scene** and **Out of service**.
   - A call that reaches the scene moves to **5 Resolved** (full width, scrolls, latest 60) with its
     final response time, tagged **At the scene** and **Replay**. A cleared call shows **Cleared**.
   - **How to read it:** red means a stage is already past its target.
3. **History tab.** Click **History** while the simulation runs. It shows the
   current shift and the previous one, following the simulated clock, and refreshes about every 5
   seconds. Its only control is the **Priority** dropdown on the chart.
   - At about 14:28 on the simulated clock, the label reads `Current: evening shift 14:00-22:00, Sep 20
     · Previous: day shift 06:00-14:00, Sep 20`.
   - Four tiles come first: about 35 to 40 calls, a median of about 6 minutes, a 90th percentile of
     about 8 minutes and about 97% on time (all priorities, each call's own target). The numbers keep
     changing as the clock runs.
   - Below them, on the left (about 60% of the width), is one **Response time by zone** chart. Its
     **Priority** dropdown picks Priority 1, 2 or 3 (Priority 1 to start). Each zone is a box plot of
     its calls. The diamond is the zone's mean. The grey line is the city center, and the dashed grey
     lines are each zone's control limits (they are wider for zones with few calls). The amber line is
     the target. A note under the chart says "No zone is slower than the city as a whole.", or names
     the zones that are.
   - On the right (about 40%) are the **Suggestions**, one compact row each, with the evidence in
     muted type. Around 14:28 you should see a **Station alert** for Zone D: "Alert Zone D's station:
     crews are slow to get rolling", with a median turnout of about 2 minutes over the two shifts
     against the 1-minute target. (Zone D's turnout is the planted problem.) The note reads "For the
     dispatcher's judgment; the tool decides nothing on its own."
   - **How to read it:** a red diamond above its dashed limit is a zone slower than the city as a
     whole. Try the Priority dropdown: each priority has its own chart.
4. **Reset to zero.** Click **Reset**. All replay and hand-logged calls disappear. Waiting, Dispatched,
   En route and On scene all show 0, Units available shows 12, Resolved is empty, and the chip
   goes back to `LIVE 1x` on real time.
5. **Log a call by hand, at 60x.** On the **Live board**, in **Log a call**, choose Zone D, Priority 1
   and **Clock speed** 60x, then click **Add call**.
   - The chip says `LIVE 60x`. One real second is one minute on the board clock. (The board clock now
     runs ahead of real time, and the History shift label follows it.)
   - The call appears in **2 Incoming calls** with a unit picker (home-zone units first) and
     **Dispatch**. Its Waiting clock turns amber, then red past 1:04, within about a second.
   - Click **Dispatch**. The stage already ran late, so a dialog "Why was this late?" asks for one of
     the 6 delay reasons. Pick "Unclear address" and click **Save reason and continue**. The time
     you pressed the button is kept.
   - The call moves to **Dispatched**. Its turnout clock (target 1:00) turns red within a second or
     two. Click **En route** and give a reason ("Crew not ready"). It moves to **En route**, which
     shows Travel (target 8:00) and Total clocks. Click **On scene**. A response past its target also
     asks for a reason.
   - The call now sits in **5 Resolved** with its response time and a small **Clear** button. Click
     **Clear**, then confirm "Clear call ...?". The row shows **Cleared**, and the ambulance is
     free again.
   - Only the next valid button is ever shown. This is the poka-yoke.
6. **Ambulances.** In **Ambulances**, click **Out of service** on M-A1: the ambulance moves into the
   **Out of service** column and its count goes up. (If that ambulance is rolling to a call you
   logged, the call is flagged **Breakdown**, and the reason "Ambulance breakdown" is recorded when it
   arrives.) Open **History**. Within about 5 seconds a **Cover** suggestion
   appears: "Ask Zone B or Zone D to cover Zone A's calls", with the evidence "1 of Zone A's
   ambulances out of service: M-A1." Click **Back in service** to undo it. If a zone has no free
   ambulance and a neighbor has two or more, History shows a **Rebalance** suggestion instead.

**Download calls (CSV)** on the live board saves this session's calls in the same format as
`data/calls_*.csv`. On the real clock, History starts empty (the demo file ends on Oct 12) and fills
with the calls you log by hand.

---

## What each dataset proves

| File | Behavior | What the tool shows |
|---|---|---|
| `calls_demo.csv` | Planted problems: D turnout (Sep 15-28, fixed Sep 29), C rush-hour travel (from Sep 20), peak-hour dispatch overload, ambulance M-B2 breakdowns | D red then fixed and confirmed; C amber with a routes suggestion; dispatcher-cover suggestion |
| `calls_baseline.csv` | Stable city | A mostly quiet dashboard: two chance single-day flags, capability verdicts for the stable zones, no suggestions |
| `calls_messy.csv` | 7 planted data errors, tiny zones, one extreme valid call | Errors listed and excluded; "not enough data" instead of fake numbers |
