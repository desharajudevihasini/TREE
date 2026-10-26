# Start TREE on Hasini's Mac — no confusion between folders

1. Download the newest ZIP named `TREE_PS2_Complete_Basic_UX_Full_Source.zip` and extract it.
2. Open Terminal and run **exactly**:

```bash
cd "$HOME/Downloads/TREE_PS2_Submission_Core"
bash start_mac.sh
```

3. Open the **exact local URL printed by Terminal**. Keep this tab running.
4. In a **second Terminal tab** (`Command + T`):

```bash
cd "$HOME/Downloads/TREE_PS2_Submission_Core"
source .venv311/bin/activate
python -m pytest -q
```

5. The home dashboard is at `/`; an earlier full artistic design is still available at `/studio`. The dashboard deliberately uses a basic visual style so the final UX can be redesigned later.

## Real-data reproducibility

Source CSV is included legally in `data/public/anon2026_50k.csv` (UK OGL attribution).

```bash
python -m ml.need_challenger --csv data/public/anon2026_50k.csv
python -m ml.serve_need --csv data/public/anon2026_50k.csv
python -m evaluation.need_slices --csv data/public/anon2026_50k.csv
python -m evaluation.judge_prompt_suite
```

Those first commands retrain real UK research models / reports and may take some time. **You do not need to retrain for the live demo**: tested model files and reports are included.

## Demo walkthrough, 5 minutes

1. Home & score: pick **Leeds detached home**, press Calculate. Explain the seven weights and EPC caveat.
2. Retrofit lab: calculate a heat pump and show **negative electricity saving, positive gas saving**, and interacting packages.
3. Compare: today vs affordable vs ambitious; demonstrate ranking by purchased energy rather than a single fuel.
4. Ask TREE: `What if I add solar and a heat pump?` and `What if electricity prices double?` Show that numerical results are recomputed in Python.
5. Memory: mark an upgrade completed / avoid solar / change budget, save and show new recommendation.
6. Evidence: NEED heldout/median/copy baselines, error slices. Do not conflate these models with validated retrofit performance.

For presentation material, open `PPT_EVERY_SLIDE_AUDIT.md`, `JUDGING_PRIORITY.md` and `SUBMISSION_PACKAGE_INDEX.md`. They list what actually works and outstanding proof gaps without exaggeration.
