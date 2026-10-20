import ast, csv, io, json, os, re, tempfile, zipfile
from collections import defaultdict, Counter
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
OUT = "nueva_estrategia_phase27g_sec_nport"
HEADERS = {"User-Agent": "NuevaEstrategia research research@example.com", "Accept-Encoding": "gzip, deflate"}
DATASETS = {
    "2021Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip",
    "2022Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip",
}

# 27G is a methodological correction only. 27F compared different fund-series panels and
# therefore interpreted absent series as 100% position exits. That is not valid. This phase
# compares only series present in BOTH snapshots. Missing ticker holdings within a common series
# are valid zeros (an actual exit); a missing fund-series is never treated as zero.

def universe():
    tree = ast.parse(open(BASE_SOURCE, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DEFAULT_UNIVERSE":
                    u = sorted(set(str(x).strip().upper() for x in ast.literal_eval(node.value)))
                    if len(u) != 335:
                        raise RuntimeError(f"Expected frozen 335 universe, got {len(u)}")
                    return set(u)
    raise RuntimeError("DEFAULT_UNIVERSE not found")

UNIVERSE = universe()

def download(url, path):
    with urlopen(Request(url, headers=HEADERS), timeout=300) as r, open(path, "wb") as f:
        while True:
            b = r.read(1024 * 1024)
            if not b: break
            f.write(b)

def member(z, stem):
    for n in z.namelist():
        b = os.path.basename(n).lower()
        if b == stem.lower() or b.startswith(stem.lower() + "."):
            return n
    raise RuntimeError(f"Missing {stem}")

def read_tsv(z, m):
    with z.open(m) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), delimiter="\t"))

def norm(x):
    return re.sub(r"[^A-Z0-9.\-]", "", (x or "").strip().upper())

def parse_date(x):
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try: return datetime.strptime(x, fmt).date()
        except Exception: pass
    return None

def period_snapshot(period):
    path = os.path.join(tempfile.gettempdir(), period + "_nport27g.zip")
    download(DATASETS[period], path)
    try:
        with zipfile.ZipFile(path) as z:
            sub = read_tsv(z, member(z, "SUBMISSION"))
            info = read_tsv(z, member(z, "FUND_REPORTED_INFO"))
            hold = read_tsv(z, member(z, "FUND_REPORTED_HOLDING"))
            ids = read_tsv(z, member(z, "IDENTIFIERS"))

        sub_by = {r.get("ACCESSION_NUMBER", ""): r for r in sub}
        series_by = {r.get("ACCESSION_NUMBER", ""): r.get("SERIES_ID", "") for r in info}
        report_by = {}
        for a, r in sub_by.items():
            d = parse_date(r.get("REPORT_DATE", ""))
            if d: report_by[a] = d
        if not report_by: raise RuntimeError(f"No REPORT_DATE rows in {period}")

        latest = max(report_by.values())
        candidates = defaultdict(list)
        for a, d in report_by.items():
            if d == latest and series_by.get(a): candidates[series_by[a]].append(a)
        selected = {
            s: max(accs, key=lambda a: parse_date(sub_by[a].get("FILING_DATE", "")) or datetime.min.date())
            for s, accs in candidates.items()
        }
        selected_acc = set(selected.values())
        ids_by_hold = defaultdict(list)
        for r in ids: ids_by_hold[r.get("HOLDING_ID", "")].append(r)

        rows, diagnostics = [], Counter()
        filing_dates = []
        for a in selected_acc:
            fd = parse_date(sub_by[a].get("FILING_DATE", ""))
            if fd: filing_dates.append(fd)
        signal_date = max(filing_dates) if filing_dates else None

        for h in hold:
            a = h.get("ACCESSION_NUMBER", "")
            if a not in selected_acc: continue
            diagnostics["selected_holdings"] += 1
            tickers = set()
            for i in ids_by_hold.get(h.get("HOLDING_ID", ""), []):
                t = norm(i.get("IDENTIFIER_TICKER"))
                if t in UNIVERSE: tickers.add(t)
            if not tickers:
                diagnostics["no_universe_ticker"] += 1; continue
            if len(tickers) > 1:
                diagnostics["ambiguous_universe_ticker"] += 1; continue
            if (h.get("ASSET_CAT") or "").strip().upper() != "EC":
                diagnostics["not_equity_common"] += 1; continue
            if (h.get("PAYOFF_PROFILE") or "").strip().upper() not in ("", "LONG"):
                diagnostics["not_long"] += 1; continue
            cusip = (h.get("ISSUER_CUSIP") or "").strip().upper()
            if not cusip or cusip in {"N/A", "000000000"}:
                diagnostics["invalid_cusip"] += 1; continue
            try: value = float(h.get("CURRENCY_VALUE") or 0.0)
            except Exception:
                diagnostics["bad_value"] += 1; continue
            if value < 0:
                diagnostics["negative_value"] += 1; continue
            ticker = next(iter(tickers))
            rows.append((ticker, series_by[a], value, cusip))
            diagnostics["accepted_rows"] += 1

        agg = defaultdict(float)
        for t, s, v, _ in rows: agg[(t, s)] += v
        by_ticker = defaultdict(float)
        for (t, _), v in agg.items(): by_ticker[t] += v
        return {
            "period": period, "report_date": latest.isoformat(),
            "signal_date": signal_date.isoformat() if signal_date else None,
            "series_selected": len(selected), "series_ids": sorted(selected),
            "holding_rows_used": len(rows), "ticker_count": len(by_ticker),
            "by_series_ticker": {f"{t}|{s}": v for (t, s), v in agg.items()},
            "by_ticker": dict(by_ticker), "diagnostics": dict(diagnostics),
        }
    finally:
        try: os.remove(path)
        except OSError: pass

def compare(prev, cur):
    prev_series, cur_series = set(prev["series_ids"]), set(cur["series_ids"])
    common = sorted(prev_series & cur_series)
    a, b = prev["by_series_ticker"], cur["by_series_ticker"]
    prev_common = {k: v for k, v in a.items() if k.rsplit("|", 1)[1] in common}
    cur_common = {k: v for k, v in b.items() if k.rsplit("|", 1)[1] in common}
    tickers = sorted({k.split("|", 1)[0] for k in prev_common} | {k.split("|", 1)[0] for k in cur_common})
    sig = []
    for t in tickers:
        rows = []
        for s in common:
            k = f"{t}|{s}"
            pv, cv = prev_common.get(k, 0.0), cur_common.get(k, 0.0)
            if pv == 0.0 and cv == 0.0: continue
            rows.append((pv, cv))
        if not rows: continue
        prior, current = sum(x for x, _ in rows), sum(y for _, y in rows)
        up = sum(1 for x, y in rows if y > x)
        down = sum(1 for x, y in rows if y < x)
        sig.append({
            "ticker": t, "prior_value": prior, "current_value": current,
            "delta_value": current-prior,
            "pct_change": (current-prior)/prior if prior else None,
            "fund_breadth_net": up-down, "funds_up": up, "funds_down": down,
            "funds_observed": len(rows),
        })
    return common, sorted(sig, key=lambda x: (x["pct_change"] is not None, x["pct_change"] or 0), reverse=True)

def main():
    os.makedirs(OUT, exist_ok=True)
    p1, p2 = period_snapshot("2021Q4"), period_snapshot("2022Q4")
    common, signals = compare(p1, p2)
    payload = {
        "phase": "27G",
        "purpose": "Series-panel correction to 27F; no alpha test and no production change.",
        "why_27F_invalid": "27F compared different fund-series panels and treated absent series as zero holdings, creating false -100% exits.",
        "panel_rule": "Compare only fund series present in both report-month snapshots. Missing ticker within a common series is a valid zero; missing series is excluded from delta calculations.",
        "knowledge_rule": "Signal date is the latest authoritative filing date used; any future return test must begin strictly after that date.",
        "amendment_rule": "Latest filing wins for each series/report month.",
        "security_rule": "Frozen 335 universe; CUSIP primary, historical ticker bridge only; ambiguous multi-ticker holdings excluded.",
        "holding_rule": "ASSET_CAT=EC, long/blank payoff profile, valid CUSIP, nonnegative USD value.",
        "periods": [p1, p2],
        "common_series_count": len(common), "common_series": common,
        "signals": signals, "alpha_status": "NOT_TESTED",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(OUT, "phase27g_series_panel_correction_2021Q4_2022Q4.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps({
        "phase": "27G", "report_dates": [p1["report_date"], p2["report_date"]],
        "common_series_count": len(common), "signal_tickers": len(signals),
        "accepted_rows": [p1["diagnostics"].get("accepted_rows", 0), p2["diagnostics"].get("accepted_rows", 0)],
        "status": "COMPLETE", "alpha_status": "NOT_TESTED"
    }, indent=2))

if __name__ == "__main__": main()
