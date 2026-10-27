"""Train a reproducible synthetic-only benchmark, NOT a real-world UK energy prediction model.
Run from project root: python -m ml.train
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
CATS = ["property_type", "heating_type", "region", "glazing"]
NUMS = ["floor_area_m2", "loft_insulated", "wall_insulated", "smart_controls", "solar_kwp"]
FEATURES = NUMS + CATS


def generate(n=900, seed=42):
    r = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        size = float(r.uniform(50, 220))
        ptype = str(r.choice(["terraced", "semi_detached", "detached", "flat", "bungalow"]))
        heat = str(r.choice(["gas_boiler", "heat_pump", "electric_resistance"]))
        region = str(r.choice(["London", "North West", "Yorkshire", "Scotland", "Wales", "South East"]))
        loft, wall, controls = [int(v) for v in r.integers(0, 2, size=3)]
        glazing = str(r.choice(["single", "double", "triple"]))
        solar = float(r.choice([0, 0, 0, 3]))
        heat_multiplier = (1 - .12 * loft) * (1 - .13 * wall) * (.95 if glazing != "single" else 1) * (1 - .05 * controls)
        heating = size * 138 * heat_multiplier
        if heat == "gas_boiler":
            gas = heating + 800 + r.normal(0, 850)
            electricity = size * 28 + 650 - solar * 450 + r.normal(0, 350)
        elif heat == "heat_pump":
            gas = 0
            electricity = size * 28 + 650 + heating / 3 - solar * 450 + r.normal(0, 550)
        else:
            gas = 0
            electricity = size * 28 + 650 + heating - solar * 450 + r.normal(0, 800)
        rows.append(dict(property_type=ptype, heating_type=heat, region=region, glazing=glazing,
                         floor_area_m2=size, loft_insulated=loft, wall_insulated=wall,
                         smart_controls=controls, solar_kwp=solar,
                         annual_electricity_kwh=max(100, electricity), annual_gas_kwh=max(0, gas)))
    return pd.DataFrame(rows)


def train():
    df = generate()
    train_data, test_data = train_test_split(df, test_size=0.2, random_state=42)
    # Separate independent hold-out test from training. No hyperparameter selection on test.
    metrics = {"dataset": "synthetic_generator_only", "rows": len(df), "train_rows": len(train_data),
               "held_out_rows": len(test_data), "split_seed": 42, "real_world_validation": False,
               "warning": "Metrics are on synthetic labels from a documented generator; NOT UK household predictive accuracy.",
               "targets": {}}
    predictions = pd.DataFrame({"synthetic_test_row": test_data.index})
    (ROOT / "ml" / "models").mkdir(parents=True, exist_ok=True)
    for target in ("annual_electricity_kwh", "annual_gas_kwh"):
        processor = ColumnTransformer([( "cat", OneHotEncoder(handle_unknown="ignore"), CATS),
                                       ( "num", "passthrough", NUMS)])
        model = Pipeline([("features", processor), ("regressor", RandomForestRegressor(n_estimators=65, max_depth=13, random_state=42, n_jobs=-1))])
        model.fit(train_data[FEATURES], train_data[target])
        pred = model.predict(test_data[FEATURES])
        naive = DummyRegressor(strategy="median").fit(train_data[FEATURES], train_data[target]).predict(test_data[FEATURES])
        metrics["targets"][target] = {"mae": round(mean_absolute_error(test_data[target], pred), 2),
                                       "rmse": round(root_mean_squared_error(test_data[target], pred), 2),
                                       "median_baseline_mae": round(mean_absolute_error(test_data[target], naive), 2),
                                       "median_baseline_rmse": round(root_mean_squared_error(test_data[target], naive), 2)}
        predictions[f"true_{target}"] = test_data[target].to_numpy()
        predictions[f"pred_{target}"] = pred
        joblib.dump(model, ROOT / "ml" / "models" / f"{target}.joblib")
    (ROOT / "evaluation").mkdir(exist_ok=True)
    predictions.to_csv(ROOT / "evaluation" / "held_out_predictions_SYNTHETIC_ONLY.csv", index=False)
    (ROOT / "evaluation" / "synthetic_ml_report.json").write_text(json.dumps(metrics, indent=2))
    (ROOT / "data" / "demo" / "synthetic_training_data.csv").write_text(df.to_csv(index=False))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    train()
