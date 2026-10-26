"""Single reproducible property report; Python owns EVERY number in the UI."""
from __future__ import annotations
from backend.schemas import Property
from backend.engines.baseline import get_baseline
from backend.engines.scoring import green_score
from backend.engines.data_quality import check_property
from backend.engines.retrofit import recommended_measures, simulate
from backend.engines.optimizer import optimize
from backend.engines.carbon import carbon_change


def sensitivity(p: Property, measures: list[str]) -> dict:
    """Explicit scenario stress test, NOT a calibrated probability/confidence interval.

    Varies annual modelled fuel changes by +/-20% with fixed baseline, and
    independently varies installation quotes by +/-20%.
    """
    result = simulate(p, measures)
    baseline = result['baseline']
    eprice, gprice = p.electricity_price_gbp_kwh,p.gas_price_gbp_kwh
    outcomes = []
    for label,factor in [('lower_effect',.8),('central',1),('higher_effect',1.2)]:
        e = round(baseline['grid_electricity_kwh'] - max(-1e9,min(baseline['grid_electricity_kwh'],result['savings']['electricity_kwh']*factor)),2)
        g = round(baseline['gas_kwh'] - max(-1e9,min(baseline['gas_kwh'],result['savings']['gas_kwh']*factor)),2)
        delta_e = round(baseline['grid_electricity_kwh'] - e,2)
        delta_g = round(baseline['gas_kwh'] - g,2)
        outcomes.append({'name':label,'grid_electricity_kwh':e,'gas_kwh':g,
                         'electricity_savings_kwh':delta_e,'gas_savings_kwh':delta_g,
                         'bill_saving_gbp':round(delta_e*eprice+delta_g*gprice,2),
                         'carbon_kg_co2e':carbon_change(delta_e,delta_g)['reduction_kg_co2e']})
    cost=result['cost_gbp']
    return {'method':'deterministic_assumption_sensitivity_not_statistical_confidence',
            'scenario_measures':measures,'factors':[.8,1,1.2], 'outcomes':outcomes,
            'installation_cost_range_gbp':[round(cost*.8,2),round(cost*1.2,2)],
            'limitation':'Illustrative +/-20% stress test on computed per-fuel changes and installed cost. Bounds are arbitrary; no calibrated probability, engineering survey or market evidence.'}


def home_report(p: Property, budget_gbp: float | None = None, objective: str = 'money') -> dict:
    baseline = get_baseline(p)
    score = green_score(p,baseline)
    chosen_budget = p.budget_gbp if budget_gbp is None else budget_gbp
    opt = optimize(p, chosen_budget, objective)
    technical = optimize(p, 30000, 'energy')['best']
    purchased = baseline['electricity_import_kwh'] + baseline['gas_kwh']
    improvement = technical['savings']['improvement_potential_pct'] if purchased>0 and p.annual_electricity_kwh is not None and p.annual_gas_kwh is not None else None
    quality=check_property(p)
    return {
      'property':p.model_dump(), 'baseline':baseline, 'score':score,
      'efficiency_detector':{'is_poor':score['classification'] in ('Poor','Very poor'),
                             'classification':score['classification'],
                             'threshold_definition':'Poor: 30–49; Very poor: 0–29'},
      'recommendations':recommended_measures(p), 'budget_plan':opt,
      'unconstrained_reference':{'max_budget_gbp':30000,'reference_measures':technical['measures'],
                                 'improvement_potential_pct':improvement,
                                 'warning':'Unavailable unless both fuel baselines are explicitly provided.' if improvement is None else 'Illustrative feasible £30k package, not a full building survey.'},
      'sensitivity':sensitivity(p,opt['best']['measures']), 'data_quality':quality,
      'source_trace':{'score':'official Lloyds weights; demonstrator subscore mappings',
                      'energy':'observed or homeowner-confirmed annual bills where provided; otherwise NEED-trained coarse consumer model for new homes, synthetic demo fallback or documented heuristic',
                      'retrofit':'multiplicative annual model with declared assumptions, not measured retrofit data',
                      'carbon':'deterministic per-fuel emissions using illustrative configurable factors',
                      'property_value':'illustrative sensitivity range only, not empirical valuation',
                      'real_UK_model':'cold-start consumer model uses NEED 2026 (type + grouped EPC only); separate richer research estimator remains opt-in'},
      'disclaimer':'Scenario estimates are not EPC certificates, retrofit guarantees or professional property valuations.'
    }
