# Dispatcher guide

This chapter is for the dispatcher on shift. It walks through every part of the dispatcher screen, in
the same order as the numbers on the screen. Click **I'm a dispatcher** on the start page to begin.

## The screen at a glance

- The **header** holds the simulation controls (Day, Speed, Start, **Simulate a shift**, **Reset**), a
  chip that shows the clock mode (such as `LIVE 1x` or `SIM 120x`), and **Switch role**.
- Two tabs sit under the header: **Live board** and **History**.
- **Live board** is for the calls happening right now. **History** looks back over the current shift
  and the one before it.

## How to read a clock

Every open call has a running clock. Each clock has a target:

| Clock | Target |
|---|---|
| **Waiting** (call received to dispatched) | 1:04 |
| **Turnout** (dispatched to en route) | 1:00 |
| **Travel** (en route to on scene) | 8:00 for priority 1, 14:00 for priority 2, 19:00 for priority 3 |
| **Total** (dispatched to on scene) | 9:00 for priority 1, 15:00 for priority 2, 20:00 for priority 3 |

A clock gives you a **warning at 80% of its target**. It changes again when it is **past the target**.
Past the target means the call is late in that stage. A supervisor can change the targets (chapter 3).

## The top row: counts

Five counters show the workload: **Waiting**, **Dispatched**, **En route**, **On scene** and **Units
available**. They update by themselves.

## 1. Log a call

Use this card to enter a call by hand. In a real center, the call-taker's system would do this for you.

1. Choose the **Zone**. The zone letters match the Ithaca map (A West Hill, B Northside & Fall Creek,
   C Cornell & Collegetown, D West End & Southwest, E Downtown & South Hill, F East Hill & Belle
   Sherman).
2. Choose the **Priority**: **1: Life-threatening**, **2: Urgent** or **3: Non-urgent**.
3. Optionally choose the **Clock speed** (see "Clock speed" below). Leave it at 1x for real time.
4. Click **Add call**.

The call gets an ID like `LIVE-20261016-001`. Its **received time is stamped from the board clock**.
You do not type any time.

## 2. Incoming calls

New calls wait here until you dispatch an ambulance. Each row shows the call ID, the zone, the priority,
and a **Waiting** clock.

1. Look at the unit menu on the row. It lists only **available** ambulances. Ambulances from the call's
   own zone come first. Ambulances from other zones are marked with their home zone.
2. Pick the ambulance you want.
3. Click **Dispatch**.

If no ambulance is free, the row says **No unit free**. Wait for one to clear, or bring one back into
service (see "Ambulances").

If the call has waited longer than its 1:04 target, ERGent asks for a delay reason first (see "The
delay-reason dialog").

## 3. Dispatched

The call is assigned and the crew must get moving. The row shows the unit and a **Turnout** clock.
When the crew leaves, click **En route**. If turnout ran past 1:00, ERGent asks why.

## 4. En route

The ambulance is on the road. The row shows two clocks: **Travel** and **Total**. When the crew
arrives, click **On scene**. If travel ran past its target, or the total response ran past its target,
ERGent asks why.

If the ambulance comes from another zone, the row says so, for example "(from zone A)".

## Ambulances

This card shows all 12 ambulances in four columns. Each column has a count:

- **Available**: free to be dispatched.
- **Responding**: dispatched or en route. The chip says which.
- **On scene**: at the scene, not yet cleared.
- **Out of service**: not usable.

Each ambulance shows its ID and home zone, and one button.

- **Out of service** takes an ambulance out of use, for example after a breakdown. If it was rolling
  to a call you logged, that call is flagged **Breakdown**. ERGent records "ambulance breakdown" as the
  reason when the call reaches the scene, so you do not have to.
- **Back in service** returns an ambulance to the **Available** column.

## Zone map

The map shows Ithaca with the six zones. The outlines are **illustrative**, not official EMS districts.

- **Hover** over a zone to see its name, its status, how many calls are open there and how many
  ambulances are available.
- **Click** a zone to pick it in **Log a call**.
- The status comes from the clocks of that zone's open calls. A zone shows **On track** when all its
  clocks are comfortable, **Watch** when a clock is above 80% of its target, and **Past target** when a
  clock is late.
- The map needs an internet connection to draw.

## 5. Resolved

A call moves here **when it reaches the scene**. "On scene" counts as resolved. The list shows the
latest 60 calls and scrolls.

Each row shows the unit, the time, the delay reason (if any), and the **final response time**. The
response time is marked as late when it passed its target.

- A call that you logged by hand, and that is still at the scene, has a **Clear** button. Click it,
  then confirm "Clear call ...?". The row changes to **Cleared** and the ambulance becomes available.
- Replayed calls (from **Simulate a shift**) show **At the scene** and **Replay**. They are
  read-only.

## The delay-reason dialog

When you press a button that ends a stage that ran **past its target**, ERGent will not accept the
press until you say why. A dialog titled **Why was this late?** opens. It tells you how long the stage
took and what the target was.

1. Choose one reason from the list:
    - Traffic or road closure
    - Ambulance breakdown
    - Unit from another zone
    - Unclear address
    - Weather
    - Crew not ready
2. Click **Save reason and continue**.

**The time you pressed the button is kept**, not the time you chose the reason. If you click
**Cancel**, the dialog closes and the press is not recorded.

The reason is saved with the call. The supervisor's suggested actions use these reasons.

## The rules that protect you (mistake-proofing)

ERGent is built so that wrong entries are hard to make:

- Only the **next valid button** works: **Dispatch**, then **En route**, then **On scene**, then
  **Clear**. Any other press is refused with a message.
- You can only dispatch an **available** ambulance.
- A **late** stage needs a **reason**. The reason is one of six fixed codes, so it can be counted.
- **Clear** asks for confirmation first.
- Times come from the clock. You never type a time.

## Clock speed

The **Clock speed** menu on the **1 Log a call** card sets how fast the board clock runs when **no
simulation is running**. The choices are **1x**, **10x**, **30x** and **60x**.

- At **1x** the board clock is real time.
- At **60x**, one real second is one minute on the board. This is good for practice, because clocks
  turn late in seconds.
- Changing the speed **continues from the current board time**. The clock never jumps.
- At a high speed the board clock runs ahead of real time. The shift label in **History** follows the
  board clock.

The header chip shows the speed, for example `LIVE 60x`.

## Simulate a shift

The header controls replay one day of the demo data on a fast clock. This is the best way to learn
ERGent.

1. Choose the **Day** (the default is Sep 20).
2. Choose the **Speed**: **30x**, **60x** or **120x**.
3. Choose where to **Start**: **00:00**, **06:00**, **14:00** or **22:00**.
4. Click **Simulate a shift**.

The chip changes to `SIM 120x` (or the speed you chose). Calls appear and move through cards 2, 3, 4
and 5 at the times in the data. The button becomes **Pause**. Then it becomes **Resume**, and **Run
again** when the day ends.

Good to know:

- Replayed calls are **read-only**. You can still add your own calls, and they use the same clock.
- Calls that were already cleared before the start time are left out.
- You can change the **Speed** while it runs.
- To change the day or the start time, click **Reset** first.

## Reset

**Reset** clears everything back to zero:

- All replayed and hand-logged calls disappear.
- **Waiting**, **Dispatched**, **En route** and **On scene** all show 0.
- All 12 ambulances are **Available** again.
- **Resolved** is empty.
- The clock goes back to real time, at the clock speed you last chose.

## Download calls

**Download calls (CSV)** saves this session's calls as a spreadsheet file. The columns are the same as
the data files in the project, so you can open it in Excel or load it back into ERGent's tools.

## History tab

History looks back over the **current shift and the one before it**. A shift is eight hours: **day**
06:00 to 14:00, **evening** 14:00 to 22:00, **night** 22:00 to 06:00. History follows the board clock,
so during a simulation it follows the simulated time. It refreshes about every 5 seconds while you look
at it.

From top to bottom:

1. **The shift label.** For example: "Current: day shift 06:00-14:00, Sep 16 · Previous: night shift
   22:00-06:00, Sep 15".
2. **Four numbers:** **Calls**, **Mean (min)**, **Standard deviation (min)** and **On time**. They
   cover all priorities and only calls that have reached the scene. "On time" means within each call's
   own target. The mean is the average response time. The standard deviation shows how spread out the
   times are.
3. **Response time by zone** (the chart). Use the **Priority** menu to switch between **Priority 1:
   Life-threatening**, **Priority 2: Urgent** and **Priority 3: Non-urgent**. Each zone has a box that
   shows where most of its calls fall, and a diamond for its average. A line shows the city's center,
   short dashed lines show each zone's limits, and a line shows the target.
    - A **red diamond** is a zone that is **slower than the whole city**. **Hover over it** to see why.
     For example: "Zone D is slower than the city: 9.3 min typical vs. 6.3 min. Main cause: crew
     turnout (100% of minutes over target). Top reason: crew not ready (2 of 2 late calls)."
    - A zone marked **faster than the city** is shown as "check the data". Be careful: very fast times
     can be a data mistake.
    - Under the chart, a note names the slower zones, or says "No zone is slower than the city as a
     whole."
    - The number under each zone letter (such as `n=5`) is how many calls it has. A zone with few calls
     has wide limits, so be careful with it.
4. **Suggested actions** (on the right). ERGent's live tips for you. See below.

Right after you start ERGent in real time, History is empty, because the demo data is from the past.
It fills up when you log calls or run **Simulate a shift**.

### Suggested actions (tips T1 to T6)

Each tip has a short name, a zone tag, a plain sentence, and the evidence in small type. A note reminds
you: "For the dispatcher's judgment; the tool decides nothing on its own."

| Tip | When it appears | What it suggests |
|---|---|---|
| **T1 Dispatch now** | A call on the board has waited longer than 64 s for dispatch | Dispatch it now. It names the nearest free ambulance: one from the call's own zone first, then one from a neighboring zone. If none is free, it says so. |
| **T2 Rebalance** | A zone has no free ambulance and a neighboring zone has two or more | Move one ambulance to stand by in the empty zone. |
| **T3 Cover** | An ambulance is out of service | Ask the neighboring zones to cover that zone's calls. |
| **T4 Route** | A zone's typical travel time is at least 1.25 times the city's (needs 3 or more calls in the two shifts) | Check the route. If two or more late calls share a reason, the tip names it: reroute around traffic or road works, or keep an ambulance posted in that zone. |
| **T5 Station alert** | A zone's typical crew turnout is over 60 s (needs 3 or more calls) | Alert that zone's station: crews are slow to get rolling. |
| **T6 Dispatcher load** | Fewer than 9 in 10 calls were dispatched within 64 s over the two shifts (the 90th percentile of dispatch time is over 64 s; needs 5 or more calls) | Ask the supervisor for a second dispatcher. |

If there is nothing to suggest, the card says "No suggestions right now."

## What to do when...

| Situation | What to do |
|---|---|
| A call has waited too long | Pick an ambulance in **2 Incoming calls** and click **Dispatch**. The **T1 Dispatch now** tip in History names the nearest free one. |
| The row says **No unit free** | Wait for an ambulance to clear. If one is out of service and ready again, click **Back in service**. |
| An ambulance breaks down | Click **Out of service** on it. Its call is flagged **Breakdown**, and the reason is recorded for you. |
| A button you expect is missing | Only the next valid button is shown. Check which card the call is in. |
| ERGent asks "Why was this late?" | Choose the real reason and click **Save reason and continue**. Your press time is kept. |
| You pressed a button by mistake before the dialog | Click **Cancel** in the dialog. The press is not recorded. |
| You want to practice | Click **Simulate a shift**, or add calls and set **Clock speed** to 60x. |
| You want to start again | Click **Reset**. |
| You want to see how the shift is going | Open **History**. |
| A zone is red in History | Hover over the red diamond to read why. Look at the **Suggested actions** next to it. |
| A zone has no free ambulance | Look for **T2 Rebalance** in History. |
| You want to keep a record | Click **Download calls (CSV)**. |
| The map is blank | Check your internet connection. The map loads from the internet. |
