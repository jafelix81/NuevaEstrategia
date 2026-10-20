"""
PHASE 21B — SEC FORM 4 RESEARCH DATASET (OFFICIAL SEC QUARTERLY FILES)

This replaces the per-filing EDGAR crawl used in the first 21B attempt.
The SEC publishes quarterly Insider Transactions Data Sets extracted from
Forms 3/4/5. They are official, reproducible and dramatically faster to
process than hundreds of thousands of individual filing downloads.

POINT-IN-TIME POLICY
--------------------
The quarterly files expose FILING_DATE but not acceptanceDateTime. Therefore
this phase uses a deliberately conservative knowledge date:
    KnowledgeDate = FILING_DATE
and downstream signal construction must use KnowledgeDate < SignalDate
(strictly prior calendar day). Same-day filings are never used. This avoids
lookahead at the cost of discarding information filed on the signal day.

AMENDMENTS
----------
Original Form 4 only (DOCUMENT_TYPE == 4) is the initial research population.
Form 4/A is retained in a separate audit count but is excluded from the
transaction table so an amendment cannot double-count the original. A later
phase may build an amendment-aware point-in-time view using accession-level
acceptance timestamps.

No F80 production change is made here.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

from Nueva_Estrategia_Fase11_Real1000_LTM_v4 import DEFAULT_UNIVERSE

OUTDIR = Path("nueva_estrategia_phase21b_sec_form4_official")
OUTDIR.mkdir(parents=True, exist_ok=True)
DATASET_PAGE = "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
START_DATE = pd.Timestamp("2016-01-01")
END_DATE = pd.Timestamp(datetime.now(timezone.utc).date())
USER_AGENT = "NuevaEstrategia research contact research@example.com"

SUBMISSION_COLS = [
    "ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "DATE_OF_ORIG_SUB",
    "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL", "AFF10B5ONE"
]
OWNER_COLS = ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNERNAME", "RPTOWNER_RELATIONSHIP", "RPTOWNER_TITLE"]
TRANS_COLS = [
    "ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "SECURITY_TITLE", "TRANS_DATE",
    "TRANS_FORM_TYPE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE",
    "TRANS_ACQUIRED_DISP_CD", "DIRECT_INDIRECT_OWNERSHIP", "SHRS_OWND_FOLWNG_TRANS",
    "VALU_OWND_FOLWNG_TRANS", "NATURE_OF_OWNERSHIP"
]


def sec_get(url: str):
    r = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}, timeout=60)
    r.raise_for_status()
    return r


def read_tsv(z: zipfile.ZipFile, member: str, columns: list[str]) -> pd.DataFrame:
    actual = {x.upper(): x for x in z.namelist()}
    key = member.upper()
    if key not in actual:
        raise FileNotFoundError(f"{member} not found in {z.filename}; members={z.namelist()[:20]}")
    with z.open(actual[key]) as fh:
        df = pd.read_csv(fh, sep="\t", dtype=str, low_memory=False)
    df.columns = [str(c).strip().upper() for c in df.columns]
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    return df[columns]


def discover_quarter_urls() -> list[tuple[str, str]]:
    html = sec_get(DATASET_PAGE).text
    hrefs = re.findall(r'href=["\']([^"\']+_form345\.zip)["\']', html, flags=re.I)
    out = {}
    for href in hrefs:
        m = re.search(r'(20\d{2})q([1-4])_form345\.zip', href, flags=re.I)
        if not m:
            continue
        year, q = int(m.group(1)), int(m.group(2))
        label = f"{year}Q{q}"
        if pd.Timestamp(f"{year}-{q*3:02d}-01") < START_DATE - pd.Timedelta(days=120):
            continue
        url = urljoin(DATASET_PAGE, href)
        out[label] = url
    # The current quarter is not necessarily closed. Include all published links.
    return sorted(out.items(), key=lambda x: x[0])


def main():
    started = datetime.now(timezone.utc)
    universe = sorted(set(DEFAULT_UNIVERSE))

    # Current SEC CIK map. CIK is preferred over ticker for historical issuer identity.
    ticker_payload = sec_get(SEC_TICKERS_URL).json()
    sec_map = {}
    for row in ticker_payload.values():
        t = str(row.get("ticker", "")).upper().strip()
        if t:
            sec_map[t] = str(row.get("cik_str", "")).zfill(10)
    universe_ciks = {sec_map[t] for t in universe if t in sec_map}
    mapping_failures = sorted(set(universe) - {t for t in universe if t in sec_map})

    quarters = discover_quarter_urls()
    if not quarters:
        raise RuntimeError("SEC quarterly dataset links could not be discovered")

    all_submissions = []
    all_transactions = []
    all_owners = []
    audit_rows = []

    for label, url in quarters:
        print(f"DOWNLOAD {label} {url}", flush=True)
        blob = sec_get(url).content
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            sub = read_tsv(z, "SUBMISSION.tsv", SUBMISSION_COLS)
            sub["FILING_DATE_PARSED"] = pd.to_datetime(sub["FILING_DATE"], errors="coerce", dayfirst=True)
            sub = sub[sub["FILING_DATE_PARSED"].between(START_DATE, END_DATE, inclusive="both")]
            sub = sub[sub["DOCUMENT_TYPE"].isin(["4", "4/A"])]
            sub = sub[sub["ISSUERCIK"].astype(str).str.zfill(10).isin(universe_ciks)]
            if sub.empty:
                audit_rows.append({"Quarter": label, "SubmissionRowsUniverse": 0, "Form4": 0, "Form4A": 0, "Transactions": 0})
                continue

            owners = read_tsv(z, "REPORTINGOWNER.tsv", OWNER_COLS)
            owners = owners[owners["ACCESSION_NUMBER"].isin(set(sub["ACCESSION_NUMBER"]))]
            trans = read_tsv(z, "NONDERIV_TRANS.tsv", TRANS_COLS)
            trans = trans[trans["ACCESSION_NUMBER"].isin(set(sub["ACCESSION_NUMBER"]))]

            # Only original Form 4 enters the initial research population.
            sub4 = sub[sub["DOCUMENT_TYPE"] == "4"].copy()
            trans4 = trans[trans["ACCESSION_NUMBER"].isin(set(sub4["ACCESSION_NUMBER"]))].copy()
            owners4 = owners[owners["ACCESSION_NUMBER"].isin(set(sub4["ACCESSION_NUMBER"]))].copy()

            all_submissions.append(sub4)
            all_transactions.append(trans4)
            all_owners.append(owners4)
            audit_rows.append({
                "Quarter": label,
                "SubmissionRowsUniverse": int(len(sub)),
                "Form4": int((sub["DOCUMENT_TYPE"] == "4").sum()),
                "Form4A": int((sub["DOCUMENT_TYPE"] == "4/A").sum()),
                "Transactions": int(len(trans4)),
                "Owners": int(len(owners4)),
            })
            print(f"  rows Form4={len(sub4):,} Form4A={int((sub['DOCUMENT_TYPE']=='4/A').sum()):,} trans={len(trans4):,}", flush=True)

    if not all_submissions:
        raise RuntimeError("No Form 4 rows matched the frozen universe")

    sub = pd.concat(all_submissions, ignore_index=True).drop_duplicates("ACCESSION_NUMBER")
    trans = pd.concat(all_transactions, ignore_index=True).drop_duplicates(["ACCESSION_NUMBER", "NONDERIV_TRANS_SK"])
    owners = pd.concat(all_owners, ignore_index=True).drop_duplicates(["ACCESSION_NUMBER", "RPTOWNERCIK"])

    # Join issuer/filing metadata and owner identities. A joint filing can have multiple owners;
    # retaining owner rows is intentional. Downstream signal construction must not silently assign
    # one owner to all transaction rows.
    tx = trans.merge(
        sub[["ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL", "DOCUMENT_TYPE", "AFF10B5ONE"]],
        on="ACCESSION_NUMBER", how="left", validate="many_to_one",
    )
    tx = tx.merge(owners, on="ACCESSION_NUMBER", how="left", validate="many_to_many")
    tx["KnowledgeDate"] = pd.to_datetime(tx["FILING_DATE"], errors="coerce", dayfirst=True)
    tx["TransactionDate"] = pd.to_datetime(tx["TRANS_DATE"], errors="coerce", dayfirst=True)
    tx["Shares"] = pd.to_numeric(tx["TRANS_SHARES"], errors="coerce")
    tx["PricePerShare"] = pd.to_numeric(tx["TRANS_PRICEPERSHARE"], errors="coerce")
    tx["Notional"] = tx["Shares"] * tx["PricePerShare"]
    tx["IsPurchase"] = tx["TRANS_CODE"].eq("P") & tx["TRANS_ACQUIRED_DISP_CD"].eq("A")
    tx["IsSale"] = tx["TRANS_CODE"].eq("S") & tx["TRANS_ACQUIRED_DISP_CD"].eq("D")
    tx["IsOpenMarket"] = tx["TRANS_CODE"].isin(["P", "S"])
    tx["SignedShares"] = tx["Shares"].fillna(0.0)
    tx.loc[tx["IsSale"], "SignedShares"] *= -1
    tx["SignedNotional"] = tx["Notional"].fillna(0.0)
    tx.loc[tx["IsSale"], "SignedNotional"] *= -1
    tx["LagDays"] = (tx["KnowledgeDate"] - tx["TransactionDate"]).dt.days

    keep = [
        "ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL",
        "FILING_DATE", "KnowledgeDate", "PERIOD_OF_REPORT", "DOCUMENT_TYPE", "AFF10B5ONE",
        "RPTOWNERCIK", "RPTOWNERNAME", "RPTOWNER_RELATIONSHIP", "RPTOWNER_TITLE",
        "SECURITY_TITLE", "TransactionDate", "TRANS_FORM_TYPE", "TRANS_CODE", "TRANS_ACQUIRED_DISP_CD",
        "DIRECT_INDIRECT_OWNERSHIP", "Shares", "PricePerShare", "Notional", "SignedShares", "SignedNotional",
        "IsPurchase", "IsSale", "IsOpenMarket", "LagDays", "NATURE_OF_OWNERSHIP"
    ]
    tx[keep].to_csv(OUTDIR / "phase21b_form4_transactions_original_only.csv", index=False)

    filing = sub[["ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL", "DOCUMENT_TYPE", "AFF10B5ONE"]].copy()
    filing["KnowledgeDate"] = pd.to_datetime(filing["FILING_DATE"], errors="coerce", dayfirst=True)
    filing.to_csv(OUTDIR / "phase21b_form4_filing_index_original_only.csv", index=False)

    # Daily issuer aggregates, still based only on original Form 4s.
    agg = tx[tx["IsOpenMarket"]].copy()
    if not agg.empty:
        daily = agg.groupby(["ISSUERCIK", "ISSUERTRADINGSYMBOL", "KnowledgeDate"], dropna=False).agg(
            OpenMarketRows=("ACCESSION_NUMBER", "count"),
            UniqueFilings=("ACCESSION_NUMBER", "nunique"),
            UniqueInsiders=("RPTOWNERCIK", "nunique"),
            PurchaseRows=("IsPurchase", "sum"),
            SaleRows=("IsSale", "sum"),
            GrossPurchaseNotional=("Notional", lambda s: s[agg.loc[s.index, "IsPurchase"]].sum()),
            GrossSaleNotional=("Notional", lambda s: s[agg.loc[s.index, "IsSale"]].sum()),
            NetOpenMarketNotional=("SignedNotional", "sum"),
            NetOpenMarketShares=("SignedShares", "sum"),
            MaxPurchaseNotional=("Notional", lambda s: s[agg.loc[s.index, "IsPurchase"]].max()),
        ).reset_index()
        daily.to_csv(OUTDIR / "phase21b_form4_daily_original_only.csv", index=False)
    else:
        pd.DataFrame().to_csv(OUTDIR / "phase21b_form4_daily_original_only.csv", index=False)

    audit = {
        "phase": "21B",
        "status": "OFFICIAL_SEC_DATASET_READY",
        "source": DATASET_PAGE,
        "dataset_scope": "SEC Insider Transactions Data Sets, Forms 3/4/5",
        "dataset_quarters": [q for q, _ in quarters],
        "research_start": str(START_DATE.date()),
        "research_end": str(END_DATE.date()),
        "universe_size": len(universe),
        "mapped_universe_ciks": len(universe_ciks),
        "mapping_failures": mapping_failures,
        "original_form4_filings": int(len(sub)),
        "original_form4_transaction_rows": int(len(trans)),
        "owner_rows_after_join": int(len(owners)),
        "purchase_rows": int(tx["IsPurchase"].sum()),
        "sale_rows": int(tx["IsSale"].sum()),
        "open_market_rows": int(tx["IsOpenMarket"].sum()),
        "amendment_form4a_excluded": int(sum(x.get("Form4A", 0) for x in audit_rows)),
        "knowledge_date_policy": "FILING_DATE; downstream must require KnowledgeDate < SignalDate",
        "acceptance_datetime_available": False,
        "lookahead_policy": "strict previous-calendar-day cutoff; same-day filings excluded downstream",
        "amendment_policy": "original Form 4 only in initial research; Form 4/A excluded to prevent double counting",
        "joint_owner_policy": "retain owner rows; do not assign one owner to all transactions",
        "quarter_audit": audit_rows,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "next_step": "21C_POINT_IN_TIME_PREDICTABILITY_AND_INCREMENTAL_TEST; compare predefined insider features against frozen LTM/F80 without selecting on final OOS",
    }
    (OUTDIR / "phase21b_sec_official_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
