#!/usr/bin/env python3
"""Global SEC Schedule 13D/13G index-to-subject identity feasibility audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, time
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
import requests
from research.phase73_sec_submission_text_extractor import _parse_sec_header, extract_primary_doc_xml, normalize_cik
from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml

SEC_BASE = "https://www.sec.gov"
USER_AGENT = "NuevaEstrategia research contact jafelix81@gmail.com"
FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
DEFAULT_QUARTERS = tuple(
    f"{y}Q{q}" for y, q in (
        [(2023, 2), (2023, 3), (2023, 4)]
        + [(y, q) for y in (2024, 2025) for q in (1, 2, 3, 4)]
        + [(2026, 1), (2026, 2), (2026, 3)]
    )
)


def normalize_form(value):
    form = re.sub(r"\s+", " ", str(value or "").strip().upper())
    form = form.replace("SCHEDULE 13D", "SC 13D").replace("SCHEDULE 13G", "SC 13G")
    form = re.sub(r"^SC\s*13([DG])\s*/\s*A$", r"SC 13\1/A", form)
    return re.sub(r"^SC\s*13([DG])$", r"SC 13\1", form)


def normalize_accession(value):
    raw = re.sub(r"\D", "", str(value or ""))
    return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}" if len(raw) == 18 else ""


def quarter_parts(value):
    m = re.fullmatch(r"(20\d{2})Q([1-4])", str(value).strip().upper())
    if not m:
        raise ValueError(f"Invalid quarter: {value}")
    return int(m.group(1)), int(m.group(2))


def parse_master_index_13dg(raw, quarter=""):
    text = raw.decode("latin-1", "replace") if isinstance(raw, bytes) else str(raw or "")
    lines = text.lstrip("\ufeff").splitlines()
    hi = next((i for i, line in enumerate(lines)
               if line.strip().lower().startswith("cik|company name|form type|date filed|filename")), None)
    if hi is None:
        raise ValueError("SEC master.idx header not found")
    grouped, malformed = {}, 0
    for line in lines[hi + 1:]:
        if not line.strip() or line.startswith("---"):
            continue
        p = line.split("|", 4)
        if len(p) != 5:
            malformed += 1
            continue
        cik_raw, company, raw_form, filed, filename = [x.strip() for x in p]
        form = normalize_form(raw_form)
        if form not in FORMS:
            continue
        m = re.search(r"(\d{10}-\d{2}-\d{6})\.txt$", filename, re.I)
        if m:
            accession = m.group(1)
        else:
            k = re.search(r"/(\d{18})/[^/]+$", filename)
            accession = normalize_accession(k.group(1)) if k else ""
        if not accession:
            malformed += 1
            continue
        cik = normalize_cik(cik_raw)
        pm = re.search(r"/data/(\d+)/", filename, re.I)
        path_cik = normalize_cik(pm.group(1)) if pm else ""
        row = grouped.setdefault(accession, {
            "accession": accession, "quarter": quarter, "master_index_ciks": set(),
            "master_index_names": {}, "archive_path_ciks": set(), "forms": set(),
            "filing_dates": set(), "filenames": set(), "raw_rows": 0,
        })
        if cik:
            row["master_index_ciks"].add(cik)
            row["master_index_names"][cik] = company
        if path_cik:
            row["archive_path_ciks"].add(path_cik)
        row["forms"].add(form)
        row["filing_dates"].add(filed)
        row["filenames"].add(filename)
        row["raw_rows"] += 1
    out = []
    for accession, row in grouped.items():
        forms, dates = sorted(row["forms"]), sorted(row["filing_dates"])
        master, path = sorted(row["master_index_ciks"]), sorted(row["archive_path_ciks"])
        out.append({
            "accession": accession, "quarter": quarter,
            "form": forms[0] if len(forms) == 1 else "",
            "form_family": "13D" if forms and "13D" in forms[0] else ("13G" if forms else ""),
            "is_amendment": bool(forms and forms[0].endswith("/A")),
            "filing_date": dates[0] if len(dates) == 1 else "",
            "master_index_ciks": master, "master_index_names": row["master_index_names"],
            "archive_path_ciks": path, "candidate_identity_ciks": sorted(set(master) | set(path)),
            "filenames": sorted(row["filenames"]), "raw_rows": row["raw_rows"],
            "metadata_conflict": len(forms) != 1 or len(dates) != 1 or len(path) != 1,
            "malformed_rows_in_quarter": malformed,
        })
    return sorted(out, key=lambda r: (r["filing_date"], r["accession"]))


def candidate_evidence(row, target_ciks):
    master, path = set(row.get("master_index_ciks") or []), set(row.get("archive_path_ciks") or [])
    mh, ph, hits = sorted(master & target_ciks), sorted(path & target_ciks), sorted((master | path) & target_ciks)
    return {"master_candidate_ciks": mh, "path_candidate_ciks": ph, "all_candidate_ciks": hits,
            "candidate_class": "control" if not hits else ("unique_candidate" if len(hits) == 1 else "ambiguous")}


def timing_regime(family, date):
    d = str(date or "")
    if family == "13D":
        if d < "2024-02-05": return "13d_legacy_deadline"
        if d < "2024-12-18": return "13d_revised_deadline_pre_xml"
        return "13d_mandatory_xml"
    if d < "2024-09-30": return "13g_legacy_deadline"
    if d < "2024-12-18": return "13g_revised_deadline_pre_xml"
    return "13g_mandatory_xml"


def stable_key(row, stratum=""):
    return hashlib.sha256(f"{row.get('accession','')}|{stratum}".encode()).hexdigest()


def stratified_sample(rows, target_ciks, limit=120):
    strata = defaultdict(list)
    for row in rows:
        ev = candidate_evidence(row, target_ciks)
        key = (row.get("form_family", ""), bool(row.get("is_amendment")),
               timing_regime(row.get("form_family", ""), row.get("filing_date", "")),
               ev["candidate_class"])
        item = dict(row, **ev)
        item["timing_regime"], item["sample_stratum"] = key[2], "|".join(map(str, key))
        strata[key].append(item)
    ordered = {k: sorted(v, key=lambda r: stable_key(r, r["sample_stratum"]))
               for k, v in sorted(strata.items(), key=lambda kv: str(kv[0]))}
    selected, offsets = [], {k: 0 for k in ordered}
    while len(selected) < limit:
        progressed = False
        for key, values in ordered.items():
            pos = offsets[key]
            if pos < len(values) and len(selected) < limit:
                selected.append(values[pos]); offsets[key] += 1; progressed = True
        if not progressed: break
    return selected


def complete_submission_url(archive_cik, accession):
    key = normalize_accession(accession)
    cik = normalize_cik(archive_cik)
    if not key: raise ValueError(f"Invalid accession: {accession}")
    if not cik: raise ValueError(f"Invalid archive CIK: {archive_cik}")
    return f"{SEC_BASE}/Archives/edgar/data/{int(cik)}/{key.replace('-', '')}/{key}.txt"


def submission_url_candidates(row):
    accession = row.get("accession", "")
    path_ciks = sorted(set(row.get("archive_path_ciks") or []))
    if len(path_ciks) != 1:
        raise ValueError("archive path CIK is missing or non-unique; quarantine accession")
    cik = normalize_cik(path_ciks[0])
    return [(cik, complete_submission_url(cik, accession))]


def classify_candidate_role(row, header):
    subject, filer = normalize_cik(header.get("subject_cik", "")), normalize_cik(header.get("filer_cik", ""))
    candidates = sorted(set(row.get("all_candidate_ciks") or []))
    subject_hits = [c for c in candidates if c == subject]
    filer_hits = [c for c in candidates if c == filer]
    unresolved_hits = [c for c in candidates if c not in {subject, filer}]
    if len(subject_hits) == 1:
        candidate, role = subject_hits[0], "subject"
    elif len(subject_hits) > 1:
        candidate, role = "", "ambiguous_subject"
    elif filer_hits:
        candidate, role = ";".join(filer_hits), "filer"
    elif candidates:
        candidate, role = "", "unresolved"
    else:
        candidate, role = "", "none"
    master, path = set(row.get("master_index_ciks") or []), set(row.get("archive_path_ciks") or [])
    return {
        "subject_cik": subject, "filer_cik": filer,
        "subject_in_master_index_ciks": bool(subject and subject in master),
        "filer_in_master_index_ciks": bool(filer and filer in master),
        "subject_in_archive_path_ciks": bool(subject and subject in path),
        "filer_in_archive_path_ciks": bool(filer and filer in path),
        "candidate_cik": candidate, "candidate_role": role,
        "subject_candidate_ciks": subject_hits, "filer_candidate_ciks": filer_hits,
        "unresolved_candidate_ciks": unresolved_hits,
    }


def parse_pilot_record(row, raw):
    header = _parse_sec_header(raw.decode("utf-8-sig", errors="replace"))
    accession, expected = normalize_accession(header.get("accession", "")), normalize_accession(row.get("accession", ""))
    form, date = normalize_form(header.get("form", "")), header.get("filing_date", "")
    result = {
        "accession": expected, "header_accession": accession, "accession_match": bool(accession and accession == expected),
        "master_index_form": normalize_form(row.get("form", "")), "header_form": form,
        "form_match": bool(form and form == normalize_form(row.get("form", ""))),
        "master_index_filing_date": row.get("filing_date", ""), "header_filing_date": date,
        "filing_date_match": bool(date and date == row.get("filing_date", "")),
        "acceptance_datetime": header.get("acceptance_datetime", ""),
        "subject_name": header.get("subject_name", ""), "filer_name": header.get("filer_name", ""),
    }
    result.update(classify_candidate_role(row, header))
    try:
        extracted = extract_primary_doc_xml(raw)
        parsed = parse_schedule13_xml(extracted["xml_bytes"])
        result.update({
            "xml_present": True, "xml_subject_cik": normalize_cik(parsed.get("issuer_cik", "")),
            "xml_filer_cik": normalize_cik(parsed.get("filer_cik_xml", "")),
            "xml_subject_matches_header": normalize_cik(parsed.get("issuer_cik", "")) == result["subject_cik"],
            "xml_filer_matches_header": normalize_cik(parsed.get("filer_cik_xml", "")) == result["filer_cik"],
            "xml_form_matches_header": normalize_form(parsed.get("submission_type", "")) == form,
        })
    except Exception:
        result.update({"xml_present": False, "xml_subject_cik": "", "xml_filer_cik": "",
                       "xml_subject_matches_header": "", "xml_filer_matches_header": "",
                       "xml_form_matches_header": ""})
    return result


class SecClient:
    def __init__(self, sleep_seconds=0.6, max_retries=5, timeout=60):
        self.sleep_seconds, self.max_retries, self.timeout = sleep_seconds, max_retries, timeout
        self.last_request, self.request_count = 0.0, 0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate",
                                     "Accept": "text/plain,text/html,application/xml,*/*"})

    def get_response(self, url):
        last_error = None
        for attempt in range(self.max_retries + 1):
            delay = self.sleep_seconds - (time.monotonic() - self.last_request)
            if delay > 0: time.sleep(delay)
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, timeout=self.timeout)
                self.request_count += 1
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    try: wait = float(response.headers.get("Retry-After", ""))
                    except (TypeError, ValueError): wait = min(60.0, 2.0 ** attempt)
                    time.sleep(max(wait, self.sleep_seconds)); continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries: break
                time.sleep(min(60.0, 2.0 ** attempt))
        raise RuntimeError(f"SEC GET failed after retries: {url}: {last_error}")

    def get(self, url):
        return self.get_response(url).content


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                             if isinstance(v, (list, dict, set, tuple)) else v for k, v in row.items()})


def load_target_ciks(path):
    raw = path.read_text(encoding="utf-8-sig")
    if not raw.strip(): return set()
    if "ciks" in raw.splitlines()[0].lower() or "cik" in raw.splitlines()[0].lower():
        values = []
        for row in csv.DictReader(raw.splitlines()):
            values.extend(re.split(r"[;,|]", row.get("ciks") or row.get("cik") or ""))
    else:
        values = raw.splitlines()
    return {normalize_cik(v) for v in values if normalize_cik(v)}


def run_index_audit(quarters, target_ciks, outdir, mode="index-only", sample_limit=120, sleep_seconds=0.6):
    outdir.mkdir(parents=True, exist_ok=True)
    raw_index_dir = outdir / "raw_master_indexes"
    raw_index_dir.mkdir(parents=True, exist_ok=True)
    client, all_rows, quarter_rows, errors = SecClient(sleep_seconds), [], [], []
    for quarter in quarters:
        year, q = quarter_parts(quarter)
        url = f"{SEC_BASE}/Archives/edgar/full-index/{year}/QTR{q}/master.idx"
        try:
            response = client.get_response(url)
            retrieved_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
            raw = response.content
            raw_name = f"master_{quarter}.idx"
            (raw_index_dir / raw_name).write_bytes(raw)
            rows = parse_master_index_13dg(raw, quarter); all_rows.extend(rows)
            quarter_rows.append({
                "quarter": quarter, "url": url, "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(raw), "retrieved_at_utc": retrieved_at_utc,
                "raw_file": f"raw_master_indexes/{raw_name}",
                "accessions": len(rows),
                "original_13d": sum(r["form"] == "SC 13D" for r in rows),
                "amendment_13d": sum(r["form"] == "SC 13D/A" for r in rows),
                "original_13g": sum(r["form"] == "SC 13G" for r in rows),
                "amendment_13g": sum(r["form"] == "SC 13G/A" for r in rows),
                "unique_master_index_ciks": len({c for r in rows for c in r["master_index_ciks"]}),
                "unique_archive_path_ciks": len({c for r in rows for c in r["archive_path_ciks"]}),
                "duplicate_raw_rows": sum(max(0, r["raw_rows"] - 1) for r in rows),
                "metadata_conflicts": sum(bool(r["metadata_conflict"]) for r in rows),
                "sha256": hashlib.sha256(raw).hexdigest(),
            })
        except Exception as exc:
            errors.append({"quarter": quarter, "url": url, "error": repr(exc)})
    accessions = [r["accession"] for r in all_rows]
    duplicates = len(accessions) - len(set(accessions))
    evidence_rows = [{**r, **candidate_evidence(r, target_ciks),
                      "timing_regime": timing_regime(r["form_family"], r["filing_date"])} for r in all_rows]
    metadata_conflicts = [r for r in evidence_rows if r.get("metadata_conflict")]
    clean_rows = [r for r in all_rows if not r.get("metadata_conflict")]
    sample = stratified_sample(clean_rows, target_ciks, sample_limit)
    summary = {
        "phase": "74-global-13dg-subject-discovery-audit",
        "status": "COMPLETE" if not errors else "PARTIAL", "mode": mode,
        "quarters_requested": quarters, "quarters_retrieved": len(quarter_rows),
        "global_13dg_accessions": len(all_rows), "duplicate_accessions_across_quarters": duplicates,
        "index_metadata_conflicts_quarantined": len(metadata_conflicts),
        "clean_accessions_available_for_pilot": len(clean_rows),
        "unique_master_index_ciks": len({c for r in all_rows for c in r["master_index_ciks"]}),
        "unique_archive_path_ciks": len({c for r in all_rows for c in r["archive_path_ciks"]}),
        "target_cik_count": len(target_ciks),
        "candidate_accessions_any_identity": sum(bool(r["all_candidate_ciks"]) for r in evidence_rows),
        "candidate_accessions_unique_identity": sum(r["candidate_class"] == "unique_candidate" for r in evidence_rows),
        "candidate_accessions_ambiguous_identity": sum(r["candidate_class"] == "ambiguous" for r in evidence_rows),
        "candidate_accessions_control": sum(r["candidate_class"] == "control" for r in evidence_rows),
        "sample_rows": len(sample), "index_errors": errors, "request_count": client.request_count,
        "forward_returns_used": False, "economic_test_authorized": False,
        "subject_identity_rule": "Master-index CIK and archive-path CIK are candidates only; validate against SEC-HEADER SUBJECT COMPANY and FILED BY.",
        "limitations": [
            "Current CIK map is not historical F80 membership or a PIT security master.",
            "The master-index CIK column is not assumed to be the subject issuer.",
            "A filer CIK in the current universe is a false target match unless header/XML confirms subject role.",
            "Legacy HTML and structured XML are measured separately; XML is optional for legacy filings.",
            "13D/13G form families and regulatory deadline regimes remain separate.",
        ],
    }
    write_csv(outdir / "global_master_index_13dg.csv", all_rows)
    write_csv(outdir / "candidate_accessions.csv", evidence_rows)
    write_csv(outdir / "quarterly_counts.csv", quarter_rows)
    write_csv(outdir / "index_errors.csv", errors)
    write_csv(outdir / "index_metadata_conflicts_quarantined.csv", metadata_conflicts)
    write_csv(outdir / "pilot_manifest.csv", sample)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if mode == "pilot":
        if not target_ciks: raise ValueError("pilot mode requires a non-empty target CIK file")
        filing_rows, fetch_errors = [], []
        for row in sample:
            resolved = None
            path_errors = []
            for archive_cik, url in submission_url_candidates(row):
                try:
                    raw = client.get(url)
                    resolved = (archive_cik, url, raw)
                    break
                except Exception as path_exc:
                    path_errors.append({"archive_cik": archive_cik, "url": url, "error": repr(path_exc)})
            if resolved is None:
                fetch_errors.append({"accession": row["accession"], "path_errors": path_errors})
                continue
            archive_cik, url, raw = resolved
            filing_rows.append({
                **row, **parse_pilot_record(row, raw),
                "source_url": url, "resolved_archive_path_cik": archive_cik,
                "archive_path_attempt_errors_json": json.dumps(path_errors, sort_keys=True),
            })
        n = len(filing_rows)
        rate = lambda key: sum(bool(r[key]) for r in filing_rows) / n if n else 0.0
        xml_rows = [r for r in filing_rows if r.get("xml_present")]
        candidate_rows = [r for r in filing_rows if r.get("candidate_class") == "unique_candidate"]
        subject_role = (sum(r["candidate_role"] == "subject" for r in candidate_rows) / len(candidate_rows)
                        if candidate_rows else None)
        xml_subject = (sum(bool(r["xml_subject_matches_header"]) for r in xml_rows) / len(xml_rows) if xml_rows else None)
        xml_filer = (sum(bool(r["xml_filer_matches_header"]) for r in xml_rows) / len(xml_rows) if xml_rows else None)
        pilot = {
            "sample_rows": len(sample), "parsed_headers": n, "fetch_or_parse_errors": len(fetch_errors),
            "header_parse_rate": n / len(sample) if sample else 0.0,
            "accession_concordance": rate("accession_match"), "form_concordance": rate("form_match"),
            "filing_date_concordance": rate("filing_date_match"),
            "subject_cik_presence": sum(bool(r["subject_cik"]) for r in filing_rows) / n if n else 0.0,
            "filer_cik_presence": sum(bool(r["filer_cik"]) for r in filing_rows) / n if n else 0.0,
            "subject_cik_in_master_or_path_rate": sum(bool(r["subject_in_master_index_ciks"] or r["subject_in_archive_path_ciks"]) for r in filing_rows) / n if n else 0.0,
            "xml_rows": len(xml_rows), "xml_subject_header_concordance": xml_subject, "xml_filer_header_concordance": xml_filer,
            "unique_candidate_rows": len(candidate_rows), "unique_candidate_subject_role_rate": subject_role,
            "candidate_filer_false_positives": sum(r["candidate_role"] == "filer" for r in candidate_rows),
            "candidate_unresolved_rows": sum(r["candidate_role"] == "unresolved" for r in candidate_rows),
            "gate_checks": {
                "header_parse_ge_99_5pct": (n / len(sample) if sample else 0.0) >= 0.995,
                "accession_form_date_concordance_ge_99_5pct": min(rate("accession_match"), rate("form_match"), rate("filing_date_match")) >= 0.995,
                "subject_and_filer_cik_presence_ge_99_5pct": min(
                    sum(bool(r["subject_cik"]) for r in filing_rows) / n if n else 0.0,
                    sum(bool(r["filer_cik"]) for r in filing_rows) / n if n else 0.0) >= 0.995,
                "subject_cik_present_in_master_or_path_ge_99_5pct": (sum(bool(r["subject_in_master_index_ciks"] or r["subject_in_archive_path_ciks"]) for r in filing_rows) / n if n else 0.0) >= 0.995,
                "xml_crosscheck_ge_99_5pct_when_xml_present": bool(xml_rows) and min(xml_subject or 0, xml_filer or 0) >= 0.995,
                "unique_candidate_ciks_are_subjects_ge_99_5pct": subject_role is not None and subject_role >= 0.995,
            },
            "limitations": ["Pilot validates discovery/identity mechanics, not full target coverage.",
                            "Current target CIKs are not historical security lineage.", "No returns or alpha inference."],
        }
        pilot["data_gate"] = "PASS" if all(pilot["gate_checks"].values()) else "FAIL"
        write_csv(outdir / "pilot_header_validation.csv", filing_rows)
        write_csv(outdir / "pilot_errors.csv", fetch_errors)
        (outdir / "pilot_summary.json").write_text(json.dumps(pilot, indent=2) + "\n", encoding="utf-8")
        summary["pilot_summary"] = pilot
        (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(pilot, indent=2), flush=True)
    if errors or duplicates: raise SystemExit(2)
    if mode == "pilot" and summary["pilot_summary"]["data_gate"] != "PASS": raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarters", default=",".join(DEFAULT_QUARTERS))
    parser.add_argument("--target-cik-file", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("phase74_global_13dg_subject_audit"))
    parser.add_argument("--mode", choices=("index-only", "pilot"), default="index-only")
    parser.add_argument("--sample-limit", type=int, default=120)
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    args = parser.parse_args()
    target = load_target_ciks(args.target_cik_file) if args.target_cik_file else set()
    run_index_audit([q.strip() for q in args.quarters.split(",") if q.strip()], target,
                    args.outdir, args.mode, args.sample_limit, args.sleep_seconds)


if __name__ == "__main__":
    main()
