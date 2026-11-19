import unittest
from research.phase497_form4_purchase_row_context_census import parse_form4_purchase_context


def form4(rows: str, owners: int = 1, plan: str = "0", footnotes: str = "") -> bytes:
    owner_xml = "".join(
        "<reportingOwner><reportingOwnerId><rptOwnerCik>0000000002</rptOwnerCik></reportingOwnerId></reportingOwner>"
        for _ in range(owners)
    )
    return f"""<ownershipDocument>
      <issuer><issuerCik>0000000001</issuerCik><issuerTradingSymbol>ABC</issuerTradingSymbol></issuer>
      {owner_xml}
      <aff10b5One><value>{plan}</value></aff10b5One>
      <nonDerivativeTable>{rows}</nonDerivativeTable>
      <footnotes>{footnotes}</footnotes>
    </ownershipDocument>""".encode()


def purchase(code="P", acquired="A", direct="D", price="10.00", shares="100",
             tx_date="2026-11-17", footnote_id="", nature="Direct"):
    ref = f'<footnoteId id="{footnote_id}"/>' if footnote_id else ""
    price_xml = f"<transactionPricePerShare><value>{price}</value></transactionPricePerShare>" if price is not None else ""
    shares_xml = f"<transactionShares><value>{shares}</value></transactionShares>" if shares is not None else ""
    date_xml = f"<transactionDate><value>{tx_date}</value></transactionDate>" if tx_date is not None else ""
    direct_xml = f"<directOrIndirectOwnership><value>{direct}</value></directOrIndirectOwnership>" if direct is not None else ""
    return f"""<nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      {date_xml}
      <transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
      <transactionAmounts>
        {shares_xml}{price_xml}
        <transactionAcquiredDisposedCode><value>{acquired}</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <ownershipNature>{direct_xml}<natureOfOwnership><value>{nature}</value></natureOfOwnership></ownershipNature>
      {ref}
    </nonDerivativeTransaction>"""


class Phase497PurchaseContextTests(unittest.TestCase):
    def test_direct_single_owner_plan_no_with_open_market_footnote(self):
        raw = form4(
            purchase(footnote_id="F1"),
            owners=1,
            plan="0",
            footnotes='<footnote id="F1">Purchased in the open market.</footnote>',
        )
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows"], 1)
        self.assertEqual(result["p_acquired_rows_by_directness"], {"D": 1})
        self.assertEqual(result["p_acquired_rows_by_owner_bucket"], {"single": 1})
        self.assertEqual(result["p_acquired_rows_by_plan_flag"], {"no": 1})
        self.assertEqual(result["high_specificity_manual_review_rows"], 1)
        self.assertEqual(result["footnote_keyword_diagnostic_counts"]["open_market"], 1)

    def test_indirect_private_purchase_is_not_manual_review_screen(self):
        raw = form4(
            purchase(direct="I", footnote_id="F2"),
            owners=1,
            plan="1",
            footnotes='<footnote id="F2">Private purchase through a family trust.</footnote>',
        )
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows_by_directness"], {"I": 1})
        self.assertEqual(result["high_specificity_manual_review_rows"], 0)
        self.assertEqual(result["footnote_keyword_diagnostic_counts"]["private_purchase_or_placement"], 1)
        self.assertEqual(result["footnote_keyword_diagnostic_counts"]["trust"], 1)

    def test_multi_owner_row_is_kept_at_filing_grain_and_not_screened(self):
        raw = form4(purchase(), owners=2, plan="0")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows_by_owner_bucket"], {"multiple": 1})
        self.assertEqual(result["high_specificity_manual_review_rows"], 0)

    def test_missing_price_shares_and_date_are_not_screened(self):
        raw = form4(purchase(price=None, shares=None, tx_date=None, direct=None), owners=1, plan="0")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows_by_directness"], {"unknown": 1})
        self.assertEqual(result["price_field_counts"]["missing"], 1)
        self.assertEqual(result["shares_field_counts"]["missing"], 1)
        self.assertEqual(result["transaction_date_field_counts"]["missing_or_invalid"], 1)
        self.assertEqual(result["high_specificity_manual_review_rows"], 0)

    def test_disposition_and_derivative_rows_are_outside_table_i_scope(self):
        table_i = purchase(code="P", acquired="D")
        raw = form4(table_i, owners=1, plan="0")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows"], 0)

    def test_transaction_after_filing_date_is_flagged_and_not_screened(self):
        raw = form4(purchase(tx_date="2026-11-19"), owners=1, plan="0")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["transaction_date_vs_filing_date"], {"after_filing_date": 1})
        self.assertEqual(result["high_specificity_manual_review_rows"], 0)

    def test_unresolved_footnote_reference_is_counted_not_guessed(self):
        raw = form4(purchase(footnote_id="MISSING"), owners=1, plan="0")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["footnote_reference_counts"]["rows_with_reference"], 1)
        self.assertEqual(result["footnote_reference_counts"]["unresolved_reference_count"], 1)

    def test_unknown_plan_flag_is_not_treated_as_no(self):
        raw = form4(purchase(), owners=1, plan="unexpected")
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertEqual(result["p_acquired_rows_by_plan_flag"], {"unknown": 1})
        self.assertEqual(result["high_specificity_manual_review_rows"], 0)

    def test_private_and_open_market_footnote_flags_can_coexist(self):
        raw = form4(
            purchase(footnote_id="F1"),
            owners=1,
            plan="0",
            footnotes='<footnote id="F1">Open market purchase followed by a private placement.</footnote>',
        )
        result = parse_form4_purchase_context(raw, "2026-11-18")
        flags = result["footnote_keyword_diagnostic_counts"]
        self.assertEqual(flags["open_market"], 1)
        self.assertEqual(flags["private_purchase_or_placement"], 1)

    def test_only_aggregate_counts_are_returned(self):
        raw = form4(
            purchase(footnote_id="F1"),
            owners=1,
            plan="0",
            footnotes='<footnote id="F1">Purchased in the open market.</footnote>',
        )
        result = parse_form4_purchase_context(raw, "2026-11-18")
        self.assertNotIn("rows", result)
        self.assertNotIn("footnote_text", result)
        self.assertNotIn("accession", result)
        self.assertNotIn("transaction_price", result)


if __name__ == "__main__":
    unittest.main()
