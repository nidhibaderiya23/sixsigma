# Submission checklist (Sat Oct 17)

Devpost closes at **1 PM ET sharp**; the showcase is 2 to 3 PM. Nothing has been pushed yet, so
GitHub still shows the older commits until you push.

## Morning plan (about 60 minutes)

| When | Who | What |
|---|---|---|
| 8:30 | all | Open each version (see "Run any version" below), pick the one to ship. |
| 9:00 | all | Fill in **About us** (`docs/manual/00-about-us.md`) and rebuild the manual. |
| 9:15 | Nidhi | Merge the chosen version into `main`, push, add the two GitHub secrets, deploy. |
| 9:45 | Nidhi | Put the live URL in `README.md` (section 2) and in Devpost. |
| 10:00 | all | Paste `devpost.md` into Devpost, upload the screenshots, add teammates. **Submit early**; Devpost lets you edit until 1 PM. |
| 10:30 | all | Rehearse the presentation once (see `docs/presentation/`). |

## 1. Run any version

Each version is its own folder (a git worktree) with its own branch:

```bash
cd /Users/nidhibaderiya/sixsigma-v3/app && ./testme.sh
```

Change `v3` to `v2` ... `v7`. Version 1 is the original folder, `/Users/nidhibaderiya/sixsigma`. Every
folder serves on port 8000, so stop one (Ctrl+C) before starting the next. `VERSIONS.md` says what
each version looks like.

## 2. Rebuild the manual after you fill in About us

```bash
cd /Users/nidhibaderiya/sixsigma-v3 && .venv/bin/python docs/manual/build_manual.py
```

The manual is the same in every version; edit it in the version you ship.

## 3. Ship the chosen version (example: version 3)

`main` is still version 1. Every version branch starts from it, so the merge is a fast-forward and
version 1 stays safe under its tag `v1`.

```bash
cd /Users/nidhibaderiya/sixsigma && git merge --ff-only version-3
```

```bash
cd /Users/nidhibaderiya/sixsigma/app && ./manifestme.sh && cd .. && git status --short
```

If `manifestme.sh` changed `app/manifest.json`, commit it. Then push `main`, the version tags, and
(optionally) the version branches so the class can browse them:

```bash
cd /Users/nidhibaderiya/sixsigma && git push origin main
```

```bash
cd /Users/nidhibaderiya/sixsigma && git push origin v1 v2 v3 v4 v5 v6 v7
```

```bash
cd /Users/nidhibaderiya/sixsigma && git push origin ithaca-base version-2 version-3 version-4 version-5 version-6 version-7
```

## 4. Deploy to Posit Connect

1. On GitHub: **Settings, Secrets and variables, Actions, New repository secret**. Add
   `CONNECT_SERVER` and `CONNECT_API_KEY` (handed out at the event). Never put them in a file.
2. The push to `main` starts **Deploy Shiny (Python) app to Posit Connect** (Actions tab). If it ran
   before the secrets existed, click **Run workflow** to start it again.
3. When it is green, copy the app URL from the log (or from Connect), and check it opens.
4. Put the URL in `README.md` at "LIVE URL: (added after deploy)", commit, and push.

## 5. Devpost

- Paste each field from [`devpost.md`](devpost.md).
- Upload the five images from [`screenshots/`](screenshots/).
- Add Zeba and Dhruv as team members. Pick the on-campus track and the Emergency Response prompt.
- Links: the GitHub repo, the live app, the manual PDF.
- Optional video: [`demo-video-script.md`](demo-video-script.md) (2.5 minutes).

## How the repo meets the judging criteria (100 points)

| Criterion | Points | Where it is met |
|---|---|---|
| An effective, working tool | 25 | The live app, `cd app && ./testme.sh`, 77 passing tests, a fresh-clone check per version |
| Valid quality-control analyses | 25 | `app/qc.py`: X̄-S and individuals charts on log times, Western Electric rules, capability (Ppk/Cpk), ANOVA, Welch before/after, stage breakdown. Explained in `docs/manual/04-statistics-explained.md` |
| Scope matches a prompt | 5 | Dispatch-to-on-scene times by zone: README section 1, `docs/six_sigma.md` |
| Clear user and use case | 5 | Supervisor (start of shift) and dispatcher (real time): README section 1, manual chapters 2-3 |
| Minimal, reasonable inputs | 5 | Button presses only; CAD fields the center already has; targets default to NFPA 1710 (README section 5) |
| Clear demonstration with test data | 10 | `demo/README.md` (every number), the live demo, the shift replay, the decks |
| Excellent documentation | 10 | README, `app/README.md` (every function: inputs, formula, known answer), the user manual |
| 2-3 working test datasets | 5 | `data/calls_baseline.csv`, `data/calls_demo.csv`, `data/calls_messy.csv` |
| Codebook and data README | 5 | `data/README.md` |
| Reproducible, public GitHub repo | 5 | Pinned `requirements.txt`, seeded `data/make_data.py`; **push before 1 PM** |

## Last checks before you submit

- [ ] The live URL opens, and both roles work.
- [ ] README section 2 has the live URL.
- [ ] About us is filled in, and the manual PDF is rebuilt.
- [ ] `git status` is clean, and `main` is pushed.
- [ ] Devpost shows "Submitted", not "Draft".
