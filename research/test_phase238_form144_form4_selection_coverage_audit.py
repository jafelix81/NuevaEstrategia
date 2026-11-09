import csv
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from research.phase238_form144_form4_selection_coverage_audit import (
    family, exact_first, load144, load4, conditional
)


class Phase238Tests(unittest.TestCase):
    def test_class_family(self):
        self.assertEqual(family("Class A Common Stock"), "CLASS_A")
        self.assertEqual(family("Ordinary Shares"), "ORDINARY")
        self.assertEqual(family("American Depositary Shares"), "DEPOSITARY")
        self.assertEqual(family("Common Stock"), "COMMON")
        self.assertEqual(family(""), "UNKNOWN")

    def test_form144_right_censored_multitranche_notice_is_excluded(self):
        rows = [
            {"include_as_issuer_event":"true","xml_issuer_cik":"0000000001",
             "quarter":"2026Q3","form":"144","accession":"N1","seller_name":"Alice",
             "plan_adoption_dates":"",
             "sale_tranches_json":json.dumps([
                 {"sale_tranche_index":1,"approx_sale_date_iso":"2026-09-24","units_numeric":"100","security_class":"Common"},
                 {"sale_tranche_index":2,"approx_sale_date_iso":"2026-09-25","units_numeric":"200","security_class":"Common"}])},
            {"include_as_issuer_event":"true","xml_issuer_cik":"0000000001",
             "quarter":"2026Q3","form":"144","accession":"N2","seller_name":"Bob",
             "plan_adoption_dates":"2026-01-01",
             "sale_tranches_json":json.dumps([
                 {"sale_tranche_index":1,"approx_sale_date_iso":"2026-09-24","units_numeric":"300","security_class":"Class A"}])},
            {"include_as_issuer_event":"true","xml_issuer_cik":"0000000001",
             "quarter":"2026Q3","form":"144/A","accession":"N3","seller_name":"Carol",
             "plan_adoption_dates":"","sale_tranches_json":"[]"},
            {"include_as_issuer_event":"false","xml_issuer_cik":"0000000002",
             "quarter":"2026Q3","form":"144","accession":"N4","seller_name":"Dan",
             "plan_adoption_dates":"","sale_tranches_json":"[]"}
        ]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"f144.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
            r=load144(p)
        self.assertEqual(r["q3"],2)
        self.assertEqual(r["notices"],1)
        self.assertEqual(r["excluded"],1)
        self.assertEqual({t["accession"] for t in r["tranches"]},{"N2"})

    def test_exact_first_reserves_ambiguous_exact_nodes(self):
        tr=[
            {"accession":"N1","idx":"1","issuer":"1","seller":"ALICE","date":date(2026,9,10),"units":100,"family":"COMMON"},
            {"accession":"N2","idx":"1","issuer":"1","seller":"BOB","date":date(2026,9,10),"units":200,"family":"COMMON"},
            {"accession":"N3","idx":"1","issuer":"1","seller":"CAROL","date":date(2026,9,10),"units":300,"family":"COMMON"},
            {"accession":"N4","idx":"1","issuer":"1","seller":"CAROL","date":date(2026,9,10),"units":300,"family":"COMMON"}]
        bs=[
            {"accession":"F1","date":date(2026,9,10),"issuer":"1","owner":"ALICE","shares":100,"family":"COMMON"},
            {"accession":"F2","date":date(2026,9,11),"issuer":"1","owner":"BOB","shares":200,"family":"COMMON"},
            {"accession":"F3","date":date(2026,9,10),"issuer":"1","owner":"CAROL","shares":300,"family":"COMMON"}]
        ee,eu,fe,fu,ambt,ambb=exact_first(tr,bs)
        self.assertEqual((len(ee),len(eu),len(fu),ambt,ambb),(3,1,1,2,1))
        self.assertEqual(eu[0][0]["seller"],"ALICE")
        self.assertEqual(fu[0][0]["seller"],"BOB")

    def test_conditional_permutation_is_deterministic_and_stratified(self):
        rows=[
            {"issuer":"A","role":"Officer","plan":True,"matched":True},
            {"issuer":"A","role":"Officer","plan":False,"matched":False},
            {"issuer":"A","role":"Director","plan":True,"matched":False},
            {"issuer":"B","role":"Officer","plan":True,"matched":True}]
        a=conditional(rows,("issuer","role"),200,9)
        b=conditional(rows,("issuer","role"),200,9)
        self.assertEqual(a,b)
        self.assertEqual(a["mixed_strata"],1)
        self.assertEqual(a["blocks"],2)
        self.assertEqual(a["plan_n"],1)
        self.assertEqual(a["nonplan_n"],1)

    def test_form4_loader_excludes_late_joint_and_non_sale_rows(self):
        subs=["ACCESSION_NUMBER\tFILING_DATE\tDOCUMENT_TYPE\tISSUERCIK\tAFF10B5ONE",
              "A1\t30-SEP-2026\t4\t0000000001\t1",
              "A2\t30-SEP-2026\t4\t0000000001\t0",
              "A3\t30-SEP-2026\t4/A\t0000000001\t0"]
        owners=["ACCESSION_NUMBER\tRPTOWNERCIK\tRPTOWNERNAME\tRPTOWNER_RELATIONSHIP",
                "A1\t0000000002\tAlice Example\tOfficer",
                "A2\t0000000003\tBob Example\tDirector",
                "A2\t0000000004\tOther Owner\tDirector",
                "A3\t0000000005\tCarol Example\tOfficer"]
        tx=["ACCESSION_NUMBER\tNONDERIV_TRANS_SK\tTRANS_FORM_TYPE\tTRANS_CODE\tTRANS_ACQUIRED_DISP_CD\tTRANS_TIMELINESS\tTRANS_DATE\tTRANS_SHARES\tSECURITY_TITLE",
            "A1\t1\t4\tS\tD\t\t29-SEP-2026\t100\tCommon Stock",
            "A1\t2\t4\tS\tD\tL\t29-SEP-2026\t50\tCommon Stock",
            "A1\t3\t4\tP\tD\t\t29-SEP-2026\t20\tCommon Stock",
            "A2\t4\t4\tS\tD\t\t29-SEP-2026\t200\tCommon Stock",
            "A3\t5\t4\tS\tD\t\t29-SEP-2026\t300\tCommon Stock"]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"f4.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("SUBMISSION.tsv","\n".join(subs)+"\n")
                z.writestr("REPORTINGOWNER.tsv","\n".join(owners)+"\n")
                z.writestr("NONDERIV_TRANS.tsv","\n".join(tx)+"\n")
            r=load4(p,{"1"})
        self.assertEqual(r["max_filing_date"],"2026-09-30")
        self.assertEqual(len(r["blocks"]),1)
        self.assertEqual(str(r["blocks"][0]["shares"]),"100")
        self.assertEqual(r["blocks"][0]["plan"],True)


if __name__=="__main__":
    unittest.main()
