"""Enumerate 2^6 retrofit packages with a shared interacting simulator."""
from itertools import combinations
from backend.engines.retrofit import RETROFITS, eligibility, simulate
from backend.schemas import Property


def optimize(p: Property, budget: float | None = None, objective: str = "money", excluded: set[str] | None = None) -> dict:
    if objective not in ("money", "energy", "carbon"):
        raise ValueError("objective must be money, energy or carbon")
    budget = p.budget_gbp if budget is None else budget
    if budget < 0: raise ValueError("budget must be non-negative")
    excluded = excluded or set()
    feasible = [k for k in RETROFITS if k not in excluded and eligibility(p, k)[0]]
    key = {"money": lambda r: r["annual_bill_savings_gbp"],
           "energy": lambda r: r["savings"]["purchased_energy_kwh"],
           "carbon": lambda r: r["carbon"]["reduction_kg_co2e"]}[objective]
    options = []
    for n in range(len(feasible) + 1):
        for combo in combinations(feasible, n):
            if sum(RETROFITS[k]["cost_gbp"] for k in combo) > budget: continue
            r = simulate(p, list(combo))
            options.append(r)
    options.sort(key=lambda r: (-key(r), r["cost_gbp"], len(r["measures"])))
    best = options[0]
    return {"objective": objective, "budget_gbp": budget, "best": best,
            "evaluated_feasible_packages": len(options), "affordable_nonempty_packages": sum(bool(x["measures"]) for x in options),
            "top_alternatives": options[1:4],
            "warning": "Optimization is over a simplified, documented catalogue; outputs are estimates, not guaranteed savings."}


def parallel_universes(p: Property, budget: float | None = None) -> dict:
    budget = p.budget_gbp if budget is None else budget
    current = simulate(p, [])
    affordable = optimize(p, budget)["best"]
    ambitious = optimize(p, 30000, "carbon")["best"]
    return {"property_id": p.property_id, "scenarios": [
        {"name": "Today", **current},
        {"name": "Affordable future", **affordable},
        {"name": "Ambitious future", **ambitious},
    ]}


def retrofit_chess(p: Property, measures: list[str]) -> dict:
    # Sequential milestones; physical final performance is order-independent under this annual steady-state model.
    for key in measures:
        if not eligibility(p, key)[0]: raise ValueError(f"Not feasible: {key}")
    def get_path(order):
        return [{"stage": i, "measure_added": step, "result": simulate(p, order[:i])}
                for i, step in enumerate(order, start=1)]
    reverse = list(reversed(measures))
    return {"first_order": get_path(measures), "reverse_order": get_path(reverse),
            "note": "Final steady-state annual energy is order-independent for the same final package. Interim bill savings and timing can differ; no fictitious final-energy sequence benefit is claimed."}
