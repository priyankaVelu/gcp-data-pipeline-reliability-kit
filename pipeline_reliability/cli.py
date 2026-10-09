"""Command-line adapter with stable JSON envelopes and exit codes."""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

from .checks import check


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def parser():
    root = Parser(description="Detect silent data-quality failures in local CSV files.")
    commands = root.add_subparsers(dest="command", required=True, parser_class=Parser)
    for name in ("duplicate-keys", "null-keys", "freshness", "duplicate-current"):
        sub = commands.add_parser(name)
        source = sub.add_mutually_exclusive_group()
        source.add_argument("--csv", type=Path)
        source.add_argument("--synthetic", action="store_true", default=None)
        sub.add_argument("--config", type=Path, help="JSON object; CLI options override its values")
        if name == "freshness":
            sub.add_argument("--timestamp-column")
            sub.add_argument("--max-age-seconds", type=float)
            sub.add_argument("--now", help="Timezone-aware ISO 8601 reference time")
        else:
            sub.add_argument("--keys", nargs="+")
        if name == "duplicate-current":
            sub.add_argument("--current-column")
    return root


def synthetic():
    return [dict(id="a", event_ts="2026-01-01T00:00:00Z", is_current="true"),
            dict(id="a", event_ts="2026-01-01T01:00:00Z", is_current="true"),
            dict(id="", event_ts="2026-01-01T02:00:00Z", is_current="false")]


def load_csv(path, required):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        headers = reader.fieldnames
        if not headers or any(not name for name in headers) or len(set(headers)) != len(headers):
            raise ValueError("CSV needs nonempty, unique column headers")
        missing = set(required) - set(headers)
        if missing:
            raise ValueError("missing CSV columns: " + ", ".join(sorted(missing)))
        rows = []
        for index, row in enumerate(reader, 1):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"data row {index}: field count differs from header")
            rows.append(row)
        return rows


def main(argv=None):
    command = None
    try:
        args = vars(parser().parse_args(argv))
        command = args.pop("command")
        config_path = args.pop("config")
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path else {}
        if not isinstance(config, dict):
            raise ValueError("configuration must be a JSON object")
        allowed = set(args)
        if set(config) - allowed:
            raise ValueError("unknown configuration fields: " + ", ".join(sorted(set(config) - allowed)))
        if args.get("csv") is not None:
            config.pop("synthetic", None)
        if args.get("synthetic"):
            config.pop("csv", None)
        config.update({key: value for key, value in args.items() if value is not None})
        csv_path = config.pop("csv", None)
        use_synthetic = config.pop("synthetic", False)
        if not isinstance(use_synthetic, bool):
            raise ValueError("synthetic must be a boolean")
        if bool(csv_path) == use_synthetic:
            raise ValueError("choose exactly one source: --csv or --synthetic")
        keys = config.get("keys")
        if command != "freshness" and (not isinstance(keys, list) or not keys or
                any(not isinstance(key, str) or not key for key in keys)):
            raise ValueError("keys must be a nonempty list of column names")
        if command == "freshness":
            limit = config.get("max_age_seconds")
            if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit < 0:
                raise ValueError("max_age_seconds must be a finite nonnegative number")
        required = list(keys or [])
        for field in ("timestamp_column", "current_column"):
            if field in args:
                value = config.get(field)
                if not isinstance(value, str) or not value:
                    raise ValueError(f"{field} is required")
                required.append(value)
        rows = synthetic() if use_synthetic else load_csv(Path(csv_path), required)
        if use_synthetic and set(required) - set(rows[0]):
            raise ValueError("synthetic columns are id, event_ts, is_current")
        result = check(rows, command, **config)
        output = {"schema_version": "1.0", "command": command,
                  "status": "pass" if result["passed"] else "fail", "result": result}
        code = 0 if result["passed"] else 1
    except (ValueError, TypeError, OSError, csv.Error, KeyError) as exc:
        output = {"schema_version": "1.0", "command": command, "status": "error", "error": str(exc)}
        code = 2
    print(json.dumps(output, allow_nan=False))
    return code
