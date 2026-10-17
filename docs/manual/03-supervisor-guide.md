# Supervisor guide

This chapter is for the EMS operations supervisor. The supervisor view helps you answer four
questions, in this order:

1. **Which zone** needs attention?
2. **Which part of the call** (dispatch, crew turnout or travel) is slow?
3. **What should we try?**
4. **Did the fix work?**

Click **I'm a supervisor** on the start page. You get two tabs: **Charts** and **Actions**. Charts
answers questions 1 and 2. Actions answers questions 3 and 4.

**Every card has one plain title.** Under most cards, a **More info** toggle opens a short explanation
of the card in two or three sentences. Use it whenever you want to know what you are looking at.

## The Charts tab

### The control bar

The control bar at the top of Charts sets what **both tabs** show.

| Control | Choices | What it does |
|---|---|---|
| **Chart** | **Daily chart**, **Every call** | Which control chart to show (one at a time) |
| **Zone** | Zone A to F, with its name | Which zone the control chart shows. You can also click a zone on the map. |
| **Priority** | **1: Life-threatening**, **2: Urgent**, **3: Non-urgent** | Which calls to look at. Each priority has its own target. |
| **Dataset** | Demo, Baseline, Messy file | Which data to look at (see chapter 1) |
| **As of** | A date in the data | The "today" for every card. Later calls are ignored. It moves to the last day of the data when you change the dataset. |
| **Chart period** | Last 14, 28 or 42 days | How much history every card uses. **It also sets the control limits** (see below). |
| **Targets** | A button | Opens the Targets dialog (see the end of this chapter) |

> **Tip.** To follow the demo story, choose the **Demo** data set and set **As of** to **2026-09-28**.
> That is the day before the fix. Then set it to **2026-10-12** to see the result.

### Control chart

The control chart is the main picture. It shows whether a zone is behaving the way it normally does.
Choose **Daily chart** or **Every call**.

#### Daily chart

The Daily chart has two panels.

**Top panel: "Zone X: daily average response."**

- Each **dot** is **one day**. Its height is that day's typical response time in minutes. ("Typical" is
  a geometric average. It is a fair average for times with a long slow tail.)
- The **center line** is the zone's normal level. It is the average of the daily dots in the chart
  period.
- The two **dashed lines** are the **control limits**. They are the upper control limit (**UCL**) and
  the lower control limit (**LCL**). They mark the normal range. They are the same for every day.
- A **red dot** is a day that broke a flag rule (see below). Something probably changed.
- A **hollow ring** is a "check the data" day: unusually *fast*. Check the records before you trust it.
- The **amber line** is the **target** (the specification limit). It is a requirement from the
  standard. It is not part of the control limits.
- A **green vertical line** marks a logged action (a fix).

**Bottom panel: "Daily spread."** It shows how spread out that day's calls were. A red dot means some
calls that day were much slower than others.

**What makes a dot red?** One of these rules fired on the slow side:

| Rule | A red dot appears when... |
|---|---|
| R1 | one day is far outside the normal range (beyond 3 sigma) |
| R2 | 2 of the last 3 days are well above normal (beyond 2 sigma) |
| R3 | 4 of the last 5 days are above normal (beyond 1 sigma) |
| R4 | 8 days in a row are above the center line |
| R5 | 6 days in a row are getting slower |

A day on the *fast* side only says "check the data". It is not an alarm.

> **Important: limits come from the chart period.** The control limits are worked out from the days in
> the **chart period** you selected. That is simple, and it keeps the chart, the map, the suggestions
> and the capability card all in agreement. But there is a trade-off. If a problem lasts for most of
> the period, it **widens the limits** and can **hide itself**. Example: in the demo data, as of Sep
> 28 with a 28-day period, Zone D's daily chart shows **no red dots**, because D's slowdown (from Sep
> 15) is inside the window. The other cards still show the problem: the **Zone map** is amber for D,
> **Delay by stage** blames crew turnout, and **Capability** says D is below the standard. **Always
> read the daily chart together with those cards.**

#### Every call

**Every call** shows each call, in the order the calls came in. The height is the response time in
minutes. The scale is a log scale, so the slow tail does not squash the rest.

- The **center line** is the typical call.
- The dashed **UCL** and **LCL** are the normal range for a *single* call.
- A **red dot** is a call **above the UCL**: an unusual delay worth looking at one by one.
- The **amber line** is the target. Calls above it missed the target.

### Statistics

The **Statistics** card sums up the chart period for **all zones**, for the priority you chose. The
line under the title shows the dates and the number of calls.

| Number | What it means |
|---|---|
| **Average** | The mean response time in minutes |
| **Standard deviation** | How spread out the response times are. A big number means less predictable service. |
| **On time** | The share of calls within the target. The goal is **at least 90%**. |
| **Zones flagged** | How many zones are amber or red on the map, out of 6 |

### Zone map

The **Zone map** shows Ithaca in six zones. The outlines are **illustrative**, not the official EMS
districts. Each zone is colored by its status over the **last 7 days**:

| Status | Meaning |
|---|---|
| **On track** | Nothing to worry about |
| **Worth a look** (amber) | One warning sign, either a real change on the chart or a 90th percentile over the target |
| **Act now** (red) | Both warning signs together |
| **Not enough data** | Too few calls to judge |

- **Hover** over a zone to see its status and the reasons, such as "90th percentile 10.2 min vs. 9
  min target" and "turnout causes 99% of minutes over target".
- **Click** a zone to select it. The **Zone** menu and the control chart switch to that zone.
- A zone that is slipping back after a logged fix is at least amber.
- A single weak sign (for example, one rule fired once) does not turn a zone amber. It is mentioned
  in the zone's reasons: "one weak signal ... keep watching". This keeps false alarms rare.

### Data quality

This card appears **only when some calls were left out** of the statistics. It lists each call and why:
a missing time, times in the wrong order, a duplicate call ID, a zero response time, or an unknown zone
or priority. These calls are never counted, so one bad record cannot distort a chart. The **Messy
file** data set shows this card.

### Delay by stage

A call has three stages: **dispatch processing**, **crew turnout** and **travel**. This card shows
**which stage causes the minutes over target** in each zone. The line under the title shows the dates
and the priority.

- Each zone has one bar. The bar is split into three parts. Each part is that stage's **share of the
  zone's minutes over target**. The bar adds up to 100%.
- The last bar, **City**, is all zones together.
- **Hover** over a part of a bar to see its share, the total minutes over target, and the median time
  of that stage.

**How to read it:** the biggest part of a zone's bar is the stage to fix first. In the demo data, Zone
D's bar is almost all crew turnout. Most other zones are mostly travel.

### Zone comparison

This card answers "**do the zones really differ?**" in a sentence. For example: "Yes. Zone D is
typically 6.0 min against 4.9 min in Zone A; a gap this big is very unlikely to be chance." If the
gaps are small, it says "No clear difference: the gaps between zones could be chance."

Open **More info** for the test result (the F value and p-value) and a probability plot. See chapter 4
if you want the details.

### Capability

The **Capability** card asks: "**Can each zone meet the target, reliably?**" It gives one plain verdict
for each zone.

| Verdict | What it means |
|---|---|
| **Very reliable** | 99 or more calls in 100 arrive within the target |
| **Reliable** | 95 to 98 calls in 100 arrive within the target |
| **Just meets the standard** | 90 to 94 in 100. There is little margin. |
| **Below the standard** | Under 90 in 100 |
| **Can't judge yet** | The zone's times changed during the period, so a score would mislead. Fix the cause first. |
| **Not enough calls** | Fewer than 30 calls in the period |

Open **More info** for the Ppk and Cpk numbers behind the verdicts. The standard asks for at least 90
calls in 100 to be on time.

## The Actions tab

Actions answers "**what should we try, and did it work?**" A line at the top reminds you of the data
set, priority and date. Change them on the **Charts** tab.

### Slip-back alerts

This card appears **only when a zone is slipping back** after a logged action. It names the zone and
the warning sign. A zone that slips back is at least amber on the map.

### Suggested actions

This card lists fixes ERGent suggests. Each one has:

- a **tag** for the kind of fix: **Crew readiness**, **Coverage**, **Routes**, **Dispatcher cover**,
  **Maintenance** or **Address checks**;
- a **zone tag** (or **Citywide**);
- the **suggestion**, in plain words;
- the **evidence**, so you can see why;
- an **estimate**, such as "on time 78% → 97%". This is a best case: what the on-time share would be if
  that stage were as fast as the city's typical call.

Every suggestion is "for review by qualified staff". ERGent decides nothing. See chapter 4 for the
rules behind S1 to S6.

**To log a suggestion as an action:**

1. Click **Log this action** on the suggestion.
2. A dialog **Log an action** opens, already filled in: the **Zone**, the **Stage**, a **Start date**
   (the day after the as-of date), **What was done** and the **Owner**. Edit anything you like.
3. Click **Save action**.

If that same action is already in the log, ERGent says "Already in the log as A1" and does not add it
twice. Once logged, the suggestion shows its status, for example "Action logged on 2026-09-29".

### Actions taken

This is the action log. Each row has an ID (A1, A2...), the zone, the stage, the date, what was done
and who owns it. An action dated after the as-of date is tagged **After the as-of date**.

Click **Log an action** to add one by hand, without a suggestion. The demo data already holds one
action: **A1**, a night crew readiness review at Zone D's station, dated 2026-09-29. Actions are only
kept for the length of your session.

### Before and after

This card shows the **daily chart** for the action's zone, with the action marked by a green line. You
can see whether the days after the fix stay in the normal range.

### Result

The **Result** card tells you whether the fix worked.

1. Choose the action in the menu (the latest action on or before the as-of date is chosen for you).
2. Read the **verdict chip**:
    - **Improved**: the drop is too large to be chance.
    - **Got worse**: the times got slower, and too much to be chance.
    - **No clear change yet**: the change could be chance.
    - **Not enough data**: there are not yet enough calls after the action. For example, if the as-of
     date is before the action.
3. Read the table. It compares the **14 days before** the action with the **days after it** (up to 14):

| Row | Before | After |
|---|---|---|
| **Mean** | average response time | average response time |
| **Standard deviation** | spread of the times | spread of the times |
| **On time** | share within the target | share within the target |
| **Calls** | number of calls | number of calls |

Open **More info** for the test numbers and to see whether the new level is **steady**: whether the
days after the action stay inside the normal range.

> **Watch out.** A better time after a fix does not *prove* the fix caused it. Other things may have
> changed. The check shows an apparent change. Staff judge the cause.

## The Targets dialog

Click **Targets** in the control bar to see and change the targets. The dialog has five numbers:

| Field | Default |
|---|---|
| **Priority 1 target (min)** | 9 |
| **Priority 2 target (min)** | 15 |
| **Priority 3 target (min)** | 20 |
| **Processing target (s)** | 64 |
| **Turnout target (s)** | 60 |

Click **Save** to apply them, or **Cancel** to close the dialog. The new targets change every card.

The defaults come from NFPA 1710, a US standard, for priority 1: 64 seconds to dispatch, 60 seconds for
the crew to get moving, and 8 minutes to travel, which makes 9 minutes from dispatch to arrival. **The
priority 2 and 3 targets are our own assumptions.** The travel target is always the response target
minus the 60-second turnout target.
