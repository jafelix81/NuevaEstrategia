import json
import unittest
from pathlib import Path
from phase401_form144a_full_parent_identity_census import (
    accession, compare, load_phase400_parents, curated_parent, tranche_sig, tranche_payload_changed
)

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/"PHASE401_FORM144_CANDIDATE_CIK_MANIFEST_2026-11-14.json"

class Phase401Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.candidates=set(cls.manifest["candidate_ciks"])

    def make_doc(self,issuer,filer,remarks=None,tranches=None):
        return {"ok":True,"parsed":{"issuer_cik":issuer,"filer_cik":filer,"issuer_name":"ISSUER",
            "seller_name":"SELLER","submission_type":"144","remarks":remarks or []},
            "tranches":tranches or self.make_tranche(),"url":"https://www.sec.gov/example.xml","sha256":"abc",
            "form_matches_index":True,"issuer_in_pair":True,"filer_in_pair":True}

    def make_tranche(self,units="100",value="1000"):
        return [{"class":"COMMON","units":units,"value":value,"outstanding":"1000000",
            "approx_sale_date":"2023-05-01","exchange":"NYSE","broker":"BROKER"}]

    def compare_pair(self,parent_cik,child_cik,remarks=None):
        parent=self.make_doc(parent_cik,"0000009999")
        child=self.make_doc(child_cik,"0000009999",remarks=remarks); child["parsed"]["submission_type"]="144/A"
        child_row={"accession":"0000000001-23-000002","filing_date":"2023-05-02"}
        parent_row={"accession":"0000000001-23-000001","filing_date":"2023-05-01"}
        return compare(child,parent,child_row,parent_row,self.candidates,"master_index")

    def test_manifest_is_exact_phase67_candidate_snapshot(self):
        self.assertEqual(len(self.candidates),290)
        self.assertTrue(all(len(x)==10 and x.isdigit() for x in self.candidates))
        self.assertEqual(self.manifest["source_artifact_id"],13334881835)

    def test_accession_normalization(self):
        self.assertEqual(accession("000176626423000002"),"0001766264-23-000002")
        self.assertEqual(accession("0001766264-23-000002"),"0001766264-23-000002")
        self.assertIsNone(accession("not-an-accession"))

    def test_candidate_parent_to_noncandidate_child(self):
        row=self.compare_pair(sorted(self.candidates)[0],"9999999999")
        self.assertEqual(row["candidate_membership_transition"],"parent_candidate_to_child_noncandidate")
        self.assertTrue(row["issuer_cik_changed"])

    def test_noncandidate_parent_to_candidate_child(self):
        row=self.compare_pair("9999999999",sorted(self.candidates)[0])
        self.assertEqual(row["candidate_membership_transition"],"parent_noncandidate_to_child_candidate")

    def test_issuer_change_is_not_automatically_called_correction(self):
        row=self.compare_pair("9999999999",sorted(self.candidates)[0],["Amends and supersedes prior notice"])
        self.assertTrue(row["issuer_cik_changed"])
        self.assertFalse(row["remarks_explicit_identity_correction"])

    def test_explicit_issuer_cik_correction(self):
        row=self.compare_pair("9999999999",sorted(self.candidates)[0],["The issuer CIK was corrected"])
        self.assertTrue(row["remarks_explicit_identity_correction"])

    def test_tranche_signature_is_deterministic_and_payload_sensitive(self):
        a=[{"security_class":"COMMON","units_numeric":"100","value_numeric":"1000","outstanding_numeric":"1000000","approx_sale_date_iso":"2023-05-01","exchange":"NYSE","broker_or_market_maker":"BROKER"}]
        b=[dict(a[0])]
        self.assertEqual(tranche_sig(a),tranche_sig(b))
        b[0]["units_numeric"]="101"
        self.assertNotEqual(tranche_sig(a),tranche_sig(b))

    def test_missing_parent_broker_is_not_treated_as_a_change(self):
        child=[{"class":"COMMON","units":"100","value":"1000","outstanding":"1000000",
            "approx_sale_date":"2023-05-01","exchange":"NYSE","broker":"BROKER"}]
        parent=[{"class":"COMMON","units":"100","value":"1000","outstanding":"1000000",
            "approx_sale_date":"2023-05-01","exchange":"NYSE","broker":None}]
        self.assertFalse(tranche_payload_changed(child,parent))

    def test_parent_child_date_inversion_is_exposed(self):
        candidate=sorted(self.candidates)[0]
        parent=self.make_doc(candidate,"0000009999")
        child=self.make_doc(candidate,"0000009999"); child["parsed"]["submission_type"]="144/A"
        child_row={"accession":"0000000001-23-000002","filing_date":"2023-05-01"}
        parent_row={"accession":"0000000001-23-000001","filing_date":"2023-05-02"}
        result=compare(child,parent,child_row,parent_row,self.candidates,"master_index")
        self.assertFalse(result["parent_child_date_order_ok"])

    def test_phase400_fallback_preserves_original_parent_identity(self):
        parents=load_phase400_parents()
        self.assertIn("0001766264-23-000002",parents)
        parent=curated_parent(parents["0001766264-23-000002"])
        self.assertTrue(parent["ok"])
        self.assertEqual(parent["parsed"]["issuer_cik"],"0000740906")
        self.assertTrue(parent["curated_phase400_fallback"])

if __name__=="__main__": unittest.main()
