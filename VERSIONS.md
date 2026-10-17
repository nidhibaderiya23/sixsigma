# ERGent versions

Every version has the same features, statistics and data. Versions 2 to 7 differ from version 1 by
the Ithaca map and the manual, and from each other only by their look. Nothing is pushed yet.

| Version | Where it lives | Git | What is in it |
|---|---|---|---|
| **v1** | `/Users/nidhibaderiya/sixsigma` (the original folder) | branch `main`, tag `v1` | The app as finished on Oct 17 after the third round of team feedback: a dark "command center" look, an unnamed city, and a 3 x 2 grid of zone tiles. **Frozen: never changed.** |
| Ithaca base | `/Users/nidhibaderiya/sixsigma-base` | branch `ithaca-base` | v1 plus: the **interactive Ithaca, NY map** (6 named zones; hover for reasons, click to pick a zone) on both views; Ithaca names in the header, start page and datasets; the **User Manual** (`docs/manual`, About us page first, a template); the **hackathon deliverables** (`docs/deliverables`); the **presentation kit** (`docs/presentation`); links that open a view directly (`?role=supervisor`). Same dark look as v1. Every version below starts from here. |
| **v2** | `/Users/nidhibaderiya/sixsigma-v2` | branch `version-2`, tag `v2` | Ithaca base + design **"Refined command center"** (dark). *Details added after review.* |
| **v3** | `/Users/nidhibaderiya/sixsigma-v3` | branch `version-3`, tag `v3` | Ithaca base + design **"Clinical light"**. *Details added after review.* |
| **v4** | `/Users/nidhibaderiya/sixsigma-v4` | branch `version-4`, tag `v4` | Ithaca base + design **"Civic Ithaca"** (navy and safety orange). *Details added after review.* |
| **v5** | `/Users/nidhibaderiya/sixsigma-v5` | branch `version-5`, tag `v5` | Ithaca base + design **"Editorial report"**. *Details added after review.* |
| **v6** | `/Users/nidhibaderiya/sixsigma-v6` | branch `version-6`, tag `v6` | Ithaca base + design **"Ops console"** (data-dense). *Details added after review.* |
| **v7** | `/Users/nidhibaderiya/sixsigma-v7` | branch `version-7`, tag `v7` | Ithaca base + design **"Friendly modern"**. *Details added after review.* |

## Run a version

```bash
cd /Users/nidhibaderiya/sixsigma-v3/app && ./testme.sh
```

Change `v3` to the version you want (`sixsigma` for v1, `sixsigma-base` for the Ithaca base). Each
serves on http://localhost:8000; stop one with Ctrl+C before starting another.

## Ship a version

See `docs/deliverables/submission-checklist.md`, section 3. In short: on `main`, run
`git merge --ff-only version-N`, re-run `app/manifestme.sh`, commit, and push `main` and the tags.
