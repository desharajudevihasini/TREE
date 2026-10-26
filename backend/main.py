"""Run: uvicorn backend.main:app --reload --port 8000"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.demo import DEMOS, get_demo
from backend.schemas import Property, ScenarioRequest, OptimizeRequest, QuestionRequest, RankRequest, ChatRequest, PropertyUpdate, ReportRequest
from backend.engines.scoring import green_score
from backend.engines.baseline import get_baseline
from backend.engines.retrofit import simulate, recommended_measures, RETROFITS
from backend.engines.optimizer import optimize, parallel_universes, retrofit_chess
from backend.engines.treeask import next_question
from backend.engines.ranking import rank_properties
from backend.companion.assistant import converse
from backend.storage import load_session, save_session

app = FastAPI(title="TREE API", version="0.1.0", description="Illustrative hackathon MVP, not certified energy advice")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health(): return {"ok": True, "app": "TREE", "version": "0.1.0", "data_mode": "hybrid_real_NEED_consumer_and_synthetic_demo"}


@app.get("/api/properties/demo")
def demos(): return [{"property_id": p.property_id, "name": p.name, "region": p.region, "epc_rating": p.epc_rating} for p in DEMOS.values()]


@app.get("/api/properties/{property_id}")
def property_by_id(property_id: str):
    try: return get_demo(property_id)
    except KeyError: raise HTTPException(404, "Demo property not found")


@app.post('/api/home/report')
def full_home_report(req: ReportRequest):
    from backend.engines.report import home_report
    return home_report(req.property,req.budget_gbp,req.objective)


@app.post('/api/scenarios/sensitivity')
def scenario_sensitivity(req: ScenarioRequest):
    from backend.engines.report import sensitivity
    try: return sensitivity(req.property,req.measures)
    except ValueError as exc: raise HTTPException(422,str(exc))


@app.post("/api/properties/quality")
def property_quality(p: Property):
    from backend.engines.data_quality import check_property
    return check_property(p)


@app.post("/api/score")
def score(p: Property): return green_score(p)


@app.post("/api/predict")
def predict(p: Property): return get_baseline(p)


@app.post("/api/retrofits/recommend")
def recommendations(p: Property): return {"retrofits": recommended_measures(p)}


@app.post("/api/retrofits/simulate")
def simulate_route(req: ScenarioRequest):
    try: return simulate(req.property, req.measures, req.electricity_price_gbp_kwh, req.gas_price_gbp_kwh)
    except ValueError as e: raise HTTPException(422, str(e))


@app.post("/api/retrofits/chess")
def chess(req: ScenarioRequest):
    try: return retrofit_chess(req.property, req.measures)
    except ValueError as e: raise HTTPException(422, str(e))


@app.post("/api/optimize")
def optimization(req: OptimizeRequest):
    try: return optimize(req.property, req.budget_gbp, req.objective)
    except ValueError as e: raise HTTPException(422, str(e))


@app.post("/api/treeask/next-question")
def question(req: QuestionRequest):
    try: return next_question(req.property, req.budget_gbp, req.objective, req.asked)
    except ValueError as e: raise HTTPException(422, str(e))


@app.post("/api/scenarios/compare")
def compare(req: OptimizeRequest): return parallel_universes(req.property, req.budget_gbp)


@app.post("/api/properties/rank")
def ranking(req: RankRequest): return {"properties": rank_properties(req.properties), "data_label": "synthetic_demo"}


@app.get("/api/properties/ranking/demo")
def demo_ranking(): return {"properties": rank_properties(list(DEMOS.values())), "data_label": "synthetic_demo"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    try: return converse(req)
    except ValueError as e: raise HTTPException(422, str(e))


@app.get("/api/sessions/{session_id}")
def session_details(session_id: str, property_id: str = "manchester"):
    try:
        state = load_session(session_id, property_id)
        return {"session_id": session_id, "property": state["property"], "messages": state["messages"], "pending": state["pending"]}
    except KeyError: raise HTTPException(404, "Property not found")


@app.patch("/api/sessions/{session_id}/property")
def edit_property(session_id: str, update: PropertyUpdate):
    try: s = load_session(session_id, "manchester")
    except KeyError: raise HTTPException(404, "Property not found")
    permitted = {"loft_insulated", "wall_insulated", "glazing", "roof_suitable", "outdoor_space", "smart_controls", "heating_type", "annual_electricity_kwh", "annual_gas_kwh", "budget_gbp"}
    if not set(update.changes).issubset(permitted): raise HTTPException(422, "One or more fields cannot be edited")
    try: s["property"] = Property.model_validate({**s["property"].model_dump(), **update.changes})
    except Exception as e: raise HTTPException(422, str(e))
    save_session(s)
    return {"property": s["property"], "evidence_source": update.source, "warning": "This local demo records the current property state only; a full evidence ledger is not yet implemented."}


from pydantic import BaseModel as _PydanticBaseModel

class EPCHypothesis(_PydanticBaseModel):
    property: Property
    hypothetical_epc_after: str

@app.post('/api/valuation/epc-hypothesis')
def valuation_hypothesis(req: EPCHypothesis):
    from backend.engines.valuation import evidence_based_epc_hypothesis
    return evidence_based_epc_hypothesis(req.property,req.hypothetical_epc_after.upper())

@app.get('/api/methodology/carbon-factors')
def carbon_factor_methodology():
    from backend.engines.carbon import current_factors
    return current_factors()

@app.get("/api/evaluation/summary")
def eval_summary():
    return {"status": "real_UK_energy_benchmarked_separately__retrofit_outcomes_not_validated", "model": "real_NEED_coarse_for_new_homes_plus_synthetic_demo_fallback_and_separate_NEED_research",
            "score": "official weights, illustrative subscore mappings", "energy": "documented illustrative physics approximations",
            "valuation": "auto-retrofit toy sensitivity only; separate explicit EPC-to-C observational research hypothesis endpoint",
            "carbon": "DESNZ 2026 location-based grid electricity and natural gas combustion factors; scope explicit",
            "ml_metrics": "See /api/evaluation/consumer-need (homeowner-compatible model) and /api/evaluation/need-challenger and /api/evaluation/real-world (research baselines).",
            "note": "The new-home cold-start estimator is now NEED-trained, but its held-out population metrics do not verify any individual home. None of the NEED benchmarks validates retrofit outcomes or property prices."}


@app.get('/api/evaluation/consumer-need')
def consumer_need_report():
    path=Path(__file__).resolve().parent.parent/'ml'/'models'/'consumer_need'/'report.json'
    if not path.exists():raise HTTPException(404,'Train: python -m ml.consumer_need --train')
    return json.loads(path.read_text())

@app.get('/api/evaluation/retrofit-external-context')
def retrofit_external_context():
    from evaluation.retrofit_reference_audit import build
    return build()

@app.get('/api/evaluation/need-slices')
def need_slice_audit():
    path = Path(__file__).resolve().parent.parent / 'evaluation' / 'need_slice_analysis.json'
    if not path.exists(): raise HTTPException(404,'Run python -m evaluation.need_slices --csv path/to/NEED.csv')
    return json.loads(path.read_text())


@app.get("/api/evaluation/need-challenger")
def need_challenger_report():
    path = Path(__file__).resolve().parent.parent / "evaluation" / "need_challenger_report.json"
    if not path.exists():
        raise HTTPException(404, "No NEED challenger evaluation has been run")
    return json.loads(path.read_text())


@app.post("/api/predict/need-research")
def need_research_predict(fields: dict[str, str | None]):
    """Opt-in real-data-trained model. Requires official NEED categories."""
    from ml.serve_need import predict
    try:
        return predict(fields)
    except ValueError as error:
        raise HTTPException(422, str(error))
    except FileNotFoundError as error:
        raise HTTPException(503, str(error))


@app.get("/api/evaluation/synthetic-ml")
def synthetic_ml_report():
    path = Path(__file__).resolve().parent.parent / "evaluation" / "synthetic_ml_report.json"
    if not path.exists(): raise HTTPException(404, "Run python -m ml.train to create benchmark")
    return json.loads(path.read_text())

@app.get("/api/evaluation/real-world")
def real_world_ml_report():
    """Show real NEED benchmark only AFTER it has actually been run."""
    file = Path(__file__).resolve().parent.parent / "evaluation" / "need_real_validation.json"
    if not file.exists():
        raise HTTPException(404, "No observed-data evaluation yet. Run python -m ml.validate_need with the official NEED CSV.")
    return json.loads(file.read_text())


@app.get("/api/evaluation/dialogue-contract")
def dialogue_contract_report():
    """Tests for deterministic API/evidence contracts, NOT provider LLM accuracy."""
    path = Path(__file__).resolve().parent.parent / 'evaluation' / 'deterministic_dialogue_contract.json'
    if not path.exists():
        raise HTTPException(404, 'Run python -m evaluation.judge_prompt_suite first')
    report = json.loads(path.read_text())
    return {key: value for key, value in report.items() if key != 'results'}


@app.get("/api/evaluation/treeask-benchmark")
def treeask_benchmark():
    """Reproducible synthetic comparison; never label this as a real-world study."""
    path = Path(__file__).resolve().parent.parent / "evaluation" / "treeask_synthetic_benchmark.json"
    if not path.exists():
        raise HTTPException(404, "Run python -m evaluation.treeask_benchmark first.")
    return json.loads(path.read_text())




# Optional local customer memory (PPT slide 12). Data is never sent to Gemini.
from backend.memory import CustomerMemory, MemoryPlanRequest, MemoryFeedback, read_memory, write_memory, clear_memory, personalized_plan, remember_feedback

@app.get('/api/memory/{session_id}')
def get_customer_memory(session_id: str):
    return read_memory(session_id)

@app.put('/api/memory/{session_id}')
def save_customer_memory(session_id: str, memory: CustomerMemory):
    try: return write_memory(session_id, memory)
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.post('/api/memory/{session_id}/feedback')
def memory_feedback(session_id: str, feedback: MemoryFeedback):
    try: return remember_feedback(session_id, feedback)
    except ValueError as exc: raise HTTPException(422,str(exc))


@app.delete('/api/memory/{session_id}')
def delete_customer_memory(session_id: str):
    return clear_memory(session_id)

@app.post('/api/memory/{session_id}/plan')
def plan_with_customer_memory(session_id: str, req: MemoryPlanRequest):
    return personalized_plan(req.property,read_memory(session_id))


# Location-first EPC and evidence-driven onboarding. Nothing is stored server-side.
from backend.intake import search_epc, record_to_property, QuestionsPayload, next_intake_question, verify_epc_selection
from backend.home_extras import Household, appliance_audit, green_extensions, household_notifications, inspect_media

class Coordinates(_PydanticBaseModel):
    latitude: float
    longitude: float

@app.post('/api/intake/geolocate-postcode')
def locate_uk_postcode(coords: Coordinates):
    """Only used when the homeowner explicitly requests geolocation."""
    from backend.location import postcode_near_coordinates
    try: return postcode_near_coordinates(coords.latitude, coords.longitude)
    except ValueError as exc: raise HTTPException(422, str(exc))

@app.post('/api/score/explain')
def score_explain(p: Property):
    """All seven weighted score components, raw inputs and source explanations."""
    from backend.engines.explain import explain_score
    return explain_score(p)

@app.get('/api/intake/epc/search')
def epc_search(postcode: str = Query(min_length=5,max_length=12)):
    try: return search_epc(postcode)
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.post('/api/intake/epc/confirm')
def epc_confirm(record: dict):
    # Confirmation is only an explicit user action on the selected record.
    # An unrecognized/unknown provider field is never fabricated.
    try: return record_to_property(verify_epc_selection(record),confirmed=True)
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.post('/api/intake/next-question')
def intake_next(req: QuestionsPayload):
    return next_intake_question(req.property, req.answered, req.budget_gbp, req.objective)

@app.post('/api/household/appliances')
def household_appliances(req: Household):return appliance_audit(req)

@app.post('/api/household/extensions')
def household_extensions(req: Household):return green_extensions(req)

@app.post('/api/household/notifications')
def household_alerts(req: Household):return {'notifications':household_notifications(req),'delivery':'in_app_while_site_open_only'}

@app.post('/api/household/finance-tips')
def household_finance_tips(p: Property):
    from backend.home_extras import finance_notifications
    return {'notifications': finance_notifications(p), 'delivery': 'in_app_only',
            'warning': 'Modelled savings, not financial advice or eligibility for subsidies.'}

@app.post('/api/evidence/inspect')
async def inspect_upload(file: UploadFile = File(...)):
    # Block oversized uploads while streaming, never persist attachments.
    chunks=[];size=0
    try:
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size>20*1024*1024:raise HTTPException(413,'File too large; maximum 20 MB')
            chunks.append(chunk)
        return inspect_media(b''.join(chunks),file.filename or '',file.content_type or '')
    except ValueError as exc:raise HTTPException(422,str(exc))
    finally:await file.close()

# Optional vision is separated from evidence ingestion and NEVER changes scores.
@app.post('/api/evidence/vision-candidates')
async def optional_visual_cues(file: UploadFile = File(...), consent: bool = Form(False)):
    from backend.optional_vision import review_image
    try:
        data=await file.read(4*1024*1024+1)
        if len(data)>4*1024*1024:raise HTTPException(413,'Vision images must be under 4 MB')
        return review_image(data,file.filename or '',consent)
    except PermissionError as exc:raise HTTPException(403,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))
    except RuntimeError as exc:raise HTTPException(503,str(exc))
    finally:await file.close()

# This is a zero-npm, fully local web build for overnight reliability.
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

@app.get("/")
def home(): return FileResponse(str(FRONTEND / "index.html"))

@app.get("/app")
def complete_home_workflow():
    """The current location-first, evidence-aware frontend backed by the SAME models."""
    return FileResponse(str(FRONTEND / "basic.html"))

@app.get("/studio")
def full_design_preview():
    """Retain the previous design-preview path for existing project links."""
    return FileResponse(str(FRONTEND / "index.html"))
