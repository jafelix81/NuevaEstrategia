import json
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

SEC_PAGE = "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets"
DATA_URLS = {
    "2019Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip",
    "2020Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip",
    "2022Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip",
    "2024Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip",
    "2026Q3": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip",
}
HEADERS = {"User-Agent": "NuevaEstrategia research contact research@example.com", "Accept-Encoding": "gzip, deflate"}


def get(url):
    req = Request(url, headers=HEADERS, method="GET")
    with urlopen(req, timeout=30) as r:
        body = r.read(12000)
        return {"status": r.status, "content_type": r.headers.get("Content-Type"), "content_length": r.headers.get("Content-Length"), "sample_bytes": len(body), "sample": body[:200].decode("utf-8", "replace")}


def main():
    out = {
        "phase": "27A",
        "source": "SEC Form N-PORT Data Sets",
        "hypothesis": "Monthly portfolio holdings of registered funds/ETFs may provide incremental institutional ownership/position-change information versus frozen LTM/F80.",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "official_page": SEC_PAGE,
        "coverage_claim": "October 2019 through September 2026; quarterly datasets; monthly portfolio holdings.",
        "checks": {},
        "decision": None,
    }
    try:
        out["checks"]["official_page"] = get(SEC_PAGE)
    except Exception as e:
        out["checks"]["official_page"] = {"error": repr(e)}
    for period, url in DATA_URLS.items():
        try:
            out["checks"][period] = get(url)
        except Exception as e:
            out["checks"][period] = {"error": repr(e)}
    # This phase deliberately does not download the 228MB-691MB ZIPs.
    # It verifies discoverability/HTTP reachability and records the official coverage.
    ok = [k for k, v in out["checks"].items() if k != "official_page" and isinstance(v, dict) and v.get("status") in (200, 206)]
    out["historical_samples_reachable"] = ok
    out["decision"] = "PROMOTE_TO_SCHEMA_AND_POINT_IN_TIME_AUDIT" if len(ok) >= 3 else "HOLD_FOR_ACCESS_REVIEW"
    with open("phase27a_sec_nport_feasibility.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
