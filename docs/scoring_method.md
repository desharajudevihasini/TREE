# Seven-component Green Home Score methodology

Official fixed weights, from Lloyds PS2:

| Subscore | Weight | GreenTwin prototype mapping (not official) |
|---|---:|---|
| Energy efficiency | 25% | EPC letter mapped A=96, B=85, C=72, D=57, E=42, F=27, G=12; missing=neutral 50 |
| Purchased-energy intensity | 20% | 100 for <=60 kWh/m²/yr, 0 for >=350, linear between |
| Insulation | 15% | Mean of loft and wall (90 insulated, 20 uninsulated, neutral 50 unknown) |
| Heating | 15% | Heat pump 90, district 70, gas boiler 40, electric resistance 35, missing 50 |
| Windows/glazing | 10% | Single 20, double 75, triple 95, missing 50 |
| Renewables | 10% | Any recorded solar >0kWp: 90, otherwise 0 |
| Smart energy management | 5% | Smart controls 90, no controls 10, missing 50 |

Overall `S = Σ(weight * subscore)`, rounded half-up to the nearest integer, clamped to 0–100.

Rounded 80–100 Highly efficient; 65–79 Good; 50–64 Moderate; 30–49 Poor; 0–29 Very poor.

All mappings **except the prescribed weights and five official classification bands are our synthetic-demo design assumptions**. A true operational model requires calibration and policy review. The post-retrofit energy-efficiency contribution is an explicitly **modelled proxy**, computed from reduction in purchased energy: initial mapped EPC value + 55 × (1 − after energy / baseline energy), clamped to 0–100. **This is not a new EPC rating/certificate**. The energy-intensity subscore independently updates using post-retrofit energy.

Unknown information uses a visible neutral placeholder and warning, which preserves numerical completeness but reduces confidence. Never quietly call this measured evidence. If baseline consumption missing, see synthetic model / heuristic disclosures in `docs/assumptions.md`.

## Score provisionality / missing-input uncertainty (NEW)

`green_score` returns `provisional`, `missing_inputs_affecting_score`, and `unknown_input_score_bound`. The bound recomputes the weighted score with each **unknown component** at its mathematical 0..100 extremes while holding known components unchanged. Each unknown loft or wall feature contributes half of the insulation component; missing measured electricity/gas makes energy intensity 0..100 rather than assuming the ML estimate is measured. These are **bounds due only to recorded unknown fields**, not statistically calibrated confidence intervals; known input error and incorrect scoring coefficients can produce results outside them. The official seven weights and official five classification thresholds are unchanged.
