import copy
from http.server import ThreadingHTTPServer
import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError

from pipeline_reliability import cdc_interactive as model


class InteractiveModelTests(unittest.TestCase):
    def test_hand_oracle_conflicts_and_independence(self):
        base=model.canonical(1,(1,3,4))
        with patch.object(model,'validate',side_effect=AssertionError('shared validator')):
            self.assertEqual(model.oracle(base),{'k0':dict(version=4,value='value-4',deleted=False)})
        for bad in (dict(base[0],value='wrong'),dict(base[0],event_id='new',value='wrong')):
            with self.assertRaises(ValueError):
                model.oracle(base+[bad])
        saved=copy.deepcopy(base)
        _,events=model.scenario('duplicate_only',1,7)
        events[0]['value']='changed'
        self.assertEqual(base,saved)

    def test_isolated_controls_and_seeded_duplicates(self):
        for name in ('ordered','duplicate_only','ordered_delete_reinsert','checkpoint_recovery'):
            for strategy in model.STRATEGIES:
                result=model.evaluate(name,strategy,keys=3)
                self.assertTrue(result['state_correct'],(name,strategy))
                self.assertEqual(sum(result['violations'].values()),0)
        _,events=model.scenario('duplicate_only',3,7)
        self.assertGreater(len(events),6)
        for key in ('k0','k1','k2'):
            versions=[e['version'] for e in events if e['key']==key]
            self.assertEqual(versions,sorted(versions))
        self.assertEqual(events,model.scenario('duplicate_only',3,7)[1])

    def test_subminute_counterexample_and_order_switch(self):
        for strategy in ('arrival','id_only'):
            result=model.evaluate('stale_update',strategy,keys=1)
            self.assertFalse(result['state_correct'])
            self.assertEqual(result['wrong_keys'][0]['reason'],'stale version')
        self.assertTrue(model.evaluate('stale_update','version',keys=1)['state_correct'])
        self.assertTrue(model.evaluate('stale_update','arrival',keys=1,ordering='version_order')['state_correct'])

    def test_attempted_versus_committed_recovered_writes(self):
        events=[model.canonical(1,(4,))[0],model.canonical(1,(3,))[0]]
        result=model.replay(events,'arrival',checkpoint=1,interruption=2)
        self.assertEqual(result['violations'],dict(attempted=1,committed_prefix=0,recovered=1))
        self.assertEqual(result['lost_attempts'],1)
        self.assertEqual(result['replayed_lost_attempts'],1)
        self.assertEqual(result['trace'][2]['discarded_on_restore'],True)
        p=model.Materializer('version',None)
        snapshot=p.snapshot();p.apply(events[0]);p.restore(snapshot)
        self.assertEqual(p.state,{})
        self.assertEqual(p.seen,{})
        for cp,cut in ((0,0),(0,4),(2,3),(4,4)):
            result=model.evaluate('ordered_delete_reinsert','version',keys=1,checkpoint=cp,interruption=cut)
            self.assertTrue(result['state_correct'])
            self.assertEqual(result['lost_attempts'],cut-cp)

    def test_conflict_modes_and_expiry(self):
        for name in ('conflicting_id','same_version_conflict'):
            for strategy in model.STRATEGIES:
                result=model.evaluate(name,strategy,keys=1)
                self.assertTrue(result['input_rejected'])
                self.assertIsNone(result['state_correct'])
                self.assertEqual(result['trace'],[])
        self.assertFalse(model.evaluate('same_version_conflict','version',keys=1,validation='online')['completed'])
        self.assertTrue(model.evaluate('same_version_conflict','id_only',keys=1,validation='online')['completed'])
        for capacity in (0,4):
            output=model.evaluate('ledger_expiry','version',keys=16,capacity=capacity,validation='online')
            self.assertTrue(output['completed'])
            self.assertTrue(output['state_correct'])
            self.assertIsNone(output['conflict_error'])
            self.assertLessEqual(output['ledger_peak'],capacity)
        output=model.evaluate('ledger_expiry','version',keys=16,validation='online')
        self.assertFalse(output['completed'])
        self.assertEqual(output['conflict_error'],'conflicting event ID')

    def test_invalid_controls(self):
        for options in (dict(checkpoint=2,interruption=1),dict(capacity=-1),dict(keys=True),dict(keys=65),dict(ordering='bad'),dict(validation='bad'),dict(strategy='bad'),dict(redeliver='yes')):
            with self.assertRaises(ValueError):model.evaluate(**options)


class InteractiveHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),model.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start();cls.url=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def post(self,options):
        request=Request(self.url+'/api/replay',data=json.dumps(options).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=5) as response:return json.load(response)

    def test_live_walkthrough(self):
        with urlopen(self.url,timeout=5) as r:
            self.assertIn(b'Run comparison',r.read())
        with urlopen(self.url+'/api/scenarios',timeout=5) as r:
            self.assertIn('stale_update',json.load(r)['scenarios'])
        # These calls follow the five-minute audience demonstration sequence.
        bad=self.post(dict(name='stale_update',strategy='arrival',keys=1))
        self.assertFalse(bad['state_correct'])
        self.assertTrue(self.post(dict(name='stale_update',strategy='version',keys=1))['state_correct'])
        recovery=self.post(dict(name='post_recovery_redelivery',strategy='version',keys=3,checkpoint=4,interruption=8))
        self.assertEqual(recovery['lost_attempts'],4)
        self.assertTrue(recovery['redelivery_state_unchanged'])
        self.assertTrue(recovery['state_correct'])
        expired=self.post(dict(name='ledger_expiry',strategy='version',keys=16,capacity=4,validation='online'))
        self.assertTrue(expired['completed'])
        self.assertIsNone(expired['conflict_error'])
        remembered=self.post(dict(name='ledger_expiry',strategy='version',keys=16,validation='online'))
        self.assertFalse(remembered['completed'])

    def test_http_errors(self):
        for payload in ('not-json','[]','{"unexpected":true}','{"checkpoint":3,"interruption":1}'):
            with self.assertRaises(HTTPError) as caught:
                urlopen(Request(self.url+'/api/replay',data=payload.encode()),timeout=5)
            self.assertEqual(caught.exception.code,400)
            self.assertEqual(json.load(caught.exception)['schema_version'],'3.0')
        with self.assertRaises(HTTPError) as caught:urlopen(self.url+'/not-here',timeout=5)
        self.assertEqual(caught.exception.code,404)
