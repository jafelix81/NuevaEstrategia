from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.phase665_form144_accession_pit_plan_date_join import (
    PIT_FIELDS,
    build_summary,
)


def make_detail(accession: str, *, plan_dates: list[str], research: bool, baseline: bool = False) -> dict[str, str]:
    status = "INITIAL_BASELINE_NO_LOWER_BOUND" if baseline else "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"
    return {
        "accession": accession,
        "plan_adoption_dates_json": json.dumps(plan_dates),
        "form": "144",
        "issuer_cik": "0000000001",
        "issuer_name": "Example Issuer",
        "seller_name": "Example Seller",
        "notice_date_iso": "2026-11-19",
        "remarks": "",
        "mentions_10b5_1_in_remarks": "False",
        "research_observation_eligible": str(research),
        "public_availability_certified": "False",
        "signal_eligible": "False",
        "first_seen_interval_status": status,
        "first_seen_interval_lower_bound_utc": "" if baseline else "2026-11-18T20:00:00Z",
        "first_seen_interval_upper_bound_utc": "2026-11-19T20:00:00Z",
    }


def make_event(detail: dict[str, str]) -> dict[str, str]:
    return {field: detail[field] for field in ("accession", *PIT_FIELDS)}


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class Phase665Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.events_path = self.root / "events.csv"
        self.details_path = self.root / "sale_details.csv"

        a = make_detail("A", plan_dates=["06/01/2026"], research=True)
        b = make_detail("B", plan_dates=["06/02/2026"], research=False, baseline=True)
        c = make_detail("C", plan_dates=[], research=True)
        d = make_detail("D", plan_dates=[], research=True)

        details = [a, dict(a), b, c]
        events = [make_event(a), make_event(b), make_event(c), make_event(d)]
        write_csv(self.details_path, details, list(details[0]))
        write_csv(self.events_path, events, ["accession", *PIT_FIELDS])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_exact_accession_join_counts_filing_grain_and_event_only_rows(self) -> None:
        summary = build_summary(self.events_path, self.details_path)
        counts = summary["counts"]
        self.assertEqual(counts["structured_detail_accessions"], 3)
        self.assertEqual(counts["research_observation_eligible_accessions"], 2)
        self.assertEqual(counts["initial_baseline_no_lower_bound_accessions"], 1)
        self.assertEqual(counts["formal_plan_date_accessions"], 2)
        self.assertEqual(counts["formal_plan_date_and_research_observation_eligible_accessions"], 1)
        self.assertEqual(counts["formal_plan_date_and_initial_baseline_accessions"], 1)
        self.assertEqual(counts["event_accessions_without_structured_details"], 1)
        self.assertEqual(counts["structured_detail_accessions_without_event"], 0)
        self.assertEqual(summary["integrity"]["crossledger_pit_mismatches"], 0)

    def test_conflicting_plan_dates_within_accession_fail_closed(self) -> None:
        rows = list(csv.DictReader(self.details_path.open(encoding="utf-8")))
        rows[1]["plan_adoption_dates_json"] = json.dumps(["06/03/2026"])
        write_csv(self.details_path, rows, list(rows[0]))
        with self.assertRaisesRegex(ValueError, "inconsistent_plan_adoption_dates_json"):
            build_summary(self.events_path, self.details_path)

    def test_crossledger_pit_mismatch_fails_closed(self) -> None:
        rows = list(csv.DictReader(self.events_path.open(encoding="utf-8")))
        rows[0]["research_observation_eligible"] = "False"
        write_csv(self.events_path, rows, ["accession", *PIT_FIELDS])
        with self.assertRaisesRegex(ValueError, "crossledger_pit_mismatch"):
            build_summary(self.events_path, self.details_path)

    def test_invalid_boolean_fails_closed(self) -> None:
        rows = list(csv.DictReader(self.details_path.open(encoding="utf-8")))
        rows[0]["signal_eligible"] = "unknown"
        write_csv(self.details_path, rows, list(rows[0]))
        with self.assertRaisesRegex(ValueError, "invalid_boolean_signal_eligible"):
            build_summary(self.events_path, self.details_path)

    def test_malformed_plan_date_json_fails_closed(self) -> None:
        rows = list(csv.DictReader(self.details_path.open(encoding="utf-8")))
        rows[0]["plan_adoption_dates_json"] = "{not-json"
        rows[1]["plan_adoption_dates_json"] = "{not-json"
        write_csv(self.details_path, rows, list(rows[0]))
        with self.assertRaisesRegex(ValueError, "invalid_plan_adoption_dates_json"):
            build_summary(self.events_path, self.details_path)


if __name__ == "__main__":
    unittest.main()
