import unittest

from research.phase603_sec_13dg_global_index_discovery_pilot import (
    build_submission_url,
    current_f80_cik_map,
    deterministic_stratified_sample,
    extract_ticker_pairs,
    group_index_rows,
    parse_index_path,
    parse_master_index,
    resolve_user_agent,
)


MASTER_INDEX_FIXTURE = """CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
001793855|ABRDN PLC|SC 13G|2024-02-12|edgar/data/1793855/0000895421-24-000178.txt
0000000001|TEST ISSUER|SC 13D/A|2026-07-01|edgar/data/0000000001/000000000126000001/0000000001-26-000001.txt
0000000002|OTHER|4|2026-07-01|edgar/data/0000000002/000000000226000001/0000000002-26-000001.txt
0000000003|BAD PATH|SC 13D|2026-07-02|bad/path/no-accession.txt
"""


class GlobalIndexPilotTests(unittest.TestCase):
    def test_parse_master_index_separates_index_cik_from_accession_filer(self):
        rows, invalid = parse_master_index(MASTER_INDEX_FIXTURE)
        self.assertEqual(len(rows), 2)
        first = next(row for row in rows if row["accession"] == "0000895421-24-000178")
        self.assertEqual(first["index_cik"], "0001793855")
        self.assertEqual(first["archive_path_cik"], "0001793855")
        self.assertEqual(first["accession_filer_cik"], "0000895421")
        self.assertNotEqual(first["index_cik"], first["accession_filer_cik"])
        self.assertEqual(first["archive_path_format"], "flat_accession_file")
        self.assertEqual(invalid["invalid_archive_path_cik"], 1)

    def test_parse_index_path_supports_flat_and_accession_directory_paths(self):
        flat = parse_index_path("edgar/data/1793855/0000895421-24-000178.txt")
        directory = parse_index_path("edgar/data/1793855/000089542124000178/0000895421-24-000178.txt")
        self.assertEqual(flat, ("0001793855", "0000895421-24-000178"))
        self.assertEqual(directory, ("0001793855", "0000895421-24-000178"))

    def test_submission_url_uses_exact_master_index_filename(self):
        url = build_submission_url(
            "edgar/data/1793855/0000895421-24-000178.txt",
            "0000895421-24-000178",
        )
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/1793855/0000895421-24-000178.txt",
        )

    def test_grouping_preserves_multiple_index_rows_for_one_accession(self):
        rows, _ = parse_master_index(MASTER_INDEX_FIXTURE)
        second = dict(rows[0])
        second["index_cik"] = "0000895421"
        second["index_company_name"] = "Filing agent index row"
        groups, exact_duplicates = group_index_rows(rows + [second], {"0001793855"})
        group = next(g for g in groups if g["accession"] == "0000895421-24-000178")
        self.assertEqual(len(group["index_rows"]), 2)
        self.assertEqual(set(group["index_ciks"]), {"0000895421", "0001793855"})
        self.assertTrue(group["any_index_cik_in_f80"])
        self.assertEqual(exact_duplicates, 0)

    def test_stratified_sample_is_deterministic_and_bounded_per_form_and_f80_presence(self):
        groups = []
        for form in ("SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"):
            for f80_present in (False, True):
                for i in range(30):
                    groups.append({
                        "form": form,
                        "form_conflict": False,
                        "filing_date_conflict": False,
                        "accession": f"0000000001-26-{i:06d}-{form[-1]}-{int(f80_present)}",
                        "index_ciks": ["0000000001"] if f80_present else ["0000000002"],
                        "any_index_cik_in_f80": f80_present,
                    })
        a = deterministic_stratified_sample(groups, {"0000000001"}, max_per_stratum=5)
        b = deterministic_stratified_sample(groups, {"0000000001"}, max_per_stratum=5)
        self.assertEqual([x["accession"] for x in a], [x["accession"] for x in b])
        self.assertEqual(len(a), 4 * 2 * 5)

    def test_ticker_sources_parse_object_exchange_and_mutual_fund_shapes(self):
        company = {"0": {"cik_str": 123, "ticker": "AAA", "title": "Alpha"}}
        exchange = {"fields": ["cik", "name", "ticker", "exchange"],
                    "data": [[456, "Beta", "BBB", "NYSE"]]}
        mf = {"fields": ["cik", "seriesId", "classId", "ticker", "name"],
              "data": [[789, "S1", "C1", "CCC", "Gamma"]]}
        self.assertEqual(extract_ticker_pairs(company, "company_tickers.json"), [("AAA", "0000000123")])
        self.assertEqual(extract_ticker_pairs(exchange, "company_tickers_exchange.json"), [("BBB", "0000000456")])
        self.assertEqual(extract_ticker_pairs(mf, "company_tickers_mf.json"), [("CCC", "0000000789")])

    def test_current_f80_mapping_merges_sources_and_quarantines_ticker_conflicts(self):
        mapping, unmapped, conflicts, meta = current_f80_cik_map(
            ["AAA", "BBB", "CCC"],
            {
                "company_tickers.json": {"0": {"ticker": "AAA", "cik_str": 123}},
                "company_tickers_exchange.json": {"fields": ["cik", "name", "ticker", "exchange"],
                                                  "data": [[123, "Alpha", "AAA", "NYSE"],
                                                           [456, "Beta", "BBB", "NYSE"]]},
                "company_tickers_mf.json": {"fields": ["cik", "seriesId", "classId", "ticker", "name"],
                                            "data": [[789, "S1", "C1", "BBB", "Beta fund"]]},
            },
        )
        self.assertEqual(mapping["0000000123"], "AAA")
        self.assertEqual(unmapped, ["CCC"])
        self.assertEqual(conflicts, ["BBB"])
        self.assertEqual(meta["tickers_mapped"], 1)

    def test_user_agent_secret_is_used_without_echoing_it(self):
        value, source, present, accepted = resolve_user_agent(
            "Project research contact analyst@example.org",
            "Fallback project contact fallback@example.org",
        )
        self.assertEqual(value, "Project research contact analyst@example.org")
        self.assertEqual(source, "repository_secret")
        self.assertTrue(present)
        self.assertTrue(accepted)

    def test_placeholder_secret_falls_back_to_shared_valid_contact(self):
        value, source, present, accepted = resolve_user_agent(
            "Project research research@example.com",
            "NuevaEstrategia research contact@domain.org",
        )
        self.assertEqual(value, "NuevaEstrategia research contact@domain.org")
        self.assertEqual(source, "shared_phase401_contact_fallback")
        self.assertTrue(present)
        self.assertFalse(accepted)


if __name__ == "__main__":
    unittest.main()
