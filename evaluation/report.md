# TREE — complete validation record (Lloyds PS2)

**Scope:** These are research / demonstration results, **not a claims audit of real installed retrofits**.

## Three distinct evidence tiers

1. **Synthetic homeowner fallback:** 900 fictional simulator-labelled records from `ml/train.py`, reproducible seed 42, saved sklearn pipelines. Synthetic R² ≈0.985 electricity and 0.991 gas only reflects simulator distributions.
2. **Observed NEED 2026 independent baseline:** Test on 50k public anonymised UK records with valid 2024 fuel consumption. A separate random forest achieved electricity test MAE 1698.51 kWh and R² 0.1309; gas MAE 4039.10 kWh and R² 0.3110. See `need_real_validation.json` and `need_held_out_predictions.csv`.
3. **Observed NEED 2026 challenger model selection:** Heldout 60/20/20 train / validation / test split, train seed 42 and candidate ridge / extra-trees / histogram gradient boosting. Best by validation MAE; final model fits training+validation and touches held-out test once. Raw NEED categories only; household-level external observed data not a verified EPC/address join. See `need_challenger_report.json` and `need_challenger_predictions.csv`.

## Actual held-out model results

| Research model | Test n | MAE | RMSE | R² | Median MAE | Prior-year copy MAE |
|---|---:|---:|---:|---:|---:|---:|
| Electricity, property only | 9043 | 1673.20 | 2459.04 | 0.1606 | 1706.83 | N/A |
| Gas, property only | 7438 | 3928.82 | 5401.82 | 0.3367 | 4862.34 | N/A |
| Electricity, with prior-year use | 8557 | 908.02 | 1598.08 | 0.6358 | 1688.49 | **885.98** |
| Gas, with prior-year use | 7099 | 1752.45 | 2966.62 | 0.8039 | 4883.21 | **1725.98** |

> The prior-year copy baseline is **better than the ML models on MAE** in both longitudinal tasks. The benchmark does not make the consumer synthetic-trained model accurate on real UK homes. All table values are recorded in the JSON source report.

## Error-slice audit

`evaluation/need_slice_analysis.json` reconstructs the untouched property-only holdout indices (same seed and valid meter flags) and merges recorded absolute errors. It reports MAE and 90th-percentile absolute error for property type, region and EPC groups with at least 50 test records. Group errors are descriptive; **not** a fairness result or a statistical prediction interval. No post-hoc model fitting used test outcome differences.

## Adversarial / robustness suite

Run `python -m pytest -q` and `python -m evaluation.judge_prompt_suite`. Cases cover missing and inconsistent attributes; infeasible or duplicate upgrades; solar grid imports vs underlying demand; negative electricity savings after heat pump; multiplicative package interactions; score bands/weights; zero purchased energy; annual cost / carbon signs; tariff-only and composite what-ifs; source-bounded dialogue; local customer memory and erase; and usable served routes.

## Remaining research work

- Validate *existing consumer* energy prediction with a defensible mapping from homeowner inputs to official NEED columns (do not invent categorical codes).
- Train and validate retrofit outcome model on actual pre/post matched treatment and comparator data, or import verified simulation/survey coefficients. The official NEED impact report uses control groups, but we have not recalibrated our specific multipliers.
- Official 2026 DESNZ electricity/gas reporting factors with exact scope, gas calorific basis, units and version; current defaults are illustrative.
- Predict home price range with licensed, linked historical transactions, controls for market date/location/property size and EPC. Current uplift range is only a disclosed sensitivity example.
- Independently run and annotate Gemini responses for organiser ≥90% groundedness/accuracy and <5% unsupported claims.

## Primary research source and licence

- https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-anonymised-data-2026
- https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026-accessible-webpage
- https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026
- Attribution: Contains public sector information licensed under OGL v3.0.
