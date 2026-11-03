import unittest
from phase35_global_subject_census_pilot import build_index_urls

class GlobalSubjectCensusPilotTests(unittest.TestCase):
    def test_master_index_path_builds_accession_directory(self):
        row = {
            "filer_cik": "0001376139",
            "accession": "0001104659-25-001464",
            "filename": "edgar/data/1376139/0001104659-25-001464.txt",
        }
        urls = build_index_urls(row)
        self.assertEqual(
            urls[0],
            "https://www.sec.gov/Archives/edgar/data/1376139/000110465925001464/0001104659-25-001464-index.htm",
        )
        self.assertEqual(
            urls[2],
            "https://www.sec.gov/Archives/edgar/data/1104659/000110465925001464/0001104659-25-001464-index.htm",
        )

if __name__ == "__main__":
    unittest.main()
