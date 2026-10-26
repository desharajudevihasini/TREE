# Responsible AI: Lloyds PS2 report

**Privacy:** The included NEED 2026 data are an *official anonymised open-data sample* attributed under the UK Open Government Licence. The 12 sample UI properties are fictional; no live EPC addresses, Lloyds confidential records, customer bank activity, identity or geolocation are fetched. Don't upload bills containing names/addresses to this prototype. Local demo SQLite memory/session lacks account authentication; remove it before redistributing or deploying publicly.

**Accuracy and distribution shift:** Custom homeowner blanks use a synthetic-trained fallback or a heuristic, explicitly flagged; research models separately learn from valid observed NEED rows. On real NEED 2026 heldout, the property-only model explains little of the individual electricity variance (R² ~0.16), even though its median-baseline MAE is slightly worse. The previous-year bill copy baseline can outperform the electricity ML on MAE. Judge both baselines and error differences instead of inflating claimed accuracy. See `evaluation/need_challenger_report.json` and `evaluation/need_slice_analysis.json`.

**Fairness and bias:** Housing-type, EPC and region holdout error slices highlight differing predictive performance and group sample counts. They do not constitute a full equity or protected-characteristics bias audit, which could require stronger legal and scientific review. No household should be denied lending or services based on these demo outputs.

**Explainability:** TREE exposes official weight coefficients, per-component mappings, per-fuel delta signs, retrofit feasibility, warnings, heldout metrics and provenance. A modelled post-retrofit score is not a new EPC certificate.

**Unsupported claims:** Retrofits are based on a simplified annual energy and multiplicative interaction model, not an energy assessor or certified building physics model. Property-value uplift is illustrative (not backed by linked sales with matched controls). An official historical retrofit-impact report exists and is cited, but it does not establish that this simulator is calibrated to individual homes. Emissions factors currently use explicitly labeled provisional defaults; teams must select and verify the right DESNZ publication year, scope and units before any claims of official emissions accounting.

**LLM safeguards:** Numbers are computed in Python. Optional Gemini only paraphrases approved evidence and falls back if numeric evidence does not match or unsupported certification is claimed. That check is not a verified 90% groundedness or accuracy benchmark; provider evaluation still requires credentials and manual claim labels.

**Human oversight:** An actual EPC certificate, solar survey, heating-system design, installer quote, energy-bill confirmation, licensed market valuation and loan or subsidy decision must be made by the appropriate professionals. Show 'unavailable' when baseline consumption is missing for ranking or property value is absent.

**Memory/consent:** User may opt into local pseudonymous session preferences, mark retrofits completed, avoid suggestions, record interested/not interested responses, and delete all memory for the session. Completed statuses are self-reported, not installer-verified. No data are silently sent to Gemini from the memory database. No hosted authentication or encryption at rest is provided.

**Before production:** Verified address consent, EPC licensing, secure accounts and access control, privacy notices and retention, independent model performance and fairness checks, certified savings basis, validated carbon conversion factors, market evidence for valuation, and LLM provider benchmark/human oversight are required.
