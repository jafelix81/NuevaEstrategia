import unittest

from phase177_sec_13d_pac_date_reconciliation import (
    PAC_COMPATIBLE,
    build_audit,
    reconcile_record,
)


class Phase177PacDateReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.first = {
            "accession": "0001213900-19-010653",
            "acceptance_datetime": "20190614090012",
            "filed_as_of_date": "20190613",
            "date_as_of_change": "20190614",
        }
        self.second = {
            "accession": "0000898822-19-000061",
            "acceptance_datetime": "20190830093859",
            "filed_as_of_date": "20190829",
            "date_as_of_change": "20190830",
        }

    def test_both_forward_date_cases_are_pac_compatible_not_confirmed(self):
        for row in (self.first, self.second):
            result = reconcile_record(row)
            self.assertEqual(result["status"], PAC_COMPATIBLE)
            self.assertFalse(result["exact_pac_payload_verified"])
            self.assertTrue(result["date_as_of_change_matches_acceptance_day"])

    def test_acceptance_timestamp_is_not_backdated(self):
        for row in (self.first, self.second):
            result = reconcile_record(row)
            self.assertEqual(result["acceptance_datetime_raw"], row["acceptance_datetime"])
            self.assertTrue(result["do_not_backdate_to_filed_as_of_date"])
            self.assertFalse(result["same_day_or_intraday_pit_allowed"])
            self.assertEqual(
                result["daily_eligibility_rule"],
                "NEXT_FULL_REGULAR_SESSION_AFTER_ACCEPTANCE_DATE",
            )

    def test_earlier_acceptance_date_is_not_assumed_to_be_pac(self):
        row = {
            "accession": "example",
            "acceptance_datetime": "20190705214802",
            "filed_as_of_date": "20190708",
            "date_as_of_change": "20190705",
        }
        self.assertEqual(
            reconcile_record(row)["status"],
            "ACCEPTANCE_DATE_PRECEDES_FILED_AS_OF_DATE",
        )

    def test_same_day_acceptance_is_distinct(self):
        row = {
            "accession": "example",
            "acceptance_datetime": "20190311165759",
            "filed_as_of_date": "20190311",
            "date_as_of_change": "20190311",
        }
        self.assertEqual(
            reconcile_record(row)["status"],
            "SAME_ACCEPTANCE_AND_FILED_AS_OF_DATE",
        )

    def test_missing_date_change_does_not_confirm_pac(self):
        row = dict(self.first, date_as_of_change=None)
        self.assertEqual(
            reconcile_record(row)["status"],
            "FORWARD_ACCEPTANCE_FILED_DATE_MISMATCH_UNRESOLVED",
        )

    def test_cohort_counts_reconcile(self):
        data = {
            "cohort_55": {
                "acceptance_date_vs_filing_date": {"same": 42, "before": 11, "after": 2},
                "date_as_of_change_vs_acceptance_day": {"same": 54, "missing": 1},
                "date_as_of_change_vs_filed_as_of_date": {
                    "before": 11, "same": 41, "after": 2, "missing": 1
                },
            },
            "records": [self.first, self.second],
        }
        result = build_audit(data)
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["pac_compatible_unverified"], 2)
        self.assertEqual(sum(data["cohort_55"]["acceptance_date_vs_filing_date"].values()), 55)
        self.assertEqual(sum(data["cohort_55"]["date_as_of_change_vs_acceptance_day"].values()), 55)
        self.assertEqual(sum(data["cohort_55"]["date_as_of_change_vs_filed_as_of_date"].values()), 55)
        self.assertFalse(result["alpha_test_performed"])
        self.assertFalse(result["final_holdout_used"])


if __name__ == "__main__":
    unittest.main()
