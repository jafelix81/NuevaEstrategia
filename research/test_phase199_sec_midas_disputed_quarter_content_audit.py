import io
import unittest
import zipfile
from datetime import date

from research.phase199_sec_midas_disputed_quarter_content_audit import (
    QUARTERS,
    REQUIRED,
    audit_csv_member,
    audit_zip_bytes,
    build_result,
    parse_date,
    quarter_bounds,
)

HEADER = sorted(REQUIRED)

def make_row(ticker="ABC", day="2016-04-01", security="Stock", cancels="1"):
    values = {name: "1" for name in HEADER}
    values.update({"ticker": ticker, "date": day, "security": security, "cancels": cancels})
    return [values[name] for name in HEADER]

def make_csv(rows, header=HEADER):
    lines = [",".join(header)]
    lines.extend(",".join(row) for row in rows)
    return ("\n".join(lines) + "\n").encode()

def make_zip(csv_bytes, member="sample.csv"):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, csv_bytes)
    return out.getvalue()


class Phase199Tests(unittest.TestCase):
    def test_quarter_bounds(self):
        self.assertEqual(quarter_bounds("2016 Q2"), (date(2016,4,1), date(2016,6,30)))
        self.assertEqual(quarter_bounds("2014 Q2"), (date(2014,4,1), date(2014,6,30)))

    def test_invalid_quarter_rejected(self):
        with self.assertRaises(ValueError):
            quarter_bounds("2016 Q5")

    def test_date_parser_formats(self):
        self.assertEqual(parse_date("20160401").isoformat(), "2016-04-01")
        self.assertEqual(parse_date("04/01/2016").isoformat(), "2016-04-01")
        self.assertIsNone(parse_date("not-a-date"))

    def test_valid_csv_schema_and_rows(self):
        result = audit_csv_member(io.BytesIO(make_csv([make_row(), make_row("XYZ","2016-06-30")])), "sample.csv", "2016 Q2")
        self.assertTrue(result["schema_passed"])
        self.assertEqual(result["rows_with_valid_ticker_and_date"], 2)
        self.assertEqual(result["unique_dates"], 2)
        self.assertEqual(result["unique_tickers"], 2)
        self.assertEqual(result["out_of_quarter_rows"], 0)

    def test_missing_required_column_fails_schema(self):
        header = [x for x in HEADER if x != "hidden"]
        row = make_row()[:-1]
        result = audit_csv_member(io.BytesIO(make_csv([row], header)), "bad.csv", "2016 Q2")
        self.assertFalse(result["schema_passed"])
        self.assertIn("hidden", result["missing_required_columns"])

    def test_out_of_quarter_rows_are_counted(self):
        result = audit_csv_member(io.BytesIO(make_csv([make_row(day="2016-07-01")])), "sample.csv", "2016 Q2")
        self.assertEqual(result["out_of_quarter_rows"], 1)

    def test_malformed_and_blank_rows_are_counted(self):
        raw = make_csv([make_row()]) + b"short,row\n\n"
        result = audit_csv_member(io.BytesIO(raw), "sample.csv", "2016 Q2")
        self.assertEqual(result["malformed_rows"], 1)
        self.assertEqual(result["blank_rows"], 1)

    def test_zip_crc_and_hash_are_recorded(self):
        result = audit_zip_bytes(make_zip(make_csv([make_row()])), "2016 Q2")
        self.assertTrue(result["zip_crc_passed"])
        self.assertEqual(len(result["archive_sha256"]), 64)
        self.assertEqual(result["csv"]["rows_with_valid_ticker_and_date"], 1)

    def test_zip_accepts_txt_data_member(self):
        result = audit_zip_bytes(make_zip(make_csv([make_row()]), "sample.txt"), "2016 Q2")
        self.assertTrue(result["zip_crc_passed"])
        self.assertEqual(result["csv"]["rows_with_valid_ticker_and_date"], 1)

    def test_zip_rejects_non_data_member(self):
        with self.assertRaises(ValueError):
            audit_zip_bytes(make_zip(make_csv([make_row()]), "sample.bin"), "2016 Q2")

    def test_conflicting_duplicate_key_is_visible(self):
        row1 = make_row()
        row2 = make_row(cancels="2")
        result = audit_csv_member(io.BytesIO(make_csv([row1,row2])), "sample.csv", "2016 Q2")
        self.assertEqual(result["conflicting_duplicate_key_groups"], 1)
        self.assertEqual(result["duplicate_rows_beyond_first"], 1)

    def test_exact_duplicate_key_is_visible(self):
        row = make_row()
        result = audit_csv_member(io.BytesIO(make_csv([row,row])), "sample.csv", "2016 Q2")
        self.assertEqual(result["exact_duplicate_key_groups"], 1)
        self.assertEqual(result["duplicate_rows_beyond_first"], 1)

    def test_build_result_never_promotes_pit_or_alpha(self):
        audits = []
        for q in QUARTERS:
            audits.append({
                "quarter": q, "archive_bytes": 100, "zip_crc_passed": True,
                "csv": {"schema_passed": True, "rows_with_valid_ticker_and_date": 1,
                        "invalid_date_rows": 0, "blank_ticker_rows": 0,
                        "malformed_rows": 0, "out_of_quarter_rows": 0},
            })
        result = build_result(audits)
        self.assertEqual(result["status"], "ALL_FOUR_DISPUTED_QUARTERS_FULL_CONTENT_VALIDATED")
        self.assertTrue(result["interpretation"]["all_six_third_party_disputed_assets_content_validated_across_phases_103_199"])
        self.assertFalse(result["interpretation"]["strict_pit_admitted"])
        self.assertFalse(result["interpretation"]["alpha_test_authorized"])
        self.assertTrue(result["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
