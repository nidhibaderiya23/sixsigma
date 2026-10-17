# Getting started

## What ERGent is

ERGent is a dashboard for a city 911 ambulance (EMS) dispatch center. Here, the city is **Ithaca, NY**.
It records the five times of every call: when the call arrived, when an ambulance was dispatched, when
it left, when it reached the scene, and when it cleared. From those times it works out how long each
part of a call took. It then shows a supervisor **which zone** is slow, **which part of the call** is
slow, and **since when**. It flags zones that need attention, suggests a fix with its evidence, and
later checks whether the fix worked. For the dispatcher on shift, it shows live clocks, so a late call
is hard to miss.

ERGent only **flags and suggests**. It never dispatches an ambulance or changes staffing. People decide.

## Why we built it this way

- A monthly average hides the slow calls. So ERGent also shows the 90th and 95th percentiles and uses
  control charts.
- Splitting each call into **stages** shows *why* a call was slow: dispatch, crew turnout, or travel.
- A chart for each **zone** shows *where* the problem is, and *since when*.
- A **before and after** check shows whether a fix really worked.

## Who it is for

| Role | When they use it | What they decide |
|---|---|---|
| **Supervisor** (the main user) | At the start of each shift, and whenever a flag appears | Which zone needs attention, which stage causes it, which fix to try, and later whether the fix worked |
| **Dispatcher** (the second user) | In real time, during a shift | Which open call is running late right now |

## How to start it

You need Python 3.12. The first time only, make a virtual environment and install the packages. Run
these in the project folder:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
```

Then start the app with one command:

```bash
cd app && ./testme.sh
```

Open **http://localhost:8000** in your browser. Stop the app with Ctrl+C in the terminal.

**Live version:** LIVE URL: (added after deploy). If your team has deployed ERGent, open that address
instead. You do not need to log in.

> **Internet needed.** The Ithaca map and its tiles load from the internet. If the map area is blank,
> check your connection.

## Choose a role

The start page has two buttons:

- **I'm a dispatcher** opens the live board and the History tab. Read chapter 2.
- **I'm a supervisor** opens the Charts and Actions tabs. Read chapter 3.

You can change role at any time. Click **Switch role** in the top right corner. Each browser tab keeps
its own board, so two people can try ERGent at once without affecting each other.

The **Manual** link in the header opens this manual in a new tab, from any page.

**Shortcut links.** Add `?role=dispatcher` or `?role=supervisor` to the app's address to open a view
directly. Add `&tab=History` or `&tab=Actions` to open that tab, and `&sim=1` to start the shift
replay. For example: `http://localhost:8000/?role=dispatcher&sim=1`.

## The data is synthetic

All the data in ERGent is **invented**. It was made by a script with a fixed random seed, so it is the
same every time. It is shaped like real field data, but it contains **no real patients, addresses or
names**. Nothing here describes real Ithaca emergency calls.

There are three data sets in the Dataset menu (the supervisor view):

| Data set | What it is for |
|---|---|
| **Demo** (42 days) | Has planted problems, so the tool has something to find. Zone D's crew turnout gets slow from Sep 15 and a fix is logged on Sep 29. Zone C slows in the weekday rush hour from Sep 20. |
| **Baseline** (28 days) | A stable city. A quiet dashboard is the right answer. |
| **Messy file** (3 days) | Has planted data errors: missing times, out-of-order times, a duplicate call ID. ERGent lists them and leaves them out. |

The dispatcher's **Simulate a shift** button replays one day of the demo data.

## The six zones

ERGent splits Ithaca into six zones. The outlines on the map are **illustrative**. They are not the
official EMS districts.

| Zone | Name |
|---|---|
| **A** | West Hill |
| **B** | Northside & Fall Creek |
| **C** | Cornell & Collegetown |
| **D** | West End & Southwest |
| **E** | Downtown & South Hill |
| **F** | East Hill & Belle Sherman |

On the map, A, B and C run west to east along the north side. D, E and F run west to east along the
south side. Zones that touch each other are neighbors. ERGent uses that when it suggests which zone
should cover for another.

## What the screens look like

The colors and layout can change between versions of ERGent. This manual describes screens by their
**titles and controls**, so it still works if the look changes.

## Targets used everywhere

Each call must meet these targets in **90% of calls**:

| Part of the call | Priority 1 | Priority 2 | Priority 3 |
|---|---|---|---|
| Dispatch (call received to dispatched) | 64 s | 64 s | 64 s |
| Turnout (dispatched to en route) | 60 s | 60 s | 60 s |
| Travel (en route to on scene) | 8:00 | 14:00 | 19:00 |
| **Response** (dispatched to on scene) | **9 min** | 15 min | 20 min |

The priority 1 numbers come from NFPA 1710, a US fire and EMS standard. **The priority 2 and 3 targets
are our own assumptions**, because the standard does not set them. A supervisor can change every target
(see chapter 3).
