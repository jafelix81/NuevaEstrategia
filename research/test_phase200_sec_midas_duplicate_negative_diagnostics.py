import io
import unittest
import zipfile

from research.phase200_sec_midas_duplicate_negative_diagnostics import (
    QUARTERS,
    audit_csv_bytes,
    build_result,
    find_midas_member,
)
from research.phase199_sec_midas_disputed_quarter_content_audit import REQUIRED

HEADER = sorted(REQUIRED)

def make_row(ticker="ABC", day="2016-04-01", security="Stock", **changes):
    values = {name: "1" for name in HEADER}
    values.update({"ticker": ticker, "date": day, "security": security})
    values.update(changes)
    return [values[name] for name in HEADER]

def make_csv(rows):
    out = io.StringIO()
    out.write(",".join(HEADER) + "\n")
    for row in rows:
        out.write(",".join(row) + "\n")
    return out.getvalue().encode()

def make_zip(payload, member="data.csv"):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, payload)
    return out.getvalue()


class Phase200Tests(unittest.TestCase):
    def test_rank_only_duplicate_is_classified(self):
        first = make_row(mcaprank="1")
        second = make_row(mcaprank="2")
        result = audit_csv_bytes(make_csv([first, second]), "2016 Q2")
        self.assertEqual(result["rank_only_conflicting_groups"], 1)
        self.assertEqual(result["activity_conflicting_groups"], 0)
        self.assertEqual(result["field_difference_group_counts"], {"mcaprank": 1})

    def test_activity_duplicate_is_classified(self):
        first = make_row(cancels="1")
        second = make_row(cancels="2")
        result = audit_csv_bytes(make_csv([first, second]), "2016 Q2")
        self.assertEqual(result["activity_conflicting_groups"], 1)
        self.assertEqual(result["rank_only_conflicting_groups"], 0)
        self.assertEqual(result["field_difference_group_counts"], {"cancels": 1})

    def test_exact_duplicate_is_classified(self):
        row = make_row()
        result = audit_csv_bytes(make_csv([row, row]), "2016 Q2")
        self.assertEqual(result["exact_duplicate_key_groups"], 1)
        self.assertEqual(result["duplicate_rows_beyond_first"], 1)

    def test_negative_hidden_and_hiddenvol_histograms(self):
        row = make_row(hidden="-1", hiddenvol_000="-1", tradesforhidden="0", tradevolforhidden_000="0")
        # Use exact normalized field names in the header mapping.
        values = {name: "1" for name in HEADER}
        values.update({"ticker":"ABC","date":"2016-04-01","security":"Stock",
                       "hidden":"-1","hiddenvol('000)":"-1",
                       "tradesforhidden":"0","tradevolforhidden('000)":"0"})
        csv_bytes = (",".join(HEADER)+"\n"+",".join(values[name] for name in HEADER)+"\n").encode()
        result = audit_csv_bytes(csv_bytes, "2016 Q2")
        self.assertEqual(result["negative_fields"]["hidden"]["count"], 1)
        self.assertEqual(result["negative_fields"]["hidden"]["histogram"], {"-1": 1})
        self.assertEqual(result["negative_fields"]["hiddenvol('000)"]["denominator_zero_count"], 1)

    def test_positive_hidden_volume_share_is_derived(self):
        values = {name: "1" for name in HEADER}
        values.update({"ticker":"ABC","date":"2016-04-01","security":"Stock",
                       "hidden":"0.25","hiddenvol('000)":"25","tradevolforhidden('000)":"100"})
        csv_bytes = (",".join(HEADER)+"\n"+",".join(values[name] for name in HEADER)+"\n").encode()
        result = audit_csv_bytes(csv_bytes, "2016 Q2")
        self.assertEqual(result["derived_hidden_volume_share"]["count"], 1)
        self.assertAlmostEqual(result["derived_hidden_volume_share"]["min"], 0.25)

    def test_invalid_and_out_of_quarter_rows_are_visible(self):
        values = {name: "1" for name in HEADER}
        values.update({"ticker":"ABC","date":"2016-07-01","security":"Stock"})
        csv_bytes = (",".join(HEADER)+"\n"+",".join(values[name] for name in HEADER)+"\n").encode()
        result = audit_csv_bytes(csv_bytes, "2016 Q2")
        self.assertEqual(result["out_of_quarter_rows"], 1)

    def test_nested_zip_member_is_found(self):
        inner = make_zip(make_csv([make_row()]), "extensionless_data")
        outer = make_zip(inner, "nested_archive.zip")
        data, meta = find_midas_member(outer)
        self.assertEqual(len(data), len(make_csv([make_row()])))
        self.assertEqual(meta["container_depth"], 1)
        self.assertEqual(len(meta["archive_layers"]), 2)

    def test_all_six_quarters_declared(self):
        self.assertEqual(len(QUARTERS), 6)
        self.assertIn("2016 Q1", QUARTERS)
        self.assertIn("2019 Q4", QUARTERS)

    def test_result_never_promotes_pit_or_alpha(self):
        result = build_result([{"quarter":q} for q in QUARTERS])
        self.assertEqual(result["status"], "SIX_QUARTER_DUPLICATE_AND_NEGATIVE_VALUE_DIAGNOSTICS_COMPLETED")
        self.assertFalse(result["interpretation"]["strict_pit_admitted"])
        self.assertFalse(result["interpretation"]["alpha_test_authorized"])
        self.assertFalse(result["interpretation"]["duplicate_rows_deduplicated"])
        self.assertTrue(result["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
