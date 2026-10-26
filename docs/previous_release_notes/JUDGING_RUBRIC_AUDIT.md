# TREE — Lloyds PS2 official judging rubric audit

**Source**: `PS2 Green Home Score - condensed.pptx`, slides 13–15, organiser-provided briefing. The percentages below are the official *category weights*, not TREE's achieved marks. We cannot assign official marks or guarantee a 10/10.

| Official category | Weight | Implemented evidence | Remaining gap / honest claim |
|---|---:|---|---|
| ML and recommendation quality | **20%** | Validated NEED 2026 50k challenger (train/validation/test), property-only and prior-year comparisons, baseline scores and held-out predictions; feasibility and budget-based optimization | Consumer home's missing-bill predictions still use synthetic-trained models; NEED research models require all official categories. Property-only electricity MAE improves only slightly over median. No directly validated retrofit-recommendation ground truth |
| Green Home Score and sustainability | **15%** | Exactly 7 official component weights totalling 100%; documented 0–100 subscores, categories and explanation; property quality warnings | Subscore mappings are model assumptions, not certified EPC methodology |
| Energy, carbon and property value | **15%** | Interacting gas/electricity model, signed per-fuel savings, solar grid import distinction, packages, non-additivity, budget, indicative **range** for property value | Heat-loss and costs approximate; carbon defaults now use sourced DESNZ 2026 operational factors, but retrofit kWh effects remain unvalidated; property value uplift synthetic and not causal market evidence |
| GenAI and LLM what-if | **15%** | True what-if scenario recomputation (retrofits and tariffs); optional Gemini constrained to paraphrasing numbers produced by backend. Rejects invented numeric values / unsupported certification phrases | Gemini API key required for live provider demonstration. 90% groundedness, 90% factual accuracy and under 5% unsupported-claims organiser targets have **not** been independently established |
| Business relevance | **10%** | Homeowner score, rank by improvement potential, feasible packages, costs, separate savings by fuel, sensitivity analysis | No integration with real Lloyds infrastructure; permissions and real household information require consent |
| Technical architecture | **10%** | FastAPI + local zero-build frontend + saved scikit-learn models; reproducible NEED and synthetic scripts, data lineage, API contracts, tests | Research models remain opt-in; secure multi-user production architecture not implemented |
| Explainability / Responsible AI | **5%** | Warnings and evidence provenance, unknown and conflicting property data flags, no invented customer records, labels not guarantees, human confirmation | Limited uncertainty quantification; fairness/bias analysis beyond simple property breakdown is pending |
| UX | **5%** | Interactive current site, manual home entry, breakdown, three futures, scenario results and comparison, method details | Final UX pass deliberately deferred at user's request |
| Innovation | **5%** | TreeAsk counterfactual questioning, 3 futures, budget optimizer, retrofit sequencing | TreeAsk benchmark synthetic only; no measured homeowner-time A/B test |

## Organiser's explicit evaluation scenarios

- **Missing / conflicting evidence:** `POST /api/properties/quality`; unknown values are not guessed into feasibility; warnings travel with calculations.
- **Infeasible upgrade:** returns reason rather than projecting fake savings.
- **Interacting upgrades:** measures are combined by multiplicative space-heating factors, not naive summation.
- **Higher heat pump electricity usage:** reported as **negative electricity saving**, while gas savings can be positive.
- **Too little information:** explicit `unavailable` valuation, neutral score assumption warnings, and TreeAsk asks for relevant missing facts.
- **LLM must not invent numbers:** scenarios recomputed in backend, AI can only paraphrase; explanation safeguard rejects some ungrounded output, but **not** a substitute for independent LLM evaluation.

## Reproduce evidence

```bash
bash start_mac.sh
# In a second Terminal window inside the project:
source .venv311/bin/activate
python -m pytest -q
python -m evaluation.judge_prompt_suite
# Optional: if downloaded the original dataset:
python -m ml.need_challenger --csv ~/Downloads/anon2026_50k.csv
```

The dialogue suite tests deterministic response/evidence **contracts** only (108 checks). Its 100% pass rate is **not** an LLM groundedness or real-world ML score. For external LLM evaluation, `GEMINI_API_KEY=... python -m evaluation.judge_prompt_suite --gemini` produces a review sheet; independent, claim-level human review is still needed before reporting the organiser's thresholds.

## Real UK test results (from saved report)

See `evaluation/need_challenger_report.json` and `evaluation/need_challenger_predictions.csv`, not copied results alone. It is a separately trained and validated NEED research model, **not** a validation of retrofit effects.

**One non-flattering result matters:** electricity with prior-year bill: copying the prior-year value gives 885.98 kWh/year MAE versus 908.02 kWh/year for the challenger ML model. Do not describe that ML as beating every baseline.

## Judges' decision and not our guarantee

The official judging score depends on independent review, the live demonstration and organiser reruns. TREE cannot be verified as "10/10" through our own test suite or the assistant's opinion.
