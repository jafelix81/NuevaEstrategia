import csv
import gzip
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.phase239_cftc_tff_prospective_capture import (
    INDEX_URL, _classify, _iso_z, _latest_scheduled, _scheduled_after_release,
    capture_current_reports, extract_tff_urls, parse_tff_file,
)


def make_row(report_date="2026-11-03", kind="FutOnly", code="13874+",
             name="S&P 500 Consolidated - CME", subgroup="F20"):
    d = datetime.strptime(report_date, "%Y-%m-%d").date()
    fields = [name, d.strftime("%y%m%d"), report_date, code, "CME", "00", "138", "1000"]
    fields += ["10"] * 16
    fields += ["0"] * 17
    fields += ["10.0"] * 17
    fields += ["1"] * 15
    fields += ["0.0"] * 8
    fields += ["(S&P 500 INDEX X $50.00)", code, "CME", "138", subgroup, kind]
    assert len(fields) == 87
    return fields


def make_file(kind="FutOnly", rows=None):
    rows = rows or [make_row(kind=kind)]
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue().encode("utf-8")


SP500_FUTURES_ONLY = r'''"S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",261103,2026-11-03,13874+,CME ,00,138 , 2013852,  183735,  877061,   75805, 1113850,  183137,  118671,  122566,  489436,   58930,   70969,   62730,     208, 1744733, 1865978,  269119,  147874,   35262,  -11031,   39662,    1577,      97,   -4469,    3700,   19599,  -13409,    4411,    9623,    1065,       0,   27977,   32537,    7286,    2725,  100.0,    9.1,   43.6,    3.8,   55.3,    9.1,    5.9,    6.1,   24.3,    2.9,    3.5,    3.1,    0.0,   86.6,   92.7,   13.4,    7.3,    441,     41,     30,     14,    171,     35,     77,     58,     77,     61,     18,     10,.,    341,    254,     9.7,    29.3,    17.1,    41.9,     9.6,    27.7,    15.7,    40.1,"(S&P 500 INDEX X $50.00)","13874+","CME ","138 ","F20","FutOnly"'''
SP500_COMBINED = r'''"S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",261103,2026-11-03,13874+,CME ,00,138 , 2970924,  176643,  877820,  306662, 1105868,  188300,  153575,  137250,  482496,  677926,   75556,   62465,   20325, 2653804, 2769568,  317120,  201356,  103546,   -9809,   39550,   11505,   -1117,   -1172,    3648,   29642,    2141,   34093,   16184,     201,    5508,   89654,   95475,   13892,    8071,  100.0,    5.9,   29.5,   10.3,   37.2,    6.3,    5.2,    4.6,   16.2,   22.8,    2.5,    2.1,    0.7,   89.3,   93.2,   10.7,    6.8,    491,     42,     31,     43,    171,     40,     91,     67,     80,    104,     39,     15,     35,    426,    338,    15.5,    21.9,    23.3,    34.8,     6.3,    18.8,    10.4,    27.2,"(S&P 500 INDEX X $50.00)","13874+","CME ","138 ","F20","Combined"'''
CANADIAN_FUTURES_ONLY = r'''"CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",261103,2026-11-03,090741,CME ,00,090 ,  348660,  154570,   86816,    1177,  117157,  100704,    4842,   25334,  111636,    2799,   14976,    5272,    1566,  322421,  314812,   26239,   33848,  -12281,  -21503,    6552,     -44,    8741,   -9037,      35,    2910,   -7535,    -493,    -412,     -17,    -281,  -11047,  -10820,   -1234,   -1461,  100.0,   44.3,   24.9,    0.3,   33.6,   28.9,    1.4,    7.3,   32.0,    0.8,    4.3,    1.5,    0.4,   92.5,   90.3,   7.5,    9.7,    143,     10,      8,.,     15,     27,     11,     16,     47,     11,     15,      5,.,     73,     98,    64.1,    30.9,    73.2,    44.9,    64.0,    30.9,    73.1,    44.9,"(CONTRACTS OF CAD 100,000)","090741","CME ","090 ","F10","FutOnly"'''
CANADIAN_COMBINED = r'''"CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",261103,2026-11-03,090741,CME ,00,090 ,  379684,  153527,   86841,    3572,  115350,  100778,    6805,   25141,  110430,   29254,   15894,    5429,    1771,  351315,  344880,   28369,   34804,  -11385,  -22565,   6208,      50,    8173,   -8997,     419,    4121,  -7543,     500,    -368,    -67,    -274,   -9944,   -9704,   -1441,   -1681,  100.0,   40.4,   22.9,    0.9,   30.4,   26.5,    1.8,    6.6,   29.1,    7.7,    4.2,    1.4,    0.5,   92.5,   90.8,   7.5,    9.2,    150,     10,      8,      8,     15,     28,     13,     16,     48,     15,     17,      8,      5,     82,    109,    58.9,    28.4,    69.6,    41.4,    58.7,    28.3,    67.0,    41.3,"(CONTRACTS OF CAD 100,000)","090741","CME ","090 ","F10","Combined"'''


class Phase239Tests(unittest.TestCase):
    def test_valid_futures_only_synthetic(self):
        self.assertEqual(parse_tff_file(make_file(), "futures_only")["field_count"], 87)

    def test_valid_combined_synthetic(self):
        self.assertEqual(parse_tff_file(make_file(kind="Combined"), "futures_options_combined")["stream"], "futures_options_combined")

    def test_official_sp500_futures_only_sample(self):
        p = parse_tff_file(SP500_FUTURES_ONLY.encode(), "futures_only")
        self.assertEqual(p["report_date"], "2026-11-03")
        self.assertEqual(p["equity_index_candidate_names"], ["S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE"])

    def test_official_sp500_combined_sample(self):
        p = parse_tff_file(SP500_COMBINED.encode(), "futures_options_combined")
        self.assertEqual(p["field_count"], 87)
        self.assertEqual(p["equity_index_candidate_names"], ["S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE"])

    def test_official_canadian_futures_only_sample(self):
        self.assertEqual(parse_tff_file(CANADIAN_FUTURES_ONLY.encode(), "futures_only")["trader_count_missing_cells"], 2)

    def test_official_canadian_combined_sample(self):
        self.assertEqual(parse_tff_file(CANADIAN_COMBINED.encode(), "futures_options_combined")["report_date"], "2026-11-03")

    def test_wrong_stream_rejected(self):
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(kind="Combined"), "futures_only")

    def test_wrong_width_rejected(self):
        row = make_row()
        row.pop()
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=[row]), "futures_only")

    def test_asof_report_mismatch_rejected(self):
        row = make_row()
        row[1] = "261104"
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=[row]), "futures_only")

    def test_mixed_report_dates_rejected(self):
        rows = [make_row(), make_row("2026-11-10", code="13874+2")]
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=rows), "futures_only")

    def test_duplicate_contract_key_rejected(self):
        row = make_row()
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=[row, row]), "futures_only")

    def test_zero_open_interest_rejected(self):
        row = make_row()
        row[7] = "0"
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=[row]), "futures_only")

    def test_negative_position_rejected(self):
        row = make_row()
        row[8] = "-1"
        with self.assertRaises(ValueError):
            parse_tff_file(make_file(rows=[row]), "futures_only")

    def test_suppressed_count_not_zero(self):
        row = make_row()
        row[58], row[59] = ".", "0"
        p = parse_tff_file(make_file(rows=[row]), "futures_only")
        self.assertEqual(p["trader_count_missing_cells"], 1)
        self.assertEqual(p["trader_count_zero_cells"], 1)

    def test_extract_current_links(self):
        html = '<a href="/dea/newcot/FinFutWk.txt">Futures Only</a><a href="/dea/newcot/FinComWk.txt">Combined</a>'
        links = extract_tff_urls(html)
        self.assertEqual(links["futures_only"], "https://www.cftc.gov/dea/newcot/FinFutWk.txt")
        self.assertEqual(links["futures_options_combined"], "https://www.cftc.gov/dea/newcot/FinComWk.txt")

    def test_unsafe_host_rejected(self):
        html = '<a href="https://evil.example/FinFutWk.txt">F</a><a href="https://www.cftc.gov/dea/newcot/FinComWk.txt">C</a>'
        with self.assertRaises(ValueError):
            extract_tff_urls(html)

    def test_missing_stream_link_rejected(self):
        with self.assertRaises(ValueError):
            extract_tff_urls('<a href="/dea/newcot/FinFutWk.txt">F</a>')

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            _iso_z(datetime(2026, 11, 6, 20, 45))

    def test_initial_scheduled_capture_is_baseline_only(self):
        now = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
        c = _classify({"report_date": "2026-11-03"}, "a" * 64, None, "schedule", now)
        self.assertEqual(c["event_type"], "INITIAL_BASELINE_STATE_ONLY")
        self.assertTrue(c["state_usable_after_receipt"])
        self.assertFalse(c["event_signal_eligible"])

    def test_new_report_is_pit_from_pipeline_receipt(self):
        now = datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc)
        prior = {"report_date": "2026-11-03", "raw_sha256": "a" * 64}
        c = _classify({"report_date": "2026-11-10"}, "b" * 64, prior, "schedule", now)
        self.assertEqual(c["event_type"], "NEW_REPORT_FIRST_SCHEDULED_OBSERVATION")
        self.assertTrue(c["pit_eligible_from_pipeline_receipt"])
        self.assertEqual(c["report_date_gap_days"], 7)

    def test_revision_is_state_only(self):
        now = datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc)
        prior = {"report_date": "2026-11-10", "raw_sha256": "a" * 64}
        c = _classify({"report_date": "2026-11-10"}, "b" * 64, prior, "schedule", now)
        self.assertEqual(c["event_type"], "NEW_REVISION_FIRST_SCHEDULED_OBSERVATION")
        self.assertTrue(c["state_usable_after_receipt"])
        self.assertFalse(c["event_signal_eligible"])

    def test_unchanged_is_not_new_event(self):
        now = datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc)
        prior = {"report_date": "2026-11-10", "raw_sha256": "a" * 64}
        c = _classify({"report_date": "2026-11-10"}, "a" * 64, prior, "schedule", now)
        self.assertEqual(c["event_type"], "UNCHANGED")
        self.assertFalse(c["pit_eligible_from_pipeline_receipt"])

    def test_manual_capture_never_pit(self):
        now = datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc)
        prior = {"report_date": "2026-11-10", "raw_sha256": "a" * 64}
        c = _classify({"report_date": "2026-11-17"}, "b" * 64, prior, "workflow_dispatch", now)
        self.assertEqual(c["event_type"], "MANUAL_OR_NONQUALIFYING_OBSERVATION")
        self.assertFalse(c["pit_eligible_from_pipeline_receipt"])

    def test_old_report_rollback_is_non_pit(self):
        now = datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc)
        prior = {"report_date": "2026-11-10", "raw_sha256": "a" * 64}
        c = _classify({"report_date": "2026-11-03"}, "b" * 64, prior, "schedule", now)
        self.assertEqual(c["event_type"], "LATE_OR_ROLLBACK_OBSERVATION_NON_PIT")

    def test_poll_after_release_in_est_and_edt(self):
        self.assertTrue(_scheduled_after_release("schedule", datetime(2026, 11, 6, 20, 35, tzinfo=timezone.utc)))
        self.assertTrue(_scheduled_after_release("schedule", datetime(2026, 7, 10, 20, 35, tzinfo=timezone.utc)))

    def test_before_release_and_weekend_are_nonqualifying(self):
        self.assertFalse(_scheduled_after_release("schedule", datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)))
        self.assertFalse(_scheduled_after_release("schedule", datetime(2026, 11, 7, 20, 35, tzinfo=timezone.utc)))

    def test_capture_both_streams_gzip_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            fut, comb = make_file(), make_file(kind="Combined")
            mapping = {
                INDEX_URL: (html, {"Date": "Fri, 06 Nov 2026 20:45:00 GMT"}),
                "https://www.cftc.gov/dea/newcot/FinFutWk.txt": (fut, {"Date": "Fri, 06 Nov 2026 20:45:00 GMT"}),
                "https://www.cftc.gov/dea/newcot/FinComWk.txt": (comb, {"Date": "Fri, 06 Nov 2026 20:45:00 GMT"}),
            }
            now = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            result = capture_current_reports(root=root, event_name="schedule", now=now, fetcher=lambda url: mapping[url], env={"GITHUB_RUN_ID": "1"})
            self.assertEqual(result["stream_count"], 2)
            self.assertEqual(result["new_snapshot_count"], 2)
            self.assertEqual(result["pit_event_count"], 0)
            for stream, raw in [("futures_only", fut), ("futures_options_combined", comb)]:
                raw_files = list((root / "data/cftc_tff/raw" / stream).glob("*.gz"))
                meta_files = list((root / "data/cftc_tff/metadata").glob(f"{stream}__*.json"))
                self.assertEqual(len(raw_files), 1)
                self.assertEqual(gzip.decompress(raw_files[0].read_bytes()), raw)
                meta = json.loads(meta_files[0].read_text())
                self.assertEqual(meta["raw_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(meta["observed_at_utc"], "2026-11-06T20:45:00Z")
                self.assertFalse(meta["historical_first_publication_time_verified"])
                self.assertEqual(meta["http_date_header_recorded_not_used_as_availability"], "Fri, 06 Nov 2026 20:45:00 GMT")

    def test_manual_capture_does_not_advance_scheduled_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            mapping = {
                INDEX_URL: (html, {}),
                "https://www.cftc.gov/dea/newcot/FinFutWk.txt": (make_file(), {}),
                "https://www.cftc.gov/dea/newcot/FinComWk.txt": (make_file(kind="Combined"), {}),
            }
            now = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            fetcher = lambda url: mapping[url]
            capture_current_reports(root=root, event_name="workflow_dispatch", now=now, fetcher=fetcher)
            self.assertIsNone(_latest_scheduled(root, "futures_only"))
            capture_current_reports(root=root, event_name="schedule", now=now, fetcher=fetcher)
            self.assertEqual(_latest_scheduled(root, "futures_only")["event_type"], "INITIAL_BASELINE_STATE_ONLY")

    def test_scheduled_rollback_does_not_replace_last_usable_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            state = {"report_date": "2026-11-03"}

            def fetcher(url):
                if url == INDEX_URL:
                    return html, {}
                stream_label = "FutOnly" if url.endswith("FinFutWk.txt") else "Combined"
                return make_file(kind=stream_label, rows=[
                    make_row(report_date=state["report_date"], kind=stream_label)
                ]), {}

            def capture(at):
                return capture_current_reports(
                    root=root, event_name="schedule", now=at,
                    fetcher=fetcher, env={"GITHUB_RUN_ID": "240"},
                )

            baseline = capture(datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc))
            self.assertEqual(baseline["pit_event_count"], 0)

            state["report_date"] = "2026-11-10"
            new_report = capture(datetime(2026, 11, 13, 20, 45, tzinfo=timezone.utc))
            self.assertEqual(new_report["pit_event_count"], 2)

            state["report_date"] = "2026-11-03"
            rollback = capture(datetime(2026, 11, 16, 20, 45, tzinfo=timezone.utc))
            self.assertEqual(rollback["pit_event_count"], 0)
            self.assertTrue(all(
                x["event_type"] == "LATE_OR_ROLLBACK_OBSERVATION_NON_PIT"
                for x in rollback["captures"]
            ))

            state["report_date"] = "2026-11-10"
            restored = capture(datetime(2026, 11, 17, 20, 45, tzinfo=timezone.utc))
            self.assertEqual(restored["pit_event_count"], 0)
            self.assertEqual(restored["new_snapshot_count"], 0)
            self.assertTrue(all(x["status"] == "UNCHANGED" for x in restored["captures"]))


    def test_manually_observed_new_report_is_not_promoted_by_later_schedule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            state = {"report_date": "2026-11-03"}

            def fetcher(url):
                if url == INDEX_URL:
                    return html, {}
                stream_label = "FutOnly" if url.endswith("FinFutWk.txt") else "Combined"
                return make_file(kind=stream_label, rows=[
                    make_row(report_date=state["report_date"], kind=stream_label)
                ]), {}

            baseline_time = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            capture_current_reports(root=root, event_name="schedule", now=baseline_time,
                                    fetcher=fetcher, env={"GITHUB_RUN_ID": "242"})
            state["report_date"] = "2026-11-10"
            manual = capture_current_reports(
                root=root, event_name="workflow_dispatch",
                now=datetime(2026, 11, 12, 20, 45, tzinfo=timezone.utc),
                fetcher=fetcher, env={"GITHUB_RUN_ID": "242"},
            )
            self.assertEqual(manual["pit_event_count"], 0)
            scheduled = capture_current_reports(
                root=root, event_name="schedule",
                now=datetime(2026, 11, 13, 20, 45, tzinfo=timezone.utc),
                fetcher=fetcher, env={"GITHUB_RUN_ID": "242"},
            )
            self.assertEqual(scheduled["pit_event_count"], 0)
            self.assertEqual(scheduled["new_snapshot_count"], 2)
            self.assertTrue(all(
                x["event_type"] == "PREVIOUSLY_OBSERVED_REPORT_DATE_STATE_ONLY"
                for x in scheduled["captures"]
            ))
            self.assertTrue(all(
                x["state_usable_after_receipt"] and not x["pit_eligible_from_pipeline_receipt"]
                for x in scheduled["captures"]
            ))

    def test_identical_index_snapshot_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            mapping = {
                INDEX_URL: (html, {}),
                "https://www.cftc.gov/dea/newcot/FinFutWk.txt": (make_file(), {}),
                "https://www.cftc.gov/dea/newcot/FinComWk.txt": (make_file(kind="Combined"), {}),
            }
            for hour in (20, 21):
                now = datetime(2026, 11, 6, hour, 45, tzinfo=timezone.utc)
                capture_current_reports(root=root, event_name="schedule", now=now, fetcher=lambda url: mapping[url])
            self.assertEqual(len(list((root / "data/cftc_tff/index_snapshots").glob("*.html.gz"))), 1)



    def test_orphan_raw_snapshot_is_state_only_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            state = {"report_date": "2026-11-03"}

            def fetcher(url):
                if url == INDEX_URL:
                    return html, {}
                kind = "FutOnly" if url.endswith("FinFutWk.txt") else "Combined"
                return make_file(kind=kind, rows=[
                    make_row(report_date=state["report_date"], kind=kind)
                ]), {}

            baseline_time = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            capture_current_reports(root=root, event_name="schedule", now=baseline_time,
                                    fetcher=fetcher)
            state["report_date"] = "2026-11-10"
            for stream, kind in (("futures_only", "FutOnly"),
                                 ("futures_options_combined", "Combined")):
                raw = make_file(kind=kind, rows=[
                    make_row(report_date=state["report_date"], kind=kind)
                ])
                digest = hashlib.sha256(raw).hexdigest()
                raw_path = root / "data/cftc_tff/raw" / stream / f"2026-11-10__{digest[:16]}.txt.gz"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(gzip.compress(raw, mtime=0))  # Simulate a raw commit after metadata failure.

            scheduled = capture_current_reports(
                root=root, event_name="schedule",
                now=datetime(2026, 11, 13, 20, 45, tzinfo=timezone.utc),
                fetcher=fetcher,
            )
            self.assertEqual(scheduled["pit_event_count"], 0)
            self.assertEqual(scheduled["new_snapshot_count"], 2)
            self.assertTrue(all(
                x["event_type"] == "PREVIOUSLY_OBSERVED_REPORT_DATE_STATE_ONLY"
                for x in scheduled["captures"]
            ))
            metadata_files = list((root / "data/cftc_tff/metadata").glob("*2026-11-10*.json"))
            self.assertEqual(len(metadata_files), 2)
            for path in metadata_files:
                metadata = json.loads(path.read_text())
                self.assertTrue(metadata["raw_snapshot_preexisting_without_metadata"])
                self.assertFalse(metadata["pit_eligible_from_pipeline_receipt"])

    def test_corrupt_orphan_raw_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            state = {"report_date": "2026-11-03"}

            def fetcher(url):
                if url == INDEX_URL:
                    return html, {}
                kind = "FutOnly" if url.endswith("FinFutWk.txt") else "Combined"
                return make_file(kind=kind, rows=[
                    make_row(report_date=state["report_date"], kind=kind)
                ]), {}

            baseline_time = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            capture_current_reports(root=root, event_name="schedule", now=baseline_time,
                                    fetcher=fetcher)
            state["report_date"] = "2026-11-10"
            raw = make_file(kind="FutOnly", rows=[
                make_row(report_date=state["report_date"], kind="FutOnly")
            ])
            digest = hashlib.sha256(raw).hexdigest()
            raw_path = root / "data/cftc_tff/raw/futures_only" / f"2026-11-10__{digest[:16]}.txt.gz"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(gzip.compress(b"corrupt bytes", mtime=0))
            with self.assertRaisesRegex(ValueError, "raw snapshot hash mismatch"):
                capture_current_reports(
                    root=root, event_name="schedule",
                    now=datetime(2026, 11, 13, 20, 45, tzinfo=timezone.utc),
                    fetcher=fetcher,
                )

    def test_missing_raw_snapshot_is_repaired_from_existing_receipt_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = b'<a href="/dea/newcot/FinFutWk.txt">F</a><a href="/dea/newcot/FinComWk.txt">C</a>'
            mapping = {
                INDEX_URL: (html, {}),
                "https://www.cftc.gov/dea/newcot/FinFutWk.txt": (make_file(), {}),
                "https://www.cftc.gov/dea/newcot/FinComWk.txt": (make_file(kind="Combined"), {}),
            }
            now = datetime(2026, 11, 6, 20, 45, tzinfo=timezone.utc)
            capture_current_reports(root=root, event_name="schedule", now=now,
                                    fetcher=lambda url: mapping[url])
            metadata = _latest_scheduled(root, "futures_only")
            raw_path = root / metadata["raw_snapshot_path"]
            raw_path.unlink()
            repaired = capture_current_reports(root=root, event_name="schedule", now=now,
                                               fetcher=lambda url: mapping[url])
            self.assertEqual(repaired["new_snapshot_count"], 0)
            self.assertTrue(raw_path.exists())
            self.assertEqual(hashlib.sha256(gzip.decompress(raw_path.read_bytes())).hexdigest(),
                             metadata["raw_sha256"])


if __name__ == "__main__":
    unittest.main()
