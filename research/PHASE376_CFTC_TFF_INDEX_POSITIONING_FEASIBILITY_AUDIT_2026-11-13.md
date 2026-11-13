# Phase 376 — CFTC Traders in Financial Futures (TFF) index-positioning feasibility audit

**Date:** 2026-11-13  
**Disposition:** **Promising public macro-positioning source; historical coverage is adequate, but strict historical PIT release timestamps are incomplete. No feature or return test admitted.**  
**Research class:** source/data-feasibility and measurement-design audit only.

## Executive decision

Add CFTC Traders in Financial Futures (TFF), Futures Only, as a **conditional weekly market-regime / positioning candidate**. It is not a stock-specific institutional-flow source and cannot identify individual traders or their investment purpose. It may add a macro positioning/crowding dimension to the existing QQQ Risk ON/OFF and frozen LTM/F80 baseline.

The public TFF Futures Only dataset advertises roughly 47.3k rows and 90 columns, is available through CFTC's public Socrata API, and has history from 2006-06-13. The dataset contains equity-index futures such as E-mini S&P 500, Nasdaq-100 Mini and Russell E-Mini in the 2006 historical records. This is enough to justify a full coverage audit.

**The hard limitation:** CFTC says actual historical release dates are only available for the most recent 13 months. The report date is the Tuesday position snapshot, while the normal release is Friday at 3:30 p.m. ET, with holiday delays. A Tuesday report date is not an availability timestamp. Older backtests cannot be labelled strict PIT until release-date reconstruction is validated. The source is static after publication, which helps revision integrity, but does not solve availability timing.

## 1. Source and historical coverage

Primary dataset:
- Name: TFF - Futures Only
- Socrata dataset ID: gpe5-46if
- API: https://publicreporting.cftc.gov/resource/gpe5-46if.json
- CFTC page snapshot at audit: approximately 47,300 rows, 90 columns; last updated 2026-11-06.
- TFF history: 2006-06-13 onward, per CFTC FAQ.
- Categories: Dealer, Asset Manager, Leveraged Money, Other Reportables and Non-Reportables.

Avoid querying TFF_All (udgc-27he) without a Futures Only / Futures-and-Options-Combined filter: CFTC says the all-data dataset contains both versions and must be filtered to avoid double-counting. TFF Futures-and-Options Combined is a separate view (yw9f-hn96); treat it as a sensitivity source, never add it to Futures Only.

The current CFTC public data view shows historical equity-index futures rows including:
- E-MINI S&P 500, contract market code 13874A;
- NASDAQ-100 STOCK INDEX (MINI), code 209742;
- RUSSELL 2000 STOCK INDEX (MINI), code 239742;
- DOW JONES INDUSTRIAL AVG - x $5, code 124603.

These are provisional contract-code anchors from the public dataset view. Phase 377 must verify each code's complete history, continuity, name changes and exchange mapping rather than assuming names/codes are immutable.

## 2. What the categories do and do not mean

CFTC classifications are based on traders' predominant business purpose self-reported on Form 40 and reviewed for reasonableness. CFTC says it does not know the specific reason for each trader's position. In TFF, a trader's category is consistent across commodities, but that still does not reveal whether a particular position is a hedge, directional speculation, relative-value trade or market-making exposure.

The data are aggregate category totals, not trader identities or account-level holdings. Therefore:
- Leveraged Money is not synonymous with hedge funds possessing superior information.
- Asset Manager is not a verified long-only institutional allocation.
- Dealer is not a clean measure of dealer gamma or net customer exposure.
- Net position changes can reflect Form 40 reclassification, new reportable traders entering, or existing traders leaving—not only trading. CFTC explicitly lists these mechanisms.
- A contract market may disappear from a weekly report when the number of large traders falls below 20, then reappear later. Missing weeks must not be forward-filled as zero.

This source can test positioning/crowding and broad risk-regime hypotheses, not identify specific informed buyers or sellers.

## 3. Availability, publication schedule and revision policy

CFTC documents:
- Positions are as of the preceding Tuesday's close.
- Reports are generally released Friday at 3:30 p.m. Eastern.
- Federal holidays can delay release by one or two days; the official release schedule should be used.
- CFTC states there is no historical list of actual release dates beyond the 13 months of reports published on its website.
- CFTC states historical data is not updated once published.
- The CFTC API is publicly accessible without a token if it is not overused.

### Known exceptional timing

The CFTC's October–November 2025 publication interruption due to a lapse in federal appropriations caused a substantial backlog. The agency published an explicit catch-up schedule with actual new release dates. Those weeks must not be assigned their originally scheduled Friday availability dates.

The current 2026 schedule also illustrates why the Tuesday report date cannot be used as availability: the 2026-11-10 position report is scheduled for publication on **2026-11-16 at 3:30 p.m. ET**, delayed by Veterans Day. The next regular equity-session entry consistent with that publication is 2026-11-17 open, not the Tuesday report date or Friday 2026-11-13 close.

### PIT ruling

- For the most recent 13 months, use CFTC's actual published release schedule/date, then enter no earlier than the next regular equity-session open.
- For the 2025 backlog, use the CFTC special-announcement catch-up dates, not the original Friday dates.
- For older history, the CFTC does not provide a complete actual release-date ledger. A reconstructed calendar can be a conservative schedule proxy for exploratory analysis, but it is **not verified first-receipt PIT**.
- Do not claim strict historical PIT or promote a backtest based solely on the Tuesday report date.
- Begin prospective capture now: save each weekly file/API response, UTC receipt timestamp, SHA-256, dataset/schema metadata and the official publication date. The immutable-after-publication policy is favorable for reproducibility.

## 4. Data structure and accounting controls

CFTC says the dataset has no primary key. Do not treat the Socrata ID column as a guaranteed natural key. Construct and audit a candidate natural key from:
- report date;
- CFTC contract market code;
- market/exchange name and contract market name;
- report type (Futures Only versus Futures-and-Options Combined).

Check duplicate keys, contract-code/name changes, missing weeks, category-field completeness and OI consistency.

For directional net-position features:
- category net = Long_All - Short_All;
- normalize by Open_Interest_All;
- do not add Spread_All to directional net; analyze spreading separately;
- retain open interest, trader counts and category coverage as quality fields;
- do not forward-fill missing markets or silently splice Futures Only and Combined.

CFTC notes that spread positions must be included when reconciling gross long/short open interest. In Futures-and-Options Combined files, totals can differ from open interest by +/-1 due to option delta calculations. This is another reason to keep Futures Only as the primary initial series.

## 5. Candidate use and falsifiable hypotheses

**Intended role:** broad equity-market regime / crowding context for the existing stock strategy, not stock selection.

Primary candidate (to be frozen before data inspection):
- E-mini S&P 500 Leveraged Money net-position share of open interest, and its four-week change, standardized using only a rolling historical window available at the signal date.

Secondary robustness, not a search for the best-performing contract:
- Nasdaq-100 Mini and Russell E-Mini versions;
- Asset Manager versus Leveraged Money net-position divergence;
- Dealer net-position share and spreading share as separate diagnostics.

Competing hypotheses:
1. **Trend-following / return-chasing:** Leveraged Money positioning changes mostly follow prior index returns; the apparent signal disappears after controlling for prior 1/4/12-week returns.
2. **Crowding / contrarian risk:** extreme net positioning predicts weaker subsequent index returns or higher drawdown risk after controlling for prior returns and volatility.
3. **Regime confirmation:** positioning adds incremental information to QQQ Risk ON/OFF and frozen LTM/F80, improving downside control without merely reducing exposure after losses.
4. **No incremental information:** COT features are redundant with momentum, volatility and QQQ risk state; archive the hypothesis if this is the result.

Use the first verified tradable session after publication for entry. Evaluate multiple horizons without imposing a minimum or maximum holding period, but preregister a small grid (e.g. 5/20/60 sessions) before any return analysis. The primary comparison is incremental value versus QQQ Risk ON/OFF and frozen LTM/F80 at identical exposure and costs. Control for prior index returns, realized volatility, trend, rates and major macro-event regimes. Use chronological validation, date-block bootstrap, contract/year LOO and the locked final holdout.

## 6. Data-feasibility gates for Phase 377

1. Download the full TFF Futures Only dataset and reconcile row count, schema, data range and Socrata metadata.
2. Measure weekly coverage and gaps for the four candidate equity-index futures codes; verify code/name/exchange continuity and reappearances.
3. Test the natural key for duplicates and conflicting records; verify category/OI arithmetic and missing-value semantics.
4. Measure availability of Dealer, Asset Manager, Leveraged Money and Other Reportables fields over time; do not assume all fields are complete back to 2006.
5. Build an actual release-date calendar for the latest 13 months and the 2025 backlog; test a conservative historical schedule reconstruction separately and label it unverified.
6. Capture one current release prospectively with immutable bytes/hash and first-receipt timestamp.
7. Only after the above gates pass, freeze one primary feature definition and begin exploratory predictive tests. No final holdout access during source feasibility.

## Decision

**Conditional candidate — advance to a public-data coverage/PIT audit, not to alpha testing.** TFF offers long, free, weekly, broad index-futures positioning data and no post-publication historical revisions. Its category labels are imperfect proxies, its market coverage is thresholded, and actual release dates are incomplete beyond 13 months. It is useful as a potential macro regime feature, not as evidence of stock-specific institutional information.

No data was purchased, no vendor contacted, no feature computed, no returns tested, no holdout used and no production changes made. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official sources reviewed 2026-11-13

- CFTC COT descriptions, methodology, FAQs and API access: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC About the COT Reports: https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm
- CFTC TFF Futures Only dataset: https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if
- CFTC TFF All dataset (contains Futures Only and Combined; filter before use): https://publicreporting.cftc.gov/Commitments-of-Traders/TFF_All/udgc-27he
- CFTC release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC historical special announcements / 2025 publication interruption: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm
- CFTC release resumption and catch-up schedule, 2025-11-18: https://www.cftc.gov/PressRoom/PressReleases/9138-25
