"""Optional household audit. Never credits unverified water/waste measures to the official score."""
from __future__ import annotations
import re
from io import BytesIO
from pydantic import BaseModel, Field
from typing import Literal

class Appliance(BaseModel):
    name: str = Field(min_length=1,max_length=70)
    quantity: int = Field(default=1,ge=1,le=80)
    rated_watts: float | None = Field(default=None,ge=0,le=30000)
    hours_per_day: float | None = Field(default=None,ge=0,le=24)
    days_per_year: int = Field(default=365,ge=0,le=366)
    standby_watts: float | None = Field(default=None,ge=0,le=1000)

class Household(BaseModel):
    appliances: list[Appliance] = Field(default_factory=list,max_length=60)
    occupants: int | None = Field(default=None,ge=1,le=25)
    kitchen_waste_kg_week: float | None = Field(default=None,ge=0,le=1000)
    outdoor_water_reuse_possible: bool | None = None
    garden: bool | None = None
    has_solar_water_heater: bool | None = None
    interested_in_composting: bool | None = None
    paper_recycling: bool | None = None
    off_peak_shift_possible: bool | None = None
    recent_electricity_bill_kwh: float | None = Field(default=None,ge=0)
    annual_water_m3: float | None = Field(default=None,ge=0,le=100000)


def appliance_audit(h: Household) -> dict:
    rows=[]
    total=0
    unknown=[]
    for i, a in enumerate(h.appliances):
        if a.rated_watts is None or a.hours_per_day is None:
            unknown.append(a.name)
            rows.append({'name':a.name,'quantity':a.quantity,'annual_kwh':None,'source':'insufficient_usage_data'})
            continue
        kwh=a.quantity*a.rated_watts*a.hours_per_day*a.days_per_year/1000
        total+=kwh
        rows.append({'name':a.name,'quantity':a.quantity,'annual_kwh':round(kwh,1),'source':'owner_supplied_power_and_hours'})
    return {'count':sum(a.quantity for a in h.appliances), 'estimated_annual_kwh_for_known_items':round(total,1),
            'items':rows,'unknown_items':unknown,
            'warning':'Bottom-up appliance estimates are not a metered electricity baseline. Do not add them to a bill figure or claim they cover heating, standby or all home use.'}


def green_extensions(h: Household) -> dict:
    advice=[
      {'id':'solar_water_heating','title':'Solar water heater', 'category':'renewable heat',
       'suitability':'explore' if not h.has_solar_water_heater else 'already_present',
       'reason':'Can offset hot-water fuel consumption if roof, demand and permissions allow; professional thermal and plumbing survey needed.',
       'score_credit':False,'saving_kwh':None},
      {'id':'solar_cooker','title':'Solar cooking / solar rice cooker', 'category':'behaviour and renewable heat',
       'suitability':'explore', 'reason':'Daytime use and weather determine practicality; no verified annual energy savings are available.',
       'score_credit':False,'saving_kwh':None},
      {'id':'kitchen_compost','title':'Kitchen waste composting', 'category':'waste diversion',
       'suitability':'explore' if h.kitchen_waste_kg_week is not None else 'needs_waste_measurement',
       'reason':'Useful waste reduction, but compost is not household electricity generation.',
       'score_credit':False,'saving_kwh':None},
      {'id':'household_biogas','title':'Biogas / gobar gas feasibility', 'category':'waste-to-energy',
       'suitability':'needs_expert_safety_design',
       'reason':'Biogas requires suitable feedstock volume, retention, gas handling, permits and certified installation; ordinary kitchen scraps alone do not justify a generation claim.',
       'score_credit':False,'saving_kwh':None},
      {'id':'greywater_reuse','title':'Greywater reuse and rainwater collection', 'category':'water conservation',
       'suitability':'explore' if h.outdoor_water_reuse_possible else 'needs_site_check',
       'reason':'Potentially useful for toilets/irrigation only with safe separate plumbing, hygienic controls and local approvals. Groundwater extraction/reinjection is not assumed feasible.',
       'score_credit':False,'saving_kwh':None},
      {'id':'paper_recycling','title':'Paper recycling', 'category':'waste diversion',
       'suitability':'explore' if not h.paper_recycling else 'already_practised',
       'reason':'A non-energy household sustainability action, tracked separately from the seven-part Green Home Score.',
       'score_credit':False,'saving_kwh':None}
    ]
    water={'annual_water_m3':h.annual_water_m3, 'litres_per_day':round(h.annual_water_m3*1000/365,1) if h.annual_water_m3 is not None else None, 'warning':'Water volume is separate from the official energy score.'}
    return {'extensions':advice,'water':water,'method':'non_scored_advisory_only',
            'warning':'Water, food waste, compost, paper recycling and unverified solar heat receive NO official electricity, carbon, property-value or Green Home Score credit.'}


def household_notifications(h: Household) -> list[dict]:
    audit=appliance_audit(h)
    notifications=[]
    if audit['unknown_items']:
        notifications.append({'id':'complete_inventory','priority':'information',
           'title':'Finish your appliance profile','body':'Add power and daily hours for: '+', '.join(audit['unknown_items'][:4])+'. This improves the bottom-up audit, not the official score.'})
    if h.recent_electricity_bill_kwh is None:
        notifications.append({'id':'bill_check','priority':'information','title':'Check annual energy usage',
                              'body':'Add kWh from a full-year bill to replace the synthetic consumption fallback where possible.'})
    for a in h.appliances:
        if a.standby_watts is not None and a.standby_watts >= 5:
            notifications.append({'id':'standby_'+str(len(notifications)), 'priority':'suggestion','title':'Review appliance standby use',
                'body':f'{a.name}: the reported standby draw is {a.standby_watts:g} W. Turn off safely when not needed; actual savings require standby hours.'})
    if not h.paper_recycling:
        notifications.append({'id':'recycling','priority':'optional','title':'Consider paper recycling',
          'body':'Record this as a sustainability habit; it does not change your formal Green Home Score.'})
    if h.kitchen_waste_kg_week is not None and h.kitchen_waste_kg_week > 0:
        notifications.append({'id':'food_waste','priority':'optional','title':'Separate kitchen scraps today',
          'body':'You reported organic waste. Consider safe compost collection where suitable. Biogas needs expert design and does not have proven savings for this home.'})
    if h.outdoor_water_reuse_possible and h.garden:
        notifications.append({'id':'rainwater','priority':'optional','title':'Check rainwater storage opportunities',
          'body':'A safe, covered rainwater collection system may replace some garden mains-water use. Follow local water hygiene rules; no automatic kWh score credit.'})
    if h.off_peak_shift_possible:
        notifications.append({'id':'offpeak','priority':'suggestion','title':'Check your tariff before shifting use',
          'body':'Only shift safe, non-essential tasks if the actual energy tariff has lower off-peak pricing. No saving is claimed without the tariff.'})
    if h.has_solar_water_heater is False:
        notifications.append({'id':'hotwater','priority':'optional','title':'Review hot-water energy demand',
          'body':'If you have high hot-water use, ask a qualified installer whether solar thermal is feasible; electricity or gas savings require a site survey.'})
    return notifications


def finance_notifications(p) -> list[dict]:
    """Informational in-app prompts only; no implied investment advice or grants."""
    from backend.engines.optimizer import optimize
    plan = optimize(p, p.budget_gbp, 'money')['best']
    if not plan['measures']:
        return [{'id':'budget_revisit','priority':'information','title':'No verified feasible upgrade in budget',
                 'body':'Do not raise your budget automatically. Confirm missing building details or ask for professional cost estimates.'}]
    return [{'id':'budget_plan','priority':'information',
             'title':'Review your homeowner-approved budget plan',
             'body': ('Within your £'+f'{p.budget_gbp:,.0f}'+' stated limit, '+', '.join(plan['labels'])
                      +' has illustrative upfront cost £'+f"{plan['cost_gbp']:,.0f}"
                      +' and modelled annual bill saving £'+f"{plan['annual_bill_savings_gbp']:,.0f}"
                      +'. Prices are not verified contractor quotes; confirm affordability before acting.')}]


# Conservative candidate-only extraction. TEXT PDFs only. NEVER auto-populate a bill.
_ELEC=re.compile(r'(?i)\b(?:electricity|electric\s+usage)\b[^\n]{0,95}?\b(\d{2,7}(?:[,.]\d+)?)\s*kwh\b')
_GAS=re.compile(r'(?i)\b(?:natural\s+gas|gas\s+usage|gas)\b[^\n]{0,95}?\b(\d{2,7}(?:[,.]\d+)?)\s*kwh\b')
_WATER=re.compile(r'(?i)\b(?:water\s+(?:usage|consumption|used)|water)\b[^\n]{0,95}?\b(\d{1,7}(?:[,.]\d+)?)\s*(?:m3|m³|cubic\s+met(?:er|re)s?)\b')

def text_bill_candidates(text: str) -> dict:
    candidates=[]
    for fuel, pattern in [('electricity',_ELEC),('gas',_GAS)]:
        values=[]
        for m in pattern.finditer(text):
            try: values.append(float(m.group(1).replace(',','')))
            except ValueError:pass
        # Repetition and bill periods are common; do not pick one silently.
        for v in values[:5]: candidates.append({'fuel':fuel,'value_kwh':v,'period':'unknown','confidence':'candidate_not_verified'})
    for match in _WATER.finditer(text):
        try: candidates.append({'fuel':'water','value_m3':float(match.group(1).replace(',','')),'unit':'m3','period':'unknown','confidence':'candidate_not_verified'})
        except ValueError: pass
    return {'candidates':candidates,'auto_filled':False,
      'warning':'The extracted numbers may refer to a billing period, not a full year. Confirm dates, fuel, imports, and annual kWh before applying.'}


def inspect_media(data: bytes, filename: str, content_type: str) -> dict:
    """No storage or external upload; metadata for images/videos, best-effort text-PDF parse."""
    suffix=filename.lower().rsplit('.',1)[-1] if '.' in filename else ''
    if suffix not in ('pdf','png','jpg','jpeg','webp','mp4','mov','txt'):
        raise ValueError('Accepted formats: PDF, PNG, JPEG, WEBP, MP4, MOV or TXT')
    max_size=20*1024*1024 if suffix in ('mp4','mov') else 8*1024*1024
    if len(data)>max_size: raise ValueError('File exceeds the media size limit')
    if not data:raise ValueError('The file is empty')
    if suffix=='pdf' and not data.startswith(b'%PDF-'):raise ValueError('Not a valid PDF signature')
    if suffix=='png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Not a PNG file')
    if suffix in ('jpg','jpeg') and not data.startswith(b'\xff\xd8'):raise ValueError('Not a JPEG file')
    if suffix=='webp' and data[8:12]!=b'WEBP':raise ValueError('Not a WEBP file')
    if suffix=='mp4' and b'ftyp' not in data[:16]:raise ValueError('Not an MP4 file')
    if suffix=='mov' and b'ftyp' not in data[:16]:raise ValueError('Not a MOV file')
    if suffix=='pdf':
        try:
            from pypdf import PdfReader
            reader=PdfReader(BytesIO(data))
            text='\n'.join((page.extract_text() or '') for page in reader.pages[:8])[:20000]
        except Exception:
            text=''
        return {'type':'pdf','extracted_text':bool(text),'analysis':text_bill_candidates(text),
                'message':'Parsed selectable PDF text locally and discarded the file; image-only/scanned PDFs require manual confirmation.'}
    if suffix=='txt':
        return {'type':'text','extracted_text':True,'analysis':text_bill_candidates(data.decode('utf-8',errors='replace')[:20000]),
                'message':'Scanned text for candidate kWh values; homeowner must confirm period.'}
    return {'type':'video' if suffix in ('mp4','mov') else 'image','extracted_text':False,
        'analysis':{'candidates':[], 'auto_filled':False},
        'message':'Photo/video accepted and checked but not computer-vision analysed. We will NOT claim appliances, insulation or meter readings were recognized. Enter confirmed observations manually.',
        'privacy':'No file saved or forwarded to an external model.'}
