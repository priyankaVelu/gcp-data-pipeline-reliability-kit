"""Deterministic local CDC experiment; no durability or exactly-once claim."""
import argparse
from collections import OrderedDict
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline_reliability.cdc_demo import InvalidEvent, validate

STRATEGIES = ('arrival', 'id_only', 'version')
SCENARIOS = ('ordered', 'out_of_order', 'duplicates', 'delete_reinsert', 'conflicts', 'checkpoint', 'redelivery')
SEEDS = (7, 17, 29)
SIZES = (8, 64)
REPEATS = 5


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def canonical(keys):
    return [dict(event_id=f'{key}:{v}', key=f'k{key}', version=v,
                 value=f'value-{v}', deleted=v == 3)
            for v in range(1, 5) for key in range(keys)]


def oracle(events):
    """Batch max reduction independent of all replay transitions and ledgers."""
    groups = {}
    for event in copy.deepcopy(events):
        groups.setdefault(event['key'], []).append(event)
    return {key: {field: max(group, key=lambda e: e['version'])[field]
                  for field in ('version', 'value', 'deleted')}
            for key, group in groups.items()}


def workload(base, scenario, seed):
    events = copy.deepcopy(base)
    rng = random.Random(seed)
    if scenario in ('out_of_order', 'duplicates', 'delete_reinsert', 'checkpoint', 'redelivery'):
        rng.shuffle(events)
    if scenario in ('out_of_order', 'delete_reinsert'):
        # A guaranteed visible stale delete, not a favorable seed search.
        events.extend(copy.deepcopy([e for e in base if e['key'] == 'k0' and e['version'] in (4, 3)]))
    if scenario == 'duplicates':
        events.extend(copy.deepcopy(events[::4]))
    if scenario == 'conflicts':
        events.append(dict(events[0], value='conflicting'))
    return events


class Processor:
    def __init__(self, strategy, capacity=None):
        if strategy not in STRATEGIES or (capacity is not None and (type(capacity) is not int or capacity < 0)):
            raise ValueError('invalid strategy or capacity')
        self.strategy, self.capacity = strategy, capacity
        self.state, self.seen = {}, OrderedDict()
        self.counts = dict(applied=0, duplicate=0, stale=0)
        self.nondecreasing = True
        self.peak = 0

    def apply(self, event):
        eid = event['event_id']
        payload = tuple(event[f] for f in ('key', 'version', 'value', 'deleted'))
        if self.strategy != 'arrival' and eid in self.seen:
            if self.seen[eid] != payload:
                raise InvalidEvent('conflicting event ID')
            self.counts['duplicate'] += 1
            return 'duplicate'
        old = self.state.get(event['key'])
        if self.strategy == 'version' and old:
            if event['version'] == old['version'] and (event['value'], event['deleted']) != (old['value'], old['deleted']):
                raise InvalidEvent('conflicting key/version')
            if event['version'] < old['version']:
                self.remember(eid, payload)
                self.counts['stale'] += 1
                return 'stale'
        if old and event['version'] < old['version']:
            self.nondecreasing = False
        self.state[event['key']] = {f: event[f] for f in ('version', 'value', 'deleted')}
        self.remember(eid, payload)
        self.counts['applied'] += 1
        return 'applied'

    def remember(self, eid, payload):
        if self.strategy == 'arrival':
            return
        if self.capacity != 0:
            self.seen[eid] = payload
        while self.capacity is not None and len(self.seen) > self.capacity:
            self.seen.popitem(last=False)
        self.peak = max(self.peak, len(self.seen))

    def checkpoint(self):
        return json.dumps(dict(state=self.state, seen=list(self.seen.items()), peak=self.peak))

    def restore(self, checkpoint):
        snapshot = json.loads(checkpoint)
        self.state = snapshot['state']
        self.seen = OrderedDict((k, tuple(v)) for k, v in snapshot['seen'])
        self.peak = snapshot['peak']


def process(events, strategy, checkpoint=0, interruption=0, redeliver=False):
    validate(events)  # Shared full-input contract; no online-detection claim.
    if not 0 <= checkpoint <= interruption <= len(events):
        raise ValueError('invalid recovery boundary')
    p = Processor(strategy)
    saved = p.checkpoint()
    for i, event in enumerate(events[:interruption], 1):
        p.apply(event)
        if i == checkpoint:
            saved = p.checkpoint()
    before_counts = dict(p.counts)
    before_monotonic = p.nondecreasing
    p = Processor(strategy)
    p.restore(saved)
    for event in events[checkpoint:]:
        p.apply(event)
    before = copy.deepcopy(p.state)
    if redeliver:
        for event in events:
            p.apply(event)
    return dict(state=p.state, before_counts=before_counts, recovery_counts=p.counts,
                nondecreasing_version=before_monotonic and p.nondecreasing,
                redelivery_state_unchanged=p.state == before if redeliver else None,
                checkpoint_offset=checkpoint, interruption_offset=interruption,
                lost_attempts=interruption-checkpoint,
                replayed_lost_attempts=interruption-checkpoint,
                restart_deliveries=len(events)-checkpoint,
                redelivery_deliveries=len(events) if redeliver else 0)


def observation(base, events, scenario, strategy):
    cp = len(events)//3 if scenario in ('checkpoint', 'redelivery') else 0
    cut = 2*len(events)//3 if cp else 0
    samples = []
    output = None
    rejected = False
    for _ in range(REPEATS):
        start = time.perf_counter_ns()
        try:
            output = process(events, strategy, cp, cut, scenario == 'redelivery')
        except InvalidEvent:
            if scenario != 'conflicts':
                raise
            rejected = True
        samples.append((time.perf_counter_ns()-start)/1e6)
    result = dict(strategy=strategy, scenario=scenario, input_rejected=rejected,
                  runtime_ms=statistics.median(samples), runtime_samples_ms=samples,
                  workload_sha256=digest(events), state_correct=None, wrong_keys=None)
    if output is not None:
        target = oracle(base)
        wrong = sorted(k for k in set(target) | set(output['state']) if target.get(k) != output['state'].get(k))
        result.update(output)
        result.update(state_correct=not wrong, wrong_keys=len(wrong))
    return result


def bounded(strategy, capacity, seed):
    events = canonical(16)
    random.Random(seed).shuffle(events)
    # Establish the first ID far outside all finite retention horizons, with
    # a newer version of the same key materialized before redelivery.
    first = canonical(16)[0]
    events = [first] + [e for e in events if e['event_id'] != first['event_id']]
    samples = []
    for _ in range(REPEATS):
        start = time.perf_counter_ns()
        p = Processor(strategy, capacity)
        for event in events:
            p.apply(event)
        before = copy.deepcopy(p.state)
        duplicate_recognized = p.apply(first) == 'duplicate'
        changed = p.state != before
        detected = False
        try:
            p.apply(dict(first, value='conflicting'))
        except InvalidEvent:
            detected = True
        samples.append((time.perf_counter_ns()-start)/1e6)
    return dict(strategy=strategy, capacity=capacity, seed=seed, ledger_peak=p.peak,
                duplicate_recognized=duplicate_recognized, redelivery_changed_state=changed,
                conflict_detected=detected, workload_sha256=digest(events),
                runtime_ms=statistics.median(samples), runtime_samples_ms=samples)


def csv_file(path, rows):
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()})


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    try:
        rows = []
        for size in SIZES:
            base = canonical(size)
            for seed in SEEDS:
                for scenario in SCENARIOS:
                    events = workload(base, scenario, seed)
                    order = len(rows)//3 % 3
                    for strategy in STRATEGIES[order:] + STRATEGIES[:order]:
                        row = observation(base, events, scenario, strategy)
                        row.update(keys=size, seed=seed)
                        rows.append(row)
        bounded_rows = [bounded(s, c, seed) for seed in SEEDS for c in (0, 4, 16, None) for s in STRATEGIES]
        assert len(rows) == 126 and len(bounded_rows) == 36
        source = Path(__file__).resolve()
        metadata = dict(schema_version='1.0', generated_at=datetime.now(timezone.utc).isoformat(),
                        commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                        tracked_dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'], text=True)),
                        python=platform.python_version(), platform=platform.platform(), repeats=REPEATS,
                        seeds=SEEDS, sizes=SIZES, scenarios=SCENARIOS,
                        runner_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                        protocol_sha256=hashlib.sha256(source.with_name('PROTOCOL.md').read_bytes()).hexdigest())
        data = dict(metadata=metadata, principal=rows, bounded=bounded_rows)
        (output/'results.json').write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
        csv_file(output/'principal.csv', rows)
        csv_file(output/'bounded.csv', bounded_rows)
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
        (output/'SHA256.json').write_text(json.dumps(hashes, indent=2, sort_keys=True)+'\n')
        print(json.dumps(dict(output=str(output), principal=len(rows), bounded=len(bounded_rows))))
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps(dict(error=repr(exc)))+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run(parser.parse_args().output)
