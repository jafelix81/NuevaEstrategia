import unittest

from research.phase604_sec_series_class_ticker_cik_crosswalk_audit import (
    mapping_summary, normalize_cik, normalize_ticker, parse_json_ticker_rows,
    parse_series_class_csv, source_mapping,
)


class Phase604CrosswalkTests(unittest.TestCase):
    def test_normalizes_cik_and_ticker_without_guessing_symbol_aliases(self):
        self.assertEqual(normalize_cik(320193), "0000320193")
        self.assertEqual(normalize_ticker(" qqq "), "QQQ")
        self.assertIsNone(normalize_cik("not-a-cik"))

    def test_parses_keyed_company_ticker_json(self):
        raw = b'{"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."}}'
        rows, count = parse_json_ticker_rows(raw, "company_tickers_json", "current")
        self.assertEqual(count, 1)
        self.assertEqual(rows[0]["ticker"], "AAPL")
        self.assertEqual(rows[0]["cik"], "0000320193")

    def test_parses_columnar_mutual_fund_json_with_class_ticker(self):
        raw = (b'{"fields":["cik","series_id","class_id","class_ticker"],'
               b'"data":[[12345,"S000000001","C000000001","QQQ"]]}')
        rows, count = parse_json_ticker_rows(raw, "company_tickers_mf_json", "current")
        self.assertEqual(count, 1)
        self.assertEqual(rows[0]["ticker"], "QQQ")
        self.assertEqual(rows[0]["series_id"], "S000000001")
        self.assertEqual(rows[0]["class_id"], "C000000001")

    def test_parses_series_class_csv_after_optional_preamble(self):
        raw = (
            b"SEC Investment Company Series and Class Report\\n"
            b"Reporting File Number,CIK,Name of Investment Company,Series ID,Series Name,Class ID,Class Name,Class Ticker\\n"
            b"811-00001,12345,Example Fund,S000000001,Example Series,C000000001,ETF Shares,QQQ\\n"
        )
        rows, data_rows, header_index = parse_series_class_csv(raw, "series_class_2026_csv", "2026-06-01")
        self.assertEqual(data_rows, 1)
        self.assertEqual(header_index, 1)
        self.assertEqual(rows[0]["ticker"], "QQQ")
        self.assertEqual(rows[0]["cik"], "0000012345")

    def test_blank_class_ticker_is_not_imputed(self):
        raw = (
            b"CIK,Series ID,Class ID,Class Ticker\\n"
            b"12345,S000000001,C000000001,\\n"
        )
        rows, data_rows, _ = parse_series_class_csv(raw, "series_class_2026_csv", "2026-06-01")
        self.assertEqual(data_rows, 1)
        self.assertEqual(rows, [])

    def test_multiple_class_rows_preserve_class_ids_but_unique_cik_mapping(self):
        rows = [
            {"ticker": "QQQ", "cik": "0000012345", "class_id": "C1"},
            {"ticker": "QQQ", "cik": "0000012345", "class_id": "C2"},
        ]
        mapping, details = source_mapping(rows)
        self.assertEqual(mapping["QQQ"], {"0000012345"})
        self.assertEqual(len(details["QQQ"]), 2)

    def test_conflicting_ciks_are_not_collapsed(self):
        mapping = {"QQQ": {"0000012345", "0000099999"}}
        summary = mapping_summary(mapping, {"QQQ", "SPY"})
        self.assertEqual(summary["tickers_mapped"], 1)
        self.assertEqual(summary["conflicting_tickers"]["QQQ"], ["0000012345", "0000099999"])
        self.assertEqual(summary["unmapped_tickers"], ["SPY"])

    def test_universe_membership_is_exact_not_fuzzy(self):
        rows = [{"ticker": "QQQ.A", "cik": "0000012345"},
                {"ticker": "QQQ", "cik": "0000099999"}]
        mapping, _ = source_mapping(rows)
        summary = mapping_summary(mapping, {"QQQ"})
        self.assertEqual(summary["tickers_mapped"], 1)
        self.assertEqual(summary["conflicting_tickers"], {})

    def test_historical_snapshot_is_not_declared_effective_dated(self):
        snapshot = {"source": "series_class_2026_csv", "snapshot_date": "2026-06-01"}
        self.assertNotIn("effective_date", snapshot)


if __name__ == "__main__":
    unittest.main()
