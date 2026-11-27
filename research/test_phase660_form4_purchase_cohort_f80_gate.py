from __future__ import annotations
import csv
import json
import tempfile
import unittest
from pathlib import Path
from research.phase660_form4_purchase_cohort_f80_gate import analyze


class Phase660Form4PurchaseCohortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.transactions = self.root / "transactions.csv"
        self.owners = self.root / "owners.csv"
        self.universe = self.root / "universe.csv"
        headers = [
            "detail_type", "accession", "transaction_code", "issuer_trading_symbol_normalized",
            "issuer_name", "filing_date", "shares_numeric", "reporting_owner_count",
            "aff10b5one_filing_flag", "footnote_flags_json", "research_observation_eligible",
            "signal_eligible", "public_availability_certified", "same_day_intraday_use_authorized",
            "security_identity_verified", "historical_f80_membership_verified",
            "owner_attribution_verified", "transaction_semantics_verified",
            "economic_event_new_trade_authorized",
        ]
        rows = [
            {"detail_type":"transaction_row","accession":"A-UPST","transaction_code":"P",
             "issuer_trading_symbol_normalized":"UPST","issuer_name":"Upstart Holdings, Inc.",
             "filing_date":"2026-11-20","shares_numeric":"50000","reporting_owner_count":"1",
             "aff10b5one_filing_flag":"no","footnote_flags_json":json.dumps([{"trust_mention":True}])},
            {"detail_type":"transaction_row","accession":"A-UPST","transaction_code":"P",
             "issuer_trading_symbol_normalized":"UPST","issuer_name":"Upstart Holdings, Inc.",
             "filing_date":"2026-11-20","shares_numeric":"60000","reporting_owner_count":"1",
             "aff10b5one_filing_flag":"no","footnote_flags_json":"[]"},
            {"detail_type":"transaction_row","accession":"B-TEAM","transaction_code":"P",
             "issuer_trading_symbol_normalized":"TEAM","issuer_name":"Atlassian Corp",
             "filing_date":"2026-11-25","shares_numeric":"13400","reporting_owner_count":"1",
             "aff10b5one_filing_flag":"yes","footnote_flags_json":json.dumps([{"rule_10b5_1_mention":True}])},
            {"detail_type":"transaction_row","accession":"C-OTHER","transaction_code":"P",
             "issuer_trading_symbol_normalized":"OTHER","issuer_name":"Other Inc",
             "filing_date":"2026-11-25","shares_numeric":"100","reporting_owner_count":"2",
             "aff10b5one_filing_flag":"no","footnote_flags_json":"[]"},
            {"detail_type":"transaction_row","accession":"D-SELL","transaction_code":"S",
             "issuer_trading_symbol_normalized":"UPST","issuer_name":"Upstart Holdings, Inc.",
             "filing_date":"2026-11-25","shares_numeric":"1000","reporting_owner_count":"1",
             "aff10b5one_filing_flag":"no","footnote_flags_json":"[]"},
            {"detail_type":"filing_header","accession":"E-HEADER","issuer_trading_symbol_normalized":"UPST"},
        ]
        self._write(self.transactions, headers, rows)
        self._write(self.owners, ["accession"], [{"accession":"A-UPST"},{"accession":"B-TEAM"}])
        self._write(self.universe, ["Ticker"], [{"Ticker":"UPST"},{"Ticker":"TEAM"}])

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def test_exact_symbol_intersection_counts_accessions_not_rows(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        self.assertEqual(result["purchase_code_p"]["transaction_rows"], 4)
        self.assertEqual(result["purchase_code_p"]["accessions"], 3)
        self.assertEqual(result["static_f80_exact_symbol_intersection"]["purchase_accessions"], 2)
        self.assertEqual(result["static_f80_exact_symbol_intersection"]["transaction_rows"], 3)
        self.assertEqual(result["static_f80_exact_symbol_intersection"]["symbols"], ["TEAM", "UPST"])

    def test_non_purchase_rows_and_headers_are_excluded_from_purchase_cohort(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        self.assertEqual(result["live_ledger"]["transaction_rows"], 5)
        self.assertEqual(result["purchase_code_p"]["transaction_rows"], 4)

    def test_missing_owner_sidecar_is_reported_not_dropped(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        self.assertEqual([x["accession"] for x in result["purchase_accessions_missing_owner_sidecar"]], ["C-OTHER"])
        self.assertEqual(result["purchase_code_p"]["owner_sidecar"]["complete_accessions"], 2)

    def test_filing_level_plan_flag_is_not_expanded_to_owner_trade(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        flags = result["purchase_code_p"]["filing_level_10b5_1"]
        self.assertEqual(flags["yes_accessions"], 1)
        self.assertEqual(flags["no_accessions"], 2)
        self.assertEqual(flags["yes_rows"], 1)
        self.assertEqual(result["static_f80_exact_symbol_intersection"]["affirmative_10b5_flagged_symbols"], ["TEAM"])

    def test_multi_owner_accession_stays_at_filing_grain(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        self.assertEqual(result["purchase_code_p"]["multi_owner_accessions"], 1)
        self.assertEqual(result["purchase_code_p"]["accessions"], 3)

    def test_descriptive_audit_never_promotes_a_signal(self) -> None:
        result = analyze(self.transactions, self.owners, self.universe)
        self.assertEqual(result["decision"]["disposition"], "P_CODE_CONTEXT_ONLY_NO_PROMOTION")
        self.assertFalse(result["decision"]["new_signal_promoted"])
        self.assertEqual(result["eligibility_true_counts"]["signal_eligible"], 0)


if __name__ == "__main__":
    unittest.main()
