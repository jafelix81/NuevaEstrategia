import unittest
from phase237_form144_xbrl_class_shares_pit_audit import (
    SHARES_CONCEPT, PUBLIC_FLOAT_CONCEPT, companyfacts_can_supply_fact,
    validate_share_fact, resolve_asof_shares, denominator_semantics,
)


def fact(value, filed="2026-05-06", end="2026-05-01", accession="A1",
         dimensions=None, acceptance_datetime="2026-05-06T16:00:00Z",
         concept=SHARES_CONCEPT, unit="shares", start=None):
    return {"concept": concept, "unit": unit, "value": value, "filed": filed,
            "end": end, "start": start, "accession": accession,
            "acceptance_datetime": acceptance_datetime,
            "dimensions": dimensions or []}


class Phase237Tests(unittest.TestCase):
    def test_entity_wide_single_class(self):
        r = resolve_asof_shares([fact(1000)], "2026-05-07", "Common", 1)
        self.assertEqual((r["status"], r["shares"]), ("ENTITY_WIDE_SINGLE_CLASS", 1000))

    def test_dimensioned_class_exact_member(self):
        a = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"us-gaap:CommonClassAMember"}]
        b = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"us-gaap:CommonClassBMember"}]
        r = resolve_asof_shares([fact(400, dimensions=a), fact(600, dimensions=b)],
                                "2026-05-07", "us-gaap:CommonClassAMember", 2)
        self.assertEqual((r["status"], r["shares"]), ("CLASS_DIMENSIONED_EXACT_MEMBER", 400))

    def test_companyfacts_excludes_dimensioned_fact(self):
        f = fact(400, dimensions=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"us-gaap:CommonClassAMember"}])
        self.assertFalse(companyfacts_can_supply_fact(f))

    def test_companyfacts_allows_entity_wide_fact(self):
        self.assertTrue(companyfacts_can_supply_fact(fact(1000)))

    def test_public_float_is_wrong_concept(self):
        ok, reason = validate_share_fact(fact(1000, concept=PUBLIC_FLOAT_CONCEPT, unit="USD"))
        self.assertFalse(ok); self.assertEqual(reason, "WRONG_CONCEPT")

    def test_exact_member_required(self):
        a = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"}]
        b = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"B"}]
        r = resolve_asof_shares([fact(1, dimensions=a), fact(2, dimensions=b)], "2026-05-07", None, 2)
        self.assertEqual(r["status"], "NO_RESOLVED_CLASS_FACT")

    def test_one_dimension_member_is_incomplete(self):
        a = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"}]
        r = resolve_asof_shares([fact(100, dimensions=a)], "2026-05-07", "A", 2)
        self.assertEqual(r["status"], "NO_RESOLVED_CLASS_FACT")

    def test_class_count_mismatch(self):
        a = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"}]
        b = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"B"}]
        r = resolve_asof_shares([fact(1, dimensions=a), fact(2, dimensions=b)], "2026-05-07", "A", 3)
        self.assertEqual(r["status"], "NO_RESOLVED_CLASS_FACT")

    def test_entity_wide_requires_proven_single_class(self):
        r = resolve_asof_shares([fact(1000)], "2026-05-07", "Common", 2)
        self.assertEqual(r["status"], "NO_RESOLVED_CLASS_FACT")

    def test_future_filed_fact_excluded(self):
        r = resolve_asof_shares([fact(1000, filed="2026-05-08")], "2026-05-07", "Common", 1)
        self.assertEqual(r["status"], "NO_ELIGIBLE_FACT")

    def test_fact_date_after_filing_rejected(self):
        r = resolve_asof_shares([fact(1000, filed="2026-05-06", end="2026-05-07")], "2026-05-08", "Common", 1)
        self.assertEqual(r["status"], "NO_ELIGIBLE_FACT")

    def test_amendment_after_event_does_not_rewrite_history(self):
        rows = [fact(1000, filed="2026-05-06", accession="ORIG"),
                fact(900, filed="2026-05-09", accession="AMEND")]
        r = resolve_asof_shares(rows, "2026-05-07", "Common", 1)
        self.assertEqual((r["shares"], r["accession"]), (1000, "ORIG"))

    def test_amendment_before_event_updates_asof_state(self):
        rows = [fact(1000, filed="2026-05-06", accession="ORIG"),
                fact(900, filed="2026-05-09", accession="AMEND")]
        r = resolve_asof_shares(rows, "2026-05-10", "Common", 1)
        self.assertEqual((r["shares"], r["accession"]), (900, "AMEND"))

    def test_same_day_conflicting_versions_without_acceptance_is_ambiguous(self):
        rows = [fact(1000, accession="A1", acceptance_datetime=None),
                fact(900, accession="A2", acceptance_datetime=None)]
        r = resolve_asof_shares(rows, "2026-05-07", "Common", 1)
        self.assertEqual(r["status"], "AMBIGUOUS_SAME_DAY_VINTAGE")

    def test_same_day_versions_use_acceptance_order(self):
        rows = [fact(1000, accession="A1", acceptance_datetime="2026-05-06T15:00:00Z"),
                fact(900, accession="A2", acceptance_datetime="2026-05-06T17:00:00Z")]
        r = resolve_asof_shares(rows, "2026-05-07", "Common", 1)
        self.assertEqual((r["shares"], r["accession"]), (900, "A2"))

    def test_duration_context_rejected(self):
        ok, reason = validate_share_fact(fact(1000, start="2026-01-01"))
        self.assertFalse(ok); self.assertEqual(reason, "NOT_INSTANT_CONTEXT")

    def test_non_shares_unit_rejected(self):
        ok, reason = validate_share_fact(fact(1000, unit="USD"))
        self.assertFalse(ok); self.assertEqual(reason, "WRONG_UNIT")

    def test_negative_or_fractional_shares_rejected(self):
        self.assertEqual(validate_share_fact(fact(-1))[1], "INVALID_SHARE_COUNT")
        self.assertEqual(validate_share_fact(fact(1.5))[1], "INVALID_SHARE_COUNT")

    def test_newer_invalid_fact_blocks_stale_fallback(self):
        rows = [fact(1000, filed="2026-05-06", accession="OLD"),
                fact(-1, filed="2026-05-09", accession="NEW")]
        r = resolve_asof_shares(rows, "2026-05-10", "Common", 1)
        self.assertEqual(r["status"], "LATEST_ASOF_FILING_HAS_INVALID_SHARE_FACT")

    def test_undated_share_fact_blocks_asof_resolution(self):
        rows = [fact(1000, filed="2026-05-06", accession="OLD"),
                fact(900, filed=None, accession="UNKNOWN")]
        r = resolve_asof_shares(rows, "2026-05-10", "Common", 1)
        self.assertEqual(r["status"], "UNDATED_SOURCE_FACT_PRESENT")

    def test_same_acceptance_timestamp_conflicting_versions_are_ambiguous(self):
        rows = [fact(1000, accession="A1", acceptance_datetime="2026-05-06T16:00:00Z"),
                fact(900, accession="A2", acceptance_datetime="2026-05-06T16:00:00Z")]
        r = resolve_asof_shares(rows, "2026-05-07", "Common", 1)
        self.assertEqual(r["status"], "AMBIGUOUS_SAME_DAY_VINTAGE")

    def test_multi_class_facts_must_share_same_instant_date(self):
        a = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"}]
        b = [{"axis":"us-gaap:StatementClassOfStockAxis","member":"B"}]
        rows = [fact(400, dimensions=a, end="2026-05-01"),
                fact(600, dimensions=b, end="2026-05-02", accession="A1")]
        r = resolve_asof_shares(rows, "2026-05-07", "A", 2)
        self.assertEqual(r["status"], "NO_RESOLVED_CLASS_FACT")

    def test_denominators_are_not_substitutable(self):
        s = denominator_semantics()
        self.assertIn("not a share count", s["public_float"])
        self.assertIn("not shares outstanding or float", s["adv"])
        self.assertIn("do not label", s["forbidden_inference"])


if __name__ == "__main__":
    unittest.main()
