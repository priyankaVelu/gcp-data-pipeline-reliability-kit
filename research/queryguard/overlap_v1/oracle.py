"""Separately authored direct accounting and exhaustive oracle, without planner helpers."""
from fractions import Fraction
from itertools import combinations


def measure(problem, names):
    selected = [c for c in problem.checks if c.id in names]
    if len(selected) != len(names) or len(set(names)) != len(names):
        raise ValueError('invalid selected check identities')
    setup = sum((s.setup_cost for s in problem.scans if any(s.id in c.scans for c in selected)),Fraction())
    cost = setup+sum((c.evaluation_cost for c in selected),Fraction())
    risk = Fraction()
    residual = Fraction()
    coverage = 0
    # Consumer-first direct loss accounting, not optimized bit masks or account().
    for consumer in problem.consumers:
        for exposure in problem.exposures:
            if exposure.consumer != consumer.id:
                continue
            probability = next(f.probability for f in problem.faults if f.id == exposure.fault)
            loss = consumer.loss*probability*exposure.severity
            detected = any((exposure.fault,consumer.id) in c.detections for c in selected)
            if detected:
                coverage += 1; risk += loss
            else:
                residual += loss
    return dict(cost=cost,risk_reduction=risk,residual_risk=residual,coverage=coverage)


def exhaustive(problem, budget):
    if len(problem.checks) > 20:
        raise ValueError('oracle enumeration is limited to 20 checks')
    best = None
    for count in range(len(problem.checks)+1):
        for subset in combinations(sorted(c.id for c in problem.checks),count):
            result = measure(problem,subset)
            if result['cost'] > budget:
                continue
            key = (-result['risk_reduction'],result['cost'],len(subset),subset)
            if best is None or key < best[0]:
                best = (key,subset,result)
    return dict(checks=best[1],**best[2])
