"""Generate descriptive tables from retained measurements, without rerunning solvers."""
import argparse
import json
import statistics as s
from fractions import Fraction as F
from pathlib import Path

def report(directory):
    data=json.loads((directory/'results.json').read_text());rows=data['rows']
    lines=['# Retained bundle benchmark results','',
           'Synthetic model only. Ratios exclude undefined zero-optimum cases. Timing is local wall time, not cloud performance. Candidate work units differ between policy families.','',
           '| Phase | Mode | Policy | Optimum matches | Ratio min / median | Cost median | Candidate median | Solver ms median |',
           '|---|---|---|---:|---:|---:|---:|---:|']
    for key,item in data['summary'].items():
        phase,mode,policy=key.split('/');group=[r for r in rows if (r['phase'],r['cost_model'],r['policy'])==(phase,mode,policy)]
        ratios=[float(F(r['optimality_ratio'])) for r in group if r['optimality_ratio'] is not None]
        lines.append(f"| {phase} | {mode} | {policy} | {item['matches_exact']}/{len(group)} | {min(ratios):.4f} / {s.median(ratios):.4f} | {float(s.median(F(r['cost']) for r in group)):.2f} | {s.median(r['examined'] for r in group):.1f} | {item['median_runtime_ms']:.3f} |")
    lines+=['','## Paired outcomes and seed sensitivity','',
            'Wins/ties/losses compare union risk at identical budgets within the same cost mode. Seed means average defined optimum-ratio deltas across each seed’s coupled configurations. Range and sample SD describe only three seeds per phase; these are not confidence intervals or independent population estimates.','',
            '| Phase/mode/policy | Baseline | Win/tie/loss | Seed means | Mean | Range | Sample SD |','|---|---|---|---|---:|---|---:|']
    for key,item in data['summary'].items():
        if '/bundle_' not in key:continue
        for base,c in item['comparisons'].items():
            lines.append(f"| {key} | {base} | {c['wins']}/{c['ties']}/{c['losses']} | {c['seed_mean_ratio_delta']} | {c['mean']:.5f} | {c['range']} | {c['sample_sd']:.5f} |")
    lines+=['','## Deterministic fixtures','','| Fixture/mode | Policy | Union risk | Cost |','|---|---|---:|---:|']
    for name,modes in data['fixtures'].items():
        for mode,fixture in modes.items():
            for r in fixture['results']:lines.append(f"| {name}/{mode} | {r['policy']} | {r['risk_reduction']} | {r['cost']} |")
    lines+=['','All 216 historical shared baseline rows reproduce every non-timing field. See results.json for all selected plans, timings, step witnesses, gaps and zero-optimum ratios; inputs.json retains both cost modes. SHA256.json authenticates the retained measurement files.','']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);args=p.parse_args();print(report(args.directory))
