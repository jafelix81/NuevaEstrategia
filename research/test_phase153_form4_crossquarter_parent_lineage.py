import unittest
from phase153_form4_crossquarter_parent_lineage import (
    candidates, candidate_index, diff_rows, date_norm, cik_norm, ND_EXACT, ND_COARSE
)

def filing(a,p,d,issuer="0000000001",fd="2026-06-30",od="",owners=None,nd=None,dv=None):
    return {"accession":a,"period":p,"doc":d,"issuer":issuer,"filing_date":fd,"orig_date":od,
            "owners":set(owners or []),"nd":list(nd or []),"dv":list(dv or [])}

class Phase153Tests(unittest.TestCase):
    def test_date_normalization(self): self.assertEqual(date_norm("31-JUL-2026"),"2026-07-31")
    def test_cik_padding(self): self.assertEqual(cik_norm("123"),"0000000123")
    def test_cross_quarter_unique(self):
        p=filing("0000000001-26-000001","2026Q2","4",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",fd="2026-07-02",od="2026-06-30",owners={"0000000002"})
        self.assertEqual(candidates(c,candidate_index({"q2":{"filings":{p["accession"]:p}}}))[0]["filing"]["period"],"2026Q2")
    def test_same_quarter_parent(self):
        p=filing("0000000001-26-000001","2026Q3","4",fd="2026-07-01",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",fd="2026-07-02",od="2026-07-01",owners={"0000000002"})
        self.assertEqual(candidates(c,candidate_index({"q3":{"filings":{p["accession"]:p}}}))[0]["filing"]["period"],"2026Q3")
    def test_no_owner_overlap(self):
        p=filing("0000000001-26-000001","2026Q2","4",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",od="2026-06-30",owners={"0000000003"})
        self.assertEqual(candidates(c,candidate_index({"q2":{"filings":{p["accession"]:p}}})),[])
    def test_ambiguous_preserved(self):
        p1=filing("0000000001-26-000001","2026Q2","4",owners={"0000000002"})
        p2=filing("0000000001-26-000003","2026Q2","4",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",od="2026-06-30",owners={"0000000002"})
        self.assertEqual(len(candidates(c,candidate_index({"q2":{"filings":{p1["accession"]:p1,p2["accession"]:p2}}})),2)
    def test_form4a_cannot_be_parent(self):
        p=filing("0000000001-26-000001","2026Q2","4/A",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",od="2026-06-30",owners={"0000000002"})
        self.assertEqual(candidates(c,candidate_index({"q2":{"filings":{p["accession"]:p}}})),[])
    def test_future_parent_rejected(self):
        p=filing("0000000001-26-000001","2026Q3","4",fd="2026-07-03",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",fd="2026-07-02",od="2026-07-03",owners={"0000000002"})
        self.assertEqual(candidates(c,candidate_index({"q3":{"filings":{p["accession"]:p}}})),[])
    def test_missing_date_or_owner_fails_closed(self):
        p=filing("0000000001-26-000001","2026Q2","4",owners={"0000000002"})
        c=filing("0000000001-26-000002","2026Q3","4/A",owners={"0000000002"})
        idx=candidate_index({"q2":{"filings":{p["accession"]:p}}})
        self.assertEqual(candidates(c,idx),[])
        c["orig_date"]="2026-06-30"; c["owners"]=set()
        self.assertEqual(candidates(c,idx),[])
    def test_exact_repeat_multiset(self):
        r={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100.0","TRANS_PRICEPERSHARE":"10.00","TRANS_ACQUIRED_DISP_CD":"D","DIRECT_INDIRECT_OWNERSHIP":"D"}
        d=diff_rows([r,r],[r,r,r],ND_EXACT,ND_COARSE)
        self.assertEqual(d["exact_repeated_candidate_rows"],2); self.assertEqual(d["added_candidate_rows"],1)
    def test_changed_line_is_possible_modified(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100","TRANS_PRICEPERSHARE":"10"}
        b=dict(a,TRANS_SHARES="90")
        d=diff_rows([a],[b],ND_EXACT,ND_COARSE)
        self.assertEqual(d["possible_modified_candidate_rows"],1); self.assertEqual(d["added_candidate_rows"],0)
    def test_new_coarse_key_is_added_candidate(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100"}
        b=dict(a,TRANS_CODE="P")
        self.assertEqual(diff_rows([a],[b],ND_EXACT,ND_COARSE)["added_candidate_rows"],1)
    def test_footnote_refs_do_not_change_transaction_signature(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100","TRANS_SHARES_FN":"F1"}
        b=dict(a,TRANS_SHARES_FN="F9")
        self.assertEqual(diff_rows([a],[b],ND_EXACT,ND_COARSE)["exact_repeated_candidate_rows"],1)
    def test_numeric_normalization(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100.000"}
        b=dict(a,TRANS_SHARES="100")
        self.assertEqual(diff_rows([a],[b],ND_EXACT,ND_COARSE)["exact_repeated_candidate_rows"],1)
    def test_omitted_parent_rows_not_called_deleted(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100"}
        b={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"02-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"50"}
        d=diff_rows([a],[b],ND_EXACT,ND_COARSE)
        self.assertEqual(d["parent_rows_not_repeated_in_amendment"],1); self.assertTrue(d["classification_candidate_only"])
    def test_diff_never_claims_confirmation(self):
        a={"SECURITY_TITLE":"Common Stock","TRANS_DATE":"01-JUN-2026","TRANS_FORM_TYPE":"4","TRANS_CODE":"S","TRANS_SHARES":"100"}
        self.assertTrue(diff_rows([a],[a],ND_EXACT,ND_COARSE)["classification_candidate_only"])

if __name__=="__main__": unittest.main()
