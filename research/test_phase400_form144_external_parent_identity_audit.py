import json
import unittest
from pathlib import Path

from phase400_form144_external_parent_identity_audit import audit


DATA = Path(__file__).with_name("PHASE400_FORM144_EXTERNAL_PARENT_IDENTITY_SUMMARY_2026-11-14.json")


class Phase400Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(DATA.read_text(encoding="utf-8"))
        cls.result = audit(cls.payload)

    def test_all_three_previous_accession_links_are_explicit(self):
        self.assertEqual(self.result["explicit_previous_accession_links"], 3)

    def test_all_three_external_parents_have_issuer_cik_corrections(self):
        self.assertEqual(self.result["issuer_cik_changes"], 3)

    def test_filer_identity_is_stable_across_each_pair(self):
        self.assertEqual(self.result["filer_cik_stable_pairs"], 3)

    def test_proposed_sale_units_and_value_are_unchanged(self):
        self.assertEqual(self.result["sale_units_unchanged_pairs"], 3)
        self.assertEqual(self.result["aggregate_market_value_unchanged_pairs"], 3)

    def test_corrected_issuer_identity_is_not_backdated(self):
        policy = self.result["event_policy"]
        self.assertFalse(policy["amendment_is_new_sale"])
        self.assertFalse(policy["corrected_issuer_identity_may_be_backdated"])
        self.assertEqual(policy["first_correct_issuer_identity_known_date"], "amendment filing date")

    def test_outstanding_field_remains_unusable_as_a_feature(self):
        self.assertEqual(self.result["no_of_units_outstanding_feature"], "KILLED; raw value retained only for version comparison")
        self.assertFalse(self.result["economic_test_authorized"])


if __name__ == "__main__":
    unittest.main()
