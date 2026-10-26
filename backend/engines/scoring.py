"""Official Lloyds weights; subscore mappings are OUR documented demonstrator assumptions."""
from backend.schemas import Property
from backend.engines.baseline import get_baseline

WEIGHTS = {"energy_efficiency": .25, "consumption_intensity": .20, "insulation": .15,
           "heating": .15, "glazing": .10, "renewables": .10, "smart_management": .05}
EPC_SCORE = dict(zip("ABCDEFG", (96, 85, 72, 57, 42, 27, 12)))


def clamp(v: float) -> float:
    return round(max(0, min(100, v)), 2)


def green_score(p: Property, baseline: dict | None = None, modelled_energy_efficiency: float | None = None) -> dict:
    b = baseline or get_baseline(p)
    warnings = list(b.get("warnings", []))
    from backend.engines.data_quality import check_property
    check = check_property(p)
    warnings.extend(issue['message'] for issue in check['issues'])
    energy = (b["electricity_import_kwh"] + b["gas_kwh"]) / p.floor_area_m2
    intensity = clamp(100 * (350 - energy) / (350 - 60))
    if modelled_energy_efficiency is not None:
        ee = clamp(modelled_energy_efficiency)
        warnings.append("Modelled post-retrofit energy-efficiency proxy; NOT an updated EPC certificate.")
    elif p.epc_rating:
        ee = EPC_SCORE[p.epc_rating]
    else:
        ee = 50
        warnings.append("EPC unavailable: energy-efficiency subscore uses a neutral 50 placeholder.")
    def bool_score(v, a, z, label):
        if v is None:
            warnings.append(f"{label} unknown: using neutral 50 subscore; confirm for better result.")
            return 50
        return a if v else z
    loft = bool_score(p.loft_insulated, 90, 20, "Loft insulation")
    wall = bool_score(p.wall_insulated, 90, 20, "Wall insulation")
    scores = {
        "energy_efficiency": ee,
        "consumption_intensity": intensity,
        "insulation": (loft + wall) / 2,
        "heating": {"gas_boiler": 40, "heat_pump": 90, "electric_resistance": 35, "district": 70}.get(p.heating_type, 50),
        "glazing": {"single": 20, "double": 75, "triple": 95}.get(p.glazing, 50),
        "renewables": 90 if p.solar_kwp > 0 else 0,
        "smart_management": bool_score(p.smart_controls, 90, 10, "Smart controls"),
    }
    if p.heating_type is None:
        warnings.append("Heating type unknown: using neutral 50 heating subscore.")
    if p.glazing is None:
        warnings.append("Glazing unknown: using neutral 50 glazing subscore.")
    contributions = {k: round(clamp(v) * WEIGHTS[k], 2) for k, v in scores.items()}
    raw = sum(scores[k] * WEIGHTS[k] for k in scores)
    # Standard half-up rounding for nonnegative scores.
    rounded = int(raw + 0.5)
    classification = ("Highly efficient" if rounded >= 80 else "Good" if rounded >= 65 else
                      "Moderate" if rounded >= 50 else "Poor" if rounded >= 30 else "Very poor")
    # Uncertainty is a *mathematical bound* for unknown inputs under our fixed
    # demonstrator mapping, NOT a confidence interval or validated prediction.
    # Known factors remain fixed; unknown components range across their 0..100
    # subscore scale. Half of insulation is varied for each unknown field.
    unknown = []
    def unsure(label: str, weight_fraction: float, placeholder: float):
        unknown.append(label)
        # Each unknown has a neutral placeholder, so subtract its current
        # contribution and replace it by either 0 or 100 below.
        return (weight_fraction * placeholder, weight_fraction * 100)
    uncertain_parts = []
    if p.epc_rating is None and modelled_energy_efficiency is None:
        uncertain_parts.append(unsure('epc_rating', WEIGHTS['energy_efficiency'], 50))
    if p.annual_electricity_kwh is None or p.annual_gas_kwh is None:
        uncertain_parts.append(unsure('observed_energy_baseline', WEIGHTS['consumption_intensity'], intensity))
    if p.loft_insulated is None:
        uncertain_parts.append(unsure('loft_insulated', WEIGHTS['insulation']/2, loft))
    if p.wall_insulated is None:
        uncertain_parts.append(unsure('wall_insulated', WEIGHTS['insulation']/2, wall))
    if p.heating_type is None:
        uncertain_parts.append(unsure('heating_type', WEIGHTS['heating'], 50))
    if p.glazing is None:
        uncertain_parts.append(unsure('glazing', WEIGHTS['glazing'], 50))
    if p.smart_controls is None:
        uncertain_parts.append(unsure('smart_controls', WEIGHTS['smart_management'], 50))
    interval_lower = max(0.0, raw - sum(cur for cur, _ in uncertain_parts))
    interval_upper = min(100.0, interval_lower + sum(full for _, full in uncertain_parts))
    provisional = bool(unknown) or b.get('status') in ('real_need_coarse', 'synthetic_trained_ml', 'estimated_heuristic')
    return {"raw_score": round(raw, 2), "score": rounded, "classification": classification,
            "subscores": {k: round(v, 2) for k, v in scores.items()}, "weights": WEIGHTS,
            "contributions": contributions, "intensity_kwh_m2": round(energy, 2),
            "provisional": provisional,
            "missing_inputs_affecting_score": unknown,
            "unknown_input_score_bound": [round(interval_lower, 2), round(interval_upper, 2)],
            "uncertainty_note": ("Range comes solely from unknown input substitutions on a 0–100 component scale. "
                                 "It does not cover errors in observed data, subscore assumptions, EPC staleness or ML prediction. "
                                 "It is not a statistical confidence interval."),
            "warnings": warnings, "methodology": "tree-v1-illustrative-subscore-mappings"}
