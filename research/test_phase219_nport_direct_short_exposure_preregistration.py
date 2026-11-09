import json
import unittest
from research.phase219_nport_direct_short_exposure_preregistration import EVIDENCE, build_audit

class Phase219NportShortPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.result = build_audit(cls.evidence)

    def test_phase_identity(self):
        self.assertEqual(self.evidence["phase"], 219)

    def test_prior_27n_27o_was_long_only_and_short_is_distinct(self):
        p = self.evidence["prior_phase_adjudication"]
        self.assertIn("LONG", p["phase27n_filter"])
        self.assertFalse(p["short_side_tested_before"])
        self.assertIn("KILLED", p["phase27o_disposition"])

    def test_direction_is_fixed_not_selected_after_returns(self):
        h = self.evidence["hypothesis"]
        self.assertTrue(h["sign_is_fixed"])
        self.assertIn("lower subsequent residual equity returns", h["direction"])

    def test_direct_short_filter_is_narrow(self):
        r = self.evidence["row_filter"]
        self.assertEqual(r["payoff_profile"], "Short")
        self.assertEqual(r["asset_cat"], "EC")
        self.assertEqual(r["issuer_cat"], "CORP")
        self.assertEqual(r["unit"], "NS")

    def test_absent_rows_are_unknown_not_zero(self):
        self.assertIn("never impute zero", self.evidence["hypothesis"]["absent_row_interpretation"])

    def test_acceptance_not_report_date_controls_availability(self):
        k = self.evidence["knowledge_time"]
        self.assertFalse(k["use_report_date_as_knowledge_time"])
        self.assertFalse(k["fixed_report_lag"])
        self.assertIn("strictly after SEC acceptance", k["trading_boundary"])

    def test_raw_retrieval_and_crosswalk_gates_remain_open(self):
        g = self.evidence["admission_gates"]
        self.assertEqual(g["five_accession_raw_hashes"], "NOT_VERIFIED")
        self.assertEqual(g["effective_dated_security_listing_crosswalk"], "NOT_ESTABLISHED")
        self.assertFalse(g["alpha_test_authorized"])

    def test_no_alpha_holdout_or_production_changes(self):
        c = self.evidence["controls"]
        self.assertFalse(c["return_test_run"])
        self.assertFalse(c["alpha_test_run"])
        self.assertFalse(c["holdout_used"])
        self.assertFalse(c["production_changed"])
        self.assertTrue(c["f80_frozen"])

    def test_holdout_remains_consumed(self):
        self.assertEqual(self.evidence["test_protocol"]["legacy_holdout"], "CONSUMED_NOT_PRISTINE")

    def test_no_fake_sec_contact(self):
        c = self.evidence["controls"]
        self.assertFalse(c["sec_requests_sent"])
        self.assertFalse(c["placeholder_contact_email_used"])

if __name__ == "__main__":
    unittest.main()
