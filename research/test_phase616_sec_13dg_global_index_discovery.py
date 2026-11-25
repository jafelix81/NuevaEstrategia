import unittest
from datetime import date

from research.phase616_sec_13dg_global_index_discovery import (
    accession_from_compact,
    build_index_header_url,
    deduplicate_index_rows,
    filing_regimes,
    normalize_cik,
    parse_master_index,
    stratified_sample,
    validate_user_agent,
)

INDEX_FIXTURE = """Description: SEC Master Index
Last Data Received: 2026-11-24
CIK|Company Name|Form Type|Date Filed|Filename
895421|MORGAN STANLEY|SC 13G|2024-02-12|edgar/data/1793855/000089542124000178/0000895421-24-000178.txt
320193|APPLE INC|10-K|2024-02-01|edgar/data/320193/000032019324000001/aapl-20231230.htm
789019|MICROSOFT CORP|SC 13D/A|2026-08-03|edgar/data/789019/000078901926000123/msft-13da.htm
"""


class Phase616IndexParserTests(unittest.TestCase):
    def test_normalize_cik_preserves_ten_digit_identity(self):
        self.assertEqual(normalize_cik("895421"), "0000895421")
        self.assertIsNone(normalize_cik("ABC"))

    def test_compact_accession_is_formatted_without_using_path_cik(self):
        self.assertEqual(accession_from_compact("000089542124000178"), "0000895421-24-000178")

    def test_header_url_uses_index_archive_path_not_accession_filer_prefix(self):
        url, path_cik = build_index_header_url(
            "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt",
            "0000895421-24-000178",
        )
        self.assertIn("/data/1793855/000089542124000178/", url)
        self.assertTrue(url.endswith("0000895421-24-000178-index-headers.html"))
        self.assertEqual(path_cik, "0001793855")
        self.assertNotIn("/data/895421/", url)

    def test_master_index_separates_filer_from_archive_path_cik(self):
        rows = parse_master_index(
            INDEX_FIXTURE,
            index_url="https://www.sec.gov/Archives/edgar/full-index/2024/QTR1/master.idx",
            index_sha256="a" * 64,
            quarter="2024Q1",
        )
        self.assertEqual(len(rows), 2)
        row = rows[0]
        self.assertEqual(row["index_filer_cik"], "0000895421")
        self.assertEqual(row["accession_filer_cik"], "0000895421")
        self.assertEqual(row["archive_path_cik"], "0001793855")
        self.assertIsNone(row["subject_issuer_cik"])
        self.assertTrue(row["index_filer_accession_match"])

    def test_master_index_filters_non_target_forms(self):
        rows = parse_master_index(
            INDEX_FIXTURE,
            index_url="https://www.sec.gov/Archives/edgar/full-index/2024/QTR1/master.idx",
            index_sha256="b" * 64,
            quarter="2024Q1",
        )
        self.assertEqual({r["form"] for r in rows}, {"SC 13G", "SC 13D/A"})

    def test_invalid_archive_path_fails_closed(self):
        bad = INDEX_FIXTURE.replace(
            "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt",
            "edgar/data/895421/not-an-accession/0000895421-24-000178.txt",
        )
        with self.assertRaises(ValueError):
            parse_master_index(
                bad,
                index_url="fixture",
                index_sha256="c" * 64,
                quarter="2024Q1",
            )

    def test_missing_master_index_header_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_master_index("CIK|Form|Date\n", index_url="fixture", index_sha256="d" * 64, quarter="x")

    def test_conflicting_duplicate_accession_fails_closed(self):
        row = {
            "accession": "0000895421-24-000178",
            "index_filer_cik": "0000895421",
            "form": "SC 13G",
            "filing_date": "2024-02-12",
            "filename": "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt",
        }
        conflict = dict(row, form="SC 13D")
        with self.assertRaises(ValueError):
            deduplicate_index_rows([row, conflict])

    def test_identical_duplicate_accession_is_deduplicated(self):
        row = {
            "accession": "0000895421-24-000178",
            "index_filer_cik": "0000895421",
            "form": "SC 13G",
            "filing_date": "2024-02-12",
            "filename": "edgar/data/1793855/000089542124000178/0000895421-24-000178.txt",
        }
        result = deduplicate_index_rows([dict(row), dict(row)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["duplicate_index_occurrences"], 1)

    def test_stratified_sample_is_deterministic_and_spans_buckets(self):
        rows = []
        for family, amendment, legal, schema, n in [
            ("13D", False, "PRE_2024_02_05", "LEGACY_PRE_2023_12_18", 3),
            ("13D", True, "POST_2024_02_05", "MANDATORY_XML_FROM_2024_12_18", 3),
            ("13G", False, "PRE_2024_09_30", "VOLUNTARY_XML_2023_12_18_TO_2024_12_17", 3),
            ("13G", True, "POST_2024_09_30", "MANDATORY_XML_FROM_2024_12_18", 3),
        ]:
            for i in range(n):
                rows.append(
                    {
                        "accession": f"0000000001-26-{len(rows)+1:06d}",
                        "form_family": family,
                        "amendment": amendment,
                        "legal_regime": legal,
                        "schema_regime": schema,
                        "index_filer_accession_match": True,
                    }
                )
        sample_a = stratified_sample(rows, sample_size=8)
        sample_b = stratified_sample(rows, sample_size=8)
        self.assertEqual([r["accession"] for r in sample_a], [r["accession"] for r in sample_b])
        keys = {(r["form_family"], r["amendment"], r["legal_regime"], r["schema_regime"]) for r in sample_a}
        self.assertEqual(len(keys), 4)

    def test_sample_fails_if_global_index_coverage_is_too_small(self):
        with self.assertRaises(ValueError):
            stratified_sample([], sample_size=44)

    def test_filing_regime_boundaries_are_explicit(self):
        self.assertEqual(filing_regimes("SC 13D", date(2024, 2, 4))[1], "PRE_2024_02_05")
        self.assertEqual(filing_regimes("SC 13D", date(2024, 2, 5))[1], "POST_2024_02_05")
        self.assertEqual(filing_regimes("SC 13G", date(2024, 9, 29))[1], "PRE_2024_09_30")
        self.assertEqual(filing_regimes("SC 13G", date(2024, 9, 30))[1], "POST_2024_09_30")
        self.assertEqual(filing_regimes("SC 13G", date(2024, 12, 18))[2], "MANDATORY_XML_FROM_2024_12_18")

    def test_user_agent_requires_monitored_contact_without_exposing_value(self):
        with self.assertRaises(RuntimeError):
            validate_user_agent("")
        with self.assertRaises(RuntimeError):
            validate_user_agent("NuevaEstrategia research research@example.com")
        self.assertEqual(
            validate_user_agent("NuevaEstrategia research analyst@domain.mx"),
            "NuevaEstrategia research analyst@domain.mx",
        )


if __name__ == "__main__":
    unittest.main()
