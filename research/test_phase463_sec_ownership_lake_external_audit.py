import unittest
from datetime import datetime, timezone

from research.phase463_sec_ownership_lake_external_audit import (
    available_as_of,
    bulk_timestamp_intraday_eligible,
    classify_form4_purchase,
    cusip_ticker_mapping_covers_date,
    issuer_ticker_identity_status,
    owner_attribution_status,
    quarterly_bulk_available_at,
    snapshot_is_pinned,
    thirteen_f_is_trade_flow,
)


class Phase463SecOwnershipExternalAuditTests(unittest.TestCase):
    def test_quarterly_filing_date_is_end_of_day_new_york(self):
        available = quarterly_bulk_available_at("2026-11-17")
        self.assertEqual(available.isoformat(), "2026-11-18T04:59:59.999000+00:00")

    def test_bulk_date_is_not_available_intraday_but_is_available_next_session(self):
        available = quarterly_bulk_available_at("2026-11-17")
        same_day = datetime(2026, 11, 17, 19, 0, tzinfo=timezone.utc)
        next_session = datetime(2026, 11, 18, 14, 30, tzinfo=timezone.utc)
        self.assertFalse(available_as_of(available, same_day))
        self.assertTrue(available_as_of(available, next_session))
        self.assertFalse(bulk_timestamp_intraday_eligible())

    def test_single_owner_form_is_filing_grain_attributable(self):
        self.assertEqual(owner_attribution_status(1), "single_owner_filing_grain")

    def test_multi_owner_form_without_line_link_is_quarantined(self):
        self.assertEqual(owner_attribution_status(3), "multi_owner_quarantine")

    def test_multi_owner_requires_explicit_transaction_owner_link(self):
        self.assertEqual(owner_attribution_status(3, True), "explicit_line_owner_link")

    def test_p_code_alone_does_not_confirm_open_market_execution(self):
        self.assertEqual(
            classify_form4_purchase("nonderiv", "P", "A"),
            "market_vs_private_unresolved",
        )

    def test_private_purchase_is_not_an_open_market_candidate(self):
        self.assertEqual(
            classify_form4_purchase("nonderiv", "P", "A", "private_purchase"),
            "private_purchase_excluded",
        )

    def test_only_confirmed_nonderivative_acquisition_is_candidate(self):
        self.assertEqual(
            classify_form4_purchase("nonderiv", "P", "A", "open_market_confirmed"),
            "open_market_purchase_candidate",
        )
        self.assertEqual(classify_form4_purchase("nonderiv", "P", "D", "open_market_confirmed"), "not_acquired")
        self.assertEqual(classify_form4_purchase("deriv", "P", "A", "open_market_confirmed"),
                         "derivative_or_non_common_equity_quarantine")

    def test_filer_entered_ticker_is_not_a_canonical_security_identity(self):
        self.assertEqual(
            issuer_ticker_identity_status("LEN, LEN.B", True, False, False),
            "provisional_filer_text_only",
        )
        self.assertEqual(
            issuer_ticker_identity_status("AAPL", True, True, True),
            "verified_effective_dated_security_identity",
        )

    def test_undated_cusip_mapping_is_rejected_without_permanence_evidence(self):
        self.assertFalse(cusip_ticker_mapping_covers_date(None, None, "2013-08-14"))
        self.assertTrue(cusip_ticker_mapping_covers_date(None, None, "2013-08-14", True))

    def test_effective_dated_cusip_mapping_must_cover_holding_date(self):
        self.assertFalse(cusip_ticker_mapping_covers_date("2022-06-09", None, "2020-01-01"))
        self.assertTrue(cusip_ticker_mapping_covers_date("2022-06-09", None, "2024-01-01"))
        self.assertFalse(cusip_ticker_mapping_covers_date("2012-01-01", "2022-06-08", "2024-01-01"))

    def test_snapshot_requires_manifest_source_commit_and_hashes(self):
        digest = "a" * 64
        self.assertTrue(snapshot_is_pinned("2026-10-27T11:17:01Z", "abc123", digest, {"2026.parquet": digest}))
        self.assertFalse(snapshot_is_pinned("2026-10-27T11:17:01Z", None, digest, {"2026.parquet": digest}))
        self.assertFalse(snapshot_is_pinned("2026-10-27T11:17:01Z", "abc123", "not-a-hash", {"2026.parquet": digest}))

    def test_13f_is_not_trade_flow(self):
        self.assertFalse(thirteen_f_is_trade_flow())


if __name__ == "__main__":
    unittest.main()
