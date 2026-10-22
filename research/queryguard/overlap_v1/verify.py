"""Verify manifests, CSV parity, direct accounting and exact reference outcomes."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
import statistics
from itertools import product
from pathlib import Path
from .experiment import canonical_json, preservation, sha, summary
from .model import Problem
from .fixtures import generated
from .oracle import exhaustive, measure
from .planner import POLICIES


def verify(directory, check_optima=True):
    directory=Path(directory)
    manifest=json.loads((directory/'SHA256.json').read_text())
    if set(manifest)!={'results.json','inputs.json','results.csv'}:
        raise ValueError('unexpected manifest membership')
    for name,digest in manifest.items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'artifact hash mismatch: {name}')
    data=json.loads((directory/'results.json').read_text())
    inputs=json.loads((directory/'inputs.json').read_text())
    problems={}
    for instance in inputs:
        if sha(instance['problem'])!=instance['workload_sha256']:
            raise ValueError('workload hash mismatch')
        if instance['workload_sha256'] in problems:
            raise ValueError('duplicate workload instance')
        regenerated=generated(instance['seed'],instance['checks'],Fraction(instance['density'])).to_dict()
        if regenerated!=instance['problem']:
            raise ValueError('input does not match declared seed/configuration')
        problems[instance['workload_sha256']]=(Problem.from_dict(instance['problem']),instance)
    expected=math.prod(len(data['metadata'][k]) for k in ('seeds','sizes','densities','budget_fractions','policies'))
    if len(data['rows'])!=expected or data['metadata']['policies']!=list(POLICIES):
        raise ValueError('wrong policy matrix')
    seen=set();optima={}
    with (directory/'results.csv').open(newline='') as handle:
        csv_rows=list(csv.DictReader(handle))
    if len(csv_rows)!=len(data['rows']):
        raise ValueError('CSV row count mismatch')
    for r,csv_row in zip(data['rows'],csv_rows):
        expected_csv={k:canonical_json(v) if isinstance(v,(dict,list)) else '' if v is None else str(v) for k,v in r.items()}
        if csv_row!=expected_csv:
            raise ValueError('CSV/JSON field mismatch')
        key=(r['checks'],r['seed'],r['density'],r['budget_fraction'],r['policy'])
        if key in seen:
            raise ValueError('duplicate row')
        seen.add(key)
        p,instance=problems[r['workload_sha256']]
        if any(r[k]!=instance[k] for k in ('seed','checks','density')):
            raise ValueError('row configuration does not match input')
        if len(p.checks)!=r['checks']:
            raise ValueError('wrong input size')
        budget=Fraction(r['budget'])
        all_checks=[c.id for c in p.checks]
        if budget!=int(measure(p,all_checks)['cost']*Fraction(r['budget_fraction'])):
            raise ValueError('budget does not match full-plan fraction')
        score=measure(p,r['selected'])
        for field in ('cost','risk_reduction','residual_risk'):
            if score[field]!=Fraction(r[field]):
                raise ValueError(f'wrong result: {field}')
        if score['risk_reduction']+score['residual_risk']!=Fraction(r['total_risk']):
            raise ValueError('incorrect total risk')
        if score['coverage']!=r['coverage'] or not r['feasible'] or score['cost']>budget:
            raise ValueError('coverage or feasibility failure')
        if len(r['runtime_samples_ms'])!=data['metadata']['repeats'] or not all(math.isfinite(t) and t>=0 for t in r['runtime_samples_ms']):
            raise ValueError('invalid timing samples')
        if r['runtime_ms']!=statistics.median(r['runtime_samples_ms']):
            raise ValueError('runtime median mismatch')
        cached=(r['workload_sha256'],budget)
        if check_optima and cached not in optima:
            optima[cached]=exhaustive(p,budget)
        optimum=optima[cached]['risk_reduction'] if check_optima else Fraction(r['reference_optimum'])
        actual=score['risk_reduction']
        if optimum!=Fraction(r['reference_optimum']) or Fraction(r['risk_gap'])!=optimum-actual or actual>optimum:
            raise ValueError('incorrect optimality gap')
        expected_ratio=str(actual/optimum) if optimum else None
        if r['optimality_ratio']!=expected_ratio:
            raise ValueError('incorrect optimality ratio')
        if check_optima and r['policy']=='exact' and tuple(r['selected'])!=optima[cached]['checks']:
            raise ValueError('wrong exact tie-break')
    expected_keys=set(product(*(data['metadata'][k] for k in ('sizes','seeds','densities','budget_fractions','policies'))))
    if seen!=expected_keys:
        raise ValueError('configuration matrix mismatch')
    if data['summary']!=summary(data['rows']):
        raise ValueError('summary mismatch')
    for fixture in data['fixtures'].values():
        problem=Problem.from_dict(fixture['problem'])
        for row in fixture['results']:
            checked=measure(problem,row['selected'])
            if checked['cost']>fixture['budget'] or checked['risk_reduction']!=Fraction(row['risk_reduction']):
                raise ValueError('fixture result mismatch')
    return dict(status='verified',rows=len(data['rows']),instances=len(inputs),
                independently_checked_optima=len(optima),
                preservation=preservation(Path(__file__).resolve().parents[3]))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    print(json.dumps(verify(parser.parse_args().directory),sort_keys=True))
