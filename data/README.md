# Response Watch test data (codebook)

**All data in this folder is synthetic.** No real calls, patients, addresses or names.
A seeded script, `make_data.py`, invents it. It uses numpy's `default_rng` with **seed 42**,
so every run writes the same bytes.

Regenerate everything with one command, from the repo root:

```
.venv/bin/python data/make_data.py
```

(Any Python 3.12 with numpy and pandas works. The script reads the column list, zones, targets and shifts
from `app/qc.py` and checks every reason code against it, so the data and the app agree.)

## The files

| File | Rows | What it is | Behavior it shows |
|---|---|---|---|
| `calls_baseline.csv` | 2,719 | 28 days (2026-09-01 to 09-28), 6 zones, about 16 calls per zone per day | A **stable** process. Nothing is planted. The tool should show green zones, apart from the odd chance alarm. |
| `calls_demo.csv` | 4,151 | 42 days (2026-09-01 to 10-12), the same city | **Four planted problems** (below). The tool should find them, suggest fixes, and confirm that Zone D improved. |
| `calls_messy.csv` | 61 | 3 days (2026-09-01 to 09-03), about 20 calls per day | **Data defects** (below). The tool must list them, leave them out of the statistics, and not crash. |
| `actions_demo.csv` | 1 | The one fix logged in the demo | Lets the tool run its before/after check on Zone D. |
| `units.csv` | 12 | The ambulance fleet | Lookup: which zone each ambulance is based in. |

## The call files: one row per call

`calls_baseline.csv`, `calls_demo.csv` and `calls_messy.csv` share these 14 columns, in this
order, sorted by `call_received`. Times are local, to the whole second.
A blank means "not recorded".

| Column | Type / units | Meaning | Allowed values | How a real 911 center collects it |
|---|---|---|---|---|
| `call_id` | text | One ID per call. | `C00001`, `C00002`, ... Unique. | CAD (computer-aided dispatch) assigns it, automatically. |
| `zone` | category | Response zone of the caller. | `A` to `F` | CAD turns the caller's address into a zone. The tool never sees the address. |
| `priority` | integer | How urgent the call is. | `1` life-threatening, `2`, `3` | The call-taker's medical triage code in CAD, mapped to 1, 2 or 3. |
| `call_received` | timestamp `YYYY-MM-DD HH:MM:SS` | The call is answered. | Valid time | CAD, automatic, when the 911 call is answered. |
| `dispatched` | timestamp | An ambulance is assigned. | Not before `call_received` | The dispatcher presses "dispatch". CAD stamps it. |
| `en_route` | timestamp | The crew starts driving. | Not before `dispatched` | The crew presses "en route" on the mobile data terminal (MDT) in the cab. |
| `on_scene` | timestamp | The ambulance arrives. | Not before `en_route` | The crew presses "on scene" on the MDT. GPS arrival at the address can stamp it too. |
| `cleared` | timestamp | The ambulance is free again. | After `on_scene` | The crew presses "available" on the MDT. Not used in the response statistics. |
| `unit_id` | text | The ambulance that went. | `M-A1` to `M-F2` (see `units.csv`) | CAD fleet list: the unit chosen at dispatch. |
| `unit_home_zone` | category | The zone the ambulance is based in. | `A` to `F` | CAD fleet list (the unit's station). If it differs from `zone`, the unit came from another zone. |
| `distance_km` | number, km, 1 decimal | Route distance from the ambulance to the scene at dispatch. | 0.5 or more | CAD's GPS (vehicle location) plus its routing engine, automatic. |
| `dispatcher_id` | text | Who dispatched the call. | `DSP-01` to `DSP-08` | CAD login. Stored, but never shown per person: the tool reports by shift and workload only. |
| `weather` | category | Weather when the call came in. | `clear`, `rain`, `snow` | A weather feed read by CAD. |
| `delay_reason` | category | Why a stage ran late. | Blank, or one of the 6 codes below | The crew taps one code on the MDT, **only** when a stage ran past its target. |

Dispatchers work in shifts, with 2 or 3 per shift: **day** (06:00-14:00) `DSP-01` to `DSP-03`,
**evening** (14:00-22:00) `DSP-04` to `DSP-06`, **night** (22:00-06:00) `DSP-07` and `DSP-08`.

### Columns the tool calculates (not stored in the files)

`qc.stage_times` adds these, in seconds:

- `processing_s` = `dispatched` - `call_received` (the dispatcher's stage)
- `turnout_s` = `en_route` - `dispatched` (the crew getting out the door)
- `travel_s` = `on_scene` - `en_route` (driving)
- `response_s` = `on_scene` - `dispatched` (turnout + travel: the headline number)
- `issue` and `valid`: why a call is left out, if it is

### The other two files

`units.csv`: `unit_id` (`M-A1`, `M-A2`, `M-B1`, ... `M-F2`) and `home_zone` (`A` to `F`).
Two ambulances per zone. A real center reads this from its fleet list.

`actions_demo.csv`: `action_id` (`A1`), `date` (`YYYY-MM-DD`), `zone`, `stage` (`processing`,
`turnout` or `travel`), `description` (free text), `owner` (a role, not a person).
The supervisor types it in the Actions screen.

## Delay reason codes

| Code | Plain words |
|---|---|
| `traffic_or_road_closure` | Traffic or a road closure |
| `ambulance_breakdown` | The ambulance broke down |
| `unit_from_another_zone` | The unit came from another zone |
| `unclear_address` | The address was unclear |
| `weather` | Weather slowed the trip |
| `crew_not_ready` | The crew was not ready |

**When must a crew enter a code?** Whenever a stage runs past its target: processing over
64 s, turnout over 60 s, or travel over the response target minus 60 s (480 s for priority 1,
840 s for priority 2, 1,140 s for priority 3). On-time calls get no code. If no code fits
exactly, the crew picks the closest one. In these files every late call has a code and no
on-time call has one.

The generator picks the code that matches the cause, looking at the stage that is
latest relative to its target: a breakdown call gets `ambulance_breakdown`; a late turnout gets
`crew_not_ready`; late travel gets `traffic_or_road_closure` on a road-works call,
`unit_from_another_zone` if the unit came from next door, `weather` on a rain or snow day,
and otherwise a random code. Any other late call (for example a slow processing time) draws
randomly: traffic 65%, crew not ready 25%, unclear address 10%.

## Targets used

From `qc.TARGETS`. Each target should be met by at least 90% of calls. The supervisor can edit them.

| Target | Value | Source |
|---|---|---|
| Processing (call received to dispatched) | 64 s | NFPA 1710 |
| Turnout (dispatched to en route) | 60 s | NFPA 1710 |
| Travel, priority 1 | 480 s | NFPA 1710, advanced life support unit |
| **Response (dispatched to on scene), priority 1** | **9 min** (540 s) | NFPA 1710: 60 s turnout + 480 s travel |
| Response, priority 2 | 15 min | **Our assumption.** NFPA does not set it. |
| Response, priority 3 | 20 min | **Our assumption.** NFPA does not set it. |

## How the data are made

Short version of `make_data.py`. Each of these is one constant at the top of the script.

- **Calls:** each zone gets a Poisson (mean 16) number of calls per day. The hour of day is
  weighted: quiet at 02:00-05:00, busiest at 16:00-19:00. Priority mix 45% / 35% / 20%.
- **Weather:** one value per day for the whole city. Every 14 days has exactly 10 clear,
  3 rain and 1 snow day. Rain makes travel 1.07 times longer, snow 1.15 times. (This mix is made up and
  does not follow real September weather.)
- **Stage times:** lognormal. Processing median 40 s (90th percentile about 52 s), turnout
  median 42 s (90th percentile about 57 s).
- **Travel:** distance divided by speed. Distance median about 3 km. Speed about 42 km/h for
  priority 1 (lights and sirens), 36 for priority 2 and 32 for priority 3, with random noise.
  Zone C's trips are 8% longer than the other zones' (it is the biggest zone).
- **On scene to cleared:** 20 to 50 minutes.
- **Ambulances:** the generator tracks every ambulance, so none is on two calls at once.
  A call goes to a home-zone ambulance. If both are busy, a neighbouring zone's ambulance
  goes, and the trip is 1 to 2 km longer. This happens on about 11% of calls. Rarely (a few calls per
  file) every ambulance in the city is busy and the call waits for one; that shows up as a long
  processing time.

## `calls_baseline.csv`: a stable process

Nothing is planted. Numbers for priority 1, in minutes (what `qc.zone_summary` prints):

| | Median | 90th percentile | 95th percentile | % on time (9 min) |
|---|---|---|---|---|
| Citywide | 5.1 | 7.7 | 8.6 | 96.3% |
| Zones A to F | 5.0 to 5.4 | 7.2 to 8.3 | 7.6 to 9.1 | 94.4% to 98.7% |

All six zones are within 0.4 min of each other at the median. Processing 90th percentile is
about 52 s and turnout 57 s, both inside their targets.
**What the tool should do:** call every zone green, apart from the rare chance alarm. With
the default settings, all six zones are green on every date from 2026-09-15 to 09-26, and
Zone C turns amber on 09-27 and 09-28 because a handful of slow calls lift its 7-day 90th
percentile just over 9 minutes.

## `calls_demo.csv`: four planted problems

Same city, 42 days. Day 1 is 2026-09-01. The tool should find all four.

| # | What is planted | Where and when | What the tool should show (numbers from this file) |
|---|---|---|---|
| a | **Crew turnout gets worse** after a new crew schedule. Turnout rises by 60-90 s on every shift. At night (22:00-06:00) the median turnout is about 3 times the day and evening level (about 370 s at night, 120 s by day, 42 s normally). | Zone D, days 15-28 (2026-09-15 to 09-28). **The fix is logged in `actions_demo.csv` on 2026-09-29, and turnout is back to normal from that day.** | Zone D is **red** on 09-16 and from 09-18 to 10-02, amber on 10-03 to 10-05 (a flag stays on for 7 days), green from 10-06. The stage breakdown puts 92% of D's minutes over target on turnout. Suggestion: "Review crew readiness at Zone D's station". Priority 1 response, days 1-14 / 15-28 / 29-42: 90th percentile 7.5 / 10.4 / 7.4 min, on time 94.9% / 77.9% / 96.9%. The before/after check says "improved" (Welch t = 6.6, p < 0.001). The daily mean of ln(response seconds) is 5.73 before, 6.02 during, 5.76 after. |
| b | **Road works slow travel.** Travel is 1.6 times longer, with some day-to-day spread. Late calls carry `traffic_or_road_closure`. | Zone C, **weekdays 16:00-19:00**, from day 20 (2026-09-20) to the end. | Median travel in that window is about 420 s, against about 270 s for other Zone C calls. Priority 1 90th percentile for Zone C is 7.8 min before and 8.7 min after day 20. Its last 7 days reach 9.2 min on 10-12, so Zone C turns **amber** on 2026-10-12. Suggestion: "Check road works and alternative routes in Zone C (weekdays 16:00-19:00)". This is a small signal: only about 14% of Zone C's calls fall in that window. |
| c | **Dispatchers are overloaded at the evening peak.** Processing is 1.6 times longer. | All zones, **weekdays 17:00-19:00**, the whole 42 days. | 90th percentile of processing: 85 s in those hours, 52 s in all other hours (target 64 s). Suggestion: "Add dispatcher cover during 17:00-19:00". |
| d | **One ambulance keeps breaking down.** Travel gets +6 min and the call carries `ambulance_breakdown`. | Unit `M-B2`, three priority-1 calls: `C00892` (2026-09-10), `C02332` (2026-09-24), `C03442` (2026-10-05). | Suggestion "Schedule preventive maintenance for ambulance M-B2" appears when the last 14 days hold two breakdowns, for example with `as_of` 2026-10-05 or 10-06. |

**Chance alarms are expected.** The charts use five run rules, so even clean data now and then shows
an alarm. In this file Zone A (from about 10-02) and Zone B (09-15 to 09-24, and from 10-05) show
some. They come from random runs of slow days, a snow day on 09-18, and for Zone B the three
M-B2 breakdowns. They are not planted. They can also trigger a stray suggestion (on 10-12 the tool also suggests an extra ambulance in Zone B). Zone E stays green, and Zone F is amber on one date (09-30).

## `calls_messy.csv`: data defects

About 60 calls, 3 days. The calls are otherwise realistic. `qc.stage_times` flags exactly the 7
rows below (7 of 61) and keeps the other 54 calls.

| Defect | Call | What it looks like | `qc` issue text |
|---|---|---|---|
| Missing `en_route` (x3) | `C00009` (D, P1), `C00024` (B, P1), `C00045` (C, P2) | The crew never pressed "en route". The field is blank. | `missing en_route` |
| `on_scene` before `en_route` (x2) | `C00002` (C, P1), `C00008` (C, P3) | The crew pressed the buttons in the wrong order. | `on_scene before en_route` |
| `dispatched` before `call_received` (x1) | `C00027` (B, P1) | A clock out of sync. | `dispatched before call_received` |
| Duplicate `call_id` (x1) | `C00004` (E, P1) | The same row appears twice. The second copy is flagged. | `duplicate call_id` |

Also in the file, and **not** defects (the tool must handle them without crashing):

- **A zone with only 2 calls:** Zone F has `C00011` and `C00046`. Its statistics rest on almost nothing, and the charts have no limits.
- **A day with no calls for one zone:** Zone E has calls on 2026-09-01 and 09-03, none on 09-02.
- **A real but extreme outlier:** `C00038` (Zone B, priority 1, 2026-09-02 19:22) has a response of
  **25.0 minutes** (8.4 km, `traffic_or_road_closure`, such as a closed bridge). The data is valid.
  The tool should keep it in the statistics and show it as an extreme delay, not delete it.

## Limits of the simulation

- The tool is meant to be tested on this data, not to describe a real city.
- Dispatcher IDs are random inside a shift. No dispatcher is slower than another.
- Hospital times, on-scene care and pre-arrival instructions are not modelled (out of scope).
- The numbers in this file are what you get with seed 42. Another seed gives different chance
  alarms, but the planted signals stay.
