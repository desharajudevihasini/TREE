# TREE — Engineering release and evidence checklist

## What works
- Dark existing UI preserved; custom property input is available without editing code.
- Existing score, recommendation, budget, TreeAsk and scenario APIs.
- New-data ML test now reports held-out MAE/RMSE/R², **training-only median baseline**, and out-of-training-range or unseen-category warnings.
-  Synthetic TreeAsk experiment remains clearly labelled as a simulation.

## Run on Mac
`bash start_mac.sh`

## Test on completely new rows
`python -m ml.evaluate_new_data --csv data/new_homes_example_SYNTHETIC.csv`

For your own data, use `ml/NEW_DATA_GUIDE.md` and make a CSV with the same columns. Add actual annual electricity/gas labels to calculate prediction errors. Never put actual household names or addresses in this dataset.

## Important: remaining gaps
- Official live EPC API lookup is **not implemented**. Do not equate GPS coordinates with verified home EPC records. Real property matching requires postcode/address plus selection/confirmation and a working authorized data service.
- Actual NEED data has **not been provided or validated**. `python -m ml.validate_need --csv /path/to/official_need.csv` is an available, separate real-data benchmark and does not directly validate the original synthetic-trained model.
- No real-world ML accuracy can be claimed yet; the example CSV is synthetic.
- Energy savings, carbon and value uplift are estimates with documented assumptions, not certified results.
- UX was intentionally preserved for your requested final design pass.

## Learning order
`backend/schemas.py` (inputs) → `ml/predict.py` (missing consumption) → `backend/engines/scoring.py` (score) → `backend/engines/retrofit.py` (measure effects) → `backend/engines/optimizer.py` (budget choice) → `backend/engines/treeask.py` (question selection) → `backend/main.py` (API) → `frontend/app.js` (screen).
