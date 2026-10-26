# TREE — illustrated TreeHacks-style edition

This is a **new page**, not a minor color update. It borrows TreeHacks 2026's composition and mood (cosmic blue sky, golden illustrated tower, futuristic sign, hand-drawn accents and scrolling editorial sections). All artwork and copy are made for TREE, with no TreeHacks name or logo inside the site.

## Fastest way to run on your Mac

1. Extract the ZIP, **open Terminal in the folder that contains this file**.
2. Paste **one command**:

```bash
bash start_mac.sh
```

3. Open <http://127.0.0.1:8770> on the SAME Mac.

The script detects your installed Python 3.11, creates `.venv311` once, installs any missing packages and starts the website. Leave Terminal open. If port 8770 is occupied, use `PORT=8771 bash start_mac.sh` and open <http://127.0.0.1:8771>.

Do not open `frontend/index.html` directly; open the localhost URL so the Python API works.

## Understand the code in this order

1. **`frontend/index.html`** — page structure. Four main parts: navigation, illustrated landing page, story/feature cards, the real home lab.
2. **`frontend/styles.css`** — visual styles. The section headings `01`–`05` explain each page area. The sky illustration is `frontend/art/green-universe.svg` (original TREE artwork).
3. **`frontend/app.js`** — the interaction code, now formatted into readable functions. Start with `api()`, `init()`, `loadProperty()`, `openView()`, `renderDashboard()`, and the two button handlers.
4. **`backend/main.py`** — each `/api/...` endpoint hands work to a calculation function.
5. **`backend/engines/`** — `scoring.py` (7 scoring components), `retrofit.py` (energy impacts), `optimizer.py` (budget decisions). We preserved these modules to protect the tested formulas.

## What actually changed

- New HTML structure with a **true full-width illustrated landing scene**, not a small banner inside a dashboard.
- New handcrafted SVG of a **golden campus tower, solar-roof home, rocket, stars and moon**.
- New responsive page: About / numbers / interactive feature cards / real home lab / footer.
- Navigation actually switches working tools; the cards open Dashboard / Future Worlds / Assistant / Home Explorer.
- JavaScript was reformatted and navigation simplified for reading. Backend calculation code was **not rewritten**.
- No React, npm, 3-D engine, Google fonts, internet requests or API key required.

## Demo to judges (around 90 seconds)

1. Start with the illustrated page. Click **EXPLORE YOUR HOME**.
2. Show the Green Home Score, select 2 upgrade cards and press **CALCULATE UPGRADES**.
3. Move the **budget** slider, click **BEST PACKAGE FOR MY BUDGET**.
4. Click **Future worlds** to compare three simulated paths, then **Ask TREE** to ask a decision question.
5. Click **Our methods** and explain which estimates use synthetic data.

**Know what this is:** an energy decision prototype, not a certified EPC or market-validated valuation system. It uses synthetic demonstration properties, approximated retrofit costs/energy effects, and sourced DESNZ 2026 operational carbon factors (retrofit kWh savings still assumptions).

## Testing

```bash
python -m pytest -q
```

The preserved backend test suite contains 17 tests. Check browser behavior yourself before your submission.
