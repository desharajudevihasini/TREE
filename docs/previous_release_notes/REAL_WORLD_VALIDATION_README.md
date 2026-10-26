# TREE — Real UK NEED Validation (drop-in code)

This is the no-3D TREE illustrated website with an optional independent real-data ML benchmark.

## Run the website on your Mac

```bash
bash start_mac.sh
```

## Run a REAL UK energy-consumption benchmark

1. Download the **2026 50,000-row CSV** from:
   https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-anonymised-data-2026
2. Open Terminal inside this extracted TREE project folder.
3. Run:

```bash
bash validate_real_mac.sh ~/Downloads/anon2026_50k.csv
```

If your downloaded CSV has a different filename, supply its exact path (drag it into Terminal after the space).

## Where the results appear

- `evaluation/need_real_validation.json`: authentic held-out results, once the dataset has been supplied.
- `evaluation/need_held_out_predictions.csv`: actual-versus-predicted values for held-out homes.
- In the website, open **Our Methods** → **Observed UK household benchmark** and refresh the page.

### Explain honestly to judges

- This trains an **independent Random Forest benchmark using real NEED features**. It **does not** validate the original synthetic-trained model directly, because the official dataset does not contain the same input columns.
- Metrics: **MAE**, **RMSE**, **R²** separately for electricity and gas. An R² of 0.8 is not “80% accuracy.”
- Only observed consumption values with official `V` flags are eligible as labels.
- 80% training / 20% held-out testing per fuel, split with seed 42.
- Data is stored only on your computer. We don't include or fabricate the government dataset or benchmark results in the ZIP.
- Property columns are anonymised / banded. The findings do not validate retrofit savings, bill savings, home valuation, or the Green Home Score.

The rest of TREE remains a prototype using synthetic demonstration property data.
