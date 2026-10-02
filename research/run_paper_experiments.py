"""Controlled baseline-vs-treatment reliability experiments.

No external services or proprietary data are used. Raw observations and a
machine-generated summary are written under research/results/.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, random, statistics, subprocess, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reliability_kit import deduplicate_events, validate_business_key, bounded_backfill, freshness_age_seconds

UTC = timezone.utc
DEFAULT_SIZES = (1000, 10000, 100000)
DEFAULT_SEEDS = (101, 202, 303, 404, 505)

def git_sha():
    try: return subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
    except Exception: return "unknown"

def make_events(n, seed):
    rng=random.Random(seed); start=datetime(2026,1,1,tzinfo=UTC); rows=[]
    for i in range(n):
        rows.append({"event_id":f"e{i}","customer_id":f"c{rng.randrange(max(1,n//4))}",
                     "event_ts":start+timedelta(seconds=i)})
    return rows

def inject_duplicate_faults(rows, rate, seed):
    rng=random.Random(seed); out=[dict(x) for x in rows]
    k=max(1,int(len(rows)*rate))
    for i in rng.sample(range(len(rows)), min(k,len(rows))): out.append(dict(rows[i]))
    rng.shuffle(out); return out, k

def inject_null_key_faults(rows, rate, seed):
    rng=random.Random(seed); out=[dict(x) for x in rows]; k=max(1,int(len(rows)*rate))
    for i in rng.sample(range(len(rows)), min(k,len(rows))): out[i]["customer_id"]=None
    return out, k

def timed(fn):
    t=time.perf_counter_ns(); value=fn(); return value,(time.perf_counter_ns()-t)/1_000_000

def row(scenario,variant,n,seed,injected,detected,correct,runtime_ms,commit):
    return {"scenario":scenario,"variant":variant,"dataset_size":n,"seed":seed,
            "faults_injected":injected,"faults_detected":detected,"correct":int(bool(correct)),
            "runtime_ms":round(runtime_ms,6),"commit_sha":commit,"python":platform.python_version()}

def run_config(n,seed,rate,commit):
    base=make_events(n,seed); observations=[]

    dup,expected=inject_duplicate_faults(base,rate,seed+1)
    (_,base_ms)=timed(lambda:list(dup))
    observations.append(row("duplicate_replay","baseline",n,seed,expected,0,False,base_ms,commit))
    ((clean,detected),ctl_ms)=timed(lambda:deduplicate_events(dup))
    observations.append(row("duplicate_replay","controlled",n,seed,expected,detected,
                            len(clean)==n and detected==expected,ctl_ms,commit))

    nulls,expected=inject_null_key_faults(base,rate,seed+2)
    (_,base_ms)=timed(lambda:list(nulls))
    observations.append(row("null_business_key","baseline",n,seed,expected,0,False,base_ms,commit))
    (bad,ctl_ms)=timed(lambda:validate_business_key(nulls,"customer_id"))
    observations.append(row("null_business_key","controlled",n,seed,expected,len(bad),
                            len(bad)==expected,ctl_ms,commit))

    start=base[0]["event_ts"]; end=start+timedelta(seconds=max(1,n//2))
    (unbounded,base_ms)=timed(lambda:list(base))
    expected_window=sum(start <= x["event_ts"] < end for x in base)
    observations.append(row("bounded_backfill","baseline",n,seed,n-expected_window,0,
                            len(unbounded)==expected_window,base_ms,commit))
    (bounded,ctl_ms)=timed(lambda:bounded_backfill(base,start,end))
    observations.append(row("bounded_backfill","controlled",n,seed,n-expected_window,
                            n-len(bounded),len(bounded)==expected_window,ctl_ms,commit))

    now=base[-1]["event_ts"]+timedelta(hours=2); threshold=3600
    (_,base_ms)=timed(lambda:base[-1]["event_ts"])
    observations.append(row("stale_data","baseline",n,seed,1,0,False,base_ms,commit))
    (age,ctl_ms)=timed(lambda:freshness_age_seconds(base[-1]["event_ts"],now))
    observations.append(row("stale_data","controlled",n,seed,1,int(age>threshold),age>threshold,ctl_ms,commit))
    return observations

def summarize(rows):
    groups={}
    for r in rows: groups.setdefault((r["scenario"],r["variant"],r["dataset_size"]),[]).append(r)
    out=[]
    for (scenario,variant,n),g in sorted(groups.items()):
        injected=sum(x["faults_injected"] for x in g); detected=sum(x["faults_detected"] for x in g)
        times=[x["runtime_ms"] for x in g]
        out.append({"scenario":scenario,"variant":variant,"dataset_size":n,"runs":len(g),
                    "detection_rate":round(detected/injected,6) if injected else None,
                    "correct_run_rate":round(sum(x["correct"] for x in g)/len(g),6),
                    "runtime_ms_median":round(statistics.median(times),6),
                    "runtime_ms_mean":round(statistics.fmean(times),6)})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sizes",nargs="+",type=int,default=DEFAULT_SIZES)
    p.add_argument("--seeds",nargs="+",type=int,default=DEFAULT_SEEDS)
    p.add_argument("--fault-rate",type=float,default=0.01)
    args=p.parse_args()
    if any(n<2 for n in args.sizes): raise SystemExit("all sizes must be >= 2")
    if not 0 < args.fault_rate < 1: raise SystemExit("fault-rate must be between 0 and 1")
    commit=git_sha(); rows=[]
    for n in args.sizes:
        for seed in args.seeds: rows.extend(run_config(n,seed,args.fault_rate,commit))
    root=Path(__file__).parent/"results"; raw=root/"raw"; raw.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path=raw/f"paper-suite-{stamp}.csv"
    with raw_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary={"schema_version":"1.0","generated_at":datetime.now(UTC).isoformat(),
             "commit_sha":commit,"python":platform.python_version(),
             "configuration":{"sizes":args.sizes,"seeds":args.seeds,"fault_rate":args.fault_rate},
             "observation_count":len(rows),"results":summarize(rows),
             "raw_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    summary_path=root/f"paper-suite-{stamp}-summary.json"
    summary_path.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"raw":str(raw_path),"summary":str(summary_path),
                      "observations":len(rows),"commit_sha":commit},indent=2))

if __name__=="__main__": main()
