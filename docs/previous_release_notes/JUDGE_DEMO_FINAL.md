# TREE — 5-minute judging demonstration, no invented data

1. **0:00–0:35 · Location first.** Enter a UK postcode. If provider is unconfigured, show TREE's honest warning, then choose manual entry. To show a *live* EPC, preconfigure and test credentials with the real provider before judging. An EPC address must be explicitly confirmed; a postcode alone is not a house.
2. **0:35–1:10 · Intelligent null questions.** Enter home floor area and property type, then show that a missing heating/insulation/roof fact prompts a decision-aware question. Skip a question to show no fake default certificate data.
3. **1:10–1:50 · Green Home Score.** Open the score and show exactly seven weights 25/20/15/15/10/10/5, class bands, weak components and provenance. Mention unknown fields and which energy values are supplied versus NEED ML estimates.
4. **1:50–2:45 · Retrofit package.** Show only feasible upgrades with suitability + reason, simulate insulation then heat pump; note **electricity may increase** even when gas and carbon fall. Show per-fuel signed changes, installations, before/after bills and indicative value range.
5. **2:45–3:20 · What-if LLM.** Ask "What if I add solar and a heat pump?"; the Python calculations execute before deterministic/Gemini explanation. Ask an infeasible measure and see it refused.
6. **3:20–4:05 · Real ML testing.** Open evidence/Methods or `ml/models/consumer_need/report.json`; show true heldout MAE/R² versus median baseline on UK NEED. Never call this household-specific validation. Show `python -m pytest -q` output.
7. **4:05–4:45 · Household extras.** Enter a 10-W lamp, 5 hours/day. Show 18.25 kWh/year for 365 days, plus water and waste ideas marked **outside score**. Upload a text/PDF bill to show candidate values, manually confirm annual use if appropriate; show no pretend video/photo analysis.
8. **4:45–5:00 · Explain limitations.** EPC credentials, market-value evidence, retrofit field validation and LLM-provider evaluation are separate next steps. Strong prototype, no invented claims.

## Edge cases judges may try

- Unknown EPC rating/loft insulation → stays unknown; reported score uses explicit neutral placeholder; missing data flagged.
- Zero purchased energy → improvement-potential percentage unavailable, not NaN.
- Gas boiler and zero gas bill → consistency warning, no secret correction.
- Roof unsuitable and solar requested → infeasible error, no savings fabricated.
- Heat pump raises grid electricity → **negative electricity saving**, while gas can fall.
- Two retrofits combined → multiplicative heat demand effects, not naïve addition.
- Bills say a number of pounds only → no conversion into imaginary kWh.
- Images/videos → never claim observations except user consent + working Gemini photo API.
- Fake EPC JSON → cannot be accepted as a provider-signed search result.
