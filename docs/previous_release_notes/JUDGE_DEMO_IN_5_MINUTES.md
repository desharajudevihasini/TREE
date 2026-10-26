# TREE — 5-minute demo grounded in official Lloyds PS2 criteria

1. **20–30 s · Open TREE and explain what it is.** Green Home Score and retrofit decision engine, not an EPC issuer. Open the Leeds demo home.
2. **40 s · Green Home Score (15%).** Show seven subscores with exact required 25/20/15/15/10/10/5 weights; they use documented demo mappings.
3. **75 s · What-if and energy outcomes (15% + 15%).** Ask **"What if I install loft insulation and a heat pump?"** Show recalculated savings with electricity **increasing** (negative kWh saving) and gas decreasing. Explain multiplicative interactions and actual per-fuel carbon formula, with disclaimer of illustrative factors.
4. **40 s · Customer realism.** Ask **"What if electricity prices double?"** Show fresh bill outcome (not an LLM estimate). Ask **"What if I install solar and wind turbines?"** to show the system flags unsupported extensions rather than silently dropping them.
5. **45 s · Uncertainty / responsible AI (5%).** Switch to Manchester and ask **"What if I install loft insulation?"**. TREE must request missing insulation status before recommending. Explain owner-provided bills override synthetic fallback.
6. **55 s · ML evidence (20%).** Open **Our Methods**. Show NEED real UK held-out MAE and R², four-experiment challenger (property-only vs prior-year), and median and copy-last-year baselines. Explicitly point out that electricity prior-year ML does not beat the copy baseline on MAE.
7. **35 s · Business and innovation (10% + 5%).** Show budget optimizer, TreeAsk decision-aware question and ranking by achievable purchased-energy reduction.
8. **30 s · Reproducibility (10%).** Run tests, show `JUDGING_RUBRIC_AUDIT.md`, source schema and method files.

**Avoid:** "98% accurate on real homes", "we've integrated live EPC", "our LLM passed the organiser thresholds", "verified property-value uplift", "the model guarantees bills will fall". These are unsupported.
