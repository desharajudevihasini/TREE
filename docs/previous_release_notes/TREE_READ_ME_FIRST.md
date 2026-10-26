# TREE — 2026 Cosmic Home Energy Edition

## What changed
- The product is called **TREE** throughout the interface.
- The 3D house was removed from the frontend. The homepage is a full-viewport illustrated night scene with the TREE marquee, stars, original tower and home art, orbit rings, and pill-shaped buttons.
- Features are now arranged as **four circular planets** instead of square cards.
- The home tools use curved panels and pill controls.
- Backend calculations and routes are unchanged and still use synthetic demo data. There is no claim of certified predictions.

## Where the code is
- `frontend/index.html` — page structure, sections and text.
- `frontend/styles.css` — entire appearance, including the bottom `TREE COSMIC` section for final overrides.
- `frontend/app.js` — button actions and API calls.
- `frontend/art/green-universe.svg` — original starfield, tower, house, rocket and forests illustration.
- `backend/main.py` — API route list. Calculation functions are in `backend/engines/`.

## Run on Mac
Open Terminal in this folder, then:
```
bash start_mac.sh
```
The script prefers Python 3.11 and starts at `http://127.0.0.1:8770` (change with `PORT=8771 bash start_mac.sh`).

## Demo path
1. Enter TREE by pressing **Let's Explore**.
2. Pick the house and choose solar/insulation.
3. Click **Calculate Upgrades** to see score, cost and carbon changes.
4. Adjust budget and run **Best Package for My Budget**.
5. Open **Ask TREE** for decision-aware dialogue and **Future Worlds** for comparisons.

*TreeHacks is a visual inspiration only. TREE is a separate project with original artwork; no affiliation is implied.*
