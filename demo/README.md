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
   - Calls appear in **Incoming calls**, then move to **Dispatched** and **En route** at the times in
     the file. Replayed rows carry a **Replay** tag and no buttons: they are read-only.
   - Each running clock is green, turns amber above 80% of its stage target, and red past it. The
     **Live zone map** tile of a zone takes the worst clock colour in it. **Ambulances** shows who is
     dispatched, en route or on scene.
   - A call that reaches the scene moves to **Resolved** (full width, latest 30) with its final
     response time, tagged **At the scene** and **Replay**. A cleared call shows **Cleared**.
   - **How to read it:** red means a stage is already past its target.
3. **History tab.** Click **History** while the simulation runs. It has no selectors. It shows the
   current shift and the previous one, following the simulated clock, and refreshes about every 5
   seconds.
   - At about 14:28 on the simulated clock, the label reads `Current: evening shift 14:00-22:00, Sep 20
     · Previous: day shift 06:00-14:00, Sep 20`.
   - **Suggestions for the dispatcher** comes first. Around then you should see a **Station alert** for
     Zone D: "Alert Zone D's station: crews are slow to get rolling", with a median turnout of about 2
     minutes over the two shifts against the 1-minute target. (Zone D's turnout is the planted
     problem.)
   - Next come four tiles: about 35 to 40 calls, a median of about 6 minutes, a 90th percentile of about
     8 minutes and about 97% on time (all priorities, each call's own target). The numbers keep
     changing as the clock runs.
   - Then three charts, one per priority, **Response time by zone**. Each zone is a box plot of its
     calls. The diamond is the zone's mean. The grey line is the city center, and the dashed grey lines
     are each zone's control limits (they are wider for zones with few calls). The amber line is the
     target. A note under each chart says "No zone is slower than the city as a whole.", or names the
     zones that are.
   - **How to read it:** a red diamond above its dashed limit is a zone slower than the city as a
     whole. The suggestions are for the dispatcher's judgment; the tool decides nothing.
4. **Reset to zero.** Click **Reset**. All replay and hand-logged calls disappear. Waiting, Dispatched,
   En route and On scene all show 0, Units available shows 12, Resolved is empty, and the chip
   goes back to `LIVE 1x` on real time.
5. **Log a call by hand, at 60x.** On the **Live board**, in **Log a call**, choose Zone D, Priority 1
   and **Clock speed** 60x, then click **Add call**.
   - The chip says `LIVE 60x`. One real second is one minute on the board clock. (The board clock now
     runs ahead of real time, and the History shift label follows it.)
   - The call appears in **Incoming calls** with a unit picker (home-zone units first) and
     **Dispatch**. Its Waiting clock turns amber, then red past 1:04, within about a second.
   - Click **Dispatch**. The stage already ran late, so a dialog "Why was this late?" asks for one of
     the 6 delay reasons. Pick "Unclear address" and click **Save reason and continue**. The time
     you pressed the button is kept.
   - The call moves to **Dispatched**. Its turnout clock (target 1:00) turns red within a second or
     two. Click **En route** and give a reason ("Crew not ready"). It moves to **En route**, which
     shows Travel (target 8:00) and Total clocks. Click **On scene**. A response past its target also
     asks for a reason.
   - The call now sits in **Resolved** with its response time and a small **Clear** button. Click
     **Clear**, then confirm "Clear call ...?". The row shows **Cleared**, and the ambulance is
     free again.
   - Only the next valid button is ever shown. This is the poka-yoke.
6. **Ambulances.** In **Ambulances**, click **Out of service** on M-A1. (If that ambulance is rolling to
   a call you logged, the call is flagged **Breakdown**, and the reason "Ambulance breakdown" is
   recorded when it arrives.) Open **History**. Within about 5 seconds a **Cover** suggestion
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
| `calls_baseline.csv` | Stable city | No chart flags; capability shown for all zones; no suggestions |
| `calls_messy.csv` | 7 planted data errors, tiny zones, one extreme valid call | Errors listed and excluded; "not enough data" instead of fake numbers |
