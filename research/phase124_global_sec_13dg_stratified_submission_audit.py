#!/usr/bin/env python3
"""Global stratified SEC 13D/13G sample and role/security feasibility audit.

Samples all 2016Q1-2026Q3 global master-index 13D/G accessions, excluding
immutable prior pilot/predecessor accessions. Downloads only the selected 600.
No returns, features, alpha tests, or production changes.
"""
from __future__ import annotations
import argparse, csv, hashlib, heapq, json, time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from research.phase120_sec_13dg_predecessor_content_audit import (
    choose_mirror, fetch_url, form_family, norm_cik, parse_submission, tag_values, xml_root
)

SAMPLE_N = 600
USER_AGENT = "jafelix81 research contact jafelix@gmail.com"
MANDATORY_XML_DATE = "2024-12-18"
SALT = "phase124-global-13dg-v1|"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def parse_json_list(value):
    try:
        out = json.loads(value or "[]")
        return out if isinstance(out, list) else []
    except Exception:
        return []

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sample_hash(accession):
    return hashlib.sha256((SALT + accession).encode("utf-8")).hexdigest()

def allocate_strata(counts, target=SAMPLE_N, minimum=2):
    if target > sum(counts.values()):
        raise ValueError("sample target exceeds eligible population")
    base = {k: min(minimum, n) for k, n in counts.items()}
    if sum(base.values()) > target:
        raise ValueError("minimum per stratum exceeds sample target")
    residual = {k: max(0, n - base[k]) for k, n in counts.items()}
    remaining = target - sum(base.values())
    denom = sum(residual.values())
    raw = {k: (remaining * residual[k] / denom if denom else 0.0) for k in counts}
    allocation = {k: base[k] + int(raw[k]) for k in counts}
    left = target - sum(allocation.values())
    order = sorted(
        counts,
        key=lambda k: (raw[k] - int(raw[k]), counts[k], k),
        reverse=True
    )
    for key in order[:left]:
        allocation[key] += 1
    if sum(allocation.values()) != target or any(allocation[k] > counts[k] for k in counts):
        raise AssertionError("invalid stratified allocation")
    return allocation

def exclusion_set(phase82_dir, phase84_dir, phase120_dir):
    excluded = set()
    p82 = phase82_dir / "pilot_manifest.csv"
    p84 = phase84_dir / "pilot_header_validation.csv"
    p120 = phase120_dir / "phase120_predecessor_audit.csv"
    for row in read_csv(p82):
        if row.get("accession"):
            excluded.add(row["accession"])
    for row in read_csv(p84):
        if row.get("accession"):
            excluded.add(row["accession"])
    for row in read_csv(p120):
        for key in ("current_accession", "previous_accession"):
            if row.get(key):
                excluded.add(row[key])
    return excluded

def build_sample(index_path, excluded):
    counts = Counter()
    index_rows = 0
    unique_accessions = set()
    with index_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            index_rows += 1
            acc = row["accession"]
            if acc in unique_accessions:
                raise ValueError(f"duplicate accession in Phase 82 global index: {acc}")
            unique_accessions.add(acc)
            if acc in excluded:
                continue
            key = (row["quarter"], row["form_family"], str(row["is_amendment"]).lower())
            counts[key] += 1
    if index_rows != 324964 or len(unique_accessions) != 324964 or len(counts) != 172:
        raise ValueError(f"unexpected Phase 82 index dimensions: rows={index_rows}, strata={len(counts)}")
    allocation = allocate_strata(counts)
    heaps = {k: [] for k in counts}
    with index_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            acc = row["accession"]
            if acc in excluded:
                continue
            key = (row["quarter"], row["form_family"], str(row["is_amendment"]).lower())
            h = int(sample_hash(acc), 16)
            item = (-h, acc, row)
            heap = heaps[key]
            if len(heap) < allocation[key]:
                heapq.heappush(heap, item)
            elif item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)
    sample = []
    for key, heap in heaps.items():
        n = allocation[key]
        for neg_hash, acc, row in heap:
            row = dict(row)
            row.update({
                "sample_hash": sample_hash(acc),
                "stratum_population_n": counts[key],
                "stratum_sample_n": n,
                "sample_weight": counts[key] / n,
                "sample_stratum": "|".join(key),
            })
            sample.append(row)
    sample.sort(key=lambda r: (r["quarter"], r["form_family"], str(r["is_amendment"]), r["sample_hash"]))
    if len(sample) != SAMPLE_N or len({r["accession"] for r in sample}) != SAMPLE_N:
        raise AssertionError("sample is not 600 unique accessions")
    return sample, {
        "index_rows": index_rows, "unique_index_accessions": len(unique_accessions),
        "eligible_after_exclusions": sum(counts.values()), "excluded_accessions": len(excluded),
        "strata": len(counts), "allocation": allocation, "stratum_counts": counts,
    }

def parse_rule_designations(raw, family):
    if family != "13G":
        return []
    root = xml_root(raw)
    if root is None:
        return []
    values = tag_values(root, "designateRulePursuantThisScheduleFiled")
    return sorted(set(v.strip() for v in values if v and v.strip()))

def download_sample(sample, output_dir, sleep_seconds=0.18):
    raw_dir = output_dir / "raw_submissions"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results = []
    path_attempts = 0
    for i, row in enumerate(sample, 1):
        accession = row["accession"]
        family = row["form_family"]
        paths = parse_json_list(row.get("filenames"))
        master_ciks = {norm_cik(x) for x in parse_json_list(row.get("master_index_ciks"))}
        archive_ciks = {norm_cik(x) for x in parse_json_list(row.get("archive_path_ciks"))}
        candidates = []
        for path in paths:
            url = "https://www.sec.gov/Archives/" + path.lstrip("/")
            status, body, error = fetch_url(url, USER_AGENT, retries=5)
            path_attempts += 1
            time.sleep(sleep_seconds)
            valid = False
            header = {}
            digest = None
            if status == 200 and body:
                raw = body.decode("utf-8", errors="replace")
                parsed = parse_submission(raw, family)
                header = {
                    "accession": parsed.get("accession"),
                    "form": parsed.get("form"),
                    "form_family": form_family(parsed.get("form")),
                    "filed_date": parsed.get("filed_date"),
                    "subject_cik": parsed.get("header_subject_cik"),
                    "filer_cik": parsed.get("header_filer_cik"),
                }
                valid = (
                    header["accession"] == accession
                    and header["form_family"] == family
                    and header["filed_date"] == row["filing_date"]
                )
                if valid:
                    digest = sha256_bytes(body)
            candidates.append({
                "path": path, "http_status": status, "error": error,
                "valid": valid, "sha256": digest, "header": header,
                "body": body if valid else None,
            })
        chosen, mirror_status = choose_mirror(candidates)
        if chosen is None:
            results.append({
                "accession": accession, "quarter": row["quarter"], "family": family,
                "is_amendment": row["is_amendment"], "filing_date_index": row["filing_date"],
                "download_status": mirror_status, "valid_path_count": sum(c["valid"] for c in candidates),
                "path_attempts": len(candidates), "path_results": [
                    {k:v for k,v in c.items() if k != "body"} for c in candidates
                ],
                "sample_weight": row["sample_weight"], "sample_stratum": row["sample_stratum"],
            })
            continue

        body = chosen["body"]
        raw = body.decode("utf-8", errors="replace")
        parsed = parse_submission(raw, family)
        raw_path = raw_dir / (accession.replace("-", "") + ".txt")
        raw_path.write_bytes(body)
        subject = parsed.get("header_subject_cik")
        filer = parsed.get("header_filer_cik")
        xml_present = bool(parsed.get("xml_present"))
        xml_subject = parsed.get("xml_issuer_cik") if xml_present else None
        xml_filer = parsed.get("xml_filer_cik") if xml_present else None
        cusip = parsed.get("cusip")
        if not cusip and not xml_present:
            cusip_source = "LEGACY_HTML_HEURISTIC"
        elif cusip:
            cusip_source = "13DG_XML"
        else:
            cusip_source = "NONE"
        rules = parse_rule_designations(raw, family)
        expected_xml = row["filing_date"] >= MANDATORY_XML_DATE
        results.append({
            "accession": accession, "quarter": row["quarter"], "family": family,
            "form": parsed.get("form"), "is_amendment": row["is_amendment"],
            "filing_date_index": row["filing_date"], "filing_date_header": parsed.get("filed_date"),
            "acceptance_datetime": parsed.get("acceptance_datetime"),
            "subject_cik": subject, "subject_name": parsed.get("subject_name"),
            "filer_cik": filer, "filer_name": parsed.get("filer_name"),
            "master_index_ciks": sorted(x for x in master_ciks if x),
            "archive_path_ciks": sorted(x for x in archive_ciks if x),
            "subject_in_master_index": subject in master_ciks if subject else False,
            "filer_in_master_index": filer in master_ciks if filer else False,
            "subject_in_archive_paths": subject in archive_ciks if subject else False,
            "filer_in_archive_paths": filer in archive_ciks if filer else False,
            "index_pair_type": row["index_pair_type"],
            "xml_present": xml_present,
            "mandatory_xml_expected": expected_xml,
            "mandatory_xml_present": xml_present if expected_xml else None,
            "xml_subject_cik": xml_subject, "xml_filer_cik": xml_filer,
            "xml_subject_matches_header": xml_subject == subject if xml_present else None,
            "xml_filer_matches_header": xml_filer == filer if xml_present else None,
            "cusip": cusip, "cusip_source": cusip_source,
            "class_title": parsed.get("class_title"),
            "event_date": parsed.get("event_date"),
            "previous_accession": parsed.get("previous_accession"),
            "amendment_no": parsed.get("amendment_no"),
            "reporting_person_count": len(parsed.get("persons") or []),
            "rule_designations": rules,
            "raw_sha256": chosen["sha256"], "raw_bytes": len(body),
            "raw_file": str(raw_path.relative_to(output_dir)),
            "mirror_status": mirror_status,
            "valid_path_count": sum(c["valid"] for c in candidates),
            "path_attempts": len(candidates),
            "path_results": [
                {k:v for k,v in c.items() if k != "body"} for c in candidates
            ],
            "sample_weight": row["sample_weight"], "sample_stratum": row["sample_stratum"],
            "sample_hash": row["sample_hash"],
        })
    return results, path_attempts

def weighted_rate(rows, field):
    usable = [r for r in rows if r.get(field) is not None]
    denom = sum(float(r["sample_weight"]) for r in usable)
    if denom <= 0:
        return None
    return sum(float(r["sample_weight"]) for r in usable if r.get(field) is True) / denom

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase82-dir", type=Path, required=True)
    p.add_argument("--phase84-dir", type=Path, required=True)
    p.add_argument("--phase120-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    index_path = a.phase82_dir / "global_master_index_13dg.csv"
    excluded = exclusion_set(a.phase82_dir, a.phase84_dir, a.phase120_dir)
    sample, sample_meta = build_sample(index_path, excluded)
    manifest_path = a.output_dir / "phase124_global_stratified_sample_manifest.csv"
    manifest_fields = list(sample[0].keys())
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(sample)

    results, path_attempts = download_sample(sample, a.output_dir)
    result_path = a.output_dir / "phase124_global_13dg_submission_audit.csv"
    if results:
        fields = list(dict.fromkeys(k for r in results for k in r))
        with result_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in results:
                clean = {k: json.dumps(v, sort_keys=True) if isinstance(v, (dict,list)) else v for k,v in row.items()}
                writer.writerow(clean)

    successful = [r for r in results if r.get("download_status") is None]
    failures = [r for r in results if r.get("download_status") is not None]
    header_accession = sum(r.get("accession") is not None for r in successful)
    header_form = sum(form_family(r.get("form")) == r.get("family") for r in successful)
    header_date = sum(r.get("filing_date_header") == r.get("filing_date_index") for r in successful)
    xml_rows = [r for r in successful if r.get("xml_present")]
    mandatory = [r for r in successful if r.get("mandatory_xml_expected")]
    cusip_rows = [r for r in successful if r.get("cusip")]
    subject_rows = [r for r in successful if r.get("subject_cik")]
    summary = {
        "phase": "124-global-sec-13dg-stratified-submission-audit",
        "status": "PASS_GLOBAL_STRATIFIED_SAMPLE_WITH_CAVEATS" if len(successful) == SAMPLE_N and not failures else "INCOMPLETE",
        "phase82_index_sha256": sha256_bytes(index_path.read_bytes()),
        "phase82_global_index_rows": sample_meta["index_rows"],
        "phase82_unique_accessions": sample_meta["unique_index_accessions"],
        "eligible_population_after_exclusions": sample_meta["eligible_after_exclusions"],
        "excluded_prior_accessions": sample_meta["excluded_accessions"],
        "quarters": len(sample_meta["stratum_counts"]) // 4,
        "nonempty_strata": sample_meta["strata"],
        "sample_size": len(sample),
        "sampled_downloads_validated": len(successful),
        "download_or_mirror_failures": len(failures),
        "archive_path_attempts": path_attempts,
        "header_accession_matches": header_accession,
        "header_form_family_matches": header_form,
        "header_filing_date_matches": header_date,
        "subject_cik_present": len(subject_rows),
        "subject_cik_in_master_index": sum(r.get("subject_in_master_index") is True for r in successful),
        "filer_cik_in_master_index": sum(r.get("filer_in_master_index") is True for r in successful),
        "subject_cik_in_archive_paths": sum(r.get("subject_in_archive_paths") is True for r in successful),
        "filer_cik_in_archive_paths": sum(r.get("filer_in_archive_paths") is True for r in successful),
        "xml_rows": len(xml_rows),
        "xml_rate": len(xml_rows) / len(successful) if successful else None,
        "xml_subject_header_matches": sum(r.get("xml_subject_matches_header") is True for r in xml_rows),
        "xml_filer_header_matches": sum(r.get("xml_filer_matches_header") is True for r in xml_rows),
        "mandatory_xml_rows": len(mandatory),
        "mandatory_xml_present": sum(r.get("mandatory_xml_present") is True for r in mandatory),
        "cusip_rows": len(cusip_rows),
        "class_title_rows": sum(bool(r.get("class_title")) for r in successful),
        "unique_subject_ciks": len({r["subject_cik"] for r in subject_rows}),
        "unique_subject_cusip_pairs": len({(r.get("subject_cik"),r.get("cusip")) for r in successful if r.get("subject_cik") and r.get("cusip")}),
        "unique_cusips": len({r["cusip"] for r in cusip_rows}),
        "previous_accession_pointers": sum(bool(r.get("previous_accession")) for r in successful),
        "reporting_person_rows": sum(int(r.get("reporting_person_count") or 0) for r in successful),
        "weighted_subject_in_master_index_rate": weighted_rate(successful,"subject_in_master_index"),
        "weighted_filer_in_master_index_rate": weighted_rate(successful,"filer_in_master_index"),
        "weighted_xml_rate": weighted_rate(successful,"xml_present"),
        "weighted_cusip_rate": weighted_rate(successful,"cusip_present"),
        "sample_strata": [
            {"stratum":"|".join(k),"population_n":n,"sample_n":sample_meta["allocation"][k],
             "sample_weight":n/sample_meta["allocation"][k]}
            for k,n in sorted(sample_meta["stratum_counts"].items())
        ],
        "limitations": [
            "The sample is a deterministic hash-stratified sample of the 2016Q1-2026Q3 global master-index 13D/G accession population after excluding prior pilot accessions; no formal inferential confidence interval is claimed.",
            "This is a filing-index sample, not a complete historical eligible-security universe or historical active/delisted membership ledger.",
            "SEC header subject/filer roles are authoritative for the filing; index CIKs and archive-path CIKs are candidate locators, not semantic roles.",
            "Legacy HTML CUSIP extraction is a heuristic probe only; no legacy reporting-person/ownership parser is validated by this phase.",
            "A CUSIP and class title are not a permanent security identifier without effective-dated corporate-action and issuer mapping.",
            "Acceptance timestamp is retained but not independently proven to equal public dissemination time; use conservative next-session availability.",
            "No forward returns, feature engineering, alpha tests, vendor purchases or production changes."
        ]
    }
    (a.output_dir / "phase124_global_13dg_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    if summary["status"] != "PASS_GLOBAL_STRATIFIED_SAMPLE_WITH_CAVEATS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
