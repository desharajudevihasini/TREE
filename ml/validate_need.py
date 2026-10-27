"""TREE: evaluate an independent model using observed UK NEED 2026 consumption data.

This does NOT measure the existing synthetic-trained model's accuracy.
It trains a separate model on NEED-compatible input features and evaluates it on
untouched UK household records. We do not substitute missing values with synthetic labels.

Run in the project directory:
    python -m ml.validate_need --csv ~/Downloads/anon2026_50k.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-anonymised-data-2026"
YEAR = 2024
# Static descriptors present in NEED. Avoid timestamp-sensitive retrofit flags,
# prior consumption, and the target itself to reduce leakage.
FEATURES = ["PROP_TYPE", "PROP_AGE_BAND", "FLOOR_AREA_BAND", "REGION", "MAIN_HEAT_FUEL"]
TARGETS = {
    "electricity": ("Econs2024", "ElecValFlag2024"),
    "gas": ("Gcons2024", "GasValFlag2024"),
}


def load_need(csv_path: Path) -> pd.DataFrame:
    """Keep official column values as categories; no guessed floor-area conversion."""
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}\n"
            f"Download the official 50,000-row CSV from {SOURCE}."
        )
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    required = FEATURES + [column for cols in TARGETS.values() for column in cols]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing NEED columns: {missing}. Check the 2026 50k CSV.")
    return df


def metrics(actual, predicted):
    """All energy errors in kWh/year. R² is not an accuracy percentage."""
    return {
        "mae_kwh_per_year": round(float(mean_absolute_error(actual, predicted)), 2),
        "rmse_kwh_per_year": round(float(np.sqrt(mean_squared_error(actual, predicted))), 2),
        "r2": round(float(r2_score(actual, predicted)), 4),
    }


def evaluate_fuel(data: pd.DataFrame, fuel: str, max_rows: int):
    consumption, flag = TARGETS[fuel]
    # Official valid-consumption code: V. Other flags are not ground truth.
    valid = data[flag].fillna("").str.strip().eq("V")
    readings = pd.to_numeric(data[consumption], errors="coerce")
    eligible = data.loc[valid & readings.notna() & readings.ge(0), FEATURES].copy()
    eligible["actual_kwh"] = readings.loc[eligible.index].astype(float)
    count_before_sample = len(eligible)

    if max_rows > 0 and len(eligible) > max_rows:
        eligible = eligible.sample(n=max_rows, random_state=42)
    if len(eligible) < 100:
        raise ValueError(f"Only {len(eligible)} valid {fuel} readings. Cannot evaluate.")

    # Keep all records from the same row together. One annual label per row.
    training, testing = train_test_split(eligible, test_size=0.20, random_state=42)

    # Imputation and encoding are fitted only to training homes.
    processor = ColumnTransformer([
        ("categories", Pipeline([
            ("fill", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), FEATURES)
    ])
    model = Pipeline([
        ("prepare", processor),
        ("forest", RandomForestRegressor(
            n_estimators=50, max_depth=14, min_samples_leaf=3,
            random_state=42, n_jobs=-1,
        )),
    ])

    X_train, y_train = training[FEATURES], training["actual_kwh"]
    X_test, y_test = testing[FEATURES], testing["actual_kwh"]
    model.fit(X_train, y_train)
    predictions = np.maximum(0, model.predict(X_test))

    baseline = DummyRegressor(strategy="median")
    baseline.fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)

    # Show where the prediction fails across property types, not just an average.
    property_breakdown = {}
    for property_type in testing["PROP_TYPE"].dropna().unique():
        mask = testing["PROP_TYPE"].to_numpy() == property_type
        if mask.sum() >= 25:
            property_breakdown[str(property_type)] = {
                "rows": int(mask.sum()),
                **metrics(y_test.to_numpy()[mask], predictions[mask]),
            }

    evidence = testing[FEATURES].copy()
    evidence["actual_kwh"] = y_test.to_numpy()
    evidence["predicted_kwh"] = np.round(predictions, 2)
    evidence["absolute_error_kwh"] = np.round(np.abs(evidence["actual_kwh"] - predictions), 2)
    evidence["fuel"] = fuel

    results = {
        "valid_records_before_sampling": int(count_before_sample),
        "used_records": int(len(eligible)),
        "training_records": int(len(training)),
        "held_out_test_records": int(len(testing)),
        "random_forest": metrics(y_test, predictions),
        "median_baseline": metrics(y_test, baseline_pred),
        "property_type_breakdown": property_breakdown,
    }
    return results, evidence


def run(csv_path: Path, max_rows: int):
    data = load_need(csv_path)
    report = {
        "project": "TREE",
        "dataset": "UK government NEED 2026 anonymised 50,000-row sample",
        "source": SOURCE,
        "source_file": csv_path.name,
        "target_year": YEAR,
        "raw_rows": len(data),
        "features": FEATURES,
        "observed_labels_only": True,
        "evaluation": "Random Forest on real NEED data; separate 80/20 holdout per fuel",
        "relation_to_synthetic_model": "Separate real-data-trained benchmark; NOT external validation of the original synthetic-trained model",
        "limitations": (
            "Anonymised sample; coarse banded property features; may not cover all housing types. "
            "Features are not necessarily known to precede the 2024 energy period. "
            "One random held-out split is not prospective validation. "
            "Results do not validate retrofit savings, Green Home Score, or monetary predictions."
        ),
        "fuels": {},
    }
    output = ROOT / "evaluation"
    output.mkdir(exist_ok=True)
    all_evidence = []
    for fuel in TARGETS:
        result, evidence = evaluate_fuel(data, fuel, max_rows)
        report["fuels"][fuel] = result
        all_evidence.append(evidence)
        print(f"{fuel.title()}: {result['held_out_test_records']} real test homes")
        print("  Random Forest", result["random_forest"])
        print("  Median baseline", result["median_baseline"])
    report_path = output / "need_real_validation.json"
    evidence_path = output / "need_held_out_predictions.csv"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.concat(all_evidence, ignore_index=True).to_csv(evidence_path, index=False)
    print(f"\nSaved {report_path}\nSaved {evidence_path}")
    print("Reminder: these are results of a separately trained real-data benchmark, NOT the synthetic model's real-world accuracy.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TREE real UK NEED energy model evaluation")
    parser.add_argument("--csv", type=Path, required=True, help="Path to official anon2026_50k.csv")
    parser.add_argument("--max-rows", type=int, default=15000, help="Maximum valid samples per fuel (0 = all)")
    args = parser.parse_args()
    run(args.csv.expanduser(), args.max_rows)
