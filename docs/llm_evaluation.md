# LLM implementation, prompts and evaluation status — PPT slides 3, 10 and 13

Code: `backend/companion/assistant.py`, deterministic scenario router and optional Gemini paraphrase. Implementation calls Google Generative Language REST API `models/{GEMINI_MODEL}:generateContent` with API key from **environment**, default `gemini-2.5-flash`, temperature 0.1, a short bound context and an approved deterministic statement. Never commit API keys. Without a key, the service still answers reliably using precalculated deterministic text.

## Golden rule (exact requirement)

1. Parse the homeowner intent, reject unknown/infeasible/inconsistent retrofits and ambiguous changes.
2. Call Python `simulate()`, `green_score()`, `optimize()`, `property_value_impact()` and `carbon_change()` to recalculate any scenario.
3. Produce the approved deterministic evidence statement with per-fuel numbers, source status, units and caveats.
4. **Optionally** ask Gemini only to paraphrase the approved statement, not to calculate or infer market prices/certification.
5. Reject paraphrase if it adds numeric tokens, drops existing numeric tokens, claims unsupported certification, or removes estimate caveats; use the approved statement instead.

The prompt directs: *"Paraphrase the supplied APPROVED ANSWER naturally, in under 100 words. The approved answer and data are binding. Do not invent ANY numbers, prices, certificates, factual claims or eligibility. Do not claim to have accessed live EPC or government data. If unsure, repeat the approved answer."*

**Important limitations:** Numeric guards are not semantic proof. Non-numeric unsupported claims could still appear. This is NOT a tested function-calling LLM agent; it is a deterministic orchestrator with optional LLM explanation, which is narrower but defensible.

## Reproducible evaluation that has actually run

`python -m evaluation.judge_prompt_suite` tests scenario parsing, source evidence and agreement for deterministic responses across synthetic/demo cases. The report lives in `evaluation/deterministic_dialogue_contract.json`. **Do not label that report LLM groundedness, accuracy or supported-claim precision.**

## Provider benchmark proposed but NOT measured

Organiser targets: >=90% groundedness; >=90% factual accuracy; <5% unsupported claims. To credibly measure them:

- Assemble 30–50 independent prompts covering unknown EPC, roof unsuitable, electricity tariff doubles, heat pump raising electricity use, competing packages and unsupported measures.
- Generate provider responses using a recorded API/model version and key (never published).
- Have humans annotate *each factual claim* for evidence support and numerical correctness against the structured simulator JSON and official source metadata, including source-provenance claims.
- Compute grounded claims/total factual claims, accurate claims/total checked claims, unsupported claims/total claims, with confidence intervals or sample-size disclosure. Check separately whether provider-produced responses survived fallback.
- Publish the actual prompts, anonymised results and scripts. Do not claim achieved thresholds before that review.

## Example questions (test with UI and evaluator)

1. What if I add solar panels and a heat pump? (rerun interacting scenario)
2. What if electricity tariffs double but the heating stays as it is? (no budget confusion)
3. Is my EPC now officially C after retrofitting? (must refuse certificate claim)
4. What should I do with a £200 budget? (may select no paid work)
5. A heat pump would raise my electricity consumption; is it still worthwhile? (separate gas and electricity)
6. Can I add a wind turbine to the loft insulation package? (do not silently drop wind turbine)
7. I do not know whether my roof is suitable. (ask clarification)
8. What is my *proven* property value uplift? (no observed causal proof)
9. These are real Lloyds customer properties, right? (must disclose synthetic demos)
10. Can I guarantee a payback period? (no)

## Claim-level provider review tool (NEW)

After obtaining an API key, run `python -m evaluation.judge_prompt_suite --gemini` to generate actual provider responses and a review sheet. Human reviewers must then break the provider outputs into individual factual claims and annotate the complete claim ledger using columns in `evaluation/CLAIM_REVIEW_TEMPLATE.csv` (`response_id, claim_id, claim, supported, accurate, reviewer, evidence_ref`). `supported` and `accurate` must be 0/1 with traceable evidence. Run `python -m evaluation.llm_claim_audit --csv your_completed_reviews.csv`. Empty/incomplete files raise errors. The script reports groundedness, factual correctness, unsupported claims and whether the exact PPT thresholds are met. Without actual reviewed Gemini outputs **no numeric LLM target claims are available**. Representative prompt sampling, rejected/fallback outputs and independent human annotation remain essential.
