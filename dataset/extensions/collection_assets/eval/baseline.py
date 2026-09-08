"""Greedy collection baseline: select EVPI-times-success in descending order."""
def objective(plan):
    return sum(row["objective_contribution"] for row in plan)
