# TREE — questions judges could ask two first-year CS teammates

## Know these answers; don't memorize unexplained code

**1. What is TREE solving?** It helps a homeowner understand a home's modelled efficiency, find feasible upgrades and compare cost, fuel, carbon and potential value impact. It is not a survey, EPC certificate or installation guarantee.

**2. Why GPS and postcode?** GPS only suggests a nearby postcode (via postcodes.io). Multiple properties can share that postcode, and an EPC may be outdated. The person selects the exact home or uses manual entry. Latitude and longitude are processed for the request, not saved in the TREE database. The third-party postcode service receives coordinates.

**3. What if there is no EPC?** Unknown fields stay unknown. TreeAsk asks high-impact questions first. Certain fields, such as floor area and type, are needed to run a property report; unresolved other fields receive neutral placeholders and a reported possible score range.

**4. How is the Green Home Score made?** Seven 0–100 components weighted 25% efficiency, 20% purchased-energy intensity, 15% insulation, 15% heating, 10% glazing, 10% renewables, 5% smart controls. `sum(weight × subscore)`. The **weights** come from Lloyds; detailed category-to-number mappings are our documented prototype assumptions.

**5. Does TREE reissue an EPC?** No. Its score is a product decision score and a scenario post-score is only a proxy.

**6. Why use ML if there's a simple calculator?** Cold-start annual consumption isn't known before a person provides bills. The coarse real UK NEED model estimates a starting baseline from property category and EPC group; observed full-year bills override estimates when supplied. The formula-based retrofit simulator then changes that baseline. Do not call the latter an ML model of retrofit effectiveness.

**7. How was ML evaluated?** NEED 2026 public anonymised data, fixed train/validation/test split, compare multiple estimators with training-median baseline, report test MAE and R² on untouched homes. For new homes, property type and grouped EPC alone explain limited variation; scores are honest about errors. Code: `ml/consumer_need.py` and `ml/models/consumer_need/report.json`.

**8. What happens to electricity after a heat pump?** It may increase. TREE tracks electricity and gas separately; the model divides estimated useful heat by heat-pump COP, then computes grid import. Fuel savings may be negative; it does not hide increased electric demand.

**9. Why not add single-retrofit savings together?** Physical interactions: insulation lowers heat demand before heat-pump sizing; the model multiplies envelope factors and recalculates the final package. Existing rooftop solar offsets grid imports, not the home's useful energy demand.

**10. Carbon formula?** `CO2e reduction = Δelectricity × EF_electricity + Δgas × EF_gas`. Operational national-average DESNZ 2026 factors in `backend/engines/carbon.py`. It excludes embodied emissions and life-cycle impacts.

**11. Is property-value increase proven?** No. Automatic value ranges are visibly synthetic sensitivities; separate historical D/E/F→C EPC repeat-sales comparisons are observational and only shown for an **explicit hypothetical** EPC change. TREE never infers a certified EPC upgrade from score change. Accurate property-specific prediction needs local sale comparables and transaction calibration.

**12. How does budget optimization work?** There are only six retrofit categories, so `optimizer.py` tries feasible combinations (at most 64), excludes options over budget, then sorts by the chosen objective: annual bills, purchased energy or operational carbon. No black-box solver necessary. It recommends a package **inside** the supplied limit.

**13. Is the GenAI generating the numbers?** No. Python calculators generate all numbers. The optional Gemini route selects one of seven allowlisted intents when the local keyword logic cannot understand the question; Python answers it and Gemini may paraphrase the approved answer. A numerical guard rejects new or missing claims. Without a key, a deterministic chat still asks smart follow-ups.

**14. Are the LLM groundedness targets achieved?** **Not independently verified.** Slide 12 requires ≥90% groundedness, ≥90% factual accuracy and <5% unsupported claims. We provide human annotation instructions/script (`evaluation/llm_claim_audit.py`) but cannot claim the percentages without real provider responses and completed reviews.

**15. What can a photo/video really do?** Images can go to an optional Gemini visual candidate function **only with consent and provider key**; findings are unverified until confirmed. Text PDFs or text bills yield candidate values, not verified annual consumption. Video can be uploaded for local metadata checks, **not** understood by a vision model in this build.

**16. What is innovative?** Adaptive high-information questions, evidence-based disclosures, feasibility-aware combined upgrades, budget tradeoffs, 3 futures, Retrofit Chess, optional opt-in customer memory, explainable score cards and daily non-scored environmental habits.

**17. What's not production-ready?** EPC credentials are site-specific; ML individual-address uncertainty is high; simulated retrofit cost/effect needs real installer quotes/outcomes; local market value needs transactions; LLM/provider evidence requires review; user authentication is not implemented.

**18. Who wrote it?** Say truthfully that you designed/refined it and ChatGPT helped implement/debug; explain what you personally tested, modified and understand. Avoid the claim "we coded every line by hand" if false.

## Five-minute demo order

1. Show manual home and missing inputs in TreeAsk (45 sec).
2. Show Green Home Score, weights and each numerical contribution (50 sec).
3. Show budget package, heat pump electricity increase and carbon change (70 sec).
4. Ask TREE a genuine challenge or what-if; show backend evidence (60 sec).
5. Show three futures, appliance/water/household habits (45 sec).
6. Show real UK NEED held-out benchmark and honest disclaimers (30 sec).
