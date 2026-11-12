import unittest

from phase303_sec_latest_filings_rss_probe import (
    accession_from_url,
    form_from_title,
    group_filing_entries,
    parse_atom,
)


class Phase303RssTests(unittest.TestCase):
    def test_form_type_parses_form4_and_amendment(self):
        self.assertEqual(form_from_title("4 - Example Corp. (0000000123) (Issuer)"), "4")
        self.assertEqual(form_from_title("4/A - Example Corp. (0000000123) (Reporting)"), "4/A")

    def test_accession_parses_dashed_and_compact_urls(self):
        self.assertEqual(
            accession_from_url("https://www.sec.gov/Archives/edgar/data/123/0000000123-26-000001.txt"),
            "0000000123-26-000001",
        )
        self.assertEqual(
            accession_from_url("https://www.sec.gov/Archives/edgar/data/123/000000012326000001/index.htm"),
            "0000000123-26-000001",
        )

    def test_atom_parser_separates_entity_cik_role_from_accession_filer_cik(self):
        payload = b"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Latest filings</title>
          <entry>
            <title>4/A - Example Corp. (0000000123) (Issuer)</title>
            <id>urn:tag:sec.gov,2008:accession-number=0000000999-26-000001</id>
            <updated>2026-11-12T00:01:02-05:00</updated>
            <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/123/000000099926000001/0000000999-26-000001-index.htm"/>
            <summary type="html">Form 4/A filing summary</summary>
          </entry>
        </feed>"""
        entries = parse_atom(payload)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["form_type_from_title"], "4/A")
        self.assertEqual(entries[0]["entity_cik_from_title"], "0000000123")
        self.assertEqual(entries[0]["entity_role_from_title"], "Issuer")
        self.assertEqual(entries[0]["path_cik_from_link"], "123")
        self.assertTrue(entries[0]["path_cik_matches_title_entity"])
        self.assertEqual(entries[0]["accession_from_link"], "0000000999-26-000001")
        self.assertEqual(entries[0]["feed_updated_raw"], "2026-11-12T00:01:02-05:00")

    def test_grouping_preserves_issuer_and_reporting_rows_per_accession(self):
        payload = b"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>4 - Example Corp. (0000000123) (Issuer)</title>
            <id>urn:tag:sec.gov,2008:accession-number=0000000999-26-000001</id>
            <updated>2026-11-12T00:01:02-05:00</updated>
            <link href="https://www.sec.gov/Archives/edgar/data/123/000000099926000001/0000000999-26-000001-index.htm"/>
          </entry>
          <entry>
            <title>4 - Example Insider (0000000456) (Reporting)</title>
            <id>urn:tag:sec.gov,2008:accession-number=0000000999-26-000001</id>
            <updated>2026-11-12T00:01:02-05:00</updated>
            <link href="https://www.sec.gov/Archives/edgar/data/456/000000099926000001/0000000999-26-000001-index.htm"/>
          </entry>
        </feed>"""
        rows = parse_atom(payload)
        filings, orphans = group_filing_entries(rows)
        self.assertEqual(orphans, [])
        self.assertEqual(len(filings), 1)
        self.assertEqual(filings[0]["raw_entity_row_count"], 2)
        self.assertEqual(filings[0]["issuer_ciks"], ["0000000123"])
        self.assertEqual(filings[0]["reporting_ciks"], ["0000000456"])
        self.assertEqual(filings[0]["entity_roles"], ["Issuer", "Reporting"])

    def test_atom_parser_rejects_non_feed_root(self):
        with self.assertRaisesRegex(ValueError, "atom_root_is_not_feed"):
            parse_atom(b"<html><body>not atom</body></html>")


if __name__ == "__main__":
    unittest.main()
