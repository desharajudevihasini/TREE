# TREE — Dark Theme Complete Source

This is the working TREE M2 application with a dark cosmic, TreeHacks-inspired frontend. The CSS/HTML frontend is the visual update; the numerical backend has not been replaced.

## Quick start on your Mac
1. Extract the ZIP and open Terminal in the `TREE_Dark_Complete` folder.
2. Run `bash start_mac.sh`.
3. Open the localhost URL printed by the script (default: http://127.0.0.1:8770). Keep Terminal open.
4. If the port is busy: `PORT=8790 bash start_mac.sh` then open http://127.0.0.1:8790.

## Where things live
- `frontend/index.html`: page content / sections (TREE brand).
- `frontend/styles.css`: original layout + illustrations.
- `frontend/dark-theme.css`: the final dark color and rounded-control styling.
- `frontend/app.js`: API calls, button clicks, form logic.
- `backend/main.py`: FastAPI routes.
- `backend/engines/`: scoring, retrofits, simulation, optimization, TreeAsk.
- `backend/companion/`: chat.
- `ml/`: synthetic model and NEED validation script.
- `tests/`: backend tests.
- `deliverables/M2.pdf`: milestone progress report.

## Evidence and limitations
All demo properties and prior high model R-squared values are synthetic. UK NEED real-world benchmark requires the downloaded dataset; no measured real-world accuracy is claimed until the validation script is run. This app is a hackathon prototype, not a certified EPC assessment.

## GitHub
Push all source and `deliverables/M2.pdf` to your existing repository's `main` branch. Do not push `.venv311` or other local virtual environments. Keep GitHub repository information and authentication private.
