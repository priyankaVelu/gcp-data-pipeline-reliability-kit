"""Deterministic synthetic experiment runner. Writes machine-generated JSON results."""
import json, platform, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reliability_kit import deduplicate_events, validate_business_key, bounded_backfill

UTC=timezone.utc
events=[
 {"event_id":"e1","customer_id":"c1","event_ts":datetime(2026,1,1,0,0,tzinfo=UTC)},
 {"event_id":"e2","customer_id":None,"event_ts":datetime(2026,1,1,1,0,tzinfo=UTC)},
 {"event_id":"e1","customer_id":"c1","event_ts":datetime(2026,1,1,2,0,tzinfo=UTC)},
]
clean,duplicates=deduplicate_events(events)
null_indexes=validate_business_key(events,"customer_id")
window=bounded_backfill(events,datetime(2026,1,1,tzinfo=UTC),datetime(2026,1,2,tzinfo=UTC))
try: commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
except Exception: commit="unknown"
result={"schema_version":"1.0","generated_at":datetime.now(UTC).isoformat(),
 "commit_sha":commit,"python":platform.python_version(),"dataset":"synthetic-v1",
 "input_rows":len(events),"unique_rows":len(clean),"duplicate_events_detected":duplicates,
 "null_business_keys_detected":len(null_indexes),"bounded_window_rows":len(window)}
out=Path(__file__).parent/"results"/"raw"/"synthetic-v1.json"
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
