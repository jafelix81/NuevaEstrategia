import unittest

from research.phase111_occ_options_account_type_audit import (
    EXCHANGE_CODES,
    parse_fixed_width,
    parse_report_header,
)


def make_header(date_text: str) -> str:
    return " " * 8 + "H" + date_text + " " * 6 + date_text


def make_row(group="EQUITY", symbol="AAPL", exchange="C", customer=100, firm=200, mm=300):
    return (
        f"{group:<6}{symbol:<6}{exchange}"
        f"{customer:>9}{firm:>9}{mm:>9}"
    )


class Phase111OccParserTests(unittest.TestCase):
    def test_header_dates_parse(self):
        line = make_header("05312019")
        self.assertEqual(parse_report_header(line), ("05312019", "05312019"))

    def test_valid_fixed_width_row(self):
        payload = (make_header("05312019") + "\n" + make_row() + "\n").encode()
        result = parse_fixed_width(payload)
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["unique_symbols"], 1)
        self.assertEqual(result["rows"][0]["customer_volume"], 100)
        self.assertEqual(result["rows"][0]["firm_volume"], 200)
        self.assertEqual(result["rows"][0]["market_maker_volume"], 300)

    def test_blank_volumes_are_zero(self):
        row = f"{'EQUITY':<6}{'MSFT':<6}{'C'}{'':>9}{0:>9}{5:>9}"
        result = parse_fixed_width((row + "\n").encode())
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["customer_volume"], 0)

    def test_unknown_exchange_is_not_silently_accepted(self):
        row = make_row(exchange="?")
        result = parse_fixed_width((row + "\n").encode())
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(len(result["unknown_exchange_rows"]), 1)

    def test_malformed_width_is_reported(self):
        result = parse_fixed_width(b"short\n")
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(len(result["malformed_rows"]), 1)

    def test_negative_volume_is_detected(self):
        row = make_row(customer=-1)
        result = parse_fixed_width((row + "\n").encode())
        self.assertEqual(result["negative_volume_count"], 1)

    def test_duplicate_group_symbol_exchange_is_counted(self):
        row = make_row()
        result = parse_fixed_width((row + "\n" + row + "\n").encode())
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["duplicate_key_count"], 1)

    def test_exchange_dictionary_matches_documented_codes(self):
        self.assertTrue({"A", "B", "C", "D", "E", "I", "M", "Q", "W", "X", "Z"}.issubset(EXCHANGE_CODES))


if __name__ == "__main__":
    unittest.main()
