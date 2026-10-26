"""Explain exactly how each of the seven Lloyds-weighted subscores was made.

No new numbers are calculated here: this uses the SAME result as green_score().
Mappings are our demonstrator assumptions; official weights come from the PPT.
"""
from __future__ import annotations
from backend.schemas import Property
from backend.engines.scoring import green_score

FIELDS = {
    'energy_efficiency': ['epc_rating'],
    'consumption_intensity': ['annual_electricity_kwh', 'annual_gas_kwh', 'floor_area_m2'],
    'insulation': ['loft_insulated', 'wall_insulated'],
    'heating': ['heating_type'],
    'glazing': ['glazing'],
    'renewables': ['solar_kwp'],
    'smart_management': ['smart_controls'],
}
REASONS = {
    'energy_efficiency': 'Uses the confirmed EPC letter mapped to a 0–100 demonstrator subscore; 50 if absent. This is not the official EPC numeric score.',
    'consumption_intensity': 'Purchased grid electricity plus gas, divided by floor area (kWh/m²/year), then mapped from 350 kWh/m² (0 points) to 60 kWh/m² (100 points).',
    'insulation': 'Average of loft and external-wall insulation subscores. Confirmed insulated = 90; not insulated = 20; unknown = 50.',
    'heating': 'Demonstrator mapping: gas boiler 40; heat pump 90; electric resistance 35; district heat 70; unknown 50.',
    'glazing': 'Demonstrator mapping: single 20, double 75, triple 95, unknown 50.',
    'renewables': 'Solar PV installed (>0 kWp) = 90; otherwise 0. Non-PV sustainability ideas do not count without a validated conversion.',
    'smart_management': 'Demonstrator mapping: controls present 90, absent 10, unknown 50.',
}

def explain_score(p: Property) -> dict:
    score = green_score(p)
    components = []
    for key, fields in FIELDS.items():
        observed = {f: getattr(p, f) for f in fields}
        unknown = [f for f, value in observed.items() if value is None]
        components.append({
            'id': key, 'weight_pct': round(score['weights'][key] * 100, 1),
            'subscore_0_100': score['subscores'][key],
            'contribution_points': score['contributions'][key],
            'inputs': observed, 'unknown_fields': unknown,
            'reason': REASONS[key],
            'basis': 'official_PPT_weight_plus_documented_TREE_demo_mapping',
        })
    return {'score': score['score'], 'classification': score['classification'],
            'components': components, 'provisional': score['provisional'],
            'unknown_input_score_bound': score['unknown_input_score_bound'],
            'warning': 'Official Lloyds weights, but TREE-authored mappings. Unknown input bounds are not statistical confidence intervals.'}
