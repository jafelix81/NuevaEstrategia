import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from phase211_edgar_acceptance_clock import (
    ET, parse_edgar_acceptance, first_session_open_after, conservative_event_clock
)


class AcceptanceClockTests(unittest.TestCase):
    def test_parse_form144_header(self):
        raw = """<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20260701160720\nACCESSION NUMBER: 0001921094-26-000697\nCONFORMED SUBMISSION TYPE: 144\n"""
        result = parse_edgar_acceptance(raw)
        self.assertEqual(result["form"], "144")
        self.assertEqual(result["accession"], "0001921094-26-000697")
        self.assertEqual(result["accepted_at"], datetime(2026, 7, 1, 16, 7, 20, tzinfo=ET))

    def test_parse_form4_amendment_type(self):
        raw = "<ACCEPTANCE-DATETIME>20260702195602\nCONFORMED SUBMISSION TYPE: 4/A\n"
        self.assertEqual(parse_edgar_acceptance(raw)["form"], "4/A")

    def test_missing_acceptance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ACCEPTANCE-DATETIME"):
            parse_edgar_acceptance("CONFORMED SUBMISSION TYPE: 144")

    def test_intraday_acceptance_uses_next_session_open(self):
        accepted = datetime(2026, 7, 1, 11, 0, tzinfo=ET)
        opens = [datetime(2026, 7, 1, 9, 30, tzinfo=ET), datetime(2026, 7, 2, 9, 30, tzinfo=ET)]
        self.assertEqual(first_session_open_after(accepted, opens), opens[1])

    def test_premarket_acceptance_can_use_same_day_open(self):
        accepted = datetime(2026, 7, 1, 8, 0, tzinfo=ET)
        opens = [datetime(2026, 7, 1, 9, 30, tzinfo=ET), datetime(2026, 7, 2, 9, 30, tzinfo=ET)]
        self.assertEqual(first_session_open_after(accepted, opens), opens[0])

    def test_acceptance_at_open_is_strictly_after(self):
        accepted = datetime(2026, 7, 1, 9, 30, tzinfo=ET)
        opens = [datetime(2026, 7, 1, 9, 30, tzinfo=ET), datetime(2026, 7, 2, 9, 30, tzinfo=ET)]
        self.assertEqual(first_session_open_after(accepted, opens), opens[1])

    def test_naive_times_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            first_session_open_after(datetime(2026, 7, 1, 10, 0), [])

    def test_conservative_clock_output(self):
        raw = "<ACCEPTANCE-DATETIME>20260803160854\nACCESSION NUMBER: 0001921094-26-000789\nCONFORMED SUBMISSION TYPE: 144\n"
        opens = [datetime(2026, 8, 4, 9, 30, tzinfo=ET)]
        result = conservative_event_clock(raw, opens)
        self.assertEqual(result["first_session_open_after_acceptance_et"], "2026-08-04T09:30:00-04:00")


if __name__ == "__main__":
    unittest.main()
