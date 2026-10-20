import ast, csv, io, json, os, re, tempfile, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
OUT = "nueva_estrategia_phase27d_sec_nport"
os.makedirs(OUT, exist_ok=True)
HEADERS = {"User-Agent": "NuevaEstrategia research research@example.com", "Accept-Encoding": "gzip, deflate"}
DATASETS = {
    "2019Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2019q4_nport.zip",
    "2020Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2020q4_nport.zip",
    "2021Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip",
    "2022Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip",
    "2023Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2023q4_nport.zip",
    "2024Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2024q4_nport.zip",
    "2025Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2025q4_nport.zip",
    "2026Q3": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q3_nport.zip",
}

def extract_universe():
    src = open(BASE_SOURCE, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    value = ast.literal_eval(node.value)
                    return sorted(set(str(x).strip().upper() for x in value))
    raise RuntimeError("DEFAULT_UNIVERSE not found in frozen Phase 0 source")

UNIVERSE = extract_universe()
if len(UNIVERSE) != 335:
    raise RuntimeError(f"Frozen universe expected 335 tickers, got {len(UNIVERSE)}")

def download(url, path):
    req = Request(url, headers=HEADERS, method="GET")
    with urlopen(req, timeout=300) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

def find_member(zf, stem):
    for n in zf.namelist():
        b = os.path.basename(n).lower()
        if b == stem.lower() or b.startswith(stem.lower() + "."):
            return n
    return None

def read_tsv(zf, member):
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        return list(csv.DictReader(text, delimiter="\t"))

def norm_ticker(x):
    return re.sub(r"[^A-Z0-9.\-]", "", (x or "").strip().upper())

def audit_period(period, url):
    path = os.path.join(tempfile.gettempdir(), period + "_nport.zip")
    info = {"period": period, "url": url}
    try:
        download(url, path)
        info["zip_bytes"] = os.path.getsize(path)
        with zipfile.ZipFile(path) as zf:
            subm = find_member(zf, "SUBMISSION")
            hold = find_member(zf, "FUND_REPORTED_HOLDING")
            ids = find_member(zf, "IDENTIFIERS")
            reg = find_member(zf, "REGISTRANT")
            if not all((subm, hold, ids, reg)):
                raise RuntimeError("required N-PORT members missing")
            submissions = read_tsv(zf, subm)
            holdings = read_tsv(zf, hold)
            identifiers = read_tsv(zf, ids)
            registrants = read_tsv(zf, reg)
        sub_by_acc = {r.get("ACCESSION_NUMBER", ""): r for r in submissions}
        ids_by_hold = defaultdict(list)
        for r in identifiers:
            ids_by_hold[r.get("HOLDING_ID", "")].append(r)
        ticker_to_cusips = defaultdict(set)
        cusip_to_tickers = defaultdict(set)
        matched = 0
        for h in holdings:
            acc = h.get("ACCESSION_NUMBER", "")
            if acc not in sub_by_acc:
                continue
            c = (h.get("ISSUER_CUSIP") or "").strip().upper()
            if not c:
                continue
            for ident in ids_by_hold.get(h.get("HOLDING_ID", ""), []):
                t = norm_ticker(ident.get("IDENTIFIER_TICKER"))
                if t in UNIVERSE:
                    ticker_to_cusips[t].add(c)
                    cusip_to_tickers[c].add(t)
                    matched += 1
        covered = sorted(ticker_to_cusips)
        ambiguous = sorted(t for t, cs in ticker_to_cusips.items() if len(cs) > 1)
        shared = sorted(c for c, ts in cusip_to_tickers.items() if len(ts) > 1)
        filing_dates = [r["FILING_DATE"] for r in submissions if r.get("FILING_DATE")]
        report_dates = [r["REPORT_DATE"] for r in submissions if r.get("REPORT_DATE")]
        info.update({
            "submission_rows": len(submissions), "holding_rows": len(holdings),
            "identifier_rows": len(identifiers), "registrant_rows": len(registrants),
            "filing_date_min_raw": min(filing_dates) if filing_dates else "",
            "filing_date_max_raw": max(filing_dates) if filing_dates else "",
            "report_date_min_raw": min(report_dates) if report_dates else "",
            "report_date_max_raw": max(report_dates) if report_dates else "",
            "universe_covered": len(covered),
            "universe_coverage_pct": round(100.0 * len(covered) / len(UNIVERSE), 2),
            "matched_holding_identifier_rows": matched,
            "ambiguous_ticker_count": len(ambiguous),
            "cusip_shared_by_multiple_universe_tickers": len(shared),
            "covered_tickers": covered,
            "ambiguous_tickers": ambiguous,
            "cusip_multi_ticker_examples": shared[:25],
        })
        info["status"] = "PASS" if len(covered) >= 100 and len(ambiguous) <= 50 else "REVIEW"
    except Exception as exc:
        info["status"] = "ERROR"
        info["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try: os.remove(path)
        except OSError: pass
    return info

def main():
    requested = [x.strip() for x in os.getenv("NPORT_PERIODS", "").split(",") if x.strip()]
    periods = requested or list(DATASETS)
    unknown = [p for p in periods if p not in DATASETS]
    if unknown:
        raise RuntimeError(f"Unknown NPORT periods: {unknown}")
    results = []
    for period in periods:
        result = audit_period(period, DATASETS[period])
        results.append(result)
        print(json.dumps({"period": period, "coverage": result.get("universe_coverage_pct"), "ambiguous": result.get("ambiguous_ticker_count"), "status": result.get("status"), "error": result.get("error")}, sort_keys=True))
    payload = {
        "phase": "27D", "source": "SEC Form N-PORT Data Sets",
        "purpose": "Historical PIT coverage of the frozen 335-name universe before alpha testing.",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "universe_size": len(UNIVERSE),
        "mapping_policy": {"ticker_role": "historical bridge/cross-check only", "primary_security_key": "ISSUER_CUSIP", "knowledge_rule": "FILING_DATE is conservative; REPORT_DATE is never used as knowledge date", "amendments": "SUB_TYPE and ACCESSION_NUMBER retained", "survivorship": "frozen 335-name universe; no replacements"},
        "periods": results,
    }
    for result in results:
        with open(os.path.join(OUT, f"phase27d_{result['period']}.json"), "w", encoding="utf-8") as f:
            json.dump(payload | {"period_result": result}, f, indent=2)
    print(json.dumps({"phase": "27D", "periods": periods, "statuses": {r['period']: r.get('status') for r in results}}, indent=2))

if __name__ == "__main__":
    main()
