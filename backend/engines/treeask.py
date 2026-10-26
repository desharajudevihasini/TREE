"""Decision-sensitive counterfactual question ranking; not an LLM intuition or calibrated expected value."""
from backend.schemas import Property
from backend.engines.optimizer import optimize

QUESTIONS = {
    "loft_insulated": "Is your loft already insulated?",
    "wall_insulated": "Do you know whether your walls are insulated?",
    "roof_suitable": "Do you have suitable roof space for solar panels?",
    "outdoor_space": "Is there space outside for a heat-pump unit?",
    "smart_controls": "Do you already have smart heating controls?",
}


def next_question(p: Property, budget: float | None = None, objective: str = "money", asked: list[str] | None = None) -> dict:
    asked = asked or []
    if len(asked) >= 3:
        return {"question": None, "reason": "Question budget reached.", "ranking": []}
    budget = p.budget_gbp if budget is None else budget
    if budget < 0: raise ValueError("Budget cannot be negative")
    ranking = []
    for field, question in QUESTIONS.items():
        if getattr(p, field) is not None or field in asked: continue
        world = {}
        for answer in (True, False):
            alternative = p.model_copy(update={field: answer})
            world[str(answer).lower()] = optimize(alternative, budget, objective)["best"]
        one, two = world["true"], world["false"]
        packages_differ = set(one["measures"]) != set(two["measures"])
        spread_money = abs(one["annual_bill_savings_gbp"] - two["annual_bill_savings_gbp"])
        spread_carbon = abs(one["carbon"]["reduction_kg_co2e"] - two["carbon"]["reduction_kg_co2e"])
        spread_energy = abs(one["savings"]["purchased_energy_kwh"] - two["savings"]["purchased_energy_kwh"])
        # Explicit heuristic: prefer changes in best package, then change in chosen objective.
        score = (1000 if packages_differ else 0) + {"money": spread_money, "carbon": spread_carbon,
                                                   "energy": spread_energy}[objective]
        ranking.append({"field": field, "question": question, "decision_impact_score": round(score, 2),
                        "packages_differ": packages_differ,
                        "best_if_yes": one["measures"], "best_if_no": two["measures"],
                        "annual_saving_spread_gbp": round(spread_money, 2)})
    ranking.sort(key=lambda x: -x["decision_impact_score"])
    if not ranking or ranking[0]["decision_impact_score"] < .01:
        return {"question": None, "reason": "No missing answer materially changes the selected decision under this model.", "ranking": ranking}
    top = ranking[0]
    return {"question": top["question"], "field": top["field"],
            "reason": "This answer changes the feasible best package or estimated outcome.",
            "decision_impact_score": top["decision_impact_score"], "ranking": ranking,
            "methodology": "counterfactual-binary-worlds-decision-impact-v1"}
