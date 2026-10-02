"""Experiment Suite v3 — compound faults and recovery realism."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,random,statistics,subprocess,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reliability_kit import deduplicate_events,validate_business_key
UTC=timezone.utc
SIZES=(1000,10000,100000); SEEDS=(1301,2609,3911,5209,6521); RATES=(.001,.01,.05,.10); CHECKPOINTS=(.25,.50,.75); REPEATS=7

def sha():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except Exception:return "unknown"
def base(n,seed):
    rng=random.Random(seed);t=datetime(2026,3,1,tzinfo=UTC)
    return [{"event_id":f"e{i}","entity_id":f"c{rng.randrange(max(10,n//20))}","business_key":f"k{i}","event_ts":t+timedelta(seconds=i),"value":i} for i in range(n)]
def bench(fn):
    vals=[];v=None
    for _ in range(REPEATS):
        s=time.perf_counter_ns();v=fn();vals.append((time.perf_counter_ns()-s)/1e6)
    return v,statistics.median(vals)
def rec(sc,strategy,n,seed,rate,checkpoint,inj,det,correct,runtime,commit):
    return {"scenario":sc,"strategy":strategy,"dataset_size":n,"seed":seed,"fault_rate":rate,"checkpoint":checkpoint,
            "faults_injected":inj,"faults_detected":det,"correct":int(correct),"runtime_ms_median":round(runtime,6),
            "timing_repeats":REPEATS,"commit_sha":commit,"python":platform.python_version()}
def run(n,seed,rate,commit):
    rows=base(n,seed);out=[];rng=random.Random(seed+71);k=max(1,round(n*rate))
    # mixed duplicate + null
    dup_idx=rng.sample(range(n),min(k,n)); mixed=[dict(x) for x in rows]+[dict(rows[i]) for i in dup_idx]
    null_idx=rng.sample(range(len(mixed)),min(k,len(mixed)))
    for i in null_idx:mixed[i]["business_key"]=None
    rng.shuffle(mixed)
    def mixed_control():
        clean,d=deduplicate_events(mixed);bad=validate_business_key(clean,"business_key");return clean,d,bad
    (clean,d,bad),tm=bench(mixed_control)
    # Some null-marked duplicate copies can be removed by dedup; expected is computed from retained first occurrences.
    expected_bad=sum(x.get("business_key") is None for x in clean)
    out.append(rec("mixed_faults","dedup_then_validate",n,seed,rate,None,k+k,d+len(bad),len(clean)==n and d==k and len(bad)==expected_bad,tm,commit))
    # out-of-order: reverse selected adjacent positions, event-time sort is oracle
    late=[dict(x) for x in rows]; idx=sorted(rng.sample(range(1,n),min(k,n-1)))
    moved=[late[i] for i in idx]; keep=[x for j,x in enumerate(late) if j not in set(idx)]; arrival=keep+moved
    arrival_ok=all(arrival[i]["event_ts"]<=arrival[i+1]["event_ts"] for i in range(len(arrival)-1))
    _,tm=bench(lambda:list(arrival))
    out.append(rec("late_arrival","arrival_order",n,seed,rate,None,k,0,arrival_ok,tm,commit))
    ordered,tm=bench(lambda:sorted(arrival,key=lambda x:x["event_ts"]))
    out.append(rec("late_arrival","event_time_order",n,seed,rate,None,k,k,ordered==rows,tm,commit))
    # conflicting entity updates
    shuffled=[dict(x) for x in rows];rng.shuffle(shuffled)
    def latest(arr,key):
        state={}
        for x in arr:
            eid=x["entity_id"]
            if eid not in state or key(x)>=key(state[eid]):state[eid]=x
        return state
    oracle=latest(rows,lambda x:x["event_ts"])
    arrival_state,tm=bench(lambda:latest(shuffled,lambda x:0))
    out.append(rec("conflicting_updates","arrival_last_write",n,seed,rate,None,n,0,arrival_state==oracle,tm,commit))
    event_state,tm=bench(lambda:latest(shuffled,lambda x:x["event_ts"]))
    out.append(rec("conflicting_updates","event_time_latest_write",n,seed,rate,None,n,n,event_state==oracle,tm,commit))
    # checkpoints
    for cp in CHECKPOINTS:
        cut=max(1,int(n*cp));partial=rows[:cut]; replay=partial+rows
        appended,tm=bench(lambda:list(replay))
        out.append(rec("checkpoint_recovery","append_replay",n,seed,rate,cp,cut,cut,len(appended)==n,tm,commit))
        (clean,d),tm=bench(lambda:deduplicate_events(replay))
        out.append(rec("checkpoint_recovery","idempotent_replay",n,seed,rate,cp,cut,d,len(clean)==n and d==cut,tm,commit))
    return out
def summarize(rows):
    g={}
    for r in rows:g.setdefault((r["scenario"],r["strategy"],r["dataset_size"],r["fault_rate"],r["checkpoint"]),[]).append(r)
    out=[]
    for key,v in sorted(g.items(),key=lambda z:str(z[0])):
        out.append({"scenario":key[0],"strategy":key[1],"dataset_size":key[2],"fault_rate":key[3],"checkpoint":key[4],
                    "runs":len(v),"correct_run_rate":round(sum(x["correct"] for x in v)/len(v),6),
                    "runtime_ms_median_across_runs":round(statistics.median(x["runtime_ms_median"] for x in v),6)})
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument("--sizes",nargs="+",type=int,default=SIZES);p.add_argument("--seeds",nargs="+",type=int,default=SEEDS);p.add_argument("--rates",nargs="+",type=float,default=RATES);a=p.parse_args()
    commit=sha();rows=[]
    for n in a.sizes:
        for seed in a.seeds:
            for rate in a.rates:rows.extend(run(n,seed,rate,commit))
    root=Path(__file__).parent/"results";raw=root/"raw";raw.mkdir(parents=True,exist_ok=True);stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    rp=raw/f"paper-suite-v3-{stamp}.csv"
    with rp.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    doc={"schema_version":"3.0","generated_at":datetime.now(UTC).isoformat(),"commit_sha":commit,"python":platform.python_version(),
         "configuration":{"sizes":a.sizes,"seeds":a.seeds,"fault_rates":a.rates,"checkpoints":CHECKPOINTS,"timing_repeats":REPEATS},
         "observation_count":len(rows),"results":summarize(rows),"raw_sha256":hashlib.sha256(rp.read_bytes()).hexdigest()}
    sp=root/f"paper-suite-v3-{stamp}-summary.json";sp.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"raw":str(rp),"summary":str(sp),"observations":len(rows),"commit_sha":commit},indent=2))
if __name__=="__main__":main()
