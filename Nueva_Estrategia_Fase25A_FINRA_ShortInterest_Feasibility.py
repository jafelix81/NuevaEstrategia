import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

OUT = Path("nueva_estrategia_phase25a_finra_short_interest_feasibility")
OUT.mkdir(exist_ok=True)

API = "https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest"
ARCHIVE = "https://otce.finra.org/otce/EquityShortInterest/archives"

# Public FINRA consolidated short-interest dataset was launched in 2023 and
# provides five years of history; we test representative dates without assuming
# that the full historical universe is immediately available.
SAMPLES = [
    "2022-06-15",
    "2023-01-13",
    "2024-06-14",
    "2025-06-13",
    "2026-09-30",
]

headers = {
    "User-Agent": "NuevaEstrategia research contact: stockpulseusa@gmail.com",
    "Accept": "application/json",
}

session = requests.Session()
session.headers.update(headers)


def post_sample(date):
    payload = {
        "limit": 5,
        "compareFilters": [
            {"compareType": "equal", "fieldName": "settlementDate", "fieldValue": date}
        ],
    }
    t0 = time.time()
    r = session.post(API, json=payload, timeout=30)
    elapsed = round(time.time() - t0, 3)
    result = {"date": date, "http": r.status_code, "seconds": elapsed, "rows": None, "error": None}
    if r.ok:
        try:
            data = r.json()
            result["rows"] = len(data) if isinstance(data, list) else None
            if isinstance(data, list) and data:
                result["sample_fields"] = sorted(data[0].keys())
        except Exception as e:
            result["error"] = f"JSON_PARSE:{e}"
    else:
        result["error"] = r.text[:500]
    return result


def archive_probe():
    r = session.get(ARCHIVE, timeout=30)
    html = r.text
    hrefs = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html, flags=re.I)
    data_links = [h for h in hrefs if any(x in h.lower() for x in ["short", ".txt", ".zip", "archive"])]
    return {
        "http": r.status_code,
        "bytes": len(r.content),
        "candidate_links": data_links[:50],
        "candidate_count": len(data_links),
    }


results = [post_sample(d) for d in SAMPLES]
archive = archive_probe()

# Official-source timing note: short interest is a twice-monthly snapshot;
# publication timing must be reconstructed from FINRA's reporting calendar in
# the research phase. We intentionally do not manufacture a point-in-time rule here.

audit = {
    "phase": "25A",
    "status": "COMPLETE_FEASIBILITY",
    "source": "FINRA Consolidated Short Interest",
    "api": API,
    "sample_results": results,
    "archive_probe": archive,
    "research_policy": "Do not use settlementDate as knowledge date; reconstruct publication availability from FINRA reporting calendar before any predictive test.",
    "relationship_to_phase20": "Complementary to FINRA short-sale volume; short interest is an open-position snapshot, not transaction volume.",
    "production_change": False,
}

pd.DataFrame(results).to_csv(OUT / "phase25a_api_samples.csv", index=False)
with open(OUT / "phase25a_audit.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

print(json.dumps(audit, indent=2, ensure_ascii=False))
