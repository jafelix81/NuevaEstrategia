import io
import json
import unittest
import zipfile
from phase150_form4_asfiled_issuer_symbol_audit import classify_symbol, parse_period_zip

META = {"tables": [{"url": "SUBMISSION.tsv", "tableSchema": {"columns": [
    {"name": "ISSUERCIK", "dc:description": "Central Index Key of Issuer"},
    {"name": "ISSUERNAME", "dc:description": "Name of Issuer"},
    {"name": "ISSUERTRADINGSYMBOL", "dc:description": "Issuer Trading Symbol"},
    {"name": "ACCESSION_NUMBER", "dc:description": "Unique identifier assigned by the SEC to each EDGAR submission"},
]}}]}
HEADER = "ACCESSION_NUMBER\tDOCUMENT_TYPE\tISSUERCIK\tISSUERTRADINGSYMBOL\tISSUERNAME\tFILING_DATE\tPERIOD_OF_REPORT\n"
AFF_DESC = "The transaction was made pursuant to a contract, instruction or written plan for the purchase or sale of equity securities of the issuer that is intended to satisfy the affirmative defense conditions of Rule 10b5-1(c)"

def fixture(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("SUBMISSION.tsv", HEADER + "".join("\t".join(r) + "\n" for r in rows))
        z.writestr("metadata.json", json.dumps(META))
    return b.getvalue()

class Phase150Tests(unittest.TestCase):
    def test_plain_ticker(self): self.assertEqual(classify_symbol("AAPL"), ("SINGLE_TOKEN", "AAPL"))
    def test_dot_class_ticker(self): self.assertEqual(classify_symbol("BRK.B"), ("SINGLE_TOKEN", "BRK.B"))
    def test_exchange_prefix(self): self.assertEqual(classify_symbol("NYSE: SSD"), ("EXCHANGE_PREFIXED_SINGLE", "SSD"))
    def test_placeholder_none(self): self.assertEqual(classify_symbol("NONE"), ("MISSING_OR_PLACEHOLDER", None))
    def test_placeholder_bracketed(self): self.assertEqual(classify_symbol("[NONE]"), ("MISSING_OR_PLACEHOLDER", None))
    def test_blank(self): self.assertEqual(classify_symbol("  "), ("MISSING_OR_PLACEHOLDER", None))
    def test_multiple_comma_not_split(self): self.assertEqual(classify_symbol("CBS, CBS.A"), ("MULTI_OR_FREEFORM", None))
    def test_multiple_slash_not_split(self): self.assertEqual(classify_symbol("JWA/JWB"), ("MULTI_OR_FREEFORM", None))
    def test_other_noncanonical_preserved(self): self.assertEqual(classify_symbol("(NYSE:FBC)"), ("OTHER_NONCANONICAL", None))
    def test_exchange_prefix_returns_candidate_only(self): self.assertEqual(classify_symbol("NASDAQ:RMR"), ("EXCHANGE_PREFIXED_SINGLE", "RMR"))

    def test_metadata_schema_required(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("SUBMISSION.tsv", HEADER)
            z.writestr("metadata.json", json.dumps({"tables": []}))
        with self.assertRaisesRegex(ValueError, "metadata schema missing"):
            parse_period_zip(b.getvalue(), "TEST")

    def test_valid_synthetic_submission(self):
        rows = [["0000000001-26-000001", "4", "0000000001", "NYSE: ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026"]]
        result = parse_period_zip(fixture(rows), "TEST")
        self.assertEqual(result["form4_rows"], 1)
        self.assertEqual(result["canonical_symbol_rows"], 1)
        self.assertEqual(result["unique_issuer_ciks"], 1)
        self.assertEqual(result["symbol_class_counts"]["EXCHANGE_PREFIXED_SINGLE"], 1)
        self.assertFalse(result["aff10b5one_field_present"])

    def test_ticker_reused_across_ciks_flagged(self):
        rows = [
            ["0000000001-26-000001", "4", "0000000001", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026"],
            ["0000000002-26-000001", "4", "0000000002", "ABC", "ISSUER B", "06-NOV-2026", "05-NOV-2026"],
        ]
        result = parse_period_zip(fixture(rows), "TEST")
        self.assertEqual(result["ticker_candidates_reused_across_ciks"], {"ABC": 2})
        self.assertEqual(result["max_ciks_per_ticker_candidate"], 2)

    def test_one_cik_multiple_symbols_not_collapsed(self):
        rows = [
            ["0000000001-26-000001", "4", "0000000001", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026"],
            ["0000000001-26-000002", "4/A", "0000000001", "XYZ", "ISSUER A", "06-NOV-2026", "05-NOV-2026"],
        ]
        result = parse_period_zip(fixture(rows), "TEST")
        self.assertEqual(result["issuer_ciks_with_multiple_canonical_symbol_candidates"], 1)

    def test_invalid_issuer_cik_rejected(self):
        rows = [["0000000001-26-000001", "4", "BAD", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026"]]
        with self.assertRaisesRegex(ValueError, "Invalid issuer CIK"):
            parse_period_zip(fixture(rows), "TEST")

    def test_aff10b5one_true_false_normalized(self):
        meta = json.loads(json.dumps(META))
        meta["tables"][0]["tableSchema"]["columns"].append({"name": "AFF10B5ONE", "dc:description": AFF_DESC})
        rows = [
            ["0000000001-26-000001", "4", "0000000001", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026", "true"],
            ["0000000002-26-000001", "4", "0000000002", "XYZ", "ISSUER B", "06-NOV-2026", "05-NOV-2026", "0"],
            ["0000000003-26-000001", "4/A", "0000000003", "DEF", "ISSUER C", "06-NOV-2026", "05-NOV-2026", "1"],
            ["0000000004-26-000001", "4", "0000000004", "GHI", "ISSUER D", "06-NOV-2026", "05-NOV-2026", "false"],
        ]
        b = io.BytesIO()
        header = HEADER.rstrip("\n") + "\tAFF10B5ONE\n"
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("SUBMISSION.tsv", header + "".join("\t".join(r) + "\n" for r in rows))
            z.writestr("metadata.json", json.dumps(meta))
        result = parse_period_zip(b.getvalue(), "TEST")
        self.assertEqual(result["aff10b5one_value_counts"], {"false": 2, "true": 2})
        self.assertEqual(result["aff10b5one_true_pct_of_form4_rows"], 50.0)

    def test_aff10b5one_unknown_is_not_assumed_false(self):
        meta = json.loads(json.dumps(META))
        meta["tables"][0]["tableSchema"]["columns"].append({"name": "AFF10B5ONE", "dc:description": AFF_DESC})
        rows = [["0000000001-26-000001", "4", "0000000001", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026", "unknown"]]
        b = io.BytesIO()
        header = HEADER.rstrip("\n") + "\tAFF10B5ONE\n"
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("SUBMISSION.tsv", header + "\t".join(rows[0]) + "\n")
            z.writestr("metadata.json", json.dumps(meta))
        result = parse_period_zip(b.getvalue(), "TEST")
        self.assertEqual(result["aff10b5one_value_counts"], {"unknown": 1})

    def test_no_form4_rejected(self):
        rows = [["0000000001-26-000001", "3", "0000000001", "ABC", "ISSUER A", "06-NOV-2026", "05-NOV-2026"]]
        with self.assertRaisesRegex(ValueError, "No Form 4"):
            parse_period_zip(fixture(rows), "TEST")

if __name__ == "__main__": unittest.main()
