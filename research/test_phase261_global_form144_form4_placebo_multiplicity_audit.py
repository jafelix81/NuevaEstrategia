import math, unittest
from phase261_global_form144_form4_placebo_multiplicity_audit import holm_adjust, extract_tests, F144, F4

def mkrow(e=0,p=None,status="COMPLETED"):
    n=1000
    return {"status":status,"replicates":n,"null_replicates_at_or_above_observed":e,"empirical_tail_plus_one":(e+1)/(n+1) if p is None else p,"observed_mutable_exact_links":10,"null_mean":2.0,"null_max":5}

def data(phase,names,sample=None):
    if sample is None: sample={"eligible_notices":1451,"eligible_tranches":1460,"form4_unique_owner_sale_blocks":10525,"exact_date_share_links":521,"fallback_links":49}
    inputs={"form144_csv_sha256":F144,"form144_sha256":F144,"form4_inner_zip_sha256":F4}
    d={"phase":phase,"inputs":inputs,"sample":sample,"decision":{"alpha_test_authorized":False,"holdout_used":False,"f80_frozen":True}}
    if phase==256: d["permutation_audit"]={"placebos":{n:mkrow() for n in names}}
    else: d["placebos"]={n:mkrow() for n in names}
    return d

class Phase261Tests(unittest.TestCase):
    def test_holm_ties(self):
        p={f"z{i}":1/1001 for i in range(11)}; p.update(month=22/1001,week=534/1001); a=holm_adjust(p)
        self.assertTrue(all(math.isclose(a[f"z{i}"],13/1001) for i in range(11))); self.assertAlmostEqual(a["month"],44/1001); self.assertAlmostEqual(a["week"],534/1001)
    def test_holm_monotonic(self):
        a=holm_adjust({"a":.001,"b":.01,"c":.2}); self.assertLessEqual(a["a"],a["b"]); self.assertLessEqual(a["b"],a["c"])
    def test_phase256_nested(self):
        n={"owner_identity_within_issuer","filing_lag_within_issuer_owner","shares_within_issuer_owner","filing_lag_and_shares_within_issuer_owner"}; self.assertEqual(len(extract_tests(data(256,n),256)),4)
    def test_phase257(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; self.assertEqual(len(extract_tests(data(257,n),257)),3)
    def test_phase258(self):
        n={"issuer_owner_cik","issuer_owner_cik_month","issuer_owner_cik_iso_week"}; self.assertEqual(len(extract_tests(data(258,n),258)),3)
    def test_phase260(self):
        n={"issuer_owner_cik_weekday","issuer_owner_cik_month_weekday","issuer_owner_cik_iso_week_weekday"}; s={"eligible_original_notices":1451,"eligible_proposed_sale_tranches":1460,"form4_sale_blocks":10525,"exact_date_share_links":521,"fallback_links_separate":49}; self.assertEqual(len(extract_tests(data(260,n,s),260)),3)
    def test_rejects_wrong_p(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; d=data(257,n); d["placebos"]["issuer_owner"]["empirical_tail_plus_one"]=.001
        with self.assertRaises(ValueError): extract_tests(d,257)
    def test_rejects_wrong_hash(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; d=data(257,n); d["inputs"]["form144_sha256"]="0"*64
        with self.assertRaises(ValueError): extract_tests(d,257)
    def test_rejects_incomplete_stratum(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; d=data(257,n); d["placebos"]["issuer_owner_iso_week"]["status"]="INSUFFICIENT"
        with self.assertRaises(ValueError): extract_tests(d,257)
    def test_rejects_alpha(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; d=data(257,n); d["decision"]["alpha_test_authorized"]=True
        with self.assertRaises(ValueError): extract_tests(d,257)
    def test_rejects_sample_drift(self):
        n={"issuer_owner","issuer_owner_month","issuer_owner_iso_week"}; s={"eligible_notices":1451,"eligible_tranches":1460,"form4_unique_owner_sale_blocks":10524,"exact_date_share_links":521,"fallback_links":49}
        with self.assertRaises(ValueError): extract_tests(data(257,n,s),257)
    def test_plus_one_never_zero(self): self.assertAlmostEqual(1/1001,.000999000999000999); self.assertGreater(1/1001,0)
    def test_zero_exceedance_upper(self): self.assertAlmostEqual(1-.05**(1/1000),.0029912495450953314)

if __name__=="__main__": unittest.main()
