import unittest
from datetime import date, timedelta

from research.phase385_finra_t1_publication_clock_audit import (
    EXPECTED_FIRST, EXPECTED_LAST, EXPECTED_WEEKS,
    validate_weekly_anchors, expected_initial_publication,
    session_strictly_after, build_clock_record,
)


class Phase385Tests(unittest.TestCase):
    def test_209_week_inventory(self):
        weeks = []
        current = EXPECTED_FIRST
        for _ in range(EXPECTED_WEEKS):
            weeks.append(current.isoformat())
            current += timedelta(days=7)
        result = validate_weekly_anchors(weeks)
        self.assertTrue(result["consecutive"])
        self.assertEqual(result["last"], EXPECTED_LAST.isoformat())

    def test_standard_t1_publication_date(self):
        self.assertEqual(
            expected_initial_publication(date(2021, 11, 15)),
            date(2021, 12, 6),
        )

    def test_memorial_day_moves_publication_to_next_session(self):
        # 2022-05-30 was Memorial Day; nominal +21 date is not an NYSE session.
        self.assertEqual(
            expected_initial_publication(date(2022, 5, 9)),
            date(2022, 5, 31),
        )

    def test_execution_session_is_strictly_after_publication(self):
        self.assertEqual(
            session_strictly_after(date(2022, 5, 31)),
            date(2022, 6, 1),
        )

    def test_one_publication_date_and_schedule_pass(self):
        week = date(2021, 11, 15)
        pub = expected_initial_publication(week)
        row = build_clock_record(
            week, {pub}, 100, 100, 0, {0: 100}, 1
        )
        self.assertEqual(row["date_level_clock_gate"], "PASS")
        self.assertEqual(row["first_eligible_nyse_session_strictly_after_publication"], "2021-12-07")


    def test_mixed_t1_response_counts_all_rows_but_dates_only_symbol_aggregates(self):
        week = date(2021, 11, 15)
        pub = expected_initial_publication(week)
        row = build_clock_record(
            week, {pub}, 20, 100, 0, {0: 20}, 1,
            retrieved_row_count=100,
        )
        self.assertTrue(row["retrieval_count_match"])
        self.assertEqual(row["aggregate_rows"], 20)
        self.assertEqual(row["retrieved_rows"], 100)

    def test_multiple_publication_dates_fail_closed(self):
        week = date(2021, 11, 15)
        pub = expected_initial_publication(week)
        row = build_clock_record(
            week, {pub, pub + timedelta(days=1)}, 100, 100, 0, {0: 100}, 1
        )
        self.assertEqual(row["date_level_clock_gate"], "FAIL_OR_REVIEW")
        self.assertIsNone(row["initial_published_date"])

    def test_missing_dates_fail_closed(self):
        week = date(2021, 11, 15)
        pub = expected_initial_publication(week)
        row = build_clock_record(
            week, {pub}, 100, 100, 1, {0: 99}, 1
        )
        self.assertEqual(row["date_level_clock_gate"], "FAIL_OR_REVIEW")

    def test_schedule_mismatch_fails_closed(self):
        week = date(2021, 11, 15)
        pub = expected_initial_publication(week)
        row = build_clock_record(
            week, {pub + timedelta(days=1)}, 100, 100, 0, {0: 100}, 1
        )
        self.assertEqual(row["date_level_clock_gate"], "FAIL_OR_REVIEW")


if __name__ == "__main__":
    unittest.main()
