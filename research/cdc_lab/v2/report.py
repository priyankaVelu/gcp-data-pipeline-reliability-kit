"""Derive report numbers from hash-verified V2 observations."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from verify import verify,preserve


def report(directory):
    directory=Path(directory)
    data=verify(directory)
    if len(data['principal'])!=144 or len(data['bounded'])!=72:
        raise ValueError('unexpected V2 matrix dimensions')
    summaries={}
    scenarios={}
    for strategy in ('arrival','id_only','version'):
        rows=[r for r in data['principal'] if r['strategy']==strategy]
        valid=[r for r in rows if r['completed']]
        summaries[strategy]=dict(correct=sum(r['state_correct'] is True for r in rows),
                                 incorrect=sum(r['state_correct'] is False for r in rows),
                                 rejected=sum(r['input_rejected'] for r in rows),
                                 valid_runtime_median_min_ms=min(r['runtime_ms'] for r in valid),
                                 valid_runtime_median_max_ms=max(r['runtime_ms'] for r in valid),
                                 attempted_violation_sum=sum(r['violations']['attempted'] for r in valid),
                                 committed_prefix_violation_sum=sum(r['violations']['committed_prefix'] for r in valid),
                                 recovered_violation_sum=sum(r['violations']['recovered'] for r in valid))
    for name in data['metadata']['scenarios']:
        scenarios[name]={s:dict(correct=sum(r['state_correct'] is True for r in data['principal'] if r['scenario']==name and r['strategy']==s),
                               rejected=sum(r['input_rejected'] for r in data['principal'] if r['scenario']==name and r['strategy']==s))
                         for s in summaries}
    return dict(generated_at=datetime.now(timezone.utc).isoformat(),
                source_results_sha256=hashlib.sha256((directory/'results.json').read_bytes()).hexdigest(),
                metadata=data['metadata'],principal_count=144,bounded_count=72,
                principal_summary=summaries,scenarios=scenarios,
                preservation=preserve(Path(__file__).resolve().parents[3]))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    with args.output.open('x') as handle:json.dump(report(args.input),handle,indent=2,sort_keys=True);handle.write('\n')
