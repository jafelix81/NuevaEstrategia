import unittest
from research.phase223_form144_units_outstanding_integrity_audit import audit_records


def row(accession, issuer, filing, security_class, units, outstanding, value=1000):
    return {
        "accession": accession,
        "xml_issuer_cik": issuer,
        "filing_date": filing,
        "sale_tranches_json": [{
            "security_class": security_class,
            "units_numeric": units,
            "outstanding_numeric": outstanding,
            "value_numeric": value,
        }],
    }


class Phase223UnitsOutstandingTests(unittest.TestCase):
    def test_zero_outstanding_is_counted_not_used_as_denominator(self):
        r = audit_records([row("a", "123", "2026-01-02", "Common", 100, 0)])
        self.assertEqual(r["zero_values"]["units_outstanding"], 1)
        self.assertEqual(r["raw_sale_to_outstanding_ratio"]["infinite_rows_positive_sale_zero_outstanding"], 1)
        self.assertFalse(r["decision"]["units_outstanding_admitted_as_universal_denominator"])

    def test_sale_over_outstanding_is_flagged(self):
        r = audit_records([row("a", "123", "2026-01-02", "Common", 120, 100)])
        self.assertEqual(r["raw_sale_to_outstanding_ratio"]["ratio_gt_100pct_rows"], 1)

    def test_same_issuer_class_date_conflict_is_detected(self):
        rows = [
            row("a", "123", "2026-01-02", "Common", 10, 1000000),
            row("b", "123", "2026-01-02", " common ", 20, 1),
        ]
        r = audit_records(rows)["same_issuer_class_filing_date_reconciliation"]
        self.assertEqual(r["groups_with_two_or_more_accessions"], 1)
        self.assertEqual(r["groups_with_conflicting_outstanding_values"], 1)
        self.assertEqual(r["tranches_in_conflict_groups"], 2)
        self.assertEqual(r["unique_accessions_in_conflict_groups"], 2)

    def test_identical_values_are_not_conflicts(self):
        rows = [
            row("a", "123", "2026-01-02", "Common", 10, 1000000),
            row("b", "123", "2026-01-02", "Common", 20, 1000000),
        ]
        r = audit_records(rows)["same_issuer_class_filing_date_reconciliation"]
        self.assertEqual(r["groups_with_conflicting_outstanding_values"], 0)

    def test_different_class_is_not_collapsed(self):
        rows = [
            row("a", "123", "2026-01-02", "Class A", 10, 1000000),
            row("b", "123", "2026-01-02", "Class B", 20, 100),
        ]
        r = audit_records(rows)["same_issuer_class_filing_date_reconciliation"]
        self.assertEqual(r["groups_with_two_or_more_accessions"], 0)
        self.assertEqual(r["groups_with_conflicting_outstanding_values"], 0)

    def test_different_issuer_is_not_collapsed(self):
        rows = [
            row("a", "123", "2026-01-02", "Common", 10, 1000000),
            row("b", "124", "2026-01-02", "Common", 20, 100),
        ]
        r = audit_records(rows)["same_issuer_class_filing_date_reconciliation"]
        self.assertEqual(r["groups_with_two_or_more_accessions"], 0)

    def test_missing_numeric_values_are_counted(self):
        rows = [{
            "accession": "a", "xml_issuer_cik": "123", "filing_date": "2026-01-02",
            "sale_tranches_json": [{"security_class":"Common","units_numeric":None,
                "outstanding_numeric":None,"value_numeric":None}]
        }]
        r = audit_records(rows)
        self.assertEqual(r["missing_numeric"], {"units":1,"value":1,"outstanding":1})

    def test_empty_tranche_json_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_records([{"accession":"a","sale_tranches_json":"[]"}])

    def test_source_field_preserved_but_not_admitted(self):
        r = audit_records([row("a", "123", "2026-01-02", "Common", 10, 1000000)])
        self.assertTrue(r["decision"]["raw_source_field_preserved"])
        self.assertFalse(r["decision"]["sale_to_outstanding_ratio_admitted_as_feature"])
        self.assertTrue(r["decision"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
