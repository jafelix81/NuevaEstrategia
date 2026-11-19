from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from research import phase401_form144a_full_parent_identity_census as p401
from research.phase403_sec_form144_first_seen_capture import (
    parse_acceptance_html,
    parse_acceptance_submission,
)

SOURCE_RUN_ID = "44440313382"
EXPECTED_ACCESSIONS = 637
REQUIRED_EVENT_FIELDS = {
    "accession", "form", "filing_date", "filing_url",
    "feed_path_cik_unverified", "feed_updated_utc",
    "first_seen_at_utc", "first_seen_interval_lower_bound_utc",
    "first_seen_interval_status", "first_seen_poll_run_id",
    "first_seen_is_upper_bound_not_exact_receipt",
}


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def direct_child(node: ET.Element | None, name: str) -> ET.Element | None:
    if node is None:
        return None
    wanted = name.lower()
    return next((x for x in list(node) if local_name(x.tag) == wanted), None)


def direct_children(node: ET.Element | None, name: str) -> list[ET.Element]:
    if node is None:
        return []
    wanted = name.lower()
    return [x for x in list(node) if local_name(x.tag) == wanted]


def direct_text(node: ET.Element | None, name: str) -> str | None:
    child = direct_child(node, name)
    if child is None:
        return None
    value = direct_child(child, "value")
    target = value if value is not None else child
    text = "".join(target.itertext()).strip()
    return text or None


def nested_value(node: ET.Element | None, parent_name: str, field_name: str) -> str | None:
    return direct_text(direct_child(node, parent_name), field_name)


def descendants(root: ET.Element, name: str) -> list[ET.Element]:
    wanted = name.lower()
    return [x for x in root.iter() if local_name(x.tag) == wanted]


def first_descendant_text(root: ET.Element, name: str) -> str | None:
    values = []
    for node in descendants(root, name):
        value = "".join(node.itertext()).strip()
        if value:
            values.append(value)
    unique = sorted(set(values))
    return unique[0] if len(unique) == 1 else None


def extract_ownership_xml(submission: bytes) -> bytes | None:
    text = submission.decode("latin-1", "replace")
    blocks = re.findall(r"<XML>\s*(.*?)\s*</XML>", text, flags=re.I | re.S)
    for block in blocks:
        if re.search(r"<\s*ownershipDocument\b", block, flags=re.I):
            return block.encode("utf-8", "replace")
    if re.search(r"<\s*ownershipDocument\b", text, flags=re.I):
        return text.encode("utf-8", "replace")
    return None


def normalize_flag(value: str | None) -> str:
    if value is None:
        return "unknown"
    token = value.strip().lower()
    if token in {"1", "true", "yes"}:
        return "yes"
    if token in {"0", "false", "no"}:
        return "no"
    return "unknown"


def parse_form4_xml(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    if local_name(root.tag) != "ownershipdocument":
        raise ValueError("unexpected_form4_xml_root")

    issuer = direct_child(root, "issuer")
    issuer_cik = p401.norm_cik(direct_text(issuer, "issuerCik"))
    issuer_name = direct_text(issuer, "issuerName")
    issuer_symbol_raw = direct_text(issuer, "issuerTradingSymbol")
    issuer_symbol = (issuer_symbol_raw or "").strip().upper() or None

    owners = direct_children(root, "reportingOwner")
    role_counts = Counter()
    for owner in owners:
        relationship = direct_child(owner, "reportingOwnerRelationship")
        for flag in ("isDirector", "isOfficer", "isTenPercentOwner", "isOther"):
            if normalize_flag(direct_text(relationship, flag)) == "yes":
                role_counts[flag] += 1

    nonderivative_table = direct_child(root, "nonDerivativeTable")
    derivative_table = direct_child(root, "derivativeTable")
    nonderivative_rows = direct_children(nonderivative_table, "nonDerivativeTransaction")
    derivative_rows = direct_children(derivative_table, "derivativeTransaction")

    code_counts = Counter()
    pa_titles = set()
    pa_rows = 0
    pa_acquired_shares = 0.0
    pa_rows_with_amount = 0
    for row in nonderivative_rows:
        code = nested_value(row, "transactionCoding", "transactionCode")
        acquired = nested_value(row, "transactionAmounts", "transactionAcquiredDisposedCode")
        if code and acquired:
            code_counts[f"{code.upper()}/{acquired.upper()}"] += 1
        if code and code.upper() == "P" and acquired and acquired.upper() == "A":
            pa_rows += 1
            title = direct_text(row, "securityTitle")
            if title:
                pa_titles.add(title.strip().upper())
            shares = nested_value(row, "transactionAmounts", "transactionShares")
            try:
                amount = float(str(shares).replace(",", "")) if shares else None
            except (TypeError, ValueError):
                amount = None
            if amount is not None:
                pa_acquired_shares += amount
                pa_rows_with_amount += 1

    aff_flag = first_descendant_text(root, "aff10b5One")
    return {
        "issuer_cik": issuer_cik,
        "issuer_name_present": bool(issuer_name),
        "issuer_symbol_raw": issuer_symbol_raw,
        "issuer_symbol": issuer_symbol,
        "owner_count": len(owners),
        "owner_role_counts": dict(role_counts),
        "nonderivative_transaction_count": len(nonderivative_rows),
        "derivative_transaction_count": len(derivative_rows),
        "transaction_code_acquired_disposed_counts": dict(code_counts),
        "p_acquired_rows": pa_rows,
        "p_acquired_rows_with_amount": pa_rows_with_amount,
        "p_acquired_shares_sum": pa_acquired_shares,
        "p_acquired_security_title_count": len(pa_titles),
        "aff10b5one": normalize_flag(aff_flag),
    }


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def seconds_between(later: str | None, earlier: str | None) -> float | None:
    a, b = parse_utc(later), parse_utc(earlier)
    return (a - b).total_seconds() if a and b else None


def load_events(path: Path, expected_count: int = EXPECTED_ACCESSIONS) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_EVENT_FIELDS.issubset(set(reader.fieldnames)):
            raise ValueError("form4_event_ledger_schema_invalid")
        for row in reader:
            if row.get("first_seen_poll_run_id") != SOURCE_RUN_ID:
                continue
            rows.append(row)

    if len(rows) != expected_count:
        raise ValueError(f"expected_{expected_count}_source_events_found_{len(rows)}")
    accessions = [x.get("accession", "") for x in rows]
    if any(not re.fullmatch(r"\d{10}-\d{2}-\d{6}", x) for x in accessions):
        raise ValueError("accession_format_invalid")
    if len(set(accessions)) != len(accessions):
        raise ValueError("duplicate_canonical_accession")
    for row in rows:
        if row.get("form") != "4":
            raise ValueError("unexpected_form_in_source_poll")
        if row.get("first_seen_interval_status") != "BOUNDED_METADATA_ONLY":
            raise ValueError("source_event_interval_not_bounded")
        if str(row.get("first_seen_is_upper_bound_not_exact_receipt", "")).lower() not in {"true", "t", "1"}:
            raise ValueError("first_seen_upper_bound_semantics_missing")
        if not all(row.get(k) for k in (
            "filing_url", "first_seen_at_utc", "first_seen_interval_lower_bound_utc"
        )):
            raise ValueError("required_temporal_or_url_field_missing")
        lower = parse_utc(row["first_seen_interval_lower_bound_utc"])
        upper = parse_utc(row["first_seen_at_utc"])
        if lower is None or upper is None or lower >= upper:
            raise ValueError("bounded_interval_clock_invalid")
        parsed = urlparse(row["filing_url"])
        if parsed.scheme != "https" or parsed.netloc != "www.sec.gov" or "/Archives/edgar/data/" not in parsed.path:
            raise ValueError("filing_url_outside_sec_archive")
        if row["accession"].replace("-", "") not in parsed.path:
            raise ValueError("accession_not_in_filing_url")
    return rows, digest


def _index_payload(event: dict, fetcher) -> tuple[bytes | None, str | None, str | None, str | None]:
    original_url = event["filing_url"]
    base = original_url.rsplit("/", 1)[0]
    candidates = [original_url]
    if original_url.endswith("-index.htm"):
        candidates.append(original_url[:-len("-index.htm")] + "-index-headers.html")
    for url in candidates:
        try:
            raw = fetcher(url)
            accepted_et, accepted_utc, filing_date = parse_acceptance_html(raw)
            if accepted_utc:
                return raw, accepted_et, accepted_utc, filing_date
        except Exception:
            continue
    return None, None, None, None


def _submission_payload(event: dict, fetcher) -> tuple[bytes | None, str | None, str | None]:
    base = event["filing_url"].rsplit("/", 1)[0]
    url = f"{base}/{event['accession']}.txt"
    try:
        raw = fetcher(url)
        accepted_et, accepted_utc = parse_acceptance_submission(raw)
        return raw, accepted_et, accepted_utc
    except Exception:
        return None, None, None


def process_event(event: dict, fetcher) -> dict:
    index_raw, index_et, index_utc, index_filing_date = _index_payload(event, fetcher)
    submission_raw, header_et, header_utc = _submission_payload(event, fetcher)
    xml_raw = extract_ownership_xml(submission_raw) if submission_raw else None
    xml_source = "complete_submission" if xml_raw else "unresolved"
    if xml_raw is None:
        base = event["filing_url"].rsplit("/", 1)[0]
        try:
            xml_raw = fetcher(f"{base}/primary_doc.xml")
            xml_source = "primary_doc.xml"
        except Exception:
            xml_raw = None

    parsed = None
    xml_status = "unresolved"
    if xml_raw:
        try:
            parsed = parse_form4_xml(xml_raw)
            xml_status = "parsed"
        except Exception as exc:
            xml_status = f"parse_error:{type(exc).__name__}:{str(exc)[:80]}"

    accepted_match = bool(header_utc and index_utc and header_utc == index_utc)
    first_seen = event.get("first_seen_at_utc")
    first_seen_delta = seconds_between(first_seen, header_utc)
    feed_delta = seconds_between(event.get("feed_updated_utc"), header_utc)
    timing_anomaly = first_seen_delta is not None and first_seen_delta < 0
    filing_date_match = bool(index_filing_date and event.get("filing_date") == index_filing_date)

    return {
        "index_retrieved": index_raw is not None,
        "index_acceptance_parsed": index_utc is not None,
        "submission_retrieved": submission_raw is not None,
        "header_acceptance_parsed": header_utc is not None,
        "acceptance_match": accepted_match,
        "filing_date_match": filing_date_match,
        "timing_anomaly": timing_anomaly,
        "first_seen_upper_minus_acceptance_seconds": first_seen_delta,
        "feed_updated_minus_acceptance_seconds": feed_delta,
        "xml_status": xml_status,
        "xml_source": xml_source,
        "parsed": parsed,
        "index_sha256": hashlib.sha256(index_raw).hexdigest() if index_raw else None,
        "submission_sha256": hashlib.sha256(submission_raw).hexdigest() if submission_raw else None,
        "xml_sha256": hashlib.sha256(xml_raw).hexdigest() if xml_raw else None,
    }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * pct))))
    return float(ordered[index])


def audit_events(events: list[dict], fetcher) -> dict:
    counters = Counter()
    owner_counts = Counter()
    aff_flags = Counter()
    transaction_counts = Counter()
    issuer_symbols = defaultdict(set)
    symbol_issuers = defaultdict(set)
    issuer_ciks_seen = set()
    all_symbols_seen = set()
    payload_parts = []
    timing_values = []
    feed_delta_values = []
    xml_errors = Counter()
    route_path_mismatches = 0
    pa_single_owner = pa_multi_owner = pa_zero_owner = 0
    pa_multi_class_filings = 0
    parsed_accessions = 0
    issuer_cik_resolved = 0
    issuer_symbol_present = 0
    distinct_owner_role_counts = Counter()

    for event_index, event in enumerate(events, start=1):
        result = process_event(event, fetcher)
        if event_index % 50 == 0 or event_index == len(events):
            print(f"PHASE496_PROGRESS={event_index}/{len(events)}", flush=True)
        counters["attempted"] += 1
        for key in ("index_retrieved", "index_acceptance_parsed", "submission_retrieved",
                    "header_acceptance_parsed", "acceptance_match", "filing_date_match", "timing_anomaly"):
            if result[key]:
                counters[key] += 1
        if result["first_seen_upper_minus_acceptance_seconds"] is not None:
            timing_values.append(result["first_seen_upper_minus_acceptance_seconds"])
        if result["feed_updated_minus_acceptance_seconds"] is not None:
            feed_delta_values.append(result["feed_updated_minus_acceptance_seconds"])

        path_match = re.search(r"/data/(\d+)/", urlparse(event["filing_url"]).path)
        route_cik = p401.norm_cik(path_match.group(1)) if path_match else None
        feed_cik = p401.norm_cik(event.get("feed_path_cik_unverified"))
        if route_cik and feed_cik and route_cik != feed_cik:
            route_path_mismatches += 1

        for digest in (result["index_sha256"], result["submission_sha256"], result["xml_sha256"]):
            if digest:
                payload_parts.append(f"{event['accession']}|{digest}")

        if result["xml_status"] != "parsed":
            xml_errors[result["xml_status"]] += 1
            continue

        parsed = result["parsed"]
        parsed_accessions += 1
        counters["xml_parsed"] += 1
        owner_count = parsed["owner_count"]
        owner_bucket = "zero" if owner_count == 0 else "single" if owner_count == 1 else "multiple"
        owner_counts[owner_bucket] += 1
        aff_flags[parsed["aff10b5one"]] += 1
        for key, value in parsed["transaction_code_acquired_disposed_counts"].items():
            transaction_counts[key] += value
        for key, value in parsed["owner_role_counts"].items():
            distinct_owner_role_counts[key] += value

        issuer_cik = parsed.get("issuer_cik")
        symbol = parsed.get("issuer_symbol")
        if issuer_cik:
            issuer_cik_resolved += 1
            issuer_ciks_seen.add(issuer_cik)
            if symbol:
                issuer_symbols[issuer_cik].add(symbol)
        if symbol:
            issuer_symbol_present += 1
            all_symbols_seen.add(symbol)
            if issuer_cik:
                symbol_issuers[symbol].add(issuer_cik)

        pa = parsed["p_acquired_rows"]
        if pa:
            if owner_count == 1:
                pa_single_owner += pa
            elif owner_count > 1:
                pa_multi_owner += pa
            else:
                pa_zero_owner += pa
            if parsed["p_acquired_security_title_count"] > 1:
                pa_multi_class_filings += 1

    payload_manifest = "\n".join(sorted(payload_parts)).encode("utf-8")
    unique_issuers = issuer_ciks_seen
    unique_symbols = all_symbols_seen
    issuer_multi_symbol = sum(len(v) > 1 for v in issuer_symbols.values())
    symbol_multi_issuer = sum(len(v) > 1 for v in symbol_issuers.values())

    return {
        "phase": 496,
        "source": {
            "poll_run_id": SOURCE_RUN_ID,
            "event_count": len(events),
            "forms": dict(Counter(x.get("form") for x in events)),
            "interval_statuses": dict(Counter(x.get("first_seen_interval_status") for x in events)),
            "first_seen_interval_lower_bound_utc": min(x["first_seen_interval_lower_bound_utc"] for x in events),
            "first_seen_upper_bound_min_utc": min(x["first_seen_at_utc"] for x in events),
            "first_seen_upper_bound_max_utc": max(x["first_seen_at_utc"] for x in events),
        },
        "retrieval": {
            "counts": dict(counters),
            "xml_parse_status_counts": dict(xml_errors),
            "acceptance_header_index_match_rate": (
                counters["acceptance_match"] / min(counters["header_acceptance_parsed"], counters["index_acceptance_parsed"])
                if min(counters["header_acceptance_parsed"], counters["index_acceptance_parsed"]) else None
            ),
            "first_seen_upper_minus_acceptance_seconds": {
                "n": len(timing_values), "min": min(timing_values) if timing_values else None,
                "median": statistics.median(timing_values) if timing_values else None,
                "p90": percentile(timing_values, 0.90), "max": max(timing_values) if timing_values else None,
                "negative_anomalies": counters["timing_anomaly"],
            },
            "feed_updated_minus_acceptance_seconds": {
                "n": len(feed_delta_values), "median": statistics.median(feed_delta_values) if feed_delta_values else None,
                "p10": percentile(feed_delta_values, 0.10), "p90": percentile(feed_delta_values, 0.90),
            },
            "route_path_cik_mismatch_count": route_path_mismatches,
            "payload_manifest_sha256": hashlib.sha256(payload_manifest).hexdigest(),
            "raw_payloads_persisted": False,
        },
        "transaction_semantics": {
            "xml_parsed_accessions": parsed_accessions,
            "owner_count_buckets": dict(owner_counts),
            "aff10b5one_filing_flags": dict(aff_flags),
            "transaction_code_acquired_disposed_counts": dict(transaction_counts),
            "p_acquired_transaction_rows_by_owner_count": {
                "single_owner": pa_single_owner, "multiple_owner": pa_multi_owner, "zero_owner": pa_zero_owner,
            },
            "p_acquired_multi_security_title_filings": pa_multi_class_filings,
            "issuer_cik_resolved_accessions": issuer_cik_resolved,
            "issuer_symbol_present_accessions": issuer_symbol_present,
            "distinct_issuer_ciks": len(unique_issuers),
            "distinct_as_filed_symbols": len(unique_symbols),
            "issuer_ciks_with_multiple_symbols_in_sample": issuer_multi_symbol,
            "symbols_linked_to_multiple_issuer_ciks": symbol_multi_issuer,
            "owner_role_flag_counts": dict(distinct_owner_role_counts),
            "p_code_is_not_confirmed_open_market": True,
            "multi_owner_rows_not_attributed_to_individual_owners": True,
            "aff10b5one_missing_is_unknown": True,
        },
        "eligibility": {
            "historical_f80_membership_verified": False,
            "public_availability_certified": False,
            "research_observation_eligible": 0,
            "signal_eligible": 0,
            "alpha_test_authorized": False,
            "forward_returns_used": False,
            "oos_used": False,
            "bootstrap_used": False,
            "loo_used": False,
            "holdout_used": False,
            "f80_changed": False,
            "production_changed": False,
            "raw_payloads_persisted": False,
            "transaction_level_rows_persisted": False,
        },
        "decision": {
            "disposition": "PAYLOAD_AND_ACCEPTANCE_FEASIBILITY_ONLY",
            "next_gate": "effective_dated_security_class_and_historical_f80_membership_reconciliation",
            "do_not_infer_smart_money_from_form4_alone": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=EXPECTED_ACCESSIONS)
    args = parser.parse_args()

    events, input_sha = load_events(args.events, args.expected_count)

    def fetcher(url: str) -> bytes:
        return p401.fetch_bytes(url, sec=True, timeout=60, retries=3)

    result = audit_events(events, fetcher)
    result["source"]["event_ledger_sha256"] = input_sha
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "phase": 496,
        "attempted": result["retrieval"]["counts"].get("attempted", 0),
        "xml_parsed": result["transaction_semantics"]["xml_parsed_accessions"],
        "acceptance_header": result["retrieval"]["counts"].get("header_acceptance_parsed", 0),
        "acceptance_index": result["retrieval"]["counts"].get("index_acceptance_parsed", 0),
        "acceptance_matches": result["retrieval"]["counts"].get("acceptance_match", 0),
        "signal_eligible": 0,
        "output": str(args.output / "summary.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
