import unittest
from datetime import date

from research.phase518_finra_t1_production_window_extension import (
    analyze_week,
    next_nyse_session,
    parse_partitions,
    parse_int,
)


def fixture_rows(pub="2026-01-26", update="2026-01-26"):
    week = "2026-01-05"
    common = {
        "weekStartDate": week,
        "initialPublishedDate": pub,
        "lastUpdateDate": update,
        "issueSymbolIdentifier": "SYNTH",
    }
    return [
        {**common, "summaryTypeCode": "ATS_W_SMBL", "productTypeCode": "CTS",
         "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
        {**common, "summaryTypeCode": "ATS_W_SMBL", "productTypeCode": "UTP",
         "totalWeeklyShareQuantity": "50", "totalWeeklyTradeCount": "5"},
        {**common, "summaryTypeCode": "ATS_W_SMBL_FIRM", "productTypeCode": "CTS",
         "MPID": "AAA", "firmCRDNumber": "1", "marketParticipantName": "Firm A",
         "totalWeeklyShareQuantity": "100", "totalWeeklyTradeCount": "10"},
        {**common, "summaryTypeCode": "ATS_W_SMBL_FIRM", "productTypeCode": "UTP",
         "MPID": "BBB", "firmCRDNumber": "2", "marketParticipantName": "Firm B",
         "totalWeeklyShareQuantity": "50", "totalWeeklyTradeCount": "5"},
    ]


class Phase518Tests(unittest.TestCase):
    def test_partition_payload_accepts_current_week_fields(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": [["2026-01-05", "T1"]], "versions": [1]},
                {"weekStartDate": "2026-01-12", "tierIdentifier": "T1"},
                {"weekStartDate": "2026-01-05", "tierIdentifier": "T1"},
            ],
        }
        records, unique = parse_partitions(payload)
        self.assertEqual(len(records), 3)
        self.assertEqual(len(unique), 2)
        self.assertEqual(unique[0], ("2026-01-05", "T1"))

    def test_aggregate_firm_bridge_and_hhi(self):
        result = analyze_week(fixture_rows(), "2026-01-05", 4, 1)
        self.assertEqual(result["symbol_bridge_gate"], "PASS")
        self.assertEqual(result["revision_stable_concentration_symbols"], 1)
        self.assertAlmostEqual(result["share_coverage_pct"], 100.0)
        self.assertAlmostEqual(result["hhi_mean"], (2/3)**2 + (1/3)**2, places=6)
        self.assertAlmostEqual(result["top1_share_mean"], 2/3, places=6)
        self.assertAlmostEqual(result["top3_share_mean"], 1.0, places=6)
        self.assertEqual(result["participant_count_mean"], 2.0)
        self.assertEqual(result["initial_published_date"], "2026-01-26")
        self.assertTrue(result["date_level_clock_valid"])

    def test_post_publication_revision_excludes_symbol(self):
        rows = fixture_rows(update="2026-01-27")
        result = analyze_week(rows, "2026-01-05", 4, 1)
        self.assertEqual(result["revised_symbols"], 1)
        self.assertEqual(result["revision_stable_concentration_symbols"], 0)
        self.assertEqual(result["share_coverage_pct"], 0.0)

    def test_invalid_publication_lag_fails_clock_and_concentration(self):
        rows = fixture_rows(pub="2026-01-28", update="2026-01-28")
        result = analyze_week(rows, "2026-01-05", 4, 1)
        self.assertFalse(result["date_level_clock_valid"])
        self.assertEqual(result["revision_stable_concentration_symbols"], 0)

    def test_aggregate_firm_mismatch_fails_bridge(self):
        rows = fixture_rows()
        rows[-1]["totalWeeklyShareQuantity"] = "49"
        result = analyze_week(rows, "2026-01-05", 4, 1)
        self.assertEqual(result["symbol_bridge_gate"], "FAIL_OR_REVIEW")
        self.assertEqual(result["revision_stable_concentration_symbols"], 0)

    def test_de_minimis_bucket_is_not_treated_as_participant(self):
        rows = fixture_rows()
        rows[-1]["marketParticipantName"] = "DE MINIMIS"
        result = analyze_week(rows, "2026-01-05", 4, 1)
        self.assertEqual(result["revision_stable_concentration_symbols"], 0)

    def test_parse_int_rejects_invalid_or_fractional_values(self):
        self.assertEqual(parse_int("1,000"), 1000)
        self.assertIsNone(parse_int("-1"))
        self.assertIsNone(parse_int("1.5"))
        self.assertIsNone(parse_int("NaN"))

    def test_next_session_is_strictly_after_publication_date(self):
        sessions = [
            date(2026, 1, 26),
            date(2026, 1, 27),
            date(2026, 1, 28),
        ]
        self.assertEqual(
            next_nyse_session(date(2026, 1, 26), sessions),
            date(2026, 1, 27),
        )


if __name__ == "__main__":
    unittest.main()
