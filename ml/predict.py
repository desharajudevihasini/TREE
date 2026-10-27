"""Synthetic-trained model inference, clearly labelled. Only called if reference baseline missing."""
from pathlib import Path
import joblib
import pandas as pd
from backend.schemas import Property

ROOT = Path(__file__).resolve().parents[1]
CACHE = {}


def synthetic_model_prediction(p: Property):
    fields = {"floor_area_m2": p.floor_area_m2, "loft_insulated": int(p.loft_insulated or False),
              "wall_insulated": int(p.wall_insulated or False), "smart_controls": int(p.smart_controls or False),
              "solar_kwp": p.solar_kwp, "property_type": p.property_type,
              "heating_type": p.heating_type or "gas_boiler", "region": p.region,
              "glazing": p.glazing or "double"}
    results = {}
    for target in ("annual_electricity_kwh", "annual_gas_kwh"):
        file = ROOT / "ml" / "models" / f"{target}.joblib"
        if not file.exists(): return None
        if target not in CACHE: CACHE[target] = joblib.load(file)
        results[target] = round(max(0., float(CACHE[target].predict(pd.DataFrame([fields]))[0])), 2)
    return results
