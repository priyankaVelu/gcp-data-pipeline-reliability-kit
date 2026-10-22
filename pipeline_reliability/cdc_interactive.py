"""Synthetic CDC replay model and local interactive UI; no durable storage."""
import argparse
from collections import OrderedDict
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import random

from .cdc_demo import InvalidEvent, validate

STRATEGIES = ('arrival', 'id_only', 'version')
SCENARIOS = ('ordered', 'duplicate_only', 'ordered_delete_reinsert', 'stale_update',
             'conflicting_id', 'same_version_conflict', 'checkpoint_recovery',
             'post_recovery_redelivery', 'ledger_expiry')
FIELDS = ('version', 'value', 'deleted')


def canonical(keys, versions):
    return [dict(event_id=f'b{k}:v{v}', key=f'k{k}', version=v,
                 value=f'value-{v}', deleted=v == 3)
            for v in versions for k in range(keys)]


def oracle(events):
    """Independent batch specification, not a replay fold or shared validator."""
    identities, versions, groups = {}, {}, {}
    for event in events:
        eid, key, version = event['event_id'], event['key'], event['version']
        payload = (key, version, event['value'], event['deleted'])
        if eid in identities and identities[eid] != payload:
            raise ValueError('oracle: ambiguous identity')
        identities[eid] = payload
        pair = (key, version)
        state = {f: event[f] for f in FIELDS}
        if pair in versions and versions[pair] != state:
            raise ValueError('oracle: ambiguous key/version')
        versions[pair] = state
        groups.setdefault(key, set()).add(version)
    return {key: copy.deepcopy(versions[(key, max(values))]) for key, values in groups.items()}


def scenario(name, keys=3, seed=7):
    if name not in SCENARIOS:
        raise ValueError('unknown scenario')
    versions = (1, 2) if name in ('ordered', 'duplicate_only', 'conflicting_id', 'same_version_conflict') else (3, 4) if name == 'stale_update' else (1, 2, 3, 4)
    base = canonical(keys, versions)
    events = copy.deepcopy(base)
    rng = random.Random(seed)
    if name == 'duplicate_only':
        selected = set(rng.sample(range(len(events)), max(1, len(events)//3)))
        events = [copy.deepcopy(event) for i, event in enumerate(events)
                  for _ in range(2 if i in selected else 1)]
    elif name == 'stale_update':
        live = [e for e in events if e['version'] == 4]
        old = [e for e in events if e['version'] == 3]
        rng.shuffle(live); rng.shuffle(old)
        events = live + old
    elif name == 'conflicting_id':
        events.append(dict(events[0], value='conflicting'))
    elif name == 'same_version_conflict':
        events.append(dict(events[-1], event_id='conflict:new-id', value='conflicting'))
    elif name == 'ledger_expiry':
        events.append(dict(events[0], value='conflicting'))
    return base, events


class Materializer:
    def __init__(self, strategy, capacity):
        self.strategy, self.capacity = strategy, capacity
        self.state, self.seen = {}, OrderedDict()
        self.peak = 0

    def apply(self, event):
        eid, key = event['event_id'], event['key']
        payload = tuple(event[f] for f in ('key', *FIELDS))
        if self.strategy != 'arrival' and eid in self.seen:
            if self.seen[eid] != payload:
                raise InvalidEvent('conflicting event ID')
            return 'duplicate'
        old = self.state.get(key)
        if self.strategy == 'version' and old:
            if event['version'] == old['version'] and any(event[f] != old[f] for f in ('value','deleted')):
                raise InvalidEvent('conflicting key/version')
            if event['version'] < old['version']:
                self.remember(eid, payload)
                return 'stale'
        self.state[key] = {f: event[f] for f in FIELDS}
        self.remember(eid, payload)
        return 'applied'

    def remember(self, eid, payload):
        if self.strategy == 'arrival' or self.capacity == 0:
            return
        self.seen[eid] = payload
        while self.capacity is not None and len(self.seen) > self.capacity:
            self.seen.popitem(last=False)
        self.peak = max(self.peak, len(self.seen))

    def snapshot(self):
        return json.dumps(dict(state=self.state, seen=list(self.seen.items()), peak=self.peak))

    def restore(self, snapshot):
        value = json.loads(snapshot)
        self.state = value['state']
        self.seen = OrderedDict((k, tuple(v)) for k, v in value['seen'])
        self.peak = value['peak']


def wrong_keys(actual, target):
    wrong = []
    for key in sorted(set(actual) | set(target)):
        got, expected = actual.get(key), target.get(key)
        if got == expected:
            continue
        reason = 'missing key' if got is None else 'unexpected key' if expected is None else 'stale version' if got['version'] < expected['version'] else 'unexpected newer version' if got['version'] > expected['version'] else 'payload/tombstone mismatch'
        wrong.append(dict(key=key, reason=reason, actual=got, expected=expected))
    return wrong


def replay(events, strategy, *, checkpoint=0, interruption=0, capacity=None,
           redeliver=False, validation='global', trace=True):
    if strategy not in STRATEGIES or validation not in ('global', 'online'):
        raise ValueError('invalid strategy or validation mode')
    if capacity is not None and (type(capacity) is not int or capacity < 0):
        raise ValueError('capacity must be a nonnegative integer or null')
    if any(type(x) is not int for x in (checkpoint, interruption)) or not 0 <= checkpoint <= interruption <= len(events):
        raise ValueError('require 0 <= checkpoint <= interruption <= event count')
    if type(redeliver) is not bool:
        raise ValueError('redeliver must be a boolean')
    counters = {phase: {d: 0 for d in ('applied','duplicate','stale','conflict')} for phase in ('attempt','restart','redelivery')}
    violations = dict(attempted=0, committed_prefix=0, recovered=0)
    log, p = [], Materializer(strategy, capacity)
    result = dict(state={}, completed=False, input_rejected=False, conflict_error=None,
                  trace=log, counters=counters, violations=violations,
                  checkpoint_offset=checkpoint, interruption_offset=interruption,
                  lost_attempts=0, replayed_lost_attempts=0, restart_deliveries=0,
                  redelivery_deliveries=0, ledger_peak=0, redelivery_state_unchanged=None)
    if validation == 'global':
        try:
            validate(events)
        except InvalidEvent as exc:
            result.update(input_rejected=True, conflict_error=str(exc))
            return result

    def deliver(event, phase, offset):
        validate([event])
        before = copy.deepcopy(p.state.get(event['key']))
        try:
            decision = p.apply(event)
        except InvalidEvent as exc:
            decision = 'conflict'
            result['conflict_error'] = str(exc)
        counters[phase][decision] += 1
        if decision == 'applied' and before is not None and before['version'] > event['version']:
            violations['attempted' if phase == 'attempt' else 'recovered'] += 1
            if phase == 'attempt' and offset < checkpoint:
                violations['committed_prefix'] += 1
        if trace:
            log.append(dict(phase=phase, offset=offset, event=copy.deepcopy(event),
                            decision=decision, before=before, after=copy.deepcopy(p.state.get(event['key'])),
                            ledger_size=len(p.seen), state=copy.deepcopy(p.state),
                            discarded_on_restore=phase == 'attempt' and offset >= checkpoint))
        return decision != 'conflict'

    def finish():
        result.update(state=copy.deepcopy(p.state), ledger_peak=p.peak)
        return result

    saved = p.snapshot()
    for i, event in enumerate(events[:interruption]):
        if not deliver(event, 'attempt', i):
            return finish()
        if i+1 == checkpoint:
            saved = p.snapshot()
            if trace:
                log.append(dict(phase='checkpoint', offset=checkpoint, state=copy.deepcopy(p.state)))
    p = Materializer(strategy, capacity)
    p.restore(saved)
    result['lost_attempts'] = interruption-checkpoint
    if trace:
        log.append(dict(phase='restore', offset=checkpoint, state=copy.deepcopy(p.state)))
    for i in range(checkpoint, len(events)):
        result['restart_deliveries'] += 1
        if i < interruption:
            result['replayed_lost_attempts'] += 1
        if not deliver(events[i], 'restart', i):
            return finish()
    before_redelivery = copy.deepcopy(p.state)
    if redeliver:
        for i, event in enumerate(reversed(events)):
            result['redelivery_deliveries'] += 1
            if not deliver(event, 'redelivery', i):
                return finish()
        result['redelivery_state_unchanged'] = p.state == before_redelivery
    result['completed'] = True
    return finish()


def evaluate(name='stale_update', strategy='arrival', keys=3, seed=7,
             checkpoint=0, interruption=0, capacity=None, ordering='native',
             validation='global', redeliver=None):
    if type(keys) is not int or not 1 <= keys <= 64 or type(seed) is not int:
        raise ValueError('keys must be 1..64 and seed must be an integer')
    if ordering not in ('native','reverse','shuffle','version_order'):
        raise ValueError('unknown ordering')
    if redeliver is not None and type(redeliver) is not bool:
        raise ValueError('redeliver must be a boolean or null')
    base, events = scenario(name, keys, seed)
    target = oracle(base)
    if ordering == 'reverse':
        events.reverse()
    elif ordering == 'shuffle':
        random.Random(seed).shuffle(events)
    elif ordering == 'version_order':
        events.sort(key=lambda e: (e['version'],e['key']))
    output = replay(events, strategy, checkpoint=checkpoint, interruption=interruption,
                    capacity=capacity, validation=validation,
                    redeliver=name == 'post_recovery_redelivery' if redeliver is None else redeliver)
    wrong = wrong_keys(output['state'], target)
    output.update(conflict_expected=name in ('conflicting_id','same_version_conflict','ledger_expiry'),
                  validation=validation, schema_version='3.0', scenario=name, strategy=strategy, events=events,
                  oracle=target, wrong_keys=wrong,
                  state_correct=not wrong if output['completed'] else None,
                  state_equals_oracle=not wrong,
                  limitations='Synthetic logical checkpoint; no disk durability, exactly-once or cloud integration.')
    return output


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, payload, content_type='application/json'):
        body = payload if isinstance(payload, bytes) else json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            # Embedded HTML keeps the interface available from the installed wheel.
            self.respond(200, HTML.encode(), 'text/html; charset=utf-8')
        elif self.path == '/api/scenarios':
            self.respond(200, dict(scenarios=SCENARIOS,strategies=STRATEGIES))
        else:
            self.respond(404, dict(error='not found'))

    def do_POST(self):
        if self.path != '/api/replay':
            self.respond(404, dict(error='not found')); return
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16384:
                raise ValueError('request body must be 1..16384 bytes')
            options = json.loads(self.rfile.read(length))
            if not isinstance(options, dict):
                raise ValueError('options must be a JSON object')
            self.respond(200, evaluate(**options))
        except (ValueError, TypeError, KeyError) as exc:
            self.respond(400, dict(schema_version='3.0', error=str(exc)))


def serve(port=8765):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('port must be 0..65535')
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'CDC Replay Lab listening on http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


HTML = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CDC Replay Correctness Lab</title><style>
body{font:15px system-ui;background:#f3f6fa;color:#16243c;margin:0} main{max-width:1200px;margin:auto;padding:28px}
h1{margin:0 0 8px} .note{color:#53617b} .controls,.card{background:white;border:1px solid #dbe2ec;border-radius:10px;padding:18px;margin:16px 0}
.controls{display:flex;gap:14px;flex-wrap:wrap} label{display:flex;flex-direction:column;gap:5px;font-weight:600}
input,select,button{font:inherit;padding:8px;border:1px solid #ccd5e0;border-radius:5px} input{width:90px}button{background:#194c88;color:white;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px} pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px} .bad{color:#9d2630}.good{color:#126b4b}
table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #e6ebf2;padding:7px} .scroll{max-height:350px;overflow:auto}
@media(max-width:700px){.grid{grid-template-columns:1fr}} #step{width:250px} #error{color:#9d2630} h2{font-size:19px}
</style><main><h1>CDC Replay Correctness Lab</h1><div class="note">Explore stale deletes, replay and finite identity memory. Synthetic logical checkpoints — no production durability, exactly-once or cloud claims.</div>
<form id="controls" class="controls">
<label>Scenario<select id="name"></select></label><label>Strategy<select id="strategy"><option value="arrival">Arrival order</option><option value="id_only">ID deduplication only</option><option value="version">Version aware</option></select></label>
<label>Order<select id="ordering"><option value="native">Scenario order</option><option value="reverse">Reverse</option><option value="shuffle">Seeded shuffle</option><option value="version_order">Version ordered</option></select></label>
<label>Keys<input id="keys" type="number" min="1" max="64" value="3" required></label><label>Seed<input id="seed" type="number" value="7" required></label>
<label>Checkpoint<input id="checkpoint" type="number" min="0" value="0" required></label><label>Interruption<input id="interruption" type="number" min="0" value="0" required></label>
<label>ID capacity<input id="capacity" type="number" min="0" placeholder="Unlimited"></label>
<label>Validation<select id="validation"><option value="global">Whole input (preflight)</option><option value="online">Online (finite memory)</option></select></label>
<button id="run" type="submit">Run comparison</button><button type="button" id="counterexample">Stale-delete preset</button></form>
<div id="error" role="alert"></div><div class="card"><strong id="verdict" aria-live="polite">Ready</strong><div id="explanation"></div></div>
<div class="grid"><section class="card"><h2>Actual materialized state</h2><pre id="actual"></pre></section><section class="card"><h2>Independent canonical oracle</h2><pre id="oracle"></pre></section></div>
<section class="card"><h2>Incorrect keys and reasons</h2><div id="wrong"></div></section>
<section class="card"><h2>Step through execution</h2><label>Trace position<input type="range" id="step" min="0" max="0" value="0"></label><button type="button" id="next">Next event</button><pre id="event"></pre><h3>State at this trace position</h3><pre id="stepstate"></pre><div class="scroll"><table><thead><tr><th>Phase</th><th>Offset</th><th>Event</th><th>Decision</th><th>Ledger</th></tr></thead><tbody id="trace"></tbody></table></div></section>
<section class="card"><h2>Recovery and invariant evidence</h2><pre id="metrics"></pre><div class="note">Attempted writes may be discarded. Restoring an older checkpoint is not counted as a stale materialization write. A rejected/incomplete input has no final correctness verdict.</div></section>
</main><script>
let result;const $=id=>document.getElementById(id), pretty=x=>JSON.stringify(x,null,2);
function showstep(){const t=result?.trace[Number($('step').value)];$('event').textContent=t?pretty({phase:t.phase,offset:t.offset,event:t.event,decision:t.decision,discarded_on_restore:t.discarded_on_restore}):'No processing trace (input may have been rejected before replay).';$('stepstate').textContent=t?pretty(t.state):'{}';}
async function run(){ $('error').textContent='';try{const options={name:$('name').value,strategy:$('strategy').value,ordering:$('ordering').value,validation:$('validation').value};for(const k of ['keys','seed','checkpoint','interruption'])options[k]=Number($(k).value);options.capacity=$('capacity').value===''?null:Number($('capacity').value);
const response=await fetch('/api/replay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(options)});const value=await response.json();if(!response.ok)throw Error(value.error);result=value;
$('verdict').textContent=value.completed?(value.state_correct?'Matches the oracle':'Incorrect final state'):(value.input_rejected?'Rejected before processing':'Online processing stopped');$('verdict').className=value.state_correct?'good':'bad';
$('explanation').textContent=value.conflict_error||(value.conflict_expected && value.validation==='online'?'Injected conflict was not detected. Final-state equality is not a guarantee.':value.limitations);$('actual').textContent=pretty(value.state);$('oracle').textContent=pretty(value.oracle);
$('wrong').textContent=value.wrong_keys.length?value.wrong_keys.map(w=>`${w.key}: ${w.reason}`).join('; '):'No mismatching keys (correctness still requires completed processing).';
$('metrics').textContent=pretty({completed:value.completed,counters:value.counters,violations:value.violations,checkpoint_offset:value.checkpoint_offset,interruption_offset:value.interruption_offset,lost_attempts:value.lost_attempts,replayed_lost_attempts:value.replayed_lost_attempts,restart_deliveries:value.restart_deliveries,redelivery_deliveries:value.redelivery_deliveries,ledger_peak:value.ledger_peak,redelivery_state_unchanged:value.redelivery_state_unchanged});
$('trace').replaceChildren();for(const t of value.trace){const row=document.createElement('tr');for(const v of [t.phase,t.offset,t.event?.event_id||'—',t.decision||'snapshot',t.ledger_size??'—']){const cell=document.createElement('td');cell.textContent=v;row.append(cell)}$('trace').append(row)}$('step').max=Math.max(0,value.trace.length-1);$('step').value=0;showstep();
}catch(e){$('error').textContent=e.message}}
$('controls').addEventListener('submit',e=>{e.preventDefault();run()});$('step').addEventListener('input',showstep);$('next').addEventListener('click',()=>{$('step').value=Math.min(Number($('step').max),Number($('step').value)+1);showstep()});
$('counterexample').addEventListener('click',()=>{for(const [k,v] of Object.entries({name:'stale_update',strategy:'arrival',ordering:'native',checkpoint:0,interruption:0,keys:1,seed:7,capacity:'',validation:'global'}))$(k).value=v;run()});
fetch('/api/scenarios').then(r=>r.json()).then(v=>{for(const name of v.scenarios){const option=document.createElement('option');option.value=name;option.textContent=name.replaceAll('_',' ');$('name').append(option)}$('name').value='stale_update';run()}).catch(e=>{$('error').textContent=e.message});
</script></html>'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    serve(parser.parse_args().port)
