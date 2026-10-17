# Demo video script (about 2.5 minutes)

Record the screen with QuickTime (File, New Screen Recording) at 1440 x 900 or larger, with the app
open in Chrome. One person narrates. Upload to YouTube as **Unlisted** and paste the link in Devpost.

Before you record:
- Open the live app (or run it locally: `cd app && ./testme.sh`, then http://localhost:8000).
- Zoom the browser to 110%, so text reads well on video.
- Have two tabs ready: `http://localhost:8000/?role=supervisor` and `http://localhost:8000/?role=dispatcher`.

| Time | Screen | Say |
|---|---|---|
| 0:00-0:15 | Start page | "Ithaca's 911 center reports a monthly average. But an average of 9.2 minutes can hide a patient who waited 20. ERGent shows where, why and since when." |
| 0:15-0:30 | Click **I'm a supervisor** | "A supervisor opens ERGent at the start of a shift. The map shows Ithaca's six zones, coloured by health." |
| 0:30-0:50 | Set **As of** to 2026-09-28. Hover **Zone D** on the map | "On September 28, Zone D, West End and Southwest, is amber. Its 90th percentile is 10.2 minutes against a 9-minute target, and the main delay is crew turnout, not the drive." |
| 0:50-1:05 | Scroll to **Delay by stage** and **Capability** | "Delay by stage confirms it: 92% of Zone D's minutes over target come from turnout. Capability says only about 89 in 100 calls arrive within 9 minutes." |
| 1:05-1:25 | **Actions** tab | "ERGent suggests a fix with its evidence: review crew readiness at Zone D's station, especially the night shift. Estimated on time: 78% to 97%. We log the action." |
| 1:25-1:45 | Back to **Charts**, set **As of** to 2026-10-12, then **Actions**, Result | "Two weeks later, the before-and-after check says Improved: on time went from 78% to 97%, and Welch's t-test says this is not chance. ERGent keeps watching for a slip back." |
| 1:45-2:15 | Dispatcher tab: **Simulate a shift** at 120x | "The dispatcher sees the same story live. Every call has running clocks that turn amber, then red. The Ithaca map colours each zone by its worst open call, and a late stage needs a reason code: mistake-proofing at the source." |
| 2:15-2:30 | **History** tab, hover a red diamond | "History compares zones in the current shift, and suggests what to do now. ERGent flags and suggests; qualified staff decide. Thank you." |

Keep it under 3 minutes. If a step goes wrong, stop and record that part again; you can cut the clips
together in iMovie.
