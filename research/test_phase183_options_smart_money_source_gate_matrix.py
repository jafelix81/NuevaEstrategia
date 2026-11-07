import copy
import json
import unittest

from research.phase183_options_smart_money_source_gate_matrix import audit, DEFAULT_INPUT


class Phase183SourceGateMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
        cls.result = audit(cls.snapshot)

    def test_phase_and_global_status(self):
        self.assertEqual(self.result["phase"], 183)
        self.assertEqual(self.result["status"], "NO_SOURCE_PIT_ADMITTED_NO_ALPHA_TEST_AUTHORIZED")

    def test_all_sources_remain_blocked_from_pit_and_alpha(self):
        self.assertEqual(self.result["pit_admitted_count"], 0)
        self.assertEqual(self.result["alpha_admitted_count"], 0)
        self.assertTrue(all(not x["pit_admitted"] and not x["alpha_admitted"] for x in self.result["sources"]))

    def test_source_ids_and_priority_ranks_are_unique(self):
        ids = [x["id"] for x in self.snapshot["sources"]]
        ranks = [x["priority_rank"] for x in self.snapshot["sources"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ranks), len(set(ranks)))

    def test_tradeflow_and_open_close_are_distinct_constructs(self):
        by_id = {x["id"]: x for x in self.snapshot["sources"]}
        self.assertIn("aggressor", by_id["ivydb_tradeflow"]["construct"])
        self.assertIn("opening/closing", by_id["cboe_open_close"]["construct"])
        self.assertNotEqual(by_id["ivydb_tradeflow"]["construct"], by_id["cboe_open_close"]["construct"])

    def test_open_interest_is_not_directional_flow(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "ivydb_open_interest")
        self.assertIn("not buyer direction", " ".join(source["limitations"]))
        self.assertEqual(source["decision"], "CONDITIONAL_LONG_HISTORY_CONTRACT_STATE")

    def test_tradeflow_backfill_is_not_live_pit(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "ivydb_tradeflow")
        self.assertIn("not proof of live availability", source["knowledge_time"])
        self.assertFalse(source["gates"]["first_receipt_vintages"])

    def test_cboe_open_close_cumulative_snapshot_risk_is_preserved(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "cboe_open_close")
        self.assertIn("cumulative snapshots", source["revision_semantics"])
        self.assertFalse(source["gates"]["revision_lineage"])

    def test_finra_short_flow_is_not_promoted(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "finra_short_volume")
        self.assertEqual(source["decision"], "NO_PROMOTION_REOPEN_ONLY_WITH_NEW_DATA_AND_NEXT_SESSION_EXECUTION")
        self.assertFalse(source["gates"]["historical_universe_coverage"])

    def test_cftc_is_quarantined_for_label_maturity(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "cftc_tff_cot")
        self.assertEqual(source["decision"], "QUARANTINED_REBUILD_ONLY_WITH_CALENDAR_AND_LABEL_EMBARGO")

    def test_sec_form4_existing_family_remains_killed(self):
        source = next(x for x in self.snapshot["sources"] if x["id"] == "sec_form4")
        self.assertEqual(source["decision"], "KILLED_FOR_NOW_EXISTING_FEATURE_FAMILY")

    def test_priority_is_not_an_alpha_ranking(self):
        self.assertFalse(self.snapshot["global_decisions"]["priority_is_expected_alpha_rank"])
        self.assertIn("not expected alpha", self.result["ranking_semantics"])

    def test_f80_and_operational_controls_remain_unchanged(self):
        controls = self.result["controls"]
        self.assertTrue(controls["f80_frozen"])
        self.assertFalse(controls["holdout_used"])
        self.assertFalse(controls["vendor_contact"])
        self.assertFalse(controls["data_purchase"])
        self.assertFalse(controls["production_changed"])

    def test_deterministic_output(self):
        self.assertEqual(self.result, audit(copy.deepcopy(self.snapshot)))

    def test_gate_schema_fails_closed(self):
        broken = copy.deepcopy(self.snapshot)
        broken["sources"][0]["gates"].pop("first_receipt_vintages")
        with self.assertRaises(ValueError):
            audit(broken)

    def test_no_source_can_be_pit_admitted_implicitly(self):
        broken = copy.deepcopy(self.snapshot)
        for key in broken["gate_names"]:
            broken["sources"][0]["gates"][key] = True
        with self.assertRaises(ValueError):
            audit(broken)


if __name__ == "__main__":
    unittest.main()
