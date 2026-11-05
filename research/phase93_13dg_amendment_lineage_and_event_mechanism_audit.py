#!/usr/bin/env python3
"""Offline Schedule 13D/G event-mechanism and conservative amendment-lineage audit.

This phase never infers a confirmed predecessor when previousAccessionNumber is absent.
Candidate parents are diagnostics only and are never used to collapse events.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from research.phase72_13dg_structured_xml_parser import parse_schedule13_xml
from research.phase73_sec_submission_text_extractor import extract_primary_doc_xml


def load_csv(path: Path) -> list[dict]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (list, dict, tuple, set)) else value
                for key, value in row.items()
            })


def normalize_cik(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits


def normalize_accession(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def normalize_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def normalize_form(value: str) -> str:
    form = re.sub(r"\\s+", " ", str(value or "").strip().upper())
    form = form.replace("SCHEDULE 13D", "SC 13D").replace("SCHEDULE 13G", "SC 13G")
    form = re.sub(r"^SC\\s*13([DG])\\s*/\\s*A$", r"SC 13\\1/A", form)
    return re.sub(r"^SC\\s*13([DG])$", r"SC 13\\1", form)


def normalize_cusip(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def parse_utc(value: str):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def json_list(value) -> list:
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value or ""))
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


EVENT_PATTERNS = {
    "activist_or_control_action": (
        "proxy contest", "solicit proxies", "nominate directors", "nomination of directors",
        "seek board representation", "board representation", "replace members of the board",
        "remove members of the board", "strategic alternatives", "sale of the company",
        "sale of the issuer", "spin-off", "spin off", "declassify the board",
        "change in control", "change management", "oppose the proposed transaction",
        "commence a consent solicitation",
    ),
    "governance_reference_only": (
        "board of directors", "corporate governance", "management of the issuer",
    ),
    "business_combination_consideration": (
        "business combination", "merger consideration", "merger agreement",
        "in connection with the merger", "acquired by way of merger",
        "shares issued in the merger", "share exchange agreement",
    ),
    "open_market_acquisition": (
        "open market purchase", "purchased in the open market",
        "purchased on the open market", "acquired in the open market",
        "purchase in the open market",
    ),
    "open_market_disposition": (
        "open market sale", "sold in the open market", "sold on the open market",
        "disposed of in the open market",
    ),
    "private_placement_or_offering": (
        "private placement", "private offering", "subscription agreement",
        "registered direct offering", "pipe investment",
    ),
    "employee_equity_compensation": (
        "stock award", "equity award", "restricted stock unit",
        "equity incentive plan", "employee stock purchase plan",
        "award agreement", "compensation for services",
    ),
    "conversion_or_exercise": (
        "conversion of preferred", "conversion of convertible", "convertible note",
        "exercise of options", "warrant exercise", "conversion of warrants",
    ),
    "gift_transfer_or_distribution": (
        "bona fide gift", "gift of shares", "donation of shares",
        "transferred an aggregate", "distribution of shares", "transfer of shares",
        "gifted shares",
    ),
    "pledge_or_collateral": (
        "pledge of shares", "pledged shares", "pledged as collateral",
        "collateral for a loan",
    ),
    "derivative_or_swap_exposure": (
        "security-based swap", "cash-settled swap", "total return swap",
        "equity swap", "call option", "put option", "derivative security",
        "derivative instrument",
    ),
    "aggregated_client_or_adviser_holdings": (
        "no one person has greater than 5% economic ownership",
        "held of record by clients", "relevant clients", "investment adviser",
        "investment advisor", "parent holding company",
    ),
    "corporate_reorganization_or_denominator_change": (
        "capital reorganization", "share capital reorganization", "recapitalization",
        "reverse stock split", "increase in the number of shares outstanding",
        "change in the number of shares outstanding", "share capital",
    ),
    "ordinary_course_no_control_intent": (
        "not acquired and are not held for the purpose or with the effect of changing or influencing control",
        "ordinary course of business and not with the purpose or effect of changing or influencing control",
        "no purpose or effect of changing or influencing control",
    ),
    "no_recent_transactions_declared": (
        "has not effected any transactions", "no transactions in the past 60 days",
        "no transactions were effected",
    ),
    "litigation_or_dispute": (
        "motion to dismiss", "district court", "lawsuit", "litigation",
        "filed a complaint", "legal proceedings",
    ),
}


def classify_event_mechanism(xml_text: str, parsed: dict) -> tuple[list[str], dict[str, list[str]]]:
    """Conservative overlapping mechanism tags; never emits a Smart Money label."""
    text = " ".join([
        str(xml_text or ""),
        str(parsed.get("purpose_text") or ""),
        str(parsed.get("group_members_narrative") or ""),
        str(parsed.get("filing_person_name_narrative") or ""),
    ]).lower()
    tags = []
    matched = {}
    for tag, phrases in EVENT_PATTERNS.items():
        hits = sorted({phrase for phrase in phrases if phrase in text})
        if hits:
            tags.append(tag)
            matched[tag] = hits
    if any(str(person.get("member_of_group", "")).strip().upper() in {"Y", "YES", "1"}
           for person in (parsed.get("reporting_persons") or [])):
        tags.append("group_or_joint_reporting_person")
    if not tags:
        tags = ["unclassified_narrative"]
    return sorted(set(tags)), matched


def person_identity_sets(person_rows: list[dict]) -> tuple[set[str], set[str]]:
    explicit_ciks, names = set(), set()
    for row in person_rows:
        cik = normalize_cik(row.get("person_explicit_cik", ""))
        name = normalize_name(row.get("person_name", ""))
        if cik:
            explicit_ciks.add(cik)
        if name:
            names.add(name)
    return explicit_ciks, names


def candidate_parent_basis(current: dict, prior: dict) -> str:
    """Return a candidate basis, never a confirmed link.

    Filer CIK, accession-prefix CIK and inferred first-person 13G CIK are
    intentionally excluded from person-identity matching.
    """
    if current.get("accession") == prior.get("accession"):
        return ""
    if current.get("subject_cik") != prior.get("subject_cik"):
        return ""
    if current.get("family") != prior.get("family"):
        return ""
    current_time = parse_utc(current.get("acceptance_utc", ""))
    prior_time = parse_utc(prior.get("acceptance_utc", ""))
    if not current_time or not prior_time or prior_time >= current_time:
        return ""
    current_cusips = set(current.get("cusips") or [])
    prior_cusips = set(prior.get("cusips") or [])
    cusip_overlap = bool(current_cusips & prior_cusips)
    if current_cusips and prior_cusips and not cusip_overlap:
        return ""
    cik_overlap = set(current.get("explicit_person_ciks") or []) & set(prior.get("explicit_person_ciks") or [])
    if cik_overlap:
        return "shared_explicit_reporting_person_cik"
    name_overlap = set(current.get("person_names") or []) & set(prior.get("person_names") or [])
    if name_overlap and cusip_overlap:
        return "shared_exact_person_name_and_cusip"
    return ""


def validate_explicit_predecessor(current: dict, previous_accession: str,
                                  header_by_accession: dict, structured_by_accession: dict) -> str:
    previous = normalize_accession(previous_accession)
    if not previous:
        return "amendment_missing_explicit_predecessor" if parse_bool(current.get("is_amendment")) else "original_no_predecessor"
    if previous == current.get("accession"):
        return "explicit_predecessor_self_reference"
    header = header_by_accession.get(previous)
    if header is None:
        return "explicit_predecessor_outside_600_header_sample"
    parent_subject = normalize_cik(header.get("subject_cik", ""))
    if parent_subject and parent_subject != current.get("subject_cik"):
        return "explicit_predecessor_subject_mismatch"
    parent_form = str(header.get("header_form", "")).upper()
    parent_family = "13D" if "13D" in parent_form else ("13G" if "13G" in parent_form else "")
    if parent_family and parent_family != current.get("family"):
        return "explicit_predecessor_family_mismatch"
    parent_date = str(header.get("header_filing_date", "") or "")
    current_date = str(current.get("filing_date", "") or "")
    if parent_date and current_date and parent_date >= current_date:
        return "explicit_predecessor_not_earlier"
    if previous in structured_by_accession:
        return "explicit_predecessor_structured_sample_consistent"
    return "explicit_predecessor_header_sample_consistent_xml_unavailable"


def run(args):
    phase84_dir = Path(args.phase84_artifact_dir)
    phase91_dir = Path(args.phase91_artifact_dir)
    raw_dir = phase84_dir / "raw_submissions"
    events = load_csv(phase91_dir / "phase91_filing_events.csv")
    persons = load_csv(phase91_dir / "phase91_reporting_person_identity.csv")
    header_rows = load_csv(phase84_dir / "pilot_header_validation.csv")
    header_by_accession = {
        normalize_accession(row.get("accession", "")): row for row in header_rows
        if normalize_accession(row.get("accession", ""))
    }
    persons_by_accession = {}
    for row in persons:
        persons_by_accession.setdefault(normalize_accession(row.get("accession", "")), []).append(row)

    records, errors = [], []
    for event in events:
        accession = normalize_accession(event.get("accession", ""))
        raw_path = raw_dir / f"{accession}.txt"
        if not raw_path.is_file():
            errors.append({"accession": accession, "error": "raw_submission_missing"})
            continue
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        expected_digest = str(event.get("raw_sha256", "")).strip().lower()
        if not expected_digest or digest != expected_digest:
            errors.append({"accession": accession, "error": "raw_sha256_mismatch"})
            continue
        try:
            extracted = extract_primary_doc_xml(raw)
            parsed = parse_schedule13_xml(extracted["xml_bytes"])
        except Exception as exc:
            errors.append({"accession": accession, "error": f"xml_parse:{exc!r}"})
            continue
        subject = normalize_cik(event.get("subject_cik", ""))
        filer = normalize_cik(event.get("filer_cik", ""))
        if normalize_cik(parsed.get("issuer_cik", "")) != subject:
            errors.append({"accession": accession, "error": "xml_subject_mismatch"})
            continue
        if normalize_cik(parsed.get("filer_cik_xml", "")) != filer:
            errors.append({"accession": accession, "error": "xml_filer_mismatch"})
            continue
        if normalize_form(parsed.get("submission_type", "")) != normalize_form(event.get("form", "")):
            errors.append({"accession": accession, "error": "xml_form_mismatch"})
            continue
        person_rows = persons_by_accession.get(accession, [])
        explicit_ciks, person_names = person_identity_sets(person_rows)
        cusips = sorted({normalize_cusip(x) for x in (parsed.get("cusips") or []) if normalize_cusip(x)})
        xml_text = extracted["xml_bytes"].decode("utf-8", errors="replace")
        tags, matched = classify_event_mechanism(xml_text, parsed)
        record = {
            "accession": accession,
            "family": event.get("family", ""),
            "form": event.get("form", ""),
            "is_amendment": parse_bool(event.get("is_amendment")),
            "filing_date": event.get("filing_date", ""),
            "acceptance_utc": event.get("acceptance_utc", ""),
            "subject_cik": subject,
            "filer_cik": filer,
            "event_date": event.get("event_date", ""),
            "amendment_number": parsed.get("amendment_number", ""),
            "xml_previous_accession": normalize_accession(parsed.get("previous_accession_number", "")),
            "reporting_person_count": len(parsed.get("reporting_persons") or []),
            "explicit_person_ciks": sorted(explicit_ciks),
            "person_names": sorted(person_names),
            "cusips": cusips,
            "event_mechanism_tags": tags,
            "matched_event_phrases": matched,
            "purpose_text_present": bool(parsed.get("purpose_text")),
            "group_members_narrative_present": bool(parsed.get("group_members_narrative")),
        }
        records.append(record)

    structured_by_accession = {row["accession"]: row for row in records}
    lineage_rows, candidate_edges = [], []
    for current in records:
        is_amendment = current["is_amendment"]
        previous = current["xml_previous_accession"]
        if previous:
            status = validate_explicit_predecessor(current, previous, header_by_accession, structured_by_accession)
            candidate_count = 0
            candidates = []
        elif is_amendment:
            candidates = []
            for prior in records:
                basis = candidate_parent_basis(current, prior)
                if basis:
                    candidates.append((prior, basis))
            candidates.sort(key=lambda item: parse_utc(item[0]["acceptance_utc"]), reverse=True)
            candidate_count = len(candidates)
            if candidate_count == 1:
                status = "unique_candidate_parent_not_confirmed"
            elif candidate_count > 1:
                status = "multiple_candidate_parents_ambiguous"
            else:
                status = "no_candidate_in_structured_sample"
            for rank, (prior, basis) in enumerate(candidates, start=1):
                candidate_edges.append({
                    "child_accession": current["accession"],
                    "candidate_parent_accession": prior["accession"],
                    "candidate_rank_by_recency": rank,
                    "candidate_basis": basis,
                    "child_subject_cik": current["subject_cik"],
                    "parent_subject_cik": prior["subject_cik"],
                    "child_family": current["family"],
                    "parent_family": prior["family"],
                    "child_acceptance_utc": current["acceptance_utc"],
                    "parent_acceptance_utc": prior["acceptance_utc"],
                    "explicit_person_cik_overlap": sorted(set(current["explicit_person_ciks"]) & set(prior["explicit_person_ciks"])),
                    "exact_person_name_overlap": sorted(set(current["person_names"]) & set(prior["person_names"])),
                    "cusip_overlap": sorted(set(current["cusips"]) & set(prior["cusips"])),
                    "confirmed_link": False,
                })
        else:
            status, candidate_count, candidates = "original_no_predecessor", 0, []
        lineage_rows.append({
            "accession": current["accession"],
            "family": current["family"],
            "form": current["form"],
            "is_amendment": is_amendment,
            "subject_cik": current["subject_cik"],
            "filer_cik": current["filer_cik"],
            "filing_date": current["filing_date"],
            "acceptance_utc": current["acceptance_utc"],
            "xml_previous_accession": previous,
            "lineage_status": status,
            "candidate_parent_count": candidate_count,
            "candidate_parent_accessions": [item[0]["accession"] for item in candidates],
            "automatic_event_collapse_permitted": False,
        })

    tag_counts = Counter(tag for row in records for tag in row["event_mechanism_tags"])
    amendment_rows = [row for row in lineage_rows if row["is_amendment"]]
    lineage_counts = Counter(row["lineage_status"] for row in amendment_rows)
    missing_explicit = sum(not bool(row["xml_previous_accession"]) for row in amendment_rows)
    summary = {
        "phase": "93-13dg-amendment-lineage-and-event-mechanism-audit",
        "status": "COMPLETE" if len(records) == len(events) == 200 and not errors else "FAIL",
        "input_structured_filings": len(events),
        "filings_reparsed": len(records),
        "raw_sha256_and_xml_identity_errors": errors,
        "amendments": len(amendment_rows),
        "amendments_with_explicit_previous_accession": len(amendment_rows) - missing_explicit,
        "amendments_missing_explicit_previous_accession": missing_explicit,
        "amendment_lineage_status_counts": dict(lineage_counts),
        "candidate_parent_edges": len(candidate_edges),
        "event_mechanism_tag_counts_nonexclusive": dict(tag_counts),
        "unclassified_filings": sum("unclassified_narrative" in row["event_mechanism_tags"] for row in records),
        "identity_rules": [
            "Subject CIK and form family are mandatory for every candidate parent.",
            "Candidate parent acceptance timestamp must be strictly earlier.",
            "Explicit reporting-person CIK overlap may support a candidate; exact reporting-person name overlap requires CUSIP overlap.",
            "If both filings contain CUSIPs, at least one CUSIP must overlap.",
            "Filer CIK, accession-prefix CIK and inferred first-person 13G CIK are never used as reporting-person identity.",
            "A unique candidate remains unconfirmed; no missing predecessor is automatically inferred.",
        ],
        "interpretation_limits": [
            "The 200 structured filings are a stratified pilot, not a complete issuer filing history.",
            "A parent outside the sample is not evidence that no predecessor exists.",
            "previousAccessionNumber is treated as an explicit reference, not assumed to be the immediate predecessor.",
            "Event tags are transparent keyword triage, not verified investor intent or a Smart Money label.",
            "No forward returns, feature selection, alpha test, vendor purchase or production change.",
        ],
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "production_changes_authorized": False,
    }
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "phase93_event_mechanism_audit.csv", records)
    write_csv(outdir / "phase93_amendment_lineage_audit.csv", lineage_rows)
    write_csv(outdir / "phase93_candidate_parent_edges.csv", candidate_edges)
    (outdir / "phase93_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["status"] != "COMPLETE":
        raise SystemExit(2)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase84-artifact-dir", type=Path, required=True)
    parser.add_argument("--phase91-artifact-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase93_audit"))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
