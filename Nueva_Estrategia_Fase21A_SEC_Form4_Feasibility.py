"""
PHASE 21A — SEC FORM 4 FEASIBILITY / POINT-IN-TIME AUDIT

Purpose
-------
Audit whether SEC insider Form 4 filings can become a reproducible Smart Money
source for the frozen stock universe. This phase does NOT trade on insiders and
makes no production change.

Critical timing rule
--------------------
A filing is considered available only at its EDGAR acceptance timestamp. Filing
Date alone is not sufficient. Future filings must never be visible to a signal.

Outputs
-------
- source audit JSON
- per-ticker coverage CSV
- sample Form 4 transaction XML/HTML retrieval diagnostics

The frozen Phase 11 DEFAULT_UNIVERSE is used so this feasibility test is tied to
our existing research universe rather than a newly selected survivorship-biased
universe.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUTDIR = Path("nueva_estrategia_phase21a_sec_form4_feasibility")
OUTDIR.mkdir(parents=True, exist_ok=True)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}/{primary_doc}"

USER_AGENT = "NuevaEstrategia research contact research@example.com"
TIMEOUT = 30
SLEEP = 0.12


def get(url: str):
    r = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r


def main():
    started = datetime.now(timezone.utc).isoformat()
    universe = sorted(set(DEFAULT_UNIVERSE))
    print(f"PHASE 21A — SEC FORM 4 FEASIBILITY | universe={len(universe)}")

    ticker_payload = get(SEC_TICKERS_URL).json()
    sec_map = {}
    for row in ticker_payload.values():
        ticker = str(row.get("ticker", "")).upper().strip()
        if ticker:
            sec_map[ticker] = {
                "cik": str(row.get("cik_str", "")).zfill(10),
                "title": row.get("title", ""),
            }

    rows = []
    sample_candidates = []
    failures = []

    for i, ticker in enumerate(universe, 1):
        meta = sec_map.get(ticker)
        if not meta:
            rows.append({"Ticker": ticker, "Mapped": False, "Form4Count": 0, "OldestAcceptance": None, "NewestAcceptance": None, "Error": "no SEC ticker mapping"})
            continue
        try:
            payload = get(SEC_SUBMISSIONS.format(cik=meta["cik"])).json()
            recent = payload.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            filing_dates = recent.get("filingDate", [])
            acceptance = recent.get("acceptanceDateTime", [])
            primary_docs = recent.get("primaryDocument", [])
            report_dates = recent.get("reportDate", [])

            idxs = [j for j, f in enumerate(forms) if f == "4"]
            acc_times = [acceptance[j] for j in idxs if acceptance[j]]
            row = {
                "Ticker": ticker,
                "Mapped": True,
                "CIK": meta["cik"],
                "Company": meta["title"],
                "Form4CountRecent": len(idxs),
                "OldestAcceptance": min(acc_times) if acc_times else None,
                "NewestAcceptance": max(acc_times) if acc_times else None,
                "Error": None,
            }
            rows.append(row)

            for j in idxs[:3]:
                sample_candidates.append({
                    "Ticker": ticker,
                    "CIK": meta["cik"],
                    "accession": accessions[j],
                    "filingDate": filing_dates[j],
                    "acceptanceDateTime": acceptance[j],
                    "reportDate": report_dates[j] if j < len(report_dates) else None,
                    "primaryDocument": primary_docs[j],
                })
        except Exception as exc:
            failures.append({"Ticker": ticker, "Error": repr(exc)})
            rows.append({"Ticker": ticker, "Mapped": True, "CIK": meta["cik"], "Company": meta["title"], "Form4CountRecent": 0, "OldestAcceptance": None, "NewestAcceptance": None, "Error": repr(exc)})
        if i % 25 == 0 or i == len(universe):
            print(f"SEC submissions {i}/{len(universe)} | failures={len(failures)}")
        time.sleep(SLEEP)

    df = pd.DataFrame(rows)
    df.to_csv(OUTDIR / "phase21a_sec_form4_coverage.csv", index=False)

    sample_df = pd.DataFrame(sample_candidates[:20])
    sample_df.to_csv(OUTDIR / "phase21a_sec_form4_samples.csv", index=False)

    sample_fetch = []
    for _, r in sample_df.head(5).iterrows():
        try:
            cik_int = int(r["CIK"])
            accession_no_dashes = str(r["accession"]).replace("-", "")
            url = SEC_ARCHIVE.format(cik_int=cik_int, accession_no_dashes=accession_no_dashes, primary_doc=r["primaryDocument"])
            resp = get(url)
            sample_fetch.append({"Ticker": r["Ticker"], "URL": url, "HTTP": resp.status_code, "Bytes": len(resp.content)})
        except Exception as exc:
            sample_fetch.append({"Ticker": r.get("Ticker"), "URL": None, "HTTP": None, "Bytes": 0, "Error": repr(exc)})
        time.sleep(SLEEP)
    pd.DataFrame(sample_fetch).to_csv(OUTDIR / "phase21a_sec_form4_sample_fetch.csv", index=False)

    mapped = int(df["Mapped"].sum()) if not df.empty else 0
    with_form4 = int((df.get("Form4CountRecent", pd.Series(dtype=float)) > 0).sum())
    audit = {
        "Phase": "21A",
        "Status": "FEASIBILITY_COMPLETE",
        "StartedUTC": started,
        "CompletedUTC": datetime.now(timezone.utc).isoformat(),
        "Universe": len(universe),
        "SEC_TickerMapped": mapped,
        "SEC_TickerMappingCoverage": mapped / len(universe) if universe else 0.0,
        "UniverseWithRecentForm4": with_form4,
        "RecentForm4Coverage": with_form4 / mapped if mapped else 0.0,
        "FailedSubmissions": len(failures),
        "PointInTimeRule": "acceptanceDateTime <= signal timestamp",
        "PrimarySource": "SEC EDGAR data.sec.gov + sec.gov Archives",
        "Conclusion": "PROMOTE_TO_FORM4_RESEARCH" if mapped / len(universe) >= 0.80 and with_form4 / mapped >= 0.80 else "REQUIRES_FURTHER_MAPPING_OR_DATA_AUDIT",
    }
    (OUTDIR / "phase21a_sec_form4_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if failures:
        pd.DataFrame(failures).to_csv(OUTDIR / "phase21a_sec_form4_failures.csv", index=False)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
