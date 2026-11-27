from __future__ import annotations

import unittest

from research.phase549_form144_10b5_plan_polarity_audit import (
    classify_remarks_10b5,
    has_plan_termination,
    has_sell_to_cover_tax_context,
    build_summary,
    summarize_form144,
    summarize_form4,
)


class Phase549Form144PlanPolarityTests(unittest.TestCase):
    def test_explicit_negative_sell_to_cover_is_not_a_10b5_plan(self):
        remarks = (
            'The shares are being sold pursuant to automatic "sell-to-cover" '
            "transactions to satisfy tax withholding obligations. The sale is "
            "not being made pursuant to a Rule 10b5-1 trading plan."
        )
        self.assertEqual(classify_remarks_10b5(remarks, "True"), "NEGATIVE_EXPLICIT")
        self.assertTrue(has_sell_to_cover_tax_context(remarks))

    def test_positive_reliance_language(self):
        remarks = (
            "The sales of shares are made in connection with a selling plan "
            "dated 05/18/2026 that is intended to comply with Rule 10b5-1(c)."
        )
        self.assertEqual(classify_remarks_10b5(remarks, "True"), "POSITIVE_EXPLICIT")

    def test_nonstandard_10b51_mention_fails_closed_as_ambiguous(self):
        remarks = "Sales were performed to cover obligations under an established 10b51 plan."
        self.assertEqual(classify_remarks_10b5(remarks, "True"), "AMBIGUOUS_MENTION")

    def test_negated_in_connection_with_phrase_is_not_positive(self):
        remarks = "The shares are not being sold in connection with a Rule 10b5-1 trading plan."
        self.assertEqual(classify_remarks_10b5(remarks), "NEGATIVE_EXPLICIT")

    def test_negated_sold_pursuant_to_phrase_is_not_positive(self):
        remarks = "The sale was not sold pursuant to a Rule 10b5-1 plan."
        self.assertEqual(classify_remarks_10b5(remarks), "NEGATIVE_EXPLICIT")

    def test_negated_plan_identity_is_negative(self):
        remarks = "The proposed sale is not a Rule 10b5-1 plan transaction."
        self.assertEqual(classify_remarks_10b5(remarks), "NEGATIVE_EXPLICIT")

    def test_conflicting_positive_and_negative_clauses_fail_closed(self):
        remarks = (
            "The prior sale was not made pursuant to a Rule 10b5-1 plan; "
            "the current sale is made pursuant to a Rule 10b5-1 plan."
        )
        self.assertEqual(classify_remarks_10b5(remarks), "AMBIGUOUS_MENTION")

    def test_plan_termination_is_separate_from_plan_reliance(self):
        remarks = (
            "The Reporting Person terminated the Plan effective November 18, 2026. "
            "No further sales will be made under the Plan."
        )
        self.assertTrue(has_plan_termination(remarks))

    def test_form144_counts_accessions_not_repeated_detail_rows(self):
        common = {
            "accession": "A1", "form": "144", "issuer_cik": "1", "issuer_name": "Issuer",
            "seller_name": "Seller", "notice_date_iso": "2026-11-19",
            "plan_adoption_dates_json": '["05/18/2026"]',
            "mentions_10b5_1_in_remarks": "False", "remarks": "",
            "proposed_units_numeric": "", "detail_section": "filing_header",
        }
        second = dict(common)
        second.update({"detail_section": "securities_information", "proposed_units_numeric": "100"})
        summary = summarize_form144([common, second])
        self.assertEqual(summary["detail_rows"], 2)
        self.assertEqual(summary["accessions"], 1)
        self.assertEqual(summary["formal_plan_date_accessions"], 1)
        self.assertEqual(summary["plan_date_lag_days"]["n"], 1)


    def test_form144_plan_percentage_is_explicitly_all_accessions(self):
        common = {
            "form": "144", "issuer_cik": "1", "issuer_name": "Issuer",
            "seller_name": "Seller", "notice_date_iso": "2026-11-19",
            "mentions_10b5_1_in_remarks": "False", "remarks": "",
            "proposed_units_numeric": "", "detail_section": "filing_header",
        }
        planned = dict(common, accession="A1", plan_adoption_dates_json='["05/18/2026"]')
        unplanned = dict(common, accession="A2", plan_adoption_dates_json="[]")
        summary = summarize_form144([planned, unplanned])
        self.assertEqual(summary["formal_plan_date_pct_of_all_accessions"], 50.0)
        self.assertEqual(
            summary["formal_plan_date_pct_denominator_scope"],
            "all_accessions_in_structured_ledger_not_point_in_time_filtered",
        )
        self.assertNotIn("formal_plan_date_pct_of_bounded_accessions", summary)

    def test_pit_context_does_not_infer_plan_date_overlap(self):
        row = {
            "accession": "A1", "form": "144", "issuer_cik": "1", "issuer_name": "Issuer",
            "seller_name": "Seller", "notice_date_iso": "2026-11-19",
            "plan_adoption_dates_json": '["05/18/2026"]',
            "mentions_10b5_1_in_remarks": "False", "remarks": "",
            "proposed_units_numeric": "", "detail_section": "filing_header",
        }
        pit = {
            "filing_count": 1,
            "pit": {
                "initial_baseline_no_lower_bound_filing_headers": 1,
                "research_observation_eligible_filing_headers": 0,
                "public_availability_certified_filing_headers": 0,
                "signal_eligible_filing_headers": 0,
            },
        }
        summary = build_summary([row], [{"accession": "F1", "aff10b5one_filing_flag": "yes"}], pit)
        context = summary["pit_eligibility_context"]
        self.assertEqual(context["filing_count"], 1)
        self.assertIsNone(context["formal_plan_date_overlap_with_research_observation_eligible_accessions"])
        self.assertEqual(context["formal_plan_date_overlap_status"], "NOT_COMPUTED_NO_ACCESSION_LEVEL_PIT_JOIN")

    def test_pit_summary_count_mismatch_fails_closed(self):
        row = {
            "accession": "A1", "form": "144", "issuer_cik": "1", "issuer_name": "Issuer",
            "seller_name": "Seller", "notice_date_iso": "2026-11-19",
            "plan_adoption_dates_json": "[]",
            "mentions_10b5_1_in_remarks": "False", "remarks": "",
            "proposed_units_numeric": "", "detail_section": "filing_header",
        }
        pit = {
            "filing_count": 2,
            "pit": {
                "initial_baseline_no_lower_bound_filing_headers": 1,
                "research_observation_eligible_filing_headers": 1,
                "public_availability_certified_filing_headers": 0,
                "signal_eligible_filing_headers": 0,
            },
        }
        with self.assertRaisesRegex(ValueError, "pit_summary_filing_count_mismatch"):
            build_summary([row], [{"accession": "F1", "aff10b5one_filing_flag": "yes"}], pit)

    def test_form4_aff10b5one_is_counted_once_per_accession(self):
        rows = [
            {"accession": "A1", "aff10b5one_filing_flag": "yes"},
            {"accession": "A1", "aff10b5one_filing_flag": "yes"},
            {"accession": "A1", "aff10b5one_filing_flag": "yes"},
            {"accession": "A2", "aff10b5one_filing_flag": "no"},
        ]
        summary = summarize_form4(rows)
        self.assertEqual(summary["detail_rows"], 4)
        self.assertEqual(summary["accessions"], 2)
        self.assertEqual(summary["aff10b5one_by_accession"]["checked"], 1)
        self.assertEqual(summary["aff10b5one_by_accession"]["unchecked"], 1)


if __name__ == "__main__":
    unittest.main()
