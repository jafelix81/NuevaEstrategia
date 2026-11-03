"""SEC Schedule 13D/G subject-census pilot using structured primary XML.

The SEC master.idx discovers accessions. The primary XML supplies subject issuer
and submission-filer CIKs. No accession prefix or master-index row order is used
as an identity role. This is a feasibility audit, not an alpha test.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, re, statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError

from phase35_13dg_parser_v3 import (
    parse_master_index, parse_xml, reporting_person_set_fingerprint,
)
from phase35_global_subject_census_pilot import (
    KNOWN_ACCESSION, cik_norm, current_cik_candidates, fetch_bytes,
    group_rows, load_universe, normalize_form, select_groups,
)


def primary_xml_urls(group):
    accession = group["accession"]
    nodash = accession.replace("-", "")
    candidates = list(group["master_index_ciks"]) + [accession.split("-")[0]]
    urls = []
    for cik in dict.fromkeys(candidates):
        normalized = cik_norm(cik)
        if normalized:
            archive_cik = str(int(normalized))
            url = (f"https://www.sec.gov/Archives/edgar/data/{archive_cik}/"
                   f"{nodash}/primary_doc.xml")
            if url not in urls:
                urls.append(url)
    return urls


def fetch_primary_xml(group):
    errors = []
    for url in primary_xml_urls(group):
        try:
            parsed = parse_xml(fetch_bytes(url, sec=True, timeout=45, retries=5))
            if parsed.get("subject_issuer_cik"):
                return parsed, url, None
            errors.append("XML_SUBJECT_CIK_MISSING")
        except HTTPError as exc:
            if exc.code == 404:
                errors.append("404")
                continue
            errors.append(f"HTTP{exc.code}")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
    return None, None, ";".join(errors[-6:]) or "PRIMARY_XML_NOT_FOUND"


def archive_path_cik_from_url(xml_url):
    """Return the numeric CIK in an SEC archive path; tolerate non-archive test URLs."""
    match = re.search(r"/Archives/edgar/data/(\d+)/", xml_url or "", flags=re.IGNORECASE)
    return match.group(1).zfill(10) if match else None


def identity_row(group, parsed, xml_url, target_ciks):
    subject = cik_norm(parsed.get("subject_issuer_cik"))
    filer = cik_norm(parsed.get("filer_cik"))
    pair = set(group["master_index_ciks"])
    people = parsed.get("reporting_persons") or []
    person_ciks = sorted({
        cik_norm(p.get("cik")) for p in people
        if p.get("cik") and cik_norm(p.get("cik"))
    })
    names = group["master_index_names"]
    return {
        "accession": group["accession"],
        "form": group["form"],
        "filing_date": group["filing_date"],
        "knowledge_date": group["filing_date"],
        "master_index_ciks": ";".join(group["master_index_ciks"]),
        "master_index_names": json.dumps(names, sort_keys=True),
        "subject_issuer_cik": subject,
        "subject_issuer_name": parsed.get("subject_issuer_name"),
        "submission_filer_cik": filer,
        "submission_filer_name_from_master_pair": names.get(filer),
        "subject_issuer_cusips": json.dumps(parsed.get("subject_issuer_cusips") or []),
        "submission_type": parsed.get("submission_type"),
        "xml_form_match": normalize_form(parsed.get("submission_type")) == group["form"],
        "event_date_raw": parsed.get("event_date"),
        "previous_accession": parsed.get("previous_accession"),
        "reporting_person_count": len(people),
        "reporting_person_cik_count": len(person_ciks),
        "reporting_person_cik_coverage": len(person_ciks) / len(people) if people else 0.0,
        "reporting_person_ciks": ";".join(person_ciks),
        "reporting_persons_json": json.dumps(people, sort_keys=True),
        "reporting_person_set_fingerprint": reporting_person_set_fingerprint(people),
        "subject_in_master_pair": bool(subject and subject in pair),
        "submission_filer_in_master_pair": bool(filer and filer in pair),
        "both_subject_and_filer_in_master_pair": bool(
            subject and filer and subject in pair and filer in pair
        ),
        "subject_is_target_candidate": bool(subject and subject in target_ciks),
        "submission_filer_is_target_candidate": bool(filer and filer in target_ciks),
        "target_relevant": group["target_relevant"],
        "validation_sample_non_target": group["validation_sample"],
        "xml_url": xml_url,
        "archive_path_cik": archive_path_cik_from_url(xml_url),
    }


def coverage(rows, key, denominator):
    return sum(bool(row.get(key)) for row in rows) / denominator if denominator else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--quarter", type=int, default=1, choices=(1, 2, 3, 4))
    ap.add_argument("--output", default="phase35_global_subject_census_xml_pilot")
    ap.add_argument("--sample-per-form", type=int, default=50)
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    tickers = load_universe()
    ticker_map, cik_to_tickers, unresolved = current_cik_candidates(tickers)
    target_ciks = set(cik_to_tickers)
    master_url = (f"https://www.sec.gov/Archives/edgar/full-index/{args.year}/"
                  f"QTR{args.quarter}/master.idx")
    master = fetch_bytes(master_url, sec=True, timeout=120)
    master_sha = hashlib.sha256(master).hexdigest()
    (out / "master.idx.gz").write_bytes(gzip.compress(master, compresslevel=9))

    groups = group_rows(parse_master_index(master))
    relevant, sample = select_groups(groups, target_ciks, per_form=args.sample_per_form)
    fetch = {
        g["accession"]: {**g, "target_relevant": True, "validation_sample": False}
        for g in relevant
    }
    for g in sample:
        fetch.setdefault(g["accession"], {
            **g, "target_relevant": False, "validation_sample": True,
        })
    known_group = next((g for g in groups if g["accession"] == KNOWN_ACCESSION), None)
    if known_group:
        fetch.setdefault(KNOWN_ACCESSION, {
            **known_group,
            "target_relevant": bool(set(known_group["master_index_ciks"]) & target_ciks),
            "validation_sample": False,
        })

    with (out / "ticker_cik_candidates.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=[
            "ticker", "candidate_ciks", "mapping_sources", "alias_used", "fund_classes",
        ])
        w.writeheader()
        for ticker, d in ticker_map.items():
            w.writerow({
                "ticker": ticker, "candidate_ciks": ";".join(d["ciks"]),
                "mapping_sources": ";".join(d["sources"]),
                "alias_used": d["alias_used"] or "",
                "fund_classes": json.dumps(d["fund_classes"], sort_keys=True),
            })

    results, errors = [], []
    ordered = sorted(fetch.values(), key=lambda g: g["accession"])
    for i, group in enumerate(ordered, 1):
        parsed, url, error = fetch_primary_xml(group)
        if error:
            errors.append({
                "accession": group["accession"], "error": error,
                "target_relevant": group["target_relevant"],
                "validation_sample_non_target": group["validation_sample"],
            })
            continue
        results.append(identity_row(group, parsed, url, target_ciks))
        if i % 100 == 0:
            print(json.dumps({
                "stage": "XML_PROGRESS", "processed": i, "total": len(ordered),
                "subject_parsed": len(results), "errors": len(errors),
            }), flush=True)

    fields = list(results[0].keys()) if results else [
        "accession", "form", "filing_date", "subject_issuer_cik", "submission_filer_cik",
    ]
    outputs = [
        ("global_subject_census_xml.csv", results),
        ("target_subject_filings_xml.csv", [r for r in results if r["subject_is_target_candidate"]]),
        ("target_submission_filer_filings_xml.csv", [r for r in results if r["submission_filer_is_target_candidate"]]),
        ("target_submission_filer_only_cross_issuer_xml.csv", [
            r for r in results if r["submission_filer_is_target_candidate"]
            and not r["subject_is_target_candidate"]
        ]),
        ("xml_fetch_errors.csv", errors),
    ]
    for filename, rows in outputs:
        with (out / filename).open("w", newline="", encoding="utf-8") as h:
            cols = list(rows[0].keys()) if rows else (
                ["accession", "error", "target_relevant", "validation_sample_non_target"]
                if filename == "xml_fetch_errors.csv" else fields
            )
            w = csv.DictWriter(h, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    rel = [r for r in results if r["target_relevant"]]
    sam = [r for r in results if r["validation_sample_non_target"]]
    n_rel, n_sam = len(relevant), len(sample)
    error_rate = len(errors) / len(ordered) if ordered else 1.0
    subject_rel = coverage(rel, "subject_issuer_cik", n_rel)
    filer_rel = coverage(rel, "submission_filer_cik", n_rel)
    subject_sam = coverage(sam, "subject_issuer_cik", n_sam)
    filer_sam = coverage(sam, "submission_filer_cik", n_sam)
    subject_pair_rel = coverage(rel, "subject_in_master_pair", n_rel)
    filer_pair_rel = coverage(rel, "submission_filer_in_master_pair", n_rel)
    subject_pair_sam = coverage(sam, "subject_in_master_pair", n_sam)
    filer_pair_sam = coverage(sam, "submission_filer_in_master_pair", n_sam)
    both_pair_rel = coverage(rel, "both_subject_and_filer_in_master_pair", n_rel)
    form_match = coverage(results, "xml_form_match", len(ordered))
    known = next((r for r in results if r["accession"] == KNOWN_ACCESSION), None)
    known_check = {
        "found": known is not None,
        "submission_filer_cik": known.get("submission_filer_cik") if known else None,
        "subject_issuer_cik": known.get("subject_issuer_cik") if known else None,
        "pass": bool(
            known and known.get("submission_filer_cik") == "0000092230"
            and known.get("subject_issuer_cik") == "0001849998"
        ),
    }
    passed = bool(
        n_rel >= 100
        and subject_rel is not None and subject_rel >= .95
        and filer_rel is not None and filer_rel >= .95
        and subject_sam is not None and subject_sam >= .95
        and filer_sam is not None and filer_sam >= .95
        and subject_pair_rel is not None and subject_pair_rel >= .95
        and filer_pair_rel is not None and filer_pair_rel >= .95
        and subject_pair_sam is not None and subject_pair_sam >= .95
        and filer_pair_sam is not None and filer_pair_sam >= .95
        and form_match is not None and form_match >= .95
        and error_rate <= .05 and known_check["pass"]
    )
    summary = {
        "phase": "35_global_subject_census_xml_pilot",
        "status": "PASS" if passed else "FAILED_VALIDATION",
        "quarter": f"{args.year}Q{args.quarter}",
        "master_index_url": master_url, "master_index_sha256": master_sha,
        "master_index_rows": len(parse_master_index(master)),
        "unique_13dg_accessions": len(groups),
        "unique_accessions_by_form": dict(Counter(g["form"] for g in groups if g["form"])),
        "frozen_tickers": len(tickers), "current_candidate_ciks": len(target_ciks),
        "unresolved_tickers": unresolved,
        "target_relevant_accessions": n_rel, "validation_sample_non_target": n_sam,
        "primary_xml_requested": len(ordered), "primary_xml_parsed": len(results),
        "primary_xml_fetch_errors": len(errors), "primary_xml_fetch_error_rate": error_rate,
        "subject_cik_coverage_target_relevant": subject_rel,
        "submission_filer_cik_coverage_target_relevant": filer_rel,
        "subject_cik_coverage_validation_sample": subject_sam,
        "submission_filer_cik_coverage_validation_sample": filer_sam,
        "subject_in_master_pair_target_relevant": subject_pair_rel,
        "submission_filer_in_master_pair_target_relevant": filer_pair_rel,
        "both_roles_in_master_pair_target_relevant": both_pair_rel,
        "subject_in_master_pair_validation_sample": subject_pair_sam,
        "submission_filer_in_master_pair_validation_sample": filer_pair_sam,
        "xml_form_match_rate": form_match,
        "target_subject_filings": sum(r["subject_is_target_candidate"] for r in results),
        "target_submission_filer_filings": sum(r["submission_filer_is_target_candidate"] for r in results),
        "target_submission_filer_only_cross_issuer": sum(
            r["submission_filer_is_target_candidate"] and not r["subject_is_target_candidate"]
            for r in results
        ),
        "reporting_person_cik_coverage_mean": (
            statistics.mean(r["reporting_person_cik_coverage"] for r in results)
            if results else None
        ),
        "known_truist_federated_fixture": known_check,
        "knowledge_date_rule": (
            "SEC filing date from master.idx; signal date must be strictly later. "
            "Accepted timestamps are not used in this pilot."
        ),
        "mapping_limitation": (
            "Current SEC ticker/exchange/mutual-fund maps plus fallback are candidate "
            "mappings, not historical active-universe membership; unresolved tickers "
            "remain outside this candidate-CIK census."
        ),
        "reporting_person_limitation": (
            "Reporting-person CIK-set fingerprint is a deterministic checksum only, "
            "not proof of an economic group; incomplete CIK sets remain unresolved."
        ),
        "economic_group_status": "NOT_TESTED",
        "forward_returns_used": False,
        "errors_sample": errors[:50],
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if not passed:
        raise RuntimeError("Global XML subject-census pilot validation failed; inspect summary.json")


if __name__ == "__main__":
    main()
