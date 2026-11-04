#!/usr/bin/env python3
"""SEC Form 144 event-field coverage and amendment-lineage feasibility audit.

Uses current CIK pairs only for candidate discovery. Primary XML confirms issuer
identity. This is a stratified schema/data-feasibility sample, not an event
population estimate and not an economic test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from research.phase50_form144_global_index_pilot import (
    current_cik_candidates, fetch_bytes, load_universe, parse_form144_xml
)
from research.phase64_form144_master_pair_cross_quarter_audit import (
    build_pair_rows, classify_xml_identity, parse_quarter, primary_xml_urls
)

DEFAULT_QUARTERS = (
    "2023Q2,2023Q3,2023Q4,2024Q1,2024Q2,2024Q3,2024Q4,"
    "2025Q1,2025Q2,2025Q3,2025Q4,2026Q1,2026Q2,2026Q3"
)
START_DATE = "2023-04-13"
OUT_DIR = Path("phase65_form144_field_coverage")
FORMS = ("144", "144/A")
SAMPLE_LIMITS = {"unique_candidate": 50, "ambiguous": 20, "control": 10}
CORE_FIELDS = (
    "issuer_cik", "seller_name", "relationships", "sale_tranche_count",
    "sale_security_class", "sale_units", "sale_value", "approx_sale_date",
    "notice_date",
)


def local_name(tag):
    return str(tag).split("}", 1)[-1].split(":")[-1].lower()


def first_text(node, wanted):
    wanted = wanted.lower()
    for element in node.iter():
        if local_name(element.tag) == wanted and element.text and element.text.strip():
            return element.text.strip()
    return None


def parse_date(value):
    if value in (None, ""):
        return None
    raw = str(value).strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def parse_number(value):
    if value in (None, ""):
        return None
    raw = str(value).strip().replace(",", "").replace("$", "").replace(" ", "")
    negative = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()")
    raw = re.sub(r"[^0-9.+\-]", "", raw)
    if not raw or raw in (".", "+", "-", "+.", "-."):
        return None
    try:
        result = float(raw)
    except ValueError:
        return None
    return -result if negative else result


def normalize_accession(value):
    if value in (None, ""):
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) != 18:
        return None
    return "{}-{}-{}".format(digits[:10], digits[10:12], digits[12:])


def stable_key(row):
    token = "{}:{}:{}:{}".format(
        row.get("year"), row.get("quarter"), row.get("form"), row.get("accession")
    )
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def select_sample(rows):
    selected = []
    for form in FORMS:
        pool = [row for row in rows if row.get("form") == form]
        for stratum, limit in SAMPLE_LIMITS.items():
            candidates = [row for row in pool if row["pair_class"] == stratum]
            for row in sorted(candidates, key=stable_key)[:limit]:
                item = dict(row)
                item["sample_stratum"] = stratum
                selected.append(item)
    return sorted(selected, key=lambda row: (
        row.get("filing_date") or "", row.get("form") or "", row["accession"]
    ))


def extract_sale_tranches(root):
    """securitiesInformation blocks describe proposed sales (not acquisition lots)."""
    nodes = [
        element for element in root.iter()
        if local_name(element.tag) == "securitiesinformation"
    ]
    result = []
    for index, node in enumerate(nodes, start=1):
        item = {
            "sale_tranche_index": index,
            "security_class": first_text(node, "securitiesClassTitle"),
            "units_to_be_sold": first_text(node, "noOfUnitsSold"),
            "aggregate_market_value": first_text(node, "aggregateMarketValue"),
            "units_outstanding": first_text(node, "noOfUnitsOutstanding"),
            "approx_sale_date": first_text(node, "approxSaleDate"),
            "exchange": first_text(node, "securitiesExchangeName"),
            "broker_or_market_maker": first_text(node, "name"),
        }
        item["units_numeric"] = parse_number(item["units_to_be_sold"])
        item["value_numeric"] = parse_number(item["aggregate_market_value"])
        item["outstanding_numeric"] = parse_number(item["units_outstanding"])
        item["approx_sale_date_iso"] = parse_date(item["approx_sale_date"])
        result.append(item)
    return result


def extract_acquisition_lots(root):
    """securitiesToBeSold blocks describe how/when the seller acquired the securities."""
    nodes = [
        element for element in root.iter()
        if local_name(element.tag) == "securitiestobesold"
    ]
    result = []
    for index, node in enumerate(nodes, start=1):
        item = {
            "acquisition_lot_index": index,
            "security_class": first_text(node, "securitiesClassTitle"),
            "acquired_date": first_text(node, "acquiredDate"),
            "nature_of_acquisition": first_text(node, "natureOfAcquisitionTransaction"),
            "acquired_from": first_text(node, "nameOfPersonfromWhomAcquired"),
            "gift_flag": first_text(node, "isGiftTransaction"),
            "amount_acquired": first_text(node, "amountOfSecuritiesAcquired"),
            "payment_date": first_text(node, "paymentDate"),
            "nature_of_payment": first_text(node, "natureOfPayment"),
        }
        item["amount_acquired_numeric"] = parse_number(item["amount_acquired"])
        item["acquired_date_iso"] = parse_date(item["acquired_date"])
        item["payment_date_iso"] = parse_date(item["payment_date"])
        result.append(item)
    return result


def extract_prior_sales(root):
    """securitiesSoldInPast3Months blocks are realized historical sales, not the proposed sale."""
    nodes = [
        element for element in root.iter()
        if local_name(element.tag) == "securitiessoldinpast3months"
    ]
    result = []
    for index, node in enumerate(nodes, start=1):
        item = {
            "past_sale_index": index,
            "seller": first_text(node, "name"),
            "security_class": first_text(node, "securitiesClassTitle"),
            "sale_date": first_text(node, "saleDate"),
            "amount_sold": first_text(node, "amountOfSecuritiesSold"),
            "gross_proceeds": first_text(node, "grossProceeds"),
        }
        item["amount_sold_numeric"] = parse_number(item["amount_sold"])
        item["gross_proceeds_numeric"] = parse_number(item["gross_proceeds"])
        item["sale_date_iso"] = parse_date(item["sale_date"])
        result.append(item)
    return result


def fetch_and_parse(row):
    errors = []
    for url in primary_xml_urls(row):
        try:
            raw = fetch_bytes(url, sec=True, timeout=45, retries=4)
            parsed = parse_form144_xml(raw)
            root = ET.fromstring(raw)
            return parsed, root, url, None
        except Exception as error:
            errors.append(type(error).__name__ + ":" + str(error)[:180])
    return None, None, None, ";".join(errors[-4:]) or "PRIMARY_XML_NOT_FOUND"


def audit_quarter(token, candidate_ciks, cik_to_tickers, workers):
    year, quarter = parse_quarter(token)
    url = "https://www.sec.gov/Archives/edgar/full-index/{}/QTR{}/master.idx".format(year, quarter)
    raw = fetch_bytes(url, sec=True, timeout=90, retries=5)
    from research.phase50_form144_global_index_pilot import parse_master_index
    index_rows = parse_master_index(raw)
    index_rows = [
        row for row in index_rows
        if row.get("form") in FORMS and row.get("filing_date")
        and row["filing_date"] >= START_DATE
    ]
    pair_rows = build_pair_rows(index_rows, candidate_ciks, cik_to_tickers, year, quarter)
    sample = select_sample(pair_rows)
    census = {
        "quarter": token,
        "master_index_accessions_after_electronic_start": len(pair_rows),
        "form144_accessions": sum(row.get("form") == "144" for row in pair_rows),
        "form144a_accessions": sum(row.get("form") == "144/A" for row in pair_rows),
        "unique_candidate_144": sum(row.get("form") == "144" and row["pair_class"] == "unique_candidate" for row in pair_rows),
        "unique_candidate_144a": sum(row.get("form") == "144/A" and row["pair_class"] == "unique_candidate" for row in pair_rows),
        "ambiguous_144": sum(row.get("form") == "144" and row["pair_class"] == "ambiguous" for row in pair_rows),
        "ambiguous_144a": sum(row.get("form") == "144/A" and row["pair_class"] == "ambiguous" for row in pair_rows),
        "control_144": sum(row.get("form") == "144" and row["pair_class"] == "control" for row in pair_rows),
        "control_144a": sum(row.get("form") == "144/A" and row["pair_class"] == "control" for row in pair_rows),
        "sampled_unique_candidate": sum(row["sample_stratum"] == "unique_candidate" for row in sample),
        "sampled_ambiguous": sum(row["sample_stratum"] == "ambiguous" for row in sample),
        "sampled_controls": sum(row["sample_stratum"] == "control" for row in sample),
        "xml_sample_requested": len(sample),
    }
    return census, sample, pair_rows


def audit_sample(rows, census_accessions, workers):
    details, sale_rows, acquisition_rows, past_sale_rows, errors = [], [], [], [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_and_parse, row): row for row in rows}
        for future in as_completed(futures):
            row = futures[future]
            try:
                parsed, root, xml_url, error = future.result()
            except Exception as exc:
                parsed, root, xml_url, error = None, None, None, type(exc).__name__ + ":" + str(exc)
            if parsed is None:
                errors.append({
                    "quarter": "{}Q{}".format(row["year"], row["quarter"]),
                    "accession": row["accession"],
                    "form": row.get("form"),
                    "sample_stratum": row["sample_stratum"],
                    "error": error,
                })
                continue

            identity = classify_xml_identity(row, parsed)
            candidates = row.get("candidate_ciks_in_pair") or []
            if row["sample_stratum"] == "unique_candidate":
                identity_ok = identity["unique_candidate_role"] == "issuer"
            elif row["sample_stratum"] == "ambiguous":
                identity_ok = identity["xml_issuer_cik"] in candidates
            else:
                identity_ok = identity["both_xml_ciks_in_pair"]

            sale_tranches = extract_sale_tranches(root)
            acquisition_lots = extract_acquisition_lots(root)
            past_sales = extract_prior_sales(root)
            previous = normalize_accession(parsed.get("previous_accession"))
            relationships = parsed.get("relationships") or []
            sale_units = [item["units_numeric"] for item in sale_tranches]
            sale_values = [item["value_numeric"] for item in sale_tranches]
            sale_outstanding = [item["outstanding_numeric"] for item in sale_tranches]
            sale_dates = [item["approx_sale_date_iso"] for item in sale_tranches]
            sale_units_raw = [item["units_to_be_sold"] for item in sale_tranches]
            sale_values_raw = [item["aggregate_market_value"] for item in sale_tranches]
            sale_dates_raw = [item["approx_sale_date"] for item in sale_tranches]
            units_total = sum(sale_units) if sale_units and all(v is not None for v in sale_units) else None
            value_total = sum(sale_values) if sale_values and all(v is not None for v in sale_values) else None
            record = {
                "quarter": "{}Q{}".format(row["year"], row["quarter"]),
                "accession": row["accession"],
                "form": row.get("form"),
                "filing_date": row.get("filing_date"),
                "sample_stratum": row["sample_stratum"],
                "candidate_tickers": ";".join(row.get("candidate_tickers") or []),
                "candidate_ciks_in_pair": ";".join(candidates),
                "xml_url": xml_url,
                "xml_issuer_cik": identity["xml_issuer_cik"],
                "xml_filer_cik": identity["xml_filer_cik"],
                "identity_ok": identity_ok,
                "xml_form_matches_index": identity["xml_form_matches_index"],
                "issuer_name": parsed.get("issuer_name") or "",
                "seller_name": parsed.get("seller_name") or "",
                "relationships": ";".join(relationships),
                "sale_tranche_count": len(sale_tranches),
                "sale_security_class_present": bool(sale_tranches) and all(item["security_class"] for item in sale_tranches),
                "sale_units_present": bool(sale_tranches) and all(sale_units_raw),
                "sale_value_present": bool(sale_tranches) and all(sale_values_raw),
                "approx_sale_date_present": bool(sale_tranches) and all(sale_dates_raw),
                "sale_units_all_numeric": bool(sale_tranches) and all(value is not None for value in sale_units),
                "sale_value_all_numeric": bool(sale_tranches) and all(value is not None for value in sale_values),
                "sale_outstanding_all_numeric": bool(sale_tranches) and all(value is not None for value in sale_outstanding),
                "sale_dates_all_parse": bool(sale_tranches) and all(value is not None for value in sale_dates),
                "sale_units_total": units_total,
                "sale_value_total": value_total,
                "sale_tranches_json": json.dumps(sale_tranches, sort_keys=True),
                "acquisition_lot_count": len(acquisition_lots),
                "acquisition_lots_json": json.dumps(acquisition_lots, sort_keys=True),
                "past_sales_count": len(past_sales),
                "past_sales_json": json.dumps(past_sales, sort_keys=True),
                "notice_date": parsed.get("notice_date") or "",
                "notice_date_iso": parse_date(parsed.get("notice_date")),
                "previous_accession": parsed.get("previous_accession") or "",
                "previous_accession_normalized": previous or "",
                "previous_accession_in_census": bool(previous and previous in census_accessions),
                "previous_accession_valid_format": bool(previous),
                "plan_adoption_dates": ";".join(parsed.get("plan_adoption_dates") or []),
                "mentions_10b5_1": bool(parsed.get("mentions_10b5_1")),
                "remarks_present": bool(parsed.get("remarks")),
                "no_prior_sales_flag": first_text(root, "nothingToReportFlagOnSecuritiesSoldInPast3Months") or "",
                "field_presence": json.dumps(parsed.get("field_presence") or {}, sort_keys=True),
            }
            details.append(record)

            for item in sale_tranches:
                sale_rows.append({
                    "quarter": record["quarter"], "accession": record["accession"],
                    "form": record["form"], "sample_stratum": record["sample_stratum"],
                    "xml_issuer_cik": record["xml_issuer_cik"], **item,
                })
            for item in acquisition_lots:
                acquisition_rows.append({
                    "quarter": record["quarter"], "accession": record["accession"],
                    "form": record["form"], "sample_stratum": record["sample_stratum"],
                    "xml_issuer_cik": record["xml_issuer_cik"], **item,
                })
            for item in past_sales:
                past_sale_rows.append({
                    "quarter": record["quarter"], "accession": record["accession"],
                    "form": record["form"], "sample_stratum": record["sample_stratum"],
                    "xml_issuer_cik": record["xml_issuer_cik"], **item,
                })
    return details, sale_rows, acquisition_rows, past_sale_rows, errors


def rate(rows, predicate):
    return sum(bool(predicate(row)) for row in rows) / len(rows) if rows else None


def summarize(details, errors, census):
    by_form = {}
    for form in FORMS:
        sub = [row for row in details if row["form"] == form]
        targets = [row for row in sub if row["sample_stratum"] in ("unique_candidate", "ambiguous")]
        item = {
            "sample_rows": len(sub),
            "candidate_rows": len(targets),
            "candidate_identity_rate": rate(targets, lambda row: row["identity_ok"]),
            "control_pair_concordance": rate([row for row in sub if row["sample_stratum"] == "control"], lambda row: row["identity_ok"]),
            "xml_form_match_rate": rate(sub, lambda row: row["xml_form_matches_index"]),
            "core_field_presence": {},
            "numeric_parse_rates": {},
            "date_parse_rates": {},
            "amendment_previous_accession_valid_rate": None,
            "amendment_previous_accession_in_census_rate": None,
            "tenb5_1_mention_rate": rate(sub, lambda row: row["mentions_10b5_1"]),
            "multi_sale_tranche_rate": rate(sub, lambda row: row["sale_tranche_count"] > 1),
            "median_sale_tranche_count": None,
            "median_acquisition_lot_count": None,
        }
        for field in CORE_FIELDS:
            if field == "issuer_cik":
                item["core_field_presence"][field] = rate(sub, lambda row: bool(row["xml_issuer_cik"]))
            elif field == "seller_name":
                item["core_field_presence"][field] = rate(sub, lambda row: bool(row["seller_name"]))
            elif field == "relationships":
                item["core_field_presence"][field] = rate(sub, lambda row: bool(row["relationships"]))
            elif field == "sale_tranche_count":
                item["core_field_presence"][field] = rate(sub, lambda row: row["sale_tranche_count"] > 0)
            elif field == "sale_security_class":
                item["core_field_presence"][field] = rate(sub, lambda row: row["sale_security_class_present"])
            elif field == "sale_units":
                item["core_field_presence"][field] = rate(sub, lambda row: row["sale_units_present"])
            elif field == "sale_value":
                item["core_field_presence"][field] = rate(sub, lambda row: row["sale_value_present"])
            elif field == "approx_sale_date":
                item["core_field_presence"][field] = rate(sub, lambda row: row["approx_sale_date_present"])
            elif field == "notice_date":
                item["core_field_presence"][field] = rate(sub, lambda row: bool(row["notice_date"]))
        for field in ("sale_units_all_numeric", "sale_value_all_numeric", "sale_outstanding_all_numeric"):
            item["numeric_parse_rates"][field] = rate(sub, lambda row, f=field: row[f])
        item["date_parse_rates"]["sale_dates_all_parse"] = rate(sub, lambda row: row["sale_dates_all_parse"])
        item["date_parse_rates"]["notice_date_iso"] = rate(sub, lambda row: bool(row["notice_date_iso"]))
        if form == "144/A":
            item["amendment_previous_accession_valid_rate"] = rate(sub, lambda row: row["previous_accession_valid_format"])
            valid = [row for row in sub if row["previous_accession_valid_format"]]
            item["amendment_previous_accession_in_census_rate"] = rate(valid, lambda row: row["previous_accession_in_census"])
        sale_counts = sorted(int(row["sale_tranche_count"] or 0) for row in sub)
        acq_counts = sorted(int(row["acquisition_lot_count"] or 0) for row in sub)
        if sale_counts:
            item["median_sale_tranche_count"] = sale_counts[len(sale_counts)//2]
        if acq_counts:
            item["median_acquisition_lot_count"] = acq_counts[len(acq_counts)//2]
        by_form[form] = item

    candidate_144 = sum(row["unique_candidate_144"] for row in census)
    candidate_144a = sum(row["unique_candidate_144a"] for row in census)
    sampled_144 = by_form["144"]["candidate_rows"]
    sampled_144a = by_form["144/A"]["candidate_rows"]
    identity_ok = all(
        row["identity_ok"] for row in details
        if row["sample_stratum"] in ("unique_candidate", "ambiguous")
    )
    controls = [row for row in details if row["sample_stratum"] == "control"]
    controls_ok = all(row["identity_ok"] for row in controls)
    xml_ok = all(row["xml_form_matches_index"] for row in details)
    core_144 = by_form["144"]["core_field_presence"]
    core_144a = by_form["144/A"]["core_field_presence"]
    core_required_144 = all((core_144.get(field) or 0) >= 0.95 for field in CORE_FIELDS)
    core_required_144a = all((core_144a.get(field) or 0) >= 0.90 for field in CORE_FIELDS)
    gates = {
        "at_least_100_candidate_form144_xml_rows": sampled_144 >= 100,
        "at_least_20_candidate_form144a_xml_rows": sampled_144a >= 20,
        "zero_xml_fetch_errors": len(errors) == 0,
        "all_sampled_candidate_identities_confirmed": identity_ok,
        "all_sampled_controls_confirm_master_pair": controls_ok,
        "all_sampled_xml_forms_match_index": xml_ok,
        "form144_core_fields_each_ge_95pct": core_required_144,
        "form144a_core_fields_each_ge_90pct": core_required_144a,
    }
    return {
        "phase": "65-form144-event-field-coverage",
        "status": "COMPLETE",
        "sample_schema_gate": "PASS" if all(gates.values()) else "FAIL",
        "quarters": [row["quarter"] for row in census],
        "quarter_census": census,
        "current_candidate_unique_accessions": {
            "form144": candidate_144, "form144a": candidate_144a,
        },
        "sampled_by_form": by_form,
        "xml_sample_rows": len(details),
        "xml_fetch_errors": len(errors),
        "gate_checks": gates,
        "historical_pit_f80_universe_gate": "NOT_TESTED",
        "accepted_timestamp_gate": "NOT_TESTED; conservative filing-date + next-full-session rule only",
        "amendment_lineage_gate": "PARTIAL; previousAccessionNumber format and in-window reference only; no immediate-predecessor assumption",
        "economic_test_authorized": False,
        "forward_returns_used": False,
        "knowledge_date_rule": "Use first full trading-session close after SEC filing_date; never use approximate sale date or same-date close.",
        "identity_rule": "Current CIK pair discovers candidates; primary XML issuerCik confirms issuer. Current mappings are not historical F80 membership.",
        "schema_rule": "securitiesInformation contains proposed-sale tranches; securitiesToBeSold contains acquisition-lot history; securitiesSoldInPast3Months contains realized prior sales. Never mix these three groups.",
        "limitations": [
            "Deterministic stratified sample is a schema diagnostic, not a population-random field-completeness estimate.",
            "Current ticker/CIK mapping does not resolve historical issuer predecessors, delistings or F80 membership.",
            "PreviousAccessionNumber is a prior-filing reference, not necessarily the immediately preceding amendment.",
            "Accepted timestamps are not collected in this phase.",
            "No forward returns or alpha tests are performed.",
        ],
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarters", default=DEFAULT_QUARTERS)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--output", default=str(OUT_DIR))
    args = parser.parse_args()

    tickers = load_universe()
    ticker_details, cik_to_tickers, unresolved, mapping_errors = current_cik_candidates(tickers)
    candidate_ciks = set(cik_to_tickers)
    census, sample_rows, all_pair_rows = [], [], []
    for token in filter(None, (value.strip() for value in args.quarters.split(","))):
        summary, sample, rows = audit_quarter(token, candidate_ciks, cik_to_tickers, args.workers)
        census.append(summary)
        sample_rows.extend(sample)
        all_pair_rows.extend(rows)
        print(json.dumps({"stage": "QUARTER_COMPLETE", "summary": summary}, sort_keys=True), flush=True)

    census_accessions = {row["accession"] for row in all_pair_rows}
    details, sale_rows, acquisition_rows, past_sale_rows, errors = audit_sample(
        sample_rows, census_accessions, args.workers
    )
    summary = summarize(details, errors, census)
    summary.update({
        "frozen_universe_size": len(tickers),
        "current_tickers_with_cik_mapping": sum(bool(item["ciks"]) for item in ticker_details.values()),
        "current_candidate_cik_count": len(candidate_ciks),
        "unresolved_tickers": unresolved,
        "mapping_source_errors": mapping_errors,
        "sample_limits_per_quarter_form": SAMPLE_LIMITS,
        "sample_accessions_requested": len(sample_rows),
        "xml_field_rows_parsed": len(details),
        "sale_tranche_rows_parsed": len(sale_rows),
        "acquisition_lot_rows_parsed": len(acquisition_rows),
        "past_sale_rows_parsed": len(past_sale_rows),
    })
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(output / "quarter_census.csv", census)
    write_csv(output / "filing_field_coverage.csv", details)
    write_csv(output / "sale_tranche_rows.csv", sale_rows)
    write_csv(output / "acquisition_lot_rows.csv", acquisition_rows)
    write_csv(output / "past_sales_rows.csv", past_sale_rows)
    write_csv(output / "xml_fetch_errors.csv", errors)
    print(json.dumps(summary, indent=2), flush=True)
    if summary["sample_schema_gate"] != "PASS":
        raise RuntimeError("Phase 65 sample schema gate failed; inspect summary.json")


if __name__ == "__main__":
    main()
