from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from research import phase401_form144a_full_parent_identity_census as p401
from research import phase496_form4_accession_payload_semantics_audit as p496

PHASE = 510
PARSER_VERSION = "phase510-v1"
DATA_DIR = Path("research/data/sec_form4_first_seen")
EVENTS_PATH = DATA_DIR / "events.csv"
DETAILS_PATH = DATA_DIR / "transaction_details.csv"
DEFAULT_LIMIT = 10

DETAIL_FIELDS = [
    "detail_row_key", "detail_type", "table_type", "row_index",
    "accession", "form", "is_amendment", "previous_accession",
    "feed_name", "feed_path_cik_unverified", "filing_url", "filing_date",
    "first_seen_at_utc", "first_seen_interval_lower_bound_utc",
    "first_seen_interval_upper_bound_utc", "first_seen_interval_status",
    "first_seen_poll_run_id", "first_seen_poll_started_utc",
    "first_seen_poll_ended_utc", "first_seen_is_upper_bound_not_exact_receipt",
    "detail_retrieved_at_utc", "acceptance_datetime_utc",
    "acceptance_clock_status", "submission_status", "xml_source",
    "submission_sha256", "xml_sha256", "source_hash_comparable",
    "source_hash_match_status", "parser_version", "parse_status", "parse_error",
    "issuer_cik", "issuer_name", "issuer_trading_symbol_raw",
    "issuer_trading_symbol_normalized", "period_of_report",
    "reporting_owner_count", "owner_count_bucket", "owner_attribution_status",
    "aff10b5one_filing_flag", "nonderivative_transaction_count",
    "derivative_transaction_count", "security_title", "transaction_date",
    "deemed_execution_date", "transaction_code", "transaction_form_type",
    "equity_swap_involved", "transaction_timeliness", "shares_raw",
    "shares_numeric", "price_per_share_raw", "price_per_share_numeric",
    "acquired_disposed_code", "shares_owned_following_raw",
    "shares_owned_following_numeric", "value_owned_following_raw",
    "value_owned_following_numeric", "direct_indirect",
    "nature_of_ownership", "conversion_exercise_price_raw",
    "conversion_exercise_price_numeric", "exercise_date", "expiration_date",
    "underlying_security_title", "underlying_security_shares_raw",
    "underlying_security_shares_numeric", "underlying_security_value_raw",
    "underlying_security_value_numeric", "footnote_ids_json",
    "footnote_flags_json", "footnote_text_hashes_json",
    "footnote_refs_resolved_count", "footnote_refs_unresolved_count",
    "transaction_fingerprint", "research_observation_eligible",
    "signal_eligible", "public_availability_certified",
    "same_day_intraday_use_authorized", "security_identity_verified",
    "historical_f80_membership_verified", "owner_attribution_verified",
    "transaction_semantics_verified", "economic_event_new_trade_authorized",
]

FOOTNOTE_PATTERNS = {
    "open_market_mention": r"\bopen[\s-]?market\b",
    "private_purchase_or_placement_mention": r"\bprivate\s+(?:purchase|placement|transaction)\b",
    "rule_10b5_1_mention": r"10b5[\s-]?1",
    "tax_or_withholding_mention": r"\b(?:tax|withhold(?:ing)?)\b",
    "trust_mention": r"\btrust(?:ee|s)?\b",
    "gift_or_donation_mention": r"\b(?:gift|donat(?:ion|ed))\b",
    "option_or_cashless_mention": r"\b(?:option|exercise|cashless)\b",
    "compensation_or_vesting_mention": r"\b(?:compensation|award|vesting|restricted stock|stock unit)\b",
    "employee_plan_mention": r"\b(?:employee stock|employee benefit|purchase plan)\b",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def text_value(node: ET.Element | None, name: str) -> str | None:
    child = direct_child(node, name)
    if child is None:
        return None
    value = direct_child(child, "value")
    target = value if value is not None else child
    result = " ".join("".join(target.itertext()).split())
    return result or None


def nested_value(node: ET.Element | None, parent: str, field: str) -> str | None:
    return text_value(direct_child(node, parent), field)


def parse_decimal(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip()
    negative = raw.startswith("(") and raw.endswith(")")
    raw = raw[1:-1] if negative else raw
    token = re.sub(r"[^0-9.+-]", "", raw)
    if not token:
        return None
    try:
        number = Decimal(token)
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite():
        return None
    if negative:
        number = -abs(number)
    return format(number.normalize(), "f")


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    token = str(value).strip()
    try:
        return date.fromisoformat(token[:10]).isoformat()
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(token[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def footnote_map(root: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in root.iter():
        if local_name(node.tag) != "footnote":
            continue
        footnote_id = str(node.attrib.get("id") or "").strip()
        content = " ".join("".join(node.itertext()).split())
        if footnote_id and content:
            result[footnote_id] = content
    return result


def row_footnote_ids(row: ET.Element) -> list[str]:
    found: set[str] = set()
    for node in row.iter():
        if local_name(node.tag) != "footnoteid":
            continue
        value = str(node.attrib.get("id") or "").strip()
        if not value:
            value = " ".join("".join(node.itertext()).split())
        if value:
            found.add(value)
    return sorted(found)


def classify_footnotes(ids: list[str], footnotes: dict[str, str]) -> tuple[dict, list[str], int]:
    texts = [footnotes[x] for x in ids if x in footnotes]
    combined = " ".join(texts)
    flags = {
        key: bool(re.search(pattern, combined, flags=re.IGNORECASE))
        for key, pattern in FOOTNOTE_PATTERNS.items()
    }
    hashes = sorted(hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts)
    return flags, hashes, len(ids) - len(texts)


def normalize_accession(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) != 18:
        return None
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def parse_form4_details(raw: bytes | str) -> dict:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    if local_name(root.tag) != "ownershipdocument":
        raise ValueError("unexpected_form4_xml_root")

    issuer = direct_child(root, "issuer")
    issuer_cik_raw = text_value(issuer, "issuerCik")
    issuer_cik = p401.norm_cik(issuer_cik_raw) if issuer_cik_raw else None
    issuer_name = text_value(issuer, "issuerName")
    issuer_symbol_raw = text_value(issuer, "issuerTradingSymbol")
    issuer_symbol = str(issuer_symbol_raw or "").strip().upper() or None

    owners = direct_children(root, "reportingOwner")
    owner_count = len(owners)
    if owner_count == 1:
        owner_status = "FILING_GRAIN_ONLY_SINGLE_OWNER"
    elif owner_count > 1:
        owner_status = "QUARANTINED_MULTI_OWNER_NO_LINE_LINK"
    else:
        owner_status = "UNKNOWN_NO_REPORTING_OWNER"

    aff_flag = p496.normalize_flag(p496.first_descendant_text(root, "aff10b5One"))
    previous_accession_raw = p496.first_descendant_text(root, "previousAccessionNumber")
    previous_accession = normalize_accession(previous_accession_raw) if previous_accession_raw else None
    footnotes = footnote_map(root)

    nonderivative_table = direct_child(root, "nonDerivativeTable")
    derivative_table = direct_child(root, "derivativeTable")
    nonderivative = direct_children(nonderivative_table, "nonDerivativeTransaction")
    derivative = direct_children(derivative_table, "derivativeTransaction")

    rows: list[dict] = []
    for table_type, source_rows in (("non_derivative", nonderivative), ("derivative", derivative)):
        for index, row in enumerate(source_rows, start=1):
            ids = row_footnote_ids(row)
            flags, hashes, unresolved = classify_footnotes(ids, footnotes)
            conversion = direct_child(row, "conversionOrExercisePrice")
            values = {
                "table_type": table_type,
                "row_index": index,
                "security_title": text_value(row, "securityTitle"),
                "transaction_date": parse_date(text_value(row, "transactionDate")),
                "deemed_execution_date": parse_date(text_value(row, "deemedExecutionDate")),
                "transaction_code": nested_value(row, "transactionCoding", "transactionCode"),
                "transaction_form_type": nested_value(row, "transactionCoding", "transactionFormType"),
                "equity_swap_involved": nested_value(row, "transactionCoding", "equitySwapInvolved"),
                "transaction_timeliness": nested_value(row, "transactionCoding", "transactionTimeliness"),
                "shares_raw": nested_value(row, "transactionAmounts", "transactionShares"),
                "shares_numeric": parse_decimal(nested_value(row, "transactionAmounts", "transactionShares")),
                "price_per_share_raw": nested_value(row, "transactionAmounts", "transactionPricePerShare"),
                "price_per_share_numeric": parse_decimal(nested_value(row, "transactionAmounts", "transactionPricePerShare")),
                "acquired_disposed_code": nested_value(row, "transactionAmounts", "transactionAcquiredDisposedCode"),
                "shares_owned_following_raw": nested_value(row, "postTransactionAmounts", "sharesOwnedFollowingTransaction"),
                "shares_owned_following_numeric": parse_decimal(nested_value(row, "postTransactionAmounts", "sharesOwnedFollowingTransaction")),
                "value_owned_following_raw": nested_value(row, "postTransactionAmounts", "valueOfSharesOwnedFollowingTransaction"),
                "value_owned_following_numeric": parse_decimal(nested_value(row, "postTransactionAmounts", "valueOfSharesOwnedFollowingTransaction")),
                "direct_indirect": nested_value(row, "ownershipNature", "directOrIndirectOwnership"),
                "nature_of_ownership": nested_value(row, "ownershipNature", "natureOfOwnership"),
                "conversion_exercise_price_raw": text_value(conversion, "value") if conversion is not None else None,
                "conversion_exercise_price_numeric": parse_decimal(text_value(conversion, "value")) if conversion is not None else None,
                "exercise_date": parse_date(text_value(row, "exerciseDate")),
                "expiration_date": parse_date(text_value(row, "expirationDate")),
                "underlying_security_title": text_value(direct_child(row, "underlyingSecurity"), "underlyingSecurityTitle"),
                "underlying_security_shares_raw": text_value(direct_child(row, "underlyingSecurity"), "underlyingSecurityShares"),
                "underlying_security_shares_numeric": parse_decimal(text_value(direct_child(row, "underlyingSecurity"), "underlyingSecurityShares")),
                "underlying_security_value_raw": text_value(direct_child(row, "underlyingSecurity"), "underlyingSecurityValue"),
                "underlying_security_value_numeric": parse_decimal(text_value(direct_child(row, "underlyingSecurity"), "underlyingSecurityValue")),
                "footnote_ids_json": json.dumps(ids, separators=(",", ":")),
                "footnote_flags_json": json.dumps(flags, sort_keys=True, separators=(",", ":")),
                "footnote_text_hashes_json": json.dumps(hashes, separators=(",", ":")),
                "footnote_refs_resolved_count": len(ids) - unresolved,
                "footnote_refs_unresolved_count": unresolved,
            }
            fingerprint = hashlib.sha256(
                json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            values["transaction_fingerprint"] = fingerprint
            rows.append(values)

    return {
        "issuer_cik": issuer_cik,
        "issuer_name": issuer_name,
        "issuer_trading_symbol_raw": issuer_symbol_raw,
        "issuer_trading_symbol_normalized": issuer_symbol,
        "period_of_report": parse_date(text_value(root, "periodOfReport")),
        "reporting_owner_count": owner_count,
        "owner_count_bucket": "zero" if owner_count == 0 else "single" if owner_count == 1 else "multiple",
        "owner_attribution_status": owner_status,
        "aff10b5one_filing_flag": aff_flag,
        "previous_accession": previous_accession,
        "nonderivative_transaction_count": len(nonderivative),
        "derivative_transaction_count": len(derivative),
        "transaction_rows": rows,
    }


def validate_event(event: dict) -> None:
    accession = str(event.get("accession") or "")
    url = str(event.get("filing_url") or "")
    parsed = urlparse(url)
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise ValueError("invalid_accession")
    if parsed.scheme != "https" or parsed.netloc != "www.sec.gov" or "/Archives/edgar/data/" not in parsed.path:
        raise ValueError("filing_url_outside_sec_archive")
    if accession.replace("-", "") not in parsed.path:
        raise ValueError("accession_not_in_filing_url")
    if event.get("first_seen_interval_status") != "BOUNDED_METADATA_ONLY":
        raise ValueError("event_interval_not_bounded")
    if not event.get("first_seen_interval_lower_bound_utc") or not event.get("first_seen_at_utc"):
        raise ValueError("event_interval_clock_missing")
    if str(event.get("first_seen_is_upper_bound_not_exact_receipt", "")).lower() not in {"true", "t", "1"}:
        raise ValueError("first_seen_upper_bound_semantics_missing")


def fetch_document(event: dict, fetcher=None) -> dict:
    validate_event(event)
    accession = event["accession"]
    base = event["filing_url"].rsplit("/", 1)[0]

    def get(url: str) -> bytes:
        if fetcher is not None:
            return fetcher(url)
        return p401.fetch_bytes(url, sec=True, timeout=45, retries=2)

    submission = None
    submission_status = "unresolved"
    submission_sha = None
    acceptance_utc = None
    try:
        submission = get(f"{base}/{accession}.txt")
        submission_status = "retrieved"
        submission_sha = hashlib.sha256(submission).hexdigest()
        try:
            _accepted_et, acceptance_utc = p496.parse_acceptance_submission(submission)
        except Exception:
            acceptance_utc = None
    except Exception as exc:
        submission_status = f"unresolved:{type(exc).__name__}:{str(exc)[:120]}"

    xml = p496.extract_ownership_xml(submission) if submission else None
    xml_source = "complete_submission" if xml is not None else None
    xml_fetch_error = None
    if xml is None:
        try:
            xml = get(f"{base}/primary_doc.xml")
            xml_source = "primary_doc.xml"
        except Exception as exc:
            xml_fetch_error = f"{type(exc).__name__}:{str(exc)[:160]}"

    if xml is None:
        return {
            "fetch_status": "unresolved",
            "submission_status": submission_status,
            "submission_sha256": submission_sha,
            "xml_fetch_error": xml_fetch_error,
        }

    return {
        "fetch_status": "retrieved",
        "submission_status": submission_status,
        "submission_sha256": submission_sha,
        "xml_source": xml_source,
        "xml_sha256": hashlib.sha256(xml).hexdigest(),
        "xml": xml,
        "acceptance_datetime_utc": acceptance_utc,
        "acceptance_clock_status": "PARSED_NOT_EXACT_PUBLIC_AVAILABILITY" if acceptance_utc else "UNRESOLVED",
        "detail_retrieved_at_utc": now_utc(),
    }


def build_detail_rows(event: dict, metadata: dict, parsed: dict | None, parse_error: str = "") -> list[dict]:
    validate_event(event)
    accession = event["accession"]
    form = event.get("form", "")
    is_amendment = form == "4/A"
    parse_status = "parsed" if parsed is not None else "parse_error"
    issuer = parsed or {}
    common = {
        "accession": accession,
        "form": form,
        "is_amendment": is_amendment,
        "previous_accession": issuer.get("previous_accession") if parsed else None,
        "feed_name": event.get("feed_name"),
        "feed_path_cik_unverified": event.get("feed_path_cik_unverified"),
        "filing_url": event.get("filing_url"),
        "filing_date": event.get("filing_date"),
        "first_seen_at_utc": event.get("first_seen_at_utc"),
        "first_seen_interval_lower_bound_utc": event.get("first_seen_interval_lower_bound_utc"),
        "first_seen_interval_upper_bound_utc": event.get("first_seen_interval_upper_bound_utc") or event.get("first_seen_at_utc"),
        "first_seen_interval_status": event.get("first_seen_interval_status"),
        "first_seen_poll_run_id": event.get("first_seen_poll_run_id"),
        "first_seen_poll_started_utc": event.get("first_seen_poll_started_utc"),
        "first_seen_poll_ended_utc": event.get("first_seen_poll_ended_utc"),
        "first_seen_is_upper_bound_not_exact_receipt": event.get("first_seen_is_upper_bound_not_exact_receipt"),
        "detail_retrieved_at_utc": metadata.get("detail_retrieved_at_utc"),
        "acceptance_datetime_utc": metadata.get("acceptance_datetime_utc"),
        "acceptance_clock_status": metadata.get("acceptance_clock_status"),
        "submission_status": metadata.get("submission_status"),
        "xml_source": metadata.get("xml_source"),
        "submission_sha256": metadata.get("submission_sha256"),
        "xml_sha256": metadata.get("xml_sha256"),
        "source_hash_comparable": False,
        "source_hash_match_status": "NOT_COMPARABLE_NO_ORIGINAL_XML_HASH_IN_EVENT_LEDGER",
        "parser_version": PARSER_VERSION,
        "parse_status": parse_status,
        "parse_error": parse_error,
        "issuer_cik": issuer.get("issuer_cik"),
        "issuer_name": issuer.get("issuer_name"),
        "issuer_trading_symbol_raw": issuer.get("issuer_trading_symbol_raw"),
        "issuer_trading_symbol_normalized": issuer.get("issuer_trading_symbol_normalized"),
        "period_of_report": issuer.get("period_of_report"),
        "reporting_owner_count": issuer.get("reporting_owner_count"),
        "owner_count_bucket": issuer.get("owner_count_bucket"),
        "owner_attribution_status": issuer.get("owner_attribution_status"),
        "aff10b5one_filing_flag": issuer.get("aff10b5one_filing_flag"),
        "nonderivative_transaction_count": issuer.get("nonderivative_transaction_count"),
        "derivative_transaction_count": issuer.get("derivative_transaction_count"),
        "research_observation_eligible": False,
        "signal_eligible": False,
        "public_availability_certified": False,
        "same_day_intraday_use_authorized": False,
        "security_identity_verified": False,
        "historical_f80_membership_verified": False,
        "owner_attribution_verified": False,
        "transaction_semantics_verified": False,
        "economic_event_new_trade_authorized": False,
    }

    header_payload = {"detail_type": "filing_header", "table_type": "", "row_index": 0, **common}
    header_fingerprint = hashlib.sha256(
        json.dumps(header_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    header_payload["transaction_fingerprint"] = header_fingerprint
    header_payload["detail_row_key"] = hashlib.sha256(
        f"{accession}|filing_header|{header_fingerprint}".encode("utf-8")
    ).hexdigest()
    rows = [header_payload]

    if parsed is not None:
        for transaction in parsed["transaction_rows"]:
            payload = {"detail_type": "transaction_row", **common, **transaction}
            payload["detail_row_key"] = hashlib.sha256(
                f"{accession}|{transaction['table_type']}|{transaction['row_index']}|{transaction['transaction_fingerprint']}".encode("utf-8")
            ).hexdigest()
            rows.append(payload)

    return [{field: row.get(field) for field in DETAIL_FIELDS} for row in rows]


def read_events(path: Path) -> list[dict]:
    required = {
        "accession", "form", "filing_url", "first_seen_at_utc",
        "first_seen_interval_lower_bound_utc", "first_seen_interval_status",
        "first_seen_is_upper_bound_not_exact_receipt",
    }
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("form4_event_ledger_schema_invalid")
        return list(reader)


def read_completed_accessions(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or reader.fieldnames != DETAIL_FIELDS:
            raise ValueError("form4_detail_ledger_schema_invalid")
        return {
            row.get("accession", "")
            for row in reader
            if row.get("detail_type") == "filing_header"
            and row.get("parse_status") in {"parsed", "parse_error"}
            and row.get("accession")
        }


def append_detail_rows(path: Path, rows: list[dict]) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_keys: set[str] = set()
    write_header = not path.exists() or path.stat().st_size == 0
    if not write_header:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != DETAIL_FIELDS:
                raise ValueError("form4_detail_ledger_header_mismatch")
            existing_keys = {row.get("detail_row_key", "") for row in reader if row.get("detail_row_key")}
    pending = [row for row in rows if row.get("detail_row_key") not in existing_keys]
    if not pending:
        return 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(pending)
    return len(pending)


def run_backfill(
    mode: str,
    limit: int,
    output_dir: Path,
    events_path: Path = EVENTS_PATH,
    details_path: Path = DETAILS_PATH,
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
        "attempted_accessions": 0,
        "accessions_parsed": 0,
        "accessions_with_parse_error": 0,
        "fetch_unresolved": 0,
        "detail_rows_appended": 0,
        "remaining_bounded_accessions": 0,
        "signal_eligible_count": 0,
        "research_observation_eligible_count": 0,
        "public_availability_certified": False,
        "raw_xml_persisted": False,
        "alpha_test_authorized": False,
    }
    if mode != "schedule":
        summary["disposition"] = "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE"
        (output_dir / "backfill_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return summary

    events = read_events(events_path)
    completed = read_completed_accessions(details_path)
    candidates = []
    for event in events:
        if event.get("first_seen_interval_status") != "BOUNDED_METADATA_ONLY":
            continue
        if event.get("accession") in completed:
            continue
        try:
            validate_event(event)
        except ValueError:
            continue
        candidates.append(event)
    candidates.sort(key=lambda row: row.get("first_seen_at_utc", ""), reverse=True)
    selected = candidates[:limit]

    for event in selected:
        summary["attempted_accessions"] += 1
        metadata = fetch_document(event, fetcher=fetcher)
        if metadata.get("fetch_status") != "retrieved":
            summary["fetch_unresolved"] += 1
            continue
        try:
            parsed = parse_form4_details(metadata["xml"])
            rows = build_detail_rows(event, metadata, parsed)
            summary["accessions_parsed"] += 1
        except Exception as exc:
            error = f"{type(exc).__name__}:{str(exc)[:180]}"
            rows = build_detail_rows(event, metadata, None, parse_error=error)
            summary["accessions_with_parse_error"] += 1
        summary["detail_rows_appended"] += append_detail_rows(details_path, rows)
        completed.add(event["accession"])

    summary["remaining_bounded_accessions"] = sum(
        1 for event in events
        if event.get("first_seen_interval_status") == "BOUNDED_METADATA_ONLY"
        and event.get("accession") not in completed
    )
    summary["disposition"] = "STRUCTURED_DETAILS_CAPTURED_NON_SIGNAL"
    (output_dir / "backfill_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["schedule", "manual"], required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = run_backfill(args.mode, args.limit, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
