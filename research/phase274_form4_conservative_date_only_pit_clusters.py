#!/usr/bin/env python3
"""Phase 274: conservative date-only PIT boundary and same-trade-date Form 4 clusters.

Uses the unchanged Phase 271 eligibility screen via Phase 272. This is a
source/event-structure audit, not a return or alpha test.
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import exchange_calendars as xc
import pandas as pd

from research.phase272_form4_candidate_unit_price_basis_audit import (
    EXPECTED_OUTER_SHA256,
    EXPECTED_INNER_SHA256,
    _candidate_rows,
    sha256_bytes,
)

ET = ZoneInfo("America/New_York")
SEARCH_DAYS = 14


def parse_filing_date(value: str) -> date:
    value = (value or "").strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"invalid SEC FILING_DATE: {value!r}")


def parse_transaction_date(value: str) -> date:
    value = (value or "").strip()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid Form 4 transaction date: {value!r}") from exc


def first_xnys_session_after(filing_date: date, calendar=None) -> dict[str, str]:
    """Return the first XNYS session strictly after a date-only EDGAR filing date.

    Execution is delayed to that session's close. This is deliberately more
    conservative than same-day or next-session-open execution and handles
    weekends, holidays, and early closes through the exchange calendar.
    """
    if not isinstance(filing_date, date):
        raise ValueError("filing_date must be a date")
    calendar = calendar or xc.get_calendar("XNYS")
    start = pd.Timestamp(filing_date + timedelta(days=1))
    end = pd.Timestamp(filing_date + timedelta(days=SEARCH_DAYS))
    sessions = calendar.sessions_in_range(start, end)
    if len(sessions) == 0:
        raise ValueError("no XNYS session found after filing date")
    session = sessions[0]
    close_utc = calendar.session_close(session)
    close_et = close_utc.tz_convert(ET.key)
    if session.date() <= filing_date:
        raise AssertionError("availability session is not strictly after filing date")
    return {
        "session": session.date().isoformat(),
        "close_et": close_et.isoformat(),
        "close_utc": close_utc.isoformat(),
    }


def _period_plan_status(period: str) -> str:
    if period >= "2023Q2":
        return "AFF10B5ONE_FALSE_REQUIRED_BY_SCREEN"
    return "AFF10B5ONE_NOT_AVAILABLE_OR_NOT_REQUIRED_UNKNOWN"


def build_cluster_records(
    rows: list[dict[str, Any]], period: str, calendar=None
) -> dict[str, Any]:
    """Build same-issuer, same-filing-date, same-transaction-date owner clusters."""
    calendar = calendar or xc.get_calendar("XNYS")
    by_accession: dict[str, list[dict[str, Any]]] = defaultdict(list)
    invalid_transaction_date_rows = 0
    negative_filing_lag_rows = 0
    for row in rows:
        accession = str(row.get("accession") or "")
        if not accession:
            raise ValueError("candidate row missing accession")
        by_accession[accession].append(row)

    accession_owner: dict[str, str] = {}
    accession_issuer: dict[str, str] = {}
    accession_filing: dict[str, date] = {}
    for accession, accession_rows in by_accession.items():
        owners = {str(r.get("owner_cik") or "") for r in accession_rows}
        issuers = {str(r.get("issuer_cik") or "") for r in accession_rows}
        filing_dates = {parse_filing_date(str(r.get("filing_date") or "")) for r in accession_rows}
        if len(owners) != 1 or "" in owners:
            raise ValueError(f"accession {accession} does not have exactly one reporting-owner CIK")
        if len(issuers) != 1 or "" in issuers:
            raise ValueError(f"accession {accession} has inconsistent/missing issuer CIK")
        if len(filing_dates) != 1:
            raise ValueError(f"accession {accession} has inconsistent filing dates")
        accession_owner[accession] = next(iter(owners))
        accession_issuer[accession] = next(iter(issuers))
        accession_filing[accession] = next(iter(filing_dates))

    groups: dict[tuple[str, date, date], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        tx_value = row.get("transaction_date_iso")
        if not tx_value:
            invalid_transaction_date_rows += 1
            continue
        tx_date = parse_transaction_date(str(tx_value))
        filing = parse_filing_date(str(row.get("filing_date") or ""))
        lag = (filing - tx_date).days
        if lag < 0:
            negative_filing_lag_rows += 1
            continue
        issuer = str(row.get("issuer_cik") or "")
        if not issuer:
            raise ValueError("candidate row missing issuer CIK")
        groups[(issuer, filing, tx_date)].append(row)

    filing_date_groups: dict[tuple[str, date], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("transaction_date_iso"):
            filing = parse_filing_date(str(row.get("filing_date") or ""))
            filing_date_groups[(str(row.get("issuer_cik") or ""), filing)].append(row)

    broad_multi_owner_filing_date_groups = 0
    for group_rows in filing_date_groups.values():
        accessions = {str(r["accession"]) for r in group_rows}
        owners = {str(r["owner_cik"]) for r in group_rows}
        if len(accessions) >= 2 and len(owners) >= 2:
            broad_multi_owner_filing_date_groups += 1

    clusters = []
    for (issuer_cik, filing, tx_date), group_rows in sorted(
        groups.items(), key=lambda x: (x[0][1], x[0][0], x[0][2])
    ):
        accessions = sorted({str(r["accession"]) for r in group_rows})
        owners = sorted({str(r["owner_cik"]) for r in group_rows})
        if len(accessions) < 2 or len(owners) < 2:
            continue
        if len({accession_issuer[a] for a in accessions}) != 1:
            raise AssertionError("cluster crosses issuer identity")
        if len({accession_filing[a] for a in accessions}) != 1:
            raise AssertionError("cluster crosses filing date")
        availability = first_xnys_session_after(filing, calendar)
        owner_roles: dict[str, str] = {}
        owner_legal_entity: dict[str, bool] = {}
        for row in group_rows:
            owner = str(row["owner_cik"])
            role = str(row.get("owner_role_class") or "unknown")
            prior = owner_roles.get(owner)
            if prior is not None and prior != role:
                raise ValueError(f"owner role class changes within cluster for CIK {owner}")
            owner_roles[owner] = role
            owner_legal_entity[owner] = bool(row.get("owner_name_legal_entity_flag"))
        clusters.append({
            "issuer_cik": issuer_cik,
            "ticker": str(group_rows[0].get("ticker") or ""),
            "filing_date": filing.isoformat(),
            "transaction_date": tx_date.isoformat(),
            "filing_lag_calendar_days": (filing - tx_date).days,
            "accession_count": len(accessions),
            "reporting_owner_cik_count": len(owners),
            "candidate_transaction_rows": len(group_rows),
            "accessions": accessions,
            "reporting_owner_ciks": owners,
            "owner_role_class_counts": dict(sorted(Counter(owner_roles.values()).items())),
            "legal_entity_name_flag_owner_count": sum(owner_legal_entity.values()),
            "first_tradable_xnys_session": availability["session"],
            "first_tradable_close_et": availability["close_et"],
            "first_tradable_close_utc": availability["close_utc"],
            "plan_status": _period_plan_status(period),
        })

    all_accessions = set(by_accession)
    all_issuers = {str(r.get("issuer_cik") or "") for r in rows}
    all_owners = {str(r.get("owner_cik") or "") for r in rows}
    cluster_accessions = {a for c in clusters for a in c["accessions"]}
    cluster_owners = {o for c in clusters for o in c["reporting_owner_ciks"]}
    cluster_issuers = {c["issuer_cik"] for c in clusters}
    cluster_rows = sum(c["candidate_transaction_rows"] for c in clusters)
    lags = [c["filing_lag_calendar_days"] for c in clusters]
    return {
        "period": period,
        "candidate_transaction_rows": len(rows),
        "unique_accessions": len(all_accessions),
        "unique_issuers": len(all_issuers),
        "unique_reporting_owners": len(all_owners),
        "broad_issuer_filing_date_multi_owner_groups": broad_multi_owner_filing_date_groups,
        "same_issuer_filing_date_transaction_date_multi_owner_clusters": len(clusters),
        "cluster_accession_memberships": sum(c["accession_count"] for c in clusters),
        "cluster_reporting_owner_memberships": sum(c["reporting_owner_cik_count"] for c in clusters),
        "unique_issuers_in_clusters": len(cluster_issuers),
        "unique_accessions_in_clusters": len(cluster_accessions),
        "unique_reporting_owners_in_clusters": len(cluster_owners),
        "transaction_rows_in_clusters": cluster_rows,
        "cluster_row_share": round(cluster_rows / len(rows), 6) if rows else None,
        "cluster_filing_lag_calendar_days": {
            "min": min(lags) if lags else None,
            "median": sorted(lags)[len(lags)//2] if lags else None,
            "max": max(lags) if lags else None,
        },
        "invalid_transaction_date_rows": invalid_transaction_date_rows,
        "negative_filing_lag_rows_quarantined": negative_filing_lag_rows,
        "plan_status": _period_plan_status(period),
        "clusters": clusters,
    }


def analyze_artifact(path: str | Path) -> dict[str, Any]:
    outer_bytes = Path(path).read_bytes()
    outer_hash = sha256_bytes(outer_bytes)
    if outer_hash != EXPECTED_OUTER_SHA256:
        raise ValueError("Phase 39 outer artifact SHA-256 mismatch")
    periods = {}
    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer:
        for filename, expected_hash in EXPECTED_INNER_SHA256.items():
            inner_bytes = outer.read(filename)
            if sha256_bytes(inner_bytes) != expected_hash:
                raise ValueError(f"Phase 39 inner artifact SHA-256 mismatch: {filename}")
            period = "2012Q1" if filename.startswith("2012") else "2026Q3"
            rows = _candidate_rows(inner_bytes, period)
            periods[period] = build_cluster_records(rows, period)

    expected = {
        "2012Q1": {
            "candidate_transaction_rows": 102, "unique_accessions": 47, "unique_issuers": 16,
            "same_issuer_filing_date_transaction_date_multi_owner_clusters": 1,
            "cluster_accession_memberships": 3, "cluster_reporting_owner_memberships": 3,
            "unique_accessions_in_clusters": 3, "unique_reporting_owners_in_clusters": 3,
            "transaction_rows_in_clusters": 3, "unique_issuers_in_clusters": 1,
        },
        "2026Q3": {
            "candidate_transaction_rows": 85, "unique_accessions": 59, "unique_issuers": 31,
            "same_issuer_filing_date_transaction_date_multi_owner_clusters": 11,
            "cluster_accession_memberships": 23, "cluster_reporting_owner_memberships": 23,
            "unique_accessions_in_clusters": 19, "unique_reporting_owners_in_clusters": 19,
            "transaction_rows_in_clusters": 24, "unique_issuers_in_clusters": 8,
        },
    }
    for period, checks in expected.items():
        for key, value in checks.items():
            if periods[period][key] != value:
                raise ValueError(f"unexpected {period} {key}: {periods[period][key]} != {value}")
    return {
        "phase": 274,
        "source": "SEC Insider Transactions Data Sets, Phase 39 immutable Form 345 artifact",
        "source_outer_sha256": outer_hash,
        "source_inner_sha256": dict(EXPECTED_INNER_SHA256),
        "availability_policy": "close of first XNYS session strictly after the EDGAR FILING_DATE; never same-day close or next-session open",
        "availability_policy_is_conservative_date_only_bound": True,
        "strict_pit_admitted": False,
        "strict_pit_blockers": [
            "The bulk extract is quarterly and is not itself an immutable original EDGAR filing receipt archive.",
            "Original accession bytes and acceptance/first-receipt vintages are not preserved for every candidate.",
            "Form 4/A parent lineage and line-level amendment state are not complete across a continuous panel.",
            "Only two endpoint quarters are present; historical universe coverage and delisted-security identity are unmeasured.",
        ],
        "alpha_test_authorized": False,
        "forward_returns_tested": False,
        "bootstrap_loo_tested": False,
        "chronological_oos_tested": False,
        "holdout_used": False,
        "f80_frozen": True,
        "periods": periods,
        "decision": "Retain same-issuer, same-filing-date, same-transaction-date multi-reporting-owner purchases as a candidate event hypothesis. Use the next-XNYS-session-close boundary for any daily-EOD study, but do not admit the bulk extract as strict historical PIT or claim alpha until original accession/vintage and continuous coverage gates pass.",
    }


def main() -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_artifact(args.artifact)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
