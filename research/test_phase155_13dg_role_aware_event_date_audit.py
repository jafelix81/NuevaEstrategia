import sys
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase155_13dg_role_aware_event_date_audit import audit_phase35, is_quarter_end, parse_event_date, weighted_rate

class Phase155Tests(unittest.TestCase):
    def test_event_date_parser_supports_legacy_and_iso(self):
        self.assertEqual(parse_event_date("09/30/2024"), date(2024, 9, 30))
        self.assertEqual(parse_event_date("2024-09-30"), date(2024, 9, 30))

    def test_quarter_end_calendar(self):
        for d in (date(2024,3,31), date(2024,6,30), date(2024,9,30), date(2024,12,31)):
            self.assertTrue(is_quarter_end(d))
        self.assertFalse(is_quarter_end(date(2024,3,30)))
        self.assertFalse(is_quarter_end(date(2024,2,29)))

    def test_phase35_positive_control_invalidates_issuer_identity(self):
        row = {
            "accession":"0000895421-24-000178", "ticker":"MS", "issuer_cik":"0000895421",
            "primary_document":"abrdnGlobalASGI.txt", "form":"SC 13G", "filing_date":"2024-02-12",
            "event_date":"2024-12-31", "report_date":"", "filing_lag_business_days":""
        }
        r=audit_phase35([row])
        self.assertTrue(r["known_positive_control"]["mismatch_confirmed"])
        self.assertEqual(r["identity_scope"],"CIK_SUBMISSIONS_QUERY_SOURCE_NOT_SUBJECT_ISSUER_VALIDATED")
        self.assertEqual(r["known_positive_control"]["independently_validated_subject_cik"],"0001793855")

    def test_phase35_report_date_missing_and_lag_invalid(self):
        rows=[
            {"accession":"0000895421-24-000178", "ticker":"MS", "issuer_cik":"0000895421", "primary_document":"abrdnGlobalASGI.txt", "form":"SC 13G", "filing_date":"2024-02-12", "event_date":"2024-12-31", "report_date":"", "filing_lag_business_days":"-1"},
            {"accession":"x", "ticker":"X", "issuer_cik":"0000000001", "primary_document":"x.txt", "form":"SC 13D", "filing_date":"2024-01-01", "event_date":"2023-12-31", "report_date":"", "filing_lag_business_days":"0"},
            {"accession":"y", "ticker":"Y", "issuer_cik":"0000000002", "primary_document":"y.txt", "form":"SC 13G", "filing_date":"2024-01-01", "event_date":"", "report_date":"", "filing_lag_business_days":""}
        ]
        r=audit_phase35(rows)
        self.assertEqual(r["report_date_missing_rows"],3)
        self.assertEqual(r["filing_lag_business_days_value_counts"],{"-1":1,"0":1,"<MISSING>":1})

    def test_weighted_rate_uses_supplied_sample_weights(self):
        rows=[{"sample_weight":"2","q":True},{"sample_weight":"1","q":False}]
        r=weighted_rate(rows,lambda x:x["q"])
        self.assertEqual(r["unweighted_count"],1)
        self.assertAlmostEqual(r["sample_weighted_pct_within_observed_xml_subset"],66.6667,places=3)

    def test_weighted_rate_empty_is_safe(self):
        self.assertIsNone(weighted_rate([],lambda x:True)["unweighted_pct"])

    def test_event_date_parser_rejects_ambiguous_format(self):
        with self.assertRaises(ValueError):
            parse_event_date("09-30-2024")

if __name__ == "__main__":
    unittest.main(verbosity=2)
