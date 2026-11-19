from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from research.phase496_form4_accession_payload_semantics_audit import (
    audit_events,
    extract_ownership_xml,
    load_events,
    normalize_flag,
    parse_form4_xml,
    process_event,
)


FORM4_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument xmlns="http://www.sec.gov/edgar/ownership">
  <documentType>4</documentType>
  <periodOfReport>2026-11-18</periodOfReport>
  <issuer>
    <issuerCik>1234567</issuerCik>
    <issuerName>Example Holdings Inc.</issuerName>
    <issuerTradingSymbol>ACME</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerCik>7654321</rptOwnerCik><rptOwnerName>Example Person</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>1</isDirector><isOfficer>0</isOfficer>
      <isTenPercentOwner>0</isTenPercentOwner><isOther>0</isOther>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2026-11-18</value></transactionDate>
      <transactionCoding><transactionCode><value>P</value></transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>100</value></transactionShares>
        <transactionPricePerShare><value>12.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionCoding><transactionCode><value>S</value></transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>20</value></transactionShares>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
  <derivativeTable/>
  <aff10b5One>1</aff10b5One>
</ownershipDocument>
"""

INDEX_HTML = b"""<html><body>Filing Date 2026-11-18 Accepted 2026-11-18 16:10:00</body></html>"""
SUBMISSION = (
    b"ACCESSION NUMBER: 0000001000-26-000001\n"
    b"CONFORMED SUBMISSION TYPE: 4\n"
    b"ACCEPTANCE-DATETIME: 20261118161000\n"
    b"<DOCUMENT><TYPE>4</TYPE><TEXT><XML>"
    + FORM4_XML
    + b"</XML></TEXT></DOCUMENT>"
)


def event_row():
    return {
        "accession": "0000001000-26-000001",
        "form": "4",
        "filing_date": "2026-11-18",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/1000/000000100026000001/0000001000-26-000001-index.htm",
        "feed_path_cik_unverified": "0000001000",
        "feed_updated_utc": "2026-11-18T21:11:00Z",
        "first_seen_at_utc": "2026-11-18T21:20:00Z",
        "first_seen_interval_lower_bound_utc": "2026-11-18T21:00:00Z",
        "first_seen_interval_status": "BOUNDED_METADATA_ONLY",
        "first_seen_poll_run_id": "44440313382",
        "first_seen_is_upper_bound_not_exact_receipt": "True",
    }


class Phase496Tests(unittest.TestCase):
    def test_extracts_ownership_xml_from_complete_submission(self):
        raw = b"<SEC-HEADER>header</SEC-HEADER><XML>" + FORM4_XML + b"</XML>"
        extracted = extract_ownership_xml(raw)
        self.assertIsNotNone(extracted)
        parsed = parse_form4_xml(extracted)
        self.assertEqual(parsed["issuer_cik"], "0001234567")
        self.assertEqual(parsed["issuer_symbol"], "ACME")

    def test_transaction_semantics_and_owner_count_are_filing_grain(self):
        parsed = parse_form4_xml(FORM4_XML)
        self.assertEqual(parsed["owner_count"], 1)
        self.assertEqual(parsed["p_acquired_rows"], 1)
        self.assertEqual(parsed["transaction_code_acquired_disposed_counts"], {"P/A": 1, "S/D": 1})
        self.assertEqual(parsed["aff10b5one"], "yes")
        self.assertEqual(parsed["owner_role_counts"]["isDirector"], 1)

    def test_missing_10b5_flag_is_unknown_not_false(self):
        xml = FORM4_XML.replace(b"<aff10b5One>1</aff10b5One>", b"")
        self.assertEqual(parse_form4_xml(xml)["aff10b5one"], "unknown")
        self.assertEqual(normalize_flag(None), "unknown")

    def test_multi_owner_filing_is_not_expanded_to_owner_trades(self):
        xml = FORM4_XML.replace(b"</reportingOwner>", b"</reportingOwner><reportingOwner><reportingOwnerRelationship/></reportingOwner>", 1)
        parsed = parse_form4_xml(xml)
        self.assertEqual(parsed["owner_count"], 2)
        self.assertEqual(parsed["p_acquired_rows"], 1)

    def test_index_and_header_acceptance_reconcile_and_receipt_is_upper_bound(self):
        event = event_row()
        def fetcher(url):
            if url.endswith("-index.htm"):
                return INDEX_HTML
            if url.endswith(".txt"):
                return SUBMISSION
            raise FileNotFoundError(url)
        result = process_event(event, fetcher)
        self.assertTrue(result["acceptance_match"])
        self.assertTrue(result["filing_date_match"])
        self.assertEqual(result["xml_status"], "parsed")
        self.assertEqual(result["first_seen_upper_minus_acceptance_seconds"], 600.0)
        self.assertFalse(result["timing_anomaly"])

    def test_audit_never_admits_signal_or_persists_rows(self):
        event = event_row()
        def fetcher(url):
            if url.endswith("-index.htm"):
                return INDEX_HTML
            if url.endswith(".txt"):
                return SUBMISSION
            raise FileNotFoundError(url)
        summary = audit_events([event], fetcher)
        self.assertEqual(summary["transaction_semantics"]["xml_parsed_accessions"], 1)
        self.assertEqual(summary["transaction_semantics"]["p_acquired_transaction_rows_by_owner_count"]["single_owner"], 1)
        self.assertFalse(summary["eligibility"]["alpha_test_authorized"])
        self.assertFalse(summary["eligibility"]["raw_payloads_persisted"])
        self.assertEqual(summary["eligibility"]["signal_eligible"], 0)

    def test_input_gate_requires_bounded_unique_form4_events(self):
        row = event_row()
        fields = list(row)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(row)
            rows, digest = load_events(path, expected_count=1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(len(digest), 64)
            row["first_seen_interval_status"] = "INITIAL_BASELINE_NO_LOWER_BOUND"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, "source_event_interval_not_bounded"):
                load_events(path, expected_count=1)


if __name__ == "__main__":
    unittest.main()
