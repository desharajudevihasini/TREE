"""Deterministic, calculation-backed dialogue. Optional Gemini paraphrases only precomputed data."""
import json
import os
import re
import uuid
import httpx
from backend.schemas import ChatRequest
from backend.storage import load_session, save_session
from backend.engines.scoring import green_score
from backend.engines.baseline import get_baseline
from backend.engines.optimizer import optimize, parallel_universes, retrofit_chess
from backend.engines.retrofit import simulate, recommended_measures, eligibility
from backend.engines.treeask import next_question

ANSWERS = {"yes": True, "y": True, "no": False, "n": False,
           "not sure": None, "unsure": None, "don't know": None, "dont know": None, "unknown": None}


def describe(p, best):
    changes = best["savings"]
    labels = ", ".join(best["labels"]) if best["labels"] else "no feasible paid upgrades"
    bill = best['annual_bill_savings_gbp']
    bill_note = f"estimated annual bill saving: £{bill:,.0f}" if bill >= 0 else f"estimated annual bill increase: £{abs(bill):,.0f}"
    return (f"For {p.name}, the model selects {labels}. Estimated upfront cost: £{best['cost_gbp']:,.0f}; "
            f"{bill_note}; "
            f"electricity saving: {changes['electricity_kwh']:,.0f} kWh/yr; "
            f"gas saving: {changes['gas_kwh']:,.0f} kWh/yr. "
            "These are simplified demonstration estimates, not guaranteed savings.")


def explanation_passes_guard(draft: str, candidate: str) -> bool:
    """Conservative safety filter; NOT independent LLM factuality evaluation.

    Falls back to deterministic output if a provider response drops numeric evidence,
    introduces new numeric claims or makes unsupported certification promises.
    This cannot establish semantic groundedness and should never be described as such.
    """
    if not candidate or len(candidate) > 2000:
        return False
    numeric_tokens = lambda text: set(re.findall(r"(?<!\w)\d+(?:[,.]\d+)*", text))
    if not numeric_tokens(candidate).issubset(numeric_tokens(draft)):
        return False
    if not numeric_tokens(draft).issubset(numeric_tokens(candidate)):
        return False
    disallowed = (r"\b(?:guaranteed savings?|certified savings?|proven uplift|official epc score|"
                  r"verified (?:energy|bill|carbon) savings?|live epc lookup|government[- ]approved results?)\b")
    if re.search(disallowed, candidate, re.IGNORECASE):
        return False
    if "estimate" in draft.lower() and not re.search(r"estimate|assumption|modelled|approximate|not guaranteed", candidate, re.IGNORECASE):
        return False
    # Some unsupported statements do not contain numbers. Preserve critical
    # disclosures whenever the approved response includes them.
    for signal, must_retain in (
        (r"\bnot an official EPC\b", r"\bnot (?:an? )?(?:official|certified) EPC\b"),
        (r"\bnot guarantees\b", r"\b(?:not guaranteed|not guarantees|no guarantee)\b"),
        (r"\bnot Lloyds customer records\b", r"\b(?:synthetic|fictional|not Lloyds customer)\b"),
    ):
        if re.search(signal, draft, re.I) and not re.search(must_retain, candidate, re.I):
            return False
    return True


def maybe_gemini(draft: str, evidence: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key: return draft
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        prompt = ("You are TREE, an evidence-aware home energy companion. Paraphrase the supplied "
                  "APPROVED ANSWER naturally, in under 100 words. The approved answer and data are binding. "
                  "Do not invent ANY numbers, prices, certificates, factual claims or eligibility. "
                  "Do not claim to have accessed live EPC or government data. "
                  "If unsure, repeat the approved answer.\n\n"
                  f"APPROVED ANSWER: {draft}\nMODEL DATA: {json.dumps(evidence, default=str)[:7000]}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        with httpx.Client(timeout=8) as client:
            res = client.post(url, params={"key": api_key}, json={"contents": [{"parts": [{"text": prompt}]}],
                                                           "generationConfig": {"temperature": 0.1}})
            res.raise_for_status()
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text if explanation_passes_guard(draft, text) else draft
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return draft


# Supported scenario intents are intentionally explicit: never ask an LLM to invent
# a retrofit, infer roof suitability, or calculate fuel savings in prose.
_MEASURE_PATTERNS = {
    "loft_insulation": r"\b(?:loft|attic)\b",
    "wall_insulation": r"\b(?:wall insulation|insulate (?:the |my |our )?walls?|cavity walls?)\b",
    "double_glazing": r"\b(?:double glaz(?:ing|ed)|replace (?:the |my |our )?windows?)\b",
    "smart_controls": r"\b(?:smart (?:controls?|thermostat)|programmable thermostat)\b",
    "heat_pump": r"\bheat pump\b",
    "solar_panels": r"\b(?:solar|pv panels?)\b",
}


def parse_what_if(message: str) -> dict | None:
    """Extract only explicitly supported user scenario inputs; no guessing."""
    low = message.lower().strip()
    scenario = bool(re.search(r"\b(?:what if|suppose|imagine|if i (?:install|add|replace|fit)|if we (?:install|add|replace|fit)|what happens if|how much if|how much (?:would|will) (?:it )?cost (?:to |if )?(?:add|install)|what (?:will|would) happen (?:if|when))\b", low))
    if not scenario:
        return None
    measures = [key for key, pat in _MEASURE_PATTERNS.items() if re.search(pat, low)]
    unsupported = [label for label, pattern in {
        'wind turbine': r'\bwind (?:turbines?|power)\b',
        'home battery': r'\b(?:home battery|battery storage|solar battery)\b',
        'ground-source heat pump': r'\bground[- ]source heat pump\b',
        'EV charger': r'\b(?:ev charger|electric vehicle charging)\b',
        'nuclear reactor': r'\b(?:nuclear|microreactor)\b',
        'hydrogen boiler': r'\bhydrogen boiler\b',
    }.items() if re.search(pattern, low)]
    if re.search(r'\binsulation\b', low) and not {'loft_insulation','wall_insulation'}.intersection(measures):
        unsupported.append('unspecified insulation')
    prices = {}
    # Accept £/kWh rates only. Never confuse a tariff change with the user's budget.
    for fuel in ('electricity', 'gas'):
        match = re.search(rf"\b{fuel}\b[^.!?]*?£\s*(0?\.\d+|\d+(?:\.\d+)?)\s*(?:/|per\s*)\s*kwh", low)
        if match:
            rate = float(match.group(1))
            if 0 <= rate <= 5:
                prices[f'{fuel}_price_gbp_kwh'] = rate
    for fuel in ('electricity', 'gas'):
        if re.search(rf"\b(?:double (?:the )?{fuel}(?: tariff| prices?| rate)?|{fuel} (?:tariff|prices?|rate) (?:is |are )?doubled?)\b", low):
            prices[f'{fuel}_price_gbp_kwh'] = 'double'
    return {'measures': measures, 'prices': prices, 'unmodelled': unsupported}


def epc_market_scenario(p, message: str) -> tuple[str, dict, str] | None:
    """Explicit EPC-rating hypothesis; never infer an EPC upgrade from retrofit score."""
    low = message.lower()
    if not re.search(r'\b(?:epc|energy rating)\b', low):
        return None
    # Examples: "what if EPC improves from E to C", "what if my EPC became C".
    change = re.search(r'\bfrom\s+([a-g])\s+to\s+([a-g])\b',low)
    if change:
        stated_before, after=change.group(1).upper(),change.group(2).upper()
        if p.epc_rating != stated_before:
            return (f"Your selected home has EPC {p.epc_rating or 'unknown'}, not {stated_before}. "
                    "Please verify the current rating before comparing a different EPC scenario.",
                    {'provided_rating':stated_before,'recorded_rating':p.epc_rating},'clarification')
    else:
        change=re.search(r'\b(?:became|becomes|improved? to|changes? to)\s+([a-g])\b',low)
        if not change:return None
        after=change.group(1).upper()
    from backend.engines.valuation import evidence_based_epc_hypothesis
    v=evidence_based_epc_hypothesis(p,after)
    if v['status']=='unavailable':
        return ('TREE cannot responsibly estimate this EPC-market-value scenario: '
                +v['reason']+' We will not invent a property premium.',
                {'valuation':v},'value')
    lo,hi=v['after_range_gbp']
    l,r=v['uplift_percent_range']
    return (f"IF a separately verified EPC rating improved from {p.epc_rating} to {after}, "
            f"published historical repeat-sales associations suggest an indicative {l:.0f}–{r:.0f}% "
            f"national comparison: £{lo:,.0f}–£{hi:,.0f} for an unchanged £{v['baseline_gbp']:,.0f} "
            "starting value. This is a historical observational research reference, not a "
            "forecast, verified current valuation, causal retrofit effect or an EPC certificate. "
            "TREE has NOT predicted that your proposed retrofits would achieve this new EPC grade; "
            "local market, type, size and market-date effects remain uncalibrated.",
            {'valuation':v},'value')


def scenario_reply(p, spec: dict) -> tuple[str, dict, str]:
    """Always obtain all reported numbers from simulate(), never from the LLM."""
    ids = spec['measures']
    if spec.get('unmodelled'):
        return ("I can't evaluate the full requested package because these are outside TREE's current "
                "calculation model: " + ', '.join(spec['unmodelled']) + ". "
                "I won't silently ignore part of a package. Please choose supported upgrades instead.",
                {'unmodelled': spec['unmodelled']}, 'clarification')
    if not ids and not spec['prices']:
        return ("I can recalculate a concrete scenario: loft or wall insulation, double glazing, "
                "smart controls, a heat pump, solar panels, or an explicit electricity/gas tariff in £/kWh. "
                "Which change should I test?", {'supported_measures': list(_MEASURE_PATTERNS)}, 'clarification')
    unsupported = [(key, eligibility(p, key)[2]) for key in ids if not eligibility(p, key)[0]]
    if unsupported:
        detail = '; '.join(f'{key.replace("_", " ")}: {reason}' for key, reason in unsupported)
        return (f"I can't model that package as feasible yet. {detail} "
                "Please confirm the missing property information or choose another upgrade.",
                {'rejected_measures': [{'measure': k, 'reason': r} for k, r in unsupported]}, 'infeasible')
    resolved_prices = {key: (round(getattr(p, key) * 2, 4) if value == 'double' else value)
                       for key, value in spec['prices'].items()}
    result = simulate(p, ids, resolved_prices.get('electricity_price_gbp_kwh'), resolved_prices.get('gas_price_gbp_kwh'))
    if resolved_prices:
        original_baseline = simulate(p, [])['after_annual_bill_gbp']
        result = {**result,
                  'tariff_adjusted_baseline_gbp': result['baseline_annual_bill_gbp'],
                  'baseline_annual_bill_gbp': original_baseline,
                  'annual_bill_savings_gbp': round(original_baseline - result['after_annual_bill_gbp'], 2)}
    saving = result['annual_bill_savings_gbp']
    bill = (f"£{saving:,.0f}/year lower" if saving >= 0 else f"£{abs(saving):,.0f}/year higher")
    label = ', '.join(result['labels']) if ids else 'no physical retrofits; tariff change only'
    co2 = result['carbon']['reduction_kg_co2e']
    carbon_description = (f"{co2:,.0f} kg CO2e/year lower" if co2 >= 0
                          else f"{abs(co2):,.0f} kg CO2e/year higher")
    green_before = result['score_before']['score']
    green_after = result['score_after']['score']
    valuation = result['valuation']
    if valuation['status'] == 'unavailable':
        value_note = "Property value impact is unavailable without a supported value baseline and market evidence."
    else:
        value_note = ("Property-value change is only an unvalidated scenario illustration, "
                      "not an estimate supported by comparable actual sales.")
    draft = (f"I recalculated the scenario for {p.name}: {label}. "
             f"Installation estimate: £{result['cost_gbp']:,.0f}. "
             f"New annual bill: £{result['after_annual_bill_gbp']:,.0f}; versus the original "
             f"£{result['baseline_annual_bill_gbp']:,.0f}, that's {bill}. "
             f"Electricity change: {result['savings']['electricity_kwh']:,.0f} kWh/year saved; "
             f"gas change: {result['savings']['gas_kwh']:,.0f} kWh/year saved "
             "(negative means more energy used). "
             f"Operational carbon: {carbon_description}, using documented 2026 UK factors. "
             f"Modelled Green Home Score: {green_before} to {green_after} (not an official EPC reassessment). "
             f"{value_note} "
             "These are modelled estimates using illustrative retrofit assumptions, not guarantees.")
    return draft, {'scenario': result, 'tariff_overrides': resolved_prices}, 'what_if'


def _decision_coach(p, msg):
    from backend.companion.decision_coach import decision_coach
    return decision_coach(p, msg)


def converse(req: ChatRequest):
    sid = req.session_id or str(uuid.uuid4())
    # Custom homes arrive with their details on the first message.
    # Later messages use the saved session, so TreeAsk answers persist.
    if req.property is not None and req.session_id is None:
        s = {"id": sid, "property": req.property, "pending": None, "asked": [], "messages": []}
    else:
        try:
            s = load_session(sid, req.property_id)
        except KeyError:
            raise ValueError("Unknown demonstration property.")
    p = s["property"]
    msg = req.message.strip()
    low = msg.lower()
    evidence = {}
    mode = "analysis"
    # One-time reply to last counterfactual question.
    if s["pending"]:
        field = s["pending"]
        answer = ANSWERS.get(low)
        if low in ANSWERS:
            if answer is not None:
                p = p.model_copy(update={field: answer})
                s["property"] = p
                intro = f"Thanks, I've recorded your answer about {field.replace('_', ' ')}. "
            else:
                intro = "That's fine. I'll retain the uncertainty rather than guessing. "
            s["asked"].append(field)
            s["pending"] = None
            plan = optimize(p)
            evidence = {"optimization": plan, "score": green_score(p)}
            draft = intro + describe(p, plan["best"])
            mode = "recommendation"
            return _finish(s, req, msg, draft, evidence, mode)
        # If an unrelated question is asked, don't overwrite the pending evidence.
    what_if = parse_what_if(msg)
    # A tariff (e.g. £0.40/kWh) must never silently replace the renovation budget.
    budget = re.search(r"\bbudget\s*(?:of|is|to|=)?\s*(?:£|gbp)?\s*([\d,]{1,9})\b", low)
    if not budget and what_if is None:
        budget = re.search(r"(?:£\s*|gbp\s*)([\d,]{2,9})(?!\s*(?:/|per)\s*kwh)", low)
    if budget:
        value = float(budget.group(1).replace(",", ""))
        if value <= 1000000:
            p = p.model_copy(update={"budget_gbp": value})
            s["property"] = p
    epc_value_hypothesis = epc_market_scenario(p, msg) if what_if is not None else None
    if epc_value_hypothesis is not None:
        draft, evidence, mode = epc_value_hypothesis
    elif what_if is not None:
        draft, evidence, mode = scenario_reply(p, what_if)
    elif any(x in low for x in ("compare", "universe", "future", "three homes", "3 homes")):
        evidence = {"scenarios": parallel_universes(p)}
        data = evidence["scenarios"]["scenarios"]
        draft = (f"I've compared three versions of {p.name}. The affordable plan costs £{data[1]['cost_gbp']:,.0f} "
                 f"and is estimated to save £{data[1]['annual_bill_savings_gbp']:,.0f}/year. "
                 f"The ambitious plan costs £{data[2]['cost_gbp']:,.0f} and is estimated to save "
                 f"£{data[2]['annual_bill_savings_gbp']:,.0f}/year. See the scenario comparison below.")
        mode = "scenarios"
    elif any(x in low for x in ("real customer", "actual lloyds", "real lloyds", "live epc", "certified epc", "official epc",
                                    "guaranteed", "guarantee", "actual data", "how accurate", "accuracy", "how certain", "confidence interval")):
        evidence = {"provenance": {
            "demo_properties": "synthetic", "live_epc_lookup": False,
            "energy_model": "coarse real-NEED trained model for missing consumption; synthetic fallback for unavailable models",
            "real_data_benchmark": "separate trained UK NEED 2026 model; not a validation of retrofits",
            "retrofit_effects": "illustrative assumptions", "property_value_uplift": "not externally validated"}}
        draft = ("TREE's demo homes are synthetic, not Lloyds customer records. Live EPC lookup "
                 "requires configured provider credentials and explicit address confirmation; without these, "
                 "no live EPC has been retrieved. A UK NEED 2026 held-out benchmark evaluates population "
                 "energy prediction, not this home's retrofit savings. Retrofit costs and effects and the "
                 "property-value relationship remain illustrative assumptions. Carbon is calculated from "
                 "documented 2026 DESNZ factors for grid electricity and natural gas combustion. "
                 "I cannot guarantee outcomes or issue an EPC certificate.")
        mode = "provenance"
    elif any(x in low for x in ("property value", "house value", "price uplift", "home value", "value increase", "value impact")):
        chosen = optimize(p)["best"]
        valuation = chosen["valuation"]
        evidence = {"valuation": valuation, "scenario": chosen}
        if valuation["status"] == "unavailable":
            draft = "I cannot estimate a value range without a property-value baseline; there is no verified market model here."
        else:
            draft = (f"The model's illustrative value range for {p.name} after the selected package is "
                     f"£{valuation['after_range_gbp'][0]:,.0f}–£{valuation['after_range_gbp'][1]:,.0f}. "
                     "This is a synthetic sensitivity example, NOT an observed sale-price effect or proven causal uplift. "
                     "A credible value impact would require location-controlled actual housing transaction data.")
        mode = "value"
    elif (advice := _decision_coach(p, msg)) is not None:
        draft = advice['answer'] + '\n\nTREE asks: ' + advice['follow_up']
        evidence = advice['evidence']
        mode = advice['mode']
    elif any(x in low for x in ("score", "efficient", "rating", "epc")):
        evidence = {"score": green_score(p)}
        q = evidence["score"]
        draft = (f"Your modelled Green Home Score is {q['score']}/100 ({q['classification']}). "
                 f"Its seven weighted components are shown below. The subscore mappings are documented demo assumptions, not official EPC recalculations.")
        mode = "score"
    elif "chess" in low or "sequence" in low or "order" in low:
        planned = [x["id"] for x in recommended_measures(p) if x["id"] in ("loft_insulation", "smart_controls", "heat_pump")][:3]
        evidence = {"chess": retrofit_chess(p, planned)}
        draft = ("I've compared two installation sequences. The final steady-state annual consumption is the same "
                 "for the same finished package in this model; the intermediate-stage savings can differ.")
        mode = "chess"
    else:
        # If opted in, Gemini interprets unfamiliar wording as one of seven
        # fixed tool intents. Its text is NEVER accepted as a calculation.
        # On error/no key, use the local clarifying-question engine.
        routed = None
        if req.use_gemini:
            from backend.companion.intent_router import route_gemini_intent, INTENT_PROMPTS
            intent = route_gemini_intent(msg)
            if intent is not None:
                routed = _decision_coach(p, INTENT_PROMPTS[intent])
        if routed is not None:
            draft = routed['answer'] + '\n\nTREE asks: ' + routed['follow_up']
            evidence = {**routed['evidence'], 'selected_tool_intent': routed['mode']}
            mode = 'gemini_routed_' + routed['mode']
            return _finish(s, req, msg, draft, evidence, mode)
        q = next_question(p, p.budget_gbp, asked=s["asked"])
        if q["question"]:
            s["pending"] = q["field"]
            evidence = {"treeask": q, "score": green_score(p)}
            draft = (f"Before I recommend an expensive upgrade, one question could change the answer: "
                     f"{q['question']} You can say Yes, No, or Not sure.")
            mode = "question"
        else:
            plan = optimize(p)
            evidence = {"optimization": plan, "recommendations": recommended_measures(p), "score": green_score(p)}
            draft = describe(p, plan["best"])
            if "solar" in low and eligibility(p, "solar_panels")[0]:
                solo = simulate(p, ["solar_panels"])
                draft += (f" A solar-only option would cost £{solo['cost_gbp']:,.0f} "
                          f"and save an estimated £{solo['annual_bill_savings_gbp']:,.0f}/year. "
                          "Compare this with the affordable package; the better choice depends on your goal.")
                evidence["solar_only"] = solo
            mode = "recommendation"
    return _finish(s, req, msg, draft, evidence, mode)


def _finish(s, req, msg, draft, evidence, mode):
    # Opt-in Gemini may paraphrase approved text; this demo doesn't claim a
    # provider-LLM groundedness score without an independently run evaluation.
    answer = maybe_gemini(draft, evidence) if req.use_gemini and mode not in ("question", "infeasible", "clarification") else draft
    s["messages"].extend([{"role": "user", "text": msg}, {"role": "assistant", "text": answer}])
    save_session(s)
    return {"session_id": s["id"], "message": answer, "mode": mode, "data": evidence,
            "property": s["property"].model_dump(),
            "source": "gemini_paraphrase_unverified" if answer != draft else "deterministic_grounded",
            "warnings": ["Retrofit savings and value impact remain assumption-based; NEED's held-out energy benchmark does not validate retrofit outcomes."]}
