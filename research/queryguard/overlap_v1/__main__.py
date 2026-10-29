"""Plan a supplied JSON instance or a deterministic fixture."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from .fixtures import overlap, shared_scan_trap
from .model import Problem, number
from .planner import POLICIES, solve


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input',type=Path)
    source.add_argument('--fixture',choices=('overlap','shared_scan_trap'))
    parser.add_argument('--budget',required=True)
    parser.add_argument('--policy',choices=POLICIES,default='exact')
    args = parser.parse_args(argv)
    try:
        problem = Problem.from_dict(json.loads(args.input.read_text())) if args.input else (overlap() if args.fixture == 'overlap' else shared_scan_trap())
        budget = number(args.budget,'budget')
        result = solve(problem,budget,args.policy)
        print(json.dumps(dict(schema_version='1.0',status='planned',policy=args.policy,budget=str(budget),
                              feasible=result['cost'] <= budget,**result),
                         default=lambda x:str(x) if isinstance(x,Fraction) else x,sort_keys=True))
        return 0
    except (ValueError,TypeError,OSError) as exc:
        print(json.dumps(dict(schema_version='1.0',status='error',error=str(exc))))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
