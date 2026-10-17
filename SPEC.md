# SPEC: Six Sigma Hackathon team project

What your tool IS. Your agent reads this before every task. Where the code and this file
disagree, the code is the bug: change this file first, then the code.

Most of this page is already decided by the event and the [rubric](docs/criteria.md).
**Only the `FILL IN` lines change, and you do not have to write them by hand:** describe your app and ask your agent to update them. They depend on the prompt your team picks at kickoff
(prompts are secret until then, see [`docs/prompts.md`](docs/prompts.md)) and on your team.
The examples after each `FILL IN` show the shape of an answer. They are not hints about the prompts.

## 1. Team and prompt
- **Team name:** Team ERG (Nidhi Baderiya, Zeba Haq, Dhruv Bhandari). Tool name: **Response Watch**.
- **Track:** on-campus (24 hours). Devpost submission due Sat Oct 17, 1 PM ET; showcase 2-3 PM.
- **Prompt we chose:** On-campus prompt, Health Systems: **Emergency Response**. "Ambulance dispatch
  to on-scene times are varying wildly across city zones, but the 911 center only looks at monthly
  averages, missing fatal outliers, not where or why these failures occur. Design a statistical tool
  to help manage dispatchers, response time logging in real-time, generate analyzes, and flag zones
  that are in need of resolution."
- **Our public repo:** github.com/nidhibaderiya23/sixsigma

## 2. User and use case (rubric: scope 5, user and use case 5)
- **User:** the **EMS operations supervisor** at a city 911 dispatch center (primary), and the
  **dispatcher on shift** (secondary). Each picks their role on the start page and gets their own screens.
- **Decision the tool helps them make, and when:**
  - Supervisor, at the start of each shift and whenever a flag fires: which zone needs attention,
    which stage is causing it (dispatcher processing, crew turnout or travel), which fix to try, and
    later whether that fix worked.
  - Dispatcher, in real time: which open call is running late right now and needs escalating.
- **Why this matches the prompt:** it logs every call's timestamps live, replaces monthly averages
  with percentiles and control charts that catch the slow outliers, splits each delay into stages to
  show *why*, and flags *where* (which zone) needs resolution.

## 3. Inputs (rubric: minimal inputs 5)
Only what this user can actually measure or already knows. Fewer is better; every input a user
cannot measure costs points.

The city's computer-aided dispatch system (CAD) records these automatically, one row per call.
Nobody types a timestamp: CAD stamps the call when it arrives, and the dispatcher and crew stamp the
rest by pressing a button. The caller's address stays in CAD; the tool only uses the zone.

| Input | Type and units | Where the user gets it |
|---|---|---|
| `call_id` | text | CAD, automatic |
| `zone` | category, A to F | CAD, from the caller's address |
| `priority` | 1 (life-threatening), 2, 3 | the call-taker's medical code in CAD |
| `call_received`, `dispatched`, `en_route`, `on_scene`, `cleared` | timestamps, to the second | CAD: automatic for the call, then the dispatcher's and crew's buttons |
| `unit_id`, `unit_home_zone` | text; A to F | CAD fleet list |
| `distance_km` | numeric, km | CAD's GPS routing |
| `dispatcher_id` | text | CAD login (stored; never shown per person) |
| `weather` | clear, rain or snow | CAD weather feed |
| `delay_reason` | one of 6 codes, blank unless late | the crew taps it only when a stage runs past its target |
| Targets (settings) | seconds or minutes, per priority | defaults from NFPA 1710 (below); the supervisor can edit them |

Delay reason codes: traffic or road closure, ambulance breakdown, unit from another zone, unclear
address, weather, crew not ready.

Default targets, each met by at least 90% of calls (NFPA 1710, the US standard for fire-department
EMS response): processing 64 s, turnout 60 s, travel 480 s for an advanced life support unit, so
**priority 1 dispatch to on scene = 9 min**. Priority 2 = 15 min and priority 3 = 20 min are our own
stated assumptions (NFPA does not set them). For every priority, the travel target is the response
target minus the 60 s turnout target: 480 s for P1, 840 s for P2, 1140 s for P3.

## 4. The statistics, and why (rubric: valid QC analysis 25)
Say the method in words before any code exists. Load the `stats-first-steering` skill first.
- **Method:** in words, one function each in `app/qc.py`:
  1. **Stage times** per call: processing = dispatched - call_received; turnout = en_route -
     dispatched; travel = on_scene - en_route; **response = on_scene - dispatched** (the prompt's
     metric). A call is flagged and left out if a timestamp is missing or out of order, its call ID
     is a duplicate, its response time is zero, or its zone or priority is unknown.
  2. **Summary numbers** per zone and period: mean (shown only for comparison), median, 90th and 95th
     percentiles (linear interpolation: R's default "type 7", Excel's PERCENTILE.INC), and % on time.
  3. **I-MR chart** (individuals and moving range) per zone, on each call's **log** response time in
     call order. Center = mean of the logs; σ_short = MR̄ / 1.128 (d₂ for pairs); limits = center ± 3σ_short.
     Moving-range upper limit = 3.267 × MR̄ (D₄), lower = 0. Limits are shown back in minutes.
  4. **Daily zone X̄-S chart** (average and standard deviation; the course's recommended pair). A
     subgroup = one zone-day's calls, as log response times. x̄̄ = mean of the daily means;
     σ_short = √(mean of the daily variances), the course formula. X̄ limits = x̄̄ ± 3σ_short/√nᵢ, so
     limits widen on quiet days with few calls. S chart: center c₄(nᵢ)σ_short, limits
     (c₄ ± 3√(1 - c₄²))σ_short, lower limit never below 0. Limits come from a baseline (default: the
     first 14 days), not from the whole series.
  5. **Flag rules** on the daily X̄ points. A point on the slow side is an alarm; a point on the fast side
     only says "check the data". Rules: (1) 1 point beyond 3σ; (2) 2 of 3 beyond 2σ, same side; (3) 4 of
     5 beyond 1σ; (4) 8 in a row above the center line; (5) 6 in a row rising. Rules 1-4 are the
     Western Electric rules. Also: rule 1 on single calls in the I chart (an extreme delay), and a spec
     flag when a zone's rolling 7-day 90th percentile is over target.
  6. **Capability**, upper side only (the target is an upper spec limit), on log times:
     Ppk = (ln USL - mean of ln x) / (3 × sd of ln x) using σ_total, and Cpk the same with σ_short.
     For Cpk, σ_short = √(mean of the daily variances) in the period. Capability is shown only when
     that zone's daily X̄-S chart has no slow-side flag in the period. Otherwise the tool says
     "not stable: capability is not meaningful".
  7. **Tests**, both on log response time, α = 0.05. One-way **ANOVA** across zones: do zones really
     differ? **Welch's t-test**, one-sided, before vs. after an action: did response time really drop?
  8. **Impact estimate and suggestions**. The impact estimate recomputes % on time with the flagged
     stage capped at the citywide median for that stage and priority, e.g. "if Zone D's turnout were
     typical, on time would rise from 78% to 97%". Suggestions are fixed if-then rules on these numbers
     (listed in `docs/plan.md`). Each shows its evidence and says "for review by qualified staff".
  9. **Dispatcher's shift view**, on the current and previous shift, following the board clock:
     - A **zones-as-subgroups X̄ chart** per priority. Each zone is one subgroup of log response
       minutes. Center x̄̄ = the mean of the zone means; σ_short = √(mean of the zone variances);
       zone limits x̄̄ ± 3σ_short/√n_zone. Each zone is drawn as a box plot plus its mean.
       Zones have no time order, so only the beyond-the-limit rule applies, like an analysis of means.
     - **Real-time dispatcher tips:** fixed rules on the live board and the two shifts (listed in
       `docs/plan.md`):
       - dispatch a call that has waited past 64 s;
       - rebalance ambulances into a zone with none free;
       - cover a zone with a unit out of service;
       - reroute when a zone's travel is ≥ 1.25× the city's;
       - alert a station whose turnout is over target;
       - ask for a second dispatcher when processing is over target.
- **Why it fits the use case:** response times are skewed, and the danger is in the slow tail.
  Percentiles and control charts on log times show the slow outliers that monthly averages hide. The
  stage split shows why a call was slow, and daily zone charts show where and since when.
- **Assumptions and how the tool checks them:**
  - Log response times are roughly normal. The Charts screen shows a normal probability plot and a
    Shapiro-Wilk p-value per zone.
  - Calls in time order are roughly independent. This is stated, not tested; the I chart uses call order.
  - The baseline period is stable (in statistical control). The tool shows the baseline chart, and the supervisor can move
    the baseline dates.
  - Capability needs stability. It is hidden for flagged zones.
- **Known-answer check:** worked by hand; every function must reproduce these numbers.
  - Summary on response minutes [4, 5, 6, 7, 8, 9, 10, 11, 12, 20], target 9: mean 9.2, median 8.5,
    90th percentile 12.8 (position 1 + 9 × 0.9 = 9.1, so 12 + 0.1 × (20 - 12)), 95th percentile 16.4,
    on time 6/10 = 60%.
  - I-MR on [10, 12, 11, 15, 12]: moving ranges 2, 1, 4, 3, so MR̄ = 2.5. Center 12,
    σ_short = 2.5/1.128 = 2.2163, limits 5.351 to 18.649, MR upper limit 8.1675.
  - X̄-S on subgroups [2, 4, 6], [3, 5, 7], [4, 6, 8]: x̄̄ = 5, σ_short = √((4 + 4 + 4)/3) = 2.
    X̄ limits 5 ± 3 × 2/√3 = 1.536 to 8.464. c₄(3) = 0.8862, so the S chart center is 1.7725,
    the upper limit 4.552 and the lower limit 0.
  - Ppk on [6, 7, 8, 9, 10] with USL 12: sd = √2.5 = 1.5811, so Ppk = (12 - 8)/(3 × 1.5811) = 0.8433.
  - ANOVA on A = [1, 2, 3] and B = [4, 5, 6]: SSB = 13.5, SSW = 4, F = 13.5/(4/4) = 13.5 (df 1 and 4).
  - Welch on before [10, 12, 14] vs. after [6, 8, 10]: t = 4/√(4/3 + 4/3) = 2.449, df = 4.
  - Impact: turnout [3, 1, 4, 1] min, travel [7, 7, 6, 9] min, target 9, city median turnout 1 min.
    On time goes from 1/4 = 25% to 3/4 = 75%.
  - Flag rules with center 0 and σ 1: [0.5, 2.5, 0.3, 2.4] fires rule 2 at the 4th point;
    eight points of 0.1 fire rule 4 at the 8th; [1, 2, 3, 4, 5, 6] fires rule 5 at the 6th.
  - Degenerate cases:
    - Constant data has σ = 0, so the limits and Ppk return None with "no variation".
    - One call: the percentiles equal that value, and the I-MR refuses (it needs at least 2).
    - A day with one call gets an X̄ point but no S point.
    - Missing timestamps: the call is excluded and listed.

Fixed for every team:
- The statistic lives in **one plain, tested function** (`app/qc.py` or `app/qc.R`). The API, app or
  package only calls it and displays the result. No statistics inside UI code.
- Every statistic has a test against a known answer and a degenerate case (constant data, n = 1, missing values).
- You can explain every number the tool prints. If you cannot, it is not done.

## 5. Delivery (rubric: working tool 25)
- **Stack:** dashboard: **Shiny for Python**, with the statistics in plain Python (pandas, numpy, scipy)
  in `app/qc.py`.
- **Starting demo:** `demos/fastapi/`, for its Python four-script contract (`testme.sh`, `manifestme.sh`,
  `deployme.sh`, `README.md`, `.python-version` 3.12). Its `app.py` is replaced by a Shiny app, because
  `demos/shinyapp/` is R-only. Deploy with `.claude/skills/connect-publish/workflows/deploy-shiny-py.yml`.

Fixed for every team:
- Start from **one** demo in `demos/`, copied to `app/`. Keep its four-script contract
  (`testme`, `manifestme`, `deployme`, `README.md`); `testme` starts the tool with one command.
- Deployed on the course **Posit Connect** server with a public URL (publisher key handed out at the
  event). Deploy early: copy one workflow from
  [`.claude/skills/connect-publish/workflows/`](.claude/skills/connect-publish/workflows/).
- A small tool that runs beats a large tool that does not.

## 6. Outputs
- **What the user sees:** a start page with two buttons, Dispatcher and Supervisor.
  - **Dispatcher:**
    - Live board (redesigned with the team on Oct 16):
      - the top row of counts: waiting, dispatched, en route, on scene and units available;
      - a 2x2 grid: Log a call (with a clock-speed option), Incoming calls, Dispatched and En route;
      - then the ambulances list and the live 6-zone tile map, then Resolved (on scene counts as
        resolved; Clear frees the ambulance).
      Every clock turns amber at 80% of its target and red past it.
    - Compact simulation controls in the header. Reset clears the board to zero.
    - Buttons that only work in order, a reason code required when a stage is late, and a
      confirmation before Clear.
    - History tab: the current and previous shift, following the board clock. It shows real-time
      dispatcher suggestions and a zones-as-subgroups control chart for each priority.
  - **Supervisor:** a settings card above the tabs sets the dataset, the priority (default 1), the as-of
    date, the baseline start and the targets.
    - **Overview:** a zone health list (green, amber or red, with the reason in plain words). It covers
      the last 7 days. A chart signal is rule 1, or 2 or more different slow-side rules. Red means a
      chart signal and the 90th percentile is over target; amber means one of the two; green means
      neither (the team chose this stricter rule on Oct 16 to cut chance alarms). Then KPI tiles
      (average next to the 90th and 95th percentiles, and % on time); a history tile map.
    - **Charts:** the I-MR and daily X̄-S charts with flagged points in red, the stage breakdown, and
      capability with the tests.
    - **Actions:** suggestions with evidence and impact, an action log, a before/after check, and
      slip-back alerts.
  - How to read the daily chart: "a red dot above the dashed line is a day when this zone was slower
    than its own normal range. Open the stage breakdown to see which stage caused it."

## 7. Test datasets and codebook (rubric: demo 10, datasets 5, codebook 5)
2-3 small CSVs in `data/`, invented but shaped like real field data, each showing one behavior.
`data/README.md` is the codebook: every file, every column with units, and what it would take to
collect this data for real.
- **Datasets:** synthetic, made by a seeded script `data/make_data.py`, and labeled as synthetic.
  - `calls_baseline.csv`: 6 zones, 28 days, about 16 calls per zone per day, stable. The tool should
    show no zone flags beyond the rare expected false alarm.
  - `calls_demo.csv`: 42 days.
    - Zone D's night-shift turnout rises from day 15. A fix is logged on day 29, and it returns to normal.
    - Zone C's weekday 4-7 PM travel slows from day 20 (road works, reason "traffic or road closure").
    - The tool must flag D for turnout and C for travel, suggest the matching fixes, and confirm that
      D improved.
  - `calls_messy.csv`: about 60 calls with missing en-route stamps, out-of-order times, a zone with 2
    calls, a day with no calls and a duplicate call ID. The tool must list them and not crash.
  - `actions_demo.csv`: the fix logged in the demo (date, zone, what was done, owner).

## 8. Documentation and reproducibility (rubric: docs 10, public repo 5)
- `README.md` says what the tool does, for whom, every input and parameter, how to run it in one
  command, and walks through the demo on each test dataset.
- Public GitHub repo; a fresh clone runs `testme` and the tests pass with no extra steps.
- Submit on Devpost: the repo link plus a demo.

## 9. Out of scope
What we will NOT build, so nobody (human or agent) builds it by accident.
- Default: logins, databases, real customer data, a second statistic before the first one is tested.
- **The tool decides nothing on its own.** No automatic dispatching or staffing changes; it flags and
  suggests for qualified staff.
- No real patient data, addresses or names. No hospital, on-scene care or pre-arrival instruction times.
- No board shared across browsers: each browser session has its own live board.
- No real street map or GPS: zones are a schematic grid of 6 tiles.
- No per-person dispatcher rankings. The ID is stored; stats are shown by shift and workload.
- No AI-written suggestions, no forecasting.
- No Pareto, fishbone or stratification screens (the team dropped them on Oct 16).
