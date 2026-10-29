"""Deterministic equal-budget bundle benchmark; never overwrites a run."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
from fractions import Fraction as F
from ..overlap_v1 import experiment as old, fixtures, model, oracle, planner
from .planner import bundle_greedy
from .scenarios import no_sharing, fixtures as small_fixtures

POLICIES = planner.POLICIES + ('bundle_2', 'bundle_3')
MODES = ('shared', 'no_sharing')
PHASES = (('frozen', (7,17,29), (6,10,12)), ('expanded', (43,101,211), (8,14)))


def solve(problem, budget, policy):
    return (bundle_greedy(problem,budget,int(policy[-1])) if policy.startswith('bundle_')
            else planner.solve(problem,budget,policy))


def check(problem,budget,result):
    old.validate_result(problem,budget,result)
    selected=[]
    for step in result.get('steps',[]):
        before=oracle.measure(problem,selected)
        selected.extend(step['bundle'])
        after=oracle.measure(problem,selected)
        assert after['cost']-before['cost']==step['marginal_cost']
        assert after['risk_reduction']-before['risk_reduction']==step['marginal_risk']
        assert after['cost']==step['cumulative_cost']
    if 'steps' in result:
        assert sorted(selected)==list(result['checks'])


def timed(problem,budget,policy):
    samples=[]; signature=None
    for _ in range(3):
        start=time.perf_counter_ns(); result=solve(problem,budget,policy)
        samples.append((time.perf_counter_ns()-start)/1e6)
        current=repr(result)
        if signature is not None: assert signature==current
        signature=current
    check(problem,budget,result)
    row=dict(policy=policy,selected=list(result['checks']),budget=str(budget),
             **{k:str(result[k]) for k in ('cost','risk_reduction','residual_risk','total_risk')},
             coverage=result['coverage'],examined=result['examined'],feasible=True,
             runtime_ms=statistics.median(samples),runtime_samples_ms=samples)
    if 'steps' in result:
        row.update(k=result['k'],rounds=result['rounds'],steps=result['steps'])
    return row


def summarize(rows):
    summary={}
    for phase in sorted({r['phase'] for r in rows}):
        for mode in MODES:
            group=[r for r in rows if r['phase']==phase and r['cost_model']==mode]
            for policy in POLICIES:
                subset=[r for r in group if r['policy']==policy]
                ratios=[float(F(r['optimality_ratio'])) for r in subset if r['optimality_ratio'] is not None]
                item=dict(rows=len(subset),matches_exact=sum(F(r['risk_gap'])==0 for r in subset),
                          min_ratio=min(ratios) if ratios else None,
                          median_runtime_ms=statistics.median(r['runtime_ms'] for r in subset),
                          max_risk_gap=str(max(F(r['risk_gap']) for r in subset)),
                          comparisons={})
                for baseline in POLICIES[1:5]:
                    pairs=[]; byseed={}
                    for r in subset:
                        b=next(b for b in group if b['policy']==baseline and all(b[k]==r[k] for k in ('seed','checks','density','budget_fraction')))
                        delta=F(r['risk_reduction'])-F(b['risk_reduction']); pairs.append(delta)
                        if r['optimality_ratio'] is not None:
                            byseed.setdefault(r['seed'],[]).append(float(F(r['optimality_ratio'])-F(b['optimality_ratio'])))
                    means={str(s):statistics.mean(v) for s,v in byseed.items()}
                    values=list(means.values())
                    item['comparisons'][baseline]=dict(wins=sum(x>0 for x in pairs),ties=sum(x==0 for x in pairs),losses=sum(x<0 for x in pairs),seed_mean_ratio_delta=means,
                        mean=statistics.mean(values) if values else None,range=[min(values),max(values)] if values else None,sample_sd=statistics.stdev(values) if len(values)>1 else None)
                summary[f'{phase}/{mode}/{policy}']=item
    return summary


def preservation(root):
    manifest=json.loads(Path(__file__).with_name('PRESERVATION.json').read_text())
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    return len(manifest['files'])


def run(output,phases=PHASES,densities=old.DENSITIES,fractions=old.BUDGET_FRACTIONS):
    start=time.perf_counter(); output=Path(output); output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[3]; rows=[]
    try:
        metadata=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            tracked_dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root,text=True)),
            python=platform.python_version(),platform=platform.platform(),repeats=3,
            phases=phases,densities=list(map(str,densities)),budget_fractions=list(map(str,fractions)),
            protected_files=preservation(root),
            source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in (Path(__file__).parent,Path(old.__file__).parent) for p in sorted(folder.glob('*.py'))},
            protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest())
        instances=[]
        for phase,seeds,sizes in phases:
            for size in sizes:
                for seed in seeds:
                    for density in densities:
                        source=fixtures.generated(seed,size,density); full=model.account(source,[c.id for c in source.checks])['cost']
                        for mode in MODES:
                            problem=source if mode=='shared' else no_sharing(source)
                            digest=old.sha(problem.to_dict())
                            instances.append(dict(phase=phase,seed=seed,checks=size,density=str(density),cost_model=mode,workload_sha256=digest,problem=problem.to_dict()))
                            for fraction in fractions:
                                budget=int(full*fraction); reference=oracle.exhaustive(problem,budget)
                                offset=len(rows)//6%6; policies=POLICIES[offset:]+POLICIES[:offset]
                                for policy in policies:
                                    r=timed(problem,budget,policy); actual=F(r['risk_reduction']); optimum=reference['risk_reduction']
                                    assert actual<=optimum
                                    if policy=='exact': assert tuple(r['selected'])==reference['checks']
                                    r.update(phase=phase,cost_model=mode,seed=seed,checks=size,density=str(density),budget_fraction=str(fraction),workload_sha256=digest,source_workload_sha256=old.sha(source.to_dict()),reference_optimum=str(optimum),risk_gap=str(optimum-actual),optimality_ratio=str(actual/optimum) if optimum else None)
                                    rows.append(r)
                            print(f'{phase} n={size} seed={seed} density={density} {mode}: {len(rows)} rows',flush=True)
        legacy=json.loads((Path(old.__file__).parent/'results/run-1/results.json').read_text())['rows']
        comparisons=0
        for r in rows:
            if r['phase']=='frozen' and r['cost_model']=='shared' and r['policy'] in planner.POLICIES:
                b=next(b for b in legacy if all(b[k]==r[k] for k in ('seed','checks','density','budget_fraction','policy')))
                for k,v in b.items():
                    if k not in ('runtime_ms','runtime_samples_ms'): assert r[k]==v,(k,r,b)
                comparisons+=1
        metadata['legacy_rows_reproduced']=comparisons
        fixture_results={}
        for name,(source,budget) in small_fixtures().items():
            fixture_results[name]={}
            for mode in MODES:
                problem=source if mode=='shared' else no_sharing(source)
                fixture_results[name][mode]=dict(problem=problem.to_dict(),budget=budget,results=[timed(problem,budget,p) for p in POLICIES])
        data=dict(metadata=metadata,rows=rows,summary=summarize(rows),fixtures=fixture_results)
        dump=lambda p,v:p.write_text(json.dumps(v,indent=2,sort_keys=True,default=str,allow_nan=False)+'\n')
        dump(output/'inputs.json',instances); dump(output/'results.json',data)
        old.write_csv(output/'results.csv',json.loads(json.dumps(rows,default=str)))
        dump(output/'execution.json',dict(end_to_end_seconds=time.perf_counter()-start,excludes='execution.json and SHA256.json writes'))
        dump(output/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())})
        return data
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps(dict(error=repr(exc),completed_rows=len(rows))))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args().output)
