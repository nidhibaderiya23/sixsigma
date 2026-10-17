# ERGent: function reference

This folder holds ERGent (version 1): a Shiny for Python dashboard for a city 911 EMS dispatch center, by Team ERG. This page explains **how each function works, what goes in, what comes out, and what happens when the data is bad**. For what the tool is and how to run it, start with the [main README](../README.md). For the formulas and the hand-worked known answers, see [`SPEC.md`](../SPEC.md) section 4.

**Contents:**
[1. What is in this folder](#1-what-is-in-this-folder) |
[2. The four scripts](#2-the-four-scripts) |
[3. Conventions](#3-conventions) |
[4. `qc.py`: the statistics](#4-qcpy-the-statistics) |
[5. `charts.py`: the figures](#5-chartspy-the-figures) |
[6. `simulator.py`: the live board](#6-simulatorpy-the-live-board) |
[7. The screens](#7-the-screens) |
[8. Tests](#8-tests)

---

## 1. What is in this folder

| File | Role |
|---|---|
| [`qc.py`](qc.py) | **Every statistic.** Plain functions on pandas tables and lists of numbers. No Shiny, no plotting. |
| [`charts.py`](charts.py) | Matplotlib figures for the supervisor screens and the dispatcher's History tab. Draws what `qc.py` computed. Computes nothing. |
| [`simulator.py`](simulator.py) | The live board's rules: the call model, the fleet, the clocks, and the shift replay. Pure Python, unit-tested. |
| [`ui_dispatcher.py`](ui_dispatcher.py) | Dispatcher screens (live board, History tab), the simulation controls for the page header, and the building blocks both roles share. |
| [`ui_supervisor.py`](ui_supervisor.py) | Supervisor screens: the Charts and Actions tabs, with short "More info" toggles. |
| [`app.py`](app.py) | The Shiny app: start page, role picker, header. Wires the two roles together. |
| [`ui_help.py`](ui_help.py), `www/help.css` | The **How to use** and **About** pages (static), opened from the header. |
| [`zonemap.py`](zonemap.py), `www/zonemap.js` | The interactive Ithaca, NY zone map (Leaflet) both roles use. See [section 5a](#5a-zonemappy-and-wwwzonemapjs-the-ithaca-map). |
| `www/rw.css`, `www/rw.js` | The look (each version has its own), and a small script that repaints the running clocks once a second and opens a view from a link. |
| `requirements.txt` | Pinned dependencies (`==`). |
| `.python-version` | `3.12`. Must match the manifest. |
| `testme.sh`, `manifestme.sh`, `deployme.sh` | The scripts in [section 2](#2-the-four-scripts). |
| `README.md` | This file. |

The rule that holds the design together: **statistics live in `qc.py` only.** The UI files call `qc.py` and draw the answer. If a number on screen looks wrong, the place to look is `qc.py`, and the place to check it is [`tests/test_qc.py`](../tests/test_qc.py).

---

## 2. The four scripts

The course's four-script contract: `testme.sh`, `manifestme.sh`, `deployme.sh`, and this `README.md`. Run the scripts from anywhere. Each one changes into `app/` first.

All three scripts pick Python the same way: if `../.venv/bin/python` (the repo-root virtual environment) exists, they use it. If not, they use `python` from your PATH.

### `testme.sh`: run the app locally

```bash
cd app && ./testme.sh        # then open http://localhost:8000
```

1. Picks Python (see above).
2. Runs `python -m shiny run app.py --port 8000`.

You must install the requirements first: `.venv/bin/pip install -r app/requirements.txt` (from the repo root).

### `manifestme.sh`: write the Posit Connect manifest

```bash
cd app && ./manifestme.sh
```

1. Stops with a message if there are no `../data/*.csv` files.
2. Copies `../data/*.csv` into `app/data/` (it creates the folder). Connect deploys only the `app/` folder, so the data must travel with it. `qc.find_data_dir()` looks in `app/data` first, then in the repo's `data/`.
3. Runs `pip install rsconnect-python` with the chosen Python. This tool is for deploying and is not in `requirements.txt`, so it does not ship with the app.
4. Runs `rsconnect write-manifest shiny . --entrypoint app:app`. This writes `app/manifest.json`: the Python version, the packages, and the list of files.

Commit `manifest.json` and `app/data/`. The GitHub Actions workflow ships exactly the files the manifest lists, and never regenerates it. Re-run this script after you change code, requirements or data.

### `deployme.sh`: publish by hand from your machine

```bash
cd app && ./deployme.sh
```

1. Picks Python and installs `rsconnect-python`.
2. If `app/.env` exists, loads it (it is git-ignored). It may define `CONNECT_SERVER` and `CONNECT_API_KEY`.
3. Copies `../data/*.csv` into `app/data/`, as above.
4. Runs `rsconnect deploy shiny --entrypoint app:app .`. It adds `--server` and `--api-key` only when those variables are set. Otherwise `rsconnect` uses your saved account.

The script never contains a key. **Keys go in your shell, in an untracked `.env`, or in GitHub repo secrets. Never in a committed file.** The normal route is the GitHub workflow in [`.github/workflows/deploy-shiny-py.yml`](../.github/workflows/deploy-shiny-py.yml); see the main README, section 10.

---

## 3. Conventions

- **Units.** Times are **seconds** in the data and in columns ending `_s`. They are **minutes** on screen and in columns ending `_min`.
- **The `stages` table.** `qc.stage_times()` turns a raw calls table into the `stages` table. Almost every other function takes `stages` as its first argument. Only rows with `valid == True` enter any statistic.
- **Log scale.** Control charts, capability and tests work on `ln(response minutes)`. Log columns say so (`mean_log`, `log_min`).
- **Zones and priorities.** `zone` is `"A"` to `"F"`, or `"All"` where a function accepts it. `priority` is `1`, `2` or `3` (an `int`).
- **The `targets` dict.** Seconds. `{"processing": 64, "turnout": 60, "response": {1: 540, 2: 900, 3: 1200}}`. The default is `qc.TARGETS`. The supervisor's settings build one of these.
- **Results.** Single statistics return a **dict** with an `ok` flag and a `message`. When `ok` is `False`, the number fields are `None` and `message` says why. Table results are **DataFrames**. Nothing here raises an error on bad data, except where a function below says so.
- **Limit window.** Control limits come from a window of `baseline_days` days (default 14) starting at `baseline_start` (default: the first day with a valid call), and apply to every day. In the app the window is the **chart period** the user picks (14, 28 or 42 days). That is simple and keeps the map, the suggestions and the chart in agreement. It has a cost: a problem that lasts most of the period widens the limits and can hide itself.

A typical session, from the repo root:

```python
from app import qc

stages = qc.stage_times(qc.load_calls("data/calls_demo.csv"))
chart = qc.daily_xbar_s(stages, "D", priority=1)                 # one row per day for Zone D
health = qc.zone_health(stages, priority=1, as_of="2026-09-28")  # one row per zone
fixes = qc.suggest(qc.until(stages, "2026-09-28"), priority=1)   # list of suggestions
```

---

## 4. `qc.py`: the statistics

`qc.py` has **37 public functions** and a few public constants, listed in the order they appear in the file. Functions starting with `_` are helpers ([4.9](#49-private-helpers)).

### 4.1 Constants

| Name | Value | Meaning |
|---|---|---|
| `ZONES` | `("A", "B", "C", "D", "E", "F")` | The six zones |
| `PRIORITIES` | `(1, 2, 3)` | Call priorities |
| `STAGES` | `("processing", "turnout", "travel")` | The three timed stages |
| `TIMESTAMPS` | `call_received, dispatched, en_route, on_scene, cleared` | The five stamps, in order |
| `TARGETS` | `{"processing": 64, "turnout": 60, "response": {1: 540, 2: 900, 3: 1200}}` | Default targets in seconds, each met by at least 90% of calls. Processing, turnout and P1 travel are NFPA 1710. P2 and P3 response targets are our assumptions. |
| `REASON_CODES` | 6 keys | `traffic_or_road_closure`, `ambulance_breakdown`, `unit_from_another_zone`, `unclear_address`, `weather`, `crew_not_ready`, each mapped to a label |
| `SHIFTS` | day 06-14, evening 14-22, night 22-06 | Shift boundaries by hour |
| `CALL_COLUMNS` | 14 names | The columns of every calls CSV (see [`data/README.md`](../data/README.md)) |
| `D2`, `D4` | 1.128, 3.267 | Control-chart constants for moving ranges of span 2 |
| `PRIORITY_NAME` | `{1: "Life-threatening", 2: "Urgent", 3: "Non-urgent"}` | Plain names of the call priorities |
| `RULE_TEXT` | R1 to R5 | Plain-words names for the flag rules, shown to the supervisor |
| `NEIGHBORS` | zone to a tuple of zones | Which zones share an edge on the city grid. Used by the dispatcher tips ([4.8](#48-live-shift-tools-dispatcher)). |

### 4.2 Loading and stage times

#### `stage_targets(priority, targets=TARGETS) -> dict`

Seconds allowed for each stage of a call with this priority.

- **Inputs:** `priority` (1, 2 or 3); `targets` (dict, seconds).
- **Returns:** `{"processing", "turnout", "travel", "response"}`, in seconds.
- **Formula:** `travel = response - turnout`. For P1 that is 540 - 60 = 480 s, the NFPA 1710 travel benchmark.
- **Degenerate:** a priority that is not in `targets["response"]` raises `KeyError`.

#### `find_data_dir() -> Path`

The folder that holds the CSVs: `app/data` if it exists (a deployed copy), else the repo's `data/`.

- **Returns:** a `Path`.
- **Degenerate:** raises `FileNotFoundError` if neither folder exists.

#### `shift_of(hour) -> str`

- **Inputs:** `hour`, 0 to 23.
- **Returns:** `"day"` for 06 to 13, `"evening"` for 14 to 21, `"night"` for 22 to 05.

#### `load_calls(path) -> DataFrame`

Reads a calls CSV.

- **Inputs:** `path` to a CSV with the `CALL_COLUMNS`.
- **Returns:** a DataFrame. The five timestamp columns are parsed to datetimes. ID and text columns are strings. A blank `delay_reason` becomes `""`.
- **Degenerate:** a blank or unreadable timestamp becomes `NaT`, and `stage_times` later flags that call as missing a stamp. A missing file raises the usual pandas error.

#### `stage_times(calls, targets=TARGETS) -> DataFrame`

The front door for the statistics. Adds stage durations, lateness and data-quality columns to every call.

- **Inputs:** `calls`, a raw calls table with at least `call_id, zone, priority, call_received, dispatched, en_route, on_scene`; `targets` (dict, seconds).
- **Returns:** a copy of `calls` plus these columns:

| Column | Meaning |
|---|---|
| `processing_s`, `turnout_s`, `travel_s`, `response_s` | Seconds: dispatched - call_received; en_route - dispatched; on_scene - en_route; **on_scene - dispatched** |
| `response_min` | `response_s / 60` |
| `response_target_s` | The response target for the call's priority |
| `late` | `response_s` is greater than the response target (`False` for invalid calls) |
| `processing_late`, `turnout_late`, `travel_late` | That stage is over its target (travel target = response target - turnout target) |
| `date`, `hour`, `shift` | The day (midnight timestamp), hour and shift of `call_received` |
| `issue` | `""` for a clean call, otherwise what is wrong |
| `valid` | `issue == ""`. **Only valid calls enter any statistic.** |

- **Formula (the checks).** They run in this order, and the first one that matches is the `issue`: `duplicate call_id` (the repeat is flagged; the first stays); `missing <column>` for `call_received`, `dispatched`, `en_route`, `on_scene`; `<later> before <earlier>` for a stamp earlier than the one before it; `zero response time` (on_scene is not after dispatched); `unknown zone`; `unknown priority`. `cleared` is not checked.
- **Degenerate:** a bad call is kept in the table with `valid == False` and the reason. It is never dropped silently and never counted. Its stage columns may be blank or negative; ignore them.

#### `data_issues(stages) -> DataFrame`

- **Inputs:** a `stages` table.
- **Returns:** the calls left out of the statistics, with columns `call_id, zone, priority, issue`. Empty when every call passed.

### 4.3 Summary numbers

#### `percentile(values, p) -> float`

- **Inputs:** `values`, numbers in any unit with **no NaN** (`summary` removes them first); `p`, a fraction from 0 to 1 (0.9 is the 90th percentile).
- **Returns:** a float.
- **Formula:** R's "type 7", also Excel's PERCENTILE.INC. Sort the values. Position h = (n - 1) x p, counting from 0. Result = x[floor h] + (h - floor h) x (x[floor h + 1] - x[floor h]). Example: on [4, 5, 6, 7, 8, 9, 10, 11, 12, 20], the 90th percentile has h = 8.1, so 12 + 0.1 x (20 - 12) = 12.8.
- **Degenerate:** one value gives that value. No values, or `p` outside 0 to 1, raises `ValueError`.

#### `summary(values_min, target_min) -> dict`

- **Inputs:** `values_min`, response times in **minutes** (NaN is ignored); `target_min`, the response target in minutes.
- **Returns:** `{"n", "mean", "sd", "median", "p90", "p95", "pct_on_time"}`. `sd` is the sample standard deviation (divides by n - 1). `pct_on_time` is 0 to 100. On time means value **at or under** the target.
- **Formula:** `median`, `p90`, `p95` are `percentile` at 0.5, 0.9, 0.95. Known answer: [4, 5, 6, 7, 8, 9, 10, 11, 12, 20] with target 9 gives mean 9.2, median 8.5, p90 12.8, p95 16.4, on time 60%.
- **Degenerate:** no values gives `n = 0` and every other field `None`. One value makes the median, p90 and p95 equal to it, and `sd` is `None`.

#### `zone_summary(stages, priority=1, targets=TARGETS) -> DataFrame`

- **Inputs:** a `stages` table; `priority`; `targets`.
- **Returns:** one row per zone A to F, plus a citywide `"All"` row. Columns: `zone, n, mean, sd, median, p90, p95, pct_on_time` (minutes, and %). It uses valid calls of that priority, with the target `targets["response"][priority] / 60`.
- **Degenerate:** a zone with no calls has `n = 0` and blank numbers.

### 4.4 Period helpers

#### `until(stages, as_of=None) -> DataFrame`

- **Inputs:** a `stages` table; `as_of`, a date or `None`.
- **Returns:** only the calls received **on or before** the as-of day. `None` returns everything.

#### `last_days(stages, days, as_of=None) -> DataFrame`

- **Inputs:** a `stages` table; `days`, a number of calendar days; `as_of`, optional.
- **Returns:** the calls in the last `days` days. The window ends on the newest day that has a valid call (up to `as_of`) and includes that day. Invalid calls cannot move the window.
- **Degenerate:** with no valid call at all, it returns the table unchanged.

### 4.5 Control charts

#### `c4(n) -> float`

The bias-correction constant for a standard deviation from `n` values.

- **Formula:** c4(n) = sqrt(2 / (n - 1)) x Gamma(n / 2) / Gamma((n - 1) / 2). It is the mean sample standard deviation of `n` normal values whose true sigma is 1. c4(2) = 0.7979, c4(3) = 0.8862.
- **Degenerate:** `n < 2` raises `ValueError`.

#### `imr_limits(values) -> dict`

Individuals and moving-range limits (the course method).

- **Inputs:** `values`, numbers in order (NaN ignored). The app passes ln minutes.
- **Returns:** `{"ok", "n", "center", "sigma", "ucl", "lcl", "mr_bar", "mr_ucl", "mr_lcl", "message"}`. `mr_lcl` is always 0.
- **Formula:** the moving ranges are the absolute differences between neighbours. MR-bar is their mean. Center = mean of the values. sigma_short = MR-bar / 1.128. Limits = center +/- 3 sigma_short. MR upper limit = 3.267 x MR-bar. Known answer: [10, 12, 11, 15, 12] gives MR-bar 2.5, center 12, sigma 2.2163, limits 5.351 to 18.649, MR upper 8.1675.
- **Degenerate:** fewer than 2 values gives `ok = False`, "need at least 2 values for a moving range". Constant values give `ok = False`, "no variation", and no limits.

#### `xbar_s_limits(subgroups, xbbar=None, sigma_short=None) -> dict`

Average (X̄) and standard-deviation (S) chart limits for subgroups of any size (the course formula). `daily_xbar_s` no longer uses it: it is used by `zone_subgroup_chart` (zones as subgroups) and by `zone_capability` (to get sigma_short).

- **Inputs:** `subgroups`, a list of lists of numbers (NaN ignored); `xbbar` and `sigma_short`, optional values estimated elsewhere (a baseline), applied as given.
- **Returns:** `{"ok", "xbbar", "sigma_short", "message", "subgroups"}`. `subgroups` has one dict per input subgroup, in order: `n, mean, sd, x_ucl, x_lcl, z, s_center, s_ucl, s_lcl`.
- **Formula:** x̄̄ = mean of the subgroup means. sigma_short = sqrt(mean of the subgroup variances), over subgroups with 2 or more values (the course formula). For a subgroup of size n_i:

| Piece | Formula |
|---|---|
| X̄ limits | x̄̄ +/- 3 sigma_short / sqrt(n_i). They widen on quiet days. |
| z | (subgroup mean - x̄̄) / (sigma_short / sqrt(n_i)) |
| S center | c4(n_i) x sigma_short |
| S limits | (c4 +/- 3 sqrt(1 - c4^2)) x sigma_short, lower limit never below 0 |

  Known answer: [2, 4, 6], [3, 5, 7], [4, 6, 8] give x̄̄ = 5, sigma_short = 2, X̄ limits 1.536 to 8.464, S center 1.7725, S upper 4.552, S lower 0.
- **Degenerate:** no subgroup with 2 or more values (and no fixed parameters) gives `ok = False` with a message. Constant subgroups give sigma_short 0, `ok = False`, "no variation". A subgroup of one value gets an X̄ point, limits and z, but its S fields are `None`. An empty subgroup has `None` everywhere.

#### `flag_rules(z, trend=None) -> list`

Run rules on standardized points.

- **Inputs:** `z`, a list of z-scores (center 0, one sigma = 1), in time order; `trend`, optional plotted values used only for R5 (the daily averages), so "6 rising" matches the chart. Without it, R5 looks at `z`.
- **Returns:** a list with one entry per point. Each entry is the sorted list of rule ids that fire **at that point**, such as `["R1+", "R2+"]`. A `+` is the slow side (an **alarm**). A `-` is the fast side (only "check the data").
- **Formula:**

| Rule | Fires at point i when |
|---|---|
| R1 | z beyond 3 sigma |
| R2 | z beyond 2 sigma, and so is at least 1 more of the last 3 points (2 of 3), same side |
| R3 | z beyond 1 sigma, and so are at least 3 more of the last 5 points (4 of 5), same side |
| R4 | this point and the 7 before it (8 in a row) are all above (or all below) the center line |
| R5 | this point and the 5 before it (6 in a row) are steadily rising (or falling) |

  R1 to R4 are the Western Electric rules. Known answers: [0.5, 2.5, 0.3, 2.4] fires R2+ at the 4th point. Eight points of 0.1 fire R4+ at the 8th. [1, 2, 3, 4, 5, 6] fires R5+ at the 6th.
- **Degenerate:** fewer than 8 points cannot fire R4, and fewer than 6 cannot fire R5. An empty list gives `[]`.

#### `daily_xbar_s(stages, zone, priority=1, baseline_days=14, baseline_start=None) -> DataFrame`

One row per day for a zone: the X̄-S chart of log response minutes, with flags. **The limits are constant**: one set for the whole chart, taken from a limit window.

- **Inputs:** `stages`; `zone` (`"A"` to `"F"` or `"All"`); `priority`; `baseline_days` (the limit window length, in days); `baseline_start` (the window's first day, or `None` for the first day with a valid call). In the app the window is the **chart period**.
- **Returns:** a DataFrame with one row for each day that has valid calls of that priority:

| Column | Meaning |
|---|---|
| `date`, `n` | The day, and the number of calls |
| `mean_log`, `sd_log` | Mean and standard deviation of ln minutes that day (`sd_log` is blank for a one-call day) |
| `x_center`, `x_ucl`, `x_lcl` | X̄ chart center and limits, in ln minutes (the same on every row) |
| `x_center_min`, `x_ucl_min`, `x_lcl_min` | The same in minutes (exp of the log values, so a geometric-mean scale) |
| `s_center`, `s_ucl`, `s_lcl` | S chart center and limits (the same on every row) |
| `s_flag` | The day's standard deviation is above `s_ucl` |
| `z` | The day's z-score: (daily mean - center) / sigma_xbar |
| `rules` | List of rule ids that fired that day (from `flag_rules`) |
| `alarm` | Any slow-side (`+`) rule fired |
| `check` | Only fast-side (`-`) rules fired: "check the data" |
| `baseline` | The day is inside the limit window |

  `df.attrs` holds `xbbar` (the center, ln minutes), `sigma_xbar`, `mr_bar` (now `None`), `sigma_short` (the window's within-day spread, for reference), `s_bar`, `n_bar`, `message`, and `baseline_note`.
- **Formula:** each day's point is the mean of that day's ln minutes. The limit window is the days from `baseline_start` up to `baseline_days` later.

| Piece | Formula |
|---|---|
| X̄ center | the mean of the daily means in the limit window |
| sigma_xbar | the standard deviation of those daily means (n - 1) |
| X̄ limits | center +/- 3 sigma_xbar. Constant, whatever the number of calls that day. |
| z | (daily mean - center) / sigma_xbar. `flag_rules` runs on these z-scores, with the daily means as the trend. |
| S center | s-bar = the mean of the window's daily standard deviations (days with 2 or more calls) |
| S limits | s-bar x (1 +/- 3 sqrt(1 - c4^2) / c4), the B4 and B3 constants, with c4 = `c4(n-bar)` and n-bar = the average calls per day in the window (rounded, at least 2). The lower limit is never below 0. |

  **A trade-off the team chose** (Oct 16 and 17): when the window is the chart period itself, the limits are simple and the map, suggestions and chart all agree. But a problem that lasts most of the period widens the limits and can hide itself. On the demo city, as of Sep 28 with a 28-day period, Zone D's daily chart shows **no red dots**, because its slowdown is inside the window. The zone map still shows D as amber, from its 90th percentile, and the capability card says D is below the standard. Limits taken from the first 14 days (the function's default) do flag D on 11 days.
- **Degenerate:** if the window has fewer than 2 days, or its daily means are all the same, the result is an **empty DataFrame** (the columns are still there) and `attrs["message"]` starts with "baseline:". If no day in the window has 2 or more calls, the S chart limits are blank and `s_flag` is `False`, but the X̄ chart still works. `baseline_note` warns when window days are themselves flagged, or when all the data is in the window.

#### `imr_chart(stages, zone, priority=1, baseline_days=14, baseline_start=None) -> DataFrame`

One row per call, in the order calls were received: the individuals chart of log response minutes (with the moving range kept in the `mr` column). The app draws it with `charts.individuals_chart`.

- **Inputs:** the same as `daily_xbar_s`.
- **Returns:** a DataFrame with `call_id, dispatched, date, response_min, log_min, mr` (the moving range, in ln minutes), `center, ucl, lcl` (ln minutes), `center_min, ucl_min, lcl_min` (minutes), `beyond` (above the upper limit: an **extreme delay**), and `below` (under the lower limit: check the data). `df.attrs` holds `mr_bar`, `mr_ucl`, `sigma`, `message`.
- **Formula:** `imr_limits` on the baseline calls' ln minutes (calls dated inside the baseline period). Those limits are applied to every call. (In the app the baseline is the chart period.)
- **Degenerate:** fewer than 2 baseline calls, or constant baseline calls, give blank limit columns, `beyond` and `below` all `False`, and `attrs["message"]` starting with "baseline:".

### 4.6 Capability and tests

#### `capability(values, usl, sigma_short=None) -> dict`

Upper-side Ppk, and Cpk when `sigma_short` is given. The target is an upper limit only, so there is no lower side.

- **Inputs:** `values`, numbers (the app passes ln minutes); `usl`, the upper specification limit on the same scale (the app passes ln of the target in minutes); `sigma_short`, optional, same scale.
- **Returns:** `{"ok", "n", "mean", "sd", "ppk", "cpk", "message"}`.
- **Formula:** Ppk = (USL - mean) / (3 x sd), where sd is the sample standard deviation (sigma_total). Cpk = (USL - mean) / (3 x sigma_short). Known answer: [6, 7, 8, 9, 10] with USL 12 gives sd 1.5811 and Ppk 0.8433.
- **Degenerate:** fewer than 2 values, or constant values, give `ok = False` and `None` indices with a message ("no variation: capability is undefined for constant data"). `cpk` is `None` when `sigma_short` is missing or 0.

#### `ppk_to_pct(ppk) -> float | None`

- **Inputs:** an upper-side Ppk.
- **Returns:** the % of calls expected within the target for a normal process: Phi(3 x Ppk) x 100, where Phi is the standard normal curve. Ppk 1.0 gives 99.87%. Ppk 0.43 gives about 90%.
- **Degenerate:** `None` or a non-finite number returns `None`.

#### `capability_verdict(row, target_min) -> dict`

A short plain-language reading of one `zone_capability` row, for someone new to Six Sigma. The Charts screen shows this instead of the numbers.

- **Inputs:** `row`, one row of the `zone_capability` table (a dict, or a pandas row, with `shown`, `message`, `n` and `ppk`); `target_min`, the response target in minutes (used in the text).
- **Returns:** `{"label", "tone", "text"}`. `tone` is `"green"`, `"amber"`, `"red"` or `"grey"`.
- **Formula:** when the row is `shown`, the expected share of calls on time is `ppk_to_pct(Ppk)` = Phi(3 x Ppk) x 100. It is **rounded first**, and the verdict is judged on that rounded number, so the label always agrees with the number in the text:

| Rounded % on time | Label | Tone | Text |
|---|---|---|---|
| 99 or more | Very reliable | green | "About 99 in 100 calls within 9 min." ("Almost every one of 100" at 100) |
| 95 to 98 | Reliable | green | "About 96 in 100 calls within 9 min." |
| 90 to 94 | Just meets the standard | amber | "About 94 in 100 calls within 9 min: little margin." |
| under 90 | Below the standard | red | "Only about 89 in 100 calls within 9 min." |

  When the row is not `shown`, the label comes from `message`: "too few calls..." gives **Not enough calls** (grey, "Only 7 calls; 30 are needed."); "not stable..." gives **Can't judge yet** (amber, "Times changed in this period, so no score yet."); anything else gives **Can't judge** (grey, the message, or "No data.").
- **Degenerate:** every non-`shown` row gets a label and text instead of a number, so nothing meaningless is printed.

#### `normality(values) -> dict`

Shapiro-Wilk test and normal probability plot points.

- **Inputs:** `values`, numbers (the app passes ln minutes).
- **Returns:** `{"ok", "w", "p", "theoretical", "ordered", "message"}`. `theoretical` and `ordered` are the plot's x and y. A p above 0.05 means the values look normal.
- **Degenerate:** fewer than 3 values, or constant values, give `ok = False` and empty plot lists.

#### `anova_zones(groups) -> dict`

One-way ANOVA across groups.

- **Inputs:** `groups`, a dict `{name: values}`.
- **Returns:** `{"ok", "F", "p", "df_between", "df_within", "ssb", "ssw", "means", "dropped", "message"}`. `means` holds each kept group's mean. `dropped` names the groups left out.
- **Formula:** with k groups and N values: SSB = sum of n_g x (group mean - grand mean)^2, SSW = sum of squared distances inside groups, F = (SSB / (k - 1)) / (SSW / (N - k)). `p` is the upper tail of the F distribution (scipy). Known answer: A = [1, 2, 3], B = [4, 5, 6] give SSB 13.5, SSW 4, F 13.5, df 1 and 4.
- **Degenerate:** groups with fewer than 2 values are dropped and named. Fewer than 2 groups left gives `ok = False`. If every group is constant, `ok = False` ("no variation inside the groups: F is undefined"), though `ssb` and `ssw` are still returned.

#### `welch_before_after(before, after) -> dict`

Welch's t-test, one-sided: is the "after" mean lower than "before"?

- **Inputs:** `before`, `after`: numbers (the app passes ln minutes).
- **Returns:** `{"ok", "t", "df", "p_one_sided", "mean_before", "mean_after", "n_before", "n_after", "message"}`.
- **Formula:** t = (mean_before - mean_after) / sqrt(s_b^2 / n_b + s_a^2 / n_a). df is the Welch-Satterthwaite value. p = P(T > t), so a **small p means "after" is really lower**. Known answer: before [10, 12, 14], after [6, 8, 10] give t = 2.449, df = 4.
- **Degenerate:** fewer than 2 values on either side gives `ok = False`. Both sides constant gives `ok = False` ("the test is undefined"). The means and counts are still returned.

#### `zone_anova(stages, priority=1) -> dict`

- **Inputs:** `stages`; `priority`.
- **Returns:** `anova_zones` on the ln response minutes of each zone's valid calls.
- **Degenerate:** as `anova_zones`. A zone with no calls is dropped.

#### `zone_capability(stages, priority=1, targets=TARGETS, baseline_days=14, baseline_start=None, min_n=30, period_days=None) -> DataFrame`

Capability per zone, shown only for stable zones with enough calls.

- **Inputs:** `stages`; `priority`; `targets`; the baseline arguments; `min_n`, the fewest calls a zone needs (default 30); `period_days`, the period to judge (for example 28). Pass all calls up to the as-of date. With `period_days`, the indices use only that period, and the control chart's limits come from the **same period**, as on the Charts screen (the baseline arguments are then ignored).
- **Returns:** one row per zone: `zone, n, ppk, cpk, stable, shapiro_p, shown, message`. `ppk` and `cpk` are filled only when `shown` is `True`.
- **Formula:** USL = ln(target minutes). Ppk uses the zone's ln minutes in the period (sigma_total). The period is the last `period_days` days, or the whole table if `period_days` is `None`. Cpk uses sigma_short = sqrt(mean of the daily variances) from the zone's daily subgroups in that period. `stable` means the zone's `daily_xbar_s` chart (limits from the period) has days in the period and **no slow-side flag on any of them**. `shown = capability is computable and stable and n >= min_n`. With few calls the indices are too uncertain to mean anything.
- **Degenerate:** an unstable zone has `shown = False` and the message "not stable: capability is not meaningful". A stable zone with fewer than `min_n` calls has `shown = False` and the message "too few calls for capability (n = X; need 30)". Constant data gives the "no variation" message. `shapiro_p` is blank when there are fewer than 3 values.

### 4.7 Stage breakdown, health, suggestions, before/after

#### `stage_breakdown(stages, priority=1, targets=TARGETS) -> DataFrame`

Which stage causes the delay, per zone and citywide.

- **Inputs:** `stages`; `priority`; `targets`.
- **Returns:** one row per zone and one `"All"` row. Columns: `zone, n`, then for each stage `<stage>_median_s` (median seconds), `<stage>_excess_min` (minutes over target, summed over calls) and `<stage>_share`.
- **Formula:** stage excess = max(0, stage time - stage target), summed over calls and shown in minutes. A stage's share = its excess / the zone's total excess over the three stages.
- **Degenerate:** no excess at all gives shares of 0. A zone with no calls has `n = 0` and blank medians.

#### `impact_estimate(calls, stage, cap_s, target_s=None) -> dict`

% on time now, and if every call's stage were at most `cap_s`.

- **Inputs:** `calls`, a table of valid calls (rows of `stages`); `stage` (`"processing"`, `"turnout"` or `"travel"`); `cap_s`, the cap in seconds (the app uses the citywide median of that stage); `target_s`, optional override.
- **Returns:** `{"stage", "cap_s", "n", "pct_on_time_before", "pct_on_time_after", "gain"}` (percent; `gain` is in percentage points).
- **Formula:** for turnout or travel: response = turnout + travel; new response = response - stage + min(stage, cap_s); on time means response is at or under the target (each call's own `response_target_s`, unless `target_s` is given). For processing: on time means processing is at or under `target_s`, by default 64 s. Known answer: turnout [3, 1, 4, 1] min, travel [7, 7, 6, 9] min, target 9 min, cap 1 min: on time goes from 1/4 = 25% to 3/4 = 75%.
- **Degenerate:** no calls gives `n = 0` and `None` percentages. It is an estimate, not a promise.

#### `chart_signal(rules) -> bool`

Is a zone's chart signal strong enough to count in zone health?

- **Inputs:** `rules`, a list of the slow-side rule ids that fired in the window, such as `["R2", "R4"]` (no `+` sign).
- **Returns:** `True` if `"R1"` is in the list, or if 2 or more different rules are in it. Otherwise `False`.
- **Formula:** rule 1 alone (a point beyond 3 sigma) counts. Any two different rules count. **One weaker rule alone does not count.** On a pure-noise simulation this keeps the chance amber rate of a stable zone-week near 2.5%, instead of 7.7% when any single rule counts.
- **Degenerate:** an empty list gives `False`.

#### `zone_health(stages, priority=1, targets=TARGETS, baseline_days=14, recent_days=7, as_of=None, actions=None, baseline_start=None, period_days=None) -> DataFrame`

The traffic light for each zone.

- **Inputs:** `stages`; `priority`; `targets`; the baseline arguments; `recent_days` (default 7); `as_of` (a date or `None`); `actions`, an optional table of logged actions (columns `date`, `zone`, optional `action_id`); `period_days`, the chart period. With `period_days`, the control limits come from the last `period_days` days up to `as_of` (the baseline arguments are then ignored), so the map agrees with the daily chart.
- **Returns:** one row per zone: `zone, status, p90_recent, rules, top_stage, top_share, reasons`. `status` is `"green"`, `"amber"`, `"red"` or `"unknown"`. `p90_recent` is in minutes. `rules` lists every slow-side rule that fired in the window (`"R1"` to `"R5"`), even when the signal is too weak to count. `top_stage` and `top_share` name the stage with the largest share of minutes over target (blank for green). `reasons` is a list of plain-words sentences.
- **Formula:** the window is the last `recent_days` days up to `as_of`. The rules are read from the daily chart's flags inside that window. A **chart signal** is `chart_signal(rules)`: rule R1 fired, or 2 or more different slow-side rules fired. **Red** = a chart signal AND the window's 90th percentile is over the target. **Amber** = exactly one of those. **Green** = neither. One weaker rule alone does not change the status. It stays in `rules` and adds the reason "one weak signal (...): not enough on its own, keep watching" to a green zone. A zone that is slipping back after a logged action (see `slip_back`) is at least amber. Amber means "worth a look"; red means "act".
- **Degenerate:** a zone whose chart has no limits, or that has no calls in the window, is `"unknown"` with the reason "not enough data for limits yet".

#### `suggest(stages, actions=None, priority=1, targets=TARGETS, window_days=14, as_of=None, baseline_days=14, baseline_start=None, period_days=None) -> list`

Fixed if-then suggestions, with evidence. The rules are in [`docs/plan.md`](../docs/plan.md).

- **Inputs:** `stages`; `actions` (logged actions, columns `date`, `zone`, `stage`); `priority`; `targets`; `window_days` (default 14); `as_of`; the baseline arguments; `period_days`, passed to `zone_health` so the suggestions use the same period limits as the map.
- **Returns:** a list of dicts, each with `rule` (`"S1"` to `"S6"`), `zone` (`"A"` to `"F"` or `"All"`), `stage`, `text`, `evidence`, `impact` (an `impact_estimate` dict, or `None`), `status`, and `note` ("For review by qualified staff."). `status` is `"new"`, or `"action logged on <date>"` when an action for the same zone and stage is dated inside the window or later.
- **Formula:** the window is the last `window_days` days up to `as_of`. A stage's *share* is its excess divided by the zone's total excess. The citywide median of each stage in the window is the cap for `impact_estimate`.

| Rule | Applies to | Fires when |
|---|---|---|
| S1 | each amber or red zone | Turnout share is 50% or more. Names a shift when that shift holds 40% or more of the zone's turnout excess **and** at least 1.5 times its share of the zone's calls (the text then gives both percentages). |
| S2 | each amber or red zone | Travel share is 50% or more, 30% or more of the late calls are coded `unit_from_another_zone`, and the zone's rate of borrowed units is at least 1.5 times the city rate. Names the busiest 3-hour window of late calls. |
| S3 | each amber or red zone | Travel share is 50% or more, and `traffic_or_road_closure` is the top delay code with at least 3 calls and at least 30% of the late calls. Names the busiest 3-hour window of late calls, and says "weekdays" if 80% or more of them fall on weekdays. |
| S4 | citywide, all priorities | In an hour of the day with above-median call counts, the processing 90th percentile is over the processing target. Lists the busy hours. |
| S5 | citywide | One ambulance has 2 or more `ambulance_breakdown` calls in the window. |
| S6 | each zone | The zone has at least 5 late calls and 20% or more are coded `unclear_address`. |

- **Degenerate:** no zone or stage matching a rule gives an empty list. Without `actions`, every status is `"new"`.

#### `before_after(stages, zone, action_date, priority=1, window_days=14, targets=TARGETS) -> dict`

Did the zone improve after the action?

- **Inputs:** `stages`; `zone`; `action_date`; `priority`; `window_days` (default 14); `targets`.
- **Returns:** `{"zone", "action_date", "test", "before", "after", "after_chart", "in_control_after", "verdict"}`. `test` is a `welch_before_after` result. `before` and `after` are `summary` dicts (minutes). `after_chart` is the zone's `daily_xbar_s` chart from the action date on, with its own limits from the first `window_days` days after the action. `in_control_after` is `True` when that chart has no slow-side flag. `verdict` is `"improved"`, `"got worse"`, `"no clear change yet"` or `"not enough data"`.
- **Formula:** "before" is the `window_days` days before the action date. "after" is the days from the action date on, up to `window_days`. Welch's one-sided test runs on ln minutes. *Improved* means p < 0.05. *Got worse* means p > 0.95 (significant the other way).
- **Degenerate:** if the test cannot run (fewer than 2 calls on either side, or no variation at all), `verdict` is `"not enough data"` and `test["message"]` says why.

#### `slip_back(stages, actions, priority=1, settle_days=7) -> list`

Zones drifting back after a fix.

- **Inputs:** `stages`; `actions` (columns `date`, `zone`, optional `action_id`); `priority`; `settle_days` (default 7).
- **Returns:** a list of dicts with `zone, action_id, since` (the first flagged day), `rules` (such as `["R4"]`) and `text`. Empty when no zone is slipping.
- **Formula:** for each action, rebuild the daily X̄-S limits from the first `settle_days` days after the action. Any slow-side flag on a day after those `settle_days` days raises an alert.
- **Degenerate:** no actions (or `None`) gives `[]`. An action whose zone has no limits (too little data) is skipped.

### 4.8 Live shift tools (dispatcher)

Support for the dispatcher's history and live-shift view: which calls belong to "this shift and the one before", how each zone compares with the city, and real-time tips. A shift is 8 hours: day 06-14, evening 14-22, night 22-06 (see `shift_of`).

#### `NEIGHBORS`

A dict from each zone to the tuple of zones that share an edge on the city grid (A B C on the top row, D E F below).

| Zone | Neighbors |
|---|---|
| A | B, D |
| B | A, C, E |
| C | B, F |
| D | A, E |
| E | B, D, F |
| F | C, E |

`dispatcher_tips` uses it to look for a nearby free ambulance and to say which zones should cover.

#### `shift_window(now) -> dict`

The shift that `now` falls in, and the shift before it.

- **Inputs:** `now`, a date and time (anything `pandas.Timestamp` accepts).
- **Returns:** `{"now", "current", "current_start", "previous", "previous_start", "label"}`. `current` and `previous` are `"day"`, `"evening"` or `"night"`. The starts are timestamps. `label` is text such as `Current: night shift 22:00-06:00, Sep 19 · Previous: evening shift 14:00-22:00, Sep 19`.
- **Formula:** `current = shift_of(now.hour)`. `current_start` is that shift's start hour (06, 14 or 22) on `now`'s date, or on the day before if that would be later than `now` (a night shift after midnight began the evening before). `previous_start = current_start - 8 hours`. Example: at 2026-09-20 02:30, the night shift began Sep 19 22:00 and the previous (evening) shift began Sep 19 14:00.
- **Degenerate:** none. A time that cannot be parsed raises the usual pandas error.

#### `shift_calls(stages, now) -> DataFrame`

The calls the dispatcher's two-shift view should use.

- **Inputs:** a `stages` table; `now`.
- **Returns:** the rows of `stages` that are valid, were received from the previous shift's start up to `now`, **and had reached the scene by `now`** (`on_scene <= now`). So a shift replay never shows the future, and calls still in progress are left out.
- **Degenerate:** no matching calls gives an empty table with the same columns.

#### `zone_subgroup_chart(stages, priority) -> DataFrame`

Each zone as one subgroup of log response minutes, compared with the city's limits. It is the course's X̄ chart with zones, not days, as the subgroups.

- **Inputs:** a `stages` table (usually from `shift_calls`); `priority` (1, 2 or 3).
- **Returns:** one row per zone A to F: `zone, n, mean_log, sd_log, mean_min, x_ucl, x_lcl, x_ucl_min, x_lcl_min, z, flag, values_log`. `_min` columns are in minutes (`mean_min` is the geometric mean). `x_ucl` and `x_lcl` are ln minutes. `values_log` is the list of the zone's ln minutes, for the box plot. `flag` is `"above"` (slower than the city), `"below"` (faster: check the data) or `""`. `df.attrs` holds `xbbar`, `sigma_short` (ln minutes), `center_min` (minutes) and `message`.
- **Formula:** this is `xbar_s_limits` on the six zones. Center x̄̄ = mean of the zone means. sigma_short = sqrt(mean of the zone variances), over zones with 2 or more calls. A zone's limits are x̄̄ +/- 3 sigma_short / sqrt(n_zone), so a zone with few calls gets wide limits. z = (zone mean - x̄̄) / (sigma_short / sqrt(n_zone)). `flag` is `"above"` when z > 3 and `"below"` when z < -3. Zones have no time order, so only this beyond-the-limit rule applies (like an analysis of means).
- **Degenerate:** no valid calls of that priority gives every `n = 0`, no limits, and `attrs["message"]` = "no completed calls yet in these two shifts". If no zone has 2 or more calls, or all calls are the same, there are no limits or flags and `message` says why. A zone with no calls has blank numbers. A zone with one call has limits and a z-score but no `sd_log`.

#### `zone_delay_reason(stages, zone, priority, targets=TARGETS) -> str`

One plain sentence on why a zone is slow. It is the hover text on a red zone in the History chart.

- **Inputs:** a `stages` table (the shift window); `zone`; `priority`; `targets`.
- **Returns:** text such as "Zone D is slower than the city: 9.3 min typical vs. 6.3 min. Main cause: crew turnout (100% of minutes over target). Top reason: crew not ready (2 of 2 late calls)."
- **Formula:** "typical" is the geometric mean (exp of the mean of ln minutes) of the zone's calls, against the same for all zones. The main cause is the stage with the largest share of minutes over target (only named when that share is above 0). The top reason is the most common delay code among the zone's late calls (late response, turnout or travel), and is left out when no late call has a code.
- **Degenerate:** a zone with no calls gives "Zone X: no completed calls."

#### `dispatcher_tips(window, board_calls, fleet, now, targets=TARGETS) -> list`

Real-time suggestions for the dispatcher, from the live board and the last two shifts. The tool decides nothing: these are for the dispatcher's judgment.

- **Inputs:**
  - `window`: a `stages` table of the last two shifts, from `shift_calls`. All priorities. Invalid calls are ignored. May be `None`.
  - `board_calls`: the live board's calls in the `CALL_COLUMNS` layout, with blank stamps for steps not done yet (the screen passes `Board.calls_frame(now)`). May be `None`.
  - `fleet`: a list of dicts with `unit_id`, `home_zone` and `state` (`available`, `dispatched`, `en_route`, `on_scene` or `out_of_service`). May be `None`.
  - `now`: the current time; `targets`: a targets dict (seconds).
- **Returns:** a list of dicts `{"rule", "zone", "text", "evidence"}`. `zone` is `"A"` to `"F"`, or `"All"` for T6. The order is T1, T2, T3, then T4 and T5 zone by zone, then T6.
- **Formula (the rules):**

| Rule | Fires when | Suggestion |
|---|---|---|
| T1 | A call on the board has no dispatch stamp and no on-scene stamp, and has waited longer than the processing target (64 s by default) | "Dispatch call X now." Names the nearest free ambulance: first one from the call's own zone, then one from a neighbor (in `NEIGHBORS` order). If none is free: "No ambulance nearby is free: ask the closest crew to clear." |
| T2 | A zone that has ambulances has none free, and a neighbor has 2 or more free | "Move one ambulance from Zone N to stand by in Zone Z." N is the neighbor with the most free. |
| T3 | A zone has an ambulance out of service | "Ask Zone N or Zone M to cover Zone Z's calls." The evidence lists the unit IDs. |
| T4 | A zone has 3 or more calls in the window, and its median travel is at least 1.25 times the city's median travel | The text follows the top delay code among the zone's late calls (late response or late travel), **but only when 2 or more late calls share that code**: `traffic_or_road_closure` gives "reroute around the traffic or road works"; `unit_from_another_zone` gives "keep an ambulance posted in the zone"; otherwise (no code shared by 2 calls) "check the route before sending the next unit" |
| T5 | A zone has 3 or more calls in the window, and its median turnout is over the turnout target (60 s by default) | "Alert Zone Z's station: crews are slow to get rolling." |
| T6 | The window has 5 or more valid calls, and the city's 90th percentile of processing (`percentile` at 0.9) is over the processing target | "Dispatch is slowing: ask the supervisor for a second dispatcher." |

- **Degenerate:** no board calls (`None` or empty) means no T1. No fleet means no T2 or T3. An empty or `None` window means no T4, T5 or T6. A quiet board returns `[]`.

### 4.9 Private helpers

These start with `_`. They are not part of the interface.

| Helper | Job |
|---|---|
| `_calls(stages, zone, priority)` | Valid calls of one priority for one zone, or all zones for `"All"` |
| `_clean(values)` | Numbers as a float array with NaN removed |
| `_no_spread(values)` | `True` when all values are the same, allowing for floating-point noise in the last bit |
| `_valid_dates(stages)` | Dates of valid calls only, so an excluded call can never move a window |
| `_baseline_window(stages, baseline_days, baseline_start)` | The start and end of the baseline period |
| `_stage_excess(calls, st)` | Minutes over target per stage, and each stage's share |
| `_busiest_hours(calls, width=3)`, `_hours_text(start, width=3)` | The busiest 3-hour window, and its text such as `17:00-20:00` |
| `_fmt_secs(s)` | Seconds as `m:ss` text for tip evidence (75 gives `1:15`) |

---

## 5. `charts.py`: the figures

Drawing only. There are 11 public functions. Each takes a result from `qc.py` and returns a matplotlib `Figure` in the app's dark style (constrained layout, backend `Agg`, so no window opens), or SVG text. **Control limits (from the process) are dashed grey. The target (a specification limit) is a solid amber line.** They are never confused.

| Function | Takes | Shows |
|---|---|---|
| `daily_chart(chart, zone, action_dates=(), target_min=None)` | `qc.daily_xbar_s` output | **Top** ("Zone D: daily average response"): the daily average in minutes (geometric mean), with the constant center line and dashed control limits. Red dots are flagged days. Hollow amber rings are "check the data" days. With `target_min`, a solid amber line draws the target (spec). Green vertical lines mark logged actions. **Bottom:** the daily standard deviation of ln minutes with the S chart's center and upper limit. Date labels appear every 5 days. |
| `individuals_chart(imr, zone, target_min)` | `qc.imr_chart` output and the target | Every call in order on a log axis (labelled in minutes), with the center line, the UCL and LCL (dashed), and the target as the amber spec line. Red dots are calls beyond the UCL. There is no moving-range panel. |
| `stage_breakdown(bd)` | `qc.stage_breakdown` output | Stacked horizontal bars: the median minutes in processing, turnout and travel, per zone |
| `stage_share(bd)` | `qc.stage_breakdown` output | Stacked horizontal bars: each stage's share of the zone's minutes over target (0 to 100%). The last bar, "City", is all zones. |
| `stage_share_svg(bd)` | `qc.stage_breakdown` output | The same chart as inline SVG. **Hover a bar** to see its share, the minutes over target in total, and the median time of that stage. |
| `to_svg(fig, tips=None)` | a figure, and a dict `{gid: text}` | The figure as inline SVG that fills its container's width. Each artist whose `gid` is a key of `tips` gets an SVG `<title>`, which the browser shows as a hover tooltip. |
| `normal_plot(norm, zone)` | `qc.normality` output | The normal probability plot of ln minutes, with a fit line and the Shapiro-Wilk p in the title |
| `before_after_chart(chart_full, zone, action_date, target_min=None)` | `qc.daily_xbar_s` output | The `daily_chart` with the action marked and the target line |
| `zone_box_chart(sub, priority, target_min, reasons=None)` | `qc.zone_subgroup_chart` output, the priority, the target in minutes, and optional `{zone: text}` | One **box plot per zone** of ln response minutes (axis labels in minutes, log scale). The title is the bold priority name, such as "Priority 2: Urgent". A diamond marks each zone's mean: blue normally, red when the zone is slower than the city, a hollow amber ring when faster (check the data). A solid grey line is the city center. Short dashed grey lines are each zone's control limits. A solid amber line is the target. The axis labels show `n` per zone. |
| `zone_box_svg(sub, priority, target_min, reasons=None)` | the same | `zone_box_chart` as inline SVG. **Hover a diamond:** a red one shows its text from `reasons` (made by `qc.zone_delay_reason`); any other shows the zone's typical time and call count. |
| `empty(message)` | text | A blank figure with a short message. The figure functions fall back to it when there is no data or no limits. |

---

## 5a. `zonemap.py` and `www/zonemap.js`: the Ithaca map

The six zones drawn on a Leaflet map of Ithaca, NY. The outlines are **illustrative** areas of the city (not official
EMS districts) on the same 3 x 2 layout as `qc.NEIGHBORS`: A West Hill, B Northside & Fall Creek, C Cornell &
Collegetown (north of State Street), D West End & Southwest, E Downtown & South Hill, F East Hill & Belle Sherman. The
names live in `qc.ZONE_NAMES`, the city in `qc.CITY`. The map tiles are Esri's grey canvas (no API key); the map needs
an internet connection.

| Name | Inputs | Output | Notes |
|---|---|---|---|
| `POLYGONS` | | `{zone: [[lat, lon], ...]}` | The zone outlines. |
| `geojson()` | | GeoJSON FeatureCollection | Each feature has `zone`, `name` and `center` (for the letter label). |
| `head()` | | Leaflet's CSS and JS (unpkg, 1.9.4) and `www/zonemap.js` | Added once to the page head in `app.py`. |
| `map_div(element_id, click_input=None, height="320px", tiles=None)` | namespaced ids (use `resolve_id` in a module UI) | the map container | `click_input`: the Shiny input that receives the clicked zone letter. `tiles`: "dark" or "light" (default: the CSS variable `--map-tiles`). |
| `update(session, element_id, zones)` (async) | `zones = {zone: {"sev": "green"/"amber"/"red"/"grey", "status": str, "lines": [str]}}` | a `rw-zonemap` custom message | Colours each zone (CSS variables `--map-green`, `--map-amber`, `--map-red`, `--map-grey`) and sets its hover text. Await it inside an async `reactive.effect`. |

The supervisor's map (`ui_supervisor.py`, `_paint_map`) paints `qc.zone_health`: the status word, the main delay and the
reasons. The dispatcher's map (`ui_dispatcher.py`, `_paint_live_map`) paints `Board.zone_tiles`: the worst open clock,
the open calls and the available units.

**Links that open a view directly** (`www/rw.js`, for demos and screenshots): `/?role=dispatcher` or
`/?role=supervisor`; add `&tab=History` or `&tab=Actions` to open that tab, and `&sim=1` to start the dispatcher's
shift replay.

## 6. `simulator.py`: the live board

Pure Python, no Shiny, no plotting, and **no statistics**. It uses `qc` only for targets and reason codes. Time is always passed in as `now`, never read from the clock inside a function, so the same code runs on wall-clock time and on the replay clock. It is unit-tested in [`tests/test_simulator.py`](../tests/test_simulator.py).

A call moves one step at a time (the poka-yoke): received, dispatched, en route, on scene, cleared. Only the next step is accepted. A step that ends a stage that ran past its target needs a delay reason from `qc.REASON_CODES`.

### `events_until(calls_df, sim_time) -> DataFrame`

Each call's state at a simulated time. This is what the "Simulate a shift" replay shows.

- **Inputs:** `calls_df`, a calls table (from `qc.load_calls`); `sim_time`, a datetime.
- **Returns:** the calls already received at `sim_time` (`call_received <= sim_time`), in arrival order. It has the `qc.CALL_COLUMNS` plus `status`: `received`, `dispatched`, `en_route`, `on_scene` or `cleared`, set from the latest stamp reached. **Stamps after `sim_time` are blanked** (`NaT`). The unit, home zone and distance stay blank until the call is dispatched. The delay reason stays blank until the call reaches the scene, as in CAD.
- **Degenerate:** if no call has been received yet, it returns an empty table with the same columns. The input table is not changed.

### The rest of the file

| Piece | Job |
|---|---|
| `day_calls(calls_df, day)`, `available_days(calls_df)`, `pick_day(days, preferred)` | Pick one day of the demo file to replay (default `2026-09-20`) |
| `Replay(day_df, speed=60, start_hour=0)` | A shift replay on a simulated clock. `start()`, `pause()`, `set_speed()`, `advance(real_seconds)` moves the clock by real seconds x speed while running. `now` is the simulated time. `state()` is `events_until` at that time. Calls cleared before the start hour are left out. It stops itself at the day's last stamp. |
| `Call` | One call, with the `CALL_COLUMNS` fields plus board fields. `status`, `elapsed(stage, now)` and `severity(now)` are properties of the call. |
| `late_stage(call, action, now)` | The stage a button press would end, if it already ran past its target. Pressing On scene also checks total response. |
| `severity(elapsed_s, target_s)`, `worst(*levels)` | `"red"` past the target, `"amber"` above 80% of it, else `"green"`. `worst` picks the most serious. |
| `ManualClock(start, mono, speed=1)` | The clock for calls logged by hand: wall time at 1x, or faster at 10x, 30x or 60x (`MANUAL_SPEEDS`). The caller passes in the monotonic time (`now(mono)`), so it is testable. `set_speed(speed, mono)` continues from the current board time, so the clock never jumps. `reset(start, mono)` goes back to a wall time and keeps the speed. |
| `Board` | One browser session's board. It has two worlds, one for the manual clock and one for the replay clock, so their calls never mix. `add_call` stamps the received time. `check` and `apply` accept only the next step (they raise `BoardError`, or `ReasonRequired` when a reason is missing). `fleet`, `available_units`, `set_out_of_service` and `back_in_service` manage the 12 ambulances. `sync_replay` loads a replay state. `reset_all` empties the board: no calls, replay or manual, and every ambulance available. `counts` and `zone_tiles` feed the live board. `calls_frame(now=None, manual_only=False, all_worlds=False)` returns the calls as a `CALL_COLUMNS` table with real timestamps (stamps after `now` blanked): the History tab and `qc.dispatcher_tips` read it. `to_frame` exports every call of both clocks as text (the "Download calls" file). |
| `SPEEDS`, `MANUAL_SPEEDS`, `START_HOURS`, `DEFAULT_DAY` | Replay speeds (30, 60, 120), manual clock speeds (1, 10, 30, 60), the replay start hours (0, 6, 14, 22), and the default replay day (`2026-09-20`) |
| `load_units(path=None)`, `default_fleet()` | The fleet list from `data/units.csv`, or the default two ambulances per zone |
| `fmt_clock`, `fmt_time`, `epoch` | Formatting helpers (`75` seconds is `1:15`) |

---

## 7. The screens

| File | Role |
|---|---|
| [`app.py`](app.py) | Builds the start page (two role buttons) and the header: the logo, the brand "ERGent" with the subtitle "Team ERG · City EMS dispatch · v1", a chip with the role, a chip with the clock mode, and a **Switch role** link. On the dispatcher screen only, the header also holds the simulation controls (`sim_controls_ui`). A hidden navset switches between the start page, the dispatcher view and the supervisor view. The live board's state lives inside `server()`, so each browser session has its own. |
| [`ui_dispatcher.py`](ui_dispatcher.py) | The dispatcher view and the building blocks both roles share (`icon`, `chip`, `tag`, `card_head`, and `get_calls`, which reads and caches a calls CSV). Details in [7.1](#71-the-dispatcher-view). |
| [`ui_supervisor.py`](ui_supervisor.py) | The supervisor view: two tabs, Charts and Actions. Details in [7.2](#72-the-supervisor-view). |

### 7.1 The dispatcher view

`ui_dispatcher.py` draws it. The rules are in `simulator.py`, and every number, limit and tip is a `qc` call.

| Piece | What it is |
|---|---|
| `sim_controls_ui()` | The compact simulation controls in the page header: **Day** (default Sep 20), **Speed** (30x, 60x, 120x), **Start at** (00:00, 06:00, 14:00, 22:00), a **Simulate a shift** button (it becomes **Pause**, **Resume** or **Run again**) and **Reset**. |
| `dispatcher_ui()`, `dispatcher_server(active)` | Two tabs: **Live board** and **History**. The server returns a reactive clock label for the header chip: `LIVE 1x` (green), `LIVE 10x`, `LIVE 30x`, `LIVE 60x`, or `SIM 30x`, `SIM 60x`, `SIM 120x` (amber). |
| `history_ui()`, `history_server(visible, board, now)` | The History tab. `visible` is true only while the tab is shown. `board` and `now` are the live board and its clock. |
| `RESOLVED_SHOWN`, `HISTORY_REFRESH_S`, `TIP_NAMES`, `chart_note_text(sub)` | The Resolved list length (60), the History refresh interval (5 s), the display names for the tips, and the one-line note under the zone chart. |

**Live board** (title "Live board"), top to bottom:

1. A KPI row: Waiting, Dispatched, En route, On scene, Units available.
2. Numbered cards in a 2 x 2 grid: **1 Log a call** (zone, priority as "1: Life-threatening", **Clock speed** 1x, 10x, 30x or 60x, **Add call**) next to **2 Incoming calls**; then **3 Dispatched** next to **4 En route**.
3. **Ambulances** next to the **Zone map**, an interactive map of Ithaca, NY (`zonemap.py`). Each zone is coloured by its worst open call (the same green / amber / red as the clocks); hover a zone for its name, status, open calls and available units; click a zone to pick it in **Log a call**. The ambulances sit in four status columns, each with a count: **Available**, **Responding** (dispatched or en route, and the chip says which), **On scene** and **Out of service**. Each chip shows the unit ID, its home zone and one button (**Out of service** or **Back in service**).
4. **5 Resolved**, full width. A call counts as resolved once it is on scene. The list scrolls (at most 360 px tall) and shows the latest 60. A call you logged by hand and that is still at the scene has a small **Clear** button (with a confirmation); a cleared call shows **Cleared**. Replay rows show **At the scene** and **Replay** tags.

The page head holds a date and time chip and **Download calls (CSV)** (`Board.to_frame`, saved as `ergent_calls_<date>_<time>.csv`).

**Clocks.** With no simulation running, the board uses `ManualClock`: real time at the chosen Clock speed. Changing the speed continues from the current board time. While a simulation runs, the board uses the replay clock. **Reset** calls `Board.reset_all` and `ManualClock.reset`: no calls, all 12 ambulances available, Resolved empty, and the clock back to wall time at the chosen manual speed.

**Ordered buttons (poka-yoke).** Only the next valid button is shown for a call. A press that ends a late stage opens a dialog that asks for one of the 6 delay reasons, and the time of the press is kept. Clear asks for confirmation. All of this is `Board.check`, `Board.needs_reason` and `Board.apply`.

**History** (title "History"; refreshed about every 5 seconds while visible). It shows the **current shift and the previous one**, following the board clock (the simulated time during a simulation). Its data is the demo file's calls that had reached the scene by the board time, plus the calls logged by hand (`Board.calls_frame(now, manual_only=True)`), cut by `qc.shift_calls`. Top to bottom:

1. The shift label from `qc.shift_window`, for example `Current: day shift 06:00-14:00, Sep 16 · Previous: night shift 22:00-06:00, Sep 15`.
2. A KPI row: **Calls**, **Mean (min)**, **Standard deviation (min)** and **On time** (all priorities; each call's own target), from `qc.summary`.
3. Two cards side by side (the chart about 72% wide, the suggestions about 28%; they stack on a narrow screen):
   - **Response time by zone**: one chart with a **Priority** dropdown ("Priority 1: Life-threatening", "Priority 2: Urgent", "Priority 3: Non-urgent"), drawn by `charts.zone_box_svg` from `qc.zone_subgroup_chart`. **Hover a red diamond** to see why the zone is slow (`qc.zone_delay_reason`). A note under it names the zones that are slower than the city.
   - **Suggested actions** from `qc.dispatcher_tips`: one compact row each with the rule's display name (T1 Dispatch now, T2 Rebalance, T3 Cover, T4 Route, T5 Station alert, T6 Dispatcher load), a zone tag, a short text and the evidence in muted type. The note reads "For the dispatcher's judgment; the tool decides nothing on its own."

### 7.2 The supervisor view

`ui_supervisor.py` draws it. Every number is a `qc` call and every chart a `charts` call. There are **two tabs, Charts and Actions**. There is no Overview tab and no settings card. Every card has one plain title, and every **More info** toggle (`_more`) holds 2 or 3 sentences.

**Control bar** (top of Charts; it sets what both tabs show): **Chart** (Daily chart or Every call), **Zone** (default D), **Priority** (1: Life-threatening, 2: Urgent, 3: Non-urgent), **Dataset** (Ithaca demo, Ithaca baseline, Messy file), **As of**, **Chart period** (14, 28 or 42 days; default 28) and a **Targets** button that opens a dialog (the three response targets, the processing target, the turnout target). There is no jump menu. The **chart period is also the limit window**: control limits, the zone map, suggestions and capability all use it, so they agree.

**Charts tab**, top to bottom:

1. **Control chart** (left, about two thirds): `charts.daily_chart` or `charts.individuals_chart`, one at a time. On the right: **Statistics** (Average, Standard deviation, On time, Zones flagged, for the chart period and all zones; from `qc.summary` and `qc.zone_health`) and **Zone map** (an interactive map of Ithaca with the six zones coloured by health; hover a zone for its reasons, click it to pick that zone in the control bar). A **Data quality** card appears below them only when calls were left out.
2. **Delay by stage** (with the date range, and hover bars from `charts.stage_share_svg`) next to **Zone comparison** (a plain answer from `qc.zone_anova`; the F value, p and the normal probability plot are in More info).
3. **Capability**: one plain verdict per zone from `qc.capability_verdict`. The Ppk, Cpk and expected-on-time table is in More info.

**Actions tab**, top to bottom: a context line (dataset, priority, as-of date); the **Slip-back alerts** card only when a zone is slipping back; **Suggested actions** (from `qc.suggest`, with **Log this action**) next to **Actions taken** (with **Log an action**); then **Before and after** (the daily chart with the action marked) next to **Result**: an action dropdown, a verdict chip, and a table of Mean, Standard deviation, On time and Calls, before and after (`qc.before_after`).

---

## 8. Tests

```bash
.venv/bin/python -m pytest tests -q        # from the repo root
```

[`pytest.ini`](../pytest.ini) puts the repo root on the path, so `from app import qc` works on a fresh clone with no install step.

| File | Covers |
|---|---|
| [`tests/test_qc.py`](../tests/test_qc.py) | Every function in section 4: the known answers from `SPEC.md` section 4, a degenerate case for each, a planted shift that must be flagged, the suggestion rules (each built to trigger only itself), before/after, slip-back, float-noise constants, invalid calls that must not move a window, the constant daily limits (center = mean of the window's daily means, sigma = their standard deviation, with the textbook B4 constant for the S chart), `summary` with `sd`, `PRIORITY_NAME` and `zone_delay_reason`, zone health following the chart period, `capability_verdict`, and the live shift tools (`shift_window`, `shift_calls`, `zone_subgroup_chart`, `dispatcher_tips`, including the 2-call rule for naming a cause in T4) |
| [`tests/test_simulator.py`](../tests/test_simulator.py) | `events_until`, the replay clock, the manual clock, the ordered buttons, delay reasons, the fleet, zone tiles, `reset_all`, `calls_frame` and the export schema |
