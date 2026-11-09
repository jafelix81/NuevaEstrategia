import unittest

from research.phase117_finra_ats_pit_revision_impact import audit_rows


def row(symbol, tier, code, initial, last_update, last_reported, shares, trades):
    return {
        "issueSymbolIdentifier": symbol,
        "tierIdentifier": tier,
        "summaryTypeCode": code,
        "initialPublishedDate": initial,
        "lastUpdateDate": last_update,
        "lastReportedDate": last_reported,
        "totalWeeklyShareQuantity": str(shares),
        "totalWeeklyTradeCount": str(trades),
        "weekStartDate": "2025-01-06",
    }


class Phase117Tests(unittest.TestCase):
    def test_unrevised_row_uses_initial_publication_date(self):
        result = audit_rows([
            row("AAA", "T1", "ATS_W_SMBL", "2025-01-27", "2025-01-27",
                "2025-01-24", 100, 2)
        ])
        self.assertEqual(result["revised_rows"], 0)
        self.assertEqual(result["overall"]["share_volume_retained_if_revised_rows_dropped"], 1.0)

    def test_revised_row_uses_last_reported_date_as_last_update(self):
        result = audit_rows([
            row("AAA", "T1", "OTC_W_SMBL", "2025-01-27", "2025-03-03",
                "2025-03-03", 900, 9),
            row("BBB", "T1", "OTC_W_SMBL", "2025-01-27", "2025-01-27",
                "2025-01-24", 100, 1),
        ])
        self.assertEqual(result["revised_rows"], 1)
        self.assertEqual(result["date_rule_mismatches"], 0)
        self.assertEqual(result["overall"]["share_volume_retained_if_revised_rows_dropped"], 0.1)

    def test_future_revision_status_is_explicitly_labelled_as_non_pit_selection(self):
        result = audit_rows([
            row("AAA", "T1", "OTC_W_SMBL", "2025-01-27", "2025-03-03",
                "2025-03-03", 900, 9),
        ])
        metric = result["by_tier_family"]["T1_OTC"]
        self.assertEqual(metric["symbols_lost_entirely_if_future_revision_status_used"], 1)

    def test_participant_detail_rows_are_not_counted_as_symbol_aggregates(self):
        result = audit_rows([
            row("AAA", "T1", "ATS_W_SMBL", "2025-01-27", "2025-01-27",
                "2025-01-24", 100, 2),
            row("AAA", "T1", "ATS_W_SMBL_FIRM", "2025-01-27", "2025-01-27",
                "2025-01-24", 100, 2),
        ])
        self.assertEqual(result["aggregate_rows"], 1)
        self.assertEqual(result["revised_rows"], 0)

    def test_blank_symbol_is_not_counted_as_a_security(self):
        result = audit_rows([
            row("", "T2", "OTC_W_SMBL", "2025-01-27", "2025-01-27",
                "2025-01-24", 100, 1)
        ])
        metric = result["by_tier_family"]["T2_OTC"]
        self.assertEqual(metric["unique_symbols_nonblank"], 0)

    def test_last_update_mismatch_is_reported_not_silently_accepted(self):
        result = audit_rows([
            row("AAA", "T1", "ATS_W_SMBL", "2025-01-27", "2025-02-01",
                "2025-01-24", 100, 1)
        ])
        self.assertEqual(result["date_rule_mismatches"], 1)


if __name__ == "__main__":
    unittest.main()
