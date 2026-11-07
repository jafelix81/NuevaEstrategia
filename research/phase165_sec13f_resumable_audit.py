#!/usr/bin/env python3
"""Phase 165: resumable SEC 13(f) official-list overlap audit.

The official 13(f) lists contain CUSIP Global Services material. Raw list rows,
CUSIPs and issuer descriptions are processed only in memory and are never written
to repository artifacts. Outputs contain source metadata and match booleans only.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import time
import tempfile
import zlib
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research.phase129_sec13f_list_cusip_pit_overlap_audit import (
    PHASE124_RUN_ID,
    PHASE127_RUN_ID,
    PHASE127_ARTIFACT_DIGEST,
    parse_acceptance_date,
    parse_last_modified,
    parse_pdf,
    parse_run_metadata,
    quarter_iter,
)
from research.phase125_sec_13dg_exact_cusip_audit import cusip_check_digit

USER_AGENT = 'jafelix81/NuevaEstrategia Smart Money Research (research-only)'
CONTACT_EMAIL = os.environ.get('SEC_CONTACT_EMAIL', '').strip()
if CONTACT_EMAIL:
    USER_AGENT += ' contact=' + CONTACT_EMAIL
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/pdf,text/plain,*/*',
    'Accept-Encoding': 'identity',
}
EXPECTED_QUARTERS = 45
SAMPLE_ROWS = 599
MANIFEST_FIELDS = [
    'quarter', 'format', 'source_url', 'source_sha256',
    'http_last_modified_utc', 'http_last_modified_header', 'http_content_encoding', 'http_etag', 'http_date',
    'content_length_header', 'run_date', 'run_time_local_unspecified',
    'stated_quarter', 'quarter_identity_basis', 'metadata_basis',
    'conservative_available_from_1d', 'conservative_available_from_5d',
    'parsed_rows', 'unique_cusips', 'checksum_valid_unique_cusips',
    'invalid_unique_cusips', 'duplicate_rows', 'checksum_validation_status', 'parse_status', 'errors',
]
MATCH_FIELDS = [
    'accession', 'quarter', 'filing_date', 'acceptance_datetime',
    'sample_weight', 'cusip_status', 'match_known', 'match_13f_list',
    'conservative_available_from_1d', 'conservative_available_from_5d',
    'source_sha256',
]
AUDIT_FIELDS = [
    'accession', 'family', 'filing_date', 'acceptance_datetime',
    'acceptance_date_source', 'sample_weight', 'cusip_status',
    'latest_prior_quarter_1d_proxy', 'match_1d_proxy',
    'latest_prior_quarter_5d_proxy', 'match_5d_proxy',
    'same_quarter_list_match_lookahead_diagnostic',
    'same_quarter_list_available', 'lookahead_only_match_vs_5d_proxy',
    'days_from_prior_run_date_5d', 'prior_list_source_sha256_5d',
]


def read_csv(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def candidate_urls(year: int, quarter: int):
    stem = f'13flist{year}q{quarter}'
    if (year, quarter) >= (2020, 1):
        # The SEC archive page exposes TXT files from 2020 onward. The paired
        # PDF is retained as a fallback and as a source of Run Date metadata.
        yield f'https://www.sec.gov/files/investment/{stem}.txt', 'txt'
        yield f'https://www.sec.gov/files/investment/{stem}.pdf', 'pdf'
        yield f'https://www.sec.gov/divisions/investment/13f/{stem}.pdf', 'pdf'
    else:
        yield f'https://www.sec.gov/divisions/investment/13f/{stem}.pdf', 'pdf'
        yield f'https://www.sec.gov/files/investment/{stem}.pdf', 'pdf'


def parse_txt_fixed_width(raw: bytes):
    """Parse the SEC fixed-width TXT: CUSIP occupies columns 1-9 and '*' is column 10."""
    text = raw.decode('utf-8-sig', errors='replace')
    run_date, run_time, stated_quarter = parse_run_metadata(text)
    cusips = []
    for line in text.splitlines():
        candidate = line[:9].strip().upper()
        if re.fullmatch(r'[A-Z0-9]{9}', candidate):
            cusips.append(candidate)
    return text, run_date, run_time, stated_quarter, cusips

def is_valid_cusip(value: str):
    # Phase 129's wrapper compared a boolean result with the string check digit,
    # classifying every 13(f) list CUSIP as invalid. Use the tested Phase 125
    # full-CUSIP validator directly.
    return bool(cusip_check_digit(value))


def parse_last_modified_safe(value):
    parsed = parse_last_modified(value)
    # SEC/CDN sometimes emits the Unix epoch as a placeholder Last-Modified.
    return None if parsed and parsed.year < 1990 else parsed


def decode_payload(raw: bytes, headers: dict):
    encoding = str(headers.get('content-encoding', '')).lower()
    if 'gzip' in encoding or raw.startswith(b'\\x1f\\x8b'):
        return gzip.decompress(raw)
    if 'deflate' in encoding:
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def download_bytes(url: str, retries: int = 1, timeout: int = 30):
    last_error = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                headers = {key.lower(): value for key, value in response.headers.items()}
                if response.status != 200:
                    raise RuntimeError(f'HTTP {response.status}')
                payload = decode_payload(raw, headers)
                return raw, payload, headers, response.geturl()
        except HTTPError as exc:
            last_error = f'HTTP {exc.code}: {exc.reason}'
            retryable = exc.code in {408, 429, 500, 502, 503, 504}
            retry_after = exc.headers.get('Retry-After') if exc.headers else None
            if not retryable or attempt >= retries:
                break
            try:
                delay = min(max(int(retry_after), 1), 10) if retry_after else min(2 ** attempt, 5)
            except ValueError:
                delay = min(2 ** attempt, 5)
            time.sleep(delay)
        except (URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = str(exc)
            if attempt >= retries:
                break
            time.sleep(min(2 ** attempt, 5))
    raise RuntimeError(last_error or 'download failed')


def metadata_basis(run_date, last_modified):
    if run_date and last_modified:
        return 'RUN_DATE_AND_LAST_MODIFIED'
    if run_date:
        return 'RUN_DATE_ONLY'
    if last_modified:
        return 'LAST_MODIFIED_ONLY'
    return 'NO_TIMESTAMP_METADATA'


def proxy_dates(run_date, last_modified):
    candidates = []
    if run_date:
        candidates.append(run_date)
    if last_modified:
        candidates.append(last_modified.date())
    if not candidates:
        return None, None
    base = max(candidates)
    # These remain sensitivity proxies, not verified first-publication times.
    return (base + timedelta(days=2)).isoformat(), (base + timedelta(days=6)).isoformat()


def download_snapshot(year: int, quarter: int, temp_dir: Path):
    expected = f'{year}Q{quarter}'
    errors = []
    for url, preferred_format in candidate_urls(year, quarter):
        try:
            raw, payload, headers, final_url = download_bytes(url)
            if payload.startswith(b'%PDF'):
                fmt = 'pdf'
                _, run_date, run_time, stated_quarter, cusips = parse_pdf(payload, temp_dir)
            else:
                sample = payload[:500].lstrip().lower()
                if b'<html' in sample or b'<!doctype html' in sample:
                    errors.append({'url': url, 'error': 'HTML response, not a list file'})
                    continue
                fmt = 'txt'
                _, run_date, run_time, stated_quarter, cusips = parse_txt_fixed_width(payload)
            if len(cusips) < 1000:
                errors.append({'url': url, 'error': f'too few parsed CUSIP rows: {len(cusips)}'})
                continue
            if stated_quarter and stated_quarter != expected:
                errors.append({'url': url, 'error': f'stated quarter {stated_quarter} != {expected}'})
                continue
            unique = set(cusips)
            valid = {value for value in unique if is_valid_cusip(value)}
            invalid = unique - valid
            last_modified_header = headers.get('last-modified')
            last_modified = parse_last_modified_safe(last_modified_header)
            available_1d, available_5d = proxy_dates(run_date, last_modified)
            manifest = {
                'quarter': expected,
                'format': fmt,
                'source_url': final_url,
                'source_sha256': hashlib.sha256(raw).hexdigest(),
                'http_last_modified_utc': last_modified.isoformat() if last_modified else None,
                'http_last_modified_header': last_modified_header,
                'http_content_encoding': headers.get('content-encoding'),
                'http_etag': headers.get('etag'),
                'http_date': headers.get('date'),
                'content_length_header': headers.get('content-length'),
                'run_date': run_date.isoformat() if run_date else None,
                'run_time_local_unspecified': run_time,
                'stated_quarter': stated_quarter,
                'quarter_identity_basis': 'FILE_CONTENT' if stated_quarter else 'OFFICIAL_SEC_ARCHIVE_URL',
                'metadata_basis': metadata_basis(run_date, last_modified),
                'conservative_available_from_1d': available_1d,
                'conservative_available_from_5d': available_5d,
                'parsed_rows': len(cusips),
                'unique_cusips': len(unique),
                'checksum_valid_unique_cusips': len(valid),
                'invalid_unique_cusips': len(invalid),
                'duplicate_rows': len(cusips) - len(unique),
                'checksum_validation_status': 'PASS_PHASE125_CHECK_DIGIT',
                'parse_status': 'PASS',
                'errors': json.dumps(errors, sort_keys=True),
            }
            return manifest, unique
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)[:500]})
    return {
        'quarter': expected,
        'format': None,
        'source_url': None,
        'source_sha256': None,
        'http_last_modified_utc': None,
        'http_last_modified_header': None,
        'http_content_encoding': None,
        'http_etag': None,
        'http_date': None,
        'content_length_header': None,
        'run_date': None,
        'run_time_local_unspecified': None,
        'stated_quarter': None,
        'quarter_identity_basis': None,
        'metadata_basis': 'NO_TIMESTAMP_METADATA',
        'conservative_available_from_1d': None,
        'conservative_available_from_5d': None,
        'parsed_rows': 0,
        'unique_cusips': 0,
        'checksum_valid_unique_cusips': 0,
        'invalid_unique_cusips': 0,
        'duplicate_rows': 0,
        'checksum_validation_status': 'NOT_AVAILABLE',
        'parse_status': 'FAILED',
        'errors': json.dumps(errors, sort_keys=True),
    }, set()


def prepare_sample(phase124_dir: Path, phase127_dir: Path, output_dir: Path):
    summary124 = json.loads((phase124_dir / 'phase124_global_13dg_summary.json').read_text(encoding='utf-8'))
    summary127 = json.loads((phase127_dir / 'phase127_sec_13dg_xml_cusip_summary.json').read_text(encoding='utf-8'))
    rows124 = read_csv(phase124_dir / 'phase124_global_13dg_submission_audit.csv')
    rows127 = read_csv(phase127_dir / 'phase127_sec_13dg_xml_cusip_audit.csv')
    if len(rows124) != 600 or len(rows127) != SAMPLE_ROWS:
        raise ValueError('Phase 124/127 artifact row counts mismatch')
    if summary124.get('source_phase124_run_id') not in (None, PHASE124_RUN_ID):
        raise ValueError('Unexpected Phase 124 source run')
    if summary127.get('source_phase124_run_id') != PHASE124_RUN_ID:
        raise ValueError('Phase 127 source Phase 124 provenance mismatch')
    if not str(summary127.get('status', '')).startswith('PASS'):
        raise ValueError('Phase 127 status/provenance mismatch')
    rows124_by = {row['accession']: row for row in rows124}
    sample = []
    for row in rows127:
        base = rows124_by.get(row['accession'])
        if base is None or base.get('raw_sha256') != row.get('raw_sha256'):
            raise ValueError(f'Phase 124/127 raw hash join mismatch for {row["accession"]}')
        sample.append({
            'accession': row['accession'],
            'family': base.get('family'),
            'filing_date': base.get('filing_date_index'),
            'acceptance_datetime': base.get('acceptance_datetime'),
            'sample_weight': float(base.get('sample_weight') or 0),
            'cusip': row.get('cusip') if row.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID' else '',
            'cusip_status': row.get('cusip_status'),
        })
    if len({row['accession'] for row in sample}) != SAMPLE_ROWS:
        raise ValueError('Phase 127 accession uniqueness mismatch')
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / 'phase165_sample.csv',
              ['accession', 'family', 'filing_date', 'acceptance_datetime', 'sample_weight', 'cusip', 'cusip_status'],
              sample)
    summary = {
        'phase': 165,
        'status': 'PASS_INPUT_RECONCILIATION',
        'source_phase124_run_id': PHASE124_RUN_ID,
        'source_phase127_run_id': PHASE127_RUN_ID,
        'source_phase127_artifact_digest': PHASE127_ARTIFACT_DIGEST,
        'phase124_rows': len(rows124),
        'phase127_rows': len(rows127),
        'sample_rows': len(sample),
        'valid_cusip_rows': sum(row['cusip_status'] == 'UNIQUE_CHECKSUM_VALID' for row in sample),
        'raw_13f_list_data_in_sample_artifact': False,
    }
    (output_dir / 'phase165_sample_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return summary


def shard_quarters(shard_index: int, shard_count: int = 9):
    if shard_count < 1 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError('invalid shard index/count')
    quarters = list(quarter_iter(2015, 3, 2026, 3))
    return quarters[shard_index::shard_count]


def run_shard(sample_csv: Path, shard_index: int, shard_count: int, output_dir: Path):
    sample = read_csv(sample_csv)
    if len(sample) != SAMPLE_ROWS:
        raise ValueError(f'expected {SAMPLE_ROWS} sample rows, got {len(sample)}')
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    match_rows = []
    manifest_path = output_dir / f'phase165_snapshot_manifest_shard_{shard_index}.csv'
    matches_path = output_dir / f'phase165_quarter_matches_shard_{shard_index}.csv'
    write_csv(manifest_path, MANIFEST_FIELDS, manifest_rows)
    write_csv(matches_path, MATCH_FIELDS, match_rows)
    with tempfile.TemporaryDirectory(prefix=f'phase165_shard_{shard_index}_') as tmp:
        temp_dir = Path(tmp)
        for year, quarter in shard_quarters(shard_index, shard_count):
            manifest, list_cusips = download_snapshot(year, quarter, temp_dir)
            manifest_rows.append(manifest)
            if manifest.get('parse_status') == 'PASS':
                for row in sample:
                    cusip = row.get('cusip') or ''
                    known = bool(cusip and row.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID')
                    match_rows.append({
                        'accession': row['accession'],
                        'quarter': manifest['quarter'],
                        'filing_date': row.get('filing_date'),
                        'acceptance_datetime': row.get('acceptance_datetime'),
                        'sample_weight': row.get('sample_weight'),
                        'cusip_status': row.get('cusip_status'),
                        'match_known': known,
                        'match_13f_list': bool(known and cusip in list_cusips) if known else None,
                        'conservative_available_from_1d': manifest.get('conservative_available_from_1d'),
                        'conservative_available_from_5d': manifest.get('conservative_available_from_5d'),
                        'source_sha256': manifest.get('source_sha256'),
                    })
            write_csv(manifest_path, MANIFEST_FIELDS, manifest_rows)
            write_csv(matches_path, MATCH_FIELDS, match_rows)
            print(json.dumps({
                'phase': 165,
                'shard': shard_index,
                'quarter': manifest['quarter'],
                'parse_status': manifest['parse_status'],
                'completed_quarters': len(manifest_rows),
                'expected_quarters': len(shard_quarters(shard_index, shard_count)),
            }, sort_keys=True))
    passed = sum(row.get('parse_status') == 'PASS' for row in manifest_rows)
    summary = {
        'phase': 165,
        'shard_index': shard_index,
        'shard_count': shard_count,
        'expected_quarters': len(shard_quarters(shard_index, shard_count)),
        'quarter_snapshots_passed': passed,
        'quarter_snapshots_failed': len(manifest_rows) - passed,
        'failed_quarters': [row['quarter'] for row in manifest_rows if row.get('parse_status') != 'PASS'],
        'raw_13f_cusips_persisted': False,
        'checkpointing': True,
        'status': 'PASS' if passed == len(manifest_rows) else 'PARTIAL',
    }
    (output_dir / f'phase165_shard_summary_{shard_index}.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return summary


def safe_rate(rows, field):
    values = [row.get(field) for row in rows if row.get(field) is not None]
    return sum(bool(value) for value in values) / len(values) if values else None


def safe_weighted_rate(rows, field):
    eligible = [row for row in rows if row.get(field) is not None]
    denominator = sum(float(row.get('sample_weight') or 0) for row in eligible)
    if denominator <= 0:
        return None
    numerator = sum(float(row.get('sample_weight') or 0) for row in eligible if row.get(field))
    return numerator / denominator


def build_audit_rows(sample, passed_snapshots, match_lookup):
    output = []
    for base in sample:
        filing_date, date_source = parse_acceptance_date(
            base.get('acceptance_datetime'), base.get('filing_date') or ''
        )
        same_quarter = f'{filing_date.year}Q{((filing_date.month - 1) // 3) + 1}'
        same_manifest = next((row for row in passed_snapshots if row['quarter'] == same_quarter), None)
        prior1 = max(
            (row for row in passed_snapshots
             if row.get('conservative_available_from_1d')
             and date.fromisoformat(row['conservative_available_from_1d']) <= filing_date),
            key=lambda row: row['conservative_available_from_1d'],
            default=None,
        )
        prior5 = max(
            (row for row in passed_snapshots
             if row.get('conservative_available_from_5d')
             and date.fromisoformat(row['conservative_available_from_5d']) <= filing_date),
            key=lambda row: row['conservative_available_from_5d'],
            default=None,
        )
        valid = base.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID' and bool(base.get('cusip'))
        match1 = match_lookup.get((base['accession'], prior1['quarter'])) if prior1 and valid else None
        match5 = match_lookup.get((base['accession'], prior5['quarter'])) if prior5 and valid else None
        same_match = match_lookup.get((base['accession'], same_quarter)) if same_manifest and valid else None
        run_date = prior5.get('run_date') if prior5 else None
        output.append({
            'accession': base['accession'],
            'family': base.get('family'),
            'filing_date': base.get('filing_date'),
            'acceptance_datetime': base.get('acceptance_datetime'),
            'acceptance_date_source': date_source,
            'sample_weight': float(base.get('sample_weight') or 0),
            'cusip_status': base.get('cusip_status'),
            'latest_prior_quarter_1d_proxy': prior1.get('quarter') if prior1 else None,
            'match_1d_proxy': match1,
            'latest_prior_quarter_5d_proxy': prior5.get('quarter') if prior5 else None,
            'match_5d_proxy': match5,
            'same_quarter_list_match_lookahead_diagnostic': same_match,
            'same_quarter_list_available': bool(same_manifest),
            'lookahead_only_match_vs_5d_proxy': bool(same_match is True and match5 is False),
            'days_from_prior_run_date_5d': (
                (filing_date - date.fromisoformat(run_date)).days if run_date else None
            ),
            'prior_list_source_sha256_5d': prior5.get('source_sha256') if prior5 else None,
        })
    return output


def aggregate(sample_csv: Path, input_dir: Path, output_dir: Path):
    sample = read_csv(sample_csv)
    manifest_rows = []
    match_rows = []
    for path in sorted(input_dir.rglob('phase165_snapshot_manifest_shard_*.csv')):
        manifest_rows.extend(read_csv(path))
    for path in sorted(input_dir.rglob('phase165_quarter_matches_shard_*.csv')):
        match_rows.extend(read_csv(path))
    if not manifest_rows:
        raise RuntimeError('No Phase 165 shard manifests found')
    by_quarter = {}
    for row in manifest_rows:
        quarter = row['quarter']
        if quarter in by_quarter and by_quarter[quarter].get('source_sha256') != row.get('source_sha256'):
            raise ValueError(f'conflicting source hashes for {quarter}')
        by_quarter[quarter] = row
    snapshots = list(by_quarter.values())
    passed = [row for row in snapshots if row.get('parse_status') == 'PASS']
    match_lookup = {}
    for row in match_rows:
        value = row.get('match_13f_list')
        if value in ('True', 'true', '1'):
            parsed = True
        elif value in ('False', 'false', '0'):
            parsed = False
        else:
            parsed = None
        match_lookup[(row['accession'], row['quarter'])] = parsed
    audit_rows = build_audit_rows(sample, passed, match_lookup)
    valid_rows = [row for row in audit_rows if row.get('cusip_status') == 'UNIQUE_CHECKSUM_VALID']
    prior5_rows = [row for row in valid_rows if row.get('latest_prior_quarter_5d_proxy')]
    prior1_rows = [row for row in valid_rows if row.get('latest_prior_quarter_1d_proxy')]
    same_rows = [row for row in valid_rows if row.get('same_quarter_list_available')]
    failures = [{'quarter': row['quarter'], 'errors': row.get('errors')} for row in snapshots if row.get('parse_status') != 'PASS']
    by_family = {}
    for family in sorted({row.get('family') for row in valid_rows if row.get('family')}):
        group = [row for row in prior5_rows if row.get('family') == family]
        by_family[family] = {
            'n_with_prior_list': len(group),
            'match_rate_5d_proxy': safe_rate(group, 'match_5d_proxy'),
            'weighted_match_rate_5d_proxy': safe_weighted_rate(group, 'match_5d_proxy'),
        }
    by_year = {}
    for year in sorted({int(row['filing_date'][:4]) for row in valid_rows if row.get('filing_date')}):
        group = [row for row in prior5_rows if int(row['filing_date'][:4]) == year]
        by_year[str(year)] = {
            'n_with_prior_list': len(group),
            'match_rate_5d_proxy': safe_rate(group, 'match_5d_proxy'),
            'weighted_match_rate_5d_proxy': safe_weighted_rate(group, 'match_5d_proxy'),
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / 'phase165_sec13f_snapshot_manifest.csv', MANIFEST_FIELDS, snapshots)
    write_csv(output_dir / 'phase165_sec13dg_13f_cusip_match_audit.csv', AUDIT_FIELDS, audit_rows)
    metadata_counts = {}
    for row in passed:
        basis = row.get('metadata_basis') or 'UNKNOWN'
        metadata_counts[basis] = metadata_counts.get(basis, 0) + 1
    summary = {
        'phase': 165,
        'status': 'PASS_SOURCE_COVERAGE_AUDIT' if len(passed) >= 40 else 'PARTIAL_SOURCE_COVERAGE_AUDIT',
        'source_phase124_run_id': PHASE124_RUN_ID,
        'source_phase127_run_id': PHASE127_RUN_ID,
        'source_phase127_artifact_digest': PHASE127_ARTIFACT_DIGEST,
        'quarter_snapshots_expected': EXPECTED_QUARTERS,
        'quarter_snapshots_observed': len(snapshots),
        'quarter_snapshots_passed': len(passed),
        'quarter_snapshots_failed': len(failures),
        'failed_quarters': failures,
        'valid_cusip_filings': len(valid_rows),
        'all_actual_filings': len(audit_rows),
        'filings_with_prior_list_1d_proxy': len(prior1_rows),
        'match_rate_1d_proxy': safe_rate(prior1_rows, 'match_1d_proxy'),
        'weighted_match_rate_1d_proxy': safe_weighted_rate(prior1_rows, 'match_1d_proxy'),
        'filings_with_prior_list_5d_proxy': len(prior5_rows),
        'match_rate_5d_proxy': safe_rate(prior5_rows, 'match_5d_proxy'),
        'weighted_match_rate_5d_proxy': safe_weighted_rate(prior5_rows, 'match_5d_proxy'),
        'same_quarter_lookahead_diagnostic_n': len(same_rows),
        'same_quarter_lookahead_match_rate': safe_rate(same_rows, 'same_quarter_list_match_lookahead_diagnostic'),
        'same_quarter_lookahead_only_matches': sum(bool(row.get('lookahead_only_match_vs_5d_proxy')) for row in same_rows),
        'match_rate_5d_proxy_by_family': by_family,
        'match_rate_5d_proxy_by_year': by_year,
        'metadata_basis_counts': metadata_counts,
        'run_date_present_snapshots': sum(bool(row.get('run_date')) for row in passed),
        'last_modified_present_snapshots': sum(bool(row.get('http_last_modified_utc')) for row in passed),
        'pit_status': 'CONSERVATIVE_PROXY_NOT_VERIFIED',
        'pit_limitation': 'PDF Run Date/Time and HTTP Last-Modified are generation/retrieval metadata, not verified first-publication timestamps. The +2/+6 calendar-day dates are sensitivity proxies only.',
        'scope_limitation': 'The Section 13(f) list covers only 13F-reportable securities; a no-match is not proof that a CUSIP is invalid or not tradable.',
        'redistribution_control': 'Raw SEC 13(f) list rows, CUSIPs sourced from those lists, issuer names and descriptions are not included in the artifact. Outputs retain only source hashes/metadata and match booleans against CUSIPs already present in SEC 13D/G filings.',
        'checkpointing': True,
        'parallel_shards': 9,
        'max_parallel_shards': 3,
        'no_alpha_test': True,
        'no_vendor_purchase': True,
        'f80_baseline_frozen': True,
    }
    (output_dir / 'phase165_sec13f_resumable_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['prepare', 'shard', 'aggregate'], required=True)
    parser.add_argument('--phase124-dir', type=Path)
    parser.add_argument('--phase127-dir', type=Path)
    parser.add_argument('--sample-csv', type=Path)
    parser.add_argument('--shard-index', type=int)
    parser.add_argument('--shard-count', type=int, default=9)
    parser.add_argument('--input-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        if not args.phase124_dir or not args.phase127_dir:
            parser.error('prepare mode requires --phase124-dir and --phase127-dir')
        prepare_sample(args.phase124_dir, args.phase127_dir, args.output_dir)
    elif args.mode == 'shard':
        if args.sample_csv is None or args.shard_index is None:
            parser.error('shard mode requires --sample-csv and --shard-index')
        run_shard(args.sample_csv, args.shard_index, args.shard_count, args.output_dir)
    else:
        if args.sample_csv is None or args.input_dir is None:
            parser.error('aggregate mode requires --sample-csv and --input-dir')
        result = aggregate(args.sample_csv, args.input_dir, args.output_dir)
        if result['quarter_snapshots_passed'] < 40:
            raise SystemExit(2)


if __name__ == '__main__':
    main()
