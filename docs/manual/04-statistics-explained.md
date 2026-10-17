# Statistics explained

Every number ERGent shows comes from **one file of plain, tested functions** (`app/qc.py`). The screens
only draw those results. This chapter explains each statistic **in plain words first**, then gives the
formula. Each one has four parts:

- **What it tells you**
- **How to read it**
- **The formula**
- **Watch out for**

You do not need this chapter to use ERGent. It is here so you can **explain every number**.

## Where each statistic appears

| Statistic | Where you see it |
|---|---|
| Stage times and data checks | Behind everything. Data quality card. |
| Mean, standard deviation, percentiles, % on time | Statistics card, History numbers, Result table |
| Daily X̄-S chart | Charts tab, Control chart (Daily chart) |
| Every-call chart | Charts tab, Control chart (Every call) |
| Flag rules and zone health | Red dots, Zone map (both views) |
| Zones-as-subgroups box chart | Dispatcher History, Response time by zone |
| Delay by stage | Charts tab, Delay by stage |
| Capability | Charts tab, Capability |
| ANOVA | Charts tab, Zone comparison |
| Welch's t-test and before/after | Actions tab, Result |
| Impact estimate and suggestion rules S1 to S6 | Actions tab, Suggested actions |
| Dispatcher tips T1 to T6 | Dispatcher History, Suggested actions |
| Slip-back | Actions tab, Slip-back alerts |

## Three ideas to know first

**1. Times are in seconds inside the data and in minutes on screen.** A response of 540 seconds is 9
minutes.

**2. Control charts and capability use the logarithm of the time.** Response times are *skewed*: most
calls are quick, and a few are very slow. The log (written `ln`) pulls in that slow tail. After the
math is done, ERGent turns the results back into minutes (with `exp`). So a "typical" time on a chart is
a *geometric* average: `exp(mean of ln minutes)`.

**3. Control limits are not the target.** A **control limit** (UCL and LCL) comes from the process
itself. It says what is *normal for this zone*. A **specification limit** (the 9-minute target) comes
from a standard. It says what is *required*. A zone can be inside its control limits and still miss the
target, and the other way round. ERGent draws the target as a separate line, so you never confuse the
two.

## 1. Stage times and data checks

**What it tells you.** How long each part of a call took, so you can say *why* a call was slow.

**How to read it.** A call has three stages. The prompt's metric, **response**, is turnout plus travel.

**The formula.**

```
processing = dispatched  - call_received      (dispatch: the call waits for an ambulance)
turnout    = en_route    - dispatched          (the crew gets moving)
travel     = on_scene    - en_route            (the drive)
response   = on_scene    - dispatched          (= turnout + travel)
```

A call is **late** when its response is greater than its priority's target. A **stage** is late when it
is greater than that stage's target. The travel target is the response target minus the turnout target:
for priority 1, 540 − 60 = 480 seconds.

**Data checks.** A call is **left out of every statistic** and listed, with its reason, if:

1. its call ID is a **duplicate** (the repeat is left out; the first is kept);
2. a needed time is **missing** (call received, dispatched, en route or on scene);
3. a time is **earlier than the one before it**;
4. its response time is **zero**;
5. its **zone or priority is unknown**.

**Watch out for.** Processing happens *before* dispatch, so it sits outside the prompt's metric. ERGent
still measures it, because a delay there also hurts the patient. Also, a crew might press "on scene" a
little after arriving, so the times are only as good as the pressing habit.

## 2. Mean, standard deviation, percentiles and % on time

**What it tells you.** The **mean** is the average. The **standard deviation (SD)** says how spread out
the times are. The **median** is the middle call. The **90th percentile** is the time that 9 in 10 calls
beat. The **95th percentile** is the time that 19 in 20 calls beat. **On time** is the share of calls
within the target.

**How to read it.** Look at the percentiles, not just the mean. The danger in emergency response is the
slow tail, and the mean hides it. The standard says 90% of calls should be on time. That is the same
as saying the 90th percentile should be at or under the target.

**The formula.**

```
mean        = (x1 + x2 + ... + xn) / n
SD          = sqrt( sum of (x - mean)^2 / (n - 1) )          (sample SD, n - 1)
on time (%) = 100 x (number of calls with x <= target) / n
percentile  : sort the values; position h = (n - 1) x p, counting from 0
              result = x[floor h] + (h - floor h) x ( x[floor h + 1] - x[floor h] )
```

This is the "type 7" percentile. It is the same as R's default and Excel's `PERCENTILE.INC`.

**Worked example.** Ten response times in minutes: 4, 5, 6, 7, 8, 9, 10, 11, 12, 20, with a 9-minute
target.

| Number | Value |
|---|---|
| Mean | 9.2 |
| Median | 8.5 |
| 90th percentile | 12.8 (h = 9 × 0.9 = 8.1, so 12 + 0.1 × (20 − 12)) |
| 95th percentile | 16.4 |
| On time | 6 of 10 = 60% |

The mean (9.2) looks close to the 9-minute target. But only 60% of the calls were on time, and one
patient waited 20 minutes. That is why ERGent does not rely on the mean.

**Watch out for.** With one call, the percentiles equal that value and the SD cannot be worked out. With
no calls, ERGent shows a dash.

## 3. Checking that logs behave (normality)

**What it tells you.** Whether the log of the response times is close to a bell curve. Several tests
assume it is.

**How to read it.** Open **More info** on the **Zone comparison** card. A probability plot shows the
points. If they sit close to a straight line, the log times look normal. The **Shapiro-Wilk** test gives
a number `p`. A `p` above 0.05 means "no sign of a problem".

**The formula.** The Shapiro-Wilk W statistic and its p-value (from the SciPy library), on `ln(minutes)`.

**Watch out for.** With hundreds of calls, even a tiny bend can give a small `p`. Judge by the plot as
well. ERGent needs at least 3 values that are not all the same.

## 4. The daily X̄-S chart

**What it tells you.** Whether a zone is behaving the way it normally does. Each dot is **one day**. A
red dot is a day when the zone was slower than its own normal range.

**How to read it.** The top panel (X̄) shows each day's typical response time. The center line is the
normal level. The dashed lines are the UCL and LCL. The bottom panel (S) shows how spread out the day's
calls were. A red dot means something changed. Open **Delay by stage** to see which stage.

**The formula.** The subgroup is one zone-day. Work on `ln(minutes)`:

```
daily point     = mean of ln(minutes) for that day's calls
center          = mean of the daily points in the chart period
sigma_xbar      = standard deviation of the daily points in the chart period (n - 1)
UCL, LCL        = center +/- 3 x sigma_xbar         (the same for every day)

S chart:
s_bar           = mean of the daily standard deviations (days with 2 or more calls)
n_bar           = average number of calls per day in the period (rounded, at least 2)
c4(n)           = sqrt( 2 / (n - 1) ) x Gamma(n / 2) / Gamma( (n - 1) / 2 )
B4 = 1 + 3 x sqrt(1 - c4^2) / c4        B3 = 1 - 3 x sqrt(1 - c4^2) / c4   (never below 0)
S limits        = B4 x s_bar (upper) and B3 x s_bar (lower)
```

Here are some values of the constants (they match the standard tables):

| Calls per day (n̄) | c4 | B3 | B4 |
|---|---|---|---|
| 2 | 0.7979 | 0 | 3.267 |
| 3 | 0.8862 | 0 | 2.568 |
| 5 | 0.9400 | 0 | 2.089 |
| 7 | 0.9594 | 0.118 | 1.882 |
| 10 | 0.9727 | 0.284 | 1.716 |

The limits are then shown back in minutes (`exp`). The chart is judged with the **flag rules** in section
6.

**Watch out for: the chart period sets the limits.** In ERGent, the limits come from the **chart period
you select** (14, 28 or 42 days). The team chose this on purpose. It is simple, and it keeps the chart,
the zone map, the suggestions and the capability card in agreement. But there is a cost. **If a problem
lasts for most of the period, it widens the limits and can hide itself.**

For example, in the demo data, Zone D's crew turnout got slow on Sep 15. As of Sep 28 with a 28-day
period, the period includes both normal days and slow days. The limits stretch to about 3.3 to 10.5
minutes, and **no day breaks them**. Zone D's chart shows **no red dots**. If the limits were taken
from the first 14 days instead (before the problem), the same chart would flag Zone D on 11 days.

So: **read the daily chart together with the Zone map, Delay by stage and Capability.** In this
example, the Zone map is amber for D (its 90th percentile is 10.2 min against a 9-min target), Delay by
stage says 92% of its overrun is crew turnout, and Capability says D is below the standard.

Also watch out for days with very few calls. Their dots are noisy, and a one-call day has no spread, so
it has no point on the S chart.

## 5. The every-call chart (individuals chart)

**What it tells you.** Whether a *single call* was unusually slow. It looks at each call, in the order
the calls came in.

**How to read it.** Each dot is one call. The dashed lines (UCL and LCL) are the normal range for a
single call. A red dot above the UCL is an unusual delay worth checking one by one: a breakdown, a wrong
address, a closed road. The amber line is the target. The scale is a log scale.

**The formula.** This is the course's I-MR (individuals and moving range) method, on `ln(minutes)`:

```
moving range   MR_i = abs( x_i - x_(i-1) )            (jump from one call to the next)
MR_bar         = mean of the moving ranges
center         = mean of ln(minutes)
sigma          = MR_bar / 1.128                         (1.128 is the constant d2 for pairs)
UCL, LCL       = center +/- 3 x sigma
MR upper limit = 3.267 x MR_bar                         (computed, not drawn)
```

**Worked example.** Five values 10, 12, 11, 15, 12. The moving ranges are 2, 1, 4, 3, so MR̄ = 2.5. The
center is 12 and σ = 2.5 / 1.128 = 2.216. The limits are 5.351 and 18.649.

**Watch out for.** It needs at least 2 calls. If every call is the same, there is no spread, so there are
no limits ("no variation"). The calls are assumed to be roughly independent, which is stated but not
tested. As on the daily chart, the limits come from the calls in the chart period.

## 6. The flag rules, and what makes a zone amber or red

**What it tells you.** The rules decide which dots on the daily chart turn red. The stricter **zone
health** rule decides whether a zone on the map is on track, worth a look, or act now.

**How to read it.** A dot **above** the center line is on the **slow side**. That is an **alarm**. A dot
**below** the center line is on the **fast side**. That only says "check the data".

**The formula.** Let `z = (daily point - center) / sigma_xbar`. So "1 sigma" means one `sigma_xbar`. The
rules are:

| Rule | A flag fires at a day when... |
|---|---|
| **R1** | that day's point is beyond 3 sigma |
| **R2** | 2 of the last 3 points are beyond 2 sigma, on the same side |
| **R3** | 4 of the last 5 points are beyond 1 sigma, on the same side |
| **R4** | 8 points in a row are on the same side of the center line |
| **R5** | 6 points in a row are steadily rising (or falling) |

R1 to R4 are the **Western Electric rules**. R5 is a trend rule. Together they catch both sudden jumps
and slow drifts.

**Zone health.** On the map, each zone looks at the **last 7 days**. First, ERGent decides if there is a
**chart signal**:

```
chart signal = rule R1 fired in the last 7 days,
               OR 2 or more DIFFERENT slow-side rules fired in the last 7 days

red    ("Act now")       = chart signal AND the 90th percentile of the last 7 days is over the target
amber  ("Worth a look")  = exactly one of those two
green  ("On track")      = neither
unknown                  = not enough data to set limits
```

A zone that is **slipping back** after a logged fix (section 18) is at least amber.

**Why stricter?** One weak rule on its own is drawn on the chart but does not count. It appears in the
zone's reasons as "one weak signal ... keep watching". The team tested this. On pure-noise simulations,
a stable zone-week shows amber by chance about **2.5%** of the time with this rule, against about
**7.7%** if any single rule counted.

**Watch out for.** Even so, **some false alarms are expected**. Amber means "worth a look", not "something
is broken". Red means act. A zone can also be amber only because its 90th percentile is just over the
target, with no change on the chart.

## 7. Zones as subgroups (the dispatcher's History chart)

**What it tells you.** Which zones are slower than the city as a whole, in the current and previous
shift.

**How to read it.** Each zone is drawn as a **box plot** (the box holds the middle half of its calls)
with a **diamond** for its average. The grey line is the city's center. The short dashed lines are that
zone's limits. A **red diamond** is a zone beyond its upper limit: slower than the city. A hollow ring is
a zone beyond its lower limit: faster, so check the data. **Hover** over a red diamond to read why.

**The formula.** Each zone is **one subgroup** of `ln(minutes)` (calls that reached the scene, for the
priority you chose):

```
center      = mean of the six zone averages
sigma_short = sqrt( mean of the zone variances )         (zones with 2 or more calls)
limits      = center +/- 3 x sigma_short / sqrt(n_zone)  (wider for zones with few calls)
z           = (zone average - center) / ( sigma_short / sqrt(n_zone) )
flag        = "above" if z > 3, "below" if z < -3
```

Zones have **no time order**, so only the "beyond the limit" rule is used. This is like an *analysis of
means*.

The hover text for a red zone says: its typical time against the city's, the stage causing the most
minutes over target, and the most common delay reason among its late calls.

**Watch out for.** A zone with few calls has wide limits, so it is hard to flag. A zone with no calls
shows nothing. The two shifts together can be a small sample early in a shift.

## 8. Delay by stage

**What it tells you.** Which stage (dispatch, crew turnout or travel) causes the minutes over target.

**How to read it.** For each zone, the three parts of the bar add up to 100%. The biggest part is the
stage to fix first. **Hover** over a part to see its share, the minutes over target, and the stage's
median time.

**The formula.**

```
stage excess = max( 0, stage time - stage target )         for each call, in minutes
share        = a stage's total excess / the sum of the three stages' total excess
```

**Watch out for.** A share is only about **minutes over target**. A stage that stays under target has
no share, even if it is slow compared with other stages. If nothing is over target, all shares are 0.

## 9. Capability

**What it tells you.** Whether a zone can meet the target **reliably**, not just on average.

**How to read it.** ERGent turns the result into a plain verdict.

| Verdict | Expected calls on time (rounded) |
|---|---|
| Very reliable | 99 in 100 or more |
| Reliable | 95 to 98 in 100 |
| Just meets the standard | 90 to 94 in 100 |
| Below the standard | under 90 in 100 |
| Can't judge yet | The zone is not stable (see below) |
| Not enough calls | Fewer than 30 calls |

**The formula.** The target is an **upper limit** only (a response cannot be "too fast"), so ERGent uses
the **upper side** of the capability indices, on `ln(minutes)`:

```
USL        = ln( target in minutes )
Ppk        = ( USL - mean of ln x ) / ( 3 x SD of ln x )              uses the overall spread (sigma_total)
Cpk        = ( USL - mean of ln x ) / ( 3 x sigma_short )              uses the spread within each day
sigma_short = sqrt( mean of the daily variances )
expected on time (%) = 100 x Phi( 3 x Ppk )                            Phi = the standard normal curve
```

Some handy values:

| Ppk | Expected on time |
|---|---|
| 0.33 | 83.9% |
| 0.43 | 90.1% (the standard's 90% line) |
| 0.50 | 93.3% |
| 0.67 | 97.8% |
| 0.80 | 99.2% |
| 1.00 | 99.9% |

The verdict is judged on the **rounded** percentage, so the label always agrees with the number in the
text.

**Stable only.** A capability score only makes sense for a **stable** zone. ERGent shows a score only
when the zone's daily chart has **no slow-side flag in the chart period** *and* the zone has **at least
30 calls**. Otherwise it says "Can't judge yet" or "Not enough calls".

**Watch out for.** Cpk and Ppk differ when a zone drifts between days. Ppk includes the drift; Cpk does
not. The numbers sit behind **More info**. The score assumes the log times are roughly normal. Because
the daily chart's limits come from the chart period, a long problem can hide on the chart (section 4).
In that case capability may still say "Below the standard", as it does for Zone D in the demo.

## 10. Zone comparison (ANOVA)

**What it tells you.** Whether the zones **really differ**, or whether the gaps could be chance.

**How to read it.** ERGent answers in a sentence: "Yes. Zone D is typically 6.0 min against 4.9 min in
Zone A ..." or "No clear difference ...". The typical times are geometric averages.

**The formula.** A one-way **analysis of variance** (ANOVA) on `ln(minutes)` of each zone's calls:

```
SSB = sum over zones of  n_zone x ( zone mean - grand mean )^2      (between zones)
SSW = sum over zones of  sum of ( x - zone mean )^2                   (within zones)
F   = ( SSB / (k - 1) ) / ( SSW / (N - k) )                           k zones, N calls
p   = the chance of an F this big if the zones were really the same  (from the F distribution)
```

ERGent says "Yes" when `p < 0.05`.

**Worked example.** Zone A = [1, 2, 3] and zone B = [4, 5, 6]. SSB = 13.5 and SSW = 4, so
F = 13.5 / (4 / 4) = 13.5 with 1 and 4 degrees of freedom.

**Watch out for.** A zone with fewer than 2 calls is left out. If every call in each zone is identical,
the test cannot run. ANOVA says *that* zones differ, not *which* one. Look at the typical times for that.
A "Yes" with hundreds of calls can come from a small gap, so check that the gap is large enough to
matter.

## 11. Welch's t-test and the before/after check

**What it tells you.** Whether response times really dropped after an action.

**How to read it.** The **Result** card shows a verdict: **Improved**, **Got worse**, **No clear change
yet** or **Not enough data**.

**The formula.** ERGent compares the **14 days before** the action date with the **days from the action
date on** (up to 14), using **Welch's one-sided t-test** on `ln(minutes)`. Welch's test does not assume
both groups have the same spread.

```
t  = ( mean_before - mean_after ) / sqrt( s_before^2 / n_before + s_after^2 / n_after )
df = Welch-Satterthwaite degrees of freedom
p  = chance of a t this big if nothing changed (one-sided: "after is lower")

Improved            if p < 0.05
Got worse           if p > 0.95     (it got slower, and too much to be chance)
No clear change yet otherwise
Not enough data     if either side has fewer than 2 calls, or there is no variation at all
```

**Worked example.** Before = [10, 12, 14] and after = [6, 8, 10]. The means are 12 and 8. Each variance
is 4, so t = 4 / √(4/3 + 4/3) = 2.449 with 4 degrees of freedom.

**Steady.** ERGent also checks whether the new level is **steady**. It draws the zone's daily chart after
the action, with limits from the first 14 days after the action, and looks for a slow-side flag.

**Watch out for.** A better time after a fix does **not prove** the fix caused it. Other things may have
changed. The check shows an *apparent* change. Staff judge the cause. If the after period is 14 days
or shorter, the "steady" check judges those days against limits made from the same days.

## 12. Impact estimate

**What it tells you.** A best-case guess of how much better on-time performance could be if one stage
were fixed. For example "on time 78% → 97%".

**How to read it.** It answers: "if this zone's slow stage were as fast as the city's typical call, how
many more calls would be on time?" It is an **estimate, not a promise**.

**The formula.** Take the flagged stage (turnout or travel). Cap each call's stage time at the **city's
median** for that stage (priority and last 14 days). Then recount.

```
new response = response - stage time + min( stage time, cap )
on time      = new response <= the call's response target
```

For the dispatch stage, "on time" means dispatch time at or under the processing target (64 s by
default).

**Worked example.** Turnout [3, 1, 4, 1] minutes and travel [7, 7, 6, 9] minutes, target 9, city median
turnout 1 minute. Responses are 10, 8, 10, 10, so 1 of 4 is on time (25%). With turnout capped at 1 minute
they become 8, 8, 7, 10, so 3 of 4 are on time (75%).

**Watch out for.** Real results are usually smaller. A fix rarely brings every call down to the median.

## 13. Suggested actions for the supervisor (rules S1 to S6)

**What they tell you.** Fixed "if this, then suggest that" rules turn the numbers into something to try.
Each suggestion shows its **evidence** and says "for review by qualified staff".

**How to read them.** The rules look at the **last 14 days** up to the as-of date. A stage's **share** is
its excess divided by the zone's total excess (section 8). Rules S1 to S3 only apply to zones that are
**amber or red**.

| Rule | Tag | If | Then suggest |
|---|---|---|---|
| **S1** | Crew readiness | Turnout share is 50% or more | Review crew readiness at that zone's station. It names a shift when that shift holds 40% or more of the turnout excess **and** at least 1.5 times its share of the calls. |
| **S2** | Coverage | Travel share is 50% or more, 30% or more of late calls are coded "unit from another zone", and the zone borrows ambulances at least 1.5 times the city rate | Consider posting an extra ambulance in that zone during the busiest three hours of late calls |
| **S3** | Routes | Travel share is 50% or more, and "traffic or road closure" is the top code (at least 3 calls and at least 30% of late calls) | Check road works and alternative routes. It says "weekdays" if 80% or more of late calls fall on weekdays. |
| **S4** | Dispatcher cover | Citywide, all priorities: in an hour of the day with above-median call counts, the 90th percentile of dispatch time is over the processing target | Add dispatcher cover in those hours |
| **S5** | Maintenance | One ambulance has 2 or more breakdowns in the window | Schedule preventive maintenance for that ambulance |
| **S6** | Address checks | A zone has at least 5 late calls, and 20% or more of them have "unclear address" | Use an address-verification script |

**The formula** for the evidence and the estimate is in sections 8 and 12.

**Watch out for.** The rules only see what the crews record. If delay reasons are missing, S2, S3, S5 and
S6 cannot fire. The tool **decides nothing**. A qualified person decides.

## 14. Dispatcher tips (rules T1 to T6)

**What they tell you.** Live suggestions for the dispatcher, from the board right now and the last two
shifts.

**How to read them.** They appear in **Suggested actions** on the History tab.

| Tip | If | Then suggest |
|---|---|---|
| **T1 Dispatch now** | A call has waited longer than the processing target (64 s) with no dispatch | Dispatch it now. It names the nearest free ambulance: own zone first, then neighboring zones. |
| **T2 Rebalance** | A zone has ambulances but none free, and a neighbor has 2 or more free | Move one to stand by (from the neighbor with the most free) |
| **T3 Cover** | An ambulance is out of service | Ask the neighboring zones to cover |
| **T4 Route** | A zone has 3 or more calls and its **median** travel is at least 1.25 times the city's | Check the route. If 2 or more late calls share a delay reason, name it: reroute around traffic or road works, or keep an ambulance posted. |
| **T5 Station alert** | A zone has 3 or more calls and its **median** turnout is over the turnout target (60 s) | Alert that station's crews |
| **T6 Dispatcher load** | The city has 5 or more calls and the **90th percentile** of dispatch time is over 64 s | Ask the supervisor for a second dispatcher |

**Watch out for.** Tips use small samples (a few calls), so they are prompts for your judgment, not
verdicts. "Neighboring zones" means zones that touch on the map: A touches B and D; B touches A, C and E;
C touches B and F; D touches A and E; E touches B, D and F; F touches C and E.

## 15. Slip-back

**What it tells you.** Whether a zone is drifting back to its old problem after a fix.

**How to read it.** A **Slip-back alert** names the zone and the warning sign, and the zone is at least
amber on the map.

**The formula.** For each logged action, ERGent builds the zone's daily chart with limits from the **first
7 days after the action**. If a slow-side flag appears on a day **after those 7 days**, it raises an alert.

**Watch out for.** It needs enough days after the action. In the demo data, there is no slip-back for
Zone D, which is the right answer.

## Quick reference: the formulas on one page

| Statistic | Formula |
|---|---|
| Response | `on_scene - dispatched` |
| SD | `sqrt( sum (x - mean)^2 / (n - 1) )` |
| Percentile (type 7) | `h = (n - 1) p`, then interpolate |
| Daily center and sigma | center = mean of daily means; `sigma_xbar` = SD of daily means |
| Daily limits | `center +/- 3 x sigma_xbar` |
| S chart | `B3 x s_bar` and `B4 x s_bar` |
| Every-call limits | `center +/- 3 x MR_bar / 1.128` |
| z | `(point - center) / sigma_xbar` |
| Zone box chart limits | `center +/- 3 x sigma_short / sqrt(n_zone)` |
| Ppk | `(ln USL - mean ln x) / (3 x SD ln x)` |
| Cpk | `(ln USL - mean ln x) / (3 x sigma_short)` |
| Expected on time | `100 x Phi(3 x Ppk)` |
| ANOVA F | `( SSB / (k - 1) ) / ( SSW / (N - k) )` |
| Welch t | `(mean_b - mean_a) / sqrt( s_b^2/n_b + s_a^2/n_a )` |
| Stage excess | `max(0, stage time - target)` |
