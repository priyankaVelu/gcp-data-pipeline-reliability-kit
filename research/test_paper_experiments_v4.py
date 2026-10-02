"""Pre-result validation tests for Experiment Suite v4."""
import importlib.util
from pathlib import Path

P=Path(__file__).with_name("run_paper_experiments_v4.py")
spec=importlib.util.spec_from_file_location("v4",P);v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)

def check(cond,msg):
    if not cond:raise AssertionError(msg)

def main():
    check(v4.STRATEGIES==("S1_minimal","S2_temporal","S3_recovery","S4_full"),"strategy set changed")
    check(v4.SIZES==(1000,10000,100000),"sizes changed")
    check(v4.SEEDS==(1301,2609,3911,5209,6521),"seeds changed")
    check(v4.INTENSITIES==(.01,.05,.10),"intensities changed")
    check(v4.REPEATS==7,"timing repeats changed")
    v4.deterministic_check()

    rows=v4.canonical(1000,1301);oracle=v4.oracle_for(rows)
    check(len(oracle["event_ids"])==1000,"oracle membership wrong")
    check(all(x["business_key"] is not None for x in rows),"canonical keys invalid")

    rates=dict(duplicate_rate=.05,null_key_rate=.05,late_rate=.05,conflict_rate=.05,
               checkpoint_fraction=.5,replay_fraction=.5,recovery=True)
    work,realized=v4.inject(rows,1301,**rates)
    check(realized["duplicate"]==50,"duplicate realized count wrong")
    check(realized["null_key"]==50,"null realized count wrong")
    check(realized["late"]==50,"late realized count wrong")
    check(realized["conflict"]>0,"conflict injection missing")
    check(realized["recovery_replay"]>0,"recovery replay missing")

    # Independent oracle must remain unchanged by injection.
    check(len(oracle["event_ids"])==1000,"oracle mutated by fault injection")
    check(all(x["business_key"] is not None for x in rows),"canonical rows mutated")

    obs=v4.run_config(1000,1301,.05,"test-sha")
    check(len(obs)==4,"principal config must emit four strategy observations")
    for r in obs:
        for key in ("state_correctness_rate","duplicate_leakage_rate","invalid_key_leakage_rate",
                    "stale_state_rate","recovery_completeness_rate","false_rejection_rate","fault_detection_recall"):
            check(0<=r[key]<=1,f"{key} outside [0,1]")
        check(r["timing_repeats"]==7,"timing repeat metadata wrong")
        check(r["commit_sha"]=="test-sha","commit metadata wrong")

    controls=v4.run_controls(1000,1301,"test-sha")
    check(len(controls)==20,"five controls x four strategies expected")
    check({r["fault_condition"] for r in controls}==set(v4.CONTROL_FAULTS),"control conditions wrong")

    # We intentionally do NOT assert which strategy wins or require favorable outcomes.
    print("Experiment Suite v4 pre-result tests: PASS")
    print("Validated: frozen matrix constants, independent oracle, deterministic injection, causal fault counts,")
    print("four principal strategies, five matched control conditions, metric bounds, and reproducibility metadata.")

if __name__=="__main__":main()
