from __future__ import annotations
import json
import tempfile
import unittest
import csv
from unittest.mock import patch
from pathlib import Path
from research import phase525_form4_reporting_owner_identity as p

XML = b"""<ownershipDocument>
<issuer><issuerCik><value>0001593899</value></issuerCik><issuerName><value>Atea Pharmaceuticals, Inc.</value></issuerName></issuer>
<reportingOwner><reportingOwnerId><rptOwnerCik><value>0001508458</value></rptOwnerCik><rptOwnerName><value>Bruce Polsky</value></rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isDirector><value>1</value></isDirector></reportingOwnerRelationship></reportingOwner>
<remarks>Sale transactions were executed to pay the exercise price of options for tax planning purposes.</remarks>
</ownershipDocument>"""
MULTI = b"""<ownershipDocument><issuer/><reportingOwner><reportingOwnerId><rptOwnerCik><value>0001508458</value></rptOwnerCik><rptOwnerName><value>Bruce Polsky</value></rptOwnerName></reportingOwnerId></reportingOwner><reportingOwner><reportingOwnerId><rptOwnerCik><value>0001829622</value></rptOwnerCik><rptOwnerName><value>Bruno Lucidi</value></rptOwnerName></reportingOwnerId></reportingOwner></ownershipDocument>"""

class Phase525OwnerIdentityTests(unittest.TestCase):
    def test_single_owner_is_filing_grain_only(self):
        parsed = p.parse_owner_identity(XML)
        self.assertEqual(parsed["reporting_owner_count"], 1)
        self.assertEqual(parsed["owners"][0]["owner_cik"], "0001508458")
        self.assertEqual(parsed["owners"][0]["owner_name"], "Bruce Polsky")
        self.assertTrue(parsed["remarks_flags"]["exercise_price_payment_mention"])
        self.assertTrue(parsed["remarks_flags"]["tax_planning_mention"])

    def test_multi_owner_never_gets_transaction_line_link(self):
        parsed = p.parse_owner_identity(MULTI)
        rows = p.build_owner_rows({"accession":"0000123456-26-000001","form":"4"}, {}, parsed)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(x["line_owner_link_status"] == "MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK" for x in rows))
        self.assertTrue(all(x["transaction_line_attribution_verified"] is False for x in rows))

    def test_scheduled_backfill_uses_bounded_parsed_accessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accession = "0000123456-26-000001"
            event = {
                "accession": accession, "form": "4", "feed_name": "4",
                "filing_url": f"https://www.sec.gov/Archives/edgar/data/123456/{accession.replace('-', '')}/{accession}-index.htm",
                "filing_date": "2026-11-19", "first_seen_at_utc": "2026-11-20T10:00:00Z",
                "first_seen_interval_lower_bound_utc": "2026-11-20T01:00:00Z",
                "first_seen_interval_upper_bound_utc": "2026-11-20T10:00:00Z",
                "first_seen_interval_status": "BOUNDED_METADATA_ONLY",
                "first_seen_poll_run_id": "12345", "capture_mode": "schedule",
                "first_seen_is_upper_bound_not_exact_receipt": "True",
            }
            events_path = root / "events.csv"
            with events_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(event))
                writer.writeheader()
                writer.writerow(event)
            details_path = root / "transaction_details.csv"
            with details_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["accession", "detail_type", "parse_status"])
                writer.writeheader()
                writer.writerow({"accession": accession, "detail_type": "filing_header", "parse_status": "parsed"})
            metadata = {"fetch_status": "retrieved", "xml": XML, "xml_sha256": "abc"}
            with patch.object(p.p510, "fetch_document", return_value=metadata) as fetch:
                summary = p.run_backfill("schedule", 10, root / "out", events_path, details_path, root / "reporting_owners.csv")
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(summary["accessions_parsed"], 1)
            self.assertEqual(summary["single_owner_accessions"], 1)
            self.assertEqual(summary["remaining_bounded_accessions"], 0)

    def test_manual_mode_does_not_fetch_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = p.run_backfill("manual", 10, Path(tmp) / "out", Path(tmp) / "events.csv", Path(tmp) / "details.csv", Path(tmp) / "owners.csv")
            self.assertEqual(summary["disposition"], "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE")
            self.assertFalse((Path(tmp) / "owners.csv").exists())

if __name__ == "__main__":
    unittest.main()
