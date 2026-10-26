"""Location-based operational GHG accounting with **published 2026 DESNZ factors**.

Scope convention: UK grid electricity (Scope 2, generation incl. imports),
plus UK natural gas combustion (Scope 1). Excludes upstream (WTT), T&D,
exported solar and construction/embodied emissions. Do not treat reduction as
carbon credits or a measured marginal-grid emissions saving.

Sources: UK Government *Greenhouse gas reporting conversion factors 2026*,
last updated 31 July 2026 (flat-file correction), and 2026 methodology.
https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026
"""
from __future__ import annotations
import math
import os

# DESNZ 2026: grid electricity generated incl. imports, kg CO2e/kWh (Scope 2).
# DESNZ 2026: natural gas combustion kg CO2e/kWh (Scope 1).
DESNZ_2026_GRID_ELECTRICITY = 0.13096
DESNZ_2026_NATURAL_GAS = 0.18231
PUBLICATION_URL = 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026'


def _factor(env: str, default: float) -> tuple[float, bool]:
    text = os.getenv(env)
    if text is None or text.strip() == '':
        return default, False
    try:
        value = float(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{env} must be a numeric kg CO2e/kWh factor') from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{env} must be finite and nonnegative')
    return value, True


def current_factors() -> dict:
    elec, edited_e = _factor('ELEC_KG_CO2E_PER_KWH', DESNZ_2026_GRID_ELECTRICITY)
    gas, edited_g = _factor('GAS_KG_CO2E_PER_KWH', DESNZ_2026_NATURAL_GAS)
    return {
        'electricity_factor_kg_co2e_kwh': elec,
        'gas_factor_kg_co2e_kwh': gas,
        'source': 'environment_override' if (edited_e or edited_g) else 'DESNZ_2026_UK_GHG_conversion_factors',
        'source_url': PUBLICATION_URL,
        'year': 2026,
        'scope': 'location-based operational grid electricity Scope 2 + natural gas combustion Scope 1',
        'excluded': ['electricity transmission/distribution', 'fuel upstream/well-to-tank',
                     'embodied retrofit emissions', 'exports and marginal emissions'],
        'warning': ('One or both factors were overridden; verify year, scope and source.' if (edited_e or edited_g)
                    else 'Published annual-average factors, not marginal emissions saved by a particular upgrade.')
    }


def carbon_change(electricity_saving_kwh: float, gas_saving_kwh: float) -> dict:
    values=(float(electricity_saving_kwh),float(gas_saving_kwh))
    if not all(math.isfinite(n) for n in values):
        raise ValueError('Energy changes must be finite kWh per year')
    result=current_factors()
    result['reduction_kg_co2e'] = round(
        values[0] * result['electricity_factor_kg_co2e_kwh']
        + values[1] * result['gas_factor_kg_co2e_kwh'], 2)
    return result
