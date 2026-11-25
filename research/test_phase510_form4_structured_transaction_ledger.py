from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from research import phase510_form4_structured_transaction_ledger as p

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
  <documentType>4</documentType>
  <periodOfReport>2026-11-18</periodOfReport>
  <issuer>
    <issuerCik><value>0000123456</value></issuerCik>
    <issuerName><value>Example Corp</value></issuerName>
    <issuerTradingSymbol><value>EXM</value></issuerTradingSymbol>
  </issuer>
  <reportingOwner><reportingOwnerId><rptOwnerCik><value>0000000001</value></rptOwnerCik></reportingOwnerId></reportingOwner>
  <reportingOwner><reportingOwnerId><rptOwnerCik><value>0000000002</value></rptOwnerCik></reportingOwnerId></reportingOwner>
  <aff10b5One><value>0</value></aff10b5One>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Class A Common Stock</value></securityTitle>
      <transactionDate><value>2026-11-17</value></transactionDate>
      <transactionCoding>
        <transactionFormType><value>4</value></transactionFormType>
        <transactionCode><value>P</value></transactionCode>
        <equitySwapInvolved><value>0</value></equitySwapInvolved>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1,250</value></transactionShares>
        <transactionPricePerShare><value>12.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts>
        <sharesOwnedFollowingTransaction><value>10,000</value></sharesOwnedFollowingTransaction>
      </postTransactionAmounts>
      <ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
      <footnoteId id="F1"/>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <securityTitle><value>Class A Common Stock</value></securityTitle>
      <transactionDate><value>2026-11-17</value></transactionDate>
      <transactionCoding><transactionCode><value>S</value></transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>100</value></transactionShares>
        <transactionPricePerShare><value>12.00</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <ownershipNature><directOrIndirectOwnership><value>I</value></directOrIndirectOwnership></ownershipNature>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
  <derivativeTable>
    <derivativeTransaction>
      <securityTitle><value>Employee Stock Option</value></securityTitle>
      <conversionOrExercisePrice><value>5.00</value></conversionOrExercisePrice>
      <exerciseDate><value>2027-01-01</value></exerciseDate>
      <expirationDate><value>2030-01-01</value></expirationDate>
      <underlyingSecurity>
        <underlyingSecurityTitle><value>Class A Common Stock</value></underlyingSecurityTitle>
        <underlyingSecurityShares><value>500</value></underlyingSecurityShares>
      </underlyingSecurity>
      <transactionCoding><transactionCode><value>M</value></transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>500</value></transactionShares>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </derivativeTransaction>
  </derivativeTable>
  <footnotes>
    <footnote id="F1">Open market purchase; footnote mentions Rule 10b5-1.</footnote>
  </footnotes>
</ownershipDocument>
"""

XML_FOOTNOTE_LINKS = b"""<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
  <documentType>4</documentType>
  <periodOfReport>2026-11-20</periodOfReport>
  <issuer>
    <issuerCik><value>0001647639</value></issuerCik>
    <issuerName><value>Upstart Holdings, Inc.</value></issuerName>
    <issuerTradingSymbol><value>UPST</value></issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerCik><value>0000000001</value></rptOwnerCik></reportingOwnerId>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2026-11-20</value></transactionDate>
      <transactionCoding><transactionCode><value>P</value></transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>60000</value></transactionShares>
        <transactionPricePerShare>
          <value>15.8498</value>
          <footnoteId id="F3"/>
        </transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <ownershipNature>
        <directOrIndirectOwnership><value>I</value></directOrIndirectOwnership>
        <natureOfOwnership>
          <value>By trust</value>
          <footnoteId id="F4"/>
        </natureOfOwnership>
        <footnoteId id="F5"/>
      </ownershipNature>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
  <footnotes>
    <footnote id="F3">Weighted average price across multiple purchases from 15.76 to 15.95.</footnote>
    <footnote id="F4">Shares are held by the 2008 D&amp;T Girouard Revocable Trust.</footnote>
    <footnote id="F5">A prior transfer between trusts was made for no consideration.</footnote>
  </footnotes>
</ownershipDocument>
"""


def event(accession="0000123456-26-000001", form="4", status="BOUNDED_METADATA_ONLY"):
    return {
        "accession": accession,
        "form": form,
        "feed_name": "4",
        "feed_path_cik_unverified": "0000123456",
        "filing_url": f"https://www.sec.gov/Archives/edgar/data/123456/{accession.replace('-', '')}/{accession}-index.htm",
        "filing_date": "2026-11-18",
        "first_seen_at_utc": "2026-11-19T10:27:00Z",
        "first_seen_interval_lower_bound_utc": "2026-11-19T01:54:00Z",
        "first_seen_interval_upper_bound_utc": "2026-11-19T10:27:00Z",
        "first_seen_interval_status": status,
        "first_seen_poll_run_id": "12345",
        "capture_mode": "schedule",
        "first_seen_poll_started_utc": "2026-11-19T10:26:55Z",
        "first_seen_poll_ended_utc": "2026-11-19T10:27:01Z",
        "first_seen_is_upper_bound_not_exact_receipt": "True",
    }


class Phase510Tests(unittest.TestCase):
    def test_parses_non_derivative_and_derivative_rows_separately(self):
        parsed = p.parse_form4_details(XML)
        self.assertEqual(parsed["issuer_cik"], "0000123456")
        self.assertEqual(parsed["issuer_trading_symbol_normalized"], "EXM")
        self.assertEqual(parsed["reporting_owner_count"], 2)
        self.assertEqual(parsed["owner_attribution_status"], "QUARANTINED_MULTI_OWNER_NO_LINE_LINK")
        self.assertEqual(parsed["aff10b5one_filing_flag"], "no")
        self.assertEqual(parsed["nonderivative_transaction_count"], 2)
        self.assertEqual(parsed["derivative_transaction_count"], 1)
        self.assertEqual(len(parsed["transaction_rows"]), 3)
        self.assertEqual(parsed["transaction_rows"][0]["transaction_code"], "P")
        self.assertEqual(parsed["transaction_rows"][0]["acquired_disposed_code"], "A")
        self.assertEqual(parsed["transaction_rows"][0]["shares_numeric"], "1250")
        self.assertEqual(parsed["transaction_rows"][0]["price_per_share_numeric"], "12.5")
        self.assertTrue(json.loads(parsed["transaction_rows"][0]["footnote_flags_json"])["open_market_mention"])
        self.assertTrue(json.loads(parsed["transaction_rows"][0]["footnote_flags_json"])["rule_10b5_1_mention"])
        self.assertEqual(parsed["transaction_rows"][2]["table_type"], "derivative")
        self.assertEqual(parsed["transaction_rows"][2]["conversion_exercise_price_numeric"], "5")

    def test_p_code_is_preserved_without_claiming_exchange_execution(self):
        parsed = p.parse_form4_details(XML)
        row = parsed["transaction_rows"][0]
        self.assertEqual(row["transaction_code"], "P")
        self.assertNotIn("is_open_market_trade", row)
        self.assertNotIn("confirmed_exchange_execution", row)

    def test_build_rows_preserves_clocks_and_never_promotes_signal(self):
        parsed = p.parse_form4_details(XML)
        metadata = {
            "detail_retrieved_at_utc": "2026-11-19T22:00:00Z",
            "acceptance_datetime_utc": "2026-11-18T20:00:00Z",
            "acceptance_clock_status": "PARSED_NOT_EXACT_PUBLIC_AVAILABILITY",
            "submission_status": "retrieved",
            "xml_source": "complete_submission",
            "submission_sha256": "sub",
            "xml_sha256": "xml",
        }
        rows = p.build_detail_rows(event(), metadata, parsed)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["detail_type"], "filing_header")
        self.assertEqual(rows[1]["detail_type"], "transaction_row")
        self.assertEqual(rows[1]["first_seen_at_utc"], "2026-11-19T10:27:00Z")
        self.assertEqual(rows[1]["detail_retrieved_at_utc"], "2026-11-19T22:00:00Z")
        self.assertEqual(rows[1]["first_seen_interval_lower_bound_utc"], "2026-11-19T01:54:00Z")
        self.assertTrue(all(row["signal_eligible"] is False for row in rows))
        self.assertTrue(all(row["research_observation_eligible"] is False for row in rows))
        self.assertTrue(all(row["public_availability_certified"] is False for row in rows))
        self.assertTrue(all(row["same_day_intraday_use_authorized"] is False for row in rows))
        self.assertTrue(all(row["owner_attribution_verified"] is False for row in rows))

    def test_amendment_is_information_arrival_not_new_trade(self):
        parsed = p.parse_form4_details(XML)
        rows = p.build_detail_rows(event(form="4/A"), {"detail_retrieved_at_utc": "2026-11-19T22:00:00Z"}, parsed)
        self.assertTrue(all(row["is_amendment"] is True for row in rows))
        self.assertTrue(all(row["economic_event_new_trade_authorized"] is False for row in rows))

    def test_invalid_numeric_and_date_fields_remain_missing(self):
        raw = b"""<ownershipDocument><issuer><issuerCik><value>0000000001</value></issuerCik></issuer>
        <nonDerivativeTable><nonDerivativeTransaction>
        <transactionDate><value>not-a-date</value></transactionDate>
        <transactionAmounts><transactionShares><value>N/A</value></transactionShares></transactionAmounts>
        </nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>"""
        parsed = p.parse_form4_details(raw)
        row = parsed["transaction_rows"][0]
        self.assertIsNone(row["transaction_date"])
        self.assertIsNone(row["shares_numeric"])

    def test_reversed_or_naive_first_seen_interval_fails_closed(self):
        bad = event()
        bad["first_seen_interval_lower_bound_utc"] = "2026-11-19T11:00:00Z"
        with self.assertRaisesRegex(ValueError, "clock_invalid"):
            p.validate_event(bad)
        bad = event()
        bad["first_seen_at_utc"] = "2026-11-19T10:27:00"
        bad["first_seen_interval_upper_bound_utc"] = "2026-11-19T10:27:00"
        with self.assertRaisesRegex(ValueError, "clock_invalid"):
            p.validate_event(bad)

    def test_wrong_root_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "root"):
            p.parse_form4_details(b"<root/>")

    def test_append_is_idempotent_and_header_marks_completion(self):
        parsed = p.parse_form4_details(XML)
        metadata = {"detail_retrieved_at_utc": "2026-11-19T22:00:00Z", "xml_sha256": "abc"}
        rows = p.build_detail_rows(event(), metadata, parsed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transaction_details.csv"
            self.assertEqual(p.append_detail_rows(path, rows), len(rows))
            self.assertEqual(p.append_detail_rows(path, rows), 0)
            self.assertIn(event()["accession"], p.read_completed_accessions(path))
            with path.open("r", newline="", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual(len(stored), len(rows))

    def test_new_parser_version_can_reprocess_prior_quarantined_accession(self):
        parsed = p.parse_form4_details(XML)
        current_rows = p.build_detail_rows(event(), {"detail_retrieved_at_utc": "2026-11-19T22:00:00Z"}, parsed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transaction_details.csv"
            old_rows = [dict(row) for row in current_rows]
            for row in old_rows:
                row["parser_version"] = "phase510-v0"
                row["detail_row_key"] = "old-" + row["detail_row_key"]
            self.assertEqual(p.append_detail_rows(path, old_rows), len(old_rows))
            self.assertNotIn(event()["accession"], p.read_completed_accessions(path))
            self.assertEqual(p.append_detail_rows(path, current_rows), len(current_rows))
            self.assertIn(event()["accession"], p.read_completed_accessions(path))

    def test_backfill_only_uses_bounded_events_and_is_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.csv"
            details_path = root / "transaction_details.csv"
            out = root / "out"
            rows = [event("0000123456-26-000001"), event("0000123456-26-000002", status="INITIAL_BASELINE_NO_LOWER_BOUND")]
            with events_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            submission = b"<SEC-DOCUMENT>\n<XML>" + XML + b"</XML>\n</SEC-DOCUMENT>"
            calls = []
            def fake_fetch(url):
                calls.append(url)
                return submission
            summary = p.run_backfill(
                "schedule", 1, out, events_path, details_path, fake_fetch,
                root / "footnote_references.csv",
            )
            self.assertEqual(summary["attempted_accessions"], 1)
            self.assertEqual(summary["accessions_parsed"], 1)
            self.assertEqual(summary["remaining_bounded_accessions"], 0)
            self.assertEqual(len(calls), 1)
            summary2 = p.run_backfill(
                "schedule", 1, out, events_path, details_path, fake_fetch,
                root / "footnote_references.csv",
            )
            self.assertEqual(summary2["attempted_accessions"], 0)

    def test_manual_mode_never_fetches_or_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            summary = p.run_backfill("manual", 10, root / "out", root / "missing.csv", root / "details.csv",
                                     lambda url: calls.append(url))
            self.assertEqual(calls, [])
            self.assertEqual(summary["disposition"], "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE")
            self.assertFalse((root / "details.csv").exists())


    def test_transaction_footnote_references_preserve_field_path_and_hash_mapping(self):
        parsed = p.parse_form4_details(XML_FOOTNOTE_LINKS)
        refs = parsed["transaction_rows"][0]["footnote_references"]
        self.assertEqual([item["footnote_id"] for item in refs], ["F3", "F4", "F5"])
        self.assertIn("transactionamounts[1].transactionpricepershare[1]", refs[0]["xml_field_path"])
        self.assertIn("ownershipnature[1].natureofownership[1]", refs[1]["xml_field_path"])
        self.assertIn("ownershipnature[1]", refs[2]["xml_field_path"])
        expected = [
            "Weighted average price across multiple purchases from 15.76 to 15.95.",
            "Shares are held by the 2008 D&T Girouard Revocable Trust.",
            "A prior transfer between trusts was made for no consideration.",
        ]
        import hashlib
        self.assertEqual(
            [item["footnote_text_sha256"] for item in refs],
            [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in expected],
        )
        self.assertTrue(all(item["reference_resolution_status"] == "RESOLVED" for item in refs))

    def test_footnote_sidecar_links_refs_to_transaction_detail_and_is_idempotent(self):
        parsed = p.parse_form4_details(XML_FOOTNOTE_LINKS)
        metadata = {
            "submission_sha256": "submission-hash",
            "xml_sha256": "xml-hash",
            "xml_source": "complete_submission",
            "acceptance_datetime_utc": "2026-11-20T20:21:55Z",
            "detail_retrieved_at_utc": "2026-11-23T07:48:52Z",
        }
        detail_rows = p.build_detail_rows(event(), metadata, parsed)
        sidecar_rows = p.build_footnote_reference_rows(event(), metadata, parsed)
        self.assertEqual(len(sidecar_rows), 4)
        self.assertEqual(sidecar_rows[0]["record_type"], "accession_parse_marker")
        self.assertEqual(sidecar_rows[0]["reference_resolution_status"], "PARSED_WITH_FOOTNOTE_REFERENCES")
        tx_detail = next(row for row in detail_rows if row["detail_type"] == "transaction_row")
        self.assertTrue(all(row["detail_row_key"] == tx_detail["detail_row_key"] for row in sidecar_rows[1:]))
        self.assertEqual([row["footnote_id"] for row in sidecar_rows[1:]], ["F3", "F4", "F5"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "footnote_references.csv"
            self.assertEqual(p.append_footnote_reference_rows(path, sidecar_rows), 4)
            self.assertEqual(p.append_footnote_reference_rows(path, sidecar_rows), 0)
            with path.open("r", newline="", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual(stored[-1]["record_type"], "accession_parse_marker")
            self.assertEqual(
                sum(row["record_type"] == "footnote_reference" for row in stored), 3
            )
            self.assertIn(event()["accession"], p.read_completed_footnote_accessions(path))

    def test_footnote_sidecar_recovers_partial_reference_append_without_marker(self):
        parsed = p.parse_form4_details(XML_FOOTNOTE_LINKS)
        metadata = {
            "submission_sha256": "submission-hash",
            "xml_sha256": "xml-hash",
            "xml_source": "complete_submission",
            "detail_retrieved_at_utc": "2026-11-23T07:48:52Z",
        }
        rows = p.build_footnote_reference_rows(event(), metadata, parsed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "footnote_references.csv"
            # Simulate a prior interrupted append that left one complete reference
            # row but no accession completion marker.
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=p.FOOTNOTE_REF_FIELDS)
                writer.writeheader()
                writer.writerow(rows[1])
            self.assertNotIn(event()["accession"], p.read_completed_footnote_accessions(path))
            self.assertEqual(p.append_footnote_reference_rows(path, rows), 3)
            self.assertIn(event()["accession"], p.read_completed_footnote_accessions(path))
            with path.open("r", newline="", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual(
                sum(row["record_type"] == "footnote_reference" for row in stored), 3
            )
            self.assertEqual(stored[-1]["record_type"], "accession_parse_marker")

    def test_footnote_reference_backfill_reprocesses_existing_parsed_accessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.csv"
            details_path = root / "transaction_details.csv"
            sidecar_path = root / "footnote_references.csv"
            out = root / "out"
            evt = event()
            with events_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(evt))
                writer.writeheader()
                writer.writerow(evt)
            metadata = {
                "detail_retrieved_at_utc": "2026-11-23T07:48:52Z",
                "acceptance_datetime_utc": "2026-11-20T20:21:55Z",
                "acceptance_clock_status": "PARSED_NOT_EXACT_PUBLIC_AVAILABILITY",
                "submission_status": "retrieved",
                "xml_source": "complete_submission",
                "submission_sha256": "submission-hash",
                "xml_sha256": "xml-hash",
            }
            p.append_detail_rows(details_path, p.build_detail_rows(evt, metadata, p.parse_form4_details(XML_FOOTNOTE_LINKS)))
            submission = b"<SEC-DOCUMENT>\n<XML>" + XML_FOOTNOTE_LINKS + b"</XML>\n</SEC-DOCUMENT>"
            calls = []
            def fake_fetch(url):
                calls.append(url)
                return submission
            summary = p.run_footnote_reference_backfill(
                "schedule", 1, out, events_path, details_path, sidecar_path, fake_fetch
            )
            self.assertEqual(summary["attempted_accessions"], 1)
            self.assertEqual(summary["accessions_parsed"], 1)
            self.assertEqual(summary["footnote_reference_rows_appended"], 4)
            self.assertEqual(summary["remaining_footnote_accessions"], 0)
            self.assertEqual(len(calls), 1)
            with details_path.open("r", newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), len(p.build_detail_rows(evt, metadata, p.parse_form4_details(XML_FOOTNOTE_LINKS))))

    def test_footnote_reference_backfill_manual_mode_never_fetches_or_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            summary = p.run_footnote_reference_backfill(
                "manual", 10, root / "out", root / "events.csv",
                root / "details.csv", root / "footnotes.csv",
                lambda url: calls.append(url),
            )
            self.assertEqual(calls, [])
            self.assertEqual(summary["disposition"], "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE")
            self.assertFalse((root / "footnotes.csv").exists())

    def test_parse_error_does_not_write_footnote_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evt = event()
            events_path = root / "events.csv"
            with events_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(evt))
                writer.writeheader()
                writer.writerow(evt)
            submission = b"<SEC-DOCUMENT>\\n<XML><notOwnershipDocument/></XML>\\n</SEC-DOCUMENT>"
            summary = p.run_backfill(
                "schedule", 1, root / "out", events_path, root / "details.csv",
                lambda url: submission, root / "footnotes.csv",
            )
            self.assertEqual(summary["accessions_with_parse_error"], 1)
            self.assertEqual(summary["footnote_reference_rows_appended"], 0)
            self.assertFalse((root / "footnotes.csv").exists())

    def test_footnote_sidecar_schema_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "footnote_references.csv"
            path.write_text("accession,footnote_id\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "header_mismatch"):
                p.append_footnote_reference_rows(path, [{
                    "footnote_ref_key": "x", "accession": "0000123456-26-000001"
                }])


if __name__ == "__main__":
    unittest.main()
