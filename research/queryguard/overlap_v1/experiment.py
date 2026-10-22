"""Run the frozen synthetic matrix and retain validated exact-rational artifacts."""
import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
from . import fixtures, model, oracle, planner

SEEDS = (7,17,29)
SIZES = (6,10,12)
DENSITIES = (Fraction(1,5),Fraction(3,5))
BUDGET_FRACTIONS = (Fraction(1,4),Fraction(1,2),Fraction(3,4))
REPEATS = 3


def canonical_json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def preservation(root):
    manifest=json.loads((Path(__file__).with_name('PRESERVATION.json')).read_text())
    changed=[name for name,digest in manifest['files'].items()
             if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest]
    if changed:
        raise ValueError('protected files changed: '+', '.join(changed))
    return dict(files_checked=len(manifest['files']),status='preserved',base_commit=manifest['base_commit'])


def validate_result(problem,budget,result):
    actual=oracle.measure(problem,result['checks'])
    for field in ('cost','risk_reduction','residual_risk','coverage'):
        if result[field] != actual[field]:
            raise ValueError(f'independent accounting mismatch: {field}')
    if actual['cost']>budget or actual['risk_reduction']<0 or actual['residual_risk']<0:
        raise ValueError('invalid risk or infeasible result')
    return actual


def row(problem,budget,policy):
    samples=[]
    signature=None
    for _ in range(REPEATS):
        start=time.perf_counter_ns()
        result=planner.solve(problem,budget,policy)
        samples.append((time.perf_counter_ns()-start)/1e6)
        current=(result['checks'],result['cost'],result['risk_reduction'])
        if signature is not None and current!=signature:
            raise ValueError('nondeterministic policy result')
        signature=current
    validate_result(problem,budget,result)
    return dict(policy=policy,selected=list(result['checks']),budget=str(budget),
                cost=str(result['cost']),risk_reduction=str(result['risk_reduction']),
                residual_risk=str(result['residual_risk']),total_risk=str(result['total_risk']),
                coverage=result['coverage'],examined=result['examined'],feasible=True,
                runtime_ms=statistics.median(samples),runtime_samples_ms=samples)


def summary(rows):
    result={}
    for policy in planner.POLICIES:
        group=[r for r in rows if r['policy']==policy]
        ratios=[float(Fraction(r['optimality_ratio'])) for r in group if r['optimality_ratio'] is not None]
        result[policy]=dict(rows=len(group),matches_exact=sum(Fraction(r['risk_gap'])==0 for r in group),
                            suboptimal=sum(Fraction(r['risk_gap'])>0 for r in group),
                            undefined_ratios=sum(r['optimality_ratio'] is None for r in group),
                            min_optimality_ratio=min(ratios) if ratios else None,
                            median_optimality_ratio=statistics.median(ratios) if ratios else None,
                            max_risk_gap=str(max(Fraction(r['risk_gap']) for r in group)),
                            min_runtime_ms=min(r['runtime_ms'] for r in group),
                            median_runtime_ms=statistics.median(r['runtime_ms'] for r in group),
                            max_runtime_ms=max(r['runtime_ms'] for r in group))
    return result


def write_csv(path,rows):
    with path.open('w',newline='') as handle:
        fields=sorted(set().union(*(r.keys() for r in rows)))
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for r in rows:
            writer.writerow({k:canonical_json(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})


def run(output,seeds=SEEDS,sizes=SIZES,densities=DENSITIES,budget_fractions=BUDGET_FRACTIONS):
    """Optional matrix overrides are for tests; CLI runs the registered matrix."""
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[3]
    rows=[]
    try:
        metadata=dict(schema_version='1.0',generated_at=datetime.now(timezone.utc).isoformat(),
                      commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
                      tracked_dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root,text=True)),
                      python=platform.python_version(),platform=platform.platform(),repeats=REPEATS,
                      seeds=list(seeds),sizes=list(sizes),densities=[str(x) for x in densities],
                      budget_fractions=[str(x) for x in budget_fractions],policies=list(planner.POLICIES),
                      preservation=preservation(root),
                      source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(Path(__file__).parent.glob('*.py'))},
                      protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest())
        instances=[]
        configuration=0
        for size in sizes:
            for seed in seeds:
                for density in densities:
                    problem=fixtures.generated(seed,size,density)
                    payload=problem.to_dict()
                    workload=sha(payload)
                    instances.append(dict(workload_sha256=workload,seed=seed,checks=size,density=str(density),problem=payload))
                    full=model.account(problem,[c.id for c in problem.checks])['cost']
                    for fraction in budget_fractions:
                        budget=int(full*fraction)
                        order=configuration%len(planner.POLICIES)
                        group=[]
                        for policy in planner.POLICIES[order:]+planner.POLICIES[:order]:
                            r=row(problem,budget,policy)
                            r.update(seed=seed,checks=size,density=str(density),budget_fraction=str(fraction),workload_sha256=workload)
                            group.append(r)
                        optimum=Fraction(next(r['risk_reduction'] for r in group if r['policy']=='exact'))
                        reference=oracle.exhaustive(problem,budget)
                        exact_row=next(r for r in group if r['policy']=='exact')
                        if (tuple(exact_row['selected']),optimum) != (reference['checks'],reference['risk_reduction']):
                            raise ValueError('exact solver disagrees with independent subset oracle')
                        for r in group:
                            actual=Fraction(r['risk_reduction'])
                            if actual>optimum:
                                raise ValueError('greedy exceeds exact optimum')
                            r.update(reference_optimum=str(reference['risk_reduction']),risk_gap=str(optimum-actual),optimality_ratio=str(actual/optimum) if optimum else None)
                            rows.append(r)
                        configuration+=1
        expected=len(seeds)*len(sizes)*len(densities)*len(budget_fractions)*len(planner.POLICIES)
        keys=[(r['seed'],r['checks'],r['density'],r['budget_fraction'],r['policy']) for r in rows]
        if len(rows)!=expected or len(set(keys))!=len(rows):
            raise ValueError('wrong matrix count or duplicate configuration')
        for r in rows:
            if not all(math.isfinite(t) and t>=0 for t in r['runtime_samples_ms']):
                raise ValueError('invalid timing')
        fixture_results={}
        for name,problem,budget in (('overlap',fixtures.overlap(),6),('shared_scan_trap',fixtures.shared_scan_trap(),7)):
            fixture_results[name]=dict(problem=problem.to_dict(),budget=budget,
                                      results=[row(problem,budget,policy) for policy in planner.POLICIES])
        data=dict(metadata=metadata,rows=rows,summary=summary(rows),fixtures=fixture_results)
        (output/'results.json').write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
        (output/'inputs.json').write_text(json.dumps(instances,indent=2,sort_keys=True)+'\n')
        write_csv(output/'results.csv',rows)
        manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
        (output/'SHA256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        print(json.dumps(dict(output=str(output),rows=len(rows),instances=len(instances))))
        return data
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps(dict(error=repr(exc),completed_rows=len(rows)))+'\n')
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args().output)
