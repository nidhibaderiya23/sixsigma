# Glossary and FAQ

## Glossary

Terms are in alphabetical order.

| Term | Meaning |
|---|---|
| **90th percentile** | The time that 9 in 10 calls beat. The slowest 1 in 10 calls take longer. The standard asks for it to be at or under the target. |
| **Action** | A fix that the supervisor logs, with a date, a zone, a stage, what was done and an owner. ERGent then checks whether it worked. |
| **Alarm** | A flag on the **slow** side of a control chart. A flag on the fast side only says "check the data". |
| **ANOVA** | A test that asks whether several groups (here, zones) really differ, or whether the gaps could be chance. |
| **Average (mean)** | The sum of the times divided by how many there are. It hides slow calls, so ERGent also shows percentiles. |
| **Baseline** | A stretch of normal days used to set a zone's normal range. In ERGent, the **chart period** plays this role. |
| **CAD** | Computer-aided dispatch. The city's system that keeps one row per 911 call and stamps the times. |
| **Capability (Ppk, Cpk)** | A measure of whether a stable process can meet its target reliably. ERGent shows it as a plain verdict. |
| **Center line** | The middle line of a control chart: the zone's normal level. |
| **Chart period** | How many days of history the cards use (14, 28 or 42). It also sets the control limits. |
| **Chart signal** | A strong warning on the daily chart: rule R1 fired, or two or more different slow-side rules fired in the last 7 days. |
| **Clock speed** | How fast the board clock runs when you log calls by hand (1x, 10x, 30x or 60x). |
| **Common cause** | Ordinary, everyday variation. The ups and downs inside the control limits. |
| **Control chart** | A chart of a process over time, with a center line and control limits. It shows when something unusual happens. |
| **Control limits (UCL and LCL)** | The upper and lower lines on a control chart, at 3 sigma from the center. They show what is **normal for the process**. They are not the target. |
| **Crew turnout** | The time from dispatch until the crew leaves (`dispatched` to `en_route`). Target: 60 seconds. |
| **Delay reason** | One of six codes the crew picks when a stage runs late: traffic or road closure, ambulance breakdown, unit from another zone, unclear address, weather, crew not ready. |
| **Dispatch processing** | The time from the call arriving until an ambulance is dispatched (`call_received` to `dispatched`). Target: 64 seconds. |
| **False alarm** | A flag that fires by chance when nothing has really changed. A few are expected. |
| **Geometric mean** | The "typical" value for skewed data: `exp` of the mean of the logs. ERGent uses it for a typical response time. |
| **Log scale (ln)** | A way of measuring that pulls in a long slow tail. ERGent's charts and tests use the natural log of the time. |
| **Median** | The middle value: half the calls are faster, half are slower. |
| **Moving range (MR)** | The size of the jump from one call to the next. |
| **NFPA 1710** | A US standard for fire and EMS response. It is the source of the priority 1 targets (64 s, 60 s and 480 s). |
| **On time** | A call whose response was at or under its target. The goal is at least 90% of calls. |
| **p-value** | The chance of seeing a difference this big if nothing had really changed. A small p (under 0.05) means the difference is probably real. |
| **Percentile** | The value that a given share of the data falls under. The 90th percentile is beaten by 90% of calls. |
| **Poka-yoke** | Mistake-proofing. The screen makes the wrong entry hard to make, for example by showing only the next valid button. |
| **Priority** | The urgency code for a call: 1 life-threatening, 2 urgent, 3 non-urgent. Each has its own response target. |
| **Response time** | The time from dispatch to arrival on scene (`dispatched` to `on_scene`). It is turnout plus travel. This is the prompt's metric. |
| **Shift** | An eight-hour block: day 06:00 to 14:00, evening 14:00 to 22:00, night 22:00 to 06:00. |
| **Sigma (σ)** | A measure of spread, like a standard deviation. Control limits sit 3 sigma from the center. |
| **Slip-back** | A zone drifting back to its old problem after a fix. |
| **Special cause** | Something that changed the process: a breakdown, road works, a new crew habit. A flag points to one. |
| **Specification limit (spec limit)** | The requirement, such as the 9-minute target. It comes from a standard, not from the process. |
| **Stable** | A process that stays inside its control limits with no flags. Capability only makes sense for a stable process. |
| **Standard deviation (SD)** | How spread out the values are around their mean. A big SD means less predictable service. |
| **Subgroup** | A small group of values charted as one point. In the daily chart, a subgroup is one zone-day. In the History chart, it is one zone. |
| **Suggested action** | A fixed "if this, then suggest that" rule on the data, shown with its evidence. |
| **Synthetic data** | Invented data, made by a script. ERGent contains no real patient data. |
| **Travel time** | The drive to the scene (`en_route` to `on_scene`). |
| **Welch's t-test** | A test of whether two groups have different averages that does not assume equal spread. ERGent uses it for before and after. |
| **X̄ chart (x-bar chart)** | A control chart of group averages. ERGent's daily chart shows each day's average. |
| **Zone** | One of six areas of Ithaca (A to F). The outlines on the map are illustrative, not official EMS districts. |

## Frequently asked questions

### 1. Why not just use the monthly average?

An average blends fast and slow calls. A handful of very slow calls can hide inside a good-looking
average. Take ten calls with times 4, 5, 6, 7, 8, 9, 10, 11, 12 and 20 minutes. The average is 9.2
minutes, close to a 9-minute target. But only 6 of the 10 were on time, and one patient waited 20
minutes. ERGent shows the 90th and 95th percentiles and on-time share next to the average, and splits
each zone and each day. That is where the slow calls show up.

### 2. Why does ERGent use logs?

Response times are skewed. Most are quick, and a few are very slow. The log pulls in the slow tail, so
control charts and tests behave. ERGent turns the results back into minutes before showing them, so you
never have to think in logs.

### 3. What is the difference between amber and red?

On the Zone map, **amber ("Worth a look")** means one warning sign: either the daily chart shows a
strong change, or the zone's 90th percentile is over its target. **Red ("Act now")** means both together.
Amber is worth checking. Red needs action. Some amber zones are false alarms, and the stricter amber
rule makes them rare.

### 4. Why does Zone D's daily chart show no red dots when the Zone map is amber?

The control limits come from the **chart period** you picked. If a problem lasts for most of that
period, it widens the limits and can hide itself on the daily chart. That is a trade-off the team chose
for simplicity and consistency. The Zone map, Delay by stage and Capability cards do not hide it. Read
the daily chart together with them.

### 5. What does "Can't judge yet" mean on the Capability card?

The zone's times changed during the period (it has a flag on its daily chart). A reliability score for
a zone that is changing would mislead. Find and fix the cause first, then judge again.

### 6. What does "Not enough calls" mean?

A zone needs at least 30 calls in the chart period for a trustworthy score. With fewer calls, the
numbers are too uncertain.

### 7. Is the data real?

No. All the data is synthetic. A script made it with a fixed random seed. It has no real patients,
addresses or names. It is shaped like real field data so that the tool has something realistic to
analyze. The Ithaca zone outlines are illustrative too.

### 8. Where do the targets come from?

For priority 1, from NFPA 1710, a US standard: 64 seconds to dispatch, 60 seconds for the crew to get
moving and 8 minutes to travel, so 9 minutes from dispatch to arrival, each met by at least 90% of
calls. **The priority 2 (15 minutes) and priority 3 (20 minutes) targets are our own assumptions**,
because the standard does not set them. A supervisor can change every target with the **Targets**
button.

### 9. Does ERGent dispatch ambulances or change staffing?

No. ERGent **flags and suggests**. Every suggestion is "for review by qualified staff", and the
dispatcher's tips are "for the dispatcher's judgment". People make every decision.

### 10. What is the difference between a control limit and the target?

A **control limit** (UCL and LCL) comes from the process: it shows what is normal for a zone. The
**target** (a specification limit) comes from a standard: it shows what is required. A zone can be
within its normal range and still miss the target, or beat the target and still be changing. ERGent
draws them as different lines so you never confuse them.
