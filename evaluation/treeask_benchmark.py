"""Reproducible synthetic counterfactual TreeAsk benchmark.

This is an internal simulation, NOT a homeowner study or proof of real-world benefit.
Run: python -m evaluation.treeask_benchmark
"""
import json
from pathlib import Path
from backend.demo import DEMOS
from backend.engines.treeask import next_question, QUESTIONS
from backend.engines.optimizer import optimize

ROOT = Path(__file__).resolve().parents[1]

def run():
    cases = []
    for home in DEMOS.values():
        for unknown in ("loft_insulated", "wall_insulated", "roof_suitable", "outdoor_space", "smart_controls"):
            original = getattr(home, unknown)
            if original is None:
                continue
            incomplete = home.model_copy(update={unknown: None})
            answer = next_question(incomplete, incomplete.budget_gbp)
            chosen = answer.get("field")
            truth = optimize(home, home.budget_gbp)["best"]["measures"]
            unverified = optimize(incomplete, incomplete.budget_gbp)["best"]["measures"]
            after = incomplete.model_copy(update={chosen: getattr(home, chosen)}) if chosen else incomplete
            corrected = optimize(after, after.budget_gbp)["best"]["measures"]
            cases.append({
                "home": home.property_id, "hidden_field": unknown,
                "asked_field": chosen,
                "asks_hidden_field_first": chosen == unknown,
                "plan_before": unverified, "plan_after_one_answer": corrected,
                "plan_with_complete_record": truth,
                "one_question_reaches_complete_record_plan": set(corrected) == set(truth),
                "initial_plan_matches_complete_record": set(unverified) == set(truth),
            })
    result = {
        "dataset": "Synthetic demo homes with one known binary field deliberately hidden",
        "method": "Compare one TreeAsk question with a static five-question checklist; ground truth is the original synthetic demo record",
        "not_real_world_validation": True,
        "cases": len(cases),
        "treeask_one_question_matches_complete_plan": sum(x["one_question_reaches_complete_record_plan"] for x in cases),
        "treeask_asks_hidden_field_first": sum(x["asks_hidden_field_first"] for x in cases),
        "initial_plan_matches_complete_plan": sum(x["initial_plan_matches_complete_record"] for x in cases),
        "fixed_form_questions": len(QUESTIONS),
        "important_limitation": "Fixed-form completion would use all five answers. This test does not establish that one question is always enough, or that outcomes are correct for real households.",
        "case_details": cases,
    }
    out = ROOT/"evaluation"/"treeask_synthetic_benchmark.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"Cases: {result['cases']}; first question hits hidden field: {result['treeask_asks_hidden_field_first']}; one-answer plan agrees: {result['treeask_one_question_matches_complete_plan']}")
    return result

if __name__ == "__main__":
    run()
