# Calculation assumptions, sources and limitations

## Energy accounting

Purchased energy = annual grid electricity import + annual gas consumption, kWh/year. The overall improvement potential is `100 × (before_purchased - after_purchased) / before_purchased`, unavailable for zero or missing reference baselines in property ranking.

## Retrofit effects (demonstrator only)

- Gas boiler: 85% of baseline gas is assumed to be for space heating; useful-space-heat conversion efficiency 85%.
- Loft insulation reduces remaining useful space-heating demand to 82% of its former value.
- Wall insulation reduces remaining useful space-heating demand to 86% of its former value.
- Double glazing reduces remaining useful space-heating demand to 92% of its former value.
- Smart controls reduce remaining space-heating demand to 93%.
- Heat pumps use seasonal COP 3.0, displacing existing gas space heating and retaining gas for other uses under the simplified model.
- Existing heat pumps use an assumed 55% share of electricity for space heating; electric resistance 55% share.
- 3kWp added solar yields an illustrative 900 kWh/kWp/year with 55% self-consumption, limited by current underlying demand. Existing solar uses the same assumption to reconstruct gross demand from a net-import baseline.
- Installation costs: loft £950, wall £5,600, glazing £5,900, smart controls £300, heat pump £8,500, solar £5,500.
- Default unit tariffs: £0.28/kWh electricity and £0.07/kWh gas; **illustrative only, not confirmed current Octopus or a customer's actual rates**. Unchanged standing charges omitted on both sides of simple bill comparison.

Effects are applied multiplicatively to remaining heating demand so packages do not artificially sum independent reductions. These factors have NOT been validated against building-energy software or real retrofits. No detailed building geometry, shading, occupancy, comfort rebound, humidity, fabric surveys or seasonal shape.

## Carbon — published DESNZ 2026 operational factors

`backend/engines/carbon.py` now defaults to **0.13096 kg CO₂e/kWh** for average UK grid electricity generated (including imports), Scope 2, and **0.18231 kg CO₂e/kWh** for natural gas combustion, Scope 1, from DESNZ's published 2026 UK company GHG conversion-factor tables. Source: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 (flat file updated 31 July 2026). Formula: `CO2e_saved_kg = (baseline_grid_electricity - post_grid_electricity) * 0.13096 + (baseline_gas - post_gas) * 0.18231`.

This is a specific **operational location-based scope convention**. It omits electricity grid transmission/distribution loss emissions, upstream natural-gas production and electricity fuel WTT, construction and embodied emissions, solar exports and marginal generation displacement. Since annual averages are used, it is **not** a claim of measured carbon savings or carbon credits. The energy-change assumptions are unvalidated. Environment overrides are explicit and flagged, and must be finite nonnegative kg CO₂e/kWh with an independently documented source. API: `/api/methodology/carbon-factors`.

## Valuation — distinguish two models

Existing automatic retrofit projections in `backend/engines/valuation.py` are a **toy illustrative score-uplift sensitivity, not a model supported by actual sales**. Their output is marked `illustrative_only_not_market_validated`; do not present it as actual appreciation.

NEW separate `/api/valuation/epc-hypothesis` uses national repeat-sale observational research from Rightmove 2021 and 2023 for an **explicitly hypothetical** EPC transition D/E/F → C, *not* an EPC transition inferred from TREE's Green Home Score. Research-rate ranges D→C = 3–4%, E→C = 7–8%, F→C = 15–16%. These spans come from two vintages of point estimates; **they are not confidence intervals**. The reference data adjusted for market inflation and floor size historically, but this output **does not adjust its reference rates individually** for a chosen region, property type, floor area, market date or tenure. The independent IFS 2026 paper estimates materially different 1–3% nationwide premiums under another identification strategy; we disclose this difference, rather than choosing whichever estimate makes TREE look best.

Sources:
- https://www.rightmove.co.uk/press-centre/green-upgrades-help-sellers-pocket-up-to-16-more-for-their-home/
- https://www.rightmove.co.uk/news/articles/property-news/green-premium-epc-ratings/
- https://ifs.org.uk/publications/information-disclosure-and-valuation-energy-efficiency-housing-markets

**No causality, no address-specific valuation and no official new EPC grade** is established. If no home-value baseline is supplied or the rating transition lies outside studied cases, the reference is unavailable. To build a genuine local model, obtain lawfully usable matched EPC + Land Registry comparable-sale records, control for geography, age/size/type and dates, validate held-out outcomes, and document limitations.

## Score

Weights and class boundaries follow Lloyds; component mappings and post-retrofit efficiency proxy are documented original assumptions in `scoring_method.md`.

## Reproducibility

Fixed synthetic training seed 42. No live APIs required. Results may differ slightly across scikit-learn versions but files can be regenerated.

## Independent official retrofit-impact context (not calibration)

The official DESNZ *NEED 2026 summary of analysis*, Chapter 3, compares treated households with similar non-intervention comparators. It reports that solid wall insulation installed in 2023 had approximately **17% median gas savings** in 2024 among analysed England/Wales properties, while the combination of solid wall and loft insulation was about **14%** for its separate sample. These are *different treated groups*, not directly additive experimental effects and not coefficients for this simulator. Year-to-year estimates are variable; the report discusses comfort-taking, sample-size limits and hidden installations. TREE's arbitrary useful-heat multipliers have **not** been replaced or validated against these group outcomes. Do not imply that individual simulated packages have measured 17% savings.

Source: https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026-accessible-webpage

## Scenario stress test

`backend/engines/report.py` varies computed per-fuel changes by ±20% and installation costs by ±20%, with the baseline held fixed. **These bounds were chosen as demonstrator stress tests and are NOT probability-based confidence intervals.** For physically different installation circumstances, real errors may be much larger. See `/api/scenarios/sensitivity`.
