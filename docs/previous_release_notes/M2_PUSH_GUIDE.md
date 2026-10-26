# TREE M2 - final submission steps

**Deadline:** 11 October 2026, 4:00 AM IST

The M2 report is already at `deliverables/M2.pdf` in this package.
It is exactly two pages.

## 1. In your EXISTING cloned GitHub repository

Keep the repository's `.git` folder. Copy the files and folders from this `TREE_M2_READY` folder **into the repository root**, including the `deliverables` folder (not as a nested second project).

In Terminal, change directory to **that GitHub repository** (not the Downloads folder), then run:

```bash
git status
git branch --show-current
# Expected branch: main. If you are on another branch, check with your teammate before switching.
git add -A
git status
git commit -m "M2: TREE prototype, validation scripts, tests and progress report"
git push origin main
```

If git says "nothing to commit" because everything is already committed, use `git push origin main`. If `git push` is rejected, **do not force-push**; fetch and reconcile the remote commits.

## 2. Verify upload

Open the GitHub repository's `main` branch in your browser. Check that these exist:

- `deliverables/M2.pdf` (2 pages)
- `backend/main.py`, `backend/engines/`
- `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
- `ml/train.py`, `ml/validate_need.py`, `ml/models/`
- `tests/`, `evaluation/`, `README.md`

## 3. Reported evidence (do not overstate)

- All 17 unit/API tests passed locally in the preparation environment.
- Seven HTTP smoke requests passed locally via FastAPI TestClient.
- Synthetic ML development split: 720 training / 180 held-out from 900 generated records.
- No official UK NEED result is claimed. `ml/validate_need.py` is provided but needs the official downloaded dataset.
- A full Mac browser walkthrough is still recommended.

## 4. Reproduce checks

```bash
python -m pytest -q
node --check frontend/app.js
```

Run them from the repository root in the Python 3.11 virtual environment. If tests cannot resolve `backend`, run `PYTHONPATH=. python -m pytest -q`.
