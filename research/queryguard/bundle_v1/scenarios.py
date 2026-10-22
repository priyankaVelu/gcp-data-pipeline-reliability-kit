"""Ablation and deliberately constructed, hand-computable triple counterexample."""
from dataclasses import replace
from ..overlap_v1.model import Check,Consumer,Exposure,Fault,Problem,Scan
from ..overlap_v1.fixtures import overlap,shared_scan_trap


def no_sharing(problem):
    costs={s.id:s.setup_cost for s in problem.scans}
    scans=[];checks=[]
    for i,check in enumerate(problem.checks):
        groups=[]
        for j,source in enumerate(check.scans):
            name=f'private:{i}:{j}'
            scans.append(Scan(name,costs[source]));groups.append(name)
        checks.append(replace(check,scans=tuple(groups)))
    return replace(problem,scans=tuple(scans),checks=tuple(checks))


def triple_trap():
    names=('A','B','C','D')
    return Problem((Fault('scenario',1),),tuple(Consumer(x,15 if x=='D' else 8) for x in names),
                   tuple(Exposure('scenario',x) for x in names),
                   (Scan('shared',5),Scan('other',5)),
                   tuple(Check(x,('other' if x=='D' else 'shared',),[('scenario',x)],1) for x in names))


def fixtures():
    return dict(overlap=(overlap(),6),shared_scan_trap=(shared_scan_trap(),7),triple_trap=(triple_trap(),8))
