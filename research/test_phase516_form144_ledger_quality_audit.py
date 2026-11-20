import unittest

from research.phase516_form144_ledger_quality_audit import summarize_rows


def header(accession, *, plan="[]", remarks_10b5="False", nothing="Y",
           notice="2026-11-19", run="run-1", lower="2026-11-19T20:00:00Z",
           upper="2026-11-19T22:00:00Z", remarks="", form="144"):
    return {
        "accession": accession, "form": form, "issuer_cik": "0000000001",
        "issuer_name": "Example Corp", "detail_section": "filing_header",
        "parse_status": "parsed", "research_observation_eligible": "True",
        "public_availability_certified": "False", "signal_eligible": "False",
        "source_xml_hash_matches_event": "True", "proposed_units_numeric": "",
        "aggregate_market_value_numeric": "", "units_outstanding_numeric": "",
        "approx_sale_date_iso": "", "approx_sale_date_relation_to_notice": "",
        "notice_date_iso": notice, "plan_adoption_dates_json": plan,
        "mentions_10b5_1_in_remarks": remarks_10b5,
        "nothing_to_report_flag": nothing, "prior_sale_amount_numeric": "",
        "first_seen_interval_lower_bound_utc": lower,
        "first_seen_interval_upper_bound_utc": upper,
        "first_seen_poll_run_id": run, "submission_acceptance_utc": "2026-11-19T21:00:00Z",
        "remarks": remarks, "previous_accession": "",
    }


def proposed(accession, *, relation="same_as_notice_date", form="144", previous=""):
    return {
        "accession": accession, "form": form, "issuer_cik": "0000000001",
        "issuer_name": "Example Corp", "detail_section": "securities_information",
        "parse_status": "parsed", "research_observation_eligible": "True",
        "public_availability_certified": "False", "signal_eligible": "False",
        "source_xml_hash_matches_event": "True", "proposed_units_numeric": "100",
        "aggregate_market_value_numeric": "1000", "units_outstanding_numeric": "10000",
        "approx_sale_date_iso": "2026-11-18" if relation == "before_notice_date" else "2026-11-19",
        "approx_sale_date_relation_to_notice": relation, "notice_date_iso": "2026-11-19",
        "plan_adoption_dates_json": "[]", "mentions_10b5_1_in_remarks": "False",
        "nothing_to_report_flag": "N", "prior_sale_amount_numeric": "",
        "first_seen_interval_lower_bound_utc": "2026-11-19T20:00:00Z",
        "first_seen_interval_upper_bound_utc": "2026-11-19T22:00:00Z",
        "first_seen_poll_run_id": "run-1", "submission_acceptance_utc": "2026-11-19T21:00:00Z",
        "remarks": "", "previous_accession": previous,
    }


def prior(accession):
    row = proposed(accession)
    row.update({
        "detail_section": "securities_sold_in_past_3_months",
        "prior_sale_amount_numeric": "10",
        "proposed_units_numeric": "", "aggregate_market_value_numeric": "",
        "units_outstanding_numeric": "", "approx_sale_date_iso": "",
        "approx_sale_date_relation_to_notice": "",
    })
    return row


class Phase516Tests(unittest.TestCase):
    def test_formal_plan_date_is_not_inferred_from_remarks(self):
        a = header("A", plan='["08/10/2026"]', remarks_10b5="False", nothing="N")
        a["notice_date_iso"] = "2026-11-19"
        b = header("B", plan="[]", remarks_10b5="True", nothing="Y")
        result = summarize_rows([a, proposed("A"), prior("A"), b])
        plan = result["rule_10b5_1"]
        self.assertEqual(plan["filings_with_formal_plan_adoption_date"], 1)
        self.assertEqual(plan["filings_with_10b5_1_remarks_mention"], 1)
        self.assertEqual(plan["formal_date_and_remarks_overlap"], 0)
        self.assertEqual(plan["formal_date_only"], 1)
        self.assertEqual(plan["remarks_only"], 1)
        self.assertEqual(plan["days_from_formal_plan_date_to_notice"]["median"], 101)

    def test_nothing_to_report_flag_reconciles_to_prior_sales_rows(self):
        a = header("A", nothing="N")
        b = header("B", nothing="Y")
        result = summarize_rows([a, proposed("A"), prior("A"), b])
        self.assertEqual(result["prior_sales"]["filings_with_prior_sales"], 1)
        self.assertEqual(result["prior_sales"]["nothing_to_report_flag_mismatches"], [])
        self.assertEqual(result["detail_section_counts"]["securities_sold_in_past_3_months"], 1)

    def test_past_sale_date_is_flagged_and_amendment_termination_is_not_new_supply(self):
        remarks = "Amendment terminates the Plan. No further sales will be made under the Plan."
        a = header("A", nothing="Y", form="144/A", remarks=remarks)
        p = proposed("A", relation="before_notice_date", form="144/A", previous="prior-accession")
        result = summarize_rows([a, p])
        case = result["proposed_sale"]["past_notice_date_cases"][0]
        self.assertTrue(case["amendment_form"])
        self.assertTrue(case["previous_accession_present"])
        self.assertTrue(case["remarks_explicitly_state_termination_or_no_further_sales"])
        self.assertEqual(result["proposed_sale"]["rows"], 1)
        self.assertEqual(result["pit"]["signal_eligible_filing_headers"], 0)

    def test_first_seen_intervals_use_timezone_aware_bounds(self):
        a = header("A")
        result = summarize_rows([a])
        interval = result["pit"]["first_seen_interval_hours_by_poll_run"]["run-1"]
        self.assertEqual(interval["median"], 2.0)
        self.assertEqual(result["pit"]["malformed_or_missing_first_seen_intervals"], 0)

    def test_no_signal_is_admitted_by_the_audit(self):
        a = header("A")
        result = summarize_rows([a])
        self.assertTrue(result["controls"]["no_signal_admitted"])
        self.assertTrue(result["controls"]["no_public_availability_claim"])
        self.assertEqual(result["disposition"], "DESCRIPTIVE_LEDGER_QUALITY_PASS_WITH_SEMANTIC_REVIEW_QUEUE")


if __name__ == "__main__":
    unittest.main()
