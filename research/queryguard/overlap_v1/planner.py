"""Small-instance exact search and explicitly defined marginal greedy policies."""
from fractions import Fraction
from math import lcm
from .model import account, number

POLICIES = ('exact','risk_aware_greedy','coverage_greedy','cost_aware_greedy')
EXACT_LIMIT = 20


class Prepared:
    def __init__(self, problem, budget):
        self.problem = problem
        self.budget_value = number(budget,'budget')
        if self.budget_value < 0:
            raise ValueError('budget must be nonnegative')
        self.checks = problem.checks  # Problem canonicalizes IDs.
        weights = problem.weights()
        self.atoms = tuple(sorted(weights))
        self.risk_unit = lcm(*(w.denominator for w in weights.values())) if weights else 1
        self.weights = tuple(int(weights[a]*self.risk_unit) for a in self.atoms)
        atom_index = {a:i for i,a in enumerate(self.atoms)}
        scan_index = {s.id:i for i,s in enumerate(problem.scans)}
        self.cost_unit = lcm(self.budget_value.denominator,
                             *(s.setup_cost.denominator for s in problem.scans),
                             *(c.evaluation_cost.denominator for c in self.checks))
        self.budget = int(self.budget_value*self.cost_unit)
        self.scan_costs = tuple(int(s.setup_cost*self.cost_unit) for s in problem.scans)
        self.evaluations = tuple(int(c.evaluation_cost*self.cost_unit) for c in self.checks)
        self.masks = tuple(sum(1 << atom_index[a] for a in c.detections) for c in self.checks)
        self.groups = tuple(sum(1 << scan_index[s] for s in c.scans) for c in self.checks)

    def bit_sum(self, mask, values):
        result = 0
        while mask:
            bit = mask & -mask
            result += values[bit.bit_length()-1]
            mask ^= bit
        return result

    def increment(self, index, opened):
        return self.evaluations[index]+self.bit_sum(self.groups[index] & ~opened,self.scan_costs)

    def result(self, indices, examined):
        result = account(self.problem,[self.checks[i].id for i in indices])
        result['examined'] = examined
        return result


def exact(problem, budget):
    if len(problem.checks) > EXACT_LIMIT:
        raise ValueError(f'exact search is limited to {EXACT_LIMIT} checks')
    p = Prepared(problem,budget)
    best_risk, best_key, best_indices = -1, None, ()
    examined = 0

    def visit(index, covered, opened, cost, risk, indices):
        nonlocal best_risk,best_key,best_indices,examined
        if index == len(p.checks):
            examined += 1
            key = (cost,len(indices),tuple(p.checks[i].id for i in indices))
            if risk > best_risk or (risk == best_risk and key < best_key):
                best_risk,best_key,best_indices = risk,key,indices
            return
        visit(index+1,covered,opened,cost,risk,indices)
        extra = p.increment(index,opened)
        if cost+extra <= p.budget:
            gain = p.bit_sum(p.masks[index] & ~covered,p.weights)
            visit(index+1,covered | p.masks[index],opened | p.groups[index],cost+extra,risk+gain,indices+(index,))

    visit(0,0,0,0,0,())
    return p.result(best_indices,examined)


def greedy(problem, budget, policy='risk_aware_greedy'):
    if policy not in POLICIES[1:]:
        raise ValueError('unknown greedy policy')
    p = Prepared(problem,budget)
    covered, opened, cost = 0,0,0
    selected = []
    examined = 0
    remaining = set(range(len(p.checks)))
    while remaining:
        candidates = []
        for index in sorted(remaining):
            examined += 1
            extra = p.increment(index,opened)
            if cost+extra > p.budget:
                continue
            new = p.masks[index] & ~covered
            gain = p.bit_sum(new,p.weights) if policy == 'risk_aware_greedy' else new.bit_count()
            if gain <= 0:
                continue
            if policy == 'coverage_greedy':
                priority = (0,Fraction(gain),gain,-extra)
            else:
                priority = (int(extra == 0),Fraction(gain,extra) if extra else Fraction(gain),gain,-extra)
            candidates.append((index,extra,priority))
        if not candidates:
            break
        # First ID wins exact ties, independent of input ordering or set iteration.
        index,extra,_ = max(candidates,key=lambda x:x[2])
        selected.append(index);remaining.remove(index)
        covered |= p.masks[index];opened |= p.groups[index];cost += extra
    return p.result(selected,examined)


def solve(problem, budget, policy='exact'):
    if policy == 'exact':
        return exact(problem,budget)
    return greedy(problem,budget,policy)
