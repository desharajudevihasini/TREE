"""Synthetic demonstration properties. NOT real EPC or observed customer records."""
from backend.schemas import Property

RAW = [
    ("manchester", "Manchester family home", "North West", "semi_detached", 105, "1950-1966", "E", "gas_boiler", None, False, "double", 0, False, True, True, 3500, 15500, 275000),
    ("bristol", "Bristol terrace", "South West", "terraced", 86, "1900-1929", "D", "gas_boiler", False, True, "single", 0, False, True, False, 2900, 12500, 320000),
    ("london", "London modern flat", "London", "flat", 67, "2012-2026", "B", "electric_resistance", True, True, "double", 0, True, False, False, 4900, 0, 490000),
    ("leeds", "Leeds detached home", "Yorkshire", "detached", 145, "1976-1982", "F", "gas_boiler", False, False, "single", 0, False, True, True, 4200, 21500, 355000),
    ("cardiff", "Cardiff bungalow", "Wales", "bungalow", 93, "1967-1975", "D", "gas_boiler", True, False, "double", 0, True, True, True, 3400, 10500, 285000),
    ("glasgow", "Glasgow family semi", "Scotland", "semi_detached", 116, "1930-1949", "E", "gas_boiler", False, False, "double", 0, False, True, True, 4100, 18600, 260000),
    ("bath", "Bath period terrace", "South West", "terraced", 98, "pre-1900", "E", "gas_boiler", None, False, "single", 0, False, False, False, 3000, 16800, 575000),
    ("oxford", "Oxford efficient house", "South East", "semi_detached", 120, "2007-2011", "B", "heat_pump", True, True, "triple", 3, True, True, True, 5800, 0, 530000),
    ("norwich", "Norwich terrace", "East", "terraced", 78, "1950-1966", "C", "gas_boiler", True, True, "double", 0, False, True, True, 2700, 9000, 230000),
    ("newcastle", "Newcastle detached", "North East", "detached", 163, "1983-1990", "E", "gas_boiler", False, False, "single", 0, False, True, True, 4800, 22200, 310000),
    ("birmingham", "Birmingham starter home", "West Midlands", "terraced", 74, "1930-1949", "D", "gas_boiler", None, True, "double", 0, False, True, False, 2500, 10100, 205000),
    ("exeter", "Exeter solar bungalow", "South West", "bungalow", 100, "1991-1995", "C", "gas_boiler", True, True, "double", 3, True, True, True, 1600, 8800, 345000),
]

FIELDS = ["property_id", "name", "region", "property_type", "floor_area_m2", "construction_age_band", "epc_rating", "heating_type", "loft_insulated", "wall_insulated", "glazing", "solar_kwp", "smart_controls", "roof_suitable", "outdoor_space", "annual_electricity_kwh", "annual_gas_kwh", "property_value_gbp"]

DEMOS = {row[0]: Property(**dict(zip(FIELDS, row))) for row in RAW}


def get_demo(id: str) -> Property:
    if id not in DEMOS:
        raise KeyError(f"Unknown demo property: {id}")
    return DEMOS[id].model_copy(deep=True)
