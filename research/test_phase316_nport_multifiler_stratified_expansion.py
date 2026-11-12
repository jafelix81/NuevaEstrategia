import unittest
import xml.etree.ElementTree as ET

from research.phase314_nport_amendment_parent_audit import parse_short_positions
from research.phase316_nport_multifiler_stratified_expansion import (
    DEFAULT_PER_STRATUM,
    identifier_metrics,
    p312_signature,
    p314_signature,
    select_expanded_sample,
)


def census_fixture():
    rows = []
    for quarter in ("2020Q1", "2020Q2"):
        for form in ("NPORT-P", "NPORT-P/A"):
            for i in range(8):
                cik = str(100000 + i)
                seq = i + (1 if quarter == "2020Q1" else 20) + (100 if form == "NPORT-P/A" else 0)
                accession = f"{int(cik):010d}-20-{seq:06d}"
                rows.append({
                    "quarter": quarter,
                    "accession": accession,
                    "cik": cik,
                    "company_name": f"Registrant {i}",
                    "form_type": form,
                    "filing_date": "2020-03-01",
                    "filename": f"edgar/data/{cik}/{accession.replace('-', '')}.txt",
                })
    rows.append({
        "quarter": "2020Q1", "accession": "0000999999-20-000001",
        "cik": "999999", "company_name": "Notice", "form_type": "NT NPORT-P",
        "filing_date": "2020-03-01", "filename": "edgar/data/999999/000099999920000001.txt",
    })
    return rows


class Phase316SelectionTests(unittest.TestCase):
    def test_selects_exact_quota_with_distinct_ciks_and_excludes_prior(self):
        rows = census_fixture()
        prior = [{"accession": rows[0]["accession"]}]
        selected = select_expanded_sample(rows, prior, per_stratum=3)
        self.assertEqual(len(selected), 12)
        self.assertNotIn(rows[0]["accession"], {r["accession"] for r in selected})
        self.assertTrue(all(r["form_type"] in {"NPORT-P", "NPORT-P/A"} for r in selected))
        for quarter in ("2020Q1", "2020Q2"):
            for form in ("NPORT-P", "NPORT-P/A"):
                group = [r for r in selected if r["quarter"] == quarter and r["form_type"] == form]
                self.assertEqual(len(group), 3)
                self.assertEqual(len({r["cik"] for r in group}), 3)

    def test_selection_is_deterministic(self):
        rows = census_fixture()
        a = select_expanded_sample(rows, [], per_stratum=2)
        b = select_expanded_sample(list(reversed(rows)), [], per_stratum=2)
        self.assertEqual(
            [(r["quarter"], r["form_type"], r["accession"]) for r in a],
            [(r["quarter"], r["form_type"], r["accession"]) for r in b],
        )

    def test_notices_are_excluded(self):
        selected = select_expanded_sample(census_fixture(), [], per_stratum=2)
        self.assertFalse(any(r["form_type"] == "NT NPORT-P" for r in selected))

    def test_fails_if_distinct_registrant_quota_is_unavailable(self):
        rows = census_fixture()
        for row in rows:
            if row["quarter"] == "2020Q1" and row["form_type"] == "NPORT-P":
                row["cik"] = "0000000001"
        with self.assertRaisesRegex(ValueError, "insufficient_distinct_registrants"):
            select_expanded_sample(rows, [], per_stratum=2)

    def test_duplicate_accession_fails_closed(self):
        rows = census_fixture()
        rows.append(dict(rows[0]))
        with self.assertRaisesRegex(ValueError, "census_accessions_missing_or_duplicated"):
            select_expanded_sample(rows, [], per_stratum=2)

    def test_default_sample_size_is_five(self):
        self.assertEqual(DEFAULT_PER_STRATUM, 5)


class Phase316ReconciliationTests(unittest.TestCase):
    def test_phase312_and_phase314_signatures_align(self):
        old = {
            "cusip": "037833100", "isin": "US0378331005", "ticker": "AAPL",
            "balance": "-10", "currency_value_usd": "-1000.00", "percentage_nav": "-0.1",
        }
        new = {
            "cusip": "037833100", "isin": "US0378331005", "ticker": "AAPL",
            "balance": "-10", "value_usd": "-1000.00", "percentage_nav": "-0.1",
        }
        self.assertEqual(p312_signature(old), p314_signature(new))


    def test_short_parser_normalizes_case_whitespace_and_missing_identifiers(self):
        xml = """<root><invstOrSec>
          <name>Example</name><title>Common Stock</title><cusip>N/A</cusip>
          <balance>-10</balance><units> ns </units><valUSD>-100</valUSD><pctVal>-0.1</pctVal>
          <payoffProfile> short </payoffProfile><assetCat> ec </assetCat>
          <issuerCat> corp </issuerCat><invCountry> us </invCountry>
          <identifiers><isin value="N/A"/><ticker value=" - "/></identifiers>
        </invstOrSec></root>"""
        rows = parse_short_positions(ET.fromstring(xml))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cusip"], "")
        self.assertEqual(rows[0]["isin"], "")
        self.assertEqual(rows[0]["ticker"], "")

    def test_nonfinite_position_values_are_excluded(self):
        xml = """<root><invstOrSec>
          <balance>NaN</balance><units>NS</units><valUSD>-100</valUSD><pctVal>-0.1</pctVal>
          <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat>
          <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
        </invstOrSec></root>"""
        self.assertEqual(parse_short_positions(ET.fromstring(xml)), [])

    def test_identifier_metrics_distinguish_presence_from_validity(self):
        rows = [
            {"cusip": "037833100", "isin": "US0378331005", "ticker": "AAPL"},
            {"cusip": "", "isin": "US5949181045", "ticker": ""},
        ]
        result = identifier_metrics(rows)
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["cusip_present"], 1)
        self.assertEqual(result["isin_present"], 2)
        self.assertEqual(result["ticker_present"], 1)
        self.assertEqual(result["cusip_check_digit_valid"], 1)
        self.assertEqual(result["isin_check_digit_valid"], 2)


if __name__ == "__main__":
    unittest.main()
