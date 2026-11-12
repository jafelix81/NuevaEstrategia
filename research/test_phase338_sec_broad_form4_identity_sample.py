import unittest
from research.phase338_sec_broad_form4_identity_sample import (
    anchor_status, compare_candidate, one_accession_per_issuer_quarter,
    stratum, weighted_rate,
)

class Phase338Tests(unittest.TestCase):
    def test_issuer_quarter_selection_preserves_index_exception_if_present(self):
        rows=[
            {"quarter":"2023Q1","issuer_cik":"100","accession":"matched","index_status":"MATCHED_ON_FILED_DATE"},
            {"quarter":"2023Q1","issuer_cik":"100","accession":"exception","index_status":"INDEX_FILED_DATE_CONFLICT"},
        ]
        self.assertEqual(one_accession_per_issuer_quarter(rows)[("2023Q1","100")]["accession"],"exception")

    def test_index_exception_is_its_own_stratum(self):
        self.assertEqual(stratum({"index_status":"INDEX_FILED_DATE_CONFLICT","ticker_as_filed":"AAPL","reporting_owner_count":"1"}),"INDEX_EXCEPTION")

    def test_single_and_multi_owner_are_separate_strata(self):
        a={"index_status":"MATCHED_ON_FILED_DATE","ticker_as_filed":"AAPL","reporting_owner_count":"1"}
        b={"index_status":"MATCHED_ON_FILED_DATE","ticker_as_filed":"AAPL","reporting_owner_count":"2"}
        self.assertEqual(stratum(a),"SINGLE_TOKEN_SINGLE_OWNER")
        self.assertEqual(stratum(b),"SINGLE_TOKEN_MULTI_OWNER")

    def test_symbol_classes_remain_distinct(self):
        self.assertEqual(stratum({"index_status":"MATCHED_ON_FILED_DATE","ticker_as_filed":"NONE","reporting_owner_count":"1"}),"MISSING_OR_PLACEHOLDER")
        self.assertEqual(stratum({"index_status":"MATCHED_ON_FILED_DATE","ticker_as_filed":"ABC, DEF","reporting_owner_count":"1"}),"MULTI_OR_FREEFORM")
        self.assertEqual(stratum({"index_status":"MATCHED_ON_FILED_DATE","ticker_as_filed":"NYSE: ABC","reporting_owner_count":"1"}),"EXCHANGE_PREFIXED_SINGLE")

    def test_anchor_must_be_strictly_pre_event(self):
        self.assertEqual(anchor_status({"filingDate":"2023-01-01"},"2023-01-01"),("INVALID_NONPRE_EVENT_ANCHOR",0))
        self.assertEqual(anchor_status({"filingDate":"2023-01-02"},"2023-01-01"),("INVALID_NONPRE_EVENT_ANCHOR",-1))

    def test_anchor_freshness_boundary(self):
        self.assertEqual(anchor_status({"filingDate":"2022-01-01"},"2022-12-31"),("FRESH_PRIOR_PERIODIC_FILING",364))
        self.assertEqual(anchor_status({"filingDate":"2022-01-01"},"2023-01-01"),("FRESH_PRIOR_PERIODIC_FILING",365))
        self.assertEqual(anchor_status({"filingDate":"2022-01-01"},"2023-01-02"),("STALE_PRIOR_PERIODIC_FILING",366))

    def test_index_exception_is_not_a_symbol_mismatch(self):
        self.assertEqual(compare_candidate("INDEX_FILED_DATE_CONFLICT","AAPL",["MSFT"],False),"INDEX_DATE_EXCEPTION_NOT_COMPARABLE")

    def test_symbol_candidate_comparison_is_exact(self):
        self.assertEqual(compare_candidate("MATCHED_ON_FILED_DATE","AAPL",["AAPL"],False),"MATCH_SINGLE_SYMBOL")
        self.assertEqual(compare_candidate("MATCHED_ON_FILED_DATE","AAPL",["AAPL","BRK.B"],False),"MATCH_AMONG_MULTIPLE_SYMBOLS")
        self.assertEqual(compare_candidate("MATCHED_ON_FILED_DATE","AAPL",["MSFT"],False),"MISMATCH")
        self.assertEqual(compare_candidate("MATCHED_ON_FILED_DATE","",["MSFT"],False),"CANDIDATE_SYMBOL_UNAVAILABLE")

    def test_weighted_rate_uses_design_weights(self):
        rows=[{"design_weight":10,"ok":True},{"design_weight":2,"ok":False}]
        got=weighted_rate(rows,lambda r:r["ok"])
        self.assertEqual(got["weighted_population_units"],12)
        self.assertAlmostEqual(got["weighted_rate_pct"],83.3333,places=3)
        self.assertEqual(got["sample_n"],2)

if __name__=="__main__":unittest.main()
