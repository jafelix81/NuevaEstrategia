#!/usr/bin/env python3
"""Phase 166: bridge Phase 165 TXT content matches to PDF historical PIT metadata.

This is an offline artifact reconciliation. It performs no SEC requests and
never persists raw Section 13(f) list CUSIPs, rows, issuer names or descriptions.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from research.phase165_sec13f_resumable_audit import (
    AUDIT_FIELDS,
    build_audit_rows,
    parse_acceptance_date,
    proxy_dates,
    read_csv,
    safe_rate,
    safe_weighted_rate,
    write_csv,
)

PDF_RUN_ID = 42278015855
CONTENT_RUN_ID = 42278657127
EXPECTED_QUARTERS = 45
QUARTER_FIELDS = [
    'quarter', 'pdf_metadata_source_sha256', 'pdf_run_date',
    'pdf_last_modified_utc', 'content_format', 'content_source_sha256',
    'content_parsed_rows', 'content_unique_identifiers',
    'content_checksum_conforming_identifiers',
    'content_checksum_nonconforming_identifiers',
    'content_checksum_conformance_rate',
    'conservative_available_from_1d_pdf_proxy',
    'conservative_available_from_5d_pdf_proxy',
    'sample_match_comparisons', 'sample_match_concordant',
    'sample_match_disagreements', 'sample_match_concordance_rate',
]
MISMATCH_FIELDS = ['accession', 'quarter', 'pdf_match', 'content_match']
BRIDGE_AUDIT_FIELDS = AUDIT_FIELDS + [
    'prior_list_content_format_5d',
    'prior_list_pdf_run_date_5d',
    'prior_list_pdf_metadata_source_sha256_5d',
    'prior_list_content_source_sha256_5d',
]


def load_shard_dir(path: Path):
    manifests = {}
    matches = {}
    manifest_files = sorted(path.rglob('phase165_snapshot_manifest_shard_*.csv'))
    match_files = sorted(path.rglob('phase165_quarter_matches_shard_*.csv'))
    if len(manifest_files) != 9 or len(match_files) != 9:
        raise ValueError(f'{path}: expected 9 manifest and 9 match shard files; got {len(manifest_files)}/{len(match_files)}')
    for file in manifest_files:
        for row in read_csv(file):
            quarter = row['quarter']
            if quarter in manifests and manifests[quarter].get('source_sha256') != row.get('source_sha256'):
                raise ValueError(f'conflicting manifest rows for {quarter}')
            manifests[quarter] = row
    for file in match_files:
        for row in read_csv(file):
            key = (row['accession'], row['quarter'])
            value = row.get('match_13f_list')
            if value in ('True', 'true', '1'):
                parsed = True
            elif value in ('False', 'false', '0'):
                parsed = False
            else:
                parsed = None
            if key in matches and matches[key] != parsed:
                raise ValueError(f'conflicting match rows for {key}')
            matches[key] = parsed
    return manifests, matches


def parse_pdf_last_modified(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return None if parsed.year < 1990 else parsed


def build_pdf_pit_manifest(pdf_manifests, content_manifests):
    output = []
    for quarter in sorted(pdf_manifests):
        pdf = pdf_manifests[quarter]
        content = content_manifests[quarter]
        run_date = date.fromisoformat(pdf['run_date']) if pdf.get('run_date') else None
        lm = parse_pdf_last_modified(pdf.get('http_last_modified_utc'))
        available_1d, available_5d = proxy_dates(run_date, lm)
        unique = int(content.get('unique_cusips') or 0)
        conforming = int(content.get('checksum_valid_unique_cusips') or 0)
        output.append({
            'quarter': quarter,
            'pdf_metadata_source_sha256': pdf.get('source_sha256'),
            'pdf_run_date': run_date.isoformat() if run_date else None,
            'pdf_last_modified_utc': lm.isoformat() if lm else None,
            'content_format': content.get('format'),
            'content_source_sha256': content.get('source_sha256'),
            'content_parsed_rows': int(content.get('parsed_rows') or 0),
            'content_unique_identifiers': unique,
            'content_checksum_conforming_identifiers': conforming,
            'content_checksum_nonconforming_identifiers': max(0, unique - conforming),
            'content_checksum_conformance_rate': conforming / unique if unique else None,
            'conservative_available_from_1d_pdf_proxy': available_1d,
            'conservative_available_from_5d_pdf_proxy': available_5d,
        })
    return output


def compare_sample_matches(pdf_matches, content_matches, valid_accessions, quarters):
    quarter_rows = []
    mismatches = []
    total_n = total_equal = 0
    for quarter in sorted(quarters):
        n = equal = 0
        for accession in sorted(valid_accessions):
            key = (accession, quarter)
            left = pdf_matches.get(key)
            right = content_matches.get(key)
            if left is None or right is None:
                continue
            n += 1
            total_n += 1
            if left == right:
                equal += 1
                total_equal += 1
            else:
                mismatches.append({
                    'accession': accession,
                    'quarter': quarter,
                    'pdf_match': left,
                    'content_match': right,
                })
        quarter_rows.append({
            'quarter': quarter,
            'sample_match_comparisons': n,
            'sample_match_concordant': equal,
            'sample_match_disagreements': n - equal,
            'sample_match_concordance_rate': equal / n if n else None,
        })
    return quarter_rows, mismatches, total_n, total_equal



def summarize_concordance_by_format(quarter_rows, content_manifests):
    by_quarter = {row['quarter']: row for row in quarter_rows}
    output = {}
    for fmt in sorted({row.get('format') for row in content_manifests.values()}):
        quarters = [q for q, row in content_manifests.items() if row.get('format') == fmt]
        comparisons = sum(int(by_quarter[q]['sample_match_comparisons']) for q in quarters)
        concordant = sum(int(by_quarter[q]['sample_match_concordant']) for q in quarters)
        disagreements = sum(int(by_quarter[q]['sample_match_disagreements']) for q in quarters)
        output[fmt] = {
            'quarters': len(quarters),
            'sample_match_comparisons': comparisons,
            'sample_match_concordant': concordant,
            'sample_match_disagreements': disagreements,
            'sample_match_concordance_rate': concordant / comparisons if comparisons else None,
            'interpretation': 'Independent TXT-versus-PDF sample check' if fmt == 'txt' else 'Repeated PDF-versus-PDF parser check; not independent format validation',
        }
    return output

def build_bridge_audit(sample, pit_manifest, content_matches):
    pit_snapshots = []
    by_quarter = {}
    for row in pit_manifest:
        snapshot = {
            'quarter': row['quarter'],
            'run_date': row.get('pdf_run_date'),
            'conservative_available_from_1d': row.get('conservative_available_from_1d_pdf_proxy'),
            'conservative_available_from_5d': row.get('conservative_available_from_5d_pdf_proxy'),
            # build_audit_rows carries this as the match-content hash.
            'source_sha256': row.get('content_source_sha256'),
            'parse_status': 'PASS',
        }
        pit_snapshots.append(snapshot)
        by_quarter[row['quarter']] = row
    rows = build_audit_rows(sample, pit_snapshots, content_matches)
    for row in rows:
        quarter = row.get('latest_prior_quarter_5d_proxy')
        source = by_quarter.get(quarter) if quarter else None
        row['prior_list_content_format_5d'] = source.get('content_format') if source else None
        row['prior_list_pdf_run_date_5d'] = source.get('pdf_run_date') if source else None
        row['prior_list_pdf_metadata_source_sha256_5d'] = source.get('pdf_metadata_source_sha256') if source else None
        row['prior_list_content_source_sha256_5d'] = source.get('content_source_sha256') if source else None
    return rows



def unique_cusip_coverage(sample, audit_rows):
    audit_by_accession = {row['accession']: row for row in audit_rows}
    by_cusip = defaultdict(list)
    for base in sample:
        if base.get('cusip_status') != 'UNIQUE_CHECKSUM_VALID' or not base.get('cusip'):
            continue
        audit = audit_by_accession.get(base['accession'])
        if audit is None:
            continue
        event_date, _ = parse_acceptance_date(
            base.get('acceptance_datetime'), base.get('filing_date') or ''
        )
        by_cusip[base['cusip']].append((event_date, audit))
    first_matches = []
    last_matches = []
    any_matches = []
    repeated = 0
    repeated_consistent = 0
    for observations in by_cusip.values():
        ordered = sorted(observations, key=lambda item: item[0])
        values = [
            item[1].get('match_5d_proxy')
            for item in ordered
            if item[1].get('match_5d_proxy') is not None
        ]
        first_matches.append(ordered[0][1].get('match_5d_proxy'))
        last_matches.append(ordered[-1][1].get('match_5d_proxy'))
        any_matches.append(any(value is True for value in values) if values else None)
        if len(ordered) > 1:
            repeated += 1
            if values and len(set(values)) == 1:
                repeated_consistent += 1
    def block(values):
        eligible = [value for value in values if value is not None]
        return {
            'n': len(eligible),
            'matches': sum(bool(value) for value in eligible),
            'rate': sum(bool(value) for value in eligible) / len(eligible) if eligible else None,
        }
    return {
        'unique_valid_cusips': len(by_cusip),
        'first_observed_filing_5d_match': block(first_matches),
        'last_observed_filing_5d_match': block(last_matches),
        'any_observed_filing_5d_match': block(any_matches),
        'repeated_cusips': repeated,
        'repeated_cusips_with_consistent_5d_match_status': repeated_consistent,
    }


def rate_block(rows, field):
    eligible = [row for row in rows if row.get(field) is not None]
    return {
        'n': len(eligible),
        'matches': sum(bool(row[field]) for row in eligible),
        'rate': safe_rate(eligible, field),
        'weighted_rate': safe_weighted_rate(eligible, field),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf-shards', type=Path, required=True)
    parser.add_argument('--content-shards', type=Path, required=True)
    parser.add_argument('--sample-csv', type=Path, required=True)
    parser.add_argument('--content-summary-json', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()

    pdf_manifests, pdf_matches = load_shard_dir(args.pdf_shards)
    content_manifests, content_matches = load_shard_dir(args.content_shards)
    sample = read_csv(args.sample_csv)
    content_summary = json.loads(args.content_summary_json.read_text(encoding='utf-8'))

    if len(sample) != 599 or len(pdf_manifests) != EXPECTED_QUARTERS or len(content_manifests) != EXPECTED_QUARTERS:
        raise ValueError('Phase 165 artifact dimensions do not reconcile')
    if set(pdf_manifests) != set(content_manifests):
        raise ValueError('PDF/content quarter sets differ')
    if any(row.get('parse_status') != 'PASS' for row in pdf_manifests.values()):
        raise ValueError('PDF metadata run contains failed quarterly snapshots')
    if any(row.get('parse_status') != 'PASS' for row in content_manifests.values()):
        raise ValueError('content run contains failed quarterly snapshots')

    valid_accessions = {
        row['accession'] for row in sample
        if row.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID' and row.get('cusip')
    }
    pit_manifest = build_pdf_pit_manifest(pdf_manifests, content_manifests)
    concordance_rows, mismatch_rows, comparison_n, concordant_n = compare_sample_matches(
        pdf_matches, content_matches, valid_accessions, set(pdf_manifests)
    )
    concordance_by_quarter = {row['quarter']: row for row in concordance_rows}
    concordance_by_format = summarize_concordance_by_format(concordance_rows, content_manifests)
    for row in pit_manifest:
        row.update(concordance_by_quarter[row['quarter']])

    audit_rows = build_bridge_audit(sample, pit_manifest, content_matches)
    unique_coverage = unique_cusip_coverage(sample, audit_rows)
    valid_audit = [row for row in audit_rows if row.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID']
    prior1 = rate_block(valid_audit, 'match_1d_proxy')
    prior5 = rate_block(valid_audit, 'match_5d_proxy')
    same = rate_block(valid_audit, 'same_quarter_list_match_lookahead_diagnostic')
    lookahead_only = sum(bool(row.get('lookahead_only_match_vs_5d_proxy')) for row in valid_audit)

    content_formats = Counter(row.get('content_format') for row in pit_manifest)
    txt_migration_rows = []
    txt_last_modified_values = Counter()
    for row in content_manifests.values():
        if row.get('format') != 'txt' or not row.get('http_last_modified_utc'):
            continue
        lm = date.fromisoformat(row['http_last_modified_utc'][:10])
        txt_last_modified_values[lm.isoformat()] += 1
        qyear, qquarter = int(row['quarter'][:4]), int(row['quarter'][-1])
        qend_month = qquarter * 3
        qend = date(qyear, qend_month, 1)
        if qend_month == 12:
            qend = date(qyear, 12, 31)
        else:
            next_month = date(qyear + (1 if qend_month == 12 else 0), (qend_month % 12) + 1, 1)
            qend = next_month - timedelta(days=1)
        if lm > qend + timedelta(days=365):
            txt_migration_rows.append(row['quarter'])

    pdf_epoch_sentinels = sum(
        bool(row.get('http_last_modified_utc')) and int(row['http_last_modified_utc'][:4]) < 1990
        for row in pdf_manifests.values()
    )
    checksum_by_format = {}
    for fmt in sorted(content_formats):
        group = [row for row in pit_manifest if row.get('content_format') == fmt]
        total_unique = sum(int(row.get('content_unique_identifiers') or 0) for row in group)
        total_conforming = sum(int(row.get('content_checksum_conforming_identifiers') or 0) for row in group)
        checksum_by_format[fmt] = {
            'snapshots': len(group),
            'unique_identifiers': total_unique,
            'checksum_conforming_identifiers': total_conforming,
            'checksum_nonconforming_identifiers': total_unique - total_conforming,
            'conformance_rate': total_conforming / total_unique if total_unique else None,
        }

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / 'phase166_sec13f_cross_format_quarter_concordance.csv',
              QUARTER_FIELDS, pit_manifest)
    write_csv(output_dir / 'phase166_sec13f_pdf_timestamp_bridge.csv',
              QUARTER_FIELDS, pit_manifest)
    write_csv(output_dir / 'phase166_sec13dg_13f_pit_overlap_audit.csv',
              BRIDGE_AUDIT_FIELDS, audit_rows)
    write_csv(output_dir / 'phase166_sec13f_cross_format_mismatches.csv',
              MISMATCH_FIELDS, mismatch_rows)

    expected_comparisons = EXPECTED_QUARTERS * len(valid_accessions)
    naive_rate = content_summary.get('match_rate_5d_proxy')
    summary = {
        'phase': 166,
        'status': 'PASS_CROSS_FORMAT_PIT_BRIDGE' if comparison_n == expected_comparisons and comparison_n == concordant_n and len(pit_manifest) == EXPECTED_QUARTERS else 'FAIL_OR_PARTIAL_CROSS_FORMAT_PIT_BRIDGE',
        'pdf_metadata_source_run_id': PDF_RUN_ID,
        'content_source_run_id': CONTENT_RUN_ID,
        'quarter_snapshots_expected': EXPECTED_QUARTERS,
        'pdf_metadata_snapshots': len(pdf_manifests),
        'content_snapshots': len(content_manifests),
        'content_source_format_counts': dict(content_formats),
        'valid_sample_filings': len(valid_accessions),
        'unique_cusip_coverage': unique_coverage,
        'expected_sample_match_comparisons': expected_comparisons,
        'sample_match_comparisons': comparison_n,
        'sample_match_concordant': concordant_n,
        'sample_match_disagreements': len(mismatch_rows),
        'sample_match_concordance_rate': concordant_n / comparison_n if comparison_n else None,
        'sample_match_concordance_by_content_format': concordance_by_format,
        'match_1d_pdf_run_date_proxy': prior1,
        'match_5d_pdf_run_date_proxy': prior5,
        'same_quarter_lookahead_diagnostic': same,
        'lookahead_only_matches_vs_5d_pdf_proxy': lookahead_only,
        'one_day_vs_five_day_match_disagreements': sum(
            row.get('match_1d_proxy') != row.get('match_5d_proxy')
            for row in valid_audit
            if row.get('match_1d_proxy') is not None and row.get('match_5d_proxy') is not None
        ),
        'naive_txt_last_modified_5d_match_rate': naive_rate,
        'naive_vs_pdf_bridge_5d_match_rate_difference_percentage_points': ((float(naive_rate) - float(prior5['rate'])) * 100) if naive_rate is not None and prior5.get('rate') is not None else None,
        'naive_txt_last_modified_5d_weighted_match_rate': content_summary.get('weighted_match_rate_5d_proxy'),
        'naive_txt_last_modified_lookahead_only_matches': content_summary.get('same_quarter_lookahead_only_matches'),
        'txt_last_modified_migration_quarters': sorted(txt_migration_rows),
        'txt_last_modified_migration_count': len(txt_migration_rows),
        'txt_last_modified_values': dict(txt_last_modified_values),
        'pdf_run_date_present_snapshots': sum(bool(row.get('run_date')) for row in pdf_manifests.values()),
        'pdf_epoch_last_modified_sentinels_ignored': pdf_epoch_sentinels,
        'checksum_diagnostic_by_content_format': checksum_by_format,
        'checksum_interpretation': 'Standard CUSIP check-digit conformance is a diagnostic, not a universal exclusion rule for the 13(f) list. Official 2026Q3 rows explicitly include CALL/PUT series identifiers whose 9-character values do not pass the standard equity CUSIP check-digit test. Sample overlap uses only the Phase 127 checksum-valid 13D/G CUSIPs.',
        'pit_status': 'PDF_RUN_DATE_PLUS_2_PLUS_6_CALENDAR_DAY_SENSITIVITY_PROXY_NOT_VERIFIED_FIRST_PUBLICATION',
        'pit_bridge_rule': 'Use PDF Run Date and non-sentinel PDF HTTP Last-Modified for historical availability sensitivities. Do not use TXT Last-Modified values that reflect later archive migration/republication dates.',
        'content_rule': 'Use the second Phase 165 run match booleans (TXT for 2020+ where available; PDF otherwise) only after sample-level concordance against the first all-PDF run.',
        'redistribution_control': 'No raw 13(f) list CUSIPs, list rows, issuer names or descriptions are persisted.',
        'no_alpha_test': True,
        'no_vendor_purchase': True,
        'f80_baseline_frozen': True,
    }
    (output_dir / 'phase166_sec13f_cross_format_pit_bridge_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    print(json.dumps(summary, indent=2))
    if summary['status'] != 'PASS_CROSS_FORMAT_PIT_BRIDGE':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
