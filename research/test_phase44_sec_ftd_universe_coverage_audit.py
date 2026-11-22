from __future__ import annotations

import csv
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research import phase44_sec_ftd_universe_coverage_audit as audit


def make_zip(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("cnsfails_test.txt", text)
    return buffer.getvalue()


class Phase44CredentialAndParserTests(unittest.TestCase):
    def test_missing_or_unmonitored_user_agent_fails_closed(self):
        with patch.dict(os.environ, {"SEC_USER_AGENT": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "SEC_USER_AGENT is required"):
                audit.require_user_agent()
        with self.assertRaisesRegex(RuntimeError, "monitored contact email"):
            audit.require_user_agent("NuevaEstrategia research contact")

    def test_user_agent_is_passed_to_sec_request_without_logging(self):
        class Response(io.BytesIO):
            pass

        captured = {}

        def fake_urlopen(request, timeout):
            captured["header"] = request.get_header("User-agent")
            captured["timeout"] = timeout
            return Response(b"zip-bytes")

        with patch.object(audit.urllib.request, "urlopen", side_effect=fake_urlopen):
            payload = audit.download(
                "https://www.sec.gov/example.zip",
                "NuevaEstrategia research monitored@example.org",
            )
        self.assertEqual(payload, b"zip-bytes")
        self.assertEqual(captured["header"], "NuevaEstrategia research monitored@example.org")
        self.assertEqual(captured["timeout"], 60)

    def test_parse_zip_preserves_symbol_and_cusip_only_identity(self):
        payload = make_zip(
            "SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE\n"
            "20180102|123456789|AAA|100|Issuer A|10.00\n"
            "20180102|987654321|AAA|200|Issuer A second class|10.00\n"
            "20180102|222222222||50|Missing ticker|10.00\n"
            "TOTAL|||||\n"
        )
        parsed = audit.parse_zip(payload)
        self.assertEqual(parsed["economic_rows"], 3)
        self.assertEqual(parsed["symbols"]["AAA"], ["123456789", "987654321"])
        self.assertEqual(parsed["cusip_only_rows"], 2)
        self.assertEqual(parsed["cusip_only_unique_cusips"], ["222222222"])
        self.assertEqual(parsed["identity_missing_rows"], 0)
        self.assertEqual(parsed["exact_duplicate_rows"], 0)

    def test_parse_zip_rejects_unexpected_schema(self):
        payload = make_zip("DATE|CUSIP|SYMBOL|QTY|DESC|PRICE\n")
        with self.assertRaisesRegex(ValueError, "unexpected FTD schema"):
            audit.parse_zip(payload)

    def test_universe_requires_exactly_335_unique_tickers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "universe.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Ticker"])
                writer.writerows([[f"T{i:03d}"] for i in range(335)])
            self.assertEqual(len(audit.load_universe(path)), 335)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Ticker"])
                writer.writerows([["DUP"] for _ in range(335)])
            with self.assertRaisesRegex(ValueError, "335 unique frozen symbols"):
                audit.load_universe(path)


if __name__ == "__main__":
    unittest.main()
