import unittest
from datetime import datetime, timezone, timedelta
from reliability_kit import deduplicate_events, validate_business_key, bounded_backfill, freshness_age_seconds, audit_record

UTC=timezone.utc
class ReliabilityKitTests(unittest.TestCase):
    def test_duplicate_replay_is_idempotent(self):
        events=[{"event_id":"a"},{"event_id":"b"},{"event_id":"a"}]
        clean,n=deduplicate_events(events)
        self.assertEqual([e["event_id"] for e in clean],["a","b"])
        self.assertEqual(n,1)

    def test_null_business_key_detection(self):
        events=[{"customer_id":"1"},{"customer_id":None},{"customer_id":""}]
        self.assertEqual(validate_business_key(events,"customer_id"),[1,2])

    def test_bounded_backfill(self):
        start=datetime(2026,1,1,tzinfo=UTC); end=start+timedelta(days=1)
        events=[{"event_ts":start},{"event_ts":end-timedelta(seconds=1)},{"event_ts":end}]
        self.assertEqual(len(bounded_backfill(events,start,end)),2)

    def test_backfill_rejects_bad_window(self):
        t=datetime(2026,1,1,tzinfo=UTC)
        with self.assertRaises(ValueError): bounded_backfill([],t,t)

    def test_freshness_is_deterministic(self):
        now=datetime(2026,1,1,12,tzinfo=UTC)
        self.assertEqual(freshness_age_seconds(now-timedelta(minutes=5),now),300)

    def test_audit_record(self):
        r=audit_record(pipeline="synthetic",run_id="r1",status="SUCCEEDED",processed=10,duplicates=2)
        self.assertEqual((r["processed"],r["duplicates"]),(10,2))

if __name__=="__main__": unittest.main()
