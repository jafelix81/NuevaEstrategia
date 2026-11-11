import unittest
from datetime import date
import exchange_calendars as xc
from research.phase275_form4_disclosure_event_unit_audit import (
    build_disclosure_events, next_session_close, normalize_address,
)

class Phase275DisclosureEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calendar=xc.get_calendar("XNYS")

    def row(self, accession, owner, txdate="2026-09-10", title="Common Stock",
            filing="14-SEP-2026", street="C/O ISSUER"):
        return {"accession":accession,"issuer_cik":"1","ticker":"ABC",
            "filing_date":filing,"transaction_date":txdate,"security_title":title,
            "owner_cik":owner,"owner_name":"Owner "+owner,
            "owner_relationship_raw":"Director,Officer","owner_title":"Director",
            "owner_street1":street,"owner_street2":"","owner_city":"NEW YORK",
            "owner_state":"NY","owner_zip":"10001"}

    def test_multiple_trade_dates_are_one_disclosure_event(self):
        rows=[self.row("a1","o1","2026-09-10"),self.row("a2","o2","2026-09-10"),
              self.row("a1","o1","2026-09-11"),self.row("a2","o2","2026-09-11")]
        r=build_disclosure_events(rows,"2026Q3",self.calendar)
        self.assertEqual(r["multi_owner_disclosure_events"],1)
        e=r["events"][0]
        self.assertEqual(e["transaction_date_count"],2)
        self.assertEqual(e["same_trade_date_multi_owner_cluster_count"],2)
        self.assertEqual(e["unique_accessions"],2)
        self.assertEqual(e["unique_reporting_owner_ciks"],2)

    def test_duplicate_rows_do_not_inflate_unique_accessions_or_owners(self):
        rows=[self.row("a1","o1"),self.row("a1","o1"),self.row("a2","o2")]
        e=build_disclosure_events(rows,"2026Q3",self.calendar)["events"][0]
        self.assertEqual(e["transaction_rows"],3)
        self.assertEqual(e["unique_accessions"],2)
        self.assertEqual(e["unique_reporting_owner_ciks"],2)

    def test_same_owner_across_two_accessions_is_not_multi_owner_event(self):
        r=build_disclosure_events([self.row("a1","o1"),self.row("a2","o1")],
                                  "2026Q3",self.calendar)
        self.assertEqual(r["multi_owner_disclosure_events"],0)

    def test_mixed_security_titles_do_not_form_one_class_cluster(self):
        rows=[self.row("a1","o1",title="Common Stock"),
              self.row("a2","o2",title="Class A Common Stock")]
        r=build_disclosure_events(rows,"2026Q3",self.calendar)
        self.assertEqual(r["events_with_security_title_mismatch"],1)
        self.assertFalse(r["events"][0]["security_title_consistent"])
        self.assertEqual(r["events"][0]["same_trade_date_multi_owner_cluster_count"],0)

    def test_security_title_case_differences_are_normalized(self):
        rows=[self.row("a1","o1",title="Common Stock"),
              self.row("a2","o2",title="COMMON STOCK")]
        e=build_disclosure_events(rows,"2026Q3",self.calendar)["events"][0]
        self.assertTrue(e["security_title_consistent"])
        self.assertEqual(e["same_trade_date_multi_owner_cluster_count"],1)

    def test_address_equality_is_only_a_mailing_proxy(self):
        e=build_disclosure_events([self.row("a1","o1"),self.row("a2","o2")],
                                  "2026Q3",self.calendar)["events"][0]
        self.assertTrue(e["all_owner_mailing_addresses_match"])
        self.assertIn("never beneficial-owner affiliation evidence",
                      e["mailing_address_interpretation"])
        self.assertFalse(e["owner_independence_proven"])

    def test_address_normalization_ignores_punctuation(self):
        a=self.row("a1","o1",street="C/O LAW FIRM, INC.")
        b=self.row("a2","o2",street="C O LAW FIRM INC")
        self.assertEqual(normalize_address(a),normalize_address(b))

    def test_next_session_close_respects_holiday(self):
        self.assertEqual(next_session_close(date(2012,1,13),self.calendar)["session"],
                         "2012-01-17")

    def test_early_close_is_respected(self):
        r=next_session_close(date(2026,11,25),self.calendar)
        self.assertEqual(r["session"],"2026-11-27")
        self.assertIn("18:00:00+00:00",r["close_utc"])

    def test_missing_transaction_date_does_not_create_trade_date_cluster(self):
        e=build_disclosure_events([self.row("a1","o1",txdate=None),
                                   self.row("a2","o2",txdate=None)],
                                  "2026Q3",self.calendar)["events"][0]
        self.assertEqual(e["transaction_date_count"],0)
        self.assertEqual(e["same_trade_date_multi_owner_cluster_count"],0)

    def test_pre_checkbox_era_remains_unknown(self):
        rows=[self.row("a1","o1",txdate="2012-01-26",filing="26-JAN-2012"),
              self.row("a2","o2",txdate="2012-01-26",filing="26-JAN-2012")]
        e=build_disclosure_events(rows,"2012Q1",self.calendar)["events"][0]
        self.assertEqual(e["plan_status"],"UNKNOWN_PRE_CHECKBOX_ERA")

if __name__=="__main__":
    unittest.main(verbosity=2)
