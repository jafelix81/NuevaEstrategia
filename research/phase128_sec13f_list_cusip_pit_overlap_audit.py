#!/usr/bin/env python3
"""Phase 128: SEC 13(f) official-list CUSIP overlap and conservative PIT feasibility audit.

Raw SEC 13(f) lists contain licensed CUSIP Global Services data. This script never
writes raw list rows, issuer names or descriptions to the repository artifact. It
stores only source hashes/metadata, CUSIPs already present in public 13D/G filings,
and derived match booleans/counts.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, subprocess, tempfile, time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research.phase125_sec_13dg_exact_cusip_audit import cusip_check_digit

PHASE124_RUN_ID = 42073725379
PHASE124_ARTIFACT_ID = 13436764625
PHASE127_RUN_ID = 42079517644
PHASE127_ARTIFACT_ID = 13438903901
PHASE127_ARTIFACT_DIGEST = "sha256:b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166"
USER_AGENT = "OpenAI ChatGPT Smart Money Research audit (research-only)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/pdf,text/plain,*/*", "Accept-Encoding": "gzip, deflate"}


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_cusip_line(line: str):
    line = line.rstrip("\r\n")
    m = re.match(r"^\s*([A-Z0-9]{6})\s+([A-Z0-9]{2})\s+([0-9])\s*\*?(?:\s+|$)", line, flags=re.I)
    if m:
        return (m.group(1) + m.group(2) + m.group(3)).upper()
    m = re.match(r"^\s*([A-Z0-9]{9})\*?(?:\s+|$)", line, flags=re.I)
    if m:
        return m.group(1).upper()
    return None


def parse_run_metadata(text: str):
    date_match = re.search(r"Run\s+Date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})", text, flags=re.I)
    time_match = re.search(r"Run\s+Time\s*:?\s*(\d{1,2}:\d{2}(?::\d{2})?)", text, flags=re.I)
    run_date = datetime.strptime(date_match.group(1), "%m/%d/%Y").date() if date_match else None
    run_time = time_match.group(1) if time_match else None
    q_match = re.search(r"Year\s*:?\s*(\d{4}).{0,20}?Qtr\s*:?\s*([1-4])", text, flags=re.I | re.S)
    stated_quarter = f"{q_match.group(1)}Q{q_match.group(2)}" if q_match else None
    return run_date, run_time, stated_quarter


def is_valid_cusip(value: str):
    return bool(value and len(value) == 9 and value[-1].isdigit()
                and cusip_check_digit(value[:8]) == value[-1])


def quarter_iter(start_year=2015, start_quarter=3, end_year=2026, end_quarter=3):
    y, q = start_year, start_quarter
    while (y, q) <= (end_year, end_quarter):
        yield y, q
        if q == 4:
            y, q = y + 1, 1
        else:
            q += 1


def add_calendar_days(base: date, n: int):
    return base + timedelta(days=n)


def candidate_urls(year, quarter):
    stem = f"13flist{year}q{quarter}"
    if (year, quarter) >= (2025, 4):
        yield f"https://www.sec.gov/files/investment/{stem}.txt", "txt"
        yield f"https://www.sec.gov/files/investment/{stem}.pdf", "pdf"
    yield f"https://www.sec.gov/divisions/investment/13f/{stem}.pdf", "pdf"
    yield f"https://www.sec.gov/files/investment/{stem}.pdf", "pdf"
    yield f"https://www.sec.gov/file/{stem}", "auto"
    yield f"https://www.sec.gov/file/{stem}pdf", "auto"


def download_bytes(url, retries=4):
    last_error = None
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=45) as response:
                raw = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
                final_url = response.geturl()
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                return raw, headers, final_url
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = str(exc)
            if isinstance(exc, HTTPError) and exc.code not in {403, 404, 408, 429, 500, 502, 503, 504}:
                break
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(last_error or "download failed")


def parse_pdf(raw: bytes, temp_dir: Path):
    pdf_path = temp_dir / "list.pdf"
    txt_path = temp_dir / "list.txt"
    pdf_path.write_bytes(raw)
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
        capture_output=True, text=True, timeout=120
    )
    if proc.returncode != 0 or not txt_path.is_file():
        raise RuntimeError(f"pdftotext failed: {proc.stderr[-1000:]}")
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    run_date, run_time, stated_quarter = parse_run_metadata(text)
    cusips = [x for line in text.splitlines() if (x := parse_cusip_line(line))]
    return text, run_date, run_time, stated_quarter, cusips


def parse_txt(raw: bytes):
    text = raw.decode("utf-8-sig", errors="replace")
    run_date, run_time, stated_quarter = parse_run_metadata(text)
    cusips = [x for line in text.splitlines() if (x := parse_cusip_line(line))]
    if len(cusips) < 1000:
        # Some SEC fixed-width text files place CUSIP in columns 1-9.
        for line in text.splitlines():
            candidate = line[:9].strip().upper()
            if re.fullmatch(r"[A-Z0-9]{9}", candidate) and candidate not in cusips:
                cusips.append(candidate)
    return text, run_date, run_time, stated_quarter, cusips


def parse_last_modified(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def download_snapshot(year, quarter, temp_dir):
    errors = []
    for url, preferred_format in candidate_urls(year, quarter):
        try:
            raw, headers, final_url = download_bytes(url)
            if raw.startswith(b"%PDF"):
                fmt = "pdf"
                parsed = parse_pdf(raw, temp_dir)
            else:
                sample = raw[:500].lstrip().lower()
                if b"<html" in sample or b"<!doctype" in sample:
                    errors.append({"url": url, "error": "HTML response, not a list file"})
                    continue
                fmt = "txt"
                parsed = parse_txt(raw)
            text, run_date, run_time, stated_quarter, cusips = parsed
            if len(cusips) < 1000:
                errors.append({"url": url, "error": f"too few parsed CUSIP rows: {len(cusips)}"})
                continue
            if not run_date:
                errors.append({"url": url, "error": "Run Date missing"})
                continue
            expected = f"{year}Q{quarter}"
            if stated_quarter and stated_quarter != expected:
                errors.append({"url": url, "error": f"stated quarter {stated_quarter} != {expected}"})
                continue
            unique = set(cusips)
            valid = {x for x in unique if is_valid_cusip(x)}
            invalid = unique - valid
            lm = parse_last_modified(headers.get("last-modified"))
            base_date = max(run_date, lm.date()) if lm else run_date
            # The SEC says lists are posted shortly after quarter-end. The PDF Run Date
            # is a generation timestamp, not a verified public-release timestamp. Use
            # +1 and +5 calendar-day buffers as conservative sensitivity proxies.
            available_1d = add_calendar_days(base_date, 2)
            available_5d = add_calendar_days(base_date, 6)
            manifest = {
                "quarter": expected, "format": fmt, "source_url": final_url,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "http_last_modified_utc": lm.isoformat() if lm else None,
                "http_etag": headers.get("etag"), "http_date": headers.get("date"),
                "content_length_header": headers.get("content-length"),
                "run_date": run_date.isoformat(), "run_time_local_unspecified": run_time,
                "stated_quarter": stated_quarter, "last_modified_present": bool(lm),
                "conservative_available_from_1d": available_1d.isoformat(),
                "conservative_available_from_5d": available_5d.isoformat(),
                "parsed_rows": len(cusips), "unique_cusips": len(unique),
                "checksum_valid_unique_cusips": len(valid), "invalid_unique_cusips": len(invalid),
                "duplicate_rows": len(cusips) - len(unique),
                "parse_status": "PASS",
            }
            return manifest, unique, errors
        except Exception as exc:
            errors.append({"url": url, "error": str(exc)[:500]})
        time.sleep(0.25)
    return {
        "quarter": f"{year}Q{quarter}", "parse_status": "FAILED",
        "errors": errors,
    }, set(), errors


def parse_acceptance_date(value, fallback):
    if value:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text).date(), "ACCEPTANCE_DATETIME"
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(text, fmt).date(), "ACCEPTANCE_DATETIME"
                except ValueError:
                    pass
    return datetime.strptime(fallback, "%Y-%m-%d").date(), "FILING_DATE_FALLBACK"


def select_latest(snapshots, filing_date, available_field):
    eligible = [s for s in snapshots if s.get(available_field) and date.fromisoformat(s[available_field]) <= filing_date]
    return max(eligible, key=lambda x: x[available_field]) if eligible else None


def audit(phase124_dir: Path, phase127_dir: Path, output_dir: Path):
    s124 = json.loads((phase124_dir / "phase124_global_13dg_summary.json").read_text(encoding="utf-8"))
    s127 = json.loads((phase127_dir / "phase127_sec_13dg_cusip_summary.json").read_text(encoding="utf-8"))
    rows124 = read_csv(phase124_dir / "phase124_global_13dg_submission_audit.csv")
    rows127 = read_csv(phase127_dir / "phase127_sec_13dg_xml_cusip_audit.csv")
    if len(rows124) != 600 or len(rows127) != 599:
        raise ValueError("Phase 124/127 artifact row counts mismatch")
    if s124.get("source_phase124_run_id") not in (None, PHASE124_RUN_ID):
        raise ValueError("Unexpected Phase 124 source run")
    if s127.get("source_phase124_run_id") != PHASE124_RUN_ID or not str(s127.get("status", "")).startswith("PASS"):
        raise ValueError("Phase 127 artifact provenance/status mismatch")
    rows124_by = {r["accession"]: r for r in rows124}
    sample = []
    for r in rows127:
        base = rows124_by.get(r["accession"])
        if base is None or base.get("raw_sha256") != r.get("raw_sha256"):
            raise ValueError(f"Phase 124/127 raw hash join mismatch for {r['accession']}")
        if r.get("cusip_status") == "UNIQUE_CHECKSUM_VALID":
            sample.append({
                "accession": r["accession"], "family": base.get("family"),
                "filing_date": base.get("filing_date_index"),
                "acceptance_datetime": base.get("acceptance_datetime"),
                "sample_weight": float(base.get("sample_weight") or 0),
                "cusip": r.get("cusip"), "cusip_status": r.get("cusip_status"),
            })

    snapshots, snapshot_sets, failures = [], {}, []
    with tempfile.TemporaryDirectory(prefix="phase128_13f_") as tmp:
        temp_dir = Path(tmp)
        for year, quarter in quarter_iter():
            manifest, cusips, errors = download_snapshot(year, quarter, temp_dir)
            snapshots.append(manifest)
            if manifest.get("parse_status") == "PASS":
                snapshot_sets[manifest["quarter"]] = cusips
            else:
                failures.append({"quarter": manifest["quarter"], "errors": errors})
            time.sleep(0.25)

    passed = [s for s in snapshots if s.get("parse_status") == "PASS"]
    if not passed:
        raise RuntimeError("No SEC 13(f) list snapshots downloaded and parsed")
    audit_rows = []
    same_quarter_available = 0
    for row in rows127:
        base = rows124_by[row["accession"]]
        filing_date, date_source = parse_acceptance_date(base.get("acceptance_datetime"), base["filing_date_index"])
        cusip = row.get("cusip") if row.get("cusip_status") == "UNIQUE_CHECKSUM_VALID" else None
        same_q = f"{filing_date.year}Q{((filing_date.month - 1) // 3) + 1}"
        same_manifest = next((s for s in passed if s["quarter"] == same_q), None)
        if same_manifest:
            same_quarter_available += 1
        prior1 = select_latest(passed, filing_date, "conservative_available_from_1d")
        prior5 = select_latest(passed, filing_date, "conservative_available_from_5d")
        match1 = bool(cusip and prior1 and cusip in snapshot_sets[prior1["quarter"]])
        match5 = bool(cusip and prior5 and cusip in snapshot_sets[prior5["quarter"]])
        same_match = bool(cusip and same_manifest and cusip in snapshot_sets[same_q])
        audit_rows.append({
            "accession": row["accession"], "family": base.get("family"),
            "filing_date": base.get("filing_date_index"), "acceptance_datetime": base.get("acceptance_datetime"),
            "acceptance_date_source": date_source, "sample_weight": float(base.get("sample_weight") or 0),
            "cusip": cusip, "cusip_status": row.get("cusip_status"),
            "latest_prior_quarter_1d_proxy": prior1["quarter"] if prior1 else None,
            "match_1d_proxy": match1,
            "latest_prior_quarter_5d_proxy": prior5["quarter"] if prior5 else None,
            "match_5d_proxy": match5,
            "same_quarter_list_match_lookahead_diagnostic": same_match,
            "same_quarter_list_available": bool(same_manifest),
            "lookahead_only_match_vs_5d_proxy": bool(same_match and not match5),
            "days_from_prior_run_date_5d": (
                (filing_date - date.fromisoformat(prior5["run_date"])).days if prior5 else None
            ),
            "prior_list_source_sha256_5d": prior5.get("source_sha256") if prior5 else None,
        })

    valid_rows = [r for r in audit_rows if r["cusip_status"] == "UNIQUE_CHECKSUM_VALID"]
    prior5_rows = [r for r in valid_rows if r["latest_prior_quarter_5d_proxy"]]
    prior1_rows = [r for r in valid_rows if r["latest_prior_quarter_1d_proxy"]]
    same_rows = [r for r in valid_rows if r["same_quarter_list_available"]]
    def rate(rows, field):
        return sum(bool(r[field]) for r in rows) / len(rows) if rows else None
    def weighted_rate(rows, field):
        denom = sum(r["sample_weight"] for r in rows)
        return sum(r["sample_weight"] for r in rows if r[field]) / denom if denom else None

    by_family = {}
    for family in sorted({r["family"] for r in valid_rows}):
        group = [r for r in prior5_rows if r["family"] == family]
        by_family[family] = {"n_with_prior_list": len(group), "match_rate_5d_proxy": rate(group, "match_5d_proxy"),
                             "weighted_match_rate_5d_proxy": weighted_rate(group, "match_5d_proxy")}
    by_year = {}
    for year in sorted({int(r["filing_date"][:4]) for r in valid_rows if r.get("filing_date")}):
        group = [r for r in prior5_rows if int(r["filing_date"][:4]) == year]
        by_year[str(year)] = {"n_with_prior_list": len(group), "match_rate_5d_proxy": rate(group, "match_5d_proxy"),
                              "weighted_match_rate_5d_proxy": weighted_rate(group, "match_5d_proxy")}

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "phase128_sec13f_list_snapshot_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        fields = sorted({k for row in snapshots for k in row})
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(snapshots)
    with (output_dir / "phase128_sec13dg_13f_cusip_match_audit.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(audit_rows)

    summary = {
        "phase": "128-sec-13f-official-list-cusip-pit-overlap-audit",
        "status": "PASS_SOURCE_COVERAGE_AUDIT" if len(passed) >= 40 else "PARTIAL_SOURCE_COVERAGE_AUDIT",
        "source_phase124_run_id": PHASE124_RUN_ID, "source_phase124_artifact_id": PHASE124_ARTIFACT_ID,
        "source_phase127_run_id": PHASE127_RUN_ID, "source_phase127_artifact_id": PHASE127_ARTIFACT_ID,
        "source_phase127_artifact_digest": PHASE127_ARTIFACT_DIGEST,
        "quarter_snapshots_expected": len(snapshots), "quarter_snapshots_passed": len(passed),
        "quarter_snapshots_failed": len(failures), "failed_quarters": failures,
        "valid_cusip_filings": len(valid_rows), "all_actual_filings": len(audit_rows),
        "filings_with_prior_list_1d_proxy": len(prior1_rows), "match_rate_1d_proxy": rate(prior1_rows, "match_1d_proxy"),
        "weighted_match_rate_1d_proxy": weighted_rate(prior1_rows, "match_1d_proxy"),
        "filings_with_prior_list_5d_proxy": len(prior5_rows), "match_rate_5d_proxy": rate(prior5_rows, "match_5d_proxy"),
        "weighted_match_rate_5d_proxy": weighted_rate(prior5_rows, "match_5d_proxy"),
        "same_quarter_lookahead_diagnostic_n": len(same_rows),
        "same_quarter_lookahead_match_rate": rate(same_rows, "same_quarter_list_match_lookahead_diagnostic"),
        "same_quarter_lookahead_only_matches": sum(r["lookahead_only_match_vs_5d_proxy"] for r in same_rows),
        "match_rate_5d_proxy_by_family": by_family, "match_rate_5d_proxy_by_year": by_year,
        "last_modified_header_present_snapshots": sum(bool(s.get("http_last_modified_utc")) for s in passed),
        "run_date_present_snapshots": sum(bool(s.get("run_date")) for s in passed),
        "pit_status": "CONSERVATIVE_PROXY_NOT_VERIFIED",
        "pit_limitation": "PDF Run Date/Time is a generation timestamp, not a verified public-release timestamp. The 1- and 5-calendar-day buffers are sensitivity proxies; exact public availability must be confirmed before using this list as a predictive feature.",
        "scope_limitation": "SEC 13(f) list covers only 13F-reportable securities; a no-match is not proof that a CUSIP is invalid or not tradable.",
        "redistribution_control": "Raw SEC 13(f) list rows, CUSIPs sourced from the list, issuer names and descriptions are not included in the artifact. Only source hashes/metadata and match booleans against CUSIPs already present in SEC 13D/G filings are retained.",
        "interpretation": "This is an identity-reference feasibility audit only, not an institutional-ownership signal or alpha test.",
        "no_alpha_test": True, "no_vendor_purchase": True, "f80_baseline_frozen": True,
    }
    (output_dir / "phase128_sec13f_list_cusip_overlap_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if len(passed) < 40:
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase124-dir", type=Path, required=True)
    parser.add_argument("--phase127-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audit(args.phase124_dir, args.phase127_dir, args.output_dir)


if __name__ == "__main__":
    main()
