"""Non-calibrating comparison against external UK NEED 2026 retrofit-outcome research.

Does not fit the simulator to the observational reference, claim causal
validation, or compare the same households. It surfaces the real-world gap.
"""
from __future__ import annotations
import json
from pathlib import Path
from statistics import median
from backend.demo import DEMOS
from backend.engines.retrofit import simulate,eligibility

SOURCE='https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026-accessible-webpage'
OUT=Path(__file__).resolve().parent/'retrofit_external_reference.json'


def build():
    examples=[]
    for p in DEMOS.values():
        if p.heating_type!='gas_boiler' or not eligibility(p,'wall_insulation')[0]:continue
        if p.annual_gas_kwh is None or p.annual_gas_kwh<=0:continue
        pred=simulate(p,['wall_insulation'])
        examples.append({'home':p.property_id,'status':'fictional_demo',
                         'estimated_wall_upgrade_gas_saving_pct':round(pred['savings']['gas_kwh']/p.annual_gas_kwh*100,2),
                         'assumptions':'generic wall heat-loss multiplier; not proven solid-wall insulation'})
    return {
        'status':'external_observational_context_only_not_calibration_or_validation',
        'official_research':'DESNZ NEED 2026 summary of analysis, Chapter 3',
        'official_reference':{'retrofit':'solid wall insulation', 'installation_year':2023,
                              'observation_year':2024, 'median_gas_savings_percent':17,
                              'reference_population':'treated England/Wales non-flat homes with selected comparable controls',
                              'source_url':SOURCE},
        'tree_model':{'retrofit':'generic wall insulation',
                      'examples':examples,
                      'median_percent_on_synthetic_demo_homes':round(median([x['estimated_wall_upgrade_gas_saving_pct'] for x in examples]),2) if examples else None},
        'interpretation':('The official 17% figure is a population-level comparator-adjusted median for SOLID wall '
                          'insulation. TREE models generic wall insulation using assumed heat multipliers on '
                          'different, entirely fictional homes. These are not like-for-like, do not validate '
                          'a household prediction, and are not appropriate to replace the model coefficient. '
                          'NEED found solid wall plus loft at ~14% in a separate sample, demonstrating that '
                          'headline percentages cannot simply be added.'),
    }

if __name__=='__main__':
    report=build();OUT.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
