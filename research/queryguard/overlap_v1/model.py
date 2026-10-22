"""Explicit fault-scenario/consumer incidence and exact rational accounting."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

Atom = tuple[str, str]


def number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal, Fraction)):
        raise ValueError(f'{field} must be a finite rational number')
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError(f'{field} must be a finite rational number') from exc


def identifier(value):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError('IDs must be nonempty strings without surrounding whitespace')
    return value


@dataclass(frozen=True)
class Fault:
    id: str
    probability: Fraction

    def __post_init__(self):
        identifier(self.id)
        p = number(self.probability, 'probability')
        if not 0 <= p <= 1:
            raise ValueError('probability must be in [0,1]')
        object.__setattr__(self, 'probability', p)


@dataclass(frozen=True)
class Consumer:
    id: str
    loss: Fraction

    def __post_init__(self):
        identifier(self.id)
        loss = number(self.loss, 'consumer loss')
        if loss < 0:
            raise ValueError('consumer loss must be nonnegative')
        object.__setattr__(self, 'loss', loss)


@dataclass(frozen=True)
class Exposure:
    fault: str
    consumer: str
    severity: Fraction = Fraction(1)

    def __post_init__(self):
        identifier(self.fault); identifier(self.consumer)
        severity = number(self.severity, 'severity')
        if not 0 <= severity <= 1:
            raise ValueError('severity must be in [0,1]')
        object.__setattr__(self, 'severity', severity)


@dataclass(frozen=True)
class Scan:
    id: str
    setup_cost: Fraction

    def __post_init__(self):
        identifier(self.id)
        cost = number(self.setup_cost, 'scan setup cost')
        if cost < 0:
            raise ValueError('scan setup cost must be nonnegative')
        object.__setattr__(self, 'setup_cost', cost)


@dataclass(frozen=True)
class Check:
    id: str
    scans: tuple[str, ...]
    detections: frozenset[Atom]
    evaluation_cost: Fraction = Fraction(0)

    def __post_init__(self):
        identifier(self.id)
        if isinstance(self.scans, str):
            raise ValueError('scans must be a sequence of scan IDs')
        scans = tuple(sorted({identifier(s) for s in self.scans}))
        atoms = set()
        for pair in self.detections:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError('detection incidence must contain [fault,consumer] pairs')
            atoms.add((identifier(pair[0]), identifier(pair[1])))
        cost = number(self.evaluation_cost, 'check evaluation cost')
        if cost < 0:
            raise ValueError('check evaluation cost must be nonnegative')
        object.__setattr__(self, 'scans', scans)
        object.__setattr__(self, 'detections', frozenset(atoms))
        object.__setattr__(self, 'evaluation_cost', cost)


@dataclass(frozen=True)
class Problem:
    faults: tuple[Fault, ...]
    consumers: tuple[Consumer, ...]
    exposures: tuple[Exposure, ...]
    scans: tuple[Scan, ...]
    checks: tuple[Check, ...]

    def __post_init__(self):
        for field, cls in (('faults',Fault),('consumers',Consumer),('exposures',Exposure),('scans',Scan),('checks',Check)):
            values = tuple(getattr(self, field))
            if not all(isinstance(x, cls) for x in values):
                raise ValueError(f'{field} contains an invalid record')
            key = (lambda x:(x.fault,x.consumer)) if field == 'exposures' else (lambda x:x.id)
            if len({key(x) for x in values}) != len(values):
                raise ValueError(f'duplicate {field} identity')
            object.__setattr__(self, field, tuple(sorted(values,key=key)))
        if sum((f.probability for f in self.faults), Fraction()) > 1:
            raise ValueError('mutually exclusive scenario probabilities must sum to at most 1')
        fault_ids = {f.id for f in self.faults}
        consumer_ids = {c.id for c in self.consumers}
        scan_ids = {s.id for s in self.scans}
        for e in self.exposures:
            if e.fault not in fault_ids or e.consumer not in consumer_ids:
                raise ValueError('exposure references an unknown fault or consumer')
        atoms = {(e.fault,e.consumer) for e in self.exposures}
        for check in self.checks:
            if not set(check.scans) <= scan_ids:
                raise ValueError('check references an unknown scan group')
            if not check.detections <= atoms:
                raise ValueError('detection incidence references an unmodeled exposure')

    def weights(self):
        probabilities = {f.id:f.probability for f in self.faults}
        losses = {c.id:c.loss for c in self.consumers}
        return {(e.fault,e.consumer): probabilities[e.fault]*losses[e.consumer]*e.severity
                for e in self.exposures}

    def to_dict(self):
        return dict(faults=[dict(id=f.id,probability=str(f.probability)) for f in self.faults],
                    consumers=[dict(id=c.id,loss=str(c.loss)) for c in self.consumers],
                    exposures=[dict(fault=e.fault,consumer=e.consumer,severity=str(e.severity)) for e in self.exposures],
                    scans=[dict(id=s.id,setup_cost=str(s.setup_cost)) for s in self.scans],
                    checks=[dict(id=c.id,scans=list(c.scans),detections=[list(a) for a in sorted(c.detections)],
                                 evaluation_cost=str(c.evaluation_cost)) for c in self.checks])

    @classmethod
    def from_dict(cls, value):
        fields = dict(faults=Fault,consumers=Consumer,exposures=Exposure,scans=Scan,checks=Check)
        if not isinstance(value,dict) or set(value) != set(fields):
            raise ValueError('problem needs exactly faults, consumers, exposures, scans and checks')
        try:
            return cls(**{name:tuple(record(**row) for row in value[name]) for name,record in fields.items()})
        except TypeError as exc:
            raise ValueError(f'invalid problem record: {exc}') from exc


def account(problem, selected):
    """Union risk/coverage and distinct scan costs. Unknown/repeated checks are errors."""
    if isinstance(selected, str):
        raise ValueError('selected checks must be a sequence of IDs, not a string')
    ids = tuple(selected)
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate checks in plan')
    checks = {c.id:c for c in problem.checks}
    if not set(ids) <= set(checks):
        raise ValueError('unknown check in plan')
    covered, scans = set(), set()
    evaluation = Fraction()
    for name in ids:
        covered.update(checks[name].detections)
        scans.update(checks[name].scans)
        evaluation += checks[name].evaluation_cost
    weights = problem.weights()
    risk = sum((weights[a] for a in covered), Fraction())
    total = sum(weights.values(), Fraction())
    cost = evaluation + sum((s.setup_cost for s in problem.scans if s.id in scans), Fraction())
    return dict(checks=tuple(sorted(ids)),cost=cost,risk_reduction=risk,residual_risk=total-risk,
                total_risk=total,covered_pairs=tuple(sorted(covered)),coverage=len(covered))
