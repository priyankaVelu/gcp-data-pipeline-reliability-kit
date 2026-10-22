"""Reproducible synthetic counterexample for QueryGuard; no external dependencies."""
from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class Check:
    name: str
    dataset: str
    coverage: int
    risk_reduction: int


CHECKS = (
    Check("A", "orders", 5, 8),
    Check("B", "orders", 5, 8),
    Check("C", "inventory", 12, 12),
)
BUDGET = 7
FIRST_SCAN_COST = 6
ADDITIONAL_CHECK_COST = 1


def plan_cost(plan: tuple[Check, ...]) -> int:
    """One base scan per dataset, plus a small incremental cost per extra check."""
    counts: dict[str, int] = {}
    for check in plan:
        counts[check.dataset] = counts.get(check.dataset, 0) + 1
    return sum(FIRST_SCAN_COST + (n - 1) * ADDITIONAL_CHECK_COST for n in counts.values())


def feasible_plans(checks=CHECKS, budget=BUDGET):
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    return [
        plan
        for size in range(len(checks) + 1)
        for plan in combinations(checks, size)
        if plan_cost(plan) <= budget
    ]


def optimize(objective: str, checks=CHECKS, budget=BUDGET):
    if objective not in ("coverage", "risk_reduction"):
        raise ValueError("unknown objective")
    plans = feasible_plans(checks, budget)
    return max(
        plans,
        key=lambda plan: (
            sum(getattr(check, objective) for check in plan),
            -plan_cost(plan),
            tuple(check.name for check in plan),
        ),
    )


def summary(plan):
    return {
        "checks": [check.name for check in plan],
        "cost": plan_cost(plan),
        "coverage": sum(check.coverage for check in plan),
        "risk_reduction": sum(check.risk_reduction for check in plan),
    }


if __name__ == "__main__":
    coverage = summary(optimize("coverage"))
    risk = summary(optimize("risk_reduction"))
    assert coverage == {"checks": ["C"], "cost": 6, "coverage": 12, "risk_reduction": 12}
    assert risk == {"checks": ["A", "B"], "cost": 7, "coverage": 10, "risk_reduction": 16}
    print("Coverage optimum:", coverage)
    print("Risk optimum:", risk)
    print("Synthetic risk improvement:", f"{(16 / 12 - 1) * 100:.1f}%")
