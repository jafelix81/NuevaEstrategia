import unittest

from research.phase89_phase84_offline_replay import expected_mandatory_xml_accessions


class Phase89OfflineReplayTests(unittest.TestCase):
    def test_actual_tender_offer_header_is_excluded_from_xml_denominator(self):
        sample = [{
            "accession": "0001104659-26-057293",
            "form": "SC 13D/A",
            "filing_date": "2026-05-07",
        }]
        parsed = {
            "0001104659-26-057293": {
                "header_form": "SC TO-T/A",
                "header_filing_date": "2026-05-07",
            }
        }
        self.assertEqual(expected_mandatory_xml_accessions(sample, parsed), set())

    def test_unretrieved_schedule13_filing_remains_in_expected_denominator(self):
        sample = [{
            "accession": "0000000001-25-000001",
            "form": "SC 13G/A",
            "filing_date": "2025-01-10",
        }]
        self.assertEqual(
            expected_mandatory_xml_accessions(sample, {}),
            {"0000000001-25-000001"},
        )

    def test_actual_schedule13_header_controls_over_index_form(self):
        sample = [{
            "accession": "0000000001-25-000002",
            "form": "SC 13D",
            "filing_date": "2025-01-10",
        }]
        parsed = {
            "0000000001-25-000002": {
                "header_form": "SC 13G",
                "header_filing_date": "2025-01-10",
            }
        }
        self.assertEqual(
            expected_mandatory_xml_accessions(sample, parsed),
            {"0000000001-25-000002"},
        )


if __name__ == "__main__":
    unittest.main()
