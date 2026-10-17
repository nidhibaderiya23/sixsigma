# Live demo cue card (about 3 minutes)

Print this or keep it on a phone. **Bold** = what to click. *Italic* = what the audience should see.
Numbers are from the Ithaca demo dataset, priority 1, chart period "Last 28 days".

## Before

- Open `<app URL>/?role=supervisor` in one tab and `<app URL>/?role=dispatcher` in another.
- Leave the supervisor tab on its defaults (Zone D, Priority 1, Ithaca demo, 28 days).

## 1. Find the problem (60 s)

| Do | See | Say |
|---|---|---|
| Set **As of** to **2026-09-28** | *Statistics: 5.6 min average, 93% on time, 1 / 6 zones flagged* | "The city average looks fine." |
| Hover **Zone D** on the Ithaca map | *Amber, "Main delay: crew turnout", 90th percentile 10.2 min vs 9* | "Zone D, West End and Southwest, is not." |
| Scroll to **Delay by stage** | *Zone D's bar is almost all turnout (92%)* | "It's the crew getting out the door, not the drive." |
| Point at **Capability** | *Zone D: Below the standard, about 89 in 100 within 9 min* | "Only 89 in 100 patients get an ambulance in time." |

## 2. Fix it (40 s)

| Do | See | Say |
|---|---|---|
| Click the **Actions** tab | *Suggested actions: "Review crew readiness at Zone D's station, especially the night shift"; estimate 78% → 97%* | "A fixed rule, with its evidence. A person decides." |
| Click **Log this action** on it, then **Save action** | *"Already in the log as A1"* (the demo data has it) | "The fix starts September 29." |

## 3. Check it (40 s)

| Do | See | Say |
|---|---|---|
| Back to **Charts**, set **As of** to **2026-10-12** | *Zone D is green on the map; Zone C is now amber (road works)* | "Two weeks later, D is green. And the next problem shows up: Zone C's rush-hour road works." |
| **Actions** tab, **Result** card | *Improved; on time 78% → 97%; Welch t = 6.57* | "The fix worked, and it is not chance." |

## 4. The dispatcher (40 s)

| Do | See | Say |
|---|---|---|
| Switch to the dispatcher tab. In the header pick **Speed 120x**, **Start 06:00**, click **Simulate a shift** | *Calls appear, clocks run, the Ithaca map colours zones* | "This is a shift replayed at 120 times speed." |
| Point at a clock turning amber or red | *A red clock* | "Amber at 80% of the target, red past it." |
| Click **History** | *Response time by zone, tips on the right* | "And tips for right now: dispatch now, rebalance, route." |

## If something goes wrong

- **Page stuck or grey:** reload the tab (the links reopen the view).
- **No internet:** the map needs the internet, but everything else runs locally (`cd app && ./testme.sh`).
- **Nothing works:** show the screenshots in `docs/deliverables/screenshots/` and keep talking.
