import unittest
from research.phase263_cftc_tff_semiweekly_scope_gate import (
    EXPECTED_STREAMS, adjudicate_tff_cadence, build_evidence, build_result,
)


class Phase263CFTCcadenceTests(unittest.TestCase):
    def test_current_announcement_is_recorded(self):
        self.assertTrue(build_evidence()["cot_semiweekly_plan_announced"])

    def test_announcement_context_is_agricultural(self):
        self.assertTrue(build_evidence()["announcement_scope_is_agricultural_markets"])

    def test_announcement_does_not_explicitly_include_tff(self):
        self.assertFalse(build_evidence()["announcement_explicitly_includes_tff"])

    def test_current_cot_index_still_says_weekly(self):
        self.assertTrue(build_evidence()["current_cot_page_says_weekly"])

    def test_current_faq_still_says_once_weekly(self):
        self.assertTrue(build_evidence()["current_faq_says_once_weekly"])

    def test_both_tff_streams_are_distinct(self):
        e = build_evidence()
        self.assertEqual(set(e["current_tff_streams"]), set(EXPECTED_STREAMS))
        self.assertNotEqual(e["current_tff_streams"]["futures_only"], e["current_tff_streams"]["futures_options_combined"])

    def test_current_tff_report_date_is_pinned(self):
        self.assertEqual(build_evidence()["current_tff_report_date"], "2026-11-03")

    def test_one_report_date_does_not_confirm_semiweekly(self):
        result = adjudicate_tff_cadence(build_evidence())
        self.assertFalse(result["tff_semiweekly_confirmed"])
        self.assertEqual(result["tff_cadence_disposition"], "RETAIN_WEEKLY_ASSUMPTION_PENDING_TFF_SPECIFIC_CONFIRMATION")

    def test_tff_confirmation_requires_all_three_independent_gates(self):
        e = build_evidence()
        e.update({"announcement_explicitly_includes_tff": True, "official_tff_wednesday_friday_schedule": True, "distinct_tff_report_dates_in_same_week": 2})
        self.assertTrue(adjudicate_tff_cadence(e)["tff_semiweekly_confirmed"])

    def test_missing_official_schedule_blocks_confirmation(self):
        e = build_evidence()
        e.update({"announcement_explicitly_includes_tff": True, "distinct_tff_report_dates_in_same_week": 2})
        self.assertFalse(adjudicate_tff_cadence(e)["tff_semiweekly_confirmed"])

    def test_missing_tff_scope_blocks_confirmation(self):
        e = build_evidence()
        e.update({"official_tff_wednesday_friday_schedule": True, "distinct_tff_report_dates_in_same_week": 2})
        self.assertFalse(adjudicate_tff_cadence(e)["tff_semiweekly_confirmed"])

    def test_missing_stream_fails_closed(self):
        e = build_evidence()
        e["current_tff_streams"].pop("futures_only")
        with self.assertRaises(ValueError):
            adjudicate_tff_cadence(e)

    def test_wrong_report_date_fails_closed(self):
        e = build_evidence()
        e["current_tff_report_date"] = "2026-11-10"
        with self.assertRaises(ValueError):
            adjudicate_tff_cadence(e)

    def test_polling_remains_weekday_and_no_duplicate_workflow(self):
        result = adjudicate_tff_cadence(build_evidence())
        self.assertTrue(result["capture_protocol"]["retain_existing_weekday_polling"])
        self.assertFalse(result["capture_protocol"]["create_duplicate_workflow"])

    def test_report_date_is_not_knowledge_time(self):
        result = adjudicate_tff_cadence(build_evidence())
        self.assertTrue(result["capture_protocol"]["report_date_is_not_knowledge_time"])
        self.assertTrue(result["capture_protocol"]["scheduled_capture_is_first_observed_known_by_not_exact_first_publication"])

    def test_categories_are_not_owner_identity_and_no_alpha(self):
        result = build_result()
        self.assertFalse(result["decision"]["research_disposition"]["category_is_beneficial_owner_identity"])
        self.assertFalse(result["decision"]["research_disposition"]["alpha_admitted"])
        self.assertTrue(result["decision"]["research_disposition"]["f80_frozen"])

    def test_result_keeps_holdout_and_production_closed(self):
        result = build_result()
        self.assertFalse(result["controls"]["holdout_used"])
        self.assertFalse(result["controls"]["production_changed"])
        self.assertFalse(result["controls"]["alpha_admitted"])


if __name__ == "__main__":
    unittest.main()
