"""Registered V2 experiment runner. Every run uses a fresh output directory."""
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pipeline_reliability import cdc_interactive as model

SEEDS=(7,17,29)
SIZES=(8,64)
REPEATS=5
SCENARIOS=model.SCENARIOS[:-1]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def observe(size, seed, name, strategy):
    base, events=model.scenario(name,size,seed)
    expected=model.oracle(base)  # before injected input is processed
    cp=len(events)//3 if name in ('checkpoint_recovery','post_recovery_redelivery') else 0
    cut=2*len(events)//3 if cp else 0
    samples=[]
    for _ in range(REPEATS):
        start=time.perf_counter_ns()
        result=model.replay(events,strategy,checkpoint=cp,interruption=cut,
                            redeliver=name=='post_recovery_redelivery',trace=True)
        samples.append((time.perf_counter_ns()-start)/1e6)
    wrong=model.wrong_keys(result['state'],expected)
    row={k:v for k,v in result.items() if k not in ('state','trace')}
    row.update(keys=size,seed=seed,scenario=name,strategy=strategy,
               state_correct=not wrong if result['completed'] else None,
               wrong_keys=wrong,runtime_ms=statistics.median(samples),runtime_samples_ms=samples,
               workload_sha256=digest(events),canonical_sha256=digest(base),oracle_sha256=digest(expected))
    return row


def expiry(strategy,capacity,seed,probe_order):
    base=model.canonical(16,(1,2,3,4))
    first=copy.deepcopy(base[0])
    samples=[]
    for _ in range(REPEATS):
        start=time.perf_counter_ns()
        p=model.Materializer(strategy,capacity)
        for event in base:
            p.apply(event)
        before=copy.deepcopy(p.state)
        recognized=None
        detected=False
        if probe_order=='exact_then_conflict':
            recognized=p.apply(first)=='duplicate'
        after_exact=copy.deepcopy(p.state)
        try:
            p.apply(dict(first,value='conflicting'))
        except model.InvalidEvent:
            detected=True
        samples.append((time.perf_counter_ns()-start)/1e6)
    return dict(strategy=strategy,capacity=capacity,seed=seed,probe_order=probe_order,
                duplicate_recognized=recognized,conflict_detected=detected,
                exact_replay_state_unchanged=after_exact==before if recognized is not None else None,
                final_state_unchanged=p.state==before,ledger_peak=p.peak,
                workload_sha256=digest(dict(base=base,probe_order=probe_order)),
                runtime_ms=statistics.median(samples),runtime_samples_ms=samples)


def write_csv(path,rows):
    fields=sorted(set().union(*(r.keys() for r in rows)))
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def run(directory):
    output=Path(directory)
    output.mkdir(parents=True,exist_ok=False)
    try:
        rows=[]
        for size in SIZES:
            for seed in SEEDS:
                for name in SCENARIOS:
                    order=len(rows)//3%3
                    for strategy in model.STRATEGIES[order:]+model.STRATEGIES[:order]:
                        rows.append(observe(size,seed,name,strategy))
        bounded=[expiry(s,c,seed,order) for seed in SEEDS for c in (0,4,16,None)
                 for order in ('conflict_first','exact_then_conflict') for s in model.STRATEGIES]
        if len(rows)!=144 or len(bounded)!=72:
            raise ValueError('unexpected matrix count')
        configs=[(r['keys'],r['seed'],r['scenario'],r['strategy']) for r in rows]
        if len(set(configs))!=144:
            raise ValueError('duplicate principal configuration')
        for row in rows+bounded:
            if len(row['runtime_samples_ms'])!=5 or not all(math.isfinite(v) and v>=0 for v in row['runtime_samples_ms']):
                raise ValueError('invalid timing samples')
        source=Path(__file__).resolve()
        metadata=dict(schema_version='2.0',generated_at=datetime.now(timezone.utc).isoformat(),
                      commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                      tracked_dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True)),
                      python=platform.python_version(),platform=platform.platform(),seeds=SEEDS,sizes=SIZES,repeats=REPEATS,
                      scenarios=SCENARIOS,capacity_policy='FIFO; duplicate hits do not refresh',
                      hashes={str(p.relative_to(source.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (source,source.with_name('PROTOCOL.md'),Path(model.__file__))})
        data=dict(metadata=metadata,principal=rows,bounded=bounded)
        (output/'results.json').write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
        write_csv(output/'principal.csv',rows)
        write_csv(output/'bounded.csv',bounded)
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
        (output/'SHA256.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
        print(json.dumps(dict(output=str(output),principal=len(rows),bounded=len(bounded))))
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps(dict(error=repr(exc)))+'\n')
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
