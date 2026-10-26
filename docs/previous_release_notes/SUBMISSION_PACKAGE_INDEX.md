# Nine Lloyds PS2 submission items — slide 15

| Required | Files | How to demonstrate |
|---|---|---|
| **A** Working prototype/dashboard | `backend/main.py`, `frontend/basic.html`, `frontend/basic.css`, `frontend/basic.js`, advanced design `/studio` | `bash start_mac.sh` → printed localhost URL |
| **B** Source + data preparation/generation, run instructions, sharing-permitted datasets | `backend/`, `ml/train.py`, `ml/need_challenger.py`, `ml/validate_need.py`, `evaluation/need_slices.py`, `data/demo/`, `data/public/anon2026_50k.csv`, `README.md` | `python -m pytest -q`; retrain/reevaluate from official CSV with documented commands |
| **C** Trained models and inference | `ml/models/annual_*.joblib`, `ml/models/need_2026/*.joblib`, `ml/predict.py`, `ml/serve_need.py` | POST `/api/predict/need-research` with official category fields; ordinary `/api/predict` labeled fallback |
| **D** Green Home Score method and mappings | `docs/scoring_method.md`, `backend/engines/scoring.py` | POST `/api/score` shows seven weights, subscores, rounded classification |
| **E** LLM implementation/prompts/API/evaluation approach | `backend/companion/assistant.py`, `docs/llm_evaluation.md`, `evaluation/judge_prompt_suite.py`, `evaluation/deterministic_dialogue_contract.json` | Demo deterministic what-if. Optional `GEMINI_API_KEY` paraphrases only; no provider accuracy claim |
| **F** Architecture diagram | `docs/architecture.md`, `docs/architecture.svg` | Diagram includes all data/calculation boundaries and research-mode separation |
| **G** Evaluation methodology and validation metrics | `evaluation/need_challenger_report.json`, `evaluation/need_real_validation.json`, `evaluation/need_slice_analysis.json`, `evaluation/report.md` | Show held-out MAE, RMSE, R², copy/median baselines, error slices |
| **H** Responsible AI note | `docs/responsible_ai.md`, `PPT_EVERY_SLIDE_AUDIT.md` | Explain privacy, source provenance, bias, missing data, not-an-EPC, noncausal value |
| **I** Held-out predictions + data schema and labels | `evaluation/need_challenger_predictions.csv`, `evaluation/need_held_out_predictions.csv`, `docs/data_dictionary.md`, `ml/need_challenger.py`, `data/public/SOURCE_AND_LICENSE.md` | Show actual vs prediction and label/flag selection logic |

**Dataset caveat:** The included NEED 50k public anonymised sample is redistributed with attribution under UK OGL. Contains no private Lloyds customer records. Synthetic demo data is separately labelled. The current saved research models use official NEED categories rather than inferred postcode-to-property guesses.
