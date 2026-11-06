import hashlib, json, tempfile, unittest
from pathlib import Path
from research.phase149_openfigi_cusip_crosswalk_audit import load_cusips, summarize, valid_cusip, run_audit

class Phase149Tests(unittest.TestCase):
    def test_cusip_check_digit(self):
        self.assertTrue(valid_cusip("037833100"))
        self.assertFalse(valid_cusip("037833101"))
    def test_leading_zero_preserved(self):
        self.assertTrue(valid_cusip("00091G104"))
    def test_bad_length_rejected(self):
        self.assertFalse(valid_cusip("12345678"))
    def test_one_share_class_deduplicates_venue_figis(self):
        x=summarize("00091G104",{"data":[
          {"figi":"F1","shareClassFIGI":"SC1","ticker":"ABC","marketSector":"Equity","securityType2":"Common Stock"},
          {"figi":"F2","shareClassFIGI":"SC1","ticker":"ABC","marketSector":"Equity","securityType2":"Common Stock"}]})
        self.assertEqual(x["status"],"MAPPED_ONE_IDENTITY"); self.assertEqual(x["figi_count"],2)
    def test_multiple_share_classes_stay_ambiguous(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1"},{"figi":"F2","shareClassFIGI":"SC2"}]})
        self.assertEqual(x["status"],"MAPPED_MULTIPLE_IDENTITIES")
    def test_mixed_identity_key_levels_not_called_multiple(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1"},{"figi":"F2","compositeFIGI":"C1"}]})
        self.assertEqual(x["status"],"MAPPED_MIXED_IDENTITY_KEY_LEVEL")
    def test_fallback_to_composite(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","compositeFIGI":"C1"},{"figi":"F2","compositeFIGI":"C1"}]})
        self.assertEqual(x["status"],"MAPPED_ONE_IDENTITY")
        self.assertEqual(x["identity_key_types"],["compositeFIGI"])
    def test_no_match_and_api_error_separate(self):
        self.assertEqual(summarize("00091G104",{"warning":"No identifier found"})["status"],"NO_MATCH")
        self.assertEqual(summarize("00091G104",{"error":"failure"})["status"],"API_ERROR")
    def test_non_equity_not_counted_as_equity(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","marketSector":"Corp","securityType":"Bond"}]})
        self.assertFalse(x["has_equity_match"]); self.assertFalse(x["has_common_stock_match"])
    def test_multiple_names_tickers_preserved(self):
        x=summarize("00091G104",{"data":[
          {"figi":"F1","shareClassFIGI":"SC1","ticker":"ABC","name":"ABC INC"},
          {"figi":"F2","shareClassFIGI":"SC1","ticker":"ABC1","name":"ABC CORP"}]})
        self.assertEqual(x["tickers"],["ABC","ABC1"]); self.assertEqual(x["names"],["ABC CORP","ABC INC"])
    def test_unpinned_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_text("[]")
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"): load_cusips(p)
    def test_batching_and_rate_spacing(self):
        source=Path(__file__).with_name("phase149_cusip_input.json")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_bytes(source.read_bytes())
            import research.phase149_openfigi_cusip_crosswalk_audit as mod
            old=mod.INPUT_SHA256; mod.INPUT_SHA256=hashlib.sha256(p.read_bytes()).hexdigest()
            calls=[]; sleeps=[]
            def fake(jobs):
                calls.append(jobs); t="2026-11-06T00:00:00Z"
                return {"status_code":200,"attempts":1,"started_at_utc":t,"received_at_utc":t,
                  "response_sha256":"a"*64,"response":[{"data":[{"figi":"F1","shareClassFIGI":"SC1"}]} for _ in jobs]}
            try: out=run_audit(p,Path(d)/"out",post_func=fake,sleeper=sleeps.append,delay_seconds=2.5)
            finally: mod.INPUT_SHA256=old
            self.assertEqual(len(calls),56); self.assertTrue(all(len(x)<=10 for x in calls))
            self.assertEqual(len(sleeps),55); self.assertTrue(all(x==2.5 for x in sleeps))
            self.assertEqual(out["summary"]["input_cusips"],553)
    def test_rate_limit_cannot_be_bypassed(self):
        source=Path(__file__).with_name("phase149_cusip_input.json")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_bytes(source.read_bytes())
            import research.phase149_openfigi_cusip_crosswalk_audit as mod
            old=mod.INPUT_SHA256; mod.INPUT_SHA256=hashlib.sha256(p.read_bytes()).hexdigest()
            try:
                with self.assertRaisesRegex(ValueError,"at least 2.5 seconds"):
                    run_audit(p,Path(d)/"out",delay_seconds=0)
            finally: mod.INPUT_SHA256=old

if __name__=="__main__": unittest.main()
