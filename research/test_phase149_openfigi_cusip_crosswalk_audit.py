import hashlib, tempfile, unittest
from pathlib import Path
from research.phase149_openfigi_cusip_crosswalk_audit import load_cusips, summarize, valid_cusip, run_audit, build_cross_cusip_links

class Phase149Tests(unittest.TestCase):
    def test_cusip_check_digit(self):
        self.assertTrue(valid_cusip("037833100")); self.assertFalse(valid_cusip("037833101"))
    def test_leading_zero_preserved(self): self.assertTrue(valid_cusip("00091G104"))
    def test_bad_length_rejected(self): self.assertFalse(valid_cusip("12345678"))
    def test_venue_figis_collapse_to_one_share_class(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1","ticker":"ABC"},{"figi":"F2","shareClassFIGI":"SC1","ticker":"ABC"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_ONE_SHARE_CLASS"); self.assertEqual(x["figi_count"],2)
    def test_shareclass_with_missing_shareclass_rows_stays_one_shareclass(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1"},{"figi":"F2","compositeFIGI":"C1"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_ONE_SHARE_CLASS"); self.assertEqual(x["rows_missing_share_class_figi"],1)
    def test_multiple_shareclasses_stay_ambiguous(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1"},{"figi":"F2","shareClassFIGI":"SC2"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_MULTIPLE_SHARE_CLASSES")
    def test_composite_only_classification(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","compositeFIGI":"C1"},{"figi":"F2","compositeFIGI":"C1"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_ONE_COMPOSITE_ONLY")
    def test_multiple_composites_only_remain_unresolved(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","compositeFIGI":"C1"},{"figi":"F2","compositeFIGI":"C2"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_MULTIPLE_COMPOSITES_ONLY")
    def test_figi_only_fallback(self):
        x=summarize("00091G104",{"data":[{"figi":"F1"}]},"ID_CUSIP")
        self.assertEqual(x["status"],"MAPPED_ONE_FIGI_ONLY")
    def test_no_match_and_api_error_separate(self):
        self.assertEqual(summarize("00091G104",{"warning":"No identifier found"},"ID_CUSIP")["status"],"NO_MATCH")
        self.assertEqual(summarize("00091G104",{"error":"failure"},"ID_CUSIP")["status"],"API_ERROR")
    def test_non_equity_not_counted_as_equity(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","marketSector":"Muni","securityType":"Municipal"}]},"ID_CUSIP")
        self.assertFalse(x["has_equity_match"]); self.assertTrue(x["has_muni_match"])
    def test_multiple_tickers_names_preserved(self):
        x=summarize("00091G104",{"data":[{"figi":"F1","shareClassFIGI":"SC1","ticker":"ABC","name":"ABC INC"},{"figi":"F2","shareClassFIGI":"SC1","ticker":"ABC1","name":"ABC CORP"}]},"ID_CUSIP")
        self.assertEqual(x["tickers"],["ABC","ABC1"]); self.assertEqual(x["names"],["ABC CORP","ABC INC"])
    def test_cross_cusip_shareclass_link(self):
        rows=[{"cusip":"00091G104","share_class_figis":["SC1"]},{"cusip":"00091G105","share_class_figis":["SC1"]}]
        self.assertEqual(build_cross_cusip_links(rows),[{"shareClassFIGI":"SC1","cusips":["00091G104","00091G105"]}])
    def test_unpinned_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_text("[]")
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"): load_cusips(p)
    def test_two_pass_batching_and_rate_spacing(self):
        source=Path(__file__).with_name("phase149_cusip_input.json")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_bytes(source.read_bytes())
            import research.phase149_openfigi_cusip_crosswalk_audit as mod
            old=mod.INPUT_SHA256; mod.INPUT_SHA256=hashlib.sha256(p.read_bytes()).hexdigest()
            calls=[]; sleeps=[]
            def fake(jobs):
                calls.append(jobs); t="2026-11-06T00:00:00Z"
                is_fallback=jobs[0]["idType"]=="ID_CUSIP_8_CHR"
                items=([{"data":[{"figi":"F1","shareClassFIGI":"SC1"}]} for _ in jobs] if is_fallback
                       else [{"warning":"No identifier found"} for _ in jobs])
                return {"status_code":200,"attempts":1,"started_at_utc":t,"received_at_utc":t,
                        "response_sha256":"a"*64,"response":items}
            try: out=run_audit(p,Path(d)/"out",post_func=fake,sleeper=sleeps.append,delay_seconds=2.5)
            finally: mod.INPUT_SHA256=old
            self.assertEqual(len(calls),112); self.assertEqual(len(sleeps),110)
            self.assertTrue(all(len(x)<=10 for x in calls))
            self.assertEqual(out["summary"]["fallback_attempted"],553)
            self.assertEqual(out["summary"]["fallback_unique_identity_recovered"],553)
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
