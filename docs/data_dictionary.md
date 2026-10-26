# Schema, synthetic dataset generation, labels

`backend/schemas.py` is authoritative. `backend/demo.py` declares 12 entirely fictional UK demonstration homes. They are neither EPC retrievals nor actual customer properties; fake postcodes and personal data are intentionally not included.

- `property_id`: non-personal synthetic reference key.
- `property_type`: detached/semi_detached/terraced/flat/bungalow.
- `floor_area_m2`: positive floor area.
- `epc_rating`: A–G optional existing record representation.
- `heating_type`: gas_boiler/heat_pump/electric_resistance/district/unknown.
- `loft_insulated`, `wall_insulated`, `smart_controls`, `roof_suitable`, `outdoor_space`: true/false/unknown.
- `glazing`: single/double/triple/unknown.
- `annual_electricity_kwh`: annual **grid-import** electricity reference (not total demand when solar already exists).
- `annual_gas_kwh`: annual purchased gas reference.
- `baseline_source`: `synthetic_demo` (for demo fixtures); `synthetic_trained_ml` or `estimated_heuristic` for unknown-input fallbacks.
- `solar_kwp`: recorded installed solar generation capacity, not a measured annual kWh value.
- `property_value_gbp`: synthetic property-value input.
- `electricity_price_gbp_kwh`, `gas_price_gbp_kwh`: illustrative unit prices.
- `budget_gbp`: available upfront budget.

## Synthetic ML generator (`ml/train.py`)

Creates 900 independently sampled homes with randomized property types, area, region, heating, insulation, solar, glazing and controls. Synthetic gas/electricity labels are constructed using a documented heating-demand formula, conversion by heating type, photovoltaic adjustment and Gaussian noise. No observed customer records or real UK NEED rows are in the dataset.

**Train**: 720 rows. **Held-out test**: 180 rows, split with seed 42. RandomForest model target labels separately for `annual_electricity_kwh`, `annual_gas_kwh`. `DummyRegressor` median baseline comparison.

The synthetic `annual_electricity_kwh` and `annual_gas_kwh` labels are **model-defined**. Measured holdout metrics indicate recovery of the generator's pattern, not generalizable real-world ML quality. No data from test split is used to train.

`evaluation/held_out_predictions_SYNTHETIC_ONLY.csv` columns:
- `synthetic_test_row`: stable sampled synthetic row reference.
- `true_annual_electricity_kwh`: synthetic label.
- `pred_annual_electricity_kwh`: model prediction on held-out sample.
- `true_annual_gas_kwh`: synthetic label.
- `pred_annual_gas_kwh`: model prediction on held-out sample.

The retrofit simulation has no supervised target labels from observed installations; it is deterministic and evaluated by scenario/unit tests, not a spurious computed "accuracy" metric.

## Public UK NEED 2026 observed-data model schema

Raw source: `data/public/anon2026_50k.csv` (OGL attribution in `data/public/SOURCE_AND_LICENSE.md`). `ml/need_challenger.py` documents exact inference features:

- Categorical predictors: `PROP_TYPE`, `PROP_AGE_BAND`, `FLOOR_AREA_BAND`, `REGION`, `MAIN_HEAT_FUEL`, `CONSERVATORY_FLAG`, `COUNCIL_TAX_BAND`, `EPC`, `LI_FLAG`, `CWI_FLAG`, `PV_FLAG`.
- Prediction targets: electricity `Econs2024`, gas `Gcons2024`, only valid flag `ElecValFlag2024 == 'V'` / `GasValFlag2024 == 'V'` and nonnegative numeric readings.
- Optional longitudinal predictors: `Econs2023` / `Gcons2023` if valid 2023 flags are present; note copy-last-year baseline is stronger on MAE than ML for both longitudinal tasks.
- Saved research models: `ml/models/need_2026/electricity.joblib`, `gas.joblib`; official category manifest with `allowed_values` in `ml/models/need_2026/manifest.json`.
- Outputs: `electricity_kwh_per_year`, `gas_kwh_per_year`; **not** per-address official EPC estimates.
- Train/validation/test: 60/20/20 with seed 42. Official 2026 *release* includes 2024 latest consumption labels, not 2026 measured consumption.
- Held-out row evidence: `evaluation/need_challenger_predictions.csv` and `evaluation/need_held_out_predictions.csv`. Slice analysis in `evaluation/need_slice_analysis.json`.

Categorical coding should be interpreted using the official DESNZ NEED 2026 metadata rather than guessed from consumer free text. TREE requires the exact official category values for research predictions; no unverified postcode or square-metre-to-band mapping is silently applied.
