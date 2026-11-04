import unittest
from research.phase54_cboe_open_close_eod_feasibility import (
    field_coverage, inspect_file, parse_csv_bytes, extract_zip_csvs, to_num,
)

class CboeOpenCloseTests(unittest.TestCase):
    def test_parse_csv_and_field_coverage(self):
        raw="quote_date,underlying_symbol,open_interest,firm_open_buy_vol\n2026-01-02,AAPL,100,20\n"
        parsed=parse_csv_bytes(raw)
        self.assertEqual(len(parsed["rows"]),1)
        self.assertTrue(field_coverage(parsed["headers"],parsed["rows"],"open_interest")["present"])

    def test_numeric_parser(self):
        self.assertEqual(to_num("1,234"),1234.0)
        self.assertIsNone(to_num(""))

    def test_inspect_file_detects_participant_fields_and_universe(self):
        headers="quote_date,underlying_symbol,expiration_date,strike_price,call_put_flag,total_exchange_vol,total_industry_vol,open_interest,previous_open_interest,firm_open_buy_vol,firm_open_sell_vol,mm_buy_vol,mm_sell_vol,cust_lt_100_open_buy_vol,cust_lt_100_open_sell_vol,procust_lt_100_open_buy_vol,procust_lt_100_open_sell_vol"
        row="2026-01-02,AAPL,2026-01-16,150,C,100,500,1000,900,20,5,10,10,40,20,5,2"
        result=inspect_file("C1OpenClose_2026-01-02.csv",(headers+"\n"+row+"\n").encode(),{"AAPL","NVDA"})
        self.assertEqual(result["target_ticker_count"],1)
        self.assertGreater(result["participant_nonzero_rows"],0)
        self.assertEqual(result["field_coverage"]["open_interest"]["nonnull_rate"],1.0)

if __name__=="__main__":
    unittest.main()
