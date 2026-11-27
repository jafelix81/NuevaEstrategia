import os
import unittest
from datetime import date
from unittest.mock import patch

from research import phase401_form144a_full_parent_identity_census as p401

from research.phase616_sec_13dg_global_index_discovery import (
    accession_from_compact,
    build_index_header_url,
    configure_user_agent,
    deduplicate_index_rows,
    filing_regimes,
    normalize_cik,
    parse_master_index,
    stratified_sample,
    validate_user_agent,
    QUARTERS,
    TARGET_FORMS,
)

INDEX_FIXTURE = """Description: SEC Master Index
Last Data Received: 2026-11-24
CIK|Company Name|Form Type|Date Filed|Filename
1174922|WYNN RESORTS LTD|SC 13G|2023-02-14|edgar/data/1174922/0001193125-23-039159.txt
320193|APPLE INC|10-K|2024-02-01|edgar/data/320193/0000320193-24-000001.txt
789019|MICROSOFT CORP|SC 13D/A|2026-08-03|edgar/data/789019/0000789019-26-000123.txt
"""


class Phase616IndexParserTests(unittest.TestCase):
    def test_normalize_cik_preserves_ten_digit_identity(self):
        self.assertEqual(normalize_cik("895421"), "0000895421")
        self.assertIsNone(normalize_cik("ABC"))

    def test_compact_accession_is_formatted_without_using_path_cik(self):
        self.assertEqual(accession_from_compact("000089542124000178"), "0000895421-24-000178")

    def test_header_url_uses_index_archive_path_not_accession_filer_prefix(self):
        url, path_cik = build_index_header_url(
            "edgar/data/1793855/0000895421-24-000178.txt",
            "0000895421-24-000178",
        )
        self.assertIn("/data/1793855/000089542124000178/", url)
        self.assertTrue(url.endswith("0000895421-24-000178-index-headers.html"))
        self.assertEqual(path_cik, "0001793855")
        self.assertNotIn("/data/895421/", url)

    def test_official_sec_flat_master_index_path_maps_to_accession_directory(self):
        url, path_cik = build_index_header_url(
            "edgar/data/1122304/0001193125-15-118890.txt",
            "0001193125-15-118890",
        )
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/1122304/000119312515118890/0001193125-15-118890-index-headers.html",
        )
        self.assertEqual(path_cik, "0001122304")

    def test_accession_directory_is_not_a_master_index_filename(self):
        with self.assertRaises(ValueError):
            build_index_header_url(
                "edgar/data/1122304/000119312515118890/0001193125-15-118890.txt",
                "0001193125-15-118890",
            )

    def test_master_index_subject_candidate_is_separate_from_agent_prefix(self):
        rows = parse_master_index(
            INDEX_FIXTURE,
            index_url="https://www.sec.gov/Archives/edgar/full-index/2023/QTR1/master.idx",
            index_sha256="a" * 64,
            quarter="2023Q1",
        )
        self.assertEqual(len(rows), 2)
        row = rows[0]
        self.assertEqual(row["index_company_cik"], "0001174922")
        self.assertEqual(row["index_company_name"], "WYNN RESORTS LTD")
        self.assertEqual(row["accession_submitter_cik"], "0001193125")
        self.assertEqual(row["archive_path_cik"], "0001174922")
        self.assertIsNone(row["subject_issuer_cik"])
        self.assertFalse(row["index_company_accession_prefix_match"])

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
            "edgar/data/1174922/0001193125-23-039159.txt",
            "edgar/data/895421/not-an-accession.txt",
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
            "index_company_cik": "0001174922",
            "form": "SC 13G",
            "filing_date": "2024-02-12",
            "filename": "edgar/data/1793855/0000895421-24-000178.txt",
        }
        conflict = dict(row, form="SC 13D")
        with self.assertRaises(ValueError):
            deduplicate_index_rows([row, conflict])

    def test_identical_duplicate_accession_is_deduplicated(self):
        row = {
            "accession": "0000895421-24-000178",
            "index_company_cik": "0001174922",
            "form": "SC 13G",
            "filing_date": "2024-02-12",
            "filename": "edgar/data/1793855/0000895421-24-000178.txt",
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
                        "form": f"SC {family}" + ("/A" if amendment else ""),
                        "amendment": amendment,
                        "legal_regime": legal,
                        "schema_regime": schema,
                        "source_quarter": "2024Q1",
                        "index_company_cik": "0000000001",
                        "index_company_accession_prefix_match": True,
                    }
                )
        sample_a = stratified_sample(rows, sample_size=8, required_quarters={"2024Q1"})
        sample_b = stratified_sample(rows, sample_size=8, required_quarters={"2024Q1"})
        self.assertEqual([r["accession"] for r in sample_a], [r["accession"] for r in sample_b])
        keys = {(r["source_quarter"], r["form_family"], r["amendment"], r["legal_regime"], r["schema_regime"]) for r in sample_a}
        self.assertEqual(len(keys), 4)

    def test_stratified_sample_keeps_third_party_agent_prefix_mismatch(self):
        rows = []
        for i, (family, form, amendment) in enumerate(
            [
                ("13D", "SC 13D", False),
                ("13D", "SC 13D/A", True),
                ("13G", "SC 13G", False),
                ("13G", "SC 13G/A", True),
            ],
            start=1,
        ):
            rows.append({
                "accession": f"0001193125-26-{i:06d}",
                "accession_submitter_cik": "0001193125",
                "index_company_cik": "0000000002",
                "index_company_accession_prefix_match": False,
                "form_family": family,
                "form": form,
                "amendment": amendment,
                "legal_regime": "POST_2024_02_05" if family == "13D" else "POST_2024_09_30",
                "schema_regime": "MANDATORY_XML_FROM_2024_12_18",
                "source_quarter": "2026Q3",
            })
        sample = stratified_sample(rows, sample_size=4, required_quarters={"2026Q3"})
        self.assertEqual(len(sample), 4)
        self.assertTrue(all(not row["index_company_accession_prefix_match"] for row in sample))

    def test_sample_fails_if_global_index_coverage_is_too_small(self):
        with self.assertRaises(ValueError):
            stratified_sample([], sample_size=44)

    def test_sample_fails_if_one_of_the_four_exact_forms_is_missing(self):
        rows = [
            {
                "accession": f"0000000001-26-{i:06d}",
                "form_family": family,
                "form": form,
                "amendment": amendment,
                "legal_regime": "POST_2024_02_05" if family == "13D" else "POST_2024_09_30",
                "schema_regime": "MANDATORY_XML_FROM_2024_12_18",
                "source_quarter": "2026Q3",
                "index_company_cik": "0000000001",
                        "index_company_accession_prefix_match": True,
            }
            for i, (family, form, amendment) in enumerate(
                [
                    ("13D", "SC 13D", False),
                    ("13D", "SC 13D/A", True),
                    ("13G", "SC 13G", False),
                ],
                start=1,
            )
        ]
        with self.assertRaises(ValueError):
            stratified_sample(rows, sample_size=3, required_quarters={"2026Q3"})

    def test_sample_includes_all_five_preregistered_quarters(self):
        quarter_labels = [f"{year}Q{quarter}" for year, quarter in QUARTERS]
        rows = []
        accession_number = 1
        for quarter in quarter_labels:
            for family, amendment, form in [
                ("13D", False, "SC 13D"),
                ("13D", True, "SC 13D/A"),
                ("13G", False, "SC 13G"),
                ("13G", True, "SC 13G/A"),
            ]:
                legal = (
                    "PRE_2024_02_05" if family == "13D" and quarter == "2023Q4"
                    else "PRE_2024_09_30" if family == "13G" and quarter in {"2023Q4", "2024Q1", "2024Q3"}
                    else "POST_2024_02_05" if family == "13D"
                    else "POST_2024_09_30"
                )
                schema = (
                    "VOLUNTARY_XML_2023_12_18_TO_2024_12_17"
                    if quarter != "2026Q3"
                    else "MANDATORY_XML_FROM_2024_12_18"
                )
                for _ in range(3):
                    rows.append({
                        "accession": f"0000000001-26-{accession_number:06d}",
                        "form_family": family,
                        "form": form,
                        "amendment": amendment,
                        "legal_regime": legal,
                        "schema_regime": schema,
                        "source_quarter": quarter,
                        "index_company_cik": "0000000001",
                        "index_company_accession_prefix_match": True,
                    })
                    accession_number += 1
        sample = stratified_sample(rows, sample_size=44)
        self.assertEqual({r["source_quarter"] for r in sample}, set(quarter_labels))
        self.assertEqual({r["form"] for r in sample}, TARGET_FORMS)

    def test_sample_fails_if_a_preregistered_quarter_is_absent(self):
        rows = []
        accession_number = 1
        for year, quarter in QUARTERS[:-1]:
            label = f"{year}Q{quarter}"
            for family, amendment, form in [
                ("13D", False, "SC 13D"),
                ("13D", True, "SC 13D/A"),
                ("13G", False, "SC 13G"),
                ("13G", True, "SC 13G/A"),
            ]:
                for _ in range(3):
                    rows.append({
                        "accession": f"0000000001-26-{accession_number:06d}",
                        "form_family": family,
                        "form": form,
                        "amendment": amendment,
                        "legal_regime": "POST_2024_02_05" if family == "13D" else "POST_2024_09_30",
                        "schema_regime": "VOLUNTARY_XML_2023_12_18_TO_2024_12_17",
                        "source_quarter": label,
                        "index_company_cik": "0000000001",
                        "index_company_accession_prefix_match": True,
                    })
                    accession_number += 1
        with self.assertRaises(ValueError):
            stratified_sample(rows, sample_size=44)

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
        with self.assertRaises(RuntimeError):
            validate_user_agent("NuevaEstrategia research research@example.org")
        self.assertEqual(
            validate_user_agent("NuevaEstrategia research analyst@domain.mx"),
            "NuevaEstrategia research analyst@domain.mx",
        )

    def test_missing_secret_uses_existing_shared_project_contact(self):
        fallback = "NuevaEstrategia quantitative research fallback@example.net"
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(p401, "SEC_UA", fallback),
        ):
            self.assertEqual(configure_user_agent(), fallback)

    def test_placeholder_secret_uses_existing_shared_project_contact(self):
        fallback = "NuevaEstrategia quantitative research fallback@example.net"
        with (
            patch.dict(os.environ, {
                "SEC_USER_AGENT": "NuevaEstrategia contact your-email@example.com"
            }, clear=True),
            patch.object(p401, "SEC_UA", fallback),
        ):
            self.assertEqual(configure_user_agent(), fallback)

    def test_valid_secret_overrides_shared_project_contact(self):
        secret = "NuevaEstrategia quantitative research analyst@domain.mx"
        fallback = "NuevaEstrategia quantitative research fallback@example.net"
        with (
            patch.dict(os.environ, {"SEC_USER_AGENT": secret}, clear=True),
            patch.object(p401, "SEC_UA", fallback),
        ):
            self.assertEqual(configure_user_agent(), secret)

    def test_invalid_secret_and_invalid_fallback_fail_before_any_request(self):
        with (
            patch.dict(os.environ, {"SEC_USER_AGENT": "placeholder"}, clear=True),
            patch.object(p401, "SEC_UA", "also-placeholder"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no SEC request was made"):
                configure_user_agent()


if __name__ == "__main__":
    unittest.main()
