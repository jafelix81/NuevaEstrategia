from __future__ import annotations

import json
from pathlib import Path
import requests

BASE = "https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
OUT = Path("phase38_finra_ats_audit")
OUT.mkdir(exist_ok=True)

# Deliberately sampled across the documented rolling-history window. The goal is
# feasibility/coverage only; no return test is run in this phase.
MONTHS = ["2023-Jan", "2024-Jan", "2025-Jan", "2026-Jan"]
TIERS = ["T1", "T2"]
FIELDS = [
    "issueSymbolIdentifier", "issueName", "weekStartDate", "tierIdentifier",
    "summaryTypeCode", "totalWeeklyShareQuantity", "totalWeeklyTradeCount",
    "initialPublishedDate", "lastUpdateDate",
]

# Reuse the repository's frozen universe definition rather than constructing a new universe.
from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE
UNIVERSE = {str(x).upper() for x in DEFAULT_UNIVERSE}


def request_month(month: str, tier: str):
    rows = []
    offset = 0
    page = 0
    audit = []
    while True:
        payload = {
            "fields": FIELDS,
            "compareFilters": [
                {"compareType": "equal", "fieldName": "historicalMonth", "fieldValue": month},
                {"compareType": "equal", "fieldName": "tierIdentifier", "fieldValue": tier},
            ],
            "limit": 5000,
            "offset": offset,
        }
        r = requests.post(BASE, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=90)
        text = r.text[:1000]
        if r.status_code != 200:
            raise RuntimeError(f"POST failed {month}/{tier}: HTTP {r.status_code}: {text}")
        obj = r.json()
        data = obj.get("data", obj) if isinstance(obj, (dict, list)) else []
        if isinstance(data, dict):
            data = data.get("data", [])
        if not data:
            break
        rows.extend(data)
        audit.append({"month": month, "tier": tier, "page": page, "offset": offset, "rows": len(data)})
        page += 1
        offset += len(data)
        if len(data) < 5000:
            break
        if page > 200:
            raise RuntimeError(f"Pagination guard exceeded for {month}/{tier}")
    return rows, audit


all_rows = []
all_audit = []
errors = []
for month in MONTHS:
    for tier in TIERS:
        try:
            rows, audit = request_month(month, tier)
            all_rows.extend(rows)
            all_audit.extend(audit)
        except Exception as exc:
            errors.append({"month": month, "tier": tier, "error": repr(exc)})

# Coverage is measured on issueSymbolIdentifier, not firms/MPIDs.
seen = {}
for row in all_rows:
    sym = str(row.get("issueSymbolIdentifier", "")).upper()
    if sym:
        seen.setdefault(sym, set()).add(f"{row.get('weekStartDate')}|{row.get('tierIdentifier')}")

covered = sorted(UNIVERSE & set(seen))
missing = sorted(UNIVERSE - set(seen))

report = {
    "phase": "38",
    "source": "FINRA OTCMarket weeklySummaryHistoric",
    "months": MONTHS,
    "tiers": TIERS,
    "frozen_universe_size": len(UNIVERSE),
    "rows_retrieved": len(all_rows),
    "unique_symbols_seen": len(seen),
    "frozen_universe_symbols_seen": len(covered),
    "frozen_universe_coverage_pct": round(100.0 * len(covered) / len(UNIVERSE), 2),
    "missing_count": len(missing),
    "errors": errors,
    "pagination": all_audit,
    "pit_fields_present": bool(all_rows) and all("initialPublishedDate" in r for r in all_rows[: min(100, len(all_rows))]),
    "status": "PROMOTE_TO_SECURITY_LEVEL_RESEARCH" if len(covered) >= 0.90 * len(UNIVERSE) and not errors else "HOLD_FOR_COVERAGE_OR_ACCESS_REVIEW",
}
(OUT / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(OUT / "covered_symbols.txt").write_text("\n".join(covered) + "\n", encoding="utf-8")
(OUT / "missing_symbols.txt").write_text("\n".join(missing) + "\n", encoding="utf-8")
(OUT / "sample_rows.json").write_text(json.dumps(all_rows[:100], indent=2, default=str), encoding="utf-8")
print(json.dumps(report, indent=2))

if report["status"] != "PROMOTE_TO_SECURITY_LEVEL_RESEARCH":
    raise SystemExit(2)
