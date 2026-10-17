# Q&A preparation

Short answers first; the detail is in `docs/manual/04-statistics-explained.md` and `app/README.md`.

## The method

**Why do you chart log times instead of minutes?**
Response times are right-skewed: most calls are 4 to 7 minutes, but a few take 15 or more. The X̄
chart, ANOVA, Welch and Ppk all assume roughly normal data, and ln(minutes) is close to normal.
The app checks this with Shapiro-Wilk and a normal probability plot (Zone comparison, More info).
Results are shown back in minutes.

**The Shapiro-Wilk p is small for some zones. Is the normal assumption broken?**
With a few hundred calls, Shapiro-Wilk flags even tiny departures from normal (Zone D over the demo's
42 days: p ≈ 0.004). Look at the normal probability plot instead: the points sit close to the line, with
slightly heavy tails. The X̄ chart plots daily means, which are closer to normal than single calls
(central limit theorem). The capability numbers are the most sensitive to the tails, which is one
reason ERGent also shows the plain 90th percentile.

**Why X̄-S and not X̄-R or a p-chart?**
The subgroup is one zone-day, and its size changes from day to day (about 5 to 10 calls). S uses
every value and handles unequal sizes; R gets less efficient as n grows. A p-chart (share of late
calls) throws away how late a call was. We also show an individuals chart (I-MR) of every call, to
catch a single extreme delay.

**How are your control limits computed?**
The center is the mean of the daily means over the chart period the supervisor picks (14, 28 or
42 days). The limits are the center ± 3 standard deviations of those daily means, constant for every
day. The S chart uses s̄ with B3 and B4 from c4 at the average calls per day.

**Doesn't a problem inside the period widen its own limits?**
Yes, and we say so on the limits slide. We chose period limits so that the chart, the map, the
suggestions and the capability card all agree. The cost: on Sep 28, Zone D's daily chart shows no red
dots. The map (amber from its 90th percentile), the capability card and the zone comparison still
catch it. Limits from the first 14 days would flag Zone D on 11 days. A longer or earlier baseline
window is an easy change.

**Running five rules at once raises false alarms. How do you control that?**
A chart signal needs rule R1, or two or more different rules, within the last 7 days. On pure-noise
simulations, that cut a stable zone's chance of turning amber in a week from 7.7% to 2.5%. Red also
needs the 90th percentile over target.

**What does Ppk mean here, and why not Cpk?**
Upper-side Ppk = (ln 9 − mean) / (3 s) on log minutes: a one-sided spec, because only late is bad.
Ppk uses the total spread (drift included), so it describes what the zone is doing. We turn it into
plain words with Φ(3·Ppk): Zone D's 0.42 means about 89 in 100 calls within 9 minutes. Capability is
hidden for a zone that is not stable, and needs at least 30 calls.

**Why Welch and not a pooled t-test for before and after?**
The spread changes too (Zone D's SD went from 2.3 to 1.8 minutes). Welch does not assume equal
variances.

**Is the zone difference real?**
One-way ANOVA on log times: F = 9.31, p ≈ 10⁻⁸ as of Sep 28 (demo data). On the stable baseline:
F = 2.11, p = 0.062, "no clear difference".

## The data and the tool

**Is this real data?**
No. A seeded script (`data/make_data.py`, seed 42) makes three files: a stable baseline, a 42-day demo
with four planted problems, and a messy file with data defects. The codebook is `data/README.md`.
The Ithaca zones are illustrative areas, not official EMS districts.

**Where do the targets come from?**
NFPA 1710: 9 minutes at the 90th percentile for life-threatening calls (a 60-second turnout plus
8 minutes of travel) and 64 seconds of processing. The 15- and 20-minute targets for priorities 2 and
3 are our own assumptions. All targets are editable (the Targets button).

**What does the user have to enter?**
Nothing they don't already have. The dispatcher and the crew press one button per step; the zone,
priority, unit, distance and weather already come from the dispatch system (CAD). A reason code is
asked for only when a stage runs late.

**Does the tool make decisions?**
No. It flags and suggests, with the evidence, and says "for review by qualified staff".

**How do you know the numbers are right?**
77 tests with hand-worked answers (for example, the 90th percentile of the ten-call example is 12.8,
and B4 = 2.568 for 3 calls a day). `demo/README.md` lists every number the demo should show.

**Why dispatcher statistics by shift, not by person?**
Ranking individuals invites gaming and blame. The system stores the dispatcher ID, but every
statistic is by shift and workload.

**What would you do next?**
Connect a real CAD export and Ithaca's real EMS districts, validate the priority 2 and 3 targets with
local agencies, add a shared board with logins, and tune the rules on a year of real data.

**How did you use AI?**
As a teammate under a written spec (`SPEC.md`) and task contract (`CONTRACT.yaml`). We wrote the
known-answer tests first and reviewed every design decision. We can explain every number on screen.
