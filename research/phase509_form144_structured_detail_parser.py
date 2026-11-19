#!/usr/bin/env python3
"""Structured, append-only parser for SEC Form 144 proposed-sale details.

The parser keeps proposed sales, acquisition lots, and realized prior-three-month
sales in separate row types. It never treats a Form 144 notice as proof of
execution, never normalizes the reported outstanding-share denominator, and
never authorizes a trading signal.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

PARSER_VERSION = "phase509-v1"

DETAIL_FIELDS = [
    "accession", "form", "issuer_cik", "issuer_name", "filer_cik", "seller_name",
    "previous_accession", "relationships_to_issuer_json", "remarks",
    "mentions_10b5_1_in_remarks", "nothing_to_report_flag",
    "notice_date_raw", "notice_date_iso", "plan_adoption_dates_json", "signature",
    "feed_updated_utc", "submission_acceptance_utc",
    "first_seen_at_utc", "first_seen_poll_run_id",
    "first_seen_interval_lower_bound_utc", "first_seen_interval_upper_bound_utc",
    "first_seen_interval_status", "first_seen_is_upper_bound_not_exact_receipt",
    "source_xml_sha256", "event_xml_sha256", "source_xml_hash_matches_event",
    "parser_version", "detail_section", "detail_index", "parse_status", "parse_error",
    "research_observation_eligible", "public_availability_certified",
    "same_day_intraday_use_authorized", "signal_eligible",
    "security_class", "broker_or_market_maker",
    "proposed_units_raw", "proposed_units_numeric",
    "aggregate_market_value_raw", "aggregate_market_value_numeric",
    "units_outstanding_raw", "units_outstanding_numeric",
    "approx_sale_date_raw", "approx_sale_date_iso",
    "approx_sale_date_relation_to_notice", "exchange",
    "acquired_date_raw", "acquired_date_iso", "nature_of_acquisition",
    "acquired_from", "gift_flag", "amount_acquired_raw", "amount_acquired_numeric",
    "payment_date_raw", "payment_date_iso", "nature_of_payment",
    "prior_sale_seller", "prior_sale_date_raw", "prior_sale_date_iso",
    "prior_sale_amount_raw", "prior_sale_amount_numeric",
    "prior_sale_gross_proceeds_raw", "prior_sale_gross_proceeds_numeric",
]


def local_name(tag: object) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def descendants(root: ET.Element, wanted: str) -> list[ET.Element]:
    name = wanted.lower()
    return [node for node in root.iter() if local_name(node.tag) == name]


def first_text(root: ET.Element | None, wanted: str) -> str | None:
    if root is None:
        return None
    for node in descendants(root, wanted):
        if node.text and node.text.strip():
            return node.text.strip()
    return None


def all_text(root: ET.Element | None, wanted: str) -> list[str]:
    if root is None:
        return []
    return [node.text.strip() for node in descendants(root, wanted) if node.text and node.text.strip()]


def parse_number(value: object) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    cleaned = re.sub(r"[$,\s]", "", raw)
    try:
        number = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite():
        return None
    if number == number.to_integral_value():
        return str(int(number))
    return format(number.normalize(), "f")


def parse_date(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_accession(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return None
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def _first_child(root: ET.Element | None, wanted: str) -> ET.Element | None:
    if root is None:
        return None
    return next((node for node in list(root) if local_name(node.tag) == wanted.lower()), None)


def extract_sale_tranches(root: ET.Element) -> list[dict]:
    """securitiesInformation rows are proposed sales, not completed sales."""
    result = []
    for index, node in enumerate(descendants(root, "securitiesInformation"), start=1):
        broker_node = next(iter(descendants(node, "brokerOrMarketmakerDetails")), None)
        units = first_text(node, "noOfUnitsSold")
        value = first_text(node, "aggregateMarketValue")
        outstanding = first_text(node, "noOfUnitsOutstanding")
        approx_date = first_text(node, "approxSaleDate")
        result.append({
            "detail_index": index,
            "security_class": first_text(node, "securitiesClassTitle"),
            "broker_or_market_maker": first_text(broker_node, "name"),
            "proposed_units_raw": units,
            "proposed_units_numeric": parse_number(units),
            "aggregate_market_value_raw": value,
            "aggregate_market_value_numeric": parse_number(value),
            "units_outstanding_raw": outstanding,
            "units_outstanding_numeric": parse_number(outstanding),
            "approx_sale_date_raw": approx_date,
            "approx_sale_date_iso": parse_date(approx_date),
            "exchange": first_text(node, "securitiesExchangeName"),
        })
    return result


def extract_acquisition_lots(root: ET.Element) -> list[dict]:
    """securitiesToBeSold rows describe acquisition history, not proposed supply."""
    result = []
    for index, node in enumerate(descendants(root, "securitiesToBeSold"), start=1):
        acquired = first_text(node, "acquiredDate")
        amount = first_text(node, "amountOfSecuritiesAcquired")
        payment = first_text(node, "paymentDate")
        result.append({
            "detail_index": index,
            "security_class": first_text(node, "securitiesClassTitle"),
            "acquired_date_raw": acquired,
            "acquired_date_iso": parse_date(acquired),
            "nature_of_acquisition": first_text(node, "natureOfAcquisitionTransaction"),
            "acquired_from": first_text(node, "nameOfPersonfromWhomAcquired"),
            "gift_flag": first_text(node, "isGiftTransaction"),
            "amount_acquired_raw": amount,
            "amount_acquired_numeric": parse_number(amount),
            "payment_date_raw": payment,
            "payment_date_iso": parse_date(payment),
            "nature_of_payment": first_text(node, "natureOfPayment"),
        })
    return result


def extract_prior_sales(root: ET.Element) -> list[dict]:
    """securitiesSoldInPast3Months rows are historical realized sales."""
    result = []
    for index, node in enumerate(descendants(root, "securitiesSoldInPast3Months"), start=1):
        sale_date = first_text(node, "saleDate")
        amount = first_text(node, "amountOfSecuritiesSold")
        proceeds = first_text(node, "grossProceeds")
        result.append({
            "detail_index": index,
            "prior_sale_seller": first_text(node, "name"),
            "security_class": first_text(node, "securitiesClassTitle"),
            "prior_sale_date_raw": sale_date,
            "prior_sale_date_iso": parse_date(sale_date),
            "prior_sale_amount_raw": amount,
            "prior_sale_amount_numeric": parse_number(amount),
            "prior_sale_gross_proceeds_raw": proceeds,
            "prior_sale_gross_proceeds_numeric": parse_number(proceeds),
        })
    return result


def parse_form144_details(raw: bytes | str) -> dict:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", "replace")
    root = ET.fromstring(str(raw))
    if local_name(root.tag) != "edgarsubmission":
        raise ValueError("Unexpected Form 144 XML root")
    submission_type = (first_text(root, "submissionType") or "").strip().upper().replace("FORM ", "")
    if submission_type not in ("144", "144/A"):
        raise ValueError("Unexpected Form 144 submissionType")

    issuer_node = next(iter(descendants(root, "issuerInfo")), None)
    filer_node = next(iter(descendants(root, "filerCredentials")), None)
    notice_node = next(iter(descendants(root, "noticeSignature")), None)
    notice_raw = first_text(notice_node, "noticeDate")
    remarks = all_text(root, "remarks")
    plan_dates = all_text(notice_node, "planAdoptionDate")
    relationships = all_text(issuer_node, "relationshipToIssuer")

    return {
        "submission_type": "144/A" if submission_type == "144/A" else "144",
        "issuer_cik": first_text(issuer_node, "issuerCik"),
        "issuer_name": first_text(issuer_node, "issuerName"),
        "filer_cik": first_text(filer_node, "cik"),
        "seller_name": first_text(root, "nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold"),
        "previous_accession": normalize_accession(first_text(root, "previousAccessionNumber")),
        "relationships_to_issuer": relationships,
        "nothing_to_report_flag": first_text(root, "nothingToReportFlagOnSecuritiesSoldInPast3Months"),
        "notice_date_raw": notice_raw,
        "notice_date_iso": parse_date(notice_raw),
        "plan_adoption_dates": plan_dates,
        "signature": first_text(notice_node, "signature"),
        "remarks": remarks,
        "mentions_10b5_1_in_remarks": any(re.search(r"10b5[\s-]*1", x, re.I) for x in remarks),
        "sale_tranches": extract_sale_tranches(root),
        "acquisition_lots": extract_acquisition_lots(root),
        "prior_sales": extract_prior_sales(root),
    }


def _date_relation(approx_sale_date: str | None, notice_date: str | None) -> str:
    if not approx_sale_date or not notice_date:
        return "unknown"
    if approx_sale_date < notice_date:
        return "before_notice_date"
    if approx_sale_date == notice_date:
        return "same_as_notice_date"
    return "after_notice_date"


def build_detail_rows(event: dict, metadata: dict) -> list[dict]:
    """Build a normalized long-form ledger; all source clocks remain separate."""
    parsed = metadata.get("structured_details")
    source_hash = metadata.get("xml_sha256")
    event_hash = event.get("xml_sha256")
    hash_match = None if not source_hash or not event_hash else str(source_hash) == str(event_hash)
    parse_status = metadata.get("structured_parse_status") or "not_parsed"
    if parse_status == "parsed":
        if hash_match is False:
            parse_status = "source_hash_mismatch"
        elif hash_match is None:
            parse_status = "parsed_unverified_hash"
    parse_error = metadata.get("structured_parse_error")

    header = parsed or {}
    base = {
        "accession": event.get("accession"),
        "form": header.get("submission_type") or event.get("form"),
        "issuer_cik": header.get("issuer_cik") or event.get("issuer_cik"),
        "issuer_name": header.get("issuer_name") or event.get("issuer_name"),
        "filer_cik": header.get("filer_cik") or event.get("filer_cik"),
        "seller_name": header.get("seller_name") or event.get("seller_name"),
        "previous_accession": header.get("previous_accession") or event.get("previous_accession"),
        "relationships_to_issuer_json": json.dumps(header.get("relationships_to_issuer") or [], ensure_ascii=False),
        "remarks": " | ".join(header.get("remarks") or []) if header else event.get("remarks"),
        "mentions_10b5_1_in_remarks": header.get("mentions_10b5_1_in_remarks"),
        "nothing_to_report_flag": header.get("nothing_to_report_flag"),
        "notice_date_raw": header.get("notice_date_raw"),
        "notice_date_iso": header.get("notice_date_iso"),
        "plan_adoption_dates_json": json.dumps(header.get("plan_adoption_dates") or [], ensure_ascii=False),
        "signature": header.get("signature"),
        "feed_updated_utc": event.get("feed_updated_utc"),
        "submission_acceptance_utc": event.get("submission_acceptance_utc"),
        "first_seen_at_utc": event.get("first_seen_at_utc"),
        "first_seen_poll_run_id": event.get("first_seen_poll_run_id"),
        "first_seen_interval_lower_bound_utc": event.get("first_seen_interval_lower_bound_utc"),
        "first_seen_interval_upper_bound_utc": event.get("first_seen_interval_upper_bound_utc"),
        "first_seen_interval_status": event.get("first_seen_interval_status"),
        "first_seen_is_upper_bound_not_exact_receipt": True,
        "source_xml_sha256": source_hash,
        "event_xml_sha256": event_hash,
        "source_xml_hash_matches_event": hash_match,
        "parser_version": PARSER_VERSION,
        "parse_status": parse_status,
        "parse_error": parse_error,
        "research_observation_eligible": event.get("research_observation_eligible"),
        "public_availability_certified": False,
        "same_day_intraday_use_authorized": False,
        "signal_eligible": False,
    }

    rows = []
    header_row = dict(base)
    header_row.update({"detail_section": "filing_header", "detail_index": 1})
    rows.append(header_row)

    if not parsed:
        return rows

    for item in parsed.get("sale_tranches") or []:
        row = dict(base)
        row.update({
            "detail_section": "securities_information",
            "detail_index": item.get("detail_index"),
            "security_class": item.get("security_class"),
            "broker_or_market_maker": item.get("broker_or_market_maker"),
            "proposed_units_raw": item.get("proposed_units_raw"),
            "proposed_units_numeric": item.get("proposed_units_numeric"),
            "aggregate_market_value_raw": item.get("aggregate_market_value_raw"),
            "aggregate_market_value_numeric": item.get("aggregate_market_value_numeric"),
            "units_outstanding_raw": item.get("units_outstanding_raw"),
            "units_outstanding_numeric": item.get("units_outstanding_numeric"),
            "approx_sale_date_raw": item.get("approx_sale_date_raw"),
            "approx_sale_date_iso": item.get("approx_sale_date_iso"),
            "approx_sale_date_relation_to_notice": _date_relation(
                item.get("approx_sale_date_iso"), parsed.get("notice_date_iso")
            ),
            "exchange": item.get("exchange"),
        })
        rows.append(row)

    for item in parsed.get("acquisition_lots") or []:
        row = dict(base)
        row.update({
            "detail_section": "securities_to_be_sold",
            "detail_index": item.get("detail_index"),
            "security_class": item.get("security_class"),
            "acquired_date_raw": item.get("acquired_date_raw"),
            "acquired_date_iso": item.get("acquired_date_iso"),
            "nature_of_acquisition": item.get("nature_of_acquisition"),
            "acquired_from": item.get("acquired_from"),
            "gift_flag": item.get("gift_flag"),
            "amount_acquired_raw": item.get("amount_acquired_raw"),
            "amount_acquired_numeric": item.get("amount_acquired_numeric"),
            "payment_date_raw": item.get("payment_date_raw"),
            "payment_date_iso": item.get("payment_date_iso"),
            "nature_of_payment": item.get("nature_of_payment"),
        })
        rows.append(row)

    for item in parsed.get("prior_sales") or []:
        row = dict(base)
        row.update({
            "detail_section": "securities_sold_in_past_3_months",
            "detail_index": item.get("detail_index"),
            "security_class": item.get("security_class"),
            "prior_sale_seller": item.get("prior_sale_seller"),
            "prior_sale_date_raw": item.get("prior_sale_date_raw"),
            "prior_sale_date_iso": item.get("prior_sale_date_iso"),
            "prior_sale_amount_raw": item.get("prior_sale_amount_raw"),
            "prior_sale_amount_numeric": item.get("prior_sale_amount_numeric"),
            "prior_sale_gross_proceeds_raw": item.get("prior_sale_gross_proceeds_raw"),
            "prior_sale_gross_proceeds_numeric": item.get("prior_sale_gross_proceeds_numeric"),
        })
        rows.append(row)

    return rows


def _row_key(row: dict) -> tuple:
    return (
        str(row.get("accession") or ""),
        str(row.get("detail_section") or ""),
        str(row.get("detail_index") or ""),
        str(row.get("source_xml_sha256") or ""),
        str(row.get("parser_version") or ""),
    )


def append_detail_rows(path: str | Path, rows: list[dict]) -> int:
    path = Path(path)
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != DETAIL_FIELDS:
                raise ValueError("structured detail ledger header mismatch")
            for row in reader:
                existing.add(_row_key(row))
    pending = []
    for row in rows:
        if set(row) - set(DETAIL_FIELDS):
            raise ValueError("structured detail row contains unknown fields")
        key = _row_key(row)
        if key not in existing:
            pending.append(row)
            existing.add(key)
    if not pending:
        return 0
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS, extrasaction="raise")
        if not exists:
            writer.writeheader()
        writer.writerows(pending)
    return len(pending)


def read_completed_accessions(path: str | Path) -> set[str]:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return set()
    completed = set()
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != DETAIL_FIELDS:
            raise ValueError("structured detail ledger header mismatch")
        for row in reader:
            if row.get("accession") and row.get("source_xml_sha256") and row.get("parser_version") == PARSER_VERSION:
                completed.add(row["accession"])
    return completed


def count_detail_rows(path: str | Path) -> int:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _ in csv.DictReader(handle))
