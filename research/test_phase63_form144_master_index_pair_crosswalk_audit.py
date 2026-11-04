import unittest

from phase63_form144_master_index_pair_crosswalk_audit import (
    audit_rows,
    norm_cik,
    parse_cik_list,
)


class TestForm144MasterPairAudit(unittest.TestCase):
    def test_cik_normalization(self):
        self.assertEqual(norm_cik("19617"), "0000019617")
        self.assertEqual(norm_cik("0000019617"), "0000019617")

    def test_pair_exactly_matches_xml_roles(self):
        census = [{"accession": "a", "master_index_ciks": "0000019617;0001726825"}]
        xml = [{
            "accession": "a", "form": "144",
            "xml_issuer_cik": "0000019617", "xml_filer_cik": "0001726825",
        }]
        summary, detail = audit_rows(census, xml, {"0000019617"})
        self.assertEqual(summary["both_xml_ciks_in_master_pair"], 1)
        self.assertEqual(summary["unique_candidate_is_issuer"], 1)
        self.assertEqual(detail[0]["unique_candidate_role"], "issuer")

    def test_filer_only_candidate_is_not_subject(self):
        census = [{"accession": "a", "master_index_ciks": "0000019617;0001726825"}]
        xml = [{
            "accession": "a", "form": "144",
            "xml_issuer_cik": "0000019617", "xml_filer_cik": "0001726825",
        }]
        summary, detail = audit_rows(census, xml, {"0001726825"})
        self.assertEqual(summary["unique_candidate_is_filer"], 1)
        self.assertEqual(detail[0]["unique_candidate_role"], "filer")

    def test_two_candidates_are_ambiguous(self):
        census = [{"accession": "a", "master_index_ciks": "0000019617;0001726825"}]
        xml = [{
            "accession": "a", "form": "144/A",
            "xml_issuer_cik": "0000019617", "xml_filer_cik": "0001726825",
        }]
        summary, detail = audit_rows(
            census, xml, {"0000019617", "0001726825"}
        )
        self.assertEqual(summary["ambiguous_candidate_pairs"], 1)
        self.assertEqual(detail[0]["unique_candidate_role"], "ambiguous")

    def test_missing_census_does_not_infer(self):
        xml = [{
            "accession": "a", "form": "144",
            "xml_issuer_cik": "1", "xml_filer_cik": "2",
        }]
        summary, detail = audit_rows([], xml, {"0000000001"})
        self.assertEqual(summary["missing_census_rows"], 1)
        self.assertEqual(detail, [])

    def test_cik_list_deduplicates(self):
        self.assertEqual(
            parse_cik_list("19617;0000019617;1726825"),
            ["0000019617", "0001726825"],
        )


if __name__ == "__main__":
    unittest.main()
