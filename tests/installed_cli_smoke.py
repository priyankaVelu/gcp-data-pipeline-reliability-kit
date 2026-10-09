"""Run with the wheel environment's Python from outside the checkout."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pipeline_reliability


def main():
    checkout = Path(__file__).resolve().parents[1]
    installed = Path(pipeline_reliability.__file__).resolve()
    if checkout in installed.parents:
        raise AssertionError(f"package imported from checkout: {installed}")
    executable = Path(sys.executable).with_name('pipeline-reliability')
    count = 0
    with tempfile.TemporaryDirectory() as directory:
        cwd = Path(directory)
        source = cwd / 'data.csv'
        source.write_text('id,is_current\na,true\n" ",false\n')
        config = cwd / 'config.json'
        config.write_text(json.dumps(dict(csv=str(source), keys=['id'], strict=True)))
        cases = [
            (['duplicate-keys', '--csv', str(source), '--keys', 'id'], 0),
            (['duplicate-keys', '--csv', str(source), '--keys', 'id', '--strict'], 1),
            (['duplicate-current', '--csv', str(source), '--keys', 'id', '--current-column', 'is_current'], 0),
            (['duplicate-current', '--csv', str(source), '--keys', 'id', '--current-column', 'is_current', '--strict'], 1),
            (['duplicate-keys', '--config', str(config), '--no-strict'], 0),
            (['null-keys', '--csv', str(source), '--keys', 'id'], 1),
            (['freshness', '--synthetic', '--timestamp-column', 'event_ts', '--max-age-seconds', '3600', '--now', '2026-01-01T02:30:00Z'], 0),
            (['freshness', '--synthetic', '--timestamp-column', 'event_ts', '--max-age-seconds', '3600', '--now', 'invalid'], 2),
            (['null-keys', '--csv', str(source), '--keys', 'missing'], 2),
        ]
        for args, expected in cases:
            result = subprocess.run([str(executable), *args], cwd=cwd, capture_output=True, text=True)
            assert result.returncode == expected, (args, result)
            assert not result.stderr, result.stderr
            output = json.loads(result.stdout)
            assert output['schema_version'] == '1.0', output
            assert output['command'] == args[0], output
            assert output['status'] == {0: 'pass', 1: 'fail', 2: 'error'}[expected], output
            count += 1
    print(f'Installed wheel outside checkout: {count} scenarios passed')


if __name__ == '__main__':
    main()
