import unittest

from research.phase364_finra_weekly_partition_census import (
    parse_partition_payload, summarize_dataset, calendar_week,
)


class Phase364Tests(unittest.TestCase):
    def test_parses_ordered_partition_values(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": ["2025-01-06", "T1"], "versions": ["v1"]},
                {"partitions": ["2025-01-06", "T2"], "versions": ["v1"]},
            ],
        }
        fields, raw, unique = parse_partition_payload(payload)
        self.assertEqual(fields, ("weekStartDate", "tierIdentifier"))
        self.assertEqual(len(raw), 2)
        self.assertEqual({(x["weekStartDate"], x["tierIdentifier"]) for x in unique},
                         {("2025-01-06", "T1"), ("2025-01-06", "T2")})

    def test_parses_dictionary_partitions(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": {"weekStartDate": "2025-01-06", "tierIdentifier": "OTCE"}}
            ],
        }
        _, _, unique = parse_partition_payload(payload)
        self.assertEqual(unique[0]["tierIdentifier"], "OTCE")

    def test_parses_nested_partition_combinations(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": [["2025-01-06", "T1"], ["2025-01-06", "T2"]]}
            ],
        }
        _, raw, unique = parse_partition_payload(payload)
        self.assertEqual(len(raw), 2)
        self.assertEqual(len(unique), 2)

    def test_deduplicates_partition_pairs_but_retains_raw_count(self):
        payload = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": ["2025-01-06", "T1"], "versions": ["v1"]},
                {"partitions": ["2025-01-06", "T1"], "versions": ["v2"]},
            ],
        }
        _, raw, unique = parse_partition_payload(payload)
        self.assertEqual(len(raw), 2)
        self.assertEqual(len(unique), 1)

    def test_summarizes_tiers_and_otce(self):
        metadata = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "fields": [
                {"name": "tierIdentifier", "description": "T1, T2, OTCE"},
                {"name": "initialPublishedDate", "description": "first publication"},
            ],
        }
        partitions = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": ["2025-01-06", "T1"]},
                {"partitions": ["2025-01-13", "T1"]},
                {"partitions": ["2025-01-06", "T2"]},
                {"partitions": ["2025-01-06", "OTCE"]},
            ],
        }
        summary, rows = summarize_dataset("weeklySummaryHistoric", metadata, partitions)
        self.assertEqual(summary["unique_partition_pairs"], 4)
        self.assertTrue(summary["partition_fields_match_expected"])
        self.assertTrue(summary["sample_week_presence"]["2025-01-06"]["T1"])
        self.assertTrue(summary["sample_week_presence"]["2025-01-06"]["T2"])
        self.assertTrue(summary["sample_week_presence"]["2025-01-06"]["OTCE"])
        self.assertFalse(summary["totalNotionalSum_in_metadata"])

    def test_calendar_week_handles_holiday_shift(self):
        self.assertEqual(calendar_week("2025-01-06"), "2025-01-06")
        self.assertEqual(calendar_week("2025-01-07"), "2025-01-06")

    def test_metadata_and_partitions_field_order_mismatch_fails_closed(self):
        metadata = {
            "partitionFields": ["tierIdentifier", "weekStartDate"],
            "fields": [],
        }
        partitions = {
            "partitionFields": ["weekStartDate", "tierIdentifier"],
            "availablePartitions": [
                {"partitions": ["2025-01-06", "T1"]}
            ],
        }
        with self.assertRaises(ValueError):
            summarize_dataset("weeklySummary", metadata, partitions)


if __name__ == "__main__":
    unittest.main()
