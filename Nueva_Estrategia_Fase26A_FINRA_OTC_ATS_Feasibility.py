import json
import time
from datetime import date
from pathlib import Path

import requests

BASE = "https://api.finra.org"
OUT = Path("phase26a_outputs")
OUT.mkdir(exist_ok=True)

RESULT = {
    "phase": "26A",
    "source": "FINRA OTC/ATS weeklySummaryHistoric",
    "hypothesis": "Historical off-exchange/ATS participation, concentration and persistence may contain incremental information versus frozen LTM/F80.",
    "status": "UNKNOWN",
    "production_access": None,
    "metadata": None,
    "mock_access": None,
    "historical_coverage_claim": "rolling 4 years according to FINRA documentation",
    "point_in_time": "Requires explicit reconstruction from weekStartDate/initialPublishedDate/lastUpdateDate; no signal will be built until publication timing is established.",
}


def get(url, **kwargs):
    try:
        r = requests.get(url, timeout=30, **kwargs)
        return {"status_code": r.status_code, "content_type": r.headers.get("content-type"), "bytes": len(r.content), "text": r.text[:1000]}
    except Exception as e:
        return {"error": repr(e)}

# 1) Metadata is the most important no-credential feasibility check.
meta_url = f"{BASE}/metadata/group/otcmarket/name/weeklysummaryhistoric"
meta = get(meta_url)
RESULT["metadata"] = meta

# 2) Mock endpoint verifies schema/access mechanics without pretending mock data is production data.
mock_url = f"{BASE}/data/group/otcmarket/name/weeklySummaryMock?limit=5"
mock = get(mock_url)
RESULT["mock_access"] = mock

# 3) Production endpoint: absence of credentials is itself a reproducibility/access constraint.
prod_url = f"{BASE}/data/group/otcmarket/name/weeklySummaryHistoric?limit=5&historicalMonth=2024-Jan"
prod = get(prod_url)
RESULT["production_access"] = prod

# 4) Conservative promotion rule.
meta_ok = meta.get("status_code") == 200
prod_open = prod.get("status_code") == 200
prod_auth_required = prod.get("status_code") in (401, 403)

if meta_ok and prod_open:
    RESULT["status"] = "PROMOTE_TO_HISTORICAL_RESEARCH"
elif meta_ok and prod_auth_required:
    RESULT["status"] = "PROMOTE_TO_RESEARCH_WITH_CREDENTIAL_BLOCK"
elif meta_ok:
    RESULT["status"] = "PROMOTE_WITH_ACCESS_UNCERTAINTY"
else:
    RESULT["status"] = "KILL_FEASIBILITY"

(OUT / "audit.json").write_text(json.dumps(RESULT, indent=2), encoding="utf-8")

rows = [
    {"check": "metadata", **meta},
    {"check": "mock", **mock},
    {"check": "production_no_auth", **prod},
]
(OUT / "endpoint_audit.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

print(json.dumps(RESULT, indent=2))
