import unittest
from datetime import date

from research.phase203_sec_midas_exchange_aggregate_reconciliation import (
    AGG_FIELDS,
    canonical_column,
    deterministic_sample,
    order_based_for_date,
    parse_order_based_base,
    parse_number,
    same_vector,
    sum_present,
)


class Phase203Tests(unittest.TestCase):
    def test_unit_suffix_is_normalized(self):
        self.assertEqual(canonical_column("OrderVol('000)"), "ordervol")
        self.assertEqual(canonical_column(" TradeVolForHidden('000) "), "tradevolforhidden")

    def test_order_based_base_is_read_from_embedded_readme(self):
        readme = "Order-based exchanges: Arca, Bats-Y, Nasdaq, PHLX\nLevel-book exchanges: Amex, NYSE"
        self.assertEqual(parse_order_based_base(readme), {"ARCA", "BATS-Y", "NASDAQ", "PHLX"})

    def test_date_effective_order_based_additions(self):
        readme = (
            "Order-based exchanges: Arca, Bats-Y, Nasdaq, PHLX\n"
            "NYSE beginning May, 2017\n"
            "NSX beginning May 21, 2018\n"
            "CHX beginning November 4, 2019\n"
        )
        base = parse_order_based_base(readme)
        self.assertNotIn("NYSE", order_based_for_date(readme, base, date(2017, 4, 28)))
        self.assertIn("NYSE", order_based_for_date(readme, base, date(2017, 5, 1)))
        self.assertIn("NSX", order_based_for_date(readme, base, date(2018, 5, 21)))
        self.assertIn("CHX", order_based_for_date(readme, base, date(2019, 11, 4)))

    def test_blank_values_are_ignored_but_all_blank_is_none(self):
        self.assertEqual(sum_present([None, 1.25, None, 2.75]), 4.0)
        self.assertIsNone(sum_present([None, None]))

    def test_nonfinite_and_blank_numbers_are_not_admitted(self):
        self.assertIsNone(parse_number(""))
        self.assertIsNone(parse_number("NaN"))
        self.assertEqual(parse_number("1,234.500"), 1234.5)

    def test_activity_duplicate_comparison_ignores_rank_fields_by_design(self):
        self.assertTrue(same_vector((1.0, 2.0, None), (1.0, 2.0, None)))
        self.assertFalse(same_vector((1.0, 2.0, None), (1.0, 2.1, None)))

    def test_aggregate_field_set_is_fixed_and_additive(self):
        self.assertIn("tradesforoddlots", AGG_FIELDS)
        self.assertIn("tradevolforoddlots", AGG_FIELDS)
        self.assertEqual(len(AGG_FIELDS), 12)


if __name__ == "__main__":
    unittest.main()
