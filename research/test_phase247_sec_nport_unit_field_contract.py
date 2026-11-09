import unittest
from decimal import Decimal
from research.phase247_sec_nport_unit_field_contract import (
    build_audit, legacy_phase27o_share_balance, parse_long_equity_share_balance
)


class Phase247NportUnitContractTests(unittest.TestCase):
    def valid_row(self):
        return {"BALANCE": "949.00000000", "UNIT": "NS", "ASSET_CAT": "EC", "PAYOFF_PROFILE": "Long"}

    def test_official_flattened_schema_uses_singular_unit(self):
        contract = build_audit()["official_flattened_table_contract"]
        self.assertEqual(contract["balance_field"], "BALANCE")
        self.assertEqual(contract["unit_field"], "UNIT")

    def test_valid_long_equity_share_balance(self):
        value, reason = parse_long_equity_share_balance(self.valid_row())
        self.assertEqual(value, Decimal("949.00000000"))
        self.assertEqual(reason, "ELIGIBLE_LONG_EQUITY_SHARES")

    def test_legacy_plural_lookup_fails_on_flattened_row(self):
        row = self.valid_row()
        self.assertEqual(legacy_phase27o_share_balance(row), Decimal("0"))
        self.assertEqual(parse_long_equity_share_balance(row)[0], Decimal("949.00000000"))

    def test_xml_tag_spelling_alone_is_not_flattened_column(self):
        row = {"BALANCE": "100", "UNITS": "NS", "ASSET_CAT": "EC", "PAYOFF_PROFILE": "Long"}
        value, reason = parse_long_equity_share_balance(row)
        self.assertIsNone(value)
        self.assertEqual(reason, "XML_ALIAS_USED_AS_FLAT_COLUMN")

    def test_conflicting_aliases_fail_closed(self):
        row = self.valid_row()
        row["UNITS"] = "PA"
        value, reason = parse_long_equity_share_balance(row)
        self.assertIsNone(value)
        self.assertEqual(reason, "UNIT_ALIAS_CONFLICT")

    def test_principal_amount_is_not_share_count(self):
        row = self.valid_row()
        row["UNIT"] = "PA"
        self.assertEqual(parse_long_equity_share_balance(row)[1], "NOT_NUMBER_OF_SHARES")

    def test_other_units_are_not_share_count(self):
        row = self.valid_row()
        row["UNIT"] = "OU"
        self.assertEqual(parse_long_equity_share_balance(row)[1], "NOT_NUMBER_OF_SHARES")

    def test_non_equity_asset_is_excluded(self):
        row = self.valid_row()
        row["ASSET_CAT"] = "DBT"
        self.assertEqual(parse_long_equity_share_balance(row)[1], "NOT_EQUITY_ASSET")

    def test_short_or_unknown_payoff_is_not_long_flow(self):
        for payoff in ("Short", "", "N/A"):
            row = self.valid_row()
            row["PAYOFF_PROFILE"] = payoff
            self.assertEqual(parse_long_equity_share_balance(row)[1], "NOT_EXPLICIT_LONG")

    def test_bad_balances_are_rejected(self):
        cases = ((None, "MISSING_BALANCE"), ("", "MISSING_BALANCE"),
                 ("abc", "INVALID_BALANCE"), ("NaN", "NONFINITE_BALANCE"),
                 ("0", "NONPOSITIVE_BALANCE"), ("-10", "NONPOSITIVE_BALANCE"))
        for raw, expected in cases:
            row = self.valid_row()
            row["BALANCE"] = raw
            value, reason = parse_long_equity_share_balance(row)
            self.assertIsNone(value)
            self.assertEqual(reason, expected)

    def test_pit_alpha_and_baseline_gates_remain_closed(self):
        disposition = build_audit()["research_disposition"]
        self.assertFalse(disposition["strict_pit_admitted"])
        self.assertFalse(disposition["alpha_test_authorized"])
        self.assertTrue(disposition["f80_frozen"])
        self.assertFalse(disposition["holdout_used"])


if __name__ == "__main__":
    unittest.main()
