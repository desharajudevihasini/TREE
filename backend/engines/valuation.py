"""Explicitly synthetic valuation illustration; not evidence of real sales-price uplift."""
from backend.schemas import Property


def property_value_impact(p: Property, before_score: int, after_score: int) -> dict:
    if p.property_value_gbp is None or p.property_value_gbp <= 0:
        return {"status": "unavailable", "reason": "No property-value baseline or validated market data.", "baseline_gbp": None,
                "after_range_gbp": None, "potential_uplift_range_gbp": None}
    delta = max(0, after_score - before_score)
    # Toy scenario: score delta translated into an assumed 0 to 2% notional uplift.
    # This IS NOT a learned, causal, or empirically established valuation relationship.
    lower_rate = min(.01, delta * .00025)
    upper_rate = min(.02, delta * .00060)
    base = p.property_value_gbp
    return {"status": "illustrative_only_not_market_validated", "baseline_gbp": round(base),
            "after_range_gbp": [round(base * (1 + lower_rate)), round(base * (1 + upper_rate))],
            "potential_uplift_range_gbp": [round(base * lower_rate), round(base * upper_rate)],
            "assumed_uplift_percent_range": [round(lower_rate * 100, 2), round(upper_rate * 100, 2)],
            "market_controls": {"region": p.region, "property_type": p.property_type, "floor_area_m2": p.floor_area_m2},
            "warning": "Synthetic scenario only. Not derived from historical property-sale evidence; no causal effect established. DO NOT claim a real market valuation uplift."}


# Observational **repeat-sale** associations from Rightmove's public reports.
# These are *not* causal estimates or an independently calibrated address model.
# A customer must explicitly choose a hypothetical EPC transition. TREE never
# converts its Green Home Score or efficiency proxy into a new official EPC.
RESEARCH_TO_C = {
    'D': (3.0, 4.0),  # Rightmove 2023 and 2021 studies, respectively
    'E': (7.0, 8.0),
    'F': (15.0, 16.0),
}
RESEARCH_SOURCES = [
    {
        'title': 'Rightmove Greener Homes repeat-sales study (2023)',
        'url': 'https://www.rightmove.co.uk/news/articles/property-news/green-premium-epc-ratings/',
        'description': '300,000 repeat-sale properties; inflation-adjusted historical observed prices, D/E/F to C.'
    },
    {
        'title': 'Rightmove original greener home upgrades report (2021)',
        'url': 'https://www.rightmove.co.uk/press-centre/green-upgrades-help-sellers-pocket-up-to-16-more-for-their-home/',
        'description': 'Over 200,000 repeat-sales; historical size and inflation adjustments, D/E/F to C.'
    },
    {
        'title': 'IFS 2026 information disclosure and energy efficiency valuation research',
        'url': 'https://ifs.org.uk/publications/information-disclosure-and-valuation-energy-efficiency-housing-markets',
        'description': 'Independent study finds 1–3% average higher-efficiency premiums nationally, and substantial geography dependence; different comparison and methods.'
    },
]


def evidence_based_epc_hypothesis(p: Property, hypothetical_epc_after: str) -> dict:
    """Explicit EPC *hypothesis* evaluated from published historical associations.

    Distinct from the production score: no EPC change is inferred from retrofits.
    The span between 2021 and 2023 point estimates is a SCENARIO RANGE, not a
    calibrated confidence interval or a promise of uplift.
    """
    source = p.epc_rating
    if p.property_value_gbp is None or p.property_value_gbp <= 0:
        return {'status': 'unavailable', 'reason': 'A current market-value estimate is required.',
                'after_range_gbp': None, 'sources': RESEARCH_SOURCES}
    if hypothetical_epc_after != 'C' or source not in RESEARCH_TO_C:
        return {'status': 'unavailable',
                'reason': 'Published D/E/F→C repeat-sales reference rates cannot support this transition; no estimate made.',
                'after_range_gbp': None, 'sources': RESEARCH_SOURCES}
    lower, upper = RESEARCH_TO_C[source]
    current = float(p.property_value_gbp)
    return {
        'status': 'observational_reference_scenario_not_causal',
        'current_epc': source,
        'hypothetical_epc_after': 'C',
        'hypothetical_not_issued_epc_certificate': True,
        'baseline_gbp': round(current),
        'uplift_percent_range': [lower,upper],
        'potential_uplift_range_gbp': [round(current*lower/100),round(current*upper/100)],
        'after_range_gbp': [round(current*(1+lower/100)),round(current*(1+upper/100))],
        'fixed_home_characteristics': {'region':p.region, 'property_type':p.property_type,
                                        'floor_area_m2':p.floor_area_m2},
        'sources': RESEARCH_SOURCES,
        'warning': ('Illustrative application of TWO historical national observational repeat-sale study rates. '
                    'These rates are not a confidence interval, property-specific valuation, causal retrofit effect '
                    'or forecast. Region, local market trends, tenure and upgrades are NOT individually calibrated. '
                    'The IFS 2026 independent comparison reports different premiums, showing study sensitivity.'),
    }
