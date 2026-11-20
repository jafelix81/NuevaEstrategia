import unittest

from research.phase535_finra_ats_archive_audit import (
    has_certification_gate,
    parse_date,
    parse_grid,
    parse_report_text,
    select_samples,
)


class Phase535Tests(unittest.TestCase):
    def test_parse_date_common_formats(self):
        self.assertEqual(parse_date("06/01/2015").isoformat(), "2015-06-01")
        self.assertEqual(parse_date("24-MAR-14").isoformat(), "2014-03-24")
        self.assertEqual(parse_date("2025-11-03").isoformat(), "2025-11-03")
        self.assertIsNone(parse_date("not-a-date"))

    def test_certification_gate_detected(self):
        self.assertTrue(has_certification_gate("<h1>User Certification</h1><button>I Agree</button>"))
        self.assertFalse(has_certification_gate("<h1>Download reports</h1><table></table>"))

    def test_grid_parser_extracts_reports_and_direct_links(self):
        html = """
        <table id="tblTrading">
          <tr><th>Year</th><th>Week</th><th>Report Type</th><th>Last Updated</th><th>Download</th></tr>
          <tr><td>2015</td><td>06/01/2015</td><td>NMS Tier 1</td><td>06/26/2015</td><td><a href="/files/t1.txt">download</a></td></tr>
          <tr><td>2015</td><td>05/25/2015</td><td>NMS Tier 2</td><td>06/26/2015</td><td><a href="/files/t2.txt">download</a></td></tr>
        </table>
        """
        parsed = parse_grid(html)
        self.assertTrue(parsed["table_found"])
        self.assertEqual(len(parsed["reports"]), 2)
        self.assertEqual(parsed["reports"][0]["week_date"], "2015-06-01")
        self.assertEqual(parsed["reports"][0]["download_path"], "/files/t1.txt")

    def test_select_samples_uses_oldest_and_latest_per_type(self):
        rows = [
            {"report_type": "NMS Tier 1", "week_date": "2015-01-05", "download_path": "/a"},
            {"report_type": "NMS Tier 1", "week_date": "2015-02-02", "download_path": "/b"},
            {"report_type": "NMS Tier 1", "week_date": "2015-03-02", "download_path": "/c"},
            {"report_type": "NMS Tier 2", "week_date": "2015-01-05", "download_path": "/d"},
        ]
        samples = select_samples(rows)
        self.assertEqual({x["download_path"] for x in samples}, {"/a", "/c", "/d"})

    def test_report_parser_counts_symbols_and_f80_overlap(self):
        f80 = {"AAPL", "MSFT"}
        text = (
            "Report_Type|Symbol|Issue_Description|ATS_Description|ATS_MPID|Shares|Shares_Last_Updated|Trades|Trades_Last_Updated\n"
            "NMS Tier 1|AAPL|Apple|ATS One|ABCD|1000|24-MAR-14|10|24-MAR-14\n"
            "NMS Tier 1|NVDA|Nvidia|ATS Two|EFGH|2000|25-MAR-14|20|25-MAR-14\n"
        )
        result = parse_report_text(text, f80, "NMS Tier 1", "2014-03-17")
        self.assertEqual(result["status"], "PARSED")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["unique_symbols"], 2)
        self.assertEqual(result["unique_ats_mpids"], 2)
        self.assertEqual(result["f80_335_overlap_count_diagnostic_only"], 1)
        self.assertEqual(result["negative_or_invalid_quantity_fields"], 0)


if __name__ == "__main__":
    unittest.main()
