import unittest

from research.phase93_13dg_amendment_lineage_and_event_mechanism_audit import (
    candidate_parent_basis,
    classify_event_mechanism,
    normalize_accession,
    normalize_cik,
    normalize_name,
    validate_explicit_predecessor,
)


class Phase93NormalizationTests(unittest.TestCase):
    def base_record(self, accession, acceptance, **overrides):
        row = {
            "accession": accession,
            "family": "13D",
            "form": "SC 13D",
            "subject_cik": "0000000001",
            "filer_cik": "0000000009",
            "acceptance_utc": acceptance,
            "explicit_person_ciks": ["0000000002"],
            "person_names": ["ALPHAHOLDINGSLLC"],
            "cusips": ["123456789"],
        }
        row.update(overrides)
        return row

    def test_normalizers(self):
        self.assertEqual(normalize_cik("123"), "0000000123")
        self.assertEqual(normalize_accession("0000000001-24-000001"), "0000000001-24-000001")
        self.assertEqual(normalize_accession("bad"), "")
        self.assertEqual(normalize_name("Alpha Holdings, LLC"), "ALPHAHOLDINGSLLC")

    def test_business_combination_and_litigation_are_not_called_open_market_buying(self):
        text = "The reporting person received shares in a business combination and later filed a complaint in district court."
        tags, _ = classify_event_mechanism(text, {})
        self.assertIn("business_combination_consideration", tags)
        self.assertIn("litigation_or_dispute", tags)
        self.assertNotIn("open_market_acquisition", tags)

    def test_employee_award_and_reorganization_are_not_market_accumulation(self):
        text = "The reporting person received a stock award followed by a share capital reorganization."
        tags, _ = classify_event_mechanism(text, {})
        self.assertIn("employee_equity_compensation", tags)
        self.assertIn("corporate_reorganization_or_denominator_change", tags)
        self.assertNotIn("open_market_acquisition", tags)

    def test_aggregated_client_holdings_are_separate_from_proprietary_position(self):
        text = "No one person has greater than 5% economic ownership; the relevant clients hold the shares."
        tags, _ = classify_event_mechanism(text, {})
        self.assertIn("aggregated_client_or_adviser_holdings", tags)

    def test_specific_proxy_action_is_activist_but_generic_board_reference_is_not(self):
        activist, _ = classify_event_mechanism("The group intends to nominate directors and solicit proxies.", {})
        generic, _ = classify_event_mechanism("The filing refers to the board of directors.", {})
        self.assertIn("activist_or_control_action", activist)
        self.assertNotIn("activist_or_control_action", generic)
        self.assertIn("governance_reference_only", generic)

    def test_open_market_buy_and_sell_are_distinct(self):
        buy, _ = classify_event_mechanism("The reporting person purchased in the open market.", {})
        sell, _ = classify_event_mechanism("The reporting person sold in the open market.", {})
        self.assertIn("open_market_acquisition", buy)
        self.assertNotIn("open_market_disposition", buy)
        self.assertIn("open_market_disposition", sell)
        self.assertNotIn("open_market_acquisition", sell)

    def test_group_flag_is_preserved(self):
        tags, _ = classify_event_mechanism("Generic filing text.", {"reporting_persons": [{"member_of_group": "Y"}]})
        self.assertIn("group_or_joint_reporting_person", tags)

    def test_no_filer_cik_only_candidate(self):
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00",
                                 explicit_person_ciks=[], person_names=[], cusips=[])
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00",
                                   explicit_person_ciks=[], person_names=[], cusips=[])
        # Same filer CIK is deliberately not an identity key.
        self.assertEqual(candidate_parent_basis(current, prior), "")

    def test_shared_explicit_reporting_person_cik_supports_candidate(self):
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00")
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00")
        self.assertEqual(candidate_parent_basis(current, prior), "shared_explicit_reporting_person_cik")

    def test_name_only_requires_cusip_overlap(self):
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00",
                                 explicit_person_ciks=[])
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00",
                                   explicit_person_ciks=[])
        self.assertEqual(candidate_parent_basis(current, prior), "shared_exact_person_name_and_cusip")
        current["cusips"] = ["999999999"]
        self.assertEqual(candidate_parent_basis(current, prior), "")

    def test_disjoint_cusips_reject_even_when_person_cik_matches(self):
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00")
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00",
                                   cusips=["999999999"])
        self.assertEqual(candidate_parent_basis(current, prior), "")

    def test_candidate_requires_same_subject_and_family(self):
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00")
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00",
                                   subject_cik="0000000003")
        self.assertEqual(candidate_parent_basis(current, prior), "")
        current["subject_cik"] = "0000000001"
        current["family"] = "13G"
        self.assertEqual(candidate_parent_basis(current, prior), "")

    def test_candidate_parent_must_be_strictly_earlier(self):
        prior = self.base_record("0000000001-24-000001", "2024-02-01T15:00:00+00:00")
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00")
        self.assertEqual(candidate_parent_basis(current, prior), "")

    def test_explicit_predecessor_same_subject_family_and_earlier(self):
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00")
        headers = {
            "0000000001-24-000001": {
                "subject_cik": "0000000001",
                "header_form": "SC 13D",
                "header_filing_date": "2024-01-01",
            }
        }
        self.assertEqual(
            validate_explicit_predecessor(
                current, "0000000001-24-000001", headers,
                {"0000000001-24-000001": {}},
            ),
            "explicit_predecessor_structured_sample_consistent",
        )

    def test_explicit_predecessor_subject_mismatch_rejected(self):
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00")
        headers = {
            "0000000001-24-000001": {
                "subject_cik": "0000000003",
                "header_form": "SC 13D",
                "header_filing_date": "2024-01-01",
            }
        }
        self.assertEqual(
            validate_explicit_predecessor(current, "0000000001-24-000001", headers, {}),
            "explicit_predecessor_subject_mismatch",
        )

    def test_explicit_predecessor_outside_sample_is_not_called_invalid(self):
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00")
        self.assertEqual(
            validate_explicit_predecessor(current, "0000000001-24-000001", {}, {}),
            "explicit_predecessor_outside_600_header_sample",
        )

    def test_inferred_first_person_13g_cik_is_not_used(self):
        # Only explicit_person_ciks is passed to candidate matching. A first-person
        # filer-CIK candidate from Phase 91 is intentionally absent here.
        prior = self.base_record("0000000001-24-000001", "2024-01-01T15:00:00+00:00",
                                 explicit_person_ciks=[], person_names=[], cusips=[])
        current = self.base_record("0000000001-24-000002", "2024-02-01T15:00:00+00:00",
                                   explicit_person_ciks=[], person_names=[], cusips=[])
        self.assertEqual(candidate_parent_basis(current, prior), "")


if __name__ == "__main__":
    unittest.main()
