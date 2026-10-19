"""
PHASE 21B — SEC FORM 4 TRANSACTION EXTRACTION / POINT-IN-TIME RESEARCH

Purpose
-------
Turn SEC Form 4 filings into an auditable transaction-level dataset for the
frozen universe. This phase is diagnostic only: it does NOT modify F80.

Design principles
-----------------
* Availability is EDGAR acceptanceDateTime, never filingDate alone.
* Historical submissions files are used when recent submissions metadata no
  longer contains the filing.
* Only filings in the research window are retrieved.
* Form 4 transaction codes are preserved; no assumption that every Form 4 is
  an informed open-market trade.
* Direct and indirect ownership are retained separately.
* Open-market purchases/sales (P/S) are separated from other codes.
* The output contains daily issuer-level aggregates and insider-level data.
* No future filing may enter a signal date.

The first research window is 2016-01-01 through the current date, matching the
long-history objective while remaining within a practical GitHub Actions job.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUTDIR = Path("nueva_estrategia_phase21b_sec_form4_research")
OUTDIR.mkdir(parents=True, exist_ok=True)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
SEC_SUBMISSION_FILE = "https://www.sec.gov/Archives/edgar/data/{cik}/{name}"

# Keep the SEC request rate conservative.
REQUEST_SLEEP = 0.16
TIMEOUT = 30
START_DATE = pd.Timestamp("2016-01-01", tz="UTC")

OPEN_MARKET_CODES = {"P", "S"}
PURCHASE_CODES = {"P"}
SALE_CODES = {"S"}
EXERCISE_CODES = {"M"}
OTHER_CODES = {"A", "D", "F", "G", "I", "J", "K", "U", "V", "W", "X", "C"}


def get(session: requests.Session, url: str):
    time.sleep(REQUEST_SLEEP)
    r = session.get(
        url,
        headers={
            "User-Agent": "NuevaEstrategia research contact research@example.com",
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r


def norm_date(value):
    if not value:
        return None
    try:
        ts = pd.to_datetime(value, utc=True)
        return ts
    except Exception:
        return None


def strip_ns(tag):
    return tag.rsplit("}", 1)[-1]


def first_text(node, names):
    wanted = set(names)
    for child in node.iter():
        if strip_ns(child.tag) in wanted and child.text is not None:
            return child.text.strip()
    return None


def child_text(node, name):
    for child in node.iter():
        if strip_ns(child.tag) == name and child.text is not None:
            return child.text.strip()
    return None


def parse_float(v):
    if v in (None, "", "--"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return None


def parse_form4_xml(content: bytes, meta, accession, acceptance, filing_date, report_date, primary_doc):
    try:
        root = ET.fromstring(content)
    except Exception:
        return []

    issuer_cik = child_text(root, "issuerCik") or meta["cik"]
    issuer_symbol = child_text(root, "issuerTradingSymbol") or meta["ticker"]
    rows = []

    # ownerRelationship contains the reporting person's role; preserve what is
    # available without hard-coding a definition of "insider quality".
    owner_nodes = [n for n in root.iter() if strip_ns(n.tag) == "reportingOwner"]
    owner_map = {}
    for owner in owner_nodes:
        oid = child_text(owner, "rptOwnerCik") or child_text(owner, "rptOwnerName") or str(len(owner_map))
        owner_map[oid] = {
            "InsiderCIK": child_text(owner, "rptOwnerCik"),
            "InsiderName": child_text(owner, "rptOwnerName"),
            "Director": child_text(owner, "isDirector"),
            "Officer": child_text(owner, "isOfficer"),
            "TenPercentOwner": child_text(owner, "isTenPercentOwner"),
            "Other": child_text(owner, "isOther"),
            "OfficerTitle": child_text(owner, "officerTitle"),
        }

    # Each nonDerivativeTransaction is one economic transaction row.
    for section_name, security_tag in [("nonDerivativeTransaction", "nonDerivativeSecurity"), ("derivativeTransaction", "derivativeSecurity")]:
        for node in [n for n in root.iter() if strip_ns(n.tag) == section_name]:
            code = None
            for child in node.iter():
                if strip_ns(child.tag) == "transactionCode":
                    code = child.text.strip() if child.text else None
                    break
            if not code:
                continue
            shares = parse_float(first_text(node, ["transactionShares", "shares"]))
            price = parse_float(first_text(node, ["transactionPricePerShare", "transactionPricePerShare"]))
            acquired = first_text(node, ["transactionAcquiredDisposedCode"])
            ownership = first_text(node, ["directOrIndirectOwnership"])
            transaction_date = first_text(node, ["transactionDate"])
            footnote_ids = []
            for child in node.iter():
                if strip_ns(child.tag) == "footnoteId" and child.text:
                    footnote_ids.append(child.text.strip())

            # The same Form 4 may report several owners; transaction rows do
            # not always carry a unique owner id. Use the first reporting owner
            # as the filing-level owner, and retain the raw accession for audit.
            owner = next(iter(owner_map.values()), {})
            rows.append({
                "Ticker": issuer_symbol,
                "IssuerCIK": issuer_cik,
                "InsiderCIK": owner.get("InsiderCIK"),
                "InsiderName": owner.get("InsiderName"),
                "Director": owner.get("Director"),
                "Officer": owner.get("Officer"),
                "TenPercentOwner": owner.get("TenPercentOwner"),
                "Other": owner.get("Other"),
                "OfficerTitle": owner.get("OfficerTitle"),
                "Accession": accession,
                "AcceptanceDateTime": acceptance,
                "FilingDate": filing_date,
                "ReportDate": report_date,
                "TransactionDate": transaction_date,
                "TransactionCode": code,
                "AcquiredDisposed": acquired,
                "Ownership": ownership,
                "Shares": shares,
                "PricePerShare": price,
                "Notional": (shares * price) if shares is not None and price is not None else None,
                "SecurityType": section_name,
                "PrimaryDocument": primary_doc,
                "FootnoteCount": len(footnote_ids),
            })
    return rows


def candidate_xml_urls(session, cik, acc, primary_doc):
    # Prefer the declared primary document first; if it is HTML/XSL, query the
    # filing index and discover XML files.
    base = SEC_ARCHIVE.format(cik=str(int(cik)), acc=acc.replace("-", ""), doc=primary_doc)
    urls = [base]
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/index.json"
    try:
        payload = get(session, index_url).json()
        for item in payload.get("directory", {}).get("item", []):
            name = str(item.get("name", ""))
            if name.lower().endswith(".xml") and name not in {primary_doc}:
                urls.append(SEC_ARCHIVE.format(cik=str(int(cik)), acc=acc.replace("-", ""), doc=quote(name)))
    except Exception:
        pass
    return urls[:6]


def collect_submission_metadata(session, meta):
    payload = get(session, SEC_SUBMISSIONS.format(cik=meta["cik"])).json()
    records = []
    recent = payload.get("filings", {}).get("recent", {})
    for j, form in enumerate(recent.get("form", [])):
        if form != "4":
            continue
        acceptance = norm_date(recent.get("acceptanceDateTime", [None])[j])
        if acceptance is None or acceptance < START_DATE:
            continue
        records.append({
            "ticker": meta["ticker"], "cik": meta["cik"],
            "accession": recent["accessionNumber"][j],
            "filingDate": recent["filingDate"][j],
            "acceptance": acceptance.isoformat(),
            "reportDate": recent.get("reportDate", [None])[j],
            "primaryDocument": recent["primaryDocument"][j],
        })

    for old in payload.get("filings", {}).get("files", []):
        frm = norm_date(old.get("filingFrom"))
        to = norm_date(old.get("filingTo"))
        if to is not None and to < START_DATE:
            continue
        name = old.get("name")
        if not name:
            continue
        url = f"https://data.sec.gov/submissions/{name}"
        try:
            old_payload = get(session, url).json()
            forms = old_payload.get("form", [])
            for j, form in enumerate(forms):
                if form != "4":
                    continue
                acceptance = norm_date(old_payload.get("acceptanceDateTime", [None])[j])
                if acceptance is None or acceptance < START_DATE:
                    continue
                records.append({
                    "ticker": meta["ticker"], "cik": meta["cik"],
                    "accession": old_payload["accessionNumber"][j],
                    "filingDate": old_payload["filingDate"][j],
                    "acceptance": acceptance.isoformat(),
                    "reportDate": old_payload.get("reportDate", [None])[j],
                    "primaryDocument": old_payload["primaryDocument"][j],
                })
        except Exception:
            continue
    return records


def main():
    started = datetime.now(timezone.utc).isoformat()
    universe = sorted(set(DEFAULT_UNIVERSE))
    session = requests.Session()
    ticker_payload = get(session, SEC_TICKERS_URL).json()
    sec_map = {}
    for row in ticker_payload.values():
        ticker = str(row.get("ticker", "")).upper().strip()
        if ticker:
            sec_map[ticker] = {"cik": str(row.get("cik_str", "")).zfill(10), "title": row.get("title", "")}

    all_meta = []
    mapping_failures = []
    for ticker in universe:
        if ticker in sec_map:
            all_meta.append({"ticker": ticker, "cik": sec_map[ticker]["cik"], "title": sec_map[ticker]["title"]})
        else:
            mapping_failures.append(ticker)

    filings = []
    submission_failures = []
    for i, meta in enumerate(all_meta, 1):
        try:
            filings.extend(collect_submission_metadata(session, meta))
        except Exception as exc:
            submission_failures.append({"Ticker": meta["ticker"], "Error": repr(exc)})
        if i % 25 == 0 or i == len(all_meta):
            print(f"SEC metadata {i}/{len(all_meta)} | filings={len(filings)} | failures={len(submission_failures)}")

    filings_df = pd.DataFrame(filings).drop_duplicates(subset=["ticker", "accession"])
    filings_df.to_csv(OUTDIR / "phase21b_form4_filing_index.csv", index=False)

    transactions = []
    fetch_failures = []
    # Limit to one retrieval per accession and retain a complete filing index even
    # if individual XML retrieval fails.
    for i, r in filings_df.iterrows():
        try:
            cik = str(r["cik"]).zfill(10)
            acc = str(r["accession"])
            urls = candidate_xml_urls(session, cik, acc, r["primaryDocument"])
            parsed = []
            for url in urls:
                try:
                    resp = get(session, url)
                    parsed = parse_form4_xml(resp.content, {"cik": cik, "ticker": r["ticker"]}, acc, r["acceptance"], r["filingDate"], r["reportDate"], r["primaryDocument"])
                    if parsed:
                        break
                except Exception:
                    continue
            if parsed:
                transactions.extend(parsed)
            else:
                fetch_failures.append({"Ticker": r["ticker"], "Accession": acc, "Reason": "no parseable Form4 XML", "PrimaryDocument": r["primaryDocument"]})
        except Exception as exc:
            fetch_failures.append({"Ticker": r["ticker"], "Accession": r["accession"], "Reason": repr(exc), "PrimaryDocument": r["primaryDocument"]})
        if (i + 1) % 100 == 0 or i + 1 == len(filings_df):
            print(f"Form4 retrieval {i + 1}/{len(filings_df)} | transactions={len(transactions)} | failures={len(fetch_failures)}")

    tx = pd.DataFrame(transactions)
    if not tx.empty:
        tx["AcceptanceDateTime"] = pd.to_datetime(tx["AcceptanceDateTime"], utc=True)
        tx["TransactionDate"] = pd.to_datetime(tx["TransactionDate"], errors="coerce")
        tx["IsOpenMarket"] = tx["TransactionCode"].isin(OPEN_MARKET_CODES)
        tx["IsPurchase"] = tx["TransactionCode"].isin(PURCHASE_CODES) & tx["AcquiredDisposed"].eq("A")
        tx["IsSale"] = tx["TransactionCode"].isin(SALE_CODES) & tx["AcquiredDisposed"].eq("D")
        tx["IsExercise"] = tx["TransactionCode"].isin(EXERCISE_CODES)
        tx["SignedShares"] = tx["Shares"].fillna(0.0)
        tx.loc[tx["IsSale"], "SignedShares"] *= -1
        tx["SignedNotional"] = tx["Notional"].fillna(0.0)
        tx.loc[tx["IsSale"], "SignedNotional"] *= -1
        tx["AcceptanceDate"] = tx["AcceptanceDateTime"].dt.floor("D")
        tx = tx.sort_values(["AcceptanceDateTime", "Ticker", "InsiderName"])

    tx.to_csv(OUTDIR / "phase21b_form4_transactions.csv", index=False)

    if not tx.empty:
        daily = tx.groupby(["Ticker", "AcceptanceDate"], dropna=False).agg(
            Form4Rows=("Accession", "count"),
            UniqueFilings=("Accession", "nunique"),
            UniqueInsiders=("InsiderName", "nunique"),
            PurchaseRows=("IsPurchase", "sum"),
            SaleRows=("IsSale", "sum"),
            ExerciseRows=("IsExercise", "sum"),
            OpenMarketRows=("IsOpenMarket", "sum"),
            PurchaseShares=("SignedShares", lambda s: s[s > 0].sum()),
            NetOpenMarketShares=("SignedShares", lambda s: s[tx.loc[s.index, "IsOpenMarket"]].sum()),
            NetOpenMarketNotional=("SignedNotional", lambda s: s[tx.loc[s.index, "IsOpenMarket"]].sum()),
            PurchaseNotional=("Notional", lambda s: s[tx.loc[s.index, "IsPurchase"]].sum()),
            SaleNotional=("Notional", lambda s: s[tx.loc[s.index, "IsSale"]].sum()),
        ).reset_index()
        daily.to_csv(OUTDIR / "phase21b_form4_daily_aggregates.csv", index=False)
    else:
        daily = pd.DataFrame()

    # Concentration / clustering diagnostics are intentionally descriptive.
    if not tx.empty:
        insider = tx.groupby(["Ticker", "InsiderName", "AcceptanceDate"], dropna=False).agg(
            Rows=("Accession", "count"),
            PurchaseRows=("IsPurchase", "sum"),
            SaleRows=("IsSale", "sum"),
            NetShares=("SignedShares", "sum"),
            NetNotional=("SignedNotional", "sum"),
            MaxPurchaseNotional=("Notional", lambda s: s[tx.loc[s.index, "IsPurchase"]].max() if (tx.loc[s.index, "IsPurchase"]).any() else 0.0),
        ).reset_index()
        insider.to_csv(OUTDIR / "phase21b_form4_insider_daily.csv", index=False)
    else:
        insider = pd.DataFrame()

    audit = {
        "Phase": "21B",
        "Status": "RESEARCH_DATASET_BUILT",
        "StartedUTC": started,
        "CompletedUTC": datetime.now(timezone.utc).isoformat(),
        "Universe": len(universe),
        "MappedTickers": len(all_meta),
        "MappingFailures": len(mapping_failures),
        "SubmissionFailures": len(submission_failures),
        "Form4FilingsIndexed": int(len(filings_df)),
        "ParsedTransactionRows": int(len(tx)),
        "RetrievalFailures": int(len(fetch_failures)),
        "ResearchStartDate": str(START_DATE.date()),
        "PointInTimeRule": "AcceptanceDateTime <= signal timestamp",
        "OpenMarketCodes": sorted(OPEN_MARKET_CODES),
        "PurchaseDefinition": "transactionCode=P and acquiredDisposed=A",
        "SaleDefinition": "transactionCode=S and acquiredDisposed=D",
        "ProductionChange": False,
        "NextStep": "POINT_IN_TIME_PREDICTABILITY_AND_INCREMENTAL_TEST",
    }
    (OUTDIR / "phase21b_sec_form4_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if mapping_failures:
        pd.DataFrame({"Ticker": mapping_failures}).to_csv(OUTDIR / "phase21b_mapping_failures.csv", index=False)
    if submission_failures:
        pd.DataFrame(submission_failures).to_csv(OUTDIR / "phase21b_submission_failures.csv", index=False)
    if fetch_failures:
        pd.DataFrame(fetch_failures).to_csv(OUTDIR / "phase21b_fetch_failures.csv", index=False)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
