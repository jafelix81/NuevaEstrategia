import unittest
from phase212_form144_route_identifiability_audit import SAMPLE, audit, infer_transaction_route

class RouteIdentifiabilityTests(unittest.TestCase):
    def test_five_unique_accessions(self):
        self.assertEqual(len(SAMPLE), 5)
        self.assertEqual(len({r["accession"] for r in SAMPLE}), 5)

    def test_same_rendered_intermediary_header(self):
        self.assertEqual({r["header"] for r in SAMPLE}, {"Name and Address of the Broker"})

    def test_no_explicit_route_flag_is_present(self):
        self.assertTrue(all("route" not in r for r in SAMPLE))

    def test_known_crd_does_not_infer_transaction_route(self):
        for row in SAMPLE:
            self.assertEqual(infer_transaction_route(row), "UNKNOWN_NOT_ENCODED")

    def test_three_distinct_intermediary_strings(self):
        self.assertEqual(len({r["intermediary"].casefold() for r in SAMPLE}), 3)

    def test_two_current_crd_candidates(self):
        self.assertEqual({r["crd"] for r in SAMPLE if r["crd"]}, {"5393", "7784"})

    def test_schw_parent_name_stays_unresolved(self):
        row = next(r for r in SAMPLE if r["ticker"] == "SCHW")
        self.assertIsNone(row["crd"])
        self.assertEqual(infer_transaction_route(row), "UNKNOWN_NOT_ENCODED")

    def test_fail_closed_decision(self):
        result = audit()
        self.assertFalse(result["route_specific_test_authorized"])
        self.assertTrue(result["mixed_route_event_conditional_only"])
        self.assertFalse(result["alpha_test_authorized"])

    def test_controls_preserved(self):
        result = audit()
        self.assertFalse(result["holdout_used"])
        self.assertTrue(result["f80_frozen"])

if __name__ == "__main__":
    unittest.main()
