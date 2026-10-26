"""Official Lloyds purchased-energy improvement formula across homes."""
from backend.schemas import Property
from backend.engines.optimizer import optimize


def rank_properties(properties: list[Property]) -> list[dict]:
    rows = []
    for p in properties:
        if p.annual_electricity_kwh is None or p.annual_gas_kwh is None:
            rows.append({"property_id": p.property_id, "name": p.name, "improvement_potential_pct": None,
                         "reason": "Missing observed/reference baseline; ranking unavailable."})
            continue
        if p.annual_electricity_kwh + p.annual_gas_kwh <= 0:
            rows.append({"property_id": p.property_id, "name": p.name, "improvement_potential_pct": None,
                         "reason": "Zero purchased-energy baseline; ranking unavailable."})
            continue
        # Technical feasibility upper bound within a documented illustrative 30k package budget.
        result = optimize(p, 30000, "energy")["best"]
        rows.append({"property_id": p.property_id, "name": p.name,
                     "baseline_purchased_kwh": p.annual_electricity_kwh + p.annual_gas_kwh,
                     "after_purchased_kwh": result["after"]["grid_electricity_kwh"] + result["after"]["gas_kwh"],
                     "improvement_potential_pct": result["savings"]["improvement_potential_pct"],
                     "measures": result["measures"], "scenario_budget_gbp": 30000,
                     "classification": result["score_before"]["classification"],
                     "reason": "Illustrative feasible package, £30k budget; synthetic/demo values."})
    return sorted(rows, key=lambda x: (x["improvement_potential_pct"] is None, -(x["improvement_potential_pct"] or 0)))
