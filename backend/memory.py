"""Optional customer memory: local, pseudonymous, opt-in, with no account or remote tracking.

Completion is homeowner-declared. This demo never claims an upgrade was independently verified.
"""
from __future__ import annotations
import json
from typing import Literal
from pydantic import BaseModel, Field
from backend.schemas import Property
from backend.engines.retrofit import RETROFITS, eligibility, recommended_measures
from backend.engines.optimizer import optimize
from backend.engines.scoring import green_score
from backend.storage import connect

class CustomerMemory(BaseModel):
    completed_measures: list[str] = Field(default_factory=list)
    avoid_measures: list[str] = Field(default_factory=list)
    budget_gbp: float = Field(default=5000, ge=0, le=1000000)
    objective: Literal['money', 'energy', 'carbon'] = 'money'
    homeowner_note: str = Field(default='', max_length=500)
    last_response: dict[str, str] = Field(default_factory=dict)

class MemoryFeedback(BaseModel):
    measure: str
    decision: Literal['interested', 'not_interested', 'considering']

class MemoryPlanRequest(BaseModel):
    property: Property

def _validate_memory(m: CustomerMemory):
    for key in m.completed_measures + m.avoid_measures:
        if key not in RETROFITS:
            raise ValueError(f'Unknown retrofit in memory: {key}')
    if len(set(m.completed_measures)) != len(m.completed_measures) or len(set(m.avoid_measures)) != len(m.avoid_measures):
        raise ValueError('Memory retrofit lists cannot contain duplicates')
    if set(m.completed_measures) & set(m.avoid_measures):
        raise ValueError('A measure cannot be both completed and excluded')
    for key, value in m.last_response.items():
        if key not in RETROFITS or value not in ('interested', 'not_interested', 'considering'):
            raise ValueError('Memory responses must use known retrofits and allowed statuses')

def read_memory(session_id: str) -> CustomerMemory:
    with connect() as conn:
        row = conn.execute('SELECT memory_json FROM customer_memory WHERE id=?', (session_id,)).fetchone()
    return CustomerMemory.model_validate_json(row['memory_json']) if row else CustomerMemory()

def write_memory(session_id: str, state: CustomerMemory) -> CustomerMemory:
    _validate_memory(state)
    with connect() as conn:
        conn.execute('INSERT OR REPLACE INTO customer_memory(id,memory_json) VALUES(?,?)',
                     (session_id,state.model_dump_json()))
    return state

def clear_memory(session_id: str) -> dict:
    with connect() as conn:
        conn.execute('DELETE FROM customer_memory WHERE id=?', (session_id,))
    return {'deleted':True, 'session_id':session_id}

def apply_completed(p: Property, memory: CustomerMemory) -> Property:
    update = {}
    for key in memory.completed_measures:
        if key == 'loft_insulation': update['loft_insulated'] = True
        elif key == 'wall_insulation': update['wall_insulated'] = True
        elif key == 'double_glazing': update['glazing'] = 'double'
        elif key == 'smart_controls': update['smart_controls'] = True
        elif key == 'heat_pump': update['heating_type'] = 'heat_pump'
        elif key == 'solar_panels': update['solar_kwp'] = max(p.solar_kwp,3.0)
    return p.model_copy(update=update)

def personalized_plan(p: Property, memory: CustomerMemory) -> dict:
    _validate_memory(memory)
    updated = apply_completed(p,memory)
    excluded = set(memory.avoid_measures) | {k for k,v in memory.last_response.items() if v=='not_interested'}
    # Completed upgrades are recorded only as homeowner assertions; don't count their
    # hypothetical construction costs again in the proposed future package.
    permitted = [key for key in RETROFITS if key not in excluded and eligibility(updated,key)[0]]
    recs = [r for r in recommended_measures(updated) if r['id'] in permitted]
    optimized = optimize(updated,memory.budget_gbp,memory.objective,excluded=excluded)
    return {'memory':memory.model_dump(), 'property_after_self_reported_completions':updated.model_dump(),
            'score':green_score(updated),'recommendations':recs,'optimization':optimized,
            'excluded_from_search':sorted(excluded),
            'warnings':['Memory is local to this device/project; no authentication or cloud sync.',
                        'Completed upgrades are homeowner self-reports, not installer or EPC verification.',
                        'Energy, cost and property-value effects remain modelling assumptions.']}


def remember_feedback(session_id: str, feedback: MemoryFeedback) -> CustomerMemory:
    if feedback.measure not in RETROFITS:
        raise ValueError('Unknown retrofit')
    memory=read_memory(session_id)
    responses={**memory.last_response, feedback.measure:feedback.decision}
    memory=memory.model_copy(update={'last_response':responses})
    return write_memory(session_id,memory)
