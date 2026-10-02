"""Experiment Suite v2: predeclared robustness and recovery experiments.

Synthetic/local only. Produces observations; it does not encode publication conclusions.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,random,statistics,subprocess,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reliability_kit import deduplicate_events,validate_business_key,bounded_backfill
UTC=timezone.utc
SIZES=(1000,10000,100000)
SEEDS=(1103,2207,3301,4409,5501)
RATES=(0.001,0.01,0.05,0.10)
REPEATS=7

def sha():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except Exception:return "unknown"

def data(n,seed):
    rng=random.Random(seed); t=datetime(2026,2,1,tzinfo=UTC)
    return [{"event_id":f"e{i}","customer_id":f"c{rng.randrange(max(1,n//3))}","event_ts":t+timedelta(seconds=i)} for i in range(n)]

def duplicate(rows,rate,seed):
    rng=random.Random(seed); k=max(1,round(len(rows)*rate)); idx=rng.sample(range(len(rows)),min(k,len(rows)))
    out=[dict(x) for x in rows]+[dict(rows[i]) for i in idx]; rng.shuffle(out); return out,len(idx)

def nulls(rows,rate,seed):
    rng=random.Random(seed); out=[dict(x) for x in rows]; k=max(1,round(len(rows)*rate)); idx=rng.sample(range(len(rows)),min(k,len(rows)))
    for i in idx:out[i]["customer_id"]=None
    return out,len(idx)

def ms(fn):
    t=time.perf_counter_ns(); v=fn(); return v,(time.perf_counter_ns()-t)/1e6

def benchmark(fn,repeats):
    vals=[]; value=None
    for _ in range(repeats):value,t=ms(fn); vals.append(t)
    return value,statistics.median(vals),statistics.fmean(vals)

def record(scenario,strategy,n,seed,rate,inj,det,ok,med,mean,commit):
    return {"scenario":scenario,"strategy":strategy,"dataset_size":n,"seed":seed,"fault_rate":rate,
            "faults_injected":inj,"faults_detected":det,"correct":int(ok),
            "runtime_ms_median":round(med,6),"runtime_ms_mean":round(mean,6),
            "timing_repeats":REPEATS,"commit_sha":commit,"python":platform.python_version()}

def run(n,seed,rate,commit):
    base=data(n,seed); out=[]
    faulty,k=duplicate(base,rate,seed+17)
    # comparator: sort/group unique IDs; treatment: streaming set-based first occurrence
    def group_dedup():
        ordered=sorted(faulty,key=lambda x:x["event_id"]); clean=[]; last=None; d=0
        for x in ordered:
            if x["event_id"]==last:d+=1
            else:clean.append(x);last=x["event_id"]
        return clean,d
    (g,gd),med,mean=benchmark(group_dedup,REPEATS)
    out.append(record("duplicate_replay","sort_group_comparator",n,seed,rate,k,gd,len(g)==n and gd==k,med,mean,commit))
    (c,cd),med,mean=benchmark(lambda:deduplicate_events(faulty),REPEATS)
    out.append(record("duplicate_replay","set_control",n,seed,rate,k,cd,len(c)==n and cd==k,med,mean,commit))

    faulty,k=nulls(base,rate,seed+29)
    def loop_validate():
        bad=[]
        for i,x in enumerate(faulty):
            if x.get("customer_id") is None or x.get("customer_id")=="":bad.append(i)
        return bad
    bad,med,mean=benchmark(loop_validate,REPEATS)
    out.append(record("null_business_key","explicit_loop_comparator",n,seed,rate,k,len(bad),len(bad)==k,med,mean,commit))
    bad,med,mean=benchmark(lambda:validate_business_key(faulty,"customer_id"),REPEATS)
    out.append(record("null_business_key","kit_control",n,seed,rate,k,len(bad),len(bad)==k,med,mean,commit))

    # partial-processing recovery: first 60%, then replay entire batch.
    cut=max(1,int(n*.6)); partial=base[:cut]
    naive=partial+base
    expected_duplicates=cut
    _,med,mean=benchmark(lambda:partial+base,REPEATS)
    out.append(record("partial_recovery","append_replay_comparator",n,seed,rate,expected_duplicates,expected_duplicates,
                      len(naive)==n,med,mean,commit))
    (recovered,det),med,mean=benchmark(lambda:deduplicate_events(partial+base),REPEATS)
    out.append(record("partial_recovery","idempotent_replay_control",n,seed,rate,expected_duplicates,det,
                      len(recovered)==n and det==expected_duplicates,med,mean,commit))

    # bounded recovery window compared with a manual timestamp predicate.
    start=base[n//4]["event_ts"]; end=base[(3*n)//4]["event_ts"]; expected=sum(start<=x["event_ts"]<end for x in base)
    manual,med,mean=benchmark(lambda:[dict(x) for x in base if start<=x["event_ts"]<end],REPEATS)
    out.append(record("bounded_recovery","predicate_comparator",n,seed,rate,n-expected,n-len(manual),len(manual)==expected,med,mean,commit))
    bounded,med,mean=benchmark(lambda:bounded_backfill(base,start,end),REPEATS)
    out.append(record("bounded_recovery","kit_control",n,seed,rate,n-expected,n-len(bounded),len(bounded)==expected,med,mean,commit))
    return out

def summary(rows):
    groups={}
    for r in rows:groups.setdefault((r["scenario"],r["strategy"],r["dataset_size"],r["fault_rate"]),[]).append(r)
    ans=[]
    for key,g in sorted(groups.items()):
        inj=sum(x["faults_injected"] for x in g);det=sum(x["faults_detected"] for x in g)
        ans.append({"scenario":key[0],"strategy":key[1],"dataset_size":key[2],"fault_rate":key[3],"runs":len(g),
                    "detection_rate":round(det/inj,6) if inj else None,
                    "correct_run_rate":round(sum(x["correct"] for x in g)/len(g),6),
                    "runtime_ms_median_across_runs":round(statistics.median(x["runtime_ms_median"] for x in g),6)})
    return ans

def main():
    p=argparse.ArgumentParser();p.add_argument("--sizes",nargs="+",type=int,default=SIZES);p.add_argument("--seeds",nargs="+",type=int,default=SEEDS)
    p.add_argument("--rates",nargs="+",type=float,default=RATES);a=p.parse_args()
    if any(n<10 for n in a.sizes):raise SystemExit("sizes must be >=10")
    if any(not 0<r<1 for r in a.rates):raise SystemExit("rates must be between 0 and 1")
    commit=sha();rows=[]
    for n in a.sizes:
        for seed in a.seeds:
            for rate in a.rates:rows.extend(run(n,seed,rate,commit))
    root=Path(__file__).parent/"results";raw=root/"raw";raw.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ");rp=raw/f"paper-suite-v2-{stamp}.csv"
    with rp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    doc={"schema_version":"2.0","generated_at":datetime.now(UTC).isoformat(),"commit_sha":commit,
         "python":platform.python_version(),"configuration":{"sizes":a.sizes,"seeds":a.seeds,"fault_rates":a.rates,"timing_repeats":REPEATS},
         "observation_count":len(rows),"results":summary(rows),"raw_sha256":hashlib.sha256(rp.read_bytes()).hexdigest()}
    sp=root/f"paper-suite-v2-{stamp}-summary.json";sp.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"raw":str(rp),"summary":str(sp),"observations":len(rows),"commit_sha":commit},indent=2))
if __name__=="__main__":main()
