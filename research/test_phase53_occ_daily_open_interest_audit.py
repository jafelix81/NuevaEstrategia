import gzip
import unittest

from research.phase53_occ_daily_open_interest_audit import (
    decode_body, extract_contract_rows, occ_oi_url, occ_volume_url,
    parse_csv_payload, parse_osi_root, report_date,
)

class OCCOpenInterestTests(unittest.TestCase):
    def test_gzip_decode(self):
        payload=b"a,b\n1,2\n"
        self.assertEqual(decode_body(gzip.compress(payload)),payload)

    def test_osi_root(self):
        self.assertEqual(parse_osi_root("AAPL  260116C00150000"),"AAPL")
        self.assertEqual(parse_osi_root("NVDA  260116P00100000"),"NVDA")
        self.assertIsNone(parse_osi_root("not-an-osi-symbol"))

    def test_csv_parse_and_underlying_extraction(self):
        raw="Underlying,Option Symbol,Expiration,Strike,Put/Call,Open Interest,Volume\nAAPL,AAPL  260116C00150000,2026-01-16,150,C,1200,300\n"
        parsed=parse_csv_payload(raw); result=extract_contract_rows(parsed)
        self.assertEqual(result["open_interest_column"],"Open Interest")
        self.assertEqual(result["rows"][0]["underlying"],"AAPL")
        self.assertEqual(result["rows"][0]["open_interest"],1200)
        self.assertEqual(result["rows"][0]["volume"],300)

    def test_osi_fallback_without_underlying_column(self):
        parsed=parse_csv_payload("Option Symbol,Open Interest\nNVDA  260116C00100000,800\n")
        result=extract_contract_rows(parsed)
        self.assertEqual(result["rows"][0]["underlying"],"NVDA")

    def test_report_date_format(self):
        self.assertEqual(report_date("2025-01-03"),"01/03/2025")

    def test_occ_urls(self):
        oi=occ_oi_url("2026-11-02")
        self.assertIn("reportDate=11%2F02%2F2026",oi)
        self.assertIn("action=download",oi)
        volume=occ_volume_url("2026-11-02","AAPL","C")
        self.assertIn("volumeQueryType=O",volume)
        self.assertIn("symbolType=U",volume)
        self.assertIn("accountType=C",volume)
        self.assertIn("productKind=OSTK",volume)
        self.assertIn("contractDt=20261102",volume)

if __name__=="__main__":
    unittest.main()
