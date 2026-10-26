# Lloyds PS2 — official evaluation weights (slide 14)

| Criterion | Weight | Strongest demonstrable evidence | Remaining shortfall |
|---|---:|---|---|
| ML & recommendation quality | **20%** | UK NEED 2026 50k, real holdout, 60/20/20, validation-based challenger selection, simple baselines, 4 model modes, property-type/region/EPC error slices, exact feasible-package search | Real-UK models are separate from the homeowner fallback; bill-based baseline beats prior-year electricity ML |
| Green Home Score / insights | **15%** | Seven exact official weights, subscore mappings, explanations, flags, all classifications tested | Sub-score mappings are illustrative, not EPC calculations |
| Energy/carbon/value | **15%** | Per-fuel, package interactions, negative heat-pump electricity savings, scenario cost and emissions, sensitivity and value ranges | Retrofit effects, carbon defaults and property value uplift not empirically validated |
| GenAI grounded explanations / what-if | **15%** | Deterministic calculation first, supported scenario parser, evidence-bound text, cautious optional Gemini, 108 deterministic contract checks | No provider-backed LLM factuality study; target thresholds unverified |
| Business relevance | **10%** | Annual bills, upfront budgets, simple payback, budget optimizer, lifecycle sequence, suitable first steps | No actual lending-product or tariff integration |
| Architecture / reproducibility | **10%** | FastAPI contracts, standalone Mac startup, pinned sklearn, data scripts, release tests, OGL dataset + heldout predictions | Local-only, unprotected demo SQLite; no enterprise auth/SLAs |
| Explainability / Responsible AI | **5%** | Source trace, data-quality conflicts, benchmark limits, per-fuel assumptions, declared uncertainty, owner controls | External fairness study/regulated deployment review not completed |
| UX and dashboard | **5%** | Basic accessible six-step workflow now; original richer interface at `/studio` | Final 3D and bespoke look intentionally deferred |
| Innovation | **5%** | TreeAsk, Retrofit Chess, Future Worlds, budget optimizer, opt-in customer memory | Synthetic question benchmark is not a randomized user study |

**Interpretation:** 9.7 or 10/10 is not a verified or guaranteed score. Organisers make the scoring decision, and the slide explicitly penalizes unsupported precision and arbitrary labels. Prioritize reliable evidence and reproducibility over inflated headline metrics.
