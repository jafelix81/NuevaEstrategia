import csv, io, unittest, zipfile
from research.phase187_orats_near_eod_public_sample_pit_audit import EXPECTED_SAMPLE_DATE, audit_archive, audit_csv

HEADERS = ["ticker","tradeDate","expirDate","strike","callVolume","putVolume","callOpenInterest","putOpenInterest","updatedAt","callMidIv","putMidIv","smvVol","stockPrice"]

def sample_row(**overrides):
    row = {"ticker":"TEST","tradeDate":EXPECTED_SAMPLE_DATE,"expirDate":"2024-02-16","strike":"100",
           "callVolume":"10","putVolume":"8","callOpenInterest":"100","putOpenInterest":"120",
           "updatedAt":"2024-01-03T20:46:00Z","callMidIv":"0.25","putMidIv":"0.27",
           "smvVol":"0.26","stockPrice":"100.50"}
    row.update(overrides)
    return row

def csv_payload(rows, headers=HEADERS):
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=headers); writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode("utf-8")

def zip_payload(data, member="ORATS_SMV_Strikes_20240103.csv"):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive: archive.writestr(member,data)
    return stream.getvalue()

class Phase187OratsNearEodTests(unittest.TestCase):
    def test_public_sample_schema_and_aggregate_counts(self):
        r=audit_archive(zip_payload(csv_payload([sample_row(),sample_row(ticker="OTHER",strike="105")])),"2026-11-07T00:00:00+00:00")
        self.assertTrue(r["sample_schema_pass"]); self.assertTrue(r["sample_overall_pass"])
        self.assertEqual(r["member_audits"][0]["row_count"],2)
        self.assertEqual(r["member_audits"][0]["unique_underlying_count"],2)

    def test_trade_date_must_match_sample_filename_date(self):
        r=audit_archive(zip_payload(csv_payload([sample_row(tradeDate="2024-01-04")])))
        self.assertFalse(r["sample_overall_pass"])
        self.assertEqual(r["member_audits"][0]["trade_date_filename_mismatch_rows"],1)

    def test_duplicate_contract_keys_are_counted(self):
        r=audit_csv("sample_20240103.csv",csv_payload([sample_row(),sample_row()]))
        self.assertEqual(r["duplicate_contract_key_rows"],1)
        self.assertEqual(r["unique_contract_key_count"],1)

    def test_naive_updated_at_is_not_timezone_aware(self):
        r=audit_archive(zip_payload(csv_payload([sample_row(updatedAt="2024-01-03T15:46:00")])))
        self.assertFalse(r["sample_overall_pass"])
        self.assertEqual(r["member_audits"][0]["updated_at_naive_rows"],1)

    def test_missing_required_header_fails_schema_gate(self):
        headers=[x for x in HEADERS if x!="putOpenInterest"]
        r=audit_csv("sample_20240103.csv",csv_payload([sample_row()],headers=headers))
        self.assertFalse(r["schema_pass"]); self.assertIn("put_oi",r["missing_required_fields"])

    def test_zero_iv_is_unavailable_not_zero_volatility(self):
        r=audit_csv("sample_20240103.csv",csv_payload([sample_row(callMidIv="0",putMidIv="")]))
        self.assertEqual(r["iv_zero_or_missing_counts"]["call_mid_iv"],1)
        self.assertEqual(r["iv_zero_or_missing_counts"]["put_mid_iv"],1)

    def test_flow_and_owner_identity_are_never_inferred(self):
        r=audit_archive(zip_payload(csv_payload([sample_row()])))
        self.assertFalse(r["aggressor_side_available"]); self.assertFalse(r["open_close_available"])
        self.assertFalse(r["participant_capacity_available"]); self.assertFalse(r["beneficial_owner_identity_available"])
        self.assertIn("not interval increments or signed flow",r["measurement_semantics"]["call_put_volume"])

    def test_raw_symbols_and_rows_are_not_persisted(self):
        r=audit_archive(zip_payload(csv_payload([sample_row()])))
        self.assertNotIn("TEST",str(r))
        self.assertFalse(r["controls"]["raw_rows_persisted"]); self.assertFalse(r["controls"]["raw_symbols_persisted"])

    def test_archive_without_csv_fails_closed(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive: archive.writestr("README.txt","sample")
        with self.assertRaises(ValueError): audit_archive(stream.getvalue())

if __name__=="__main__": unittest.main()
