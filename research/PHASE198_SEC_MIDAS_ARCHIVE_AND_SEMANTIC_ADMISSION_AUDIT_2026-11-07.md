# Phase 198 — SEC MIDAS archive inventory, disputed-quarter reconciliation and semantic admission

**Audit date:** 2026-11-07  
**Disposition:** archive-index and asset-reachability audit only; **strict PIT and alpha remain NOT ADMITTED**.  
**Scope:** SEC's current public Metrics by Individual Security page, the six quarters claimed missing by a third-party data catalog, and official SEC methodology/FAQ. The hosted workflow fetches the page and reads only four bytes from each of six disputed ZIP URLs; it does not download full quarterly archives.

## 1. Why this phase was necessary

The prior MIDAS work established a long public history and identified publication-time as the decisive PIT gate. A third-party dataset description now claims six quarters are absent at source: 2014 Q2, all four quarters of 2016, and 2019 Q4. That claim conflicts with the SEC's own current archive index, which lists every quarter from 2012 Q1 through 2026 Q2.

This phase resolves the archive-index discrepancy without assuming that a listed ZIP is complete or that its rows were available on the observation date.

## 2. Current official archive inventory

The SEC's Metrics by Individual Security page currently states January 2012–June 2026, more than 4,800 securities, daily security-level fields, and quarterly ZIP downloads from 2012 Q1 through 2026 Q2. The index contains **58 consecutive quarter labels**. The separate Metrics by Individual Security and Exchange page also advertises 2012 Q1–2026 Q2 and lists 58 quarterly downloads.

The six disputed quarters are:
- 2014 Q2
- 2016 Q1, Q2, Q3 and Q4
- 2019 Q4

The hosted Phase 198 workflow parses the official SEC HTML, verifies the 58-quarter sequence and issues a Range bytes=0-3 request for each disputed ZIP. A valid ZIP signature confirms that a public ZIP asset is reachable; it does **not** establish that the archive contains complete daily observations, that the rows are non-empty, or that the third-party parser was correct. Full-file content reconciliation is a separate gate.

## 3. Important semantic correction: public MIDAS metrics are not off-exchange flow

The SEC's MIDAS platform itself processes exchange order/quote feeds and off-exchange trade executions. However, the public individual-security market-activity metrics are computed from exchange-feed activity during continuous trading. The SEC's FAQ says these measures generally exclude off-exchange volume, opening/closing auctions and off-hours activity.

Consequently:
- HiddenVol is not dark-pool volume. It is volume identified as trading against hidden orders on exchanges where the SEC can determine that classification.
- TradeVolForHidden is a restricted denominator. Exchanges without sufficient information to determine hidden executions are excluded; the SEC specifically names NYSE, Amex, CHX and NSX in its FAQ.
- The files do not identify a beneficial owner, fund, institutional participant, buyer/seller aggressor or opening/closing position.
- MIDAS public metrics are daily **on-exchange microstructure aggregates**, not direct institutional flow and not an off-exchange activity series.

The distinction matters: the SEC system may collect off-exchange prints internally, but that does not mean the public ticker-level HiddenVol/TradeVol metrics include them.

## 4. PIT and release chronology

The observation date inside a row is not the date on which a strategy could first use the quarterly file. The SEC page's current "Last Reviewed or Updated: June 30, 2026" field is a page-maintenance date, not the first-publication date of each quarter.

Phase 104 previously identified three contemporaneous SEC Market Structure bulletin anchors:
- 2021 Q3 — 2021-11-02
- 2023 Q1 — 2023-05-02
- 2023 Q4 — 2024-01-31

That is only **3 of 58 quarter releases (5.17%)**. The other 55 quarter-level release dates are not yet supported by a complete contemporaneous ledger. The Data.gov catalog's dataset-level modified date is stale and cannot substitute for a per-resource first-publication timestamp.

PIT ruling:
1. Never assign a row's trading date as its knowledge date.
2. Never use the current quarterly archive as if the entire quarter's rows had been available daily.
3. Preserve the first public release/vintage for each quarterly file and any later replacement separately.
4. Until all quarter release dates are reconstructed, admit no strict-PIT feature and run no forward-return test.
5. If release chronology can be reconstructed, test MIDAS first as a lagged quarterly microstructure-regime feature, not as a same-day daily order-flow signal.

## 5. Methodology breaks and candidate role

Two known methodology breaks require explicit treatment:
- **2017-05-01:** NYSE input changed from Ultrabook level feed to NYSE Integrated Feed. Hidden/quote/order metrics must be split or normalized across the break.
- **2025-11-03:** the SEC's round-lot definition changed. Odd-lot variables must be regime-separated or normalized; raw levels cannot be spliced blindly.

If the release/PIT gate passes, the narrow candidate family should begin with trade-to-order volume, hidden-volume rate using the SEC's exact denominator, and cancel-to-trade measures with the documented exchange coverage. Odd-lot features come later because of the 2025 definition change. Any predictive claim must control for contemporaneous/prior return, turnover, volatility, liquidity and the frozen LTM/F80 ranking.

MIDAS is retained as a **market-structure context candidate**, not as a Smart Money label. Its quarterly batch cadence may be useful for slow regime context, but it is not an intraday or daily first-receipt feed.

## 6. Hosted validation and reproducibility

The Phase 198 workflow:
- parses the current SEC page and expects 58 consecutive quarter links;
- probes only the first four bytes of the six disputed ZIPs;
- records HTTP status, ZIP magic, Content-Range, Content-Length, Last-Modified, Date and ETag;
- persists only metadata, not raw ZIPs or rows;
- enforces no PIT/alpha/holdout/production admission.

The resulting metadata-only JSON is retained as the GitHub Actions artifact. Offline regression tests cover quarter continuity, missing-quarter detection, ZIP signature validation and frozen/PIT controls.

## 7. Decision

**Keep SEC MIDAS in the candidate queue for slow market-structure context. Do not call it off-exchange or institutional flow. Do not admit it to a return test until a complete 58-quarter first-publication/vintage ledger, actual daily-row completeness and effective-dated ticker identity are established.**

No forward returns or alpha tests were run. No final holdout was used. No data were purchased, no provider was contacted, production was not changed, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- SEC [Metrics by Individual Security](https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security) — 2012 Q1–2026 Q2 archive.
- SEC [Metrics by Individual Security and Exchange](https://www.sec.gov/opa/data/market-structure/market-structure-data-security-and-exchange.html) — separate exchange-partitioned series.
- SEC [Market Structure Data Downloads](https://www.sec.gov/data-research/market-structure-data).
- SEC [MIDAS overview](https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system).
- SEC [MIDAS feedback and methodology FAQs](https://www.sec.gov/securities-topics/market-structure-analytics/midas-feedback).
- Third-party gap claim, retained only as a discrepancy to reconcile: [Obscura SEC MIDAS dataset description](https://obscura.trade/datasets/sec-midas-security-metrics/).
