# Submission checklist (Sat Oct 17)

Devpost closes at **1 PM ET sharp**. The final app is version 4 ("Civic Ithaca") with the last round
of team changes, on `main` in `/Users/nidhibaderiya/sixsigma`. Everything is committed locally;
**nothing is pushed yet**.

## Before you submit (review)

- [ ] Run the app and click through both roles, How to use and About:
      `cd /Users/nidhibaderiya/sixsigma/app && ./testme.sh`, then http://localhost:8000.
- [ ] Fill in the three "Role and program: to be added" lines on the About page (`app/ui_help.py`).
- [ ] Read `devpost.md` and fill in its **[square brackets]**.

## Push and deploy

1. Push `main` and the version tags (the other versions stay on their own branches):

```bash
cd /Users/nidhibaderiya/sixsigma && git push origin main
```

```bash
cd /Users/nidhibaderiya/sixsigma && git push origin v1 v2 v3 v4 v5 v6 v7
```

2. On GitHub: **Settings, Secrets and variables, Actions, New repository secret**. Add
   `CONNECT_SERVER` and `CONNECT_API_KEY` (from the event). Never put them in a file.
3. The push starts **Deploy Shiny (Python) app to Posit Connect** (Actions tab). If it ran before the
   secrets existed, click **Run workflow**. When it is green, open the app URL from the log.
4. Done: the live app is https://connect.systems-apps.com/content/0bfdba33-58e1-4b6e-91c0-17452a4a3a9e/ (in `README.md` and `devpost.md`). In Posit Connect, set Settings → Access to "Anyone - no login required".

## Devpost

- Paste the fields from [`devpost.md`](devpost.md).
- Upload the seven images in [`screenshots/`](screenshots/), in their numbered order.
- Add Zeba and Dhruv as team members; on-campus track; Emergency Response prompt.
- Links: the GitHub repo and the live app. A video is optional ([`demo-video-script.md`](demo-video-script.md)).
- Make sure it says **Submitted**, not Draft.

## How the repo meets the judging criteria (100 points)

| Criterion | Points | Where it is met |
|---|---|---|
| An effective, working tool | 25 | The live app; `cd app && ./testme.sh`; 77 passing tests; a fresh-clone check |
| Valid quality-control analyses | 25 | `app/qc.py`: X̄-S and individuals charts, Western Electric rules, capability (Ppk/Cpk), ANOVA, Welch before/after, stage breakdown |
| Scope matches a prompt | 5 | Dispatch-to-on-scene times by zone: README section 1, `docs/six_sigma.md` |
| Clear user and use case | 5 | Supervisor (start of shift) and dispatcher (real time); the app's About page |
| Minimal, reasonable inputs | 5 | Button presses only; the dispatch system's own fields; NFPA 1710 targets by default |
| Clear demonstration with test data | 10 | `demo/README.md` (every number), the shift replay, the How to use page |
| Excellent documentation | 10 | README, `app/README.md` (every function: inputs, formula, known answer), the in-app How to use page |
| 2-3 working test datasets | 5 | `data/calls_baseline.csv`, `data/calls_demo.csv`, `data/calls_messy.csv` |
| Codebook and data README | 5 | `data/README.md` |
| Reproducible, public GitHub repo | 5 | Pinned `requirements.txt`, seeded `data/make_data.py`; **push before 1 PM** |
