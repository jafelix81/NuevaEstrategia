import unittest
from research.phase184_cftc_release_vintage_pit_audit import (
    build_audit, build_rows, label_mature, pit_admissible
)

class Phase184Tests(unittest.TestCase):
    def setUp(self):
        self.audit = build_audit()
        self.rows = build_rows()

    def test_21_documented_exception_rows(self):
        self.assertEqual(len(self.rows), 21)

    def test_2023_ion_has_seven_rows(self):
        self.assertEqual(self.audit["exception_counts"]["ION_2023"], 7)

    def test_2025_shutdown_final_schedule_has_thirteen_rows(self):
        self.assertEqual(self.audit["exception_counts"]["SHUTDOWN_2025_FINAL"], 13)

    def test_2021_holiday_has_one_row(self):
        self.assertEqual(self.audit["exception_counts"]["HOLIDAY_2021"], 1)

    def test_report_dates_are_unique(self):
        dates = [r["report_date"] for r in self.rows]
        self.assertEqual(len(dates), len(set(dates)))

    def test_scheduled_dates_do_not_follow_actual_dates(self):
        for row in self.rows:
            self.assertLessEqual(row["scheduled_release_date"], row["documented_actual_release_date"])

    def test_plus_six_rule_is_early_on_twenty_rows(self):
        self.assertEqual(self.audit["report_date_plus_6_comparison"]["synthetic_earlier_than_documented_release"], 20)

    def test_plus_six_rule_is_same_date_on_one_row(self):
        self.assertEqual(self.audit["report_date_plus_6_comparison"]["synthetic_same_date_time_unknown"], 1)

    def test_2023_first_ion_delay(self):
        row = next(r for r in self.rows if r["report_date"] == "2023-01-31")
        self.assertEqual(row["documented_actual_release_date"], "2023-02-24")

    def test_2023_last_ion_delay(self):
        row = next(r for r in self.rows if r["report_date"] == "2023-03-14")
        self.assertEqual(row["documented_actual_release_date"], "2023-03-21")

    def test_2025_first_shutdown_release(self):
        row = next(r for r in self.rows if r["report_date"] == "2025-09-30")
        self.assertEqual(row["documented_actual_release_date"], "2025-11-19")

    def test_2025_final_schedule_revision_is_used(self):
        row = next(r for r in self.rows if r["report_date"] == "2025-11-18")
        self.assertEqual(row["documented_actual_release_date"], "2025-12-12")

    def test_2021_holiday_date_only(self):
        row = next(r for r in self.rows if r["report_date"] == "2021-06-15")
        self.assertIsNone(row["release_time_et"])
        self.assertEqual(row["documented_actual_release_date"], "2021-06-21")

    def test_first_receipt_missing_blocks_pit(self):
        self.assertFalse(pit_admissible(
            actual_release_date="2025-11-19",
            first_receipt_utc=None,
            next_eligible_exchange_session="2025-11-20",
            identity_resolved=True,
            methodology_versioned=True,
        ))

    def test_next_session_must_follow_release_date(self):
        self.assertFalse(pit_admissible(
            actual_release_date="2025-11-19",
            first_receipt_utc="2025-11-19T20:00:00Z",
            next_eligible_exchange_session="2025-11-19",
            identity_resolved=True,
            methodology_versioned=True,
        ))

    def test_complete_prospective_row_can_pass_data_gate(self):
        self.assertTrue(pit_admissible(
            actual_release_date="2026-11-06",
            first_receipt_utc="2026-11-06T20:35:00Z",
            next_eligible_exchange_session="2026-11-09",
            identity_resolved=True,
            methodology_versioned=True,
        ))

    def test_label_must_end_strictly_before_entry(self):
        self.assertTrue(label_mature("2026-11-05", "2026-11-06"))
        self.assertFalse(label_mature("2026-11-06", "2026-11-06"))

    def test_missing_label_dates_fail_closed(self):
        self.assertFalse(label_mature(None, "2026-11-06"))
        self.assertFalse(label_mature("2026-11-05", None))

    def test_historical_calendar_limit_is_thirteen_months(self):
        self.assertEqual(self.audit["official_historical_release_date_limit_months"], 13)
        self.assertFalse(self.audit["complete_official_release_date_ledger_available_for_2016_2024"])

    def test_phase23c_is_quarantined(self):
        self.assertEqual(self.audit["phase23c_static_findings"]["disposition"], "QUARANTINED_NO_REUSE")

    def test_no_alpha_or_holdout_admission(self):
        self.assertFalse(self.audit["admission"]["alpha_test_authorized"])
        self.assertFalse(self.audit["admission"]["holdout_used"])

    def test_f80_remains_frozen(self):
        self.assertEqual(self.audit["admission"]["f80_baseline"], "FROZEN")

if __name__ == "__main__":
    unittest.main()
