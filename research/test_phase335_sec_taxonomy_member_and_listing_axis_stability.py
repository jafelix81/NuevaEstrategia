import unittest

from research.phase335_sec_taxonomy_member_and_listing_axis_stability import (
    build_profiles,
    classify_symbol_profile,
)


class Phase335Tests(unittest.TestCase):
    def test_one_class_qname_is_not_promoted_to_permanent_stability(self):
        got = classify_symbol_profile(
            ["axis=MemberA"],
            {"axis=MemberA": ["Common stock, class A"]},
        )
        self.assertEqual(got, "SINGLE_QNAME_IN_SAMPLE_NOT_LONGITUDINAL_PROOF")

    def test_multiple_qnames_with_same_context_title_are_candidate_alias_only(self):
        got = classify_symbol_profile(
            ["axis=MemberA", "axis=MemberA_v2"],
            {
                "axis=MemberA": ["5.50% preferred stock"],
                "axis=MemberA_v2": ["5.50% preferred stock"],
            },
        )
        self.assertEqual(got, "CANDIDATE_TAXONOMY_ALIAS_SAME_TITLE_NOT_MERGED")

    def test_multiple_qnames_with_different_titles_remain_ambiguous(self):
        got = classify_symbol_profile(
            ["axis=MemberA", "axis=MemberB"],
            {
                "axis=MemberA": ["Common stock"],
                "axis=MemberB": ["Preferred stock"],
            },
        )
        self.assertEqual(got, "MULTIPLE_QNAME_VARIANTS_AMBIGUOUS")

    def test_missing_title_evidence_does_not_create_alias(self):
        got = classify_symbol_profile(
            ["axis=MemberA", "axis=MemberB"],
            {"axis=MemberA": ["Common stock"], "axis=MemberB": []},
        )
        self.assertEqual(got, "MULTIPLE_QNAME_VARIANTS_AMBIGUOUS")

    def test_no_class_axis_stays_unmapped_even_if_listing_axis_exists(self):
        source = {
            "documents": [{
                "accession": "a1", "filing_date": "2022-01-01",
                "hash_match": True, "symbol_set_status": "MATCH_PHASE332_SYMBOL_SET",
                "source_pair_ids": ["P1"], "candidate_tickers": ["ABC"],
                "context_associations": [{
                    "symbol": "ABC", "context_ref": "c1",
                    "class_axis_members": [],
                    "listing_axis_members": ["dei:EntityListingsExchangeAxis=ex:NYSEMember"],
                    "same_context_security_titles": ["Common stock"],
                    "direct_class_binding": False,
                }],
            }],
        }
        got = build_profiles(source)
        self.assertEqual(got["symbol_profiles"][0]["classification"], "NO_DIRECT_CLASS_AXIS")
        self.assertEqual(got["summary"]["symbols_with_listing_axis"], 1)
        self.assertEqual(got["summary"]["class_axis_fact_rows"], 0)
        self.assertEqual(got["summary"]["listing_axis_fact_rows"], 1)

    def test_bad_hash_document_is_excluded_from_symbol_profiles(self):
        source = {
            "documents": [{
                "accession": "a1", "filing_date": "2022-01-01",
                "hash_match": False, "symbol_set_status": "NOT_ADMITTED_HASH_MISMATCH",
                "source_pair_ids": ["P1"], "candidate_tickers": ["ABC"],
                "context_associations": [{
                    "symbol": "ABC", "context_ref": "c1",
                    "class_axis_members": ["axis=MemberA"],
                    "listing_axis_members": [],
                    "same_context_security_titles": ["Common stock"],
                    "direct_class_binding": True,
                }],
            }],
        }
        got = build_profiles(source)
        self.assertEqual(got["summary"]["excluded_source_documents"], 1)
        self.assertEqual(got["symbol_profiles"], [])
        self.assertEqual(got["excluded_documents"][0]["reason"], "SOURCE_HASH_OR_SYMBOL_SET_NOT_ADMITTED")

    def test_same_symbol_member_aliases_are_not_merged_in_output(self):
        source = {
            "documents": [{
                "accession": "a1", "filing_date": "2022-01-01",
                "hash_match": True, "symbol_set_status": "MATCH_PHASE332_SYMBOL_SET",
                "source_pair_ids": ["P1"], "candidate_tickers": ["ABC"],
                "context_associations": [{
                    "symbol": "ABC", "context_ref": "c1",
                    "class_axis_members": ["axis=MemberA"],
                    "listing_axis_members": [],
                    "same_context_security_titles": ["5.50% preferred stock"],
                    "direct_class_binding": True,
                }],
            }, {
                "accession": "a2", "filing_date": "2022-02-01",
                "hash_match": True, "symbol_set_status": "MATCH_PHASE332_SYMBOL_SET",
                "source_pair_ids": ["P1"], "candidate_tickers": ["ABC"],
                "context_associations": [{
                    "symbol": "ABC", "context_ref": "c2",
                    "class_axis_members": ["axis=MemberA_v2"],
                    "listing_axis_members": [],
                    "same_context_security_titles": ["5.50% preferred stock"],
                    "direct_class_binding": True,
                }],
            }],
        }
        got = build_profiles(source)
        profile = got["symbol_profiles"][0]
        self.assertEqual(profile["classification"], "CANDIDATE_TAXONOMY_ALIAS_SAME_TITLE_NOT_MERGED")
        self.assertEqual(profile["class_member_count"], 2)
        self.assertEqual(got["summary"]["qname_aliases_merged"], 0)

    def test_listing_profiles_keep_exchange_members_distinct(self):
        source = {
            "documents": [{
                "accession": "a1", "filing_date": "2022-01-01",
                "hash_match": True, "symbol_set_status": "MATCH_PHASE332_SYMBOL_SET",
                "source_pair_ids": ["P1"], "candidate_tickers": ["ABC"],
                "context_associations": [
                    {"symbol": "ABC", "context_ref": "c1", "class_axis_members": ["axis=Common"],
                     "listing_axis_members": ["dei:ExchangeAxis=ex:NYSEMember"],
                     "same_context_security_titles": ["Common stock"], "direct_class_binding": True},
                    {"symbol": "ABCPRA", "context_ref": "c2", "class_axis_members": ["axis=Preferred"],
                     "listing_axis_members": ["dei:ExchangeAxis=ex:NYSEAmericanMember"],
                     "same_context_security_titles": ["Preferred stock"], "direct_class_binding": True},
                ],
            }],
        }
        got = build_profiles(source)
        self.assertEqual(got["summary"]["unique_listing_axis_members"], 2)
        self.assertEqual(got["summary"]["symbols_with_listing_axis"], 2)
        self.assertEqual(got["summary"]["listing_and_class_axis_fact_rows"], 2)


if __name__ == "__main__":
    unittest.main()
