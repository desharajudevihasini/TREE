# TREE — real UK evidence and opt-in real-data predictions

Run on macOS: `bash start_mac.sh`. Keep Terminal open and visit the URL it prints.

## What changed

- Trained and bundled **two separate real-UK NEED 2026 property-only models**, one for electricity and one for gas, using the official 50,000-household sample and 11 NEED categorical descriptors.
- Saved each model trained on the **same 80% train+validation subset** used by the existing challenger experiment; the published 20% test subset was not used to fit the saved models.
- Added `GET /api/evaluation/need-challenger` to expose the existing four-experiment comparison: property-only and with-prior-year-bill, electricity and gas.
- Added `POST /api/predict/need-research` to make actual predictions using the saved NEED-trained models. It **requires all 11 official NEED category fields** and rejects incomplete inputs rather than guessing a category conversion.
- Added API tests for the new endpoints.

## IMPORTANT — no fake 9.7 claim

The existing TREE consumer form still uses its original synthetic-trained fallback when a home has no measured consumption. It is NOT silently switched to the NEED model because the 11 NEED category codes are not equivalent to the consumer form's descriptors. This protects users from fake feature mapping. The NEED models are an explicit research API, not an address lookup or a validated retrofit prediction.

The real-UK challenger report has these **held-out** test results:

| Experiment | MAE (kWh/year) | R² | Median baseline MAE |
|---|---:|---:|---:|
| Electricity, property only | 1673.20 | 0.1606 | 1706.83 |
| Gas, property only | 3928.82 | 0.3367 | 4862.34 |
| Electricity, with prior-year consumption | 908.02 | see `evaluation/need_challenger_report.json` | see report |
| Gas, with prior-year consumption | 1752.45 | 0.8039 | 4883.21 |

The prior-year models are an **evaluation only**, not bundled serving models. They are not cold-start models; knowing a previous bill changes the task.

The government NEED sample is anonymised, and these benchmarks do not validate TREE's retrofit savings, valuations, or Green Home Score. An authentic 9.7/10 hackathon rating cannot be verified by tests alone; it depends on judges and a compelling, truthful demo.

## Try the research prediction API

Visit `/docs` on your local TREE server, choose `POST /api/predict/need-research`, and supply all fields from the official NEED dataset. If you want to regenerate models: `python -m ml.serve_need --csv ~/Downloads/anon2026_50k.csv`.

## Reproduce tests

`python -m pytest -q`
