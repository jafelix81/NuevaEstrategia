import unittest
from phase35_global_subject_census_pilot import group_rows, index_urls, select_groups, records

class GlobalSubjectCensusPilotTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"accession":"0000092230-25-000015","master_index_cik":"0001849998","master_index_company_name":"Federated Hermes ETF Trust","form":"SC 13G/A","filing_date":"2025-02-06","filename":"edgar/data/1849998/0000092230-25-000015.txt"},
            {"accession":"0000092230-25-000015","master_index_cik":"0000092230","master_index_company_name":"TRUIST FINANCIAL CORP","form":"SC 13G/A","filing_date":"2025-02-06","filename":"edgar/data/92230/0000092230-25-000015.txt"},
            {"accession":"0000315066-25-000987","master_index_cik":"0002023554","master_index_company_name":"Sandisk Corp","form":"SC 13G","filing_date":"2025-03-07","filename":"edgar/data/2023554/0000315066-25-000987.txt"},
            {"accession":"0000315066-25-000987","master_index_cik":"0000315066","master_index_company_name":"FMR LLC","form":"SC 13G","filing_date":"2025-03-07","filename":"edgar/data/315066/0000315066-25-000987.txt"},
        ]

    def test_sec_fields_data_json_rows_are_mapped(self):
        payload = {"fields":["cik","name","ticker","exchange"],"data":[[92230,"TRUIST FINANCIAL CORP","TFC","NYSE"]]}
        self.assertEqual(records(payload), [{"cik":92230,"name":"TRUIST FINANCIAL CORP","ticker":"TFC","exchange":"NYSE"}])

    def test_grouping_retains_both_ciks_for_accession(self):
        groups = group_rows(self.rows)
        self.assertEqual(len(groups), 2)
        g = next(x for x in groups if x["accession"] == "0000092230-25-000015")
        self.assertEqual(g["master_index_ciks"], ["0000092230", "0001849998"])
        self.assertEqual(g["master_index_row_count"], 2)
        self.assertFalse(g["metadata_conflict"])

    def test_index_urls_use_archive_cik_and_accession_directory(self):
        g = next(x for x in group_rows(self.rows) if x["accession"] == "0000092230-25-000015")
        urls = index_urls(g)
        self.assertEqual(urls[0], "https://www.sec.gov/Archives/edgar/data/92230/000009223025000015/0000092230-25-000015-index.htm")
        self.assertGreaterEqual(len(urls), 4)

    def test_target_filter_matches_either_master_index_cik(self):
        groups = group_rows(self.rows)
        relevant, sample = select_groups(groups, {"0001849998"}, per_form=1)
        self.assertEqual([x["accession"] for x in relevant], ["0000092230-25-000015"])
        self.assertEqual(len(sample), 1)

if __name__ == "__main__":
    unittest.main()
