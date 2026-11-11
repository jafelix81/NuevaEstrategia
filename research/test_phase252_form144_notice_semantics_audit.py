import json
import unittest
from datetime import date

from phase252_form144_notice_semantics_audit import (
    audit_rows, proposed_notional_to_adv20, resolve_issuer_ticker_candidates,
    resolve_zillow_class_ticker, sale_date_relation
)

def filing(accession, form="144", filing_date="2025-01-10", issuer="0001780312",
           seller="Seller A", candidate="ASTS", plan="", keyword="False",
           notice="2025-01-10", previous="", sale_date="2025-01-10", past=None):
    tranches=[] if sale_date is None else [{
        "approx_sale_date_iso":sale_date,"units_numeric":100,"value_numeric":1000,
        "security_class":"Class A Common"
    }]
    return {"accession":accession,"form":form,"filing_date":filing_date,
        "xml_issuer_cik":issuer,"seller_name":seller,"candidate_tickers":candidate,
        "plan_adoption_dates":plan,"mentions_10b5_1":keyword,"notice_date":notice,
        "previous_accession_normalized":previous,"sale_tranches_json":json.dumps(tranches),
        "past_sales_json":json.dumps(past or [])}

class Phase252Tests(unittest.TestCase):
    def test_single_current_ticker_resolves_by_issuer_cik(self):
        self.assertEqual(resolve_issuer_ticker_candidates("0001780312",{"1780312":{"ASTS"}}),
            {"status":"UNIQUE_CURRENT_TICKER","tickers":["ASTS"]})

    def test_dual_class_map_remains_ambiguous(self):
        r=resolve_issuer_ticker_candidates("0001617640",{"1617640":{"Z","ZG"}})
        self.assertEqual(r["status"],"AMBIGUOUS_CURRENT_TICKER_MAP")
        self.assertEqual(r["tickers"],["Z","ZG"])

    def test_approximate_sale_date_is_not_availability_clock(self):
        self.assertEqual(sale_date_relation(date(2025,1,10),date(2025,1,9)),"BEFORE_FILING")
        self.assertEqual(sale_date_relation(date(2025,1,10),date(2025,1,10)),"SAME_DAY")
        self.assertEqual(sale_date_relation(date(2025,1,10),date(2025,1,11)),"AFTER_FILING")

    def test_notional_to_adv_days_avoids_outstanding_denominator(self):
        self.assertAlmostEqual(proposed_notional_to_adv20("1000","50000"),0.02)
        self.assertIsNone(proposed_notional_to_adv20("1000","0"))
        self.assertIsNone(proposed_notional_to_adv20("0","50000"))

    def test_plan_date_and_keyword_flag_are_separate(self):
        rows=[filing("O1",plan="01/01/2024",keyword="False"),
              filing("O2",plan="",keyword="True")]
        r=audit_rows(rows,[{"ticker":"ASTS","ciks":"0001780312"}])
        self.assertEqual(r["plan_dates"]["original_144_present"],1)
        self.assertEqual(r["plan_dates"]["plan_present_keyword_false_original"],1)
        self.assertEqual(r["plan_dates"]["keyword_true_without_plan_original"],1)

    def test_amendment_plan_date_is_not_backfilled(self):
        rows=[filing("O1",plan=""),filing("A1",form="144/A",filing_date="2025-01-13",
              plan="12/01/2024",previous="O1",sale_date=None)]
        r=audit_rows(rows,[{"ticker":"ASTS","ciks":"0001780312"}])
        self.assertEqual(r["panel"]["original_144"],1)
        self.assertEqual(r["panel"]["144a"],1)
        self.assertEqual(r["amendments"]["added_plan_date"],1)

    def test_filer_ticker_in_candidate_list_is_flagged(self):
        rows=[filing("O1",candidate="AMT;ASTS")]
        r=audit_rows(rows,[{"ticker":"AMT","ciks":"0001053507"},
                           {"ticker":"ASTS","ciks":"0001780312"}])
        self.assertEqual(r["panel"]["candidate_ticker_cross_cik_mismatch_rows"],1)
        self.assertEqual(r["panel"]["issuer_cik_current_ticker_map"]["unique"],1)

    def test_notice_and_prior_sale_date_anomalies_are_flagged(self):
        rows=[filing("O1",notice="2025-01-09",sale_date="2025-01-09",
              past=[{"sale_date_iso":"2025-01-11"}])]
        r=audit_rows(rows,[{"ticker":"ASTS","ciks":"0001780312"}])
        self.assertEqual(r["dates"]["notice_mismatch_original"],1)
        self.assertEqual(r["dates"]["approx_sale_date_original"],{"BEFORE_FILING":1})
        self.assertEqual(r["dates"]["past_sales_after_filing"],1)

    def test_same_seller_issuer_day_is_not_silently_deduplicated(self):
        rows=[filing("O1"),filing("O2")]
        r=audit_rows(rows,[{"ticker":"ASTS","ciks":"0001780312"}])
        self.assertEqual(r["repeats"]["original_accessions_beyond_first_in_issuer_seller_day_groups"],1)

    def test_zillow_class_c_maps_to_z_since_2015(self):
        self.assertEqual(resolve_zillow_class_ticker("0001617640","Common Class C",date(2023,5,4)),"Z")

    def test_zillow_class_a_maps_to_zg_since_2015(self):
        self.assertEqual(resolve_zillow_class_ticker("0001617640","Common Class A",date(2023,5,4)),"ZG")

    def test_zillow_unspecified_common_remains_ambiguous(self):
        self.assertIsNone(resolve_zillow_class_ticker("0001617640","Common",date(2023,5,4)))

    def test_zillow_crosswalk_is_not_applied_before_effective_date(self):
        self.assertIsNone(resolve_zillow_class_ticker("0001617640","Common Class C",date(2015,8,16)))

    def test_current_ticker_map_is_not_effective_dated(self):
        r=audit_rows([filing("O1")],[{"ticker":"ASTS","ciks":"0001780312"}])
        self.assertFalse(r["panel"]["issuer_cik_current_ticker_map"]["effective_dated"])
        self.assertFalse(r["admission"]["strict_pit"])
        self.assertFalse(r["admission"]["alpha"])

if __name__=="__main__":
    unittest.main()
