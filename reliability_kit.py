"""Dependency-free reference reliability controls for reproducible experiments."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any

def deduplicate_events(events: Iterable[Mapping[str, Any]], key: str = "event_id"):
    """Keep first event per non-null key; return (clean, duplicate_count)."""
    seen=set(); clean=[]; duplicates=0
    for event in events:
        value=event.get(key)
        if value is None:
            clean.append(dict(event)); continue
        if value in seen:
            duplicates += 1; continue
        seen.add(value); clean.append(dict(event))
    return clean, duplicates

def validate_business_key(events: Iterable[Mapping[str, Any]], key: str):
    """Return indexes whose business key is null or empty."""
    return [i for i,e in enumerate(events) if e.get(key) in (None, "")]

def bounded_backfill(events: Iterable[Mapping[str, Any]], start: datetime, end: datetime, timestamp_key: str="event_ts"):
    """Select events in [start,end); reject invalid/unbounded windows."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must be timezone-aware")
    if start >= end:
        raise ValueError("start must be before end")
    return [dict(e) for e in events if start <= e[timestamp_key] < end]

def freshness_age_seconds(latest_event_ts: datetime, now: datetime | None=None):
    """Age of latest event, suitable for a freshness threshold assertion."""
    if latest_event_ts.tzinfo is None:
        raise ValueError("latest_event_ts must be timezone-aware")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return (now-latest_event_ts).total_seconds()

def audit_record(*, pipeline: str, run_id: str, status: str, processed: int, duplicates: int=0):
    """Create a minimal machine-readable audit record."""
    if status not in {"SUCCEEDED","FAILED"}:
        raise ValueError("unsupported status")
    return {"pipeline":pipeline,"run_id":run_id,"status":status,
            "processed":processed,"duplicates":duplicates}
