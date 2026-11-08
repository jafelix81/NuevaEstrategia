import io
import unittest
import zipfile

from research.phase202_sec_midas_per_exchange_archive_structure import (
    EXCHANGE_REQUIRED,
    SAMPLE_QUARTERS,
    QuarterAnchorParser,
    build_result,
    inspect_zip_bytes,
)

HEADER = sorted(EXCHANGE_REQUIRED)

def make_csv():
    out = io.StringIO()
    out.write(",".join(HEADER) + "\n")
    values = {name: "1" for name in HEADER}
    values.update({"ticker":"ABC","date":"2016-04-01","security":"Stock"})
    out.write(",".join(values[name] for name in HEADER) + "\n")
    return out.getvalue().encode()

def make_zip(members):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as zf:
        for name,data in members.items():
            zf.writestr(name,data)
    return out.getvalue()


class Phase202Tests(unittest.TestCase):
    def test_inventory_parser_extracts_quarter_links(self):
        parser=QuarterAnchorParser()
        parser.feed('<a href="/files/a_2016_q2.zip">2016 Q2</a><a href="/files/a_2017_q2.zip">2017 Q2</a>')
        self.assertEqual(parser.links["2016 Q2"],"https://www.sec.gov/files/a_2016_q2.zip")
        self.assertEqual(len(parser.links),2)

    def test_single_csv_member_detected(self):
        result=inspect_zip_bytes(make_zip({"data.csv":make_csv()}))
        self.assertEqual(result["data_member_count"],1)
        self.assertFalse(result["data_members"][0]["exchange_column_present"])
        self.assertEqual(result["data_members"][0]["member"],"data.csv")

    def test_multiple_members_may_encode_exchange_by_filename(self):
        result=inspect_zip_bytes(make_zip({"NYSE.csv":make_csv(),"NASDAQ.csv":make_csv()}))
        self.assertEqual(result["data_member_count"],2)
        self.assertEqual(result["data_members"][0]["filename_exchange_hints"],["nyse"])
        self.assertEqual(result["data_members"][1]["filename_exchange_hints"],["nasdaq"])

    def test_nested_archive_is_recursively_inspected(self):
        inner=make_zip({"README.txt":b"sample readme","NYSE.csv":make_csv()})
        outer=make_zip({"nested.zip":inner})
        result=inspect_zip_bytes(outer)
        self.assertEqual(result["nested_zip_count"],1)
        self.assertEqual(result["nested_archives"][0]["inspection"]["data_member_count"],1)
        self.assertEqual(result["nested_archives"][0]["inspection"]["readme_count"],1)
        self.assertTrue(result["has_data_member_recursive"])

    def test_readme_and_crc_metadata_are_not_overstated(self):
        result=inspect_zip_bytes(make_zip({"README.txt":b"sample readme","data.csv":make_csv()}))
        self.assertEqual(result["readme_count"],1)
        self.assertFalse(result["full_crc_validation_performed"])

    def test_result_never_promotes_pit_or_alpha(self):
        inventory={"quarter_urls":{q:"https://example.invalid/"+q for q in SAMPLE_QUARTERS},"quarter_count":58}
        results=[{"quarter":q,"archive_inspection":{"data_member_count":1,"nested_archives":[]}} for q in SAMPLE_QUARTERS]
        built=build_result(inventory,results)
        self.assertEqual(built["status"],"THREE_QUARTER_PER_EXCHANGE_ARCHIVE_STRUCTURE_AUDITED")
        self.assertFalse(built["interpretation"]["strict_pit_admitted"])
        self.assertFalse(built["interpretation"]["alpha_test_authorized"])
        self.assertTrue(built["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
