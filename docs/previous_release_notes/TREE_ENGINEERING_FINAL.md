# TREE — rubric-led engineering build

This engineering pass followed the **actual Lloyds PS2 judging criteria** in `JUDGING_RUBRIC_AUDIT.md`. The existing dark UX is preserved; final visual polish has been deferred.

## Main changes from the previous ZIP

- Real, calculation-backed **what-if chat** for individual and multiple supported retrofits, and changed electricity/gas tariffs, including doubled rates.
- Recalculates fuel changes, bills, costs, score, carbon from shared scenario logic before any optional LLM paraphrase.
- Handles missing, conflicting and infeasible property evidence without silently assuming eligibility.
- Returns a clear clarification for unsupported composite scenarios; does not drop an unsupported wind turbine or battery from an otherwise supported package.
- Adds `POST /api/properties/quality`, evidence provenance in scenario results, and live status of NEED challenger work in **Our Methods**.
- Tightens optional Gemini guardrail against changed or missing numeric evidence and unsupported certification phrases. This is not an independent LLM benchmark.
- Adds extensive judge-oriented tests, deterministic dialogue-contract suite and a source-backed weighted rubric audit.

## How to run on a Mac

```bash
cd ~/Downloads/TREE_Rubric_Release
bash start_mac.sh
```

Open the localhost URL printed by Terminal, keep that window open.

Second Terminal:

```bash
cd ~/Downloads/TREE_Rubric_Release
source .venv311/bin/activate
python -m pytest -q
python -m evaluation.judge_prompt_suite
```

**Real-data research models and their 2026 NEED held-out reports remain separate from the original homeowner form**; without a verified conversion from consumer answers to official NEED categories it would be dishonest to silently replace that model.

For exact judges' rubric and evidence: `JUDGING_RUBRIC_AUDIT.md`. For short presentation: `JUDGE_DEMO_IN_5_MINUTES.md`.

## Honest limitations

No live EPC API credential/address match; synthetic-trained consumption fallback for homeowner custom entries; unvalidated retrofit installation costs and carbon-factors; toy property-value uplift range; provider-level LLM evaluation needs an actual key and independent claim-level review. The release is a stronger engineering prototype, **not** a guaranteed perfect score.
