import tempfile
import unittest
from datetime import date
from pathlib import Path

from research.phase166_sec13f_cross_format_pit_bridge import (
    build_pdf_pit_manifest,
    compare_sample_matches,
    load_shard_dir,
    parse_pdf_last_modified,
    summarize_concordance_by_format,
    unique_cusip_coverage,
)


class Phase166Tests(unittest.TestCase):
    def test_pdf_run_date_overrides_txt_archive_migration_timestamp(self):
        pdf = {'2020Q1': {
            'quarter': '2020Q1', 'run_date': '2020-04-21',
            'http_last_modified_utc': '2020-04-21T10:00:00+00:00',
            'source_sha256': 'a' * 64, 'parse_status': 'PASS',
        }}
        content = {'2020Q1': {
            'quarter': '2020Q1', 'format': 'txt',
            'source_sha256': 'b' * 64, 'parsed_rows': '8880',
            'unique_cusips': '8880', 'checksum_valid_unique_cusips': '8880',
            'http_last_modified_utc': '2026-09-04T00:00:00+00:00',
        }}
        row = build_pdf_pit_manifest(pdf, content)[0]
        self.assertEqual(row['conservative_available_from_5d_pdf_proxy'], '2020-04-27')
        self.assertEqual(row['content_format'], 'txt')
        self.assertEqual(row['pdf_run_date'], '2020-04-21')

    def test_pdf_iso_last_modified_is_parsed(self):
        value = parse_pdf_last_modified('2020-04-21T10:00:00+00:00')
        self.assertEqual(value.date().isoformat(), '2020-04-21')

    def test_pdf_epoch_last_modified_is_ignored(self):
        pdf = {'2024Q3': {
            'quarter': '2024Q3', 'run_date': '2024-10-01',
            'http_last_modified_utc': '1970-01-01T00:00:00+00:00',
            'source_sha256': 'a' * 64, 'parse_status': 'PASS',
        }}
        content = {'2024Q3': {
            'quarter': '2024Q3', 'format': 'txt',
            'source_sha256': 'b' * 64, 'parsed_rows': '11332',
            'unique_cusips': '11332', 'checksum_valid_unique_cusips': '11332',
        }}
        row = build_pdf_pit_manifest(pdf, content)[0]
        self.assertIsNone(row['pdf_last_modified_utc'])
        self.assertEqual(row['conservative_available_from_5d_pdf_proxy'], '2024-10-07')

    def test_cross_format_comparison_detects_no_difference(self):
        pdf = {('A1', '2020Q1'): True, ('A2', '2020Q1'): False}
        txt = {('A1', '2020Q1'): True, ('A2', '2020Q1'): False}
        rows, mismatches, n, equal = compare_sample_matches(pdf, txt, {'A1', 'A2'}, {'2020Q1'})
        self.assertEqual(n, 2)
        self.assertEqual(equal, 2)
        self.assertEqual(mismatches, [])
        self.assertEqual(rows[0]['sample_match_concordance_rate'], 1.0)

    def test_cross_format_comparison_records_mismatch(self):
        pdf = {('A1', '2020Q1'): True}
        txt = {('A1', '2020Q1'): False}
        rows, mismatches, n, equal = compare_sample_matches(pdf, txt, {'A1'}, {'2020Q1'})
        self.assertEqual(n, 1)
        self.assertEqual(equal, 0)
        self.assertEqual(mismatches[0]['accession'], 'A1')

    def test_missing_matches_are_not_counted_as_negative(self):
        pdf = {('A1', '2020Q1'): None}
        txt = {('A1', '2020Q1'): False}
        rows, mismatches, n, equal = compare_sample_matches(pdf, txt, {'A1'}, {'2020Q1'})
        self.assertEqual(n, 0)
        self.assertEqual(equal, 0)
        self.assertEqual(mismatches, [])

    def test_concordance_summary_separates_txt_pdf_crosscheck_from_pdf_repeat(self):
        rows = [
            {'quarter': '2020Q1', 'sample_match_comparisons': 10, 'sample_match_concordant': 10, 'sample_match_disagreements': 0},
            {'quarter': '2019Q4', 'sample_match_comparisons': 10, 'sample_match_concordant': 10, 'sample_match_disagreements': 0},
        ]
        manifests = {'2020Q1': {'format': 'txt'}, '2019Q4': {'format': 'pdf'}}
        result = summarize_concordance_by_format(rows, manifests)
        self.assertEqual(result['txt']['sample_match_comparisons'], 10)
        self.assertIn('Independent TXT-versus-PDF', result['txt']['interpretation'])
        self.assertIn('not independent', result['pdf']['interpretation'])

    def test_unique_cusip_coverage_deduplicates_repeated_filings(self):
        sample = [
            {'accession': 'A1', 'cusip': '037833100', 'cusip_status': 'UNIQUE_CHECKSUM_VALID',
             'acceptance_datetime': '2020-01-02T12:00:00-05:00', 'filing_date': '2020-01-02'},
            {'accession': 'A2', 'cusip': '037833100', 'cusip_status': 'UNIQUE_CHECKSUM_VALID',
             'acceptance_datetime': '2021-01-02T12:00:00-05:00', 'filing_date': '2021-01-02'},
            {'accession': 'B1', 'cusip': '594918104', 'cusip_status': 'UNIQUE_CHECKSUM_VALID',
             'acceptance_datetime': '2020-02-02T12:00:00-05:00', 'filing_date': '2020-02-02'},
            {'accession': 'C1', 'cusip': '', 'cusip_status': 'INVALID_CHECKSUM',
             'acceptance_datetime': '2020-03-02T12:00:00-05:00', 'filing_date': '2020-03-02'},
        ]
        audit = [
            {'accession': 'A1', 'match_5d_proxy': True},
            {'accession': 'A2', 'match_5d_proxy': True},
            {'accession': 'B1', 'match_5d_proxy': False},
            {'accession': 'C1', 'match_5d_proxy': None},
        ]
        result = unique_cusip_coverage(sample, audit)
        self.assertEqual(result['unique_valid_cusips'], 2)
        self.assertEqual(result['first_observed_filing_5d_match']['matches'], 1)
        self.assertEqual(result['first_observed_filing_5d_match']['rate'], 0.5)
        self.assertEqual(result['repeated_cusips'], 1)
        self.assertEqual(result['repeated_cusips_with_consistent_5d_match_status'], 1)

    def test_no_raw_cusip_fields_in_output_schema(self):
        from research.phase166_sec13f_cross_format_pit_bridge import QUARTER_FIELDS, MISMATCH_FIELDS, BRIDGE_AUDIT_FIELDS
        self.assertNotIn('cusip', QUARTER_FIELDS)
        self.assertNotIn('cusip', MISMATCH_FIELDS)
        self.assertNotIn('cusip', BRIDGE_AUDIT_FIELDS)


if __name__ == '__main__':
    unittest.main()
