"""Strict artifact validation and non-timing baseline comparison."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

TIMING = {'runtime_ms', 'runtime_samples_ms'}


def csv_cell(value):
    if isinstance(value, (dict,list)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ''
    return str(value)


def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'SHA256.json').read_text())
    expected = {'results.json','principal.csv','bounded.csv'}
    if set(manifest) != expected:
        raise ValueError('unexpected artifact manifest entries')
    for name, digest in manifest.items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'hash mismatch: {name}')
    data = json.loads((directory/'results.json').read_text())
    for group in ('principal','bounded'):
        with (directory/f'{group}.csv').open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != len(data[group]):
            raise ValueError(f'row count mismatch: {group}')
        fields = set().union(*(row.keys() for row in data[group]))
        for actual, row in zip(rows, data[group]):
            if actual != {k: csv_cell(row.get(k)) for k in fields}:
                raise ValueError(f'CSV/JSON mismatch: {group}')
    return data


def compare(original, reproduced):
    old, new = verify(original), verify(reproduced)
    for field in ('runner_sha256','protocol_sha256','seeds','sizes','repeats','scenarios'):
        if old['metadata'][field] != new['metadata'][field]:
            raise ValueError(f'baseline configuration changed: {field}')
    counts = {}
    for group, count in (('principal',126),('bounded',36)):
        if len(old[group]) != count or len(new[group]) != count:
            raise ValueError(f'incorrect baseline row count: {group}')
        strip = lambda rows: [{k:v for k,v in row.items() if k not in TIMING} for row in rows]
        if strip(old[group]) != strip(new[group]):
            raise ValueError(f'non-timing outcomes differ: {group}')
        counts[group] = count
    return dict(status='identical_non_timing_outcomes', counts=counts,
                original_metadata=old['metadata'], reproduced_metadata=new['metadata'],
                note='Independent execution of the original implementation, not independent implementation replication. Timing samples intentionally excluded.')


def preserve(root):
    root = Path(root)
    manifest = json.loads((root/'research/cdc_lab/v2/BASELINE_INTEGRITY.json').read_text())
    changed = [name for name, digest in manifest['files'].items()
               if not (root/name).exists() or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest]
    if changed:
        raise ValueError('protected files changed: '+', '.join(changed))
    return dict(status='preserved', files_checked=len(manifest['files']),base_commit=manifest['base_commit'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True)
    parser.add_argument('--reproduced', required=True)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    result = compare(args.original,args.reproduced)
    result['preservation'] = preserve(Path(__file__).resolve().parents[3])
    with args.report.open('x') as handle:
        json.dump(result,handle,indent=2,sort_keys=True)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'],preservation=result['preservation'])))
