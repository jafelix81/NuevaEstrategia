from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

PHASE = 525
DATA_DIR = Path("research/data")
FORM144_PATH = DATA_DIR / "sec_form144_first_seen" / "sale_details.csv"
FORM4_PATH = DATA_DIR / "sec_form4_first_seen" / "transaction_details.csv"
OWNERS_PATH = DATA_DIR / "sec_form4_first_seen" / "reporting_owners.csv"

OUTPUT_FIELDS = [
    "form144_event_role", "form144_accession", "form4_accession",
    "issuer_cik", "issuer_name", "owner_cik", "owner_name",
    "transaction_date", "shares", "transaction_code", "acquired_disposed_code",
    "security_class", "security_title", "form144_reported_value",
    "form4_calculated_gross_value", "value_difference",
    "form144_acceptance_utc", "form144_first_seen_upper_utc",
    "form4_acceptance_utc", "form4_first_seen_upper_utc",
    "availability_relation", "form4_remarks_flags_json",
    "economic_context_class", "signal_eligible", "historical_f80_membership_verified",
]


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return list(reader)


def decimal_value(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def normalize_name(value: str | None) -> tuple[str, ...]:
    tokens = re.findall(r"[A-Z0-9]+", str(value or "").upper())
    return tuple(sorted(tokens))


def security_matches(left: str | None, right: str | None) -> bool:
    def canonical(value: str | None) -> tuple[str, ...]:
        tokens = re.findall(r"[A-Z0-9]+", str(value or "").upper())
        while tokens and tokens[-1] in {"STOCK", "SHARES"}:
            tokens.pop()
        return tuple(tokens)
    a, b = canonical(left), canonical(right)
    return bool(a and b and a == b)


def load_single_owner_index(owner_rows: list[dict]) -> tuple[dict, set[str]]:
    grouped: dict[str, list[dict]] = {}
    for row in owner_rows:
        grouped.setdefault(row.get("accession", ""), []).append(row)
    index = {}
    multi_owner = set()
    for accession, rows in grouped.items():
        first = rows[0]
        count = int(first.get("reporting_owner_count") or 0)
        status = first.get("line_owner_link_status")
        if count > 1 or status == "MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK":
            multi_owner.add(accession)
            continue
        if (
            count == 1
            and status == "SINGLE_REPORTING_OWNER_FILING_GRAIN_ONLY"
            and first.get("owner_cik")
            and first.get("owner_name")
            and first.get("parse_status") == "parsed"
        ):
            index[accession] = first
    return index, multi_owner


def availability_relation(event_role: str, form144_acceptance: str, form4_acceptance: str) -> str:
    if event_role == "PRIOR_SALE_HISTORY":
        return "HISTORICAL_SALE_LISTED_IN_FORM144"
    if not form144_acceptance or not form4_acceptance:
        return "ACCEPTANCE_CLOCK_UNRESOLVED"
    if form144_acceptance < form4_acceptance:
        return "FORM144_ACCEPTED_BEFORE_FORM4_ACCEPTANCE_EXECUTION_TIME_UNKNOWN"
    if form144_acceptance > form4_acceptance:
        return "FORM144_ACCEPTED_AFTER_FORM4_ACCEPTANCE"
    return "SAME_ACCEPTANCE_TIMESTAMP_EXECUTION_TIME_UNKNOWN"


def economic_context(flags: dict) -> str:
    if any(flags.get(key) for key in (
        "exercise_price_payment_mention", "tax_planning_mention",
        "tax_or_withholding_mention", "automatic_sell_to_cover_mention",
    )):
        return "EXERCISE_OR_TAX_CONTEXT_MENTIONED"
    if flags.get("rule_10b5_1_mention"):
        return "RULE_10B5_1_MENTIONED"
    if flags.get("open_market_mention"):
        return "OPEN_MARKET_MENTIONED"
    return "NO_SPECIFIC_REMARKS_FLAG"


def form144_events(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        if row.get("parse_status") != "parsed" or row.get("form") == "144/A":
            continue
        section = row.get("detail_section")
        if section == "securities_information":
            quantity = decimal_value(row.get("proposed_units_numeric"))
            event_date = row.get("approx_sale_date_iso")
            reported_value = decimal_value(row.get("aggregate_market_value_numeric"))
            seller = row.get("seller_name")
            role = "PROPOSED_SALE"
        elif section == "securities_sold_in_past_3_months":
            quantity = decimal_value(row.get("prior_sale_amount_numeric"))
            event_date = row.get("prior_sale_date_iso")
            reported_value = decimal_value(row.get("prior_sale_gross_proceeds_numeric"))
            seller = row.get("prior_sale_seller") or row.get("seller_name")
            role = "PRIOR_SALE_HISTORY"
        else:
            continue
        if quantity is None or not event_date or not row.get("issuer_cik") or not row.get("filer_cik"):
            continue
        result.append({
            "role": role,
            "accession": row.get("accession"),
            "issuer_cik": row.get("issuer_cik"),
            "issuer_name": row.get("issuer_name"),
            "owner_cik": row.get("filer_cik"),
            "owner_name": seller,
            "owner_name_key": normalize_name(seller),
            "date": event_date,
            "quantity": quantity,
            "security_class": row.get("security_class"),
            "reported_value": reported_value,
            "acceptance": row.get("submission_acceptance_utc"),
            "first_seen_upper": row.get("first_seen_interval_upper_bound_utc") or row.get("first_seen_at_utc"),
        })
    return result


def build_crosswalk(form144_rows: list[dict], form4_rows: list[dict], owner_rows: list[dict]) -> tuple[list[dict], dict]:
    owner_index, multi_owner = load_single_owner_index(owner_rows)
    sales = form144_events(form144_rows)
    transactions = [
        row for row in form4_rows
        if row.get("detail_type") == "transaction_row"
        and row.get("parse_status") == "parsed"
        and row.get("transaction_code") == "S"
        and row.get("acquired_disposed_code") == "D"
    ]
    output = []
    ambiguous_events = 0
    candidate_pairs = []
    for sale in sales:
        candidates = []
        for tx in transactions:
            owner = owner_index.get(tx.get("accession", ""))
            if owner is None:
                continue
            if (
                sale["issuer_cik"] != tx.get("issuer_cik")
                or sale["owner_cik"] != owner.get("owner_cik")
                or sale["owner_name_key"] != normalize_name(owner.get("owner_name"))
                or sale["date"] != tx.get("transaction_date")
                or sale["quantity"] != decimal_value(tx.get("shares_numeric"))
                or not security_matches(sale["security_class"], tx.get("security_title"))
            ):
                continue
            candidates.append((tx, owner))
        if len(candidates) > 1:
            ambiguous_events += 1
        elif len(candidates) == 1:
            candidate_pairs.append((sale, candidates[0][0], candidates[0][1]))

    def transaction_key(tx: dict) -> str:
        return "|".join((
            tx.get("accession", ""), tx.get("table_type", ""),
            tx.get("row_index", ""), tx.get("transaction_date", ""),
            tx.get("transaction_code", ""), tx.get("shares_numeric", ""),
            tx.get("price_per_share_numeric", ""), tx.get("acquired_disposed_code", ""),
            tx.get("security_title", ""),
        ))

    reuse_counts = {}
    for _, tx, _ in candidate_pairs:
        key = transaction_key(tx)
        reuse_counts[key] = reuse_counts.get(key, 0) + 1
    ambiguous_reuse_keys = {key for key, count in reuse_counts.items() if count > 1}

    for sale, tx, owner in candidate_pairs:
        if transaction_key(tx) in ambiguous_reuse_keys:
            continue
        price = decimal_value(tx.get("price_per_share_numeric"))
        gross = sale["quantity"] * price if price is not None else None
        difference = sale["reported_value"] - gross if sale["reported_value"] is not None and gross is not None else None
        try:
            flags = json.loads(owner.get("remarks_flags_json") or "{}")
        except json.JSONDecodeError:
            flags = {}
        output.append({
            "form144_event_role": sale["role"],
            "form144_accession": sale["accession"],
            "form4_accession": tx.get("accession"),
            "issuer_cik": sale["issuer_cik"],
            "issuer_name": sale["issuer_name"] or tx.get("issuer_name"),
            "owner_cik": sale["owner_cik"],
            "owner_name": sale["owner_name"],
            "transaction_date": sale["date"],
            "shares": str(sale["quantity"]),
            "transaction_code": tx.get("transaction_code"),
            "acquired_disposed_code": tx.get("acquired_disposed_code"),
            "security_class": sale["security_class"],
            "security_title": tx.get("security_title"),
            "form144_reported_value": str(sale["reported_value"]) if sale["reported_value"] is not None else "",
            "form4_calculated_gross_value": str(gross) if gross is not None else "",
            "value_difference": str(difference) if difference is not None else "",
            "form144_acceptance_utc": sale["acceptance"],
            "form144_first_seen_upper_utc": sale["first_seen_upper"],
            "form4_acceptance_utc": tx.get("acceptance_datetime_utc"),
            "form4_first_seen_upper_utc": tx.get("first_seen_interval_upper_bound_utc") or tx.get("first_seen_at_utc"),
            "availability_relation": availability_relation(sale["role"], sale["acceptance"], tx.get("acceptance_datetime_utc", "")),
            "form4_remarks_flags_json": json.dumps(flags, sort_keys=True, separators=(",", ":")),
            "economic_context_class": economic_context(flags),
            "signal_eligible": False,
            "historical_f80_membership_verified": False,
        })

    proposed_output = [row for row in output if row["form144_event_role"] == "PROPOSED_SALE"]
    missing_form144_acceptance = [
        row for row in proposed_output if not row["form144_acceptance_utc"]
    ]
    missing_form4_acceptance = [
        row for row in proposed_output if not row["form4_acceptance_utc"]
    ]
    unresolved_acceptance = [
        row for row in proposed_output
        if row["availability_relation"] == "ACCEPTANCE_CLOCK_UNRESOLVED"
    ]
    acceptance_clock_audit = {
        "proposed_sale_rows": len(proposed_output),
        "missing_form144_acceptance_rows": len(missing_form144_acceptance),
        "missing_form144_acceptance_accessions": sorted({
            row["form144_accession"] for row in missing_form144_acceptance
        }),
        "missing_form4_acceptance_rows": len(missing_form4_acceptance),
        "missing_form4_acceptance_accessions": sorted({
            row["form4_accession"] for row in missing_form4_acceptance
        }),
        "unresolved_acceptance_clock_rows": len(unresolved_acceptance),
    }

    summary = {
        "phase": PHASE,
        "acceptance_clock_audit": acceptance_clock_audit,
        "form144_proposed_sale_rows": sum(1 for x in form144_rows if x.get("detail_section") == "securities_information" and x.get("parse_status") == "parsed"),
        "form144_prior_sale_rows": sum(1 for x in form144_rows if x.get("detail_section") == "securities_sold_in_past_3_months" and x.get("parse_status") == "parsed"),
        "form144_amendment_detail_rows_excluded": sum(1 for x in form144_rows if x.get("form") == "144/A"),
        "form144_proposed_sale_rows_considered": sum(1 for x in sales if x["role"] == "PROPOSED_SALE"),
        "form144_prior_sale_rows_considered": sum(1 for x in sales if x["role"] == "PRIOR_SALE_HISTORY"),
        "form4_sale_disposition_rows": len(transactions),
        "owner_sidecar_accessions": len(owner_index) + len(multi_owner),
        "single_owner_accessions_with_identity": len(owner_index),
        "multi_owner_accessions_quarantined": len(multi_owner),
        "matched_proposed_sales": sum(1 for x in output if x["form144_event_role"] == "PROPOSED_SALE"),
        "matched_prior_sales": sum(1 for x in output if x["form144_event_role"] == "PRIOR_SALE_HISTORY"),
        "matched_form4_accessions": len({row["form4_accession"] for row in output}),
        "ambiguous_form144_events_quarantined": ambiguous_events,
        "ambiguous_transaction_reuse_quarantined": len(ambiguous_reuse_keys),
        "form4_accessions_without_single_owner_identity": sum(
            1 for tx in transactions if tx.get("accession") not in owner_index
        ),
        "signal_eligible_matches": 0,
        "historical_f80_membership_verified": False,
        "execution_intraday_time_known": False,
        "alpha_test_authorized": False,
    }
    return output, summary


def run_crosswalk(
    output_dir: Path,
    form144_path: Path = FORM144_PATH,
    form4_path: Path = FORM4_PATH,
    owners_path: Path = OWNERS_PATH,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, summary = build_crosswalk(
        read_csv(form144_path), read_csv(form4_path), read_csv(owners_path)
    )
    with (output_dir / "form144_form4_crosswalk.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary["crosswalk_rows"] = len(rows)
    summary["disposition"] = "DESCRIPTIVE_CROSSWALK_ONLY_NO_SIGNAL"
    (output_dir / "crosswalk_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_crosswalk(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
