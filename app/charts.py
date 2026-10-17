"""Matplotlib figures for the supervisor screens, in the app's dark style.

Drawing only: every number plotted comes from a qc.py result passed in.
Control limits (from the process) are dashed grey; the target (a spec limit,
from NFPA 1710) is a solid amber line, so the two are never confused.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import html  # noqa: E402
import io  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402

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
    # constrained layout re-fits titles, legends and labels at whatever size Shiny draws the figure
    fig, axes = plt.subplots(rows, 1, figsize=(9, height), sharex=sharex, facecolor=BG,
                             squeeze=False, layout="constrained")
    return fig, [a[0] for a in axes]


def _legend(ax, ncol=6):
    """A legend between the title and the plot, so it never covers data."""
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8, frameon=False,
                    ncol=ncol, borderaxespad=0.2, handlelength=1.6, columnspacing=1.2)
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


def daily_chart(chart, zone: str, action_dates=(), target_min: float | None = None):
    """X-bar chart (top) and S chart (bottom) from qc.daily_xbar_s(), with the
    target (a spec limit for single calls) drawn as an amber line for reference."""
    if chart is None or not len(chart):
        msg = chart.attrs.get("message", "no data") if chart is not None else "no data"
        return empty(f"Zone {zone}: {msg}")
    fig, (ax1, ax2) = _fig(rows=2, height=5.2, sharex=True)
    d = chart["date"]
    base = chart[chart["baseline"]]
    if 0 < len(base) < len(chart):          # shade only a separate baseline, not the whole chart
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
    if target_min is not None:
        ax1.axhline(target_min, color=AMBER, linewidth=1.4, label=f"{target_min:.0f}-min target (spec)")
    for when in action_dates:
        for ax in (ax1, ax2):
            ax.axvline(when, color=GREEN, linewidth=1.2)
        ax1.text(when, ax1.get_ylim()[1], " action", color=GREEN, fontsize=8, va="top")
    _style(ax1, f"Zone {zone}: daily average response", "minutes")
    _legend(ax1, ncol=4)
    ax1.set_title(ax1.get_title(loc="left"), color=FG, fontsize=11, loc="left", pad=36)
    s = chart.dropna(subset=["sd_log"])
    ax2.step(s["date"], s["s_ucl"], where="mid", color=MUTED, linestyle="--", linewidth=1)
    ax2.plot(s["date"], s["s_center"], color=MUTED, linewidth=1)
    ax2.plot(s["date"], s["sd_log"], color=LINE, linewidth=1.2, marker="o", markersize=3)
    sf = s[s["s_flag"]]
    ax2.scatter(sf["date"], sf["sd_log"], color=RED, s=30, zorder=5)
    _style(ax2, "Daily spread (standard deviation of log minutes)", "sd of ln(min)")
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=5))     # a date label every 5 days
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()
    return fig


def individuals_chart(imr, zone: str, target_min: float):
    """A plain control chart of every call (from qc.imr_chart()): each call's
    response time in order, the center line, the upper and lower control limits
    (UCL, LCL) and the target as the spec limit. Log scale, labelled in minutes."""
    if imr is None or not len(imr) or imr["ucl"].isna().all():
        msg = imr.attrs.get("message", "no data") if imr is not None else "no data"
        return empty(f"Zone {zone}: {msg}")
    fig, (ax1,) = _fig(height=3.8)
    x = np.arange(len(imr))
    ax1.plot(x, imr["response_min"], color=LINE, linewidth=0.8, marker="o", markersize=2,
             label="each call")
    ax1.axhline(imr["center_min"].iloc[0], color=MUTED, linewidth=1, label="center")
    ax1.axhline(imr["ucl_min"].iloc[0], color=MUTED, linestyle="--", linewidth=1, label="UCL / LCL (3σ)")
    ax1.axhline(imr["lcl_min"].iloc[0], color=MUTED, linestyle="--", linewidth=1)
    ax1.axhline(target_min, color=AMBER, linewidth=1.4, label=f"{target_min:.0f}-min target (spec)")
    bad = imr[imr["beyond"]]
    ax1.scatter(np.flatnonzero(imr["beyond"]), bad["response_min"], color=RED, s=30,
                zorder=5, label="beyond UCL")
    ax1.set_yscale("log")
    lo, hi = ax1.get_ylim()
    ticks = [t for t in (1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60) if lo <= t <= hi]
    ax1.set_yticks(ticks)
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    _style(ax1, f"Zone {zone}: every call", "minutes (log scale)")
    ax1.set_xlabel("call number, in order", color=MUTED, fontsize=9)
    _legend(ax1, ncol=3)
    ax1.set_title(ax1.get_title(loc="left"), color=FG, fontsize=11, loc="left", pad=36)
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
    return fig


STAGE_LABEL = {"processing": "dispatch processing", "turnout": "crew turnout", "travel": "travel"}


def _secs(s) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return "–"
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


def _stage_share_fig(bd):
    fig, (ax,) = _fig(height=3.4)
    zones = list(bd["zone"])
    labels = ["City" if z == "All" else z for z in zones]
    left = np.zeros(len(zones))
    tips = {}
    for stage in ("processing", "turnout", "travel"):
        vals = bd[f"{stage}_share"].fillna(0).to_numpy() * 100
        bars = ax.barh(labels, vals, left=left, color=STAGE_COLORS[stage], label=stage, height=0.6)
        for z, bar, v, over, med in zip(zones, bars, vals, bd[f"{stage}_excess_min"],
                                        bd[f"{stage}_median_s"]):
            gid = f"bar-{z}-{stage}"
            bar.set_gid(gid)
            who = "City" if z == "All" else f"Zone {z}"
            tips[gid] = (f"{who} · {STAGE_LABEL[stage]}: {v:.0f}% of the minutes over target "
                         f"({over:.1f} min over in total; median {_secs(med)})")
        left += vals
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    _style(ax, "Share of minutes over target, by stage", None)
    ax.set_xlabel("% of minutes over target", color=MUTED, fontsize=9)
    _legend(ax)
    return fig, tips


def stage_share(bd):
    """Each stage's share of minutes over target, by zone."""
    if bd is None or not len(bd):
        return empty("no data")
    return _stage_share_fig(bd)[0]


def to_svg(fig, tips: dict | None = None) -> str:
    """The figure as inline SVG markup that fills its container's width. Each
    artist whose gid is a key of `tips` gets a <title>, which the browser shows
    as a tooltip when the user hovers over it."""
    buf = io.StringIO()
    fig.savefig(buf, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    svg = buf.getvalue()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r'<svg([^>]*?) width="[^"]+" height="[^"]+"',
                 r'<svg\1 width="100%" style="height:auto;display:block"', svg, count=1)
    for gid, text in (tips or {}).items():
        svg = svg.replace(f'<g id="{gid}">',
                          f'<g id="{gid}" class="rw-tip"><title>{html.escape(text)}</title>', 1)
    return svg


def stage_share_svg(bd) -> str:
    """stage_share() as SVG; hover a bar to see its share, minutes over target and median."""
    if bd is None or not len(bd):
        return to_svg(empty("no data"))
    fig, tips = _stage_share_fig(bd)
    return to_svg(fig, tips)


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
    return fig


def before_after_chart(chart_full, zone: str, action_date, target_min: float | None = None):
    """The zone's daily chart with the action marked, and the target line."""
    return daily_chart(chart_full, zone, action_dates=[action_date], target_min=target_min)


def _priority_title(priority: int) -> str:
    try:
        import qc
        return f"Priority {priority}: {qc.PRIORITY_NAME[int(priority)]}"
    except Exception:  # charts.py must still draw if qc is not importable
        return f"Priority {priority}"


def zone_box_chart(sub, priority: int, target_min: float, reasons: dict | None = None,
                   _tips: dict | None = None):
    """Zones as subgroups, from qc.zone_subgroup_chart(): a box plot of each zone's
    log response minutes, the zone mean (diamond), and the city's center line and
    control limits (each zone's limits depend on its number of calls). The title
    is the priority's name, in bold. With `_tips` (a dict), each zone mean gets an
    id and a hover text: the reason from `reasons` for red points (slower than the
    city), else its typical time."""
    if sub is None or not len(sub) or int(sub["n"].sum()) == 0:
        return empty(f"{_priority_title(priority)}: no completed calls in these two shifts yet")
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
                pt = ax.scatter(i, r.mean_log, marker="D", s=40, color=RED, zorder=5)
            elif r.flag == "below":
                pt = ax.scatter(i, r.mean_log, marker="D", s=40, facecolors="none", edgecolors=AMBER,
                                zorder=5)
            else:
                pt = ax.scatter(i, r.mean_log, marker="D", s=34, color=LINE, zorder=5)
            if _tips is not None:
                gid = f"box-{priority}-{r.zone}"
                pt.set_gid(gid)
                typical = math.exp(r.mean_log)
                _tips[gid] = ((reasons or {}).get(r.zone) if r.flag == "above" and reasons
                              and r.zone in reasons else
                              f"Zone {r.zone}: {typical:.1f} min typical ({r.n} call{'s' if r.n != 1 else ''})"
                              + (", slower than the city" if r.flag == "above" else
                                 ", faster than the city: check the data" if r.flag == "below" else
                                 ", within the city's limits"))
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
    _style(ax, _priority_title(priority), "minutes (log scale)")
    ax.set_title(_priority_title(priority), color=FG, fontsize=12, loc="left", pad=36,
                 fontweight="bold")
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8, frameon=False, ncol=3,
                    borderaxespad=0.2, handlelength=1.6, columnspacing=1.2)
    for text in leg.get_texts():
        text.set_color(MUTED)
    return fig


def zone_box_svg(sub, priority: int, target_min: float, reasons: dict | None = None) -> str:
    """zone_box_chart() as SVG: hover a zone's diamond to see why it is red, or its typical time."""
    tips: dict = {}
    fig = zone_box_chart(sub, priority, target_min, reasons, _tips=tips)
    return to_svg(fig, tips)
