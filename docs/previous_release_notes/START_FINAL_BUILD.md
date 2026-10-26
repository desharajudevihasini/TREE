# TREE — Final engineering challenger (UX unchanged)

## Mac launch

```bash
cd ~/Downloads/TREE_97_Engineering
bash start_mac.sh
```

Use the URL printed by the server. Open a second Terminal for tests:

```bash
cd ~/Downloads/TREE_97_Engineering
source .venv/bin/activate
python -m pytest -q
```

## Real UK evidence

The included `evaluation/need_challenger_report.json` is computed from the user's official UK NEED 2026 anonymised 50,000-row CSV. `evaluation/need_challenger_predictions.csv` contains held-out prediction errors. Reproduce with:

```bash
python -m ml.need_challenger --csv ~/Downloads/anon2026_50k.csv
```

Three candidate regressors (Ridge, ExtraTrees, HistGradientBoosting) are selected on a validation split, then assessed once on an untouched test split. The model uses only property descriptors in **property-only** mode; **with-prior-year-bill** uses the previous year's consumption and requires that reading. The two modes answer different questions.

- Property-only electricity MAE 1,673.20 kWh/year; gas 3,928.82 kWh/year.
- With-prior-year-bill electricity MAE 908.02 kWh/year; gas 1,752.45 kWh/year.

**Important:** This challenger is a separately trained real-data benchmark. TREE's existing `/api/predict` route and production estimates have **not** been switched to this model: NEED provides coarse categorical bands that are not a one-to-one match for the app's property schema. No fabricated conversion or inference bridge was inserted. The challenger does **not** validate retrofit savings, valuation, carbon forecasts, Green Home Score, or live EPC access. Do not describe it as 98% accurate.

New API: `/api/evaluation/need-challenger`. Existing dark UX remains unchanged.

## What to say to judges

"We initially built a synthetic-data pipeline to test our architecture. Then we challenged our approach against 50,000 anonymised UK homes. Our first property-only benchmark had limited explanatory power. We compared multiple algorithms on validation data and evaluated the winner on held-out records. Adding a known previous-year bill significantly improved consumption estimates. We show both modes transparently, because homes with no historical bill are a harder prediction problem."
