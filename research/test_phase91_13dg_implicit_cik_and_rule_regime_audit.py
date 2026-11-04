import unittest
from datetime import date

from research.phase91_13dg_implicit_cik_and_rule_regime_audit import (
    classify_13g_person_identity, expected_timing_regime, is_structured_xml_filing,
    lag_stats, normalize_name, parse_sample_stratum,
)


class Phase91IdentityTimingTests(unittest.TestCase):
    def test_13d_rule_regime_boundaries(self):
        self.assertEqual(expected_timing_regime("13D", "2024-02-04"), "13d_legacy_deadline")
        self.assertEqual(expected_timing_regime("13D", "2024-02-05"), "13d_revised_deadline_pre_xml")
        self.assertEqual(expected_timing_regime("13D", "2024-12-17"), "13d_revised_deadline_pre_xml")
        self.assertEqual(expected_timing_regime("13D", "2024-12-18"), "13d_mandatory_xml")

    def test_13g_rule_regime_boundaries(self):
        self.assertEqual(expected_timing_regime("13G", "2024-09-29"), "13g_legacy_deadline")
        self.assertEqual(expected_timing_regime("13G", "2024-09-30"), "13g_revised_deadline_pre_xml")
        self.assertEqual(expected_timing_regime("13G", "2024-12-17"), "13g_revised_deadline_pre_xml")
        self.assertEqual(expected_timing_regime("13G", "2024-12-18"), "13g_mandatory_xml")

    def test_unknown_dates_fail_closed(self):
        self.assertEqual(expected_timing_regime("13G", "not-a-date"), "unknown_date")
        self.assertEqual(expected_timing_regime("OTHER", "2025-01-01"), "unknown_family")

    def test_sample_stratum_parses_all_dimensions(self):
        parsed = parse_sample_stratum("13G|True|13g_mandatory_xml|ambiguous")
        self.assertEqual(parsed, {
            "family": "13G", "is_amendment": True,
            "timing_regime": "13g_mandatory_xml", "candidate_class": "ambiguous",
        })
        self.assertIsNone(parse_sample_stratum("bad")["is_amendment"])

    def test_legacy_13dg_html_txt_is_not_counted_as_xml_parse_failure(self):
        self.assertFalse(is_structured_xml_filing({"xml_present": False}, "13D"))
        self.assertFalse(is_structured_xml_filing({"xml_present": False}, "13G"))
        self.assertFalse(is_structured_xml_filing({"xml_present": True}, ""))
        self.assertTrue(is_structured_xml_filing({"xml_present": True}, "13D"))

    def test_first_13g_person_filer_cik_is_only_a_candidate_on_exact_name_match(self):
        person = {"name": "Rubric Capital Management, L.P.", "person_cik": "",
                  "person_no_cik_flag": ""}
        match = classify_13g_person_identity(person, 0, "0001687509", "Rubric Capital Management LP")
        self.assertEqual(match["identity_status"], "first_person_filer_cik_candidate_name_match")
        self.assertEqual(match["candidate_person_cik"], "0001687509")
        self.assertFalse(match["identity_resolved"])

        mismatch = classify_13g_person_identity(person, 0, "0001687509", "Unrelated Filing Agent")
        self.assertEqual(mismatch["identity_status"], "first_person_filer_cik_unverified")
        self.assertEqual(mismatch["candidate_person_cik"], "")

    def test_additional_13g_person_never_inherits_filer_cik(self):
        person = {"name": "Second Person", "person_cik": "", "person_no_cik_flag": ""}
        result = classify_13g_person_identity(person, 1, "0001687509", "Rubric Capital Management LP")
        self.assertEqual(result["identity_status"], "additional_person_cik_unresolved")
        self.assertEqual(result["candidate_person_cik"], "")
        self.assertFalse(result["identity_resolved"])

    def test_explicit_and_declared_no_cik_take_precedence(self):
        explicit = classify_13g_person_identity(
            {"name": "Investor", "person_cik": "0000001234", "person_no_cik_flag": "N"},
            1, "0000009999", "Agent",
        )
        self.assertEqual(explicit["candidate_person_cik"], "0000001234")
        self.assertTrue(explicit["identity_resolved"])
        no_cik = classify_13g_person_identity(
            {"name": "Individual", "person_cik": "", "person_no_cik_flag": "Y"},
            1, "0000009999", "Agent",
        )
        self.assertEqual(no_cik["identity_status"], "declared_no_reporting_person_cik")
        self.assertTrue(no_cik["identity_resolved"])

    def test_name_normalization_is_conservative_but_punctuation_insensitive(self):
        self.assertEqual(normalize_name("Rubric Capital Management, L.P."), "RUBRICCAPITALMANAGEMENTLP")
        self.assertNotEqual(normalize_name("Rubric Capital"), normalize_name("Rubric Capital Management"))

    def test_lag_summary_is_descriptive_and_robust(self):
        stats = lag_stats([1, 3, 5, 9, None])
        self.assertEqual(stats["n"], 4)
        self.assertEqual(stats["median"], 4)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 9)
        self.assertEqual(stats["pct_le_5"], .75)
        self.assertEqual(lag_stats([])["n"], 0)


if __name__ == "__main__":
    unittest.main()
