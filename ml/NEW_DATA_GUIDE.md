# TREE: How to test with DIFFERENT data

## Two different experiments

**A. Try another house (in the website):** Open **Home Lab > Try a different home**, enter the building details, then press **Use these home details**. If you know the actual annual electricity/gas kWh, enter them. If you leave either blank, the system predicts the missing consumption using the saved synthetic-trained Random Forest. This is *inference*, not an accuracy measurement.

**B. Validate the model on unseen labelled homes (in Terminal):** Create a CSV where each row represents a different home and where the annual electricity and gas kWh are known. The test program loads the SAVED models, without retraining them, and computes MAE, RMSE and R². It refuses rows identical to the original synthetic dataset.

Example command, from the project root after activating Python:

```bash
python -m ml.evaluate_new_data --csv data/new_homes_example_SYNTHETIC.csv
```

Results: `evaluation/new_data_report.json` and `evaluation/new_data_predictions.csv`.

## Required CSV columns

The 9 predictor columns are:

`floor_area_m2, loft_insulated, wall_insulated, smart_controls, solar_kwp, property_type, heating_type, region, glazing`

Use 1/0 or yes/no for the three insulation/control flags, a positive numeric floor area, nonnegative solar kWp, and the appropriate categories (e.g. property_type=terraced, heating_type=gas_boiler). Optional measured outcome columns to compute error:

`annual_electricity_kwh, annual_gas_kwh`

If those outcome columns are absent, TREE produces forecasts but **cannot measure accuracy**. Model accuracy requires observed labels. New home rows must not duplicate training data.

**The bundled example CSV is also SYNTHETIC.** It only proves the code path works. A successful run is not a real-world validation result.

## Can we test on real UK households?

Yes, with lawful, compatible measured data and a careful data dictionary. **UK NEED** fields are not the same as the nine TREE synthetic-model inputs, so don't force a fake direct comparison. The separate command:

```bash
python -m ml.validate_need --csv /path/to/official_need_2026.csv
```

trains and evaluates a DIFFERENT model on UK NEED's available categories and observed consumption. Use the official source and metadata, report the random holdout and its limitations, and state explicitly that this does not validate the original synthetic-trained model. Neither experiment proves predicted retrofit savings.

## Understand the model in 40 seconds

1. `ml/train.py` generated 900 fictional homes with nine property features and simulated energy readings.
2. 720 examples trained two Random Forest regressors; 180 were held out for the benchmark.
3. `ml/predict.py` loads the saved regressors and predicts missing annual electricity/gas demand.
4. `backend/engines/baseline.py` uses actual supplied values when present and predicts missing ones.
5. `ml/evaluate_new_data.py` tests the saved model against an independent labelled CSV without fitting again.
