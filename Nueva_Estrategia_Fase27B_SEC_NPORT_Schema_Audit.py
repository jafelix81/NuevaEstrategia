import csv
import io
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen

HEADERS = {"User-Agent": "NuevaEstrategia research contact research@example.com", "Accept-Encoding": "gzip, deflate"}
DATASETS = {
    "2019Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip",
    "2026Q3": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip",
}
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
OUT = "nueva_estrategia_phase27b_sec_nport"


def download(url, path):
    req = Request(url, headers=HEADERS, method="GET")
    with urlopen(req, timeout=180) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def get_json(url):
    req = Request(url, headers=HEADERS, method="GET")
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def sample_member(zf, name, n=5):
    with zf.open(name) as raw:
        data = raw.read(200000)
    text = data.decode("utf-8-sig", "replace")
    rows = list(csv.reader(io.StringIO(text)))
    return rows[:n]


def main():
    os.makedirs(OUT, exist_ok=True)
    audit = {
        "phase": "27B",
        "source": "SEC Form N-PORT Data Sets",
        "purpose": "Schema, identifier, coverage and point-in-time feasibility audit before any alpha test.",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
        "current_sec_ticker_mapping": None,
        "decision": None,
    }
    try:
        mapping = get_json(SEC_TICKERS)
        audit["current_sec_ticker_mapping"] = {"status": "OK", "records": len(mapping)}
    except Exception as e:
        audit["current_sec_ticker_mapping"] = {"status": "ERROR", "error": repr(e)}

    for period, url in DATASETS.items():
        path = os.path.join(tempfile.gettempdir(), f"{period}_nport.zip")
        download(url, path)
        info = {"url": url, "local_bytes": os.path.getsize(path)}
        with zipfile.ZipFile(path) as zf:
            members = zf.infolist()
            info["member_count"] = len(members)
            info["members"] = [{"name": x.filename, "compressed": x.compress_size, "uncompressed": x.file_size} for x in members[:200]]
            candidates = [x.filename for x in members if x.filename.lower().endswith(('.csv', '.txt'))]
            keyword_candidates = [x for x in candidates if any(k in x.lower() for k in ('investment','holding','nport','submission','general','portfolio','security'))]
            info["candidate_count"] = len(keyword_candidates)
            samples = {}
            for name in keyword_candidates[:30]:
                try:
                    samples[name] = sample_member(zf, name)
                except Exception as e:
                    samples[name] = {"error": repr(e)}
            info["samples"] = samples
            metadata = [x.filename for x in members if x.filename.lower().endswith('.json') and 'metadata' in x.filename.lower()]
            info["metadata_members"] = metadata
            if metadata:
                try:
                    with zf.open(metadata[0]) as raw:
                        meta = json.loads(raw.read().decode('utf-8-sig'))
                    info["metadata_sample"] = meta if isinstance(meta, dict) else str(meta)[:5000]
                except Exception as e:
                    info["metadata_error"] = repr(e)
        audit["datasets"][period] = info
        try:
            os.remove(path)
        except OSError:
            pass

    usable = 0
    for period, info in audit["datasets"].items():
        names = ' '.join(x['name'].lower() for x in info.get('members', []))
        if info.get('member_count', 0) > 0 and any(k in names for k in ('investment','holding')):
            usable += 1
    audit["decision"] = "PROMOTE_TO_PIT_ISSUER_MAPPING" if usable == len(DATASETS) else "HOLD_FOR_SCHEMA_REVIEW"
    with open(os.path.join(OUT, "phase27b_sec_nport_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(json.dumps({"phase": "27B", "decision": audit["decision"], "datasets": {k: {"bytes": v.get("local_bytes"), "members": v.get("member_count"), "candidates": v.get("candidate_count")} for k,v in audit["datasets"].items()}}, indent=2))


if __name__ == "__main__":
    main()
