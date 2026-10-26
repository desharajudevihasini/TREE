"""Transparent input checks; these are consistency warnings, not data corrections.

Never overwrite household answers or secretly infer an unknown EPC rating.
"""
from backend.schemas import Property


def check_property(p: Property) -> dict:
    issues = []
    unknowns = []
    for field in ('epc_rating', 'heating_type', 'loft_insulated', 'wall_insulated',
                  'glazing', 'smart_controls', 'roof_suitable', 'outdoor_space'):
        if getattr(p, field) is None:
            unknowns.append(field)
    if p.annual_electricity_kwh is None:
        unknowns.append('annual_electricity_kwh')
    if p.annual_gas_kwh is None:
        unknowns.append('annual_gas_kwh')
    if p.solar_kwp > 0 and p.roof_suitable is False:
        issues.append({'code':'solar_roof_conflict','severity':'review',
                       'message':'Solar panels are recorded as installed, but the roof is marked unsuitable; confirm whether they are ground-mounted or the roof status is outdated.'})
    if p.heating_type == 'gas_boiler' and p.annual_gas_kwh == 0:
        issues.append({'code':'gas_boiler_zero_gas','severity':'review',
                       'message':'A gas boiler is recorded but annual gas use is zero; check whether bills cover a full occupied year.'})
    if p.heating_type in ('electric_resistance', 'heat_pump') and (p.annual_gas_kwh or 0) > 7000:
        issues.append({'code':'electric_heating_high_gas','severity':'review',
                       'message':'An electric primary heating system is recorded alongside substantial gas usage; verify whether a secondary heating system is present.'})
    if p.annual_electricity_kwh is not None and p.annual_electricity_kwh > 25000:
        issues.append({'code':'unusually_high_electricity','severity':'review',
                       'message':'Electricity consumption is unusually high; verify annual kWh and billing dates.'})
    if p.annual_gas_kwh is not None and p.annual_gas_kwh > 65000:
        issues.append({'code':'unusually_high_gas','severity':'review',
                       'message':'Gas consumption is unusually high; verify annual kWh and billing dates.'})
    if p.floor_area_m2 < 20 or p.floor_area_m2 > 650:
        issues.append({'code':'unusual_area','severity':'review',
                       'message':'Floor area falls outside the usual demonstration range; verify the square-metre units.'})
    if p.epc_rating in ('A','B') and p.annual_electricity_kwh is not None and p.annual_gas_kwh is not None:
        intensity = (p.annual_electricity_kwh + p.annual_gas_kwh)/p.floor_area_m2
        if intensity > 350:
            issues.append({'code':'efficient_epc_high_intensity','severity':'review',
                           'message':'An efficient EPC category conflicts with very high purchased-energy intensity; confirm the property, EPC date and bills.'})
    return {'status':'needs_review' if issues else 'incomplete' if unknowns else 'provided_consistent',
            'issues':issues, 'unknown_fields':unknowns,
            'warning':'Consistency checks do not verify an EPC certificate, energy bill, customer identity, or building suitability.'}
