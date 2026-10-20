import ast, csv, io, json, os, re, tempfile, zipfile
from collections import defaultdict, Counter
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
OUT = "nueva_estrategia_phase27f_sec_nport"
os.makedirs(OUT, exist_ok=True)
HEADERS = {"User-Agent": "NuevaEstrategia research research@example.com", "Accept-Encoding": "gzip, deflate"}
DATASETS = {
    "2021Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2021q4_nport.zip",
    "2022Q4": "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2022q4_nport.zip",
}

# Phase 27E produced zero matched holdings. This phase is a correction, not an alpha test.
# SEC N-PORT schema: ASSET_CAT=EC is equity-common; issuer title is not a reliable security-type classifier.

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
            if not b:
                break
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
        try:
            return datetime.strptime(x, fmt).date()
        except Exception:
            pass
    return None

def period_snapshot(period):
    path = os.path.join(tempfile.gettempdir(), period + "_nport27f.zip")
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
            if d:
                report_by[a] = d
        if not report_by:
            raise RuntimeError(f"No REPORT_DATE rows in {period}")

        # Use the latest report month present in the quarterly dataset. For each series/report
        # month, the latest filing wins, so NPORT-P/A replaces the prior filing.
        latest = max(report_by.values())
        candidates = defaultdict(list)
        for a, d in report_by.items():
            if d == latest and series_by.get(a):
                candidates[series_by[a]].append(a)

        selected = {}
        for s, accs in candidates.items():
            selected[s] = max(
                accs,
                key=lambda a: parse_date(sub_by[a].get("FILING_DATE", "")) or datetime.min.date(),
            )
        selected_acc = set(selected.values())

        ids_by_hold = defaultdict(list)
        for r in ids:
            ids_by_hold[r.get("HOLDING_ID", "")].append(r)

        rows = []
        diagnostics = Counter()
        filing_dates = []
        for a in selected_acc:
            fd = parse_date(sub_by[a].get("FILING_DATE", ""))
            if fd:
                filing_dates.append(fd)
        signal_date = max(filing_dates) if filing_dates else None

        for h in hold:
            a = h.get("ACCESSION_NUMBER", "")
            if a not in selected_acc:
                continue
            diagnostics["selected_holdings"] += 1

            # Security identity: CUSIP is primary. Ticker is used only as the historical
            # bridge/cross-check into the frozen universe. A holding that maps to >1 universe
            # ticker is conservatively excluded rather than double-counted.
            tickers = set()
            for i in ids_by_hold.get(h.get("HOLDING_ID", ""), []):
                t = norm(i.get("IDENTIFIER_TICKER"))
                if t in UNIVERSE:
                    tickers.add(t)
            if not tickers:
                diagnostics["no_universe_ticker"] += 1
                continue
            if len(tickers) > 1:
                diagnostics["ambiguous_universe_ticker"] += 1
                continue

            # SEC schema uses ASSET_CAT=EC for equity-common. Do not infer security type from
            # free-text ISSUER_TITLE (the Phase 27E bug).
            asset_cat = (h.get("ASSET_CAT") or "").strip().upper()
            if asset_cat != "EC":
                diagnostics["not_equity_common"] += 1
                continue

            payoff = (h.get("PAYOFF_PROFILE") or "").strip().upper()
            if payoff not in ("", "LONG"):
                diagnostics["not_long"] += 1
                continue

            cusip = (h.get("ISSUER_CUSIP") or "").strip().upper()
            if not cusip or cusip in {"N/A", "000000000"}:
                diagnostics["invalid_cusip"] += 1
                continue

            try:
                value = float(h.get("CURRENCY_VALUE") or 0.0)
            except Exception:
                diagnostics["bad_value"] += 1
                continue
            if value < 0:
                diagnostics["negative_value"] += 1
                continue

            ticker = next(iter(tickers))
            rows.append((ticker, series_by[a], value, a, cusip))
            diagnostics["accepted_rows"] += 1

        # Aggregate all historical CUSIPs for the same fund-series/ticker. This avoids choosing
        # a single current CUSIP and therefore avoids a survivorship-prone bridge.
        agg = defaultdict(float)
        for t, s, v, _, _ in rows:
            agg[(t, s)] += v
        by_ticker = defaultdict(float)
        for (t, _), v in agg.items():
            by_ticker[t] += v

        return {
            "period": period,
            "report_date": latest.isoformat(),
            "signal_date": signal_date.isoformat() if signal_date else None,
            "series_selected": len(selected),
            "holding_rows_used": len(rows),
            "ticker_count": len(by_ticker),
            "by_series_ticker": {f"{t}|{s}": v for (t, s), v in agg.items()},
            "by_ticker": dict(by_ticker),
            "diagnostics": dict(diagnostics),
        }
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

def compare(prev, cur):
    a = prev["by_series_ticker"]
    b = cur["by_series_ticker"]
    keys = set(a) | set(b)
    out = []
    for k in keys:
        t = k.split("|", 1)[0]
        pv = a.get(k, 0.0)
        cv = b.get(k, 0.0)
        if pv == 0 and cv == 0:
            continue
        delta = cv - pv
        out.append({
            "ticker": t,
            "series_key": k,
            "prior_value": pv,
            "current_value": cv,
            "delta_value": delta,
            "pct_change": (delta / pv if pv else None),
        })

    by = defaultdict(list)
    for r in out:
        by[r["ticker"]].append(r)

    sig = []
    for t, rs in by.items():
        prior = sum(r["prior_value"] for r in rs)
        current = sum(r["current_value"] for r in rs)
        delta = current - prior
        up = sum(1 for r in rs if r["delta_value"] > 0)
        down = sum(1 for r in rs if r["delta_value"] < 0)
        sig.append({
            "ticker": t,
            "prior_value": prior,
            "current_value": current,
            "delta_value": delta,
            "pct_change": delta / prior if prior else None,
            "fund_breadth_net": up - down,
            "funds_up": up,
            "funds_down": down,
            "funds_observed": len(rs),
        })
    return sorted(sig, key=lambda x: (x["pct_change"] is not None, x["pct_change"] or 0), reverse=True)

def main():
    p1 = period_snapshot("2021Q4")
    p2 = period_snapshot("2022Q4")
    signals = compare(p1, p2)

    payload = {
        "phase": "27F",
        "purpose": "Corrected PIT construction pilot for institutional fund position changes; no production change.",
        "correction_from_27E": "Use SEC ASSET_CAT=EC for common equity; do not infer security type from ISSUER_TITLE. Exclude holdings mapping to multiple frozen-universe tickers instead of requiring exactly one identifier record.",
        "knowledge_rule": "Signal date is the latest filing date among authoritative report-month filings used; any future return test must begin strictly after that date.",
        "amendment_rule": "For each series/report month, latest filing date wins; NPORT-P/A therefore replaces the prior version.",
        "security_rule": "Frozen 335 universe; CUSIP is primary security identity; ticker is only a historical bridge/cross-check. Ambiguous multi-ticker holdings are excluded conservatively.",
        "holding_rule": "ASSET_CAT=EC (equity-common), long/blank payoff profile, valid CUSIP, nonnegative USD value.",
        "periods": [p1, p2],
        "signals": signals,
        "alpha_status": "NOT_TESTED",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(OUT, "phase27f_pilot_2021Q4_2022Q4.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps({
        "phase": "27F",
        "report_dates": [p1["report_date"], p2["report_date"]],
        "signal_date": p2["signal_date"],
        "ticker_count": len(signals),
        "accepted_rows": [p1["diagnostics"].get("accepted_rows", 0), p2["diagnostics"].get("accepted_rows", 0)],
        "status": "COMPLETE",
    }, indent=2))

if __name__ == "__main__":
    main()
