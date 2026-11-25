import unittest

from research.phase607_sec_13f_source_xml_reconciliation import (
    extract_xml_urls,
    parse_13f_xml,
    summarize_source_xml,
    tokenize_reference,
)


class Phase607Tests(unittest.TestCase):
    def test_index_html_extracts_only_xml_document_links(self):
        html = b"""<html><a href="xslForm13F_X02/primary_doc.xml">primary_doc.xml</a>
        <a href="xslForm13F_X02/infotable.xml">infotable.xml</a>
        <a href="primary_doc.html">HTML</a></html>"""
        urls = extract_xml_urls(html, "https://www.sec.gov/Archives/edgar/data/1/0001/0001-index.htm")
        self.assertEqual(len(urls), 2)
        self.assertTrue(any(url.endswith("primary_doc.xml") for url in urls))
        self.assertTrue(any(url.endswith("infotable.xml") for url in urls))

    def test_reference_tokenizer_separates_zero_and_nonnumeric(self):
        out = tokenize_reference("1, 2 3,0,XXEC")
        self.assertEqual(out["numeric_tokens"], ["1", "2", "3"])
        self.assertEqual(out["zero_tokens"], 1)
        self.assertEqual(out["nonnumeric_tokens"], ["XXEC"])

    def test_namespaced_xml_extracts_manager_sequences_and_info_refs(self):
        payload = b"""<?xml version="1.0"?>
        <edgarSubmission xmlns="urn:test">
          <coverPage><otherManagersInfo>
            <otherManager2><sequenceNumber>1</sequenceNumber><cik>0000000001</cik><name>Manager A</name></otherManager2>
            <otherManager2><sequenceNumber>2</sequenceNumber><cik>0000000002</cik><name>Manager B</name></otherManager2>
          </otherManagersInfo></coverPage>
          <informationTable>
            <infoTable><nameOfIssuer>ABC</nameOfIssuer><otherManager>1,2</otherManager></infoTable>
            <infoTable><nameOfIssuer>XYZ</nameOfIssuer><otherManager>0</otherManager></infoTable>
          </informationTable>
        </edgarSubmission>"""
        out = parse_13f_xml(payload)
        self.assertEqual([x["sequence_number"] for x in out["manager_entries"]], ["1", "2"])
        self.assertEqual(out["info_table_rows"], 2)
        self.assertEqual(out["info_tokens"], ["1", "2", "ZERO"])

    def test_source_summary_detects_duplicate_sequences_and_unmatched_refs(self):
        docs = [{
            "manager_entries": [
                {"sequence_number":"1"}, {"sequence_number":"1"}, {"sequence_number":"2"}
            ],
            "info_table_rows": 2,
            "info_tokens": ["1","2","9","ZERO","NONNUM:Wellesley"],
        }]
        out = summarize_source_xml(docs)
        self.assertEqual(out["duplicate_sequence_values"], {"1":2})
        self.assertEqual(out["sequence_matched_tokens"], 2)
        self.assertEqual(out["ambiguous_sequence_tokens"], 1)
        self.assertEqual(out["unmatched_numeric_tokens"], 1)
        self.assertEqual(out["zero_reference_tokens"], 1)
        self.assertEqual(out["nonnumeric_reference_tokens"], 1)


if __name__ == "__main__":
    unittest.main()
