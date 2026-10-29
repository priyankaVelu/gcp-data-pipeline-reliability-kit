from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from research.queryguard.overlap_v1 import fixtures,model,oracle,planner as v1
from research.queryguard.bundle_v1.planner import bundle_greedy
from research.queryguard.bundle_v1.scenarios import no_sharing,triple_trap


def direct_bundle(problem,budget,k):
    """Slow independently costed lookahead, without Prepared or optimized scoring."""
    selected=()
    candidates_examined=0
    while True:
        before=oracle.measure(problem,selected)
        remaining=sorted(c.id for c in problem.checks if c.id not in selected)
        candidates=[]
        for size in range(1,min(k,len(remaining))+1):
            for bundle in combinations(remaining,size):
                candidates_examined+=1
                after=oracle.measure(problem,selected+bundle)
                cost=after['cost']-before['cost']
                gain=after['risk_reduction']-before['risk_reduction']
                if after['cost']>budget or gain<=0:continue
                score=(int(cost==0),gain/cost if cost else gain,gain,-cost,-size)
                candidates.append((score,bundle))
        if not candidates:break
        best_score=max(score for score,_ in candidates)
        chosen=min(bundle for score,bundle in candidates if score==best_score)
        selected+=chosen
    return tuple(sorted(selected)),candidates_examined


class BundleTests(unittest.TestCase):
    def test_original_shared_and_overlap_fixtures(self):
        for k in (2,3):
            r=bundle_greedy(fixtures.shared_scan_trap(),7,k)
            self.assertEqual((r['checks'],r['cost'],r['risk_reduction']),(('A','B'),7,16))
            self.assertEqual(r['steps'][0]['marginal_cost'],7)
            self.assertEqual(bundle_greedy(fixtures.overlap(),6,k)['risk_reduction'],52)

    def test_pair_insufficient_for_triple_fixture(self):
        p=triple_trap()
        self.assertEqual(bundle_greedy(p,8,2)['risk_reduction'],15)
        r=bundle_greedy(p,8,3)
        self.assertEqual((r['checks'],r['risk_reduction'],r['cost']),(('A','B','C'),24,8))
        self.assertEqual(oracle.exhaustive(p,8)['risk_reduction'],24)
        # A coverage baseline also solves this designed case; no universal claim.
        self.assertEqual(v1.solve(p,8,'coverage_greedy')['risk_reduction'],24)

    def test_direct_local_oracle_and_exact_bounds(self):
        for seed in range(5):
            source=fixtures.generated(seed,7)
            for p in (source,no_sharing(source)):
                for budget in (0,7,15):
                    exact=oracle.exhaustive(p,budget)
                    for k in (1,2,3):
                        result=bundle_greedy(p,budget,k)
                        names,work=direct_bundle(p,budget,k)
                        self.assertEqual((result['checks'],result['examined']),(names,work))
                        self.assertEqual(result['risk_reduction'],oracle.measure(p,names)['risk_reduction'])
                        self.assertLessEqual(result['cost'],budget)
                        self.assertLessEqual(result['risk_reduction'],exact['risk_reduction'])

    def test_singleton_equivalence(self):
        for seed in range(8):
            p=fixtures.generated(seed,8)
            for budget in (0,7,20,100):
                a=bundle_greedy(p,budget,1);b=v1.solve(p,budget,'risk_aware_greedy')
                for key,value in b.items():self.assertEqual(a[key],value)

    def test_private_scans_preserve_singleton_and_additive_joint_costs(self):
        source=fixtures.generated(7,6)
        p=no_sharing(source)
        for size in range(7):
            for names in combinations([c.id for c in p.checks],size):
                expected=sum((oracle.measure(source,[x])['cost'] for x in names),F())
                self.assertEqual(oracle.measure(p,names)['cost'],expected)
                self.assertGreaterEqual(expected,oracle.measure(source,names)['cost'])
        self.assertEqual(source,fixtures.generated(7,6))
        for k in (2,3):
            self.assertEqual(bundle_greedy(no_sharing(fixtures.shared_scan_trap()),7,k)['risk_reduction'],12)
            self.assertEqual(bundle_greedy(no_sharing(triple_trap()),8,k)['risk_reduction'],15)

    def test_union_multi_group_costs_steps_and_ties(self):
        p=fixtures.overlap()
        p=replace(p,scans=p.scans+(model.Scan('extra',2),),checks=tuple(replace(c,scans=('extra','shared')) for c in p.checks))
        r=bundle_greedy(p,8,3)
        self.assertEqual((r['risk_reduction'],r['cost']),(52,8))
        selected=()
        for step in r['steps']:
            before=oracle.measure(p,selected);selected+=step['bundle'];after=oracle.measure(p,selected)
            self.assertEqual(step['marginal_cost'],after['cost']-before['cost'])
            self.assertEqual(step['marginal_risk'],after['risk_reduction']-before['risk_reduction'])
        tie=model.Problem((model.Fault('f',1),),(model.Consumer('c',1),),(model.Exposure('f','c'),),(),
                          (model.Check('a',(),[('f','c')],'1/3'),model.Check('b',(),[('f','c')],'1/3')))
        self.assertEqual(bundle_greedy(tie,F(1,3),3)['checks'],('a',))
        self.assertEqual(bundle_greedy(tie,'0.3333333333333333',3)['checks'],())

    def test_free_empty_zero_risk_and_input_order(self):
        p=fixtures.overlap()
        free=replace(p,scans=(model.Scan('shared',0),),checks=tuple(replace(c,evaluation_cost=0) for c in p.checks))
        for k in (1,2,3):
            self.assertEqual(bundle_greedy(free,0,k)['risk_reduction'],52)
            self.assertEqual(bundle_greedy(model.Problem((),(),(),(),()),0,k)['checks'],())
            zero=replace(free,consumers=tuple(replace(c,loss=0) for c in free.consumers))
            self.assertEqual(bundle_greedy(zero,0,k)['checks'],())
            self.assertEqual(bundle_greedy(p,6,k),bundle_greedy(replace(p,checks=tuple(reversed(p.checks))),6,k))

    def test_invalid_controls_and_cli(self):
        for k in (0,4,-1,True,'2',None):
            with self.assertRaises(ValueError):bundle_greedy(fixtures.overlap(),6,k)
        for budget in (-1,True,'nan','inf'):
            with self.assertRaises(ValueError):bundle_greedy(fixtures.overlap(),budget,2)
        result=subprocess.run([sys.executable,'-m','research.queryguard.bundle_v1','--fixture','triple_trap','--budget','8','--k','3'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['risk_reduction'],'24')

    def test_oracle_independence(self):
        p=triple_trap()
        with patch.object(v1,'account',side_effect=AssertionError('optimized accounting')):
            with patch.object(model.Problem,'weights',side_effect=AssertionError('optimized weights')):
                self.assertEqual(oracle.exhaustive(p,8)['risk_reduction'],24)
