# Phase 649 — Russell outcome-source rights and daily-history feasibility audit

**Audit cutoff:** 2026-11-26 20:20 UTC  
**Base main HEAD:** `b4d57f524c6ecd79e18c23cbec1bd853a619e047`  
**Disposition:** **NO DAILY RUSSELL PRICE + VOLATILITY PAIR IS CURRENTLY CLEARED FOR THE PHASE 646 OUTCOME STUDY UNDER THE EXISTING USD 0 / NO-VENDOR-CONTACT AUTHORIZATION.** FRED-hosted CBOE series and direct Cboe website content are not admitted for software/strategy development without the required rights. IWM is a plausible investable Russell 2000 proxy, but a reproducible daily total-return history was not established from the official issuer page in this audit.

## 1. Research question and boundary

Phase 646/647/648 established a Russell E-mini CFTC feature and a reproducible offline construction pipeline. The next blocked step is a frozen outcome/control source for:
- Russell 2000 proxy OHLC total-return path;
- a small-cap options-volatility control (preferably RVX) or a separately preregistered broad-market volatility control;
- exact daily session alignment and immutable source/retrieval provenance.

This phase is a source-contract, rights and coverage audit only. It does not download price observations, inspect forward outcomes, change Phase 646, or test returns.

## 2. Source findings

### 2.1 FRED RVXCLS / VIXCLS — technically accessible, rights gate fails

FRED's `RVXCLS` series is the Cboe Russell 2000 Volatility Index, daily close, with observed history beginning 2004-01-02 and a current series page showing observations through 2026-11-24. Its notes explicitly identify Cboe as source and state: “Copyright, 2016, Chicago Board Options Exchange, Inc. Reprinted with permission.”

FRED's terms state that copyrighted third-party series require permission from the data owner for use beyond personal use. FRED's legal notice also prohibits using FRED Services or FRED Content in connection with development or training of software programs/systems or machine learning. This project is an automated strategy-research/software workflow; the FRED route is therefore **not admitted** absent explicit rights clearance from the data owner and any required FRED permission.

The same restriction applies to `VIXCLS`; switching from RVX to VIX does not solve the rights problem.

Sources:
- FRED RVXCLS: https://fred.stlouisfed.org/series/RVXCLS
- FRED API terms / property rights: https://fred.stlouisfed.org/docs/api/terms_of_use.html
- FRED legal / prohibited use and copyrighted series: https://fred.stlouisfed.org/legal/

### 2.2 Direct Cboe historical index CSV — technically accessible, prior approval required

Cboe's historical-data page provides daily VIX closing-value downloads from 1990 to present and several other volatility-index histories. The listed historical index downloads on that page do **not** include RVX. The page also says the historical data are provided for site visitors' convenience and without an accuracy guarantee.

Cboe's separate Use of Content page states that prior approval is required to use any Cboe website data/content and that approval is not effective until a license agreement is signed. Cboe's Global Indices Feed / DataShop material describes subscription/custom-pricing access for index data and historical files.

Therefore:
- VIX daily history is a technical candidate, not a cleared input to this strategy project.
- It is not a direct replacement for Russell-specific RVX.
- No permission request, quote, vendor contact, account, sample, or purchase was made.

Sources:
- Cboe VIX historical data: https://www.cboe.com/tradable-products/vix/vix-historical-data
- Cboe Use of Content: https://www.cboe.com/use-of-content
- Cboe Global Indices Feed / licensing: https://www.cboe.com/data/global-indices-feed

### 2.3 IWM — credible investable proxy, daily historical file not established

The official iShares page identifies IWM as an ETF tracking the Russell 2000 Index and gives its inception date as 2000-05-22. It reports NAV/price information and a quarterly distribution schedule. This makes IWM a defensible *investable proxy candidate* for small-cap market exposure, but not identical to the Russell 2000 index.

The public page exposes performance summaries and distribution records, but the accessible page did not provide a reproducible full daily OHLC/NAV total-return file. The page's “Download Excel” request timed out in this audit. Because IWM distributes cash quarterly, a price-only close series would understate total return across ex-dates. A future source must preserve raw OHLC, distribution ex-dates/amounts, split adjustments, retrieval time, revisions and hashes, and must not double-adjust dividends.

No IWM price data were downloaded or used.

Source:
- iShares IWM product page: https://www.ishares.com/us/products/239710/ishares-russell-2000-etf-iwm-us-class

### 2.4 Licensed index history

FTSE Russell/LSEG advertises end-of-day and historical index data packages across FTSE Russell index families. This is a technically appropriate direct-index route, but it is a subscription/licensing route, not a no-cost source established under current authorization.

Source:
- LSEG FTSE Russell index data: https://www.lseg.com/en/ftse-russell/index-resources/indices-subscribe-data

## 3. Decision matrix

| Candidate | History / relevance | PIT and adjustment evidence | Rights under current authorization | Decision |
|---|---|---|---|---|
| FRED RVXCLS | Daily Russell volatility close; history from 2004 | FRED real-time/vintage semantics are date-only and series is subject to revision; exact intraday release not established | Cboe-copyrighted; FRED software-development restriction applies | **Reject for this project absent written clearance** |
| FRED VIXCLS | Long daily broad-market volatility history | Date-only vintage does not establish same-day intraday availability | Same Cboe/FRED restrictions | **Reject for this project absent written clearance** |
| Cboe VIX historical CSV | Daily VIX close from 1990 | Daily close; historical page disclaims accuracy; no exact intraday receipt ledger | Cboe website content requires prior approval/license | **Not admitted** |
| IWM official issuer page | ETF inception 2000-05-22; tracks Russell 2000; quarterly distributions | Full daily total-return file and retrieval/revision contract not established | No data-use clearance for an automated research artifact established here | **Proxy candidate only; not admitted** |
| LSEG/FTSE Russell EOD | Direct index-family historical/EOD packages | Product-level scope; detailed vintage/revision contract not audited | Subscription/license route; no quote/contact authorized | **Parked** |

**Conclusion:** the Phase 646 outcome-source gate remains open. No provider is silently substituted, and no price source is frozen.

## 4. Impact on Phase 646 / CFTC Russell

- The fixed-reference feature pipeline from Phase 648 remains valid as an offline feature-construction control.
- Prospective Russell observations remain exactly two: 2026-11-10 and 2026-11-17.
- Both remain below the preregistered 80th-percentile crowding threshold (40.625% and 45.4167%).
- The 52 matured-training / 150 evaluation sample gates remain unmet.
- No forward price outcomes were accessed.
- No drawdown, semivariance, return, volatility, MAE, bootstrap, HAC, LOO or OOS result was produced.
- Do not relax the Phase 646 sample gates or substitute a broad-market VIX series for RVX after seeing outcomes. Any alternative control must be declared before outcome inspection.

## 5. Broader Smart Money source disposition

This audit does not elevate or demote an “institutional” interpretation. It only closes two tempting free volatility-data routes on rights grounds and leaves IWM as an unverified proxy candidate.

Existing independent source gates remain:
- SEC Form 4: descriptive owner/transaction enrichment only; no signal-eligible matches.
- SEC 13F: first-seen capture is running, but current baseline observations have no lower-bound interval; holdings were not downloaded.
- SEC Form 144: descriptive proposed-sale / plan context only; no signal eligibility.
- FINRA T1 ATS: publication clock and revision-stable panel exist, but effective-dated identity and total-return history are unresolved.
- FINRA Reg SHO / consolidated short interest: prior completeness and identity gates remain unresolved; no new eligible first-seen observation in the latest daily capture.
- SEC MIDAS: retain as a separate exchange-market-structure hypothesis, not a dark-pool/institutional-identity measure; its open Draft PR #201 has not been merged.
- Cboe OPRA / Open-Close and Massive options: remain conditional on history, PIT/correction clocks, exact-universe coverage and explicit license terms. No options data have been purchased or requested.

## 6. Actions / repository preflight

- Main HEAD at cutoff: `b4d57f524c6ecd79e18c23cbec1bd853a619e047`.
- Actions inventory: 8,354 total runs; latest 100: 70 success, 18 failure, 12 cancelled; zero queued or in-progress.
- PR #246 (Phase 648) is merged. Final run [45883866597](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597) passed 10/10 offline tests; artifact [15148442172](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883866597/artifacts/15148442172) was downloaded and inspected. It reproduces the two prospective Russell feature rows; both are non-high and `signals_admitted=0`.
- Open Draft source branches were reviewed; no stacked research PR was merged. Relevant open drafts include #200 (Cboe OPRA), #201 (SEC MIDAS), #188 (Massive options), #159 (FINRA short interest), #50/#61 (FINRA T1) and #57 (price-provider fallback).
- Latest scheduled SEC runs remain Form 4 [45848689364], 13F [45839454376] and Form 144 [45827105431]. Their jobs succeeded and artifacts remain unexpired.
- Form 4 log: 10 owner rows appended in the bounded enrichment batch; descriptive crosswalk contains 12 rows, with 0 signal-eligible matches, 2 unresolved acceptance-clock rows and 7 multi-owner accessions quarantined. The new duplicate audit contains two observations, both prior-watermark rows and neither an exact duplicate.
- 13F log: 29 new accessions were recorded as initial baseline observations; 0 metadata/research/signal-eligible observations; no holdings downloaded.
- Form 144 log/state: 53 feed observations, 825 structured accessions, 5,495 detail rows and 178 structured-detail backfill accessions remaining; 0 signal eligibility.
- CFTC scheduled capture [45753716471] reported no new reports/revisions; 3,043 total records and 0 signal-eligible historical rows.
- FINRA Reg SHO daily first-seen capture [45754121648] recorded 0 first-seen/eligible events and persisted no raw market data.
- Form 4's next scheduled slot at 20:17 UTC was not visible by the 20:20 UTC cutoff. This is an observed schedule-delivery gap, not proof that the workflow is disabled. No manual dispatch, rerun, or duplicate poll was made. Form 144 and 13F's next scheduled slots had not yet occurred at cutoff.

## 7. Controls and next gate

- Do not use FRED RVX/VIX or Cboe website data in the strategy pipeline absent explicit written rights.
- Do not contact a vendor, request a quote, create an account/trial, or buy data under the current authorization.
- Keep IWM as a candidate only until a lawful daily OHLC/total-return history, distribution adjustment method, retrieval contract and revision policy are demonstrated.
- Continue prospective CFTC collection without backdating; do not inspect price outcomes until the source is frozen.
- Continue SEC natural captures and bounded backfills; keep owner/acceptance/line attribution uncertainty visible.
- F80 and the legacy holdout remain untouched.

**Frozen strategy:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged. No incremental alpha, OOS, bootstrap or LOO evidence has been established. No universe, parameter, cost, exposure, capital, holding-period or production change was made. Options-data budget remains USD 0.
