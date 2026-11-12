import unittest
from pathlib import Path

from research.phase330_legacy_coverpage_table_pilot import (
    extract_coverpage_symbols,
    find_symbol_column,
    load_manifest,
    normalize_symbol_cell,
    parse_tables,
)


class Phase330LegacyCoverpageTests(unittest.TestCase):
    def test_committed_manifest_is_pinned_and_complete(self):
        rows = load_manifest(Path("research/phase330_legacy_coverpage_manifest.csv"))
        self.assertEqual(len(rows), 25)
        self.assertTrue(all(r["selected_filing_date"] < r["event_date"] for r in rows))

    def test_detects_trading_symbol_column(self):
        mapping = find_symbol_column([
            "Title of each class",
            "Trading Symbol(s)",
            "Name of each exchange on which registered",
        ])
        self.assertEqual(mapping["symbol"], 1)
        self.assertEqual(mapping["title"], 0)
        self.assertEqual(mapping["exchange"], 2)

    def test_extracts_single_candidate_from_visible_coverpage(self):
        raw = b"""
        <html><body>
        <table>
          <tr><th>Title of each class</th><th>Trading Symbol</th><th>Name of each exchange on which registered</th></tr>
          <tr><td>Common Stock</td><td>AMCP</td><td>NASDAQ Global Market</td></tr>
        </table>
        </body></html>
        """
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertEqual(parsed["visible_symbols"], ["AMCP"])
        self.assertEqual(parsed["header_tables_found"], 1)

    def test_extracts_multiple_share_class_symbols(self):
        raw = b"""
        <table>
          <tr><th>Title of each class</th><th>Trading Symbol(s)</th><th>Exchange</th></tr>
          <tr><td>Common Stock</td><td>BRK.B</td><td>NYSE</td></tr>
          <tr><td>Preferred Stock</td><td>BRK-P</td><td>NYSE</td></tr>
        </table>
        """
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertEqual(parsed["visible_symbols"], ["BRK-P", "BRK.B"])

    def test_no_symbol_table_is_unknown_not_no_security(self):
        raw = b"<table><tr><th>Title of each class</th><th>Name of exchange</th></tr><tr><td>Common stock</td><td>NYSE</td></tr></table>"
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertEqual(parsed["header_tables_found"], 0)
        self.assertEqual(parsed["visible_symbols"], [])

    def test_header_without_values_is_distinguished(self):
        raw = b"<table><tr><th>Title of each class</th><th>Trading Symbol</th><th>Exchange</th></tr></table>"
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertEqual(parsed["header_tables_found"], 1)
        self.assertEqual(parsed["visible_symbols"], [])

    def test_nested_table_is_also_parsed(self):
        raw = b"""
        <table><tr><td>outer
          <table>
            <tr><th>Title of each class</th><th>Trading Symbol</th><th>Exchange</th></tr>
            <tr><td>Common stock</td><td>XYZ</td><td>NYSE</td></tr>
          </table>
        </td></tr></table>
        """
        tables = parse_tables(raw)
        parsed = extract_coverpage_symbols(tables)
        self.assertIn("XYZ", parsed["visible_symbols"])

    def test_exchange_names_are_not_treated_as_symbols(self):
        self.assertEqual(normalize_symbol_cell("NASDAQ"), [])
        self.assertEqual(normalize_symbol_cell("NYSE"), [])
        # The parser only consumes the Trading Symbol column; exchange-column tokens
        # are not passed to normalize_symbol_cell by extract_coverpage_symbols.

    def test_symbol_normalization_preserves_dots_and_hyphens(self):
        self.assertEqual(normalize_symbol_cell("BRK.B"), ["BRK.B"])
        self.assertEqual(normalize_symbol_cell("ABC-PD"), ["ABC-PD"])

    def test_header_search_is_case_insensitive(self):
        mapping = find_symbol_column(["TITLE OF EACH CLASS", "TRADING SYMBOL", "NAME OF EXCHANGE"])
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping["symbol"], 1)

    def test_candidate_mismatch_remains_visible_evidence(self):
        raw = b"""
        <table>
          <tr><th>Title of each class</th><th>Trading Symbol</th><th>Exchange</th></tr>
          <tr><td>Common stock</td><td>RVSB</td><td>NASDAQ</td></tr>
        </table>
        """
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertNotIn("TSBK", parsed["visible_symbols"])
        self.assertIn("RVSB", parsed["visible_symbols"])

    def test_plain_text_without_table_does_not_invent_symbol(self):
        raw = b"Title of each class Common Stock Trading Symbol not available"
        parsed = extract_coverpage_symbols(parse_tables(raw))
        self.assertEqual(parsed["visible_symbols"], [])


if __name__ == "__main__":
    unittest.main()
