#!/usr/bin/env python3
"""Phase 272: Form 4 candidate unit-of-analysis and reported-price integrity audit.

Reuses the exact Phase 271 eligibility screen on the immutable Phase 39 source
artifact. This is a descriptive source-quality audit only; it does not test
returns, PIT availability, or alpha.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

EXPECTED_OUTER_SHA256 = "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
EXPECTED_INNER_SHA256 = {
    "2012q1_form345.zip": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2026q3_form345.zip": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
OPEN_MARKET_RE = re.compile(r"\bopen[- ]market\b", re.I)
PRIVATE_RE = re.compile(r"\bprivate\b", re.I)
PLAN_RE = re.compile(r"\b(?:10b5[- ]?1|plan|ESPP|employee stock purchase)\b", re.I)
MECHANICAL_RE = re.compile(r"\b(?:tax|withhold|exercise|grant|vesting|gift|automatic|option|award|compensation|employee|match(?:ing)?)\b", re.I)
COMMON_RE = re.compile(r"\bcommon (?:stock|shares)\b", re.I)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def classify_purchase_row(row, footnote_text, owner_count, aff_value, require_known_false):
    aff = (aff_value or "").strip().lower()
    aff = "true" if aff in {"1", "true", "yes"} else "false" if aff in {"0", "false", "no"} else "unknown"
    return {
        "base": row.get("DOCUMENT_TYPE") == "4" and row.get("TRANS_FORM_TYPE") == "4" and row.get("TRANS_CODE") == "P" and row.get("TRANS_ACQUIRED_DISP_CD") == "A",
        "explicit_open_market": bool(OPEN_MARKET_RE.search(footnote_text)),
        "no_private_disclosure": not bool(PRIVATE_RE.search(footnote_text)),
        "no_plan_disclosure": not bool(PLAN_RE.search(footnote_text)),
        "no_mechanical_disclosure": not bool(MECHANICAL_RE.search(footnote_text)),
        "direct_ownership": row.get("DIRECT_INDIRECT_OWNERSHIP") == "D",
        "single_reporting_owner": owner_count == 1,
        "common_stock_title": bool(COMMON_RE.search(row.get("SECURITY_TITLE", ""))),
        "aff_status": aff,
        "aff_gate": (aff == "false") if require_known_false else True,
    }

SHARE_BASIS_RE = re.compile(
    r"\b(?:converted|adjusted)\s+to\s+apply\b|\bmost recent (?:quarterly|annual) report\b",
    re.I,
)
LEGAL_ENTITY_NAME_RE = re.compile(
    r"\b(?:INC(?:ORPORATED)?|CORP(?:ORATION)?|LLC|L\.?P\.?|LTD|LIMITED|TRUST|COMPANY|CO\.?)\b",
    re.I,
)


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t"))


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def parse_sec_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def role_class(role: str | None) -> str:
    tokens = {x.strip() for x in (role or "").split(",") if x.strip()}
    if tokens & {"Director", "Officer"}:
        return "director_or_officer"
    if tokens == {"TenPercentOwner"}:
        return "ten_percent_owner_only"
    if not tokens:
        return "unknown"
    return "other_or_mixed"


def _candidate_rows(inner_bytes: bytes, period: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as zf:
        submissions = read_tsv(zf, "SUBMISSION.tsv")
        transactions = read_tsv(zf, "NONDERIV_TRANS.tsv")
        footnotes = read_tsv(zf, "FOOTNOTES.tsv")
        owners = read_tsv(zf, "REPORTINGOWNER.tsv")

    submission_by_acc = {r["ACCESSION_NUMBER"]: r for r in submissions}
    owners_by_acc: dict[str, list[dict[str, str]]] = defaultdict(list)
    for owner in owners:
        owners_by_acc[owner["ACCESSION_NUMBER"]].append(owner)
    footnotes_by_acc: dict[str, dict[str, str]] = defaultdict(dict)
    for row in footnotes:
        footnotes_by_acc[row["ACCESSION_NUMBER"]][row["FOOTNOTE_ID"]] = row["FOOTNOTE_TXT"]

    require_known_false = period >= "2023Q2"
    output: list[dict[str, Any]] = []
    for tx in transactions:
        accession = tx.get("ACCESSION_NUMBER", "")
        sub = submission_by_acc.get(accession)
        if not sub:
            continue
        owner_rows = owners_by_acc.get(accession, [])
        foot_map = footnotes_by_acc.get(accession, {})
        refs: set[str] = set()
        for key, value in tx.items():
            if key.endswith("_FN"):
                refs.update(re.findall(r"F\d+", value or ""))
        footnote_text = " ".join(foot_map[x] for x in sorted(refs) if x in foot_map)
        row = dict(tx)
        row["DOCUMENT_TYPE"] = sub.get("DOCUMENT_TYPE", "")
        aff = sub.get("AFF10B5ONE", "")
        flags = classify_purchase_row(row, footnote_text, len(owner_rows), aff, require_known_false)
        eligible = (
            flags["base"]
            and flags["explicit_open_market"]
            and flags["no_private_disclosure"]
            and flags["no_plan_disclosure"]
            and flags["no_mechanical_disclosure"]
            and flags["direct_ownership"]
            and flags["single_reporting_owner"]
            and flags["common_stock_title"]
            and flags["aff_gate"]
        )
        if not eligible:
            continue
        owner = owner_rows[0]
        shares = parse_decimal(tx.get("TRANS_SHARES"))
        price = parse_decimal(tx.get("TRANS_PRICEPERSHARE"))
        share_basis_restatement = bool(SHARE_BASIS_RE.search(footnote_text))
        if shares is None or shares <= 0:
            value_status = "invalid_shares"
            reported_value_proxy = None
        elif price is None:
            value_status = "missing_price"
            reported_value_proxy = None
        elif price < 0:
            value_status = "negative_price"
            reported_value_proxy = None
        elif price == 0:
            value_status = "reported_zero_price_unquantifiable"
            reported_value_proxy = None
        elif share_basis_restatement:
            value_status = "positive_price_but_share_basis_restatement"
            reported_value_proxy = None
        else:
            value_status = "positive_price_proxy_only"
            reported_value_proxy = shares * price

        tx_date = parse_sec_date(tx.get("TRANS_DATE"))
        role = owner.get("RPTOWNER_RELATIONSHIP", "")
        output.append({
            "accession": accession,
            "issuer_cik": sub.get("ISSUERCIK", ""),
            "issuer_name": sub.get("ISSUERNAME", ""),
            "ticker": sub.get("ISSUERTRADINGSYMBOL", ""),
            "filing_date": sub.get("FILING_DATE", ""),
            "transaction_date_iso": tx_date.date().isoformat() if tx_date else None,
            "owner_cik": owner.get("RPTOWNERCIK", ""),
            "owner_name": owner.get("RPTOWNERNAME", ""),
            "owner_role_class": role_class(role),
            "owner_name_legal_entity_flag": bool(LEGAL_ENTITY_NAME_RE.search(owner.get("RPTOWNERNAME", ""))),
            "reported_value_proxy": str(reported_value_proxy) if reported_value_proxy is not None else None,
            "reported_value_status": value_status,
            "share_basis_restatement_flag": share_basis_restatement,
        })
    return output


def _hhi_summary(counter: Counter[str], total: int) -> dict[str, Any]:
    if total <= 0:
        return {"groups": 0, "hhi": None, "effective_groups": None, "top1_share": None, "top2_share": None}
    shares = [n / total for n in counter.values()]
    hhi = sum(x * x for x in shares)
    ordered = sorted(shares, reverse=True)
    return {
        "groups": len(counter),
        "hhi": round(hhi, 6),
        "effective_groups": round(1 / hhi, 3) if hhi else None,
        "top1_share": round(ordered[0], 6) if ordered else 0.0,
        "top2_share": round(sum(ordered[:2]), 6),
    }


def _nearest_rank(values: list[Decimal], p: Decimal) -> str | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(float(p * len(ordered))))
    return str(ordered[rank - 1])


def summarize_period(rows: list[dict[str, Any]], period: str) -> dict[str, Any]:
    n = len(rows)
    by_issuer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_accession: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_issuer_owner: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_issuer[row["issuer_cik"]].append(row)
        by_owner[row["owner_cik"]].append(row)
        by_accession[row["accession"]].append(row)
        by_issuer_owner[(row["issuer_cik"], row["owner_cik"])].append(row)

    issuer_counter = Counter({k: len(v) for k, v in by_issuer.items()})
    owner_counter = Counter({k: len(v) for k, v in by_owner.items()})
    accession_counter = Counter({k: len(v) for k, v in by_accession.items()})
    role_counter = Counter(r["owner_role_class"] for r in rows)
    price_status_counter = Counter(r["reported_value_status"] for r in rows)
    zero_price_rows = [r for r in rows if r["reported_value_status"] == "reported_zero_price_unquantifiable"]
    basis_rows = [r for r in rows if r["share_basis_restatement_flag"]]
    legal_entity_rows = [r for r in rows if r["owner_name_legal_entity_flag"]]
    multi_row_accessions = {k: v for k, v in by_accession.items() if len(v) > 1}
    multi_owner_issuers = sum(1 for v in by_issuer.values() if len({x["owner_cik"] for x in v}) > 1)
    multi_accession_issuer_owner_groups = sum(1 for v in by_issuer_owner.values() if len({x["accession"] for x in v}) > 1)
    rows_in_multi_accession_issuer_owner_groups = sum(len(v) for v in by_issuer_owner.values() if len({x["accession"] for x in v}) > 1)

    value_proxies = [Decimal(r["reported_value_proxy"]) for r in rows if r["reported_value_proxy"] is not None]
    thresholds = {
        "under_10000": sum(x < Decimal("10000") for x in value_proxies),
        "under_100000": sum(x < Decimal("100000") for x in value_proxies),
        "under_1000000": sum(x < Decimal("1000000") for x in value_proxies),
    }

    examples: dict[str, Any] = {}
    for key, selector in {
        "2012_onteco": lambda r: r["ticker"].lower() == "ontc" or r["issuer_name"].lower() == "onteco corp",
        "2026_income_opportunity_realty": lambda r: r["ticker"].upper() == "IOR",
        "2026_ault_cross_issuer": lambda r: r["owner_name"].upper() == "AULT MILTON C III",
    }.items():
        group = [r for r in rows if selector(r)]
        if group:
            dates = [r["transaction_date_iso"] for r in group if r["transaction_date_iso"]]
            examples[key] = {
                "rows": len(group),
                "accessions": len({r["accession"] for r in group}),
                "issuers": len({r["issuer_cik"] for r in group}),
                "owners": len({r["owner_cik"] for r in group}),
                "filing_dates": sorted({r["filing_date"] for r in group}),
                "transaction_date_min": min(dates) if dates else None,
                "transaction_date_max": max(dates) if dates else None,
                "zero_reported_price_rows": sum(r["reported_value_status"] == "reported_zero_price_unquantifiable" for r in group),
                "share_basis_restatement_rows": sum(r["share_basis_restatement_flag"] for r in group),
                "owner_role_classes": dict(Counter(r["owner_role_class"] for r in group)),
                "legal_entity_name_rows": sum(r["owner_name_legal_entity_flag"] for r in group),
            }

    return {
        "period": period,
        "candidate_transaction_rows": n,
        "unique_accessions": len(by_accession),
        "unique_issuers": len(by_issuer),
        "unique_reporting_owners": len(by_owner),
        "unique_issuer_owner_groups": len(by_issuer_owner),
        "issuers_with_multiple_reporting_owners": multi_owner_issuers,
        "issuer_owner_groups_with_multiple_accessions": multi_accession_issuer_owner_groups,
        "rows_in_issuer_owner_groups_with_multiple_accessions": rows_in_multi_accession_issuer_owner_groups,
        "row_unit_concentration": {
            "issuer": _hhi_summary(issuer_counter, n),
            "owner": _hhi_summary(owner_counter, n),
            "accession": _hhi_summary(accession_counter, n),
        },
        "accession_row_clustering": {
            "accessions_with_multiple_transaction_rows": len(multi_row_accessions),
            "rows_in_multirow_accessions": sum(len(v) for v in multi_row_accessions.values()),
            "share_of_rows_in_multirow_accessions": round(sum(len(v) for v in multi_row_accessions.values()) / n, 6) if n else None,
            "maximum_rows_in_one_accession": max(accession_counter.values(), default=0),
        },
        "owner_role_row_counts": dict(sorted(role_counter.items())),
        "owner_name_legal_entity_flag_rows": len(legal_entity_rows),
        "owner_name_legal_entity_flag_unique_owners": len({r["owner_cik"] for r in legal_entity_rows}),
        "reported_price_field_status_counts": dict(sorted(price_status_counter.items())),
        "share_basis_restatement_rows": len(basis_rows),
        "share_basis_restatement_accessions": len({r["accession"] for r in basis_rows}),
        "share_basis_restatement_issuers": len({r["issuer_cik"] for r in basis_rows}),
        "reported_value_proxy": {
            "eligible_rows": len(value_proxies),
            "median": _nearest_rank(value_proxies, Decimal("0.50")),
            "p75": _nearest_rank(value_proxies, Decimal("0.75")),
            "p90": _nearest_rank(value_proxies, Decimal("0.90")),
            "max": str(max(value_proxies)) if value_proxies else None,
            "threshold_counts": thresholds,
            "warning": "TRANS_SHARES x TRANS_PRICEPERSHARE is only a reported-field diagnostic; it is not ADV-scaled, executable notional, or market impact. Zero/missing/negative prices and share-basis-restated rows are not assigned a zero value.",
        },
        "descriptive_examples": examples,
    }


def analyze_artifact(path: str | Path) -> dict[str, Any]:
    outer = Path(path).read_bytes()
    outer_hash = sha256_bytes(outer)
    if outer_hash != EXPECTED_OUTER_SHA256:
        raise ValueError("Phase 39 outer artifact SHA-256 mismatch")
    periods: dict[str, Any] = {}
    with zipfile.ZipFile(io.BytesIO(outer)) as zf:
        for filename, expected_hash in EXPECTED_INNER_SHA256.items():
            inner = zf.read(filename)
            if sha256_bytes(inner) != expected_hash:
                raise ValueError(f"Phase 39 inner artifact SHA-256 mismatch: {filename}")
            period = "2012Q1" if filename.startswith("2012") else "2026Q3"
            rows = _candidate_rows(inner, period)
            periods[period] = summarize_period(rows, period)

    return {
        "phase": 272,
        "date": "2026-11-10",
        "source_artifact": {
            "workflow_run_id": 40606706518,
            "artifact_id": 12781850078,
            "outer_sha256": outer_hash,
            "inner_sha256": EXPECTED_INNER_SHA256,
        },
        "method": {
            "candidate_population": "exact Phase 271 original Form 4 Table I P/A high-precision screen; no change to eligibility rules",
            "unit_of_analysis": "transaction rows are nested within accessions, issuer-owner groups, and issuers; row counts are not independent event counts",
            "price_basis": "reported TRANS_PRICEPERSHARE and TRANS_SHARES fields; zero price is UNKNOWN/unquantifiable rather than zero economic value; explicit share-basis restatement footnotes are quarantined from reported-value proxy",
            "role_split": "separate director/officer, ten-percent-owner-only, and other/mixed reporting-owner relationships; legal-entity-name match is a diagnostic only",
            "no_lookahead": "no transaction is assigned an event-availability time; filing date remains date-only and accession acceptance timestamps are not joined for these candidates",
        },
        "periods": periods,
        "admission": {
            "strict_pit": False,
            "universe_coverage": False,
            "return_test": False,
            "alpha": False,
            "bootstrap_loo": False,
            "chronological_oos": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "vendor_contact_or_purchase": False,
            "sec_request_made": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_artifact(args.artifact)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE272_STATUS=ROW_COUNTS_NOT_INDEPENDENT_EVENTS_PRICE_BASIS_AND_OWNER_ROLE_GATES_REQUIRED")
    for period, item in result["periods"].items():
        print(f"{period}: rows={item['candidate_transaction_rows']} accessions={item['unique_accessions']} issuers={item['unique_issuers']} zero_price={item['reported_price_field_status_counts'].get('reported_zero_price_unquantifiable',0)}")
    print("STRICT_PIT=false ALPHA=false HOLDOUT_USED=false F80_FROZEN=true")


if __name__ == "__main__":
    main()