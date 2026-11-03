import unittest

from phase35_13dg_reporting_person_crosswalk_audit import (
    canonical_name,
    match_filer_to_reporting_person,
)


class ReportingPersonCrosswalkTests(unittest.TestCase):
    def test_entity_legal_suffix_and_leading_the(self):
        self.assertEqual(
            canonical_name("The Vanguard Group", ["IA"]),
            canonical_name("VANGUARD GROUP INC.", ["IA"]),
        )

    def test_individual_allows_surname_first_display(self):
        self.assertEqual(
            canonical_name("Christopher Pavlovski", ["IN"]),
            canonical_name("Pavlovski Christopher", ["IN"]),
        )

    def test_entity_order_is_not_reversed(self):
        self.assertNotEqual(
            canonical_name("T Rowe Price Associates", ["IA"]),
            canonical_name("Price T Rowe Associates", ["IA"]),
        )

    def test_unique_match_emits_candidate_without_mutating_person(self):
        people = [{"name": "The Vanguard Group", "types": ["IA"], "cik": None}]
        result = match_filer_to_reporting_person(
            people, "VANGUARD GROUP INC", "0000102909"
        )
        self.assertEqual(result["status"], "unique_exact_normalized_name_match")
        self.assertEqual(result["candidate_reporting_person_cik"], "0000102909")
        self.assertIsNone(people[0]["cik"])

    def test_ambiguous_duplicate_names_are_not_resolved(self):
        people = [
            {"name": "The Vanguard Group", "types": ["IA"], "cik": None},
            {"name": "Vanguard Group Inc.", "types": ["IA"], "cik": None},
        ]
        result = match_filer_to_reporting_person(
            people, "VANGUARD GROUP INC", "0000102909"
        )
        self.assertEqual(result["status"], "ambiguous_multiple_reporting_person_matches")
        self.assertNotIn("candidate_reporting_person_cik", result)

    def test_nonmatching_name_is_not_fuzzily_resolved(self):
        people = [{"name": "Vanguard Advisers", "types": ["IA"], "cik": None}]
        result = match_filer_to_reporting_person(
            people, "VANGUARD GROUP INC", "0000102909"
        )
        self.assertEqual(result["status"], "no_exact_normalized_name_match")


if __name__ == "__main__":
    unittest.main()
