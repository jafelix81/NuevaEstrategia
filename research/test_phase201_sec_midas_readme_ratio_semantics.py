import io
import unittest
import zipfile

from research.phase201_sec_midas_readme_ratio_semantics import (
    QUARTERS,
    audit_derived_ratios,
    build_result,
    collect_readmes,
)
from research.phase199_sec_midas_disputed_quarter_content_audit import REQUIRED

HEADER = sorted(REQUIRED)

def make_csv(values):
    out = io.StringIO()
    out.write(",".join(HEADER) + "\n")
    for row in values:
        out.write(",".join(row[name] for name in HEADER) + "\n")
    return out.getvalue().encode()

def row(**changes):
    values = {name: "1" for name in HEADER}
    values.update({"ticker":"ABC","date":"2016-04-01","security":"Stock",
                   "hidden":"2","tradesforhidden":"10",
                   "hiddenvol('000)":"25","tradevolforhidden('000)":"100"})
    values.update(changes)
    return values

def make_zip(members):
    out = io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name,data)
    return out.getvalue()


class Phase201Tests(unittest.TestCase):
    def test_hidden_rate_and_volume_share(self):
        result=audit_derived_ratios(make_csv([row()]),"2016 Q2")
        self.assertAlmostEqual(result["ratios"]["hidden_rate"]["min"],0.2)
        self.assertAlmostEqual(result["ratios"]["hidden_volume_share"]["min"],0.25)

    def test_negative_numerators_are_not_treated_as_sentinels(self):
        result=audit_derived_ratios(make_csv([row(hidden="-7",**{"hiddenvol('000)":"-3"})]),"2016 Q2")
        self.assertEqual(result["ratios"]["hidden_rate"]["negative_numerator_count"],1)
        self.assertEqual(result["ratios"]["hidden_volume_share"]["negative_numerator_count"],1)
        self.assertEqual(result["ratios"]["hidden_rate"]["denominator_zero_count"],0)

    def test_ratio_above_one_is_visible(self):
        result=audit_derived_ratios(make_csv([row(hidden="11")]),"2016 Q2")
        self.assertEqual(result["ratios"]["hidden_rate"]["greater_than_one_count"],1)

    def test_zero_denominator_is_excluded(self):
        result=audit_derived_ratios(make_csv([row(tradesforhidden="0",**{"tradevolforhidden('000)":"0"})]),"2016 Q2")
        self.assertEqual(result["ratios"]["hidden_rate"]["denominator_zero_count"],1)
        self.assertEqual(result["ratios"]["hidden_volume_share"]["denominator_zero_count"],1)
        self.assertEqual(result["ratios"]["hidden_rate"]["valid_count"],0)

    def test_readme_extracted_from_direct_zip(self):
        archive=make_zip({"README.txt":b"Hidden is a numerator.\n","data.csv":make_csv([row()])})
        docs,layers=collect_readmes(archive)
        self.assertEqual(len(docs),1)
        self.assertIn("Hidden is a numerator",docs[0]["text"])
        self.assertEqual(len(docs[0]["sha256"]),64)

    def test_readme_extracted_from_nested_zip(self):
        inner=make_zip({"README2_q.txt":b"HiddenVol is volume.\n","data.csv":make_csv([row()])})
        outer=make_zip({"nested.zip":inner})
        docs,layers=collect_readmes(outer)
        self.assertEqual(len(docs),1)
        self.assertEqual(docs[0]["member"],"README2_q.txt")
        self.assertEqual(len(layers),2)

    def test_build_result_never_promotes_pit_or_alpha(self):
        results=[{"quarter":q,"readmes":[]} for q in QUARTERS]
        built=build_result(results)
        self.assertEqual(built["status"],"SIX_QUARTER_README_AND_DERIVED_RATIO_AUDIT_COMPLETED")
        self.assertFalse(built["interpretation"]["strict_pit_admitted"])
        self.assertFalse(built["interpretation"]["alpha_test_authorized"])
        self.assertTrue(built["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
