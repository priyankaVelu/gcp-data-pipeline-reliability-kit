"""Independent checks of rational union utility and shared-cost planning."""
from dataclasses import replace
from fractions import Fraction as F
import json
from itertools import combinations
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.queryguard.overlap_v1 import model, planner, oracle, fixtures


class ModelTests(unittest.TestCase):
    def test_hand_union_no_double_count(self):
        p=fixtures.overlap()
        a=model.account(p,['A']);b=model.account(p,['B']);both=model.account(p,['A','B'])
        self.assertEqual((a['risk_reduction'],b['risk_reduction'],both['risk_reduction']),(22,50,52))
        self.assertEqual(a['risk_reduction']+b['risk_reduction'],72)
        self.assertEqual(model.account(p,['A','B','redundant'])['risk_reduction'],52)
        self.assertEqual(both['residual_risk'],0)
        self.assertEqual((both['cost'],both['coverage']),(6,3))

    def test_duplicate_incidence_and_multi_scan_are_sets(self):
        p=fixtures.overlap()
        c=model.Check('multi',['shared','other','shared'],[('f1','critical')]*4,2)
        p=replace(p,scans=p.scans+(model.Scan('other',3),),checks=p.checks+(c,))
        self.assertEqual(model.account(p,['multi'])['cost'],9)
        self.assertEqual(model.account(p,['multi'])['risk_reduction'],20)
        self.assertEqual(model.account(p,['multi','A'])['cost'],10)

    def test_mutually_exclusive_and_severity_accounting(self):
        p=model.Problem((model.Fault('a','1/4'),model.Fault('b','1/2')),(model.Consumer('c',80),),
                        (model.Exposure('a','c','1/2'),model.Exposure('b','c')),(),
                        (model.Check('q',(),[('a','c')]),))
        score=model.account(p,['q'])
        self.assertEqual((score['total_risk'],score['risk_reduction'],score['residual_risk']),(50,10,40))
        self.assertLessEqual(score['total_risk'],80)

    def test_round_trip_and_input_canonicalization(self):
        p=fixtures.generated(7,6)
        self.assertEqual(model.Problem.from_dict(json.loads(json.dumps(p.to_dict()))),p)
        self.assertEqual(replace(p,checks=tuple(reversed(p.checks))),p)
        with self.assertRaises(ValueError):model.Problem.from_dict({'checks':[]})
        raw=p.to_dict();raw['checks'][0]['extra']=True
        with self.assertRaises(ValueError):model.Problem.from_dict(raw)

    def test_invalid_numbers_ids_and_relations(self):
        for value in (-1,'NaN','inf',True,None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):model.Scan('s',value)
        for value in ('-1','2','NaN',False):
            with self.assertRaises(ValueError):model.Fault('f',value)
        for value in ('-1','2'):
            with self.assertRaises(ValueError):model.Exposure('f','c',value)
        for name in ('',' bad',None):
            with self.assertRaises(ValueError):model.Consumer(name,1)
        p=fixtures.overlap()
        for changes in (dict(faults=(model.Fault('f1',1),model.Fault('f2',1))),
                        dict(checks=p.checks+(p.checks[0],)),dict(exposures=p.exposures+(p.exposures[0],)),
                        dict(exposures=(model.Exposure('unknown','critical'),)),
                        dict(checks=(model.Check('q',['missing'],[]),)),
                        dict(checks=(model.Check('q',[],[('f2','bulk')]),))):
            with self.assertRaises(ValueError):replace(p,**changes)
        with self.assertRaises(ValueError):model.Check('q','shared',[])
        with self.assertRaises(ValueError):model.Check('q',[],['f1'])
        with self.assertRaises(ValueError):model.account(p,['missing'])
        with self.assertRaises(ValueError):model.account(p,['A','A'])


class PlannerTests(unittest.TestCase):
    def test_shared_bundle_counterexample_all_greedies(self):
        p=fixtures.shared_scan_trap()
        result=planner.exact(p,7)
        self.assertEqual((result['checks'],result['cost'],result['risk_reduction']),(('A','B'),7,16))
        for policy in planner.POLICIES[1:]:
            greedy=planner.solve(p,7,policy)
            self.assertEqual((greedy['checks'],greedy['risk_reduction']),(('C',),12))

    def test_exact_vs_separate_enumeration(self):
        for seed in range(8):
            p=fixtures.generated(seed,7)
            full=model.account(p,[c.id for c in p.checks])['cost']
            for budget in (0,full//3,full):
                expected=oracle.exhaustive(p,budget)
                actual=planner.exact(p,budget)
                self.assertEqual(actual['checks'],expected['checks'])
                self.assertEqual(actual['risk_reduction'],expected['risk_reduction'])
                for policy in planner.POLICIES[1:]:
                    r=planner.solve(p,budget,policy)
                    checked=oracle.measure(p,r['checks'])
                    self.assertEqual(r['cost'],checked['cost'])
                    self.assertEqual(r['risk_reduction'],checked['risk_reduction'])
                    self.assertLessEqual(r['cost'],budget)
                    self.assertLessEqual(r['risk_reduction'],expected['risk_reduction'])

    def test_oracle_does_not_use_optimized_accounting(self):
        p=fixtures.overlap()
        with patch.object(planner,'account',side_effect=AssertionError('not independent')):
            with patch.object(model.Problem,'weights',side_effect=AssertionError('shared weights')):
                self.assertEqual(oracle.exhaustive(p,F(6))['risk_reduction'],52)

    def test_free_checks_zero_risk_and_empty_instances(self):
        p=fixtures.overlap()
        free=replace(p,scans=(model.Scan('shared',0),),checks=tuple(replace(c,evaluation_cost=0) for c in p.checks))
        for policy in planner.POLICIES:
            result=planner.solve(free,0,policy)
            self.assertEqual(result['risk_reduction'],52)
            self.assertEqual(result['cost'],0)
            empty=planner.solve(model.Problem((),(),(),(),()),0,policy)
            self.assertEqual((empty['checks'],empty['risk_reduction'],empty['cost']),((),0,0))
        zero=replace(free,consumers=tuple(replace(c,loss=0) for c in free.consumers))
        self.assertEqual(planner.exact(zero,0)['checks'],())
        self.assertEqual(planner.greedy(zero,0)['checks'],())

    def test_fractional_budget_boundary_and_ties(self):
        p=model.Problem((model.Fault('f',1),),(model.Consumer('c',1),),(model.Exposure('f','c'),),(),
                        (model.Check('a',(),[('f','c')],'1/3'),model.Check('b',(),[('f','c')],'1/3')))
        for policy in planner.POLICIES:
            self.assertEqual(planner.solve(p,'1/3',policy)['checks'],('a',))
            self.assertEqual(planner.solve(p,'0.3333333333333333',policy)['checks'],())

    def test_recomputed_marginals_and_raw_coverage_policy(self):
        p=fixtures.overlap()
        for policy in planner.POLICIES:
            self.assertEqual(planner.solve(p,6,policy)['risk_reduction'],52)
        # The redundant check adds no gain and is never selected by greedy.
        for policy in planner.POLICIES[1:]:
            self.assertNotIn('redundant',planner.solve(p,100,policy)['checks'])

    def test_diminishing_utility_and_shared_cost_increment(self):
        p=fixtures.generated(17,6)
        for check in p.checks:
            for other in p.checks:
                if check.id==other.id:continue
                single=model.account(p,[check.id]);before=model.account(p,[other.id]);after=model.account(p,[check.id,other.id])
                self.assertLessEqual(after['risk_reduction']-before['risk_reduction'],single['risk_reduction'])
                self.assertLessEqual(after['cost']-before['cost'],single['cost'])

    def test_limits_and_invalid_policies(self):
        p=fixtures.overlap()
        for policy in planner.POLICIES:
            for value in (-1,True,'nan','inf'):
                with self.assertRaises(ValueError):planner.solve(p,value,policy)
        with self.assertRaises(ValueError):planner.solve(p,1,'unknown')
        with self.assertRaises(ValueError):planner.exact(fixtures.generated(1,21),1)

    def test_input_order_and_seed_repeatability(self):
        p=fixtures.generated(101,8)
        self.assertEqual(p,fixtures.generated(101,8))
        self.assertNotEqual(p,fixtures.generated(102,8))
        for policy in planner.POLICIES:
            self.assertEqual(planner.solve(p,15,policy),planner.solve(replace(p,checks=tuple(reversed(p.checks))),15,policy))


class CliTests(unittest.TestCase):
    def test_fixture_and_json_input_errors(self):
        command=[sys.executable,'-m','research.queryguard.overlap_v1']
        completed=subprocess.run(command+['--fixture','shared_scan_trap','--budget','7'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(completed.stdout)['risk_reduction'],'16')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'problem.json';path.write_text(json.dumps(fixtures.overlap().to_dict()))
            completed=subprocess.run(command+['--input',str(path),'--budget','6'],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(completed.stdout)['risk_reduction'],'52')
            path.write_text('{')
            bad=subprocess.run(command+['--input',str(path),'--budget','6'],capture_output=True,text=True)
            self.assertEqual(bad.returncode,2)
            self.assertEqual(json.loads(bad.stdout)['status'],'error')


class PolicyDistinctionTests(unittest.TestCase):
    def test_unweighted_coverage_vs_cost_and_risk(self):
        p=model.Problem((model.Fault('f',1),),
                        tuple(model.Consumer(c,100 if c=='important' else 1) for c in ('a','b','c','important')),
                        tuple(model.Exposure('f',c) for c in ('a','b','c','important')),(),
                        (model.Check('broad',(),[('f',c) for c in ('a','b','c')],4),
                         model.Check('small',(),[('f','important')],1)))
        self.assertEqual(planner.solve(p,4,'coverage_greedy')['checks'],('broad',))
        self.assertEqual(planner.solve(p,4,'cost_aware_greedy')['checks'],('small',))
        self.assertEqual(planner.solve(p,4,'risk_aware_greedy')['checks'],('small',))

    def test_exact_cost_cardinality_then_lexical_ties(self):
        p=fixtures.overlap()
        checks=(model.Check('A',(),[('f1','critical')],1),model.Check('B',(),[('f1','bulk')],1),
                model.Check('C',(),[('f1','critical'),('f1','bulk')],2),
                model.Check('D',(),[('f1','critical'),('f1','bulk')],3))
        p=replace(p,checks=checks)
        self.assertEqual(planner.exact(p,3)['checks'],('C',))
        with self.assertRaises(ValueError):model.account(p,'AB')
