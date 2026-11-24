import unittest

from research.phase603_sec_13dg_global_index_discovery_pilot import (
    build_index_headers_url,
    current_f80_cik_map,
    deterministic_stratified_sample,
    parse_index_path,
    parse_master_index,
    resolve_user_agent,
)


MASTER_INDEX_FIXTURE = """CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
0000895421|MORGAN STANLEY|SC 13G|2024-02-12|edgar/data/1793855/000089542124000178/0000895421-24-000178.txt
0000000001|TEST ISSUER|SC 13D/A|2026-07-01|edgar/data/0000000001/000000000126000001/0000000001-26-000001.txt
0000000002|OTHER|4|2026-07-01|edgar/data/0000000002/000000000226000001/0000000002-26-000001.txt
0000000003|BAD PATH|SC 13D|2026-07-02|bad/path/no-accession.txt
"""


class GlobalIndexPilotTests(unittest.TestCase):
    def test_parse_master_index_keeps_filer_and_archive_path_separate(self):
        rows, invalid = parse_master_index(MASTER_INDEX_FIXTURE)
        self.assertEqual(len(rows), 2)
        first = next(row for row in rows if row["accession"] == "0000895421-24-000178")
        self.assertEqual(first["index_filer_cik"], "0000895421")
        self.assertEqual(first["accession_filer_cik"], "0000895421")
        self.assertEqual(first["archive_path_cik"], "0001793855")
        self.assertEqual(first["form"], "SC 13G")
        self.assertEqual(invalid["invalid_archive_path_cik"], 1)

    def test_parse_index_path_uses_exact_archive_path(self):
        path_cik, accession = parse_index_path(
            "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt"
        )
        self.assertEqual(path_cik, "0001793855")
        self.assertEqual(accession, "0000895421-24-000178")

    def test_build_index_headers_url_uses_master_index_directory_not_filer_prefix(self):
        url = build_index_headers_url(
            "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt",
            "0000895421-24-000178",
        )
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/1793855/000089542124000178/0000895421-24-000178-index-headers.html",
        )

    def test_stratified_sample_is_deterministic_and_bounded_per_form_filer_stratum(self):
        records = []
        for form in ("SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"):
            for filer_is_f80 in (False, True):
                for i in range(40):
                    records.append({
                        "form": form,
                        "index_filer_cik": "0000000001" if filer_is_f80 else "0000000002",
                        "accession": f"0000000001-26-{i:06d}" if filer_is_f80 else f"0000000002-26-{i:06d}",
                        "_f80_ciks": {"0000000001"},
                    })
        a = deterministic_stratified_sample(records, max_per_stratum=7)
        b = deterministic_stratified_sample(records, max_per_stratum=7)
        self.assertEqual([x["accession"] for x in a], [x["accession"] for x in b])
        self.assertEqual(len(a), 4 * 2 * 7)
        strata = {}
        for row in a:
            key = (row["form"], row["index_filer_cik"] in row["_f80_ciks"])
            strata[key] = strata.get(key, 0) + 1
        self.assertTrue(all(count == 7 for count in strata.values()))

    def test_current_ticker_mapping_is_explicitly_cik_based(self):
        mapping, unmapped = current_f80_cik_map(
            ["AAA", "BBB"],
            {"0": {"ticker": "AAA", "cik_str": 123}, "1": {"ticker": "OTHER", "cik_str": 456}},
        )
        self.assertEqual(mapping, {"0000000123": "AAA"})
        self.assertEqual(unmapped, ["BBB"])

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

    def test_missing_secret_uses_shared_contact_without_requiring_human_input(self):
        value, source, present, accepted = resolve_user_agent(
            "",
            "NuevaEstrategia research contact@domain.org",
        )
        self.assertEqual(value, "NuevaEstrategia research contact@domain.org")
        self.assertFalse(present)
        self.assertFalse(accepted)


if __name__ == "__main__":
    unittest.main()
