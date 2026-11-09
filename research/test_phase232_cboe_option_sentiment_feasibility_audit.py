import unittest
from research.phase232_cboe_option_sentiment_feasibility_audit import (
    SPEC_FIELDS,DIRECTIONAL_FIELDS,PARTICIPANT_FIELDS,OI_FIELDS,VOL_SKEW_FIELDS,
    SIZE_FIELDS,DTX_FIELDS,NOT_ADMITTED_FIELDS,audit_specification
)

class Phase232Tests(unittest.TestCase):
    def test_spec_has_exactly_80_unique_fields(self):
        self.assertEqual(len(SPEC_FIELDS),80)
        self.assertEqual(len(set(SPEC_FIELDS)),80)
    def test_primary_directional_fields_are_present(self):
        for field in ("net_option_delta","call_premium_bought","call_premium_sold",
                      "put_premium_bought","put_premium_sold","calls_bought","puts_bought",
                      "calls_sold","puts_sold"):
            self.assertIn(field,DIRECTIONAL_FIELDS)
            self.assertIn(field,SPEC_FIELDS)
    def test_participant_categories_are_separate_aggregates(self):
        self.assertEqual(PARTICIPANT_FIELDS,("cust_volume","firm_volume","mkt_mkr_volume"))
        self.assertTrue(set(PARTICIPANT_FIELDS).issubset(SPEC_FIELDS))
        self.assertNotIn("customer_net_delta",SPEC_FIELDS)
    def test_oi_and_volatility_fields_present(self):
        self.assertTrue(set(OI_FIELDS).issubset(SPEC_FIELDS))
        self.assertTrue(set(VOL_SKEW_FIELDS).issubset(SPEC_FIELDS))
    def test_size_and_dtx_buckets_complete(self):
        self.assertEqual(len(SIZE_FIELDS),6)
        self.assertEqual(len(DTX_FIELDS),7)
        self.assertTrue(set(SIZE_FIELDS+DTX_FIELDS).issubset(SPEC_FIELDS))
    def test_documented_history_and_frequency(self):
        r=audit_specification()
        self.assertEqual(r["documented_historical_start"],"2012-01 (month precision)")
        self.assertEqual(r["frequency"],"daily")
        self.assertIn("first day",r["availability"]["first_subscription_day"])
        self.assertTrue(r["pit_gates"]["history_depth_documented"])
    def test_pit_blockers_are_explicit(self):
        r=audit_specification()
        self.assertFalse(r["pit_gates"]["historical_first_receipt"])
        self.assertFalse(r["pit_gates"]["correction_vintage_semantics"])
        self.assertFalse(r["pit_admission"])
        self.assertFalse(r["alpha_admission"])
    def test_vendor_averages_and_adjusted_close_not_admitted_yet(self):
        self.assertTrue({"avg_call_volume","avg_put_volume","split_adj_close"}.issubset(NOT_ADMITTED_FIELDS))
    def test_no_purchase_no_production_no_holdout(self):
        r=audit_specification()
        self.assertFalse(r["data_purchased"])
        self.assertFalse(r["production_changed"])
        self.assertFalse(r["f80_changed"])
        self.assertFalse(r["final_holdout_used"])
    def test_primary_hypothesis_is_explicit(self):
        r=audit_specification()
        self.assertIn("net_option_delta",r["primary_hypothesis"])
        self.assertEqual(r["overall_status"],"CONDITIONAL_HIGH_PRIORITY_CANDIDATE_PIT_BLOCKED")

if __name__=="__main__": unittest.main()
