import unittest
from pathlib import Path

from research.phase328_sec_collision_prior_filing_xbrl_pilot import (
    ALLOWED_FORMS,
    load_collision_pairs,
    InlineXBRLHTMLParser,
    choose_instance_file,
    latest_shared_date,
    norm_cik,
    norm_symbol,
    parse_instance_xml,
    parse_inline_html,
    select_prior_periodic_filing,
    summarize_facts,
)


class Phase328IdentityPilotTests(unittest.TestCase):
    def test_committed_collision_manifest_is_complete_and_pinned(self):
        rows = load_collision_pairs(Path("research/phase328_collision_pair_manifest.csv"))
        self.assertEqual(len(rows), 28)
        self.assertEqual(sum(len(r["shared_filing_dates"].split(";")) for r in rows), 42)
        self.assertEqual(rows[-1]["ticker_candidate"], "UNIT")

    def test_latest_shared_date_uses_latest_valid_date(self):
        self.assertEqual(
            latest_shared_date("2023-04-03;2025-07-01;2026-09-25"),
            "2026-09-25",
        )

    def test_empty_shared_dates_rejected(self):
        with self.assertRaises(ValueError):
            latest_shared_date("")

    def test_cik_normalization_removes_leading_zeroes(self):
        self.assertEqual(norm_cik("0001041368"), "1041368")

    def test_symbol_normalization_is_exact_whitespace_only(self):
        self.assertEqual(norm_symbol(" brk . b "), "BRK.B")

    def test_same_day_and_later_periodic_filings_are_excluded(self):
        submissions = {"filings": {"recent": {
            "form": ["10-Q", "10-K", "10-Q"],
            "filingDate": ["2026-09-25", "2026-08-01", "2026-10-01"],
            "accessionNumber": ["a", "b", "c"],
            "primaryDocument": ["a.htm", "b.htm", "c.htm"],
            "reportDate": ["2026-06-30", "2025-12-31", "2026-09-30"],
        }, "files": []}}
        selected, source = select_prior_periodic_filing(submissions, "2026-09-25")
        self.assertEqual(selected["accessionNumber"], "b")
        self.assertEqual(selected["filingDate"], "2026-08-01")
        self.assertEqual(source, "RECENT")
        self.assertLess(selected["filingDate"], "2026-09-25")

    def test_only_supported_periodic_forms_are_selected(self):
        self.assertIn("N-CSR", ALLOWED_FORMS)
        submissions = {"filings": {"recent": {
            "form": ["8-K", "N-CSR", "13F-HR"],
            "filingDate": ["2026-09-01", "2026-08-01", "2026-07-01"],
            "accessionNumber": ["a", "b", "c"],
            "primaryDocument": ["a.htm", "b.htm", "c.htm"],
            "reportDate": ["", "2026-06-30", ""],
        }, "files": []}}
        selected, _ = select_prior_periodic_filing(submissions, "2026-09-25")
        self.assertEqual(selected["accessionNumber"], "b")

    def test_instance_parser_preserves_class_and_listing_axes(self):
        raw = b'''<?xml version="1.0"?>
        <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
          xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
          xmlns:dei="http://xbrl.sec.gov/dei/2026"
          xmlns:us-gaap="http://fasb.org/us-gaap/2026">
          <xbrli:context id="classA">
            <xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier>
              <xbrli:segment>
                <xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">us-gaap:ClassACommonStockMember</xbrldi:explicitMember>
                <xbrldi:explicitMember dimension="dei:EntityListingsExchangeAxis">dei:NYSEMember</xbrldi:explicitMember>
              </xbrli:segment>
            </xbrli:entity>
            <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period>
          </xbrli:context>
          <dei:TradingSymbol contextRef="classA">ABC</dei:TradingSymbol>
          <dei:Security12bTitle contextRef="classA">Class A common stock</dei:Security12bTitle>
          <dei:SecurityExchangeName contextRef="classA">NYSE</dei:SecurityExchangeName>
        </xbrli:xbrl>'''
        facts = parse_instance_xml(raw)
        summary = summarize_facts(facts, "ABC")
        self.assertEqual(summary["symbol_match_status"], "MATCH_SINGLE_SYMBOL")
        self.assertTrue(summary["has_security_title_fact"])
        self.assertTrue(summary["has_class_axis"])
        self.assertTrue(summary["has_listing_axis"])
        self.assertIn("ABC", summary["trading_symbols"])

    def test_html_fallback_extracts_inline_trading_symbol(self):
        raw = b'''<html><body><ix:nonNumeric name="dei:TradingSymbol" contextRef="c1">XYZ</ix:nonNumeric></body></html>'''
        facts = parse_inline_html(raw)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["name"], "TradingSymbol")
        self.assertEqual(facts[0]["value"], "XYZ")
        self.assertEqual(summarize_facts(facts, "XYZ")["symbol_match_status"], "MATCH_SINGLE_SYMBOL")

    def test_missing_symbol_fact_remains_unknown(self):
        summary = summarize_facts([], "ABC")
        self.assertEqual(summary["symbol_match_status"], "TRADING_SYMBOL_FACT_MISSING")
        self.assertFalse(summary["has_trading_symbol_fact"])

    def test_explicit_no_symbol_is_not_misclassified_as_missing(self):
        facts = [{"name": "NoTradingSymbolFlag", "value": "true", "context_ref": "c1", "dimensions": []}]
        summary = summarize_facts(facts, "ABC")
        self.assertEqual(summary["symbol_match_status"], "EXPLICIT_NO_SYMBOL")
        self.assertTrue(summary["has_trading_symbol_fact"])

    def test_multiple_symbols_are_not_collapsed(self):
        facts = [
            {"name": "TradingSymbol", "value": "ABC", "context_ref": "a", "dimensions": []},
            {"name": "TradingSymbol", "value": "ABC.B", "context_ref": "b", "dimensions": []},
        ]
        summary = summarize_facts(facts, "ABC")
        self.assertEqual(summary["symbol_match_status"], "MATCH_AMONG_MULTIPLE_SYMBOLS")
        self.assertEqual(summary["trading_symbols"], ["ABC", "ABC.B"])

    def test_instance_file_selection_prefers_inline_generated_instance(self):
        index = {"directory": {"item": [
            {"name": "issuer-20260630_htm.xml", "type": "text"},
            {"name": "issuer-20260630_cal.xml", "type": "EX-101.CAL"},
            {"name": "issuer-20260630.xsd", "type": "EX-101.SCH"},
        ]}}
        self.assertEqual(
            choose_instance_file(index, "issuer-20260630.htm"),
            "issuer-20260630_htm.xml",
        )

    def test_security_title_is_not_used_as_a_security_key(self):
        facts = [{"name": "Security12bTitle", "value": "Common Stock", "context_ref": "c1", "dimensions": []}]
        summary = summarize_facts(facts, "ABC")
        self.assertEqual(summary["symbol_match_status"], "TRADING_SYMBOL_FACT_MISSING")
        self.assertTrue(summary["has_security_title_fact"])


if __name__ == "__main__":
    unittest.main()
