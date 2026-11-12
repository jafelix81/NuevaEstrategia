import unittest

from research.phase334_sec_stratified_symbol_class_coverage import (
    build_fresh_document_manifest,
    classify_anchor_observation,
)


def observation(pair="P01", side="A", event="2024-01-01", anchor="2023-01-01",
                truncated=False, shard_errors=0, submissions="OK"):
    return {
        "pair_id": pair, "side": side, "issuer_cik": "100",
        "event_date": event, "prior_periodic_filed_date": anchor,
        "event_window_truncated": truncated, "shard_errors": shard_errors,
        "submissions_status": submissions,
    }


def filing(accession="a1", pair="P01", side="A", cik="100", filed="2023-06-01",
           event="2024-01-01", digest="a" * 64, symbols=None):
    return {
        "accession": accession, "pair_id": pair, "side": side,
        "issuer_cik": cik, "ticker_candidate": "ABC", "event_date": event,
        "filing_date": filed, "form": "8-K", "primary_document": "event.htm",
        "document_sha256": digest,
        "trading_symbols": ["ABC"] if symbols is None else symbols,
    }


class Phase334Tests(unittest.TestCase):
    def test_exactly_365_calendar_days_is_fresh(self):
        got = classify_anchor_observation(observation())
        self.assertEqual(got["anchor_age_days"], 365)
        self.assertEqual(got["anchor_status"], "FRESH_COMPLETE")

    def test_366_calendar_days_is_stale(self):
        got = classify_anchor_observation(
            observation(event="2024-01-01", anchor="2022-12-31")
        )
        self.assertEqual(got["anchor_age_days"], 366)
        self.assertEqual(got["anchor_status"], "STALE_ANCHOR")

    def test_missing_anchor_is_not_zero_or_fresh(self):
        got = classify_anchor_observation(observation(anchor=""))
        self.assertEqual(got["anchor_status"], "NO_VALID_PRIOR_PERIODIC_ANCHOR")

    def test_anchor_on_or_after_event_is_invalid(self):
        self.assertEqual(
            classify_anchor_observation(observation(anchor="2024-01-01"))["anchor_status"],
            "INVALID_ANCHOR_CHRONOLOGY",
        )
        self.assertEqual(
            classify_anchor_observation(observation(anchor="2024-01-02"))["anchor_status"],
            "INVALID_ANCHOR_CHRONOLOGY",
        )

    def test_truncated_fresh_window_is_incomplete(self):
        got = classify_anchor_observation(observation(truncated=True))
        self.assertEqual(got["anchor_status"], "INCOMPLETE_TRUNCATED_EVENT_WINDOW")

    def test_shard_errors_block_fresh_admission(self):
        got = classify_anchor_observation(observation(shard_errors=1))
        self.assertEqual(got["anchor_status"], "INCOMPLETE_SHARD_ERRORS")

    def test_unavailable_submissions_block_fresh_admission(self):
        got = classify_anchor_observation(observation(submissions="HTTP_404"))
        self.assertEqual(got["anchor_status"], "INCOMPLETE_SUBMISSIONS")

    def test_same_accession_cofiler_rows_collapse_only_after_identical_signature(self):
        observations = [
            observation("P01", "A"),
            observation("P01", "B"),
        ]
        rows = [
            filing(accession="shared", pair="P01", side="A", cik="100"),
            filing(accession="shared", pair="P01", side="B", cik="200"),
        ]
        result = build_fresh_document_manifest(observations, rows)
        self.assertEqual(len(result["documents"]), 1)
        doc = result["documents"][0]
        self.assertEqual(doc["accession"], "shared")
        self.assertEqual(doc["cofiler_duplicate_rows"], 1)
        self.assertEqual(len(doc["source_contexts"]), 2)
        self.assertEqual(result["summary"]["cofiler_duplicate_rows_collapsed"], 1)

    def test_accession_hash_conflict_is_quarantined_not_deduplicated(self):
        observations = [
            observation("P01", "A"),
            observation("P01", "B"),
        ]
        rows = [
            filing(accession="shared", pair="P01", side="A", cik="100", digest="a" * 64),
            filing(accession="shared", pair="P01", side="B", cik="200", digest="b" * 64),
        ]
        result = build_fresh_document_manifest(observations, rows)
        self.assertEqual(result["documents"], [])
        self.assertEqual(len(result["quarantines"]), 1)
        self.assertEqual(
            result["quarantines"][0]["reason"],
            "COFILER_DOCUMENT_HASH_OR_SCHEMA_CONFLICT",
        )

    def test_stale_observation_rows_are_excluded_even_when_document_has_symbol(self):
        observations = [observation(event="2024-01-01", anchor="2022-12-31")]
        rows = [filing()]
        result = build_fresh_document_manifest(observations, rows)
        self.assertEqual(result["documents"], [])
        self.assertEqual(
            result["rejected_event_rows"]["outside_fresh_complete_anchor"], 1
        )

    def test_same_day_and_post_event_filings_are_excluded(self):
        observations = [observation()]
        rows = [
            filing(accession="same", filed="2024-01-01"),
            filing(accession="after", filed="2024-01-02"),
        ]
        result = build_fresh_document_manifest(observations, rows)
        self.assertEqual(result["documents"], [])
        self.assertEqual(
            result["rejected_event_rows"]["invalid_or_non_pre_event_filing_date"], 2
        )

    def test_missing_symbol_or_hash_is_not_admitted(self):
        observations = [observation()]
        rows = [
            filing(accession="no-symbol", symbols=[]),
            filing(accession="no-hash", digest=""),
        ]
        result = build_fresh_document_manifest(observations, rows)
        self.assertEqual(result["documents"], [])
        self.assertEqual(result["rejected_event_rows"]["no_trading_symbol_fact"], 1)
        self.assertEqual(result["rejected_event_rows"]["missing_or_invalid_document_hash"], 1)

    def test_fresh_gate_counts_are_mutually_exclusive(self):
        observations = [
            observation("P01", "A"),
            observation("P02", "A", anchor="2022-12-31"),
            observation("P03", "A", anchor=""),
            observation("P04", "A", truncated=True),
        ]
        result = build_fresh_document_manifest(observations, [])
        s = result["summary"]
        accounted = (
            s["fresh_complete_anchor_observations"]
            + s["stale_anchor_observations"]
            + s["no_valid_prior_anchor_observations"]
            + s["invalid_anchor_chronology_observations"]
            + s["incomplete_observations"]
        )
        self.assertEqual(accounted, len(observations))
        self.assertEqual(s["fresh_complete_anchor_observations"], 1)


if __name__ == "__main__":
    unittest.main()
