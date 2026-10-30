# Phase 42B — SEC MIDAS PIT release audit

Date: 2026-10-30

## Objective
Determine whether SEC MIDAS Metrics by Individual Security can be assigned a conservative point-in-time knowledge date before any incremental alpha test versus frozen LTM/F80.

## Fresh official verification
The SEC Metrics by Individual Security page currently states coverage from January 2012 through June 2026, more than 4,800 securities, daily security-level fields including Cancels, Trades, LitTrades, OddLots, Hidden, TradesForHidden, OrderVol, TradeVol, LitVol, OddLotVol, HiddenVol and TradeVolForHidden, and quarterly ZIP downloads from 2012 Q1 through 2026 Q2. The current SEC page was last reviewed or updated June 30, 2026. The SEC Data Library also lists Metrics by Individual Security as a public Market Activity Data Asset last updated June 2026.

The Data.gov catalog currently exposes 58 quarterly resources (2012 Q1 through 2026 Q2) and confirms the dataset is public. Its catalog metadata says it was inventoried December 16, 2021, but its generic `modified` field is October 30, 2017 even though later quarterly resources are now listed. Therefore the catalog metadata cannot be used as a per-file historical publication timestamp.

## New PIT evidence / lag audit
The live SEC index still does not expose a first-publication timestamp for each quarterly ZIP. We therefore do NOT treat quarter-end observation dates as information dates.

There is, however, independent SEC documentation showing that the public MIDAS market-activity series has historically been distributed on a quarterly update cycle: a March 3, 2021 SEC data highlight states that the next scheduled quarterly data-series update was expected in mid-February, and SEC statements describe quarterly publication of MIDAS-derived market activity data. This supports the existence of a non-zero post-quarter publication lag, but it does NOT establish an exact lag for every Metrics by Individual Security ZIP.

Methodological consequence: a conservative lag convention may be used only as a sensitivity framework, not as proof of PIT availability. The minimum acceptable exploratory framework is to test at least 2-, 3-, and 4-month knowledge lags, applied identically to every quarter, and require conclusions to survive the full lag range. A shorter lag must not be selected because it improves returns.

This does not yet pass the strict PIT gate for production-quality alpha because the actual first-availability date of each file remains unobserved. A stronger pass would still require archived SEC index snapshots or another timestamped official publication record.

## Research design if the PIT gate passes
Prefer hidden-volume and trade-to-order features initially. Treat odd-lot variables separately because of the SEC's November 3, 2025 round-lot definition change. Treat pre/post May 1, 2017 NYSE feed changes as separate regimes or include explicit controls.

Candidate daily features:
- HiddenVol / TradeVol
- Hidden / Trades
- Trades / OrderVol
- Cancels / OrderVol
- TradesForHidden / Trades

The first statistical test must be incremental information versus the frozen LTM/F80 signal, using chronological train/validation/OOS splits, identical exposure and costs, and no future revisions. Any evidence consistent with return-chasing must be explicitly separated from predictive content.

## Gate status
PIT release timing: NOT PROVEN.
Historical data feasibility: PASS at the source/catalog level.
Conservative lag framework: CANDIDATE ONLY (2/3/4-month sensitivity); not a substitute for a verified publication timestamp.
Alpha authorization: FALSE.
Baseline modification: FORBIDDEN.

## Official sources
SEC, Metrics by Individual Security:
https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security

SEC, Market Activity Report Methodology:
https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology

SEC, 2014-01 Data Highlight (quarterly update cadence reference):
https://www.sec.gov/about/odd-lot-rates-post-transparency-world-2014-01-market-structure

Data.gov, Metrics by Individual Security:
https://catalog.data.gov/dataset/metrics-by-individual-security
