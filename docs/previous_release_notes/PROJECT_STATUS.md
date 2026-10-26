# TREE — Hackathon prototype status

- **New immersive illustration-based frontend:** built in plain HTML, CSS and JavaScript.
- **Backend:** existing FastAPI API unchanged.
- **7-component score:** existing implementation preserved.
- **Recommendations, simulation, budget optimization, scenarios, comparison ranking and energy assistant:** preserved.
- **Synthetic ML evaluation:** existing demonstrator and reports preserved.
- **Tests:** 17/17 backend unit/API tests pass; JavaScript passes `node --check`.
- **Browser UI inspection:** visual render tested at 1440x900 and 390x844 (no horizontal overflow), click handlers tested with backend-generated mock responses for score, retrofit simulation, scenarios, ranking, and evaluation. The team's Mac should still be used for final live API/browser demo check.
- **Evidence caveat:** property examples and energy-effect assumptions are synthetic/illustrative, not validated live UK house or valuation data.

Read START_HERE.md first, then open frontend/index.html and frontend/app.js.
