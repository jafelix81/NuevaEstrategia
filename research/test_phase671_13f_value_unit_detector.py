import copy
import unittest
from decimal import Decimal

from phase671_13f_value_unit_detector import audit_value_scale


REPORT_DATE = "2026-09-30"


def row(cusip, value, shares, price, **overrides):
    result = {
        "cusip": cusip,
        "title_of_class": "COMMON STOCK",
        "share_type": "SH",
        "put_call": "",
        "value": value,
        "shares": shares,
        "reference_price": price,
        "reference_date": REPORT_DATE,
    }
    result.update(overrides)
    return result


CANADA_LIFE_AMENDMENT = [
    row("06849F108", 71766, 1764862, "40.67"),
    row("070830104", 2214, 139134, "15.92"),
    row("09290D101", 111382, 105330, "1058.29"),
    row("573874104", 223843, 848130, "264.21"),
]

HOME_FEDERAL_CONTROL = [
    row("037833100", 9869714, 29637, "333.02"),
    row("023135106", 338096, 1357, "249.15"),
    row("594918104", 7341139, 14313, "512.90"),
    row("67066G104", 1224116, 5360, "228.38"),
    row("11135F101", 823542, 2345, "351.19"),
]

CANADA_LIFE_BASE_SPARSE = [
    row("037833100", 3812648, 11461129, "333.02"),
    row("023135106", 1997269, 8026987, "249.15"),
]


class Form13FValueUnitDetectorTests(unittest.TestCase):
    def test_canada_life_amendment_is_legacy_thousands_candidate(self):
        result = audit_value_scale(CANADA_LIFE_AMENDMENT, report_date=REPORT_DATE)
        self.assertEqual(result["status"], "LEGACY_THOUSANDS_CANDIDATE")
        self.assertEqual(result["scale_factor_candidate"], 1000)
        self.assertEqual(result["eligible_unique_cusips"], 4)
        self.assertEqual(result["candidate_scores"]["1000"]["consensus_fraction"], "1")
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["trading_signal_eligible"])

    def test_home_federal_same_quarter_control_is_nearest_dollar_candidate(self):
        result = audit_value_scale(HOME_FEDERAL_CONTROL, report_date=REPORT_DATE)
        self.assertEqual(result["status"], "NEAREST_DOLLAR_CANDIDATE")
        self.assertEqual(result["scale_factor_candidate"], 1)
        self.assertEqual(result["eligible_unique_cusips"], 5)
        self.assertEqual(result["candidate_scores"]["1"]["consensus_fraction"], "1")
        self.assertFalse(result["normalization_applied"])

    def test_two_row_canada_life_base_filing_fails_closed(self):
        result = audit_value_scale(CANADA_LIFE_BASE_SPARSE, report_date=REPORT_DATE)
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(result["scale_factor_candidate"])
        self.assertEqual(result["eligible_unique_cusips"], 2)

    def test_mixed_units_are_not_classified(self):
        mixed = CANADA_LIFE_AMENDMENT[:2] + HOME_FEDERAL_CONTROL[:2]
        result = audit_value_scale(mixed, report_date=REPORT_DATE)
        self.assertEqual(result["status"], "MIXED_OR_UNRESOLVED")
        self.assertIsNone(result["scale_factor_candidate"])

    def test_non_common_options_prn_and_wrong_date_are_excluded(self):
        sample = CANADA_LIFE_AMENDMENT + [
            row("594918104", 7341139, 14313, "512.90", put_call="CALL"),
            row("67066G104", 1224116, 5360, "228.38", share_type="PRN"),
            row("11135F101", 823542, 2345, "351.19", title_of_class="PFD"),
            row("023135106", 338096, 1357, "249.15", reference_date="2026-09-29"),
        ]
        result = audit_value_scale(sample, report_date=REPORT_DATE)
        self.assertEqual(result["eligible_unique_cusips"], 4)
        self.assertEqual(result["status"], "LEGACY_THOUSANDS_CANDIDATE")
        self.assertEqual(result["excluded_rows_by_reason"]["put_or_call"], 1)
        self.assertEqual(result["excluded_rows_by_reason"]["non_share_amount"], 1)
        self.assertEqual(result["excluded_rows_by_reason"]["non_common_class"], 1)
        self.assertEqual(result["excluded_rows_by_reason"]["reference_date_mismatch"], 1)

    def test_duplicate_cusip_rows_are_aggregated_and_not_double_counted(self):
        sample = CANADA_LIFE_AMENDMENT + [
            row("06849F108", 35883, 882431, "40.67")
        ]
        result = audit_value_scale(sample, report_date=REPORT_DATE)
        self.assertEqual(result["eligible_unique_cusips"], 4)
        self.assertEqual(result["status"], "LEGACY_THOUSANDS_CANDIDATE")

    def test_source_rows_are_never_mutated_or_rescaled(self):
        sample = copy.deepcopy(CANADA_LIFE_AMENDMENT)
        before = copy.deepcopy(sample)
        result = audit_value_scale(sample, report_date=REPORT_DATE)
        self.assertEqual(sample, before)
        self.assertFalse(result["normalization_applied"])
        self.assertEqual(sample[0]["value"], 71766)

    def test_invalid_cusip_and_nonpositive_values_are_excluded(self):
        sample = CANADA_LIFE_AMENDMENT + [
            row("BAD", 100, 10, "10.0"),
            row("123456789", 0, 10, "10.0"),
        ]
        result = audit_value_scale(sample, report_date=REPORT_DATE)
        self.assertEqual(result["eligible_unique_cusips"], 4)
        self.assertEqual(result["excluded_rows_by_reason"]["invalid_cusip"], 1)
        self.assertEqual(result["excluded_rows_by_reason"]["invalid_or_nonpositive_numeric"], 1)


    def test_conflicting_duplicate_cusip_is_quarantined_permanently(self):
        sample = CANADA_LIFE_AMENDMENT + [
            row("06849F108", 35883, 882431, "41.00"),
            row("06849F108", 35883, 882431, "40.67"),
        ]
        result = audit_value_scale(sample, report_date=REPORT_DATE)
        self.assertEqual(result["eligible_unique_cusips"], 3)
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["excluded_rows_by_reason"]["duplicate_cusip_price_conflict"], 3)

    def test_invalid_thresholds_rejected(self):
        with self.assertRaises(ValueError):
            audit_value_scale(CANADA_LIFE_AMENDMENT, report_date=REPORT_DATE,
                              relative_error_tolerance=Decimal("1"))
        with self.assertRaises(ValueError):
            audit_value_scale(CANADA_LIFE_AMENDMENT, report_date=REPORT_DATE,
                              min_consensus_fraction=Decimal("0"))


if __name__ == "__main__":
    unittest.main()
