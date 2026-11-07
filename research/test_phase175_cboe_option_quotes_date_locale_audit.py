import io
import unittest
import zipfile
from datetime import datetime

from research.phase174_cboe_option_quotes_sample_audit import BASE_REQUIRED
from research.phase175_cboe_option_quotes_date_locale_audit import (
    EXPIRATION_FORMATS, QUOTE_DATETIME_FORMATS, _candidate_interpretations,
    audit_archive, diagnose_csv_bytes,
)


def make_csv(expiration="2025-04-17", quote_datetime="2025-03-28 09:31:00"):
    header = list(BASE_REQUIRED)
    row = [
        "SPY", quote_datetime, "SPY", expiration, "500", "C",
        "1.0", "1.1", "0.9", "1.05", "10", "20", "1.00", "15", "1.10",
        "570.00", "570.10",
    ]
    return (",".join(header) + "\n" + ",".join(row) + "\n").encode()


class Phase175Tests(unittest.TestCase):
    def test_us_expiration_only_when_day_exceeds_twelve(self):
        found, classification, value = _candidate_interpretations("04/17/2025", EXPIRATION_FORMATS)
        self.assertEqual(set(found), {"us_slash"})
        self.assertEqual(classification, "single_format_interpretation")
        self.assertEqual(value.date().isoformat(), "2025-04-17")

    def test_dmy_expiration_only_when_first_component_exceeds_twelve(self):
        found, classification, value = _candidate_interpretations("17/04/2025", EXPIRATION_FORMATS)
        self.assertEqual(set(found), {"dmy_slash"})
        self.assertEqual(classification, "single_format_interpretation")
        self.assertEqual(value.date().isoformat(), "2025-04-17")

    def test_ambiguous_expiration_is_not_selected(self):
        found, classification, value = _candidate_interpretations("04/05/2025", EXPIRATION_FORMATS)
        self.assertEqual(set(found), {"us_slash", "dmy_slash"})
        self.assertEqual(classification, "ambiguous_multiple_interpretations")
        self.assertIsNone(value)

    def test_equivalent_interpretations_do_not_create_false_ambiguity(self):
        found, classification, value = _candidate_interpretations("04/04/2025", EXPIRATION_FORMATS)
        self.assertEqual(set(found), {"us_slash", "dmy_slash"})
        self.assertEqual(classification, "equivalent_multiple_formats")
        self.assertEqual(value.date().isoformat(), "2025-04-04")

    def test_quote_timestamp_locale_ambiguity_is_preserved(self):
        found, classification, value = _candidate_interpretations(
            "04/05/2025 09:31", QUOTE_DATETIME_FORMATS
        )
        self.assertEqual(set(found), {"us_slash_minute", "dmy_slash_minute"})
        self.assertEqual(classification, "ambiguous_multiple_interpretations")
        self.assertIsNone(value)

    def test_iso_quote_timestamp_is_single_interpretation(self):
        found, classification, value = _candidate_interpretations(
            "2025-03-28 09:31:00.123", QUOTE_DATETIME_FORMATS
        )
        self.assertEqual(set(found), {"iso_fraction"})
        self.assertEqual(classification, "single_format_interpretation")
        self.assertEqual(value.second, 0)

    def test_diagnostic_counts_rows_without_persisting_dates_or_symbols(self):
        result = diagnose_csv_bytes(make_csv("04/05/2025", "04/05/2025 09:31"))
        self.assertTrue(result["diagnostic_complete"])
        self.assertEqual(result["populated_rows"], 1)
        self.assertEqual(result["expiration_interpretation_counts"]["ambiguous_multiple_interpretations"], 1)
        self.assertEqual(result["quote_datetime_interpretation_counts"]["ambiguous_multiple_interpretations"], 1)
        self.assertFalse(result["raw_dates_persisted"])
        self.assertFalse(result["raw_timestamps_persisted"])
        self.assertFalse(result["raw_symbols_persisted"])

    def test_iso_sample_row_has_unambiguous_date_fields(self):
        result = diagnose_csv_bytes(make_csv())
        self.assertEqual(result["expiration_interpretation_counts"]["single_format_interpretation"], 1)
        self.assertEqual(result["quote_datetime_interpretation_counts"]["single_format_interpretation"], 1)
        self.assertEqual(result["expiry_after_quote_date_rows"], 1)

    def test_archive_diagnostic_never_admits_sample_or_alpha(self):
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("sample.csv", make_csv("04/05/2025", "04/05/2025 09:31"))
        result = audit_archive(outer.getvalue())
        self.assertTrue(result["date_locale_diagnostic_complete"])
        self.assertEqual(result["date_locale_diagnostic_member_count"], 1)
        self.assertEqual(result["overall_status"], "DIAGNOSTIC_COMPLETE_SAMPLE_NOT_ADMITTED")
        self.assertFalse(result["sample_admission"])
        self.assertFalse(result["pit_admission"])
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["final_holdout_used"])
        self.assertFalse(result["production_changed"])
        self.assertFalse(result["f80_changed"])


if __name__ == "__main__":
    unittest.main()
