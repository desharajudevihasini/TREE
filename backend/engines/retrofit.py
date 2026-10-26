"""Interacting, fuel-separated retrofit model. Assumptions are DEMO approximations, not engineering certificates."""
from __future__ import annotations
from backend.schemas import Property
from backend.engines.baseline import get_baseline
from backend.engines.scoring import green_score, EPC_SCORE

RETROFITS = {
    "loft_insulation": {"label": "Loft insulation", "cost_gbp": 950, "description": "Reduce heat loss through the loft"},
    "wall_insulation": {"label": "Wall insulation", "cost_gbp": 5600, "description": "Reduce heat loss through walls"},
    "double_glazing": {"label": "Double glazing", "cost_gbp": 5900, "description": "Upgrade single glazed windows"},
    "smart_controls": {"label": "Smart controls", "cost_gbp": 300, "description": "Reduce avoidable heating consumption"},
    "heat_pump": {"label": "Heat pump", "cost_gbp": 8500, "description": "Replace gas space heating with an electric heat pump"},
    "solar_panels": {"label": "Solar panels (3 kWp)", "cost_gbp": 5500, "description": "Offset grid imports with onsite solar"},
}


def eligibility(p: Property, key: str) -> tuple[bool, str, str]:
    if key not in RETROFITS:
        return False, "Low", "Unknown retrofit."
    if key == "loft_insulation":
        if p.property_type == "flat": return False, "Low", "No individual accessible loft modelled for this flat."
        if p.loft_insulated is None: return False, "Low", "Loft status unknown; confirm before recommending."
        return (False, "Low", "Loft already insulated.") if p.loft_insulated else (True, "High", "Uninsulated loft; inexpensive first step.")
    if key == "wall_insulation":
        if p.wall_insulated is None: return False, "Low", "Wall insulation status unknown."
        return (False, "Low", "Walls already insulated.") if p.wall_insulated else (True, "Medium", "Wall upgrade feasible under simplified assumptions; survey required.")
    if key == "double_glazing":
        if p.glazing is None: return False, "Low", "Glazing type unknown."
        return (True, "Medium", "Single glazing can be replaced subject to permissions.") if p.glazing == "single" else (False, "Low", "Existing glazing not single-glazed.")
    if key == "smart_controls":
        if p.smart_controls is None: return False, "Low", "Smart controls status unknown."
        if p.heating_type is None: return False, "Low", "Heating system unknown."
        return (False, "Low", "Controls already installed.") if p.smart_controls else (True, "High", "Heating controls not present.")
    if key == "heat_pump":
        if p.heating_type != "gas_boiler": return False, "Low", "MVP replacement model only supports gas-boiler homes."
        if p.outdoor_space is None: return False, "Low", "Outdoor-unit suitability unknown."
        return (True, "Medium", "Potential gas boiler replacement; detailed heat-loss and installer survey needed.") if p.outdoor_space else (False, "Low", "No modelled outdoor unit location.")
    if key == "solar_panels":
        if p.solar_kwp > 0: return False, "Low", "Solar already present; expansion outside MVP scope."
        if p.roof_suitable is None: return False, "Low", "Roof suitability unknown."
        return (True, "Medium", "Illustrative roof suitability; actual survey, orientation and shading needed.") if p.roof_suitable else (False, "Low", "No suitable roof modelled.")
    return False, "Low", "Unsupported."


def _initial_heating(p: Property, b: dict) -> tuple[float, float, float]:
    """Return useful space heat, non-space gas, and non-space electricity.
    Gas-boiler model assumes 85% gas is space heat, 85% conversion efficiency.
    Existing heat-pump/electric heat fraction uses 55% of electricity demand.
    """
    gas, elec = b["gas_kwh"], b["electricity_demand_kwh"]
    if p.heating_type == "gas_boiler":
        return gas * .85 * .85, gas * .15, elec
    if p.heating_type == "heat_pump":
        heat_elec = elec * .55
        return heat_elec * 3, gas, elec - heat_elec
    if p.heating_type == "electric_resistance":
        heat_elec = elec * .55
        return heat_elec, gas, elec - heat_elec
    return 0.0, gas, elec


def _energy(p: Property, measures: list[str], base: dict) -> dict:
    useful_heat, other_gas, other_elec = _initial_heating(p, base)
    # Effects multiply so insulation + glazing + smart controls never double-count independently.
    factors = {"loft_insulation": .82, "wall_insulation": .86, "double_glazing": .92, "smart_controls": .93}
    for key in measures:
        if key in factors: useful_heat *= factors[key]
    gas = other_gas
    elec_demand = other_elec
    if "heat_pump" in measures or p.heating_type == "heat_pump":
        elec_demand += useful_heat / 3.0
    elif p.heating_type == "gas_boiler":
        gas += useful_heat / .85
    elif p.heating_type == "electric_resistance":
        elec_demand += useful_heat
    else:
        # No unsupported heat-use reduction on unknown or district-heated homes.
        gas = base["gas_kwh"]
        elec_demand = base["electricity_demand_kwh"]
    if "solar_panels" in measures:
        # 3kWp x 900 kWh/kWp/year x 55% onsite utilization, capped at demand.
        new_self_use = min(2700 * .55, elec_demand)
    else:
        new_self_use = 0
    # Baseline electricity is NET grid imports: added solar is credited only against modeled demand.
    if p.solar_kwp > 0:
        base_import = base["electricity_import_kwh"]
        base_demand = base["electricity_demand_kwh"]
        base_self_use = min(p.solar_kwp * 900 * .55, max(0, base_demand))
        # If user-supplied imports are net of existing solar, recover demand first.
        # Existing solar benefit is carried through changing demand.
        elec_import = max(0, elec_demand - min(base_self_use, elec_demand) - new_self_use)
    else:
        elec_import = max(0, elec_demand - new_self_use)
    return {"grid_electricity_kwh": round(elec_import, 2), "electricity_demand_kwh": round(elec_demand, 2),
            "gas_kwh": round(max(0, gas), 2), "added_solar_self_consumption_kwh": round(new_self_use, 2)}


def simulate(p: Property, measures: list[str], electricity_price: float | None = None, gas_price: float | None = None) -> dict:
    if len(measures) != len(set(measures)): raise ValueError("Duplicate retrofits are invalid")
    for key in measures:
        ok, _, reason = eligibility(p, key)
        if not ok: raise ValueError(f"{key}: {reason}")
    from backend.engines.data_quality import check_property
    input_quality = check_property(p)
    base = get_baseline(p)
    eprice = p.electricity_price_gbp_kwh if electricity_price is None else electricity_price
    gprice = p.gas_price_gbp_kwh if gas_price is None else gas_price
    # For existing solar, the provided annual electricity figure represents grid imports.
    if p.solar_kwp > 0:
        inferred_demand = base["electricity_import_kwh"] + min(p.solar_kwp * 900 * .55, base["electricity_import_kwh"] + p.solar_kwp * 900 * .55)
        base = {**base, "electricity_demand_kwh": round(inferred_demand, 2)}
    after = _energy(p, measures, base)
    diff_e = round(base["electricity_import_kwh"] - after["grid_electricity_kwh"], 2)
    diff_g = round(base["gas_kwh"] - after["gas_kwh"], 2)
    cost = sum(RETROFITS[k]["cost_gbp"] for k in measures)
    annual = round(diff_e * eprice + diff_g * gprice, 2)
    from backend.engines.carbon import carbon_change
    co2 = carbon_change(diff_e, diff_g)
    baseline_purchased = base["electricity_import_kwh"] + base["gas_kwh"]
    after_purchased = after["grid_electricity_kwh"] + after["gas_kwh"]
    improvement = round(100 * (baseline_purchased - after_purchased) / baseline_purchased, 2) if baseline_purchased > 0 else None
    updated = p.model_copy(deep=True)
    for key in measures:
        if key == "loft_insulation": updated.loft_insulated = True
        elif key == "wall_insulation": updated.wall_insulated = True
        elif key == "double_glazing": updated.glazing = "double"
        elif key == "smart_controls": updated.smart_controls = True
        elif key == "heat_pump": updated.heating_type = "heat_pump"
        elif key == "solar_panels": updated.solar_kwp = 3
    if baseline_purchased > 0:
        efficiency_proxy = EPC_SCORE.get(p.epc_rating, 50) + 55 * (1 - after_purchased / baseline_purchased)
    else:
        efficiency_proxy = EPC_SCORE.get(p.epc_rating, 50)
    score_before = green_score(p, base)
    score_after = green_score(updated, {"electricity_import_kwh": after["grid_electricity_kwh"], "gas_kwh": after["gas_kwh"], "warnings": []}, efficiency_proxy)
    from backend.engines.valuation import property_value_impact
    return {
        "measures": measures, "labels": [RETROFITS[k]["label"] for k in measures],
        "baseline": {"grid_electricity_kwh": base["electricity_import_kwh"], "gas_kwh": base["gas_kwh"], "electricity_demand_kwh": base["electricity_demand_kwh"]},
        "after": after,
        "savings": {"electricity_kwh": diff_e, "gas_kwh": diff_g, "purchased_energy_kwh": round(baseline_purchased - after_purchased, 2), "improvement_potential_pct": improvement},
        "carbon": co2, "cost_gbp": cost, "annual_bill_savings_gbp": annual,
        "simple_payback_years": round(cost / annual, 1) if annual > 0 and cost > 0 else None,
        "baseline_annual_bill_gbp": round(base["electricity_import_kwh"] * eprice + base["gas_kwh"] * gprice, 2),
        "after_annual_bill_gbp": round(after["grid_electricity_kwh"] * eprice + after["gas_kwh"] * gprice, 2),
        "score_before": score_before, "score_after": score_after,
        "valuation": property_value_impact(p, score_before["score"], score_after["score"]),
        "model": "simplified-interacting-energy-model-v1",
        "input_quality": input_quality,
        "baseline_evidence": {"status": base.get('status'), "source": p.baseline_source,
                               "electricity_observed": p.annual_electricity_kwh is not None,
                               "gas_observed": p.annual_gas_kwh is not None},
        "warnings": ["DEMONSTRATION MODEL: retrofit effects, costs and prices are illustrative assumptions, not installer quotes or certified energy modelling.",
                     "Heat demand and solar self-consumption are simplified annual approximations; roof and heat-pump surveys required."] + base.get("warnings", []) + [i['message'] for i in input_quality['issues']],
    }


def recommended_measures(p: Property) -> list[dict]:
    out = []
    for key, meta in RETROFITS.items():
        ok, rating, reason = eligibility(p, key)
        if not ok: continue
        sim = simulate(p, [key])
        out.append({"id": key, "label": meta["label"], "suitability": rating,
                    "reason": reason, "cost_gbp": meta["cost_gbp"],
                    "electricity_saving_kwh": sim["savings"]["electricity_kwh"],
                    "gas_saving_kwh": sim["savings"]["gas_kwh"],
                    "carbon_reduction_kg": sim["carbon"]["reduction_kg_co2e"],
                    "annual_bill_savings_gbp": sim["annual_bill_savings_gbp"]})
    out.sort(key=lambda r: (r["suitability"] != "High", -(r["annual_bill_savings_gbp"] / max(r["cost_gbp"], 1))))
    return out
