import unittest

from research.phase439_form4_identity_unit_coverage_audit import as_bool, summarize


def row(cik, accession, filing_date, pit="true", matched="false", symbol=""):
    return {
        "issuer_cik": cik,
        "form4_accession": accession,
        "form4_filing_date": filing_date,
        "pit_eligible_at_transaction": pit,
        "ticker_exact_match": matched,
        "form4_symbol": symbol,
    }


class Phase439Tests(unittest.TestCase):
    def test_boolean_normalization_preserves_unknown(self):
        self.assertIs(as_bool("1"), True)
        self.assertIs(as_bool("false"), False)
        self.assertIs(as_bool(""), None)
        self.assertIs(as_bool("unexpected"), None)

    def test_duplicate_rows_do_not_inflate_issuer_or_accession_coverage(self):
        rows = [
            row("100", "A1", "2020-01-02", matched="true", symbol="AAA"),
            row("100", "A1", "2020-01-02", matched="true", symbol="AAA"),
            row("100", "A1", "2020-01-02", matched="true", symbol="AAA"),
            row("200", "B1", "2020-01-03", matched="false", symbol="BBB"),
        ]
        result = summarize(rows)
        evidence = result["exact_ticker_evidence"]
        self.assertEqual(evidence["matched_transaction_rows"], 3)
        self.assertAlmostEqual(evidence["row_weighted_rate"], 0.75)
        self.assertEqual(evidence["matched_issuer_ciks"], 1)
        self.assertAlmostEqual(evidence["issuer_weighted_rate"], 0.5)
        self.assertEqual(evidence["matched_issuer_accessions"], 1)
        self.assertAlmostEqual(evidence["accession_weighted_rate"], 0.5)

    def test_non_pit_rows_are_excluded_from_all_denominators(self):
        rows = [
            row("100", "A1", "2020-01-02", matched="true"),
            row("200", "B1", "2020-01-03", pit="false", matched="true"),
            row("300", "C1", "2020-01-04", pit="", matched="true"),
        ]
        result = summarize(rows)
        self.assertEqual(result["sample"]["candidate_rows_all"], 3)
        self.assertEqual(result["sample"]["pit_eligible_rows"], 1)
        self.assertEqual(result["exact_ticker_evidence"]["matched_issuer_ciks"], 1)

    def test_filing_unit_is_distinct_from_accession_unit(self):
        rows = [
            row("100", "A1", "2020-01-02", matched="true"),
            row("100", "A2", "2020-01-02", matched="false"),
        ]
        result = summarize(rows)
        self.assertEqual(result["sample"]["distinct_issuer_accessions"], 2)
        self.assertEqual(result["sample"]["distinct_issuer_filing_date_units"], 1)
        self.assertEqual(result["exact_ticker_evidence"]["matched_issuer_filing_date_units"], 1)

    def test_no_alpha_is_authorized(self):
        result = summarize([row("100", "A1", "2020-01-02", matched="true")])
        self.assertFalse(result["interpretation"]["alpha_authorized"])


if __name__ == "__main__":
    unittest.main()
