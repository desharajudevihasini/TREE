# TREE — explanation for judges (start here)

## What is TREE?
TREE helps a homeowner understand the green-energy state of their home, choose realistic retrofits, and compare the costs, carbon impact and energy use of alternative futures. It is a **decision-support prototype**, not a certified EPC tool.

## Five files to understand first
1. `frontend/index.html`: visible TREE page, feature buttons, dashboard layout.
2. `frontend/styles.css`: TreeHacks-inspired illustrated atmosphere, circular navigation and pill buttons.
3. `frontend/app.js`: events, calls to the API, live result rendering. Search `renderDashboard`, `openView`, and `renderEvaluation`.
4. `backend/main.py`: route definitions; maps the frontend requests to the calculation functions.
5. `backend/engines/scoring.py`, `retrofit.py`, `optimizer.py`: 7-weight scoring; per-fuel scenario recomputation; find feasible package in budget.

## Real-data validation — precise meaning
Run `bash validate_real_mac.sh /absolute/path/to/official_need.csv` after downloading the official NEED 2026 50k dataset. This trains a **separate** Random Forest on observed NEED energy-consumption records and compares it to a median baseline on held-out NEED rows. The original demonstration Random Forest is trained on synthetic property data; the NEED experiment **does not independently validate that original model**. Do not say it does.

Mean absolute error (MAE) and root mean squared error (RMSE) use kWh/year. R² is explained variance, not accuracy %. No official real-data result exists until the validation is run with the actual CSV.

## What differentiates TREE?
- **TreeAsk**: check whether an answer to a property question changes a feasible recommendation. Show a yes-vs-no example and its impact.
- **Package-based model**: heat pumps increase electricity and reduce gas; solar reduces purchased grid electricity; recalculate packages rather than add isolated savings.
- **Budget optimizer**: checks feasible combinations within a homeowner budget.
- **Honest evidence**: synthetic/observed data and engineering assumptions are labelled.

## Two-person, 3-minute pitch
- Person A (30 sec): the pain point, house and quick demo.
- Person A (60 sec): score and selecting 2 upgrades; show new cost and carbon.
- Person B (45 sec): budget optimizer and TreeAsk/alternate future.
- Person B (30 sec): explain Random Forest and difference between synthetic and observed benchmark.
- Both (15 sec): explain limitations and next step: real UK EPC + meter data validation / field study.

## Four tough judge questions
**Why use ML?** Predict modelled energy consumption from property features; transparent engineering rules still control retrofit eligibility and numeric cost/carbon accounting.
**Why not call it 99% accurate?** R² on synthetic data measures explained variance on that synthetic distribution, not real-world household accuracy.
**What if input data are missing?** TREE flags assumptions, asks a decision-relevant question, and should avoid unjustified certainty.
**How do you validate retrofit savings?** Current prototype only verifies code invariants. Real-world savings require measured before/after homes, weather adjustment, comparable controls, and documented provenance.

## Start on a Mac
`bash start_mac.sh` then visit the printed URL. Use another port with `PORT=8791 bash start_mac.sh` if the default is occupied.
