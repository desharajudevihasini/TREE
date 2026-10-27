"""Test saved TREE Random Forests on a NEW, schema-compatible CSV.

This does NOT retrain either model. To measure prediction error, the CSV must
contain ground-truth electricity and gas consumption that the model never saw.

Usage: python -m ml.evaluate_new_data --csv data/new_homes_example_SYNTHETIC.csv
For actual UK NEED data use the separate ml.validate_need workflow; the schemas differ.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
from ml.train import FEATURES, CATS, NUMS

TARGETS = ("annual_electricity_kwh", "annual_gas_kwh")
BOOL_FIELDS = ("loft_insulated", "wall_insulated", "smart_controls")


def prepare(csv_path: Path):
    if not csv_path.is_file():
        raise FileNotFoundError(f"File not found: {csv_path}")
    if csv_path.stat().st_size > 20_000_000:
        raise ValueError("Use a CSV smaller than 20 MB for this simple testing script.")
    df = pd.read_csv(csv_path, low_memory=False)
    missing = [column for column in FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. See ml/NEW_DATA_GUIDE.md")
    if len(df) == 0:
        raise ValueError("Empty CSV.")

    for name in BOOL_FIELDS:
        mapped = (df[name].astype(str).str.strip().str.lower()
                  .replace({"yes": "1", "true": "1", "no": "0", "false": "0"}))
        df[name] = pd.to_numeric(mapped, errors="coerce")
    for name in ("floor_area_m2", "solar_kwp"):
        df[name] = pd.to_numeric(df[name], errors="coerce")
    for name in CATS:
        df[name] = df[name].fillna("Unknown").astype(str)
    if df[NUMS].isna().any().any() or (df["floor_area_m2"] <= 0).any() or (df["solar_kwp"] < 0).any():
        raise ValueError("Invalid or missing numeric features (floor area, insulation flags, solar, smart controls).")

    # Detect accidental reuse of the same training/demonstration records.
    original = ROOT / "data/demo/synthetic_training_data.csv"
    if original.exists():
        seen = pd.read_csv(original, usecols=FEATURES)
        overlap = df[FEATURES].merge(seen.drop_duplicates(), on=FEATURES, how="inner")
        if len(overlap):
            raise ValueError(f"{len(overlap)} rows overlap the existing synthetic dataset. "
                             "Use NEW homes; re-testing existing benchmark rows isn't new validation.")
    return df


def evaluate_new_data(csv_path: Path, *, output_dir: Path | None = None):
    df = prepare(csv_path)
    output_dir = output_dir or (ROOT / "evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {
        "model": "original_RF_models_trained_on_synthetic_examples",
        "dataset": str(csv_path),
        "rows_predicted": int(len(df)),
        "real_world_validated": False,
        "data_source_verified": False,
        "warning": "This script does not authenticate source records. Results on illustrative CSVs are NOT real-world validation.",
        "targets": {},
    }
    predictions = pd.DataFrame({"input_row": range(len(df))})
    training_file = ROOT / "data/demo/synthetic_training_data.csv"
    training = pd.read_csv(training_file) if training_file.exists() else None
    shifts = []
    if training is not None:
        for col in NUMS:
            low, high = float(training[col].min()), float(training[col].max())
            outside = int(((df[col] < low) | (df[col] > high)).sum())
            if outside:
                shifts.append({"feature": col, "outside_training_range": outside,
                               "training_min": low, "training_max": high})
        for col in CATS:
            unseen = sorted(set(df[col].astype(str)) - set(training[col].astype(str)))
            if unseen:
                shifts.append({"feature": col, "unseen_categories": unseen})
    results["input_shift_warnings"] = shifts
    results["limitations"] = "Input-shift checks are not uncertainty estimates; supplied labels and their provenance must be independently verified."
    for target in TARGETS:
        model_path = ROOT / "ml" / "models" / f"{target}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing trained model: {model_path}. Run python -m ml.train")
        model = joblib.load(model_path)  # Only load trusted models bundled with TREE.
        estimated = np.maximum(0, model.predict(df[FEATURES]))
        predictions[f"predicted_{target}"] = np.round(estimated, 2)
        result = {"tested_on_labeled_rows": 0, "status": "predictions_only_no_ground_truth"}
        if target in df:
            actual = pd.to_numeric(df[target], errors="coerce")
            valid = actual.notna() & actual.ge(0)
            n = int(valid.sum())
            if n:
                predictions[f"observed_{target}"] = actual
                naive_mae = None
                if training is not None and target in training:
                    naive_mae = round(float(mean_absolute_error(actual[valid],
                        np.full(n, float(training[target].median())))), 2)
                result = {"tested_on_labeled_rows": n,
                          "training_median_baseline_mae_kwh_per_year": naive_mae,
                          "mae_kwh_per_year": round(float(mean_absolute_error(actual[valid], estimated[valid])), 2),
                          "rmse_kwh_per_year": round(float(np.sqrt(mean_squared_error(actual[valid], estimated[valid]))), 2),
                          "r2": round(float(r2_score(actual[valid], estimated[valid])), 4) if n >= 2 else None,
                          "status": "measured_against_supplied_labels_source_not_independently_verified"}
        results["targets"][target] = result
    (output_dir / "new_data_report.json").write_text(json.dumps(results, indent=2))
    predictions.to_csv(output_dir / "new_data_predictions.csv", index=False)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path, help="CSV with the ML's nine input features")
    args = parser.parse_args()
    print(json.dumps(evaluate_new_data(args.csv.expanduser()), indent=2))
