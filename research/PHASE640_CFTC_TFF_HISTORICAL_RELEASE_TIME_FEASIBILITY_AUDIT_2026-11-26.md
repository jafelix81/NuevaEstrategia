# Phase 640 — CFTC TFF historical release-time feasibility audit

**Audit cutoff:** 2026-11-26 11:01 UTC  
**Base:** `main` at `3d13c44e2267b73df3266f5a3e842e2a2fb11cdc`  
**Disposition:** historical CFTC TFF report dates cannot be promoted to point-in-time publication timestamps from the normal Friday schedule. Retain historical archive rows as non-PIT proxies; continue prospective first-seen capture. No signal or model change.

## 1. Question

Can the 3,035-row CFTC TFF historical archive be assigned defensible historical knowledge timestamps by mapping each Tuesday report date to the usual Friday 3:30 p.m. ET publication time?

**Answer: no, not across the full archive.** The CFTC confirms the usual schedule, but also confirms that it does not maintain a public list of historical release dates beyond the most recent 13 months. Its own historical special-announcement page documents multi-week publication disruptions and catch-up releases. A routine Tuesday-to-Friday imputation would therefore create material look-ahead in known periods and cannot be certified for unlisted periods.

Official references:
- CFTC COT Release Schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC COT FAQ / report methodology: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC Historical Special Announcements: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm
- CFTC About the COT Reports: https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/cot_about.html

## 2. Normal schedule is not a complete historical PIT clock

The CFTC says COT reports are generally released Friday at 3:30 p.m. Eastern using positions from the immediately preceding Tuesday. The official release schedule is explicitly tentative; federal holidays may delay publication by one or two days.

The CFTC FAQ also states:
- There is no public list of historical release dates.
- Only release dates for the latest 13 months of reports are available on the Commission website.
- TFF historical data itself reaches back to June 13, 2006.

The position archive therefore has much longer coverage than the public release-date archive. A Tuesday report date is a position snapshot date, not an observed publication timestamp.

## 3. Direct evidence: 2025 lapse in appropriations

The CFTC's December 9, 2025 special announcement says COT processing/publication was interrupted from October 1 through November 12, 2025. The Commission then released reports in chronological catch-up order.

| Report date | Original publish date | Actual new publish date | Calendar days late |
|---|---|---|---:|
| 2025-09-30 | 2025-10-03 | 2025-11-19 | 47 |
| 2025-10-07 | 2025-10-10 | 2025-11-21 | 42 |
| 2025-10-14 | 2025-10-17 | 2025-11-25 | 39 |
| 2025-10-21 | 2025-10-24 | 2025-12-02 | 39 |
| 2025-10-28 | 2025-10-31 | 2025-12-05 | 35 |
| 2025-11-04 | 2025-11-07 | 2025-12-09 | 32 |
| 2025-11-10 | 2025-11-14 | 2025-12-10 | 26 |
| 2025-11-18 | 2025-11-21 | 2025-12-12 | 21 |
| 2025-11-25 | 2025-12-01 | 2025-12-15 | 14 |
| 2025-12-02 | 2025-12-05 | 2025-12-17 | 12 |
| 2025-12-09 | 2025-12-12 | 2025-12-19 | 7 |
| 2025-12-16 | 2025-12-19 | 2025-12-23 | 4 |
| 2025-12-23 | 2025-12-29 | 2025-12-29 | 0 |

The first report in this table would be backdated by 47 calendar days if a researcher assigned the normal scheduled Friday as its availability date. This is not a marginal clock discrepancy.

Other documented exceptions within the TFF archive period include:
- **2023 ION cyber incident:** reports scheduled for February 3 and subsequent weeks were delayed; the February 3 report was not issued until February 24, followed by a sequence of catch-up releases. Some affected contract-market values were adjusted to provide the best estimate.
- **2025-01-09 National Day of Mourning:** the weekly report was released Monday, January 13.
- **2018 and 2019 federal shutdowns:** CFTC announcements state that publication was suspended during shutdown periods.
- **2015-07-03:** a premature and incomplete COT release was corrected with a complete report on July 6.

These exceptions demonstrate that schedule-based release imputation is not safe as a full-history PIT reconstruction. The special-announcement page is an exception log, not a complete timestamp archive.

## 4. Reconciliation to the repository's CFTC inventory

Phase 637 previously reconciled the repository's 3,043 rows:

| Component | Rows | Current disposition |
|---|---:|---|
| Historical archive | 3,035 | `UNVERIFIED_ARCHIVE_PROXY`; signal-ineligible |
| Prospective first-seen batches | 8 | Research-observation eligible; signal-ineligible |
| **Total** | **3,043** | Not 3,043 historical PIT observations |

The eight prospective observations are four index-futures contracts across only two report dates (2026-11-10 and 2026-11-17). They are two time clusters, not eight independent weekly samples. Their first-seen times are conservative upper bounds from the collector, not exact CFTC publication timestamps.

The latest prospective poll [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) found no new report or revision. The archive CSV remains blob `4711abbaeeb6107d1cb8f50a7c2e3627373b6d29`; its rows remain excluded from PIT model training and validation.

## 5. "Smart money" interpretation is not warranted by category labels

CFTC documentation says positions are supplied by reporting firms and trader categories are based on the predominant business purpose self-reported by traders on Form 40, subject to staff review. The Commission does not know the specific reasons for each trader's positions, and individual trader classifications are not published.

Therefore:
- Asset Manager/Institutional is not a verified label for informed or superior investors.
- Leveraged Funds is not a verified hedge-fund-alpha label.
- Dealer/Intermediary positions can reflect intermediation and client facilitation, not directional conviction.
- Week-to-week category changes can reflect new or departing traders and reclassification, not only trading activity.

Treat category net positioning as hypotheses about aggregate market regime, not as ground truth for "smart money".

## 6. Research disposition and prospective design

**Historical backfill: do not promote.** Keep all 3,035 archive rows marked `UNVERIFIED_ARCHIVE_PROXY`. Do not assign Tuesday+3-day timestamps, use the archive-derived 4-report change or 52-report z-score to initialize prospective features, or include these rows in chronological OOS.

**Prospective stream: continue.** Use the actual first-seen upper bound from successful polling as the conservative knowledge clock. For a daily equity model, make the feature available only after the first regular XNYS session strictly following that upper bound. Retain report date, poll start/end, response receipt, raw-source hash, row hash and revision status separately.

A later study may preregister:
- net positions scaled by open interest for Dealer, Asset Manager and Leveraged Money;
- changes across four consecutive observed report dates;
- leveraged-money versus asset-manager divergence;
- a 52-report rolling statistic only after a full 52-report prospective history exists.

Do not treat the four index futures as independent observations. The economic test must be a market-regime overlay compared against frozen F80 at identical exposure and costs, with chronological splits, time-block bootstrap and time-block LOO. Two report-date clusters are insufficient to run any predictive test.

## 7. Decision

CFTC TFF remains a **conditional prospective broad-market regime covariate**, not a stock-level institutional-flow signal. Historical coverage is long, but complete historical release-time coverage is not. Prospective first-seen accumulation is the only currently defensible path to a PIT series.

No alpha, event study, OOS, bootstrap or LOO result was generated. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, exposure, costs, capital, holdout or holding-period policy changed. Options-data budget remains USD 0.
