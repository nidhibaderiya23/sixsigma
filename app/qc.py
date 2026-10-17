"""ERGent statistics: every number the app shows comes from this file.

Plain functions with plain inputs (pandas DataFrames, lists of numbers) and plain
outputs (numbers, dicts, DataFrames). No Shiny, no plotting. Formulas and the
hand-worked known answers are in SPEC.md section 4; tests are in tests/.

Times are in seconds inside the data and in minutes on screen. Control charts and
capability work on the natural log of response time, because response times are
right-skewed (a long slow tail) and their logs are close to normal.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

# ---- constants ---------------------------------------------------------------

ZONES = ("A", "B", "C", "D", "E", "F")

#: The city ERGent models, and the plain names of its six zones (illustrative areas of
#: Ithaca, NY, not official EMS districts). The grid order A B C / D E F matches NEIGHBORS.
CITY = "Ithaca, NY"
ZONE_NAMES = {
    "A": "West Hill",
    "B": "Northside & Fall Creek",
    "C": "Cornell & Collegetown",
    "D": "West End & Southwest",
    "E": "Downtown & South Hill",
    "F": "East Hill & Belle Sherman",
}
PRIORITIES = (1, 2, 3)
STAGES = ("processing", "turnout", "travel")
TIMESTAMPS = ("call_received", "dispatched", "en_route", "on_scene", "cleared")

#: Default targets in seconds, each to be met by at least 90% of calls.
#: processing, turnout and priority-1 travel come from NFPA 1710 (64 s, 60 s,
#: 480 s for an advanced life support unit); response = dispatched -> on scene.
#: Priority 2 and 3 response targets are our own stated assumptions.
TARGETS = {
    "processing": 64,
    "turnout": 60,
    "response": {1: 540, 2: 900, 3: 1200},
}

#: Plain names of the call priorities (the call-taker's medical code).
PRIORITY_NAME = {1: "Life-threatening", 2: "Urgent", 3: "Non-urgent"}

#: Delay reason codes the crew taps when a stage runs late (key -> label).
REASON_CODES = {
    "traffic_or_road_closure": "Traffic or road closure",
    "ambulance_breakdown": "Ambulance breakdown",
    "unit_from_another_zone": "Unit from another zone",
    "unclear_address": "Unclear address",
    "weather": "Weather",
    "crew_not_ready": "Crew not ready",
}

#: Shifts by hour of the call: day 06-14, evening 14-22, night 22-06.
SHIFTS = (("day", 6, 14), ("evening", 14, 22), ("night", 22, 6))

#: Columns every calls CSV has (see data/README.md for the codebook).
CALL_COLUMNS = (
    "call_id", "zone", "priority",
    "call_received", "dispatched", "en_route", "on_scene", "cleared",
    "unit_id", "unit_home_zone", "distance_km", "dispatcher_id", "weather",
    "delay_reason",
)

D2 = 1.128   # d2 for moving ranges of span 2
D4 = 3.267   # D4 for moving ranges of span 2


def stage_targets(priority: int, targets: dict = TARGETS) -> dict:
    """Seconds allowed for each stage of a call with this priority.

    Travel's target is what is left of the response target after turnout:
    priority 1 gets 540 - 60 = 480 s, the NFPA 1710 travel benchmark.
    """
    response = targets["response"][int(priority)]
    return {
        "processing": targets["processing"],
        "turnout": targets["turnout"],
        "travel": response - targets["turnout"],
        "response": response,
    }


def find_data_dir() -> Path:
    """The folder holding the CSVs: app/data when deployed, else repo data/."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "data", here.parent / "data"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("no data folder next to app/ or at the repo root")


def shift_of(hour: int) -> str:
    """'day' (06-14), 'evening' (14-22) or 'night' (22-06)."""
    if 6 <= hour < 14:
        return "day"
    if 14 <= hour < 22:
        return "evening"
    return "night"


# ---- loading and stage times ---------------------------------------------------

def load_calls(path) -> pd.DataFrame:
    """Read a calls CSV and parse its timestamp columns (blank -> NaT)."""
    df = pd.read_csv(path, dtype={"call_id": str, "zone": str, "unit_id": str,
                                  "unit_home_zone": str, "dispatcher_id": str,
                                  "weather": str, "delay_reason": str})
    for col in TIMESTAMPS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["delay_reason"] = df["delay_reason"].fillna("")
    return df


def stage_times(calls: pd.DataFrame, targets: dict = TARGETS) -> pd.DataFrame:
    """Add stage durations, lateness and data-quality columns to each call.

    New columns (seconds unless noted):
      processing_s = dispatched - call_received
      turnout_s    = en_route - dispatched
      travel_s     = on_scene - en_route
      response_s   = on_scene - dispatched   (the prompt's metric)
      response_min = response_s / 60
      late         = response_s > the priority's response target
      <stage>_late = that stage over its target (see stage_targets)
      date (midnight Timestamp), hour, shift (from call_received)
      issue        = "" for a clean call, else what is wrong with it
      valid        = issue == ""   (only valid calls enter any statistic)
    """
    df = calls.copy()
    issues = pd.Series("", index=df.index, dtype=object)

    dup = df["call_id"].duplicated(keep="first")
    issues[dup] = "duplicate call_id"

    for col in ("call_received", "dispatched", "en_route", "on_scene"):
        missing = df[col].isna() & (issues == "")
        issues[missing] = f"missing {col}"

    order = [("call_received", "dispatched"), ("dispatched", "en_route"),
             ("en_route", "on_scene")]
    for earlier, later in order:
        bad = (df[later] < df[earlier]) & (issues == "")
        issues[bad] = f"{later} before {earlier}"

    zero = (df["on_scene"] <= df["dispatched"]) & (issues == "")
    issues[zero] = "zero response time"

    bad_zone = ~df["zone"].isin(ZONES) & (issues == "")
    issues[bad_zone] = "unknown zone"
    bad_pri = ~df["priority"].isin(PRIORITIES) & (issues == "")
    issues[bad_pri] = "unknown priority"

    df["processing_s"] = (df["dispatched"] - df["call_received"]).dt.total_seconds()
    df["turnout_s"] = (df["en_route"] - df["dispatched"]).dt.total_seconds()
    df["travel_s"] = (df["on_scene"] - df["en_route"]).dt.total_seconds()
    df["response_s"] = (df["on_scene"] - df["dispatched"]).dt.total_seconds()
    df["response_min"] = df["response_s"] / 60.0

    df["issue"] = issues
    df["valid"] = issues == ""

    resp_target = df["priority"].map(lambda p: targets["response"].get(p, np.nan))
    df["response_target_s"] = resp_target
    df["late"] = df["valid"] & (df["response_s"] > resp_target)
    df["processing_late"] = df["valid"] & (df["processing_s"] > targets["processing"])
    df["turnout_late"] = df["valid"] & (df["turnout_s"] > targets["turnout"])
    df["travel_late"] = df["valid"] & (df["travel_s"] > resp_target - targets["turnout"])

    df["date"] = df["call_received"].dt.normalize()   # midnight Timestamp of the call's day
    df["hour"] = df["call_received"].dt.hour
    df["shift"] = df["hour"].map(lambda h: shift_of(int(h)) if pd.notna(h) else "")
    return df


def data_issues(stages: pd.DataFrame) -> pd.DataFrame:
    """The calls left out of the statistics, with the reason for each."""
    return stages.loc[~stages["valid"], ["call_id", "zone", "priority", "issue"]]


# ---- summary numbers -------------------------------------------------------------

def percentile(values, p: float) -> float:
    """Percentile by linear interpolation (R type 7, Excel PERCENTILE.INC).

    Position h = (n - 1) * p on the sorted values (0-based); the result is
    x[floor(h)] + (h - floor(h)) * (x[floor(h) + 1] - x[floor(h)]).
    """
    xs = np.sort(np.asarray(values, dtype=float))
    if xs.size == 0:
        raise ValueError("need at least 1 value")
    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1")
    h = (xs.size - 1) * p
    lo = math.floor(h)
    hi = min(lo + 1, xs.size - 1)
    return float(xs[lo] + (h - lo) * (xs[hi] - xs[lo]))


def summary(values_min, target_min: float) -> dict:
    """Mean, standard deviation, median, 90th and 95th percentile and % on time, in minutes.

    sd = sample standard deviation (n - 1), None with fewer than 2 values.
    On time = value <= target. With no values, every number is None.
    """
    xs = np.asarray(values_min, dtype=float)
    xs = xs[~np.isnan(xs)]
    if xs.size == 0:
        return {"n": 0, "mean": None, "sd": None, "median": None, "p90": None,
                "p95": None, "pct_on_time": None}
    return {
        "n": int(xs.size),
        "mean": float(xs.mean()),
        "sd": float(xs.std(ddof=1)) if xs.size >= 2 else None,
        "median": percentile(xs, 0.5),
        "p90": percentile(xs, 0.9),
        "p95": percentile(xs, 0.95),
        "pct_on_time": float((xs <= target_min).mean() * 100.0),
    }


def zone_summary(stages: pd.DataFrame, priority: int = 1,
                 targets: dict = TARGETS) -> pd.DataFrame:
    """summary() of response minutes for each zone plus a citywide 'All' row."""
    target_min = targets["response"][priority] / 60.0
    ok = stages[stages["valid"] & (stages["priority"] == priority)]
    rows = []
    for zone in ZONES + ("All",):
        sub = ok if zone == "All" else ok[ok["zone"] == zone]
        rows.append({"zone": zone, **summary(sub["response_min"], target_min)})
    return pd.DataFrame(rows)


# ---- period helpers -------------------------------------------------------------------

def until(stages: pd.DataFrame, as_of=None) -> pd.DataFrame:
    """Only the calls received on or before the as_of date (all calls if None)."""
    if as_of is None:
        return stages
    return stages[stages["date"] <= pd.Timestamp(as_of).normalize()]


def last_days(stages: pd.DataFrame, days: int, as_of=None) -> pd.DataFrame:
    """The calls in the last `days` days up to as_of (default: the newest call)."""
    s = until(stages, as_of)
    dates = _valid_dates(s)
    if dates.notna().sum() == 0:
        return s
    end = dates.max()
    return s[(s["date"] > end - pd.Timedelta(days=days)) & (s["date"] <= end)]


def _calls(stages: pd.DataFrame, zone: str, priority: int) -> pd.DataFrame:
    """Valid calls of one priority, for one zone or for 'All' zones."""
    ok = stages[stages["valid"] & (stages["priority"] == priority)]
    return ok if zone == "All" else ok[ok["zone"] == zone]


def _clean(values) -> np.ndarray:
    xs = np.asarray(values, dtype=float)
    return xs[~np.isnan(xs)]


def _no_spread(values) -> bool:
    """True when the values are all the same, allowing for floating-point noise
    (e.g. 60 copies of ln(340/60) can differ in the last bit)."""
    xs = _clean(values)
    if xs.size == 0:
        return True
    return float(np.ptp(xs)) <= 1e-9 * max(1.0, float(np.abs(xs).max()))


def _valid_dates(stages: pd.DataFrame) -> pd.Series:
    """Dates of valid calls only, so a flagged call can never move a window."""
    return stages.loc[stages["valid"], "date"]


# ---- control charts ------------------------------------------------------------------

#: Plain-words names for the slow-side flag rules, as shown to the supervisor.
RULE_TEXT = {
    "R1": "a day far beyond its normal range",
    "R2": "2 of 3 days well above normal",
    "R3": "4 of 5 days above normal",
    "R4": "8 days in a row above normal",
    "R5": "6 days in a row getting slower",
}


def c4(n: int) -> float:
    """c4(n) = sqrt(2/(n-1)) * Gamma(n/2) / Gamma((n-1)/2): the mean sample
    standard deviation of n normal values whose true sigma is 1."""
    if n < 2:
        raise ValueError("c4 needs n >= 2")
    return math.sqrt(2.0 / (n - 1)) * math.exp(math.lgamma(n / 2.0) - math.lgamma((n - 1) / 2.0))


def imr_limits(values) -> dict:
    """Individuals and moving-range limits (course method, sigma = MR-bar / d2).

    Returns ok, center, sigma, ucl, lcl, mr_bar, mr_ucl (the MR lower limit is
    always 0) and message. Needs at least 2 values; constant data has no
    variation, so the limits are None and 'message' says why.
    """
    xs = _clean(values)
    out = {"ok": False, "n": int(xs.size), "center": None, "sigma": None,
           "ucl": None, "lcl": None, "mr_bar": None, "mr_ucl": None,
           "mr_lcl": 0.0, "message": ""}
    if xs.size < 2:
        out["message"] = "need at least 2 values for a moving range"
        return out
    mr_bar = float(np.abs(np.diff(xs)).mean())
    if _no_spread(xs):
        out["message"] = "no variation: every value is the same, so there are no limits"
        return out
    center = float(xs.mean())
    sigma = mr_bar / D2
    out.update(ok=True, center=center, sigma=sigma, ucl=center + 3 * sigma,
               lcl=center - 3 * sigma, mr_bar=mr_bar, mr_ucl=D4 * mr_bar)
    return out


def xbar_s_limits(subgroups, xbbar: float | None = None,
                  sigma_short: float | None = None) -> dict:
    """Average and standard-deviation chart limits for subgroups of any size.

    x-double-bar = mean of the subgroup means; sigma_short = sqrt(mean of the
    subgroup variances), from subgroups with n >= 2 (the course formula).
    Pass xbbar and sigma_short to apply limits estimated elsewhere (a baseline).
    Per subgroup i with n_i values:
      x-bar limits  x-double-bar +/- 3 sigma_short / sqrt(n_i)
      z             (mean_i - x-double-bar) / (sigma_short / sqrt(n_i))
      S chart       center c4(n_i) sigma_short,
                    limits (c4 +/- 3 sqrt(1 - c4^2)) sigma_short, lower >= 0
    """
    groups = [_clean(g) for g in subgroups]
    out = {"ok": False, "xbbar": None, "sigma_short": None, "message": "",
           "subgroups": []}
    if xbbar is None or sigma_short is None:
        means = [g.mean() for g in groups if g.size >= 1]
        variances = [g.var(ddof=1) for g in groups if g.size >= 2]
        if not means or not variances:
            out["message"] = "need at least one subgroup with 2 or more values"
            return out
        if xbbar is None:
            xbbar = float(np.mean(means))
        if sigma_short is None:
            flat = all(_no_spread(g) for g in groups if g.size >= 2)
            sigma_short = 0.0 if flat else float(math.sqrt(np.mean(variances)))
    if sigma_short <= 1e-12 * max(1.0, abs(xbbar)):
        out.update(xbbar=float(xbbar), sigma_short=0.0,
                   message="no variation: every subgroup is constant, so there are no limits")
        return out
    rows = []
    for g in groups:
        n = int(g.size)
        row = {"n": n, "mean": float(g.mean()) if n else None,
               "sd": float(g.std(ddof=1)) if n >= 2 else None,
               "x_ucl": None, "x_lcl": None, "z": None,
               "s_center": None, "s_ucl": None, "s_lcl": None}
        if n >= 1:
            se = sigma_short / math.sqrt(n)
            row.update(x_ucl=xbbar + 3 * se, x_lcl=xbbar - 3 * se,
                       z=(row["mean"] - xbbar) / se)
        if n >= 2:
            k = c4(n)
            w = 3 * math.sqrt(1 - k * k)
            row.update(s_center=k * sigma_short, s_ucl=(k + w) * sigma_short,
                       s_lcl=max(0.0, (k - w) * sigma_short))
        rows.append(row)
    out.update(ok=True, xbbar=float(xbbar), sigma_short=float(sigma_short),
               subgroups=rows)
    return out


def flag_rules(z, trend=None) -> list:
    """Run rules on standardized points z (center 0, one sigma = 1).

    Returns, for each point, a sorted list of the rule ids that fire AT that point:
      R1  the point is beyond 3 sigma
      R2  the point is beyond 2 sigma and so is 1 more of the last 3
      R3  the point is beyond 1 sigma and so are 3 more of the last 5
      R4  this point and the 7 before it are all on the same side of center
      R5  this point and the 5 before it are steadily rising (or falling)
    Ids end in "+" on the slow side (an alarm) and "-" on the fast side
    (only 'check the data'), e.g. "R2+". R1-R4 are the Western Electric rules.
    R5 looks at `trend` (the plotted values, e.g. daily averages) when given,
    so "6 rising" always matches what the chart shows; otherwise at z.
    """
    zs = [float(v) for v in z]
    ts = zs if trend is None else [float(v) for v in trend]
    fired = []
    for i, v in enumerate(zs):
        hits = set()
        if abs(v) > 3:
            hits.add("R1+" if v > 0 else "R1-")
        for size, limit, need, rid in ((3, 2, 2, "R2"), (5, 1, 4, "R3")):
            window = zs[max(0, i - size + 1): i + 1]
            if v > limit and sum(w > limit for w in window) >= need:
                hits.add(rid + "+")
            if v < -limit and sum(w < -limit for w in window) >= need:
                hits.add(rid + "-")
        if i >= 7:
            window = zs[i - 7: i + 1]
            if all(w > 0 for w in window):
                hits.add("R4+")
            elif all(w < 0 for w in window):
                hits.add("R4-")
        if i >= 5:
            steps = np.diff(ts[i - 5: i + 1])
            if np.all(steps > 0):
                hits.add("R5+")
            elif np.all(steps < 0):
                hits.add("R5-")
        fired.append(sorted(hits))
    return fired


def _baseline_window(stages: pd.DataFrame, baseline_days: int, baseline_start=None):
    start = (pd.Timestamp(baseline_start).normalize() if baseline_start is not None
             else _valid_dates(stages).min())
    return start, start + pd.Timedelta(days=baseline_days)


def daily_xbar_s(stages: pd.DataFrame, zone: str, priority: int = 1,
                 baseline_days: int = 14, baseline_start=None) -> pd.DataFrame:
    """One row per day for a zone: the X-bar and S chart of log response minutes,
    with CONSTANT limits (the team's decisions, Oct 16-17).

    X-bar chart: each day's point is the mean of that day's log minutes. The
    center line = the mean of the daily means in the limit window; sigma_xbar =
    the standard deviation of those daily means; limits = center +/- 3
    sigma_xbar, the same for every day. The limit window is
    [baseline_start, + baseline_days): by default the first 14 days, and in the
    app the chart period the user selects (the team chose this, knowing that a
    long problem inside the period widens the limits and can hide itself).
    S chart: center s-bar = mean of the baseline daily standard deviations
    (days with 2+ calls); limits B4 s-bar and B3 s-bar (lower >= 0), with
    B3/B4 = 1 -/+ 3 sqrt(1 - c4^2) / c4 for n-bar = average calls per baseline day.
    Columns: date, n, mean_log, sd_log, x_center/x_ucl/x_lcl (log minutes) and
    the same back in minutes (_min, a geometric mean), s_center/s_ucl/s_lcl,
    s_flag, z, rules (list of rule ids), alarm (any slow-side rule), check (a
    fast-side rule only), baseline (the day is in the baseline).
    attrs: xbbar (the center), sigma_xbar (SD of the daily means), mr_bar (None), sigma_short (the window's
    within-day sigma, for reference; zone_capability computes its own), s_bar, n_bar,
    message, baseline_note.
    """
    calls = _calls(stages, zone, priority)
    start, end = _baseline_window(stages, baseline_days, baseline_start)
    days = sorted(calls["date"].dropna().unique())
    groups = [np.log(calls.loc[calls["date"] == d, "response_min"].to_numpy()) for d in days]
    means = [float(g.mean()) for g in groups]
    sds = [float(g.std(ddof=1)) if g.size >= 2 else None for g in groups]
    in_base = [bool(start <= d < end) for d in days]
    cols = ["date", "n", "mean_log", "sd_log", "x_center", "x_ucl", "x_lcl",
            "x_center_min", "x_ucl_min", "x_lcl_min", "s_center", "s_ucl", "s_lcl",
            "s_flag", "z", "rules", "alarm", "check", "baseline"]
    base_means = np.asarray([m for m, b in zip(means, in_base) if b], dtype=float)
    lim = {"ok": False, "message": "need at least 2 days with calls"}
    if base_means.size >= 2:
        if _no_spread(base_means):
            lim = {"ok": False, "message": "no variation: every value is the same, so there are no limits"}
        else:
            lim = {"ok": True, "center": float(base_means.mean()),
                   "sigma": float(base_means.std(ddof=1)), "mr_bar": None}
    if not lim["ok"]:
        out = pd.DataFrame(columns=cols)
        out.attrs.update(xbbar=None, sigma_xbar=None, mr_bar=None, sigma_short=None,
                         s_bar=None, n_bar=None, message="baseline: " + lim["message"],
                         baseline_note="")
        return out
    center, sig = lim["center"], lim["sigma"]
    ucl, lcl = center + 3 * sig, center - 3 * sig
    z = [(m - center) / sig for m in means]
    rules = flag_rules(z, trend=means)

    base_sds = [s for s, b in zip(sds, in_base) if b and s is not None]
    base_ns = [g.size for g, b in zip(groups, in_base) if b]
    s_bar = float(np.mean(base_sds)) if base_sds else None
    n_bar = max(2, int(round(float(np.mean(base_ns))))) if base_ns else None
    s_center = s_ucl = s_lcl = None
    if s_bar is not None:
        k = c4(n_bar)
        w = 3 * math.sqrt(1 - k * k) / k
        s_center, s_ucl, s_lcl = s_bar, (1 + w) * s_bar, max(0.0, (1 - w) * s_bar)
    base_var = [g.var(ddof=1) for g, b in zip(groups, in_base) if b and g.size >= 2]
    sigma_short = float(math.sqrt(np.mean(base_var))) if base_var else None

    rows = []
    for d, g, m, sd, zz, fired, b in zip(days, groups, means, sds, z, rules, in_base):
        rows.append({
            "date": d, "n": int(g.size), "mean_log": m, "sd_log": sd,
            "x_center": center, "x_ucl": ucl, "x_lcl": lcl,
            "x_center_min": math.exp(center), "x_ucl_min": math.exp(ucl),
            "x_lcl_min": math.exp(lcl),
            "s_center": s_center, "s_ucl": s_ucl, "s_lcl": s_lcl,
            "s_flag": bool(sd is not None and s_ucl is not None and sd > s_ucl),
            "z": zz, "rules": fired,
            "alarm": any(f.endswith("+") for f in fired),
            "check": bool(fired) and not any(f.endswith("+") for f in fired),
            "baseline": b,
        })
    out = pd.DataFrame(rows, columns=cols)
    flagged_base = int((out["baseline"] & out["alarm"]).sum())
    note = (f"{flagged_base} baseline day(s) are themselves flagged: consider moving the baseline"
            if flagged_base else "")
    if out["baseline"].all():
        note = "all the data is baseline: limits come from the same days being judged"
    out.attrs.update(xbbar=center, sigma_xbar=sig, mr_bar=lim["mr_bar"],
                     sigma_short=sigma_short, s_bar=s_bar, n_bar=n_bar, message="",
                     baseline_note=note)
    return out


def imr_chart(stages: pd.DataFrame, zone: str, priority: int = 1,
              baseline_days: int = 14, baseline_start=None) -> pd.DataFrame:
    """One row per call in call order (call_received): the I-MR chart of log response minutes.

    Limits come from the baseline calls. Columns: call_id, dispatched, date,
    response_min, log_min, mr, center/ucl/lcl (log), center_min/ucl_min/lcl_min
    (minutes), beyond (an extreme delay: above the upper limit), below (below
    the lower limit: check the data). attrs: mr_bar, mr_ucl, sigma, message.
    """
    calls = _calls(stages, zone, priority).sort_values("call_received")
    start, end = _baseline_window(stages, baseline_days, baseline_start)
    log_min = np.log(calls["response_min"].to_numpy())
    in_base = ((calls["date"] >= start) & (calls["date"] < end)).to_numpy()
    lim = imr_limits(log_min[in_base])
    out = pd.DataFrame({
        "call_id": calls["call_id"].to_numpy(),
        "dispatched": calls["dispatched"].to_numpy(),
        "date": calls["date"].to_numpy(),
        "response_min": calls["response_min"].to_numpy(),
        "log_min": log_min,
    })
    out["mr"] = out["log_min"].diff().abs()
    if lim["ok"]:
        out["center"], out["ucl"], out["lcl"] = lim["center"], lim["ucl"], lim["lcl"]
        out["center_min"] = math.exp(lim["center"])
        out["ucl_min"], out["lcl_min"] = math.exp(lim["ucl"]), math.exp(lim["lcl"])
        out["beyond"] = out["log_min"] > lim["ucl"]
        out["below"] = out["log_min"] < lim["lcl"]
    else:
        for col in ("center", "ucl", "lcl", "center_min", "ucl_min", "lcl_min"):
            out[col] = np.nan
        out["beyond"] = False
        out["below"] = False
    out.attrs.update(mr_bar=lim["mr_bar"], mr_ucl=lim["mr_ucl"], sigma=lim["sigma"],
                     message="" if lim["ok"] else "baseline: " + lim["message"])
    return out


# ---- capability and tests --------------------------------------------------------------

def capability(values, usl: float, sigma_short: float | None = None) -> dict:
    """Upper-side Ppk (and Cpk when sigma_short is given) on the values as given.

    Ppk = (USL - mean) / (3 sd), with sd the sample standard deviation (sigma_total).
    Cpk = (USL - mean) / (3 sigma_short). The app passes log minutes and
    ln(target minutes), so the formula runs on the log scale.
    Constant data has no spread, so both are None with a message.
    """
    xs = _clean(values)
    out = {"ok": False, "n": int(xs.size), "mean": None, "sd": None,
           "ppk": None, "cpk": None, "message": ""}
    if xs.size < 2:
        out["message"] = "need at least 2 values"
        return out
    sd = float(xs.std(ddof=1))
    mean = float(xs.mean())
    if _no_spread(xs):
        out.update(mean=mean, sd=0.0,
                   message="no variation: capability is undefined for constant data")
        return out
    out.update(ok=True, mean=mean, sd=sd, ppk=(usl - mean) / (3 * sd))
    if sigma_short:
        out["cpk"] = (usl - mean) / (3 * sigma_short)
    return out


def ppk_to_pct(ppk: float | None) -> float | None:
    """% of calls expected within an upper spec for a normal process with this
    upper-side index: Phi(3 * Ppk) * 100. Ppk 1.0 -> 99.87%, 0.43 -> about 90%."""
    if ppk is None or not np.isfinite(ppk):
        return None
    from statistics import NormalDist
    return NormalDist().cdf(3 * ppk) * 100.0


def capability_verdict(row, target_min: float) -> dict:
    """A short plain-language reading of one zone_capability() row, for non-experts.

    Uses the expected share of calls on time, Phi(3 * Ppk), against the 90%
    standard: >= 99% "Very reliable", >= 95% "Reliable", >= 90% "Just meets the
    standard", below 90% "Below the standard". A zone that is not stable, or has
    too few calls, gets "Can't judge yet" / "Not enough calls" instead of a score.
    Returns {"label", "tone" (green/amber/red/grey), "text"}.
    """
    get = row.get if isinstance(row, dict) else (lambda k, d=None: getattr(row, k, d))
    if not get("shown"):
        msg = get("message") or ""
        if msg.startswith("too few calls"):
            return {"label": "Not enough calls", "tone": "grey",
                    "text": f"Only {get('n')} calls; 30 are needed."}
        if msg.startswith("not stable"):
            return {"label": "Can't judge yet", "tone": "amber",
                    "text": "Times changed in this period, so no score yet."}
        return {"label": "Can't judge", "tone": "grey", "text": msg or "No data."}
    pct = round(ppk_to_pct(get("ppk")))            # judge on the same rounded number we show
    per100 = f"About {pct:.0f} in 100" if pct < 100 else "Almost every one of 100"
    if pct >= 99:
        return {"label": "Very reliable", "tone": "green",
                "text": f"{per100} calls within {target_min:.0f} min."}
    if pct >= 95:
        return {"label": "Reliable", "tone": "green",
                "text": f"{per100} calls within {target_min:.0f} min."}
    if pct >= 90:
        return {"label": "Just meets the standard", "tone": "amber",
                "text": f"{per100} calls within {target_min:.0f} min: little margin."}
    return {"label": "Below the standard", "tone": "red",
            "text": f"{per100.replace('About', 'Only about')} calls within {target_min:.0f} min."}


def normality(values) -> dict:
    """Shapiro-Wilk test and normal probability plot points for the values."""
    from scipy import stats
    xs = _clean(values)
    if xs.size < 3 or _no_spread(xs):
        return {"ok": False, "w": None, "p": None, "theoretical": [], "ordered": [],
                "message": "need at least 3 values that are not all the same"}
    w, p = stats.shapiro(xs)
    (theoretical, ordered), _ = stats.probplot(xs, dist="norm")
    return {"ok": True, "w": float(w), "p": float(p), "theoretical": list(theoretical),
            "ordered": list(ordered), "message": ""}


def anova_zones(groups: dict) -> dict:
    """One-way ANOVA across groups {name: values}.

    F = (SSB / (k - 1)) / (SSW / (N - k)). Groups with fewer than 2 values are
    left out (named in 'dropped'); fewer than 2 groups left, or no variation,
    means no test.
    """
    from scipy import stats
    use = {name: _clean(v) for name, v in groups.items()}
    dropped = [name for name, v in use.items() if v.size < 2]
    use = {name: v for name, v in use.items() if v.size >= 2}
    out = {"ok": False, "F": None, "p": None, "df_between": None, "df_within": None,
           "ssb": None, "ssw": None, "means": {k: float(v.mean()) for k, v in use.items()},
           "dropped": dropped, "message": ""}
    if len(use) < 2:
        out["message"] = "need at least 2 groups with 2 or more values"
        return out
    allv = np.concatenate(list(use.values()))
    grand = allv.mean()
    ssb = float(sum(v.size * (v.mean() - grand) ** 2 for v in use.values()))
    ssw = float(sum(((v - v.mean()) ** 2).sum() for v in use.values()))
    k, n = len(use), allv.size
    if all(_no_spread(v) for v in use.values()):
        out.update(ssb=ssb, ssw=0.0, message="no variation inside the groups: F is undefined")
        return out
    f = (ssb / (k - 1)) / (ssw / (n - k))
    out.update(ok=True, F=float(f), p=float(stats.f.sf(f, k - 1, n - k)),
               df_between=k - 1, df_within=n - k, ssb=ssb, ssw=ssw)
    return out


def welch_before_after(before, after) -> dict:
    """Welch's t-test, one-sided: is the 'after' mean lower than 'before'?

    t = (mean_b - mean_a) / sqrt(s_b^2/n_b + s_a^2/n_a); Welch-Satterthwaite df;
    p = P(T > t). Needs 2+ values on each side and some variation.
    """
    from scipy import stats
    b, a = _clean(before), _clean(after)
    out = {"ok": False, "t": None, "df": None, "p_one_sided": None,
           "mean_before": float(b.mean()) if b.size else None,
           "mean_after": float(a.mean()) if a.size else None,
           "n_before": int(b.size), "n_after": int(a.size), "message": ""}
    if b.size < 2 or a.size < 2:
        out["message"] = "need at least 2 values before and 2 after"
        return out
    vb, va = b.var(ddof=1) / b.size, a.var(ddof=1) / a.size
    if _no_spread(b) and _no_spread(a):
        out["message"] = "no variation: the test is undefined"
        return out
    t = (b.mean() - a.mean()) / math.sqrt(vb + va)
    df = (vb + va) ** 2 / (vb ** 2 / (b.size - 1) + va ** 2 / (a.size - 1))
    out.update(ok=True, t=float(t), df=float(df), p_one_sided=float(stats.t.sf(t, df)))
    return out


def zone_anova(stages: pd.DataFrame, priority: int = 1) -> dict:
    """anova_zones() on log response minutes of each zone's valid calls."""
    return anova_zones({z: np.log(_calls(stages, z, priority)["response_min"])
                        for z in ZONES})


def zone_capability(stages: pd.DataFrame, priority: int = 1, targets: dict = TARGETS,
                    baseline_days: int = 14, baseline_start=None,
                    min_n: int = 30, period_days: int | None = None) -> pd.DataFrame:
    """Per zone, on log minutes vs. ln(target): Ppk, Cpk (sigma_short from the
    daily subgroups), Shapiro-Wilk p, and whether the zone is stable (no
    slow-side flag in the period). Capability is only shown when the zone is
    stable and has at least `min_n` calls (fewer gives a uselessly wide interval).

    Pass ALL the calls in `stages` and the period length in `period_days`: the
    control chart is then built with its real baseline, and only the period's
    days are checked for flags and used for the indices.
    """
    usl = math.log(targets["response"][priority] / 60.0)
    period = last_days(stages, period_days) if period_days else stages
    start = _valid_dates(period).min()
    if period_days:                     # limits from the chart period, as on the chart
        baseline_start, baseline_days = start, period_days
    rows = []
    for zone in ZONES:
        calls = _calls(period, zone, priority)
        logs = np.log(calls["response_min"].to_numpy())
        daily = [np.log(g["response_min"].to_numpy()) for _, g in calls.groupby("date")]
        sig = xbar_s_limits(daily)["sigma_short"] if daily else None
        cap = capability(logs, usl, sigma_short=sig)
        chart = daily_xbar_s(stages, zone, priority, baseline_days, baseline_start)
        in_period = chart[chart["date"] >= start] if len(chart) else chart
        stable = bool(len(in_period)) and not in_period["alarm"].any()
        norm = normality(logs)
        enough = cap["n"] >= min_n
        shown = cap["ok"] and stable and enough
        rows.append({
            "zone": zone, "n": cap["n"],
            "ppk": cap["ppk"] if shown else None, "cpk": cap["cpk"] if shown else None,
            "stable": stable, "shapiro_p": norm["p"], "shown": shown,
            "message": (cap["message"] if not cap["ok"] else
                        "" if shown else
                        f"too few calls for capability (n = {cap['n']}; need {min_n})"
                        if not enough else "not stable: capability is not meaningful"),
        })
    return pd.DataFrame(rows)


# ---- stage breakdown, health, suggestions, before/after ----------------------------------

def _stage_excess(calls: pd.DataFrame, st: dict) -> tuple[dict, dict]:
    """Minutes over target for each stage, and each stage's share of the total."""
    excess = {s: float(np.maximum(0.0, calls[f"{s}_s"] - st[s]).sum() / 60.0) for s in STAGES}
    total = sum(excess.values())
    share = {s: (excess[s] / total if total > 0 else 0.0) for s in STAGES}
    return excess, share


def stage_breakdown(stages: pd.DataFrame, priority: int = 1,
                    targets: dict = TARGETS) -> pd.DataFrame:
    """Per zone (and 'All'): calls, median seconds per stage, minutes over each
    stage's target, and each stage's share of the zone's minutes over target.
    Stage excess = max(0, stage time - stage target), summed over calls."""
    st = stage_targets(priority, targets)
    rows = []
    for zone in ZONES + ("All",):
        calls = _calls(stages, zone, priority)
        excess, share = _stage_excess(calls, st)
        row = {"zone": zone, "n": int(len(calls))}
        for s in STAGES:
            row[f"{s}_median_s"] = float(calls[f"{s}_s"].median()) if len(calls) else None
            row[f"{s}_excess_min"] = excess[s]
            row[f"{s}_share"] = share[s]
        rows.append(row)
    return pd.DataFrame(rows)


def impact_estimate(calls: pd.DataFrame, stage: str, cap_s: float,
                    target_s: float | None = None) -> dict:
    """% on time now, and if every call's `stage` were at most cap_s seconds.

    For turnout or travel: response = turnout + travel, new response = response
    - stage + min(stage, cap_s), on time = response <= target (each call's own
    response_target_s unless target_s is given). For processing, on time means
    processing <= target (default 64 s). An estimate, not a promise.
    """
    col = f"{stage}_s"
    n = int(len(calls))
    if n == 0:
        return {"stage": stage, "cap_s": cap_s, "n": 0,
                "pct_on_time_before": None, "pct_on_time_after": None, "gain": None}
    capped = np.minimum(calls[col], cap_s)
    if stage == "processing":
        target = TARGETS["processing"] if target_s is None else target_s
        before = float((calls[col] <= target).mean() * 100)
        after = float((capped <= target).mean() * 100)
    else:
        target = calls["response_target_s"] if target_s is None else target_s
        response = calls["turnout_s"] + calls["travel_s"]
        new = response - calls[col] + capped
        before = float((response <= target).mean() * 100)
        after = float((new <= target).mean() * 100)
    return {"stage": stage, "cap_s": float(cap_s), "n": n, "pct_on_time_before": before,
            "pct_on_time_after": after, "gain": after - before}


def chart_signal(rules) -> bool:
    """Is a zone's chart signal strong enough to count in zone health?

    `rules` = the slow-side rule ids that fired in the window, e.g. ["R2", "R4"].
    True for rule 1 (a point beyond 3 sigma) or for 2 or more different rules.
    One weaker rule on its own is shown on the chart but does not count.
    """
    rules = set(rules)
    return "R1" in rules or len(rules) >= 2


def zone_health(stages: pd.DataFrame, priority: int = 1, targets: dict = TARGETS,
                baseline_days: int = 14, recent_days: int = 7, as_of=None,
                actions: pd.DataFrame | None = None, baseline_start=None,
                period_days: int | None = None) -> pd.DataFrame:
    """Per zone: 'green', 'amber', 'red' or 'unknown', with reasons in plain words.

    Looks at the last `recent_days` days up to as_of. A chart signal = rule 1
    fired, or 2 or more different slow-side rules fired (one weaker rule alone
    is shown but is not enough: it keeps chance alarms near 2.5% of stable
    zone-weeks instead of 7.7%). Red = a chart signal AND the 90th percentile is
    over target; amber = one of the two; green = neither; unknown = not enough
    data for limits. Amber means "worth a look"; red means "act". A zone
    slipping back after a logged action (slip_back) is at least amber.
    """
    s = until(stages, as_of)
    target_min = targets["response"][priority] / 60.0
    st = stage_targets(priority, targets)
    end = _valid_dates(s).max()
    if period_days:                     # limits from the chart period, as on the chart
        baseline_days = period_days
        baseline_start = end - pd.Timedelta(days=period_days - 1)
    slipping = {a["zone"]: a for a in slip_back(s, actions, priority)} if actions is not None else {}
    recent_start = end - pd.Timedelta(days=recent_days - 1)
    rows = []
    for zone in ZONES:
        chart = daily_xbar_s(s, zone, priority, baseline_days, baseline_start)
        recent_calls = _calls(s, zone, priority)
        recent_calls = recent_calls[recent_calls["date"] >= recent_start]
        p90 = percentile(recent_calls["response_min"], 0.9) if len(recent_calls) else None
        if chart.attrs.get("message") or p90 is None:
            rows.append({"zone": zone, "status": "unknown", "p90_recent": p90,
                         "rules": [], "top_stage": None, "top_share": None,
                         "reasons": ["not enough data for limits yet"]})
            continue
        recent = chart[chart["date"] >= recent_start]
        rules = sorted({f[:-1] for fired in recent["rules"] for f in fired if f.endswith("+")})
        over = p90 > target_min
        signal = chart_signal(rules)
        _, share = _stage_excess(recent_calls, st)
        top = max(share, key=share.get)
        reasons = [f"{RULE_TEXT[r]} (rule {r[1]})" for r in rules] if signal else []
        if over:
            reasons.append(f"90th percentile {p90:.1f} min vs. {target_min:.0f} min target")
        if (signal or over) and share[top] > 0:
            reasons.append(f"{top} causes {share[top]:.0%} of minutes over target")
        status = "red" if signal and over else "amber" if signal or over else "green"
        if zone in slipping:
            reasons.insert(0, slipping[zone]["text"])
            if status == "green":
                status = "amber"
        if status == "green":
            reasons = ["within normal range and on target"]
            if rules:
                reasons.append(f"one weak signal ({RULE_TEXT[rules[0]]}, rule {rules[0][1]}): "
                               "not enough on its own, keep watching")
        rows.append({"zone": zone, "status": status, "p90_recent": p90, "rules": rules,
                     "top_stage": top if status != "green" else None,
                     "top_share": share[top] if status != "green" else None,
                     "reasons": reasons})
    return pd.DataFrame(rows)


def _busiest_hours(calls: pd.DataFrame, width: int = 3) -> tuple[int, float]:
    """Start hour of the `width`-hour window holding the most of these calls, and its share."""
    if len(calls) == 0:
        return 0, 0.0
    counts = np.bincount(calls["hour"].astype(int), minlength=24)
    best = max(range(24), key=lambda h: sum(counts[(h + i) % 24] for i in range(width)))
    share = sum(counts[(best + i) % 24] for i in range(width)) / counts.sum()
    return best, float(share)


def _hours_text(start: int, width: int = 3) -> str:
    return f"{start:02d}:00-{(start + width) % 24:02d}:00"


def suggest(stages: pd.DataFrame, actions: pd.DataFrame | None = None,
            priority: int = 1, targets: dict = TARGETS, window_days: int = 14,
            as_of=None, baseline_days: int = 14, baseline_start=None,
            period_days: int | None = None) -> list:
    """Suggestions from the rules in docs/plan.md, on the last `window_days` days.

    Each is a dict: rule, zone, stage, text, evidence, impact (impact_estimate
    or None), status ("new" or "action logged on <date>"). Every suggestion is
    for review by qualified staff; the tool decides nothing on its own.
    """
    s = until(stages, as_of)
    window = last_days(s, window_days)
    win_all = window[window["valid"]]
    win_p = win_all[win_all["priority"] == priority]
    st = stage_targets(priority, targets)
    health = zone_health(s, priority, targets, baseline_days=baseline_days,
                         baseline_start=baseline_start, period_days=period_days)
    city_median = {stg: float(win_p[f"{stg}_s"].median()) for stg in STAGES}
    found = []

    def add(rule, zone, stage, text, evidence, impact=None):
        found.append({"rule": rule, "zone": zone, "stage": stage, "text": text,
                      "evidence": evidence, "impact": impact, "status": "new",
                      "note": "For review by qualified staff."})

    flagged = health[health["status"].isin(["amber", "red"])]["zone"]
    for zone in flagged:
        calls = win_p[win_p["zone"] == zone]
        excess, share = _stage_excess(calls, st)
        late = calls[calls["late"]]
        codes = late["delay_reason"][late["delay_reason"] != ""].value_counts()
        if share["turnout"] >= 0.5:
            by_shift = {sh: float(np.maximum(0.0, g["turnout_s"] - st["turnout"]).sum())
                        for sh, g in calls.groupby("shift")}
            calls_share = calls["shift"].value_counts(normalize=True)
            total = sum(by_shift.values())
            worst = max(by_shift, key=by_shift.get) if total > 0 else None
            # name a shift when it holds >= 40% of the turnout excess AND >= 1.5x its share of calls
            focus = ""
            if worst:
                excess_share = by_shift[worst] / total
                if excess_share >= 0.4 and excess_share >= 1.5 * calls_share.get(worst, 1.0):
                    focus = (f", especially the {worst} shift ({excess_share:.0%} of the turnout "
                             f"delay from {calls_share.get(worst, 0):.0%} of the calls)")
            add("S1", zone, "turnout", f"Review crew readiness at Zone {zone}'s station{focus}.",
                f"Turnout causes {share['turnout']:.0%} of Zone {zone}'s minutes over target; "
                f"median turnout {calls['turnout_s'].median():.0f} s vs. {st['turnout']:.0f} s target.",
                impact_estimate(calls, "turnout", city_median["turnout"]))
        if share["travel"] >= 0.5:
            other = (late["delay_reason"] == "unit_from_another_zone").mean() if len(late) else 0.0
            zone_rate = (calls["unit_home_zone"] != calls["zone"]).mean() if len(calls) else 0.0
            city_rate = (win_p["unit_home_zone"] != win_p["zone"]).mean() if len(win_p) else 0.0
            start, _ = _busiest_hours(late)
            if other >= 0.3 and zone_rate >= 1.5 * city_rate and zone_rate > 0:
                add("S2", zone, "travel",
                    f"Consider posting an extra ambulance in Zone {zone} during {_hours_text(start)}.",
                    f"Travel causes {share['travel']:.0%} of minutes over target; {other:.0%} of "
                    f"late calls were answered by a unit from another zone, and Zone {zone} "
                    f"borrows units {zone_rate / city_rate:.1f} times as often as the city.",
                    impact_estimate(calls, "travel", city_median["travel"]))
            if (len(codes) and codes.index[0] == "traffic_or_road_closure"
                    and codes.iloc[0] >= 3 and codes.iloc[0] >= 0.3 * len(late)):
                weekday = (late["call_received"].dt.dayofweek < 5).mean() if len(late) else 0.0
                when = f"weekdays {_hours_text(start)}" if weekday >= 0.8 else _hours_text(start)
                add("S3", zone, "travel",
                    f"Check road works and alternative routes in Zone {zone} ({when}).",
                    f"Travel causes {share['travel']:.0%} of minutes over target; the top delay "
                    f"reason is {REASON_CODES['traffic_or_road_closure'].lower()} "
                    f"({codes.iloc[0]} of {len(late)} late calls).",
                    impact_estimate(calls, "travel", city_median["travel"]))

    # S4: dispatcher processing, citywide, by hour of day (all priorities).
    if len(win_all):
        by_hour = win_all.groupby("hour")
        counts = by_hour.size()
        p90 = by_hour["processing_s"].apply(lambda v: percentile(v, 0.9))
        busy = sorted(h for h in counts.index
                      if counts[h] > counts.median() and p90[h] > targets["processing"])
        if busy:
            runs = []
            for h in busy:
                if runs and h == runs[-1][-1] + 1:
                    runs[-1].append(h)
                else:
                    runs.append([h])
            span = ", ".join(f"{r[0]:02d}:00-{(r[-1] + 1) % 24:02d}:00" for r in runs)
            peak = win_all[win_all["hour"].isin(busy)]
            add("S4", "All", "processing", f"Add dispatcher cover during {span}.",
                f"In these busy hours the 90th percentile of processing is "
                f"{percentile(peak['processing_s'], 0.9):.0f} s vs. the {targets['processing']:.0f} s target.",
                impact_estimate(peak, "processing", float(win_all["processing_s"].median()),
                                target_s=targets["processing"]))

    # S5: repeated breakdowns of one ambulance.
    breaks = win_all[win_all["delay_reason"] == "ambulance_breakdown"]["unit_id"].value_counts()
    for unit, count in breaks.items():
        if count >= 2:
            add("S5", "All", "travel", f"Schedule preventive maintenance for ambulance {unit}.",
                f"{unit} broke down on {count} calls in the last {window_days} days.")

    # S6: unclear addresses, per zone with at least 5 late calls.
    for zone in ZONES:
        late = win_all[(win_all["zone"] == zone) & win_all["late"]]
        if len(late) >= 5:
            share_unclear = (late["delay_reason"] == "unclear_address").mean()
            if share_unclear >= 0.2:
                add("S6", zone, "travel", f"Use an address-verification script for Zone {zone} calls.",
                    f"{share_unclear:.0%} of Zone {zone}'s late calls had an unclear address.")

    if actions is not None and len(actions):
        acts = actions.copy()
        acts["date"] = pd.to_datetime(acts["date"]).dt.normalize()
        start = window["date"].min() if len(window) else None
        for sug in found:
            match = acts[(acts["zone"] == sug["zone"]) & (acts["stage"] == sug["stage"])]
            if start is not None:
                match = match[match["date"] >= start]
            if len(match):
                sug["status"] = f"action logged on {match['date'].max():%Y-%m-%d}"
    return found


def before_after(stages: pd.DataFrame, zone: str, action_date, priority: int = 1,
                 window_days: int = 14, targets: dict = TARGETS) -> dict:
    """Did the zone improve after the action?

    Compares the `window_days` days before the action with the days from it on
    (up to window_days): Welch's one-sided t-test on log response minutes, the
    summary numbers, and the after-period X-bar chart with its own limits.
    """
    d0 = pd.Timestamp(action_date).normalize()
    calls = _calls(stages, zone, priority)
    before = calls[(calls["date"] < d0) & (calls["date"] >= d0 - pd.Timedelta(days=window_days))]
    after = calls[(calls["date"] >= d0) & (calls["date"] < d0 + pd.Timedelta(days=window_days))]
    target_min = targets["response"][priority] / 60.0
    test = welch_before_after(np.log(before["response_min"]), np.log(after["response_min"]))
    chart = daily_xbar_s(stages, zone, priority, baseline_days=window_days, baseline_start=d0)
    chart_after = chart[chart["date"] >= d0] if len(chart) else chart
    improved = bool(test["ok"] and test["p_one_sided"] < 0.05)
    worse = bool(test["ok"] and test["p_one_sided"] > 0.95)   # significant the other way
    return {
        "zone": zone, "action_date": d0, "test": test,
        "before": summary(before["response_min"], target_min),
        "after": summary(after["response_min"], target_min),
        "after_chart": chart_after,
        "in_control_after": bool(len(chart_after)) and not chart_after["alarm"].any(),
        "verdict": ("improved" if improved else "got worse" if worse
                    else "no clear change yet" if test["ok"] else "not enough data"),
    }


def slip_back(stages: pd.DataFrame, actions: pd.DataFrame, priority: int = 1,
              settle_days: int = 7) -> list:
    """Zones drifting back after a fix.

    For each action, limits are rebuilt from the first `settle_days` days after
    it; any slow-side flag on a later day raises an alert.
    """
    alerts = []
    if actions is None or not len(actions):
        return alerts
    for _, act in actions.iterrows():
        d0 = pd.Timestamp(act["date"]).normalize()
        chart = daily_xbar_s(stages, act["zone"], priority, baseline_days=settle_days,
                             baseline_start=d0)
        if not len(chart):
            continue
        later = chart[(chart["date"] >= d0 + pd.Timedelta(days=settle_days)) & chart["alarm"]]
        if len(later):
            rules = sorted({f[:-1] for fired in later["rules"] for f in fired if f.endswith("+")})
            alerts.append({"zone": act["zone"], "action_id": act.get("action_id", ""),
                           "since": later["date"].min(), "rules": rules,
                           "text": f"Zone {act['zone']} is slipping back after the "
                                   f"{d0:%Y-%m-%d} action: "
                                   + "; ".join(RULE_TEXT[r] for r in rules) + "."})
    return alerts


# ---- live shift tools (dispatcher history tab) -------------------------------------------------

#: Zones that share an edge on the city grid (A B C on the top row, D E F below).
NEIGHBORS = {"A": ("B", "D"), "B": ("A", "C", "E"), "C": ("B", "F"),
             "D": ("A", "E"), "E": ("B", "D", "F"), "F": ("C", "E")}

_SHIFT_START = {"day": 6, "evening": 14, "night": 22}
_PREVIOUS_SHIFT = {"day": "night", "evening": "day", "night": "evening"}


def shift_window(now) -> dict:
    """The shift `now` falls in and the shift before it (each 8 hours long).

    Returns now, current, current_start, previous, previous_start and a label.
    A night shift that started before midnight starts on the previous day.
    """
    now = pd.Timestamp(now)
    name = shift_of(now.hour)
    start = now.normalize() + pd.Timedelta(hours=_SHIFT_START[name])
    if start > now:
        start -= pd.Timedelta(days=1)
    prev = _PREVIOUS_SHIFT[name]
    prev_start = start - pd.Timedelta(hours=8)

    def span(shift, s):
        return f"{shift} shift {s:%H:%M}-{s + pd.Timedelta(hours=8):%H:%M}, {s:%b %d}"

    return {"now": now, "current": name, "current_start": start, "previous": prev,
            "previous_start": prev_start,
            "label": f"Current: {span(name, start)} · Previous: {span(prev, prev_start)}"}


def shift_calls(stages: pd.DataFrame, now) -> pd.DataFrame:
    """Valid calls received from the previous shift's start up to `now` that had
    reached the scene by `now` (so a replay never shows the future)."""
    w = shift_window(now)
    return stages[stages["valid"] & (stages["call_received"] >= w["previous_start"])
                  & (stages["call_received"] <= w["now"]) & (stages["on_scene"] <= w["now"])]


def zone_subgroup_chart(stages: pd.DataFrame, priority: int) -> pd.DataFrame:
    """Each zone as one subgroup of log response minutes, against the city's limits.

    Center x-double-bar = mean of the zone means; sigma_short = sqrt(mean of the
    zone variances) (the course's X-bar formula, with zones as subgroups). A
    zone's limits are x-double-bar +/- 3 sigma_short / sqrt(n_zone). flag is
    "above" (slower than the city as a whole) or "below" (faster: check the
    data) when the zone mean is beyond its limit. Zones have no time order, so
    only the beyond-the-limit rule applies (like an analysis of means).
    One row per zone: zone, n, mean_log, sd_log, mean_min, x_ucl, x_lcl (log),
    x_ucl_min, x_lcl_min, z, flag, values_log (list for the box plot).
    attrs: xbbar, sigma_short, center_min, message.
    """
    calls = stages[stages["valid"] & (stages["priority"] == priority)]
    groups = [np.log(calls.loc[calls["zone"] == z, "response_min"].to_numpy()) for z in ZONES]
    lim = xbar_s_limits(groups)
    rows = []
    for z, g, r in zip(ZONES, groups, lim["subgroups"] or [None] * len(ZONES)):
        row = {"zone": z, "n": int(g.size),
               "mean_log": float(g.mean()) if g.size else None,
               "sd_log": float(g.std(ddof=1)) if g.size >= 2 else None,
               "mean_min": float(math.exp(g.mean())) if g.size else None,
               "x_ucl": None, "x_lcl": None, "x_ucl_min": None, "x_lcl_min": None,
               "z": None, "flag": "", "values_log": list(g)}
        if r is not None and r["z"] is not None:
            row.update(x_ucl=r["x_ucl"], x_lcl=r["x_lcl"], x_ucl_min=math.exp(r["x_ucl"]),
                       x_lcl_min=math.exp(r["x_lcl"]), z=r["z"],
                       flag="above" if r["z"] > 3 else "below" if r["z"] < -3 else "")
        rows.append(row)
    out = pd.DataFrame(rows)
    out.attrs.update(xbbar=lim["xbbar"], sigma_short=lim["sigma_short"],
                     center_min=math.exp(lim["xbbar"]) if lim["ok"] else None,
                     message="" if lim["ok"] else
                     ("no completed calls yet in these two shifts" if not len(calls)
                      else lim["message"]))
    return out


def zone_delay_reason(stages: pd.DataFrame, zone: str, priority: int,
                      targets: dict = TARGETS) -> str:
    """One plain sentence on why a zone is slow, for a chart hover label: its
    typical time vs. the city's, the stage causing most minutes over target, and
    the most-cited delay reason among its late calls."""
    calls = _calls(stages, zone, priority)
    city = _calls(stages, "All", priority)
    if not len(calls):
        return f"Zone {zone}: no completed calls."
    mine = math.exp(np.log(calls["response_min"]).mean())
    whole = math.exp(np.log(city["response_min"]).mean()) if len(city) else mine
    _, share = _stage_excess(calls, stage_targets(priority, targets))
    top = max(share, key=share.get)
    words = {"processing": "dispatch processing", "turnout": "crew turnout", "travel": "travel"}
    text = f"Zone {zone} is slower than the city: {mine:.1f} min typical vs. {whole:.1f} min."
    if share[top] > 0:
        text += f" Main cause: {words[top]} ({share[top]:.0%} of minutes over target)."
    late = calls[calls["late"] | calls["turnout_late"] | calls["travel_late"]]
    codes = late["delay_reason"][late["delay_reason"] != ""].value_counts()
    if len(codes):
        text += f" Top reason: {REASON_CODES[codes.index[0]].lower()} ({codes.iloc[0]} of {len(late)} late calls)."
    return text


def _fmt_secs(s: float) -> str:
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


def dispatcher_tips(window: pd.DataFrame, board_calls: pd.DataFrame | None, fleet,
                    now, targets: dict = TARGETS) -> list:
    """Real-time suggestions for the dispatcher, from the board and the last two shifts.

    window       stage_times rows from shift_calls() (current + previous shift)
    board_calls  the live board's calls in CALL_COLUMNS (blank stamps = not yet)
    fleet        list of {unit_id, home_zone, state}; state is available,
                 dispatched, en_route, on_scene or out_of_service
    Rules (each a dict: rule, zone, text, evidence):
      T1 a call has waited longer than the processing target -> dispatch it now,
         naming the nearest free unit (own zone first, then neighbours)
      T2 a zone has no free ambulance and a neighbour has 2 or more -> move one
         to stand by (redistribute availability)
      T3 an ambulance is out of service -> ask a neighbour zone to cover
      T4 a zone's median travel this window >= 1.25 x the city's (3+ calls) ->
         reroute (road works / traffic) or post a unit (calls from other zones);
         a cause is named only when 2+ late calls share that reason
      T5 a zone's median turnout this window is over the turnout target (3+ calls)
         -> alert that station's crews
      T6 the city's 90th percentile of processing is over target (5+ calls) ->
         ask for a second dispatcher
    Suggestions are for the dispatcher's judgment; the tool decides nothing.
    """
    now = pd.Timestamp(now)
    tips = []

    def add(rule, zone, text, evidence):
        tips.append({"rule": rule, "zone": zone, "text": text, "evidence": evidence})

    fl = pd.DataFrame(list(fleet) if fleet is not None else [],
                      columns=["unit_id", "home_zone", "state"])
    free = fl[fl["state"] == "available"]
    free_by_zone = free["home_zone"].value_counts()

    if board_calls is not None and len(board_calls):
        bc = board_calls.copy()
        for col in ("call_received", "dispatched", "on_scene"):
            bc[col] = pd.to_datetime(bc[col], errors="coerce")
        waiting = bc[bc["dispatched"].isna() & bc["call_received"].notna() & bc["on_scene"].isna()]
        for r in waiting.sort_values("call_received").itertuples():
            waited = (now - r.call_received).total_seconds()
            if waited > targets["processing"]:
                pool = (list(free[free["home_zone"] == r.zone]["unit_id"])
                        + [u for n in NEIGHBORS.get(r.zone, ()) for u in free[free["home_zone"] == n]["unit_id"]])
                unit = (f" Nearest free ambulance: {pool[0]} (Zone {fl.set_index('unit_id').loc[pool[0], 'home_zone']})."
                        if pool else " No ambulance nearby is free: ask the closest crew to clear.")
                add("T1", r.zone, f"Dispatch call {r.call_id} now.{unit}",
                    f"It has waited {_fmt_secs(waited)} (target {_fmt_secs(targets['processing'])}); "
                    f"priority {r.priority}.")

    if len(fl):
        for z in ZONES:
            if free_by_zone.get(z, 0) == 0 and (fl["home_zone"] == z).any():
                donors = [n for n in NEIGHBORS[z] if free_by_zone.get(n, 0) >= 2]
                if donors:
                    best = max(donors, key=lambda n: free_by_zone.get(n, 0))
                    add("T2", z, f"Move one ambulance from Zone {best} to stand by in Zone {z}.",
                        f"Zone {z} has no free ambulance; Zone {best} has {free_by_zone[best]} free.")
        out = fl[fl["state"] == "out_of_service"]
        for z, units in out.groupby("home_zone"):
            cover = " or ".join(f"Zone {n}" for n in NEIGHBORS.get(z, ()))
            add("T3", z, f"Ask {cover} to cover Zone {z}'s calls.",
                f"{len(units)} of Zone {z}'s ambulances out of service: {', '.join(units['unit_id'])}.")

    w = window[window["valid"]] if window is not None and len(window) else window
    if w is not None and len(w):
        city_travel = float(w["travel_s"].median())
        for z in ZONES:
            zc = w[w["zone"] == z]
            if len(zc) < 3:
                continue
            travel = float(zc["travel_s"].median())
            if city_travel > 0 and travel >= 1.25 * city_travel:
                late = zc[zc["late"] | zc["travel_late"]]
                codes = late["delay_reason"][late["delay_reason"] != ""].value_counts()
                cause = codes.index[0] if len(codes) and codes.iloc[0] >= 2 else ""   # 2+ calls to name a cause
                if cause == "traffic_or_road_closure":
                    text = f"Reroute ambulances heading into Zone {z} around the traffic or road works."
                elif cause == "unit_from_another_zone":
                    text = f"Keep an ambulance posted in Zone {z}: its calls are being answered from other zones."
                else:
                    text = f"Travel into Zone {z} is slow: check the route before sending the next unit."
                ev = (f"Median travel {travel / 60:.1f} min vs. {city_travel / 60:.1f} min citywide "
                      f"over these two shifts ({len(zc)} calls)")
                if cause:
                    ev += f"; top delay reason: {REASON_CODES[cause].lower()} ({codes.iloc[0]} of {len(late)} late calls)"
                add("T4", z, text, ev + ".")
            turnout = float(zc["turnout_s"].median())
            if turnout > targets["turnout"]:
                add("T5", z, f"Alert Zone {z}'s station: crews are slow to get rolling.",
                    f"Median turnout {_fmt_secs(turnout)} over these two shifts vs. the "
                    f"{_fmt_secs(targets['turnout'])} target ({len(zc)} calls).")
        if len(w) >= 5:
            p90 = percentile(w["processing_s"], 0.9)
            if p90 > targets["processing"]:
                add("T6", "All", "Dispatch is slowing: ask the supervisor for a second dispatcher, and "
                                 "dispatch as soon as the address and code are confirmed.",
                    f"90th percentile of call-to-dispatch is {p90:.0f} s vs. the "
                    f"{targets['processing']:.0f} s target ({len(w)} calls).")
    return tips
