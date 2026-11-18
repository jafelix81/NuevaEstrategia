import unittest

from research.phase468_finra_flow_pit_labeler import build_executable_labels


def ts(day, hour, minute=0):
    return f"2026-11-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def make_sessions(days):
    return [
        {
            "session_date": f"2026-11-{d:02d}",
            "open_utc": ts(d, 14, 30),
            "close_utc": ts(d, 21, 0),
        }
        for d in days
    ]


def make_bars(days, basis="total_return_adjusted_ohlc"):
    return [
        {
            "symbol": "ABC",
            "session_date": f"2026-11-{d:02d}",
            "open": 100.0 + i,
            "close": 101.0 + i,
            "price_basis": basis,
        }
        for i, d in enumerate(days)
    ]


def make_event(**overrides):
    event = {
        "symbol": "abc",
        "trade_date": "2026-11-16",
        "poll_start_utc": "2026-11-16T21:01:00Z",
        "first_seen_utc": "2026-11-16T21:05:00Z",
        "poll_end_utc": "2026-11-16T21:10:00Z",
        "http_status": 200,
        "raw_sha256": "a" * 64,
        "row_count": 400,
        "schema_version": "CNMSshvol-v1",
        "observation_kind": "first_seen",
    }
    event.update(overrides)
    return event


class TestPhase468ExecutableLabels(unittest.TestCase):
    def setUp(self):
        self.days = [16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 30]
        self.sessions = make_sessions(self.days)
        self.bars = make_bars(self.days)

    def run_one(self, event=None, bars=None, horizons=(2, 5)):
        return build_executable_labels(
            [event or make_event()],
            self.bars if bars is None else bars,
            self.sessions,
            horizons=horizons,
        )

    def test_post_close_flow_enters_next_session_open_not_signal_close(self):
        result = self.run_one()
        row = result["labels"][0]
        self.assertEqual(row["entry_date"], "2026-11-17")
        self.assertEqual(row["entry_open"], 101.0)
        self.assertNotEqual(row["entry_open"], 100.0)
        self.assertFalse(result["summary"]["signal_date_close_used"])
        self.assertEqual(row["exit_date_2"], "2026-11-18")
        self.assertAlmostEqual(row["fwd_2"], 103.0 / 101.0 - 1.0)

    def test_first_seen_exactly_at_open_skips_that_open(self):
        event = make_event(
            poll_start_utc="2026-11-17T14:29:00Z",
            first_seen_utc="2026-11-17T14:30:00Z",
            poll_end_utc="2026-11-17T14:31:00Z",
        )
        result = self.run_one(event)
        self.assertEqual(result["labels"][0]["entry_date"], "2026-11-18")

    def test_first_seen_after_open_uses_following_session(self):
        event = make_event(
            poll_start_utc="2026-11-17T14:30:00Z",
            first_seen_utc="2026-11-17T14:31:00Z",
            poll_end_utc="2026-11-17T14:32:00Z",
        )
        result = self.run_one(event)
        self.assertEqual(result["labels"][0]["entry_date"], "2026-11-18")

    def test_late_first_seen_enters_only_after_actual_receipt_and_records_age(self):
        event = make_event(
            trade_date="2026-11-16",
            poll_start_utc="2026-11-17T22:01:00Z",
            first_seen_utc="2026-11-17T22:05:00Z",
            poll_end_utc="2026-11-17T22:10:00Z",
            observation_kind="late_first_seen",
        )
        result = self.run_one(event, horizons=(2,))
        row = result["labels"][0]
        self.assertEqual(row["entry_date"], "2026-11-18")
        self.assertEqual(row["signal_age_sessions"], 2)
        self.assertEqual(row["observation_kind"], "late_first_seen")
        self.assertEqual(result["summary"]["late_first_seen_events"], 1)

    def test_missing_first_seen_rejected(self):
        result = self.run_one(make_event(first_seen_utc=None))
        self.assertEqual(result["rejections"][0]["reason"], "first_seen_utc_missing")

    def test_naive_first_seen_rejected(self):
        result = self.run_one(make_event(first_seen_utc="2026-11-16T21:05:00"))
        self.assertEqual(
            result["rejections"][0]["reason"], "first_seen_utc_timezone_missing"
        )

    def test_first_seen_before_poll_start_rejected(self):
        result = self.run_one(
            make_event(
                poll_start_utc="2026-11-16T21:10:00Z",
                first_seen_utc="2026-11-16T21:05:00Z",
            )
        )
        self.assertEqual(
            result["rejections"][0]["reason"], "first_seen_precedes_poll_start"
        )

    def test_first_seen_not_post_close_rejected(self):
        result = self.run_one(
            make_event(
                poll_start_utc="2026-11-16T20:59:00Z",
                first_seen_utc="2026-11-16T20:59:59Z",
                poll_end_utc="2026-11-16T21:01:00Z",
            )
        )
        self.assertEqual(
            result["rejections"][0]["reason"], "first_seen_not_strictly_post_close"
        )

    def test_http_non_200_rejected(self):
        result = self.run_one(make_event(http_status=403))
        self.assertEqual(result["rejections"][0]["reason"], "http_status_not_200")

    def test_bad_hash_rejected(self):
        result = self.run_one(make_event(raw_sha256="bad"))
        self.assertEqual(result["rejections"][0]["reason"], "raw_sha256_invalid")

    def test_zero_rows_rejected(self):
        result = self.run_one(make_event(row_count=0))
        self.assertEqual(result["rejections"][0]["reason"], "row_count_not_positive")

    def test_revision_not_first_seen_rejected(self):
        result = self.run_one(make_event(observation_kind="revision"))
        self.assertEqual(
            result["rejections"][0]["reason"], "observation_not_first_seen"
        )

    def test_duplicate_symbol_trade_date_rejected(self):
        result = build_executable_labels(
            [make_event(), make_event(raw_sha256="b" * 64)],
            self.bars,
            self.sessions,
            horizons=(2,),
        )
        self.assertEqual(result["summary"]["eligible_events"], 0)
        self.assertEqual(len(result["rejections"]), 2)
        self.assertTrue(
            all(
                x["reason"] == "duplicate_first_seen_symbol_trade_date"
                for x in result["rejections"]
            )
        )

    def test_missing_entry_bar_rejected(self):
        bars = [x for x in self.bars if x["session_date"] != "2026-11-17"]
        result = self.run_one(bars=bars)
        self.assertEqual(result["rejections"][0]["reason"], "entry_price_missing")

    def test_incomplete_intermediate_path_rejects_horizon(self):
        bars = [x for x in self.bars if x["session_date"] != "2026-11-20"]
        result = self.run_one(bars=bars, horizons=(2, 5))
        row = result["labels"][0]
        self.assertEqual(row["horizon_status"]["2"], "eligible")
        self.assertEqual(row["horizon_status"]["5"], "incomplete_price_path")
        self.assertEqual(result["summary"]["eligible_events"], 1)

    def test_insufficient_tail_keeps_shorter_horizon_only(self):
        sessions = make_sessions([16, 17, 18])
        bars = make_bars([16, 17, 18])
        result = build_executable_labels(
            [make_event()], bars, sessions, horizons=(2, 5)
        )
        row = result["labels"][0]
        self.assertEqual(row["horizon_status"]["2"], "eligible")
        self.assertEqual(
            row["horizon_status"]["5"], "insufficient_future_sessions"
        )

    def test_unsupported_price_basis_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported_price_basis"):
            self.run_one(bars=make_bars(self.days, basis="raw_ohlc"))

    def test_duplicate_session_date_is_configuration_error(self):
        with self.assertRaisesRegex(ValueError, "duplicate_session_date"):
            build_executable_labels(
                [make_event()],
                self.bars,
                self.sessions + [self.sessions[0]],
                horizons=(2,),
            )

    def test_duplicate_price_bar_is_configuration_error(self):
        with self.assertRaisesRegex(ValueError, "duplicate_price_bar"):
            self.run_one(bars=self.bars + [self.bars[0]])

    def test_no_future_session_rejected(self):
        sessions = make_sessions([16])
        bars = make_bars([16])
        result = build_executable_labels(
            [make_event()], bars, sessions, horizons=(1,)
        )
        self.assertEqual(
            result["rejections"][0]["reason"], "no_future_executable_session"
        )

    def test_trade_date_must_be_calendar_session(self):
        result = self.run_one(make_event(trade_date="2026-11-15"))
        self.assertEqual(
            result["rejections"][0]["reason"], "trade_date_not_in_session_calendar"
        )

    def test_horizons_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "horizons_must_be_positive"):
            self.run_one(horizons=(0, 5))

    def test_exit_timestamp_is_after_first_seen(self):
        result = self.run_one()
        row = result["labels"][0]
        self.assertGreater(row["exit_close_utc_2"], row["first_seen_utc"])

    def test_timezone_offsets_normalize_to_utc(self):
        event = make_event(
            poll_start_utc="2026-11-16T16:01:00-05:00",
            first_seen_utc="2026-11-16T16:05:00-05:00",
            poll_end_utc="2026-11-16T16:10:00-05:00",
        )
        result = self.run_one(event)
        self.assertEqual(
            result["labels"][0]["first_seen_utc"], "2026-11-16T21:05:00Z"
        )

    def test_missing_poll_end_rejected(self):
        event = make_event()
        event.pop("poll_end_utc")
        result = self.run_one(event)
        self.assertEqual(result["rejections"][0]["reason"], "poll_end_utc_missing")

    def test_first_seen_after_poll_end_rejected(self):
        result = self.run_one(make_event(poll_end_utc="2026-11-16T21:04:59Z"))
        self.assertEqual(
            result["rejections"][0]["reason"], "first_seen_follows_poll_end"
        )

    def test_poll_end_before_poll_start_rejected(self):
        result = self.run_one(
            make_event(
                poll_start_utc="2026-11-16T21:06:00Z",
                first_seen_utc="2026-11-16T21:07:00Z",
                poll_end_utc="2026-11-16T21:05:00Z",
            )
        )
        self.assertEqual(
            result["rejections"][0]["reason"], "poll_end_precedes_poll_start"
        )

    def test_fractional_row_count_rejected(self):
        result = self.run_one(make_event(row_count=10.5))
        self.assertEqual(result["rejections"][0]["reason"], "row_count_invalid")

    def test_fractional_http_status_rejected(self):
        result = self.run_one(make_event(http_status=200.5))
        self.assertEqual(result["rejections"][0]["reason"], "http_status_not_200")

    def test_overlapping_session_clock_is_configuration_error(self):
        sessions = make_sessions(self.days)
        sessions[0]["close_utc"] = "2026-11-17T21:00:00Z"
        sessions[1]["open_utc"] = "2026-11-17T20:59:00Z"
        with self.assertRaisesRegex(ValueError, "session_clocks_overlap"):
            build_executable_labels(
                [make_event()], self.bars, sessions, horizons=(2,)
            )

    def test_summary_marks_historical_unknown_timestamps_not_admitted(self):
        result = self.run_one()
        self.assertFalse(
            result["summary"]["historical_rows_without_first_seen_admitted"]
        )


if __name__ == "__main__":
    unittest.main()
