"""Matplotlib figures for the supervisor screens, in the app's dark style.

Drawing only: every number plotted comes from a qc.py result passed in.
Control limits (from the process) are dashed grey; the target (a spec limit,
from NFPA 1710) is a solid amber line, so the two are never confused.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import math  # noqa: E402

import numpy as np  # noqa: E402

BG = "#16191f"
FG = "#f2f2f0"
MUTED = "#9aa0a6"
GRID = "#2a2e36"
GREEN, AMBER, RED = "#6fd39a", "#f2c14e", "#ef6461"
LINE = "#7aa7ff"
STAGE_COLORS = {"processing": "#b39ddb", "turnout": AMBER, "travel": LINE}


def _style(ax, title=None, ylabel=None):
    ax.set_facecolor(BG)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=FG, fontsize=11, loc="left", pad=22)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=9)


def _fig(rows=1, height=3.2, sharex=False):
    fig, axes = plt.subplots(rows, 1, figsize=(9, height), sharex=sharex, facecolor=BG,
                             squeeze=False)
    return fig, [a[0] for a in axes]


def _legend(ax):
    """A one-line legend between the title and the plot, so it never covers data."""
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8, frameon=False,
                    ncol=6, borderaxespad=0.2, handlelength=1.6, columnspacing=1.2)
    for text in leg.get_texts():
        text.set_color(MUTED)


def empty(message: str):
    """A blank figure carrying a short message (no data, no limits yet)."""
    fig, (ax,) = _fig(height=2.0)
    _style(ax)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, message, color=MUTED, ha="center", va="center", fontsize=10,
            transform=ax.transAxes)
    return fig


def daily_chart(chart, zone: str, action_dates=()):
    """X-bar chart (top) and S chart (bottom) from qc.daily_xbar_s()."""
    if chart is None or not len(chart):
        msg = chart.attrs.get("message", "no data") if chart is not None else "no data"
        return empty(f"Zone {zone}: {msg}")
    fig, (ax1, ax2) = _fig(rows=2, height=5.2, sharex=True)
    d = chart["date"]
    base = chart[chart["baseline"]]
    if len(base):
        for ax in (ax1, ax2):
            ax.axvspan(base["date"].min(), base["date"].max(), color="#ffffff", alpha=0.04,
                       label="baseline" if ax is ax1 else None)
    ax1.plot(d, chart["x_center_min"], color=MUTED, linewidth=1, label="center")
    ax1.step(d, chart["x_ucl_min"], where="mid", color=MUTED, linestyle="--", linewidth=1,
             label="control limits (3σ)")
    ax1.step(d, chart["x_lcl_min"], where="mid", color=MUTED, linestyle="--", linewidth=1)
    ax1.plot(d, np.exp(chart["mean_log"]), color=LINE, linewidth=1.4, marker="o",
             markersize=3.5, label="daily average")
    alarm = chart[chart["alarm"]]
    ax1.scatter(alarm["date"], np.exp(alarm["mean_log"]), color=RED, s=36, zorder=5,
                label="flagged day")
    check = chart[chart["check"]]
    ax1.scatter(check["date"], np.exp(check["mean_log"]), facecolors="none",
                edgecolors=AMBER, s=40, zorder=5, label="check the data")
    for when in action_dates:
        for ax in (ax1, ax2):
            ax.axvline(when, color=GREEN, linewidth=1.2)
        ax1.text(when, ax1.get_ylim()[1], " action", color=GREEN, fontsize=8, va="top")
    _style(ax1, f"Zone {zone}: daily average response (geometric mean of the day's calls)",
           "minutes")
    _legend(ax1)
    s = chart.dropna(subset=["sd_log"])
    ax2.step(s["date"], s["s_ucl"], where="mid", color=MUTED, linestyle="--", linewidth=1)
    ax2.plot(s["date"], s["s_center"], color=MUTED, linewidth=1)
    ax2.plot(s["date"], s["sd_log"], color=LINE, linewidth=1.2, marker="o", markersize=3)
    sf = s[s["s_flag"]]
    ax2.scatter(sf["date"], sf["sd_log"], color=RED, s=30, zorder=5)
    _style(ax2, "Daily spread (standard deviation of log minutes)", "sd of ln(min)")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def imr_chart(imr, zone: str, target_min: float):
    """Individuals chart (log scale, minutes) and moving-range chart from qc.imr_chart()."""
    if imr is None or not len(imr) or imr["ucl"].isna().all():
        msg = imr.attrs.get("message", "no data") if imr is not None else "no data"
        return empty(f"Zone {zone}: {msg}")
    fig, (ax1, ax2) = _fig(rows=2, height=5.2, sharex=True)
    x = np.arange(len(imr))
    ax1.plot(x, imr["response_min"], color=LINE, linewidth=0.8, marker="o", markersize=2,
             label="each call")
    ax1.axhline(imr["center_min"].iloc[0], color=MUTED, linewidth=1, label="center")
    ax1.axhline(imr["ucl_min"].iloc[0], color=MUTED, linestyle="--", linewidth=1,
                label="control limits (3σ)")
    ax1.axhline(imr["lcl_min"].iloc[0], color=MUTED, linestyle="--", linewidth=1)
    ax1.axhline(target_min, color=AMBER, linewidth=1.4,
                label=f"{target_min:.0f}-min target (spec, not a control limit)")
    bad = imr[imr["beyond"]]
    ax1.scatter(np.flatnonzero(imr["beyond"]), bad["response_min"], color=RED, s=30,
                zorder=5, label="extreme delay")
    ax1.set_yscale("log")
    lo, hi = ax1.get_ylim()
    ticks = [t for t in (1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60) if lo <= t <= hi]
    ax1.set_yticks(ticks)
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    _style(ax1, f"Zone {zone}: every call in order (log scale)", "minutes")
    _legend(ax1)
    ax2.plot(x, imr["mr"], color=LINE, linewidth=0.8)
    if imr.attrs.get("mr_ucl") is not None:
        ax2.axhline(imr.attrs["mr_ucl"], color=MUTED, linestyle="--", linewidth=1)
        ax2.axhline(imr.attrs["mr_bar"], color=MUTED, linewidth=1)
    _style(ax2, "Moving range (jump between consecutive calls, log minutes)", "MR")
    ax2.set_xlabel("call number", color=MUTED, fontsize=9)
    fig.tight_layout()
    return fig


def stage_breakdown(bd):
    """Median seconds per stage per zone, as stacked bars, from qc.stage_breakdown()."""
    if bd is None or not len(bd):
        return empty("no data")
    fig, (ax,) = _fig(height=3.4)
    zones = list(bd["zone"])
    left = np.zeros(len(zones))
    for stage in ("processing", "turnout", "travel"):
        vals = bd[f"{stage}_median_s"].fillna(0).to_numpy() / 60.0
        ax.barh(zones, vals, left=left, color=STAGE_COLORS[stage], label=stage, height=0.6)
        left += vals
    ax.invert_yaxis()
    _style(ax, "Median minutes in each stage, by zone", None)
    ax.set_xlabel("minutes", color=MUTED, fontsize=9)
    _legend(ax)
    fig.tight_layout()
    return fig


def stage_share(bd):
    """Each stage's share of minutes over target, by zone."""
    if bd is None or not len(bd):
        return empty("no data")
    fig, (ax,) = _fig(height=3.4)
    zones = list(bd["zone"])
    left = np.zeros(len(zones))
    for stage in ("processing", "turnout", "travel"):
        vals = bd[f"{stage}_share"].fillna(0).to_numpy() * 100
        ax.barh(zones, vals, left=left, color=STAGE_COLORS[stage], label=stage, height=0.6)
        left += vals
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    _style(ax, "Which stage causes the minutes over target (% of each zone's total)", None)
    ax.set_xlabel("% of minutes over target", color=MUTED, fontsize=9)
    _legend(ax)
    fig.tight_layout()
    return fig


def normal_plot(norm: dict, zone: str):
    """Normal probability plot of log minutes from qc.normality()."""
    if not norm.get("ok"):
        return empty(f"Zone {zone}: {norm.get('message', 'no data')}")
    fig, (ax,) = _fig(height=3.0)
    t, o = np.asarray(norm["theoretical"]), np.asarray(norm["ordered"])
    ax.scatter(t, o, color=LINE, s=8)
    slope, intercept = np.polyfit(t, o, 1)
    ax.plot(t, slope * t + intercept, color=MUTED, linewidth=1)
    _style(ax, f"Zone {zone}: normal probability plot of ln(minutes)  "
               f"(Shapiro-Wilk p = {norm['p']:.3f})", "ln(minutes)")
    ax.set_xlabel("normal quantile", color=MUTED, fontsize=9)
    fig.tight_layout()
    return fig


def before_after_chart(chart_full, zone: str, action_date):
    """Daily averages before and after an action, the after part with its own limits."""
    return daily_chart(chart_full, zone, action_dates=[action_date])


def zone_box_chart(sub, priority: int, target_min: float):
    """Zones as subgroups, from qc.zone_subgroup_chart(): a box plot of each zone's
    log response minutes, the zone mean (diamond), and the city's center line and
    control limits (each zone's limits depend on its number of calls)."""
    if sub is None or not len(sub) or int(sub["n"].sum()) == 0:
        return empty(f"Priority {priority}: no completed calls in these two shifts yet")
    fig, (ax,) = _fig(height=3.6)
    zones = list(sub["zone"])
    have = [i for i, v in enumerate(sub["values_log"]) if len(v)]
    ax.boxplot([sub["values_log"].iloc[i] for i in have], positions=have, widths=0.5,
               patch_artist=True, showfliers=True, manage_ticks=False,
               medianprops={"color": FG, "linewidth": 1.2},
               boxprops={"facecolor": "#232833", "edgecolor": MUTED},
               whiskerprops={"color": MUTED}, capprops={"color": MUTED},
               flierprops={"marker": "o", "markersize": 3, "markerfacecolor": MUTED,
                           "markeredgecolor": "none"})
    xbbar = sub.attrs.get("xbbar")
    if sub.attrs.get("center_min") is not None:
        ax.axhline(xbbar, color=MUTED, linewidth=1, label="city center")
    first = True
    for i, r in enumerate(sub.itertuples()):
        if r.x_ucl is not None and not (isinstance(r.x_ucl, float) and np.isnan(r.x_ucl)):
            ax.hlines([r.x_ucl, r.x_lcl], i - 0.38, i + 0.38, colors=MUTED, linestyles="--",
                      linewidth=1, label="city limits (3σ)" if first else None)
            first = False
        if r.mean_log is not None and not (isinstance(r.mean_log, float) and np.isnan(r.mean_log)):
            if r.flag == "above":
                ax.scatter(i, r.mean_log, marker="D", s=40, color=RED, zorder=5)
            elif r.flag == "below":
                ax.scatter(i, r.mean_log, marker="D", s=40, facecolors="none", edgecolors=AMBER,
                           zorder=5)
            else:
                ax.scatter(i, r.mean_log, marker="D", s=34, color=LINE, zorder=5)
    ax.scatter([], [], marker="D", s=34, color=LINE, label="zone mean")
    ax.scatter([], [], marker="D", s=40, color=RED, label="slower than city")
    ax.axhline(math.log(target_min), color=AMBER, linewidth=1.4,
               label=f"{target_min:.0f}-min target")
    lo, hi = ax.get_ylim()
    ticks = [t for t in (1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90) if lo <= math.log(t) <= hi]
    ax.set_yticks([math.log(t) for t in ticks])
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    ax.set_xticks(range(len(zones)))
    ax.set_xticklabels([f"{z}\nn={n}" for z, n in zip(zones, sub["n"])])
    ax.set_xlim(-0.6, len(zones) - 0.4)
    _style(ax, f"Priority {priority}: each zone's calls against the city's control limits",
           "minutes (log scale)")
    _legend(ax)
    fig.tight_layout()
    return fig
