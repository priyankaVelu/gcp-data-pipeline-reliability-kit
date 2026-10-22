"""Recheck retained artifacts with the independent subset oracle."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from fractions import Fraction as F
from pathlib import Path
from ..overlap_v1 import model, oracle, fixtures
from . import experiment as e
from .scenarios import no_sharing


def verify(directory):
    directory=Path(directory)
    for name,digest in json.loads((directory/'SHA256.json').read_text()).items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest,name
    data=json.loads((directory/'results.json').read_text()); meta=data['metadata']; rows=data['rows']
    expected={}
    for phase,seeds,sizes in meta['phases']:
        for size in sizes:
            for seed in seeds:
                for density in meta['densities']:
                    source=fixtures.generated(seed,size,F(density))
                    for mode in e.MODES:
                        p=source if mode=='shared' else no_sharing(source)
                        for fraction in meta['budget_fractions']:
                            key=(phase,seed,size,density,mode,fraction)
                            expected[key]=(p,int(model.account(source,[c.id for c in source.checks])['cost']*F(fraction)))
    inputs=json.loads((directory/'inputs.json').read_text())
    assert len(inputs)*len(meta['budget_fractions'])*6==len(rows)==len(expected)*6
    for item in inputs:
        key=(item['phase'],item['seed'],item['checks'],item['density'],item['cost_model'],meta['budget_fractions'][0])
        assert item['problem']==expected[key][0].to_dict()
        assert item['workload_sha256']==e.old.sha(item['problem'])
    seen=set()
    for key,(p,budget) in expected.items():
        optimum=oracle.exhaustive(p,budget)
        group=[r for r in rows if (r['phase'],r['seed'],r['checks'],r['density'],r['cost_model'],r['budget_fraction'])==key]
        assert sorted(r['policy'] for r in group)==sorted(e.POLICIES)
        for r in group:
            identity=key+(r['policy'],); assert identity not in seen; seen.add(identity)
            actual=oracle.measure(p,r['selected'])
            assert F(r['budget'])==budget and actual['cost']<=budget
            for field in ('cost','risk_reduction','residual_risk','coverage'):
                assert actual[field]==(r[field] if field=='coverage' else F(r[field]))
            assert F(r['risk_gap'])==optimum['risk_reduction']-actual['risk_reduction']>=0
            assert F(r['reference_optimum'])==optimum['risk_reduction']
            ratio=str(actual['risk_reduction']/optimum['risk_reduction']) if optimum['risk_reduction'] else None
            assert r['optimality_ratio']==ratio
            result=e.solve(p,budget,r['policy']); e.check(p,budget,result)
            assert list(result['checks'])==r['selected'] and result['examined']==r['examined']
            if 'steps' in result: assert json.loads(json.dumps(result['steps'],default=str))==r['steps']
            assert len(r['runtime_samples_ms'])==3 and all(math.isfinite(t) and t>=0 for t in r['runtime_samples_ms'])
            assert r['runtime_ms']==statistics.median(r['runtime_samples_ms'])
    assert data['summary']==e.summarize(rows)
    with (directory/'results.csv').open(newline='') as handle:
        csvrows=list(csv.DictReader(handle))
    assert len(csvrows)==len(rows)
    for a,b in zip(csvrows,rows):
        for k,v in b.items():
            encoded=e.old.canonical_json(v) if isinstance(v,(list,dict)) else '' if v is None else str(v)
            assert a[k]==encoded,(k,a[k],encoded)
    for fixture in data['fixtures'].values():
        for mode in fixture.values():
            p=model.Problem.from_dict(mode['problem'])
            for r in mode['results']:
                result=e.solve(p,mode['budget'],r['policy']);e.check(p,mode['budget'],result)
                assert list(result['checks'])==r['selected']
    e.preservation(Path(__file__).resolve().parents[3])
    print(json.dumps(dict(verified_rows=len(rows),independent_optima=len(expected),status='verified')))
    return data

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
