import unittest
import zipfile
import io

from research.phase311_nport_accession_census import (
    accession_from_filename,
    parse_master_index,
    parse_master_zip,
    quarter_bounds,
    quarter_list,
    select_stratified_sample,
)

HEADER = "CIK|Company Name|Form Type|Date Filed|Filename"


def row(cik, name, form, filed, accession_digits, filename="primary_doc.xml"):
    return f"{cik}|{name}|{form}|{filed}|edgar/data/{int(cik)}/{accession_digits}/{filename}"


class Phase311NportCensusTests(unittest.TestCase):
    def test_quarter_list_covers_all_28_expected_quarters(self):
        quarters = quarter_list("2019Q4", "2026Q3")
        self.assertEqual(len(quarters), 28)
        self.assertEqual(quarters[0], "2019Q4")
        self.assertEqual(quarters[-1], "2026Q3")

    def test_quarter_bounds(self):
        self.assertEqual(str(quarter_bounds("2019Q4")[0]), "2019-10-01")
        self.assertEqual(str(quarter_bounds("2019Q4")[1]), "2020-01-01")
        self.assertEqual(str(quarter_bounds("2026Q3")[1]), "2026-10-01")

    def test_accession_reconstruction_and_cik_guard(self):
        self.assertEqual(
            accession_from_filename("edgar/data/1145549/000114554922056239/primary_doc.xml", "1145549"),
            "0001145549-22-056239",
        )
        with self.assertRaisesRegex(ValueError, "index_cik_path_cik_mismatch"):
            accession_from_filename("edgar/data/123456/000012345620000001/primary_doc.xml", "999999")

    def test_exact_forms_are_kept_and_nt_prefix_is_excluded(self):
        lines = [
            "Description: Form 13F-HR",
            HEADER,
            "--------------------------------------------------------------------------------",
            row("1145549", "Fund A", "NPORT-P", "2022-09-15", "000114554922056239"),
            row("1145549", "Fund A", "NPORT-P/A", "2022-09-16", "000114554922056240"),
            row("1145549", "Fund A", "NT NPORT-P", "2022-09-16", "000114554922056241"),
            row("1145549", "Fund A", "NPORT-P2", "2022-09-16", "000114554922056242"),
        ]
        result = parse_master_index("\n".join(lines), "2022Q3")
        self.assertEqual([x["form_type"] for x in result], ["NPORT-P", "NPORT-P/A"])
        self.assertEqual(result[0]["accession"], "0001145549-22-056239")

    def test_company_name_pipe_does_not_shift_form_and_filename_columns(self):
        text = "\\n".join([
            HEADER,
            "-----",
            row("1145549", "Fund | Series A", "NPORT-P", "2022-09-15", "000114554922056239"),
        ])
        result = parse_master_index(text, "2022Q3")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["company_name"], "Fund | Series A")
        self.assertEqual(result[0]["form_type"], "NPORT-P")

    def test_target_filing_outside_quarter_fails_closed(self):
        text = "\n".join([
            HEADER,
            "--------------------------------------------------------------------------------",
            row("1145549", "Fund A", "NPORT-P", "2022-10-01", "000114554922056239"),
        ])
        with self.assertRaisesRegex(ValueError, "target_row_outside_quarter"):
            parse_master_index(text, "2022Q3")

    def test_duplicate_accession_in_quarter_fails_closed(self):
        target = row("1145549", "Fund A", "NPORT-P", "2022-09-15", "000114554922056239")
        with self.assertRaisesRegex(ValueError, "duplicate_accession_within_quarter"):
            parse_master_index("\n".join([HEADER, "-----", target, target]), "2022Q3")

    def test_target_form_without_accession_path_fails_closed(self):
        text = "\n".join([
            HEADER,
            "-----",
            "1145549|Fund A|NPORT-P|2022-09-15|bad/path.xml",
        ])
        with self.assertRaisesRegex(ValueError, "target_form_filename_missing_accession_path"):
            parse_master_index(text, "2022Q3")

    def test_missing_header_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "master_index_header_missing"):
            parse_master_index("no header\nno rows", "2022Q3")

    def test_master_zip_requires_one_master_index(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as z:
            z.writestr("master.idx", "\n".join([
                HEADER, "-----",
                row("1145549", "Fund A", "NPORT-P", "2022-09-15", "000114554922056239"),
            ]))
        parsed = parse_master_zip(payload.getvalue(), "2022Q3")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["form_type"], "NPORT-P")

    def test_sample_is_deterministic_and_one_per_quarter_form(self):
        rows = [
            {"quarter": "2022Q3", "form_type": "NPORT-P", "accession": "0000000001-22-000001"},
            {"quarter": "2022Q3", "form_type": "NPORT-P", "accession": "0000000001-22-000002"},
            {"quarter": "2022Q3", "form_type": "NPORT-P/A", "accession": "0000000001-22-000003"},
        ]
        first = select_stratified_sample(rows)
        second = select_stratified_sample(list(reversed(rows)))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)
        self.assertEqual({x["form_type"] for x in first}, {"NPORT-P", "NPORT-P/A"})


if __name__ == "__main__":
    unittest.main()
