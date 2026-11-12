import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from research.phase343_form4_candidate_specific_event_time_crosswalk import (
    crosswalk_symbol_to_anchor,
    extract_candidate_rows,
    norm_date,
    parse_ownership_document,
    select_prior_anchor,
    transaction_signature,
)


class FakeClient:
    def __init__(self, payloads):
        self.payloads = payloads
    def get(self, url, max_bytes=20_000_000):
        name = url.rsplit("/", 1)[-1]
        if name in self.payloads:
            return self.payloads[name], 200, "", {}
        return None, 404, "HTTP_404", {}


class Phase343Tests(unittest.TestCase):
    def test_parse_ownership_xml_extracts_issuer_owner_transaction_and_footnote(self):
        raw = b"""<?xml version="1.0"?>
        <ownershipDocument>
          <issuer><issuerCik>0000000123</issuerCik><issuerTradingSymbol>NYSE: ABC</issuerTradingSymbol></issuer>
          <aff10b5One>0</aff10b5One>
          <reportingOwner><reportingOwnerId><rptOwnerCik>0000000456</rptOwnerCik><rptOwnerName>Test Owner</rptOwnerName></reportingOwnerId>
            <reportingOwnerRelationship><isDirector>1</isDirector><isOfficer>0</isOfficer><isTenPercentOwner>0</isTenPercentOwner></reportingOwnerRelationship>
          </reportingOwner>
          <nonDerivativeTable><nonDerivativeTransaction>
            <securityTitle><value>Common Stock</value></securityTitle>
            <transactionDate><value>2026-07-31</value></transactionDate>
            <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
            <transactionAmounts><transactionShares><value>100</value></transactionShares>
              <transactionPricePerShare><value>10.00</value></transactionPricePerShare>
              <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode></transactionAmounts>
            <ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
            <footnoteId id="F1"/>
          </nonDerivativeTransaction></nonDerivativeTable>
          <footnotes><footnote id="F1">Open market purchase</footnote></footnotes>
        </ownershipDocument>"""
        parsed = parse_ownership_document(raw)
        self.assertEqual(parsed["issuer_cik"], "123")
        self.assertEqual(parsed["issuer_symbol_raw"], "NYSE: ABC")
        self.assertEqual(parsed["aff10b5one_raw"], "0")
        self.assertEqual(len(parsed["owners"]), 1)
        self.assertEqual(parsed["owners"][0]["cik"], "456")
        self.assertEqual(len(parsed["transactions"]), 1)
        self.assertEqual(parsed["transactions"][0]["transaction_code"], "P")
        self.assertEqual(parsed["transactions"][0]["footnote_text"], ["Open market purchase"])

    def test_complete_submission_selects_form4_xml_not_xsl_or_attachment(self):
        ownership = """<?xml version="1.0"?>
        <ownershipDocument>
          <issuer><issuerCik>0000000123</issuerCik><issuerTradingSymbol>ABC</issuerTradingSymbol></issuer>
          <aff10b5One>0</aff10b5One>
          <reportingOwner><reportingOwnerId><rptOwnerCik>0000000456</rptOwnerCik></reportingOwnerId></reportingOwner>
          <nonDerivativeTable><nonDerivativeTransaction>
            <securityTitle><value>Common Stock</value></securityTitle>
            <transactionDate><value>2026-07-31</value></transactionDate>
            <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
            <transactionAmounts><transactionShares><value>100</value></transactionShares>
              <transactionPricePerShare><value>10</value></transactionPricePerShare>
              <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode></transactionAmounts>
            <ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
          </nonDerivativeTransaction></nonDerivativeTable>
        </ownershipDocument>"""
        raw = (
            b"<SEC-DOCUMENT>0000000123-26-000001.txt</SEC-DOCUMENT>\n"
            b"<DOCUMENT><TYPE>GRAPHIC</TYPE><TEXT><XML><notOwnership/></XML></TEXT></DOCUMENT>\n"
            b"<DOCUMENT><TYPE>4</TYPE><TEXT><XML>" + ownership.encode("utf-8") +
            b"</XML></TEXT></DOCUMENT>\n"
        )
        parsed = parse_ownership_document(raw)
        self.assertEqual(parsed["issuer_cik"], "123")
        self.assertEqual(parsed["issuer_symbol_raw"], "ABC")
        self.assertEqual(len(parsed["transactions"]), 1)

    def test_transaction_signature_normalizes_dates_and_numeric_strings(self):
        a = {"security_title":"Common Stock","transaction_date":"31-JUL-2026",
             "transaction_code":"P","acquired_disposed":"A","direct_indirect":"D",
             "shares":"100.000","price":"10.00"}
        b = {"security_title":"Common Stock","transaction_date":"2026-07-31",
             "transaction_code":"P","acquired_disposed":"A","direct_indirect":"D",
             "shares":"100","price":"10"}
        self.assertEqual(transaction_signature(a), transaction_signature(b))

    def test_prior_anchor_is_latest_strictly_before_event_date(self):
        payload = {"filings":{"recent":{
            "form":["10-K","10-Q","10-Q","8-K","10-Q"],
            "filingDate":["2026-02-15","2026-07-15","2026-08-01","2026-07-30","2026-08-02"],
            "accessionNumber":["a","b","same-day","c","later"],
            "primaryDocument":["a.htm","b.htm","same.htm","c.htm","later.htm"],
            "reportDate":["2025-12-31","2026-06-30","2026-06-30","2026-06-30","2026-06-30"],
        },"files":[]}}
        anchor, source = select_prior_anchor(payload, "2026-08-01", FakeClient({}))
        self.assertEqual(anchor["accessionNumber"], "b")
        self.assertEqual(anchor["form"], "10-Q")
        self.assertEqual(source, "RECENT")

    def test_symbol_class_exchange_requires_same_context(self):
        associations = [{
            "symbol":"ABC",
            "association_status":"SYMBOL_12B_TITLE_AND_EXCHANGE_SAME_CONTEXT",
            "has_symbol_12b_title_exchange_same_context":True,
            "same_context_security_12b_titles":["Common Stock, par value $0.001"],
            "same_context_exchange_values":["NASDAQ"],
            "symbol_class_axis_members":[],
            "symbol_listing_axis_members":[],
            "symbol_context_ref":"ctx1",
        }]
        result = crosswalk_symbol_to_anchor("NASDAQ: ABC","Common Stock",associations)
        self.assertTrue(result["unique_symbol_context"])
        self.assertTrue(result["title_compatible"])
        self.assertEqual(result["matched_exchange"],"NASDAQ")

    def test_multi_listing_axis_is_quarantined(self):
        associations = [{
            "symbol":"ABC",
            "association_status":"MULTI_LISTING_AXIS_ON_SYMBOL_CONTEXT",
            "has_symbol_12b_title_exchange_same_context":True,
            "same_context_security_12b_titles":["Common Stock"],
            "same_context_exchange_values":["NYSE"],
        }]
        result = crosswalk_symbol_to_anchor("ABC","Common Stock",associations)
        self.assertFalse(result["unique_symbol_context"])

    def test_candidate_extraction_reproduces_one_synthetic_high_precision_row(self):
        tables = {
            "SUBMISSION.tsv": (
                ["ACCESSION_NUMBER","DOCUMENT_TYPE","FILING_DATE","ISSUERCIK","ISSUERNAME",
                 "ISSUERTRADINGSYMBOL","PERIOD_OF_REPORT","DATE_OF_ORIG_SUB","AFF10B5ONE"],
                [["acc-1","4","01-AUG-2026","123","Issuer","ABC","31-JUL-2026","","0"]],
            ),
            "NONDERIV_TRANS.tsv": (
                ["ACCESSION_NUMBER","NONDERIV_TRANS_SK","SECURITY_TITLE","TRANS_DATE","TRANS_FORM_TYPE",
                 "TRANS_CODE","TRANS_ACQUIRED_DISP_CD","DIRECT_INDIRECT_OWNERSHIP","TRANS_PRICEPERSHARE_FN",
                 "TRANS_SHARES","TRANS_PRICEPERSHARE"],
                [["acc-1","1","Common Stock","31-JUL-2026","4","P","A","D","F1","100","10"]],
            ),
            "REPORTINGOWNER.tsv": (["ACCESSION_NUMBER","RPTOWNERCIK"], [["acc-1","456"]]),
            "FOOTNOTES.tsv": (["ACCESSION_NUMBER","FOOTNOTE_ID","FOOTNOTE_TXT"], [["acc-1","F1","Open market purchase"]]),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.zip"
            with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as zf:
                for name,(fields,rows) in tables.items():
                    buf=io.StringIO(newline="")
                    writer=csv.writer(buf,delimiter="\t",lineterminator="\n")
                    writer.writerow(fields)
                    writer.writerows(rows)
                    zf.writestr(name,buf.getvalue().encode())
            raw=path.read_bytes()
            rows=extract_candidate_rows(raw,{"candidate_rows":1,"candidate_accessions":1,"candidate_issuer_ciks":1})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["accession"],"acc-1")
        self.assertEqual(rows[0]["filing_date"],"2026-08-01")
        self.assertEqual(rows[0]["filing_date_raw"],"01-AUG-2026")
        self.assertEqual(norm_date("29-SEP-2026"),"2026-09-29")
        self.assertEqual(rows[0]["owner_count_bulk"],1)
        self.assertEqual(rows[0]["aff10b5one_bulk"],"false")
        self.assertEqual(rows[0]["footnote_ids_bulk"],["F1"])


if __name__ == "__main__":
    unittest.main()
