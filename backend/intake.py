"""Location-first, evidence-labelled EPC ingestion and adaptive homeowner verification.

No API credentials embedded. No address caching. Never claim postcode identifies a home.
Configure TREE_EPC_SEARCH_URL and TREE_EPC_AUTHORIZATION for a licensed EPC
provider. The official 2026 platform requires registered API access.
"""
from __future__ import annotations
import csv
import io
import os
import re
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from datetime import datetime
import httpx
from pydantic import BaseModel, Field
from backend.schemas import Property
from backend.engines.treeask import next_question

# Sign EPC selections without keeping homeowner addresses in a server-side cache.
_EPC_SIGNING_SECRET=secrets.token_bytes(32)

def sign_epc_record(record: dict) -> dict:
    expires=int(time.time())+900
    canonical=json.dumps({'record':record,'expires':expires},sort_keys=True,separators=(',',':'),default=str).encode()
    signature=hmac.new(_EPC_SIGNING_SECRET,canonical,hashlib.sha256).hexdigest()
    return {'record':record,'expires':expires,'signature':signature}

def verify_epc_selection(data:dict) -> dict:
    record=data.get('record');expires=data.get('expires');sig=data.get('signature','')
    if not isinstance(record,dict) or not isinstance(expires,int) or expires<int(time.time()) or expires>int(time.time())+900:
        raise ValueError('Choose a recent EPC result from your postcode search; old or unsourced records are not accepted.')
    expected=sign_epc_canonical(record,expires)
    if not isinstance(sig,str) or not hmac.compare_digest(sig,expected):
        raise ValueError('Unverified EPC selection. Please search and select the property again.')
    return record

def sign_epc_canonical(record:dict,expires:int)->str:
    canonical=json.dumps({'record':record,'expires':expires},sort_keys=True,separators=(',',':'),default=str).encode()
    return hmac.new(_EPC_SIGNING_SECRET,canonical,hashlib.sha256).hexdigest()

POSTCODE = re.compile(r"^(GIR\s?0AA|(?:[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}))$", re.I)


def normalize_postcode(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value.strip().upper())
    if not POSTCODE.fullmatch(cleaned):
        raise ValueError("Enter a valid UK postcode (for example SW1A 1AA).")
    return cleaned[:-3] + " " + cleaned[-3:]


def safe_text(v: Any) -> str:
    if v is None: return ""
    return str(v).strip()


def get_key(record: dict, *names: str) -> Any:
    lowered = {str(k).replace("_","-").lower():v for k,v in record.items()}
    for name in names:
        val = lowered.get(name.replace("_", "-").lower())
        if val is not None and str(val).strip().lower() not in ("", "unknown", "n/a", "no data", "null"):
            return val
    return None


def epc_record_summary(record: dict) -> dict:
    address = get_key(record,"address", "address1", "address-1", "address-line-1") or "Address not supplied"
    return {"id":safe_text(get_key(record,"lmk-key", "certificate-id", "lodgement-number", "uprn")),
            "address":safe_text(address)[:180],
            "postcode":safe_text(get_key(record,"postcode")),
            "rating":safe_text(get_key(record,"current-energy-rating")),
            "lodged":safe_text(get_key(record,"lodgement-datetime", "lodgement-date")),
            "record": record}


def decode_records(response: httpx.Response) -> list[dict]:
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type or response.text.lstrip().startswith(("{","[")):
        obj = response.json()
        rows = obj if isinstance(obj,list) else (obj.get('rows') or obj.get('results') or obj.get('data') or [])
        if isinstance(rows,dict): rows = rows.get('rows',[])
    else:
        rows = list(csv.DictReader(io.StringIO(response.text)))
    if not isinstance(rows,list): raise ValueError("Unrecognised EPC service response format")
    return [r for r in rows if isinstance(r,dict)][:50]


def search_epc(postcode: str) -> dict:
    postcode = normalize_postcode(postcode)
    endpoint = os.getenv("TREE_EPC_SEARCH_URL", "").strip()
    authorization = os.getenv("TREE_EPC_AUTHORIZATION", "").strip()
    if not endpoint or not authorization:
        return {"status":"not_configured", "postcode":postcode, "properties":[],
                "message":"Live EPC lookup requires provider API credentials. Use your own home details or an explicitly synthetic demo; no certificate has been retrieved.",
                "reference":"https://get-energy-performance-data.communities.gov.uk/"}
    if not endpoint.startswith("https://"):
        raise ValueError("EPC search endpoint must use HTTPS")
    try:
        with httpx.Client(timeout=8, follow_redirects=False) as client:
            res=client.get(endpoint,params={"postcode":postcode,"size":50},headers={"Authorization":authorization,"Accept":"application/json,text/csv"})
        res.raise_for_status()
        records=decode_records(res)
    except (httpx.HTTPError,ValueError) as err:
        return {"status":"provider_error", "postcode":postcode, "properties":[],
                "message":"EPC provider could not be reached or returned an unsupported format; no certificate was invented.",
                "technical_detail":str(err)[:180]}
    records=[r for r in records if re.sub(r'\s+','',safe_text(get_key(r,'postcode')).upper()) == postcode.replace(' ','')]
    summaries=[{**epc_record_summary(r), **{'selection':sign_epc_record(r)}} for r in records]
    summaries.sort(key=lambda r:r["lodged"],reverse=True)
    return {"status":"live_epc", "postcode":postcode, "properties":summaries,
            "message":"Select and confirm your exact property; certificates may be outdated, superseded or associated with another unit.",
            "warning":"Provider data only. TREE is not issuing a government EPC."}


def read_bool_description(value: Any, positive: str, negative: str) -> bool | None:
    s=safe_text(value).lower()
    if not s:return None
    if any(term in s for term in negative.split('|')):return False
    if any(term in s for term in positive.split('|')):return True
    return None


def record_to_property(record: dict, *, confirmed: bool=False) -> dict:
    """Conservative EPC map: unsupported/ambiguous fields remain null, never guessed."""
    if not confirmed: raise ValueError("Confirm the address/flat before applying an EPC record")
    sources={}
    def assign(key, val):
        if val is not None:
            sources[key]={"source":"epc_provider", "status":"recorded_not_survey_verified"}
        return val
    raw_rating=safe_text(get_key(record,"current-energy-rating")).upper()
    rating=assign("epc_rating",raw_rating if raw_rating in 'ABCDEFG' and len(raw_rating)==1 else None)
    area=get_key(record,"total-floor-area")
    try:
        area=float(area)
        if not 10<=area<=1000:area=None
    except (ValueError,TypeError):area=None
    area=assign("floor_area_m2",area)
    ptype=safe_text(get_key(record,"property-type")).lower()
    built=safe_text(get_key(record,"built-form")).lower()
    # Do not put the street address in a reusable homeowner/LLM session name.
    name="My confirmed UK home"
    if "bungalow" in ptype: typ="bungalow"
    elif "flat" in ptype or "maisonette" in ptype:typ="flat"
    elif "semi" in built:typ="semi_detached"
    elif "detached" in built:typ="detached"
    elif "terrace" in built:typ="terraced"
    else: typ=None
    typ=assign("property_type",typ)
    heat=safe_text(get_key(record,"mainheat-description", "main-fuel")).lower()
    if "heat pump" in heat:heating="heat_pump"
    elif "gas" in heat and ("boiler" in heat or "radiator" in heat):heating="gas_boiler"
    elif "electric" in heat and any(t in heat for t in ('panel','storage','resistance')):heating="electric_resistance"
    elif "community" in heat or "district" in heat:heating="district"
    else:heating=None
    heating=assign("heating_type",heating)
    windows=safe_text(get_key(record,"windows-description")).lower()
    if "triple" in windows:glazing="triple"
    elif "double" in windows:glazing="double"
    elif "single" in windows:glazing="single"
    else:glazing=None
    glazing=assign("glazing",glazing)
    roof=safe_text(get_key(record,"roof-description")).lower()
    loft=read_bool_description(roof,'insulated|mm loft insulation','no insulation|uninsulated|0 mm insulation')
    loft=assign("loft_insulated",loft)
    walls=safe_text(get_key(record,"walls-description")).lower()
    wall=read_bool_description(walls,'insulated|filled cavity','no insulation|uninsulated|as built')
    wall=assign("wall_insulated",wall)
    # EPC fields alone cannot establish solar roof suitability, outdoor unit space,
    # tariff, annual metered gas/electricity or this home's current market value.
    return {"property":{"property_id":"epc_confirmed_home", "name":name,"region":safe_text(get_key(record,"local-authority","county")) or "Unknown", "property_type":typ,
            "floor_area_m2":area,"construction_age_band":safe_text(get_key(record,"construction-age-band")) or "unknown",
            "epc_rating":rating,"heating_type":heating,"glazing":glazing,"loft_insulated":loft,"wall_insulated":wall,
            "smart_controls":None,"roof_suitable":None,"outdoor_space":None,"solar_kwp":0,
            "annual_electricity_kwh":None,"annual_gas_kwh":None,"baseline_source":"epc_record_no_metered_consumption",
            "property_value_gbp":None,"electricity_price_gbp_kwh":0.28,"gas_price_gbp_kwh":0.07,"budget_gbp":5000},
            "evidence":sources,
            "missing_fields":[x for x in ("property_type","floor_area_m2","heating_type","glazing","loft_insulated","wall_insulated","smart_controls","roof_suitable","outdoor_space","annual_electricity_kwh","annual_gas_kwh","property_value_gbp") if (x not in sources)],
            "warning":"EPC data is a historical certificate, not an energy bill, property valuation or guaranteed current building state. Confirm details before using estimated results."}


class QuestionsPayload(BaseModel):
    property: dict
    answered: list[str]=Field(default_factory=list)
    budget_gbp: float=Field(default=5000,ge=0)
    objective: str="money"


QUESTION_BANK={
    "floor_area_m2":("What is your home's approximate floor area in square metres?","number",None,"Needed for energy intensity and ML consumption predictions."),
    "property_type":("Which type of home do you live in?","choice",["detached","semi_detached","terraced","flat","bungalow"],"Influences energy usage and which upgrades are feasible."),
    "epc_rating":("Do you know your current EPC rating?","choice",list("ABCDEFG"),"Energy efficiency carries 25% of the official Green Home Score."),
    "heating_type":("How is your home mainly heated?","choice",["gas_boiler","heat_pump","electric_resistance","district"],"Heating carries 15% of the score and changes heat-pump feasibility."),
    "glazing":("What type of glazing do your windows have?","choice",["single","double","triple"],"Windows carry 10% of the score and affect retrofit feasibility."),
    "loft_insulated":("Does your loft have insulation?","bool",None,"Insulation is 15% of the score; this may change the best-value retrofit."),
    "wall_insulated":("Are the external walls insulated?","bool",None,"Insulation is 15% of the score and reduces modeled heat loss."),
    "outdoor_space":("Is there safe space outside for a heat-pump unit?","bool",None,"Heat pumps can only be recommended where an outdoor unit may be feasible."),
    "roof_suitable":("Is your roof reasonably unshaded and suitable for panels?","bool",None,"Solar feasibility needs homeowner confirmation and later a professional survey."),
    "smart_controls":("Do you already have a smart thermostat or heating controls?","bool",None,"Smart management accounts for 5% of the score."),
    "annual_electricity_kwh":("Do you know your annual grid electricity usage in kWh from your bill?","number",None,"Observed bills make predictions more useful; leave unknown if unavailable."),
    "annual_gas_kwh":("Do you know your annual gas usage in kWh from your bill?","number",None,"Solar or heat-pump scenarios need per-fuel baselines; leave unknown if unavailable."),
    "property_value_gbp":("Do you have an approximate current property value in £?","number",None,"Without a value TREE correctly reports any property-value impact as unavailable."),
}
PRIORITY=["floor_area_m2","property_type","epc_rating","heating_type","glazing","loft_insulated","wall_insulated","outdoor_space","roof_suitable","smart_controls","annual_electricity_kwh","annual_gas_kwh","property_value_gbp"]


def next_intake_question(values: dict, answered: list[str]|None=None,budget:float=5000, objective:str="money") -> dict:
    answered=answered or []
    missing=[key for key in PRIORITY if values.get(key) is None and key not in answered]
    if not missing:return {"question":None,"reason":"All supported questions answered or skipped.","missing":[]}
    # First ask blockers preventing any meaningful model, then decision-sensitive questions.
    field=missing[0]
    if values.get('floor_area_m2') is not None and values.get('property_type') is not None:
        try:
            p=Property.model_validate({**values,'floor_area_m2':values['floor_area_m2'],'property_type':values['property_type'],
                'property_id':values.get('property_id') or 'question_home','name':values.get('name') or 'Home'})
            ranked=next_question(p,budget,objective,asked=answered)
            if ranked.get('field') in missing:
                field=ranked['field']
        except (ValueError,TypeError): pass
    title,kind,options,why=QUESTION_BANK[field]
    return {"field":field,"question":title,"type":kind,"options":options,"why":why,
            "missing":missing,"method":"blocking-inputs_then_counterfactual_retrofit_change_then_score_priority",
            "can_skip":True}
