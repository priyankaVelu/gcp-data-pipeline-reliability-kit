"""Reconcile manuscript numbers, all retained rows and preserved source hashes.

Uses a separately expressed batch specification for canonical final state. This is
an audit of synthetic semantics, not independent implementation replication.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline_reliability import cdc_interactive as m

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

v=load('artifact_verify','research/cdc_lab/v2/verify.py')
r=load('isolated_runner','research/cdc_lab/v2/run.py')

def require(condition,message):
    if not condition:raise ValueError(message)

def independent_target(events):
    bykey={}
    for key in sorted({e['key'] for e in events}):
        group=[e for e in events if e['key']==key]
        latest=sorted(group,key=lambda e:e['version'])[-1]
        bykey[key]={f:latest[f] for f in ('version','value','deleted')}
    return bykey

def audit():
    here=Path(__file__).parent
    protected=json.loads((here/'PRESERVATION.json').read_text())
    for name,digest in protected['files'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'protected file changed: '+name)
    old=ROOT/'research/cdc_lab/results/run-1'
    repeated=ROOT/'research/cdc_lab/v2/results/baseline-reproduction-1'
    comparison=v.compare(old,repeated)
    data=v.verify(ROOT/'research/cdc_lab/v2/results/isolated-1')
    for name,digest in data['metadata']['hashes'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'measured source mismatch: '+name)
    require((len(data['principal']),len(data['bounded']))==(144,72),'matrix size')
    keys={(row['keys'],row['seed'],row['scenario'],row['strategy']) for row in data['principal']}
    expected={(n,s,c,p) for n in (8,64) for s in (7,17,29) for c in m.SCENARIOS[:-1] for p in m.STRATEGIES}
    require(keys==expected,'missing/duplicate principal configuration')
    require(len({(x['strategy'],x['capacity'],x['seed'],x['probe_order']) for x in data['bounded']})==72,'duplicate expiry configuration')
    for row in data['principal']:
        base,events=m.scenario(row['scenario'],row['keys'],row['seed'])
        target=independent_target(base)
        require(target==m.oracle(base),'independent specification disagreement')
        cp=len(events)//3 if row['scenario'] in ('checkpoint_recovery','post_recovery_redelivery') else 0
        cut=2*len(events)//3 if cp else 0
        result=m.replay(events,row['strategy'],checkpoint=cp,interruption=cut,redeliver=row['scenario']=='post_recovery_redelivery',trace=True)
        for name,value in result.items():
            if name not in ('state','trace'):require(row[name]==value,'retained technical field differs: '+name)
        require(row['state_correct']==(result['state']==target if result['completed'] else None),'correctness verdict')
        require(row['wrong_keys']==m.wrong_keys(result['state'],target),'wrong-key evidence')
        for name,value in (('workload_sha256',events),('canonical_sha256',base),('oracle_sha256',target)):
            require(row[name]==r.digest(value),'input/oracle digest mismatch')
        require(row['runtime_ms']==statistics.median(row['runtime_samples_ms']) and len(row['runtime_samples_ms'])==5,'timing summary')
    for row in data['bounded']:
        new=r.expiry(row['strategy'],row['capacity'],row['seed'],row['probe_order'])
        require({k:value for k,value in new.items() if k not in v.TIMING}=={k:value for k,value in row.items() if k not in v.TIMING},'expiry outcome differs')
    counts={}
    for policy,outcome in zip(m.STRATEGIES,((24,12,12),(30,6,12),(36,0,12))):
        rows=[x for x in data['principal'] if x['strategy']==policy]
        count=(sum(x['state_correct'] is True for x in rows),sum(x['state_correct'] is False for x in rows),sum(x['input_rejected'] for x in rows))
        require(count==outcome,'manuscript table mismatch');counts[policy]=dict(zip(('correct','incorrect','rejected'),count))
        for scenario in ('ordered','duplicate_only','ordered_delete_reinsert','checkpoint_recovery'):
            require(sum(x['state_correct'] is True for x in rows if x['scenario']==scenario)==6,'isolated control claim')
    for capacity in (0,4,16,None):
        for row in [x for x in data['bounded'] if x['strategy']=='version' and x['capacity']==capacity]:
            detected=capacity is None if row['probe_order']=='conflict_first' else capacity!=0
            require(row['conflict_detected']==detected and row['final_state_unchanged'],'probe-order claim')
    for policy,correct in (('arrival',False),('id_only',False),('version',True)):
        x=m.evaluate(name='stale_update',strategy=policy,keys=1)
        require(x['state_correct']==correct,'visible counterexample')
    recovery=m.evaluate(name='post_recovery_redelivery',strategy='version',keys=3,checkpoint=4,interruption=8)
    require(recovery['lost_attempts']==recovery['replayed_lost_attempts']==4 and recovery['redelivery_state_unchanged'],'walkthrough recovery counts')
    return dict(status='passed',protected_files=len(protected['files']),baseline_comparison=comparison['counts'],principal_rows=144,expiry_rows=72,counts=counts,
        independently_specified_canonical_targets=144,replayed_principal_rows=144,reexecuted_expiry_rows=72,
        limitations=['Specification assumes authoritative integer versions','Reexecution of existing implementation, not independent implementation replication','Retained runtimes are historical observations; no performance comparison'],
        evidence_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (old/'results.json',repeated/'results.json',ROOT/'research/cdc_lab/v2/results/isolated-1/results.json')})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args();result=audit()
    if a.output:
        with a.output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(result,sort_keys=True))
