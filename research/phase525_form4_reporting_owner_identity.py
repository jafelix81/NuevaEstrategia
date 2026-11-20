from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from research import phase510_form4_structured_transaction_ledger as p510

PHASE = 525
PARSER_VERSION = "phase525-owner-v1"
DATA_DIR = Path("research/data/sec_form4_first_seen")
EVENTS_PATH = DATA_DIR / "events.csv"
DETAILS_PATH = DATA_DIR / "transaction_details.csv"
OWNER_PATH = DATA_DIR / "reporting_owners.csv"
DEFAULT_LIMIT = 10

OWNER_FIELDS = [
    "owner_identity_row_key", "accession", "form", "filing_date",
    "issuer_cik", "issuer_name", "issuer_trading_symbol_normalized",
    "period_of_report", "reporting_owner_count", "owner_index",
    "owner_cik_raw", "owner_cik", "owner_name",
    "is_director", "is_officer", "is_ten_percent_owner", "is_other",
    "officer_title", "other_text", "relationships_json",
    "owner_identity_status", "line_owner_link_status",
    "first_seen_at_utc", "first_seen_interval_lower_bound_utc",
    "first_seen_interval_upper_bound_utc", "first_seen_interval_status",
    "first_seen_poll_run_id", "acceptance_datetime_utc",
    "acceptance_clock_status", "detail_retrieved_at_utc",
    "submission_sha256", "source_xml_sha256", "remarks_text",
    "remarks_sha256", "remarks_flags_json", "aff10b5one_filing_flag",
    "parser_version", "parse_status", "signal_eligible",
    "transaction_line_attribution_verified",
]

REMARK_PATTERNS = {
    "exercise_price_payment_mention": r"\bpay(?:ment)?\s+(?:the\s+)?exercise\s+price\b",
    "tax_planning_mention": r"\btax\s+planning\b",
    "tax_or_withholding_mention": r"\b(?:tax|withhold(?:ing)?)\b",
    "rule_10b5_1_mention": r"10b5[\s-]?1",
    "open_market_mention": r"\bopen[\s-]?market\b",
    "compensation_or_vesting_mention": r"\b(?:compensation|award|vesting|restricted stock|stock unit)\b",
    "gift_or_donation_mention": r"\b(?:gift|donat(?:ion|ed))\b",
    "employee_plan_mention": r"\b(?:employee stock|employee benefit|purchase plan)\b",
    "automatic_sell_to_cover_mention": r"\b(?:automatic|sell[\s-]?to[\s-]?cover)\b",
    "option_exercise_mention": r"\b(?:option|exercise|cashless)\b",
}


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def direct_child(node: ET.Element | None, name: str) -> ET.Element | None:
    if node is None:
        return None
    wanted = name.lower()
    return next((child for child in list(node) if local_name(child.tag) == wanted), None)


def direct_children(node: ET.Element | None, name: str) -> list[ET.Element]:
    if node is None:
        return []
    wanted = name.lower()
    return [child for child in list(node) if local_name(child.tag) == wanted]


def node_text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    value = direct_child(node, "value")
    target = value if value is not None else node
    result = " ".join("".join(target.itertext()).split())
    return result or None


def child_text(node: ET.Element | None, name: str) -> str | None:
    return node_text(direct_child(node, name))


def normalize_flag(value: str | None) -> str:
    token = str(value or "").strip().upper()
    if token in {"1", "Y", "YES", "TRUE"}:
        return "true"
    if token in {"0", "N", "NO", "FALSE"}:
        return "false"
    return ""


def remarks_flags(remarks: str) -> dict:
    return {
        key: bool(re.search(pattern, remarks or "", flags=re.IGNORECASE))
        for key, pattern in REMARK_PATTERNS.items()
    }


def parse_owner_identity(raw: bytes | str) -> dict:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    if local_name(root.tag) != "ownershipdocument":
        raise ValueError("unexpected_form4_xml_root")

    parsed = p510.parse_form4_details(raw)
    remarks_node = direct_child(root, "remarks")
    remarks = node_text(remarks_node) or ""
    owner_nodes = direct_children(root, "reportingOwner")
    owners = []
    for index, owner_node in enumerate(owner_nodes, start=1):
        owner_id = direct_child(owner_node, "reportingOwnerId")
        relationship = direct_child(owner_node, "reportingOwnerRelationship")
        cik_raw = child_text(owner_id, "rptOwnerCik")
        cik = p510.p401.norm_cik(cik_raw) if cik_raw else None
        name = child_text(owner_id, "rptOwnerName")
        owner = {
            "owner_index": index,
            "owner_cik_raw": cik_raw,
            "owner_cik": cik,
            "owner_name": name,
            "is_director": normalize_flag(child_text(relationship, "isDirector")),
            "is_officer": normalize_flag(child_text(relationship, "isOfficer")),
            "is_ten_percent_owner": normalize_flag(child_text(relationship, "isTenPercentOwner")),
            "is_other": normalize_flag(child_text(relationship, "isOther")),
            "officer_title": child_text(relationship, "officerTitle"),
            "other_text": child_text(relationship, "otherText"),
        }
        owner["relationships_json"] = json.dumps(
            {k: owner[k] for k in (
                "is_director", "is_officer", "is_ten_percent_owner",
                "is_other", "officer_title", "other_text"
            )},
            sort_keys=True, separators=(",", ":"),
        )
        owner["owner_identity_status"] = "COMPLETE" if cik and name else "PARTIAL"
        owners.append(owner)

    return {
        "issuer_cik": parsed.get("issuer_cik"),
        "issuer_name": parsed.get("issuer_name"),
        "issuer_trading_symbol_normalized": parsed.get("issuer_trading_symbol_normalized"),
        "period_of_report": parsed.get("period_of_report"),
        "reporting_owner_count": len(owner_nodes),
        "aff10b5one_filing_flag": parsed.get("aff10b5one_filing_flag"),
        "owners": owners,
        "remarks_text": remarks,
        "remarks_flags": remarks_flags(remarks),
    }


def build_owner_rows(event: dict, metadata: dict, parsed: dict) -> list[dict]:
    accession = event["accession"]
    owner_count = int(parsed.get("reporting_owner_count") or 0)
    if owner_count == 1:
        line_link_status = "SINGLE_REPORTING_OWNER_FILING_GRAIN_ONLY"
    elif owner_count > 1:
        line_link_status = "MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK"
    else:
        line_link_status = "NO_REPORTING_OWNER"

    owners = parsed.get("owners") or []
    records = owners if owners else [{
        "owner_index": 0, "owner_cik_raw": None, "owner_cik": None,
        "owner_name": None, "is_director": "", "is_officer": "",
        "is_ten_percent_owner": "", "is_other": "", "officer_title": None,
        "other_text": None, "relationships_json": "{}",
        "owner_identity_status": "NO_REPORTING_OWNER",
    }]
    remarks = parsed.get("remarks_text") or ""
    remarks_hash = hashlib.sha256(remarks.encode("utf-8")).hexdigest() if remarks else ""
    remarks_json = json.dumps(parsed.get("remarks_flags") or {}, sort_keys=True, separators=(",", ":"))
    rows = []
    for owner in records:
        owner_index = int(owner.get("owner_index") or 0)
        identity_material = "|".join((
            accession, str(owner_index), PARSER_VERSION,
            str(metadata.get("xml_sha256") or ""),
        ))
        row = {
            "owner_identity_row_key": hashlib.sha256(identity_material.encode("utf-8")).hexdigest(),
            "accession": accession,
            "form": event.get("form"),
            "filing_date": event.get("filing_date"),
            "issuer_cik": parsed.get("issuer_cik"),
            "issuer_name": parsed.get("issuer_name"),
            "issuer_trading_symbol_normalized": parsed.get("issuer_trading_symbol_normalized"),
            "period_of_report": parsed.get("period_of_report"),
            "reporting_owner_count": owner_count,
            "owner_index": owner_index,
            "owner_cik_raw": owner.get("owner_cik_raw"),
            "owner_cik": owner.get("owner_cik"),
            "owner_name": owner.get("owner_name"),
            "is_director": owner.get("is_director"),
            "is_officer": owner.get("is_officer"),
            "is_ten_percent_owner": owner.get("is_ten_percent_owner"),
            "is_other": owner.get("is_other"),
            "officer_title": owner.get("officer_title"),
            "other_text": owner.get("other_text"),
            "relationships_json": owner.get("relationships_json"),
            "owner_identity_status": owner.get("owner_identity_status"),
            "line_owner_link_status": line_link_status,
            "first_seen_at_utc": event.get("first_seen_at_utc"),
            "first_seen_interval_lower_bound_utc": event.get("first_seen_interval_lower_bound_utc"),
            "first_seen_interval_upper_bound_utc": event.get("first_seen_interval_upper_bound_utc") or event.get("first_seen_at_utc"),
            "first_seen_interval_status": event.get("first_seen_interval_status"),
            "first_seen_poll_run_id": event.get("first_seen_poll_run_id"),
            "acceptance_datetime_utc": metadata.get("acceptance_datetime_utc"),
            "acceptance_clock_status": metadata.get("acceptance_clock_status"),
            "detail_retrieved_at_utc": metadata.get("detail_retrieved_at_utc"),
            "submission_sha256": metadata.get("submission_sha256"),
            "source_xml_sha256": metadata.get("xml_sha256"),
            "remarks_text": remarks,
            "remarks_sha256": remarks_hash,
            "remarks_flags_json": remarks_json,
            "aff10b5one_filing_flag": parsed.get("aff10b5one_filing_flag"),
            "parser_version": PARSER_VERSION,
            "parse_status": "parsed",
            "signal_eligible": False,
            "transaction_line_attribution_verified": False,
        }
        rows.append(row)
    return rows


def read_existing_accessions(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != OWNER_FIELDS:
            raise ValueError("owner_identity_ledger_header_mismatch")
        return {
            row.get("accession", "")
            for row in reader
            if row.get("parse_status") == "parsed" and row.get("accession")
        }


def append_owner_rows(path: Path, rows: list[dict]) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_keys: set[str] = set()
    write_header = not path.exists() or path.stat().st_size == 0
    if not write_header:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != OWNER_FIELDS:
                raise ValueError("owner_identity_ledger_header_mismatch")
            existing_keys = {row.get("owner_identity_row_key", "") for row in reader}
    pending = [row for row in rows if row.get("owner_identity_row_key") not in existing_keys]
    if not pending:
        return 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OWNER_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(pending)
    return len(pending)


def read_structured_accessions(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"accession", "detail_type", "parse_status"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("form4_detail_ledger_schema_invalid")
        seen = set()
        result = []
        for row in reader:
            accession = row.get("accession", "")
            if (
                row.get("detail_type") == "filing_header"
                and row.get("parse_status") == "parsed"
                and accession and accession not in seen
            ):
                seen.add(accession)
                result.append(accession)
        return result


def run_backfill(
    mode: str,
    limit: int,
    output_dir: Path,
    events_path: Path = EVENTS_PATH,
    details_path: Path = DETAILS_PATH,
    owner_path: Path = OWNER_PATH,
    fetcher=None,
) -> dict:
    if limit < 1 or limit > 50:
        raise ValueError("limit_must_be_between_1_and_50")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "phase": PHASE,
        "parser_version": PARSER_VERSION,
        "mode": mode,
        "limit": limit,
        "structured_accessions_seen": 0,
        "bounded_accessions_pending": 0,
        "attempted_accessions": 0,
        "accessions_parsed": 0,
        "single_owner_accessions": 0,
        "multi_owner_accessions": 0,
        "no_owner_accessions": 0,
        "partial_owner_identity_accessions": 0,
        "fetch_unresolved": 0,
        "parse_errors": 0,
        "owner_rows_appended": 0,
        "remaining_bounded_accessions": 0,
        "signal_eligible_rows": 0,
        "transaction_line_attribution_verified": False,
        "raw_xml_persisted": False,
    }
    if mode != "schedule":
        summary["disposition"] = "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE"
        (output_dir / "owner_identity_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return summary

    events = p510.read_events(events_path)
    event_by_accession = {row.get("accession"): row for row in events}
    structured = read_structured_accessions(details_path)
    completed = read_existing_accessions(owner_path)
    summary["structured_accessions_seen"] = len(structured)

    candidates = []
    for accession in structured:
        if accession in completed:
            continue
        event = event_by_accession.get(accession)
        if event is None:
            continue
        try:
            p510.validate_event(event)
        except ValueError:
            continue
        candidates.append(event)
    candidates.sort(key=lambda row: row.get("first_seen_at_utc", ""))

    summary["bounded_accessions_pending"] = len(candidates)
    selected = candidates[:limit]
    for event in selected:
        summary["attempted_accessions"] += 1
        metadata = p510.fetch_document(event, fetcher=fetcher)
        if metadata.get("fetch_status") != "retrieved":
            summary["fetch_unresolved"] += 1
            continue
        try:
            parsed = parse_owner_identity(metadata["xml"])
            rows = build_owner_rows(event, metadata, parsed)
        except Exception:
            summary["parse_errors"] += 1
            continue
        appended = append_owner_rows(owner_path, rows)
        summary["owner_rows_appended"] += appended
        summary["accessions_parsed"] += 1
        count = int(parsed.get("reporting_owner_count") or 0)
        if count == 1:
            summary["single_owner_accessions"] += 1
        elif count > 1:
            summary["multi_owner_accessions"] += 1
        else:
            summary["no_owner_accessions"] += 1
        if any(row.get("owner_identity_status") != "COMPLETE" for row in rows if row.get("owner_index", 0)):
            summary["partial_owner_identity_accessions"] += 1

    completed_after = read_existing_accessions(owner_path)
    summary["remaining_bounded_accessions"] = sum(
        1 for event in candidates if event.get("accession") not in completed_after
    )
    summary["disposition"] = "FILING_LEVEL_OWNER_IDENTITY_CAPTURED_NO_TRANSACTION_LINE_LINK"
    (output_dir / "owner_identity_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["schedule", "manual"], required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_backfill(args.mode, args.limit, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
