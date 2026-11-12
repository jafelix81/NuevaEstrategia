import unittest

from research.phase325_form4_issuer_symbol_full_census_audit import (
    classify_symbol,
    same_day_symbol_collision_rows,
    summarize_records,
)


class Phase325IssuerSymbolTests(unittest.TestCase):
    def test_placeholder_is_not_a_symbol_candidate(self):
        self.assertEqual(classify_symbol(None), ("MISSING_OR_PLACEHOLDER", None))
        self.assertEqual(classify_symbol(" N/A "), ("MISSING_OR_PLACEHOLDER", None))

    def test_exchange_prefix_is_normalized_but_not_security_identity(self):
        self.assertEqual(classify_symbol("NASDAQ: AAPL"), ("EXCHANGE_PREFIXED_SINGLE", "AAPL"))

    def test_single_token_is_only_a_candidate(self):
        self.assertEqual(classify_symbol("brk.b"), ("SINGLE_TOKEN", "BRK.B"))

    def test_multi_symbol_and_freeform_values_are_not_split_into_guessed_tickers(self):
        self.assertEqual(classify_symbol("AAPL, BRK.B"), ("MULTI_OR_FREEFORM", None))

    def test_noncanonical_values_are_not_admitted(self):
        self.assertEqual(classify_symbol("AAPL?"), ("OTHER_NONCANONICAL", None))

    def test_same_day_collision_requires_exact_date_overlap(self):
        records = [
            {"quarter": "2023Q1", "issuer_cik": "1", "issuer_name": "Issuer One", "filing_date": "2023-01-03", "ticker_as_filed": "AAA"},
            {"quarter": "2023Q1", "issuer_cik": "2", "issuer_name": "Issuer Two", "filing_date": "2023-01-03", "ticker_as_filed": "AAA"},
            {"quarter": "2006Q1", "issuer_cik": "3", "issuer_name": "Old One", "filing_date": "2006-02-15", "ticker_as_filed": "OLD"},
            {"quarter": "2026Q3", "issuer_cik": "4", "issuer_name": "New One", "filing_date": "2026-09-15", "ticker_as_filed": "OLD"},
        ]
        rows = same_day_symbol_collision_rows(records)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ticker_candidate"], "AAA")
        self.assertEqual(rows[0]["issuer_cik_a"], "1")
        self.assertEqual(rows[0]["issuer_cik_b"], "2")
        self.assertEqual(rows[0]["shared_filing_dates"], "2023-01-03")

    def test_summary_separates_ticker_reuse_from_same_day_collision(self):
        records = [
            {"quarter": "2023Q1", "issuer_cik": "1", "issuer_name": "Issuer One", "filing_date": "2023-01-03", "ticker_as_filed": "AAA"},
            {"quarter": "2023Q1", "issuer_cik": "2", "issuer_name": "Issuer Two", "filing_date": "2023-01-03", "ticker_as_filed": "AAA"},
            {"quarter": "2006Q1", "issuer_cik": "3", "issuer_name": "Old One", "filing_date": "2006-02-15", "ticker_as_filed": "OLD"},
            {"quarter": "2026Q3", "issuer_cik": "4", "issuer_name": "New One", "filing_date": "2026-09-15", "ticker_as_filed": "OLD"},
            {"quarter": "2023Q1", "issuer_cik": "1", "issuer_name": "Issuer One", "filing_date": "2023-02-01", "ticker_as_filed": "BBB"},
        ]
        result = summarize_records(records)
        self.assertEqual(result["total_accessions"], 5)
        self.assertEqual(result["unique_issuer_ciks"], 4)
        self.assertEqual(result["ticker_candidates_reused_across_ciks_across_sampled_quarters"], 2)
        self.assertEqual(result["same_day_symbol_collision_pairs_across_sampled_quarters"], 1)
        self.assertEqual(result["ticker_candidates_with_same_day_multiple_issuer_ciks"], 1)
        self.assertEqual(result["same_day_symbol_collision_shared_dates"], 1)
        self.assertEqual(result["issuer_ciks_with_multiple_canonical_candidates_across_sampled_quarters"], 1)


if __name__ == "__main__":
    unittest.main()
