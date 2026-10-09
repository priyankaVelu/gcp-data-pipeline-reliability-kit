# Five-minute quickstart

Python 3.10 or newer is required. No cloud credentials or runtime packages are needed.
From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
pipeline-reliability --help
pipeline-reliability duplicate-keys --csv examples/cli/events.csv --keys id
pipeline-reliability null-keys --synthetic --keys id
pipeline-reliability duplicate-current --csv examples/cli/events.csv --keys id --current-column is_current
pipeline-reliability freshness --config examples/cli/freshness.json
```

The first three checks intentionally exit **1**: the fictional fixture contains two
current records for `a` and one empty key. The freshness example exits **0** using
a fixed reference time. Omit `--now` to use the current UTC clock.

For development use `python -m pip install -e .`, then
`python -m unittest discover -s tests -v`. Additional research validation runs with
`python research/test_paper_experiments_v4.py` and
`python research/test_paper_experiments_v5.py`.

## Commands and semantics

| Command | Required options | Failure condition |
| --- | --- | --- |
| `duplicate-keys` | `--keys id [other_key ...]` | More than one row per non-null composite key |
| `null-keys` | `--keys id [other_key ...]` | Any key is empty or whitespace |
| `freshness` | `--timestamp-column ts --max-age-seconds N` | Latest timestamp exceeds N seconds of age, or is in the future |
| `duplicate-current` | `--keys id --current-column flag` | More than one current row per non-null composite key |

Choose `--csv PATH` or `--synthetic`. CSV must have unique, nonempty headers and
consistent field counts. UTF-8 (including BOM), quoted fields, and composite keys
are supported. Key values are case-sensitive strings with surrounding whitespace
trimmed. Literal `NULL` is a string, not a null marker. Duplicate checks exclude
empty keys and report their count; run `null-keys` separately to enforce completeness.
Current flags accept `true`, `false`, `1`, `0` (case-insensitive). Other flags are input
errors. Timestamps must be timezone-aware ISO 8601; offsets and `Z` are supported.
Every timestamp is validated, not just the latest. The freshness boundary is inclusive.
An empty dataset fails every check rather than silently passing.

## JSON and automation

Every check emits one JSON object on stdout, including errors:

```json
{"schema_version":"1.0","command":"duplicate-keys","status":"fail","result":{"passed":false,"rows_checked":3,"selected_rows":3,"duplicate_groups":1,"duplicate_rows":2,"excess_rows":1,"null_key_rows_excluded":1}}
```

Exit codes: **0** check passed, **1** data-quality failure, **2** input/configuration
error. Errors include `status: "error"` and an `error` message. Help exits 0 and
prints ordinary help text. Null-check samples contain at most 20 data-record
numbers, starting at 1 (excluding the header). Results do not include raw key values.

`--config FILE` accepts a JSON object using option names with underscores, for example
`csv`, `keys`, `timestamp_column`, `max_age_seconds`, `now`, and `current_column`.
Only fields valid for that command are accepted. Explicit CLI options override
configuration values. Paths are relative to the current working directory.
See `examples/cli/duplicate-keys.json` and `examples/cli/freshness.json`.

This initial implementation loads the CSV in memory. It provides local checks,
not a cloud connector or a guarantee that a pipeline is correct. Full research
matrices are separate from CLI validation; no performance claims are made.
