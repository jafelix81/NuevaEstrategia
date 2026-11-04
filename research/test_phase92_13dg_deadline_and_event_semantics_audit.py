import unittest
from datetime import date

import holidays

from research.phase92_13dg_deadline_and_event_semantics_audit import (
    add_business_days, add_calendar_days_adjust, classify_event_text,
    deadline_candidates, quarter_end,
)


class Phase92DeadlineEventTests(unittest.TestCase):
    def setUp(self):
        self.cal = holidays.UnitedStates(years=range(2024, 2027), observed=True)

    def test_quarter_end(self):
        self.assertEqual(quarter_end(date(2025, 12, 15)), date(2025, 12, 31))
        self.assertEqual(quarter_end(date(2025, 1, 2)), date(2025, 3, 31))

    def test_45_day_quarter_deadline_rolls_weekend_and_presidents_day(self):
        raw_due = date(2026, 2, 14)  # Saturday
        self.assertEqual(add_calendar_days_adjust(date(2025, 12, 31), 45, self.cal), date(2026, 2, 17))

    def test_13g_qii_initial_45_days_after_quarter_end(self):
        result = deadline_candidates("13G", "SC 13G", date(2025, 12, 31), date(2026, 2, 17),
                                     {"rule 13d-1(b)"}, 5.2, self.cal)
        self.assertEqual(result["base_due_date"], "2026-02-17")
        self.assertEqual(result["deadline_status"], "base_deadline_met")

    def test_13g_qii_initial_january_event_due_may_15(self):
        result = deadline_candidates("13G", "SC 13G", date(2025, 1, 2), date(2025, 5, 14),
                                     {"rule 13d-1(b)"}, 6.0, self.cal)
        self.assertEqual(result["base_due_date"], "2025-05-15")
        self.assertEqual(result["deadline_status"], "base_deadline_met")

    def test_13g_passive_initial_five_business_days(self):
        result = deadline_candidates("13G", "SC 13G", date(2025, 1, 2), date(2025, 1, 9),
                                     {"rule 13d-1(c)"}, 6.0, self.cal)
        self.assertEqual(result["base_due_date"], "2025-01-09")
        self.assertEqual(result["deadline_status"], "base_deadline_met")

    def test_13d_initial_and_amendment_business_day_deadlines(self):
        initial = deadline_candidates("13D", "SC 13D", date(2025, 6, 9), date(2025, 6, 16),
                                       set(), 11.8, self.cal)
        amendment = deadline_candidates("13D", "SC 13D/A", date(2025, 6, 9), date(2025, 6, 11),
                                        set(), 11.8, self.cal)
        self.assertEqual(initial["base_due_date"], "2025-06-16")
        self.assertEqual(amendment["base_due_date"], "2025-06-11")

    def test_event_classifier_separates_award_merger_and_client_aggregation(self):
        award, _ = classify_event_text("stock award under an employee equity incentive plan")
        merger, _ = classify_event_text("business combination closed on June 18")
        clients, _ = classify_event_text("No one person has greater than 5% economic ownership; shares held by clients")
        self.assertIn("employee_equity_award", award)
        self.assertIn("business_combination_or_merger", merger)
        self.assertIn("aggregated_client_holdings", clients)


if __name__ == "__main__":
    unittest.main()
