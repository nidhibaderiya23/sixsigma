# Response Watch: function reference

This folder holds the Response Watch tool: a Shiny for Python dashboard for a city 911 EMS dispatch center (Team ERG). This page explains **how each function works, what goes in, what comes out, and what happens when the data is bad**. For what the tool is and how to run it, start with the [main README](../README.md). For the formulas and the hand-worked known answers, see [`SPEC.md`](../SPEC.md) section 4.

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
| [`charts.py`](charts.py) | Matplotlib figures for the supervisor screens. Draws what `qc.py` computed. Computes nothing. |
| [`simulator.py`](simulator.py) | The live board's rules: the call model, the fleet, alerts, and the shift replay. Pure Python, unit-tested. |
| [`ui_dispatcher.py`](ui_dispatcher.py) | Dispatcher screens (live board, history) and the building blocks both roles share. |
| [`ui_supervisor.py`](ui_supervisor.py) | Supervisor screens: settings card, Overview, Charts, Actions. |
| [`app.py`](app.py) | The Shiny app: start page, role picker, header, banner. Wires the two roles together. |
| `www/rw.css`, `www/rw.js` | The dark look, and a small script that repaints the running clocks once a second. |
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
- **Baseline.** Control limits come from a baseline period: `baseline_days` days (default 14) starting at `baseline_start` (default: the first day with a valid call). They are applied to every day.

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

Public functions are listed in the order they appear in the file. Functions starting with `_` are helpers ([4.8](#48-private-helpers)).

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
| `RULE_TEXT` | R1 to R5 | Plain-words names for the flag rules, shown to the supervisor |

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
- **Returns:** `{"n", "mean", "median", "p90", "p95", "pct_on_time"}`. `pct_on_time` is 0 to 100. On time means value **at or under** the target.
- **Formula:** `median`, `p90`, `p95` are `percentile` at 0.5, 0.9, 0.95. The mean is shown for comparison only. Known answer: [4, 5, 6, 7, 8, 9, 10, 11, 12, 20] with target 9 gives mean 9.2, median 8.5, p90 12.8, p95 16.4, on time 60%.
- **Degenerate:** no values gives `n = 0` and every other field `None`. One value makes the median, p90 and p95 equal to it.

#### `zone_summary(stages, priority=1, targets=TARGETS) -> DataFrame`

- **Inputs:** a `stages` table; `priority`; `targets`.
- **Returns:** one row per zone A to F, plus a citywide `"All"` row. Columns: `zone, n, mean, median, p90, p95, pct_on_time` (minutes, and %). It uses valid calls of that priority, with the target `targets["response"][priority] / 60`.
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

Average (X̄) and standard-deviation (S) chart limits for subgroups of any size.

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

One row per day for a zone: the X̄-S chart of log response minutes, with flags.

- **Inputs:** `stages`; `zone` (`"A"` to `"F"` or `"All"`); `priority`; `baseline_days` (days); `baseline_start` (a date, or `None` for the first day with a valid call).
- **Returns:** a DataFrame with one row for each day that has valid calls of that priority:

| Column | Meaning |
|---|---|
| `date`, `n` | The day, and the number of calls |
| `mean_log`, `sd_log` | Mean and standard deviation of ln minutes that day (`sd_log` is blank for a one-call day) |
| `x_center`, `x_ucl`, `x_lcl` | X̄ chart center and limits, in ln minutes |
| `x_center_min`, `x_ucl_min`, `x_lcl_min` | The same in minutes (exp of the log values, so a geometric-mean scale) |
| `s_center`, `s_ucl`, `s_lcl` | S chart center and limits |
| `s_flag` | The day's standard deviation is above `s_ucl` |
| `z` | The day's z-score |
| `rules` | List of rule ids that fired that day (from `flag_rules`) |
| `alarm` | Any slow-side (`+`) rule fired |
| `check` | Only fast-side (`-`) rules fired: "check the data" |
| `baseline` | The day is inside the baseline period |

  `df.attrs` holds `xbbar`, `sigma_short` (ln minutes), `message`, and `baseline_note`.
- **Formula:** the baseline is the days from `baseline_start` up to `baseline_days` later. `xbar_s_limits` estimates x̄̄ and sigma_short from the baseline days only. Those limits are applied to every day. `flag_rules` runs on the z-scores, with the daily means as the trend.
- **Degenerate:** if the baseline has no day with 2 or more calls, or its calls are constant, the result is an **empty DataFrame** (the columns are still there) and `attrs["message"]` starts with "baseline:". `baseline_note` warns when baseline days are themselves flagged, or when all the data is baseline.

#### `imr_chart(stages, zone, priority=1, baseline_days=14, baseline_start=None) -> DataFrame`

One row per call, in the order calls were received: the I-MR chart of log response minutes.

- **Inputs:** the same as `daily_xbar_s`.
- **Returns:** a DataFrame with `call_id, dispatched, date, response_min, log_min, mr` (the moving range, in ln minutes), `center, ucl, lcl` (ln minutes), `center_min, ucl_min, lcl_min` (minutes), `beyond` (above the upper limit: an **extreme delay**), and `below` (under the lower limit: check the data). `df.attrs` holds `mr_bar`, `mr_ucl`, `sigma`, `message`.
- **Formula:** `imr_limits` on the baseline calls' ln minutes (calls dated inside the baseline period). Those limits are applied to every call.
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

- **Inputs:** `stages`; `priority`; `targets`; the baseline arguments; `min_n`, the fewest calls a zone needs (default 30); `period_days`, the period to judge (e.g. 28). Pass ALL calls up to the as-of date: the control chart is built with its real baseline, then only the last `period_days` days are checked for flags and used for the indices. (The Charts screen does exactly this.)
- **Returns:** one row per zone: `zone, n, ppk, cpk, stable, shapiro_p, shown, message`. `ppk` and `cpk` are filled only when `shown` is `True`.
- **Formula:** USL = ln(target minutes). Ppk uses all the zone's ln minutes in the table (sigma_total). Cpk uses sigma_short = sqrt(mean of the daily variances) from the zone's daily subgroups. `stable` means the zone's `daily_xbar_s` chart is non-empty and has **no slow-side flag**. `shown = capability is computable and stable and n >= min_n`. With few calls the indices are too uncertain to mean anything.
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

#### `zone_health(stages, priority=1, targets=TARGETS, baseline_days=14, recent_days=7, as_of=None, actions=None, baseline_start=None) -> DataFrame`

The traffic light for each zone.

- **Inputs:** `stages`; `priority`; `targets`; the baseline arguments; `recent_days` (default 7); `as_of` (a date or `None`); `actions`, an optional table of logged actions (columns `date`, `zone`, optional `action_id`).
- **Returns:** one row per zone: `zone, status, p90_recent, rules, top_stage, top_share, reasons`. `status` is `"green"`, `"amber"`, `"red"` or `"unknown"`. `p90_recent` is in minutes. `rules` lists every slow-side rule that fired in the window (`"R1"` to `"R5"`), even when the signal is too weak to count. `top_stage` and `top_share` name the stage with the largest share of minutes over target (blank for green). `reasons` is a list of plain-words sentences.
- **Formula:** the window is the last `recent_days` days up to `as_of`. A **chart signal** is `chart_signal(rules)`: rule R1 fired, or 2 or more different slow-side rules fired. **Red** = a chart signal AND the window's 90th percentile is over the target. **Amber** = exactly one of those. **Green** = neither. One weaker rule alone does not change the status. It stays in `rules` and adds the reason "one weak signal (...): not enough on its own, keep watching" to a green zone. A zone that is slipping back after a logged action (see `slip_back`) is at least amber. Amber means "worth a look"; red means "act".
- **Degenerate:** a zone whose chart has no limits, or that has no calls in the window, is `"unknown"` with the reason "not enough data for limits yet".

#### `suggest(stages, actions=None, priority=1, targets=TARGETS, window_days=14, as_of=None, baseline_days=14, baseline_start=None) -> list`

Fixed if-then suggestions, with evidence. The rules are in [`docs/plan.md`](../docs/plan.md).

- **Inputs:** `stages`; `actions` (logged actions, columns `date`, `zone`, `stage`); `priority`; `targets`; `window_days` (default 14); `as_of`; the baseline arguments.
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

### 4.8 Private helpers

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

---

## 5. `charts.py`: the figures

Drawing only. Each function takes a result from `qc.py` and returns a matplotlib `Figure` in the app's dark style. The backend is `Agg`, so no window opens. **Control limits (from the process) are dashed grey. The target (a specification limit) is a solid amber line.** They are never confused.

| Function | Takes | Shows |
|---|---|---|
| `daily_chart(chart, zone, action_dates=())` | `qc.daily_xbar_s` output | **Top:** the daily average in minutes (geometric mean), with the center line and dashed control limits. Red dots are flagged days. Hollow amber rings are "check the data" days. The baseline period is lightly shaded. Green vertical lines mark logged actions. **Bottom:** the daily standard deviation of ln minutes with the S chart's center and upper limit. Red dots are days above it. |
| `imr_chart(imr, zone, target_min)` | `qc.imr_chart` output and the target | **Top:** every call in order on a log axis (in minutes) with the center line, dashed control limits and the solid amber target. Red dots are extreme delays. **Bottom:** the moving range with its center and upper limit. |
| `stage_breakdown(bd)` | `qc.stage_breakdown` output | Stacked horizontal bars: the median minutes in processing, turnout and travel, per zone |
| `stage_share(bd)` | `qc.stage_breakdown` output | Stacked horizontal bars: each stage's share of the zone's minutes over target (0 to 100%) |
| `normal_plot(norm, zone)` | `qc.normality` output | The normal probability plot of ln minutes, with a fit line and the Shapiro-Wilk p in the title |
| `before_after_chart(chart_full, zone, action_date)` | `qc.daily_xbar_s` output | The `daily_chart` with the action marked |
| `empty(message)` | text | A blank figure with a short message. Every function above falls back to it when there is no data or no limits. |

---

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
| `Board` | One browser session's board. It has two clocks, the wall clock and the replay clock, so their calls never mix. `add_call` stamps the received time. `check` and `apply` accept only the next step (they raise `BoardError`, or `ReasonRequired` when a reason is missing). `fleet`, `available_units`, `set_out_of_service` and `back_in_service` manage the 12 ambulances. `sync_replay` loads a replay state. `counts`, `zone_tiles` and `alerts` feed the screen. `to_frame` exports every call in the `CALL_COLUMNS` schema (the "Download calls" file). |
| `load_units(path=None)`, `default_fleet()` | The fleet list from `data/units.csv`, or the default two ambulances per zone |
| `fmt_clock`, `fmt_time`, `epoch` | Formatting helpers (`75` seconds is `1:15`) |

---

## 7. The screens

| File | Role |
|---|---|
| [`app.py`](app.py) | Builds the start page (two role buttons), the header (with the clock-mode and role chips and a **Switch role** link) and the "synthetic data" banner. A hidden navset switches between the start page, the dispatcher view and the supervisor view. The live board's state lives inside `server()`, so each browser session has its own. |
| [`ui_dispatcher.py`](ui_dispatcher.py) | `dispatcher_ui` and `dispatcher_server`: the live board (call tables, unit picker, ordered buttons, reason dialog, clear confirmation, fleet, alerts, live map, simulation controls, CSV download) and `history_ui` and `history_server` (per-zone summary table and the 20 latest resolved calls). It calls `qc.zone_summary` and `qc.last_days`. It also holds the small building blocks both roles share (`icon`, `chip`, `tag`, `card_head`, `eyebrow`) and `get_calls`, which reads and caches a calls CSV. A one-second tick moves the replay clock and repaints the clocks. |
| [`ui_supervisor.py`](ui_supervisor.py) | The settings card (dataset: demo, baseline or messy; priority, as-of date, chart period, targets, baseline) and three tab modules listed in `TABS`: **Overview** (KPI tiles, zone health, history map, and a data-quality card that lists every excluded call, which is how the messy file's 7 planted defects show up), **Charts** (the X̄-S and I-MR figures, stage breakdown, capability table, ANOVA and normal plot) and **Actions** (slip-back alerts, suggestions, action log, before/after). `supervisor_server` builds the shared settings (targets, `stages`, `upto`, `health`, actions) once, and each tab reads them. Every number is a `qc` call. Every chart is a `charts` call. |

---

## 8. Tests

```bash
.venv/bin/python -m pytest tests -q        # from the repo root
```

[`pytest.ini`](../pytest.ini) puts the repo root on the path, so `from app import qc` works on a fresh clone with no install step.

| File | Covers |
|---|---|
| [`tests/test_qc.py`](../tests/test_qc.py) | Every function in section 4: the known answers from `SPEC.md` section 4, a degenerate case for each, a planted shift that must be flagged, the suggestion rules (each built to trigger only itself), before/after, slip-back, float-noise constants, and invalid calls that must not move a window |
| [`tests/test_simulator.py`](../tests/test_simulator.py) | `events_until`, the replay clock, the ordered buttons, delay reasons, the fleet, alerts, zone tiles and the export schema |
