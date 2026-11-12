import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from research.phase342_sec_insider_bulk_sample_audit import (
    aff_gate_required,
    audit_archive,
    key_audit,
    normalize_aff,
    parse_sec_date,
)


class Phase342Tests(unittest.TestCase):
    def test_aff_normalization_preserves_unknown(self):
        self.assertEqual(normalize_aff("0"), "false")
        self.assertEqual(normalize_aff("FALSE"), "false")
        self.assertEqual(normalize_aff("1"), "true")
        self.assertEqual(normalize_aff(""), "unknown")
        self.assertEqual(normalize_aff(None), "unknown")

    def test_checkbox_gate_uses_actual_filing_date(self):
        self.assertFalse(aff_gate_required("31-MAR-2023"))
        self.assertTrue(aff_gate_required("01-APR-2023"))
        self.assertTrue(aff_gate_required("03-APR-2023"))
        self.assertFalse(aff_gate_required(""))
        self.assertEqual(parse_sec_date("31-MAR-2023").isoformat(), "2023-03-31")

    def test_key_audit_separates_exact_and_conflicting_duplicates(self):
        rows = [
            {"ACCESSION_NUMBER": "a", "SK": "1", "V": "x"},
            {"ACCESSION_NUMBER": "a", "SK": "1", "V": "x"},
            {"ACCESSION_NUMBER": "a", "SK": "2", "V": "y"},
            {"ACCESSION_NUMBER": "b", "SK": "", "V": "z"},
        ]
        result = key_audit(rows, ["ACCESSION_NUMBER", "SK"])
        self.assertEqual(result["row_count"], 4)
        self.assertEqual(result["duplicate_key_count"], 1)
        self.assertEqual(result["conflicting_duplicate_key_count"], 0)
        self.assertEqual(result["missing_key_rows"], 1)

    def _make_archive(self, path: Path):
        tables = {
            "SUBMISSION.tsv": (
                ["ACCESSION_NUMBER","DOCUMENT_TYPE","FILING_DATE","ISSUERCIK","ISSUERNAME",
                 "ISSUERTRADINGSYMBOL","PERIOD_OF_REPORT","DATE_OF_ORIG_SUB","AFF10B5ONE"],
                [
                    ["a1","4","31-MAR-2023","1","Issuer A","AAA","30-MAR-2023","",""],
                    ["a2","4","03-APR-2023","2","Issuer B","BBB","31-MAR-2023","","0"],
                    ["a3","4","04-APR-2023","3","Issuer C","CCC","03-APR-2023","",""],
                    ["a4","4","05-APR-2023","4","Issuer D","DDD","04-APR-2023","","0"],
                    ["a5","4","06-APR-2023","5","Issuer E","EEE","05-APR-2023","","0"],
                    ["a6","4/A","07-APR-2023","6","Issuer F","FFF","06-APR-2023","01-APR-2023","0"],
                ],
            ),
            "REPORTINGOWNER.tsv": (
                ["ACCESSION_NUMBER","RPTOWNERCIK"],
                [["a1","11"],["a2","22"],["a3","33"],["a4","44"],["a5","55"],["a5","56"],["a6","66"]],
            ),
            "NONDERIV_TRANS.tsv": (
                ["ACCESSION_NUMBER","NONDERIV_TRANS_SK","SECURITY_TITLE","TRANS_DATE","TRANS_FORM_TYPE",
                 "TRANS_CODE","TRANS_ACQUIRED_DISP_CD","DIRECT_INDIRECT_OWNERSHIP","TRANS_PRICEPERSHARE_FN",
                 "TRANS_SHARES","TRANS_PRICEPERSHARE"],
                [
                    ["a1","1","Common Stock","30-MAR-2023","4","P","A","D","F1","100","10"],
                    ["a2","1","Common Stock","31-MAR-2023","4","P","A","D","F2","100","10"],
                    ["a3","1","Common Stock","03-APR-2023","4","P","A","D","F3","100","10"],
                    ["a4","1","Common Stock","04-APR-2023","4","P","A","D","F4","100","10"],
                    ["a5","1","Common Stock","05-APR-2023","4","P","A","D","F5","100","10"],
                    ["a6","1","Common Stock","06-APR-2023","4","P","A","D","F6","100","10"],
                ],
            ),
            "NONDERIV_HOLDING.tsv": (["ACCESSION_NUMBER","NONDERIV_HOLDING_SK"], []),
            "DERIV_TRANS.tsv": (["ACCESSION_NUMBER","DERIV_TRANS_SK"], []),
            "DERIV_HOLDING.tsv": (["ACCESSION_NUMBER","DERIV_HOLDING_SK"], []),
            "FOOTNOTES.tsv": (
                ["ACCESSION_NUMBER","FOOTNOTE_ID","FOOTNOTE_TXT"],
                [
                    ["a1","F1","Open market purchase of common stock"],
                    ["a2","F2","Open market purchase of common stock"],
                    ["a3","F3","Open market purchase of common stock"],
                    ["a4","F4","Private purchase of common stock"],
                    ["a5","F5","Open market purchase of common stock"],
                    ["a6","F6","Open market purchase of common stock"],
                ],
            ),
            "OWNER_SIGNATURE.tsv": (["ACCESSION_NUMBER","OWNERSIGNATURENAME"], []),
        }
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, (fields, rows) in tables.items():
                buffer = io.StringIO(newline="")
                writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
                writer.writerow(fields)
                writer.writerows(rows)
                zf.writestr(name, buffer.getvalue().encode("utf-8"))

    def test_archive_screen_respects_april_2023_boundary_and_fail_closed_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2023q2_form345.zip"
            self._make_archive(path)
            result = audit_archive(path, "2023Q2")
        self.assertEqual(result["zip_integrity"], "PASS")
        self.assertEqual(result["submission_rows"], 6)
        self.assertEqual(result["candidate_rows"], 2)
        self.assertEqual(result["candidate_accessions"], 2)
        self.assertEqual(result["candidate_issuer_ciks"], 2)
        self.assertEqual({r["accession"] for r in result["candidate_events"]}, {"a1","a2"})
        self.assertEqual(result["aff10b5one_field_present"], True)
        self.assertEqual(result["aff10b5one_by_filing_date_regime"]["pre_effective_date"], {"unknown": 1})
        self.assertEqual(
            result["aff10b5one_by_filing_date_regime"]["post_effective_date"],
            {"false": 3, "unknown": 1},
        )
        self.assertEqual(result["missing_referenced_footnote_ids_in_base_rows"], 0)
        self.assertEqual(result["orphan_rows_total"], 0)
        self.assertEqual(result["key_conflicting_duplicate_count_total"], 0)

    def test_missing_referenced_footnote_cannot_become_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2023q2_form345.zip"
            self._make_archive(path)
            # Replace the archive with a copy whose a2 footnote reference is missing.
            source = {}
            with zipfile.ZipFile(path) as zf:
                source = {n: zf.read(n) for n in zf.namelist()}
            lines = source["NONDERIV_TRANS.tsv"].decode().splitlines()
            parts = lines[2].split("\t")
            parts[8] = "F999"
            lines[2] = "\t".join(parts)
            source["NONDERIV_TRANS.tsv"] = ("\n".join(lines) + "\n").encode()
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, data in source.items():
                    zf.writestr(name, data)
            result = audit_archive(path, "2023Q2")
        self.assertEqual(result["candidate_rows"], 1)
        self.assertEqual(result["missing_referenced_footnote_ids_in_base_rows"], 1)

    def test_archive_rejects_missing_required_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("SUBMISSION.tsv", "ACCESSION_NUMBER\n")
            with self.assertRaises(ValueError):
                audit_archive(path, "2023Q2")


if __name__ == "__main__":
    unittest.main()
