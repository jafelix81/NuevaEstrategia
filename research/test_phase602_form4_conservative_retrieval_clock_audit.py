import unittest

from research.phase602_form4_conservative_retrieval_clock_audit import (
    audit_ledgers,
    evaluate_detail,
)


ACCESSION = "0000000123-26-000001"


def sample_event():
    return {
        "accession": ACCESSION,
        "capture_mode": "schedule",
        "first_seen_interval_status": "BOUNDED_METADATA_ONLY",
        "first_seen_is_upper_bound_not_exact_receipt": "True",
        "event_metadata_interval_bounded": "True",
        "first_seen_poll_run_id": "123456",
        "first_seen_interval_lower_bound_utc": "2026-11-24T10:00:00Z",
        "first_seen_interval_upper_bound_utc": "2026-11-24T11:00:00Z",
        "first_seen_at_utc": "2026-11-24T11:00:00Z",
        "feed_updated_utc": "2026-11-24T10:30:00Z",
    }


def sample_detail():
    return {
        "accession": ACCESSION,
        "detail_type": "transaction_row",
        "first_seen_interval_status": "BOUNDED_METADATA_ONLY",
        "first_seen_is_upper_bound_not_exact_receipt": "True",
        "first_seen_poll_run_id": "123456",
        "first_seen_interval_upper_bound_utc": "2026-11-24T11:00:00Z",
        "first_seen_at_utc": "2026-11-24T11:00:00Z",
        "detail_retrieved_at_utc": "2026-11-24T11:00:02Z",
        "acceptance_datetime_utc": "2026-11-24T08:00:00Z",
        "parse_status": "parsed",
        "parse_error": "",
        "xml_source": "complete_submission",
        "xml_sha256": "a" * 64,
        "submission_sha256": "b" * 64,
        "filing_url": (
            "https://www.sec.gov/Archives/edgar/data/123/"
            "000000012326000001/0000000123-26-000001-index.htm"
        ),
        "research_observation_eligible": "False",
        "signal_eligible": "False",
    }


class Phase602ConservativeRetrievalClockTests(unittest.TestCase):
    def test_valid_detail_uses_retrieval_not_acceptance_clock(self):
        result = evaluate_detail(sample_detail(), sample_event())
        self.assertTrue(result["eligible"], result["reasons"])
        self.assertEqual(
            result["knowledge_time_upper_bound_utc"],
            "2026-11-24T11:00:02Z",
        )

    def test_unbounded_event_is_rejected(self):
        event = sample_event()
        event["first_seen_interval_status"] = "INITIAL_BASELINE_NO_LOWER_BOUND"
        detail = sample_detail()
        detail["first_seen_interval_status"] = event["first_seen_interval_status"]
        result = evaluate_detail(detail, event)
        self.assertFalse(result["eligible"])
        self.assertIn("first_seen_interval_not_bounded", result["reasons"])

    def test_retrieval_before_first_seen_upper_bound_is_rejected(self):
        detail = sample_detail()
        detail["detail_retrieved_at_utc"] = "2026-11-24T10:59:59Z"
        result = evaluate_detail(detail, sample_event())
        self.assertFalse(result["eligible"])
        self.assertIn("detail_retrieved_before_first_seen_upper_bound", result["reasons"])

    def test_missing_source_hash_is_rejected(self):
        detail = sample_detail()
        detail["xml_sha256"] = ""
        result = evaluate_detail(detail, sample_event())
        self.assertFalse(result["eligible"])
        self.assertIn("xml_sha256_missing_or_invalid", result["reasons"])

    def test_parse_error_is_rejected(self):
        detail = sample_detail()
        detail["parse_status"] = "parse_error"
        detail["parse_error"] = "malformed_xml"
        result = evaluate_detail(detail, sample_event())
        self.assertFalse(result["eligible"])
        self.assertIn("detail_parse_not_clean", result["reasons"])

    def test_accession_mismatched_sec_url_is_rejected(self):
        detail = sample_detail()
        detail["filing_url"] = (
            "https://www.sec.gov/Archives/edgar/data/123/"
            "000000099926000001/0000000999-26-000001-index.htm"
        )
        result = evaluate_detail(detail, sample_event())
        self.assertFalse(result["eligible"])
        self.assertIn("filing_url_accession_mismatch", result["reasons"])

    def test_missing_poll_run_id_is_rejected(self):
        event = sample_event()
        event["first_seen_poll_run_id"] = ""
        detail = sample_detail()
        detail["first_seen_poll_run_id"] = ""
        result = evaluate_detail(detail, event)
        self.assertFalse(result["eligible"])
        self.assertIn("poll_run_id_missing", result["reasons"])

    def test_duplicate_event_accession_fails_closed(self):
        event = sample_event()
        detail = sample_detail()
        summary = audit_ledgers([event, dict(event)], [detail])
        self.assertEqual(summary["form4"]["retrieval_clock_candidate_rows"], 0)
        self.assertEqual(summary["form4"]["duplicate_event_accessions"], [ACCESSION])
        self.assertEqual(summary["disposition"], "REVIEW_REQUIRED")

    def test_acceptance_time_is_not_used_for_eligibility(self):
        detail = sample_detail()
        detail["acceptance_datetime_utc"] = "2026-11-24T07:00:00Z"
        result = evaluate_detail(detail, sample_event())
        self.assertTrue(result["eligible"], result["reasons"])
        self.assertEqual(
            result["knowledge_time_upper_bound_utc"],
            detail["detail_retrieved_at_utc"],
        )


if __name__ == "__main__":
    unittest.main()
