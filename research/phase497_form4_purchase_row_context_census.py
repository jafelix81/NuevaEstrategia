from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research import phase401_form144a_full_parent_identity_census as p401
from research import phase496_form4_accession_payload_semantics_audit as p496

SOURCE_RUN_ID = "44440313382"
EXPECTED_ACCESSIONS = 637
PHASE496_RUN_ID = "44474285899"
PHASE496_ARTIFACT_ID = "14506425194"


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
    result = "".join(target.itertext()).strip()
    return result or None


def nested_text(node: ET.Element | None, parent: str, field: str) -> str | None:
    return direct_text(direct_child(node, parent), field)


def normalized_bucket(value: str | None, allowed: set[str]) -> str:
    token = str(value or "").strip().upper()
    return token if token in allowed else "unknown"


def parse_positive_decimal(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    token = re.sub(r"[$,\s]", "", str(value).strip())
    try:
        number = Decimal(token)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


FOOTNOTE_PATTERNS = {
    "open_market": r"\bopen[\s-]?market\b",
    "private_purchase_or_placement": r"\bprivate\s+(?:purchase|placement|transaction)\b",
    "mentions_rule_10b5_1": r"10b5[\s-]?1",
    "mentions_401k": r"401\s*\(?k\)?",
    "tax_or_withholding": r"\b(?:tax|withhold(?:ing)?)\b",
    "trust": r"\btrust(?:ee|s)?\b",
    "gift_or_donation": r"\b(?:gift|donat(?:ion|ed))\b",
    "option_or_cashless": r"\b(?:option|exercise|cashless)\b",
    "compensation_or_vesting": r"\b(?:compensation|award|vesting|restricted stock|stock unit)\b",
    "employee_plan": r"\b(?:employee stock|employee benefit|purchase plan)\b",
}


def parse_form4_purchase_context(raw: bytes, filing_date: str) -> dict:
    root = ET.fromstring(raw)
    if local_name(root.tag) != "ownershipdocument":
        raise ValueError("unexpected_form4_xml_root")

    owners = direct_children(root, "reportingOwner")
    owner_count = len(owners)
    owner_bucket = "zero" if owner_count == 0 else "single" if owner_count == 1 else "multiple"
    aff = p496.normalize_flag(p496.first_descendant_text(root, "aff10b5One"))

    footnotes: dict[str, str] = {}
    for node in root.iter():
        if local_name(node.tag) == "footnote":
            footnote_id = str(node.attrib.get("id") or "").strip()
            footnote_text = " ".join("".join(node.itertext()).split())
            if footnote_id and footnote_text:
                footnotes[footnote_id] = footnote_text

    table = direct_child(root, "nonDerivativeTable")
    rows = direct_children(table, "nonDerivativeTransaction")
    filing_day = parse_iso_date(filing_date)

    directness = Counter()
    owner_buckets = Counter()
    plan_flags = Counter()
    matrix = Counter()
    price_presence = Counter()
    shares_presence = Counter()
    date_presence = Counter()
    date_relation = Counter()
    footnote_counts = Counter()
    footnote_flags = Counter()
    review_screen = 0
    pa_rows = 0

    for row in rows:
        code = (nested_text(row, "transactionCoding", "transactionCode") or "").strip().upper()
        acquired = (nested_text(row, "transactionAmounts", "transactionAcquiredDisposedCode") or "").strip().upper()
        if code != "P" or acquired != "A":
            continue

        pa_rows += 1
        ownership_code = normalized_bucket(
            nested_text(row, "ownershipNature", "directOrIndirectOwnership"), {"D", "I"}
        )
        directness[ownership_code] += 1
        owner_buckets[owner_bucket] += 1
        plan_flags[aff] += 1
        matrix[f"{owner_bucket}|{ownership_code}|{aff}"] += 1

        price_raw = nested_text(row, "transactionAmounts", "transactionPricePerShare")
        shares_raw = nested_text(row, "transactionAmounts", "transactionShares")
        price = parse_positive_decimal(price_raw)
        shares = parse_positive_decimal(shares_raw)
        price_presence["present" if price_raw else "missing"] += 1
        price_presence["positive_numeric" if price is not None else "not_positive_or_unparseable"] += 1
        shares_presence["present" if shares_raw else "missing"] += 1
        shares_presence["positive_numeric" if shares is not None else "not_positive_or_unparseable"] += 1

        transaction_day = parse_iso_date(direct_text(row, "transactionDate"))
        date_presence["present" if transaction_day else "missing_or_invalid"] += 1
        if transaction_day is None or filing_day is None:
            relation = "unknown"
        elif transaction_day < filing_day:
            relation = "before_filing_date"
        elif transaction_day == filing_day:
            relation = "same_filing_date"
        else:
            relation = "after_filing_date"
        date_relation[relation] += 1

        referenced_ids = set()
        for node in row.iter():
            if local_name(node.tag) == "footnoteid":
                footnote_id = str(node.attrib.get("id") or "").strip()
                if not footnote_id:
                    footnote_id = "".join(node.itertext()).strip()
                if footnote_id:
                    referenced_ids.add(footnote_id)
        referenced_texts = [footnotes[x] for x in sorted(referenced_ids) if x in footnotes]
        unresolved = referenced_ids - set(footnotes)
        footnote_counts["rows_with_reference" if referenced_ids else "rows_without_reference"] += 1
        footnote_counts["rows_with_resolved_text" if referenced_texts else "rows_without_resolved_text"] += 1
        footnote_counts["unresolved_reference_count"] += len(unresolved)
        combined_footnote_text = " ".join(referenced_texts)
        for flag, pattern in FOOTNOTE_PATTERNS.items():
            if re.search(pattern, combined_footnote_text, flags=re.IGNORECASE):
                footnote_flags[flag] += 1

        # This is a narrow manual-review queue only. It is NOT proof of exchange execution,
        # discretion, or informed trading; code P also includes private purchases.
        if (
            owner_count == 1
            and ownership_code == "D"
            and aff == "no"
            and price is not None
            and shares is not None
            and transaction_day is not None
            and filing_day is not None
            and transaction_day <= filing_day
        ):
            review_screen += 1

    return {
        "owner_count_bucket": owner_bucket,
        "aff10b5one_filing_flag": aff,
        "p_acquired_rows": pa_rows,
        "p_acquired_rows_by_directness": dict(directness),
        "p_acquired_rows_by_owner_bucket": dict(owner_buckets),
        "p_acquired_rows_by_plan_flag": dict(plan_flags),
        "p_acquired_owner_direct_plan_matrix": dict(matrix),
        "price_field_counts": dict(price_presence),
        "shares_field_counts": dict(shares_presence),
        "transaction_date_field_counts": dict(date_presence),
        "transaction_date_vs_filing_date": dict(date_relation),
        "footnote_reference_counts": dict(footnote_counts),
        "footnote_keyword_diagnostic_counts": dict(footnote_flags),
        "high_specificity_manual_review_rows": review_screen,
    }


def audit_events(events: list[dict], fetcher, event_ledger_sha256: str) -> dict:
    retrieval = Counter()
    xml_errors = Counter()
    filing_owner_buckets = Counter()
    filing_plan_flags = Counter()
    p_a_owner_buckets = Counter()
    p_a_directness = Counter()
    p_a_plan_flags = Counter()
    p_a_matrix = Counter()
    price_counts = Counter()
    shares_counts = Counter()
    date_counts = Counter()
    date_relations = Counter()
    footnote_counts = Counter()
    footnote_flags = Counter()
    payload_manifest_parts = []
    p_a_total = 0
    manual_review_total = 0
    filing_dates = Counter()

    for index, event in enumerate(events, start=1):
        submission, _accepted_et, _accepted_utc = p496._submission_payload(event, fetcher)
        retrieval["attempted"] += 1
        if submission is None:
            retrieval["submission_failed"] += 1
            xml_errors["submission_unavailable"] += 1
        else:
            retrieval["submission_retrieved"] += 1
            submission_sha = hashlib.sha256(submission).hexdigest()
            xml = p496.extract_ownership_xml(submission)
            xml_source = "complete_submission"
            if xml is None:
                base = event["filing_url"].rsplit("/", 1)[0]
                try:
                    xml = fetcher(f"{base}/primary_doc.xml")
                    xml_source = "primary_doc.xml"
                except Exception:
                    xml = None
            if xml is None:
                xml_errors["ownership_xml_unavailable"] += 1
            else:
                try:
                    parsed = parse_form4_purchase_context(xml, event["filing_date"])
                    retrieval["xml_parsed"] += 1
                    xml_sha = hashlib.sha256(xml).hexdigest()
                    payload_manifest_parts.append(
                        f"{event['accession']}|{submission_sha}|{xml_sha}|{xml_source}"
                    )
                    filing_owner_buckets[parsed["owner_count_bucket"]] += 1
                    filing_plan_flags[parsed["aff10b5one_filing_flag"]] += 1
                    p_a_total += parsed["p_acquired_rows"]
                    manual_review_total += parsed["high_specificity_manual_review_rows"]
                    for source, target in (
                        (parsed["p_acquired_rows_by_directness"], p_a_directness),
                        (parsed["p_acquired_rows_by_owner_bucket"], p_a_owner_buckets),
                        (parsed["p_acquired_rows_by_plan_flag"], p_a_plan_flags),
                        (parsed["p_acquired_owner_direct_plan_matrix"], p_a_matrix),
                        (parsed["price_field_counts"], price_counts),
                        (parsed["shares_field_counts"], shares_counts),
                        (parsed["transaction_date_field_counts"], date_counts),
                        (parsed["transaction_date_vs_filing_date"], date_relations),
                        (parsed["footnote_reference_counts"], footnote_counts),
                        (parsed["footnote_keyword_diagnostic_counts"], footnote_flags),
                    ):
                        target.update(source)
                except Exception as exc:
                    xml_errors[f"parse_error:{type(exc).__name__}"] += 1
        if index % 50 == 0 or index == len(events):
            print(f"PHASE497_PROGRESS={index}/{len(events)}", flush=True)
        filing_dates[event.get("filing_date", "unknown")] += 1

    manifest = "\n".join(sorted(payload_manifest_parts)).encode("utf-8")
    return {
        "phase": 497,
        "source": {
            "source_poll_run_id": SOURCE_RUN_ID,
            "phase496_audit_run_id": PHASE496_RUN_ID,
            "phase496_artifact_id": PHASE496_ARTIFACT_ID,
            "expected_accessions": len(events),
            "event_ledger_sha256": event_ledger_sha256,
            "filing_date_counts": dict(filing_dates),
            "first_seen_lower_bound_utc": min(x["first_seen_interval_lower_bound_utc"] for x in events),
            "first_seen_upper_bound_min_utc": min(x["first_seen_at_utc"] for x in events),
            "first_seen_upper_bound_max_utc": max(x["first_seen_at_utc"] for x in events),
            "first_seen_is_upper_bound_not_exact_publication": True,
        },
        "retrieval": {
            "counts": dict(retrieval),
            "xml_error_counts": dict(xml_errors),
            "payload_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "raw_payloads_persisted": False,
        },
        "transaction_semantics": {
            "scope": "non_derivative_table_i_P_acquired_rows_only",
            "filing_owner_count_buckets": dict(filing_owner_buckets),
            "filing_aff10b5one_flags": dict(filing_plan_flags),
            "p_acquired_transaction_rows": p_a_total,
            "p_acquired_rows_by_directness": dict(p_a_directness),
            "p_acquired_rows_by_owner_bucket": dict(p_a_owner_buckets),
            "p_acquired_rows_by_filing_plan_flag": dict(p_a_plan_flags),
            "p_acquired_owner_direct_plan_matrix": dict(p_a_matrix),
            "price_field_counts": dict(price_counts),
            "shares_field_counts": dict(shares_counts),
            "transaction_date_field_counts": dict(date_counts),
            "transaction_date_vs_filing_date": dict(date_relations),
            "footnote_reference_counts": dict(footnote_counts),
            "footnote_keyword_diagnostic_counts": dict(footnote_flags),
            "high_specificity_manual_review_rows": manual_review_total,
            "multi_owner_rows_not_attributed_to_individual_owners": True,
            "footnote_text_persisted": False,
            "transaction_level_rows_persisted": False,
            "code_p_is_not_proof_of_exchange_execution_or_discretion": True,
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
            "raw_payloads_persisted": False,
            "transaction_level_rows_persisted": False,
            "f80_changed": False,
            "production_changed": False,
        },
        "decision": {
            "disposition": "P_A_ROW_CONTEXT_SCREEN_ONLY",
            "next_gate": "effective_dated_security_class_listing_and_historical_f80_membership_reconciliation",
            "manual_review_screen_is_not_a_signal": True,
            "no_discretionary_open_market_purchase_claim": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=EXPECTED_ACCESSIONS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    events, event_sha = p496.load_events(args.events, args.expected_count)

    def fetcher(url: str) -> bytes:
        return p401.fetch_bytes(url, sec=True, timeout=60, retries=6)

    result = audit_events(events, fetcher, event_sha)
    args.output.mkdir(parents=True, exist_ok=True)
    output_path = args.output / "summary.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": 497,
        "attempted": result["retrieval"]["counts"].get("attempted", 0),
        "xml_parsed": result["retrieval"]["counts"].get("xml_parsed", 0),
        "p_acquired_rows": result["transaction_semantics"]["p_acquired_transaction_rows"],
        "manual_review_rows": result["transaction_semantics"]["high_specificity_manual_review_rows"],
        "signal_eligible": 0,
        "output": str(output_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
