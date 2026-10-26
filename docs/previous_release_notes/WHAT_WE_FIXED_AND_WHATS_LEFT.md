# TREE — improvements and honest limitations

## Implemented and tested
- Preserved the working dark illustrated TREE interface, seven-part score, feasibility-aware retrofit engine, budget optimization, three futures, chat and TreeAsk.
- Added `evaluation/treeask_benchmark.py`, a reproducible **synthetic** experiment. It hides one known yes/no field in each eligible demonstration home and tests what TreeAsk asks first and whether one answer restores the complete-record package.
- Added `GET /api/evaluation/treeask-benchmark` and a results panel under **Our methods**.
- Added seven reliability tests, including missing-consumption ML fallback, budget/feasibility, TreeAsk, and a mock-file smoke test of the UK NEED evaluation pipeline.
- All 24 automated tests pass. `node --check frontend/app.js` passes.
- Existing independent NEED evaluation script retained. It will only report real-data metrics after the actual UK NEED CSV is supplied and processed.

## Actual TreeAsk experiment (synthetic fixtures)
- 57 simulated cases with one known yes/no property field hidden.
- TreeAsk selected the hidden field first in 17/57 cases.
- After one TreeAsk answer, the selected package matched the complete-record package in 54/57 cases.
- These are **not** evidence that TreeAsk beats a fixed questionnaire in a user study. Many cases already have an unchanged plan, and this benchmark is not blinded real-world data.

## Important unresolved limitations (do not claim solved)
1. **Synthetic ML data:** the original Random Forest's R² is not real-home accuracy. Real UK NEED dataset has NOT been supplied; separate NEED benchmark is prepared but not executed.
2. **ML centrality:** for demo properties with recorded synthetic usage, TREE uses those values directly; the trained model fills missing usage, not every request.
3. **Live EPC lookup:** not implemented; the app uses synthetic homes and accepts editable property data through the session API.
4. **Retrofit accuracy:** simplified assumptions; not calibrated against real installation outcomes.
5. **Property value:** displayed uplift is a toy sensitivity calculation, not market-validated. Avoid presenting it as a predicted financial gain.
6. **Carbon:** DESNZ 2026 grid-electricity and natural-gas defaults now have official source/year/scope documentation; estimated energy effects remain unvalidated.
7. **LLM:** deterministic explanations work. Gemini paraphrasing is optional and has not been verified end-to-end in this build.
8. **Real homeowner workflow:** persistent multi-user accounts, bill extraction, and verified address matching remain out of scope.
9. **TreeAsk superiority:** one synthetic counterfactual test is not a controlled comparison with a fixed form.
10. **UX:** the site is interactive and dark themed; independent usability testing is not yet done.

## Demo that you can defend
1. Open TREE, select Manchester.
2. Show the seven subscores and the original property evidence label.
3. Use Ask TREE to get a decision-sensitive question. Answer Yes/No; show the recommendation changing when relevant.
4. Move the budget slider, compare packages and the three futures.
5. Open Our Methods: show both synthetic model errors and the TreeAsk benchmark.
6. Explain the limitations above without implying UK consumption data was used.

## Run
Mac: `bash start_mac.sh`
Tests: `python -m pytest -q`
Synthetic TreeAsk benchmark: `python -m evaluation.treeask_benchmark`
Real NEED benchmark **after** downloading the official CSV: `python -m ml.validate_need --csv /path/to/actual.csv`

This is a working hackathon prototype, not a certified home energy assessment.
