import unittest
from research.phase378_cftc_russell_contract_era_audit import build_summary, split_episodes, weekly_interval_summary

def row(day,code="239742",name="RUSSELL E-MINI",oi="1000"):
    return {"report_date_as_yyyy_mm_dd":day+"T00:00:00.000","cftc_contract_market_code":code,
            "market_and_exchange_names":name+" - CHICAGO MERCANTILE EXCHANGE",
            "contract_market_name":name,"cftc_market_code":"CME","open_interest_all":oi}

class Phase378Tests(unittest.TestCase):
    def test_split_contract_code_after_long_absence(self):
        rows=[row("2006-06-13"),row("2006-06-20"),row("2017-09-12"),row("2017-09-19")]
        episodes=split_episodes(rows,break_days=365)
        self.assertEqual(len(episodes),2)
        self.assertEqual(len(episodes[0][0]),2)
        self.assertEqual(episodes[0][1]["gap_days"],4102)

    def test_holiday_shifted_monday_is_not_missing_week(self):
        rows=[row("2026-11-03"),row("2026-11-09"),row("2026-11-17")]
        result=weekly_interval_summary(rows)
        self.assertEqual(result["intervals_over_8_days"],0)
        self.assertEqual(result["inferred_missing_week_count_within_episode"],0)
        self.assertEqual(result["non_tuesday_report_dates"],1)
        self.assertEqual(result["weekly_interval_coverage_pct"],100.0)

    def test_actual_missing_week_is_flagged(self):
        rows=[row("2026-10-20"),row("2026-11-03")]
        result=weekly_interval_summary(rows)
        self.assertEqual(result["intervals_over_8_days"],1)
        self.assertEqual(result["inferred_missing_week_count_within_episode"],1)
        self.assertEqual(result["weekly_interval_coverage_pct"],50.0)

    def test_239742_old_and_new_eras_gate(self):
        rows=[row("2006-06-13"),row("2006-06-20"),row("2017-09-12"),row("2017-09-19"),
              row("2026-11-03","239741","RUSSELL 2000 STOCK INDEX FUTURE"),
              row("2026-11-03","23977A","RUSSELL 2000 MINI INDEX FUTURE")]
        result=build_summary(rows,6,6,123,123)
        self.assertTrue(result["russell_239742_contract_era_split_gate"])
        self.assertEqual(result["series_by_code"]["239742"]["episode_count"],2)
        self.assertFalse(result["pre_launch_rows_eligible_for_primary_tff_feature"])
        self.assertTrue(result["separate_contracts_must_not_be_spliced"])

    def test_duplicate_natural_key_is_rejected(self):
        rows=[row("2026-11-03"),row("2026-11-03","239742","RUSSELL E-MINI","1001"),
              row("2026-11-03","239741","RUSSELL 2000 STOCK INDEX FUTURE"),
              row("2026-11-03","23977A","RUSSELL 2000 MINI INDEX FUTURE")]
        result=build_summary(rows,4,4,123,123)
        self.assertEqual(result["duplicate_natural_key_groups"],1)
        self.assertEqual(result["research_disposition"],"RUSSELL_CONTRACT_ERA_AUDIT_INCOMPLETE")

    def test_missing_series_is_not_accepted(self):
        rows=[row("2026-11-03"),row("2026-11-03","239741","RUSSELL 2000 STOCK INDEX FUTURE")]
        result=build_summary(rows,2,2,123,123)
        self.assertFalse(result["all_russell_codes_present_gate"])

    def test_snapshot_change_fails(self):
        rows=[row("2006-06-13"),row("2006-06-20"),row("2017-09-12"),row("2017-09-19"),
              row("2026-11-03","239741","RUSSELL 2000 STOCK INDEX FUTURE"),
              row("2026-11-03","23977A","RUSSELL 2000 MINI INDEX FUTURE")]
        result=build_summary(rows,6,6,123,124)
        self.assertFalse(result["snapshot_stable_during_retrieval"])
        self.assertEqual(result["research_disposition"],"RUSSELL_CONTRACT_ERA_AUDIT_INCOMPLETE")

    def test_no_raw_data_or_alpha(self):
        rows=[row("2006-06-13"),row("2006-06-20"),row("2017-09-12"),row("2017-09-19"),
              row("2026-11-03","239741","RUSSELL 2000 STOCK INDEX FUTURE"),
              row("2026-11-03","23977A","RUSSELL 2000 MINI INDEX FUTURE")]
        result=build_summary(rows,6,6,123,123)
        self.assertFalse(result["raw_rows_retained"])
        self.assertFalse(result["raw_ids_retained"])
        self.assertFalse(result["forward_returns_used"])
        self.assertFalse(result["alpha_test_authorized"])
        self.assertFalse(result["holdout_used"])
        self.assertFalse(result["f80_changed"])

if __name__=="__main__":
    unittest.main()
