import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError

from research.phase165_sec13f_resumable_audit import (
    candidate_urls,
    parse_txt_fixed_width,
    proxy_dates,
    metadata_basis,
    shard_quarters,
    build_audit_rows,
    MANIFEST_FIELDS,
    MATCH_FIELDS,
    download_bytes,
    safe_rate,
    safe_weighted_rate,
)


class Phase165Tests(unittest.TestCase):
    def test_fixed_width_txt_parses_starred_and_unstarred_cusips(self):
        raw = (
            'B38564108*EURONAV NV                   SHS                                    N\n'
            'G0080J104 ACT II GLOBAL ACQUISITION CO  CL A SHS                               E\n'
            'CUSIP NO ISSUER NAME\n'
            'Page 1 of 4\n'
        ).encode()
        _, run_date, run_time, stated_quarter, cusips = parse_txt_fixed_width(raw)
        self.assertIsNone(run_date)
        self.assertIsNone(run_time)
        self.assertIsNone(stated_quarter)
        self.assertEqual(cusips, ['B38564108', 'G0080J104'])

    def test_txt_is_first_candidate_from_2020(self):
        first = next(candidate_urls(2020, 1))
        self.assertEqual(first[1], 'txt')
        self.assertTrue(first[0].endswith('/13flist2020q1.txt'))

    def test_pdf_is_first_candidate_before_2020(self):
        first = next(candidate_urls(2015, 3))
        self.assertEqual(first[1], 'pdf')
        self.assertIn('/divisions/investment/13f/', first[0])

    def test_all_45_quarters_partition_exactly_once(self):
        shards = [shard_quarters(i, 9) for i in range(9)]
        flattened = [quarter for shard in shards for quarter in shard]
        self.assertEqual(len(flattened), 45)
        self.assertEqual(len(set(flattened)), 45)
        self.assertTrue(all(len(shard) == 5 for shard in shards))

    def test_round_robin_shards_balance_legacy_pdfs(self):
        pdf_quarters = {(y, q) for y, q in [
            (2015, 3), (2015, 4), (2016, 1), (2016, 2), (2016, 3), (2016, 4),
            (2017, 1), (2017, 2), (2017, 3), (2017, 4), (2018, 1), (2018, 2),
            (2018, 3), (2018, 4), (2019, 1), (2019, 2), (2019, 3), (2019, 4),
        ]}
        counts = [sum(q in pdf_quarters for q in shard_quarters(i, 9)) for i in range(9)]
        self.assertEqual(counts, [2] * 9)

    def test_proxy_dates_use_last_modified_when_txt_has_no_run_date(self):
        lm = datetime(2020, 4, 6, 12, 0, tzinfo=timezone.utc)
        one, five = proxy_dates(None, lm)
        self.assertEqual(one, '2020-04-08')
        self.assertEqual(five, '2020-04-12')
        self.assertEqual(metadata_basis(None, lm), 'LAST_MODIFIED_ONLY')

    def test_proxy_dates_take_later_timestamp_date(self):
        lm = datetime(2020, 4, 6, 12, 0, tzinfo=timezone.utc)
        one, five = proxy_dates(date(2020, 4, 8), lm)
        self.assertEqual(one, '2020-04-10')
        self.assertEqual(five, '2020-04-14')
        self.assertEqual(metadata_basis(date(2020, 4, 8), lm), 'RUN_DATE_AND_LAST_MODIFIED')

    def test_no_timestamp_means_no_pit_proxy(self):
        self.assertEqual(proxy_dates(None, None), (None, None))
        self.assertEqual(metadata_basis(None, None), 'NO_TIMESTAMP_METADATA')

    def test_404_is_not_retried(self):
        error = HTTPError('https://www.sec.gov/missing', 404, 'Not Found', {}, None)
        with patch('research.phase165_sec13f_resumable_audit.urlopen', side_effect=error) as mocked:
            with self.assertRaises(RuntimeError):
                download_bytes('https://www.sec.gov/missing', retries=3)
        self.assertEqual(mocked.call_count, 1)

    def test_audit_rows_respect_prior_knowledge_and_same_quarter_lookahead(self):
        sample = [{
            'accession': 'A1', 'family': 'SC 13G', 'filing_date': '2025-10-15',
            'acceptance_datetime': '2025-10-15T16:20:00-04:00',
            'sample_weight': '1.0', 'cusip': '037833100',
            'cusip_status': 'UNIQUE_CHECKSUM_VALID',
        }]
        snapshots = [
            {'quarter': '2025Q2', 'conservative_available_from_1d': '2025-07-07',
             'conservative_available_from_5d': '2025-07-11', 'run_date': '2025-07-05',
             'source_sha256': 'a' * 64, 'parse_status': 'PASS'},
            {'quarter': '2025Q3', 'conservative_available_from_1d': '2025-10-07',
             'conservative_available_from_5d': '2025-10-11', 'run_date': '2025-10-05',
             'source_sha256': 'b' * 64, 'parse_status': 'PASS'},
            {'quarter': '2025Q4', 'conservative_available_from_1d': '2025-10-17',
             'conservative_available_from_5d': '2025-10-21', 'run_date': '2025-10-15',
             'source_sha256': 'd' * 64, 'parse_status': 'PASS'},
        ]
        lookup = {('A1', '2025Q2'): True, ('A1', '2025Q3'): False, ('A1', '2025Q4'): True}
        rows = build_audit_rows(sample, snapshots, lookup)
        self.assertEqual(rows[0]['latest_prior_quarter_1d_proxy'], '2025Q3')
        self.assertEqual(rows[0]['latest_prior_quarter_5d_proxy'], '2025Q3')
        self.assertFalse(rows[0]['match_5d_proxy'])
        self.assertTrue(rows[0]['same_quarter_list_available'])
        self.assertTrue(rows[0]['same_quarter_list_match_lookahead_diagnostic'])
        self.assertTrue(rows[0]['lookahead_only_match_vs_5d_proxy'])

    def test_missing_proxy_never_uses_snapshot(self):
        sample = [{
            'accession': 'A2', 'family': 'SC 13D', 'filing_date': '2025-10-15',
            'acceptance_datetime': None, 'sample_weight': '1',
            'cusip': '037833100', 'cusip_status': 'UNIQUE_CHECKSUM_VALID',
        }]
        snapshots = [{
            'quarter': '2025Q3', 'conservative_available_from_1d': None,
            'conservative_available_from_5d': None, 'run_date': None,
            'source_sha256': 'c' * 64, 'parse_status': 'PASS',
        }]
        rows = build_audit_rows(sample, snapshots, {})
        self.assertIsNone(rows[0]['latest_prior_quarter_1d_proxy'])
        self.assertIsNone(rows[0]['latest_prior_quarter_5d_proxy'])
        self.assertIsNone(rows[0]['match_5d_proxy'])

    def test_output_schemas_do_not_contain_raw_list_cusip_or_issuer_name(self):
        self.assertNotIn('cusip', MATCH_FIELDS)
        self.assertNotIn('issuer_name', MANIFEST_FIELDS)
        self.assertNotIn('cusip', MANIFEST_FIELDS)

    def test_missing_match_is_not_treated_as_no_match(self):
        sample = [{
            'accession': 'A3', 'family': 'SC 13G', 'filing_date': '2025-10-15',
            'acceptance_datetime': '2025-10-15T12:00:00-04:00',
            'sample_weight': '1', 'cusip': '037833100',
            'cusip_status': 'UNIQUE_CHECKSUM_VALID',
        }]
        snapshots = [{
            'quarter': '2025Q3', 'conservative_available_from_1d': '2025-10-07',
            'conservative_available_from_5d': '2025-10-11', 'run_date': None,
            'source_sha256': 'e' * 64, 'parse_status': 'PASS',
        }]
        rows = build_audit_rows(sample, snapshots, {})
        self.assertIsNone(rows[0]['match_5d_proxy'])

    def test_weighted_rates_ignore_missing(self):
        rows = [{'sample_weight': 1, 'm': True}, {'sample_weight': 2, 'm': None},
                {'sample_weight': 1, 'm': False}]
        self.assertAlmostEqual(safe_rate(rows, 'm'), 0.5)
        self.assertAlmostEqual(safe_weighted_rate(rows, 'm'), 0.5)


if __name__ == '__main__':
    unittest.main()
