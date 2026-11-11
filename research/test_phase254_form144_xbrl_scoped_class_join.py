import unittest

from research.phase253_form144_xbrl_registered_security_crosswalk_audit import validate_context
from research.phase254_form144_xbrl_scoped_class_join import (
    normalize_cik,
    select_prior_vintage_scoped,
    resolve_form144_class_scoped,
)


def filing(cik="000123", accession="A", filed="2025-01-02", form="10-K", accepted=None):
    row = {"issuer_cik": cik, "accession": accession, "filing_date": filed, "form": form}
    if accepted is not None:
        row["acceptance_datetime"] = accepted
    return row


def context(
    accession="A", cik="000123", filed="2025-01-02", title="Class A common stock",
    symbol="ABC", class_axis="us-gaap:StatementClassOfStockAxis",
    class_member="us-gaap:CommonClassAMember", listing_axis="dei:EntityListingsExchangeAxis",
    listing_member="exch:XNYS", exchange="NYSE",
):
    if exchange is None:
        facts = {"dei:Security12gTitle": [title]}
    else:
        facts = {"dei:Security12bTitle": [title], "dei:SecurityExchangeName": [exchange]}
    if symbol is not None:
        facts["dei:TradingSymbol"] = [symbol]
    dims = []
    if class_axis and class_member:
        dims.append({"axis": class_axis, "member": class_member})
    if listing_axis and listing_member:
        dims.append({"axis": listing_axis, "member": listing_member})
    normalized = validate_context({
        "context_id": "ctx-1", "facts": facts, "dimensions": dims,
    })
    normalized.update({
        "issuer_cik": cik, "accession": accession, "filing_date": filed,
    })
    return normalized


class Phase254Tests(unittest.TestCase):
    def selected(self, filings=None, event_date="2025-02-01", cik="000123"):
        return select_prior_vintage_scoped(
            filings if filings is not None else [filing()],
            cik, event_date,
        )

    def test_normalize_cik(self):
        self.assertEqual(normalize_cik("00000123"), "123")

    def test_issuer_scope_selects_expected_cik(self):
        result = self.selected([
            filing("000999", "OTHER", "2025-01-30"),
            filing("000123", "RIGHT", "2025-01-10"),
        ])
        self.assertEqual(result["accession"], "RIGHT")

    def test_no_filings_for_issuer(self):
        result = self.selected([filing("000999", "OTHER", "2025-01-10")])
        self.assertEqual(result["status"], "NO_FILINGS_FOR_ISSUER")

    def test_same_day_and_future_are_excluded(self):
        result = self.selected([
            filing("000123", "SAME", "2025-02-01"),
            filing("000123", "FUTURE", "2025-02-02"),
        ])
        self.assertEqual(result["status"], "NO_STRICTLY_PRIOR_VINTAGE")

    def test_latest_strictly_prior_selected(self):
        result = self.selected([
            filing("000123", "OLD", "2025-01-01"),
            filing("000123", "NEW", "2025-01-31"),
        ])
        self.assertEqual(result["accession"], "NEW")

    def test_same_day_tie_without_acceptance_is_unknown(self):
        result = self.selected([
            filing("000123", "A", "2025-01-31"),
            filing("000123", "B", "2025-01-31"),
        ])
        self.assertEqual(result["status"], "SAME_DAY_VINTAGE_TIE_UNKNOWN")

    def test_same_day_tie_uses_timezone_aware_acceptance(self):
        result = self.selected([
            filing("000123", "A", "2025-01-31", accepted="2025-01-31T09:00:00-05:00"),
            filing("000123", "B", "2025-01-31", accepted="2025-01-31T16:00:00-05:00"),
        ])
        self.assertEqual(result["accession"], "B")
        self.assertTrue(result["acceptance_order_used"])

    def test_naive_acceptance_does_not_resolve_tie(self):
        result = self.selected([
            filing("000123", "A", "2025-01-31", accepted="2025-01-31T09:00:00"),
            filing("000123", "B", "2025-01-31", accepted="2025-01-31T16:00:00"),
        ])
        self.assertEqual(result["status"], "SAME_DAY_VINTAGE_TIE_UNKNOWN")

    def test_later_amendment_not_backdated(self):
        result = self.selected([
            filing("000123", "ORIGINAL", "2025-01-01", "10-K"),
            filing("000123", "AMENDMENT", "2025-02-10", "10-K/A"),
        ], event_date="2025-02-05")
        self.assertEqual(result["accession"], "ORIGINAL")

    def test_prior_amendment_is_selected_as_its_own_vintage(self):
        result = self.selected([
            filing("000123", "ORIGINAL", "2025-01-01", "10-K"),
            filing("000123", "AMENDMENT", "2025-01-20", "10-K/A"),
        ], event_date="2025-02-05")
        self.assertEqual(result["accession"], "AMENDMENT")
        self.assertEqual(result["form"], "10-K/A")

    def test_missing_expected_cik_fails_closed(self):
        self.assertEqual(
            select_prior_vintage_scoped([filing()], "", "2025-02-01")["status"],
            "MISSING_EXPECTED_ISSUER_CIK",
        )

    def test_context_accession_mismatch_rejected(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock", [context(accession="OTHER")], vintage,
        )
        self.assertEqual(result["status"], "CONTEXT_ACCESSION_MISMATCH")

    def test_context_issuer_mismatch_rejected(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock", [context(cik="000999")], vintage,
        )
        self.assertEqual(result["status"], "CONTEXT_ISSUER_SCOPE_MISMATCH")

    def test_context_filing_date_mismatch_rejected(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock", [context(filed="2025-01-03")], vintage,
        )
        self.assertEqual(result["status"], "CONTEXT_FILING_DATE_MISMATCH")

    def test_missing_context_accession_rejected(self):
        vintage = self.selected()
        ctx = context()
        ctx["accession"] = ""
        result = resolve_form144_class_scoped("Class A common stock", [ctx], vintage)
        self.assertEqual(result["status"], "CONTEXT_ACCESSION_MISSING")

    def test_listing_axis_alone_is_not_class_identity(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock",
            [context(class_axis=None, class_member=None)],
            vintage,
        )
        self.assertEqual(result["status"], "CLASS_SCOPE_UNKNOWN")

    def test_exact_class_and_listing_resolve(self):
        result = resolve_form144_class_scoped(
            "Class A common stock", [context()], self.selected(),
        )
        self.assertEqual(result["status"], "UNIQUE_CLASS_LISTING")
        self.assertEqual(result["symbol"], "ABC")

    def test_multiple_listings_same_class(self):
        vintage = self.selected()
        first = context(listing_member="exch:XNYS", exchange="NYSE")
        second = context(listing_member="exch:XCHI", exchange="NYSE Texas")
        result = resolve_form144_class_scoped(
            "Class A common stock", [first, second], vintage,
        )
        self.assertEqual(result["status"], "MULTIPLE_LISTINGS_SAME_CLASS")

    def test_multiple_class_members_are_ambiguous(self):
        vintage = self.selected()
        first = context(class_member="us-gaap:CommonClassAMember")
        second = context(class_member="us-gaap:CommonClassBMember")
        result = resolve_form144_class_scoped(
            "Class A common stock", [first, second], vintage,
        )
        self.assertEqual(result["status"], "AMBIGUOUS_CLASS_OR_SYMBOL")

    def test_unknown_symbol_is_not_admitted(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock", [context(symbol=None)], vintage,
        )
        self.assertEqual(result["status"], "TRADING_SYMBOL_UNKNOWN")

    def test_single_class_without_listing_is_not_a_unique_listing(self):
        result = resolve_form144_class_scoped(
            "Class A common stock",
            [context(exchange=None, listing_axis=None, listing_member=None)],
            self.selected(),
        )
        self.assertEqual(result["status"], "UNIQUE_CLASS_SYMBOL_LISTING_UNKNOWN")

    def test_mixed_known_and_unknown_listing_scope_is_not_multiple_listings(self):
        result = resolve_form144_class_scoped(
            "Class A common stock",
            [
                context(listing_member="exch:XNYS", exchange="NYSE"),
                context(exchange=None, listing_axis=None, listing_member=None),
            ],
            self.selected(),
        )
        self.assertEqual(result["status"], "LISTING_SCOPE_UNKNOWN")

    def test_no_fuzzy_title_join(self):
        result = resolve_form144_class_scoped(
            "Class A", [context()], self.selected(),
        )
        self.assertEqual(result["status"], "NO_EXACT_CLASS_TITLE_MATCH")

    def test_mixed_accessions_rejected_before_join(self):
        vintage = self.selected()
        result = resolve_form144_class_scoped(
            "Class A common stock",
            [context(), context(accession="OTHER")],
            vintage,
        )
        self.assertEqual(result["status"], "CONTEXT_ACCESSION_MISMATCH")


if __name__ == "__main__":
    unittest.main()
