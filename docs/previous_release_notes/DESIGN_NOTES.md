# TREE: the 2026 cosmic illustrated redesign

Reference: https://2026.treehacks.com — **visual inspiration only**. The new site echoes the page's space-themed composition: deep blue starry sky, oversize floating sci-fi sign, playful decorative architecture, illustrated landscape, and an editorial scroll. It uses original TREE lettering, solar home art, a golden campus-style tower and rocket. We have not copied the TreeHacks logo, proprietary artwork, website code, or written content.

## Files changed
- `frontend/index.html`: rebuilt page structure (hero / about / 4 interactive exploration cards / real lab / footer).
- `frontend/styles.css`: readable, five-section stylesheet with responsive and reduced-motion styles.
- `frontend/art/green-universe.svg`: original, local vector art; no network dependencies.
- `frontend/app.js`: readable formatting and navigation functions; calculation response rendering still uses the existing backend API.
- `start_mac.sh`: correctly selects Python 3.11 and default port 8770, avoiding previous startup issues.

Backend engines were deliberately not rewritten. Tested functions and assumptions are in `backend/engines/`.

Visual QA: the hero was rendered at desktop and mobile viewport sizes using inline HTML/CSS/SVG. Browser interface controls were exercised against mocked responses computed from the real FastAPI endpoints. Actual app still needs a check in Safari on the team's Mac before submission.
