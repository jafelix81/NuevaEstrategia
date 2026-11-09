import unittest
from research.phase224_sec_companyfacts_shares_outstanding_pit_audit import (
    classify_dei_measure, extract_dei_shares_facts, select_class_specific_fact,
    select_companyfacts_shares,
)

def obs(val, end, filed, accn, form="10-K", unit="shares"):
    return {"val":val,"end":end,"filed":filed,"accn":accn,"form":form,"unit":unit}

def companyfacts(items):
    units={}
    for item in items:
        units.setdefault(item["unit"],[]).append({k:v for k,v in item.items() if k!="unit"})
    return {"facts":{"dei":{"EntityCommonStockSharesOutstanding":{"units":units}}}}

class Phase224CompanyfactsPITTests(unittest.TestCase):
    def test_selects_latest_measurement_known_before_event(self):
        p=companyfacts([obs(116000000,"2025-09-30","2025-11-05","a1","10-Q"),
                        obs(117011421,"2026-01-30","2026-02-13","a2"),
                        obs(118000000,"2026-04-30","2026-05-10","a3","10-Q")])
        r=select_companyfacts_shares(p,"2026-03-04")
        self.assertEqual(r["status"],"SELECTED_ENTITY_WIDE")
        self.assertEqual(r["value"],"117011421")
    def test_same_day_fact_is_excluded(self):
        r=select_companyfacts_shares(companyfacts([obs(1000,"2026-03-04","2026-03-04","same")]),"2026-03-04")
        self.assertEqual(r["status"],"SAME_DAY_ONLY")
    def test_future_filed_fact_is_excluded(self):
        r=select_companyfacts_shares(companyfacts([obs(1000,"2026-02-28","2026-03-05","future")]),"2026-03-04")
        self.assertEqual(r["status"],"NO_PRIOR_ELIGIBLE_FACT")
    def test_future_measurement_date_is_excluded(self):
        r=select_companyfacts_shares(companyfacts([obs(1000,"2026-03-05","2026-03-03","future")]),"2026-03-04")
        self.assertEqual(r["status"],"NO_PRIOR_ELIGIBLE_FACT")
    def test_same_measurement_filed_conflict_is_ambiguous(self):
        p=companyfacts([obs(1000,"2026-01-31","2026-02-13","a1"),obs(1100,"2026-01-31","2026-02-13","a2")])
        self.assertEqual(select_companyfacts_shares(p,"2026-03-04")["status"],"AMBIGUOUS_SAME_DATE_CONFLICT")
    def test_amendment_only_changes_value_after_amendment_filing(self):
        p=companyfacts([obs(1000,"2025-12-31","2026-02-13","orig","10-K"),
                        obs(1050,"2025-12-31","2026-03-10","amend","10-K/A")])
        self.assertEqual(select_companyfacts_shares(p,"2026-03-04")["value"],"1000")
        self.assertEqual(select_companyfacts_shares(p,"2026-03-11")["value"],"1050")
    def test_missing_fact_is_unknown_not_zero(self):
        r=select_companyfacts_shares({"facts":{"dei":{}}},"2026-03-04")
        self.assertEqual(r["status"],"NO_ENTITY_WIDE_FACT")
        self.assertIsNone(r["value"])
    def test_zero_shares_not_denominator(self):
        r=select_companyfacts_shares(companyfacts([obs(0,"2026-01-31","2026-02-13","zero")]),"2026-03-04")
        self.assertEqual(r["status"],"NO_PRIOR_ELIGIBLE_FACT")
    def test_wrong_unit_rejected(self):
        r=select_companyfacts_shares(companyfacts([obs(1000,"2026-01-31","2026-02-13","usd",unit="USD")]),"2026-03-04")
        self.assertEqual(r["status"],"NO_PRIOR_ELIGIBLE_FACT")
    def test_unsupported_form_rejected(self):
        r=select_companyfacts_shares(companyfacts([obs(1000,"2026-01-31","2026-02-13","8k",form="8-K")]),"2026-03-04")
        self.assertEqual(r["status"],"NO_PRIOR_ELIGIBLE_FACT")
    def test_public_float_usd_is_not_shares(self):
        self.assertEqual(classify_dei_measure("EntityPublicFloat","USD"),"PUBLIC_FLOAT_MARKET_VALUE_NOT_SHARES")
    def test_raw_xbrl_extracts_two_class_dimensions(self):
        xml='''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:dei="http://xbrl.sec.gov/dei/2025" xmlns:us-gaap="http://fasb.org/us-gaap/2025">
        <context id="a"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">us-gaap:CommonClassAMember</xbrldi:explicitMember></segment></entity><period><instant>2026-01-30</instant></period></context>
        <context id="b"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">us-gaap:CommonClassBMember</xbrldi:explicitMember></segment></entity><period><instant>2026-01-30</instant></period></context>
        <unit id="shares"><measure>xbrli:shares</measure></unit>
        <dei:EntityCommonStockSharesOutstanding contextRef="a" unitRef="shares">1000</dei:EntityCommonStockSharesOutstanding>
        <dei:EntityCommonStockSharesOutstanding contextRef="b" unitRef="shares">200</dei:EntityCommonStockSharesOutstanding></xbrl>'''
        rows=extract_dei_shares_facts(xml)
        self.assertEqual(len(rows),2)
        self.assertEqual({r["class_member"] for r in rows},{"us-gaap:CommonClassAMember","us-gaap:CommonClassBMember"})
    def test_exact_class_member_selected(self):
        xml='''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:dei="http://xbrl.sec.gov/dei/2025" xmlns:us-gaap="http://fasb.org/us-gaap/2025">
        <context id="a"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">us-gaap:CommonClassAMember</xbrldi:explicitMember></segment></entity><period><instant>2026-01-30</instant></period></context>
        <unit id="shares"><measure>xbrli:shares</measure></unit>
        <dei:EntityCommonStockSharesOutstanding contextRef="a" unitRef="shares">1000</dei:EntityCommonStockSharesOutstanding></xbrl>'''
        rows=extract_dei_shares_facts(xml)
        r=select_class_specific_fact(rows,"us-gaap:CommonClassAMember","2026-03-04","2026-02-13","a1","10-K")
        self.assertEqual(r["status"],"SELECTED_CLASS_SPECIFIC")
        self.assertEqual(r["value"],"1000")
    def test_class_mismatch_does_not_fall_back_to_entity_wide(self):
        xml='''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:dei="http://xbrl.sec.gov/dei/2025">
        <context id="a"><entity><identifier scheme="x">1</identifier></entity><period><instant>2026-01-30</instant></period></context>
        <unit id="shares"><measure>xbrli:shares</measure></unit>
        <dei:EntityCommonStockSharesOutstanding contextRef="a" unitRef="shares">1000</dei:EntityCommonStockSharesOutstanding></xbrl>'''
        rows=extract_dei_shares_facts(xml)
        r=select_class_specific_fact(rows,"us-gaap:CommonClassAMember","2026-03-04","2026-02-13","a1","10-K")
        self.assertEqual(r["status"],"CLASS_FACT_NOT_FOUND")
    def test_class_same_day_is_excluded(self):
        rows=[{"tag":"EntityCommonStockSharesOutstanding","value":"1000","unit":"shares","end":"2026-03-04","class_member":"A","class_member_count":1}]
        r=select_class_specific_fact(rows,"A","2026-03-04","2026-03-04","same","10-K")
        self.assertEqual(r["status"],"SAME_DAY_OR_FUTURE_FILING")

if __name__=="__main__":
    unittest.main()
