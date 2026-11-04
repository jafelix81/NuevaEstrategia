import unittest
from research.phase64_form144_master_pair_cross_quarter_audit import (
    build_pair_rows, classify_xml_identity, parse_master_index, parse_quarter,
    primary_xml_urls, select_pair_sample, wilson_lower_bound,
)

class TestPhase64MasterPairAudit(unittest.TestCase):
    def test_quarter_parser(self):
        self.assertEqual(parse_quarter("2023Q2"), (2023, 2))
        with self.assertRaises(ValueError):
            parse_quarter("2023Q5")

    def test_master_index_groups_two_ciks(self):
        raw = (
            "Description: SEC filing index\n"
            "CIK|Company Name|Form Type|Date Filed|Filename\n"
            "0000000001|ISSUER|144|2025-01-01|edgar/data/1/0000000001-25-000001.txt\n"
            "0000000002|SELLER|144|2025-01-01|edgar/data/2/0000000001-25-000001.txt\n"
        )
        rows = parse_master_index(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["master_index_ciks"], ["0000000001", "0000000002"])
        self.assertEqual(rows[0]["master_index_row_count"], 2)

    def test_pair_classes(self):
        source = [
            {"accession":"a","form":"144","master_index_ciks":["0000000001","0000000002"]},
            {"accession":"b","form":"144/A","master_index_ciks":["0000000001","0000000003"]},
            {"accession":"c","form":"144","master_index_ciks":["0000000004","0000000005"]},
        ]
        rows = build_pair_rows(source, {"0000000001","0000000003"},
                               {"0000000001":["AAA"],"0000000003":["BBB"]}, 2025, 1)
        self.assertEqual([r["pair_class"] for r in rows], ["unique_candidate","ambiguous","control"])

    def test_sample_is_deterministic_and_stratified(self):
        rows=[]
        for form in ("144","144/A"):
            for i in range(8):
                for cls,n in (("unique_candidate",1),("control",0),("ambiguous",2)):
                    rows.append({"accession":f"{form}-{cls}-{i}","form":form,
                                 "year":2025,"quarter":1,"pair_class":cls,
                                 "candidate_count_in_pair":n})
        a=select_pair_sample(rows,2,2,1); b=select_pair_sample(rows,2,2,1)
        self.assertEqual([r["accession"] for r in a],[r["accession"] for r in b])
        self.assertEqual(len(a),10)
        self.assertEqual(sum(r["sample_stratum"]=="unique_candidate" for r in a),4)
        self.assertEqual(sum(r["sample_stratum"]=="control" for r in a),4)
        self.assertEqual(sum(r["sample_stratum"]=="ambiguous" for r in a),2)

    def test_candidate_role_uses_issuer_not_filer(self):
        row={"master_index_ciks":["0000000001","0000000002"],
             "candidate_ciks_in_pair":["0000000001"],"form":"144"}
        issuer=classify_xml_identity(row,{"issuer_cik":"1","filer_cik":"2","submission_type":"144"})
        filer=classify_xml_identity(row,{"issuer_cik":"2","filer_cik":"1","submission_type":"144"})
        self.assertEqual(issuer["unique_candidate_role"],"issuer")
        self.assertEqual(filer["unique_candidate_role"],"filer")
        self.assertTrue(issuer["both_xml_ciks_in_pair"])

    def test_multiple_candidates_stay_ambiguous(self):
        row={"master_index_ciks":["0000000001","0000000002"],
             "candidate_ciks_in_pair":["0000000001","0000000002"],"form":"144/A"}
        got=classify_xml_identity(row,{"issuer_cik":"1","filer_cik":"2","submission_type":"144/A"})
        self.assertEqual(got["unique_candidate_role"],"ambiguous")

    def test_primary_xml_paths_try_both_ciks(self):
        row={"accession":"0001959173-25-004176","master_index_ciks":["0000000001","0000000002"]}
        urls=primary_xml_urls(row)
        self.assertEqual(len(urls),2)
        self.assertTrue(urls[0].endswith("/1/000195917325004176/primary_doc.xml"))
        self.assertTrue(urls[1].endswith("/2/000195917325004176/primary_doc.xml"))

    def test_wilson_lower_bound(self):
        self.assertGreater(wilson_lower_bound(100,100),.95)
        self.assertLess(wilson_lower_bound(9,9),.75)
        self.assertIsNone(wilson_lower_bound(0,0))

if __name__ == "__main__":
    unittest.main()
