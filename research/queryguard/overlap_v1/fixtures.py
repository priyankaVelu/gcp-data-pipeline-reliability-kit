"""Hand-computable counterexamples and seeded synthetic instances."""
from fractions import Fraction
import random
from .model import Check, Consumer, Exposure, Fault, Problem, Scan, number


def overlap():
    return Problem((Fault('f1','1/5'),Fault('f2','3/10')),
                   (Consumer('critical',100),Consumer('bulk',10)),
                   (Exposure('f1','critical'),Exposure('f1','bulk'),Exposure('f2','critical')),
                   (Scan('shared',4),),
                   (Check('A',('shared',),[('f1','critical'),('f1','bulk')],1),
                    Check('B',('shared',),[('f1','critical'),('f2','critical')],1),
                    Check('redundant',('shared',),[('f1','critical')],1)))


def shared_scan_trap():
    faults = tuple(Fault(name,'1/3') for name in ('a','b','c'))
    consumers = tuple(Consumer(f'{name}{i}',Fraction(24,5) if name in ('a','b') else 3)
                      for name,count in (('a',5),('b',5),('c',12)) for i in range(count))
    exposures = tuple(Exposure(c.id[0],c.id) for c in consumers)
    checks = tuple(Check(name.upper(),('orders' if name in ('a','b') else 'inventory',),
                         [(e.fault,e.consumer) for e in exposures if e.fault == name],1)
                   for name in ('a','b','c'))
    return Problem(faults,consumers,exposures,(Scan('orders',5),Scan('inventory',5)),checks)


def generated(seed, checks=10, density=Fraction(1,5)):
    density = number(density,'incidence density')
    if type(seed) is not int or type(checks) is not int or checks < 0 or not 0 <= density <= 1:
        raise ValueError('seed/check count/density are invalid')
    rng = random.Random(seed)
    masses = [rng.randint(1,9) for _ in range(8)]
    faults = tuple(Fault(f'f{i}',Fraction(4*m,5*sum(masses))) for i,m in enumerate(masses))
    consumers = tuple(Consumer(f'c{i}',rng.randint(1,50)) for i in range(5))
    exposures = []
    for fault in faults:
        affected = [c.id for c in consumers if rng.random() < .6]
        if not affected:
            affected = [rng.choice(consumers).id]
        exposures.extend(Exposure(fault.id,c) for c in affected)
    scans = tuple(Scan(f's{i}',rng.randint(1,9)) for i in range(4))
    result = []
    for i in range(checks):
        groups = [rng.choice(scans).id]
        if i % 5 == 4:
            groups.append(rng.choice([s.id for s in scans if s.id != groups[0]]))
        incidence = [(e.fault,e.consumer) for e in exposures if rng.random() < float(density)]
        result.append(Check(f'q{i:02}',groups,incidence,rng.randint(0,3)))
    return Problem(faults,consumers,tuple(exposures),scans,tuple(result))
