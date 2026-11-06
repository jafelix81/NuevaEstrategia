import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase154_13dg_event_date_semantics_audit import audit_rows, base_form, is_quarter_end


def row(accession, form, filing, event, lag="-1", amendment=None, report_date="", person="", ptype="", purpose="", mapping="sec_current"):
    if amendment is None:
        amendment = form.endswith("/A")
    return {
        "ticker": "XYZ", "issuer_cik": "0000000001", "form": form,
        "filing_date": filing, "report_date": report_date, "event_date": event,
        "filing_lag_business_days": lag, "accession": accession,
        "reporting_person": person, "reporting_person_type": ptype,
        "purpose_text": purpose, "event_date_available": "True" if event else "False",
        "is_amendment": str(amendment), "mapping_source": mapping,
    }


class Phase154Tests(unittest.TestCase):
    def test_quarter_end_calendar(self):
        self.assertTrue(is_quarter_end(date(2024, 3, 31)))
        self.assertTrue(is_quarter_end(date(2024, 6, 30)))
        self.assertTrue(is_quarter_end(date(2024, 9, 30)))
        self.assertTrue(is_quarter_end(date(2024, 12, 31)))
        self.assertFalse(is_quarter_end(date(2024, 3, 30)))
        self.assertFalse(is_quarter_end(date(2024, 2, 29)))

    def test_base_form(self):
        self.assertEqual(base_form("SC 13G/A"), "SC 13G")
        self.assertEqual(base_form("SC 13D"), "SC 13D")

    def test_13g_quarter_end_is_separated_from_13d(self):
        rows = [
            row("0000000001-24-000001", "SC 13G", "2024-11-14", "2024-09-30", "-1", False),
            row("0000000001-24-000002", "SC 13G/A", "2024-11-14", "2024-09-30", "-1", True),
            row("0000000001-24-000003", "SC 13D", "2024-11-14", "2024-11-01", "-1", False),
        ]
        r = audit_rows(rows, "outer", "inner")
        g = r["quarter_end_event_date_by_form_regime"]
        self.assertEqual(g["SC 13G|original|post_2024-09-30"]["quarter_end_event_count"], 1)
        self.assertEqual(g["SC 13G/A".replace("/A", "") + "|amendment|post_2024-09-30"]["quarter_end_event_count"], 1)
        self.assertEqual(g["SC 13D|original|post_2024-09-30"]["quarter_end_event_count"], 0)

    def test_future_event_date_is_counted_and_quarantined(self):
        rows = [row("0000000001-24-000001", "SC 13G", "2024-11-14", "2024-11-15")]
        r = audit_rows(rows, "o", "i")
        self.assertEqual(r["event_date_quality"]["after_filing"], 1)
        self.assertEqual(r["event_date_quality"]["future_event_rows"][0]["accession"], "0000000001-24-000001")

    def test_invalid_negative_lag_field_is_flagged(self):
        rows = [row("0000000001-24-000001", "SC 13D", "2024-11-14", "2024-11-01", "-1")]
        r = audit_rows(rows, "o", "i")
        self.assertEqual(r["reported_filing_lag_business_days"]["negative_rows"], 1)
        self.assertIn("INVALID_DO_NOT_USE", r["reported_filing_lag_business_days"]["decision"])

    def test_missing_report_date_and_person_coverage_are_visible(self):
        rows = [row("0000000001-24-000001", "SC 13D", "2024-11-14", "2024-11-01")]
        r = audit_rows(rows, "o", "i")
        self.assertEqual(r["field_coverage"]["report_date_missing"], 1)
        self.assertEqual(r["field_coverage"]["reporting_person_missing"], 1)

    def test_accession_duplicates_are_not_hidden(self):
        rows = [
            row("0000000001-24-000001", "SC 13D", "2024-11-14", "2024-11-01"),
            row("0000000001-24-000001", "SC 13D", "2024-11-14", "2024-11-01"),
        ]
        r = audit_rows(rows, "o", "i")
        self.assertEqual(r["identity_and_integrity"]["duplicate_accession_rows"], 1)

    def test_pre_post_regime_uses_filing_date(self):
        rows = [
            row("0000000001-24-000001", "SC 13G", "2024-09-29", "2024-06-30"),
            row("0000000001-24-000002", "SC 13G", "2024-09-30", "2024-06-30"),
        ]
        r = audit_rows(rows, "o", "i")
        g = r["quarter_end_event_date_by_form_regime"]
        self.assertIn("SC 13G|original|pre_2024-09-30", g)
        self.assertIn("SC 13G|original|post_2024-09-30", g)

    def test_missing_event_date_does_not_enter_denominator(self):
        rows = [
            row("0000000001-24-000001", "SC 13G", "2024-11-14", ""),
            row("0000000001-24-000002", "SC 13G", "2024-11-14", "2024-09-30"),
        ]
        r = audit_rows(rows, "o", "i")
        g = r["quarter_end_event_date_by_form_regime"]["SC 13G|original|post_2024-09-30"]
        self.assertEqual(g["event_missing"], 1)
        self.assertEqual(g["event_valid"], 1)
        self.assertEqual(g["quarter_end_event_pct_of_valid"], 100.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
