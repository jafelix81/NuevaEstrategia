import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from research.phase469_finra_regsho_daily_first_seen_capture import (
    build_symbol_observations,
    candidate_trade_dates,
    parse_finra_file,
    run_capture,
)

HEADER = "Date|Symbol|ShortVolume|Short Exempt Volume|TotalVolume|Market"


def file_bytes(day="20261117", rows=None):
    rows = rows if rows is not None else [
        f"{day}|ABC|120.5|2.5|300.0|B",
        f"{day}|XYZ|0|0|100|N",
    ]
    return (HEADER + "\n" + "\n".join(rows) + f"\n{len(rows)}\n").encode()


class TestPhase469Parser(unittest.TestCase):
    def test_valid_fractional_file_and_trailer(self):
        parsed = parse_finra_file(file_bytes(), date(2026, 11, 17))
        self.assertEqual(parsed["row_count"], 2)
        self.assertEqual(parsed["symbol_count"], 2)
        self.assertEqual(parsed["rows"][0]["symbol"], "ABC")
        self.assertEqual(str(parsed["rows"][0]["short_volume"]), "120.5")
        self.assertEqual(parsed["rows"][0]["market"], "B")
        self.assertEqual(len(parsed["raw_sha256"]), 64)

    def test_empty_but_valid_file_is_not_a_signal(self):
        parsed = parse_finra_file(file_bytes(rows=[]), date(2026, 11, 17))
        self.assertEqual(parsed["row_count"], 0)
        self.assertEqual(parsed["symbol_count"], 0)

    def test_missing_trailer_rejected(self):
        raw = (HEADER + "\n20261117|ABC|1|0|2|N\n").encode()
        with self.assertRaisesRegex(ValueError, "trailer_count"):
            parse_finra_file(raw, date(2026, 11, 17))

    def test_trailer_count_mismatch_rejected(self):
        raw = (HEADER + "\n20261117|ABC|1|0|2|N\n2\n").encode()
        with self.assertRaisesRegex(ValueError, "trailer_count_mismatch"):
            parse_finra_file(raw, date(2026, 11, 17))

    def test_same_symbol_across_facilities_is_aggregated(self):
        rows = [
            "20261117|ABC|120.5|2.5|300.0|N",
            "20261117|abc|10.25|0.25|40.0|Q",
            "20261117|XYZ|0|0|100|B",
        ]
        parsed = parse_finra_file(file_bytes(rows=rows), date(2026, 11, 17))
        self.assertEqual(parsed["row_count"], 3)
        self.assertEqual(parsed["facility_row_count"], 3)
        self.assertEqual(parsed["symbol_count"], 2)
        self.assertEqual(parsed["facility_count"], 3)
        abc = next(row for row in parsed["rows"] if row["symbol"] == "ABC")
        self.assertEqual(str(abc["short_volume"]), "130.75")
        self.assertEqual(str(abc["short_exempt_volume"]), "2.75")
        self.assertEqual(str(abc["total_volume"]), "340.0")
        self.assertEqual(abc["market"], "N,Q")

    def test_duplicate_symbol_market_rejected(self):
        rows = [
            "20261117|ABC|1|0|2|N",
            "20261117|abc|1|0|2|n",
        ]
        with self.assertRaisesRegex(ValueError, "duplicate_symbol_market"):
            parse_finra_file(file_bytes(rows=rows), date(2026, 11, 17))

    def test_market_code_must_be_one_letter(self):
        rows = ["20261117|ABC|1|0|2|B,Q,N"]
        with self.assertRaisesRegex(ValueError, "market_code_invalid"):
            parse_finra_file(file_bytes(rows=rows), date(2026, 11, 17))

    def test_market_header_is_required(self):
        raw = b"Date|Symbol|ShortVolume|Short Exempt Volume|TotalVolume\\n20261117|ABC|1|0|2\\n1\\n"
        with self.assertRaisesRegex(ValueError, "required_header_missing:market"):
            parse_finra_file(raw, date(2026, 11, 17))

    def test_short_exempt_must_be_subset_of_short(self):
        with self.assertRaisesRegex(ValueError, "short_exempt_exceeds_short"):
            parse_finra_file(
                file_bytes(rows=["20261117|ABC|1|2|3|N"]),
                date(2026, 11, 17),
            )

    def test_short_volume_must_not_exceed_total(self):
        with self.assertRaisesRegex(ValueError, "short_exceeds_total"):
            parse_finra_file(
                file_bytes(rows=["20261117|ABC|4|0|3|N"]),
                date(2026, 11, 17),
            )

    def test_negative_volume_rejected(self):
        with self.assertRaisesRegex(ValueError, "negative_or_nonfinite"):
            parse_finra_file(
                file_bytes(rows=["20261117|ABC|-1|0|3|N"]),
                date(2026, 11, 17),
            )

    def test_trade_date_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "row_trade_date_mismatch"):
            parse_finra_file(
                file_bytes(rows=["20261116|ABC|1|0|3|N"]),
                date(2026, 11, 17),
            )

    def test_missing_required_header_rejected(self):
        raw = b"Date|Symbol|ShortVolume|TotalVolume\n20261117|ABC|1|2\n1\n"
        with self.assertRaisesRegex(ValueError, "required_header_missing"):
            parse_finra_file(raw, date(2026, 11, 17))

    def test_bad_row_width_rejected(self):
        raw = (HEADER + "\n20261117|ABC|1|0|2\n1\n").encode()
        with self.assertRaisesRegex(ValueError, "row_field_count_mismatch"):
            parse_finra_file(raw, date(2026, 11, 17))

    def test_fractional_decimal_is_finite(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            parse_finra_file(
                file_bytes(rows=["20261117|ABC|NaN|0|2|N"]),
                date(2026, 11, 17),
            )


class TestPhase469Capture(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 22, 30, tzinfo=timezone.utc)

    def fixed_now(self):
        return self.now

    def fetch_current_only(self, payload):
        def fetch(url):
            if "CNMSshvol20261117.txt" in url:
                return 200, payload, ""
            return 403, b"", "not published or non-session"
        return fetch

    def test_candidate_dates_skip_weekends(self):
        dates = candidate_trade_dates(date(2026, 11, 17), 7)
        self.assertEqual(
            [x.isoformat() for x in dates],
            ["2026-11-17", "2026-11-16", "2026-11-13", "2026-11-12", "2026-11-11"],
        )

    def test_same_day_scheduled_first_seen_is_eligible_but_not_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_capture(
                mode="schedule", run_id="1", data_dir=root / "data",
                output_dir=root / "out", lookback_days=1,
                now_fn=self.fixed_now,
                fetcher=self.fetch_current_only(file_bytes()),
            )
            self.assertEqual(summary["research_observation_eligible_count"], 1)
            self.assertEqual(summary["signal_eligible_count"], 0)
            state = json.loads((root / "data" / "state.json").read_text())
            event = state["files"]["2026-11-17"]
            self.assertEqual(event["first_seen_kind"], "first_seen")
            self.assertFalse(summary["raw_market_data_persisted"])

    def test_late_first_seen_requires_prior_scheduled_not_available_and_expands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def unavailable(url):
                return 403, b"", "not available at prior scheduled poll"
            run_capture(
                mode="schedule", run_id="late-a", data_dir=root / "data",
                output_dir=root / "out-a", lookback_days=1,
                now_fn=self.fixed_now, fetcher=unavailable,
            )
            self.now = datetime(2026, 11, 18, 22, 30, tzinfo=timezone.utc)
            payload = file_bytes(
                day="20261117",
                rows=["20261117|ABC|120.5|2.5|300.0|B"],
            )
            def delayed_fetch(url):
                if "CNMSshvol20261117.txt" in url:
                    return 200, payload, ""
                return 403, b"", "not available"
            summary = run_capture(
                mode="schedule", run_id="late-b", data_dir=root / "data",
                output_dir=root / "out-b", lookback_days=2,
                now_fn=self.fixed_now, fetcher=delayed_fetch,
            )
            self.assertEqual(summary["counts"]["late_first_seen"], 1)
            self.assertEqual(summary["research_observation_eligible_count"], 1)
            self.assertEqual(summary["signal_eligible_count"], 0)
            state = json.loads((root / "data" / "state.json").read_text())
            self.assertEqual(
                state["files"]["2026-11-17"]["first_seen_kind"], "late_first_seen"
            )
            with (root / "data" / "events.csv").open(newline="") as handle:
                events = list(csv.DictReader(handle))
            late_event = next(x for x in events if x["observation_kind"] == "late_first_seen")
            self.assertEqual(late_event["research_observation_eligible"], "True")
            self.assertEqual(late_event["signal_eligible"], "False")
            parsed = parse_finra_file(payload, date(2026, 11, 17))
            expanded = build_symbol_observations(parsed, late_event)
            self.assertEqual(len(expanded), 1)
            self.assertEqual(expanded[0]["observation_kind"], "late_first_seen")
            self.assertEqual(expanded[0]["first_seen_utc"], late_event["first_seen_utc"])

    def test_invalid_http_200_records_hash_and_size_without_advancing_state(self):
        bad_payload = file_bytes(rows=[
            "20261117|ABC|1|0|2|N",
            "20261117|ABC|1|0|2|N",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_capture(
                mode="schedule", run_id="invalid-200", data_dir=root / "data",
                output_dir=root / "out", lookback_days=1,
                now_fn=self.fixed_now,
                fetcher=self.fetch_current_only(bad_payload),
            )
            self.assertEqual(summary["counts"]["invalid_files"], 1)
            with (root / "data" / "polls.csv").open(newline="") as handle:
                poll = next(csv.DictReader(handle))
            self.assertEqual(poll["poll_status"], "invalid_file")
            self.assertEqual(poll["error"], "duplicate_symbol_market")
            self.assertEqual(poll["raw_sha256"], hashlib.sha256(bad_payload).hexdigest())
            self.assertEqual(int(poll["response_bytes"]), len(bad_payload))
            state = json.loads((root / "data" / "state.json").read_text())
            self.assertEqual(state["files"], {})

    def test_old_date_first_capture_is_bootstrap_not_eligible(self):
        payload = file_bytes(day="20261116", rows=["20261116|ABC|1|0|2|N"])
        def fetch(url):
            if "CNMSshvol20261116.txt" in url:
                return 200, payload, ""
            return 403, b"", ""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_capture(
                mode="schedule", run_id="2", data_dir=root / "data",
                output_dir=root / "out", lookback_days=2,
                now_fn=self.fixed_now, fetcher=fetch,
            )
            self.assertEqual(summary["research_observation_eligible_count"], 0)
            state = json.loads((root / "data" / "state.json").read_text())
            self.assertEqual(state["files"]["2026-11-16"]["first_seen_kind"], "bootstrap")

    def test_manual_capture_never_persists_or_becomes_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_capture(
                mode="manual", run_id="3", data_dir=root / "data",
                output_dir=root / "out", lookback_days=1,
                now_fn=self.fixed_now,
                fetcher=self.fetch_current_only(file_bytes()),
            )
            self.assertEqual(summary["research_observation_eligible_count"], 0)
            self.assertFalse((root / "data" / "state.json").exists())

    def test_revision_preserves_original_first_seen_and_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = file_bytes()
            run_capture(
                mode="schedule", run_id="4a", data_dir=root / "data",
                output_dir=root / "out1", lookback_days=1,
                now_fn=self.fixed_now, fetcher=self.fetch_current_only(first),
            )
            original = json.loads((root / "data" / "state.json").read_text())["files"]["2026-11-17"]["first_seen_utc"]
            self.now = datetime(2026, 11, 17, 23, 30, tzinfo=timezone.utc)
            revised = file_bytes(rows=[
                "20261117|ABC|121.5|2.5|301.0|B",
                "20261117|XYZ|0|0|100|N",
            ])
            summary = run_capture(
                mode="schedule", run_id="4b", data_dir=root / "data",
                output_dir=root / "out2", lookback_days=1,
                now_fn=self.fixed_now, fetcher=self.fetch_current_only(revised),
            )
            state = json.loads((root / "data" / "state.json").read_text())
            self.assertEqual(state["files"]["2026-11-17"]["first_seen_utc"], original)
            self.assertEqual(summary["counts"]["revisions"], 1)
            with (root / "data" / "events.csv").open(newline="") as handle:
                events = list(csv.DictReader(handle))
            self.assertEqual(events[-1]["observation_kind"], "revision")
            self.assertEqual(events[-1]["research_observation_eligible"], "False")

    def test_unchanged_hash_does_not_create_new_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = file_bytes()
            for run_id in ("5a", "5b"):
                run_capture(
                    mode="schedule", run_id=run_id, data_dir=root / "data",
                    output_dir=root / run_id, lookback_days=1,
                    now_fn=self.fixed_now, fetcher=self.fetch_current_only(payload),
                )
            with (root / "data" / "events.csv").open(newline="") as handle:
                events = list(csv.DictReader(handle))
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["observation_kind"], "first_seen")

    def test_symbol_expansion_requires_matching_hash_and_eligible_event(self):
        parsed = parse_finra_file(file_bytes(), date(2026, 11, 17))
        event = {
            "trade_date": "2026-11-17", "observation_kind": "first_seen",
            "research_observation_eligible": True,
            "poll_start_utc": "2026-11-17T22:30:00Z",
            "first_seen_utc": "2026-11-17T22:30:01Z",
            "poll_end_utc": "2026-11-17T22:30:01Z",
            "raw_sha256": parsed["raw_sha256"],
        }
        expanded = build_symbol_observations(parsed, event)
        self.assertEqual([x["symbol"] for x in expanded], ["ABC", "XYZ"])
        self.assertTrue(all(x["observation_kind"] == "first_seen" for x in expanded))
        self.assertNotIn("short_volume", expanded[0])
        with self.assertRaisesRegex(ValueError, "hash_does_not_match"):
            build_symbol_observations(parsed, {**event, "raw_sha256": "0" * 64})

    def test_manual_or_bootstrap_event_never_expands_to_labeler_input(self):
        parsed = parse_finra_file(file_bytes(), date(2026, 11, 17))
        event = {
            "trade_date": "2026-11-17", "observation_kind": "bootstrap",
            "research_observation_eligible": False,
            "raw_sha256": parsed["raw_sha256"],
        }
        self.assertEqual(build_symbol_observations(parsed, event), [])


if __name__ == "__main__":
    unittest.main()
