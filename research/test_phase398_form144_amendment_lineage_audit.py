import json
import tempfile
import unittest
from pathlib import Path

from phase398_form144_amendment_lineage_audit import (
    audit,
    canonical_class,
    ticker_map_for_ambiguous_row,
)


def make_row(
    accession,
    form="144",
    filing_date="2024-01-02",
    parent="",
    parent_in_census="False",
    issuer_cik="0001617640",
    filer_cik="0001709817",
    candidates="Z;ZG",
    candidate_ciks="0001617640",
    tranches=None,
):
    if tranches is None:
        tranches = [{
            "security_class": "Common Class C",
            "units_numeric": 100,
            "value_numeric": 1000,
            "outstanding_numeric": 100000,
            "approx_sale_date_iso": "2024-01-02",
            "broker_or_market_maker": "Broker A",
            "exchange": "NASDAQ",
        }]
    return {
        "accession": accession,
        "form": form,
        "filing_date": filing_date,
        "candidate_tickers": candidates,
        "candidate_ciks_in_pair": candidate_ciks,
        "xml_issuer_cik": issuer_cik,
        "xml_filer_cik": filer_cik,
        "issuer_name": "Issuer",
        "seller_name": "Seller",
        "previous_accession_normalized": parent,
        "previous_accession_in_14q_census": parent_in_census,
        "sale_tranche_count": str(len(tranches)),
        "sale_tranches_json": json.dumps(tranches),
    }


class Phase398Tests(unittest.TestCase):
    def test_class_normalization_does_not_guess_generic_common(self):
        self.assertEqual(canonical_class("Common Class C"), "class c")
        self.assertEqual(canonical_class("Class C Capital Stock"), "class c")
        self.assertEqual(canonical_class("Class A Common Stock"), "class a")
        self.assertEqual(canonical_class("Common"), "common")

    def test_zillow_dual_class_tranches_map_separately(self):
        row = make_row(
            "zillow",
            tranches=[
                {"security_class": "Common Class C"},
                {"security_class": "Common Class A"},
                {"security_class": "Common"},
            ],
        )
        mapped = ticker_map_for_ambiguous_row(row)
        self.assertEqual([x["ticker"] for x in mapped], ["Z", "ZG", None])
        self.assertEqual(mapped[2]["status"], "unresolved_generic_class")

    def test_filer_ticker_is_not_used_when_xml_issuer_identifies_asts(self):
        row = make_row(
            "asts",
            issuer_cik="0001780312",
            filer_cik="0001053507",
            candidates="AMT;ASTS",
            candidate_ciks="0001053507;0001780312",
            tranches=[{"security_class": "Class A Common Stock"}],
        )
        mapped = ticker_map_for_ambiguous_row(row)
        self.assertEqual(mapped[0]["ticker"], "ASTS")
        self.assertIn("issuer_side", mapped[0]["status"])

    def test_amendments_are_versioned_and_parent_chain_is_preserved(self):
        base = make_row("base", filing_date="2024-01-02")
        amend1 = make_row(
            "amend1", form="144/A", filing_date="2024-01-03",
            parent="base", parent_in_census="True",
            tranches=[{
                "security_class": "Common Class C",
                "units_numeric": 90, "value_numeric": 900,
                "outstanding_numeric": 100000,
                "approx_sale_date_iso": "2024-01-02",
                "broker_or_market_maker": "Broker A", "exchange": "NASDAQ",
            }],
        )
        amend2 = make_row(
            "amend2", form="144/A", filing_date="2024-01-04",
            parent="amend1", parent_in_census="True",
            tranches=[{
                "security_class": "Common Class C",
                "units_numeric": 80, "value_numeric": 800,
                "outstanding_numeric": 100000,
                "approx_sale_date_iso": "2024-01-02",
                "broker_or_market_maker": "Broker A", "exchange": "NASDAQ",
            }],
        )
        missing = make_row(
            "amend_missing", form="144/A", filing_date="2024-01-05",
            parent="not_in_candidate", parent_in_census="True",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            fields = list(base)
            with path.open("w", newline="", encoding="utf-8") as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows([base, amend1, amend2, missing])
            result = audit(path)

        self.assertEqual(result["matched_parent_count"], 2)
        self.assertEqual(result["matched_parent_form_counts"], {"144": 1, "144/A": 1})
        self.assertEqual(result["amendment_parent_status"]["in_14q_census_not_in_candidate_panel"], 1)
        self.assertEqual(result["amendment_chain_depth_counts"], {"0": 1, "1": 1, "2": 1})
        self.assertEqual(result["amendment_payload_change_counts"]["units_changed"], 2)
        self.assertEqual(result["amendment_payload_change_counts"]["value_changed"], 2)
        self.assertEqual(result["parent_date_inversions"], 0)
        self.assertEqual(result["amendment_chain_cycles"], 0)
        self.assertTrue(result["amendments_must_be_versioned_at_own_filing_date"])
        self.assertFalse(result["amendments_are_independent_sale_events"])


if __name__ == "__main__":
    unittest.main()
