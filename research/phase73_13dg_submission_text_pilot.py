"""Stratified SEC Schedule 13D/13G pilot using complete-submission .txt files.

This is a schema/identity feasibility pilot only. The Phase 35 input is a
filer-side retrieval sample and is not a subject-issuer universe census.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from research.phase72_13dg_structured_xml_corpus_audit import (
    SecClient,
    build_lineage_edge,
    expected_submission_type,
    fetch_submission_index,
    normalize_accession,
    normalize_cik,
    stratified_sample,
)
from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml
from research.phase73_sec_submission_text_extractor import (
    extract_primary_doc_xml,
    normalize_acceptance_datetime,
)


SEC_ARCHIVE_TEXT = "https://www.sec.gov/Archives/edgar/data/{archive_cik}/{accession_key}/{accession}.txt"


def complete_submission_url(archive_cik: str, accession: str) -> str:
    """Build the SEC archive URL using a party CIK, not the accession prefix."""
    cik = normalize_cik(archive_cik)
    if not cik:
        raise ValueError("missing subject/party CIK for SEC archive path")
    return SEC_ARCHIVE_TEXT.format(
        archive_cik=str(int(cik)),
        accession_key=normalize_accession(accession),
        accession=accession,
    )


def _person_rows(source: dict, parsed: dict, submission: dict) -> list[dict]:
    rows = []
    for index, person in enumerate(parsed.get("reporting_persons", []), 1):
        rows.append({
            "accession": source.get("accession", ""),
            "accession_key": normalize_accession(source.get("accession", "")),
            "ticker": source.get("ticker", ""),
            "issuer_cik_xml": normalize_cik(parsed.get("issuer_cik", "")),
            "filing_date": source.get("filing_date", ""),
            "accepted_datetime": submission.get("acceptance_datetime", ""),
            "person_index": index,
            "person_cik": person.get("person_cik", ""),
            "person_cik_status": person.get("person_cik_status", ""),
            "person_no_cik_flag": person.get("person_no_cik_flag", ""),
            "name": person.get("name", ""),
            "member_of_group": person.get("member_of_group", ""),
            "type_codes_json": json.dumps(person.get("type_codes", []), ensure_ascii=False),
            "fund_types_json": json.dumps(person.get("fund_types", []), ensure_ascii=False),
            "aggregate_amount_owned": person.get("aggregate_amount_owned", ""),
            "percent_of_class": person.get("percent_of_class", ""),
        })
    return rows


def run_pilot(
    input_csv: Path,
    outdir: Path,
    sleep_seconds: float = 0.6,
    max_retries: int = 5,
    limit: int = 80,
) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    source = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    required = {"ticker", "issuer_cik", "form", "filing_date", "accession", "primary_document"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"source artifact missing columns: {missing}")

    xml = source[
        source["primary_document"].str.lower().str.endswith(".xml")
        & source["primary_document"].str.lower().str.contains(r"primary_doc\.xml", regex=True)
    ].drop_duplicates(subset=["accession"]).reset_index(drop=True)
    available = len(xml)
    sample = stratified_sample(xml, limit)
    if sample.empty:
        raise RuntimeError("no primary_doc.xml source rows found")

    filer_to_needed: dict[str, set[str]] = defaultdict(set)
    for row in sample.to_dict("records"):
        key = normalize_accession(row["accession"])
        filer_to_needed[normalize_cik(key[:10])].add(key)

    client = SecClient(sleep_seconds=sleep_seconds, max_retries=max_retries)
    submission_index: dict[str, dict] = {}
    submission_errors: list[dict] = []
    min_date, max_date = str(sample["filing_date"].min()), str(sample["filing_date"].max())
    for filer_cik, needed in sorted(filer_to_needed.items()):
        index, errors = fetch_submission_index(client, filer_cik, needed, min_date, max_date)
        submission_index.update(index)
        submission_errors.extend(errors)

    filing_rows: list[dict] = []
    person_rows: list[dict] = []
    errors: list[dict] = []
    for row in sample.to_dict("records"):
        accession = str(row["accession"])
        key = normalize_accession(accession)
        accession_filer_cik = normalize_cik(key[:10])
        subject_cik_path = normalize_cik(row.get("issuer_cik", ""))
        path_candidates = list(dict.fromkeys(x for x in (subject_cik_path, accession_filer_cik) if x))
        submission = submission_index.get(key, {})
        try:
            response = None
            url = ""
            archive_path_cik = ""
            path_errors = []
            for candidate_cik in path_candidates:
                candidate_url = complete_submission_url(candidate_cik, accession)
                try:
                    response = client.get(candidate_url)
                    url = candidate_url
                    archive_path_cik = candidate_cik
                    break
                except Exception as path_exc:
                    path_errors.append(f"{candidate_cik}: {path_exc!r}")
            if response is None:
                raise RuntimeError("all SEC archive CIK path candidates failed: " + " | ".join(path_errors))
            extracted = extract_primary_doc_xml(response.content)
            parsed = parse_schedule13_xml(extracted["xml_bytes"])
            header = extracted
            source_form = expected_submission_type(row.get("form", ""))
            xml_form = str(parsed.get("submission_type", "")).upper()
            header_form = str(header.get("form", "")).upper()
            xml_issuer = normalize_cik(parsed.get("issuer_cik", ""))
            header_subject = normalize_cik(header.get("subject_cik", ""))
            xml_filer = normalize_cik(parsed.get("filer_cik_xml", ""))
            header_filer = normalize_cik(header.get("filer_cik", ""))
            header_date = header.get("filing_date", "")
            submission_date = str(submission.get("filing_date", ""))
            header_acceptance = str(header.get("acceptance_datetime", ""))
            submission_acceptance = str(submission.get("acceptance_datetime", ""))
            header_acceptance_normalized = normalize_acceptance_datetime(
                header_acceptance, source_timezone="America/New_York"
            )
            submission_acceptance_normalized = normalize_acceptance_datetime(submission_acceptance)
            header_accession = normalize_accession(header.get("accession", ""))
            accession_match = bool(header_accession and header_accession == key)
            filing_rows.append({
                "ticker": row.get("ticker", ""),
                "legacy_source_cik": normalize_cik(row.get("issuer_cik", "")),
                "legacy_source_cik_matches_filer": normalize_cik(row.get("issuer_cik", "")) == accession_filer_cik,
                "issuer_cik_xml": xml_issuer,
                "header_subject_cik": header_subject,
                "issuer_cik_match": bool(xml_issuer and xml_issuer == header_subject),
                "issuer_name_xml": parsed.get("issuer_name", ""),
                "header_subject_name": header.get("subject_name", ""),
                "filer_cik_xml": xml_filer,
                "header_filer_cik": header_filer,
                "accession_prefix_cik": accession_filer_cik,
                "filer_cik_match": bool(xml_filer and xml_filer == header_filer == accession_filer_cik),
                "header_filer_name": header.get("filer_name", ""),
                "form_source": row.get("form", ""),
                "submission_type_xml": xml_form,
                "header_form": header_form,
                "form_match": bool(source_form and source_form == xml_form == header_form),
                "filing_date": row.get("filing_date", ""),
                "header_filing_date": header_date,
                "submission_filing_date": submission_date,
                "filing_date_match": bool(row.get("filing_date", "") == header_date == submission_date),
                "knowledge_date": row.get("filing_date", ""),
                "knowledge_date_rule": "SEC submissions filingDate; date-level conservative; XML eventDate is descriptive only",
                "accepted_datetime": submission_acceptance,
                "header_acceptance_datetime": header_acceptance,
                "acceptance_datetime_normalized": header_acceptance_normalized,
                "submission_acceptance_datetime_raw": submission_acceptance,
                "submission_acceptance_datetime_normalized": submission_acceptance_normalized,
                "acceptance_datetime_match": bool(header_acceptance_normalized and header_acceptance_normalized == submission_acceptance_normalized),
                "header_accession": header.get("accession", ""),
                "accession_match": accession_match,
                "accession": accession,
                "accession_key": key,
                "source_primary_document": row.get("primary_document", ""),
                "full_submission_text_url": url,
                "archive_path_cik": archive_path_cik,
                "archive_path_role_candidate": "subject_or_party_cik; verified against SEC header below",
                "extraction_method": extracted.get("extraction_method", ""),
                "event_date_xml": parsed.get("event_date", ""),
                "is_amendment": parsed.get("is_amendment", False),
                "amendment_number": parsed.get("amendment_number", ""),
                "previous_accession_number": parsed.get("previous_accession_number", ""),
                "lineage_status": parsed.get("lineage_status", ""),
                "reporting_person_count": parsed.get("reporting_person_count", 0),
                "cusips_json": json.dumps(parsed.get("cusips", []), ensure_ascii=False),
                "rule_designations_json": json.dumps(parsed.get("rule_designations", []), ensure_ascii=False),
                "purpose_text": parsed.get("purpose_text", ""),
                "parser_version": parsed.get("parser_version", ""),
                "schema_version": parsed.get("schema_version", ""),
                "parse_status": "success",
            })
            person_rows.extend(_person_rows(row, parsed, submission))
        except Exception as exc:
            errors.append({
                "accession": accession,
                "accession_key": key,
                "ticker": row.get("ticker", ""),
                "legacy_source_cik": row.get("issuer_cik", ""),
                "form": row.get("form", ""),
                "filing_date": row.get("filing_date", ""),
                "url": url,
                "error": repr(exc),
            })

    filing_frame = pd.DataFrame(filing_rows)
    person_frame = pd.DataFrame(person_rows)
    if not filing_frame.empty:
        accession_index = {
            normalize_accession(r["accession"]): {
                "accession": r["accession"],
                "issuer_cik": r["issuer_cik_xml"],
                "form": r["submission_type_xml"],
                "filing_date": r["filing_date"],
            }
            for r in filing_rows
        }
        lineage_rows = []
        for row in filing_rows:
            if str(row.get("is_amendment", "")).lower() == "true":
                current = {
                    "accession": row["accession"],
                    "issuer_cik": row["issuer_cik_xml"],
                    "form": row["submission_type_xml"],
                    "filing_date": row["filing_date"],
                }
                edge = build_lineage_edge(current, row.get("previous_accession_number", ""), accession_index)
                edge["amendment_number"] = row.get("amendment_number", "")
                lineage_rows.append(edge)
    else:
        lineage_rows = []

    issuer_rate = float(filing_frame["issuer_cik_match"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0
    accession_rate = float(filing_frame["accession_match"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0
    filer_rate = float(filing_frame["filer_cik_match"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0
    form_rate = float(filing_frame["form_match"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0
    filing_date_rate = float(filing_frame["filing_date_match"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0
    acceptance_present = int(filing_frame["header_acceptance_datetime"].astype(str).ne("").sum()) if not filing_frame.empty else 0
    acceptance_match = int(filing_frame["acceptance_datetime_match"].astype(str).str.lower().eq("true").sum()) if not filing_frame.empty else 0
    acceptance_rate = acceptance_match / acceptance_present if acceptance_present else 0.0
    people_rate = float((pd.to_numeric(filing_frame["reporting_person_count"], errors="coerce").fillna(0) > 0).mean()) if not filing_frame.empty else 0.0
    parse_rate = len(filing_frame) / len(sample) if len(sample) else 0.0
    cross_issuer = sum(1 for r in lineage_rows if r.get("lineage_status") == "predecessor_in_panel_cross_issuer")
    gates = {
        "xml_parse_rate_ge_99_5pct": parse_rate >= 0.995,
        "xml_issuer_matches_sec_header_subject_ge_99_5pct": issuer_rate >= 0.995,
        "xml_accession_matches_sec_header_ge_99_5pct": accession_rate >= 0.995,
        "xml_filer_matches_sec_header_and_accession_ge_99_5pct": filer_rate >= 0.995,
        "form_concordance_ge_99_5pct": form_rate >= 0.995,
        "filing_date_concordance_ge_99_5pct": filing_date_rate >= 0.995,
        "acceptance_datetime_concordance_ge_99_5pct_when_present": acceptance_rate >= 0.995 if acceptance_present else False,
        "reporting_person_count_positive_ge_99_5pct": people_rate >= 0.995,
        "no_cross_issuer_predecessor_edges": cross_issuer == 0,
    }
    data_gate = "PASS" if all(gates.values()) else "FAIL"
    summary = {
        "phase": "73-13dg-complete-submission-text-pilot",
        "status": "COMPLETE" if len(filing_frame) == len(sample) else "PARTIAL",
        "data_gate": data_gate,
        "source_run_id": 41575083622,
        "source_artifact_id": 13212292743,
        "source_input_rows": int(len(source)),
        "xml_rows_available": int(available),
        "sample_rows": int(len(sample)),
        "sample_strata_counts": (sample.assign(form_family=sample["form"].str.upper().apply(lambda x: "13D" if "13D" in x else ("13G" if "13G" in x else "OTHER")), is_amendment=sample["form"].str.upper().str.endswith("/A"), period=sample["filing_date"].apply(lambda x: "voluntary_xml_pre_mandate" if str(x) < "2024-12-18" else "mandatory_era")).groupby(["form_family", "is_amendment", "period"]).size().reset_index(name="rows").to_dict("records")),
        "parsed_filings": int(len(filing_frame)),
        "parse_errors": int(len(errors)),
        "reporting_person_rows": int(len(person_frame)),
        "issuer_xml_vs_sec_header_subject_rate": issuer_rate,
        "accession_vs_sec_header_rate": accession_rate,
        "filer_xml_vs_sec_header_and_accession_rate": filer_rate,
        "form_concordance_rate": form_rate,
        "filing_date_concordance_rate": filing_date_rate,
        "acceptance_datetime_rows": acceptance_present,
        "acceptance_datetime_concordance_rate_when_present": acceptance_rate,
        "reporting_person_count_positive_rate": people_rate,
        "legacy_source_cik_matches_filer_rate": float(filing_frame["legacy_source_cik_matches_filer"].astype(str).str.lower().eq("true").mean()) if not filing_frame.empty else 0.0,
        "submission_index_matches": int(len(submission_index)),
        "submission_index_errors": int(len(submission_errors)),
        "amendments": int(filing_frame["is_amendment"].astype(str).str.lower().eq("true").sum()) if not filing_frame.empty else 0,
        "amendments_with_previous_accession": int(filing_frame["previous_accession_number"].astype(str).ne("").sum()) if not filing_frame.empty else 0,
        "amendment_predecessor_in_panel_same_issuer": sum(1 for r in lineage_rows if r.get("lineage_status") == "predecessor_in_panel_same_issuer"),
        "amendment_predecessor_in_panel_cross_issuer": cross_issuer,
        "amendment_predecessor_outside_panel": sum(1 for r in lineage_rows if r.get("lineage_status") == "predecessor_outside_input_panel"),
        "lineage_edges": int(len(lineage_rows)),
        "gate_checks": gates,
        "request_count": client.request_count,
        "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_date_rule": "Use SEC submissions filingDate as conservative date-level KnowledgeDate; preserve acceptanceDateTime separately; never substitute XML eventDate.",
        "source_scope_warning": "Phase 35 input is a filer-side retrieval sample, not a subject-issuer census; issuer identity is validated against the SEC complete-submission header SUBJECT COMPANY block.",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "limitations": [
            "This is a schema/identity pilot over an existing filer-side sample, not subject-issuer coverage.",
            "A complete submission .txt XML block is parsed; the separate primary_doc.xml HTTP representation is not used.",
            "A declared previousAccessionNumber is a direct edge, not a complete economic-group history.",
            "Reporting-person CIKs and group flags are preserved as filed; no account-level identity or economic group is inferred.",
            "Historical F80 membership, delisted predecessor coverage and legacy HTML filings remain untested.",
        ],
    }
    filing_frame.to_csv(outdir / "filings.csv", index=False)
    person_frame.to_csv(outdir / "reporting_persons.csv", index=False)
    pd.DataFrame(lineage_rows).to_csv(outdir / "lineage_edges.csv", index=False)
    pd.DataFrame(errors).to_csv(outdir / "fetch_parse_errors.csv", index=False)
    pd.DataFrame(submission_errors).to_csv(outdir / "submission_index_errors.csv", index=False)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase73_13dg_submission_text_pilot"))
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()
    summary = run_pilot(
        input_csv=args.input_csv,
        outdir=args.outdir,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
        limit=args.limit,
    )
    if summary["status"] != "COMPLETE" or summary["data_gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
