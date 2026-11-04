import unittest
from research.phase53_occ_volume_query_universe_audit import (
    inspect_response, parse_csv, volume_url,
)

class OCCVolumeQueryTests(unittest.TestCase):
    def test_volume_query_omits_contract_date_filter(self):
        url=volume_url("2026-11-02","AAPL")
        self.assertIn("accountType=ALL",url)
        self.assertIn("porc=BOTH",url)
        self.assertNotIn("contractDt",url)

    def test_all_series_response_without_contract_date_is_valid(self):
        raw=(
            "quantity,underlying,symbol,actype,porc,exchange,actdate\n"
            "100,AAPL,AAPL,C,C,CBOE,11/02/2026\n"
            "50,AAPL,2AAPL,F,P,PHLX,11/02/2026\n"
        )
        result=inspect_response(raw,"AAPL","2026-11-02")
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["account_types"],["C","F"])

    def test_schema_and_account_type_parsing(self):
        raw=(
            "quantity,underlying,symbol,actype,porc,exchange,actdate,contractDate\n"
            "100,AAPL,AAPL,C,C,CBOE,11/02/2026,01/16/2027\n"
            "50,AAPL,AAPL,F,P,PHLX,11/02/2026,01/16/2027\n"
        )
        parsed=parse_csv(raw)
        result=inspect_response(raw,"AAPL","2026-11-02")
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["account_types"],["C","F"])
        self.assertEqual(result["put_call_values"],["C","P"])
        self.assertEqual(result["quantities_by_account_type"]["C"],100)
        self.assertEqual(result["activity_date_match_rate"],1.0)

if __name__=="__main__":
    unittest.main()
