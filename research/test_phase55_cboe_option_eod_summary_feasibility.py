import unittest
from research.phase55_cboe_option_eod_summary_feasibility import (
    field_stats, inspect_file, parse_csv,
)

class OptionEODTests(unittest.TestCase):
    def test_csv_parser(self):
        raw="underlying_symbol,quote_date,open_interest\nAAPL,2026-01-02,100\n"
        parsed=parse_csv(raw)
        self.assertEqual(len(parsed["rows"]),1)

    def test_field_coverage(self):
        headers=["underlying_symbol","open_interest"]
        rows=[{"underlying_symbol":"AAPL","open_interest":"100"}]
        self.assertEqual(field_stats(headers,rows,"open_interest")["nonnull_rate"],1.0)

    def test_inspect_option_eod_sample_schema(self):
        headers="underlying_symbol,quote_date,root,expiration,strike,option_type,open,high,low,close,trade_volume,bid_size_1545,bid_1545,ask_size_1545,ask_1545,active_underlying_price_1545,implied_volatility_1545,delta_1545,gamma_1545,theta_1545,vega_1545,rho_1545,bid_size_eod,bid_eod,ask_size_eod,ask_eod,vwap,open_interest"
        row="AAPL,2026-01-02,AAPL,2026-01-16,150,C,1,2,1,2,100,10,1,12,1.2,250,0.25,0.5,0.1,-0.1,0.2,0.01,10,1,12,1.2,1.5,1000"
        result=inspect_file("option_eod.csv",(headers+"\n"+row+"\n").encode(),{"AAPL","NVDA"})
        self.assertEqual(result["target_ticker_count"],1)
        self.assertEqual(result["option_type_counts"],{"C":1})
        self.assertEqual(result["iv_nonnull_rate"],1.0)
        self.assertEqual(result["open_interest_nonnull_rate"],1.0)

if __name__=="__main__":unittest.main()
