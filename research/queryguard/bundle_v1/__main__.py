"""Inspect a bounded bundle plan on a JSON instance or a deterministic fixture."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from ..overlap_v1.model import Problem
from .planner import bundle_greedy
from .scenarios import fixtures,no_sharing


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--fixture',choices=tuple(fixtures()))
    source.add_argument('--input',type=Path)
    parser.add_argument('--budget',required=True)
    parser.add_argument('--k',type=int,choices=(1,2,3),default=2)
    parser.add_argument('--cost-model',choices=('shared','no_sharing'),default='shared')
    args=parser.parse_args(argv)
    try:
        problem=Problem.from_dict(json.loads(args.input.read_text())) if args.input else fixtures()[args.fixture][0]
        if args.cost_model=='no_sharing':problem=no_sharing(problem)
        result=bundle_greedy(problem,args.budget,args.k)
        print(json.dumps(dict(schema_version='1.0',status='planned',cost_model=args.cost_model,**result),
                         default=lambda value:str(value) if isinstance(value,Fraction) else value,sort_keys=True))
        return 0
    except (ValueError,TypeError,OSError) as exc:
        print(json.dumps(dict(schema_version='1.0',status='error',error=str(exc))))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
