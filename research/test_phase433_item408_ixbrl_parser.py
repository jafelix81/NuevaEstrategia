import unittest

from research.phase433_item408_ixbrl_parser import (
    extract_item408_facts,
    parse_acceptance_datetime,
)


FIXTURE = """<!DOCTYPE html>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:ecd="http://xbrl.sec.gov/ecd/2026">
<head></head><body>
<ix:header><ix:resources>
  <xbrli:context id="c_william_a">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0001373715</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2023-07-01</xbrli:startDate><xbrli:endDate>2023-09-30</xbrli:endDate></xbrli:period>
    <xbrli:scenario>
      <xbrldi:explicitMember dimension="ecd:IndividualAxis">now:WilliamRMcDermottMember</xbrldi:explicitMember>
      <xbrldi:explicitMember dimension="ecd:TradingArrAxis">now:WilliamRMcDermottRuleTradingArrangementCommonStockMember</xbrldi:explicitMember>
    </xbrli:scenario>
  </xbrli:context>
  <xbrli:context id="c_william_b">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0001373715</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2023-07-01</xbrli:startDate><xbrli:endDate>2023-09-30</xbrli:endDate></xbrli:period>
    <xbrli:scenario>
      <xbrldi:explicitMember dimension="ecd:IndividualAxis">now:WilliamRMcDermottMember</xbrldi:explicitMember>
      <xbrldi:explicitMember dimension="ecd:TradingArrAxis">now:WilliamRMcDermottRuleTradingArrangementNetSharesMember</xbrldi:explicitMember>
    </xbrli:scenario>
  </xbrli:context>
  <xbrli:context id="c_missing_dimension">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0001373715</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:instant>2023-09-30</xbrli:instant></xbrli:period>
  </xbrli:context>
</ix:resources>
<ix:hidden>
  <ix:nonNumeric name="ecd:TrdArrIndName" contextRef="c_william_a">William R. <b>McDermott</b></ix:nonNumeric>
</ix:hidden>
<ix:nonNumeric name="ecd:TrdArrIndTitle" contextRef="c_william_a">Chief Executive Officer</ix:nonNumeric>
<ix:nonNumeric name="ecd:TrdArrAdoptionDate" contextRef="c_william_a">2023-08-31</ix:nonNumeric>
<ix:nonNumeric name="ecd:Rule10b51ArrAdoptedFlag" contextRef="c_william_a">true</ix:nonNumeric>
<ix:nonFraction name="ecd:TrdArrSecuritiesAggAvailAmt" contextRef="c_william_a" unitRef="shares" scale="3" decimals="0">30.489</ix:nonFraction>
<ix:nonNumeric name="ecd:MtrlTermsOfTrdArrTextBlock" contextRef="c_william_a" continuedAt="cont1">Sale of 30,489 shares <ix:exclude>not part of the fact</ix:exclude></ix:nonNumeric>
<ix:continuation id="cont1">plus net shares from vesting of 9,986 gross shares.</ix:continuation>
<ix:nonNumeric name="ecd:TrdArrIndName" contextRef="c_william_b">William R. McDermott</ix:nonNumeric>
<ix:nonNumeric name="ecd:TrdArrExpirationDate" contextRef="c_william_b">2025-02-18</ix:nonNumeric>
<ix:nonNumeric name="ecd:TrdArrIndTitle" contextRef="c_missing_dimension">Chief Executive Officer</ix:nonNumeric>
<ix:nonNumeric name="ecd:TrdArrDuration" contextRef="context_not_present">unknown context must stay unknown</ix:nonNumeric>
<ix:nonNumeric name="ecd:TrdArrTerminationDate" contextRef="c_william_a" xsi:nil="true"></ix:nonNumeric>
</body></html>
"""


class Phase433AcceptanceTests(unittest.TestCase):
    def test_header_clock_is_eastern_and_dst_aware(self):
        parsed = parse_acceptance_datetime(
            "<ACCEPTANCE-DATETIME>20231025192050\nFILED AS OF DATE: 20231026"
        )
        self.assertEqual(parsed["acceptance_eastern"], "2023-10-25T19:20:50-04:00")
        self.assertEqual(parsed["acceptance_utc"], "2023-10-25T23:20:50Z")
        self.assertEqual(parsed["acceptance_timezone"], "America/New_York")

    def test_winter_offset_is_standard_time(self):
        parsed = parse_acceptance_datetime("<ACCEPTANCE-DATETIME>20231115192050")
        self.assertEqual(parsed["acceptance_eastern"], "2023-11-15T19:20:50-05:00")
        self.assertEqual(parsed["acceptance_utc"], "2023-11-16T00:20:50Z")

    def test_missing_or_conflicting_header_clock_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_acceptance_datetime("FILED AS OF DATE: 20231026")
        with self.assertRaises(ValueError):
            parse_acceptance_datetime(
                "<ACCEPTANCE-DATETIME>20231025192050\n"
                "<ACCEPTANCE-DATETIME>20231025192100"
            )


class Phase433InlineXbrlTests(unittest.TestCase):
    def setUp(self):
        self.result = extract_item408_facts(
            FIXTURE, accession="0001373715-23-000419", issuer_cik="1373715"
        )
        self.facts = self.result["facts"]

    def by_concept(self, concept):
        return [fact for fact in self.facts if fact["concept"] == concept]

    def test_filing_metadata_and_fact_count(self):
        self.assertEqual(self.result["issuer_cik"], "0001373715")
        self.assertEqual(self.result["context_count"], 3)
        self.assertEqual(self.result["item408_fact_count"], 11)

    def test_individual_and_arrangement_dimensions_are_preserved(self):
        name_facts = self.by_concept("TrdArrIndName")
        self.assertEqual(len(name_facts), 2)
        first_dims = name_facts[0]["dimensions"]
        self.assertEqual(
            first_dims["ecd:IndividualAxis"][0]["member"],
            "now:WilliamRMcDermottMember",
        )
        self.assertEqual(
            first_dims["ecd:TradingArrAxis"][0]["member"],
            "now:WilliamRMcDermottRuleTradingArrangementCommonStockMember",
        )
        second_dims = name_facts[1]["dimensions"]
        self.assertEqual(
            second_dims["ecd:TradingArrAxis"][0]["member"],
            "now:WilliamRMcDermottRuleTradingArrangementNetSharesMember",
        )

    def test_hidden_fact_is_included_and_text_order_is_preserved(self):
        name = self.by_concept("TrdArrIndName")[0]
        self.assertTrue(name["is_hidden"])
        self.assertEqual(name["value"], "William R. McDermott")
        text = self.by_concept("MtrlTermsOfTrdArrTextBlock")[0]
        self.assertEqual(
            text["value"],
            "Sale of 30,489 shares plus net shares from vesting of 9,986 gross shares.",
        )
        self.assertNotIn("not part of the fact", text["value"])

    def test_scaled_numeric_value_is_normalized_without_losing_raw_value(self):
        amount = self.by_concept("TrdArrSecuritiesAggAvailAmt")[0]
        self.assertEqual(amount["value"], "30.489")
        self.assertEqual(amount["numeric_value"], "30489.000")

    def test_missing_dimensions_remain_missing_not_imputed(self):
        title = self.by_concept("TrdArrIndTitle")[-1]
        self.assertTrue(title["context_found"])
        self.assertEqual(title["dimensions"], {})
        self.assertIsNone(title["dimensions"].get("ecd:IndividualAxis"))

    def test_unresolved_context_and_nil_fact_are_not_imputed(self):
        unresolved = self.by_concept("TrdArrDuration")[0]
        self.assertFalse(unresolved["context_found"])
        self.assertIsNone(unresolved["dimensions"])
        nil_fact = self.by_concept("TrdArrTerminationDate")[0]
        self.assertTrue(nil_fact["nil"])
        self.assertIsNone(nil_fact["value"])
        self.assertEqual(self.result["extraction_status"], "facts_found")

    def test_ecd_namespace_alias_is_recognized(self):
        alias_fixture = FIXTURE.replace("xmlns:ecd=", "xmlns:execd=")
        alias_fixture = alias_fixture.replace("ecd:", "execd:")
        result = extract_item408_facts(
            alias_fixture, accession="0001373715-23-000419", issuer_cik="1373715"
        )
        self.assertEqual(result["item408_fact_count"], 11)

    def test_zero_tagged_facts_is_unknown_not_no_plans(self):
        result = extract_item408_facts(
            "<html><body><p>No tagged facts in this fixture.</p></body></html>",
            accession="0000000000-00-000000",
            issuer_cik="1",
        )
        self.assertEqual(result["item408_fact_count"], 0)
        self.assertEqual(result["extraction_status"], "no_tagged_item408_facts_unknown")

    def test_fact_context_is_not_collapsed_or_summed(self):
        expiration = self.by_concept("TrdArrExpirationDate")[0]
        self.assertEqual(expiration["context_ref"], "c_william_b")
        self.assertEqual(
            expiration["dimensions"]["ecd:TradingArrAxis"][0]["member"],
            "now:WilliamRMcDermottRuleTradingArrangementNetSharesMember",
        )


if __name__ == "__main__":
    unittest.main()
