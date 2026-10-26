"""Reproducible dialogue contract suite; not a provider LLM groundedness study.

Run: python -m evaluation.judge_prompt_suite
Optional live Gemini: python -m evaluation.judge_prompt_suite --gemini
Live mode records a review sheet. Human evaluation is still required for
organiser LLM targets; deterministic rules cannot certify those targets.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from backend.demo import DEMOS
from backend.main import app
import backend.storage as storage

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('What if I install solar panels?', 'solar_panels'),
    ('What if I install a heat pump?', 'heat_pump'),
    ('What if I install loft insulation?', 'loft_insulation'),
    ('What if electricity prices double?', 'what_if'),
    ('What if gas prices double?', 'what_if'),
    ('How is my Green Home Score calculated?', 'score_why'),
    ('Are these actual Lloyds customer data?', 'provenance'),
    ('What if I install a nuclear microreactor?', 'clarification'),
    ('What is my property value impact?', 'value'),
]


def evaluate(use_gemini:bool=False)->dict:
    if use_gemini and not os.getenv('GEMINI_API_KEY'):
        raise ValueError('Provide GEMINI_API_KEY to perform a live provider test. Otherwise run deterministic mode.')
    records=[]
    with TemporaryDirectory(prefix='tree_judge_') as t:
        previous=storage.DB_FILE
        storage.DB_FILE=str(Path(t)/'sessions.sqlite')
        try:
            client=TestClient(app)
            for home in DEMOS:
                for prompt,kind in CASES:
                    request={'property_id':home,'message':prompt,'use_gemini':use_gemini}
                    r=client.post('/api/chat',json=request)
                    data=r.json() if r.status_code==200 else {}
                    passed = r.status_code == 200
                    reason = ''
                    if passed:
                        if kind in ('solar_panels','heat_pump','loft_insulation'):
                            passed=data['mode'] in ('what_if','infeasible')
                            if data['mode']=='what_if':
                                result=data['data']['scenario']
                                passed=passed and kind in result['measures']
                                for value in (result['cost_gbp'],result['after_annual_bill_gbp']):
                                    passed=passed and f'{value:,.0f}' in data['message']
                        elif kind == 'what_if':
                            passed=data['mode']=='what_if' and bool(data['data']['tariff_overrides'])
                        elif kind == 'score_why':
                            score = data.get('data',{}).get('score_explanation',{})
                            components = score.get('components',[])
                            passed = (data.get('mode') == 'score_why' and len(components) == 7
                                      and str(score.get('score')) in data.get('message','')
                                      and abs(sum(x['contribution_points'] for x in components)
                                              - score.get('score',0)) <= 0.6)
                        else:
                            passed=data['mode']==kind
                        if not passed: reason='Mode, evidence or numeric output not aligned with supported request'
                    else:reason=str(data.get('detail','HTTP error'))
                    records.append({'home':home,'prompt':prompt,'result_mode':data.get('mode'),
                                    'source':data.get('source'),'contract_pass':bool(passed),
                                    'reason':reason,'response':data.get('message','')})
        finally:
            storage.DB_FILE=previous
    passed=sum(x['contract_pass'] for x in records)
    return {'cases':len(records),'contract_passed':passed,'contract_failed':len(records)-passed,
            'mode':'provider_requested_with_guard_and_fallback' if use_gemini else 'deterministic_no_provider',
            'not_a_provider_llm_groundedness_metric':True,
            'organiser_llm_targets_verified':False,
            'method':'Expected intent mode plus evidence-linked numeric comparison; not a semantic claim audit.',
            'review_required':'To claim 90% groundedness and factual accuracy, run provider outputs and have independent human claim-level scoring.',
            'results':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--gemini',action='store_true')
    args=parser.parse_args()
    report=evaluate(use_gemini=args.gemini)
    out=ROOT/'evaluation'/('live_gemini_review_sheet.json' if args.gemini else 'deterministic_dialogue_contract.json')
    out.write_text(json.dumps(report,indent=2))
    print(f"{report['contract_passed']}/{report['cases']} evidence-contract checks passed (mode={report['mode']}).")
    print(f'Written to {out}. Not an LLM factuality score.')
