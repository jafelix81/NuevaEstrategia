import csv
import io
import unittest
import zipfile

from research.phase195_cboe_trade_condition_exchange_mapping_audit import (
    classify_condition,
    parse_condition_mapping,
    parse_exchange_mapping_csv,
    read_xlsx_sheets,
    count_sample_ids,
)

def make_xlsx():
    shared = [
        "Trade Condition ID","Name","Message Type","Security Types",
        "0","Regular","trade","option",
        "18","Complex Spread","trade","option",
        "95","Late Report","trade","option"
    ]
    shared_xml = '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' + "".join(f"<si><t>{x}</t></si>" for x in shared) + "</sst>"
    workbook = """<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Conditions" sheetId="1" r:id="rId1"/></sheets></workbook>"""
    rels = """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>"""
    rows=[]
    for r, values in enumerate([[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,10,11]],1):
        cells=[]
        for c,v in enumerate(values):
            col=chr(65+c)
            cells.append(f'<c r="{col}{r}" t="s"><v>{v}</v></c>')
        rows.append(f'<row r="{r}">{"".join(cells)}</row>')
    sheet = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+"".join(rows)+"</sheetData></worksheet>"
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",workbook)
        z.writestr("xl/_rels/workbook.xml.rels",rels)
        z.writestr("xl/sharedStrings.xml",shared_xml)
        z.writestr("xl/worksheets/sheet1.xml",sheet)
    return buff.getvalue()

def sample_zip():
    fields=["trade_condition_id","exchange_id","canceled_trade_condition_id"]
    rows=[{"trade_condition_id":"18","exchange_id":"1","canceled_trade_condition_id":"0"},
          {"trade_condition_id":"95","exchange_id":"2","canceled_trade_condition_id":"0"}]
    out=io.StringIO()
    w=csv.DictWriter(out,fieldnames=fields,lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    payload=out.getvalue().encode()
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("UnderlyingOptionsTrades_2026-01-07.csv",payload)
        z.writestr("UnderlyingOptionsTradesCalcs_2026-01-07.csv",payload)
    return buff.getvalue()

class Phase195Tests(unittest.TestCase):
    def test_xlsx_reader_resolves_workbook_relationship_and_shared_strings(self):
        sheets=read_xlsx_sheets(make_xlsx())
        self.assertIn("Conditions",sheets)
        self.assertEqual(sheets["Conditions"][0][0],"Trade Condition ID")
        self.assertEqual(sheets["Conditions"][1][1],"Regular")

    def test_condition_mapping_extracts_ids_names_types_and_security(self):
        mapping=parse_condition_mapping(make_xlsx())
        self.assertEqual(mapping["row_count"],3)
        self.assertEqual(mapping["mapping_by_id"][0]["name"],"Regular")
        self.assertEqual(mapping["mapping_by_id"][18]["message_type"],"trade")
        self.assertEqual(mapping["mapping_by_id"][95]["security_types"],"option")

    def test_condition_mapping_does_not_invent_effective_dates(self):
        mapping=parse_condition_mapping(make_xlsx())
        self.assertEqual(mapping["effective_date_fields"],[])

    def test_condition_classification_regular(self):
        self.assertEqual(classify_condition({"name":"Regular","fields":{}}),"regular")

    def test_condition_classification_complex(self):
        self.assertEqual(classify_condition({"name":"Complex Spread","fields":{}}),"complex_or_spread")

    def test_condition_classification_late(self):
        self.assertEqual(classify_condition({"name":"Late Report","fields":{}}),"late_or_out_of_sequence")

    def test_condition_classification_cancel(self):
        self.assertEqual(classify_condition({"name":"Cancel/Correction","fields":{}}),"cancel_or_correction")

    def test_exchange_csv_mapping_parses_id_name_code(self):
        payload=b"Exchange ID,Exchange Name,Exchange Code\n1,Example Options,EX\n2,Another Options,AO\n"
        mapping=parse_exchange_mapping_csv(payload)
        self.assertEqual(mapping["row_count"],2)
        self.assertEqual(mapping["mapping_by_id"][1]["name"],"Example Options")
        self.assertEqual(mapping["mapping_by_id"][2]["code"],"AO")

    def test_sample_counts_condition_exchange_and_cancel_ids(self):
        result=count_sample_ids(sample_zip())
        self.assertEqual(result["member_count"],2)
        self.assertTrue(result["core_id_counts_match_across_members"])
        self.assertEqual(result["observed_condition_counts"],{"18":1,"95":1})
        self.assertEqual(result["observed_exchange_counts"],{"1":1,"2":1})
        self.assertEqual(result["observed_canceled_condition_counts"],{"0":2})

    def test_sample_count_output_contains_no_trade_rows_or_symbols(self):
        result=count_sample_ids(sample_zip())
        rendered=str(result)
        self.assertNotIn("XYZ",rendered)
        self.assertNotIn("1.25",rendered)
        self.assertEqual(result["members"][0]["nonblank_rows"],2)

if __name__ == "__main__":
    unittest.main()
