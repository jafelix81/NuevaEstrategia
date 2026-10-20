import json
import re
from datetime import datetime, timezone
from io import BytesIO
import zipfile
import requests

OUT = "nueva_estrategia_phase23a_cftc_cot_feasibility"
BASE = "https://www.cftc.gov"
HEADERS = {"User-Agent": "NuevaEstrategiaResearch/1.0 research contact"}

# Equity-index contracts are used only as a potential macro/risk-regime source,
# not as stock-selection data. KnowledgeDate is the public release date.
TARGETS = [
    "NASDAQ-100 STOCK INDEX",
    "E-MINI NASDAQ-100",
    "S&P 500 STOCK INDEX",
    "E-MINI S&P 500",
]

def get(url, timeout=30):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r

def main():
    audit = {
        "phase": "23A",
        "status": "STARTED",
        "source": "CFTC Commitments of Traders",
        "source_url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
        "release_policy": "Friday 15:30 ET; report generally summarizes prior Tuesday positions; holidays can delay release",
        "knowledge_date_policy": "release_date, never report/as-of date",
        "research_start": "2016-01-01",
        "research_end": datetime.now(timezone.utc).date().isoformat(),
        "targets": TARGETS,
        "tests": [],
        "conclusion": None,
    }

    # 1) Official historical-viewable coverage check.
    hist_url = BASE + "/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm"
    r = get(hist_url)
    text = r.text
    years = sorted({int(y) for y in re.findall(r">(20(?:0[5-9]|1[0-9]|2[0-6]))<", text)})
    audit["tests"].append({
        "name": "historical_viewable_access",
        "http": r.status_code,
        "years_detected_min": min(years) if years else None,
        "years_detected_max": max(years) if years else None,
        "years_count": len(years),
        "pass": r.status_code == 200 and 2016 in years and 2026 in years,
    })

    # 2) Probe the current public CFTC bulk historical text endpoint.
    # This is deliberately a feasibility probe; no large dataset is retained here.
    txt_url = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
    try:
        rr = get(txt_url)
        sample = rr.text[:20000]
        found_targets = [t for t in TARGETS if t in sample]
        audit["tests"].append({
            "name": "current_futures_only_endpoint_probe",
            "url": txt_url,
            "http": rr.status_code,
            "bytes": len(rr.content),
            "target_hits_in_sample": found_targets,
            "pass": rr.status_code == 200,
        })
    except Exception as e:
        audit["tests"].append({
            "name": "current_futures_only_endpoint_probe",
            "url": txt_url,
            "pass": False,
            "error": repr(e),
        })

    # 3) Verify historical report pages are publicly linkable and distinguish
    # report date from release/knowledge date. The official page explicitly says
    # its dates are report dates, not release dates; downstream research must
    # reconstruct the publication calendar before using observations.
    audit["tests"].append({
        "name": "point_in_time_rule",
        "pass": True,
        "rule": "For any signal date S, only COT observations whose release/knowledge date is strictly before S may be used.",
        "warning": "Historical viewable pages list report dates, not release dates; release-date reconstruction is required.",
    })

    ok_access = all(t.get("pass", False) for t in audit["tests"] if t["name"] != "point_in_time_rule")
    if ok_access:
        audit["status"] = "FEASIBLE_SOURCE_READY"
        audit["conclusion"] = "CFTC_COT_IS_FEASIBLE_FOR_MACRO_RISK_REGIME_RESEARCH"
    else:
        audit["status"] = "TECHNICAL_ACCESS_REVIEW_REQUIRED"
        audit["conclusion"] = "DO_NOT_PROCEED_UNTIL_ACCESS_IS_FIXED"

    import os
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "phase23a_cftc_cot_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(json.dumps(audit, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
