"""Deterministic bounded union-risk-per-marginal-cost lookahead, without fallback."""
from fractions import Fraction
from itertools import combinations
from ..overlap_v1.planner import Prepared


def bundle_greedy(problem, budget, k=2):
    if type(k) is not int or k not in (1,2,3):
        raise ValueError('k must be 1, 2 or 3 (bounded lookahead)')
    p=Prepared(problem,budget)
    covered=opened=cost=examined=0
    selected=[]
    remaining=set(range(len(p.checks)))
    steps=[]
    while remaining:
        best=None
        for size in range(1,min(k,len(remaining))+1):
            for bundle in combinations(sorted(remaining),size):
                examined+=1
                atoms=groups=0
                evaluation=0
                for i in bundle:
                    atoms |= p.masks[i]
                    groups |= p.groups[i]
                    evaluation += p.evaluations[i]
                extra=evaluation+p.bit_sum(groups & ~opened,p.scan_costs)
                if cost+extra>p.budget:
                    continue
                gain=p.bit_sum(atoms & ~covered,p.weights)
                if gain<=0:
                    continue
                priority=(int(extra==0),Fraction(gain,extra) if extra else Fraction(gain),gain,-extra,-size)
                ids=tuple(p.checks[i].id for i in bundle)
                if best is None or priority>best[0] or (priority==best[0] and ids<best[1]):
                    best=(priority,ids,bundle,atoms,groups,extra,gain)
        if best is None:
            break
        _,ids,bundle,atoms,groups,extra,gain=best
        selected.extend(bundle);remaining.difference_update(bundle)
        covered |= atoms;opened |= groups;cost+=extra
        steps.append(dict(bundle=ids,marginal_cost=Fraction(extra,p.cost_unit),
                          marginal_risk=Fraction(gain,p.risk_unit),
                          cumulative_cost=Fraction(cost,p.cost_unit)))
    result=p.result(selected,examined)
    result.update(k=k,rounds=len(steps),steps=steps)
    return result
