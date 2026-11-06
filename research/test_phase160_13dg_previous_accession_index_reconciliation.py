import unittest
from phase160_13dg_previous_accession_index_reconciliation import audit, norm_accession, accession_year, family

def ix(form="SC 13D", filing="2020-01-02", candidates='["0000000001","0000000002"]'):
    return {"accession":"0000000001-20-000001","quarter":"2020Q1","form":form,"filing_date":filing,
      "candidate_identity_ciks":candidates,"metadata_conflict":"False","is_amendment":"False"}

def sm(previous="0000000001-20-000001", filing="2020-02-01", subject="0000000001", filer="0000000002",
       form="SC 13D/A", family_value="13D", xml="true", alias="false"):
    return {"accession":"0000000002-20-000001","form":form,"family":family_value,"previous_accession":previous,
      "filing_date_index":filing,"subject_cik":subject,"filer_cik":filer,"xml_present":xml,"is_index_alias":alias}

class Phase160Tests(unittest.TestCase):
    def test_exact_accession(self): self.assertEqual(norm_accession("0000000001-20-000001"),"0000000001-20-000001")
    def test_pad_cik(self): self.assertEqual(norm_accession("1-20-000001"),"0000000001-20-000001")
    def test_pad_sequence(self): self.assertEqual(norm_accession("1-20-1"),"0000000001-20-000001")
    def test_bad_accession(self): self.assertIsNone(norm_accession("bad"))
    def test_year_mapping(self): self.assertEqual(accession_year("12"),2012); self.assertEqual(accession_year("99"),1999)
    def test_form_families(self): self.assertEqual(family("SC 13G/A"),"13G"); self.assertIsNone(family("SC TO-T/A"))
    def test_exact_parent_found(self):
        rows,s=audit([ix()],[sm()]); self.assertEqual(rows[0]["lineage_status"],"PARENT_FOUND_FORM_DATE_AND_CIK_CANDIDATES_MATCH"); self.assertEqual(s["parents_found_in_index"],1)
    def test_padding_recovers_parent(self):
        rows,s=audit([ix()],[sm(previous="1-20-1")]); self.assertTrue(rows[0]["parent_found_in_global_index"]); self.assertEqual(s["parents_recovered_by_canonicalization"],1)
    def test_pre_window_parent(self):
        rows,s=audit([ix()],[sm(previous="1-12-1")]); self.assertEqual(rows[0]["lineage_status"],"OUTSIDE_INDEX_HISTORY"); self.assertEqual(s["parents_outside_index_history"],1)
    def test_missing_inside_window(self):
        rows,_=audit([ix()],[sm(previous="3-20-1")]); self.assertEqual(rows[0]["lineage_status"],"PARENT_NOT_FOUND_WITHIN_INDEX_WINDOW")
    def test_form_mismatch(self):
        rows,_=audit([ix(form="SC 13G")],[sm()]); self.assertEqual(rows[0]["lineage_status"],"PARENT_FORM_FAMILY_MISMATCH")
    def test_parent_date_must_precede_child(self):
        rows,_=audit([ix(filing="2020-03-01")],[sm(filing="2020-02-01")]); self.assertEqual(rows[0]["lineage_status"],"PARENT_DATE_NOT_BEFORE_CURRENT")
    def test_subject_candidate_mismatch_is_quarantined(self):
        rows,s=audit([ix()],[sm(subject="0000000009")]); self.assertTrue(rows[0]["parent_found_in_global_index"]); self.assertEqual(rows[0]["lineage_status"],"PARENT_FOUND_SUBJECT_CIK_CANDIDATE_MISMATCH"); self.assertEqual(s["parents_found_in_index"],1)
    def test_filer_candidate_mismatch(self):
        rows,_=audit([ix()],[sm(filer="0000000009")]); self.assertEqual(rows[0]["lineage_status"],"PARENT_INDEX_CIKS_DO_NOT_INCLUDE_CURRENT_FILER_CANDIDATE")
    def test_non_xml_and_alias_excluded(self):
        rows,s=audit([ix()],[sm(xml="false"),sm(alias="true")]); self.assertEqual(rows,[]); self.assertEqual(s["direct_previous_accession_links"],0)
    def test_duplicate_index_accession_flagged(self):
        _,s=audit([ix(),ix()],[sm()]); self.assertEqual(s["index_integrity"]["duplicate_accession_count"],1); self.assertEqual(s["status"],"INDEX_INTEGRITY_REVIEW_REQUIRED")
    def test_reused_parent_counted(self):
        second=sm(); second["accession"]="0000000003-20-000001"
        _,s=audit([ix()],[sm(),second]); self.assertEqual(s["reused_parent_accessions"],1)
    def test_no_economic_or_holdout_claim(self):
        _,s=audit([ix()],[sm()]); self.assertFalse(s["economic_test_authorized"]); self.assertFalse(s["forward_returns_used"]); self.assertFalse(s["final_holdout_used"]); self.assertFalse(s["production_changed"])

if __name__=="__main__": unittest.main()
