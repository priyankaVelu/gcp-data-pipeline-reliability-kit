"""Pure checks; row numbers refer to CSV data records, starting at one."""
from collections import Counter
from datetime import datetime, timezone
import math

from reliability_kit import freshness_age_seconds, validate_business_key


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("timestamps must be ISO 8601 with a timezone") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return result


def check(rows, command, *, keys=None, timestamp_column=None,
          max_age_seconds=None, now=None, current_column=None, strict=False):
    if not rows:
        return {"passed": False, "rows_checked": 0, "reason": "empty_dataset"}
    if command == "freshness":
        if max_age_seconds is None or not math.isfinite(max_age_seconds) or max_age_seconds < 0:
            raise ValueError("max_age_seconds must be a finite nonnegative number")
        reference = timestamp(now) if now is not None else datetime.now(timezone.utc)
        times = []
        for index, row in enumerate(rows, 1):
            try:
                times.append(timestamp(row[timestamp_column]))
            except ValueError as exc:
                raise ValueError(f"data row {index}: {exc}") from exc
        latest = max(times)
        age = freshness_age_seconds(latest, reference)
        return {"passed": 0 <= age <= max_age_seconds, "rows_checked": len(rows),
                "latest_timestamp": latest.isoformat(), "age_seconds": age,
                "max_age_seconds": max_age_seconds,
                "future_timestamp_count": sum(t > reference for t in times)}
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("provide one or more distinct keys")
    normalized = [{key: row[key].strip() for key in keys} for row in rows]
    nulls = sorted(set(i for key in keys for i in validate_business_key(normalized, key)))
    if command == "null-keys":
        return {"passed": not nulls, "rows_checked": len(rows),
                "invalid_rows": len(nulls), "row_numbers": [i + 1 for i in nulls[:20]]}
    selected = normalized
    if command == "duplicate-current":
        selected = []
        for index, row in enumerate(rows):
            flag = row[current_column].strip().lower()
            if flag not in {"true", "false", "1", "0"}:
                raise ValueError(f"data row {index + 1}: current flag must be true, false, 1, or 0")
            if flag in {"true", "1"}:
                selected.append(normalized[index])
    counts = Counter(tuple(row[key] for key in keys) for row in selected
                     if all(row[key] != "" for key in keys))
    duplicates = [count for count in counts.values() if count > 1]
    return {"passed": not duplicates and (not strict or not nulls), "rows_checked": len(rows),
            "strict": strict, "invalid_key_rows": len(nulls),
            "selected_rows": len(selected), "duplicate_groups": len(duplicates),
            "duplicate_rows": sum(duplicates),
            "excess_rows": sum(count - 1 for count in duplicates),
            "null_key_rows_excluded": sum(any(row[key] == "" for key in keys) for row in selected)}
