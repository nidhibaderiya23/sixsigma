# ERGent versions

**Final choice (Oct 17): version 4, "Civic Ithaca".** It is on `main` in `/Users/nidhibaderiya/sixsigma`,
with the last round of team changes on top: the How to use and About tabs (they replace the manual),
a rearranged Charts tab, instant hover text, the Every call chart in plain minutes, distinct stage
colours and a fuller Cpk/Ppk explanation. The other versions are kept, unchanged, in
`/Users/nidhibaderiya/ERGent-versions/` (one folder each, on their own branches and tags).

All versions have the same features, statistics, data and texts; every one passes the same 77 tests.
Versions 2 to 7 add the Ithaca map and the manual to version 1, and differ from each other only in
their look. Each design was made with the impeccable design skill. Nothing is pushed yet.

| Version | Folder | Git | In one line |
|---|---|---|---|
| **v1** | `ERGent-versions/v1` | `version-1`, tag `v1` | The finished app from the third feedback round: dark, an unnamed city, zone tiles. **Frozen.** |
| Ithaca base | `ERGent-versions/base` | `ithaca-base` | v1 + everything below that all versions share, still in v1's look. |
| **v2** | `ERGent-versions/v2` | `version-2`, tag `v2` | **Refined command center**: v1's dark look, done with precision. |
| **v3** | `ERGent-versions/v3` | `version-3`, tag `v3` | **Clinical light** ("The Lab Report"): white and teal, projector-friendly. |
| **v4** | `ERGent-versions/v4` | `version-4`, tag `v4` | **Civic Ithaca**: navy masthead, safety orange for actions. |
| **v5** | `ERGent-versions/v5` | `version-5`, tag `v5` | **Editorial report** ("Cayuga Report"): paper, ink and serif headings. |
| **v6** | `ERGent-versions/v6` | `version-6`, tag `v6` | **Ops console**: dense graphite; the dispatcher board fits one screen. |
| **v7** | `ERGent-versions/v7` | `version-7`, tag `v7` | **Friendly modern** ("The Calm Clinic Board"): soft, rounded, for first-time users. |

## What every version from v2 has (the Ithaca base)

- **Ithaca, NY.** An interactive Leaflet map of Ithaca with six named zones (A West Hill, B Northside &
  Fall Creek, C Cornell & Collegetown, D West End & Southwest, E Downtown & South Hill, F East Hill &
  Belle Sherman). The zones are illustrative, not official EMS districts.
  - Supervisor: zones coloured by health; hover for the reasons; click a zone to chart it.
  - Dispatcher: zones coloured by their worst open call; hover for open calls and free units; click a
    zone to pick it in Log a call.
  - Ithaca in the header, the start page and the dataset names. The map needs the internet.
- **The User Manual** (`docs/manual`, HTML and PDF), opened by a **Manual** link in the header.
  In the final version it is replaced by the in-app How to use and About tabs.
- **Hackathon deliverables** (`docs/deliverables`): the Devpost text, a submission checklist mapped to
  the judging criteria, and a demo video script.
- **Presentation kit** (`docs/presentation`), removed in the final version (the team presents the website).
- **Shortcut links**: `?role=dispatcher`, `?role=supervisor`, `&tab=History`, `&tab=Actions`, `&sim=1`.
- **Fixes:**
  - The Shapiro-Wilk p value is no longer cut off in the normal plot.
  - The map keeps its view while hidden.
  - Every design also fixes v1's overlapping "Just meets the standard" chip.

## The six designs

### v2: Refined command center (dark)
- Near-black blue-slate surfaces in layers; one "Star of Life" EMS blue for actions, kept apart from
  the status colours. (v1's coral was too close to the status red.)
- Atkinson Hyperlegible Next and Mono, made so that 0/O, 1/l/I and B/8 never look alike: good for
  call IDs and unit IDs read under fatigue.
- Sentence-case labels, squared corners, underline tabs, a one-row control bar, and the count tiles
  as one panel.
- Best for: a dark dispatch room, or the closest thing to v1.

### v3: Clinical light ("The Lab Report")
- White cards on a cool grey canvas, a deep-teal header band and one clinical teal.
- **Signature:** like a lab report, values in range print plain; only out-of-range values get a
  tinted flag (amber or red ink on a pale fill).
- Source Sans 3 with fixed-width digits, so running clocks don't jitter.
- Best for: a **classroom projector**; light themes survive washed-out projectors.

### v4: Civic Ithaca (navy and safety orange)
- A navy masthead and tab band, a warm-grey working area, and white panels. Safety orange appears only on
  primary buttons and the logo.
- Status is told apart by **shape as well as colour**: green circle, amber diamond (like a road sign),
  red square, so it also works for colour-blind viewers.
- Zone letters are drawn as navy street-name plates. Barlow Semi Condensed and Public Sans.
- Best for: a city-government look; the strongest identity of the six.

### v5: Editorial report ("Cayuga Report")
- Warm paper, near-black ink and one Cayuga-blue accent, like a printed statistical report.
- Source Serif 4 headings with Public Sans; ruled sections instead of boxed cards; light charts.
- Best for: a professor reading the statistics; the calmest and most "academic" look.

### v6: Ops console (data-dense)
- Graphite panes split by 1 px lines, one cyan signal colour, Barlow Semi Condensed and JetBrains Mono.
- **The whole dispatcher board fits a 1440 x 900 screen** with no page scroll: the lists scroll inside
  their panes. Clocks light up by severity: amber cell for watch, solid red for past target.
- Best for: power users and a live demo where everything should be visible at once.

### v7: Friendly modern ("The Calm Clinic Board")
- Light lake-mist ground, white rounded panels, soft shadows, and one Cayuga-lake blue.
- Figtree with tabular figures; icon tiles on the counts; friendly empty states; large touch targets.
- Best for: first-time and non-expert users; the most approachable look.
- Known nit: at 1440 px the supervisor control bar wraps to a second row.

## Things every version shares (not fixed)
- The PNG charts (the control chart, Every call, before and after, the normal plot) are drawn on the
  server, so their text uses the server's font (DejaVu Sans on Posit Connect), not the page font.
  The SVG charts use the page font.
- On the daily chart, the "action" label touches the upper control-limit line in some designs.

## Run a version

```bash
cd /Users/nidhibaderiya/ERGent-versions/v3/app && ./testme.sh
```

Change `v3` to the version you want (`v1`, `base`, `v2` ... `v7`). The final app runs from
`/Users/nidhibaderiya/sixsigma/app`. Each serves on
http://localhost:8000; stop one with Ctrl+C before starting the next.

## Ship a version

See `docs/deliverables/submission-checklist.md`, section 3. In short, on `main`:
`git merge --ff-only version-N`, re-run `app/manifestme.sh`, commit, and push `main` and the tags.
