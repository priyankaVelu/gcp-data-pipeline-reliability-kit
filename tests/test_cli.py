import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pipeline_reliability.checks import check, timestamp
from pipeline_reliability.cli import main


class CheckTests(unittest.TestCase):
    def test_composite_duplicates_and_null_exclusion(self):
        rows = [dict(a='x', b='1'), dict(a='x', b='2'), dict(a='x', b='1'), dict(a='', b='1')]
        result = check(rows, 'duplicate-keys', keys=['a', 'b'])
        self.assertFalse(result['passed'])
        self.assertEqual((result['duplicate_groups'], result['duplicate_rows'], result['excess_rows']), (1, 2, 1))
        self.assertEqual(result['null_key_rows_excluded'], 1)

    def test_null_whitespace_and_sample_bound(self):
        result = check([dict(id='  ')] * 30, 'null-keys', keys=['id'])
        self.assertEqual(result['invalid_rows'], 30)
        self.assertEqual(result['row_numbers'], list(range(1, 21)))

    def test_current_history_and_flags(self):
        rows = [dict(id='a', current='true'), dict(id='a', current='false')]
        self.assertTrue(check(rows, 'duplicate-current', keys=['id'], current_column='current')['passed'])
        rows[1]['current'] = '1'
        self.assertFalse(check(rows, 'duplicate-current', keys=['id'], current_column='current')['passed'])
        rows[1]['current'] = 'yes'
        with self.assertRaisesRegex(ValueError, 'data row 2'):
            check(rows, 'duplicate-current', keys=['id'], current_column='current')

    def test_freshness_boundaries(self):
        rows = [dict(ts='2026-01-01T01:00:00+01:00')]
        for reference, expected in [('2026-01-01T01:00:00Z', True), ('2026-01-01T01:00:01Z', False), ('2025-12-31T23:59:59Z', False)]:
            self.assertEqual(check(rows, 'freshness', timestamp_column='ts', max_age_seconds=3600, now=reference)['passed'], expected)
        for limit in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                check(rows, 'freshness', timestamp_column='ts', max_age_seconds=limit)
        for value in ['2026-01-01', 'garbage', '']:
            with self.assertRaises(ValueError):
                timestamp(value)

    def test_empty_fails(self):
        self.assertFalse(check([], 'null-keys', keys=['id'])['passed'])


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        return code, json.loads(output.getvalue())

    def test_all_synthetic_commands(self):
        for command in ['duplicate-keys', 'null-keys']:
            code, output = self.invoke(command, '--synthetic', '--keys', 'id')
            self.assertEqual(code, 1)
            self.assertEqual(output['status'], 'fail')
        self.assertEqual(self.invoke('duplicate-current', '--synthetic', '--keys', 'id', '--current-column', 'is_current')[0], 1)
        self.assertEqual(self.invoke('freshness', '--synthetic', '--timestamp-column', 'event_ts', '--max-age-seconds', '3600', '--now', '2026-01-01T02:30:00Z')[0], 0)

    def test_csv_and_config(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / 'data.csv'
            csv.write_text('\ufeffid,name\n1,"fictional, person"\n2,other\n', encoding='utf-8')
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps(dict(csv=str(csv), keys=['id'])))
            self.assertEqual(self.invoke('duplicate-keys', '--config', str(config))[0], 0)
            self.assertEqual(self.invoke('null-keys', '--csv', str(csv), '--keys', 'missing')[0], 2)
            for content in ['id,id\na,b\n', 'id\na,b\n', 'id,name\na\n', 'id\n"unclosed\n', '']:
                csv.write_text(content)
                code, output = self.invoke('null-keys', '--csv', str(csv), '--keys', 'id')
                self.assertEqual(code, 2, content)
                self.assertEqual(output['status'], 'error')
            csv.write_text('id\n')
            self.assertEqual(self.invoke('null-keys', '--csv', str(csv), '--keys', 'id')[0], 1)

    def test_invalid_arguments_and_configuration(self):
        for args in [[], ['unknown'], ['null-keys', '--synthetic'], ['null-keys', '--csv', '/nonexistent', '--keys', 'id'], ['freshness', '--synthetic', '--timestamp-column', 'event_ts', '--max-age-seconds', 'nan']]:
            self.assertEqual(self.invoke(*args)[0], 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            for content in ['{', '[]', '{"unknown":1}', '{"synthetic": "true", "keys":["id"]}']:
                path.write_text(content)
                self.assertEqual(self.invoke('null-keys', '--config', str(path))[0], 2)

    def test_module_subprocess_exit_and_json(self):
        result = subprocess.run([sys.executable, '-m', 'pipeline_reliability', 'duplicate-keys', '--synthetic', '--keys', 'id'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['result']['duplicate_groups'], 1)
        self.assertEqual(result.stderr, '')
