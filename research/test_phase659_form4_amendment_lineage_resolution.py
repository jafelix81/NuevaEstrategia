from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research.phase659_form4_amendment_lineage_resolution import audit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "data" / "sec_form4_first_seen"


class Phase659Form4AmendmentLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transactions = DATA / "transaction_details.csv"
        cls.owners = DATA / "reporting_owners.csv"
        cls.sidecar = DATA / "amendment_lineage_resolutions.json"
        cls.result = audit(cls.transactions, cls.owners, cls.sidecar)

    def test_two_original_accessions_are_resolved(self):
        links = self.result["lineage_resolutions"]
        self.assertEqual(len(links), 2)
        self.assertEqual(
            {x["original_accession"] for x in links},
            {"0001104659-26-105049", "0001493152-26-015786"},
        )
        self.assertTrue(all(x["original_accession_resolution"] == "VERIFIED_FROM_SEC_PRIMARY_INDEX_AND_OWNERSHIP_XML" for x in links))

    def test_crescent_is_final_nav_update_not_second_purchase(self):
        item = next(x for x in self.result["lineage_resolutions"] if x["amendment_accession"] == "0001104659-26-130067")
        state = item["transaction_state_comparison"]
        self.assertEqual(state["original_shares"], "208279.91")
        self.assertEqual(state["amended_shares"], "207178.32")
        self.assertEqual(state["original_price_usd"], "26.33")
        self.assertEqual(state["amended_price_usd"], "26.47")
        self.assertEqual(state["both_round_to_reported_combined_investment_usd"], "5484010")
        self.assertEqual(item["lineage_classification"], "FINAL_NAV_VALUE_UPDATE_SAME_UNDERLYING_INVESTMENT")
        self.assertFalse(item["new_economic_event"])

    def test_tron_amendment_only_adds_joint_owner(self):
        item = next(x for x in self.result["lineage_resolutions"] if x["amendment_accession"] == "0001493152-26-053612")
        state = item["transaction_state_comparison"]
        self.assertTrue(state["original_and_amended_rows_identical"])
        self.assertEqual(state["added_reporting_owner_ciks"], ["0002075159"])
        self.assertEqual(state["transaction_codes"], ["A", "M"])
        self.assertFalse(item["new_economic_event"])

    def test_all_amendment_rows_remain_signal_ineligible(self):
        self.assertEqual(self.result["results"]["amendment_transaction_rows_reviewed"], 5)
        self.assertEqual(self.result["results"]["new_economic_events_created"], 0)
        self.assertEqual(self.result["results"]["signal_eligible_rows"], 0)
        self.assertTrue(all(not x["signal_eligible"] for x in self.result["lineage_resolutions"]))

    def test_source_ledgers_are_not_rewritten(self):
        before_transactions = self.transactions.read_bytes()
        before_owners = self.owners.read_bytes()
        self.assertFalse(self.result["results"]["source_ledger_rows_rewritten"])
        self.assertFalse(self.result["results"]["source_ledger_previous_accession_fields_rewritten"])
        self.assertEqual(before_transactions, self.transactions.read_bytes())
        self.assertEqual(before_owners, self.owners.read_bytes())

    def test_audit_writes_reproducible_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "summary.json"
            output.write_text(json.dumps(self.result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["phase"], 659)
            self.assertEqual(parsed["results"]["amendment_lineage_links_resolved"], 2)


if __name__ == "__main__":
    unittest.main()
