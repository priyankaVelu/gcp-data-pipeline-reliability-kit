"""Experiment Suite v4 — compound-failure control-composition study.

Implements the frozen research/EXPERIMENT_PROTOCOL_V4.md specification.
Local deterministic synthetic Python only; timings are not cloud performance.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,random,statistics,subprocess,time
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from pathlib import Path

UTC=timezone.utc
SIZES=(1000,10000,100000)
SEEDS=(1301,2609,3911,5209,6521)
INTENSITIES=(.01,.05,.10)
REPEATS=7
CHECKPOINT_FRACTION=.50
REPLAY_FRACTION=.50
STRATEGIES=("S1_minimal","S2_temporal","S3_recovery","S4_full")
CONTROL_FAULTS=("duplicate","null_key","late","conflict","recovery")
PROTOCOL_VERSION="4.0"

@dataclass(frozen=True)
class Strategy:
    temporal: bool
    idempotent_recovery: bool

SPECS={
    "S1_minimal":Strategy(False,False),
    "S2_temporal":Strategy(True,False),
    "S3_recovery":Strategy(False,True),
    "S4_full":Strategy(True,True),
}

def git_sha():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except Exception:return "unknown"

def canonical(n,seed):
    rng=random.Random(seed)
    entities=max(10,n//20)
    t=datetime(2026,4,1,tzinfo=UTC)
    rows=[]
    for i in range(n):
        entity=f"c{rng.randrange(entities)}"
        rows.append({"event_id":f"e{i}","entity_id":entity,"business_key":f"k{i}",
                     "event_ts":t+timedelta(seconds=i),"value":i,"fault_tags":()})
    return rows

def latest_state(rows,temporal=True):
    state={}
    for x in rows:
        eid=x["entity_id"]
        if temporal:
            if eid not in state or (x["event_ts"],x["event_id"])>(state[eid]["event_ts"],state[eid]["event_id"]):
                state[eid]=x
        else:
            state[eid]=x
    return state

def oracle_for(rows):
    return {
        "event_ids":frozenset(x["event_id"] for x in rows),
        "state":latest_state(rows,True),
        "entities":frozenset(x["entity_id"] for x in rows),
    }

def choose(rng,pop,k):
    return rng.sample(list(pop),min(k,len(pop))) if k else []

def count_for(n,rate):
    return min(n,max(1,round(n*rate))) if rate>0 else 0

def inject(rows,seed,duplicate_rate=0,null_key_rate=0,late_rate=0,conflict_rate=0,
           checkpoint_fraction=CHECKPOINT_FRACTION,replay_fraction=REPLAY_FRACTION,recovery=True):
    """Inject faults deterministically. Returns immutable-ish row copies plus realized counts."""
    rng=random.Random(seed+404)
    work=[dict(x) for x in rows]
    for x in work:x["fault_tags"]=tuple(x.get("fault_tags",()))

    # Conflicts are valid additional updates. Their canonical event time is deliberately older
    # than the source entity's latest canonical event, while arrival is late in the list.
    kc=count_for(len(rows),conflict_rate)
    conflict_entities=choose(rng,sorted({x["entity_id"] for x in rows}),kc)
    by_entity={}
    for x in rows:by_entity.setdefault(x["entity_id"],[]).append(x)
    conflicts=[]
    for j,eid in enumerate(conflict_entities):
        src=max(by_entity[eid],key=lambda x:x["event_ts"])
        c=dict(src);c["event_id"]=f"conflict-{seed}-{j}-{src['event_id']}"
        c["event_ts"]=src["event_ts"]-timedelta(microseconds=1)
        c["value"]=-(j+1);c["business_key"]=f"conflict-k-{seed}-{j}"
        c["fault_tags"]=("conflict",)
        conflicts.append(c)
    work.extend(conflicts)

    # Late arrivals: selected ordinary events are moved to the end without changing event time.
    kl=count_for(len(rows),late_rate)
    late_ids=set(x["event_id"] for x in choose(rng,rows,kl))
    if late_ids:
        kept=[];late=[]
        for x in work:
            if x["event_id"] in late_ids:
                y=dict(x);y["fault_tags"]=tuple(sorted(set(y["fault_tags"])|{"late"}));late.append(y)
            else:kept.append(x)
        work=kept+late

    # Null keys mutate observable copies only; the pre-fault oracle remains unchanged.
    kn=count_for(len(rows),null_key_rate)
    ordinary=[x for x in work if x["event_id"] in {r["event_id"] for r in rows}]
    null_ids=set(x["event_id"] for x in choose(rng,ordinary,kn))
    for x in work:
        if x["event_id"] in null_ids:
            x["business_key"]=None;x["fault_tags"]=tuple(sorted(set(x["fault_tags"])|{"null_key"}))

    # Duplicate replay copies existing observable records.
    kd=count_for(len(rows),duplicate_rate)
    dup_sources=choose(rng,work,kd)
    duplicates=[]
    for x in dup_sources:
        y=dict(x);y["fault_tags"]=tuple(sorted(set(y["fault_tags"])|{"duplicate"}));duplicates.append(y)
    work.extend(duplicates)

    replayed=0
    if recovery:
        cut=max(1,int(len(work)*checkpoint_fraction))
        replay_n=max(1,int(cut*replay_fraction))
        replay=[dict(x) for x in work[:replay_n]]
        for x in replay:x["fault_tags"]=tuple(sorted(set(x["fault_tags"])|{"recovery_replay"}))
        work=work+replay
        replayed=len(replay)

    realized={"duplicate":len(duplicates),"null_key":len(null_ids),"late":len(late_ids),
              "conflict":len(conflicts),"recovery_replay":replayed}
    return tuple(work),realized

def dedup(rows):
    seen=set();out=[];det=0
    for x in rows:
        if x["event_id"] in seen:det+=1;continue
        seen.add(x["event_id"]);out.append(x)
    return out,det

def process(work,strategy):
    spec=SPECS[strategy]
    # All strategies deduplicate ordinary injected duplicates. Recovery idempotency determines
    # whether recovery-tagged copies are recognized as replay or treated as fresh append input.
    seen=set();clean=[];dup_detected=0;recovery_detected=0
    for x in work:
        recovery_copy="recovery_replay" in x["fault_tags"]
        key=x["event_id"]
        if key in seen and (not recovery_copy or spec.idempotent_recovery):
            dup_detected+=1
            if recovery_copy:recovery_detected+=1
            continue
        seen.add(key);clean.append(x)
    valid=[];invalid_detected=0
    for x in clean:
        if x["business_key"] is None:invalid_detected+=1;continue
        valid.append(x)
    state=latest_state(valid,spec.temporal)
    return valid,state,{"duplicate":dup_detected,"null_key":invalid_detected,
                        "recovery_replay":recovery_detected,
                        "late":0,
                        "conflict":0}

def metrics(valid,state,oracle,realized,detected):
    expected_ids=oracle["event_ids"]; oracle_state=oracle["state"]; entities=oracle["entities"]
    counts={}
    counts["oracle_entities"]=len(entities)
    counts["entities_matching_oracle"]=sum(
        eid in state and state[eid]["event_id"]==oracle_state[eid]["event_id"] and state[eid]["value"]==oracle_state[eid]["value"]
        for eid in entities)
    freq={}
    for x in valid:
        if x["event_id"] in expected_ids:freq[x["event_id"]]=freq.get(x["event_id"],0)+1
    counts["duplicate_leakage_count"]=sum(max(0,v-1) for v in freq.values())
    counts["duplicate_denominator"]=max(1,len(expected_ids))
    counts["invalid_key_leakage_count"]=sum(x["business_key"] is None for x in valid)
    counts["invalid_key_denominator"]=max(1,realized["null_key"])
    counts["stale_state_count"]=sum(
        eid in state and (state[eid]["event_id"]!=oracle_state[eid]["event_id"] or state[eid]["value"]!=oracle_state[eid]["value"])
        for eid in entities)
    counts["stale_state_denominator"]=max(1,len(entities))
    recovered_ids={x["event_id"] for x in valid if x["event_id"] in expected_ids}
    counts["recovered_expected_count"]=len(recovered_ids)
    counts["recovery_denominator"]=max(1,len(expected_ids))
    # Valid canonical events absent from processed logical membership.
    counts["false_rejection_count"]=len(expected_ids-recovered_ids)
    counts["false_rejection_denominator"]=max(1,len(expected_ids))
    detectable=sum(realized.values())
    detected_total=sum(min(realized[k],detected.get(k,0)) for k in realized)
    counts["faults_injected"]=detectable;counts["faults_detected"]=detected_total
    counts["fault_detection_denominator"]=max(1,detectable)
    rates={
        "state_correctness_rate":counts["entities_matching_oracle"]/counts["oracle_entities"],
        "duplicate_leakage_rate":counts["duplicate_leakage_count"]/counts["duplicate_denominator"],
        "invalid_key_leakage_rate":counts["invalid_key_leakage_count"]/counts["invalid_key_denominator"],
        "stale_state_rate":counts["stale_state_count"]/counts["stale_state_denominator"],
        "recovery_completeness_rate":counts["recovered_expected_count"]/counts["recovery_denominator"],
        "false_rejection_rate":counts["false_rejection_count"]/counts["false_rejection_denominator"],
        "fault_detection_recall":counts["faults_detected"]/counts["fault_detection_denominator"],
    }
    return counts,{k:round(v,9) for k,v in rates.items()}

def timed(work,strategy):
    vals=[]
    for _ in range(REPEATS):
        s=time.perf_counter_ns();process(work,strategy);vals.append((time.perf_counter_ns()-s)/1e6)
    return statistics.median(vals),statistics.mean(vals)

def observation(kind,fault_condition,n,seed,rates,strategy,work,realized,oracle,commit):
    valid,state,det=process(work,strategy)
    counts,rs=metrics(valid,state,oracle,realized,det)
    med,mean=timed(work,strategy)
    return {"schema_version":PROTOCOL_VERSION,"experiment_kind":kind,"fault_condition":fault_condition,
        "dataset_size":n,"seed":seed,"duplicate_rate":rates["duplicate_rate"],"null_key_rate":rates["null_key_rate"],
        "late_rate":rates["late_rate"],"conflict_rate":rates["conflict_rate"],
        "replay_fraction":rates["replay_fraction"],"checkpoint_fraction":rates["checkpoint_fraction"],
        "strategy":strategy,**{f"realized_{k}":v for k,v in realized.items()},**counts,**rs,
        "runtime_ms_median":round(med,6),"runtime_ms_mean":round(mean,6),"timing_repeats":REPEATS,
        "commit_sha":commit,"python":platform.python_version()}

def run_config(n,seed,intensity,commit):
    rows=canonical(n,seed);oracle=oracle_for(rows)
    rates={"duplicate_rate":intensity,"null_key_rate":intensity,"late_rate":intensity,"conflict_rate":intensity,
           "replay_fraction":REPLAY_FRACTION,"checkpoint_fraction":CHECKPOINT_FRACTION}
    work,realized=inject(rows,seed,**rates,recovery=True)
    return [observation("principal","compound",n,seed,rates,s,work,realized,oracle,commit) for s in STRATEGIES]

def run_controls(n,seed,commit):
    rows=canonical(n,seed);oracle=oracle_for(rows);out=[]
    for fault in CONTROL_FAULTS:
        rates={"duplicate_rate":0.0,"null_key_rate":0.0,"late_rate":0.0,"conflict_rate":0.0,
               "replay_fraction":REPLAY_FRACTION if fault=="recovery" else 0.0,
               "checkpoint_fraction":CHECKPOINT_FRACTION}
        if fault!="recovery":rates[fault+"_rate" if fault!="null_key" else "null_key_rate"]=.05
        work,realized=inject(rows,seed,duplicate_rate=rates["duplicate_rate"],null_key_rate=rates["null_key_rate"],
            late_rate=rates["late_rate"],conflict_rate=rates["conflict_rate"],
            checkpoint_fraction=rates["checkpoint_fraction"],replay_fraction=rates["replay_fraction"],
            recovery=fault=="recovery")
        for s in STRATEGIES:out.append(observation("single_fault_control",fault,n,seed,rates,s,work,realized,oracle,commit))
    return out

def deterministic_check():
    rows=canonical(1000,SEEDS[0]);oracle=oracle_for(rows)
    kw=dict(duplicate_rate=.05,null_key_rate=.05,late_rate=.05,conflict_rate=.05,
            checkpoint_fraction=CHECKPOINT_FRACTION,replay_fraction=REPLAY_FRACTION,recovery=True)
    a,ra=inject(rows,SEEDS[0],**kw);b,rb=inject(rows,SEEDS[0],**kw)
    if a!=b or ra!=rb:raise AssertionError("fault injection is not deterministic")
    for s in STRATEGIES:
        if process(a,s)!=process(b,s):raise AssertionError(f"non-timing output not deterministic for {s}")
    if len(oracle["state"])==0:raise AssertionError("oracle is empty")

def summarize(rows):
    out=[]
    groups={}
    for r in rows:
        k=(r["experiment_kind"],r["fault_condition"],r["strategy"],r["dataset_size"],
           r["duplicate_rate"],r["null_key_rate"],r["late_rate"],r["conflict_rate"])
        groups.setdefault(k,[]).append(r)
    for k,v in sorted(groups.items(),key=lambda z:str(z[0])):
        out.append({"experiment_kind":k[0],"fault_condition":k[1],"strategy":k[2],"dataset_size":k[3],
            "duplicate_rate":k[4],"null_key_rate":k[5],"late_rate":k[6],"conflict_rate":k[7],"runs":len(v),
            "state_correctness_rate_mean":round(statistics.mean(x["state_correctness_rate"] for x in v),9),
            "duplicate_leakage_rate_mean":round(statistics.mean(x["duplicate_leakage_rate"] for x in v),9),
            "stale_state_rate_mean":round(statistics.mean(x["stale_state_rate"] for x in v),9),
            "recovery_completeness_rate_mean":round(statistics.mean(x["recovery_completeness_rate"] for x in v),9),
            "false_rejection_rate_mean":round(statistics.mean(x["false_rejection_rate"] for x in v),9),
            "fault_detection_recall_mean":round(statistics.mean(x["fault_detection_recall"] for x in v),9),
            "runtime_ms_median_across_runs":round(statistics.median(x["runtime_ms_median"] for x in v),6)})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sizes",nargs="+",type=int,default=SIZES)
    p.add_argument("--seeds",nargs="+",type=int,default=SEEDS)
    p.add_argument("--intensities",nargs="+",type=float,default=INTENSITIES)
    p.add_argument("--skip-controls",action="store_true")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    deterministic_check()
    if a.self_test:
        print("v4 deterministic self-test: PASS");return
    commit=git_sha();rows=[];failures=[]
    for n in a.sizes:
        for seed in a.seeds:
            for intensity in a.intensities:
                try:rows.extend(run_config(n,seed,intensity,commit))
                except Exception as e:failures.append({"kind":"principal","dataset_size":n,"seed":seed,"intensity":intensity,"reason":repr(e)})
            if not a.skip_controls:
                try:rows.extend(run_controls(n,seed,commit))
                except Exception as e:failures.append({"kind":"single_fault_controls","dataset_size":n,"seed":seed,"reason":repr(e)})
    if not rows:raise RuntimeError("no valid observations generated")
    root=Path(__file__).parent/"results";raw=root/"raw";raw.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ");rp=raw/f"paper-suite-v4-{stamp}.csv"
    with rp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fp=root/f"paper-suite-v4-{stamp}-failures.json"
    fp.write_text(json.dumps(failures,indent=2)+"\n",encoding="utf-8")
    doc={"schema_version":PROTOCOL_VERSION,"protocol":"research/EXPERIMENT_PROTOCOL_V4.md",
        "generated_at":datetime.now(UTC).isoformat(),"commit_sha":commit,"python":platform.python_version(),
        "configuration":{"sizes":a.sizes,"seeds":a.seeds,"intensities":a.intensities,
            "strategies":STRATEGIES,"checkpoint_fraction":CHECKPOINT_FRACTION,"replay_fraction":REPLAY_FRACTION,
            "timing_repeats":REPEATS,"single_fault_controls":not a.skip_controls},
        "observation_count":len(rows),"principal_observation_count":sum(r["experiment_kind"]=="principal" for r in rows),
        "control_observation_count":sum(r["experiment_kind"]=="single_fault_control" for r in rows),
        "failure_count":len(failures),"results":summarize(rows),"raw_sha256":hashlib.sha256(rp.read_bytes()).hexdigest()}
    sp=root/f"paper-suite-v4-{stamp}-summary.json";sp.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"raw":str(rp),"summary":str(sp),"failures":str(fp),"observations":len(rows),
        "principal_observations":doc["principal_observation_count"],"control_observations":doc["control_observation_count"],
        "failure_count":len(failures),"commit_sha":commit},indent=2))

if __name__=="__main__":main()
