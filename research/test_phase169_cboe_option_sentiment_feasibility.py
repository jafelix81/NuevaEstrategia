import unittest
from decimal import Decimal
from research.phase169_cboe_option_sentiment_feasibility import (
 CANDIDATE_FEATURES,DATE_FIELDS,EXCHANGE_VOLUME_FIELDS,FIELDS,FLOAT_FIELDS,
 INTEGER_FIELDS,OPTIONAL_BLANK_FIELDS,STRING_FIELDS,build_summary,
 directional_pct_fraction,knowledge_time_gate,schema_audit,signed_directional_premium)

class Phase169Tests(unittest.TestCase):
 def test_spec_has_80_fields(self): self.assertEqual(len(FIELDS),80)
 def test_field_names_unique(self): self.assertEqual(len(FIELDS),len(set(FIELDS)))
 def test_type_partition_complete_disjoint(self):
  groups=[set(DATE_FIELDS),set(STRING_FIELDS),set(FLOAT_FIELDS),set(INTEGER_FIELDS)]
  self.assertEqual(set.union(*groups),set(FIELDS))
  self.assertEqual(sum(map(len,groups)),len(FIELDS))
  self.assertEqual((len(DATE_FIELDS),len(STRING_FIELDS),len(FLOAT_FIELDS)),(1,2,18))
 def test_eighteen_exchange_volume_fields(self):
  self.assertEqual(len(EXCHANGE_VOLUME_FIELDS),18)
  self.assertIn("exch_vol_memx",EXCHANGE_VOLUME_FIELDS)
  self.assertIn("exch_vol_sphr",EXCHANGE_VOLUME_FIELDS)
 def test_optional_blank_fields(self):
  self.assertEqual(len(OPTIONAL_BLANK_FIELDS),11)
  self.assertIn("cust_volume",OPTIONAL_BLANK_FIELDS)
  self.assertIn("size1001up",OPTIONAL_BLANK_FIELDS)
 def test_exact_schema_passes(self):
  r=schema_audit(FIELDS); self.assertEqual(r["status"],"PASS_SPEC_SCHEMA")
  self.assertEqual(r["observed_fields"],80)
 def test_missing_field_fails(self):
  r=schema_audit(FIELDS[:-1]); self.assertEqual(r["status"],"FAIL_SPEC_SCHEMA")
  self.assertEqual(r["missing_fields"],["exch_vol_sphr"])
 def test_extra_field_fails(self):
  r=schema_audit((*FIELDS,"unregistered_field")); self.assertEqual(r["status"],"FAIL_SPEC_SCHEMA")
  self.assertEqual(r["extra_fields"],["unregistered_field"])
 def test_duplicate_field_fails(self):
  r=schema_audit((*FIELDS,"trade_date")); self.assertEqual(r["status"],"FAIL_SPEC_SCHEMA")
  self.assertEqual(r["duplicate_fields"],["trade_date"])
 def test_directional_pct_percentage_points(self):
  self.assertEqual(directional_pct_fraction("98.011"),Decimal("0.98011"))
 def test_directional_pct_keeps_scale(self):
  self.assertEqual(directional_pct_fraction("0.75"),Decimal("0.0075"))
 def test_directional_pct_out_of_range(self):
  with self.assertRaisesRegex(ValueError,"percentage_point_range"): directional_pct_fraction("100.01")
 def test_signed_premium_signs(self):
  row={"call_premium_bought":"1000","call_premium_sold":"200","put_premium_bought":"500","put_premium_sold":"100"}
  self.assertEqual(signed_directional_premium(row),Decimal("400"))
 def test_signed_premium_missing_stays_missing(self):
  row={"call_premium_bought":"1000","call_premium_sold":"200","put_premium_bought":"","put_premium_sold":"100"}
  self.assertIsNone(signed_directional_premium(row))
 def test_actual_receipt_next_day_passes(self):
  r=knowledge_time_gate("2026-11-05","2026-11-05T20:30:00-05:00","2026-11-06T09:35:00-05:00")
  self.assertTrue(r["eligible"]); self.assertEqual(r["knowledge_time_basis"],"ACTUAL_FIRST_RECEIPT")
  self.assertFalse(r["same_day_use"])
 def test_same_trade_date_decision_rejected(self):
  with self.assertRaisesRegex(ValueError,"same_trade_date"):
   knowledge_time_gate("2026-11-05","2026-11-05T20:30:00-05:00","2026-11-05T21:00:00-05:00")
 def test_decision_before_receipt_rejected(self):
  with self.assertRaisesRegex(ValueError,"decision_precedes"):
   knowledge_time_gate("2026-11-05","2026-11-06T05:00:00-05:00","2026-11-06T04:59:00-05:00")
 def test_naive_timestamp_rejected(self):
  with self.assertRaisesRegex(ValueError,"timezone_required"):
   knowledge_time_gate("2026-11-05","2026-11-06T05:00:00","2026-11-06T09:35:00-05:00")
 def test_receipt_before_trade_date_rejected(self):
  with self.assertRaisesRegex(ValueError,"receipt_precedes"):
   knowledge_time_gate("2026-11-05","2026-11-04T23:00:00-05:00","2026-11-06T09:35:00-05:00")
 def test_summary_fails_closed(self):
  s=build_summary(); self.assertFalse(s["strict_pit"]); self.assertFalse(s["alpha_admission"])
  self.assertFalse(s["public_sample_found"]); self.assertEqual(s["current_orderability"],"UNCONFIRMED")
 def test_feature_family_is_limited(self):
  self.assertIn("signed_directional_premium",CANDIDATE_FEATURES)
  self.assertIn("opening_oi_state",CANDIDATE_FEATURES); self.assertEqual(len(CANDIDATE_FEATURES),6)

if __name__=="__main__": unittest.main()
