import json
import tempfile
import unittest
from pathlib import Path

from phase648_cftc_russell_feature_pipeline import (
    BASELINE,
    EVENTS,
    MANIFEST,
    build_report,
    git_blob_sha,
    load_reference,
    midrank_percentile,
    parse_utc,
    prospective_russell_events,
)
from decimal import Decimal


class RussellFeaturePipelineTests(unittest.TestCase):
    def test_frozen_git_blob_identities(self):
        self.assertEqual(git_blob_sha(BASELINE), "4711abbaeeb6107d1cb8f50a7c2e3627373b6d29")
        self.assertEqual(git_blob_sha(MANIFEST), "9e58849093f2144ce8cfbf1d3e5efc626a1aa250")

    def test_reference_panel_has_exact_preregistered_coverage(self):
        values, audit = load_reference()
        self.assertEqual(len(values), 480)
        self.assertEqual(audit["all_contract_rows"], 3035)
        self.assertEqual(audit["russell_archive_rows"], 482)
        self.assertEqual(audit["excluded_dates"], ["2018-09-25", "2019-12-24"])
        self.assertEqual(audit["reference_first_date"], "2017-08-15")
        self.assertEqual(audit["reference_last_date"], "2026-11-03")
        self.assertFalse(audit["historical_rows_are_signal_eligible"])

    def test_midrank_uses_half_weight_for_ties(self):
        self.assertEqual(
            midrank_percentile([Decimal("1"), Decimal("2"), Decimal("2"), Decimal("3")], Decimal("2")),
            Decimal("0.5"),
        )

    def test_current_prospective_events_reproduce_phase647(self):
        report = build_report()
        by_date = {event["report_date"]: event for event in report["prospective_events"]}
        self.assertGreaterEqual(len(by_date), 2)
        self.assertAlmostEqual(by_date["2026-11-10"]["reference_percentile"], 0.40625, places=10)
        self.assertAlmostEqual(by_date["2026-11-17"]["reference_percentile"], 0.45416666666666666, places=10)
        self.assertFalse(by_date["2026-11-10"]["high_lm_crowding"])
        self.assertFalse(by_date["2026-11-17"]["high_lm_crowding"])

    def test_pipeline_never_claims_outcomes_or_signals(self):
        report = build_report()
        self.assertFalse(report["outcomes_accessed"])
        self.assertFalse(report["price_data_accessed"])
        self.assertEqual(report["signals_admitted"], 0)
        self.assertFalse(report["f80_changed"])

    def test_timezone_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            parse_utc("2026-11-18T03:44:57")

    def test_non_utc_offset_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            parse_utc("2026-11-18T04:44:57+01:00")

    def _copy_first_event(self, mutate):
        source = sorted(EVENTS.glob("*.json"))[0]
        payload = json.loads(source.read_text(encoding="utf-8"))
        for event in payload["events"]:
            if event.get("contract_code") == "239742":
                mutate(event)
                break
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        target = Path(temp.name) / source.name
        target.write_text(json.dumps(payload), encoding="utf-8")
        return Path(temp.name)

    def test_event_before_frozen_reference_knowledge_bound_rejected(self):
        directory = self._copy_first_event(
            lambda event: event.update({"first_seen_utc": "2026-11-13T23:59:59Z"})
        )
        with self.assertRaisesRegex(ValueError, "predates"):
            prospective_russell_events(directory)

    def test_tampered_source_row_hash_rejected(self):
        directory = self._copy_first_event(
            lambda event: event.update({"current_row_sha256": "0" * 64})
        )
        with self.assertRaisesRegex(ValueError, "source-row hash"):
            prospective_russell_events(directory)

    def test_duplicate_report_date_rejected(self):
        source = sorted(EVENTS.glob("*.json"))[0]
        payload = json.loads(source.read_text(encoding="utf-8"))
        russell = next(event for event in payload["events"] if event.get("contract_code") == "239742")
        duplicate = dict(russell)
        duplicate["first_seen_utc"] = "2026-11-18T04:00:00Z"
        payload["events"].append(duplicate)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        target = Path(temp.name) / source.name
        target.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate prospective"):
            prospective_russell_events(Path(temp.name))


if __name__ == "__main__":
    unittest.main()
