import unittest

from research.phase69_form144_incremental_fund_registrant_scan import (
    NEW_FUND_REGISTRANT_CIKS,
    EXPECTED_LEGACY_UNRESOLVED_TICKERS,
    audit_overlap,
    derive_new_ciks,
    merge_events,
    merge_rows,
    validate_base,
    validate_legacy_snapshot,
)


class Phase69IncrementalFundRegistrantTests(unittest.TestCase):
    def test_exact_ten_new_ciks(self):
        old = {f"{i:010d}" for i in range(1, 310)}
        expanded = old | NEW_FUND_REGISTRANT_CIKS
        self.assertEqual(len(NEW_FUND_REGISTRANT_CIKS), 10)
        self.assertEqual(derive_new_ciks(expanded, old), NEW_FUND_REGISTRANT_CIKS)

    def test_rejects_incomplete_expanded_cik_map(self):
        old = {f"{i:010d}" for i in range(1, 310)}
        with self.assertRaises(ValueError):
            derive_new_ciks(old | (NEW_FUND_REGISTRANT_CIKS - {"0001174610"}), old)


    def test_rejects_wrong_legacy_set_even_when_counts_match(self):
        old = {f"{i:010d}" for i in range(1, 310)}
        expanded = old | NEW_FUND_REGISTRANT_CIKS
        wrong_legacy = set(old)
        wrong_legacy.remove("0000000001")
        wrong_legacy.add("0009999999")
        with self.assertRaises(ValueError):
            derive_new_ciks(expanded, wrong_legacy)


    def test_legacy_snapshot_requires_exact_unresolved_names(self):
        legacy_map = {f"{i:010d}": ["T"] for i in range(309)}
        validate_legacy_snapshot(legacy_map, sorted(EXPECTED_LEGACY_UNRESOLVED_TICKERS), [])
        wrong = set(EXPECTED_LEGACY_UNRESOLVED_TICKERS)
        wrong.remove("ARKF")
        wrong.add("OTHER")
        with self.assertRaises(ValueError):
            validate_legacy_snapshot(legacy_map, sorted(wrong), [])

    def test_merge_replaces_overlap_and_adds_new_accession(self):
        base = [
            {"accession":"A","candidate_role_status":"filer_only_false_positive",
             "xml_issuer_cik":"0001","xml_filer_cik":"0002","master_index_ciks":"0001;0002",
             "form":"144","filing_date":"2025-01-01"},
            {"accession":"B","candidate_role_status":"issuer_match","xml_issuer_cik":"0003",
             "xml_filer_cik":"0004","master_index_ciks":"0003;0004","form":"144","filing_date":"2025-01-02"},
        ]
        incremental = [
            {"accession":"A","candidate_role_status":"ambiguous_pair_issuer_match",
             "xml_issuer_cik":"0001","xml_filer_cik":"0002","master_index_ciks":"0001;0002",
             "form":"144","filing_date":"2025-01-01"},
            {"accession":"C","candidate_role_status":"issuer_match","xml_issuer_cik":"0005",
             "xml_filer_cik":"0006","master_index_ciks":"0005;0006","form":"144","filing_date":"2025-01-03"},
        ]
        merged, overlaps = merge_rows(base, incremental)
        self.assertEqual({r["accession"] for r in merged}, {"A","B","C"})
        self.assertEqual(next(r for r in merged if r["accession"]=="A")["candidate_role_status"],
                         "ambiguous_pair_issuer_match")
        self.assertEqual(len(overlaps), 1)
        self.assertTrue(overlaps[0]["identity_consistent"])

    def test_overlap_identity_mismatch_is_detected(self):
        base = {"accession":"A","xml_issuer_cik":"0001","xml_filer_cik":"0002",
                "master_index_ciks":"0001;0002","form":"144","filing_date":"2025-01-01"}
        expanded = {"accession":"A","xml_issuer_cik":"0002","xml_filer_cik":"0001",
                    "master_index_ciks":"0001;0002","form":"144","filing_date":"2025-01-01"}
        self.assertFalse(audit_overlap(base, expanded)["identity_consistent"])

    def test_expanded_event_merge_drops_filer_only_and_adds_new(self):
        base_events = [{"accession":"A","value":1},{"accession":"B","value":2}]
        incremental_rows = [
            {"accession":"A","candidate_role_status":"filer_only_false_positive"},
            {"accession":"C","candidate_role_status":"issuer_match"},
        ]
        incremental_events = [{"accession":"C","value":3}]
        merged = merge_events(base_events, incremental_rows, incremental_events)
        self.assertEqual({e["accession"] for e in merged}, {"B","C"})

    def test_base_artifact_requires_pass_and_exact_counts(self):
        summary = {
            "data_gate":"PASS","current_candidate_cik_count":309,
            "current_tickers_with_cik_mapping":308,"candidate_rows_processed":21648,
            "issuer_event_rows":21634,"filer_only_false_positive_rows":14,
            "unresolved_rows":0,"xml_candidate_fetch_or_processing_errors":0,
            "current_tickers_unresolved":[str(i) for i in range(27)],
        }
        rows = [{"accession":str(i),"candidate_role_status":"issuer_match"} for i in range(21648)]
        events = [{"accession":str(i)} for i in range(21634)]
        validate_base(summary, rows, events)
        summary["data_gate"] = "FAIL"
        with self.assertRaises(ValueError):
            validate_base(summary, rows, events)


if __name__ == "__main__":
    unittest.main()
