import os
import unittest
from datetime import date
from pathlib import Path
from research.phase225_13dg_event_semantics_lag_audit import (
    _rules, audit, summarize_group, weighted_quantile,
)

class Phase225WeightedQuantileTests(unittest.TestCase):
    def test_weighted_quantile_respects_design_weights(self):
        self.assertEqual(weighted_quantile([1, 40], [1, 10], .5), 40.0)
    def test_empty_quantile_is_none(self):
        self.assertIsNone(weighted_quantile([], [], .5))

class Phase225GroupSummaryTests(unittest.TestCase):
    def test_weighted_and_unweighted_lags_are_separate(self):
        rows=[
            {"event_date":date(2024,3,31),"event_quarter_end":True,"sample_weight":10.0,"lag_calendar_days":40},
            {"event_date":date(2024,3,20),"event_quarter_end":False,"sample_weight":1.0,"lag_calendar_days":1},
            {"event_date":None,"event_quarter_end":False,"sample_weight":1.0,"lag_calendar_days":None},
        ]
        r=summarize_group(rows)
        self.assertEqual(r["n"],3)
        self.assertEqual(r["parsed_n"],2)
        self.assertEqual(r["sample_weighted_coverage_pct"],91.6667)
        self.assertEqual(r["quarter_end_sample_weighted_pct_within_parsed"],90.9091)
        self.assertEqual(r["lag_median_calendar_days_unweighted"],20.5)
        self.assertEqual(r["lag_median_calendar_days_weighted"],40.0)
    def test_future_event_date_is_counted(self):
        r=summarize_group([{"event_date":date(2024,4,2),"event_quarter_end":False,
                            "sample_weight":1.0,"lag_calendar_days":-1}])
        self.assertEqual(r["future_event_date_n"],1)

class Phase225RuleParsingTests(unittest.TestCase):
    def test_rule_designation_json(self):
        self.assertEqual(_rules('["Rule 13d-1(b)"]'),["Rule 13d-1(b)"])
    def test_bad_json_fails_closed(self):
        self.assertEqual(_rules("not-json"),[])

class Phase225ArtifactIntegrationTests(unittest.TestCase):
    def test_phase124_immutable_sample_when_paths_are_supplied(self):
        input_dir=os.environ.get("PHASE124_INPUT_DIR")
        zip_path=os.environ.get("PHASE124_ZIP_PATH")
        if not input_dir or not zip_path:
            self.skipTest("Set PHASE124_INPUT_DIR and PHASE124_ZIP_PATH for immutable-artifact integration.")
        r=audit(Path(input_dir),Path(zip_path))
        self.assertEqual(r["integrity"]["raw_submission_sha256_verified"],600)
        self.assertEqual(r["integrity"]["actual_13dg_rows"],599)
        self.assertEqual(r["integrity"]["structured_xml_event_dates_verified"],102)
        self.assertEqual(r["by_family_and_index_amendment"]["13G_amendment"]["quarter_end_sample_weighted_pct_within_parsed"],82.2679)
        self.assertFalse(r["alpha_test_performed"])
        self.assertFalse(r["final_holdout_used"])

if __name__=="__main__": unittest.main()
