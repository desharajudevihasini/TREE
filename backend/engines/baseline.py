"""Heuristic missing-consumption fallback. Not a supervised ML accuracy claim."""
from backend.schemas import Property


def get_baseline(p: Property) -> dict:
    warnings = []
    assumed = False
    elec = p.annual_electricity_kwh
    gas = p.annual_gas_kwh
    synthetic_ml_used = False
    real_need_used = False
    if (elec is None or gas is None) and p.baseline_source in (
        "epc_record_no_metered_consumption", "synthetic_fallback_if_missing", "self_reported", "consumer_need"):
        try:
            from ml.consumer_need import predict as need_estimate
            observed = need_estimate(p.property_type, p.epc_rating)
            if elec is None: elec = observed['predictions']['electricity_kwh']; real_need_used = True
            if gas is None: gas = observed['predictions']['gas_kwh']; real_need_used = True
            if real_need_used:
                assumed = True
                warnings.append('Consumption estimated using a REAL NEED 2026 trained model on coarse property type and grouped EPC rating. Not household-specific, not a verified EPC bill, and not a retrofit-outcome estimate.')
                if p.heating_type in ('heat_pump','electric_resistance','district'):
                    warnings.append('The coarse NEED model has no heating-system feature: gas estimates for non-gas homes can be inaccurate. Confirm an actual gas bill or zero gas use.')
        except (ImportError,FileNotFoundError,ValueError):
            warnings.append('Real NEED consumer estimator unavailable; using explicitly labelled synthetic fallback for any missing fuel values.')
    if elec is None or gas is None:
        try:
            from ml.predict import synthetic_model_prediction
            pred = synthetic_model_prediction(p)
        except (ImportError, FileNotFoundError, ValueError):
            pred = None
        if pred is not None:
            if elec is None: elec = pred["annual_electricity_kwh"]; synthetic_ml_used = True
            if gas is None: gas = pred["annual_gas_kwh"]; synthetic_ml_used = True
            if synthetic_ml_used:
                assumed = True
                warnings.append("Consumption estimated by model trained on synthetic demo labels; NOT externally validated on UK household data.")
    if elec is None:
        elec = p.floor_area_m2 * (49 if p.heating_type in ("electric_resistance", "heat_pump") else 31)
        assumed = True
        warnings.append("Electricity missing: using documented synthetic heuristic (not measured or validated ML).")
    if gas is None:
        gas = (p.floor_area_m2 * 125) if p.heating_type == "gas_boiler" else 0.0
        assumed = True
        warnings.append("Gas missing: using synthetic heuristic based on heating type (not a real measurement).")
    return {
        "electricity_import_kwh": round(float(elec), 2),
        "gas_kwh": round(float(gas), 2),
        "electricity_demand_kwh": round(float(elec), 2),
        "status": ("real_need_coarse" if real_need_used else "synthetic_trained_ml" if synthetic_ml_used else "estimated_heuristic") if assumed else p.baseline_source,
        "warnings": warnings,
    }
