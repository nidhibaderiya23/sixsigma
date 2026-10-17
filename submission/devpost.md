# Devpost submission: ready to paste

Each field below matches a box on the Devpost "Submit a project" form. Replace anything in
**[square brackets]** first. Submit by **Sat Oct 17, 1 PM ET**.

---

## Project name

ERGent

## Elevator pitch (the one-line tagline, 200 characters max)

Monthly averages hide the patient who waited 20 minutes. ERGent shows Ithaca's 911 center which zone is slow, which stage causes it, since when, and whether the fix worked.

---

## About the project (the story; paste everything between the lines)

---

### Inspiration

Our prompt: ambulance dispatch-to-on-scene times vary wildly across city zones, but the 911 center only looks at monthly averages. An average can look fine while one patient waits far too long. Take ten response times: 4, 5, 6, 7, 8, 9, 10, 11, 12 and 20 minutes. The mean is 9.2 minutes, close to a 9-minute target. But only 6 of the 10 calls were on time, and one patient waited 20 minutes. We wanted a tool that makes that patient visible: **where** it happens, **why**, and **since when**.

### What it does

ERGent is a Shiny for Python dashboard for the 911 EMS dispatch center of **Ithaca, NY**, with two roles.

**The dispatcher (in real time)**
- Logs each call. The five timestamps (received, dispatched, en route, on scene, cleared) are stamped by button presses, so nobody types a time.
- Running clocks turn amber at 80% of a target and red past it.
- A reason code is required only when a stage runs late (poka-yoke).
- A live map of Ithaca colours each zone by its worst open call.
- A History tab shows the current and previous shift as a box chart by zone, with suggestions such as "Dispatch now", "Rebalance" or "Route".
- A "Simulate a shift" replay shows all of this in a minute.

**The supervisor (start of every shift)**
- An interactive map of Ithaca's six zones, coloured by health (green, amber, red). Hover a zone for the reasons; click it to drill in.
- A daily **X̄-S control chart** per zone on log response times, with Western Electric rules, plus a chart of every single call.
- 90th and 95th percentiles and % on time, instead of only an average.
- **Delay by stage:** is it the dispatcher (processing), the crew getting out the door (turnout), or the drive (travel)?
- **Zone comparison:** one-way ANOVA on log times. **Capability:** Ppk turned into "about 89 in 100 calls within 9 minutes".
- **Actions:**
  - rule-based suggestions with an impact estimate;
  - an action log;
  - a before/after Welch test that checks whether a fix worked;
  - slip-back alerts if the zone gets worse again.

The tool flags and suggests. Qualified staff decide.

### How we built it

- **Six Sigma first.** We wrote the Define and Measure work (charter, CTQ tree, SIPOC, process map, data-quality plan) before any code. Targets follow NFPA 1710: 9 minutes for life-threatening calls at the 90th percentile, a 64-second processing target and a 60-second turnout target.
- **Statistics first.** Every number on screen comes from one file, `qc.py`, which has no plotting and no UI. Every function has a hand-worked known-answer test: 77 pytest tests in all, for example a 90th percentile of 12.8 on the ten-call example and B4 = 2.568 for subgroups of 3.
- **Synthetic but realistic data.** A seeded script makes three test datasets with a codebook: a stable 28-day baseline, a 42-day demo and a messy 3-day file with data defects. The demo dataset has four planted problems the tool must find:
  - a night-shift turnout slowdown in Zone D, then a fix;
  - road works slowing travel in Zone C at rush hour;
  - an evening dispatcher bottleneck;
  - an ambulance that keeps breaking down.
- **The app.** Shiny for Python (Core), matplotlib charts with hover text, and a Leaflet map of Ithaca, deployed on the course's Posit Connect server.
- **AI as a teammate.** We used an AI coding agent under a written contract (`CONTRACT.yaml`) and a spec (`SPEC.md`). The team reviewed every design decision and can explain every number.

### Challenges we ran into

- **Choosing control limits honestly.** Limits from the selected chart period keep every card in agreement. But a long problem widens its own limits and can hide itself on the daily chart. We kept that method, documented the trade-off, and made sure the zone map, the capability card and the zone comparison still catch it.
- **False alarms.** Running many rules at once fires by chance. We count a chart signal only when rule 1 fires, or two or more different rules fire. On pure noise, that cut a stable zone's weekly false-amber rate from 7.7% to 2.5%.
- **Skewed times.** Response times are right-skewed, so the charts and tests work on log minutes, with a normality check in the app.
- **Making statistics readable.** We replaced p-values and Ppk on the main screens with plain sentences, such as "Only about 89 in 100 calls within 9 min", and kept the formulas behind "More info".

### Accomplishments that we're proud of

- The tool finds all four planted problems in the demo data, and confirms that Zone D's fix worked.
- The dispatcher needs no statistics: clocks, colours and one-line tips.
- Fully reproducible: one command to run, pinned packages, a seeded data script, and 77 tests.
- Built-in **How to use** and **About** pages, so a new user can learn every feature and statistic inside the app.

### What we learned

- The 90th percentile tells the truth that the average hides.
- A control chart is only as good as its limits, and the limits are only as good as the window you choose.
- Splitting a response into stages turns "it's slow" into "it's the night-shift turnout in Zone D", which someone can act on.
- Writing the spec and the tests before the code made working with an AI agent fast and safe.

### What's next for ERGent

- Connect to a real CAD export, and use the city's official EMS districts instead of our illustrative zones.
- Validate the P2 and P3 targets with Ithaca's EMS agencies (NFPA 1710 sets only P1).
- A shared live board across dispatchers, with logins.
- Test the rules on a year of real data, to tune the false-alarm rate.

---

## Built with (tags)

python, shiny, shiny-for-python, pandas, numpy, scipy, matplotlib, leaflet, pytest, posit-connect, github-actions, statistical-process-control, six-sigma

## "Try it out" links

- GitHub repo: https://github.com/nidhibaderiya23/sixsigma
- Live app: https://connect.systems-apps.com/content/0bfdba33-58e1-4b6e-91c0-17452a4a3a9e/

## Video demo link

**[YouTube or Vimeo link, if you record one: see `demo-video-script.md` in this folder. Devpost accepts the live app link as the demo if no video is required.]**

## Image gallery

Upload the PNGs in [`screenshots/`](screenshots/), in this order:
1. `01_start.png`: the role picker.
2. `02_supervisor.png`: the Charts tab, with the Ithaca map, the control chart and the capability card.
3. `03_actions.png`: the suggested actions and the before/after check.
4. `04_dispatcher.png`: the live board during a shift replay.
5. `05_history.png`: the dispatcher's History tab.
6. `06_how_to_use.png`: the How to use page.
7. `07_about.png`: the About page.

## Team members (add them on Devpost)

Nidhi Baderiya, Zeba Haq, Dhruv Bhandari

## Which prompt / track

On-campus track. Prompt: Health Systems / Emergency Response.
