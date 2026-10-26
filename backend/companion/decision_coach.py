"""Readable, evidence-first decision coach.

TREE asks a relevant follow-up when important data is missing. It never lets an
LLM invent kWh, savings or value numbers. Hard calculations are delegated to
our tested core functions. No external service needed for fallback responses.
"""
from __future__ import annotations
import re
from backend.schemas import Property
from backend.engines.baseline import get_baseline
from backend.engines.scoring import green_score
from backend.engines.retrofit import recommended_measures, simulate, RETROFITS
from backend.engines.optimizer import optimize
from backend.engines.carbon import current_factors
from backend.engines.valuation import evidence_based_epc_hypothesis
from backend.engines.explain import explain_score


def decision_coach(p: Property, question: str) -> dict | None:
    """Return answer + machine evidence + follow-up, or None for ordinary TreeAsk.

    Designed for questions homeowners actually ask, including challenges to
    the numbers, financing, feasibility, operational carbon and household habits.
    """
    q = question.casefold()
    plan = None
    if any(x in q for x in ('why my score', 'explain my score', 'score breakdown', 'score calculated', 'green home score calculated')):
        detail = explain_score(p)
        lowest = sorted(detail['components'], key=lambda c: c['subscore_0_100'])[:2]
        return {'mode': 'score_why', 'answer': (
            f"Your score is {detail['score']}/100. The two lowest subscores are "
            + ', '.join(f"{x['id'].replace('_',' ')} ({x['subscore_0_100']}/100)" for x in lowest)
            + '. Each component uses the exact official PPT weight, with a documented TREE-specific mapping. '
            + ('The score is provisional because some evidence is missing.' if detail['provisional'] else 'All core score inputs are present.')
            + ' The evidence table below shows every input and contribution.'),
            'evidence': {'score_explanation': detail},
            'follow_up': ('Would you like to confirm an unknown property detail?' if detail['provisional'] else 'Would you like to compare a retrofit package?')}
    if any(x in q for x in ('why recommend', 'why this recommendation', 'why that upgrade','challenge recommendation', 'prove recommendation','why not')):
        recommendations = recommended_measures(p)
        plan = optimize(p, p.budget_gbp)
        best = plan['best']
        if not best['measures']:
            reply = 'No affordable, confirmed-feasible upgrade was selected. That may reflect your budget or unresolved property suitability, not proof that your home needs no improvements.'
        else:
            reply = ('Under your £' + f"{p.budget_gbp:,.0f}" + ' budget, the optimizer selected '
                     + ', '.join(best['labels']) + f" for an illustrative £{best['cost_gbp']:,.0f} install cost and £{best['annual_bill_savings_gbp']:,.0f}/year estimated bill change. "
                     + 'It tests feasible combinations and their interactions; it does not simply add every single-upgrade saving. See model assumptions and suitability below.')
        return {'mode': 'recommendation_challenge', 'answer': reply,
                'evidence': {'optimization': plan, 'recommendations': recommendations},
                'follow_up': 'What budget can you comfortably invest, or is there an upgrade you want to avoid?'}
    if any(x in q for x in ('carbon factor', 'carbon calculated', 'co2 calculated', 'emission factor', 'environmental impact', 'co₂ calculated')):
        factors = current_factors()
        return {'mode': 'carbon_why', 'answer': (
            'Operational carbon change = electricity kWh saved × electricity emissions factor '
            '+ gas kWh saved × gas combustion factor. Electricity can increase after a heat-pump change, so we keep negative electricity savings. '
            'The carbon endpoint below includes the factor year and boundaries; it excludes embodied carbon and installed-product manufacturing.'),
            'evidence': {'carbon_factors': factors},
            'follow_up': 'Should we compare carbon savings or money savings for your home?'}
    if any(x in q for x in ('house value', 'property value', 'value estimate','resale value','house price', 'sale price')):
        # Never claim green-score change implies an observed or certified EPC change.
        if p.property_value_gbp is None:
            return {'mode': 'property_value', 'answer': 'I cannot estimate a property-specific sale-price change without a current value or comparable sale evidence. Even with a value, a retrofit does not automatically change the official EPC grade. Our historical EPC study can illustrate a verified hypothetical D/E/F→C transition, not predict your sale price.',
                    'evidence': {'status': 'unavailable'}, 'follow_up': 'Do you have an independently estimated current home value and a confirmed EPC rating?'}
        hypothesis = evidence_based_epc_hypothesis(p, 'C')
        if hypothesis['status'] == 'unavailable':
            answer = 'A current property value is available, but published D/E/F→C observations do not support automatically projecting this home’s resale value. No market uplift is claimed.'
        else:
            answer = (f"If, and only if, an EPC assessment separately confirmed a change from {p.epc_rating} to C, historical national repeat-sales studies observed {hypothesis['uplift_percent_range'][0]:g}–{hypothesis['uplift_percent_range'][1]:g}% differences in the relevant comparisons. This is not a causal forecast or an EPC reassessment.")
        return {'mode': 'property_value', 'answer': answer, 'evidence': {'epc_research_hypothesis': hypothesis},
                'follow_up': 'Would you rather compare estimated annual bills and payback, which TREE can calculate directly?'}
    if any(x in q for x in ('water','rainwater','greywater','groundwater','kitchen waste','biogas','compost','solar cooker','recycl','daily tips','daily habits')):
        topics=[]
        if any(x in q for x in ('rainwater','water','groundwater','greywater')):
            topics.append('Rainwater collection or appropriate greywater reuse may reduce mains-water use, but requires a site/plumbing and safety check; it does not directly earn energy-score credit.')
        if any(x in q for x in ('kitchen waste','biogas','compost')):
            topics.append('Composting diverts organic waste. Small household biogas needs suitable feedstock, gas safety and a professional design; we cannot claim automatic electricity generation from scraps.')
        if any(x in q for x in ('solar cooker', 'solar heat')):
            topics.append('Solar cooking and solar hot water depend on weather, usable roof/space, demand and installation constraints. Without verified data, TREE does not invent annual kWh savings.')
        if 'recycl' in q or not topics:
            topics.append('Simple habits include recycling, reducing avoidable standby use, checking actual bills and using safe appliance schedules. These are advisory and separate from the official weighted score.')
        return {'mode': 'household_habits', 'answer': ' '.join(topics), 'evidence': {'official_score_credit': False, 'quantified_kwh': None},
                'follow_up': 'Do you have a garden, safe water storage and space for a compost bin?'}
    if any(x in q for x in ('budget','afford','finance','payback','cheap','worth it','cost effective','best upgrade','best option','return on investment')) and not (
        ('i want' in q or 'we want' in q) and any(x in q for x in ('solar','loft','wall','heat pump','glazing'))
    ):
        plan = optimize(p, p.budget_gbp, 'money')
        best = plan['best']
        question_next = 'Could you share your maximum upfront budget in pounds? You can also type “my budget is £3000”.'
        if best['measures']:
            answer = (f"Within your stated £{p.budget_gbp:,.0f} limit, TREE's current bill-savings objective picks "
                     + ', '.join(best['labels']) + f". Installation assumptions total £{best['cost_gbp']:,.0f}; modelled annual bill saving £{best['annual_bill_savings_gbp']:,.0f}; "
                     + (f"simple payback {best['simple_payback_years']:g} years. " if best['simple_payback_years'] is not None else 'payback unavailable. ')
                     + 'Upfront costs are not contractor quotes; we do not assume loans or eligibility for grants.')
        else:
            answer = ('No confirmed feasible retrofit currently fits the specified budget in this small option set. '
                      'We need to clarify constraints instead of pushing you into spending more.')
        return {'mode': 'budget', 'answer': answer, 'evidence': {'optimization': plan}, 'follow_up': question_next}
    if any(x in q for x in ('how accurate', 'real world', 'where data', 'training data', 'validation','trust the model', 'is this reliable')):
        return {'mode': 'model_evidence', 'answer': (
            'For new homes, TREE has a coarse consumption model trained and evaluated on anonymised UK NEED records using held-out data. Its error is nontrivial at individual-home level. '
            'Retrofit effects are a separately documented, interacting engineering approximation—not observed treatment-outcome predictions. '
            'Public 2026 carbon factors are used for calculations. Sale-value effects are not independently calibrated.'),
            'evidence': {'benchmark_endpoint': '/api/evaluation/consumer-need', 'assumptions': '/docs'},
            'follow_up': 'Would you like to add a full-year energy bill so TREE depends less on estimated consumption?'}
    return None
